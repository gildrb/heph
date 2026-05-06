"""Keyboard shortcut helpers for the Textual TUI."""

from __future__ import annotations

import os
import subprocess  # nosec B404
from functools import lru_cache

_ARMORY_SHORTCUT = "ctrl+a"
_ARMORY_TMUX_FALLBACK_SHORTCUT = "ctrl+o"
_CTRL_A_TMUX_PREFIXES = frozenset({"C-a", "^A", "ctrl+a", "Ctrl-A", "CTRL+A"})
_TMUX_PREFIX_TIMEOUT_SECONDS = 0.2


def armory_binding_keys() -> str:
    """Return all keys that should open the armory browser."""
    return f"{_ARMORY_SHORTCUT},{_ARMORY_TMUX_FALLBACK_SHORTCUT}"


@lru_cache(maxsize=1)
def tmux_uses_ctrl_a_prefix() -> bool:
    """Return True when tmux will consume the first physical ctrl+a press."""
    if not os.environ.get("TMUX"):
        return False
    try:
        result = subprocess.run(  # nosec B603 B607
            ("tmux", "show-options", "-gqv", "prefix"),
            capture_output=True,
            check=False,
            text=True,
            timeout=_TMUX_PREFIX_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    return result.stdout.strip() in _CTRL_A_TMUX_PREFIXES


def armory_shortcut_key() -> str:
    """Return the armory shortcut to show for this terminal session."""
    if tmux_uses_ctrl_a_prefix():
        return _ARMORY_TMUX_FALLBACK_SHORTCUT
    return _ARMORY_SHORTCUT
