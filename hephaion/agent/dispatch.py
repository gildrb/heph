"""Agent loop helpers for model/tool dispatch within an armory workspace."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion.agent.compact import (
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from hephaion.agent.model_stream import ModelStreamState, run_model_turn
from hephaion.agent.runtime_notes import (
    repeated_tool_call_notice,
    tool_call_fingerprint,
    tool_runtime_note,
)
from hephaion.agent.steering import Steering
from hephaion.agent.tool_execution import (
    ToolCall,
    execute_tool_calls,
    format_tool_args,
    parse_tool_arguments,
    summarize_result,
)
from hephaion.agent.tool_schema import ToolSchema
from hephaion.agent.tools import ToolRegistry, default_registry
from hephaion.logging import Timer, get_logger
from hephaion.rag.context import TurnEvidence
from hephaion.runtime import (
    ApiMessage,
    ChatConfig,
    Conversation,
    RetryConfig,
    ToolCallDelta,
    UsagePayload,
)
from hephaion.runtime.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    GuardrailEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaion.runtime.messages import api_content_text
from hephaion.runtime.prompt_cache import StablePrefixBuilder
from hephaion.runtime.usage import ContextBudget, SessionUsage, TokenUsage
from hephaion.safety import GuardrailDecision, GuardrailToolCall, check_tool_call_names

_log = get_logger("agent.dispatch")

_MAX_TURNS = 20
SteeringQueue = Steering


@dataclass(slots=True)
class AgentLoopState:
    api_messages: list[ApiMessage]
    loop_timer: Timer
    budget: ContextBudget
    tool_call_counts: dict[str, int]


def _sync_conversation(conversation: Conversation, api_messages: list[ApiMessage]) -> None:
    """Rebuild *conversation* messages from the compacted API messages.

    The full ``api_messages`` list stays authoritative for tool messages.
    Tool-call-only assistant turns are mirrored with ``"[tool calls]"``.
    """
    conversation.messages.clear()
    for msg in api_messages:
        role = msg["role"]
        content = api_content_text(msg["content"])
        if role == "assistant" and not content and msg.get("tool_calls"):
            content = "[tool calls]"
        if role in ("system", "user", "assistant") and content:
            conversation.add(role, content)


def _inject_turn_context(
    messages: list[ApiMessage],
    turn_evidence: TurnEvidence | None,
    extra_system_prompt: str | None,
) -> list[ApiMessage]:
    """Build a copy of *messages* with ephemeral turn context injected."""
    inserts: list[ApiMessage] = []
    if extra_system_prompt:
        inserts.append({"role": "system", "content": extra_system_prompt})
    if turn_evidence:
        rendered = turn_evidence.render()
        if rendered:
            inserts.append({"role": "system", "content": rendered})
    if not inserts:
        return messages
    msgs = list(messages)
    insert_at = StablePrefixBuilder().build(msgs).message_count
    for pos, insert in enumerate(inserts):
        msgs.insert(insert_at + pos, insert)
    return msgs


def _record_usage(
    usage: SessionUsage | None,
    stream_usage: UsagePayload | None,
    api_messages: list[ApiMessage],
    text: str,
    model: str,
) -> None:
    if usage is None:
        return
    if stream_usage:
        usage.record(TokenUsage.from_api_response(stream_usage), model)
        return
    prompt_chars = sum(len(api_content_text(message["content"])) for message in api_messages)
    usage.estimate_from_chars(prompt_chars, len(text), model)


def _drain_steering_events(
    steering: Steering | None,
    api_messages: list[ApiMessage],
    conversation: Conversation,
    *,
    turn_idx: int | None = None,
) -> Iterator[NoticeEvent]:
    if steering is None:
        return
    for message in steering.drain():
        api_messages.append({"role": "user", "content": message})
        conversation.add("user", message)
        yield NoticeEvent(f"Steering: {message[:100]}", code="steering")
        if turn_idx is not None:
            _log.info(
                "steering message injected",
                extra={"fields": {"message_len": len(message), "turn": turn_idx}},
            )


def _tool_call_events(
    collected_tool_calls: list[ToolCall],
    api_messages: list[ApiMessage],
    registry: ToolRegistry,
    tool_call_counts: dict[str, int],
) -> Iterator[TurnEvent]:
    for tool_call in collected_tool_calls:
        name = tool_call["function"]["name"]
        arguments = parse_tool_arguments(tool_call["function"]["arguments"])
        fingerprint = tool_call_fingerprint(name, arguments)
        tool_call_counts[fingerprint] = tool_call_counts.get(fingerprint, 0) + 1
        repeat_count = tool_call_counts[fingerprint]
        yield ToolCallEvent(
            call_id=tool_call.get("id", ""),
            name=name,
            arguments=arguments,
            display=format_tool_args(name, arguments),
        )
        if repeat_count > 1:
            repeat_note = repeated_tool_call_notice(name, arguments, repeat_count)
            api_messages.append({"role": "system", "content": repeat_note.message})
            yield repeat_note
        if registry.is_control_tool(name):
            yield CompactRequestEvent(
                call_id=tool_call.get("id", ""),
                name=name,
                arguments=arguments,
            )


def _tool_result_events(
    collected_tool_calls: list[ToolCall],
    tool_results: list[ApiMessage],
    api_messages: list[ApiMessage],
) -> Iterator[TurnEvent]:
    for tool_call, tool_result in zip(collected_tool_calls, tool_results, strict=False):
        name = tool_call["function"]["name"]
        content = api_content_text(tool_result["content"])
        yield ToolResultEvent(
            call_id=tool_result.get("tool_call_id", ""),
            name=name,
            content=content,
            summary=summarize_result(content),
            success=tool_result.get("tool_success", True),
            metadata=tool_result.get("tool_metadata", {}),
            error=tool_result.get("tool_error"),
        )
        runtime_note = tool_runtime_note(name, tool_result)
        if runtime_note is not None:
            api_messages.append({"role": "system", "content": runtime_note.message})
            yield runtime_note


def _dry_run_events(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    registry: ToolRegistry,
    budget: ContextBudget,
    loop_timer: Timer,
) -> Iterator[TurnEvent]:
    tokens_remaining = budget.tokens_remaining(api_messages)
    yield NoticeEvent(
        (
            "Dry run: skipped model streaming and tool execution "
            f"({len(registry.schemas)} tool schemas available)."
        ),
        code="dry_run",
    )
    yield TurnCompleteEvent(
        full_text="",
        turn_index=0,
        latency_ms=loop_timer.ms,
        finish_reason="dry_run",
        tokens_remaining=tokens_remaining,
    )
    _log.info(
        "agent_loop dry_run complete",
        extra={
            "fields": {
                "model": config.model,
                "message_count": len(api_messages),
                "tool_schema_count": len(registry.schemas),
                "tokens_remaining": tokens_remaining,
            }
        },
    )


def _context_warning_events(
    budget: ContextBudget,
    api_messages: list[ApiMessage],
    *,
    turn_idx: int,
) -> Iterator[NoticeEvent]:
    urgency = budget.compaction_urgency(api_messages)
    if urgency not in ("medium", "high"):
        return
    remaining = budget.tokens_remaining(api_messages)
    yield NoticeEvent(
        (
            f"Warning: context window {remaining} tokens remaining "
            f"({urgency} urgency). Consider /compact."
        ),
        code="context_warning",
    )
    _log.warning(
        "context budget low",
        extra={
            "fields": {
                "remaining": remaining,
                "urgency": urgency,
                "turn": turn_idx,
            }
        },
    )


def _final_response_events(
    *,
    config: ChatConfig,
    conversation: Conversation,
    api_messages: list[ApiMessage],
    collected_text: str,
    stream_state: ModelStreamState,
    budget: ContextBudget,
    loop_timer: Timer,
    turn_idx: int,
    usage: SessionUsage | None,
    steering: Steering | None,
) -> Iterator[TurnEvent]:
    _record_usage(usage, stream_state.stream_usage, api_messages, collected_text, config.model)
    api_messages.append({"role": "assistant", "content": collected_text})
    conversation.add("assistant", collected_text)
    tokens_remaining = budget.tokens_remaining(api_messages)
    yield from _drain_steering_events(steering, api_messages, conversation)
    _log.info(
        "agent_loop complete",
        extra={
            "fields": {
                "model": config.model,
                "turn": turn_idx,
                "latency_ms": loop_timer.ms,
                "text_len": len(collected_text),
                "finish_reason": stream_state.finish_reason,
                "tokens_remaining": tokens_remaining,
            }
        },
    )
    yield TurnCompleteEvent(
        full_text=collected_text,
        turn_index=turn_idx,
        latency_ms=loop_timer.ms,
        finish_reason=stream_state.finish_reason,
        tokens_remaining=tokens_remaining,
    )


def _api_tool_calls(collected_tool_calls: list[ToolCall]) -> list[ToolCallDelta]:
    return [
        {
            "id": tool_call["id"],
            "type": "function",
            "function": {
                "name": tool_call["function"]["name"],
                "arguments": tool_call["function"]["arguments"],
            },
        }
        for tool_call in collected_tool_calls
    ]


def _append_tool_call_message(
    conversation: Conversation,
    api_messages: list[ApiMessage],
    collected_text: str,
    collected_tool_calls: list[ToolCall],
) -> None:
    api_messages.append(
        {
            "role": "assistant",
            "content": collected_text or None,
            "tool_calls": _api_tool_calls(collected_tool_calls),
        }
    )
    conversation.add("assistant", collected_text or "[tool calls]")


def _prepare_llm_messages(
    *,
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    api_messages: list[ApiMessage],
    budget: ContextBudget,
    turn_evidence: TurnEvidence | None,
    extra_system_prompt: str | None,
) -> tuple[list[ApiMessage], NoticeEvent | None]:
    llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)
    compaction_threshold = int(budget.prompt_budget * 0.75)
    if estimate_messages_tokens(llm_messages) <= compaction_threshold:
        return llm_messages, None
    notice = NoticeEvent(
        "Auto-compacting conversation (context threshold reached)...",
        code="auto_compact",
    )
    api_messages[:] = auto_compact(api_messages, config, workspace)
    _sync_conversation(conversation, api_messages)
    return _inject_turn_context(api_messages, turn_evidence, extra_system_prompt), notice


def _new_loop_state(config: ChatConfig, conversation: Conversation) -> AgentLoopState:
    api_messages = list(conversation.to_api_messages())
    return AgentLoopState(
        api_messages=api_messages,
        loop_timer=Timer(),
        budget=ContextBudget(model=config.model, max_tokens=config.max_tokens),
        tool_call_counts={},
    )


def _restricted_tool_registry(
    registry: ToolRegistry,
    allowed_names: Sequence[str] | None,
) -> ToolRegistry:
    if allowed_names is None:
        return registry
    allowed = frozenset(allowed_names)
    restricted = ToolRegistry()
    for spec in registry.specs:
        if spec.name in allowed:
            restricted.register(spec)
    return restricted


def _log_agent_loop_start(config: ChatConfig, state: AgentLoopState, max_turns: int) -> None:
    _log.info(
        "agent_loop start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": len(state.api_messages),
                "max_turns": max_turns,
                "context_window": state.budget.context_window,
                "prompt_budget": state.budget.prompt_budget,
                "tokens_remaining": state.budget.tokens_remaining(state.api_messages),
            }
        },
    )


def _abort_requested(
    abort: threading.Event | None,
    *,
    turn_idx: int,
    loop_timer: Timer,
) -> bool:
    if abort is None or not abort.is_set():
        return False
    _log.info(
        "agent_loop aborted",
        extra={
            "fields": {
                "turn": turn_idx,
                "latency_ms": loop_timer.ms,
            }
        },
    )
    return True


def _guardrail_tool_calls(tool_calls: list[ToolCall]) -> tuple[GuardrailToolCall, ...]:
    return tuple(
        GuardrailToolCall(
            call_id=tool_call.get("id", ""),
            name=tool_call["function"]["name"],
            arguments=tool_call["function"]["arguments"],
        )
        for tool_call in tool_calls
    )


def _blocked_tool_call_events(
    *,
    decision: GuardrailDecision,
    conversation: Conversation,
    state: AgentLoopState,
    usage: SessionUsage | None,
    model_stream_state: ModelStreamState,
    model_result_text: str,
    config: ChatConfig,
    turn_idx: int,
) -> Iterator[TurnEvent]:
    _record_usage(
        usage, model_stream_state.stream_usage, state.api_messages, model_result_text, config.model
    )
    yield GuardrailEvent(
        stage=decision.stage,
        action=decision.action,
        message=decision.message,
        metadata=decision.metadata,
    )
    state.api_messages.append({"role": "assistant", "content": decision.message})
    conversation.add("assistant", decision.message)
    yield AssistantDeltaEvent(decision.message)
    yield TurnCompleteEvent(
        full_text=decision.message,
        turn_index=turn_idx,
        latency_ms=state.loop_timer.ms,
        finish_reason="guardrail",
        tokens_remaining=state.budget.tokens_remaining(state.api_messages),
    )


def _tool_turn_events(
    *,
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    registry: ToolRegistry,
    abort: threading.Event | None,
    usage: SessionUsage | None,
    steering: Steering | None,
    state: AgentLoopState,
    model_result_text: str,
    model_result_tool_calls: list[ToolCall],
    model_stream_state: ModelStreamState,
    model_turn_timer: Timer,
    turn_idx: int,
) -> Generator[TurnEvent, None, bool]:
    tool_decision = check_tool_call_names(
        _guardrail_tool_calls(model_result_tool_calls),
        allowed_tool_names=frozenset(registry.tool_names),
    )
    if tool_decision.blocks:
        yield from _blocked_tool_call_events(
            decision=tool_decision,
            conversation=conversation,
            state=state,
            usage=usage,
            model_stream_state=model_stream_state,
            model_result_text=model_result_text,
            config=config,
            turn_idx=turn_idx,
        )
        return True
    if tool_decision.warns:
        yield GuardrailEvent(
            stage=tool_decision.stage,
            action=tool_decision.action,
            message=tool_decision.message,
            metadata=tool_decision.metadata,
        )

    _append_tool_call_message(
        conversation,
        state.api_messages,
        model_result_text,
        model_result_tool_calls,
    )

    tool_names = [tool_call["function"]["name"] for tool_call in model_result_tool_calls]
    yield from _tool_call_events(
        model_result_tool_calls,
        state.api_messages,
        registry,
        state.tool_call_counts,
    )

    _log.info(
        "agent_loop tool calls",
        extra={
            "fields": {
                "turn": turn_idx,
                "tools": tool_names,
                "latency_ms": model_turn_timer.ms,
            }
        },
    )

    tool_results = execute_tool_calls(
        model_result_tool_calls,
        workspace,
        registry=registry,
        abort=abort,
    )
    state.api_messages.extend(tool_results)

    _record_usage(
        usage,
        model_stream_state.stream_usage,
        state.api_messages,
        model_result_text,
        config.model,
    )

    yield from _context_warning_events(state.budget, state.api_messages, turn_idx=turn_idx)
    yield from _tool_result_events(model_result_tool_calls, tool_results, state.api_messages)
    yield from _drain_steering_events(
        steering,
        state.api_messages,
        conversation,
        turn_idx=turn_idx,
    )

    if any(registry.is_control_tool(name) for name in tool_names):
        yield NoticeEvent("Compacting conversation...", code="context_compact")
        state.api_messages[:] = auto_compact(state.api_messages, config, workspace)
        _sync_conversation(conversation, state.api_messages)
    return False


def iter_agent_events(
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    *,
    abort: threading.Event | None = None,
    max_turns: int = _MAX_TURNS,
    retry: RetryConfig | None = None,
    usage: SessionUsage | None = None,
    steering: Steering | None = None,
    turn_evidence: TurnEvidence | None = None,
    extra_system_prompt: str | None = None,
    tool_schemas: list[ToolSchema] | None = None,
    allowed_tool_names: Sequence[str] | None = None,
    registry: ToolRegistry | None = None,
    dry_run: bool = False,
) -> Iterator[TurnEvent]:
    """Run the model/tool loop and emit structured turn events."""
    retry = retry or RetryConfig()
    if registry is None:
        registry = default_registry
    registry = _restricted_tool_registry(registry, allowed_tool_names)
    if allowed_tool_names is not None and tool_schemas is None:
        tool_schemas = registry.schemas
    state = _new_loop_state(config, conversation)
    _log_agent_loop_start(config, state, max_turns)

    if dry_run:
        yield from _dry_run_events(
            config,
            state.api_messages,
            registry,
            state.budget,
            state.loop_timer,
        )
        return

    for turn_idx in range(max_turns):
        if _abort_requested(abort, turn_idx=turn_idx, loop_timer=state.loop_timer):
            return

        micro_compact(state.api_messages)

        llm_messages, compaction_notice = _prepare_llm_messages(
            config=config,
            conversation=conversation,
            workspace=workspace,
            api_messages=state.api_messages,
            budget=state.budget,
            turn_evidence=turn_evidence,
            extra_system_prompt=extra_system_prompt,
        )
        if compaction_notice is not None:
            yield compaction_notice

        model_result = yield from run_model_turn(
            config=config,
            retry=retry,
            abort=abort,
            registry=registry,
            tool_schemas=tool_schemas,
            llm_messages=llm_messages,
            turn_idx=turn_idx,
            turn_evidence=turn_evidence,
        )

        if not model_result.tool_calls:
            yield from _final_response_events(
                config=config,
                conversation=conversation,
                api_messages=state.api_messages,
                collected_text=model_result.text,
                stream_state=model_result.stream_state,
                budget=state.budget,
                loop_timer=state.loop_timer,
                turn_idx=turn_idx,
                usage=usage,
                steering=steering,
            )
            return

        turn_completed = yield from _tool_turn_events(
            config=config,
            conversation=conversation,
            workspace=workspace,
            registry=registry,
            abort=abort,
            usage=usage,
            steering=steering,
            state=state,
            model_result_text=model_result.text,
            model_result_tool_calls=model_result.tool_calls,
            model_stream_state=model_result.stream_state,
            model_turn_timer=model_result.turn_timer,
            turn_idx=turn_idx,
        )
        if turn_completed:
            return

    yield NoticeEvent("Agent loop reached maximum turns", code="max_turns")
    _log.warning(
        "agent loop max turns reached",
        extra={
            "fields": {
                "max_turns": max_turns,
                "model": config.model,
            }
        },
    )
