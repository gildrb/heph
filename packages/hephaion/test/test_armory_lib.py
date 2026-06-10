from __future__ import annotations

import stat
from pathlib import Path

import pytest
from hephaion.armory import state_files
from hephaion.armory.state_files import armory_state_location, write_armory_state_text
from hephaion.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    initialize,
    normalize_path,
    validate,
)


def test_initialize_armory_creates_required_layout(tmp_path: Path) -> None:
    armory_path = tmp_path / "my-armory"

    initialize(armory_path)

    for dirname in ARMORY_DIRS:
        assert (armory_path / dirname).is_dir()
    assert (armory_path / MARKER_FILE).is_file()


def test_validate_armory_passes_for_initialized_path(tmp_path: Path) -> None:
    armory_path = tmp_path / "valid-armory"
    initialize(armory_path)

    validate(armory_path)


def test_validate_armory_fails_when_marker_is_missing(tmp_path: Path) -> None:
    armory_path = tmp_path / "broken-armory"
    initialize(armory_path)
    (armory_path / MARKER_FILE).unlink()

    with pytest.raises(ArmoryValidationError):
        validate(armory_path)


def test_validate_armory_rejects_symlinked_internal_dir(tmp_path: Path) -> None:
    armory_path = tmp_path / "symlink-armory"
    initialize(armory_path)
    outside = tmp_path / "outside-state"
    outside.mkdir()
    internal = armory_path / ".hephaion"
    for child in internal.iterdir():
        if child.is_dir():
            child.rmdir()
        else:
            child.unlink()
    internal.rmdir()
    try:
        internal.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    with pytest.raises(ArmoryValidationError, match="must not be a symlink"):
        validate(armory_path)


def test_armory_state_location_uses_armory_internal_dir_boundary(tmp_path: Path) -> None:
    armory_path = tmp_path / ".hephaion" / "course-armory"
    state_path = armory_path / ".hephaion" / "learning" / "attempts.jsonl"

    parsed_armory, rel_path = armory_state_location(state_path)

    assert parsed_armory == armory_path
    assert rel_path == Path(".hephaion/learning/attempts.jsonl")


def test_write_armory_state_text_falls_back_without_fchmod(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    armory_path = tmp_path / "armory"
    initialize(armory_path)
    monkeypatch.delattr(state_files.os, "fchmod", raising=False)

    state_path = write_armory_state_text(armory_path, ".hephaion/session.json", "ok")

    assert state_path.read_text(encoding="utf-8") == "ok"
    assert stat.S_IMODE(state_path.stat().st_mode) == state_files.STATE_FILE_MODE


def test_normalize_path_returns_absolute_path(tmp_path: Path) -> None:
    rel_path = tmp_path / "rel-armory"
    normalized = normalize_path(rel_path)
    assert normalized.is_absolute()
