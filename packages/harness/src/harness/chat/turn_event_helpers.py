"""Shared turn event helper constructors."""

from __future__ import annotations

from collections.abc import Iterator

from harness.chat.events import AssistantDeltaEvent, TurnCompleteEvent, TurnEvent


def _turn_complete_from_result(
    event: TurnCompleteEvent | None,
    final_reply: str,
) -> TurnCompleteEvent:
    if event is None:
        return TurnCompleteEvent(
            full_text=final_reply,
            turn_index=0,
            latency_ms=0.0,
            finish_reason="fallback",
            tokens_remaining=0,
        )
    return TurnCompleteEvent(
        full_text=final_reply,
        turn_index=event.turn_index,
        latency_ms=event.latency_ms,
        finish_reason=event.finish_reason,
        tokens_remaining=event.tokens_remaining,
    )


def _final_reply_events(
    final_reply: str,
    completion_event: TurnCompleteEvent | None = None,
) -> Iterator[TurnEvent]:
    if final_reply:
        yield AssistantDeltaEvent(final_reply)
    yield _turn_complete_from_result(completion_event, final_reply)
