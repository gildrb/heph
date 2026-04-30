"""Base classes and helpers for slash commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from hephaistos.chat.compaction import compact_session
from hephaistos.chat.session import ChatSession

if TYPE_CHECKING:
    from hephaistos.app.commands import CommandRegistry


class CommandResult:
    __slots__ = ("new_session", "output", "should_exit")

    def __init__(
        self,
        output: str | None = None,
        should_exit: bool = False,
        new_session: ChatSession | None = None,
    ) -> None:
        self.output = output
        self.should_exit = should_exit
        self.new_session = new_session


class Command:
    """Base class for slash commands. Subclasses set class-level attributes."""

    name: str = ""
    description: str = ""
    aliases: tuple[str, ...] = ()
    hidden: bool = False

    def handle(self, session: object, args: str) -> CommandResult:
        raise NotImplementedError


# Lazy registry accessor — avoids circular imports between __init__.py and
# sub-modules that need to enumerate commands (e.g. HelpCommand).
_registry_fn: Callable[[], CommandRegistry] | None = None


def set_registry_fn(fn: Callable[[], CommandRegistry]) -> None:
    global _registry_fn  # noqa: PLW0603
    _registry_fn = fn


def get_registry_lazy() -> CommandRegistry:
    """Return the CommandRegistry by calling the lazy getter set by __init__.py."""
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
    """Return a percentage string like '42%'."""
    if total == 0:
        return "0%"
    return f"{part * 100 // total}%"


def do_compact(session: ChatSession) -> None:
    """Run the compact logic: summarize conversation and replace messages."""
    compact_session(session)
