"""Agent loop: the harness dispatch that runs between user and LLM.

Implements the core tool-call loop:
- Send messages + tool definitions to LLM
- If tool_calls -> execute -> append results -> loop
- If text -> stream to caller -> done

The MODEL decides when to call tools and when to stop.
The CODE just executes what the model asks for.

Token usage is extracted from streaming responses and tracked via
:class:`~hephaistos.chat.usage.SessionUsage`.  The caller receives
interleaved text deltas and tool-activity annotations.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path

from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    StreamRecoveryError,
    _build_client,
    _wait_backoff,
    is_retryable_error,
)
from hephaistos.chat.usage import ContextBudget, SessionUsage, TokenUsage
from hephaistos.harness.compact import (
    TOKEN_THRESHOLD,
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from hephaistos.harness.tools import TOOL_SCHEMAS, get_handler
from hephaistos.logging import Timer, get_logger

_log = get_logger("harness.dispatch")

_MAX_TURNS = 20
_MAX_RESULT_DISPLAY = 200
_MAX_TOOL_CALLS_PER_TURN = 5  # strict limit: study agent doesn't need many


class SteeringQueue:
    """Thread-safe queue for steering messages typed while the agent works.

    The shell can enqueue messages while the agent loop is running.
    After each assistant turn finishes executing its tool calls, the loop
    checks for queued steering messages and injects them.

    This is cost-effective: the steering message just adds to the normal
    conversation — no extra API call is made. The next turn includes the
    queued message as part of its context.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: list[str] = []

    def enqueue(self, message: str) -> None:
        """Add a steering message to the queue."""
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
        """Remove and return all queued messages."""
        with self._lock:
            msgs = self._messages[:]
            self._messages.clear()
        return msgs

    @property
    def pending(self) -> int:
        with self._lock:
            return len(self._messages)


def execute_tool_calls(
    tool_calls: list[dict],
    workspace: Path,
    *,
    max_calls: int = _MAX_TOOL_CALLS_PER_TURN,
) -> list[dict]:
    """Execute each tool call and return tool-result messages.

    Enforces *max_calls* per turn.  Excess tool calls are rejected with
    an error message instead of being executed.

    Returns a list of messages with ``role: "tool"`` to append back.
    """
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

        handler = get_handler(name)
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
    """Rebuild *conversation* messages from the (possibly compacted) API messages."""
    conversation.messages.clear()
    for msg in api_messages:
        role = msg.get("role", "")
        content = msg.get("content")
        if role in ("system", "user", "assistant") and content:
            conversation.add(role, content)


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
) -> Iterator[str]:
    """Run the agent loop, yielding text chunks as they stream.

    Tool calls are executed automatically.  The caller sees interleaved
    text chunks and tool-activity annotations (prefixed with newlines).

    After iteration completes, *conversation* has been updated with all
    messages (user, assistant, tool calls, tool results).

    If *usage* is provided, token counts from API responses are recorded
    for cost tracking and budget management.

    Transient streaming failures are retried with exponential backoff.
    If a failure occurs after content has already been yielded, a
    :class:`StreamRecoveryError` is raised.
    """
    retry = retry or RetryConfig()
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

        # --- Layer 1: micro_compact (silent, every turn) ---
        micro_compact(api_messages)

        # --- Layer 2: auto_compact (token threshold) ---
        if estimate_messages_tokens(api_messages) > TOKEN_THRESHOLD:
            yield "\n[Auto-compacting conversation (context threshold reached)...]\n"
            api_messages[:] = auto_compact(api_messages, config, workspace)
            _sync_conversation(conversation, api_messages)

        turn_timer = Timer()
        last_api_error: Exception | None = None

        for api_attempt in range(retry.max_retries + 1):
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

            client = _build_client(config)
            try:
                with turn_timer:
                    response = client.chat.completions.create(
                        model=config.model,
                        messages=api_messages,  # type: ignore[arg-type]
                        tools=TOOL_SCHEMAS,  # type: ignore[arg-type]
                        max_tokens=config.max_tokens,
                        stream=True,
                    )
            except Exception as exc:
                last_api_error = exc
                _log.warning(
                    "agent_loop request failed (attempt %d/%d, turn %d)",
                    api_attempt + 1,
                    retry.max_retries + 1,
                    turn_idx,
                    extra={"fields": {"error": str(exc), "latency_ms": turn_timer.ms}},
                )
                if is_retryable_error(exc) and api_attempt < retry.max_retries:
                    if not _wait_backoff(api_attempt, retry, abort):
                        return
                    continue
                _log.error(
                    "agent_loop LLM request failed",
                    extra={
                        "fields": {
                            "model": config.model,
                            "turn": turn_idx,
                            "latency_ms": turn_timer.ms,
                            "error": str(exc),
                        }
                    },
                )
                raise EngineError(f"LLM request failed: {exc}") from exc
            collected_text = ""
            collected_tool_calls: list[dict] = []
            finish_reason = ""
            stream_usage: dict | None = None

            try:
                for chunk in response:
                    if abort is not None and abort.is_set():
                        response.close()
                        return
                    if not chunk.choices:
                        if hasattr(chunk, "usage") and chunk.usage:
                            stream_usage = {
                                "prompt_tokens": (getattr(chunk.usage, "prompt_tokens", 0) or 0),
                                "completion_tokens": (
                                    getattr(chunk.usage, "completion_tokens", 0) or 0
                                ),
                                "total_tokens": (getattr(chunk.usage, "total_tokens", 0) or 0),
                            }
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta
                    finish_reason = choice.finish_reason or finish_reason
                    if delta.content:
                        collected_text += delta.content
                        yield delta.content
                    if delta.tool_calls:
                        _merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)
                    if finish_reason and hasattr(chunk, "usage") and chunk.usage:
                        stream_usage = {
                            "prompt_tokens": (getattr(chunk.usage, "prompt_tokens", 0) or 0),
                            "completion_tokens": (
                                getattr(chunk.usage, "completion_tokens", 0) or 0
                            ),
                            "total_tokens": (getattr(chunk.usage, "total_tokens", 0) or 0),
                        }
            except Exception as exc:
                _log.error(
                    "agent_loop mid-stream failure (attempt %d/%d, turn %d, %d chars)",
                    api_attempt + 1,
                    retry.max_retries + 1,
                    turn_idx,
                    len(collected_text),
                    extra={"fields": {"error": str(exc), "latency_ms": turn_timer.ms}},
                )
                if collected_text:
                    raise StreamRecoveryError(collected_text, exc) from exc
                last_api_error = exc
                if is_retryable_error(exc) and api_attempt < retry.max_retries:
                    if not _wait_backoff(api_attempt, retry, abort):
                        return
                    continue
                raise EngineError(f"LLM stream failed: {exc}") from exc
            break
        else:
            raise EngineError(
                f"LLM request failed after {retry.max_retries + 1} attempts: {last_api_error}"
            ) from last_api_error

        # --- No tool calls: we're done ---
        if not collected_tool_calls:
            if usage is not None:
                if stream_usage:
                    usage.record(TokenUsage.from_api_response(stream_usage), config.model)
                else:
                    prompt_chars = sum(len(m.get("content", "") or "") for m in api_messages)
                    usage.estimate_from_chars(prompt_chars, len(collected_text), config.model)
            conversation.add("assistant", collected_text)
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

        # --- Tool calls: execute and continue ---
        assistant_content = collected_text or None
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
                "content": assistant_content,
                "tool_calls": tool_calls_api,
            }
        )
        conversation.add(
            "assistant",
            collected_text or "[tool calls]",
        )
        tool_names = []
        for tc in collected_tool_calls:
            name = tc["function"]["name"]
            tool_names.append(name)
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            yield f"\n{_format_tool_args(name, args)}\n"

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
        tool_results = execute_tool_calls(collected_tool_calls, workspace)
        if usage is not None:
            if stream_usage:
                usage.record(TokenUsage.from_api_response(stream_usage), config.model)
            else:
                prompt_chars = sum(len(m.get("content", "") or "") for m in api_messages)
                usage.estimate_from_chars(prompt_chars, len(collected_text), config.model)
        urgency = budget.compaction_urgency(api_messages)
        if urgency in ("medium", "high"):
            remaining = budget.tokens_remaining(api_messages)
            yield (
                f"\n[Warning: context window {remaining} tokens remaining"
                f" ({urgency} urgency). Consider /compact.]"
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
        for tr in tool_results:
            api_messages.append(tr)
            summary = _summarize_result(tr.get("content", ""))
            yield f"{summary}\n"

        # --- Steering: inject queued user messages after tool execution ---
        if steering is not None:
            queued = steering.drain()
            for msg in queued:
                api_messages.append({"role": "user", "content": msg})
                conversation.add("user", msg)
                yield f"\n[Steering: {msg[:100]}]\n"
                _log.info(
                    "steering message injected",
                    extra={
                        "fields": {
                            "message_len": len(msg),
                            "turn": turn_idx,
                        }
                    },
                )

        # --- Layer 3: manual compact tool ---
        if "compact" in tool_names:
            yield "\n[Compacting conversation...]\n"
            api_messages[:] = auto_compact(api_messages, config, workspace)
            _sync_conversation(conversation, api_messages)
            continue
    yield "\n[Agent loop reached maximum turns]"
    _log.warning(
        "agent loop max turns reached",
        extra={
            "fields": {
                "max_turns": max_turns,
                "model": config.model,
            }
        },
    )
