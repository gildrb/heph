"""Path helpers shared by multiple features."""

from __future__ import annotations

from pathlib import Path


def normalize_path(raw_path: str | Path) -> Path:
    """Expand and resolve a user path to an absolute path."""
    return Path(raw_path).expanduser().resolve()

