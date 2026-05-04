"""Provider access decisions independent of UI adapters."""

from __future__ import annotations

from hephaistos.providers.catalog import hydrate_provider_models
from hephaistos.providers.config import Provider, ProviderConfig
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.providers.keyring_store import resolve_key


def provider_is_accessible(provider: Provider) -> bool:
    """Return whether the user can call models from this provider now."""
    if is_keyless_endpoint(provider.endpoint):
        return True
    return bool(resolve_key(provider.slug, provider.api_key_env))


def activate_provider_config(pc: ProviderConfig, slug: str) -> Provider:
    """Activate a provider and refresh its model catalog."""
    pc.set_active(slug)
    hydrate_provider_models(pc)
    provider = pc.providers[slug]
    if not provider.current_model and provider.models:
        provider.current_model = provider.models[0]
    return provider
