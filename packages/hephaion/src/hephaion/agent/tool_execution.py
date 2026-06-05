"""Tool-call execution and streaming merge helpers for the agent loop."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from ai.logging import Timer, get_logger
from ai.runtime import ApiMessage, ToolCallDelta

from hephaion._types import is_string_mapping
from hephaion.agent.tool_schema import ToolHandlerResult
from hephaion.agent.tools import ToolRegistry, ToolResult, default_registry

_log = get_logger("hephaion.agent.tool_execution")

_MAX_RESULT_DISPLAY = 200
_MAX_TOOL_CALLS_PER_TURN = 5
_TOOL_DISPLAY_INDENT = "    "
_TOOL_DISPLAY_FIELDS = {
    "bash": ("Running", "command"),
    "read_file": ("Reading", "path"),
    "edit_file": ("Editing", "path"),
    "create_named_armory": ("Creating armory", "name"),
    "search_materials": ("Searching materials", "query"),
}
type _ToolArgFormatter = Callable[[dict[str, object]], str]


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


def _tool_message(call_id: str, result: ToolResult) -> ApiMessage:
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": result.content,
        "tool_success": result.success,
        "tool_metadata": result.metadata,
        "tool_error": result.error,
    }


def execute_tool_calls(
    tool_calls: list[ToolCall],
    workspace: Path,
    *,
    registry: ToolRegistry | None = None,
    max_calls: int = _MAX_TOOL_CALLS_PER_TURN,
    abort: threading.Event | None = None,
) -> list[ApiMessage]:
    if registry is None:
        registry = default_registry
    _warn_if_tool_call_limit_exceeded(len(tool_calls), max_calls)

    results: list[ApiMessage] = []
    for index, tool_call in enumerate(tool_calls):
        results.append(
            _execute_tool_call(
                tool_call,
                workspace,
                registry=registry,
                max_calls=max_calls,
                index=index,
                abort=abort,
            )
        )

    return results


def _warn_if_tool_call_limit_exceeded(requested: int, max_calls: int) -> None:
    if requested <= max_calls:
        return
    _log.warning(
        "tool call limit exceeded",
        extra={"fields": {"requested": requested, "max": max_calls}},
    )


def _execute_tool_call(
    tool_call: ToolCall,
    workspace: Path,
    *,
    registry: ToolRegistry,
    max_calls: int,
    index: int,
    abort: threading.Event | None,
) -> ApiMessage:
    call_id = tool_call.get("id", "")
    name = tool_call["function"]["name"]
    if index >= max_calls:
        return _tool_call_limit_message(call_id, name, max_calls)
    if registry.is_control_tool(name):
        return _control_tool_message(call_id, name)

    arguments = _parse_tool_call_arguments(tool_call, call_id, name)
    if arguments is None:
        return _invalid_json_message(call_id, name)

    arguments.pop("workspace", None)
    handler = registry.get_handler(name)
    if handler is None:
        return _unknown_tool_message(call_id, name)
    if abort is not None and abort.is_set():
        return _cancelled_tool_message(call_id, name)

    timer = Timer()
    result = _run_tool_handler(handler, name, workspace, arguments, timer, abort)
    _log_tool_result(name, arguments, result, timer.ms)
    return _timed_tool_message(call_id, name, result, timer.ms)


def _tool_call_limit_message(call_id: str, name: str, max_calls: int) -> ApiMessage:
    content = (
        f"Error: tool call limit reached ({max_calls} per turn). "
        f"Prioritize reading and writing documents. "
        f"Tool '{name}' was not executed."
    )
    return _tool_message(
        call_id,
        ToolResult(
            success=False,
            content=content,
            metadata={"max_calls": max_calls},
            error=content,
        ),
    )


def _control_tool_message(call_id: str, name: str) -> ApiMessage:
    return _tool_message(
        call_id,
        ToolResult(
            success=True,
            content=f"Control tool handled by agent: {name}",
            metadata={"control": True},
        ),
    )


def _parse_tool_call_arguments(
    tool_call: ToolCall,
    call_id: str,
    name: str,
) -> dict[str, object] | None:
    try:
        return parse_tool_arguments(tool_call["function"]["arguments"])
    except json.JSONDecodeError:
        _log.warning(
            "tool call invalid JSON",
            extra={"fields": {"tool": name, "call_id": call_id}},
        )
        return None


def _invalid_json_message(call_id: str, name: str) -> ApiMessage:
    content = f"Error: invalid JSON arguments for {name}"
    return _tool_message(call_id, ToolResult(False, content, error=content))


def _unknown_tool_message(call_id: str, name: str) -> ApiMessage:
    _log.warning(
        "unknown tool",
        extra={"fields": {"tool": name, "call_id": call_id}},
    )
    content = f"Unknown tool: {name}"
    return _tool_message(call_id, ToolResult(False, content, error=content))


def _cancelled_tool_message(call_id: str, name: str) -> ApiMessage:
    return _tool_message(
        call_id,
        ToolResult(
            success=False,
            content=f"Tool cancelled before execution: {name}",
            metadata={"tool": name},
            error="cancelled",
        ),
    )


def _run_tool_handler(
    handler: Callable[..., ToolHandlerResult],
    name: str,
    workspace: Path,
    arguments: dict[str, object],
    timer: Timer,
    abort: threading.Event | None,
) -> ToolResult:
    try:
        with timer:
            output = handler(workspace=workspace, abort=abort, **arguments)
    except Exception as exc:
        _log_tool_error(name, arguments, timer.ms, exc)
        return ToolResult(
            success=False,
            content=f"Tool error ({name}): {exc}",
            metadata={},
            error=str(exc),
        )
    return output if isinstance(output, ToolResult) else ToolResult(True, str(output))


def _log_tool_error(
    name: str,
    arguments: dict[str, object],
    latency_ms: float,
    exc: Exception,
) -> None:
    _log.error(
        "tool execution failed",
        extra={
            "fields": {
                "tool": name,
                "args": arguments,
                "latency_ms": latency_ms,
                "error": str(exc),
            }
        },
    )


def _log_tool_result(
    name: str,
    arguments: dict[str, object],
    result: ToolResult,
    latency_ms: float,
) -> None:
    _log.info(
        "tool executed",
        extra={
            "fields": {
                "tool": name,
                "args": _tool_args_summary(name, arguments),
                "latency_ms": round(latency_ms, 1),
                "result_len": len(result.content),
                "success": result.success,
            }
        },
    )


def _tool_args_summary(name: str, arguments: dict[str, object]) -> dict[str, object]:
    if name == "bash":
        return {"command": _string_arg(arguments, "command")[:200]}
    if name == "write_file":
        return {
            "path": _string_arg(arguments, "path"),
            "content_len": len(_string_arg(arguments, "content")),
        }
    return {
        key: (str(value)[:100] if isinstance(value, str) and len(value) > 100 else value)
        for key, value in arguments.items()
    }


def _timed_tool_message(
    call_id: str,
    name: str,
    result: ToolResult,
    latency_ms: float,
) -> ApiMessage:
    metadata = dict(result.metadata)
    metadata.setdefault("tool", name)
    metadata["latency_ms"] = round(latency_ms, 1)
    metadata["result_length"] = len(result.content)
    return _tool_message(
        call_id,
        ToolResult(result.success, result.content, metadata, result.error),
    )


def merge_tool_call_deltas(accumulated: list[ToolCall], deltas: list[ToolCallDelta]) -> None:
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


def format_tool_args(name: str, args: dict[str, object]) -> str:
    if name in _TOOL_DISPLAY_FIELDS:
        label, key = _TOOL_DISPLAY_FIELDS[name]
        return f"{_TOOL_DISPLAY_INDENT}{label}: {_string_arg(args, key)}"
    if formatter := _TOOL_ARG_FORMATTERS.get(name):
        return f"{_TOOL_DISPLAY_INDENT}{formatter(args)}"
    return f"{_TOOL_DISPLAY_INDENT}[{name}] {args}"


def _format_write_file_args(args: dict[str, object]) -> str:
    path = _string_arg(args, "path")
    size = len(_string_arg(args, "content"))
    return f"Writing: {path} ({size} chars)"


def _format_list_files_args(args: dict[str, object]) -> str:
    return f"Listing: {_string_arg(args, 'path') or '.'}"


def _format_open_material_args(args: dict[str, object]) -> str:
    source = _string_arg(args, "source")
    chunk = args.get("chunk")
    if isinstance(chunk, int):
        return f"Opening material: {source}#chunk={chunk}"
    return f"Opening material: {source}"


def _format_import_materials_args(args: dict[str, object]) -> str:
    source = _string_arg(args, "source_path")
    target = _string_arg(args, "target_armory")
    if target:
        return f"Importing: {source} -> {target}"
    return f"Importing: {source} -> current armory"


def _format_compact_args(_args: dict[str, object]) -> str:
    return "Compacting conversation"


_TOOL_ARG_FORMATTERS: dict[str, _ToolArgFormatter] = {
    "write_file": _format_write_file_args,
    "list_files": _format_list_files_args,
    "import_materials": _format_import_materials_args,
    "open_material": _format_open_material_args,
    "compact": _format_compact_args,
}


def summarize_result(content: str) -> str:
    lines = content.splitlines()
    if len(content) <= _MAX_RESULT_DISPLAY:
        return f"{_TOOL_DISPLAY_INDENT}-> {content}"
    first_line = lines[0] if lines else content[:80]
    return f"{_TOOL_DISPLAY_INDENT}-> {first_line} ... ({len(lines)} lines)"
