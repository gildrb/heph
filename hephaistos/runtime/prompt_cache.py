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
from hephaistos.runtime._api_types import ApiMessage, ContentPart

_log = get_logger("runtime.prompt_cache")


@dataclass(frozen=True, slots=True)
class PromptSegment:
    name: Literal["stable_prefix", "dynamic_tail"]
    messages: tuple[ApiMessage, ...]
    fingerprint: str
    message_count: int
    char_count: int


@dataclass(frozen=True, slots=True)
class PromptCacheRequest:
    stable_prefix: PromptSegment
    dynamic_tail: PromptSegment

    @property
    def messages(self) -> list[ApiMessage]:
        return [*self.stable_prefix.messages, *self.dynamic_tail.messages]

    @property
    def total_messages(self) -> int:
        return self.stable_prefix.message_count + self.dynamic_tail.message_count


class StablePrefixBuilder:
    def build(self, messages: list[ApiMessage]) -> PromptSegment:
        prefix: list[ApiMessage] = []
        for message in messages:
            content = message.get("content")
            is_summary = isinstance(content, str) and content.lstrip().startswith(
                ("[Conversation summary]", "[Earlier conversation summary]")
            )
            if message.get("role") != "system" or is_summary:
                break
            prefix.append(_copy_message(message))
        return _segment("stable_prefix", prefix)

    def build_request(self, messages: list[ApiMessage]) -> PromptCacheRequest:
        stable = self.build(messages)
        dynamic = _segment(
            "dynamic_tail",
            [_copy_message(message) for message in messages[stable.message_count :]],
        )
        return PromptCacheRequest(stable_prefix=stable, dynamic_tail=dynamic)


def annotate_anthropic_cache_breakpoints(
    request: PromptCacheRequest,
    model: str,
) -> PromptCacheRequest:
    slug = model.lower()
    if ("claude" not in slug and "anthropic" not in slug) or not request.stable_prefix.messages:
        return request
    messages = [_copy_message(message) for message in request.stable_prefix.messages]
    cached_message = messages[-1]
    content = cached_message.get("content")
    parts: list[ContentPart]
    if isinstance(content, str):
        parts = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        parts = [cast("ContentPart", dict(part)) for part in content]
    else:
        parts = [{"type": "text", "text": ""}]
    if not parts:
        parts.append({"type": "text", "text": ""})
    parts[-1]["cache_control"] = {"type": "ephemeral"}
    cached_message["content"] = parts
    messages[-1] = cached_message
    return PromptCacheRequest(
        stable_prefix=_segment("stable_prefix", messages),
        dynamic_tail=request.dynamic_tail,
    )


class MetricsLogger:
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


def _segment(
    name: Literal["stable_prefix", "dynamic_tail"],
    messages: list[ApiMessage],
) -> PromptSegment:
    copied = tuple(_copy_message(message) for message in messages)
    return PromptSegment(
        name=name,
        messages=copied,
        fingerprint=hashlib.sha256(_canonical_json(list(copied)).encode("utf-8")).hexdigest()[:16],
        message_count=len(copied),
        char_count=sum(len(_canonical_json(message)) for message in copied),
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
