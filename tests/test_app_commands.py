from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.app import commands
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession, create_plain_session
from hephaistos.providers.config import _default_config  # type: ignore[reportPrivateUsage]


def test_command_registry_includes_login_logout() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("login") is not None
    assert registry.find("logout") is not None
    assert "login" in names
    assert "logout" in names


def test_command_registry_includes_settings() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("settings") is not None
    assert "settings" in names


def test_command_registry_includes_memory_and_recommend() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("memory") is not None
    assert registry.find("recommend") is not None
    assert "memory" in names
    assert "recommend" in names


def test_memory_status_reports_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    monkeypatch.setattr(commands, "resolve_supermemory_key", lambda: "")

    result = commands.MemoryCommand().handle(session, "status")

    out = capsys.readouterr().out
    assert result.output is None
    assert "Supermemory: disabled" in out
    assert "Run /memory setup" in out


def test_memory_disable_updates_settings(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.MemoryCommand().handle(session, "disable")

    out = capsys.readouterr().out
    assert "Supermemory disabled" in out


def test_recommend_command_lists_study_models(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.RecommendCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Study picks" in out
    assert "study" in out


def test_command_registry_includes_saved_chat_shortcuts() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("chats") is not None
    assert registry.find("sessions") is not None
    assert registry.find("resume") is not None
    assert "chats" in names
    assert "sessions" in names
    assert "resume" in names


def test_command_registry_includes_session_utility_commands() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    for name in ("evidence", "tokens", "cost", "stats"):
        assert registry.find(name) is not None
        assert name in names


def test_tokens_and_cost_commands_toggle_live_toolbar() -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "show")
    commands.CostCommand().handle(session, "show")

    assert session.live_tokens_visible is True
    assert session.live_cost_visible is True

    commands.TokensCommand().handle(session, "hide")
    commands.CostCommand().handle(session, "hide")

    assert session.live_tokens_visible is False
    assert session.live_cost_visible is False


def test_stats_command_reports_current_session(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")
    session.conversation.add("assistant", "hi")

    commands.StatsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Current session:" in out
    assert "Turns:      1" in out
    assert "Assistant:  1 messages" in out


def test_model_command_validates_against_session_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        classmethod(lambda _cls: _default_config()),  # type: ignore[reportUnknownLambdaType]
    )
    monkeypatch.setattr(
        commands,
        "print_success",
        lambda msg: messages.append(("success", msg)),  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )
    monkeypatch.setattr(
        commands,
        "print_error",
        lambda msg: messages.append(("error", msg)),  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )

    result = commands.ModelCommand().handle(session, "gpt-4o-mini")

    assert result.output is None
    assert session.config.model == "gpt-4o-mini"
    assert messages == [("success", "Model: gpt-5.4 -> gpt-4o-mini")]


def test_clear_command_supports_plain_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")

    monkeypatch.setattr(
        commands,
        "confirm",
        lambda *_args, **_kwargs: True,  # type: ignore[reportUnknownLambdaType]
    )

    result = commands.ClearCommand().handle(session, "")

    assert result.new_session is not None
    assert result.new_session.armory_path is None
    assert result.new_session.conversation.messages[0].role == "system"
    assert len(result.new_session.conversation.messages) == 1


def test_persona_command_updates_plain_chat_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    before = session.conversation.messages[0].content

    monkeypatch.setattr(
        commands,
        "print_success",
        lambda _msg: None,  # type: ignore[reportUnknownLambdaType]
    )

    result = commands.PersonaCommand().handle(session, "tutor")

    after = session.conversation.messages[0].content
    assert result.output is None
    assert session.persona.slug == "tutor"
    assert after != before
    assert "patient tutor" in after
    assert "Plain chat mode" in after


def test_model_command_rejects_unsupported_model_for_known_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        classmethod(lambda _cls: _default_config()),  # type: ignore[reportUnknownLambdaType]
    )
    monkeypatch.setattr(
        commands,
        "print_success",
        lambda msg: messages.append(("success", msg)),  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )
    monkeypatch.setattr(
        commands,
        "print_error",
        lambda msg: messages.append(("error", msg)),  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )

    result = commands.ModelCommand().handle(session, "glm-5-turbo")

    assert result.output is None
    assert session.config.model == "gpt-5.4"
    assert messages == [("error", "Model unavailable.")]


# ---------------------------------------------------------------------------
# Coverage-boosting tests for command handlers
# ---------------------------------------------------------------------------


def test_exit_command_returns_quit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.ExitCommand().handle(session, "")

    assert result.should_exit is True


def test_quit_command_returns_quit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.QuitCommand().handle(session, "")

    assert result.should_exit is True


def test_status_command_reports_model(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.StatusCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Model:" in out


def test_history_command_no_armory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.HistoryCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Turns:" in out


def test_evidence_command_no_armory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.EvidenceCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "evidence" in out.lower()


def test_save_command_plain_session(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    monkeypatch.setattr(
        commands,
        "save_session",
        lambda _s: Path("/fake/saved.json"),  # type: ignore[reportUnknownLambdaType]
    )

    commands.SaveCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "Saved" in out


def test_compact_command_empty_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CompactCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "Nothing to compact" in out


def test_edit_command_no_messages(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.EditCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "No user messages" in out


def test_api_command_set_url(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.ApiCommand().handle(session, "url https://api.example.com/v1")

    out = capsys.readouterr().out
    assert "Base URL:" in out
    assert session.config.base_url == "https://api.example.com/v1"


def test_api_command_set_url_missing_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.ApiCommand().handle(session, "url")
    out = capsys.readouterr().out
    assert "Usage:" in out


def test_api_command_set_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    monkeypatch.setattr(
        commands.ProviderConfig,
        "load",
        classmethod(lambda cls: _default_config()),  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )
    monkeypatch.setattr(commands, "store_key", lambda *_a: None)  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]

    commands.ApiCommand().handle(session, "key sk-test-123")
    out = capsys.readouterr().out
    assert "key saved" in out.lower() or "API key" in out


def test_api_command_set_key_missing_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.ApiCommand().handle(session, "key")
    out = capsys.readouterr().out
    assert "Usage:" in out


def test_api_command_unknown_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.ApiCommand().handle(session, "bogus value")
    out = capsys.readouterr().out
    assert "Unknown subcommand" in out


def test_tokens_command_invalid_arg(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "bogus")
    out = capsys.readouterr().out
    assert "Usage:" in out or "toggle" in out.lower()


def test_tokens_command_toggle(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "tokens" in out.lower()


def test_cost_command_invalid_arg(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "bogus")
    out = capsys.readouterr().out
    assert "Usage:" in out or "toggle" in out.lower()


def test_cost_command_toggle(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "cost" in out.lower()
