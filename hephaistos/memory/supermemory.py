"""Supermemory-backed study memory.

This module keeps Supermemory optional. The local JSON store remains the
default, and callers can fall back to it whenever this backend is not enabled
or cannot reach the API.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.memory import MemoryEntry, MemoryStore
from hephaistos.parameters.settings import load_app_settings
from hephaistos.providers.keyring_store import resolve_key

_log = get_logger("memory.supermemory")

SUPERMEMORY_API_KEY_ENV = "SUPERMEMORY_API_KEY"
SUPERMEMORY_URL_ENV = "SUPERMEMORY_URL"
SUPERMEMORY_PROVIDER_SLUG = "supermemory"
SUPERMEMORY_DEFAULT_URL = "https://api.supermemory.ai"
SUPERMEMORY_DEFAULT_PROFILE = "heph-study"


class SupermemoryUnavailableError(RuntimeError):
    """Raised when Supermemory is requested but cannot be used."""


class SupermemorySearchResult(TypedDict, total=False):
    id: str
    memory: str
    chunk: str
    similarity: float
    metadata: dict[str, object]
    updatedAt: str


class SupermemorySearchPayload(TypedDict):
    results: list[SupermemorySearchResult]
    total: int


@dataclass(frozen=True)
class SupermemoryConfig:
    api_key: str
    base_url: str
    profile: str


def resolve_supermemory_key() -> str:
    """Resolve the Supermemory API key from keychain or environment."""
    key = resolve_key(SUPERMEMORY_PROVIDER_SLUG, SUPERMEMORY_API_KEY_ENV)
    if key:
        return key
    return os.environ.get(SUPERMEMORY_API_KEY_ENV, "").strip()


def supermemory_configured() -> bool:
    """Return whether Supermemory is enabled and has credentials."""
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


class SupermemoryClient:
    """Tiny stdlib REST client for the Supermemory API."""

    def __init__(self, config: SupermemoryConfig, *, timeout: float = 10.0) -> None:
        self.config = config
        self.timeout = timeout

    def add_document(
        self,
        *,
        content: str,
        container_tag: str,
        custom_id: str,
        metadata: Mapping[str, object],
    ) -> str:
        payload = {
            "content": content,
            "containerTag": container_tag,
            "customId": custom_id,
            "metadata": _flat_metadata(metadata),
        }
        data = self._request("POST", "/v3/documents", payload)
        raw_id = data.get("id", "") if is_string_mapping(data) else ""
        return raw_id if isinstance(raw_id, str) else ""

    def search(
        self,
        *,
        query: str,
        container_tag: str,
        limit: int,
        mode: Literal["hybrid", "memories"] = "hybrid",
    ) -> SupermemorySearchPayload:
        payload = {
            "q": query,
            "containerTag": container_tag,
            "searchMode": mode,
            "limit": limit,
        }
        data = self._request("POST", "/v4/search", payload)
        results: list[SupermemorySearchResult] = []
        if is_string_mapping(data):
            raw_results = data.get("results", [])
            if is_object_list(raw_results):
                for item in raw_results:
                    if not is_string_mapping(item):
                        continue
                    result = _coerce_search_result(item)
                    if result:
                        results.append(result)
            raw_total = data.get("total", len(results))
            total = raw_total if isinstance(raw_total, int) else len(results)
            return {"results": results, "total": total}
        return {"results": results, "total": 0}

    def _request(self, method: str, path: str, payload: Mapping[str, object]) -> object:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "hephaistos",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # nosec B310
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise SupermemoryUnavailableError(f"Supermemory API error: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise SupermemoryUnavailableError(
                f"Supermemory API unavailable: {exc.reason}"
            ) from exc
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SupermemoryUnavailableError("Supermemory API returned invalid JSON.") from exc


class SupermemoryStore(MemoryStore):
    """MemoryStore-compatible backend that reads/writes Supermemory."""

    def __init__(
        self,
        armory_path: Path,
        *,
        client: SupermemoryClient | None = None,
        config: SupermemoryConfig | None = None,
    ) -> None:
        super().__init__(armory_path)
        effective_config = config or load_supermemory_config()
        self.client = client or SupermemoryClient(effective_config)
        self.config = effective_config
        self.armory_tag = armory_container_tag(armory_path)
        self.profile_tag = profile_container_tag(effective_config.profile)
        self.backend = "supermemory"

    def load(self) -> bool:
        """Prime a small cache of known memory results."""
        payload = self.client.search(
            query="study concepts learned by the user",
            container_tag=self.armory_tag,
            limit=20,
            mode="memories",
        )
        self.entries = [_entry_from_result(result) for result in payload["results"]]
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
        self.client.add_document(
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
            self.client.add_document(
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
        payload = self.client.search(
            query="study topics learned by the user",
            container_tag=self.armory_tag,
            limit=50,
            mode="memories",
        )
        return [_entry_from_result(result).topic for result in payload["results"]]

    def build_system_context(self, *, max_entries: int = 20, max_chars: int = 3000) -> str:
        payloads = [
            self.client.search(
                query="study concepts already learned by the user",
                container_tag=self.armory_tag,
                limit=max_entries,
                mode="memories",
            ),
            self.client.search(
                query="cross subject study concepts already learned by the user",
                container_tag=self.profile_tag,
                limit=max_entries,
                mode="memories",
            ),
        ]
        entries: list[MemoryEntry] = []
        for payload in payloads:
            entries.extend(_entry_from_result(result) for result in payload["results"])
        self.entries = entries[:max_entries]
        return super().build_system_context(max_entries=max_entries, max_chars=max_chars)


def _coerce_search_result(data: Mapping[str, object]) -> SupermemorySearchResult | None:
    result: SupermemorySearchResult = {}
    for key in ("id", "memory", "chunk", "updatedAt"):
        raw = data.get(key)
        if isinstance(raw, str):
            result[key] = raw  # type: ignore[literal-required]
    similarity = data.get("similarity")
    if isinstance(similarity, int | float):
        result["similarity"] = float(similarity)
    metadata = data.get("metadata")
    if is_string_mapping(metadata):
        result["metadata"] = dict(metadata)
    return result if result.get("memory") or result.get("chunk") else None


def _entry_from_result(result: SupermemorySearchResult) -> MemoryEntry:
    metadata = result.get("metadata", {})
    topic = metadata.get("topic", "")
    source = metadata.get("source", "")
    confidence = metadata.get("confidence", "discussed")
    content = result.get("memory") or result.get("chunk") or ""
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


def _flat_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in metadata.items()
        if isinstance(value, str | int | float | bool)
    }
