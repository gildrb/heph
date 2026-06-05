"""Chat-session model selection service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.providers.access import provider_is_accessible
from ai.providers.config import ProviderConfig

if TYPE_CHECKING:
    from chat.session import ChatSession


def switch_model(session: ChatSession, slug: str, model: str) -> bool:
    pc = ProviderConfig.load()
    provider = pc.providers.get(slug)
    if provider is None or model not in provider.models:
        return False
    if not provider_is_accessible(provider, refresh_oauth=False):
        return False
    pc.set_active(slug)
    provider.current_model = model
    pc.apply_to_config(session.config)
    pc.save()
    return True
