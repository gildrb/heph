"""ANSI terminal helpers: styling, prompt rendering."""

from __future__ import annotations

import os
import re
import sys

from hephaistos.app import palette
from hephaistos.app.palette import (
    BOLD,
    FORGE_EMBER,
    RESET,
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_ERROR,
    STYLE_PROMPT,
    STYLE_WARNING,
    ansi_fg,
)

STYLE_ASSISTANT = palette.STYLE_ASSISTANT


def styled(text: str, style: str) -> str:
    return f"{style}{text}{RESET}"


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(text: str) -> int:
    """Return the visible (non-ANSI) character count of a string."""
    return len(_ANSI_RE.sub("", text))


def print_error(msg: str) -> None:
    print(f"{styled('error:', STYLE_ERROR)} {msg}")


def print_info(msg: str) -> None:
    print(f"{styled('info:', STYLE_DIM)} {msg}")


def print_success(msg: str) -> None:
    print(f"{styled(msg, STYLE_ACCENT)}")


_BANNER = r"""
    __  __           __          _      __
   / / / /__  ____  / /_  ____ _(_)____/ /_____  _____
  / /_/ / _ \/ __ \/ __ \/ __ `/ / ___/ __/ __ \/ ___/
 / __  /  __/ /_/ / / / / /_/ / (__  ) /_/ /_/ (__  )
/_/ /_/\___/ .___/_/ /_/\__,_/_/____/\__/\____/____/
          /_/
""".strip()


def print_banner(version: str = "") -> None:
    """Print the Hephaistos ASCII art banner centered across the terminal."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    lines = _BANNER.split("\n")
    banner_width = max(visible_len(line) for line in lines)
    pad = max(0, (cols - banner_width) // 2)
    for line in lines:
        sys.stdout.write(f"{' ' * pad}{BOLD}{ansi_fg(FORGE_EMBER)}{line}{RESET}\n")
    if version:
        ver_text = f"v{version}"
        ver_pad = max(0, (cols - len(ver_text)) // 2)
        sys.stdout.write(f"\n{' ' * ver_pad}{styled(ver_text, STYLE_DIM)}\n")
    sys.stdout.write("\n")


def _center_line(text: str, width: int = 80) -> str:
    """Center a line of text (accounting for ANSI escape codes)."""
    vis = visible_len(text)
    pad = max(0, (width - vis) // 2)
    return f"{' ' * pad}{text}"


def print_shell_intro(
    version: str,
    armory_path: str,
    source_file_count: int,
    model: str,
    has_api_key: bool,
) -> None:
    """Print the full startup screen with banner, status, and tips."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80

    print_banner(version)

    armory_status = styled(armory_path, STYLE_ACCENT)
    api_status = (
        styled("configured", STYLE_ACCENT)
        if has_api_key
        else styled("not configured", STYLE_ERROR)
    )
    model_display = styled(model, STYLE_PROMPT)

    status = (
        f"{styled('armory', STYLE_DIM)} {armory_status}"
        f"    {styled('model', STYLE_DIM)} {model_display}"
        f"    {styled('api', STYLE_DIM)} {api_status}"
    )
    if source_file_count:
        status += (
            f"    {styled('context', STYLE_DIM)}"
            f" {styled(f'{source_file_count} files', STYLE_ACCENT)}"
        )
    print(_center_line(status, cols))
    print()

    tips = [
        (
            f"Type {styled('/help', STYLE_ACCENT)} for commands"
            f"  \u00b7  {styled('/armory', STYLE_ACCENT)} to switch workspace"
            f"  \u00b7  {styled('!', STYLE_ACCENT)} prefix for shell mode"
        ),
    ]
    if not has_api_key:
        tips.insert(
            0,
            f"{styled('Set your API key:', STYLE_WARNING)}"
            f" {styled('/api key <your-key>', STYLE_ACCENT)}",
        )

    for tip in tips:
        print(_center_line(tip, cols))

    print()
