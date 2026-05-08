"""Slash command catalog helpers shared by app adapters.

Mirrors Codex's focused `slash_command` module: this module describes command
names/help text, while TUI and shell adapters decide how to render or apply them.
"""

from __future__ import annotations

from dataclasses import dataclass

from hephaistos.tui.slash_completion import SlashCompletionEngine


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str
    aliases: tuple[str, ...] = ()


def _command_registry_suggestions() -> list[CommandSuggestion]:
    from hephaistos.commands import get_registry

    return [
        CommandSuggestion(
            name=suggestion.name,
            description=suggestion.description,
            aliases=suggestion.aliases,
        )
        for suggestion in get_registry().suggestions()
    ]


def tui_command_suggestions() -> list[CommandSuggestion]:
    suggestions = _command_registry_suggestions()
    suggestions.append(
        CommandSuggestion(
            name="sources",
            description="List or fuzzy-filter material files",
        )
    )
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
    max_name = max(len(s.name) for s in suggestions)
    lines: list[str] = []
    for suggestion in sorted(suggestions, key=lambda s: s.name):
        padded = f"  /{suggestion.name}".ljust(max_name + 4)
        lines.append(f"{padded} {suggestion.description}")
    return "\n".join(lines)
