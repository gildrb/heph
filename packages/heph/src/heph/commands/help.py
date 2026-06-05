"""Help and exit commands."""

from __future__ import annotations

from heph_interfaces.terminal import STYLE_PROMPT, styled

from heph.commands._base import Command, CommandResult, get_registry_lazy

_HELP_ENTRY_GAP = 4

type _HelpEntry = tuple[str, str]


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"
    aliases = ("?", "h")

    def handle(self, session: object, args: str) -> CommandResult:
        del session, args
        registry = get_registry_lazy()
        command_entries = [
            (f"/{cmd.name}", cmd.description)
            for cmd in sorted(registry.commands, key=lambda c: c.name)
        ]
        input_entries = [("/help", "Show command reference")]
        shortcut_entries = [
            ("Up/Down", "Browse input history"),
            ("Tab", "Autocomplete slash commands"),
            ("Shift+Enter/Ctrl+J", "Insert newline"),
            ("Ctrl+C", "Exit Heph"),
            ("Ctrl+D", "Exit Heph"),
        ]
        label_width = _help_label_width(command_entries, input_entries, shortcut_entries)
        lines: list[str] = []
        lines.append(styled("Commands", STYLE_PROMPT))
        lines.extend(_format_help_entries(command_entries, label_width=label_width))
        lines.append("")
        lines.append(styled("Input", STYLE_PROMPT))
        lines.extend(_format_help_entries(input_entries, label_width=label_width))
        lines.append("")
        lines.append(styled("Shortcuts", STYLE_PROMPT))
        lines.extend(_format_help_entries(shortcut_entries, label_width=label_width))
        lines.append("")
        print("\n".join(lines))
        return CommandResult()


class ExitCommand(Command):
    name = "exit"
    description = "Leave Heph"
    aliases = ("quit", "q")

    def handle(self, session: object, args: str) -> CommandResult:
        del session, args
        return CommandResult(should_exit=True)


def _help_label_width(*groups: list[_HelpEntry]) -> int:
    return max((len(label) for group in groups for label, _description in group), default=0)


def _format_help_entries(entries: list[_HelpEntry], *, label_width: int) -> list[str]:
    gap = " " * _HELP_ENTRY_GAP
    return [f"  {label:<{label_width}}{gap}{description}" for label, description in entries]
