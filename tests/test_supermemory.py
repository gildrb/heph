"""Tests for the Supermemory backend using the official SDK."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hephaistos.memory import MemoryStore, load_memory
from hephaistos.memory.supermemory import (
    SUPERMEMORY_API_KEY_ENV,
    SUPERMEMORY_PROVIDER_SLUG,
    SupermemoryConfig,
    SupermemoryStore,
    armory_container_tag,
    profile_container_tag,
    resolve_supermemory_key,
    supermemory_configured,
)
from hephaistos.parameters.settings import save_setting
from hephaistos.providers.keyring_store import set_volatile


def _fake_sdk_client() -> MagicMock:
    """Create a MagicMock that behaves like a supermemory.Supermemory client."""
    client = MagicMock()

    # client.add(...) -> AddResponse with id
    add_resp = MagicMock()
    add_resp.id = "fake-doc-id"
    client.add.return_value = add_resp

    # client.search.memories(...) -> SearchMemoriesResponse-like
    def _make_search_result(
        memory: str, topic: str, source: str = "conversation", confidence: str = "discussed"
    ) -> MagicMock:
        result = MagicMock()
        result.memory = memory
        result.chunk = None
        result.metadata = {
            "topic": topic,
            "source": source,
            "confidence": confidence,
        }
        return result

    result = _make_search_result(
        memory="TCP uses a three-way handshake.",
        topic="TCP handshake",
    )

    search_resp = MagicMock()
    search_resp.results = [result]
    search_resp.total = 1
    client.search.memories.return_value = search_resp

    return client


def _store(tmp_path: Path) -> tuple[SupermemoryStore, MagicMock]:
    sdk_client = _fake_sdk_client()
    store = SupermemoryStore(
        tmp_path,
        client=sdk_client,
        config=SupermemoryConfig(
            api_key="test-key",
            base_url="https://api.supermemory.ai",
            profile="heph-study",
        ),
    )
    return store, sdk_client


def test_container_tags_are_stable(tmp_path: Path) -> None:
    assert armory_container_tag(tmp_path) == armory_container_tag(tmp_path)
    assert armory_container_tag(tmp_path).startswith("heph:armory:")
    assert profile_container_tag("My Study Profile") == "heph:profile:My-Study-Profile"


def test_add_batch_writes_armory_documents(tmp_path: Path) -> None:
    store, sdk_client = _store(tmp_path)

    added = store.add_batch([{"topic": "HTTP", "content": "HyperText Transfer Protocol"}])

    assert added == 1
    sdk_client.add.assert_called_once()
    call_kwargs: dict[str, object] = sdk_client.add.call_args[1]
    assert call_kwargs["container_tag"] == store.armory_tag
    assert "# HTTP" in str(call_kwargs["content"])


def test_add_batch_to_profile_writes_global_profile(tmp_path: Path) -> None:
    store, sdk_client = _store(tmp_path)

    added = store.add_batch_to_profile([{"topic": "DNS", "content": "Domain name system"}])

    assert added == 1
    sdk_client.add.assert_called_once()
    call_kwargs: dict[str, object] = sdk_client.add.call_args[1]
    assert call_kwargs["container_tag"] == store.profile_tag
    metadata = call_kwargs["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["topic"] == "DNS"  # ty:ignore[invalid-argument-type]
    assert metadata["profile"] == "heph-study"  # ty:ignore[invalid-argument-type]
    assert metadata["scope"] == "profile"  # ty:ignore[invalid-argument-type]


def test_build_system_context_queries_armory_and_profile(tmp_path: Path) -> None:
    store, sdk_client = _store(tmp_path)

    context = store.build_system_context()

    assert "TCP handshake" in context
    assert sdk_client.search.memories.call_count == 2
    call_tags = {call[1]["container_tag"] for call in sdk_client.search.memories.call_args_list}
    assert call_tags == {store.armory_tag, store.profile_tag}


def test_load_primes_entries_from_search(tmp_path: Path) -> None:
    store, sdk_client = _store(tmp_path)

    result = store.load()

    assert result is True
    assert len(store.entries) == 1
    assert store.entries[0].topic == "TCP handshake"
    sdk_client.search.memories.assert_called_once()


def test_topics_covered_uses_search_when_no_entries(tmp_path: Path) -> None:
    store, sdk_client = _store(tmp_path)

    topics = store.topics_covered()

    assert topics == ["TCP handshake"]
    sdk_client.search.memories.assert_called_once()


def test_resolve_supermemory_key_ignores_global_llm_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAISTOS_API_KEY", "llm-provider-key")
    monkeypatch.delenv(SUPERMEMORY_API_KEY_ENV, raising=False)
    monkeypatch.setattr("hephaistos.memory.supermemory.retrieve_key", lambda _slug: None)

    assert resolve_supermemory_key() == ""


def test_resolve_supermemory_key_uses_supermemory_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("hephaistos.memory.supermemory.retrieve_key", lambda _slug: None)
    monkeypatch.setenv(SUPERMEMORY_API_KEY_ENV, "env-supermemory-key")

    assert resolve_supermemory_key() == "env-supermemory-key"

    monkeypatch.delenv(SUPERMEMORY_API_KEY_ENV)
    set_volatile(SUPERMEMORY_PROVIDER_SLUG, "volatile-supermemory-key")

    assert resolve_supermemory_key() == "volatile-supermemory-key"


def test_supermemory_disabled_uses_local_memory_even_with_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(SUPERMEMORY_API_KEY_ENV, "env-supermemory-key")
    save_setting("supermemory_enabled", False)

    assert not supermemory_configured()

    store = load_memory(tmp_path)

    assert type(store) is MemoryStore
