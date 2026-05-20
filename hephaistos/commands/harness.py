"""Slash-command parsing and execution harness.

The harness is intentionally separate from the TUI. It turns raw slash input into
an invocation and executes it against the command registry. Presentation of
unknown commands remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from hephaistos.commands import get_registry

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


class CommandResultLike(Protocol):
    output: str | None
    should_exit: bool
    new_session: ChatSession | None


@dataclass(frozen=True, slots=True)
class SlashCommandInvocation:
    raw: str
    name: str
    args: str


@dataclass(frozen=True, slots=True)
class SlashCommandDispatch:
    found: bool
    result: CommandResultLike | None
    invocation: SlashCommandInvocation


def parse_slash_command(value: str) -> SlashCommandInvocation:
    stripped = value.strip()
    if not stripped.startswith("/"):
        raise ValueError("slash command must start with '/'")
    if stripped == "/":
        return SlashCommandInvocation(raw=stripped, name="help", args="")

    space_idx = stripped.find(" ")
    if space_idx == -1:
        return SlashCommandInvocation(raw=stripped, name=stripped[1:].lower(), args="")
    return SlashCommandInvocation(
        raw=stripped,
        name=stripped[1:space_idx].lower(),
        args=stripped[space_idx + 1 :].strip(),
    )


def dispatch_slash_command(session: object, value: str) -> SlashCommandDispatch:
    invocation = parse_slash_command(value)
    registry = get_registry()
    cmd = registry.find(invocation.name)
    if cmd is None:
        return SlashCommandDispatch(False, None, invocation)
    return SlashCommandDispatch(True, cmd.handle(session, invocation.args), invocation)
