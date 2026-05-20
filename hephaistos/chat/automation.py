"""Non-interactive chat automation services.

This module is deliberately UI-agnostic: callers decide whether events become
plain text, JSONL, logs, or TUI widgets.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator

from hephaistos.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    MaterialOperationEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaistos.chat.orchestrator import TurnOrchestrator
from hephaistos.chat.session import ChatSession


def iter_chat_events(
    session: ChatSession,
    prompt: str,
    *,
    abort: threading.Event | None = None,
) -> Iterator[TurnEvent]:
    session.mark_activity()
    orchestrator = TurnOrchestrator(session)
    yield from orchestrator.iter_events(prompt, abort=abort)
    session.mark_activity()


def event_to_json_object(event: TurnEvent) -> dict[str, object]:
    if isinstance(event, AssistantDeltaEvent):
        return {"type": event.kind, "delta": event.delta}
    if isinstance(event, ToolCallEvent):
        return {
            "type": event.kind,
            "call_id": event.call_id,
            "name": event.name,
            "arguments": event.arguments,
            "display": event.display,
        }
    if isinstance(event, ToolResultEvent):
        return {
            "type": event.kind,
            "call_id": event.call_id,
            "name": event.name,
            "content": event.content,
            "summary": event.summary,
            "success": event.success,
            "metadata": event.metadata,
            "error": event.error,
        }
    if isinstance(event, MaterialOperationEvent):
        return {
            "type": event.kind,
            "operation": event.operation,
            "message": event.message,
            "metadata": event.metadata,
        }
    if isinstance(event, CompactRequestEvent):
        return {
            "type": event.kind,
            "call_id": event.call_id,
            "name": event.name,
            "arguments": event.arguments,
        }
    if isinstance(event, TurnCompleteEvent):
        return {
            "type": event.kind,
            "full_text": event.full_text,
            "turn_index": event.turn_index,
            "latency_ms": event.latency_ms,
            "finish_reason": event.finish_reason,
            "tokens_remaining": event.tokens_remaining,
        }
    payload: dict[str, object] = {
        "type": event.kind,
        "message": event.message,
        "code": event.code,
    }
    if event.metadata:
        payload["metadata"] = event.metadata
    return payload
