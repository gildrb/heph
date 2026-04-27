"""Hephaistos brand assets: ASCII logo, wordmark, separator rules."""

from __future__ import annotations

from hephaistos.app.palette import RESET, STYLE_DIM, STYLE_EMBER, ansi_fg, current_palette

_ASCII_LOGO_SMALL = (
    "  @@@@@@@@@@@@            @@@@@@@@@@@@\n"
    "  @@@@@@@@@@@@            @@@@@@@@@@@@\n"
    "  @@@@@@@@@@@@            @@@@@@@@@@@@\n"
    "  @@@@@@@@@@@@            @@@@@@@@@@@@\n"
    "  @@@@@@@@@@@            @@@@@@@@@@@\n"
    "   @@@@@@@@@            @@@@@@@@@\n"
    "    @@@@@@@              @@@@@@@\n"
    "      @@@@                @@@@"
)


def ascii_logo(*, color: bool = True) -> str:
    """Return the Hephaistos ASCII logo.

    When *color* is True, the logo is rendered in ember color.
    """
    logo = _ASCII_LOGO_SMALL
    if not color:
        return logo
    return f"{STYLE_EMBER}{logo}{RESET}"


def wordmark(*, color: bool = True) -> str:
    """Return the inline wordmark: forge-mark glyph + name.

    Uses the ⌁ (spark) dingbat as a compact inline logo substitute.
    """
    spark = "\u2301"
    if color:
        ember = current_palette().ember
        dim = current_palette().dim
        return f"{ansi_fg(ember)}{spark} Hephaistos{ansi_fg(dim)}"
    return f"{spark} Hephaistos"


def separator_line(width: int = 40, *, color: bool = True) -> str:
    """Return a horizontal separator line using straight horizontal chars."""
    line = "\u2500" * width
    if not color:
        return line
    return f"{STYLE_DIM}{line}{RESET}"
