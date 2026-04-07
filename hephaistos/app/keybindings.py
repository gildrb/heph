"""Configurable keybindings for the shell and menu.

All key identifiers follow prompt_toolkit key names (e.g. ``"c-c"``, ``"up"``,
``"enter"``).  Users can override any binding by constructing their own dict
and passing it through.
"""

from __future__ import annotations

DEFAULT_SHELL_KEYBINDINGS: dict[str, str | list[str]] = {
    "submit": "enter",
    "newline": "escape,enter",
    "cancel": "c-c",
    "exit": "c-d",
    "history_up": "up",
    "history_down": "down",
    "cursor_left": "left",
    "cursor_right": "right",
    "delete": "delete",
    "home": "c-a",
    "end": "c-e",
    "clear_line": "c-u",
    "kill_to_end": "c-k",
    "complete": "tab",
    "escape_guard": "escape",
}

DEFAULT_MENU_KEYBINDINGS: dict[str, str | list[str]] = {
    "navigate_up": "up",
    "navigate_down": "down",
    "select": "enter",
    "cancel": ["c-c", "escape"],
}
