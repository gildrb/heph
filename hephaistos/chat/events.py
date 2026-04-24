"""Structured events emitted while processing a single chat turn."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AssistantDeltaEvent:
    """A streamed assistant text delta."""

    delta: str
    kind: str = field(default="assistant_delta", init=False)


@dataclass(frozen=True, slots=True)
class ToolCallEvent:
    """A tool call requested by the model."""

    call_id: str
    name: str
    arguments: dict[str, object]
    display: str
    kind: str = field(default="tool_call", init=False)


@dataclass(frozen=True, slots=True)
class ToolResultEvent:
    """The result of an executed tool call."""

    call_id: str
    name: str
    content: str
    summary: str
    success: bool = True
    metadata: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    kind: str = field(default="tool_result", init=False)


@dataclass(frozen=True, slots=True)
class CompactRequestEvent:
    """A model-requested conversation compaction control event."""

    call_id: str
    name: str
    arguments: dict[str, object]
    kind: str = field(default="compact_request", init=False)


@dataclass(frozen=True, slots=True)
class TurnCompleteEvent:
    """The final completion signal for an agent turn."""

    full_text: str
    turn_index: int
    latency_ms: float
    finish_reason: str
    tokens_remaining: int
    kind: str = field(default="turn_complete", init=False)


@dataclass(frozen=True, slots=True)
class NoticeEvent:
    """A non-token notice emitted during turn processing."""

    message: str
    code: str = "notice"
    kind: str = field(default="notice", init=False)


TurnEvent = (
    AssistantDeltaEvent
    | ToolCallEvent
    | ToolResultEvent
    | CompactRequestEvent
    | TurnCompleteEvent
    | NoticeEvent
)


def render_turn_event(event: TurnEvent) -> str:
    """Render a turn event for the legacy stdout-based UI."""
    if isinstance(event, AssistantDeltaEvent):
        return event.delta
    if isinstance(event, ToolCallEvent):
        return f"\n{event.display}\n"
    if isinstance(event, ToolResultEvent):
        return f"{event.summary}\n"
    if isinstance(event, CompactRequestEvent | TurnCompleteEvent):
        return ""
    if event.code == "verification":
        return f"\n{event.message}\n"
    return f"\n[{event.message}]\n"
