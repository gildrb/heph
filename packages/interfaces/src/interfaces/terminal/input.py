"""Slash-command dispatch used when the TUI parks for terminal prompts."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from interfaces.terminal import (
    print_error,
    print_info,
)
from interfaces.terminal.history import InputHistory

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class CommandResultProtocol(Protocol):
    should_exit: bool
    new_session: ChatSession | None
    output: str | None


class CommandProtocol(Protocol):
    def handle(self, session: object, args: str) -> CommandResultProtocol: ...


class CommandRegistryProtocol(Protocol):
    def find(self, name: str) -> CommandProtocol | None: ...


_command_registry_fn: Callable[[], CommandRegistryProtocol] | None = None
_RESEND_PREFIX = "__RESEND__:"


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
    stripped = user_input.strip()
    if not stripped or not user_input.startswith("/"):
        return session, True

    history.add(user_input)
    if stripped == "/":
        _show_help(session)
        return session, True

    registry = _get_command_registry()
    cmd_name, cmd_args = _parse_command(stripped)
    cmd = registry.find(cmd_name)
    if cmd is None:
        _print_unknown_command(stripped)
        return session, True

    result = cmd.handle(session, cmd_args)
    if result.should_exit:
        return session, False
    if result.new_session is not None:
        session = result.new_session
    _handle_command_output(result.output, history)
    return session, True


def _show_help(session: ChatSession) -> None:
    cmd = _get_command_registry().find("help")
    if cmd is not None:
        cmd.handle(session, "")


def _parse_command(stripped: str) -> tuple[str, str]:
    cmd_name, _, cmd_args = stripped[1:].partition(" ")
    return cmd_name.lower(), cmd_args.strip()


def _print_unknown_command(stripped: str) -> None:
    print_error(f"Unknown command: {stripped}")
    print_info("Type /help for available commands.")


def _handle_command_output(output: str | None, history: InputHistory) -> None:
    if not output:
        return
    if output.startswith(_RESEND_PREFIX):
        history.add(output[len(_RESEND_PREFIX) :])
        return
    print(output)
