from __future__ import annotations

from pathlib import Path

from hephaion.armory.cli import default_armory_home
from hephaion.armory.search import (
    add_known_armory,
    discover_armory_home_entries,
    get_last_armory,
    load_available_armory_entries,
)
from hephaion.armory.storage import ArmoryError
from hephaion.chat.session import validate_armory_path


def _append_unique(paths: list[Path], seen: set[Path], path: Path) -> None:
    resolved = path.expanduser().resolve()
    if resolved in seen:
        return
    seen.add(resolved)
    paths.append(resolved)


def discover_available_armories() -> list[Path]:
    armories: list[Path] = []
    seen: set[Path] = set()
    for entry in load_available_armory_entries():
        if entry.valid:
            _append_unique(armories, seen, entry.path)

    armory_home = default_armory_home()
    if armory_home.is_dir():
        for entry in discover_armory_home_entries():
            _append_unique(armories, seen, entry.path)
            add_known_armory(entry.path)
    return armories


def discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass

    valid = discover_available_armories()
    last = get_last_armory()
    if last in valid:
        return last
    return valid[0] if len(valid) == 1 else None
