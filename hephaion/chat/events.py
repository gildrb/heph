"""Structured events emitted while processing a single chat turn."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_DECORATIVE_SYMBOL_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0000fe0f\U0000200d]"
)


def strip_decorative_symbols(text: str) -> str:
    """Remove emoji-style decorations from assistant-visible text."""
    return _DECORATIVE_SYMBOL_RE.sub("", text)


@dataclass(frozen=True, slots=True)
class AssistantDeltaEvent:
    delta: str
    kind: str = field(default="assistant_delta", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta", strip_decorative_symbols(self.delta))


@dataclass(frozen=True, slots=True)
class ToolCallEvent:
    call_id: str
    name: str
    arguments: dict[str, object]
    display: str
    kind: str = field(default="tool_call", init=False)


@dataclass(frozen=True, slots=True)
class ToolResultEvent:
    call_id: str
    name: str
    content: str
    summary: str
    success: bool = True
    metadata: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    kind: str = field(default="tool_result", init=False)


@dataclass(frozen=True, slots=True)
class MaterialOperationEvent:
    operation: str
    message: str
    metadata: dict[str, object] = field(default_factory=dict)
    kind: str = field(default="material_operation", init=False)


@dataclass(frozen=True, slots=True)
class CompactRequestEvent:
    call_id: str
    name: str
    arguments: dict[str, object]
    kind: str = field(default="compact_request", init=False)


@dataclass(frozen=True, slots=True)
class TurnCompleteEvent:
    full_text: str
    turn_index: int
    latency_ms: float
    finish_reason: str
    tokens_remaining: int
    kind: str = field(default="turn_complete", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "full_text", strip_decorative_symbols(self.full_text))


@dataclass(frozen=True, slots=True)
class NoticeEvent:
    message: str
    code: str = "notice"
    metadata: dict[str, object] = field(default_factory=dict)
    kind: str = field(default="notice", init=False)


@dataclass(frozen=True, slots=True)
class GuardrailEvent:
    stage: str
    action: str
    message: str
    metadata: dict[str, object] = field(default_factory=dict)
    kind: str = field(default="guardrail", init=False)


TurnEvent = (
    AssistantDeltaEvent
    | ToolCallEvent
    | ToolResultEvent
    | MaterialOperationEvent
    | CompactRequestEvent
    | TurnCompleteEvent
    | GuardrailEvent
    | NoticeEvent
)


def render_turn_event(event: TurnEvent) -> str:
    if isinstance(event, AssistantDeltaEvent):
        return event.delta
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
