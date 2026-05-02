from __future__ import annotations

import pytest

from hephaistos.app.autocomplete import CommandSuggestion, SlashCompletionEngine
from hephaistos.providers.config import default_config


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


def test_models_completion_searches_accessible_model_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    candidates = engine.candidates("/models gl", [])

    assert any(candidate.text == "glm-5 " for candidate in candidates)
    assert any(candidate.text == "glm-5-turbo " for candidate in candidates)


def test_models_completion_starts_with_openrouter_provider_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    candidates = engine.candidates("/models", [])

    openrouter_candidates = [
        candidate for candidate in candidates if candidate.display_source == "OpenRouter"
    ]
    assert openrouter_candidates
    assert candidates[: len(openrouter_candidates)] == openrouter_candidates


def test_models_completion_keeps_provider_grouping_when_current_model_is_elsewhere(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    config = default_config()
    config.set_active("openrouter")
    config.providers["openrouter"].current_model = "arcee-ai/trinity-large-preview:free"
    engine = SlashCompletionEngine(provider_config_loader=lambda: config)

    candidates = engine.candidates("/models", [])

    openrouter_candidates = [
        candidate for candidate in candidates if candidate.display_source == "OpenRouter"
    ]
    assert candidates[: len(openrouter_candidates)] == openrouter_candidates
    assert any(candidate.display_tags == "free+key current" for candidate in openrouter_candidates)


def test_models_completion_marks_openrouter_free_models_as_key_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    engine = SlashCompletionEngine(provider_config_loader=default_config)

    candidates = engine.candidates("/models trinity", [])

    assert candidates
    assert candidates[0].text == "arcee-ai/trinity-large-preview:free "
    assert candidates[0].display_source == "OpenRouter"
    assert candidates[0].display_tags == "free+key"
