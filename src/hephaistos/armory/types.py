"""Types and constants for armory feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ARMORY_DIRS = ("source", "library", "notes", "chats", "parameters", ".hephaistos")
MARKER_FILE = Path(".hephaistos/armory.toml")


@dataclass(frozen=True)
class ArmoryInfo:
    """Minimal armory identity data."""

    path: Path

