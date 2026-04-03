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
