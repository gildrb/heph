"""Tool schema and result primitives for agent tools."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, NotRequired, Required, TypedDict


class ToolParameter(TypedDict, total=False):
    type: Required[str]
    description: NotRequired[str]


class ToolParameters(TypedDict):
    type: Literal["object"]
    properties: dict[str, ToolParameter]
    required: list[str]


class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: ToolParameters


class ToolSchema(TypedDict):
    type: Literal["function"]
    function: ToolFunction


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Structured result from a tool handler."""

    success: bool
    content: str
    metadata: dict[str, object] = field(default_factory=dict)
    error: str | None = None


ToolHandlerResult = str | ToolResult


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A single tool: its JSON schema and its handler function."""

    schema: ToolSchema
    handler: Callable[..., ToolHandlerResult]
    kind: Literal["normal", "control"] = "normal"

    @property
    def name(self) -> str:
        return self.schema["function"]["name"]
