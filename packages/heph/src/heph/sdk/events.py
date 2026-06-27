"""Stable SDK event DTOs for Heph turns."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from harness.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    GuardrailEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ReasoningDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    snapshot = dict(value)
    return MappingProxyType(snapshot)


@dataclass(frozen=True, slots=True)
class AssistantDelta:
    delta: str
    kind: Literal["assistant_delta"] = field(default="assistant_delta", init=False)

    def to_dict(self) -> dict[str, object]:
        return {"type": self.kind, "delta": self.delta}


@dataclass(frozen=True, slots=True)
class ReasoningDelta:
    delta: str
    summary: bool
    kind: Literal["reasoning_delta"] = field(default="reasoning_delta", init=False)

    def to_dict(self) -> dict[str, object]:
        return {"type": self.kind, "delta": self.delta, "summary": self.summary}


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    name: str
    arguments: Mapping[str, object]
    display: str
    kind: Literal["tool_call"] = field(default="tool_call", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _freeze_mapping(self.arguments))

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.kind,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": dict(self.arguments),
            "display": self.display,
        }


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    name: str
    content: str
    summary: str
    success: bool
    metadata: Mapping[str, object]
    error: str | None
    kind: Literal["tool_result"] = field(default="tool_result", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "call_id": self.call_id,
            "name": self.name,
            "content": self.content,
            "summary": self.summary,
            "success": self.success,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True, slots=True)
class MaterialOperation:
    operation: str
    message: str
    metadata: Mapping[str, object]
    kind: Literal["material_operation"] = field(default="material_operation", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "operation": self.operation,
            "message": self.message,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class CompactRequest:
    call_id: str
    name: str
    arguments: Mapping[str, object]
    kind: Literal["compact_request"] = field(default="compact_request", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _freeze_mapping(self.arguments))

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.kind,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": dict(self.arguments),
        }


@dataclass(frozen=True, slots=True)
class TurnComplete:
    full_text: str
    turn_index: int
    latency_ms: float
    finish_reason: str
    tokens_remaining: int
    kind: Literal["turn_complete"] = field(default="turn_complete", init=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.kind,
            "full_text": self.full_text,
            "turn_index": self.turn_index,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "tokens_remaining": self.tokens_remaining,
        }


@dataclass(frozen=True, slots=True)
class Notice:
    message: str
    code: str
    metadata: Mapping[str, object]
    kind: Literal["notice"] = field(default="notice", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "message": self.message,
            "code": self.code,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class Guardrail:
    stage: str
    action: str
    message: str
    metadata: Mapping[str, object]
    kind: Literal["guardrail"] = field(default="guardrail", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "stage": self.stage,
            "action": self.action,
            "message": self.message,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


HephEvent = (
    AssistantDelta
    | ReasoningDelta
    | ToolCall
    | ToolResult
    | MaterialOperation
    | CompactRequest
    | TurnComplete
    | Notice
    | Guardrail
)

type _EventConverter = Callable[[object], HephEvent]


@dataclass(frozen=True, slots=True)
class _EventConversionRule:
    source_type: type[object]
    converter: _EventConverter

    def convert_if_matching(self, event: TurnEvent) -> HephEvent | None:
        if not isinstance(event, self.source_type):
            return None
        return self.converter(event)


def from_turn_event(event: TurnEvent) -> HephEvent:
    """Convert the harness turn event into the public SDK DTO."""
    for rule in _EVENT_CONVERSION_RULES:
        converted = rule.convert_if_matching(event)
        if converted is not None:
            return converted
    raise TypeError(f"Unsupported turn event: {type(event).__name__}")


def event_to_dict(event: HephEvent) -> dict[str, object]:
    return event.to_dict()


def _expect_event[T](event: object, event_type: type[T]) -> T:
    if isinstance(event, event_type):
        return event
    raise TypeError(f"Expected {event_type.__name__}, got {type(event).__name__}.")


def _assistant_delta_from_event(event: object) -> AssistantDelta:
    source = _expect_event(event, AssistantDeltaEvent)
    return AssistantDelta(delta=source.delta)


def _reasoning_delta_from_event(event: object) -> ReasoningDelta:
    source = _expect_event(event, ReasoningDeltaEvent)
    return ReasoningDelta(delta=source.delta, summary=source.summary)


def _tool_call_from_event(event: object) -> ToolCall:
    source = _expect_event(event, ToolCallEvent)
    return ToolCall(
        call_id=source.call_id,
        name=source.name,
        arguments=source.arguments,
        display=source.display,
    )


def _tool_result_from_event(event: object) -> ToolResult:
    source = _expect_event(event, ToolResultEvent)
    return ToolResult(
        call_id=source.call_id,
        name=source.name,
        content=source.content,
        summary=source.summary,
        success=source.success,
        metadata=source.metadata,
        error=source.error,
    )


def _material_operation_from_event(event: object) -> MaterialOperation:
    source = _expect_event(event, MaterialOperationEvent)
    return MaterialOperation(
        operation=source.operation,
        message=source.message,
        metadata=source.metadata,
    )


def _compact_request_from_event(event: object) -> CompactRequest:
    source = _expect_event(event, CompactRequestEvent)
    return CompactRequest(
        call_id=source.call_id,
        name=source.name,
        arguments=source.arguments,
    )


def _turn_complete_from_event(event: object) -> TurnComplete:
    source = _expect_event(event, TurnCompleteEvent)
    return TurnComplete(
        full_text=source.full_text,
        turn_index=source.turn_index,
        latency_ms=source.latency_ms,
        finish_reason=source.finish_reason,
        tokens_remaining=source.tokens_remaining,
    )


def _notice_from_event(event: object) -> Notice:
    source = _expect_event(event, NoticeEvent)
    return Notice(message=source.message, code=source.code, metadata=source.metadata)


def _guardrail_from_event(event: object) -> Guardrail:
    source = _expect_event(event, GuardrailEvent)
    return Guardrail(
        stage=source.stage,
        action=source.action,
        message=source.message,
        metadata=source.metadata,
    )


_EVENT_CONVERSION_RULES = (
    _EventConversionRule(AssistantDeltaEvent, _assistant_delta_from_event),
    _EventConversionRule(ReasoningDeltaEvent, _reasoning_delta_from_event),
    _EventConversionRule(ToolCallEvent, _tool_call_from_event),
    _EventConversionRule(ToolResultEvent, _tool_result_from_event),
    _EventConversionRule(MaterialOperationEvent, _material_operation_from_event),
    _EventConversionRule(CompactRequestEvent, _compact_request_from_event),
    _EventConversionRule(TurnCompleteEvent, _turn_complete_from_event),
    _EventConversionRule(NoticeEvent, _notice_from_event),
    _EventConversionRule(GuardrailEvent, _guardrail_from_event),
)


__all__ = [
    "AssistantDelta",
    "CompactRequest",
    "Guardrail",
    "HephEvent",
    "MaterialOperation",
    "Notice",
    "ReasoningDelta",
    "ToolCall",
    "ToolResult",
    "TurnComplete",
    "event_to_dict",
    "from_turn_event",
]
