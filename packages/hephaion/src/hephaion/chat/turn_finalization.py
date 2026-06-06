"""Turn finalization, tracing, and persistence side effects."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ai.logging import Timer, get_logger
from ai.runtime.conversation import Message

from hephaion.agent.citation import VerificationResult, verify_citations, verify_response
from hephaion.chat.events import MaterialOperationEvent
from hephaion.chat.evidence import (
    ResolvedTurnPlan,
)
from hephaion.chat.evidence import (
    assess_turn_evidence as _assess_turn_evidence,
)
from hephaion.chat.evidence import (
    evidence_assessment_trace as _evidence_assessment_trace,
)
from hephaion.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from hephaion.chat.evidence import (
    evidence_trace_coverage as _evidence_trace_coverage,
)
from hephaion.chat.evidence import (
    evidence_trace_items as _evidence_trace_items,
)
from hephaion.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from hephaion.chat.learning_reply import _source_qa_abstain_reply, _validation_guard_abstain_reply
from hephaion.chat.learning_signals import (
    _learner_assessment_trace,
    _pedagogy_validation_trace,
    _trace_task,
    _trace_turn_retrieval_query,
)
from hephaion.chat.material_state import _material_operation_events
from hephaion.chat.reply_repair import _MAX_INTERNAL_PASSES
from hephaion.chat.titles import derive_title
from hephaion.chat.turn_contract import (
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    TurnContract,
)
from hephaion.chat.turn_history import build_turn_snapshot
from hephaion.chat.turn_planning import (
    _resolved_turn_intent,
    _resolved_with_citation_requirement,
    _resolved_with_validation_result,
    _resolved_with_visible_evidence_refs,
    _turn_contract_can_seed_followup,
)
from hephaion.chat.turn_predicates import (
    _stored_turn_evidence,
    _trace_excerpt,
    _visible_turn_evidence,
)
from hephaion.chat.usage import save_usage
from hephaion.diagnostics.crashes import get_meter, get_tracer
from hephaion.learning.actions import AttemptAction
from hephaion.learning.automation import maybe_auto_train_attempt_policy
from hephaion.learning.environment import LiveHephEnv
from hephaion.learning.observation import AttemptObservation, build_attempt_observation
from hephaion.learning.policy_artifact import ExportedAttemptPolicy, load_runtime_policy
from hephaion.learning.reward import score_attempt_reward
from hephaion.learning.storage import (
    ActionOutcome,
    AttemptRecord,
    ValidationState,
    new_attempt_record,
)
from hephaion.memory.workflow import schedule_memory_extraction
from hephaion.rag.context import TurnEvidence
from hephaion.study.prompt_plans import LearningTurnPlan
from hephaion.study.state import LearningAction, LearningState

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

_log = get_logger("hephaion.chat.turn_finalization")
_tracer = get_tracer("hephaion.chat.turn_finalization")
_meter = get_meter("hephaion.chat.turn_finalization")
_rag_duration_hist = _meter.create_histogram(
    "hephaion.rag.retrieval.duration",
    unit="ms",
    description="Duration of RAG retrieval queries",
)


@dataclass(frozen=True, slots=True)
class _RecordedLearningAttempt:
    record: AttemptRecord
    observation: AttemptObservation
    action: AttemptAction
    recommended_action: AttemptAction


class TurnFinalizationMixin:
    session: ChatSession
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None
    _learning_action_override: AttemptAction | None
    _learning_recommended_action_override: AttemptAction | None
    _learning_followup_seed_blocked: bool

    def _reset_learning_attempt_overrides(self) -> None:
        self._learning_action_override = None
        self._learning_recommended_action_override = None
        self._learning_followup_seed_blocked = False

    def _resolve_timed_turn_plan(self, plan: LearningTurnPlan) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("hephaion.rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(plan)
        if not isinstance(resolved, ResolvedTurnPlan):
            resolved = ResolvedTurnPlan(learning_plan=plan)
        resolved = replace(resolved, retrieval_latency_ms=rag_timer.ms)
        session.last_turn_evidence = _stored_turn_evidence(resolved)
        if resolved.turn_evidence is not None:
            rag_span.set_attribute("hephaion.rag.retrieved", len(resolved.turn_evidence.items))
        rag_span.end()
        _rag_duration_hist.record(rag_timer.ms, {"armory": str(session.armory_path or "none")})
        return resolved

    def _resolve_turn_plan(self, plan: LearningTurnPlan) -> ResolvedTurnPlan:
        turn_evidence = _resolve_turn_evidence(self.session, plan)
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=turn_evidence,
            evidence_assessment=_assess_turn_evidence(plan, turn_evidence),
        )

    def _iter_material_operation_events(
        self,
        plan: LearningTurnPlan,
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
        original_learning_state: LearningState,
    ) -> None:
        self.session.conversation.messages = original_messages
        self.session.learning_state = original_learning_state

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
        resolved = self._apply_promoted_runtime_action(
            resolved,
            visible_evidence,
            user_input=user_input,
            latency_ms=latency_ms,
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
        followup_evidence = None if self._learning_followup_seed_blocked else visible_evidence
        followup_contract = (
            None if self._learning_followup_seed_blocked else resolved.turn_contract
        )
        notice = self._verification_notice(resolved, visible_evidence)
        resolved = _resolved_with_validation_result(resolved, notice)
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
        elif self._learning_followup_seed_blocked:
            self.session.last_turn_contract = None
        snapshot = build_turn_snapshot(
            self.session.conversation,
            self.session.turn_history,
            learning_state=self.session.learning_state,
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

    def _prepare_learning_reply_for_emit(
        self,
        resolved: ResolvedTurnPlan,
        final_reply: str,
        *,
        user_input: str,
        latency_ms: float,
    ) -> tuple[ResolvedTurnPlan, str]:
        self.last_reply = final_reply
        visible_evidence = _visible_turn_evidence(resolved)
        resolved = _resolved_with_visible_evidence_refs(
            resolved,
            self.last_reply,
            visible_evidence,
        )
        resolved = self._apply_promoted_runtime_action(
            resolved,
            visible_evidence,
            user_input=user_input,
            latency_ms=latency_ms,
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
            resolved.learning_plan is not None
            and resolved.learning_plan.action is LearningAction.CALIBRATE
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
        self._record_learning_attempt(
            resolved,
            visible_evidence,
            user_input=user_input,
            latency_ms=latency_ms,
        )
        self._trace_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )

    def _record_learning_attempt(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        user_input: str,
        latency_ms: float,
    ) -> None:
        session = self.session
        if session.armory_path is None:
            return
        runtime_policy = load_runtime_policy(session.armory_path)
        attempt = _recorded_learning_attempt(
            session,
            resolved,
            visible_evidence,
            user_input=user_input,
            reply=self.last_reply,
            internal_passes=self.last_internal_passes,
            latency_ms=latency_ms,
            action_override=getattr(self, "_learning_action_override", None),
            recommended_action_override=getattr(
                self,
                "_learning_recommended_action_override",
                None,
            ),
            runtime_action=runtime_policy.choose,
        )
        try:
            env = LiveHephEnv(session.armory_path)
            env.choose_action(attempt.observation, attempt.recommended_action)
            env.finalize(attempt.record)
        except OSError:
            _log.warning("failed to record local learning attempt", exc_info=True)
            return
        session.trace.record_session_event(
            "learning_attempt",
            action=attempt.action.value,
            recommended_action=attempt.recommended_action.value,
            reward=attempt.record.reward.total,
            reward_components={
                component.name: round(component.value, 4)
                for component in attempt.record.reward.components
            },
        )
        self._maybe_auto_train_learning_policy()

    def _maybe_auto_train_learning_policy(self) -> None:
        session = self.session
        if session.armory_path is None:
            return
        try:
            decision = maybe_auto_train_attempt_policy(session.armory_path)
        except (OSError, RuntimeError, ValueError):
            _log.warning("automated learning-policy training failed", exc_info=True)
            return
        session.trace.record_session_event(
            "learning_auto_train",
            status=decision.status,
            reason=decision.reason,
            attempt_count=decision.attempt_count,
            new_attempt_count=decision.new_attempt_count,
            policy_id=decision.report.policy_id if decision.report is not None else "",
            training_decision=(decision.report.decision if decision.report is not None else ""),
        )

    def _apply_promoted_runtime_action(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        user_input: str,
        latency_ms: float,
    ) -> ResolvedTurnPlan:
        session = self.session
        if session.armory_path is None:
            return resolved
        runtime_policy = load_runtime_policy(session.armory_path)
        if not isinstance(runtime_policy, ExportedAttemptPolicy):
            return resolved
        observation = _policy_observation(
            resolved,
            visible_evidence,
            reply=self.last_reply,
            latency_ms=latency_ms,
            internal_passes=self.last_internal_passes,
        )
        action = runtime_policy.choose(observation)
        if action is not AttemptAction.ABSTAIN:
            # Retry actions require a separate retrieval/generation executor. Until one exists,
            # keep them as policy recommendations in replay metadata rather than pretending
            # the completed turn actually retried.
            return resolved
        runtime_reply = _runtime_abstain_reply(resolved)
        if not runtime_reply:
            return resolved
        self._learning_action_override = AttemptAction.ABSTAIN
        self._learning_recommended_action_override = action
        self.last_reply = runtime_reply
        self._replace_last_assistant_message(self.last_reply)
        self._last_reply_citation_required = False
        self.session.last_turn_evidence = None
        self.session.last_turn_contract = None
        self._learning_followup_seed_blocked = True
        resolved = _resolved_with_citation_requirement(resolved, citation_required=False)
        return _resolved_with_visible_evidence_refs(resolved, self.last_reply, visible_evidence)

    def _apply_structural_validation_guard(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> ResolvedTurnPlan:
        if self._learning_action_override is not None:
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
        runtime_policy = load_runtime_policy(self.session.armory_path)
        recommended_action = runtime_policy.choose(observation)
        if recommended_action is AttemptAction.ACCEPT:
            recommended_action = _validation_failure_action(observation)
        guard_reply = _validation_guard_abstain_reply(resolved, observation)
        self._learning_action_override = AttemptAction.ABSTAIN
        self._learning_recommended_action_override = recommended_action
        self.last_reply = guard_reply
        self._replace_last_assistant_message(self.last_reply)
        self.session.trace.record_session_event(
            "learning_validation_guard",
            recommended_action=recommended_action.value,
            missing_required_citations=observation.missing_required_citation_count,
            unverified_citations=observation.unverified_citation_count,
            citation_required=observation.citation_required,
        )
        self.session.last_turn_evidence = None
        self.session.last_turn_contract = None
        self._learning_followup_seed_blocked = True
        return _resolved_with_visible_evidence_refs(resolved, self.last_reply, visible_evidence)

    def _apply_structural_relevance_guard(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> ResolvedTurnPlan:
        if self._learning_action_override is not None:
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
        self._learning_action_override = AttemptAction.ABSTAIN
        self._learning_recommended_action_override = AttemptAction.ABSTAIN
        self.last_reply = abstain_reply
        self._replace_last_assistant_message(self.last_reply)
        self._last_reply_citation_required = False
        self.session.trace.record_session_event(
            "learning_relevance_guard",
            answer_relevance_score=observation.answer_relevance_score,
            retrieval_strategy=observation.retrieval_strategy,
            answer_mode=observation.answer_mode,
        )
        self.session.last_turn_evidence = None
        self.session.last_turn_contract = None
        self._learning_followup_seed_blocked = True
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
                    "learning_phase": session.learning_state.phase.value,
                    "learning_feedback": session.learning_state.last_feedback_type.value,
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
            learning_phase=session.learning_state.phase.value,
            learning_action=resolved.learning_plan.action.value if resolved.learning_plan else "",
            material_task=_trace_task(resolved.learning_plan),
            retrieval_query=_trace_turn_retrieval_query(resolved),
            turn_contract=(
                resolved.turn_contract.to_dict() if resolved.turn_contract is not None else {}
            ),
            learning_feedback=session.learning_state.last_feedback_type.value,
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
                resolved.learning_plan,
                self.last_reply,
            ),
            learner_assessment=_learner_assessment_trace(
                resolved.learning_plan,
                session.learning_state,
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


def _citation_validation_states(
    citation_result: VerificationResult,
    *,
    required: bool,
) -> tuple[ValidationState, ...]:
    verified = getattr(citation_result, "verified", [])
    unverified = getattr(citation_result, "unverified", [])
    has_citations = bool(getattr(citation_result, "has_citations", False))
    all_verified = bool(getattr(citation_result, "all_verified", True))
    return (
        ValidationState(
            name="citation_present",
            passed=has_citations or not required,
            detail=f"verified={len(verified)} unverified={len(unverified)}",
        ),
        ValidationState(
            name="citation_verified",
            passed=all_verified,
            detail=", ".join(str(item) for item in unverified),
        ),
    )


def _recorded_learning_attempt(
    session: ChatSession,
    resolved: ResolvedTurnPlan,
    visible_evidence: TurnEvidence | None,
    *,
    user_input: str,
    reply: str,
    internal_passes: int,
    latency_ms: float,
    action_override: AttemptAction | None,
    recommended_action_override: AttemptAction | None,
    runtime_action: Callable[[AttemptObservation], AttemptAction],
) -> _RecordedLearningAttempt:
    turn_cost_usd = _turn_cost_usd(session)
    citation_result = verify_citations(reply, visible_evidence)
    observation = _policy_observation(
        resolved,
        visible_evidence,
        reply=reply,
        latency_ms=latency_ms,
        internal_passes=internal_passes,
        cost_usd=turn_cost_usd,
        citation_result=citation_result,
    )
    action = action_override or _final_action_for_observation(observation)
    recommended_action = recommended_action_override or runtime_action(observation)
    record = _attempt_record(
        session,
        resolved,
        visible_evidence,
        user_input=user_input,
        reply=reply,
        latency_ms=latency_ms,
        cost_usd=turn_cost_usd,
        citation_result=citation_result,
        observation=observation,
        action=action,
        recommended_action=recommended_action,
    )
    return _RecordedLearningAttempt(
        record=record,
        observation=observation,
        action=action,
        recommended_action=recommended_action,
    )


def _attempt_record(
    session: ChatSession,
    resolved: ResolvedTurnPlan,
    visible_evidence: TurnEvidence | None,
    *,
    user_input: str,
    reply: str,
    latency_ms: float,
    cost_usd: float,
    citation_result: VerificationResult,
    observation: AttemptObservation,
    action: AttemptAction,
    recommended_action: AttemptAction,
) -> AttemptRecord:
    accepted = action is AttemptAction.ACCEPT
    abstained = action is AttemptAction.ABSTAIN
    final_outcome = _final_outcome_for_action(action)
    reward = score_attempt_reward(observation, accepted=accepted, abstained=abstained)
    citation_validation = _citation_validation_states(
        citation_result,
        required=observation.citation_required,
    )
    evidence_validation = _evidence_validation_states(resolved, observation)
    validation_states = (*citation_validation, *evidence_validation)
    turn_id = _learning_turn_id(session)
    return new_attempt_record(
        session_id=session.session_id,
        turn_id=turn_id,
        episode_id=turn_id,
        attempt_index=1,
        action=action,
        observation=observation,
        reward=reward,
        user_input=user_input,
        reply=reply,
        evidence=visible_evidence,
        accepted=accepted,
        abstained=abstained,
        final_outcome=final_outcome,
        failed_validation_states=tuple(state for state in validation_states if not state.passed),
        evidence_validation=evidence_validation,
        citation_validation=citation_validation,
        action_outcomes=(
            ActionOutcome(
                action=action,
                observation=observation,
                reward=reward,
                final_outcome=final_outcome,
                accepted=accepted,
                abstained=abstained,
                attempts=1,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                validation_states=validation_states,
            ),
        ),
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        replay_metadata={
            "data_origin": "local",
            "dataset_kind": "armory-local",
            "policy_action": recommended_action.value,
            "schema": "heph-learning-episode-v2",
        },
    )


def _learning_turn_id(session: ChatSession) -> str:
    return f"{session.session_id}:{len(session.turn_history) + 1}"


def _evidence_validation_states(
    resolved: ResolvedTurnPlan,
    observation: AttemptObservation,
) -> tuple[ValidationState, ...]:
    assessment = resolved.evidence_assessment
    if assessment is None:
        return (ValidationState(name="evidence_assessed", passed=False, detail="missing"),)
    return (
        ValidationState(
            name="evidence_sufficient",
            passed=assessment.sufficient,
            detail=assessment.recommended_action,
        ),
        ValidationState(
            name="evidence_source_diversity",
            passed=assessment.source_diversity_score > 0,
            detail=f"{assessment.source_diversity_score:.3f}",
        ),
        ValidationState(
            name="answer_relevance",
            passed=not observation.off_topic_answer,
            detail=f"{observation.answer_relevance_score:.3f}",
        ),
    )


def _turn_cost_usd(session: ChatSession) -> float:
    summary = session.usage.summary()
    value = summary.get("cost_usd", 0.0)
    if isinstance(value, bool):
        return 0.0
    total = float(value) if isinstance(value, int | float) else 0.0
    turn_cost = round(max(0.0, total - session._last_learning_cost_usd), 6)
    session._last_learning_cost_usd = total
    return turn_cost


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
    )


def _runtime_abstain_reply(resolved: ResolvedTurnPlan) -> str:
    plan = resolved.learning_plan
    if plan is None:
        return ""
    return _source_qa_abstain_reply(plan, resolved)


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
    plan = resolved.learning_plan
    if plan is None:
        return ""
    return _source_qa_abstain_reply(plan, resolved, force=True)


def _final_action_for_observation(observation: AttemptObservation) -> AttemptAction:
    if _observation_abstained(observation):
        return AttemptAction.ABSTAIN
    return AttemptAction.ACCEPT


def _observation_abstained(observation: AttemptObservation) -> bool:
    return bool(
        not observation.citation_required
        and not observation.evidence_sufficient
        and observation.evidence_recommended_action == "abstain"
    )


def _final_outcome_for_action(action: AttemptAction) -> str:
    if action is AttemptAction.ACCEPT:
        return "accepted"
    if action is AttemptAction.ABSTAIN:
        return "abstained"
    return "retry_recommended"
