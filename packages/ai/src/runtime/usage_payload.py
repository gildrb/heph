"""Usage payload extraction from provider stream chunks."""

from __future__ import annotations

from collections.abc import Iterator

from ai_types import is_string_mapping

from runtime._api_types import UsagePayload


def optional_int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None


def cached_tokens_from_usage_details(details: object) -> int | None:
    if is_string_mapping(details):
        return optional_int_value(details.get("cached_tokens"))
    return optional_int_value(getattr(details, "cached_tokens", None))


def cached_prompt_tokens_from_usage(usage: object) -> int | None:
    for details in usage_detail_sources(usage):
        cached_tokens = cached_tokens_from_usage_details(details)
        if cached_tokens is not None:
            return cached_tokens
    return None


def usage_detail_sources(usage: object) -> Iterator[object]:
    names = ("prompt_tokens_details", "input_tokens_details")
    for name in names:
        yield getattr(usage, name, None)
    if is_string_mapping(usage):
        for name in names:
            yield usage.get(name)


def extract_usage(chunk: object) -> UsagePayload | None:
    usage = getattr(chunk, "usage", None)
    if not usage:
        return None
    payload = base_usage_payload(usage)
    cached_prompt_tokens = cached_prompt_tokens_from_usage(usage)
    if cached_prompt_tokens is not None:
        payload["cached_prompt_tokens"] = cached_prompt_tokens
    return payload


def base_usage_payload(usage: object) -> UsagePayload:
    return {
        "prompt_tokens": (getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": (getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": (getattr(usage, "total_tokens", 0) or 0),
    }


__all__ = [
    "base_usage_payload",
    "cached_prompt_tokens_from_usage",
    "cached_tokens_from_usage_details",
    "extract_usage",
    "optional_int_value",
    "usage_detail_sources",
]
