"""Slash command registry and handlers.

Public API::

    from hephaistos.commands import (
        Command, CommandResult, CommandRegistry, get_registry,
    )
"""

from __future__ import annotations

from hephaistos.chat.session import save_session
from hephaistos.commands._base import Command, CommandResult, set_registry_fn
from hephaistos.commands.armory import ExportCommand, ImportCommand, IndexCommand
from hephaistos.commands.auth import LoginCommand, LogoutCommand
from hephaistos.commands.compact import CompactCommand
from hephaistos.commands.display import (
    CostCommand,
    EvidenceCommand,
    StatsCommand,
    TokensCommand,
    UsageCommand,
)
from hephaistos.commands.help import ExitCommand, HelpCommand, QuitCommand

# Re-export helpers that tests monkeypatch via the commands namespace.
# These are imported into the sub-modules and re-exported here so that
# test code doing ``commands.resolve_supermemory_key`` still works.
from hephaistos.commands.memory import (
    MemoryCommand,
    mask_key,
    resolve_supermemory_key,
    set_volatile,
    store_key,
)
from hephaistos.commands.model import ModelsCommand, RecommendCommand
from hephaistos.commands.persona import PersonaCommand
from hephaistos.commands.session import (
    ArmoryCommand,
    ClearCommand,
    EditCommand,
    NewCommand,
    ResumeCommand,
    SaveCommand,
    SessionsCommand,
    StatusCommand,
)
from hephaistos.commands.settings import SettingsCommand
from hephaistos.commands.study import RemindCommand, VocabCommand
from hephaistos.commands.suggestions import CommandSuggestion
from hephaistos.providers.config import ProviderConfig
from hephaistos.terminal import confirm
from hephaistos.terminal.display import (
    print_error,
    print_info,
    print_success,
)
from hephaistos.terminal.input import set_command_registry_fn


class CommandRegistry:
    def __init__(self) -> None:
        self.commands: list[Command] = []

    def register(self, cmd: Command) -> None:
        self.commands.append(cmd)

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
            if not cmd.hidden
        ]


_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = CommandRegistry()
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
            ExportCommand,
            ImportCommand,
            RemindCommand,
            EditCommand,
            ModelsCommand,
            RecommendCommand,
            MemoryCommand,
            PersonaCommand,
            SettingsCommand,
            SessionsCommand,
            IndexCommand,
            UsageCommand,
            VocabCommand,
        ):
            _registry.register(cmd_class())
    return _registry


# Wire up lazy registry accessors so sub-modules and workspace input handling
# can access the registry without creating circular imports.
set_registry_fn(get_registry)
set_command_registry_fn(get_registry)


__all__ = [
    # Command classes (for direct import)
    "ArmoryCommand",
    "ClearCommand",
    "Command",
    "CommandRegistry",
    "CommandResult",
    "CompactCommand",
    "CostCommand",
    "EditCommand",
    "EvidenceCommand",
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
    "PersonaCommand",
    "ProviderConfig",
    "QuitCommand",
    "RecommendCommand",
    "RemindCommand",
    "ResumeCommand",
    "SaveCommand",
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
    "mask_key",
    "print_error",
    "print_info",
    "print_success",
    "resolve_supermemory_key",
    "save_session",
    "set_volatile",
    "store_key",
]
