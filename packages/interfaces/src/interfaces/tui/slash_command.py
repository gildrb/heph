"""Slash command catalog helpers shared by app adapters.

Mirrors Codex's focused `slash_command` module: this module describes command
names/help text, while adapters decide how to render or apply them.
"""

from __future__ import annotations

from typing import Final

from interfaces.tui.command_access import CommandSuggestion, get_registry
from interfaces.tui.slash_completion import SlashCompletionEngine

_COMMAND_HELP_GAP = 4

TUI_ONLY_COMMAND_SUGGESTIONS: Final[tuple[CommandSuggestion, ...]] = (
    CommandSuggestion(
        name="materials",
        description="Choose which materials are used for retrieval",
    ),
    CommandSuggestion(
        name="keymap",
        description="Edit keyboard shortcuts",
    ),
)


def tui_command_suggestions() -> list[CommandSuggestion]:
    suggestions = [
        CommandSuggestion(
            name=suggestion.name,
            description=suggestion.description,
            aliases=suggestion.aliases,
        )
        for suggestion in get_registry().suggestions()
    ]
    suggestions.extend(TUI_ONLY_COMMAND_SUGGESTIONS)
    return suggestions


def slash_suggestion(engine: SlashCompletionEngine, value: str) -> str | None:
    return engine.suggestion(value, tui_command_suggestions())


def command_help() -> str:
    suggestions = tui_command_suggestions()
    label_width = max((len(f"/{suggestion.name}") for suggestion in suggestions), default=0)
    gap = " " * _COMMAND_HELP_GAP
    lines = []
    for suggestion in sorted(suggestions, key=lambda s: s.name):
        label = f"/{suggestion.name}"
        lines.append(f"  {label:<{label_width}}{gap}{suggestion.description}")
    return "\n".join(lines)
