from __future__ import annotations

from hephaistos.app.autocomplete import CommandSuggestion


def test_command_suggestion_smoke() -> None:
    suggestion = CommandSuggestion(name="/help", description="Show help")

    assert suggestion.name == "/help"
    assert suggestion.description == "Show help"
