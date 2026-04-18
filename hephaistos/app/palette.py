"""Shared monochrome palette for Hephaistos terminal surfaces."""

from __future__ import annotations

from hephaistos.palette import (  # re-export for backward compat
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

__all__ = [
    "BOLD",
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
    "STYLE_ERROR",
    "STYLE_PROMPT",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "ansi_fg",
]

STYLE_PROMPT = f"{BOLD}{ansi_fg(FORGE_EMBER)}"
STYLE_ACCENT = STYLE_PROMPT
STYLE_DIM = f"{DIM}{ansi_fg(FORGE_SMOKE)}"
STYLE_ERROR = f"{BOLD}{ansi_fg(FORGE_IRON)}"
STYLE_SUCCESS = f"{BOLD}{ansi_fg(FORGE_GREEN)}"
STYLE_WARNING = STYLE_PROMPT
STYLE_ASSISTANT = STYLE_PROMPT
