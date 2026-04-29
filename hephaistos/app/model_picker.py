"""Shared model picker helpers for shell and TUI commands."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.registry import get_registry as get_provider_registry

_MODEL_PROVIDER_ORDER = {
    "pollinations": 0,
    "openai-codex": 1,
    "openrouter": 2,
    "zai": 3,
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
    "openai-codex": "OpenAI Codex",
    "openrouter": "OpenRouter",
    "pollinations": "Pollinations",
    "zai": "Z.AI",
}


def configured_model_choices(
    pc: ProviderConfig | None = None,
) -> list[tuple[str, str, str, bool]]:
    """Return configured models as (provider slug, model, display label, free)."""
    pc = pc or ProviderConfig.load()
    registry = get_provider_registry()
    choices: list[tuple[str, str, str, bool]] = []
    for slug, provider in pc.providers.items():
        if slug == "custom" and not provider.models:
            continue
        for model in provider.models:
            info = registry.get(model)
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
    is_free: bool,
    is_current: bool,
) -> tuple[str, str, str, str]:
    """Return display columns as provider, model, source, tags."""
    provider = _model_provider_label(slug, model, display_name)
    model_label = model.rsplit("/", 1)[1] if "/" in model else model
    source = _SOURCE_LABELS.get(slug, display_name.removesuffix(" (free)"))
    tags = " ".join(
        tag for tag in ("free" if is_free else "", "current" if is_current else "") if tag
    )
    return provider, model_label, source, tags


def _model_provider_label(slug: str, model: str, display_name: str) -> str:
    if "/" in model:
        owner, _model_name = model.split("/", 1)
        return _OWNER_LABELS.get(owner, owner.replace("-", " ").title())
    if slug == "pollinations":
        for prefix, label in _POLLINATIONS_FAMILIES:
            if model.startswith(prefix):
                return label
        return "Pollinations"
    if slug == "openai-codex":
        return "OpenAI"
    if slug == "zai":
        return "Z.AI"
    return display_name.removesuffix(" (free)")


def switch_model(session: ChatSession, slug: str, model: str) -> bool:
    pc = ProviderConfig.load()
    provider = pc.providers.get(slug)
    if provider is None or model not in provider.models:
        return False
    pc.set_active(slug)
    provider.current_model = model
    pc.apply_to_config(session.config)
    pc.save()
    return True
