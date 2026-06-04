"""Shared helpers for the built-in model catalog."""

from __future__ import annotations

_PROVIDER_PREFIXES: dict[str, tuple[str, ...]] = {
    "pollinations": ("openai", "openai-fast"),
    "openrouter": (
        "openrouter/",
        "/",
    ),
    "openai": ("gpt-", "o"),
    "openai-codex": ("gpt-",),
    "deepseek": ("deepseek-",),
    "zai": ("glm-",),
}


def _normalize_endpoint(base_url: str) -> str:
    return base_url.strip().rstrip("/")


_ENDPOINT_PREFIXES: dict[str, tuple[str, ...]] = {
    _normalize_endpoint("https://text.pollinations.ai/openai"): _PROVIDER_PREFIXES["pollinations"],
    _normalize_endpoint("https://openrouter.ai/api/v1"): _PROVIDER_PREFIXES["openrouter"],
    _normalize_endpoint("https://api.openai.com/v1"): _PROVIDER_PREFIXES["openai"],
    _normalize_endpoint("https://api.deepseek.com"): _PROVIDER_PREFIXES["deepseek"],
    _normalize_endpoint("https://api.deepseek.com/v1"): _PROVIDER_PREFIXES["deepseek"],
    _normalize_endpoint("https://api.z.ai/api/paas/v4/"): _PROVIDER_PREFIXES["zai"],
}


def _matches_prefixes(model_name: str, prefixes: tuple[str, ...]) -> bool:
    normalized = model_name.strip().lower()
    if not normalized:
        return False
    if prefixes == _PROVIDER_PREFIXES["pollinations"]:
        return normalized in prefixes
    if "/" in prefixes:
        return "/" in normalized
    return any(normalized.startswith(prefix) for prefix in prefixes)


def filter_supported_models(models: list[str], provider_slug: str) -> list[str]:
    prefixes = _PROVIDER_PREFIXES.get(provider_slug)
    if prefixes is None:
        return list(models)
    return [model for model in models if _matches_prefixes(model, prefixes)]


def is_supported_model_for_endpoint(model_name: str, base_url: str) -> bool:
    prefixes = _ENDPOINT_PREFIXES.get(_normalize_endpoint(base_url))
    if prefixes is None:
        return True
    return _matches_prefixes(model_name, prefixes)


def is_supported_model_for_provider(model_name: str, provider_slug: str) -> bool:
    prefixes = _PROVIDER_PREFIXES.get(provider_slug)
    if prefixes is None:
        return True
    return _matches_prefixes(model_name, prefixes)
