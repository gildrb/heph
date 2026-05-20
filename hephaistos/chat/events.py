"""Structured events emitted while processing a single chat turn."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AssistantDeltaEvent:
    delta: str
    kind: str = field(default="assistant_delta", init=False)


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


@dataclass(frozen=True, slots=True)
class NoticeEvent:
    message: str
    code: str = "notice"
    metadata: dict[str, object] = field(default_factory=dict)
    kind: str = field(default="notice", init=False)


TurnEvent = (
    AssistantDeltaEvent
    | ToolCallEvent
    | ToolResultEvent
    | MaterialOperationEvent
    | CompactRequestEvent
    | TurnCompleteEvent
    | NoticeEvent
)


def render_turn_event(event: TurnEvent) -> str:
    if isinstance(event, AssistantDeltaEvent):
        return event.delta
    if isinstance(event, ToolCallEvent):
        return f"\n{event.display}\n"
    if isinstance(event, ToolResultEvent):
        return f"{event.summary}\n"
    if isinstance(event, MaterialOperationEvent):
        return f"{event.message}\n"
    if isinstance(event, CompactRequestEvent | TurnCompleteEvent):
        return ""
    if event.code in {"model_request", "model_delta", "model_complete"}:
        return ""
    if event.code == "verification":
        return f"\n{event.message}\n"
    return f"\n[{event.message}]\n"
