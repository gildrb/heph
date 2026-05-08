"""Dense embedding retrieval and cross-encoder reranking."""

from __future__ import annotations

import contextlib
import os

from hephaistos.rag import optional_backends
from hephaistos.rag.index import ArmoryIndex
from hephaistos.rag.optional_backends import (
    CrossEncoderProtocol,
    SentenceTransformerProtocol,
)
from hephaistos.rag.retrieval_types import ScoredChunk
from hephaistos.rag.scoring import cosine_similarity, embedding_rows, float_list

_EMBED_MODEL_ENV = "HEPHAISTOS_EMBED_MODEL"
_EMBED_MODEL_DEFAULT = "all-MiniLM-L6-v2"

_RERANK_MODEL_ENV = "HEPHAISTOS_RERANK_MODEL"
_RERANK_MODEL_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class EmbeddingRetriever:
    """Dense vector retriever using sentence-transformers embeddings."""

    def __init__(self, index: ArmoryIndex, model_name: str | None = None) -> None:
        self._index = index
        self._chunks = index.all_chunks
        self._model_name = model_name or os.environ.get(_EMBED_MODEL_ENV, _EMBED_MODEL_DEFAULT)
        self._embeddings: list[list[float]] | None = None
        self._model: SentenceTransformerProtocol | None = None

    def _ensure_model(self) -> SentenceTransformerProtocol:
        """Lazy-load the sentence-transformers model."""
        if self._model is not None:
            return self._model
        factory = optional_backends.sentence_transformer()
        if factory is None:
            raise RuntimeError("sentence-transformers is not installed")
        self._model = factory(self._model_name)
        return self._model

    def _ensure_embeddings(self) -> list[list[float]]:
        """Build chunk embeddings if not yet computed."""
        if self._embeddings is not None:
            return self._embeddings

        if not self._chunks:
            self._embeddings = []
            return self._embeddings

        cached = self._index.load_embeddings(self._model_name)
        if cached is not None and len(cached) == len(self._chunks):
            self._embeddings = cached
            return self._embeddings

        model = self._ensure_model()
        texts = [chunk.text for chunk in self._chunks]
        self._embeddings = embedding_rows(
            model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        )

        if self._embeddings:
            with contextlib.suppress(Exception):
                self._index.save_embeddings(self._embeddings, self._model_name)

        return self._embeddings

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return the top-k chunks by embedding cosine similarity."""
        if not self._chunks:
            return []

        embeddings = self._ensure_embeddings()
        model = self._ensure_model()
        query_rows = embedding_rows(
            model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        )
        if not query_rows:
            return []
        query_embedding = query_rows[0]
        scored: list[ScoredChunk] = []
        for i, chunk_embedding in enumerate(embeddings):
            sim = cosine_similarity(query_embedding, chunk_embedding)
            if sim > 0:
                scored.append(ScoredChunk(chunk=self._chunks[i], score=sim))

        scored.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
        return scored[:top_k]


class CrossEncoderReranker:
    """Cross-encoder re-ranker for improved retrieval precision."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.environ.get(_RERANK_MODEL_ENV, _RERANK_MODEL_DEFAULT)
        self._model: CrossEncoderProtocol | None = None

    @property
    def model_name(self) -> str:
        """Name of the cross-encoder model."""
        return self._model_name

    def _ensure_model(self) -> CrossEncoderProtocol:
        """Lazy-load the CrossEncoder model."""
        if self._model is not None:
            return self._model
        factory = optional_backends.cross_encoder()
        if factory is None:
            raise RuntimeError("sentence-transformers is not installed")
        self._model = factory(self._model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Re-score candidates with the cross-encoder and return top_k."""
        if not candidates:
            return []

        model = self._ensure_model()
        pairs = [(query, scored_chunk.chunk.text) for scored_chunk in candidates]
        scores = float_list(model.predict(pairs))
        scored = [
            ScoredChunk(chunk=candidates[i].chunk, score=float(scores[i]))
            for i in range(len(candidates))
        ]
        scored.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
        return scored[:top_k]
