"""Slash command registry and handlers."""

from __future__ import annotations

from ai.providers.config import ProviderConfig
from harness.chat.session import save_session
from interfaces.terminal import (
    confirm,
    print_error,
    print_info,
    print_success,
)
from interfaces.terminal.input import set_command_registry_fn

from heph.commands._base import Command, CommandResult, set_registry_fn
from heph.commands.armory import ExportCommand, ImportCommand, IndexCommand
from heph.commands.auth import LoginCommand, LogoutCommand
from heph.commands.compact import CompactCommand
from heph.commands.display import (
    CostCommand,
    EvidenceCommand,
)
from heph.commands.help import ExitCommand, HelpCommand
from heph.commands.local import LocalCommand
from heph.commands.memory import MemoryCommand
from heph.commands.model import ModelsCommand
from heph.commands.session import (
    ArmoryCommand,
    DetachCommand,
    NewCommand,
    SessionsCommand,
    StatsCommand,
    StatusCommand,
    TurnCommand,
)
from heph.commands.settings import SettingsCommand
from heph.commands.study import (
    ExamCommand,
    PriorityCommand,
    VocabCommand,
)
from heph.commands.suggestions import CommandSuggestion
from heph.commands.trust import TrustCommand


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
                LocalCommand,
                LogoutCommand,
                StatusCommand,
                NewCommand,
                DetachCommand,
                ArmoryCommand,
                CompactCommand,
                EvidenceCommand,
                CostCommand,
                PriorityCommand,
                ExamCommand,
                ExportCommand,
                ImportCommand,
                MemoryCommand,
                ModelsCommand,
                SettingsCommand,
                SessionsCommand,
                StatsCommand,
                TrustCommand,
                TurnCommand,
                IndexCommand,
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
    "DetachCommand",
    "EvidenceCommand",
    "ExamCommand",
    "ExitCommand",
    "ExportCommand",
    "HelpCommand",
    "ImportCommand",
    "IndexCommand",
    "LocalCommand",
    "LoginCommand",
    "LogoutCommand",
    "MemoryCommand",
    "ModelsCommand",
    "NewCommand",
    "PriorityCommand",
    "ProviderConfig",
    "SessionsCommand",
    "SettingsCommand",
    "StatsCommand",
    "StatusCommand",
    "TrustCommand",
    "TurnCommand",
    "VocabCommand",
    # Re-exported helpers (for test monkeypatching)
    "confirm",
    "get_registry",
    "print_error",
    "print_info",
    "print_success",
    "save_session",
]
