"""OpenAI tool-call delta normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.runtime._api_types import ToolCallDelta

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall


def normalize_tool_calls(tool_calls: list[ChoiceDeltaToolCall]) -> list[ToolCallDelta]:
    return [_normalize_tool_call(tool_call) for tool_call in tool_calls]


def _normalize_tool_call(tool_call: ChoiceDeltaToolCall) -> ToolCallDelta:
    result: ToolCallDelta = {"index": tool_call.index}
    _add_optional_tool_call_fields(result, tool_call)
    if tool_call.function is not None:
        result["function"] = {
            "name": tool_call.function.name or "",
            "arguments": tool_call.function.arguments or "",
        }
    return result


def _add_optional_tool_call_fields(
    result: ToolCallDelta,
    tool_call: ChoiceDeltaToolCall,
) -> None:
    if tool_call.id:
        result["id"] = tool_call.id
    if tool_call.type:
        result["type"] = str(tool_call.type)


__all__ = ["normalize_tool_calls"]
