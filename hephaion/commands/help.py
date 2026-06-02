"""Help and exit commands."""

from __future__ import annotations

from hephaion.commands._base import Command, CommandResult, get_registry_lazy
from hephaion.terminal import STYLE_PROMPT, styled


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"
    aliases = ("?", "h")

    def handle(self, session: object, args: str) -> CommandResult:
        del session, args
        registry = get_registry_lazy()
        max_name = max(len(c.name) for c in registry.commands)
        lines: list[str] = []
        lines.append(styled("Commands", STYLE_PROMPT))
        for cmd in sorted(registry.commands, key=lambda c: c.name):
            padded = f"  /{cmd.name}".ljust(max_name + 4)
            lines.append(f"{padded} {cmd.description}")
        lines.append("")
        lines.append(styled("Input", STYLE_PROMPT))
        lines.append("  /help           Show command reference")
        lines.append("")
        lines.append(styled("Shortcuts", STYLE_PROMPT))
        lines.append("  Up/Down         Browse input history")
        lines.append("  Tab             Autocomplete slash commands")
        lines.append("  Shift+Enter/Ctrl+J  Insert newline")
        lines.append("  Ctrl+C          Exit Heph")
        lines.append("  Ctrl+D          Exit Heph")
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
