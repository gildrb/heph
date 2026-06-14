"""Help and exit commands."""

from __future__ import annotations

from interfaces.terminal import STYLE_PROMPT, styled, visible_len

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
        input_entries = [("COMMAND", "/help")]
        shortcut_entries = [
            ("HISTORY", "up/down"),
            ("COMPLETE", "tab"),
            ("NEWLINE", "shift+enter/ctrl+j"),
            ("EXIT", "ctrl+c"),
            ("EXIT", "ctrl+d"),
        ]
        lines: list[str] = []
        lines.append(_help_section("commands"))
        lines.extend(_format_help_entries(command_entries))
        lines.append("")
        lines.append(_help_section("input"))
        lines.extend(_format_help_entries(input_entries))
        lines.append("")
        lines.append(_help_section("shortcuts"))
        lines.extend(_format_help_entries(shortcut_entries))
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
    return max(
        (visible_len(label) for group in groups for label, _description in group),
        default=0,
    )


def _help_section(label: str) -> str:
    return styled(label.strip().upper(), STYLE_PROMPT)


def _format_help_entries(entries: list[_HelpEntry]) -> list[str]:
    label_width = _help_label_width(entries)
    gap = " " * _HELP_ENTRY_GAP
    return [
        f"  {_pad_visible(label, label_width)}{gap}{description}" for label, description in entries
    ]


def _pad_visible(value: str, width: int) -> str:
    padding = width - visible_len(value)
    if padding <= 0:
        return value
    return f"{value}{' ' * padding}"
