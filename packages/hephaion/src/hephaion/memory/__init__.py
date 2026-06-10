"""Armory-scoped learning memory."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from ai.logging import get_logger

from hephaion._types import is_object_list, is_string_mapping
from hephaion.armory.state_files import read_armory_state_text, write_armory_state_text

_log = get_logger("memory")

_MEMORY_FILE = "memory.json"
_ENTRY_CHAR_LIMIT = 2_000
_STORE_CHAR_LIMIT = 6_000
_CONFIDENCE_ORDER = {"extracted": 1, "discussed": 2, "verified": 3}
_INVISIBLE_CHARS = frozenset(
    {
        "\u200b",
        "\u200c",
        "\u200d",
        "\u2060",
        "\ufeff",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
    }
)
_MEMORY_THREAT_PATTERNS = (
    (r"ignore\s+(previous|all|above|prior)\s+instructions", "prompt_injection"),
    (r"disregard\s+(your|all|any)\s+(instructions|rules|guidelines)", "disregard_rules"),
    (r"system\s+prompt\s+override", "system_prompt_override"),
    (r"do\s+not\s+tell\s+the\s+user", "hidden_instruction"),
    (r"curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)", "exfil_curl"),
    (r"wget\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)", "exfil_wget"),
    (r"cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass|\.npmrc|\.pypirc)", "read_secrets"),
)


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
        return _split_tag_string(value)
    return _string_list(value)


def _split_tag_string(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _string_list(value: object) -> list[str]:
    if not is_object_list(value):
        return []
    return [item for item in value if isinstance(item, str)]


def _string_field(data: Mapping[str, object], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def _scan_memory_content(content: str) -> str | None:
    for char in _INVISIBLE_CHARS:
        if char in content:
            return f"Blocked: content contains invisible Unicode U+{ord(char):04X}."

    for pattern, pattern_id in _MEMORY_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return f"Blocked: content matches memory threat pattern '{pattern_id}'."

    return None


def _entry_text(entry: MemoryEntry) -> str:
    return " ".join((entry.topic, entry.content, entry.source, " ".join(entry.tags))).strip()


def _memory_entry_matches(entry: MemoryEntry, cleaned_query: str) -> bool:
    return not cleaned_query or cleaned_query in _entry_text(entry).lower()


def _entries_from_payload(payload: object) -> list[MemoryEntry] | None:
    if not is_string_mapping(payload):
        return None
    raw_entries = payload.get("entries", [])
    entry_list = raw_entries if is_object_list(raw_entries) else []
    return [MemoryEntry.from_dict(entry) for entry in entry_list if is_string_mapping(entry)]


def _loaded_entry_is_safe(entry: MemoryEntry) -> bool:
    if not entry.topic.strip() or not entry.content.strip():
        return False
    if len(entry.topic) + len(entry.content) > _ENTRY_CHAR_LIMIT:
        return False
    return _scan_memory_content(_entry_text(entry)) is None


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
        return self.armory_path / ".hephaion" / _MEMORY_FILE

    def load(self) -> bool:
        if not self._path.is_file():
            return False
        try:
            entries = _entries_from_payload(
                json.loads(read_armory_state_text(self.armory_path, ".hephaion/memory.json"))
            )
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
        if entries is None:
            _log.warning("memory load failed", extra={"fields": {"error": "invalid payload"}})
            return False
        self.entries = [entry for entry in entries if _loaded_entry_is_safe(entry)]
        self._log_loaded()
        return True

    def _log_loaded(self) -> None:
        _log.info(
            "memory loaded",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "entries": len(self.entries),
                }
            },
        )

    def save(self) -> Path:
        data = {
            "version": 1,
            "updated_at": time.time(),
            "entries": [e.to_dict() for e in self.entries],
        }
        path = write_armory_state_text(
            self.armory_path,
            ".hephaion/memory.json",
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
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
        return path

    def topics_covered(self) -> list[str]:
        return [e.topic for e in self.entries if e.topic]

    def _char_count(self, entries: Sequence[MemoryEntry] | None = None) -> int:
        selected_entries = self.entries if entries is None else entries
        return sum(len(_entry_text(entry)) for entry in selected_entries)

    def _entry_for_topic(self, topic: str) -> MemoryEntry | None:
        topic_lower = topic.casefold().strip()
        return next(
            (entry for entry in self.entries if entry.topic.casefold().strip() == topic_lower),
            None,
        )

    def _entry_from_fields(
        self,
        *,
        topic: str,
        content: str,
        source: str,
        confidence: str,
        tags: list[str] | None,
    ) -> MemoryEntry:
        return MemoryEntry(
            topic=topic.strip(),
            content=content.strip(),
            source=source.strip(),
            confidence=confidence.strip() or "discussed",
            tags=tags or [],
        )

    def read(self, query: str = "", *, limit: int = 20) -> list[MemoryEntry]:
        cleaned_query = query.lower().strip()
        matches = self._read_matches(cleaned_query, limit)
        for entry in matches:
            entry.access_count += 1
        if matches:
            self._dirty = True
        return matches

    def _read_matches(self, cleaned_query: str, limit: int) -> list[MemoryEntry]:
        matches: list[MemoryEntry] = []
        for entry in self.entries:
            if len(matches) >= limit:
                break
            if _memory_entry_matches(entry, cleaned_query):
                matches.append(entry)
        return matches

    def _unique_match_index(self, old_text: str) -> int | str:
        old_text = old_text.strip()
        if not old_text:
            return "old_text cannot be empty."

        matches = self._matching_entry_indices(old_text)
        if not matches:
            return f"No memory entry matched '{old_text}'."
        if self._has_ambiguous_matches(matches):
            return f"Multiple memory entries matched '{old_text}'. Use a more specific substring."
        return matches[0][0]

    def _matching_entry_indices(self, old_text: str) -> list[tuple[int, MemoryEntry]]:
        needle = old_text.casefold()
        return [
            (index, entry)
            for index, entry in enumerate(self.entries)
            if needle in _entry_text(entry).casefold()
        ]

    @staticmethod
    def _has_ambiguous_matches(matches: Sequence[tuple[int, MemoryEntry]]) -> bool:
        return len({_entry_text(entry) for _, entry in matches}) > 1

    def replace(
        self,
        old_text: str,
        *,
        topic: str,
        content: str,
        source: str = "",
        confidence: str = "discussed",
        tags: list[str] | None = None,
    ) -> MemoryEntry | str:
        replacement_error = self._validate_entry(topic, content)
        if replacement_error:
            return replacement_error
        index = self._unique_match_index(old_text)
        if isinstance(index, str):
            return index

        replacement = self._entry_from_fields(
            topic=topic.strip(),
            content=content.strip(),
            source=source.strip(),
            confidence=confidence.strip() or "discussed",
            tags=tags,
        )
        candidate_entries = list(self.entries)
        candidate_entries[index] = replacement
        if self._char_count(candidate_entries) > _STORE_CHAR_LIMIT:
            return f"Memory would exceed {_STORE_CHAR_LIMIT:,} chars. Shorten the entry first."

        self.entries[index] = replacement
        self._dirty = True
        return replacement

    def remove(self, old_text: str) -> int | str:
        index = self._unique_match_index(old_text)
        if isinstance(index, str):
            return index

        del self.entries[index]
        self._dirty = True
        return 1

    def _validate_entry(self, topic: str, content: str) -> str | None:
        topic = topic.strip()
        content = content.strip()
        if not topic:
            return "topic cannot be empty."
        if not content:
            return "content cannot be empty."
        if len(topic) + len(content) > _ENTRY_CHAR_LIMIT:
            return f"memory entry is too long ({_ENTRY_CHAR_LIMIT:,} char limit)."
        return _scan_memory_content(f"{topic}\n{content}")

    def add(
        self,
        topic: str,
        content: str,
        *,
        source: str = "",
        confidence: str = "discussed",
        tags: list[str] | None = None,
    ) -> MemoryEntry | None:
        validation_error = self._validate_entry(topic, content)
        if validation_error:
            _log.warning("memory rejected", extra={"fields": {"error": validation_error}})
            return None

        if existing := self._entry_for_topic(topic):
            return self._upgrade_confidence(existing, confidence, topic=topic)

        candidate_entry = self._entry_from_fields(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence,
            tags=tags,
        )
        if self._char_count([*self.entries, candidate_entry]) > _STORE_CHAR_LIMIT:
            _log.warning(
                "memory rejected",
                extra={"fields": {"error": "store limit exceeded", "topic": topic}},
            )
            return None

        self.entries.append(candidate_entry)
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
        return candidate_entry

    def _upgrade_confidence(
        self,
        entry: MemoryEntry,
        confidence: str,
        *,
        topic: str,
    ) -> MemoryEntry | None:
        if _CONFIDENCE_ORDER.get(confidence, 0) <= _CONFIDENCE_ORDER.get(entry.confidence, 0):
            return None
        entry.confidence = confidence
        self._dirty = True
        _log.debug(
            "memory confidence upgraded",
            extra={"fields": {"topic": topic, "confidence": confidence}},
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

        parts: list[str] = []
        used_chars = 0
        for entry in self._system_context_entries(max_entries):
            line = _system_context_line(entry)
            if used_chars + len(line) + 1 > max_chars:
                break
            parts.append(line)
            used_chars += len(line) + 1

        if not parts:
            return ""

        header = "Armory memory snapshot. Use sparingly as stable context, not source evidence:"
        return header + "\n" + "\n".join(parts)

    def _system_context_entries(self, max_entries: int) -> list[MemoryEntry]:
        confidence_order = {"verified": 0, "discussed": 1, "extracted": 2}
        return sorted(
            self.entries,
            key=lambda entry: (confidence_order.get(entry.confidence, 2), -entry.created_at),
        )[:max_entries]


def _system_context_line(entry: MemoryEntry) -> str:
    line = f"- [{entry.confidence}] {entry.topic}"
    if entry.content and len(entry.content) < 100:
        return f"{line}: {entry.content}"
    return line


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
