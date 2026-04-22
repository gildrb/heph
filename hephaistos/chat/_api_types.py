from __future__ import annotations

from typing import NotRequired, Required, TypedDict


class ContentPart(TypedDict, total=False):
    type: Required[str]
    text: NotRequired[str]
    content: NotRequired[str]


class ToolCallFunction(TypedDict):
    name: str
    arguments: str


class ToolCallDelta(TypedDict, total=False):
    index: NotRequired[int]
    id: NotRequired[str]
    type: NotRequired[str]
    function: NotRequired[ToolCallFunction]


class UsagePayload(TypedDict, total=False):
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


class ApiMessage(TypedDict, total=False):
    role: Required[str]
    content: Required[str | None | list[ContentPart]]
    tool_calls: NotRequired[list[ToolCallDelta]]
    tool_call_id: NotRequired[str]
