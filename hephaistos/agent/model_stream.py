"""Model streaming helpers for the agent dispatch loop."""

from __future__ import annotations

import threading
import time
from collections.abc import Generator
from dataclasses import dataclass

from hephaistos.agent.runtime_notes import acceptance_criteria_notice
from hephaistos.agent.tool_execution import ToolCall, merge_tool_call_deltas
from hephaistos.agent.tools import ToolRegistry
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, TurnEvent
from hephaistos.logging import Timer
from hephaistos.rag.context import TurnEvidence
from hephaistos.runtime import (
    ApiMessage,
    ChatConfig,
    CompletionDelta,
    RetryConfig,
    UsagePayload,
    build_client,
    stream_completion,
)

_MODEL_STREAM_PROGRESS_SECONDS = 8.0


@dataclass(slots=True)
class ModelStreamState:
    model_name: str
    started_at: float
    last_progress_at: float
    content_delta_count: int = 0
    content_char_count: int = 0
    tool_delta_count: int = 0
    finish_reason: str = ""
    stream_usage: UsagePayload | None = None


@dataclass(slots=True)
class ModelTurnResult:
    text: str
    tool_calls: list[ToolCall]
    stream_state: ModelStreamState
    turn_timer: Timer


def _format_duration_ms(milliseconds: float) -> str:
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    return f"{milliseconds / 1000:.1f}s"


def _elapsed_ms(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000


def _model_delta_metadata(state: ModelStreamState) -> dict[str, object]:
    return {
        "model": state.model_name,
        "delta_count": state.content_delta_count,
        "character_count": state.content_char_count,
        "elapsed_ms": round(_elapsed_ms(state.started_at), 1),
    }


def _model_delta_notice(state: ModelStreamState) -> NoticeEvent | None:
    if state.content_delta_count == 1:
        return NoticeEvent(
            (
                f"Read first model delta from {state.model_name} "
                f"in {_format_duration_ms(_elapsed_ms(state.started_at))}."
            ),
            code="model_delta",
            metadata=_model_delta_metadata(state),
        )
    if time.perf_counter() - state.last_progress_at < _MODEL_STREAM_PROGRESS_SECONDS:
        return None
    return NoticeEvent(
        (
            f"Read {state.content_char_count} model character(s) from "
            f"{state.model_name} across {state.content_delta_count} delta(s) in "
            f"{_format_duration_ms(_elapsed_ms(state.started_at))}."
        ),
        code="model_delta",
        metadata=_model_delta_metadata(state),
    )


def _apply_model_delta(
    delta: CompletionDelta,
    state: ModelStreamState,
    collected_parts: list[str],
    collected_tool_calls: list[ToolCall],
) -> Generator[TurnEvent]:
    if delta.content:
        collected_parts.append(delta.content)
        state.content_delta_count += 1
        state.content_char_count += len(delta.content)
        notice = _model_delta_notice(state)
        if notice is not None:
            yield notice
            state.last_progress_at = time.perf_counter()
        yield AssistantDeltaEvent(delta.content)
    if delta.tool_calls:
        merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)
        state.tool_delta_count += len(delta.tool_calls)
    if delta.finish_reason:
        state.finish_reason = delta.finish_reason
    if delta.usage:
        state.stream_usage = delta.usage


def _model_complete_event(state: ModelStreamState, tool_call_count: int) -> NoticeEvent:
    return NoticeEvent(
        (
            f"Read complete model response from {state.model_name}: "
            f"{state.content_char_count} character(s), {tool_call_count} tool call(s) "
            f"in {_format_duration_ms(_elapsed_ms(state.started_at))}."
        ),
        code="model_complete",
        metadata={
            "model": state.model_name,
            "delta_count": state.content_delta_count,
            "character_count": state.content_char_count,
            "tool_delta_count": state.tool_delta_count,
            "tool_call_count": tool_call_count,
            "elapsed_ms": round(_elapsed_ms(state.started_at), 1),
            "finish_reason": state.finish_reason,
        },
    )


def _model_request_event(
    *,
    model_name: str,
    turn_idx: int,
    message_count: int,
    schema_count: int,
) -> NoticeEvent:
    return NoticeEvent(
        (
            f"Ran model request {model_name} "
            f"(turn {turn_idx + 1}, {message_count} message(s), "
            f"{schema_count} tool schema(s))."
        ),
        code="model_request",
        metadata={
            "model": model_name,
            "turn": turn_idx + 1,
            "message_count": message_count,
            "tool_schema_count": schema_count,
        },
    )


def run_model_turn(
    *,
    config: ChatConfig,
    retry: RetryConfig,
    abort: threading.Event | None,
    registry: ToolRegistry,
    tool_schemas: list[dict[str, object]] | None,
    llm_messages: list[ApiMessage],
    turn_idx: int,
    turn_evidence: TurnEvidence | None,
) -> Generator[TurnEvent, None, ModelTurnResult]:
    collected_parts: list[str] = []
    collected_tool_calls: list[ToolCall] = []
    turn_timer = Timer()

    with turn_timer:
        schemas = registry.schemas if tool_schemas is None else tool_schemas
        if config.provider_slug == "openai-codex":
            schemas = []
        require_verification_tool = turn_idx == 0 and bool(schemas) and not bool(turn_evidence)
        if require_verification_tool:
            yield acceptance_criteria_notice()
        model_name = config.model or "configured model"
        yield _model_request_event(
            model_name=model_name,
            turn_idx=turn_idx,
            message_count=len(llm_messages),
            schema_count=len(schemas or []),
        )
        stream_state = ModelStreamState(
            model_name=model_name,
            started_at=time.perf_counter(),
            last_progress_at=time.perf_counter(),
        )
        for delta in stream_completion(
            config,
            llm_messages,
            tools=schemas or None,
            abort=abort,
            retry=retry,
            client_factory=build_client,
            tool_choice="required" if require_verification_tool else None,
        ):
            yield from _apply_model_delta(
                delta,
                stream_state,
                collected_parts,
                collected_tool_calls,
            )

    yield _model_complete_event(stream_state, len(collected_tool_calls))
    return ModelTurnResult(
        text="".join(collected_parts),
        tool_calls=collected_tool_calls,
        stream_state=stream_state,
        turn_timer=turn_timer,
    )
