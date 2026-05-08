"""Agent harness: tool execution, dispatch loop, and prompt building."""

from __future__ import annotations

__all__ = [
    "SystemPrompt",
    "ToolCall",
    "ToolCallFunction",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "agent_loop",
    "build_system_prompt_sections",
    "default_registry",
    "execute_tool_calls",
    "format_tool_args",
    "merge_tool_call_deltas",
    "render_tool_docs",
    "summarize_result",
]


def __getattr__(name: str) -> object:
    """Load public agent helpers on demand to keep submodule imports cheap."""
    if name == "agent_loop":
        from hephaistos.agent.dispatch import agent_loop

        return agent_loop
    if name in {"SystemPrompt", "build_system_prompt_sections", "render_tool_docs"}:
        from hephaistos.agent.prompt import (
            SystemPrompt,
            build_system_prompt_sections,
            render_tool_docs,
        )

        return {
            "SystemPrompt": SystemPrompt,
            "build_system_prompt_sections": build_system_prompt_sections,
            "render_tool_docs": render_tool_docs,
        }[name]
    if name in {
        "ToolCall",
        "ToolCallFunction",
        "execute_tool_calls",
        "format_tool_args",
        "merge_tool_call_deltas",
        "summarize_result",
    }:
        from hephaistos.agent.tool_execution import (
            ToolCall,
            ToolCallFunction,
            execute_tool_calls,
            format_tool_args,
            merge_tool_call_deltas,
            summarize_result,
        )

        return {
            "ToolCall": ToolCall,
            "ToolCallFunction": ToolCallFunction,
            "execute_tool_calls": execute_tool_calls,
            "format_tool_args": format_tool_args,
            "merge_tool_call_deltas": merge_tool_call_deltas,
            "summarize_result": summarize_result,
        }[name]
    if name in {"ToolRegistry", "ToolResult", "ToolSpec", "default_registry"}:
        from hephaistos.agent.tools import (
            ToolRegistry,
            ToolResult,
            ToolSpec,
            default_registry,
        )

        return {
            "ToolRegistry": ToolRegistry,
            "ToolResult": ToolResult,
            "ToolSpec": ToolSpec,
            "default_registry": default_registry,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
