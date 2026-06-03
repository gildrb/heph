from __future__ import annotations

from pathlib import Path

from hephaion import commands
from hephaion.armory.storage import initialize
from hephaion.chat.session import ChatSession
from hephaion.runtime import ChatConfig, Conversation


def test_registry_exposes_status_without_stats() -> None:
    registry = commands.get_registry()
    names = {suggestion.name for suggestion in registry.suggestions()}

    assert registry.find("status") is not None
    assert "status" in names
    assert registry.find("stats") is None
    assert "stats" not in names


def test_status_includes_session_usage_and_armory_stats(tmp_path: Path) -> None:
    armory = tmp_path / "status-armory"
    initialize(armory)
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="status-1",
        armory_path=armory,
    )
    session.conversation.add("user", "hello")
    session.conversation.add("assistant", "hi")

    result = commands.StatusCommand().handle(session, "")

    assert result.output is not None
    assert "Current session:" in result.output
    assert "Model:" in result.output
    assert "Turns:     1" in result.output
    assert "Assistant: 1 messages" in result.output
    assert "API calls:" in result.output
    assert "Tokens:" in result.output
    assert "Armory:" in result.output
    assert "Saved:" in result.output
    assert "Vocabulary:" in result.output
