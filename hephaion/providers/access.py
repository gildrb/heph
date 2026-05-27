"""Provider access decisions independent of UI adapters."""

from __future__ import annotations

from hephaion.providers.catalog import hydrate_provider_models
from hephaion.providers.config import Provider, ProviderConfig
from hephaion.providers.endpoints import is_keyless_endpoint
from hephaion.providers.keyring_store import resolve_key
from hephaion.providers.oauth import resolve_oauth_key


def provider_is_accessible(provider: Provider, *, refresh_oauth: bool = True) -> bool:
    if provider.slug == "openai-codex":
        return bool(resolve_oauth_key(provider.slug, refresh_expired=refresh_oauth))
    if is_keyless_endpoint(provider.endpoint):
        return True
    return bool(
        resolve_key(
            provider.slug,
            provider.api_key_env,
            refresh_oauth=refresh_oauth,
        )
    )


def activate_provider_config(pc: ProviderConfig, slug: str) -> Provider:
    pc.set_active(slug)
    hydrate_provider_models(pc, provider_slugs={slug})
    provider = pc.providers[slug]
    if not provider.current_model and provider.models:
        provider.current_model = provider.models[0]
    return provider
