"""Agent loop helpers for model/tool dispatch within an armory workspace."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path

from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    RetryConfig,
    _build_client,
    stream_completion,
)
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnEvent,
    render_turn_event,
)
from hephaistos.chat.usage import ContextBudget, SessionUsage, TokenUsage
from hephaistos.harness.compact import (
    TOKEN_THRESHOLD,
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from hephaistos.harness.rag.context import TurnEvidence
from hephaistos.harness.tools import ToolRegistry, default_registry
from hephaistos.logging import Timer, get_logger

_log = get_logger("harness.dispatch")

_MAX_TURNS = 20
_MAX_RESULT_DISPLAY = 200
_MAX_TOOL_CALLS_PER_TURN = 5


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


def execute_tool_calls(
    tool_calls: list[dict],
    workspace: Path,
    *,
    registry: ToolRegistry | None = None,
    max_calls: int = _MAX_TOOL_CALLS_PER_TURN,
) -> list[dict]:
    """Execute each tool call and return tool-result messages."""
    if registry is None:
        registry = default_registry
    if len(tool_calls) > max_calls:
        _log.warning(
            "tool call limit exceeded",
            extra={
                "fields": {
                    "requested": len(tool_calls),
                    "max": max_calls,
                }
            },
        )

    results: list[dict] = []
    for i, tc in enumerate(tool_calls):
        call_id = tc.get("id", "")
        name = tc["function"]["name"]
        if i >= max_calls:
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": (
                        f"Error: tool call limit reached ({max_calls} per turn). "
                        f"Prioritize reading and writing documents. "
                        f"Tool '{name}' was not executed."
                    ),
                }
            )
            continue

        try:
            arguments = json.loads(tc["function"]["arguments"])
        except json.JSONDecodeError:
            _log.warning(
                "tool call invalid JSON",
                extra={
                    "fields": {
                        "tool": name,
                        "call_id": call_id,
                    }
                },
            )
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Error: invalid JSON arguments for {name}",
                }
            )
            continue

        arguments.pop("workspace", None)
        handler = registry.get_handler(name)
        if handler is None:
            _log.warning(
                "unknown tool",
                extra={
                    "fields": {
                        "tool": name,
                        "call_id": call_id,
                    }
                },
            )
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Unknown tool: {name}",
                }
            )
            continue

        timer = Timer()
        try:
            with timer:
                output = handler(workspace=workspace, **arguments)
        except Exception as exc:
            output = f"Tool error ({name}): {exc}"
            _log.error(
                "tool execution failed",
                extra={
                    "fields": {
                        "tool": name,
                        "args": arguments,
                        "latency_ms": timer.ms,
                        "error": str(exc),
                    }
                },
            )

        _log.info(
            "tool executed",
            extra={
                "fields": {
                    "tool": name,
                    "args": _summarise_args(name, arguments),
                    "latency_ms": round(timer.ms, 1),
                    "result_len": len(output),
                }
            },
        )
        results.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": str(output),
            }
        )

    return results


def _merge_tool_call_deltas(
    accumulated: list[dict],
    deltas: list[dict],
) -> None:
    """Merge streaming tool-call deltas into accumulated list in-place."""
    for delta in deltas:
        idx = delta.get("index", 0)
        while len(accumulated) <= idx:
            accumulated.append(
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }
            )
        entry = accumulated[idx]
        if delta.get("id"):
            entry["id"] = delta["id"]
        fn = delta.get("function", {})
        if fn.get("name"):
            entry["function"]["name"] += fn["name"]
        if fn.get("arguments"):
            entry["function"]["arguments"] += fn["arguments"]


def _summarise_args(name: str, args: dict) -> dict:
    """Summarise tool args for logging (truncate large content)."""
    if name == "bash":
        return {"command": args.get("command", "")[:200]}
    if name == "write_file":
        return {"path": args.get("path", ""), "content_len": len(args.get("content", ""))}
    return {
        k: (str(v)[:100] if isinstance(v, str) and len(v) > 100 else v) for k, v in args.items()
    }


def _format_tool_args(name: str, args: dict) -> str:
    """Format tool call for display."""
    if name == "bash":
        return f"  $ {args.get('command', '')}"
    if name == "read_file":
        return f"  [read] {args.get('path', '')}"
    if name == "write_file":
        path = args.get("path", "")
        size = len(args.get("content", ""))
        return f"  [write] {path} ({size} chars)"
    if name == "edit_file":
        return f"  [edit] {args.get('path', '')}"
    if name == "list_files":
        return f"  [list] {args.get('path', '.') or '.'}"
    if name == "compact":
        return "  [compact] compressing conversation"
    return f"  [{name}] {args}"


def _summarize_result(content: str) -> str:
    """Brief summary of tool result for display."""
    lines = content.splitlines()
    if len(content) <= _MAX_RESULT_DISPLAY:
        return f"  -> {content}"
    first_line = lines[0] if lines else content[:80]
    return f"  -> {first_line} ... ({len(lines)} lines)"


def _sync_conversation(conversation: Conversation, api_messages: list[dict]) -> None:
    """Rebuild *conversation* messages from the compacted API messages."""
    conversation.messages.clear()
    for msg in api_messages:
        role = msg.get("role", "")
        content = msg.get("content")
        if role in ("system", "user", "assistant") and content:
            conversation.add(role, content)


def _inject_turn_context(
    messages: list[dict],
    turn_evidence: TurnEvidence | None,
    extra_system_prompt: str | None,
) -> list[dict]:
    """Build a copy of *messages* with ephemeral turn context injected."""
    inserts: list[dict] = []
    if extra_system_prompt:
        inserts.append({"role": "system", "content": extra_system_prompt})
    if turn_evidence:
        rendered = turn_evidence.render()
        if rendered:
            inserts.append({"role": "system", "content": rendered})
    if not inserts:
        return messages
    msgs = list(messages)
    last_user = next(
        (i for i in range(len(msgs) - 1, -1, -1) if msgs[i].get("role") == "user"),
        None,
    )
    if last_user is None:
        return msgs + inserts
    for pos, insert in enumerate(inserts):
        msgs.insert(last_user + pos, insert)
    return msgs


def _record_usage(
    usage: SessionUsage | None,
    stream_usage: dict | None,
    api_messages: list[dict],
    text: str,
    model: str,
) -> None:
    if usage is None:
        return
    if stream_usage:
        usage.record(TokenUsage.from_api_response(stream_usage), model)
        return
    prompt_chars = sum(len(m.get("content", "") or "") for m in api_messages)
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
    tool_schemas: list[dict] | None = None,
    registry: ToolRegistry | None = None,
) -> Iterator[TurnEvent]:
    """Run the model/tool loop and emit structured turn events."""
    retry = retry or RetryConfig()
    if registry is None:
        registry = default_registry
    api_messages: list[dict] = conversation.to_api_messages()  # type: ignore[assignment]
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

        # Account for turn evidence and extra system prompt in budget checks
        # so injected context doesn't silently push past the context window.
        pre_inject_messages = api_messages
        llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)
        budget_messages = llm_messages

        if estimate_messages_tokens(budget_messages) > TOKEN_THRESHOLD:
            yield NoticeEvent(
                "Auto-compacting conversation (context threshold reached)...",
                code="auto_compact",
            )
            api_messages[:] = auto_compact(api_messages, config, workspace)
            _sync_conversation(conversation, api_messages)
            llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)

        collected_text = ""
        collected_tool_calls: list[dict] = []
        finish_reason = ""
        stream_usage: dict | None = None
        turn_timer = Timer()

        with turn_timer:
            schemas = registry.schemas if tool_schemas is None else tool_schemas
            for delta in stream_completion(
                config,
                llm_messages,  # type: ignore[arg-type]
                tools=schemas or None,
                abort=abort,
                retry=retry,
                client_factory=_build_client,
            ):
                if delta.content:
                    collected_text += delta.content
                    yield AssistantDeltaEvent(delta.content)
                if delta.tool_calls:
                    _merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)
                if delta.finish_reason:
                    finish_reason = delta.finish_reason
                if delta.usage:
                    stream_usage = delta.usage

        if not collected_tool_calls:
            _record_usage(usage, stream_usage, api_messages, collected_text, config.model)
            conversation.add("assistant", collected_text)

            # Drain steering messages even on text-only turns so they are
            # not stuck indefinitely in the queue.
            if steering is not None:
                queued = steering.drain()
                for msg in queued:
                    api_messages.append({"role": "user", "content": msg})
                    conversation.add("user", msg)
                    yield NoticeEvent(f"Steering: {msg[:100]}", code="steering")

            _log.info(
                "agent_loop complete",
                extra={
                    "fields": {
                        "model": config.model,
                        "turn": turn_idx,
                        "latency_ms": loop_timer.ms,
                        "text_len": len(collected_text),
                        "finish_reason": finish_reason,
                        "tokens_remaining": budget.tokens_remaining(api_messages),
                    }
                },
            )
            return

        tool_calls_api = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                },
            }
            for tc in collected_tool_calls
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
        for tc in collected_tool_calls:
            name = tc["function"]["name"]
            tool_names.append(name)
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            yield ToolCallEvent(
                call_id=tc.get("id", ""),
                name=name,
                arguments=args,
                display=_format_tool_args(name, args),
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

        tool_results = execute_tool_calls(collected_tool_calls, workspace, registry=registry)
        # Append tool results before recording usage so the char-based
        # estimation fallback counts prompt tokens accurately.
        for tc, tr in zip(collected_tool_calls, tool_results, strict=False):
            api_messages.append(tr)

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

        for tc, tr in zip(collected_tool_calls, tool_results, strict=False):
            name = tc["function"]["name"]
            content = tr.get("content", "")
            yield ToolResultEvent(
                call_id=tr.get("tool_call_id", ""),
                name=name,
                content=content,
                summary=_summarize_result(content),
            )

        if steering is not None:
            queued = steering.drain()
            for msg in queued:
                api_messages.append({"role": "user", "content": msg})
                conversation.add("user", msg)
                yield NoticeEvent(f"Steering: {msg[:100]}", code="steering")
                _log.info(
                    "steering message injected",
                    extra={
                        "fields": {
                            "message_len": len(msg),
                            "turn": turn_idx,
                        }
                    },
                )

        if "compact" in tool_names:
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
    tool_schemas: list[dict] | None = None,
    registry: ToolRegistry | None = None,
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
    ):
        yield render_turn_event(event)
