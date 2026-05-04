from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.cli.main import build_parser, run_argv


def test_init_armory_returns_success_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    armory_path = tmp_path / "study-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert str(armory_path.resolve()) in out


def test_armory_name_shortcut_creates_in_default_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path / "Armories"))
    armory_path = tmp_path / "Armories" / "mfi-1"

    run_argv(parser, ["armory", "mfi-1"])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert armory_path.is_dir()


def test_armory_name_shortcut_creates_inside_explicit_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path / "unused"))
    parent = tmp_path / "Code"
    armory_path = parent / "Armories" / "mfi-1"

    run_argv(parser, ["armory", "mfi-1", str(parent)])

    out = capsys.readouterr().out
    assert "Open it later with: heph mfi-1" in out
    assert armory_path.is_dir()


def test_armory_name_shortcut_can_cancel_second_armory_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    code_parent = tmp_path / "Code"
    design_parent = tmp_path / "Design"
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(code_parent / "Armories"))
    run_argv(parser, ["armory", "gdp"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["armory", "mfi-1", str(design_parent)])

    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "Your armories are currently stored here" in out
    assert str(code_parent / "Armories") in out
    assert "rerun without the path" in out
    assert not (design_parent / "Armories").exists()


def test_armory_name_shortcut_can_move_existing_armory_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    code_parent = tmp_path / "Code"
    design_parent = tmp_path / "Design"
    old_home = code_parent / "Armories"
    new_home = design_parent / "Armories"
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(old_home))
    run_argv(parser, ["armory", "gdp"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")

    run_argv(parser, ["armory", "mfi-1", str(design_parent)])

    out = capsys.readouterr().out
    assert "Moved Armories folder" in out
    assert not old_home.exists()
    assert (new_home / "gdp").is_dir()
    assert (new_home / "mfi-1").is_dir()


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
