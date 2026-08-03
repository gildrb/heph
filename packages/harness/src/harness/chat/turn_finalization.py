"""Turn finalization, tracing, and persistence side effects."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from dataclasses import replace
from typing import TYPE_CHECKING

from ai.diagnostics import get_meter, get_tracer
from ai.logging import Timer, get_logger
from ai.runtime.conversation import Message

from harness.agent.citation import VerificationResult, verify_citations, verify_response
from harness.attempts.actions import AttemptAction
from harness.attempts.observation import AttemptObservation, build_attempt_observation
from harness.attempts.policy import StaticAttemptPolicy
from harness.chat.document_reply import _source_qa_abstain_reply, _validation_guard_abstain_reply
from harness.chat.document_signals import (
    _learner_assessment_trace,
    _pedagogy_validation_trace,
    _trace_task,
    _trace_turn_retrieval_query,
)
from harness.chat.events import MaterialOperationEvent
from harness.chat.evidence import (
    ResolvedTurnPlan,
)
from harness.chat.evidence import (
    assess_turn_evidence as _assess_turn_evidence,
)
from harness.chat.evidence import (
    evidence_assessment_trace as _evidence_assessment_trace,
)
from harness.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from harness.chat.evidence import (
    evidence_trace_coverage as _evidence_trace_coverage,
)
from harness.chat.evidence import (
    evidence_trace_items as _evidence_trace_items,
)
from harness.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from harness.chat.material_state import _material_operation_events
from harness.chat.overview_reply import _overview_answer_has_bad_shape
from harness.chat.reply_evidence import _resolved_with_visible_evidence_refs
from harness.chat.reply_repair import _MAX_INTERNAL_PASSES
from harness.chat.titles import derive_title
from harness.chat.turn_contract import (
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    TurnContract,
)
from harness.chat.turn_contract_checks import _contract_requests_table, _material_overview_turn
from harness.chat.turn_history import build_turn_snapshot
from harness.chat.turn_planning import (
    _resolved_turn_intent,
    _resolved_with_citation_requirement,
    _resolved_with_validation_result,
    _turn_contract_can_seed_followup,
)
from harness.chat.turn_predicates import (
    _stored_turn_evidence,
    _trace_excerpt,
    _visible_turn_evidence,
)
from harness.chat.usage import save_usage
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.documents.state import DocumentAction, RecallState
from harness.memory.workflow import schedule_memory_extraction
from harness.rag.context import TurnEvidence

if TYPE_CHECKING:
    from harness.chat.session import ChatSession

_log = get_logger("harness.chat.turn_finalization")
_tracer = get_tracer("harness.chat.turn_finalization")
_meter = get_meter("harness.chat.turn_finalization")
_rag_duration_hist = _meter.create_histogram(
    "harness.rag.retrieval.duration",
    unit="ms",
    description="Duration of RAG retrieval queries",
)


class TurnFinalizationMixin:
    session: ChatSession
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None
    _attempt_action_override: AttemptAction | None
    _attempt_followup_seed_blocked: bool

    def _reset_attempt_overrides(self) -> None:
        self._attempt_action_override = None
        self._attempt_followup_seed_blocked = False

    def _resolve_timed_turn_plan(self, plan: DocumentTurnPlan) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("harness.rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(plan)
        if not isinstance(resolved, ResolvedTurnPlan):
            resolved = ResolvedTurnPlan(document_plan=plan)
        resolved = replace(resolved, retrieval_latency_ms=rag_timer.ms)
        session.last_turn_evidence = _stored_turn_evidence(resolved)
        if resolved.turn_evidence is not None:
            rag_span.set_attribute("harness.rag.retrieved", len(resolved.turn_evidence.items))
        rag_span.end()
        _rag_duration_hist.record(rag_timer.ms, {"armory": str(session.armory_path or "none")})
        return resolved

    def _resolve_turn_plan(self, plan: DocumentTurnPlan) -> ResolvedTurnPlan:
        turn_evidence = _resolve_turn_evidence(self.session, plan)
        return ResolvedTurnPlan(
            document_plan=plan,
            turn_evidence=turn_evidence,
            evidence_assessment=_assess_turn_evidence(plan, turn_evidence),
        )

    def _iter_material_operation_events(
        self,
        plan: DocumentTurnPlan,
        resolved: ResolvedTurnPlan,
    ) -> Iterator[MaterialOperationEvent]:
        yield from self._record_material_operation_events(
            _material_operation_events(self.session, plan, resolved)
        )

    def _record_material_operation_events(
        self,
        events: Iterator[MaterialOperationEvent],
    ) -> Iterator[MaterialOperationEvent]:
        for event in events:
            self.session.trace.record_material_operation(
                operation=event.operation,
                message=event.message,
                metadata=event.metadata,
            )
            yield event

    def _rollback_turn(
        self,
        original_messages: list[Message],
        original_recall_state: RecallState,
    ) -> None:
        self.session.conversation.messages = original_messages
        self.session.recall_state = original_recall_state

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str:
        resolved = _resolved_with_citation_requirement(
            resolved,
            citation_required=self._last_reply_citation_required,
        )
        visible_evidence = _visible_turn_evidence(resolved)
        resolved = _resolved_with_visible_evidence_refs(
            resolved,
            self.last_reply,
            visible_evidence,
        )
        resolved = self._apply_structural_validation_guard(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
        )
        resolved = self._apply_structural_relevance_guard(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
        )
        visible_evidence = _visible_turn_evidence(resolved)
        followup_evidence = None if self._attempt_followup_seed_blocked else visible_evidence
        notice = self._verification_notice(resolved, visible_evidence)
        resolved = _resolved_with_validation_result(resolved, notice)
        followup_contract = None if self._attempt_followup_seed_blocked else resolved.turn_contract
        self._mark_session_dirty()
        self._record_successful_reply(
            resolved,
            visible_evidence,
            user_input=user_input,
            latency_ms=latency_ms,
            notice=notice,
        )
        if _turn_contract_can_seed_followup(
            followup_contract,
            visible_evidence=followup_evidence,
        ):
            self.session.last_plan_intent = _resolved_turn_intent(resolved)
            self.session.last_turn_contract = followup_contract
        elif self._attempt_followup_seed_blocked:
            self.session.last_turn_contract = None
        snapshot = build_turn_snapshot(
            self.session.conversation,
            self.session.turn_history,
            recall_state=self.session.recall_state,
            user_input=user_input,
            assistant_reply=self.last_reply,
            evidence=followup_evidence,
            plan_intent=_resolved_turn_intent(resolved),
            contract=followup_contract,
        )
        if snapshot is not None:
            self.session.turn_history.append(snapshot)
        self._schedule_memory_extraction(user_input, followup_evidence)
        self._save_usage_if_armory_session()
        return notice

    def _prepare_document_reply_for_emit(
        self,
        resolved: ResolvedTurnPlan,
        final_reply: str,
        *,
        user_input: str,
        latency_ms: float,
    ) -> tuple[ResolvedTurnPlan, str]:
        self.last_reply = final_reply
        resolved = _resolved_with_citation_requirement(
            resolved,
            citation_required=self._last_reply_citation_required,
        )
        visible_evidence = _visible_turn_evidence(resolved)
        resolved = _resolved_with_visible_evidence_refs(
            resolved,
            self.last_reply,
            visible_evidence,
        )
        resolved = self._apply_structural_validation_guard(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
        )
        resolved = self._apply_structural_relevance_guard(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
        )
        return resolved, self.last_reply

    def _verification_notice(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
    ) -> str:
        if (
            resolved.document_plan is not None
            and resolved.document_plan.action is DocumentAction.CALIBRATE
        ):
            return ""
        if resolved.turn_contract is not None and not resolved.turn_contract.citation_required:
            return ""
        return verify_response(self.last_reply, visible_evidence)

    def _mark_session_dirty(self) -> None:
        if not self.session.title:
            self.session.title = derive_title(self.session.conversation)
        self.session.dirty = True

    def _record_successful_reply(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        user_input: str,
        latency_ms: float,
        notice: str,
    ) -> None:
        self._log_successful_reply(visible_evidence, latency_ms=latency_ms)
        self._trace_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )

    def _apply_structural_validation_guard(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> ResolvedTurnPlan:
        if self._attempt_action_override is not None:
            return resolved
        observation = _policy_observation(
            resolved,
            visible_evidence,
            reply=self.last_reply,
            latency_ms=latency_ms,
            internal_passes=self.last_internal_passes,
        )
        if not _unsafe_validation_failure(observation):
            return resolved
        recommended_action = StaticAttemptPolicy().choose(observation)
        if recommended_action is AttemptAction.ACCEPT:
            recommended_action = _validation_failure_action(observation)
        guard_reply = _validation_guard_abstain_reply(resolved, observation)
        self._attempt_action_override = AttemptAction.ABSTAIN
        self.last_reply = guard_reply
        self._replace_last_assistant_message(self.last_reply)
        self.session.trace.record_session_event(
            "attempt_validation_guard",
            recommended_action=recommended_action.value,
            missing_required_citations=observation.missing_required_citation_count,
            unverified_citations=observation.unverified_citation_count,
            citation_required=observation.citation_required,
        )
        self.session.last_turn_evidence = None
        self.session.last_turn_contract = None
        self._attempt_followup_seed_blocked = True
        return _resolved_with_visible_evidence_refs(resolved, self.last_reply, visible_evidence)

    def _apply_structural_relevance_guard(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> ResolvedTurnPlan:
        if self._attempt_action_override is not None:
            return resolved
        observation = _policy_observation(
            resolved,
            visible_evidence,
            reply=self.last_reply,
            latency_ms=latency_ms,
            internal_passes=self.last_internal_passes,
        )
        if not observation.off_topic_answer:
            return resolved
        abstain_reply = _structural_abstain_reply(resolved)
        if not abstain_reply:
            return resolved
        self._attempt_action_override = AttemptAction.ABSTAIN
        self.last_reply = abstain_reply
        self._replace_last_assistant_message(self.last_reply)
        self._last_reply_citation_required = False
        self.session.trace.record_session_event(
            "attempt_relevance_guard",
            answer_relevance_score=observation.answer_relevance_score,
            retrieval_strategy=observation.retrieval_strategy,
            answer_mode=observation.answer_mode,
        )
        self.session.last_turn_evidence = None
        self.session.last_turn_contract = None
        self._attempt_followup_seed_blocked = True
        resolved = _resolved_with_citation_requirement(resolved, citation_required=False)
        return _resolved_with_visible_evidence_refs(resolved, self.last_reply, visible_evidence)

    def _replace_last_assistant_message(self, reply: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = reply
                return
        self.session.conversation.add("assistant", reply)

    def _log_successful_reply(
        self,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> None:
        session = self.session
        _log.info(
            "reply complete",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "reply_len": len(self.last_reply),
                    "latency_ms": latency_ms,
                    "recall_phase": session.recall_state.phase.value,
                    "recall_feedback": session.recall_state.last_feedback_type.value,
                    "evidence_blocks": len(visible_evidence.items) if visible_evidence else 0,
                }
            },
        )

    def _trace_successful_reply(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
        notice: str,
    ) -> None:
        session = self.session
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            reply_excerpt=_trace_excerpt(self.last_reply),
            recall_phase=session.recall_state.phase.value,
            document_action=resolved.document_plan.action.value if resolved.document_plan else "",
            material_task=_trace_task(resolved.document_plan),
            retrieval_query=_trace_turn_retrieval_query(resolved),
            turn_contract=(
                resolved.turn_contract.to_dict() if resolved.turn_contract is not None else {}
            ),
            recall_feedback=session.recall_state.last_feedback_type.value,
            evidence_blocks=len(visible_evidence.items) if visible_evidence else 0,
            evidence_refs=(
                list(resolved.turn_contract.evidence_refs)
                if resolved.turn_contract is not None
                else []
            ),
            evidence_coverage=_evidence_trace_coverage(visible_evidence),
            evidence_items=_evidence_trace_items(visible_evidence),
            evidence_assessment=_evidence_assessment_trace(resolved.evidence_assessment),
            pedagogy_validation=_pedagogy_validation_trace(
                resolved.document_plan,
                self.last_reply,
            ),
            learner_assessment=_learner_assessment_trace(
                resolved.document_plan,
                session.recall_state,
            ),
            internal_passes=self.last_internal_passes,
            internal_pass_max=_MAX_INTERNAL_PASSES,
            verification_notice=notice,
        )

    def _schedule_memory_extraction(
        self,
        user_input: str,
        visible_evidence: TurnEvidence | None,
    ) -> None:
        session = self.session
        if session.config.is_feature_enabled("disable_memory_extraction"):
            return
        schedule_memory_extraction(
            config=session.config,
            memory=session.memory,
            user_input=user_input,
            reply=self.last_reply,
            evidence=", ".join(_evidence_refs(visible_evidence)),
        )

    def _save_usage_if_armory_session(self) -> None:
        session = self.session
        if session.armory_path is None:
            return
        with contextlib.suppress(Exception):
            save_usage(session.armory_path, session.session_id, session.usage)


def _policy_observation(
    resolved: ResolvedTurnPlan,
    visible_evidence: TurnEvidence | None,
    *,
    reply: str,
    latency_ms: float,
    internal_passes: int,
    cost_usd: float = 0.0,
    citation_result: VerificationResult | None = None,
) -> AttemptObservation:
    contract = resolved.turn_contract
    return build_attempt_observation(
        attempt_index=1,
        intent=contract.resolved_intent if contract is not None else "",
        answer_mode=contract.answer_mode if contract is not None else "",
        retrieval_strategy=contract.retrieval_strategy if contract is not None else "",
        citation_required=contract.citation_required if contract is not None else False,
        evidence=visible_evidence,
        evidence_assessment=resolved.evidence_assessment,
        citation_result=(
            citation_result
            if citation_result is not None
            else verify_citations(reply, visible_evidence)
        ),
        reply=reply,
        latency_ms=latency_ms,
        internal_passes=internal_passes,
        cost_usd=cost_usd,
        request_text=_answer_relevance_target(contract),
        answer_relevance_required=_answer_relevance_required(contract),
        answer_shape_failed=_answer_shape_failed(resolved, visible_evidence, reply),
    )


def _unsafe_validation_failure(observation: AttemptObservation) -> bool:
    if observation.off_topic_answer:
        return False
    if observation.reply_chars <= 0:
        return True
    if observation.citation_required and (
        not observation.has_citations
        or not observation.all_citations_verified
        or observation.unverified_citation_count > 0
        or observation.missing_required_citation_count > 0
    ):
        return True
    return bool(observation.unsupported_claim_count)


def _validation_failure_action(observation: AttemptObservation) -> AttemptAction:
    if observation.evidence_count <= 0:
        return AttemptAction.RETRY_EXPAND_EVIDENCE
    if observation.citation_required or observation.unsupported_claim_count:
        return AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
    return AttemptAction.ABSTAIN


def _answer_relevance_required(contract: TurnContract | None) -> bool:
    if contract is None:
        return False
    return bool(
        contract.prior_answer_reference
        or contract.answer_mode
        in {
            ANSWER_MODE_REASON_FROM_PRIOR,
            ANSWER_MODE_TRANSFORM_PRIOR,
        }
        or contract.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        or contract.direct_evidence_required
    )


def _answer_shape_failed(
    resolved: ResolvedTurnPlan,
    visible_evidence: TurnEvidence | None,
    reply: str,
) -> bool:
    plan = resolved.document_plan
    contract = resolved.turn_contract
    if (
        plan is None
        or visible_evidence is None
        or not visible_evidence.items
        or not _material_overview_turn(plan, contract)
    ):
        return False
    return _overview_answer_has_bad_shape(
        reply,
        visible_evidence,
        allow_table=_contract_requests_table(contract),
    )


def _answer_relevance_target(contract: TurnContract | None) -> str:
    if contract is None:
        return ""
    return "\n".join(
        value
        for value in (
            getattr(contract, "canonical_request", ""),
            getattr(contract, "retrieval_query", ""),
            getattr(contract, "original_user_input", ""),
            _prior_answer_relevance_target(contract),
        )
        if isinstance(value, str) and value.strip()
    )


def _prior_answer_relevance_target(contract: TurnContract) -> str:
    if contract.retrieval_query.strip():
        return ""
    if not (
        contract.prior_answer_reference
        or contract.answer_mode
        in {
            ANSWER_MODE_REASON_FROM_PRIOR,
            ANSWER_MODE_TRANSFORM_PRIOR,
        }
    ):
        return ""
    return contract.prior_answer_excerpt


def _structural_abstain_reply(resolved: ResolvedTurnPlan) -> str:
    plan = resolved.document_plan
    if plan is None:
        return ""
    return _source_qa_abstain_reply(plan, resolved, force=True)
