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
    """Semantic colour roles consumed by UI components."""

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

    status_error_text: str


DARK = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised="#1C1C1C",
    text_primary="#E0E0E0",
    text_secondary="#D4C6A5",
    text_muted="#858585",
    text_inverse="#000000",
    border_subtle="#555555",
    brand_primary="#E06666",
    action_primary_bg="#7F9A6A",
    action_primary_text="#000000",
    status_error_text="#E06666",
)

LIGHT = Theme(
    bg_app="#f8f9fa",
    bg_surface="#ffffff",
    bg_raised="#ffffff",
    text_primary="#212529",
    text_secondary="#495057",
    text_muted="#868e96",
    text_inverse="#ffffff",
    border_subtle="#dee2e6",
    brand_primary="#e03131",
    action_primary_bg="#228be6",
    action_primary_text="#ffffff",
    status_error_text="#e03131",
)

HIGH_CONTRAST = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised="#1A1A1A",
    text_primary="#FFFFFF",
    text_secondary="#C0C0C0",
    text_muted="#C0C0C0",
    text_inverse="#000000",
    border_subtle="#8A8A8A",
    brand_primary="#FF4D4D",
    action_primary_bg="#FFD400",
    action_primary_text="#000000",
    status_error_text="#FF4D4D",
)

FORGE_THEME = DARK
LIGHT_THEME = LIGHT
HIGH_CONTRAST_THEME = HIGH_CONTRAST

THEMES: Final[dict[str, Theme]] = {
    "forge": FORGE_THEME,
    "light": LIGHT_THEME,
    "high_contrast": HIGH_CONTRAST_THEME,
}


def ansi_fg(hex_color: str) -> str:
    """Return a truecolor ANSI foreground sequence for a hex color."""
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
