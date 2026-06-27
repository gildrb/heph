"""Structured model choice DTOs for SDK clients."""

from __future__ import annotations

from dataclasses import dataclass

from ai.providers.config import ProviderConfig
from ai.providers.model_choices import configured_model_choices, model_free_description
from ai.runtime import ChatConfig
from harness.chat.model_selection import switch_config_model


@dataclass(frozen=True, slots=True)
class ModelChoiceSummary:
    provider_slug: str
    provider_display_name: str
    model: str
    endpoint: str
    is_free: bool
    is_current: bool
    free_description: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_slug": self.provider_slug,
            "provider_display_name": self.provider_display_name,
            "model": self.model,
            "endpoint": self.endpoint,
            "is_free": self.is_free,
            "is_current": self.is_current,
            "free_description": self.free_description,
        }


def list_model_choices(
    config: ChatConfig,
    *,
    refresh_live: bool = False,
) -> tuple[ModelChoiceSummary, ...]:
    pc = ProviderConfig.load()
    active = pc.get_active()
    active_slug = config.provider_slug or (active.slug if active is not None else "")
    choices = configured_model_choices(pc, refresh_live=refresh_live)
    return tuple(
        _model_choice_summary(
            pc,
            provider_slug=provider_slug,
            model=model,
            provider_display_name=provider_display_name,
            is_free=is_free,
            is_current=provider_slug == active_slug and model == config.model,
        )
        for provider_slug, model, provider_display_name, is_free in choices
    )


def switch_model(config: ChatConfig, provider_slug: str, model: str) -> bool:
    return switch_config_model(config, provider_slug, model)


def _model_choice_summary(
    pc: ProviderConfig,
    *,
    provider_slug: str,
    model: str,
    provider_display_name: str,
    is_free: bool,
    is_current: bool,
) -> ModelChoiceSummary:
    provider = pc.providers[provider_slug]
    return ModelChoiceSummary(
        provider_slug=provider_slug,
        provider_display_name=provider_display_name,
        model=model,
        endpoint=provider.endpoint,
        is_free=is_free,
        is_current=is_current,
        free_description=(
            model_free_description(provider.endpoint, provider_slug=provider_slug)
            if is_free
            else ""
        ),
    )


__all__ = [
    "ModelChoiceSummary",
    "list_model_choices",
    "switch_model",
]
