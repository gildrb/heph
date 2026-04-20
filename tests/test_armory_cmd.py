from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.app.cli import build_parser, run_argv


def test_init_armory_returns_success_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    armory_path = tmp_path / "study-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert str(armory_path.resolve()) in out


def test_open_armory_returns_success_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    armory_path = tmp_path / "study-armory"
    run_argv(parser, ["armory", "init", str(armory_path)])

    run_argv(parser, ["armory", "open", str(armory_path)])

    out = capsys.readouterr().out
    assert "Opened armory" in out
    assert str(armory_path.resolve()) in out


def test_open_armory_fails_for_uninitialized_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    uninitialized = tmp_path / "not-initialized"
    uninitialized.mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["armory", "open", str(uninitialized)])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "missing armory marker file" in err
