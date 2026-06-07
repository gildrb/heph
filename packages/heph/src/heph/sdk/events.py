"""Stable SDK event DTOs for Heph turns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from hephaion.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    GuardrailEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)


@dataclass(frozen=True, slots=True)
class AssistantDelta:
    delta: str
    kind: Literal["assistant_delta"] = field(default="assistant_delta", init=False)

    def to_dict(self) -> dict[str, object]:
        return {"type": self.kind, "delta": self.delta}


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, object]
    display: str
    kind: Literal["tool_call"] = field(default="tool_call", init=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.kind,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": self.arguments,
            "display": self.display,
        }


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    name: str
    content: str
    summary: str
    success: bool
    metadata: dict[str, object]
    error: str | None
    kind: Literal["tool_result"] = field(default="tool_result", init=False)

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
            payload["metadata"] = self.metadata
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True, slots=True)
class MaterialOperation:
    operation: str
    message: str
    metadata: dict[str, object]
    kind: Literal["material_operation"] = field(default="material_operation", init=False)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "operation": self.operation,
            "message": self.message,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass(frozen=True, slots=True)
class CompactRequest:
    call_id: str
    name: str
    arguments: dict[str, object]
    kind: Literal["compact_request"] = field(default="compact_request", init=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.kind,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": self.arguments,
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
    metadata: dict[str, object]
    kind: Literal["notice"] = field(default="notice", init=False)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "message": self.message,
            "code": self.code,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass(frozen=True, slots=True)
class Guardrail:
    stage: str
    action: str
    message: str
    metadata: dict[str, object]
    kind: Literal["guardrail"] = field(default="guardrail", init=False)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.kind,
            "stage": self.stage,
            "action": self.action,
            "message": self.message,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


HephEvent = (
    AssistantDelta
    | ToolCall
    | ToolResult
    | MaterialOperation
    | CompactRequest
    | TurnComplete
    | Notice
    | Guardrail
)


def from_turn_event(event: TurnEvent) -> HephEvent:
    """Convert the harness turn event into the public SDK DTO."""
    if isinstance(event, AssistantDeltaEvent):
        return AssistantDelta(delta=event.delta)
    if isinstance(event, ToolCallEvent):
        return ToolCall(
            call_id=event.call_id,
            name=event.name,
            arguments=event.arguments,
            display=event.display,
        )
    if isinstance(event, ToolResultEvent):
        return ToolResult(
            call_id=event.call_id,
            name=event.name,
            content=event.content,
            summary=event.summary,
            success=event.success,
            metadata=event.metadata,
            error=event.error,
        )
    if isinstance(event, MaterialOperationEvent):
        return MaterialOperation(
            operation=event.operation,
            message=event.message,
            metadata=event.metadata,
        )
    if isinstance(event, CompactRequestEvent):
        return CompactRequest(
            call_id=event.call_id,
            name=event.name,
            arguments=event.arguments,
        )
    if isinstance(event, TurnCompleteEvent):
        return TurnComplete(
            full_text=event.full_text,
            turn_index=event.turn_index,
            latency_ms=event.latency_ms,
            finish_reason=event.finish_reason,
            tokens_remaining=event.tokens_remaining,
        )
    if isinstance(event, NoticeEvent):
        return Notice(message=event.message, code=event.code, metadata=event.metadata)
    if isinstance(event, GuardrailEvent):
        return Guardrail(
            stage=event.stage,
            action=event.action,
            message=event.message,
            metadata=event.metadata,
        )
    raise TypeError(f"Unsupported turn event: {type(event).__name__}")


def event_to_dict(event: HephEvent) -> dict[str, object]:
    return event.to_dict()


__all__ = [
    "AssistantDelta",
    "CompactRequest",
    "Guardrail",
    "HephEvent",
    "MaterialOperation",
    "Notice",
    "ToolCall",
    "ToolResult",
    "TurnComplete",
    "event_to_dict",
    "from_turn_event",
]
