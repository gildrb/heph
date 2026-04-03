"""Arrow-key history with file-based persistence."""

from __future__ import annotations

import json
from pathlib import Path


class InputHistory:
    """Tracks user inputs and supports arrow-key navigation."""

    def __init__(self, entries: list[str] | None = None) -> None:
        self._entries: list[str] = entries or []
        self._index = -1  # -1 means "not navigating"

    @property
    def entries(self) -> list[str]:
        return list(self._entries)

    def add(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        # Deduplicate: if the same line was the last entry, skip
        if self._entries and self._entries[-1] == line:
            self._index = -1
            return
        self._entries.append(line)
        # Cap at 1000 entries
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]
        self._index = -1

    def up(self, current: str) -> str:
        """Move up in history. Returns the entry at the new position."""
        if not self._entries:
            return current
        if self._index == -1:
            self._index = len(self._entries) - 1
        elif self._index > 0:
            self._index -= 1
        return self._entries[self._index]

    def down(self, current: str) -> str:
        """Move down in history. Returns the entry or current if at bottom."""
        if self._index == -1:
            return current
        if self._index < len(self._entries) - 1:
            self._index += 1
            return self._entries[self._index]
        self._index = -1
        return current

    def reset_nav(self) -> None:
        self._index = -1

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._entries[-500:], indent=None) + "\n")

    @classmethod
    def load(cls, path: Path) -> InputHistory:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                return cls([str(e) for e in data])
        except (json.JSONDecodeError, OSError):
            pass
        return cls()
