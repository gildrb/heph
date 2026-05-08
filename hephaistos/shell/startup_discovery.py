from __future__ import annotations

from pathlib import Path

from hephaistos.armory.cli import default_armory_home
from hephaistos.armory.search import add_known_armory, load_known_armory_entries
from hephaistos.armory.storage import MARKER_FILE, ArmoryError
from hephaistos.chat.session import validate_armory_path


def discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass

    valid = [entry.path for entry in load_known_armory_entries() if entry.valid]
    if len(valid) == 1:
        return valid[0]

    armory_home = default_armory_home()
    if armory_home.is_dir():
        discovered: list[Path] = []
        for entry in armory_home.iterdir():
            if entry.is_dir() and (entry / MARKER_FILE).is_file():
                discovered.append(entry)
                add_known_armory(entry)
        if len(discovered) == 1 and not valid:
            return discovered[0]

    return None
