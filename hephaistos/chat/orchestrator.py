"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
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
from hephaistos.runtime import (
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaistos.study import StudyState, apply_turn_result, plan_turn

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

        raw_reply = "".join(raw_parts)
        if last_reply_parts:
            self.last_reply = "".join(last_reply_parts)

        if raw_reply:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                raw_reply,
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

    def _resolve_timed_turn_plan(self, user_input: str) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(user_input)
        session.last_turn_evidence = resolved.turn_evidence
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
        notice = verify_response(self.last_reply, resolved.turn_evidence)

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
                    "evidence_blocks": (
                        len(resolved.turn_evidence.items) if resolved.turn_evidence else 0
                    ),
                }
            },
        )
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            study_phase=session.study_state.phase.value,
            study_feedback=session.study_state.last_feedback_type.value,
            evidence_blocks=len(resolved.turn_evidence.items) if resolved.turn_evidence else 0,
            evidence_refs=_evidence_refs(resolved.turn_evidence),
        )

        schedule_memory_extraction(
            config=session.config,
            memory=session.memory,
            user_input=user_input,
            reply=self.last_reply,
            evidence=", ".join(_evidence_refs(resolved.turn_evidence)),
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
