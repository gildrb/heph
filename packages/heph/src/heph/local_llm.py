"""Heph-facing activation helpers for tool-capable local llama.cpp models."""

from __future__ import annotations

from ai.providers.catalog import hydrate_provider_models
from ai.providers.config import ProviderConfig
from ai.providers.llama_cpp import (
    LLAMA_CPP_PROVIDER_SLUG,
    LlamaCppModelRecord,
    find_hf_candidate,
    install_local_target,
)
from hephaion.chat.session import ChatSession

__all__ = ["activate_local_record", "find_hf_candidate", "install_local_target"]


def activate_local_record(record: LlamaCppModelRecord, session: ChatSession | None = None) -> None:
    pc = ProviderConfig.load()
    hydrate_provider_models(pc, provider_slugs={LLAMA_CPP_PROVIDER_SLUG})
    provider = pc.providers[LLAMA_CPP_PROVIDER_SLUG]
    if record.model_id not in provider.models:
        provider.models.append(record.model_id)
    provider.endpoint = record.endpoint
    provider.current_model = record.model_id
    pc.set_active(LLAMA_CPP_PROVIDER_SLUG)
    if session is not None:
        pc.apply_to_config(session.config)
    pc.save()
