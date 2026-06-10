"""Provider access decisions independent of UI adapters."""

from __future__ import annotations

from ai.providers.catalog import hydrate_provider_models
from ai.providers.config import Provider, ProviderConfig
from ai.providers.endpoints import provider_uses_keyless_access
from ai.providers.keyring_store import resolve_key
from ai.providers.oauth import resolve_oauth_key


def provider_is_accessible(provider: Provider, *, refresh_oauth: bool = True) -> bool:
    if provider.slug == "openai-codex":
        return bool(resolve_oauth_key(provider.slug, refresh_expired=refresh_oauth))
    if provider_uses_keyless_access(provider.slug, provider.endpoint):
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
