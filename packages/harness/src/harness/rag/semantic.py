"""Provider-backed semantic retrieval without a local ML runtime."""

from __future__ import annotations

import hashlib
import json
import math
from collections import OrderedDict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, cast

from ai.runtime import ChatConfig, build_embeddings_client

from harness.armory.state_files import read_armory_state_text, write_armory_state_text
from harness.rag.config import EMBEDDING_BATCH_SIZE
from harness.rag.retrieval_types import ScoredChunk
from harness.rag.vector import embedding_rows

if TYPE_CHECKING:
    from openai import OpenAI

    from harness.rag.chunker import Chunk

_SIDECAR = ".harness/rag_embeddings.json"
_CACHE_VERSION = 1
_NORMALIZATION = "l2"
_QUERY_CACHE_SIZE = 32


class EmbeddingUnavailableError(RuntimeError):
    """Raised when the configured provider cannot serve embeddings."""


def _endpoint(config: ChatConfig) -> str:
    return config.base_url.strip().rstrip("/")


def _text_hash(chunk: Chunk) -> str:
    return hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()


def _chunk_key(chunk: Chunk) -> str:
    return f"{chunk.source}#{chunk.index}"


def _normalize(values: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return []
    return [value / norm for value in values]


def _stored_vector(value: object) -> list[float] | None:
    if not isinstance(value, list) or not all(isinstance(item, int | float) for item in value):
        return None
    typed_value = cast("list[int | float]", value)
    return [float(item) for item in typed_value]


def _sidecar_metadata(config: ChatConfig, model: str, dimension: int) -> dict[str, object]:
    return {
        "version": _CACHE_VERSION,
        "provider": config.provider_slug or "custom",
        "endpoint": _endpoint(config),
        "model": model,
        "dimension": dimension,
        "normalization": _NORMALIZATION,
    }


def _read_sidecar(armory_path: Path) -> dict[str, object]:
    try:
        value = json.loads(read_armory_state_text(armory_path, _SIDECAR))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_sidecar(armory_path: Path, payload: dict[str, object]) -> None:
    write_armory_state_text(
        armory_path,
        _SIDECAR,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


def _matching_entries(
    sidecar: dict[str, object],
    metadata: dict[str, object],
) -> dict[str, dict[str, object]]:
    if any(
        sidecar.get(key) != value for key, value in metadata.items() if key != "dimension" or value
    ):
        return {}
    entries = sidecar.get("entries")
    if not isinstance(entries, dict):
        return {}
    result: dict[str, dict[str, object]] = {}
    for key, value in entries.items():
        if isinstance(key, str) and isinstance(value, dict):
            result[key] = cast("dict[str, object]", value)
    return result


def _sidecar_dimension(sidecar: dict[str, object]) -> int:
    value = sidecar.get("dimension", 0)
    return value if isinstance(value, int) else 0


def _save_partial(
    armory_path: Path,
    metadata: dict[str, object],
    entries: dict[str, dict[str, object]],
) -> None:
    _write_sidecar(
        armory_path,
        {
            **metadata,
            "complete": False,
            "covered_chunks": len(entries),
            "entries": entries,
        },
    )


def _request_embeddings(client: OpenAI, model: str, texts: Sequence[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=list(texts))
    return embedding_rows(
        [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    )


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
    metadata = _sidecar_metadata(config, model, dimension)
    _save_partial(armory_path, metadata, entries)
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
            entries[_chunk_key(chunk)] = {
                "text_hash": _text_hash(chunk),
                "vector": normalized,
            }
        metadata = _sidecar_metadata(config, model, dimension)
        _save_partial(armory_path, metadata, entries)
        if progress is not None:
            progress(
                "embedded",
                f"{min(start + len(batch), len(missing))}/{len(missing)} chunks",
            )
    return entries, dimension


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
        _save_partial(armory_path, _sidecar_metadata(config, model, dimension), entries)
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
        dimension = _sidecar_dimension(sidecar)
        return EmbeddingRetriever(chunks, entries, config, model, dimension=dimension)
    if not config.base_url:
        raise EmbeddingUnavailableError("No provider endpoint is configured for embeddings.")
    dimension = _sidecar_dimension(sidecar)
    entries, dimension = _embed_with_recovery(
        armory_path,
        missing,
        entries,
        config,
        model,
        dimension,
        progress,
    )
    _write_sidecar(
        armory_path,
        {
            **_sidecar_metadata(config, model, dimension),
            "complete": len(entries) == len(chunks),
            "covered_chunks": len(entries),
            "entries": entries,
        },
    )
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
        self._vectors: dict[str, list[float]] = {
            key: vector
            for key, entry in entries.items()
            if (vector := _stored_vector(entry.get("vector"))) is not None
        }
        self._config = config
        self._model = model
        self._dimension = dimension
        self._query_cache: OrderedDict[str, list[float]] = OrderedDict()

    def _cache_query_vectors(self, queries: Sequence[str]) -> None:
        missing = [query for query in dict.fromkeys(queries) if query not in self._query_cache]
        if not missing:
            return
        rows = _request_embeddings(
            build_embeddings_client(self._config),
            self._model,
            missing,
        )
        if len(rows) != len(missing):
            raise EmbeddingUnavailableError(
                "Provider returned an incomplete query embedding response."
            )
        for query, row in zip(missing, rows, strict=True):
            normalized = _normalize(row)
            if len(normalized) != self._dimension:
                raise EmbeddingUnavailableError(
                    "Query embedding dimension does not match the index."
                )
            self._query_cache[query] = normalized
            self._query_cache.move_to_end(query)
        while len(self._query_cache) > _QUERY_CACHE_SIZE:
            self._query_cache.popitem(last=False)

    def _embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        active = [query for query in queries if query.strip()]
        self._cache_query_vectors(active)
        return [self._query_cache[query] for query in active]

    def retrieve_many(self, queries: Sequence[str], top_k: int = 5) -> list[list[ScoredChunk]]:
        vectors = self._embed_queries(queries)
        results: list[list[ScoredChunk]] = []
        for vector in vectors:
            scored = [
                ScoredChunk(
                    chunk=chunk,
                    score=sum(
                        float(a) * float(b)
                        for a, b in zip(
                            vector,
                            self._vectors[_chunk_key(chunk)],
                            strict=True,
                        )
                    ),
                )
                for chunk in self._chunks
                if _chunk_key(chunk) in self._vectors
            ]
            scored.sort(key=lambda item: item.score, reverse=True)
            results.append(scored[:top_k])
        return results

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        results = self.retrieve_many([query], top_k=top_k)
        return results[0] if results else []


class CrossEncoderReranker:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Reranking is unavailable in the lean install; use lexical retrieval.")
