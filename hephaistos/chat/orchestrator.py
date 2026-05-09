"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import re
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hephaistos.agent.citation import verify_response
from hephaistos.agent.dispatch import iter_agent_events
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, TurnEvent
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
)
from hephaistos.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from hephaistos.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from hephaistos.chat.titles import derive_title
from hephaistos.chat.usage import save_usage
from hephaistos.diagnostics.crashes import get_meter, get_tracer
from hephaistos.logging import Timer, get_logger
from hephaistos.memory.workflow import schedule_memory_extraction
from hephaistos.rag import TurnEvidence
from hephaistos.runtime import (
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaistos.study import StudyAction, StudyState, StudyTurnPlan, apply_turn_result, plan_turn
from hephaistos.study.schedule import load_study_schedule, save_study_schedule

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_log = get_logger("chat.orchestrator")
_tracer = get_tracer("chat.orchestrator")
_meter = get_meter("chat.orchestrator")
_rag_duration_hist = _meter.create_histogram(
    "rag.retrieval.duration",
    unit="ms",
    description="Duration of RAG retrieval queries",
)

_EVIDENCE_REQUIRED_ACTIONS = frozenset(
    {
        StudyAction.PRIORITY,
        StudyAction.SOURCE_QA,
        StudyAction.PRESENT,
        StudyAction.HINT,
        StudyAction.SIMPLIFY,
        StudyAction.REVIEW,
        StudyAction.ASSESS,
    }
)
_EVIDENCE_CITATION_TEXT_RE = re.compile(
    r"\s*(?:\[|【)(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*(?:\]|】)"
)
_EXACT_PHRASE_AFTER_LABEL_RE = re.compile(
    r"\b(?:exact\s+)?phrase\s+(?:is\s*:?\s*)?(?P<phrase>[^\n.;:]+?)(?:\s+when\b|[.]\s*|$)",
    re.IGNORECASE,
)
_QUOTED_PHRASE_RE = re.compile(r"[\"“”'](?P<phrase>[^\"“”']{2,80})[\"“”']")


def _material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    return f"@{name or source}"


def _format_material_labels(sources: list[str]) -> str:
    labels = [_material_label(source) for source in sources[:3]]
    rendered = ", ".join(labels)
    remaining = len(sources) - len(labels)
    if remaining > 0:
        rendered = f"{rendered}, and {remaining} more"
    return rendered


def _missing_indexed_material_reply(session: ChatSession, action: StudyAction) -> str:
    if action not in _EVIDENCE_REQUIRED_ACTIONS:
        return ""
    index = session.rag_index
    if session.source_file_count <= 0:
        return ""
    if index is None:
        return (
            "The armory has visible materials, but the materials index could not be "
            "loaded for this turn. I cannot answer from outside knowledge. Rebuild the "
            "materials index with `heph index <armory>`."
        )
    if index.chunk_count > 0:
        indexed_enabled = any(
            document.source not in session.disabled_source_files and document.chunks
            for document in index.documents
        )
        if indexed_enabled:
            return ""
        return (
            "The armory has searchable materials, but all indexed material is currently "
            "disabled. Enable at least one material with /materials before asking."
        )

    unindexable_sources = [
        source
        for source in sorted(index.unindexable_files)
        if source not in session.disabled_source_files
    ]
    if unindexable_sources:
        materials = _format_material_labels(unindexable_sources)
        reasons = {index.unindexable_files[source] for source in unindexable_sources}
        if all("conversion backend unavailable" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but PDF/document conversion is unavailable in this "
                "installation. I cannot answer from outside knowledge. Update or reinstall "
                "Hephaistos, then rebuild the materials index with `heph index <armory>`."
            )
        if all("docling conversion failed" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but document conversion did not extract searchable "
                "text from it. I cannot answer from outside knowledge. Re-export or replace "
                "the document, then rebuild the materials index with `heph index <armory>`."
            )
        if all("docling" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but it is not searchable armory evidence yet. "
                "I cannot answer from outside knowledge. Update Hephaistos and rebuild the "
                "materials index with `heph index <armory>`."
            )
        return (
            f"I can see {materials}, but no searchable text was indexed from it. "
            "I cannot answer from outside knowledge. Convert the material to text or "
            "Markdown and rebuild the materials index with `heph index <armory>`."
        )

    return (
        "The armory has visible materials, but no searchable evidence is indexed yet. "
        "I cannot answer from outside knowledge. Rebuild the materials index with "
        "`heph index <armory>`."
    )


def _visible_turn_evidence(resolved: ResolvedTurnPlan) -> TurnEvidence | None:
    plan = resolved.study_plan
    if plan is not None and plan.action is StudyAction.CALIBRATE:
        return None
    return resolved.turn_evidence


def _student_visible_reply(plan: StudyTurnPlan, reply: str) -> str:
    if plan.action is StudyAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", reply).strip()
    return reply


def _source_qa_fallback_reply(plan: StudyTurnPlan, evidence: TurnEvidence | None) -> str:
    """Return a local source-grounded fallback when source QA streaming is empty."""
    if plan.action is not StudyAction.SOURCE_QA:
        return ""
    if evidence is None or not evidence.items:
        return (
            "The enabled armory sources do not contain an answer to that question. "
            "Enable the relevant material with /materials or add a more specific source."
        )

    query = plan.retrieval_query or ""
    wants_exact_phrase = bool(
        re.search(r"\bexact phrase\b|\bexact wording\b", query, re.IGNORECASE)
    )
    if wants_exact_phrase:
        for item in evidence.items:
            for pattern in (_QUOTED_PHRASE_RE, _EXACT_PHRASE_AFTER_LABEL_RE):
                match = pattern.search(item.content)
                if match is not None:
                    phrase = " ".join(match.group("phrase").strip().split())
                    if phrase:
                        return f'"{phrase}" [{item.evidence_id}]'

    first = evidence.items[0]
    return (
        "I found relevant source text, but could not generate a direct answer. "
        f"Expand /evidence {first.evidence_id} to read it."
    )


@dataclass(slots=True)
class TurnOrchestrator:
    """Own one user turn end-to-end."""

    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)

    def iter_events(
        self,
        user_input: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        original_messages = list(session.conversation.messages)
        original_study_state = session.study_state.clone()
        timer = Timer()
        self.last_reply = ""

        session.conversation.add("user", user_input)
        session.trace.record_user_message(user_input)
        _log.info(
            "user message",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "input_len": len(user_input),
                    "message_count": len(session.conversation.messages),
                    "study_phase": session.study_state.phase.value,
                }
            },
        )

        resolved = ResolvedTurnPlan()
        try:
            with timer:
                if session.armory_path is not None:
                    resolved = self._resolve_timed_turn_plan(user_input)
                    for event in self._iter_study_events(
                        resolved,
                        original_study_state,
                        abort=abort,
                    ):
                        yield event
                else:
                    session.last_turn_evidence = None
                    plain_plan = plan_turn(original_study_state, user_input)
                    if plain_plan.direct_reply is not None:
                        session.study_state, final_reply = apply_turn_result(
                            original_study_state,
                            plain_plan,
                            plain_plan.direct_reply,
                            [],
                        )
                        self.last_reply = final_reply
                        if final_reply and (
                            not session.conversation.messages
                            or session.conversation.messages[-1].role != "assistant"
                        ):
                            session.conversation.add("assistant", final_reply)
                        if final_reply:
                            yield AssistantDeltaEvent(final_reply)
                        return
                    for event in self._iter_plain_events(abort=abort):
                        yield event

            notice = self._finalize_successful_turn(user_input, resolved, latency_ms=timer.ms)
            if notice:
                yield NoticeEvent(notice, code="verification")
        except StreamRecoveryError as rec:
            _log.warning(
                "stream interrupted, rolling back",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "partial_len": len(rec.partial_content),
                        "latency_ms": timer.ms,
                    }
                },
            )
            self._rollback_turn(original_messages, original_study_state)
            session.dirty = True
            raise
        except EngineError as exc:
            _log.warning(
                "turn orchestration failed: %s",
                exc,
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "latency_ms": timer.ms,
                    }
                },
            )
            self._rollback_turn(original_messages, original_study_state)
            raise
        except Exception:
            _log.error(
                "turn orchestration failed",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "latency_ms": timer.ms,
                    }
                },
                exc_info=True,
            )
            self._rollback_turn(original_messages, original_study_state)
            raise

    def _iter_plain_events(self, *, abort: threading.Event | None) -> Iterator[TurnEvent]:
        session = self.session
        parts: list[str] = []
        for delta in stream_completion(
            session.config,
            session.conversation,
            abort=abort,
            retry=self.retry,
            client_factory=build_client,
        ):
            if not delta.content:
                continue
            parts.append(delta.content)
            yield AssistantDeltaEvent(delta.content)

        if parts:
            self.last_reply = "".join(parts)

        if self.last_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", self.last_reply)

    def _iter_study_events(
        self,
        resolved: ResolvedTurnPlan,
        original_study_state: StudyState,
        *,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.study_plan
        assert plan is not None

        if missing_reply := _missing_indexed_material_reply(session, plan.action):
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                missing_reply,
                [],
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if plan.direct_reply is not None:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                plan.direct_reply,
                [],
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        raw_parts: list[str] = []
        last_reply_parts: list[str] = []
        for event in iter_agent_events(
            session.config,
            session.conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=plan.prompt,
            tool_schemas=None if plan.allow_tools else [],
            registry=session.tool_registry,
        ):
            if isinstance(event, AssistantDeltaEvent):
                raw_parts.append(event.delta)
                if not plan.buffer_response:
                    last_reply_parts.append(event.delta)
                    yield event
            else:
                yield event

        raw_reply = "".join(raw_parts)
        visible_reply = _student_visible_reply(plan, raw_reply)
        if last_reply_parts:
            self.last_reply = "".join(last_reply_parts)

        if not raw_reply:
            fallback_reply = _source_qa_fallback_reply(plan, resolved.turn_evidence)
            if not fallback_reply:
                fallback_reply = (
                    "I could not generate a grounded assessment. Please try again."
                    if plan.buffer_response
                    else "I could not generate a study prompt. Please try again."
                )
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                fallback_reply,
                _evidence_refs(resolved.turn_evidence),
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if raw_reply:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                visible_reply,
                _evidence_refs(resolved.turn_evidence),
            )
            self._record_study_review_if_needed(
                original_study_state,
                plan,
                _evidence_refs(resolved.turn_evidence),
            )
        else:
            session.study_state = original_study_state
            final_reply = raw_reply

        if final_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", final_reply)
        elif final_reply and raw_reply != final_reply:
            self._replace_last_assistant_message(final_reply)

        self.last_reply = final_reply
        if plan.buffer_response and final_reply:
            yield AssistantDeltaEvent(final_reply)

    def _record_study_review_if_needed(
        self,
        original_study_state: StudyState,
        plan: StudyTurnPlan,
        source_refs: list[str],
    ) -> None:
        session = self.session
        if session.armory_path is None or plan.action is not StudyAction.ASSESS:
            return
        if session.study_state.last_recall_rating.value == "none":
            return
        store = load_study_schedule(session.armory_path)
        store.record_review(
            original_study_state.current_item,
            retrieval_query=original_study_state.retrieval_query,
            source_refs=source_refs or original_study_state.expected_source_refs,
            rating=session.study_state.last_recall_rating,
            elapsed_seconds=session.study_state.last_recall_seconds,
        )
        save_study_schedule(store)

    def _resolve_timed_turn_plan(self, user_input: str) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(user_input)
        visible_evidence = _visible_turn_evidence(resolved)
        session.last_turn_evidence = visible_evidence
        if resolved.turn_evidence is not None:
            rag_span.set_attribute("rag.retrieved", len(resolved.turn_evidence.items))
        rag_span.end()
        _rag_duration_hist.record(rag_timer.ms, {"armory": str(session.armory_path or "none")})
        return resolved

    def _resolve_turn_plan(self, user_input: str) -> ResolvedTurnPlan:
        plan = plan_turn(self.session.study_state, user_input)
        return ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=_resolve_turn_evidence(self.session, plan),
        )

    def _rollback_turn(
        self,
        original_messages: list[Message],
        original_study_state: StudyState,
    ) -> None:
        self.session.conversation.messages = original_messages
        self.session.study_state = original_study_state

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str:
        session = self.session
        visible_evidence = _visible_turn_evidence(resolved)
        if resolved.study_plan is not None and resolved.study_plan.action is StudyAction.CALIBRATE:
            notice = ""
        else:
            notice = verify_response(self.last_reply, visible_evidence)

        if not session.title:
            session.title = derive_title(session.conversation)
        session.dirty = True

        _log.info(
            "reply complete",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "reply_len": len(self.last_reply),
                    "latency_ms": latency_ms,
                    "study_phase": session.study_state.phase.value,
                    "study_feedback": session.study_state.last_feedback_type.value,
                    "evidence_blocks": len(visible_evidence.items) if visible_evidence else 0,
                }
            },
        )
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            study_phase=session.study_state.phase.value,
            study_feedback=session.study_state.last_feedback_type.value,
            evidence_blocks=len(visible_evidence.items) if visible_evidence else 0,
            evidence_refs=_evidence_refs(visible_evidence),
        )

        schedule_memory_extraction(
            config=session.config,
            memory=session.memory,
            user_input=user_input,
            reply=self.last_reply,
            evidence=", ".join(_evidence_refs(visible_evidence)),
        )

        if session.armory_path is not None:
            with contextlib.suppress(Exception):
                save_usage(session.armory_path, session.session_id, session.usage)

        return notice

    def _replace_last_assistant_message(self, content: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = content
                return
