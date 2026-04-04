"""Agent loop: the harness dispatch that runs between user and LLM.

Implements the core s01/s02 pattern from learn-claude-code:
- Send messages + tool definitions to LLM
- If tool_calls -> execute -> append results -> loop
- If text -> stream to caller -> done

The MODEL decides when to call tools and when to stop.
The CODE just executes what the model asks for.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path

from hephaistos.chat.engine import ChatConfig, Conversation, EngineError, _build_client
from hephaistos.harness.tools import TOOL_SCHEMAS, get_handler

_MAX_TURNS = 20
_MAX_RESULT_DISPLAY = 200


# ---------------------------------------------------------------------------
# Tool call execution
# ---------------------------------------------------------------------------


def execute_tool_calls(
    tool_calls: list[dict],
    workspace: Path,
) -> list[dict]:
    """Execute each tool call and return tool-result messages.

    Returns a list of messages with ``role: "tool"`` to append back.
    """
    results: list[dict] = []
    for tc in tool_calls:
        name = tc["function"]["name"]
        call_id = tc.get("id", "")
        try:
            arguments = json.loads(tc["function"]["arguments"])
        except json.JSONDecodeError:
            results.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": f"Error: invalid JSON arguments for {name}",
            })
            continue

        handler = get_handler(name)
        if handler is None:
            results.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": f"Unknown tool: {name}",
            })
            continue

        try:
            output = handler(workspace=workspace, **arguments)
        except Exception as exc:
            output = f"Tool error ({name}): {exc}"

        results.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": str(output),
        })

    return results


# ---------------------------------------------------------------------------
# Helpers for streaming collection
# ---------------------------------------------------------------------------


def _merge_tool_call_deltas(
    accumulated: list[dict],
    deltas: list[dict],
) -> None:
    """Merge streaming tool-call deltas into accumulated list in-place."""
    for delta in deltas:
        idx = delta.get("index", 0)
        # Extend the list if needed
        while len(accumulated) <= idx:
            accumulated.append({
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            })
        entry = accumulated[idx]
        if delta.get("id"):
            entry["id"] = delta["id"]
        fn = delta.get("function", {})
        if fn.get("name"):
            entry["function"]["name"] += fn["name"]
        if fn.get("arguments"):
            entry["function"]["arguments"] += fn["arguments"]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


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
    return f"  [{name}] {args}"


def _summarize_result(content: str) -> str:
    """Brief summary of tool result for display."""
    lines = content.splitlines()
    if len(content) <= _MAX_RESULT_DISPLAY:
        return f"  -> {content}"
    first_line = lines[0] if lines else content[:80]
    return f"  -> {first_line} ... ({len(lines)} lines)"


# ---------------------------------------------------------------------------
# Agent loop (streaming)
# ---------------------------------------------------------------------------


def agent_loop(
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    *,
    abort: threading.Event | None = None,
    max_turns: int = _MAX_TURNS,
) -> Iterator[str]:
    """Run the agent loop, yielding text chunks as they stream.

    Tool calls are executed automatically.  The caller sees interleaved
    text chunks and tool-activity annotations (prefixed with newlines).

    After iteration completes, *conversation* has been updated with all
    messages (user, assistant, tool calls, tool results).
    """
    api_messages = conversation.to_api_messages()

    for _ in range(max_turns):
        if abort is not None and abort.is_set():
            return

        client = _build_client(config)
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=api_messages,
                tools=TOOL_SCHEMAS,
                max_tokens=config.max_tokens,
                stream=True,
            )
        except Exception as exc:
            raise EngineError(f"LLM request failed: {exc}") from exc

        # Collect streamed response
        collected_text = ""
        collected_tool_calls: list[dict] = []
        finish_reason = ""

        for chunk in response:
            if abort is not None and abort.is_set():
                response.close()
                return

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta
            finish_reason = choice.finish_reason or finish_reason

            # Stream text content immediately
            if delta.content:
                collected_text += delta.content
                yield delta.content

            # Accumulate tool-call deltas
            if delta.tool_calls:
                _merge_tool_call_deltas(collected_tool_calls, delta.tool_calls)

        # --- No tool calls: we're done ---
        if not collected_tool_calls:
            # Append final assistant message to conversation
            conversation.add("assistant", collected_text)
            return

        # --- Tool calls: execute and continue ---
        # Build the assistant message with tool calls for history
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

        api_messages.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": tool_calls_api,
        })
        # Store a simplified version in our Conversation
        conversation.add(
            "assistant",
            collected_text or "[tool calls]",
        )

        # Display tool activity
        for tc in collected_tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            yield f"\n{_format_tool_args(name, args)}\n"

        # Execute
        tool_results = execute_tool_calls(collected_tool_calls, workspace)

        # Append results
        for tr in tool_results:
            api_messages.append(tr)
            summary = _summarize_result(tr.get("content", ""))
            yield f"{summary}\n"

    # Max turns reached
    yield "\n[Agent loop reached maximum turns]"
