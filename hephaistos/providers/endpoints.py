"""Provider endpoint classification helpers."""

from __future__ import annotations


def normalize_endpoint_url(url: str) -> str:
    """Return a canonical endpoint URL for provider comparisons."""
    return url.strip().rstrip("/")


KEYLESS_ENDPOINTS = frozenset(
    {
        normalize_endpoint_url("https://text.pollinations.ai/openai"),
    }
)


def is_keyless_endpoint(base_url: str) -> bool:
    """Return whether an endpoint can be called without an API key."""
    return normalize_endpoint_url(base_url) in KEYLESS_ENDPOINTS
