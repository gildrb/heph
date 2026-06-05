"""Current terminal theme selection."""

from __future__ import annotations

from typing import Final

from heph_ai.palette import THEMES, Theme
from hephaion.parameters.settings import DEFAULT_THEME

_PALETTES: Final[dict[str, Theme]] = THEMES
_current_theme_name = DEFAULT_THEME


def set_theme(theme_name: str) -> str:
    global _current_theme_name  # noqa: PLW0603
    normalized = theme_name.strip().lower()
    if normalized not in _PALETTES:
        normalized = DEFAULT_THEME
    _current_theme_name = normalized
    return normalized


def current_theme_name() -> str:
    return _current_theme_name


def current_palette() -> Theme:
    return _PALETTES.get(_current_theme_name, _PALETTES[DEFAULT_THEME])
