"""Shared forge-inspired palette for Hephaistos terminal surfaces."""

from __future__ import annotations

BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
RESET = "\033[0m"

FORGE_COAL = "#17120F"
FORGE_PANEL = "#241B16"
FORGE_PANEL_RAISED = "#2D221C"
FORGE_ASH = "#F0DFC8"
FORGE_SMOKE = "#9C8B7E"
FORGE_COPPER = "#B9652A"
FORGE_EMBER = "#E66B1E"
FORGE_BRASS = "#D8A24A"
FORGE_SPARK = "#F0C36C"
FORGE_IRON = "#C2492E"


def ansi_fg(hex_color: str) -> str:
    """Return a truecolor ANSI foreground sequence for a hex color."""
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


STYLE_PROMPT = f"{BOLD}{ansi_fg(FORGE_EMBER)}"
STYLE_ACCENT = f"{BOLD}{ansi_fg(FORGE_BRASS)}"
STYLE_DIM = f"{DIM}{ansi_fg(FORGE_SMOKE)}"
STYLE_ERROR = f"{BOLD}{ansi_fg(FORGE_IRON)}"
STYLE_WARNING = f"{BOLD}{ansi_fg(FORGE_SPARK)}"
STYLE_MODE = f"{BOLD}{ansi_fg(FORGE_COPPER)}"
STYLE_ASSISTANT = f"{BOLD}{ansi_fg(FORGE_EMBER)}"
