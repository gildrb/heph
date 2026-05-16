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

BLACK = "#000000"
WHITE = "#FFFFFF"
TRANSPARENT = "transparent"
RICH_BLACK_COLOR_NAME = "black"
BLACK_RGB: Final[tuple[int, int, int]] = (0, 0, 0)

# Raw palette tokens. Concrete colours live here; semantic themes map them into
# roles that components consume.
FORGE_BG_RAISED = "#1C1C1C"
FORGE_TEXT_PRIMARY = "#E0E0E0"
FORGE_TEXT_SECONDARY = "#D4C6A5"
FORGE_TEXT_MUTED = "#858585"
FORGE_BORDER_SUBTLE = "#555555"
FORGE_ACTION_PRIMARY_BG = "#7F9A6A"
FORGE_ACTION_PRIMARY_TEXT = BLACK
FORGE_STATUS_ERROR_TEXT = "#E06666"

LIGHT_BG_RAISED = "#EDE8DC"
LIGHT_TEXT_PRIMARY = "#2C241B"
LIGHT_TEXT_SECONDARY = "#7D4F4F"
LIGHT_TEXT_MUTED = "#6A615A"
LIGHT_BORDER_SUBTLE = "#C4B8A6"
LIGHT_ACTION_PRIMARY_BG = "#526837"
LIGHT_ACTION_PRIMARY_TEXT = WHITE
LIGHT_STATUS_ERROR_TEXT = "#B03A2E"

HIGH_CONTRAST_BG_RAISED = "#1A1A1A"
HIGH_CONTRAST_TEXT_PRIMARY = WHITE
HIGH_CONTRAST_TEXT_SECONDARY = "#C0C0C0"
HIGH_CONTRAST_TEXT_MUTED = "#C0C0C0"
HIGH_CONTRAST_BORDER_SUBTLE = "#8A8A8A"
HIGH_CONTRAST_ACTION_PRIMARY_BG = "#FFD400"
HIGH_CONTRAST_ACTION_PRIMARY_TEXT = BLACK
HIGH_CONTRAST_STATUS_ERROR_TEXT = "#FF4D4D"


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

    action_primary_bg: str
    action_primary_text: str

    status_error_text: str


FORGE_THEME = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised=FORGE_BG_RAISED,
    text_primary=FORGE_TEXT_PRIMARY,
    text_secondary=FORGE_TEXT_SECONDARY,
    text_muted=FORGE_TEXT_MUTED,
    text_inverse=BLACK,
    border_subtle=FORGE_BORDER_SUBTLE,
    action_primary_bg=FORGE_ACTION_PRIMARY_BG,
    action_primary_text=FORGE_ACTION_PRIMARY_TEXT,
    status_error_text=FORGE_STATUS_ERROR_TEXT,
)

LIGHT_THEME = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised=LIGHT_BG_RAISED,
    text_primary=LIGHT_TEXT_PRIMARY,
    text_secondary=LIGHT_TEXT_SECONDARY,
    text_muted=LIGHT_TEXT_MUTED,
    text_inverse=BLACK,
    border_subtle=LIGHT_BORDER_SUBTLE,
    action_primary_bg=LIGHT_ACTION_PRIMARY_BG,
    action_primary_text=LIGHT_ACTION_PRIMARY_TEXT,
    status_error_text=LIGHT_STATUS_ERROR_TEXT,
)

HIGH_CONTRAST_THEME = Theme(
    bg_app=TRANSPARENT,
    bg_surface=TRANSPARENT,
    bg_raised=HIGH_CONTRAST_BG_RAISED,
    text_primary=HIGH_CONTRAST_TEXT_PRIMARY,
    text_secondary=HIGH_CONTRAST_TEXT_SECONDARY,
    text_muted=HIGH_CONTRAST_TEXT_MUTED,
    text_inverse=BLACK,
    border_subtle=HIGH_CONTRAST_BORDER_SUBTLE,
    action_primary_bg=HIGH_CONTRAST_ACTION_PRIMARY_BG,
    action_primary_text=HIGH_CONTRAST_ACTION_PRIMARY_TEXT,
    status_error_text=HIGH_CONTRAST_STATUS_ERROR_TEXT,
)

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
