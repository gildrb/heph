"""Model thinking visibility controls."""

from __future__ import annotations

from typing import Final

THINKING_VISIBILITY_OFF: Final[str] = "off"
THINKING_VISIBILITY_MINIMAL: Final[str] = "minimal"
THINKING_VISIBILITY_ALL: Final[str] = "all"
THINKING_VISIBILITY_MODES: Final[tuple[str, ...]] = (
    THINKING_VISIBILITY_OFF,
    THINKING_VISIBILITY_MINIMAL,
    THINKING_VISIBILITY_ALL,
)
DEFAULT_THINKING_VISIBILITY: Final[str] = THINKING_VISIBILITY_OFF


def normalize_thinking_visibility(value: object) -> str:
    normalized = str(value).strip().lower()
    if normalized in THINKING_VISIBILITY_MODES:
        return normalized
    return DEFAULT_THINKING_VISIBILITY


def next_thinking_visibility(current: object) -> str:
    normalized = normalize_thinking_visibility(current)
    index = THINKING_VISIBILITY_MODES.index(normalized)
    return THINKING_VISIBILITY_MODES[(index + 1) % len(THINKING_VISIBILITY_MODES)]


__all__ = [
    "DEFAULT_THINKING_VISIBILITY",
    "THINKING_VISIBILITY_ALL",
    "THINKING_VISIBILITY_MINIMAL",
    "THINKING_VISIBILITY_MODES",
    "THINKING_VISIBILITY_OFF",
    "next_thinking_visibility",
    "normalize_thinking_visibility",
]
