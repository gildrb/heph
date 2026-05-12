"""Memory system: extract and persist learned concepts per armory.

The memory system ensures the agent does NOT repeat information the user
has already extracted or studied.  It works by:

1. **Extraction**: After each exchange, key concepts/facts are extracted
   from the conversation and stored as memory entries.
2. **Injection**: Before each LLM call, relevant memory entries are
   injected into the system prompt so the agent knows what's been covered.
3. **Deduplication**: New extractions are compared against existing memory
   to avoid storing duplicates.

Memory entries are stored per-armory in ``.hephaistos/memory.json`` and
carry:
- ``topic``: what this memory is about
- ``content``: the learned fact/concept
- ``source``: where it came from (document name, conversation, web)
- ``confidence``: "extracted" (from docs), "discussed" (from conversation),
  or "verified" (confirmed by user)
- ``created_at``: when it was stored
- ``access_count``: how many times it's been referenced (for relevance decay)

This is NOT a vector store — it's a structured knowledge base optimized
for a study agent that needs to know what the user already understands.
"""

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
    """Serialized representation of a memory entry."""

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


@dataclass
class MemoryEntry:
    """A single learned concept or fact."""

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
        raw_topic = data.get("topic", "")
        topic = raw_topic if isinstance(raw_topic, str) else ""
        raw_content = data.get("content", "")
        content = raw_content if isinstance(raw_content, str) else ""
        raw_source = data.get("source", "")
        source = raw_source if isinstance(raw_source, str) else ""
        raw_confidence = data.get("confidence", "discussed")
        confidence = raw_confidence if isinstance(raw_confidence, str) else "discussed"
        raw_created_at = data.get("created_at", 0.0)
        created_at = float(raw_created_at) if isinstance(raw_created_at, int | float) else 0.0
        raw_access_count = data.get("access_count", 0)
        access_count = raw_access_count if isinstance(raw_access_count, int) else 0
        return cls(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence,
            created_at=created_at,
            access_count=access_count,
            tags=_normalize_tags(data.get("tags", [])),
        )


class MemoryStore:
    """Persistent memory store for an armory.

    Stores learned concepts, tracks what the user has already covered,
    and prevents the agent from repeating information.
    """

    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.entries: list[MemoryEntry] = []
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaistos" / _MEMORY_FILE

    def load(self) -> bool:
        """Load memory from disk. Returns False if no memory file exists."""
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
        """Persist memory to disk."""
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
        """Return all topics the user has already studied."""
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
        """Add a memory entry. Returns None if it duplicates an existing entry."""
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
        """Add multiple entries at once. Returns the number actually added."""
        added = 0
        for entry in entries:
            raw_topic = entry.get("topic", "")
            topic = raw_topic if isinstance(raw_topic, str) else ""
            raw_content = entry.get("content", "")
            content = raw_content if isinstance(raw_content, str) else ""
            raw_source = entry.get("source", source)
            entry_source = raw_source if isinstance(raw_source, str) else source
            raw_confidence = entry.get("confidence", confidence)
            entry_confidence = raw_confidence if isinstance(raw_confidence, str) else confidence
            tags = _normalize_tags(entry.get("tags", []))
            result = self.add(
                topic=topic,
                content=content,
                source=entry_source,
                confidence=entry_confidence,
                tags=tags,
            )
            if result is not None:
                added += 1
        return added

    def build_system_context(self, *, max_entries: int = 20, max_chars: int = 3000) -> str:
        """Build a system-prompt section summarizing what the user already knows.

        This is injected into the system prompt so the agent knows what's
        been covered and avoids repeating it.
        """
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


from hephaistos.memory.supermemory import (  # noqa: E402
    SupermemoryStore,
    supermemory_configured,
)


def load_memory(armory_path: Path) -> MemoryStore:
    """Load memory for an armory.

    Uses Supermemory when an API key is available.  Falls back to the
    local JSON store when the key is missing or the API is unreachable.
    """
    try:
        if supermemory_configured():
            store = SupermemoryStore(armory_path)
            store.load()
            return store
    except Exception as exc:
        _log.warning(
            "supermemory unavailable, falling back to local memory",
            extra={"fields": {"error": str(exc)}},
        )
    store = MemoryStore(armory_path)
    store.load()
    return store


def save_memory(store: MemoryStore) -> Path:
    """Save memory if it has changed."""
    if store._dirty:
        return store.save()
    return store._path


__all__ = [
    "MemoryEntry",
    "MemoryEntryPayload",
    "MemoryStore",
    "SupermemoryStore",
    "load_memory",
    "save_memory",
    "supermemory_configured",
]
