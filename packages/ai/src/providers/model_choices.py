"""Provider model choice construction independent of UI adapters."""

from __future__ import annotations

from collections.abc import Iterable

from providers.access import provider_is_accessible
from providers.catalog import hydrate_provider_models
from providers.config import Provider, ProviderConfig
from providers.endpoints import is_keyless_endpoint
from providers.registry import get_registry as get_provider_registry

_MODEL_PROVIDER_ORDER = {
    "openai": 0,
    "openai-codex": 1,
    "deepseek": 2,
    "openrouter": 3,
    "zai": 4,
    "pollinations": 5,
    "custom": 99,
}

_OWNER_LABELS = {
    "arcee-ai": "Arcee AI",
    "google": "Google",
    "minimax": "MiniMax",
    "moonshotai": "Moonshot AI",
    "nvidia": "NVIDIA",
    "openai": "OpenAI",
    "qwen": "Qwen",
    "stepfun": "StepFun",
    "x-ai": "xAI",
    "xiaomi": "Xiaomi",
    "z-ai": "Z.AI",
}

_POLLINATIONS_FAMILIES = (
    ("openai", "OpenAI"),
    ("mistral", "Mistral"),
    ("qwen", "Qwen"),
    ("deepseek", "DeepSeek"),
    ("llama", "Llama"),
    ("gemini", "Google"),
)

_SOURCE_LABELS = {
    "openai": "OpenAI API",
    "openai-codex": "OpenAI Codex",
    "deepseek": "DeepSeek API",
    "openrouter": "OpenRouter",
    "pollinations": "Pollinations",
    "zai": "Z.AI",
}

_PROVIDER_LABELS = {
    "openai-codex": "OpenAI",
    "zai": "Z.AI",
}


def configured_model_choices(
    pc: ProviderConfig | None = None,
    *,
    refresh_live: bool = False,
) -> list[tuple[str, str, str, bool]]:
    pc = pc or ProviderConfig.load()
    eligible_slugs = _eligible_provider_slugs(pc.providers.values(), refresh_live=refresh_live)

    hydrate_provider_models(
        pc,
        allow_network=refresh_live,
        provider_slugs=eligible_slugs,
    )

    choices = _model_choice_rows(pc, eligible_slugs)
    return sorted(choices, key=_model_choice_sort_key)


def _eligible_provider_slugs(
    providers: Iterable[Provider],
    *,
    refresh_live: bool,
) -> set[str]:
    return {
        provider.slug
        for provider in providers
        if not _empty_custom_provider(provider)
        and provider_is_accessible(provider, refresh_oauth=refresh_live)
    }


def _empty_custom_provider(provider: Provider) -> bool:
    return provider.slug == "custom" and not provider.models


def _model_choice_rows(
    pc: ProviderConfig,
    eligible_slugs: set[str],
) -> list[tuple[str, str, str, bool]]:
    registry = get_provider_registry()
    return [
        (
            slug,
            model,
            provider.display_name,
            (info.is_free if (info := registry.get(model, provider=slug)) is not None else False),
        )
        for slug, provider in pc.providers.items()
        if slug in eligible_slugs
        for model in provider.models
    ]


def _model_choice_sort_key(item: tuple[str, str, str, bool]) -> tuple[int, int, str]:
    slug, model, _display_name, is_free = item
    return (_MODEL_PROVIDER_ORDER.get(slug, 50), 0 if is_free else 1, model.lower())


def model_picker_columns(
    *,
    slug: str,
    model: str,
    display_name: str,
    endpoint: str = "",
    is_free: bool,
    is_current: bool,
) -> tuple[str, str, str, str]:
    provider = _model_provider_label(slug, model, display_name)
    model_label = model.rsplit("/", 1)[1] if "/" in model else model
    source = _SOURCE_LABELS.get(slug, display_name.removesuffix(" (free)"))
    tags = " ".join(
        tag
        for tag in (
            _free_model_tag(endpoint) if is_free else "",
            "current" if is_current else "",
        )
        if tag
    )
    return provider, model_label, source, tags


def model_free_description(endpoint: str) -> str:
    return "free, no API key" if is_keyless_endpoint(endpoint) else "free, API key required"


def _model_provider_label(slug: str, model: str, display_name: str) -> str:
    if "/" in model:
        owner, _model_name = model.split("/", 1)
        return _OWNER_LABELS.get(owner, owner.replace("-", " ").title())
    if slug == "pollinations":
        return next(
            (label for prefix, label in _POLLINATIONS_FAMILIES if model.startswith(prefix)),
            "Pollinations",
        )
    return _PROVIDER_LABELS.get(slug, display_name.removesuffix(" (free)"))


def _free_model_tag(endpoint: str) -> str:
    return "free" if is_keyless_endpoint(endpoint) else "free+key"
