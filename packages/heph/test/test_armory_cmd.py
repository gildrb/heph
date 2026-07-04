from __future__ import annotations

from pathlib import Path

import pytest
from harness.armory.storage import initialize
from heph.cli.main import build_parser, run_argv


def _initialize_legacy_armory(path: Path) -> None:
    initialize(path)
    (path / ".harness").rename(path / ".hephaion")


def test_init_armory_returns_success_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    armory_path = armory_home / "notes-armory"

    run_argv(parser, ["armory", "init", "notes-armory"])

    out = capsys.readouterr().out
    assert "Created armory" in out
    assert str(armory_path.resolve()) in out


def test_init_armory_fails_outside_armories_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    armory_path = tmp_path / "outside-armories" / "notes-armory"

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["armory", "init", str(armory_path)])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Armories can only be created in the armories directory" in err


def test_armory_name_shortcut_creates_in_default_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path / ".armories"))
    armory_path = tmp_path / ".armories" / "workspace-fixture-1"

    run_argv(parser, ["armory", "workspace-fixture-1"])

    out = capsys.readouterr().out
    assert "Created armory" in out
    assert armory_path.is_dir()


def test_armory_name_shortcut_rejects_explicit_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path / ".armories"))

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["armory", "workspace-fixture-1", str(tmp_path / "Code")])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "armory parent paths are no longer supported" in err


def test_open_armory_returns_success_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    armory_path = armory_home / "notes-armory"
    run_argv(parser, ["armory", "init", str(armory_path)])

    run_argv(parser, ["armory", "open", str(armory_path)])

    out = capsys.readouterr().out
    assert "Opened armory" in out
    assert str(armory_path.resolve()) in out


def test_open_armory_migrates_legacy_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    armory_path = armory_home / "legacy-armory"
    _initialize_legacy_armory(armory_path)

    run_argv(parser, ["armory", "open", str(armory_path)])

    out = capsys.readouterr().out
    assert "Opened armory" in out
    assert (armory_path / ".harness" / "armory.toml").is_file()
    assert not (armory_path / ".hephaion").exists()


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
