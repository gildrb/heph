"""Shared forge-inspired palette for Hephaistos terminal surfaces."""

from __future__ import annotations

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

FORGE_PANEL = "#261112"
FORGE_ASH = "#F4DED8"
FORGE_SMOKE = "#B8948D"
FORGE_EMBER = "#D94A2B"
FORGE_IRON = "#8E241E"


def ansi_fg(hex_color: str) -> str:
    """Return a truecolor ANSI foreground sequence for a hex color."""
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


STYLE_PROMPT = f"{BOLD}{ansi_fg(FORGE_EMBER)}"
STYLE_ACCENT = STYLE_PROMPT
STYLE_DIM = f"{DIM}{ansi_fg(FORGE_SMOKE)}"
STYLE_ERROR = f"{BOLD}{ansi_fg(FORGE_IRON)}"
STYLE_WARNING = STYLE_PROMPT
STYLE_ASSISTANT = STYLE_PROMPT
