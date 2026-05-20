"""Slash command catalog helpers shared by app adapters.

Mirrors Codex's focused `slash_command` module: this module describes command
names/help text, while adapters decide how to render or apply them.
"""

from __future__ import annotations

from hephaistos.commands.suggestions import CommandSuggestion
from hephaistos.tui.slash_completion import SlashCompletionEngine


def tui_command_suggestions() -> list[CommandSuggestion]:
    from hephaistos.commands import get_registry

    suggestions = get_registry().suggestions()
    suggestions.append(
        CommandSuggestion(
            name="materials",
            description="Choose which materials are used for retrieval",
        )
    )
    return suggestions


def slash_suggestion(engine: SlashCompletionEngine, value: str) -> str | None:
    return engine.suggestion(value, tui_command_suggestions())


def command_help() -> str:
    suggestions = tui_command_suggestions()
    lines = [
        f"  /{suggestion.name}  {suggestion.description}"
        for suggestion in sorted(suggestions, key=lambda s: s.name)
    ]
    return "\n".join(lines)
