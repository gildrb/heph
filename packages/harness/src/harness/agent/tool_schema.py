"""Tool schema and result primitives for agent tools."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, NotRequired, Required, TypedDict


class ToolParameter(TypedDict, total=False):
    type: Required[str]
    description: NotRequired[str]
    properties: NotRequired[dict[str, ToolParameter]]
    items: NotRequired[ToolParameter]
    required: NotRequired[list[str]]
    additionalProperties: NotRequired[bool]


class ToolParameters(TypedDict, total=False):
    type: Required[Literal["object"]]
    properties: Required[dict[str, ToolParameter]]
    required: Required[list[str]]
    additionalProperties: NotRequired[bool]


class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: ToolParameters


class ToolSchema(TypedDict):
    type: Literal["function"]
    function: ToolFunction


@dataclass(frozen=True, slots=True)
class ToolResult:
    success: bool
    content: str
    metadata: dict[str, object] = field(default_factory=dict)
    error: str | None = None


ToolHandlerResult = str | ToolResult


@dataclass(frozen=True, slots=True)
class ToolSpec:
    schema: ToolSchema
    handler: Callable[..., ToolHandlerResult]
    kind: Literal["normal", "control"] = "normal"
    prompt_guidelines: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return self.schema["function"]["name"]
