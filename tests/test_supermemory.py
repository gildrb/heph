"""Tests for the optional Supermemory backend."""

from __future__ import annotations

from pathlib import Path

from hephaistos.memory.supermemory import (
    SupermemoryConfig,
    SupermemoryStore,
    armory_container_tag,
    profile_container_tag,
)


class FakeSupermemoryClient:
    def __init__(self) -> None:
        self.documents: list[dict[str, object]] = []
        self.searches: list[dict[str, object]] = []

    def add_document(
        self,
        *,
        content: str,
        container_tag: str,
        custom_id: str,
        metadata: dict[str, object],
    ) -> str:
        self.documents.append(
            {
                "content": content,
                "container_tag": container_tag,
                "custom_id": custom_id,
                "metadata": metadata,
            }
        )
        return custom_id

    def search(
        self,
        *,
        query: str,
        container_tag: str,
        limit: int,
        mode: str = "hybrid",
    ) -> dict[str, object]:
        self.searches.append(
            {
                "query": query,
                "container_tag": container_tag,
                "limit": limit,
                "mode": mode,
            }
        )
        return {
            "results": [
                {
                    "memory": "TCP uses a three-way handshake.",
                    "metadata": {
                        "topic": "TCP handshake",
                        "source": "conversation",
                        "confidence": "discussed",
                    },
                }
            ],
            "total": 1,
        }


def _store(tmp_path: Path) -> tuple[SupermemoryStore, FakeSupermemoryClient]:
    client = FakeSupermemoryClient()
    store = SupermemoryStore(
        tmp_path,
        client=client,  # type: ignore[arg-type]
        config=SupermemoryConfig(
            api_key="test-key",
            base_url="https://api.supermemory.ai",
            profile="heph-study",
        ),
    )
    return store, client


def test_container_tags_are_stable(tmp_path: Path) -> None:
    assert armory_container_tag(tmp_path) == armory_container_tag(tmp_path)
    assert armory_container_tag(tmp_path).startswith("heph:armory:")
    assert profile_container_tag("My Study Profile") == "heph:profile:My-Study-Profile"


def test_add_batch_writes_armory_documents(tmp_path: Path) -> None:
    store, client = _store(tmp_path)

    added = store.add_batch([{"topic": "HTTP", "content": "HyperText Transfer Protocol"}])

    assert added == 1
    assert client.documents[0]["container_tag"] == store.armory_tag
    assert "# HTTP" in str(client.documents[0]["content"])


def test_add_batch_to_profile_writes_global_profile(tmp_path: Path) -> None:
    store, client = _store(tmp_path)

    added = store.add_batch_to_profile([{"topic": "DNS", "content": "Domain name system"}])

    assert added == 1
    assert client.documents[0]["container_tag"] == store.profile_tag
    metadata = client.documents[0]["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["topic"] == "DNS"
    assert metadata["profile"] == "heph-study"
    assert metadata["scope"] == "profile"


def test_build_system_context_queries_armory_and_profile(tmp_path: Path) -> None:
    store, client = _store(tmp_path)

    context = store.build_system_context()

    assert "TCP handshake" in context
    assert len(client.searches) == 2
    assert {search["container_tag"] for search in client.searches} == {
        store.armory_tag,
        store.profile_tag,
    }
