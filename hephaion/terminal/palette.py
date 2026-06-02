"""Low-level ANSI primitives and shared design tokens.

This module is the only place that should assign concrete colour values. App,
TUI, terminal, and generated-report code should consume semantic ``Theme`` roles
rather than hard-coded colours so a theme change propagates consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

TRANSPARENT = "transparent"
RICH_BLACK_COLOR_NAME = "black"
BLACK_RGB: Final[tuple[int, int, int]] = (0, 0, 0)


@dataclass(frozen=True)
class Theme:
    bg_app: str
    bg_surface: str
    bg_raised: str

    text_primary: str
    text_secondary: str
    text_muted: str
    text_inverse: str

    border_subtle: str

    brand_primary: str

    action_primary_bg: str
    action_primary_text: str

    status_success_text: str
    status_error_text: str


DARK = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised="#161616",
    text_primary="#CFCFCF",
    text_secondary="#8F8F8F",
    text_muted="#6F6F6F",
    text_inverse="#000000",
    border_subtle="#3D3D3D",
    brand_primary="#FFFFFF",
    action_primary_bg="#57C785",
    action_primary_text="#000000",
    status_success_text="#57C785",
    status_error_text="#FF6B6B",
)

LIGHT = Theme(
    bg_app="#FAFAFA",
    bg_surface="#FFFFFF",
    bg_raised="#F2F2F2",
    text_primary="#000000",
    text_secondary="#404040",
    text_muted="#666666",
    text_inverse="#FFFFFF",
    border_subtle="#D9D9D9",
    brand_primary="#000000",
    action_primary_bg="#0F7A3A",
    action_primary_text="#FFFFFF",
    status_success_text="#006B32",
    status_error_text="#B00020",
)

DARK_THEME = DARK
LIGHT_THEME = LIGHT

THEMES: Final[dict[str, Theme]] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def ansi_fg(hex_color: str) -> str:
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
