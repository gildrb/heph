"""Provider access helpers shared by login, model, and autocomplete flows."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.catalog import hydrate_provider_models
from hephaistos.providers.config import Provider, ProviderConfig
from hephaistos.providers.keyring_store import resolve_key
from hephaistos.runtime import is_keyless_endpoint


def provider_is_accessible(provider: Provider) -> bool:
    """Return whether the user can call models from this provider now."""
    if is_keyless_endpoint(provider.endpoint):
        return True
    return bool(resolve_key(provider.slug, provider.api_key_env))


def activate_provider(pc: ProviderConfig, session: ChatSession, slug: str) -> Provider:
    """Activate a provider, refresh its model catalog, and apply it to a session."""
    pc.set_active(slug)
    hydrate_provider_models(pc)
    provider = pc.providers[slug]
    if not provider.current_model and provider.models:
        provider.current_model = provider.models[0]
    pc.apply_to_config(session.config)
    pc.save()
    return provider
