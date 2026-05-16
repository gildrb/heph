"""Agent loop helpers for model/tool dispatch within an armory workspace."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from pathlib import Path

from hephaistos.agent.compact import (
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from hephaistos.agent.runtime_notes import (
    acceptance_criteria_notice,
    repeated_tool_call_notice,
    tool_call_fingerprint,
    tool_runtime_note,
)
from hephaistos.agent.steering import Steering
from hephaistos.agent.tool_execution import (
    ToolCall,
    ToolCallFunction,
    execute_tool_calls,
    format_tool_args,
    merge_tool_call_deltas,
    parse_tool_arguments,
    summarize_result,
)
from hephaistos.agent.tools import ToolRegistry, default_registry
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
    render_turn_event,
)
from hephaistos.chat.usage import ContextBudget, SessionUsage, TokenUsage
from hephaistos.logging import Timer, get_logger
from hephaistos.rag.context import TurnEvidence
from hephaistos.runtime import (
    ApiMessage,
    ChatConfig,
    ContentPart,
    Conversation,
    RetryConfig,
    ToolCallDelta,
    UsagePayload,
    build_client,
    stream_completion,
)
from hephaistos.runtime.prompt_cache import StablePrefixBuilder

_log = get_logger("agent.dispatch")

_MAX_TURNS = 20
_MODEL_STREAM_PROGRESS_SECONDS = 8.0
_ToolCallFunction = ToolCallFunction
SteeringQueue = Steering


def _content_to_text(content: str | None | list[ContentPart]) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return "".join(part.get("text", "") or part.get("content", "") for part in content)


_merge_tool_call_deltas = merge_tool_call_deltas
_format_tool_args = format_tool_args
_summarize_result = summarize_result


def _sync_conversation(conversation: Conversation, api_messages: list[ApiMessage]) -> None:
    """Rebuild *conversation* messages from the compacted API messages.

    ``Conversation`` only stores ``role`` + ``content``, so tool messages
    (``role="tool"``) and structured ``tool_calls`` fields cannot be
    represented.  The full ``api_messages`` list remains the authoritative
    source for the API; this mirror is used for persistence and title
    derivation.

    Assistant messages whose content is ``None`` (tool-call-only turns)
    are preserved with a ``"[tool calls]"`` placeholder so they are not
    silently dropped.
    """
    conversation.messages.clear()
    for msg in api_messages:
        role = msg["role"]
        content = _content_to_text(msg["content"])
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
    prompt_chars = sum(len(_content_to_text(message["content"])) for message in api_messages)
    usage.estimate_from_chars(prompt_chars, len(text), model)


def _format_duration_ms(milliseconds: float) -> str:
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    return f"{milliseconds / 1000:.1f}s"


def _elapsed_ms(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000


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
    tool_schemas: list[dict[str, object]] | None = None,
    registry: ToolRegistry | None = None,
    dry_run: bool = False,
) -> Iterator[TurnEvent]:
    """Run the model/tool loop and emit structured turn events."""
    retry = retry or RetryConfig()
    if registry is None:
        registry = default_registry
    api_messages = list(conversation.to_api_messages())
    loop_timer = Timer()
    budget = ContextBudget(model=config.model, max_tokens=config.max_tokens)
    tool_call_counts: dict[str, int] = {}

    _log.info(
        "agent_loop start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": len(api_messages),
                "max_turns": max_turns,
                "context_window": budget.context_window,
                "prompt_budget": budget.prompt_budget,
                "tokens_remaining": budget.tokens_remaining(api_messages),
            }
        },
    )

    if dry_run:
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
        return

    for turn_idx in range(max_turns):
        if abort is not None and abort.is_set():
            _log.info(
                "agent_loop aborted",
                extra={
                    "fields": {
                        "turn": turn_idx,
                        "latency_ms": loop_timer.ms,
                    }
                },
            )
            return

        micro_compact(api_messages)

        llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)
        compaction_threshold = int(budget.prompt_budget * 0.75)
        if estimate_messages_tokens(llm_messages) > compaction_threshold:
            yield NoticeEvent(
                "Auto-compacting conversation (context threshold reached)...",
                code="auto_compact",
            )
            api_messages[:] = auto_compact(api_messages, config, workspace)
            _sync_conversation(conversation, api_messages)
            llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)

        collected_parts: list[str] = []
        collected_tool_calls: list[ToolCall] = []
        finish_reason = ""
        stream_usage: UsagePayload | None = None
        tool_stream_disabled = config.provider_slug == "openai-codex"
        turn_timer = Timer()

        with turn_timer:
            schemas = registry.schemas if tool_schemas is None else tool_schemas
            if tool_stream_disabled:
                schemas = []
            require_verification_tool = turn_idx == 0 and bool(schemas) and not bool(turn_evidence)
            if require_verification_tool:
                criteria_notice = acceptance_criteria_notice()
                criteria_message: ApiMessage = {
                    "role": "system",
                    "content": criteria_notice.message,
                }
                llm_messages = [*llm_messages, criteria_message]
                yield criteria_notice
            model_name = config.model or "configured model"
            schema_count = len(schemas or [])
            yield NoticeEvent(
                (
                    f"Ran model request {model_name} "
                    f"(turn {turn_idx + 1}, {len(llm_messages)} message(s), "
                    f"{schema_count} tool schema(s))."
                ),
                code="model_request",
                metadata={
                    "model": model_name,
                    "turn": turn_idx + 1,
                    "message_count": len(llm_messages),
                    "tool_schema_count": schema_count,
                },
            )
            stream_started_at = time.perf_counter()
            last_progress_at = stream_started_at
            content_delta_count = 0
            content_char_count = 0
            tool_delta_count = 0
            for delta in stream_completion(
                config,
                llm_messages,
                tools=schemas or None,
                abort=abort,
                retry=retry,
                client_factory=build_client,
                tool_choice="required" if require_verification_tool else None,
            ):
                if delta.content:
                    collected_parts.append(delta.content)
                    content_delta_count += 1
                    content_char_count += len(delta.content)
                    now = time.perf_counter()
                    if content_delta_count == 1:
                        yield NoticeEvent(
                            (
                                f"Read first model delta from {model_name} "
                                f"in {_format_duration_ms(_elapsed_ms(stream_started_at))}."
                            ),
                            code="model_delta",
                            metadata={
                                "model": model_name,
                                "delta_count": content_delta_count,
                                "character_count": content_char_count,
                                "elapsed_ms": round(_elapsed_ms(stream_started_at), 1),
                            },
                        )
                        last_progress_at = now
                    elif now - last_progress_at >= _MODEL_STREAM_PROGRESS_SECONDS:
                        yield NoticeEvent(
                            (
                                f"Read {content_char_count} model character(s) from "
                                f"{model_name} across {content_delta_count} delta(s) in "
                                f"{_format_duration_ms(_elapsed_ms(stream_started_at))}."
                            ),
                            code="model_delta",
                            metadata={
                                "model": model_name,
                                "delta_count": content_delta_count,
                                "character_count": content_char_count,
                                "elapsed_ms": round(_elapsed_ms(stream_started_at), 1),
                            },
                        )
                        last_progress_at = now
                    yield AssistantDeltaEvent(delta.content)
                if delta.tool_calls:
                    merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)
                    tool_delta_count += len(delta.tool_calls)
                if delta.finish_reason:
                    finish_reason = delta.finish_reason
                if delta.usage:
                    stream_usage = delta.usage

        collected_text = "".join(collected_parts)
        yield NoticeEvent(
            (
                f"Read complete model response from {model_name}: "
                f"{content_char_count} character(s), {len(collected_tool_calls)} tool call(s) "
                f"in {_format_duration_ms(_elapsed_ms(stream_started_at))}."
            ),
            code="model_complete",
            metadata={
                "model": model_name,
                "delta_count": content_delta_count,
                "character_count": content_char_count,
                "tool_delta_count": tool_delta_count,
                "tool_call_count": len(collected_tool_calls),
                "elapsed_ms": round(_elapsed_ms(stream_started_at), 1),
                "finish_reason": finish_reason,
            },
        )

        if not collected_tool_calls:
            _record_usage(usage, stream_usage, api_messages, collected_text, config.model)
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
                        "finish_reason": finish_reason,
                        "tokens_remaining": tokens_remaining,
                    }
                },
            )
            yield TurnCompleteEvent(
                full_text=collected_text,
                turn_index=turn_idx,
                latency_ms=loop_timer.ms,
                finish_reason=finish_reason,
                tokens_remaining=tokens_remaining,
            )
            return

        tool_calls_api: list[ToolCallDelta] = [
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

        api_messages.append(
            {
                "role": "assistant",
                "content": collected_text or None,
                "tool_calls": tool_calls_api,
            }
        )
        conversation.add("assistant", collected_text or "[tool calls]")

        tool_names: list[str] = []
        for tool_call in collected_tool_calls:
            name = tool_call["function"]["name"]
            tool_names.append(name)
            try:
                arguments = parse_tool_arguments(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                arguments = {}
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

        _log.info(
            "agent_loop tool calls",
            extra={
                "fields": {
                    "turn": turn_idx,
                    "tools": tool_names,
                    "latency_ms": turn_timer.ms,
                }
            },
        )

        tool_results = execute_tool_calls(
            collected_tool_calls,
            workspace,
            registry=registry,
            abort=abort,
        )
        api_messages.extend(tool_results)

        _record_usage(usage, stream_usage, api_messages, collected_text, config.model)

        urgency = budget.compaction_urgency(api_messages)
        if urgency in ("medium", "high"):
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

        for tool_call, tool_result in zip(collected_tool_calls, tool_results, strict=False):
            name = tool_call["function"]["name"]
            content = _content_to_text(tool_result["content"])
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

        yield from _drain_steering_events(
            steering,
            api_messages,
            conversation,
            turn_idx=turn_idx,
        )

        if any(registry.is_control_tool(name) for name in tool_names):
            yield NoticeEvent("Compacting conversation...", code="manual_compact")
            api_messages[:] = auto_compact(api_messages, config, workspace)
            _sync_conversation(conversation, api_messages)
            continue

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


def agent_loop(
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
    tool_schemas: list[dict[str, object]] | None = None,
    registry: ToolRegistry | None = None,
    dry_run: bool = False,
) -> Iterator[str]:
    """Backward-compatible string stream wrapper over ``iter_agent_events``."""
    for event in iter_agent_events(
        config,
        conversation,
        workspace,
        abort=abort,
        max_turns=max_turns,
        retry=retry,
        usage=usage,
        steering=steering,
        turn_evidence=turn_evidence,
        extra_system_prompt=extra_system_prompt,
        tool_schemas=tool_schemas,
        registry=registry,
        dry_run=dry_run,
    ):
        yield render_turn_event(event)
