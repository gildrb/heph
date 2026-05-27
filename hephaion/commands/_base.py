"""Base classes and helpers for slash commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from hephaion.chat.session import ChatSession


class CommandRegistryProtocol(Protocol):
    commands: list[Command]

    def find(self, name: str) -> Command | None: ...

    def suggestions(self) -> object: ...


@dataclass(slots=True)
class CommandResult:
    output: str | None = None
    should_exit: bool = False
    new_session: ChatSession | None = None


class Command:
    name: str = ""
    description: str = ""
    aliases: tuple[str, ...] = ()

    def handle(self, session: object, args: str) -> CommandResult:
        raise NotImplementedError


# Lazy registry accessor — avoids circular imports between __init__.py and
# sub-modules that need to enumerate commands (e.g. HelpCommand).
_registry_fn: Callable[[], CommandRegistryProtocol] | None = None


def set_registry_fn(fn: Callable[[], CommandRegistryProtocol]) -> None:
    global _registry_fn  # noqa: PLW0603
    _registry_fn = fn


def get_registry_lazy() -> CommandRegistryProtocol:
    if _registry_fn is None:
        msg = "Registry not initialized — call set_registry_fn first"
        raise RuntimeError(msg)
    return _registry_fn()


def ensure_session(session: object) -> ChatSession:
    if not isinstance(session, ChatSession):
        raise TypeError(f"Expected ChatSession, got {type(session).__name__}")
    return session


def format_duration(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minute}m {sec}s"
    if minute:
        return f"{minute}m {sec}s"
    return f"{sec}s"


def pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{part * 100 // total}%"
