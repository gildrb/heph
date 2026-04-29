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
