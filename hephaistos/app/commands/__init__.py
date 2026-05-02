"""Slash command registry and handlers.

Public API::

    from hephaistos.app.commands import (
        Command, CommandResult, CommandRegistry, get_registry,
    )
"""

from __future__ import annotations

from hephaistos.app.autocomplete import CommandSuggestion
from hephaistos.app.commands._base import Command, CommandResult, set_registry_fn
from hephaistos.app.commands.armory import ExportCommand, ImportCommand, IndexCommand
from hephaistos.app.commands.auth import ApiCommand, LoginCommand, LogoutCommand
from hephaistos.app.commands.compact import CompactCommand
from hephaistos.app.commands.display import (
    CostCommand,
    EvidenceCommand,
    HistoryCommand,
    StatsCommand,
    TokensCommand,
    UsageCommand,
)
from hephaistos.app.commands.help import ExitCommand, HelpCommand, QuitCommand

# Re-export helpers that tests monkeypatch via the commands namespace.
# These are imported into the sub-modules and re-exported here so that
# test code doing ``commands.resolve_supermemory_key`` still works.
from hephaistos.app.commands.memory import (
    MemoryCommand,
    mask_key,
    resolve_supermemory_key,
    set_volatile,
    store_key,
)
from hephaistos.app.commands.model import (
    ModelsCommand,
    ProviderCommand,
    RecommendCommand,
)
from hephaistos.app.commands.persona import PersonaCommand
from hephaistos.app.commands.session import (
    ArmoryCommand,
    ClearCommand,
    EditCommand,
    NewCommand,
    ResumeCommand,
    SaveCommand,
    SessionsCommand,
    StatusCommand,
)
from hephaistos.app.commands.settings import SettingsCommand
from hephaistos.app.commands.study import RemindCommand, VocabCommand
from hephaistos.app.display import (
    print_error,
    print_info,
    print_success,
)
from hephaistos.app.menu import confirm
from hephaistos.chat.session import save_session
from hephaistos.providers.config import ProviderConfig


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
            ApiCommand,
            CompactCommand,
            HistoryCommand,
            EvidenceCommand,
            TokensCommand,
            CostCommand,
            StatsCommand,
            ExportCommand,
            ImportCommand,
            RemindCommand,
            EditCommand,
            ProviderCommand,
            ModelsCommand,
            RecommendCommand,
            MemoryCommand,
            PersonaCommand,
            SettingsCommand,
            IndexCommand,
            UsageCommand,
            VocabCommand,
        ):
            _registry.register(cmd_class())
    return _registry


# Wire up the lazy registry accessor so sub-modules (e.g. HelpCommand)
# can access the registry without creating a circular import.
set_registry_fn(get_registry)


__all__ = [
    # Command classes (for direct import)
    "ApiCommand",
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
    "HistoryCommand",
    "ImportCommand",
    "IndexCommand",
    "LoginCommand",
    "LogoutCommand",
    "MemoryCommand",
    "ModelsCommand",
    "NewCommand",
    "PersonaCommand",
    "ProviderCommand",
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
