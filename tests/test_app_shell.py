from __future__ import annotations

from pathlib import Path

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
    shell.run_chat_shell(session)

    out = capsys.readouterr().out
    assert f"Using armory {armory_path.resolve()}" in out


def test_run_chat_shell_save_without_armory_prints_error(monkeypatch, capsys) -> None:
    responses = iter(["/save", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = create_session(ChatConfig(), None)
    shell.run_chat_shell(session)

    err = capsys.readouterr().err
    assert "cannot save chat without an active armory" in err
