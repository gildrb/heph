"""Slash command catalog helpers shared by app adapters.

Mirrors Codex's focused `slash_command` module: this module describes command
names/help text, while TUI and shell adapters decide how to render or apply them.
"""

from __future__ import annotations

from hephaistos.commands import get_registry
from hephaistos.commands.suggestions import CommandSuggestion
from hephaistos.tui.slash_completion import SlashCompletionEngine


def tui_command_suggestions() -> list[CommandSuggestion]:
    suggestions = get_registry().suggestions()
    suggestions.append(
        CommandSuggestion(
            name="sources",
            description="List or fuzzy-filter material files",
        )
    )
    return suggestions


def slash_suggestion(engine: SlashCompletionEngine, value: str) -> str | None:
    return engine.suggestion(value, tui_command_suggestions())


def command_help() -> str:
    suggestions = tui_command_suggestions()
    max_name = max(len(s.name) for s in suggestions)
    lines: list[str] = []
    for suggestion in sorted(suggestions, key=lambda s: s.name):
        padded = f"  /{suggestion.name}".ljust(max_name + 4)
        lines.append(f"{padded} {suggestion.description}")
    return "\n".join(lines)
