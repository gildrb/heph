"""Armory filesystem operations."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import tomllib

ARMORY_DIRS = ("source", "library", "notes", "chats", "parameters", ".hephaistos")
MARKER_FILE = Path(".hephaistos/armory.toml")


class ArmoryError(Exception):
    """Base error for armory operations."""


class ArmoryValidationError(ArmoryError):
    """Raised when a path is not a valid armory."""


def normalize_path(raw_path: str | Path) -> Path:
    """Expand and resolve a user path to an absolute path."""
    return Path(raw_path).expanduser().resolve()


def initialize(path: Path) -> None:
    """Create the armory directory layout and marker file."""
    path.mkdir(parents=True, exist_ok=True)

    for dirname in ARMORY_DIRS:
        (path / dirname).mkdir(parents=True, exist_ok=True)

    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        created_at = datetime.now(UTC).isoformat()
        marker_path.write_text(
            f'version = 1\ncreated_at = "{created_at}"\n',
            encoding="utf-8",
        )


def validate(path: Path) -> None:
    """Ensure path is a valid armory folder."""
    if not path.exists():
        raise ArmoryValidationError(f"armory does not exist: {path}")
    if not path.is_dir():
        raise ArmoryValidationError(f"path is not a directory: {path}")
    
def read_marker(path: Path) -> dict[str, object]:
    """Read and return the parsed armory marker file."""
    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        raise ArmoryValidationError(f"missing armory marker file: {marker_path}")
    with marker_path.open("rb") as f:
        return tomllib.load(f)

    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        raise ArmoryValidationError(f"missing armory marker file: {marker_path}")

    missing_dirs = [dirname for dirname in ARMORY_DIRS if not (path / dirname).is_dir()]
    if missing_dirs:
        missing = ", ".join(missing_dirs)
        raise ArmoryValidationError(f"armory is missing required dirs: {missing}")
