"""Input routing rules for the Textual adapter.

This keeps command classification out of widget event handlers so the CLI command
surface remains the source of behavior and the TUI only chooses presentation.
"""

from __future__ import annotations

from enum import Enum

TERMINAL_INTERACTIVE_COMMANDS = {
    "local",
    "vocabulary",
}


class TuiInputRoute(Enum):
    EMPTY = "empty"
    MATERIALS = "materials"
    SESSIONS = "sessions"
    TURN = "turn"
    NEW = "new"
    DETACH = "detach"
    ARMORY = "armory"
    EXTERNAL = "external"
    CHAT = "chat"


_INLINE_ROUTES = {
    "materials": TuiInputRoute.MATERIALS,
    "sessions": TuiInputRoute.SESSIONS,
    "turn": TuiInputRoute.TURN,
    "armory": TuiInputRoute.ARMORY,
}


def pending_input_requires_terminal(value: str) -> bool:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return False

    command, _, args = stripped[1:].partition(" ")
    command_name = command.lower()
    arg_text = args.strip()

    if command_name in {"login", "logout", "settings"}:
        return False
    if command_name == "local":
        return arg_text.lower() not in {"status", "stop"}
    if command_name == "vocabulary":
        return arg_text.lower() != "status"

    return command_name in TERMINAL_INTERACTIVE_COMMANDS


def is_armory_command(value: str) -> bool:
    stripped = value.strip().lower()
    return stripped == "/armory" or stripped.startswith("/armory ")


def tui_input_route(value: str) -> TuiInputRoute:
    stripped = value.strip()
    if not stripped:
        return TuiInputRoute.EMPTY
    if not stripped.startswith("/"):
        return TuiInputRoute.CHAT

    command = stripped[1:].partition(" ")[0].lower()
    if command == "new" and stripped == "/new":
        return TuiInputRoute.NEW
    if command == "detach" and stripped == "/detach":
        return TuiInputRoute.DETACH
    return _INLINE_ROUTES.get(command, TuiInputRoute.EXTERNAL)
