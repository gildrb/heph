"""Help, exit, and quit commands."""

from __future__ import annotations

from hephaistos.commands._base import Command, CommandResult, get_registry_lazy
from hephaistos.terminal import STYLE_PROMPT
from hephaistos.terminal.display import print_info, styled


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"
    aliases = ("?", "h")

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_registry_lazy()
        visible = [c for c in registry.commands if not c.hidden]
        max_name = max(len(c.name) for c in visible)
        lines: list[str] = []
        lines.append(styled("Commands", STYLE_PROMPT))
        for cmd in sorted(visible, key=lambda c: c.name):
            padded = f"  /{cmd.name}".ljust(max_name + 4)
            lines.append(f"{padded} {cmd.description}")
        lines.append("")
        lines.append(styled("Input", STYLE_PROMPT))
        pad = max_name + 2
        lines.append(f"  !{'command'.ljust(pad)} Run a shell command")
        lines.append("  /help           Show command reference")
        lines.append("")
        lines.append(styled("Shortcuts", STYLE_PROMPT))
        lines.append("  Up/Down         Browse input history")
        lines.append("  Tab             Autocomplete slash commands")
        lines.append("  Alt+Enter       Insert newline")
        lines.append("  Ctrl+C          Cancel current response")
        lines.append("  Ctrl+D          Exit shell")
        lines.append("")
        print("\n".join(lines))
        return CommandResult()


class ExitCommand(Command):
    name = "exit"
    description = "Leave the shell"
    aliases = ("quit", "q")

    def handle(self, session: object, args: str) -> CommandResult:
        return CommandResult(should_exit=True)


class QuitCommand(Command):
    name = "quit"
    description = "Leave the shell"
    aliases = ("q",)
    hidden = True

    def handle(self, session: object, args: str) -> CommandResult:
        print_info(f"Exiting... (/{self.name} \u2192 /exit)")
        return CommandResult(should_exit=True)
