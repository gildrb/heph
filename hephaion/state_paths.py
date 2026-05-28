from __future__ import annotations

import contextlib
from pathlib import Path

INTERNAL_DIR = ".hephaion"
LEGACY_INTERNAL_DIR = ".hephaistos"
MARKER_FILE = Path(INTERNAL_DIR) / "armory.toml"
LEGACY_MARKER_FILE = Path(LEGACY_INTERNAL_DIR) / "armory.toml"


def internal_dir(path: Path) -> Path:
    return path / INTERNAL_DIR


def state_path(path: Path, *parts: str) -> Path:
    return internal_dir(path).joinpath(*parts)


def legacy_state_path(path: Path, *parts: str) -> Path:
    return path.joinpath(LEGACY_INTERNAL_DIR, *parts)


def existing_state_path(path: Path, *parts: str) -> Path:
    current = state_path(path, *parts)
    if current.exists():
        return current
    legacy = legacy_state_path(path, *parts)
    return legacy if legacy.exists() else current


def legacy_layout_exists(path: Path) -> bool:
    return (path / LEGACY_MARKER_FILE).exists()


def is_armory_path(path: Path) -> bool:
    return (path / MARKER_FILE).is_file() or (path / LEGACY_MARKER_FILE).is_file()


def migrate_legacy_layout(path: Path) -> None:
    legacy_dir = path / LEGACY_INTERNAL_DIR
    current_dir = path / INTERNAL_DIR
    if not legacy_dir.is_dir():
        return
    if not current_dir.exists():
        legacy_dir.rename(current_dir)
        return
    if not current_dir.is_dir():
        return
    for child in legacy_dir.iterdir():
        target = current_dir / child.name
        if not target.exists():
            child.rename(target)
        elif child.is_dir() and target.is_dir():
            _merge_directory(child, target)
    with contextlib.suppress(OSError):
        legacy_dir.rmdir()


def _merge_directory(source: Path, target: Path) -> None:
    for child in source.iterdir():
        child_target = target / child.name
        if not child_target.exists():
            child.rename(child_target)
        elif child.is_dir() and child_target.is_dir():
            _merge_directory(child, child_target)
    with contextlib.suppress(OSError):
        source.rmdir()
