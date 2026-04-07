from __future__ import annotations

from hephaistos.app import commands


def test_command_registry_excludes_oauth_commands() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("login") is None
    assert registry.find("logout") is None
    assert "login" not in names
    assert "logout" not in names
