from __future__ import annotations

from pathlib import Path

from hephaistos.armory.cli import default_armory_home
from hephaistos.armory.search import add_known_armory, get_last_armory, load_known_armory_entries
from hephaistos.armory.storage import MARKER_FILE, ArmoryError
from hephaistos.chat.session import validate_armory_path


def _append_unique(paths: list[Path], seen: set[Path], path: Path) -> None:
    resolved = path.expanduser().resolve()
    if resolved in seen:
        return
    seen.add(resolved)
    paths.append(resolved)


def discover_available_armories() -> list[Path]:
    armories: list[Path] = []
    seen: set[Path] = set()
    for entry in load_known_armory_entries():
        if entry.valid:
            _append_unique(armories, seen, entry.path)

    armory_home = default_armory_home()
    if armory_home.is_dir():
        for entry in sorted(armory_home.iterdir(), key=lambda path: path.name.lower()):
            if entry.is_dir() and (entry / MARKER_FILE).is_file():
                _append_unique(armories, seen, entry)
                add_known_armory(entry)
    return armories


def discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass

    last = get_last_armory()
    if last is not None:
        return last

    valid = discover_available_armories()
    return valid[0] if len(valid) == 1 else None
