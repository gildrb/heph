"""Slash command catalog helpers shared by app adapters.

Mirrors Codex's focused `slash_command` module: this module describes command
names/help text, while adapters decide how to render or apply them.
"""

from __future__ import annotations

from typing import Final

from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_cell_right
from interfaces.tui.command_access import CommandSuggestion, get_registry
from interfaces.tui.slash_completion import SlashCompletionEngine

_COMMAND_HELP_GAP = 4
_HELP_INPUT_ENTRIES: Final[tuple[tuple[str, str], ...]] = (("COMMAND", "/help"),)
_HELP_SHORTCUT_ENTRIES: Final[tuple[tuple[str, str], ...]] = (
    ("HISTORY", "up/down"),
    ("COMPLETE", "tab"),
    ("NEWLINE", "shift+enter/ctrl+j"),
    ("EXIT", "ctrl+c"),
    ("EXIT", "ctrl+d"),
)

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
    command_entries = [
        (f"/{suggestion.name}", suggestion.description)
        for suggestion in sorted(suggestions, key=lambda s: s.name)
    ]
    lines = []
    lines.append(_help_section("commands"))
    lines.extend(_format_help_entries(command_entries))
    lines.append("")
    lines.append(_help_section("input"))
    lines.extend(_format_help_entries(_HELP_INPUT_ENTRIES))
    lines.append("")
    lines.append(_help_section("shortcuts"))
    lines.extend(_format_help_entries(_HELP_SHORTCUT_ENTRIES))
    return "\n".join(lines)


def _help_section(label: str) -> str:
    return label.strip().upper()


def _format_help_entries(
    entries: tuple[tuple[str, str], ...] | list[tuple[str, str]],
) -> list[str]:
    label_width = max((_cell_width(label) for label, _value in entries), default=0)
    gap = " " * _COMMAND_HELP_GAP
    return [f"  {_pad_cell_right(label, label_width)}{gap}{value}" for label, value in entries]
