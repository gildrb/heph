"""Hybrid sparse+dense RAG retrieval."""

from __future__ import annotations

import math
import sys
from collections import Counter
from collections.abc import Callable
from typing import cast

from hephaistos.rag import optional_backends
from hephaistos.rag.index import ArmoryIndex
from hephaistos.rag.query_transform import (
    ModeSpecificQueryTransformerProtocol,
    QueryTransformerProtocol,
)
from hephaistos.rag.retrieval_types import RerankerProtocol, RetrieverProtocol, ScoredChunk
from hephaistos.rag.scoring import reciprocal_rank_fusion, tokenize
from hephaistos.rag.semantic import EmbeddingRetriever
from hephaistos.rag.sparse import Bm25Retriever, TfidfRetriever

_DEFAULT_EMBEDDING_RETRIEVER = EmbeddingRetriever
DEFAULT_PSEUDO_FEEDBACK_DOCS = 3
DEFAULT_PSEUDO_FEEDBACK_TERMS = 6
DEFAULT_PSEUDO_FEEDBACK_WEIGHT = 0.1


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
    def __init__(
        self,
        index: ArmoryIndex,
        embed_model: str | None = None,
        embed_query_prefix: str = "",
        embed_document_prefix: str = "",
        reranker: RerankerProtocol | None = None,
        *,
        candidate_multiplier: int = 3,
        sparse_weight: float = 1.0,
        dense_weight: float = 1.0,
        pseudo_feedback: bool = False,
        pseudo_feedback_docs: int = DEFAULT_PSEUDO_FEEDBACK_DOCS,
        pseudo_feedback_terms: int = DEFAULT_PSEUDO_FEEDBACK_TERMS,
        pseudo_feedback_weight: float = DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
        query_transformer: QueryTransformerProtocol | None = None,
    ) -> None:
        self._chunks = index.all_chunks
        bm25 = Bm25Retriever(index)
        self._sparse: RetrieverProtocol = bm25 if bm25.available else TfidfRetriever(index)
        self._embedding: EmbeddingRetriever | None = None
        self._reranker = reranker
        self._candidate_multiplier = candidate_multiplier
        self._sparse_weight = max(0.0, sparse_weight)
        self._dense_weight = max(0.0, dense_weight)
        self._pseudo_feedback = pseudo_feedback
        self._feedback_docs = max(1, pseudo_feedback_docs)
        self._feedback_terms = max(1, pseudo_feedback_terms)
        self._feedback_weight = max(0.0, pseudo_feedback_weight)
        self._feedback_idf: dict[str, float] | None = None
        self._feedback_tokens: dict[tuple[str, int], list[str]] = {}
        self._query_transformer = query_transformer

        if self._dense_weight > 0.0 and _sentence_transformers_available():
            try:
                factory = _embedding_retriever_factory()
                self._embedding = factory(
                    index,
                    model_name=embed_model,
                    query_prefix=embed_query_prefix,
                    document_prefix=embed_document_prefix,
                )
            except Exception:
                self._embedding = None

    @property
    def has_embeddings(self) -> bool:
        return self._embedding is not None

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        pool = top_k * self._candidate_multiplier
        mode_specific_transformer = (
            self._query_transformer
            if isinstance(self._query_transformer, ModeSpecificQueryTransformerProtocol)
            else None
        )
        if mode_specific_transformer is not None:
            candidates = self._retrieve_mode_specific(query, pool, mode_specific_transformer)
        else:
            queries = (
                self._query_transformer.transform(query) if self._query_transformer else [query]
            )
            candidates = self._retrieve_query_set(queries, pool)

        if self._reranker is not None:
            if not candidates:
                return []
            return self._reranker.rerank(query, candidates, top_k=top_k)

        return candidates[:top_k]

    def _retrieve_mode_specific(
        self,
        query: str,
        pool: int,
        transformer: ModeSpecificQueryTransformerProtocol,
    ) -> list[ScoredChunk]:
        sparse_queries = transformer.transform_sparse(query)
        dense_queries = transformer.transform_dense(query)

        sparse_results = self._retrieve_sparse_query_set(sparse_queries, pool)
        dense_results = self._retrieve_dense_query_set(dense_queries, pool)
        if not sparse_results and not dense_results:
            return []
        if not sparse_results:
            return dense_results
        if not dense_results:
            return sparse_results
        return reciprocal_rank_fusion(
            [sparse_results, dense_results],
            weights=[self._sparse_weight, self._dense_weight],
        )

    def _retrieve_sparse_query_set(self, queries: list[str], pool: int) -> list[ScoredChunk]:
        ranked = [results for query in queries if (results := self._sparse.retrieve(query, pool))]
        if not ranked:
            return []
        if len(ranked) == 1:
            return ranked[0]
        return reciprocal_rank_fusion(ranked)

    def _retrieve_dense_query_set(self, queries: list[str], pool: int) -> list[ScoredChunk]:
        if self._embedding is None:
            return []
        ranked: list[list[ScoredChunk]] = []
        try:
            for query in queries:
                results = self._embedding.retrieve(query, top_k=pool)
                if results:
                    ranked.append(results)
        except Exception:
            self._embedding = None
            return []
        if not ranked:
            return []
        if len(ranked) == 1:
            return ranked[0]
        return reciprocal_rank_fusion(ranked)

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
        sparse_results = self._sparse.retrieve(query, top_k=pool)
        feedback_results = self._pseudo_feedback_results(query, sparse_results, pool)

        if self._embedding is None:
            if not feedback_results:
                return sparse_results
            return reciprocal_rank_fusion(
                [sparse_results, feedback_results],
                weights=[self._sparse_weight, self._feedback_weight],
            )

        try:
            embed_results = self._embedding.retrieve(query, top_k=pool)
        except Exception:
            self._embedding = None
            if not feedback_results:
                return sparse_results
            return reciprocal_rank_fusion(
                [sparse_results, feedback_results],
                weights=[self._sparse_weight, self._feedback_weight],
            )

        if not sparse_results and not embed_results and not feedback_results:
            return []
        if not sparse_results and not feedback_results:
            return embed_results
        if not embed_results:
            if not feedback_results:
                return sparse_results
            return reciprocal_rank_fusion(
                [sparse_results, feedback_results],
                weights=[self._sparse_weight, self._feedback_weight],
            )

        ranked_lists = [sparse_results, embed_results]
        weights = [self._sparse_weight, self._dense_weight]
        if feedback_results:
            ranked_lists.append(feedback_results)
            weights.append(self._feedback_weight)
        return reciprocal_rank_fusion(ranked_lists, weights=weights)

    def _pseudo_feedback_results(
        self,
        query: str,
        sparse_results: list[ScoredChunk],
        pool: int,
    ) -> list[ScoredChunk]:
        if not self._pseudo_feedback or not sparse_results:
            return []
        feedback_query = self._feedback_query(query, sparse_results)
        if feedback_query == query:
            return []
        return self._sparse.retrieve(feedback_query, top_k=pool)

    def _feedback_query(self, query: str, sparse_results: list[ScoredChunk]) -> str:
        self._ensure_feedback_state()
        query_terms = set(tokenize(query))
        scored_terms: Counter[str] = Counter()
        for rank, result in enumerate(sparse_results[: self._feedback_docs], start=1):
            cached_terms = self._feedback_tokens.get((result.chunk.source, result.chunk.index))
            terms = cached_terms if cached_terms is not None else tokenize(result.chunk.text)
            terms = [*terms, *tokenize(result.chunk.source)]
            local_counts = Counter(
                term for term in terms if len(term) >= 3 and term not in query_terms
            )
            for term, count in local_counts.items():
                idf = 1.0 if self._feedback_idf is None else self._feedback_idf.get(term, 1.0)
                scored_terms[term] += (count * idf) / rank
        feedback_terms = [term for term, _score in scored_terms.most_common(self._feedback_terms)]
        if not feedback_terms:
            return query
        return " ".join([query, *feedback_terms])

    def _ensure_feedback_state(self) -> None:
        if self._feedback_idf is not None:
            return
        document_frequency: Counter[str] = Counter()
        for chunk in self._chunks:
            terms = tokenize("\n".join(part for part in (chunk.heading, chunk.text) if part))
            self._feedback_tokens[(chunk.source, chunk.index)] = terms
            document_frequency.update(set(terms))
        document_count = max(1, len(self._chunks))
        self._feedback_idf = {
            term: math.log((document_count + 1) / (frequency + 1)) + 1
            for term, frequency in document_frequency.items()
        }
