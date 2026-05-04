"""Shared model picker helpers for shell and TUI commands."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.model_choices import (
    configured_model_choices,
    model_free_description,
    model_picker_columns,
)

__all__ = [
    "configured_model_choices",
    "model_free_description",
    "model_picker_columns",
    "switch_model",
]


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
