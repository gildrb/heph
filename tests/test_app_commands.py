from __future__ import annotations

from hephaistos.app import commands
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession, create_plain_session
from hephaistos.providers.config import _default_config


def test_command_registry_includes_login_logout() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("login") is not None
    assert registry.find("logout") is not None
    assert "login" in names
    assert "logout" in names


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


def test_clear_command_supports_plain_chat(monkeypatch) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")

    monkeypatch.setattr(commands, "confirm", lambda *_args, **_kwargs: True)

    result = commands.ClearCommand().handle(session, "")

    assert result.new_session is not None
    assert result.new_session.armory_path is None
    assert result.new_session.conversation.messages[0].role == "system"
    assert len(result.new_session.conversation.messages) == 1


def test_persona_command_updates_plain_chat_system_prompt(monkeypatch) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    before = session.conversation.messages[0].content

    monkeypatch.setattr(commands, "print_success", lambda _msg: None)

    result = commands.PersonaCommand().handle(session, "tutor")

    after = session.conversation.messages[0].content
    assert result.output is None
    assert session.persona.slug == "tutor"
    assert after != before
    assert "patient tutor" in after
    assert "Plain chat mode" in after


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
