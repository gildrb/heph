from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str
    aliases: tuple[str, ...] = ()


class CommandSuggestionLike(Protocol):
    name: str
    description: str
    aliases: tuple[str, ...]


class CommandResult(Protocol):
    should_exit: bool
    output: str | None
    new_session: ChatSession | None


class Command(Protocol):
    name: str
    aliases: tuple[str, ...]

    def handle(self, session: object, args: str) -> CommandResult: ...


class CommandRegistry(Protocol):
    def find(self, name: str) -> Command | None: ...

    def suggestions(self) -> Sequence[CommandSuggestionLike]: ...


_registry_fn: Callable[[], CommandRegistry] | None = None


def set_command_registry_fn(fn: Callable[[], CommandRegistry]) -> None:
    global _registry_fn  # noqa: PLW0603
    _registry_fn = fn


def get_registry() -> CommandRegistry:
    if _registry_fn is None:
        raise RuntimeError("TUI command registry has not been configured")
    return _registry_fn()
