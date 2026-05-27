"""Provider endpoint classification helpers."""

from __future__ import annotations

KEYLESS_ENDPOINTS = frozenset(
    {
        "https://text.pollinations.ai/openai",
    }
)


def is_keyless_endpoint(base_url: str) -> bool:
    return base_url.strip().rstrip("/") in KEYLESS_ENDPOINTS
