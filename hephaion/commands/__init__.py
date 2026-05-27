"""Slash command registry and handlers."""

from __future__ import annotations

from hephaion.chat.session import save_session
from hephaion.commands._base import Command, CommandResult, set_registry_fn
from hephaion.commands.armory import ExportCommand, ImportCommand, IndexCommand
from hephaion.commands.auth import LoginCommand, LogoutCommand
from hephaion.commands.compact import CompactCommand
from hephaion.commands.display import (
    CostCommand,
    EvidenceCommand,
    StatsCommand,
    TokensCommand,
    UsageCommand,
)
from hephaion.commands.help import ExitCommand, HelpCommand
from hephaion.commands.memory import MemoryCommand
from hephaion.commands.model import ModelsCommand, RecommendCommand
from hephaion.commands.session import (
    ArmoryCommand,
    NewCommand,
    SessionsCommand,
    StatusCommand,
)
from hephaion.commands.settings import SettingsCommand
from hephaion.commands.study import (
    ExamCommand,
    PriorityCommand,
    RemindCommand,
    VocabCommand,
)
from hephaion.commands.suggestions import CommandSuggestion
from hephaion.providers.config import ProviderConfig
from hephaion.terminal import (
    confirm,
    print_error,
    print_info,
    print_success,
)
from hephaion.terminal.input import set_command_registry_fn


class CommandRegistry:
    def __init__(self) -> None:
        self.commands: list[Command] = []

    def find(self, name: str) -> Command | None:
        name_lower = name.lower()
        for cmd in self.commands:
            if cmd.name == name_lower or name_lower in cmd.aliases:
                return cmd
        return None

    def suggestions(self) -> list[CommandSuggestion]:
        return [
            CommandSuggestion(name=cmd.name, description=cmd.description, aliases=cmd.aliases)
            for cmd in self.commands
        ]


_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = CommandRegistry()
        _registry.commands.extend(
            cmd_class()
            for cmd_class in (
                HelpCommand,
                ExitCommand,
                LoginCommand,
                LogoutCommand,
                StatusCommand,
                NewCommand,
                ArmoryCommand,
                CompactCommand,
                EvidenceCommand,
                TokensCommand,
                CostCommand,
                StatsCommand,
                PriorityCommand,
                ExamCommand,
                ExportCommand,
                ImportCommand,
                RemindCommand,
                ModelsCommand,
                RecommendCommand,
                MemoryCommand,
                SettingsCommand,
                SessionsCommand,
                IndexCommand,
                UsageCommand,
                VocabCommand,
            )
        )
    return _registry


# Wire up lazy registry accessors so sub-modules and workspace input handling
# can access the registry without creating circular imports.
set_registry_fn(get_registry)
set_command_registry_fn(get_registry)


__all__ = [
    # Command classes (for direct import)
    "ArmoryCommand",
    "Command",
    "CommandRegistry",
    "CommandResult",
    "CompactCommand",
    "CostCommand",
    "EvidenceCommand",
    "ExamCommand",
    "ExitCommand",
    "ExportCommand",
    "HelpCommand",
    "ImportCommand",
    "IndexCommand",
    "LoginCommand",
    "LogoutCommand",
    "MemoryCommand",
    "ModelsCommand",
    "NewCommand",
    "PriorityCommand",
    "ProviderConfig",
    "RecommendCommand",
    "RemindCommand",
    "SessionsCommand",
    "SettingsCommand",
    "StatsCommand",
    "StatusCommand",
    "TokensCommand",
    "UsageCommand",
    "VocabCommand",
    # Re-exported helpers (for test monkeypatching)
    "confirm",
    "get_registry",
    "print_error",
    "print_info",
    "print_success",
    "save_session",
]
