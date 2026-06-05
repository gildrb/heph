"""Top-level chat turn lifecycle and rollback handling."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from ai_logging import Timer, get_logger
from runtime.conversation import Message
from runtime.errors import EngineError, StreamRecoveryError
from safety.contracts import (
    GUARDRAIL_ACTION_WARN,
    GUARDRAIL_STAGE_OUTPUT,
    GuardrailMessage,
)
from safety.local import check_user_input
from study.state import LearningState

from chat.events import GuardrailEvent, NoticeEvent, TurnEvent
from chat.evidence import ResolvedTurnPlan
from chat.turn_event_helpers import _final_reply_events

if TYPE_CHECKING:
    from chat.session import ChatSession

_log = get_logger("chat.turn_lifecycle")


@dataclass(frozen=True, slots=True)
class _PreparedTurn:
    original_messages: list[Message]
    original_learning_state: LearningState
    guardrail_event: GuardrailEvent | None
    blocked: bool


class _TurnLifecycleHost(Protocol):
    session: ChatSession
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None

    def _prepare_turn(self, user_input: str) -> _PreparedTurn: ...

    def _record_user_turn(self, user_input: str) -> None: ...

    def _iter_prepared_turn(
        self,
        prepared: _PreparedTurn,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]: ...

    def _iter_session_turn_events(
        self,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]: ...

    def _iter_armory_turn_events(
        self,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]: ...

    def _iter_plain_events(
        self,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]: ...

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str: ...

    def _emit_verification_notice(self, notice: str) -> Iterator[TurnEvent]: ...

    def _handle_stream_recovery_error(
        self,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
        error: StreamRecoveryError,
    ) -> None: ...

    def _handle_engine_error(
        self,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
        error: EngineError,
    ) -> None: ...

    def _handle_unexpected_error(
        self,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
    ) -> None: ...

    def _record_turn_error(self, user_input: str, timer: Timer, error: str) -> None: ...

    def _rollback_turn(
        self,
        original_messages: list[Message],
        original_learning_state: LearningState,
    ) -> None: ...


class TurnLifecycleMixin:
    session: ChatSession
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None

    def iter_events(
        self: _TurnLifecycleHost,
        user_input: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        prepared = self._prepare_turn(user_input)
        if prepared.guardrail_event is not None:
            yield prepared.guardrail_event
        if prepared.blocked:
            yield from _final_reply_events(self.last_reply)
            return

        self._record_user_turn(user_input)
        yield from self._iter_prepared_turn(prepared, user_input, abort=abort)

    def _prepare_turn(self: _TurnLifecycleHost, user_input: str) -> _PreparedTurn:
        self.last_reply = ""
        self.last_internal_passes = 1
        self._last_reply_citation_required = None
        decision = check_user_input(
            user_input,
            conversation=tuple(
                GuardrailMessage(role=message.role, content=message.content)
                for message in self.session.conversation.messages
            ),
        )
        guardrail_event = _guardrail_event(decision) if decision.blocks or decision.warns else None
        if decision.blocks:
            self.last_reply = decision.message
        return _PreparedTurn(
            original_messages=list(self.session.conversation.messages),
            original_learning_state=self.session.learning_state.clone(),
            guardrail_event=guardrail_event,
            blocked=decision.blocks,
        )

    def _record_user_turn(self: _TurnLifecycleHost, user_input: str) -> None:
        self.session.conversation.add("user", user_input)
        self.session.trace.record_user_message(user_input)
        _log.info(
            "user message",
            extra={
                "fields": {
                    "session_id": self.session.session_id,
                    "input_len": len(user_input),
                    "message_count": len(self.session.conversation.messages),
                    "learning_phase": self.session.learning_state.phase.value,
                }
            },
        )

    def _iter_prepared_turn(
        self: _TurnLifecycleHost,
        prepared: _PreparedTurn,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        timer = Timer()
        resolved = ResolvedTurnPlan()
        try:
            with timer:
                resolved = yield from self._iter_session_turn_events(
                    prepared.original_learning_state,
                    user_input,
                    abort=abort,
                )
            notice = self._finalize_successful_turn(user_input, resolved, latency_ms=timer.ms)
            if notice:
                yield from self._emit_verification_notice(notice)
        except StreamRecoveryError as error:
            self._handle_stream_recovery_error(prepared, user_input, timer, error)
            raise
        except EngineError as error:
            self._handle_engine_error(prepared, user_input, timer, error)
            raise
        except Exception:
            self._handle_unexpected_error(prepared, user_input, timer)
            raise

    def _iter_session_turn_events(
        self: _TurnLifecycleHost,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]:
        if self.session.armory_path is not None:
            return (
                yield from self._iter_armory_turn_events(
                    original_learning_state,
                    user_input,
                    abort=abort,
                )
            )
        self.session.last_turn_evidence = None
        yield from self._iter_plain_events(user_input=user_input, abort=abort)
        return ResolvedTurnPlan()

    def _emit_verification_notice(self, notice: str) -> Iterator[TurnEvent]:
        yield GuardrailEvent(
            stage=GUARDRAIL_STAGE_OUTPUT,
            action=GUARDRAIL_ACTION_WARN,
            message=notice,
            metadata={"code": "verification", "silent": True},
        )
        yield NoticeEvent(notice, code="verification")

    def _handle_stream_recovery_error(
        self: _TurnLifecycleHost,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
        error: StreamRecoveryError,
    ) -> None:
        _log.warning(
            "stream interrupted, rolling back",
            extra={
                "fields": {
                    "session_id": self.session.session_id,
                    "partial_len": len(error.partial_content),
                    "latency_ms": timer.ms,
                }
            },
        )
        self._record_turn_error(user_input, timer, str(error))
        self._rollback_turn(prepared.original_messages, prepared.original_learning_state)
        self.session.dirty = True

    def _handle_engine_error(
        self: _TurnLifecycleHost,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
        error: EngineError,
    ) -> None:
        _log.warning(
            "turn orchestration failed: %s",
            error,
            extra={"fields": {"session_id": self.session.session_id, "latency_ms": timer.ms}},
        )
        self._record_turn_error(user_input, timer, str(error))
        self._rollback_turn(prepared.original_messages, prepared.original_learning_state)

    def _handle_unexpected_error(
        self: _TurnLifecycleHost,
        prepared: _PreparedTurn,
        user_input: str,
        timer: Timer,
    ) -> None:
        _log.error(
            "turn orchestration failed",
            extra={"fields": {"session_id": self.session.session_id, "latency_ms": timer.ms}},
            exc_info=True,
        )
        self._record_turn_error(user_input, timer, "unexpected turn orchestration failure")
        self._rollback_turn(prepared.original_messages, prepared.original_learning_state)

    def _record_turn_error(
        self: _TurnLifecycleHost,
        user_input: str,
        timer: Timer,
        error: str,
    ) -> None:
        self.session.trace.record_session_event(
            "turn_error",
            original_user_input=user_input,
            error=error,
            latency_ms=round(timer.ms, 1),
        )


def _guardrail_event(decision) -> GuardrailEvent:
    return GuardrailEvent(
        stage=decision.stage,
        action=decision.action,
        message=decision.message,
        metadata=decision.metadata,
    )
