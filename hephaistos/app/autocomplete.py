"""Slash command autocomplete suggestions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str


def match_commands(prefix: str, commands: list[CommandSuggestion]) -> list[CommandSuggestion]:
    """Return commands whose names start with the given prefix (after /), sorted alphabetically."""
    if not prefix.startswith("/"):
        return []
    search = prefix[1:].lower()
    matches = [cmd for cmd in commands if cmd.name.lower().startswith(search)]
    return sorted(matches, key=lambda c: c.name)


def format_suggestions(
    matches: list[CommandSuggestion],
    max_width: int = 80,
    selected: int = -1,
) -> list[str]:
    """Format matched commands into displayable suggestion lines."""
    if not matches:
        return []
    lines: list[str] = []
    for i, cmd in enumerate(matches):
        entry = f"  /{cmd.name}"
        if cmd.description:
            padded = entry.ljust(min(22, max_width - len(cmd.description) - 2))
            text = f"{padded} {cmd.description}"
        else:
            text = entry
        if i == selected:
            text = f"\033[7m{text}\033[0m"
        lines.append(text)
    return lines
