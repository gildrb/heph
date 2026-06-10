"""Provider-specific request profiles for OpenAI-compatible API surfaces."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Protocol

from ai.providers.llama_cpp import LLAMA_CPP_PROVIDER_SLUG

ReasoningPayload = Literal["openai", "deepseek", "openrouter", "none"]

_REASONING_ORDER = ("low", "medium", "high", "xhigh")
_OPENAI_ENDPOINT = "https://api.openai.com/v1"
_DEEPSEEK_ENDPOINTS = ("https://api.deepseek.com", "https://api.deepseek.com/v1")
_OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"


class ProviderProfileConfig(Protocol):
    provider_slug: str
    base_url: str
    model: str


class ReasoningPayloadConfig(ProviderProfileConfig, Protocol):
    reasoning_level: str


@dataclass(frozen=True, slots=True)
class ProviderRequestProfile:
    name: str
    reasoning_payload: ReasoningPayload
    suppress_temperature_when_reasoning: bool = False


_GENERIC_OPENAI_COMPATIBLE_PROFILE = ProviderRequestProfile(
    name="openai-compatible",
    reasoning_payload="openai",
)
_DEEPSEEK_PROFILE = ProviderRequestProfile(
    name="deepseek",
    reasoning_payload="deepseek",
    suppress_temperature_when_reasoning=True,
)
_OPENROUTER_PROFILE = ProviderRequestProfile(
    name="openrouter",
    reasoning_payload="openrouter",
)
_NO_REASONING_PROFILE = ProviderRequestProfile(
    name="provider-neutral",
    reasoning_payload="none",
)


def request_profile_for_config(config: ProviderProfileConfig) -> ProviderRequestProfile:
    slug = config.provider_slug
    endpoint = _normalize_endpoint(config.base_url)
    model = config.model.strip().lower()
    if slug == LLAMA_CPP_PROVIDER_SLUG:
        return _NO_REASONING_PROFILE
    if slug == "deepseek" or endpoint in _DEEPSEEK_ENDPOINTS:
        return _DEEPSEEK_PROFILE
    if slug == "openrouter" or endpoint == _OPENROUTER_ENDPOINT:
        return _OPENROUTER_PROFILE
    if slug in {"openai", "openai-codex"} or endpoint == _OPENAI_ENDPOINT:
        return _GENERIC_OPENAI_COMPATIBLE_PROFILE
    if model.startswith("deepseek-") and "deepseek.com" in endpoint:
        return _DEEPSEEK_PROFILE
    if slug == "pollinations":
        return _NO_REASONING_PROFILE
    return _GENERIC_OPENAI_COMPATIBLE_PROFILE


def reasoning_payload_for_profile(
    profile: ProviderRequestProfile,
    requested_level: str,
    supported_levels: Iterable[str],
) -> dict[str, object]:
    level = _select_reasoning_level(requested_level, supported_levels)
    if level is None or profile.reasoning_payload == "none":
        return {}
    if profile.reasoning_payload == "deepseek":
        effort = "max" if level == "xhigh" else "high"
        return {"extra_body": {"thinking": {"type": "enabled"}}, "reasoning_effort": effort}
    if profile.reasoning_payload == "openrouter":
        return {"extra_body": {"reasoning": {"effort": level}}}
    return {"reasoning_effort": level}


def reasoning_payload_for_config(
    config: ReasoningPayloadConfig,
    supported_levels: Iterable[str],
) -> tuple[dict[str, object], bool]:
    profile = request_profile_for_config(config)
    payload = reasoning_payload_for_profile(profile, config.reasoning_level, supported_levels)
    suppress_temperature = profile.suppress_temperature_when_reasoning and bool(payload)
    return payload, suppress_temperature


def _select_reasoning_level(requested_level: str, supported_levels: Iterable[str]) -> str | None:
    choices = tuple(level for level in supported_levels if level in _REASONING_ORDER)
    if not choices:
        return None
    normalized = requested_level.casefold()
    if normalized in choices:
        return normalized
    return choices[0]


def _normalize_endpoint(base_url: str) -> str:
    return base_url.strip().rstrip("/")
