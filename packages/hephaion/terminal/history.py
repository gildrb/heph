"""Arrow-key history with file-based persistence."""

from __future__ import annotations

import json
from pathlib import Path


class InputHistory:
    def __init__(self, entries: list[str] | None = None) -> None:
        self._entries: list[str] = entries or []

    @property
    def entries(self) -> list[str]:
        return list(self._entries)

    def add(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        if self._entries and self._entries[-1] == line:
            return
        self._entries.append(line)
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._entries[-500:], indent=None) + "\n")

    @classmethod
    def load(cls, path: Path) -> InputHistory:
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text())
            if isinstance(raw, list):
                return cls([str(e) for e in raw])
        except (json.JSONDecodeError, OSError):
            pass
        return cls()
