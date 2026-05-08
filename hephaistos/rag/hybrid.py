"""Hybrid sparse+dense RAG retrieval."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import cast

from hephaistos.rag import optional_backends
from hephaistos.rag.index import ArmoryIndex
from hephaistos.rag.query_transform import QueryTransformerProtocol
from hephaistos.rag.retrieval_types import RerankerProtocol, RetrieverProtocol, ScoredChunk
from hephaistos.rag.scoring import reciprocal_rank_fusion
from hephaistos.rag.semantic import EmbeddingRetriever
from hephaistos.rag.sparse import Bm25Retriever, TfidfRetriever

_DEFAULT_EMBEDDING_RETRIEVER = EmbeddingRetriever


def _sentence_transformers_available() -> bool:
    retrieve_module = sys.modules.get("hephaistos.rag.retrieve")
    helper = getattr(retrieve_module, "_is_sentence_transformers_available", None)
    if callable(helper):
        return bool(helper())
    return optional_backends.sentence_transformers_available()


def _embedding_retriever_factory() -> Callable[..., EmbeddingRetriever]:
    retrieve_module = sys.modules.get("hephaistos.rag.retrieve")
    factory = getattr(retrieve_module, "EmbeddingRetriever", None)
    if callable(factory) and factory is not _DEFAULT_EMBEDDING_RETRIEVER:
        return cast("Callable[..., EmbeddingRetriever]", factory)
    return EmbeddingRetriever


class HybridRetriever:
    """Hybrid retriever combining sparse and embedding retrieval via RRF."""

    def __init__(
        self,
        index: ArmoryIndex,
        embed_model: str | None = None,
        reranker: RerankerProtocol | None = None,
        *,
        candidate_multiplier: int = 3,
        query_transformer: QueryTransformerProtocol | None = None,
    ) -> None:
        bm25 = Bm25Retriever(index)
        self._sparse: RetrieverProtocol = bm25 if bm25.available else TfidfRetriever(index)
        self._embedding: EmbeddingRetriever | None = None
        self._reranker = reranker
        self._candidate_multiplier = candidate_multiplier
        self._query_transformer = query_transformer

        if _sentence_transformers_available():
            try:
                factory = _embedding_retriever_factory()
                self._embedding = factory(index, model_name=embed_model)
            except Exception:
                self._embedding = None

    @property
    def has_embeddings(self) -> bool:
        """Whether the embedding backend is active."""
        return self._embedding is not None

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Retrieve with sparse+dense fusion and optional reranking."""
        queries = self._query_transformer.transform(query) if self._query_transformer else [query]
        candidates = self._retrieve_query_set(queries, top_k * self._candidate_multiplier)

        if self._reranker is not None:
            if not candidates:
                return []
            return self._reranker.rerank(query, candidates, top_k=top_k)

        return candidates[:top_k]

    def _retrieve_query_set(self, queries: list[str], pool: int) -> list[ScoredChunk]:
        if len(queries) == 1:
            return self._retrieve_single(queries[0], pool)

        all_results = [
            results for query in queries if (results := self._retrieve_single(query, pool))
        ]
        if not all_results:
            return []
        if len(all_results) == 1:
            return all_results[0]
        return reciprocal_rank_fusion(all_results)

    def _retrieve_single(self, query: str, pool: int) -> list[ScoredChunk]:
        """Run sparse + optional embedding retrieval for a single query."""
        if self._embedding is None:
            return self._sparse.retrieve(query, top_k=pool)

        sparse_results = self._sparse.retrieve(query, top_k=pool)
        try:
            embed_results = self._embedding.retrieve(query, top_k=pool)
        except Exception:
            self._embedding = None
            return sparse_results

        if not sparse_results and not embed_results:
            return []
        if not sparse_results:
            return embed_results
        if not embed_results:
            return sparse_results

        return reciprocal_rank_fusion([sparse_results, embed_results])
