"""Streaming completion delta types."""

from __future__ import annotations

from dataclasses import dataclass

from hephaion.runtime._api_types import ToolCallDelta, UsagePayload


@dataclass(frozen=True, slots=True)
class CompletionDelta:
    content: str | None = None
    tool_calls: list[ToolCallDelta] | None = None
    finish_reason: str = ""
    usage: UsagePayload | None = None
