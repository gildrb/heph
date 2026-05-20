"""Agent harness: tool execution, dispatch loop, and prompt building."""

from __future__ import annotations

from hephaistos.agent.dispatch import iter_agent_events
from hephaistos.agent.prompt import SystemPrompt, build_system_prompt_sections, render_tool_docs
from hephaistos.agent.tool_execution import (
    ToolCall,
    ToolCallFunction,
    execute_tool_calls,
    format_tool_args,
    merge_tool_call_deltas,
    summarize_result,
)
from hephaistos.agent.tools import ToolRegistry, ToolResult, ToolSpec, default_registry

__all__ = [
    "SystemPrompt",
    "ToolCall",
    "ToolCallFunction",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "build_system_prompt_sections",
    "default_registry",
    "execute_tool_calls",
    "format_tool_args",
    "iter_agent_events",
    "merge_tool_call_deltas",
    "render_tool_docs",
    "summarize_result",
]
