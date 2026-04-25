from __future__ import annotations

from hephaistos.app.autocomplete import CommandSuggestion, SlashCompletionEngine
from hephaistos.providers.config import _default_config  # type: ignore[reportPrivateUsage]


def test_command_suggestion_smoke() -> None:
    suggestion = CommandSuggestion(name="/help", description="Show help")

    assert suggestion.name == "/help"
    assert suggestion.description == "Show help"


def test_slash_completion_matches_command_aliases() -> None:
    engine = SlashCompletionEngine(provider_config_loader=_default_config)
    commands = [
        CommandSuggestion(name="help", description="Show help", aliases=("h", "?")),
        CommandSuggestion(name="quit", description="Leave", aliases=("q",)),
    ]

    candidates = engine.candidates("/q", commands)

    assert candidates[0].text == "quit "
    assert candidates[0].start_position == -1


def test_slash_completion_suggests_provider_arguments() -> None:
    engine = SlashCompletionEngine(provider_config_loader=_default_config)

    candidates = engine.candidates("/provider use za", [])

    assert any(candidate.text == "zai " for candidate in candidates)


def test_slash_completion_returns_textual_full_value() -> None:
    engine = SlashCompletionEngine(provider_config_loader=_default_config)
    commands = [CommandSuggestion(name="status", description="Show status")]

    suggestion = engine.suggestion("/sta", commands)

    assert suggestion == "/status "
