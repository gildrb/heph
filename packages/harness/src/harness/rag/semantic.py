"""Provider-backed semantic retrieval without a local ML runtime."""

from __future__ import annotations

import base64
import hashlib
import heapq
import json
import math
import operator
from array import array
from collections import OrderedDict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, cast

from ai.runtime import ChatConfig, build_embeddings_client

from harness.armory.state_files import (
    append_armory_state_text,
    read_armory_state_text,
    write_armory_state_text,
)
from harness.rag.config import EMBEDDING_BATCH_SIZE
from harness.rag.retrieval_types import ScoredChunk
from harness.rag.vector import embedding_rows

if TYPE_CHECKING:
    from openai import OpenAI

    from harness.rag.chunker import Chunk

_SIDECAR = ".harness/rag_embeddings.jsonl"
_CACHE_VERSION = 2
_NORMALIZATION = "l2"
_VECTOR_ENCODING = "float32-base64"
_QUERY_CACHE_SIZE = 32
_IDENTITY_KEYS = ("version", "provider", "endpoint", "model", "dimension", "normalization")


class EmbeddingUnavailableError(RuntimeError):
    """Raised when the configured provider cannot serve embeddings."""


def _endpoint(config: ChatConfig) -> str:
    return config.base_url.strip().rstrip("/")


def _text_hash(chunk: Chunk) -> str:
    return hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()


def _chunk_key(chunk: Chunk) -> str:
    return f"{chunk.source}#{chunk.index}"


def _normalize(values: Sequence[float]) -> array[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return array("f")
    return array("f", (value / norm for value in values))


def _pack_vector(values: Sequence[float]) -> str:
    return base64.b64encode(array("f", values).tobytes()).decode("ascii")


def _unpack_vector(value: object) -> array[float] | None:
    if not isinstance(value, str):
        return None
    try:
        vector = array("f")
        vector.frombytes(base64.b64decode(value, validate=True))
    except (ValueError, TypeError):
        return None
    return vector


def _sidecar_metadata(config: ChatConfig, model: str, dimension: int) -> dict[str, object]:
    return {
        "type": "metadata",
        "version": _CACHE_VERSION,
        "provider": config.provider_slug or "custom",
        "endpoint": _endpoint(config),
        "model": model,
        "dimension": dimension,
        "normalization": _NORMALIZATION,
        "vector_encoding": _VECTOR_ENCODING,
    }


def _sidecar_record(line: str) -> dict[str, object] | None:
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    return record if isinstance(record, dict) else None


def _collect_sidecar_records(
    metadata: dict[str, object],
    records: Sequence[dict[str, object]],
) -> dict[str, object]:
    entries: dict[str, dict[str, object]] = {}
    complete = False
    dimension = metadata.get("dimension", 0)
    for record in records:
        if record.get("type") == "chunk":
            key = record.get("key")
            if isinstance(key, str):
                entries[key] = record
        elif record.get("type") == "complete":
            complete = record.get("complete") is True
            dimension = record.get("dimension", dimension)
        elif record.get("type") == "checkpoint":
            dimension = record.get("dimension", dimension)
    return {
        **metadata,
        "dimension": dimension,
        "entries": entries,
        "complete": complete,
        "covered_chunks": len(entries),
    }


def _read_sidecar(armory_path: Path) -> dict[str, object]:
    try:
        lines = read_armory_state_text(armory_path, _SIDECAR).splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines:
        return {}
    metadata = _sidecar_record(lines[0])
    if metadata is None or metadata.get("type") != "metadata":
        return {}
    records = [record for line in lines[1:] if (record := _sidecar_record(line)) is not None]
    return _collect_sidecar_records(metadata, records)


def _write_metadata(armory_path: Path, metadata: dict[str, object]) -> None:
    write_armory_state_text(
        armory_path,
        _SIDECAR,
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")) + "\n",
    )


def _append_chunk(
    armory_path: Path,
    chunk: Chunk,
    vector: Sequence[float],
) -> None:
    record = {
        "type": "chunk",
        "key": _chunk_key(chunk),
        "text_hash": _text_hash(chunk),
        "vector": _pack_vector(vector),
    }
    append_armory_state_text(
        armory_path,
        _SIDECAR,
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n",
    )


def _append_complete(armory_path: Path, covered_chunks: int) -> None:
    append_armory_state_text(
        armory_path,
        _SIDECAR,
        json.dumps(
            {
                "type": "complete",
                "complete": True,
                "covered_chunks": covered_chunks,
                "dimension": _sidecar_dimension(_read_sidecar(armory_path)),
            },
            separators=(",", ":"),
        )
        + "\n",
    )


def _append_checkpoint(armory_path: Path, dimension: int, covered_chunks: int) -> None:
    append_armory_state_text(
        armory_path,
        _SIDECAR,
        json.dumps(
            {
                "type": "checkpoint",
                "dimension": dimension,
                "covered_chunks": covered_chunks,
            },
            separators=(",", ":"),
        )
        + "\n",
    )


def _matching_entries(
    sidecar: dict[str, object],
    metadata: dict[str, object],
) -> dict[str, dict[str, object]]:
    """Return entries only when every known cache identity field matches."""
    for key in _IDENTITY_KEYS:
        expected = metadata.get(key)
        actual = sidecar.get(key)
        if key == "dimension" and expected == 0:
            continue
        if actual != expected:
            return {}
    entries = sidecar.get("entries")
    if not isinstance(entries, dict):
        return {}
    return {
        key: cast("dict[str, object]", value)
        for key, value in entries.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def _sidecar_dimension(sidecar: dict[str, object]) -> int:
    value = sidecar.get("dimension", 0)
    return value if isinstance(value, int) else 0


def _embedding_inputs(
    chunks: Sequence[Chunk],
    entries: dict[str, dict[str, object]],
) -> list[Chunk]:
    return [
        chunk
        for chunk in chunks
        if (
            not isinstance(entry := entries.get(_chunk_key(chunk)), dict)
            or entry.get("text_hash") != _text_hash(chunk)
        )
    ]


def _request_embeddings(client: OpenAI, model: str, texts: Sequence[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=list(texts))
    return embedding_rows(
        [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    )


def _query_vectors(
    config: ChatConfig,
    model: str,
    dimension: int,
    queries: Sequence[str],
) -> dict[str, array[float]]:
    rows = _request_embeddings(build_embeddings_client(config), model, queries)
    if len(rows) != len(queries):
        raise EmbeddingUnavailableError(
            "Provider returned an incomplete query embedding response."
        )
    vectors: dict[str, array[float]] = {}
    for query, row in zip(queries, rows, strict=True):
        normalized = _normalize(row)
        if len(normalized) != dimension:
            raise EmbeddingUnavailableError("Query embedding dimension does not match the index.")
        vectors[query] = normalized
    return vectors


def _embed_missing_chunks(
    armory_path: Path,
    missing: Sequence[Chunk],
    entries: dict[str, dict[str, object]],
    config: ChatConfig,
    model: str,
    dimension: int,
    progress: Callable[[str, str], None] | None,
) -> tuple[dict[str, dict[str, object]], int]:
    client = build_embeddings_client(config)
    for start in range(0, len(missing), EMBEDDING_BATCH_SIZE):
        batch = missing[start : start + EMBEDDING_BATCH_SIZE]
        rows = _request_embeddings(client, model, [chunk.text for chunk in batch])
        if len(rows) != len(batch):
            raise EmbeddingUnavailableError(
                f"Provider returned {len(rows)} embeddings for {len(batch)} chunks."
            )
        for chunk, row in zip(batch, rows, strict=True):
            normalized = _normalize(row)
            if not normalized:
                raise EmbeddingUnavailableError("Provider returned a zero-length embedding.")
            if dimension and len(normalized) != dimension:
                raise EmbeddingUnavailableError("Embedding dimension changed during indexing.")
            dimension = len(normalized)
            _append_chunk(armory_path, chunk, normalized)
            entries[_chunk_key(chunk)] = {
                "type": "chunk",
                "key": _chunk_key(chunk),
                "text_hash": _text_hash(chunk),
                "vector": _pack_vector(normalized),
            }
        if progress is not None:
            progress(
                "embedded",
                f"{min(start + len(batch), len(missing))}/{len(missing)} chunks",
            )
        _append_checkpoint(armory_path, dimension, len(entries))
    return entries, dimension


def _embed_with_recovery(
    armory_path: Path,
    missing: Sequence[Chunk],
    entries: dict[str, dict[str, object]],
    config: ChatConfig,
    model: str,
    dimension: int,
    progress: Callable[[str, str], None] | None,
) -> tuple[dict[str, dict[str, object]], int]:
    try:
        return _embed_missing_chunks(
            armory_path,
            missing,
            entries,
            config,
            model,
            dimension,
            progress,
        )
    except Exception as exc:
        if isinstance(exc, EmbeddingUnavailableError):
            raise
        raise EmbeddingUnavailableError(f"Embedding request failed: {exc}") from exc


def build_embedding_store(
    armory_path: Path,
    chunks: Sequence[Chunk],
    config: ChatConfig | None,
    model: str | None,
    *,
    progress: Callable[[str, str], None] | None = None,
) -> EmbeddingRetriever | None:
    """Build or incrementally extend the provider-backed embedding sidecar."""
    if config is None or not model:
        return None
    metadata = _sidecar_metadata(config, model, 0)
    sidecar = _read_sidecar(armory_path)
    entries = _matching_entries(sidecar, metadata)
    missing = _embedding_inputs(chunks, entries)
    reused = len(chunks) - len(missing)
    if progress is not None:
        progress(
            "embedding_notice",
            f"{len(missing)} new chunk(s), {reused} reused; "
            f"endpoint={_endpoint(config)} model={model}",
        )
    if not missing and entries:
        return EmbeddingRetriever(
            chunks,
            entries,
            config,
            model,
            dimension=_sidecar_dimension(sidecar),
        )
    if not config.base_url:
        raise EmbeddingUnavailableError("No provider endpoint is configured for embeddings.")
    dimension = _sidecar_dimension(sidecar)
    if not entries:
        _write_metadata(armory_path, _sidecar_metadata(config, model, dimension))
    entries, dimension = _embed_with_recovery(
        armory_path,
        missing,
        entries,
        config,
        model,
        dimension,
        progress,
    )
    _append_complete(armory_path, len(entries))
    return EmbeddingRetriever(chunks, entries, config, model, dimension=dimension)


class EmbeddingRetriever:
    def __init__(
        self,
        chunks: Sequence[Chunk],
        entries: dict[str, dict[str, object]],
        config: ChatConfig,
        model: str,
        *,
        dimension: int,
    ) -> None:
        self._chunks = tuple(chunks)
        vectors_by_key = {
            key: vector
            for key, entry in entries.items()
            if (vector := _unpack_vector(entry.get("vector"))) is not None
        }
        self._chunk_vectors: tuple[tuple[Chunk, array[float]], ...] = tuple(
            (chunk, vectors_by_key[key])
            for chunk in self._chunks
            if (key := _chunk_key(chunk)) in vectors_by_key
        )
        self._config = config
        self._model = model
        self._dimension = dimension
        self._query_cache: OrderedDict[str, array[float]] = OrderedDict()

    def _cache_query_vectors(self, queries: Sequence[str]) -> dict[str, array[float]]:
        missing = [query for query in dict.fromkeys(queries) if query not in self._query_cache]
        if not missing:
            return {query: self._query_cache[query] for query in queries}
        fresh = _query_vectors(
            self._config,
            self._model,
            self._dimension,
            missing,
        )
        self._query_cache.update(fresh)
        while len(self._query_cache) > _QUERY_CACHE_SIZE:
            self._query_cache.popitem(last=False)
        return {
            query: self._query_cache[query] for query in queries if query in self._query_cache
        } | fresh

    def _embed_queries(self, queries: Sequence[str]) -> list[array[float]]:
        active = [query for query in queries if query.strip()]
        vectors = self._cache_query_vectors(active)
        return [vectors[query] for query in active]

    def retrieve_many(self, queries: Sequence[str], top_k: int = 5) -> list[list[ScoredChunk]]:
        vectors = self._embed_queries(queries)
        results: list[list[ScoredChunk]] = []
        for vector in vectors:
            scored = [
                (
                    chunk,
                    sum(map(operator.mul, vector, chunk_vector)),
                )
                for chunk, chunk_vector in self._chunk_vectors
            ]
            top_scored = heapq.nlargest(top_k, scored, key=lambda item: item[1])
            results.append([ScoredChunk(chunk=chunk, score=score) for chunk, score in top_scored])
        return results

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        results = self.retrieve_many([query], top_k=top_k)
        return results[0] if results else []


class CrossEncoderReranker:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Reranking is unavailable in the lean install; use lexical retrieval.")
