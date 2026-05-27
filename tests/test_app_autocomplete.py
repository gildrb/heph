from __future__ import annotations

from hephaion.commands.suggestions import CommandSuggestion
from hephaion.providers.config import default_config
from hephaion.tui.slash_completion import SlashCompletionEngine


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


def test_slash_completion_picks_closest_command_match() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)
    commands = [
        CommandSuggestion(name="help", description="Show help"),
        CommandSuggestion(name="index", description="Build the search index"),
        CommandSuggestion(name="models", description="Pick the active model"),
        CommandSuggestion(name="memory", description="Manage armory memory"),
    ]

    for query in ("/del", "/odel", "/mdel"):
        candidates = engine.candidates(query, commands)

        assert len(candidates) == 1
        assert candidates[0].text == "models "
        assert candidates[0].start_position == 1 - len(query)
        assert engine.suggestion(query, commands) == "/models "


def test_slash_completion_skips_distant_command_matches() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)
    commands = [CommandSuggestion(name="models", description="Pick the active model")]

    assert engine.candidates("/zzz", commands) == []
    assert engine.suggestion("/zzz", commands) is None


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


def test_sessions_completion_shows_subcommands() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    candidates = engine.candidates("/sessions ", [])
    texts = {candidate.text for candidate in candidates}

    assert {"list ", "browse ", "resume "} <= texts


def test_mode_completion_has_no_mode_subcommands() -> None:
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    assert engine.candidates("/mode ", []) == []
