"""Chat-session model selection service."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig


def switch_model(session: ChatSession, slug: str, model: str) -> bool:
    """Persist a selected provider model and apply it to a chat session."""
    pc = ProviderConfig.load()
    provider = pc.providers.get(slug)
    if provider is None or model not in provider.models:
        return False
    pc.set_active(slug)
    provider.current_model = model
    pc.apply_to_config(session.config)
    pc.save()
    return True
