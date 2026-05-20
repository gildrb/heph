"""Memory management command."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.terminal import (
    print_error,
)


class MemoryCommand(Command):
    name = "memory"
    description = "Manage local armory memory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "status"

        if subcmd == "status":
            return self._status(s)

        print_error("Usage: /memory [status]")
        return CommandResult()

    @staticmethod
    def _status(session: ChatSession) -> CommandResult:
        memory_backend = type(session.memory).__name__ if session.memory is not None else "none"
        mem_count = len(session.memory.entries) if session.memory else 0
        lines = [
            f"  Backend:     {memory_backend}",
            f"  Entries:     {mem_count}",
        ]
        print("\n".join(lines))
        return CommandResult()


__all__ = ["MemoryCommand"]
