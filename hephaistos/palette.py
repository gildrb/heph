"""Low-level ANSI primitives shared by UI and infra layers.

This module exists so that ``hephaistos.logging`` (an infra module) can
use terminal colour helpers without importing from the ``app`` package.
Higher-level style composites live in ``hephaistos.app.palette``.
"""

from __future__ import annotations

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

FORGE_PANEL = "#1C1C1C"
FORGE_STONE = "#555555"
FORGE_ASH = "#E0E0E0"
FORGE_SMOKE = "#808080"
FORGE_EMBER = "#C8C8C8"
FORGE_IRON = "#CC3333"
FORGE_GREEN = "#66BB6A"


def ansi_fg(hex_color: str) -> str:
    """Return a truecolor ANSI foreground sequence for a hex color."""
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
