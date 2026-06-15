"""Shared SDK configuration update helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from ai.providers.reasoning import normalize_reasoning_level
from ai.runtime import ChatConfig, normalize_thinking_visibility

from heph.sdk.runtime import HephSdkError
from heph.sdk.value_types import sdk_json_finite_float

type SdkConfigUpdateName = Literal[
    "base_url",
    "model",
    "max_tokens",
    "rag_context_budget",
    "temperature",
    "reasoning_level",
    "thinking_visibility",
    "feature_flags",
]
type SdkConfigUpdateValue = str | int | float | None | frozenset[str]
type _ConfigValueApplier = Callable[[ChatConfig, SdkConfigUpdateValue], None]


@dataclass(frozen=True, slots=True)
class SdkConfigUpdate:
    name: SdkConfigUpdateName
    value: SdkConfigUpdateValue


@dataclass(frozen=True, slots=True)
class _ConfigUpdateRule:
    apply: _ConfigValueApplier


def apply_sdk_config_updates(
    config: ChatConfig,
    updates: tuple[SdkConfigUpdate, ...],
) -> None:
    """Apply normalized SDK config updates to a mutable chat config."""
    for update in updates:
        rule = _CONFIG_UPDATE_RULES.get(update.name)
        if rule is None:
            raise HephSdkError(f"Unsupported SDK config field: {update.name}")
        rule.apply(config, update.value)


def sdk_config_update(
    name: SdkConfigUpdateName,
    value: SdkConfigUpdateValue | None,
) -> SdkConfigUpdate | None:
    if value is None:
        return None
    return SdkConfigUpdate(name, value)


def _require_string_update(name: str, value: SdkConfigUpdateValue) -> str:
    if not isinstance(value, str):
        raise HephSdkError(f"SDK config field '{name}' must be a string.")
    if "\0" not in value:
        return value
    raise HephSdkError(f"SDK config field '{name}' must not contain null bytes.")


def _require_feature_flag_string(value: object) -> str:
    if not isinstance(value, str):
        raise HephSdkError("SDK config field 'feature_flags' must be a set of strings.")
    if "\0" in value:
        raise HephSdkError("SDK config field 'feature_flags' must not contain null bytes.")
    return value


def _require_nonempty_string_update(name: str, value: SdkConfigUpdateValue) -> str:
    string = _require_string_update(name, value)
    if string.strip():
        return string
    raise HephSdkError(f"SDK config field '{name}' must be a non-empty string.")


def _require_integer_update(name: str, value: SdkConfigUpdateValue) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise HephSdkError(f"SDK config field '{name}' must be an integer.")


def _require_nonnegative_integer_update(name: str, value: SdkConfigUpdateValue) -> int:
    integer = _require_integer_update(name, value)
    if integer >= 0:
        return integer
    raise HephSdkError(f"SDK config field '{name}' must be non-negative.")


def _optional_temperature_update(value: SdkConfigUpdateValue) -> float | None:
    if value is None:
        return None
    temperature = sdk_json_finite_float(value)
    if temperature is not None:
        return min(2.0, max(0.0, temperature))
    raise HephSdkError("SDK config field 'temperature' must be a finite number or null.")


def _require_feature_flags_update(value: SdkConfigUpdateValue) -> frozenset[str]:
    if isinstance(value, frozenset):
        return frozenset(_require_feature_flag_string(item) for item in value)
    raise HephSdkError("SDK config field 'feature_flags' must be a set of strings.")


def _apply_base_url(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    base_url = _require_nonempty_string_update("base_url", value)
    config.base_url = base_url


def _apply_model(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    model = _require_nonempty_string_update("model", value)
    config.model = model


def _apply_max_tokens(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    max_tokens = _require_nonnegative_integer_update("max_tokens", value)
    config.max_tokens = max_tokens


def _apply_rag_context_budget(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    rag_context_budget = _require_nonnegative_integer_update("rag_context_budget", value)
    config.rag_context_budget = rag_context_budget


def _apply_temperature(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    temperature = _optional_temperature_update(value)
    config.temperature = temperature


def _apply_reasoning_level(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    reasoning_level = _require_string_update("reasoning_level", value)
    config.reasoning_level = normalize_reasoning_level(reasoning_level)


def _apply_thinking_visibility(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    thinking_visibility = _require_string_update("thinking_visibility", value)
    config.thinking_visibility = normalize_thinking_visibility(thinking_visibility)


def _apply_feature_flags(config: ChatConfig, value: SdkConfigUpdateValue) -> None:
    feature_flags = _require_feature_flags_update(value)
    config.feature_flags = feature_flags


_CONFIG_UPDATE_RULES: Mapping[SdkConfigUpdateName, _ConfigUpdateRule] = {
    "base_url": _ConfigUpdateRule(_apply_base_url),
    "model": _ConfigUpdateRule(_apply_model),
    "max_tokens": _ConfigUpdateRule(_apply_max_tokens),
    "rag_context_budget": _ConfigUpdateRule(_apply_rag_context_budget),
    "temperature": _ConfigUpdateRule(_apply_temperature),
    "reasoning_level": _ConfigUpdateRule(_apply_reasoning_level),
    "thinking_visibility": _ConfigUpdateRule(_apply_thinking_visibility),
    "feature_flags": _ConfigUpdateRule(_apply_feature_flags),
}


__all__ = [
    "SdkConfigUpdate",
    "SdkConfigUpdateName",
    "SdkConfigUpdateValue",
    "apply_sdk_config_updates",
    "sdk_config_update",
]
