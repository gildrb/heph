"""Armory use-case functions."""

from __future__ import annotations

from hephaistos.armory.storage import initialize, validate
from hephaistos.armory.types import ArmoryInfo
from hephaistos.shared.paths import normalize_path


def init_armory(path_arg: str) -> str:
    """Initialize an armory and return a user-facing message."""
    armory_path = normalize_path(path_arg)
    initialize(armory_path)
    info = ArmoryInfo(path=armory_path)
    return f"Initialized armory at {info.path}"


def open_armory(path_arg: str) -> str:
    """Validate an armory and return a user-facing message."""
    armory_path = normalize_path(path_arg)
    validate(armory_path)
    info = ArmoryInfo(path=armory_path)
    return f"Opened armory {info.path}"

