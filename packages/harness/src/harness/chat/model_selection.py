"""Chat-session model selection service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.providers import llama_cpp
from ai.providers.access import provider_is_accessible
from ai.providers.catalog import hydrate_provider_models
from ai.providers.config import Provider, ProviderConfig

if TYPE_CHECKING:
    from ai.runtime import ChatConfig

    from harness.chat.session import ChatSession


def switch_model(session: ChatSession, slug: str, model: str) -> bool:
    return switch_config_model(session.config, slug, model)


def switch_config_model(config: ChatConfig, slug: str, model: str) -> bool:
    pc = ProviderConfig.load()
    if slug == llama_cpp.LLAMA_CPP_PROVIDER_SLUG:
        hydrate_provider_models(pc, provider_slugs={slug})
    provider = pc.providers.get(slug)
    if provider is None or model not in provider.models:
        return False
    if not provider_is_accessible(provider, refresh_oauth=False):
        return False
    if not _prepare_provider_for_model(provider, model):
        return False
    pc.set_active(slug)
    provider.current_model = model
    pc.apply_to_config(config)
    pc.save()
    return True


def ensure_session_model_ready(session: ChatSession) -> bool:
    if not _session_uses_llama_cpp(session):
        return True

    pc = ProviderConfig.load()

    hydrate_provider_models(pc, provider_slugs={llama_cpp.LLAMA_CPP_PROVIDER_SLUG})
    provider = pc.providers.get(llama_cpp.LLAMA_CPP_PROVIDER_SLUG)
    if provider is None:
        return False
    model = session.config.model
    if not model or model not in provider.models:
        return False
    if not _prepare_provider_for_model(provider, model):
        return False
    provider.current_model = model
    _apply_provider_to_config(session.config, provider)
    pc.save()
    return True


def _session_uses_llama_cpp(session: ChatSession) -> bool:
    config = session.config
    if config.provider_slug and config.provider_slug != llama_cpp.LLAMA_CPP_PROVIDER_SLUG:
        return False
    return config.model.startswith("llama-cpp/") and llama_cpp.is_llama_cpp_endpoint(
        config.base_url
    )


def _apply_provider_to_config(config: ChatConfig, provider: Provider) -> None:
    config.base_url = provider.endpoint
    config.apply_provider_reference(provider.slug, provider.api_key_env)


def _prepare_provider_for_model(provider: Provider, model: str) -> bool:
    if provider.slug != llama_cpp.LLAMA_CPP_PROVIDER_SLUG:
        return True
    record = llama_cpp.model_record(model)
    if record is None or not record.tool_capable:
        return False
    try:
        server = llama_cpp.start_record(record)
    except (OSError, RuntimeError):
        return False
    provider.endpoint = server.endpoint
    return True
