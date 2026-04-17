from __future__ import annotations

import io
import re
from pathlib import Path

import hephaistos.app.cli as app_cli
from hephaistos.app.cli import build_parser, run_argv


class _FakeTTY(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_parser_includes_expected_top_level_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "armory" in help_text
    assert "chat" not in help_text
    assert "source" in help_text
    assert "parameters" not in help_text


def test_run_argv_dispatches_armory_init(tmp_path: Path, capsys) -> None:
    parser = build_parser()
    armory_path = tmp_path / "integration-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert armory_path.is_dir()


def test_main_without_args_uses_chat_shell_on_tty(monkeypatch) -> None:
    called = False

    def fake_shell() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(app_cli, "run_chat_shell", fake_shell)
    monkeypatch.setattr(app_cli.sys, "argv", ["heph"])
    monkeypatch.setattr(app_cli.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(app_cli.sys, "stdout", _FakeTTY(True))

    app_cli.main()

    assert called


def test_main_without_args_prints_help_on_non_tty(monkeypatch) -> None:
    fake_stdout = _FakeTTY(False)
    monkeypatch.setattr(app_cli.sys, "argv", ["heph"])
    monkeypatch.setattr(app_cli.sys, "stdin", _FakeTTY(False))
    monkeypatch.setattr(app_cli.sys, "stdout", fake_stdout)

    app_cli.main()

    output = re.sub(r"\x1b\[[0-9;]*m", "", fake_stdout.getvalue())
    assert "usage: heph" in output
