"""Shared helpers for the built-in model catalog."""

from __future__ import annotations


_PROVIDER_PREFIXES: dict[str, tuple[str, ...]] = {
    "openrouter": (
        "openai/",
        "google/",
        "qwen/",
        "stepfun/",
        "minimax/",
        "z-ai/",
        "moonshotai/",
        "xiaomi/",
        "x-ai/",
        "nvidia/",
        "arcee-ai/",
    ),
    "openai-codex": ("gpt-",),
    "zai": ("glm-",),
}

_ENDPOINT_PREFIXES: dict[str, tuple[str, ...]] = {
    "https://openrouter.ai/api/v1": _PROVIDER_PREFIXES["openrouter"],
    "https://api.openai.com/v1": _PROVIDER_PREFIXES["openai-codex"],
    "https://api.z.ai/api/paas/v4/": _PROVIDER_PREFIXES["zai"],
}


def _matches_prefixes(model_name: str, prefixes: tuple[str, ...]) -> bool:
    normalized = model_name.strip().lower()
    if not normalized:
        return False
    return any(normalized.startswith(prefix) for prefix in prefixes)


def filter_supported_models(models: list[str], provider_slug: str) -> list[str]:
    """Keep only models that belong to the built-in catalog for a provider."""
    prefixes = _PROVIDER_PREFIXES.get(provider_slug)
    if prefixes is None:
        return list(models)
    return [model for model in models if _matches_prefixes(model, prefixes)]


def is_supported_model_for_endpoint(model_name: str, base_url: str) -> bool:
    """Return True when a model matches the known families for an endpoint."""
    prefixes = _ENDPOINT_PREFIXES.get(base_url.rstrip("/"))
    if prefixes is None:
        return True
    return _matches_prefixes(model_name, prefixes)


def is_supported_model_for_provider(model_name: str, provider_slug: str) -> bool:
    """Return True when a model matches the known families for a provider."""
    prefixes = _PROVIDER_PREFIXES.get(provider_slug)
    if prefixes is None:
        return True
    return _matches_prefixes(model_name, prefixes)
