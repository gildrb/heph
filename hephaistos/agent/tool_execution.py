"""Tool-call execution and streaming merge helpers for the agent loop."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import TypedDict

from hephaistos._types import is_string_mapping
from hephaistos.agent.tools import ToolRegistry, ToolResult, default_registry
from hephaistos.logging import Timer, get_logger
from hephaistos.runtime import ApiMessage, ToolCallDelta

_log = get_logger("agent.tool_execution")

_MAX_RESULT_DISPLAY = 200
_MAX_TOOL_CALLS_PER_TURN = 5
_TOOL_DISPLAY_INDENT = "    "


class ToolCallFunction(TypedDict):
    name: str
    arguments: str


class ToolCall(TypedDict):
    id: str
    type: str
    function: ToolCallFunction


def parse_tool_arguments(raw_arguments: str) -> dict[str, object]:
    parsed: object = json.loads(raw_arguments)
    if not is_string_mapping(parsed):
        return {}
    return parsed


def _normalise_tool_result(output: object) -> ToolResult:
    if isinstance(output, ToolResult):
        return output
    return ToolResult(success=True, content=str(output))


def execute_tool_calls(
    tool_calls: list[ToolCall],
    workspace: Path,
    *,
    registry: ToolRegistry | None = None,
    max_calls: int = _MAX_TOOL_CALLS_PER_TURN,
    abort: threading.Event | None = None,
) -> list[ApiMessage]:
    """Execute each tool call and return tool-result messages."""
    if registry is None:
        registry = default_registry
    if len(tool_calls) > max_calls:
        _log.warning(
            "tool call limit exceeded",
            extra={"fields": {"requested": len(tool_calls), "max": max_calls}},
        )

    results: list[ApiMessage] = []
    for i, tc in enumerate(tool_calls):
        call_id = tc.get("id", "")
        name = tc["function"]["name"]
        if i >= max_calls:
            content = (
                f"Error: tool call limit reached ({max_calls} per turn). "
                f"Prioritize reading and writing documents. "
                f"Tool '{name}' was not executed."
            )
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                    "tool_success": False,
                    "tool_metadata": {"max_calls": max_calls},
                    "tool_error": content,
                }
            )
            continue

        if registry.is_control_tool(name):
            content = f"Control tool handled by agent: {name}"
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                    "tool_success": True,
                    "tool_metadata": {"control": True},
                    "tool_error": None,
                }
            )
            continue

        try:
            arguments = parse_tool_arguments(tc["function"]["arguments"])
        except json.JSONDecodeError:
            _log.warning(
                "tool call invalid JSON",
                extra={"fields": {"tool": name, "call_id": call_id}},
            )
            content = f"Error: invalid JSON arguments for {name}"
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                    "tool_success": False,
                    "tool_metadata": {},
                    "tool_error": content,
                }
            )
            continue

        arguments.pop("workspace", None)
        handler = registry.get_handler(name)
        if handler is None:
            _log.warning(
                "unknown tool",
                extra={"fields": {"tool": name, "call_id": call_id}},
            )
            content = f"Unknown tool: {name}"
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                    "tool_success": False,
                    "tool_metadata": {},
                    "tool_error": content,
                }
            )
            continue

        if abort is not None and abort.is_set():
            result = ToolResult(
                success=False,
                content=f"Tool cancelled before execution: {name}",
                metadata={"tool": name},
                error="cancelled",
            )
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result.content,
                    "tool_success": result.success,
                    "tool_metadata": result.metadata,
                    "tool_error": result.error,
                }
            )
            continue

        timer = Timer()
        try:
            with timer:
                output = handler(workspace=workspace, abort=abort, **arguments)
                result = _normalise_tool_result(output)
        except Exception as exc:
            result = ToolResult(
                success=False,
                content=f"Tool error ({name}): {exc}",
                metadata={},
                error=str(exc),
            )
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
                    "result_len": len(result.content),
                    "success": result.success,
                }
            },
        )
        metadata = dict(result.metadata)
        metadata.setdefault("tool", name)
        metadata["latency_ms"] = round(timer.ms, 1)
        metadata["result_length"] = len(result.content)
        results.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": result.content,
                "tool_success": result.success,
                "tool_metadata": metadata,
                "tool_error": result.error,
            }
        )

    return results


def merge_tool_call_deltas(accumulated: list[ToolCall], deltas: list[ToolCallDelta]) -> None:
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
        raw_id = delta.get("id")
        if isinstance(raw_id, str) and raw_id:
            entry["id"] = raw_id
        raw_fn = delta.get("function")
        if raw_fn is None:
            continue
        raw_name = raw_fn.get("name", "")
        if raw_name:
            entry["function"]["name"] += raw_name
        raw_arguments = raw_fn.get("arguments", "")
        if raw_arguments:
            entry["function"]["arguments"] += raw_arguments


def _string_arg(args: dict[str, object], key: str) -> str:
    value = args.get(key, "")
    return value if isinstance(value, str) else ""


def _summarise_args(name: str, args: dict[str, object]) -> dict[str, object]:
    """Summarise tool args for logging, truncating large content."""
    if name == "bash":
        return {"command": _string_arg(args, "command")[:200]}
    if name == "write_file":
        return {
            "path": _string_arg(args, "path"),
            "content_len": len(_string_arg(args, "content")),
        }
    return {
        key: (str(value)[:100] if isinstance(value, str) and len(value) > 100 else value)
        for key, value in args.items()
    }


def format_tool_args(name: str, args: dict[str, object]) -> str:
    """Format tool call for display."""
    if name == "bash":
        return f"{_TOOL_DISPLAY_INDENT}Running: {_string_arg(args, 'command')}"
    if name == "read_file":
        return f"{_TOOL_DISPLAY_INDENT}Reading: {_string_arg(args, 'path')}"
    if name == "write_file":
        path = _string_arg(args, "path")
        size = len(_string_arg(args, "content"))
        return f"{_TOOL_DISPLAY_INDENT}Writing: {path} ({size} chars)"
    if name == "edit_file":
        return f"{_TOOL_DISPLAY_INDENT}Editing: {_string_arg(args, 'path')}"
    if name == "list_files":
        path = _string_arg(args, "path") or "."
        return f"{_TOOL_DISPLAY_INDENT}Listing: {path}"
    if name == "search_materials":
        query = _string_arg(args, "query")
        return f"{_TOOL_DISPLAY_INDENT}Searching materials: {query}"
    if name == "open_material":
        source = _string_arg(args, "source")
        chunk = args.get("chunk")
        if isinstance(chunk, int):
            return f"{_TOOL_DISPLAY_INDENT}Opening material: {source}#chunk={chunk}"
        return f"{_TOOL_DISPLAY_INDENT}Opening material: {source}"
    if name == "compact":
        return f"{_TOOL_DISPLAY_INDENT}Compacting conversation"
    return f"{_TOOL_DISPLAY_INDENT}[{name}] {args}"


def summarize_result(content: str) -> str:
    """Brief summary of tool result for display."""
    lines = content.splitlines()
    if len(content) <= _MAX_RESULT_DISPLAY:
        return f"{_TOOL_DISPLAY_INDENT}-> {content}"
    first_line = lines[0] if lines else content[:80]
    return f"{_TOOL_DISPLAY_INDENT}-> {first_line} ... ({len(lines)} lines)"
