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


def shell_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"fg:{palette.text}",
        "armory": palette.text,
        "prompt-mark": f"bold {palette.accent}",
        "composer": f"fg:{palette.text}",
        "bottom-toolbar": f"noreverse fg:{palette.dim}",
        "bottom-toolbar.text": f"noreverse fg:{palette.dim}",
        "toolbar-location": f"noreverse fg:{palette.text}",
        "toolbar-accent": f"noreverse bold fg:{palette.text}",
        "toolbar-error": f"noreverse bold fg:{palette.error}",
        "completion-menu.completion.current": f"bg:{palette.stone} fg:{palette.text} bold",
        "completion-menu.completion": f"bg:{palette.panel} fg:{palette.text}",
        "completion-menu.meta.completion.current": f"bg:{palette.stone} fg:{palette.text}",
        "completion-menu.meta.completion": f"bg:{palette.panel} fg:{palette.dim}",
        "scrollbar.background": f"bg: fg:{palette.stone}",
        "scrollbar.button": f"bg: fg:{palette.stone}",
        "header": f"fg:{palette.text}",
        "header.title": f"bold fg:{palette.ember}",
        "header.dim": f"fg:{palette.dim}",
        "header.accent": f"fg:{palette.accent}",
        "header.ember": f"bold fg:{palette.ember}",
        "header.configured": f"fg:{palette.configured}",
        "header.error": f"bold fg:{palette.error}",
        "header.success": f"fg:{palette.configured}",
        "header.warning": f"bold fg:{palette.error}",
        "separator": f"fg:{palette.stone}",
        "chat-area": f"fg:{palette.text}",
        "chat-area.user": f"fg:{palette.text}",
        "chat-area.assistant": f"fg:{palette.accent}",
        "chat-area.assistant-label": f"bold fg:{palette.accent}",
        "chat-area.system": f"fg:{palette.dim}",
        "chat-area.error": f"bold fg:{palette.error}",
        "chat-area.success": f"fg:{palette.success}",
        "chat-area.tool": f"fg:{palette.dim}",
    }


def menu_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"fg:{palette.text}",
        "inline-menu.title": f"bold fg:{palette.text}",
        "inline-menu.option": f"fg:{palette.text}",
        "inline-menu.option.current": f"bg:{palette.highlight} fg:{palette.text} bold",
        "inline-menu.description": f"fg:{palette.dim}",
        "inline-menu.description.current": f"bg:{palette.highlight} fg:{palette.text}",
        "inline-menu.badge": f"fg:{palette.accent}",
        "inline-menu.hint": f"fg:{palette.dim}",
    }


def browser_style_dict() -> dict[str, str]:
    palette = current_palette()
    return {
        "": f"fg:{palette.text}",
        "browser.title": f"bold fg:{palette.text}",
        "browser.path": f"fg:{palette.dim}",
        "browser.entry": f"fg:{palette.text}",
        "browser.entry.selected": f"bg:{palette.highlight} fg:{palette.text} bold",
        "browser.parent": f"fg:{palette.dim}",
        "browser.parent.selected": f"bg:{palette.highlight} fg:{palette.text} bold",
        "browser.hint": f"fg:{palette.dim}",
    }


STYLE_PROMPT = _StyleToken("prompt")
STYLE_ACCENT = _StyleToken("accent")
STYLE_DIM = _StyleToken("dim")
STYLE_EMBER = _StyleToken("ember")
STYLE_ERROR = _StyleToken("error")
STYLE_SUCCESS = _StyleToken("success")
STYLE_WARNING = _StyleToken("warning")
STYLE_ASSISTANT = _StyleToken("assistant")
