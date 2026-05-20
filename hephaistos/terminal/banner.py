"""Hephaistos brand assets: ASCII logo, wordmark, separator rules."""

from __future__ import annotations

from hephaistos.terminal import RESET, STYLE_BRAND, STYLE_DIM, ansi_fg, current_palette

_ASCII_LOGO = (
    "@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@@\n"
    "@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@@\n"
    "@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@@\n"
    "@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@@\n"
    "@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@@\n"
    "@@@@@@@@@@@@@@@@             @@@@@@@"
)


def ascii_logo() -> str:
    return f"{STYLE_BRAND}{_ASCII_LOGO}{RESET}"


def wordmark() -> str:
    spark = "\u2301"
    brand = current_palette().brand_primary
    dim = current_palette().text_muted
    return f"{ansi_fg(brand)}{spark} Hephaistos{ansi_fg(dim)}"


def separator_line(width: int = 40) -> str:
    line = "\u2500" * width
    return f"{STYLE_DIM}{line}{RESET}"
