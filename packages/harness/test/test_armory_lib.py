from __future__ import annotations

import stat
from pathlib import Path

import pytest
from harness.armory.state_files import (
    STATE_FILE_MODE,
    armory_state_location,
    write_armory_state_text,
)
from harness.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    armory_display_name,
    initialize,
    normalize_path,
    validate,
    validate_armory_path,
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


def test_validate_armory_path_normalizes_and_reads_marker(tmp_path: Path) -> None:
    armory_path = tmp_path / "valid-armory"
    initialize(armory_path)

    assert validate_armory_path(armory_path) == armory_path.resolve()


def test_armory_display_name_preserves_existing_directory_casing(tmp_path: Path) -> None:
    armory_path = tmp_path / "MixedCase-2"
    armory_path.mkdir()

    assert armory_display_name(tmp_path / "mixedcase-2") == "MixedCase-2"


def test_armory_display_name_prefers_exact_case_when_case_distinct_siblings_exist(
    tmp_path: Path,
) -> None:
    mixed_case = tmp_path / "MixedCase-2"
    exact_case = tmp_path / "mixedcase-2"
    mixed_case.mkdir()
    try:
        exact_case.mkdir()
    except FileExistsError:
        pytest.skip("case-insensitive filesystem does not allow case-distinct siblings")

    assert armory_display_name(exact_case) == "mixedcase-2"


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
    internal = armory_path / ".harness"
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
    armory_path = tmp_path / ".harness" / "course-armory"
    state_path = armory_path / ".harness" / "traces" / "session.jsonl"

    parsed_armory, rel_path = armory_state_location(state_path)

    assert parsed_armory == armory_path
    assert rel_path == Path(".harness/traces/session.jsonl")


def test_write_armory_state_text_falls_back_without_fchmod(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    armory_path = tmp_path / "armory"
    initialize(armory_path)
    monkeypatch.delattr("harness.armory.state_files.os.fchmod", raising=False)

    state_path = write_armory_state_text(armory_path, ".harness/session.json", "ok")

    assert state_path.read_text(encoding="utf-8") == "ok"
    assert stat.S_IMODE(state_path.stat().st_mode) == STATE_FILE_MODE


def test_normalize_path_returns_absolute_path(tmp_path: Path) -> None:
    rel_path = tmp_path / "rel-armory"
    normalized = normalize_path(rel_path)
    assert normalized.is_absolute()
