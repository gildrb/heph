"""Shared rules for allowed and blocked model names."""

from __future__ import annotations


def is_blocked_model_name(model_name: str) -> bool:
    """Return True when the model name refers to Anthropic/Claude."""
    normalized = model_name.strip().lower()
    if not normalized:
        return False
    return "anthropic" in normalized or "claude" in normalized


def filter_blocked_models(models: list[str]) -> list[str]:
    """Return only models that are currently allowed."""
    return [model for model in models if not is_blocked_model_name(model)]
