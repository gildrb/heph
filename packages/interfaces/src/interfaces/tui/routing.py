"""Input routing rules for the Textual adapter.

This keeps command classification out of widget event handlers so the CLI command
surface remains the source of behavior and the TUI only chooses presentation.
"""

from __future__ import annotations

from enum import Enum

TERMINAL_INTERACTIVE_COMMANDS = {
    "vocabulary",
}

_LOCAL_COMMAND_ACTIONS = {"search", "install", "status", "revalidate", "stop"}


class TuiInputRoute(Enum):
    EMPTY = "empty"
    HELP = "help"
    MATERIALS = "materials"
    KEYMAP = "keymap"
    SESSIONS = "sessions"
    TURN = "turn"
    LOCAL = "local"
    NEW = "new"
    DETACH = "detach"
    ARMORY = "armory"
    LIVE_TOKENS = "live_tokens"
    LIVE_COST = "live_cost"
    THINKING_VISIBILITY = "thinking_visibility"
    EXTERNAL = "external"
    CHAT = "chat"


_INLINE_ROUTES = {
    "?": TuiInputRoute.HELP,
    "h": TuiInputRoute.HELP,
    "help": TuiInputRoute.HELP,
    "materials": TuiInputRoute.MATERIALS,
    "keymap": TuiInputRoute.KEYMAP,
    "sessions": TuiInputRoute.SESSIONS,
    "turn": TuiInputRoute.TURN,
    "local": TuiInputRoute.LOCAL,
    "armory": TuiInputRoute.ARMORY,
    "tokens": TuiInputRoute.LIVE_TOKENS,
    "cost": TuiInputRoute.LIVE_COST,
    "thinking": TuiInputRoute.THINKING_VISIBILITY,
    "reasoning": TuiInputRoute.THINKING_VISIBILITY,
}


def pending_input_requires_terminal(value: str) -> bool:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return False

    command, _, args = stripped[1:].partition(" ")
    command_name = command.lower()
    arg_text = args.strip()

    if command_name in {"login", "logout", "settings", "tokens", "cost", "thinking", "reasoning"}:
        return False
    if command_name == "vocabulary":
        return arg_text.lower() != "status"

    return command_name in TERMINAL_INTERACTIVE_COMMANDS


def local_picker_query(value: str) -> str | None:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return None

    command, _, args = stripped[1:].partition(" ")
    if command.lower() != "local":
        return None

    action, remainder = _split_local_args(args)
    if action == "search":
        return remainder
    if action == "install" and not remainder:
        return ""
    return None


def local_install_target(value: str) -> str | None:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return None

    command, _, args = stripped[1:].partition(" ")
    if command.lower() != "local":
        return None

    action, remainder = _split_local_args(args)
    if action == "install" and remainder:
        return remainder
    return None


def _split_local_args(args: str) -> tuple[str, str]:
    command, separator, remainder = args.strip().partition(" ")
    if separator and command in _LOCAL_COMMAND_ACTIONS:
        return command, remainder.strip()
    if command in _LOCAL_COMMAND_ACTIONS:
        return command, ""
    return "search", args.strip()


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
