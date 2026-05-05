from __future__ import annotations

from hephaistos.commands.suggestions import CommandSuggestion
from hephaistos.providers.config import default_config
from hephaistos.tui.slash_completion import SlashCompletionEngine


def test_command_suggestion_smoke() -> None:
    suggestion = CommandSuggestion(name="/help", description="Show help")

    assert suggestion.name == "/help"
    assert suggestion.description == "Show help"


def test_slash_completion_matches_command_aliases() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)
    commands = [
        CommandSuggestion(name="help", description="Show help", aliases=("h", "?")),
        CommandSuggestion(name="quit", description="Leave", aliases=("q",)),
    ]

    candidates = engine.candidates("/q", commands)

    assert candidates[0].text == "quit "
    assert candidates[0].start_position == -1


def test_slash_completion_returns_textual_full_value() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)
    commands = [CommandSuggestion(name="status", description="Show status")]

    suggestion = engine.suggestion("/sta", commands)

    assert suggestion == "/status "


def test_models_completion_shows_command_suggestion() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)
    commands = [CommandSuggestion(name="models", description="Pick the active model")]

    candidates = engine.candidates("/models", commands)

    assert len(candidates) == 1
    assert candidates[0].text == "models "
    assert candidates[0].description == "Pick the active model"


def test_models_with_args_shows_no_candidates() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    candidates = engine.candidates("/models gl", [])

    assert candidates == []
