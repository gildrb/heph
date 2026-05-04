"""Provider access helpers shared by login, model, and autocomplete flows."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.access import activate_provider_config
from hephaistos.providers.config import Provider, ProviderConfig


def activate_provider(pc: ProviderConfig, session: ChatSession, slug: str) -> Provider:
    """Activate a provider, refresh its model catalog, and apply it to a session."""
    provider = activate_provider_config(pc, slug)
    pc.apply_to_config(session.config)
    pc.save()
    return provider
