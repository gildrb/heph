"""Armory-scoped learning memory."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger

_log = get_logger("memory")

_MEMORY_FILE = "memory.json"


class MemoryEntryPayload(TypedDict):
    topic: str
    content: str
    source: str
    confidence: str
    created_at: float
    access_count: int
    tags: list[str]


def _normalize_tags(value: object) -> list[str]:
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if not is_object_list(value):
        return []
    return [tag for tag in value if isinstance(tag, str)]


def _string_field(data: Mapping[str, object], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


@dataclass
class MemoryEntry:
    topic: str
    content: str
    source: str = ""
    confidence: str = "discussed"  # "extracted", "discussed", "verified"
    created_at: float = 0.0
    access_count: int = 0
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> MemoryEntryPayload:
        return {
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "access_count": self.access_count,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> MemoryEntry:
        raw_created_at = data.get("created_at", 0.0)
        created_at = float(raw_created_at) if isinstance(raw_created_at, int | float) else 0.0
        raw_access_count = data.get("access_count", 0)
        access_count = raw_access_count if isinstance(raw_access_count, int) else 0
        return cls(
            topic=_string_field(data, "topic"),
            content=_string_field(data, "content"),
            source=_string_field(data, "source"),
            confidence=_string_field(data, "confidence", "discussed"),
            created_at=created_at,
            access_count=access_count,
            tags=_normalize_tags(data.get("tags", [])),
        )


class MemoryStore:
    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.entries: list[MemoryEntry] = []
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaistos" / _MEMORY_FILE

    def load(self) -> bool:
        if not self._path.is_file():
            return False
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if not is_string_mapping(data):
                _log.warning("memory load failed", extra={"fields": {"error": "invalid payload"}})
                return False
            raw_entries = data.get("entries", [])
            entry_list = raw_entries if is_object_list(raw_entries) else []
            self.entries = [
                MemoryEntry.from_dict(entry) for entry in entry_list if is_string_mapping(entry)
            ]
            _log.info(
                "memory loaded",
                extra={
                    "fields": {
                        "armory": str(self.armory_path),
                        "entries": len(self.entries),
                    }
                },
            )
            return True
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning(
                "memory load failed",
                extra={
                    "fields": {
                        "error": str(exc),
                    }
                },
            )
            return False

    def save(self) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "updated_at": time.time(),
            "entries": [e.to_dict() for e in self.entries],
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._dirty = False
        _log.info(
            "memory saved",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "entries": len(self.entries),
                }
            },
        )
        return self._path

    def topics_covered(self) -> list[str]:
        return [e.topic for e in self.entries if e.topic]

    def add(
        self,
        topic: str,
        content: str,
        *,
        source: str = "",
        confidence: str = "discussed",
        tags: list[str] | None = None,
    ) -> MemoryEntry | None:
        topic_lower = topic.lower().strip()

        for existing in self.entries:
            if existing.topic.lower().strip() == topic_lower:
                confidence_order = {"extracted": 1, "discussed": 2, "verified": 3}
                if confidence_order.get(confidence, 0) > confidence_order.get(
                    existing.confidence, 0
                ):
                    existing.confidence = confidence
                    self._dirty = True
                    _log.debug(
                        "memory confidence upgraded",
                        extra={
                            "fields": {
                                "topic": topic,
                                "confidence": confidence,
                            }
                        },
                    )
                    return existing
                return None

        entry = MemoryEntry(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence,
            tags=tags or [],
        )
        self.entries.append(entry)
        self._dirty = True
        _log.info(
            "memory added",
            extra={
                "fields": {
                    "topic": topic,
                    "source": source,
                    "confidence": confidence,
                }
            },
        )
        return entry

    def add_batch(
        self,
        entries: Sequence[Mapping[str, object]],
        *,
        source: str = "",
        confidence: str = "discussed",
    ) -> int:
        added = 0
        for entry in entries:
            tags = _normalize_tags(entry.get("tags", []))
            result = self.add(
                topic=_string_field(entry, "topic"),
                content=_string_field(entry, "content"),
                source=_string_field(entry, "source", source),
                confidence=_string_field(entry, "confidence", confidence),
                tags=tags,
            )
            if result is not None:
                added += 1
        return added

    def build_system_context(self, *, max_entries: int = 20, max_chars: int = 3000) -> str:
        if not self.entries:
            return ""

        # Prioritize: verified > discussed > extracted, then most recent
        confidence_order = {"verified": 0, "discussed": 1, "extracted": 2}
        sorted_entries = sorted(
            self.entries,
            key=lambda e: (confidence_order.get(e.confidence, 2), -e.created_at),
        )

        parts: list[str] = []
        used_chars = 0
        for entry in sorted_entries[:max_entries]:
            line = f"- [{entry.confidence}] {entry.topic}"
            if entry.content and len(entry.content) < 100:
                line += f": {entry.content}"
            if used_chars + len(line) + 1 > max_chars:
                break
            parts.append(line)
            used_chars += len(line) + 1

        if not parts:
            return ""

        header = (
            "The user has already studied these topics (do NOT repeat this material unless asked):"
        )
        return header + "\n" + "\n".join(parts)


def load_memory(armory_path: Path) -> MemoryStore:
    """Load local memory for an armory."""
    store = MemoryStore(armory_path)
    store.load()
    return store


def save_memory(store: MemoryStore) -> Path:
    if store._dirty:
        return store.save()
    return store._path


__all__ = [
    "MemoryEntry",
    "MemoryEntryPayload",
    "MemoryStore",
    "load_memory",
    "save_memory",
]
