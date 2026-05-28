from __future__ import annotations

import os
from typing import Final

_PREFIX: Final[str] = "HEPHAION_"
_LEGACY_PREFIX: Final[str] = "HEPHAISTOS_"


def legacy_env_name(name: str) -> str:
    if not name.startswith(_PREFIX):
        return name
    return f"{_LEGACY_PREFIX}{name.removeprefix(_PREFIX)}"


def get_env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return value
    legacy_name = legacy_env_name(name)
    if legacy_name == name:
        return default
    return os.environ.get(legacy_name, default)
