"""Theme-aware terminal palette helpers for app-facing surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

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
]


@dataclass(frozen=True)
class ThemePalette:
    name: str
    panel: str
    stone: str
    text: str
    dim: str
    accent: str
    ember: str
    configured: str
    error: str
    success: str
    highlight: str
    is_transparent: bool = True
    background: str = "transparent"


_PALETTES: Final[dict[str, ThemePalette]] = {
    "forge": ThemePalette(
        name="forge",
        panel="#1C1C1C",
        stone="#555555",
        text="#E0E0E0",
        dim="#808080",
        accent="#C8C8C8",
        ember="#9B4A2E",
        configured="#7F9A6A",
        error="#CC3333",
        success="#66BB6A",
        highlight="#333333",
        is_transparent=True,
        background="transparent",
    ),
    "light": ThemePalette(
        name="light",
        panel="#EDE8DC",
        stone="#C4B8A6",
        text="#2C241B",
        dim="#7A7068",
        accent="#8A5A2B",
        ember="#8E4A32",
        configured="#687A4B",
        error="#B03A2E",
        success="#2E8B57",
        highlight="#D4C9B8",
        is_transparent=False,
        background="#F6F2EA",
    ),
    "high_contrast": ThemePalette(
        name="high_contrast",
        panel="#1A1A1A",
        stone="#2E2E2E",
        text="#FFFFFF",
        dim="#C0C0C0",
        accent="#FFD400",
        ember="#E08050",
        configured="#A9C97A",
        error="#FF4D4D",
        success="#00FF88",
        highlight="#404040",
        is_transparent=False,
        background="#000000",
    ),
}


class _StyleToken:
    __slots__ = ("_style_name",)

    def __init__(self, style_name: str) -> None:
        self._style_name = style_name

    def __str__(self) -> str:
        return style_code(self._style_name)

    def __repr__(self) -> str:
        return f"_StyleToken({self._style_name!r})"


_current_theme_name = DEFAULT_THEME


def set_theme(theme_name: str) -> str:
    """Set the active theme and return the normalized preset name."""
    global _current_theme_name  # noqa: PLW0603
    normalized = theme_name.strip().lower()
    if normalized not in _PALETTES:
        normalized = DEFAULT_THEME
    _current_theme_name = normalized
    return normalized


def current_theme_name() -> str:
    return _current_theme_name


def current_palette() -> ThemePalette:
    return _PALETTES.get(_current_theme_name, _PALETTES[DEFAULT_THEME])


def style_code(style_name: str) -> str:
    palette = current_palette()
    if style_name in {"prompt", "accent", "warning", "assistant"}:
        return f"{BOLD}{ansi_fg(palette.accent)}"
    if style_name == "ember":
        return f"{BOLD}{ansi_fg(palette.ember)}"
    if style_name == "dim":
        return f"{DIM}{ansi_fg(palette.dim)}"
    if style_name == "error":
        return f"{BOLD}{ansi_fg(palette.error)}"
    if style_name == "success":
        return f"{BOLD}{ansi_fg(palette.success)}"
    return ""


STYLE_PROMPT = _StyleToken("prompt")
STYLE_ACCENT = _StyleToken("accent")
STYLE_DIM = _StyleToken("dim")
STYLE_EMBER = _StyleToken("ember")
STYLE_ERROR = _StyleToken("error")
STYLE_SUCCESS = _StyleToken("success")
STYLE_WARNING = _StyleToken("warning")
STYLE_ASSISTANT = _StyleToken("assistant")
