"""Structured provider status DTOs for SDK clients."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ai.providers import oauth
from ai.providers.config import Provider, ProviderConfig
from ai.providers.endpoints import provider_uses_keyless_access
from ai.providers.keyring_store import (
    GLOBAL_API_KEY_ENV,
    get_volatile,
    retrieve_key,
)
from ai.runtime import ChatConfig


@dataclass(frozen=True, slots=True)
class ProviderSummary:
    provider_slug: str
    display_name: str
    endpoint: str
    api_key_env: str
    current_model: str
    model_count: int
    is_active: bool
    is_current: bool
    credential_kind: str
    credential_source: str
    credential_required: bool
    credential_configured: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_slug": self.provider_slug,
            "display_name": self.display_name,
            "endpoint": self.endpoint,
            "api_key_env": self.api_key_env,
            "current_model": self.current_model,
            "model_count": self.model_count,
            "is_active": self.is_active,
            "is_current": self.is_current,
            "credential_kind": self.credential_kind,
            "credential_source": self.credential_source,
            "credential_required": self.credential_required,
            "credential_configured": self.credential_configured,
        }


def list_providers(config: ChatConfig) -> tuple[ProviderSummary, ...]:
    pc = ProviderConfig.load()
    current_slug = _current_provider_slug(pc, config)
    oauth_providers = frozenset(oauth.list_providers())
    return tuple(
        _provider_summary(provider, current_slug=current_slug, oauth_providers=oauth_providers)
        for provider in pc.providers.values()
    )


def _current_provider_slug(pc: ProviderConfig, config: ChatConfig) -> str:
    if config.provider_slug:
        return config.provider_slug
    active = pc.get_active()
    return active.slug if active is not None else ""


def _provider_summary(
    provider: Provider,
    *,
    current_slug: str,
    oauth_providers: frozenset[str],
) -> ProviderSummary:
    credential = _credential_status(provider, oauth_providers=oauth_providers)
    return ProviderSummary(
        provider_slug=provider.slug,
        display_name=provider.display_name,
        endpoint=provider.endpoint,
        api_key_env=provider.api_key_env,
        current_model=provider.resolved_model,
        model_count=len(provider.models),
        is_active=provider.active,
        is_current=provider.slug == current_slug,
        credential_kind=credential.kind,
        credential_source=credential.source,
        credential_required=credential.required,
        credential_configured=credential.configured,
    )


@dataclass(frozen=True, slots=True)
class _CredentialStatus:
    kind: str
    source: str
    required: bool
    configured: bool


def _credential_status(
    provider: Provider,
    *,
    oauth_providers: frozenset[str],
) -> _CredentialStatus:
    if provider_uses_keyless_access(provider.slug, provider.endpoint):
        return _CredentialStatus("keyless", "keyless", required=False, configured=True)
    if not provider.api_key_env:
        source = "oauth" if provider.slug in oauth_providers else "missing"
        return _CredentialStatus(
            "oauth",
            source,
            required=True,
            configured=source != "missing",
        )
    return _api_key_credential_status(provider)


def _api_key_credential_status(provider: Provider) -> _CredentialStatus:
    source = _api_key_credential_source(provider)
    return _CredentialStatus(
        "api_key",
        source,
        required=True,
        configured=source != "missing",
    )


def _api_key_credential_source(provider: Provider) -> str:
    if os.environ.get(GLOBAL_API_KEY_ENV, "").strip():
        return "global_env"
    if retrieve_key(provider.slug):
        return "keychain"
    if provider.api_key_env and os.environ.get(provider.api_key_env, "").strip():
        return "provider_env"
    if get_volatile(provider.slug):
        return "session"
    return "missing"


__all__ = [
    "ProviderSummary",
    "list_providers",
]
