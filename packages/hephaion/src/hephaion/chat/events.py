"""Chat rendering helpers for shared turn events."""

from __future__ import annotations

import ai.runtime.events as _events

AssistantDeltaEvent = _events.AssistantDeltaEvent
CompactRequestEvent = _events.CompactRequestEvent
GuardrailEvent = _events.GuardrailEvent
MaterialOperationEvent = _events.MaterialOperationEvent
NoticeEvent = _events.NoticeEvent
ReasoningDeltaEvent = _events.ReasoningDeltaEvent
ToolCallEvent = _events.ToolCallEvent
ToolResultEvent = _events.ToolResultEvent
TurnCompleteEvent = _events.TurnCompleteEvent
TurnEvent = _events.TurnEvent
strip_decorative_symbols = _events.strip_decorative_symbols


def render_turn_event(event: TurnEvent) -> str:
    if isinstance(event, AssistantDeltaEvent):
        return event.delta
    if isinstance(event, ReasoningDeltaEvent):
        return ""
    if isinstance(event, NoticeEvent):
        return _render_notice(event)
    if isinstance(event, GuardrailEvent):
        return _render_guardrail_event(event)
    if isinstance(event, ToolCallEvent | ToolResultEvent | MaterialOperationEvent):
        return _render_display_event(event)
    if isinstance(event, CompactRequestEvent | TurnCompleteEvent):
        return ""
    return ""


def _render_notice(event: NoticeEvent) -> str:
    if event.code in {
        "model_request",
        "model_delta",
        "model_complete",
    }:
        return ""
    if event.code == "verification":
        return f"\n{event.message}\n"
    return f"\n[{event.message}]\n"


def _render_guardrail_event(event: GuardrailEvent) -> str:
    if event.metadata.get("silent") is True:
        return ""
    return f"\n[Guardrail {event.action}: {event.message}]\n"


def _render_display_event(
    event: ToolCallEvent | ToolResultEvent | MaterialOperationEvent,
) -> str:
    if isinstance(event, ToolCallEvent):
        return f"\n{event.display}\n"
    if isinstance(event, ToolResultEvent):
        return f"{event.summary}\n"
    return f"{event.message}\n"
