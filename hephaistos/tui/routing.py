"""Input routing rules for the Textual adapter.

This keeps command classification out of widget event handlers so the CLI command
surface remains the source of behavior and the TUI only chooses presentation.
"""

from __future__ import annotations

from enum import Enum

TERMINAL_INTERACTIVE_COMMANDS = {
    "edit",
    "login",
    "logout",
    "persona",
    "settings",
    "vocab",
}


class TuiInputRoute(Enum):
    EMPTY = "empty"
    MATERIALS = "materials"
    SESSIONS = "sessions"
    NEW = "new"
    ARMORY = "armory"
    EXTERNAL = "external"
    CHAT = "chat"


def pending_input_requires_terminal(value: str) -> bool:
    """Return True when a shared slash command should own the real terminal."""
    stripped = value.strip()
    if not stripped.startswith("/"):
        return False

    command, _, args = stripped[1:].partition(" ")
    command_name = command.lower()
    arg_text = args.strip()

    if command_name in {"login", "logout", "settings"}:
        return False
    if command_name == "memory":
        return arg_text.lower().startswith("setup")
    if command_name == "persona":
        return not arg_text
    if command_name == "vocab":
        return arg_text.lower() != "status"

    return command_name in TERMINAL_INTERACTIVE_COMMANDS


def is_armory_command(value: str) -> bool:
    """Return True when *value* is a /armory command handled inline by the TUI."""
    stripped = value.strip().lower()
    return stripped == "/armory" or stripped.startswith("/armory ")


def is_sessions_command(value: str) -> bool:
    """Return True when *value* is a saved-session command handled inline."""
    stripped = value.strip().lower()
    return stripped == "/sessions" or stripped.startswith("/sessions ")


def tui_input_route(value: str) -> TuiInputRoute:
    """Classify submitted TUI input before dispatching side effects."""
    stripped = value.strip()
    if not stripped:
        return TuiInputRoute.EMPTY
    if stripped == "/materials" or stripped.startswith("/materials "):
        return TuiInputRoute.MATERIALS
    if is_sessions_command(stripped):
        return TuiInputRoute.SESSIONS
    if stripped == "/new":
        return TuiInputRoute.NEW
    if is_armory_command(stripped):
        return TuiInputRoute.ARMORY
    if stripped.startswith(("/", "!")):
        return TuiInputRoute.EXTERNAL
    return TuiInputRoute.CHAT
