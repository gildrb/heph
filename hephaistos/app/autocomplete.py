"""Slash command autocomplete suggestions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str


def match_commands(prefix: str, commands: list[CommandSuggestion]) -> list[CommandSuggestion]:
    """Return commands whose names start with the given prefix (after /)."""
    if not prefix.startswith("/"):
        return []
    search = prefix[1:].lower()
    return [cmd for cmd in commands if cmd.name.lower().startswith(search)]


def format_suggestions(matches: list[CommandSuggestion], max_width: int = 80) -> list[str]:
    """Format matched commands into displayable suggestion lines."""
    if not matches:
        return []
    lines: list[str] = []
    for cmd in matches:
        entry = f"  /{cmd.name}"
        if cmd.description:
            # Pad to column 20 for alignment
            padded = entry.ljust(min(22, max_width - len(cmd.description) - 2))
            lines.append(f"{padded} {cmd.description}")
        else:
            lines.append(entry)
    return lines
