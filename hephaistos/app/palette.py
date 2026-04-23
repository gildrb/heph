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
    "STYLE_ERROR",
    "STYLE_PROMPT",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "THEME_PRESETS",
    "ThemePalette",
    "ansi_fg",
    "browser_style_dict",
    "current_palette",
    "current_theme_name",
    "menu_style_dict",
    "set_theme",
    "shell_style_dict",
]


@dataclass(frozen=True)
class ThemePalette:
    name: str
    panel: str
    stone: str
    text: str
    dim: str
    accent: str
    error: str
    success: str


_PALETTES: Final[dict[str, ThemePalette]] = {
    "forge": ThemePalette(
        name="forge",
        panel="#1C1C1C",
        stone="#555555",
        text="#E0E0E0",
        dim="#808080",
        accent="#C8C8C8",
        error="#CC3333",
        success="#66BB6A",
    ),
    "light": ThemePalette(
        name="light",
        panel="#F6F2EA",
        stone="#D9CCBA",
        text="#2C241B",
        dim="#6E655B",
        accent="#8A5A2B",
        error="#B03A2E",
        success="#2E8B57",
    ),
    "high_contrast": ThemePalette(
        name="high_contrast",
        panel="#000000",
        stone="#2E2E2E",
        text="#FFFFFF",
        dim="#D0D0D0",
        accent="#FFD400",
        error="#FF4D4D",
        success="#00FF88",
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
    if style_name == "dim":
        return f"{DIM}{ansi_fg(palette.dim)}"
    if style_name == "error":
        return f"{BOLD}{ansi_fg(palette.error)}"
    if style_name == "success":
        return f"{BOLD}{ansi_fg(palette.success)}"
    return ""


def shell_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"bg:{palette.panel} fg:{palette.text}",
        "armory": palette.text,
        "prompt-mark": f"bold {palette.accent}",
        "composer": f"bg:{palette.panel} fg:{palette.text}",
        "bottom-toolbar": f"noreverse bg:{palette.panel} fg:{palette.dim}",
        "bottom-toolbar.text": f"noreverse bg:{palette.panel} fg:{palette.dim}",
        "toolbar-location": f"noreverse bg:{palette.panel} fg:{palette.text}",
        "toolbar-accent": f"noreverse bg:{palette.panel} bold fg:{palette.text}",
        "toolbar-error": f"noreverse bg:{palette.panel} bold fg:{palette.error}",
        "completion-menu.completion.current": f"bg:{palette.stone} fg:{palette.text} bold",
        "completion-menu.completion": f"bg:{palette.panel} fg:{palette.text}",
        "completion-menu.meta.completion.current": f"bg:{palette.stone} fg:{palette.text}",
        "completion-menu.meta.completion": f"bg:{palette.panel} fg:{palette.dim}",
        "scrollbar.background": f"bg:{palette.panel}",
        "scrollbar.button": f"bg:{palette.stone}",
    }


def menu_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"bg:{palette.panel} fg:{palette.text}",
        "inline-menu.title": f"bg:{palette.panel} bold fg:{palette.accent}",
        "inline-menu.option": f"bg:{palette.panel} fg:{palette.text}",
        "inline-menu.option.current": f"bg:{palette.stone} bold fg:{palette.accent}",
        "inline-menu.description": f"bg:{palette.panel} fg:{palette.dim}",
        "inline-menu.description.current": f"bg:{palette.stone} fg:{palette.text}",
        "inline-menu.badge": f"bg:{palette.stone} bold fg:{palette.accent}",
        "inline-menu.hint": f"bg:{palette.panel} fg:{palette.dim}",
    }


def browser_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"bg:{palette.panel} fg:{palette.text}",
        "browser.title": f"bg:{palette.panel} bold fg:{palette.accent}",
        "browser.path": f"bg:{palette.panel} fg:{palette.dim}",
        "browser.entry": f"bg:{palette.panel} fg:{palette.text}",
        "browser.entry.selected": f"bg:{palette.stone} bold fg:{palette.accent}",
        "browser.parent": f"bg:{palette.panel} fg:{palette.dim}",
        "browser.parent.selected": f"bg:{palette.stone} bold fg:{palette.accent}",
        "browser.hint": f"bg:{palette.panel} fg:{palette.dim}",
    }


STYLE_PROMPT = _StyleToken("prompt")
STYLE_ACCENT = _StyleToken("accent")
STYLE_DIM = _StyleToken("dim")
STYLE_ERROR = _StyleToken("error")
STYLE_SUCCESS = _StyleToken("success")
STYLE_WARNING = _StyleToken("warning")
STYLE_ASSISTANT = _StyleToken("assistant")
