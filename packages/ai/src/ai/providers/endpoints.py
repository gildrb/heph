"""Provider endpoint classification helpers."""

from __future__ import annotations

from ai.providers.llama_cpp import LLAMA_CPP_PROVIDER_SLUG, is_llama_cpp_endpoint

KEYLESS_ENDPOINTS = frozenset(
    {
        "https://text.pollinations.ai/openai",
    }
)


def is_keyless_endpoint(base_url: str) -> bool:
    return base_url.strip().rstrip("/") in KEYLESS_ENDPOINTS


def provider_uses_keyless_access(provider_slug: str, base_url: str) -> bool:
    return (
        provider_slug == LLAMA_CPP_PROVIDER_SLUG and is_llama_cpp_endpoint(base_url)
    ) or is_keyless_endpoint(base_url)
