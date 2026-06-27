"""Symlink-safe JSON persistence helpers for armory RAG state."""

from __future__ import annotations

import json
from pathlib import Path

from harness._types import is_string_mapping
from harness.armory.state_files import (
    armory_state_location,
    read_armory_state_text,
    write_armory_state_text,
)


def read_index_json_mapping(path: Path) -> dict[str, object] | None:
    try:
        armory_path, rel_path = armory_state_location(path)
        data: object = json.loads(read_armory_state_text(armory_path, rel_path))
    except (json.JSONDecodeError, OSError):
        return None
    return data if is_string_mapping(data) else None


def write_armory_index_json(
    armory_path: Path,
    path: Path,
    payload: object,
    *,
    indent: int | None = None,
) -> None:
    write_armory_state_text(
        armory_path,
        path.relative_to(armory_path),
        json.dumps(payload, ensure_ascii=False, indent=indent),
    )
