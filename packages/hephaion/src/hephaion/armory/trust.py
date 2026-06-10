"""Path-scoped trust helpers for portable armory content."""

from __future__ import annotations

import os
from pathlib import Path


def armory_path_trusted(armory_path: Path, env_var: str) -> bool:
    """Return whether *env_var* explicitly trusts this resolved armory path."""
    requested = os.environ.get(env_var, "")
    if not requested.strip():
        return False
    trusted_paths = _trusted_paths(requested)
    if not trusted_paths:
        return False
    try:
        resolved_armory = armory_path.expanduser().resolve(strict=True)
    except OSError:
        return False
    return resolved_armory in trusted_paths


def _trusted_paths(raw_value: str) -> set[Path]:
    paths: set[Path] = set()
    for item in raw_value.split(os.pathsep):
        cleaned = item.strip()
        if not cleaned:
            continue
        try:
            path = Path(cleaned).expanduser().resolve(strict=True)
        except OSError:
            continue
        paths.add(path)
    return paths
