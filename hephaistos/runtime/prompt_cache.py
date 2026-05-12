"""Prompt-cache-aware request construction.

Provider-side prompt caches work best when stable instructions and corpus context
stay at the front of every request.  This module makes that split explicit while
preserving the exact message order sent to the model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, cast

from hephaistos.logging import get_logger
from hephaistos.runtime._api_types import ApiMessage

_log = get_logger("runtime.prompt_cache")


@dataclass(frozen=True, slots=True)
class PromptSegment:
    """One prompt-cache segment and its stable diagnostics."""

    name: Literal["stable_prefix", "dynamic_tail"]
    messages: tuple[ApiMessage, ...]
    fingerprint: str
    message_count: int
    char_count: int


@dataclass(frozen=True, slots=True)
class PromptCacheRequest:
    """A request split into cache-friendly stable prefix and dynamic tail."""

    stable_prefix: PromptSegment
    dynamic_tail: PromptSegment

    @property
    def messages(self) -> list[ApiMessage]:
        """Return the model request messages in their original order."""
        return [*self.stable_prefix.messages, *self.dynamic_tail.messages]

    @property
    def total_messages(self) -> int:
        return self.stable_prefix.message_count + self.dynamic_tail.message_count


class StablePrefixBuilder:
    """Build the provider-cacheable leading system-message prefix."""

    def build(self, messages: list[ApiMessage]) -> PromptSegment:
        prefix: list[ApiMessage] = []
        for message in messages:
            if message.get("role") != "system" or _is_conversation_summary(message):
                break
            prefix.append(_copy_message(message))
        return _segment("stable_prefix", prefix)

    def build_request(self, messages: list[ApiMessage]) -> PromptCacheRequest:
        stable = self.build(messages)
        dynamic = DynamicTailBuilder().build(messages, stable_prefix_messages=stable.message_count)
        return PromptCacheRequest(stable_prefix=stable, dynamic_tail=dynamic)


class DynamicTailBuilder:
    """Build the per-turn tail: user, assistant, tool, and summary messages."""

    def build(
        self,
        messages: list[ApiMessage],
        *,
        stable_prefix_messages: int,
    ) -> PromptSegment:
        return _segment(
            "dynamic_tail",
            [_copy_message(message) for message in messages[stable_prefix_messages:]],
        )


class MetricsLogger:
    """Log prompt-cache structure and usage without recording prompt text."""

    def record_request(self, request: PromptCacheRequest, *, model: str) -> None:
        _log.info(
            "prompt_cache_request",
            extra={"fields": _metrics_fields(request, model=model)},
        )

    def record_usage(
        self,
        request: PromptCacheRequest | None,
        *,
        model: str,
        cached_prompt_tokens: int | None,
    ) -> None:
        if request is None and cached_prompt_tokens is None:
            return
        fields: dict[str, object] = (
            _metrics_fields(request, model=model) if request is not None else {"model": model}
        )
        if cached_prompt_tokens is not None:
            fields["cached_prompt_tokens"] = cached_prompt_tokens
        _log.info("prompt_cache_usage", extra={"fields": fields})


def _copy_message(message: ApiMessage) -> ApiMessage:
    copied = dict(message)
    content = copied.get("content")
    if isinstance(content, list):
        copied["content"] = [dict(part) for part in content]
    tool_calls = copied.get("tool_calls")
    if isinstance(tool_calls, list):
        copied["tool_calls"] = [dict(call) for call in tool_calls]
    tool_metadata = copied.get("tool_metadata")
    if isinstance(tool_metadata, dict):
        copied["tool_metadata"] = dict(tool_metadata)
    return cast("ApiMessage", copied)


def _is_conversation_summary(message: ApiMessage) -> bool:
    content = message.get("content")
    if not isinstance(content, str):
        return False
    stripped = content.lstrip()
    return stripped.startswith(("[Conversation summary]", "[Earlier conversation summary]"))


def _segment(
    name: Literal["stable_prefix", "dynamic_tail"],
    messages: list[ApiMessage],
) -> PromptSegment:
    copied = tuple(_copy_message(message) for message in messages)
    return PromptSegment(
        name=name,
        messages=copied,
        fingerprint=_fingerprint(copied),
        message_count=len(copied),
        char_count=sum(_message_chars(message) for message in copied),
    )


def _fingerprint(messages: tuple[ApiMessage, ...]) -> str:
    encoded = json.dumps(
        list(messages),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _message_chars(message: ApiMessage) -> int:
    encoded = json.dumps(
        message,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return len(encoded)


def _metrics_fields(request: PromptCacheRequest, *, model: str) -> dict[str, object]:
    stable = request.stable_prefix
    dynamic = request.dynamic_tail
    return {
        "model": model,
        "stable_prefix_hash": stable.fingerprint,
        "stable_prefix_messages": stable.message_count,
        "stable_prefix_chars": stable.char_count,
        "dynamic_tail_hash": dynamic.fingerprint,
        "dynamic_tail_messages": dynamic.message_count,
        "dynamic_tail_chars": dynamic.char_count,
        "total_messages": request.total_messages,
    }
