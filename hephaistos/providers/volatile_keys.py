"""Session-scoped provider key storage."""

from __future__ import annotations

_volatile: dict[str, str] = {}


def set_volatile_key(slug: str, api_key: str) -> None:
    """Store a provider key in process memory only."""
    _volatile[slug] = api_key


def get_volatile_key(slug: str) -> str | None:
    """Return a session-scoped provider key, if one exists."""
    return _volatile.get(slug)


def clear_volatile_key(slug: str) -> bool:
    """Remove a session-scoped provider key."""
    return _volatile.pop(slug, None) is not None
