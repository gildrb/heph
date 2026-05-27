from __future__ import annotations

from pathlib import Path

import pytest

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


def test_normalize_path_returns_absolute_path(tmp_path: Path) -> None:
    rel_path = tmp_path / "rel-armory"
    normalized = normalize_path(rel_path)
    assert normalized.is_absolute()
