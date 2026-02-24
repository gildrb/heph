"""Storage helpers for source feature."""

from __future__ import annotations

from pathlib import Path

from hephaistos.armory.types import ARMORY_DIRS


def source_root(armory_path: Path) -> Path:
    """Return source folder path for a given armory."""
    return armory_path / "source"


def ensure_armory_has_source_dir(armory_path: Path) -> None:
    """Ensure armory has expected source directory."""
    if "source" not in ARMORY_DIRS:
        raise RuntimeError("armory layout misconfigured: missing source dir constant")
    source_root(armory_path).mkdir(parents=True, exist_ok=True)

