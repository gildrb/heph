"""Memory slash command."""

from __future__ import annotations

from heph.commands._base import Command, CommandResult, ensure_session
from heph.commands.terminal_text import terminal_safe_text
from hephaion.memory import MemoryEntry


def _format_memory_entry(entry: MemoryEntry) -> str:
    source = f" ({terminal_safe_text(entry.source)})" if entry.source else ""
    return (
        f"- [{terminal_safe_text(entry.confidence)}] "
        f"{terminal_safe_text(entry.topic)}: {terminal_safe_text(entry.content)}{source}"
    )


class MemoryCommand(Command):
    name = "memory"
    description = "Show saved armory memory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        subcommand = args.strip().lower() or "status"
        if subcommand != "status":
            print("Usage: /memory [status]")
            return CommandResult()
        if s.memory is None or not s.memory.entries:
            print("No saved memory yet.")
            return CommandResult()
        print("Saved memory:")
        for entry in s.memory.entries:
            print(_format_memory_entry(entry))
        return CommandResult()
