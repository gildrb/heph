"""Armory filesystem operations."""

from __future__ import annotations

import os
import tomllib
from datetime import UTC, datetime
from pathlib import Path

MATERIALS_DIR = "materials"
INTERNAL_DIR = ".hephaion"
GENERATED_DIR = ".hephaion/generated"
CHATS_DIR = ".hephaion/chats"
TRACES_DIR = ".hephaion/traces"
USAGE_DIR = ".hephaion/usage"
TOOLS_DIR = ".hephaion/tools"
DEFAULT_ARMORY_HOME_ENV = "HEPHAION_ARMORY_HOME"
ARMORY_DIRS = (
    MATERIALS_DIR,
    INTERNAL_DIR,
    GENERATED_DIR,
    CHATS_DIR,
    TRACES_DIR,
    USAGE_DIR,
    TOOLS_DIR,
)
MARKER_FILE = Path(".hephaion/armory.toml")
LAYOUT_VERSION = 2


class ArmoryError(Exception):
    pass


class ArmoryValidationError(ArmoryError):
    pass


def normalize_path(raw_path: str | Path) -> Path:
    return Path(raw_path).expanduser().resolve()


def default_armory_home() -> Path:
    configured = os.environ.get(DEFAULT_ARMORY_HOME_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".armories"


def initialize(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

    for dirname in ARMORY_DIRS:
        (path / dirname).mkdir(parents=True, exist_ok=True)

    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        created_at = datetime.now(UTC).isoformat()
        marker_path.write_text(
            f'version = {LAYOUT_VERSION}\ncreated_at = "{created_at}"\n',
            encoding="utf-8",
        )


def validate(path: Path) -> None:
    if not path.exists():
        raise ArmoryValidationError(f"armory does not exist: {path}")
    if not path.is_dir():
        raise ArmoryValidationError(f"path is not a directory: {path}")

    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        raise ArmoryValidationError(f"missing armory marker file: {marker_path}")

    missing_dirs = [dirname for dirname in ARMORY_DIRS if not (path / dirname).is_dir()]
    if missing_dirs:
        missing = ", ".join(missing_dirs)
        raise ArmoryValidationError(f"armory is missing required dirs: {missing}")


def read_marker(path: Path) -> dict[str, object]:
    marker_path = path / MARKER_FILE
    if not marker_path.exists():
        raise ArmoryValidationError(f"missing armory marker file: {marker_path}")
    with marker_path.open("rb") as f:
        return tomllib.load(f)
