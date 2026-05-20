"""Provider model choice construction independent of UI adapters."""

from __future__ import annotations

from hephaistos.providers.access import provider_is_accessible
from hephaistos.providers.catalog import hydrate_provider_models
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.providers.registry import get_registry as get_provider_registry

_MODEL_PROVIDER_ORDER = {
    "openai": 0,
    "openai-codex": 1,
    "openrouter": 2,
    "zai": 3,
    "pollinations": 4,
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
    eligible_slugs: set[str] = set()
    for slug, provider in pc.providers.items():
        if slug == "custom" and not provider.models:
            continue
        if not provider_is_accessible(
            provider,
            refresh_oauth=refresh_live,
        ):
            continue
        eligible_slugs.add(slug)

    hydrate_provider_models(
        pc,
        allow_network=refresh_live,
        provider_slugs=eligible_slugs,
    )

    registry = get_provider_registry()
    choices: list[tuple[str, str, str, bool]] = []
    for slug, provider in pc.providers.items():
        if slug not in eligible_slugs:
            continue
        for model in provider.models:
            info = registry.get(model, provider=slug)
            is_free = info.is_free if info is not None else False
            choices.append((slug, model, provider.display_name, is_free))
    return sorted(
        choices,
        key=lambda item: (
            _MODEL_PROVIDER_ORDER.get(item[0], 50),
            0 if item[3] else 1,
            item[1].lower(),
        ),
    )


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
