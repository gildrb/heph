"""Memory slash command."""

from __future__ import annotations

from commands._base import Command, CommandResult, ensure_session


class MemoryCommand(Command):
    name = "memory"
    description = "Show local armory memory status"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        subcommand = args.strip().lower() or "status"
        if subcommand != "status":
            print("Usage: /memory [status]")
            return CommandResult()
        backend = "armory-local" if s.armory_path is not None else "session-local"
        entries = len(s.memory.entries) if s.memory is not None else 0
        print(f"Backend: {backend}")
        print(f"Entries: {entries}")
        return CommandResult()
