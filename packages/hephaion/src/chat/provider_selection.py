"""Chat-session provider selection service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from heph_ai.providers.access import activate_provider_config
from heph_ai.providers.config import Provider, ProviderConfig

if TYPE_CHECKING:
    from chat.session import ChatSession


def activate_provider_for_session(
    pc: ProviderConfig,
    session: ChatSession,
    slug: str,
) -> Provider:
    provider = activate_provider_config(pc, slug)
    pc.apply_to_config(session.config)
    pc.save()
    return provider
