"""Agent loop helpers for model/tool dispatch within an armory workspace."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path

from hephaistos.agent.compact import (
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
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

_log = get_logger("agent.dispatch")

_MAX_TURNS = 20
_ToolCallFunction = ToolCallFunction


def _content_to_text(content: str | None | list[ContentPart]) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return "".join(part.get("text", "") or part.get("content", "") for part in content)


class SteeringQueue:
    """Thread-safe queue for steering messages typed while the agent works."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: list[str] = []

    def enqueue(self, message: str) -> None:
        if not message.strip():
            return
        with self._lock:
            self._messages.append(message)
        _log.info(
            "steering message queued",
            extra={
                "fields": {
                    "queue_len": len(self._messages),
                    "message_len": len(message),
                }
            },
        )

    def drain(self) -> list[str]:
        with self._lock:
            msgs = self._messages[:]
            self._messages.clear()
        return msgs


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
    last_user = next((i for i in range(len(msgs) - 1, -1, -1) if msgs[i]["role"] == "user"), None)
    if last_user is None:
        return msgs + inserts
    for pos, insert in enumerate(inserts):
        msgs.insert(last_user + pos, insert)
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


def iter_agent_events(
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    *,
    abort: threading.Event | None = None,
    max_turns: int = _MAX_TURNS,
    retry: RetryConfig | None = None,
    usage: SessionUsage | None = None,
    steering: SteeringQueue | None = None,
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
        turn_timer = Timer()

        with turn_timer:
            schemas = registry.schemas if tool_schemas is None else tool_schemas
            for delta in stream_completion(
                config,
                llm_messages,
                tools=schemas or None,
                abort=abort,
                retry=retry,
                client_factory=build_client,
            ):
                if delta.content:
                    collected_parts.append(delta.content)
                    yield AssistantDeltaEvent(delta.content)
                if delta.tool_calls:
                    merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)
                if delta.finish_reason:
                    finish_reason = delta.finish_reason
                if delta.usage:
                    stream_usage = delta.usage

        collected_text = "".join(collected_parts)

        if not collected_tool_calls:
            _record_usage(usage, stream_usage, api_messages, collected_text, config.model)
            api_messages.append({"role": "assistant", "content": collected_text})
            conversation.add("assistant", collected_text)
            tokens_remaining = budget.tokens_remaining(api_messages)

            if steering is not None:
                for message in steering.drain():
                    api_messages.append({"role": "user", "content": message})
                    conversation.add("user", message)
                    yield NoticeEvent(f"Steering: {message[:100]}", code="steering")

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
            yield ToolCallEvent(
                call_id=tool_call.get("id", ""),
                name=name,
                arguments=arguments,
                display=format_tool_args(name, arguments),
            )
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

        if steering is not None:
            for message in steering.drain():
                api_messages.append({"role": "user", "content": message})
                conversation.add("user", message)
                yield NoticeEvent(f"Steering: {message[:100]}", code="steering")
                _log.info(
                    "steering message injected",
                    extra={
                        "fields": {
                            "message_len": len(message),
                            "turn": turn_idx,
                        }
                    },
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
    steering: SteeringQueue | None = None,
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
