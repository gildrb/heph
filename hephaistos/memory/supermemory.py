"""Opt-in Supermemory-backed study memory using the official SDK.

Supermemory is a remote memory backend.  Hephaistos uses it only when the user
has enabled Supermemory and configured a Supermemory-specific API key.  The
local JSON store remains the default and offline fallback.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.logging import get_logger
from hephaistos.memory import MemoryEntry, MemoryStore
from hephaistos.parameters.settings import load_app_settings
from hephaistos.providers.keyring_store import get_volatile, retrieve_key

if TYPE_CHECKING:
    from supermemory import Supermemory
    from supermemory.types.search_memories_response import (
        Result as SearchResult,
    )
    from supermemory.types.search_memories_response import (
        SearchMemoriesResponse,
    )

_log = get_logger("memory.supermemory")

SUPERMEMORY_API_KEY_ENV = "SUPERMEMORY_API_KEY"
SUPERMEMORY_URL_ENV = "SUPERMEMORY_URL"
SUPERMEMORY_PROVIDER_SLUG = "supermemory"
SUPERMEMORY_DEFAULT_URL = "https://api.supermemory.ai"
SUPERMEMORY_DEFAULT_PROFILE = "heph-study"


class SupermemoryUnavailableError(RuntimeError):
    """Raised when Supermemory is requested but cannot be used."""


@dataclass(frozen=True)
class SupermemoryConfig:
    api_key: str
    base_url: str
    profile: str


def resolve_supermemory_key() -> str:
    """Resolve only Supermemory-specific credentials."""
    key = retrieve_key(SUPERMEMORY_PROVIDER_SLUG)
    if key:
        return key
    env_key = os.environ.get(SUPERMEMORY_API_KEY_ENV, "").strip()
    if env_key:
        return env_key
    return get_volatile(SUPERMEMORY_PROVIDER_SLUG) or ""


def supermemory_configured() -> bool:
    """Return whether Supermemory is enabled and has credentials available."""
    settings = load_app_settings()
    return settings.supermemory_enabled and bool(resolve_supermemory_key())


def load_supermemory_config() -> SupermemoryConfig:
    """Load the effective Supermemory configuration or raise."""
    api_key = resolve_supermemory_key()
    if not api_key:
        raise SupermemoryUnavailableError("Supermemory API key is not configured.")
    settings = load_app_settings()
    return SupermemoryConfig(
        api_key=api_key,
        base_url=os.environ.get(SUPERMEMORY_URL_ENV, SUPERMEMORY_DEFAULT_URL).strip().rstrip("/"),
        profile=settings.supermemory_profile or SUPERMEMORY_DEFAULT_PROFILE,
    )


def _build_sdk_client(config: SupermemoryConfig) -> Supermemory:
    """Create an SDK client from config."""
    from supermemory import Supermemory

    return Supermemory(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=10.0,
        max_retries=2,
    )


def armory_container_tag(armory_path: Path) -> str:
    """Return a stable Supermemory container tag for an armory."""
    resolved = str(armory_path.expanduser().resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]
    return f"heph:armory:{digest}"


def profile_container_tag(profile: str) -> str:
    """Return a Supermemory container tag for a global study profile."""
    normalized = profile.strip() or SUPERMEMORY_DEFAULT_PROFILE
    safe = "".join(ch if ch.isalnum() or ch in "-_:" else "-" for ch in normalized)
    return f"heph:profile:{safe}"


def _sdk_add_document(
    client: Supermemory,
    *,
    content: str,
    container_tag: str,
    custom_id: str,
    metadata: dict[str, object],
) -> str:
    """Add a document via the SDK, wrapping errors."""
    from supermemory import APIConnectionError, APIStatusError

    flat: dict[str, str | float | bool] = {
        k: v for k, v in metadata.items() if isinstance(v, str | int | float | bool)
    }
    try:
        resp = client.add(
            content=content,
            container_tag=container_tag,
            custom_id=custom_id,
            metadata=flat,  # ty:ignore[invalid-argument-type]
        )
        return resp.id
    except APIConnectionError as exc:
        raise SupermemoryUnavailableError(f"Supermemory API unavailable: {exc}") from exc
    except APIStatusError as exc:
        raise SupermemoryUnavailableError(
            f"Supermemory API error: HTTP {exc.status_code}"
        ) from exc


def _sdk_search_memories(
    client: Supermemory,
    *,
    query: str,
    container_tag: str,
    limit: int,
) -> SearchMemoriesResponse:
    """Search memories via the SDK, wrapping errors."""
    from supermemory import APIConnectionError, APIStatusError

    try:
        return client.search.memories(
            q=query,
            container_tag=container_tag,
            limit=limit,
        )
    except APIConnectionError as exc:
        raise SupermemoryUnavailableError(f"Supermemory API unavailable: {exc}") from exc
    except APIStatusError as exc:
        raise SupermemoryUnavailableError(
            f"Supermemory API error: HTTP {exc.status_code}"
        ) from exc


class SupermemoryStore(MemoryStore):
    """MemoryStore-compatible backend that reads/writes Supermemory."""

    def __init__(
        self,
        armory_path: Path,
        *,
        client: Supermemory | None = None,
        config: SupermemoryConfig | None = None,
    ) -> None:
        super().__init__(armory_path)
        effective_config = config or load_supermemory_config()
        self._sdk_client = client or _build_sdk_client(effective_config)
        self.config = effective_config
        self.armory_tag = armory_container_tag(armory_path)
        self.profile_tag = profile_container_tag(effective_config.profile)
        self.backend = "supermemory"

    @property
    def client(self) -> Supermemory:
        return self._sdk_client

    def load(self) -> bool:
        """Prime a small cache of known memory results."""
        resp = _sdk_search_memories(
            self._sdk_client,
            query="study concepts learned by the user",
            container_tag=self.armory_tag,
            limit=20,
        )
        self.entries = [_entry_from_result(r) for r in resp.results]
        return True

    def save(self) -> Path:
        """Supermemory persists remotely as entries are added."""
        self._dirty = False
        return self._path

    def add(
        self,
        topic: str,
        content: str,
        *,
        source: str = "",
        confidence: str = "discussed",
        tags: list[str] | None = None,
    ) -> MemoryEntry | None:
        entry = MemoryEntry(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence,
            tags=tags or [],
        )
        custom_id = _custom_id(self.armory_tag, entry)
        _sdk_add_document(
            self._sdk_client,
            content=_document_content(entry),
            container_tag=self.armory_tag,
            custom_id=custom_id,
            metadata=_metadata(entry, self.config.profile, "armory"),
        )
        self.entries.append(entry)
        self._dirty = False
        _log.info("supermemory memory added", extra={"fields": {"topic": topic}})
        return entry

    def add_batch(
        self,
        entries: Sequence[Mapping[str, object]],
        *,
        source: str = "",
        confidence: str = "discussed",
    ) -> int:
        added = 0
        for raw in entries:
            topic = raw.get("topic", "")
            content = raw.get("content", "")
            if not isinstance(topic, str) or not isinstance(content, str):
                continue
            if not topic.strip() or not content.strip():
                continue
            raw_source = raw.get("source", source)
            raw_confidence = raw.get("confidence", confidence)
            result = self.add(
                topic.strip(),
                content.strip(),
                source=raw_source if isinstance(raw_source, str) else source,
                confidence=raw_confidence if isinstance(raw_confidence, str) else confidence,
            )
            if result is not None:
                added += 1
        return added

    def add_batch_to_profile(
        self,
        entries: Sequence[Mapping[str, object]],
        *,
        source: str = "",
        confidence: str = "discussed",
    ) -> int:
        """Add entries to the global cross-armory study profile."""
        added = 0
        for raw in entries:
            topic = raw.get("topic", "")
            content = raw.get("content", "")
            if not isinstance(topic, str) or not isinstance(content, str):
                continue
            if not topic.strip() or not content.strip():
                continue
            raw_source = raw.get("source", source)
            raw_confidence = raw.get("confidence", confidence)
            entry = MemoryEntry(
                topic=topic.strip(),
                content=content.strip(),
                source=raw_source if isinstance(raw_source, str) else source,
                confidence=raw_confidence if isinstance(raw_confidence, str) else confidence,
            )
            _sdk_add_document(
                self._sdk_client,
                content=_document_content(entry),
                container_tag=self.profile_tag,
                custom_id=_custom_id(self.profile_tag, entry),
                metadata=_metadata(entry, self.config.profile, "profile"),
            )
            added += 1
        return added

    def topics_covered(self) -> list[str]:
        if self.entries:
            return super().topics_covered()
        resp = _sdk_search_memories(
            self._sdk_client,
            query="study topics learned by the user",
            container_tag=self.armory_tag,
            limit=50,
        )
        return [_entry_from_result(r).topic for r in resp.results]

    def build_system_context(self, *, max_entries: int = 20, max_chars: int = 3000) -> str:
        armory_resp = _sdk_search_memories(
            self._sdk_client,
            query="study concepts already learned by the user",
            container_tag=self.armory_tag,
            limit=max_entries,
        )
        profile_resp = _sdk_search_memories(
            self._sdk_client,
            query="cross subject study concepts already learned by the user",
            container_tag=self.profile_tag,
            limit=max_entries,
        )
        entries: list[MemoryEntry] = [_entry_from_result(r) for r in armory_resp.results]
        entries.extend(_entry_from_result(r) for r in profile_resp.results)
        self.entries = entries[:max_entries]
        return super().build_system_context(max_entries=max_entries, max_chars=max_chars)


def _entry_from_result(result: SearchResult) -> MemoryEntry:
    metadata = result.metadata or {}
    topic = metadata.get("topic", "")
    source = metadata.get("source", "")
    confidence = metadata.get("confidence", "discussed")
    content = result.memory or result.chunk or ""
    return MemoryEntry(
        topic=topic if isinstance(topic, str) and topic else content[:80],
        content=content,
        source=source if isinstance(source, str) else "",
        confidence=confidence if isinstance(confidence, str) else "discussed",
    )


def _document_content(entry: MemoryEntry) -> str:
    return f"# {entry.topic}\n\n{entry.content}"


def _custom_id(container_tag: str, entry: MemoryEntry) -> str:
    raw = f"{container_tag}\n{entry.topic.lower().strip()}\n{entry.content.strip()}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"heph-{digest}"


def _metadata(entry: MemoryEntry, profile: str, scope: str) -> dict[str, object]:
    return {
        "app": "hephaistos",
        "topic": entry.topic[:100],
        "source": entry.source[:200],
        "confidence": entry.confidence,
        "profile": profile,
        "scope": scope,
        "created_at": int(entry.created_at or time.time()),
    }
