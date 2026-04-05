"""Tests for the interactive shell (using fallback mode)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from hephaistos.app import shell
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_session


def test_run_chat_shell_armory_command_opens_existing_armory(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    armory_path = tmp_path / "study-armory"
    initialize(armory_path)

    responses = iter(["/armory", str(armory_path), "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    monkeypatch.setattr(shell, "select_option", lambda *_args, **_kwargs: 0)

    session = create_session(ChatConfig(), None)
    # Force fallback mode since pytest isn't a TTY
    with patch.object(shell.sys.stdin, "isatty", return_value=False), \
         patch.object(shell.sys.stdout, "isatty", return_value=False):
        shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert f"Using armory {armory_path.resolve()}" in out


def test_run_chat_shell_save_without_armory_prints_error(monkeypatch, capsys) -> None:
    responses = iter(["/save", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = create_session(ChatConfig(), None)
    shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert "cannot save chat without an active armory" in out


def test_fallback_shell_exits_on_quit(monkeypatch, capsys) -> None:
    responses = iter(["/quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = create_session(ChatConfig(), None)
    shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert "basic mode" in out


def test_fallback_shell_runs_bang_command(monkeypatch, capsys) -> None:
    responses = iter(["!echo hello", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = create_session(ChatConfig(), None)
    shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert "hello" in out


def test_handle_input_slash_command(monkeypatch, capsys) -> None:
    from hephaistos.app.input_history import InputHistory

    session = create_session(ChatConfig(), None)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/status", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "Session:" in out


def test_handle_input_exit(monkeypatch) -> None:
    from hephaistos.app.input_history import InputHistory

    session = create_session(ChatConfig(), None)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/exit", history)
    assert cont is False


def test_handle_input_shell_mode(monkeypatch, capsys) -> None:
    from hephaistos.app.input_history import InputHistory

    session = create_session(ChatConfig(), None)
    history = InputHistory()
    session, cont = shell._handle_input(session, "!echo test-output", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "test-output" in out


def test_handle_input_unknown_command(capsys) -> None:
    from hephaistos.app.input_history import InputHistory

    session = create_session(ChatConfig(), None)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/unknown", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "Unknown command" in out


# ---------------------------------------------------------------------------
# Cancellation / back-navigation tests
# ---------------------------------------------------------------------------


def test_prompt_path_returns_none_on_q(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_none_on_cancel(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "cancel")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_none_on_back(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "back")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_default_on_empty(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    result = shell._prompt_path("Path", "/default")
    assert result == "/default"


def test_prompt_path_returns_value_when_provided(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "/my/path")
    result = shell._prompt_path("Path", "/default")
    assert result == "/my/path"


def test_open_armory_cancelled_returns_session_unchanged(monkeypatch, capsys) -> None:
    session = create_session(ChatConfig(), None)
    assert session.armory_path is None

    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    new_session = shell._open_armory(session)

    assert new_session is session
    assert new_session.armory_path is None
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_create_armory_cancelled_returns_session_unchanged(monkeypatch, capsys) -> None:
    session = create_session(ChatConfig(), None)
    assert session.armory_path is None

    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    new_session = shell._create_armory(session)

    assert new_session is session
    assert new_session.armory_path is None
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_prompt_armory_for_sessions_cancelled_returns_none(monkeypatch, capsys) -> None:
    session = create_session(ChatConfig(), None)

    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    result = shell._prompt_armory_for_sessions(session)

    assert result is None
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_resume_saved_chat_cancelled_returns_session_unchanged(monkeypatch, capsys) -> None:
    session = create_session(ChatConfig(), None)

    # Cancel at the path prompt
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    new_session = shell._resume_saved_chat(session)

    assert new_session is session


def test_list_saved_chats_cancelled_returns_early(monkeypatch, capsys) -> None:
    session = create_session(ChatConfig(), None)

    # Cancel at the path prompt
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    shell._list_saved_chats(session)

    out = capsys.readouterr().out
    assert "Cancelled" in out
