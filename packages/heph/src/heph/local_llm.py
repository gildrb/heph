"""Heph-facing activation helpers for tool-capable local llama.cpp models."""

from __future__ import annotations

from pathlib import Path

from ai.providers.catalog import hydrate_provider_models
from ai.providers.config import ProviderConfig
from ai.providers.llama_cpp import (
    LLAMA_CPP_PROVIDER_SLUG,
    LlamaCppCandidate,
    LlamaCppInstallResult,
    LlamaCppModelRecord,
    find_gguf_model,
    install_hf_model,
    install_local_model,
    search_gguf_models,
)
from hephaion.chat.session import ChatSession


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


def install_local_target(target: str, *, model_id: str = "") -> LlamaCppInstallResult:
    path = Path(target).expanduser()
    if path.is_file() or target.lower().endswith(".gguf"):
        return install_local_model(path, model_id=model_id or None)
    candidate = find_hf_candidate(target)
    if candidate is None:
        raise RuntimeError("No public GGUF model matched that Hugging Face target.")
    return install_hf_model(candidate)


def find_hf_candidate(target: str) -> LlamaCppCandidate | None:
    repo_id, quant = _split_hf_target(target)
    if quant:
        return find_gguf_model(repo_id, quant=quant)
    candidates = search_gguf_models(repo_id, limit=50)
    for candidate in candidates:
        if candidate.repo_id == repo_id:
            return candidate
    return None


def _split_hf_target(target: str) -> tuple[str, str]:
    repo_id, separator, quant = target.strip().rpartition(":")
    if separator and repo_id and quant:
        return repo_id, quant.upper()
    return target.strip(), ""
