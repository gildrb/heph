from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from ai.runtime import ChatConfig
from harness.rag.chunker import Chunk, ChunkedDocument
from harness.rag.config import configured_embedding_model
from harness.rag.hybrid import HybridRetriever
from harness.rag.index import ArmoryIndex
from harness.rag.semantic import (
    EmbeddingUnavailableError,
    build_embedding_store,
)


def _chunk(index: int, text: str | None = None) -> Chunk:
    value = text or f"chunk {index}"
    return Chunk(value, "notes.md", index, 0, len(value))


class _EmbeddingClient:
    def __init__(self, *, fail_after: int | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_after = fail_after

    def embeddings_create(self, *, model: str, **kwargs: object) -> object:
        del model
        input_texts = kwargs["input"]
        assert isinstance(input_texts, list)
        typed_input = cast("list[str]", input_texts)
        self.calls.append(typed_input)
        if self.fail_after is not None and len(self.calls) > self.fail_after:
            raise RuntimeError("provider unavailable")
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    index=index,
                    embedding=[float(index + 1), float(len(text) + 1)],
                )
                for index, text in enumerate(typed_input)
            ]
        )

    @property
    def embeddings(self) -> object:
        return SimpleNamespace(create=self.embeddings_create)


def _config() -> ChatConfig:
    config = ChatConfig(base_url="https://provider.example/v1")
    config.apply_provider_reference("example", "EXAMPLE_API_KEY")
    return config


def test_embedding_sidecar_batches_requests_and_uses_secure_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _EmbeddingClient()
    monkeypatch.setattr("harness.rag.semantic.build_embeddings_client", lambda _config: client)
    chunks = [_chunk(index) for index in range(65)]

    store = build_embedding_store(tmp_path, chunks, _config(), "embed-model")

    assert store is not None
    assert [len(call) for call in client.calls] == [64, 1]
    sidecar = tmp_path / ".harness" / "rag_embeddings.json"
    assert sidecar.stat().st_mode & 0o777 == 0o600
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["complete"] is True
    assert payload["covered_chunks"] == 65


def test_embedding_query_vectors_are_batched_and_cached(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _EmbeddingClient()
    monkeypatch.setattr("harness.rag.semantic.build_embeddings_client", lambda _config: client)
    store = build_embedding_store(tmp_path, [_chunk(0), _chunk(1)], _config(), "embed-model")
    assert store is not None
    client.calls.clear()

    results = store.retrieve_many(["one", "two", "one"], top_k=1)
    store.retrieve("one", top_k=1)

    assert len(results) == 3
    assert len(client.calls) == 1
    assert client.calls[0] == ["one", "two"]


def test_embedding_sidecar_records_partial_progress_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _EmbeddingClient(fail_after=1)
    monkeypatch.setattr("harness.rag.semantic.build_embeddings_client", lambda _config: client)
    chunks = [_chunk(index) for index in range(65)]

    with pytest.raises(EmbeddingUnavailableError, match="Embedding request failed"):
        build_embedding_store(tmp_path, chunks, _config(), "embed-model")

    sidecar = tmp_path / ".harness" / "rag_embeddings.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["complete"] is False
    assert payload["covered_chunks"] == 64


def test_embedding_cache_identity_changes_with_provider_endpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _EmbeddingClient()
    monkeypatch.setattr("harness.rag.semantic.build_embeddings_client", lambda _config: client)
    chunks = [_chunk(0)]
    build_embedding_store(tmp_path, chunks, _config(), "embed-model")

    changed = ChatConfig(base_url="https://other.example/v1")
    changed.apply_provider_reference("other", "OTHER_API_KEY")
    build_embedding_store(tmp_path, chunks, changed, "embed-model")

    assert len(client.calls) == 2


def test_configured_embedding_model_uses_explicit_environment_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESS_EMBED_MODEL", "provider-embed")
    assert configured_embedding_model() == "provider-embed"
    monkeypatch.delenv("HARNESS_EMBED_MODEL")
    assert configured_embedding_model() is None


def test_hybrid_retrieval_reports_provider_degradation() -> None:
    index = ArmoryIndex(Path("/fake"))
    index.documents.append(
        ChunkedDocument(
            source="notes.md",
            chunks=[_chunk(0, "lexical fallback")],
            content_hash="x",
        )
    )

    class _BrokenRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[object]:
            raise RuntimeError("endpoint rejected embeddings")

    index.embedding_retriever = _BrokenRetriever()
    retriever = HybridRetriever(index, dense_weight=1.0)
    retriever.retrieve("query")

    assert retriever.embedding_warning is not None
    assert "lexical retrieval" in retriever.embedding_warning
