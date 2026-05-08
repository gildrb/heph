"""Chat-session provider selection service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.providers.access import activate_provider_config
from hephaistos.providers.config import Provider, ProviderConfig

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


def activate_provider_for_session(
    pc: ProviderConfig,
    session: ChatSession,
    slug: str,
) -> Provider:
    """Activate a provider, persist it, and apply it to a chat session."""
    provider = activate_provider_config(pc, slug)
    pc.apply_to_config(session.config)
    pc.save()
    return provider
