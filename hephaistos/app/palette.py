"""Theme-aware terminal palette helpers for app-facing surfaces.

Re-exports from ``hephaistos.terminal`` (the canonical location) and
``hephaistos.palette`` (low-level ANSI primitives) for backward compatibility.
"""

from __future__ import annotations

# pylint: disable=duplicate-code
from hephaistos.palette import (  # re-export low-level helpers for backward compat
    BOLD,
    DIM,
    FORGE_ASH,
    FORGE_EMBER,
    FORGE_GREEN,
    FORGE_IRON,
    FORGE_PANEL,
    FORGE_SMOKE,
    FORGE_STONE,
    RESET,
    ansi_fg,
)
from hephaistos.parameters.settings import DEFAULT_THEME, THEME_PRESETS
from hephaistos.terminal import (  # re-export shared theme/style tokens
    STYLE_ACCENT,
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_EMBER,
    STYLE_ERROR,
    STYLE_PROMPT,
    STYLE_SUCCESS,
    STYLE_WARNING,
    ThemePalette,
    current_palette,
    current_theme_name,
    set_theme,
    style_code,
)

__all__ = [
    "BOLD",
    "DEFAULT_THEME",
    "DIM",
    "FORGE_ASH",
    "FORGE_EMBER",
    "FORGE_GREEN",
    "FORGE_IRON",
    "FORGE_PANEL",
    "FORGE_SMOKE",
    "FORGE_STONE",
    "RESET",
    "STYLE_ACCENT",
    "STYLE_ASSISTANT",
    "STYLE_DIM",
    "STYLE_EMBER",
    "STYLE_ERROR",
    "STYLE_PROMPT",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "THEME_PRESETS",
    "ThemePalette",
    "ansi_fg",
    "current_palette",
    "current_theme_name",
    "set_theme",
    "style_code",
]
