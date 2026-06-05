"""Provider request payload construction for runtime streaming."""

from __future__ import annotations

from collections.abc import Sequence

from ai.providers.api_profiles import reasoning_payload_for_config
from ai.providers.reasoning import (
    normalize_reasoning_level,
    reasoning_levels_for_model,
)
from ai.runtime._api_types import ApiMessage
from ai.runtime.config import ChatConfig
from ai.runtime.conversation import to_chat_completion_messages


def request_kwargs(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    *,
    tools: Sequence[object] | None,
    tool_choice: object | None,
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "model": config.model,
        "messages": to_chat_completion_messages(api_messages),
        "max_tokens": config.max_tokens,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = list(tools)
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    reasoning_payload, suppress_temperature = reasoning_payload_for_config(
        config, reasoning_levels_for_model(config.model, config.provider_slug or None)
    )
    if config.temperature is not None and not suppress_temperature:
        kwargs["temperature"] = config.temperature
    kwargs.update(reasoning_payload)
    return kwargs


def model_reasoning_effort(config: ChatConfig) -> str | None:
    levels = reasoning_levels_for_model(config.model, config.provider_slug or None)
    if not levels:
        return None
    normalized = normalize_reasoning_level(config.reasoning_level)
    return normalized if normalized in levels else levels[0]


__all__ = ["model_reasoning_effort", "request_kwargs"]
