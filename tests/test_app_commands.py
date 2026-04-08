from __future__ import annotations

from hephaistos.app import commands
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import _default_config


def test_command_registry_excludes_oauth_commands() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("login") is None
    assert registry.find("logout") is None
    assert "login" not in names
    assert "logout" not in names


def test_model_command_validates_against_session_endpoint(monkeypatch) -> None:
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="session-1",
    )
    messages: list[tuple[str, str]] = []

    monkeypatch.setattr(
        commands.ProviderConfig,
        "load",
        classmethod(lambda cls: _default_config()),
    )
    monkeypatch.setattr(
        commands,
        "print_success",
        lambda msg: messages.append(("success", msg)),
    )
    monkeypatch.setattr(
        commands,
        "print_error",
        lambda msg: messages.append(("error", msg)),
    )

    result = commands.ModelCommand().handle(session, "gpt-4o-mini")

    assert result.output is None
    assert session.config.model == "gpt-4o-mini"
    assert messages == [("success", "Model: gpt-5.4 -> gpt-4o-mini")]


def test_model_command_rejects_unsupported_model_for_known_endpoint(monkeypatch) -> None:
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="session-1",
    )
    messages: list[tuple[str, str]] = []

    monkeypatch.setattr(
        commands.ProviderConfig,
        "load",
        classmethod(lambda cls: _default_config()),
    )
    monkeypatch.setattr(
        commands,
        "print_success",
        lambda msg: messages.append(("success", msg)),
    )
    monkeypatch.setattr(
        commands,
        "print_error",
        lambda msg: messages.append(("error", msg)),
    )

    result = commands.ModelCommand().handle(session, "glm-5-turbo")

    assert result.output is None
    assert session.config.model == "gpt-5.4"
    assert messages == [("error", "Model unavailable.")]
