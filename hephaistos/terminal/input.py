"""Slash-command dispatch used when the TUI parks for terminal prompts."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from hephaistos.terminal import (
    print_error,
    print_info,
)
from hephaistos.terminal.history import InputHistory

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


class CommandResultProtocol(Protocol):
    should_exit: bool
    new_session: ChatSession | None
    output: str | None


class CommandProtocol(Protocol):
    def handle(self, session: object, args: str) -> CommandResultProtocol: ...


class CommandRegistryProtocol(Protocol):
    def find(self, name: str) -> CommandProtocol | None: ...


_command_registry_fn: Callable[[], CommandRegistryProtocol] | None = None


def set_command_registry_fn(fn: Callable[[], CommandRegistryProtocol]) -> None:
    global _command_registry_fn  # noqa: PLW0603
    _command_registry_fn = fn


def _get_command_registry() -> CommandRegistryProtocol:
    if _command_registry_fn is None:
        msg = "Command registry not initialized"
        raise RuntimeError(msg)
    return _command_registry_fn()


def handle_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
) -> tuple[ChatSession, bool]:
    if not user_input.strip():
        return session, True
    if not user_input.startswith("/"):
        return session, True

    history.add(user_input)
    stripped = user_input.strip()
    if stripped == "/":
        registry = _get_command_registry()
        cmd = registry.find("help")
        if cmd:
            cmd.handle(session, "")
        return session, True
    cmd_name, _, cmd_args = stripped[1:].partition(" ")
    cmd_name = cmd_name.lower()
    cmd_args = cmd_args.strip()

    registry = _get_command_registry()
    cmd = registry.find(cmd_name)
    if cmd is None:
        print_error(f"Unknown command: {stripped}")
        print_info("Type /help for available commands.")
        return session, True

    result = cmd.handle(session, cmd_args)
    if result.should_exit:
        return session, False
    if result.new_session is not None:
        session = result.new_session
    if result.output and not result.output.startswith("__RESEND__:"):
        print(result.output)
    if result.output and result.output.startswith("__RESEND__:"):
        new_input = result.output[len("__RESEND__:") :]
        history.add(new_input)
    return session, True
