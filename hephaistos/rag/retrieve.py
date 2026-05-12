"""Retrieval engine: pluggable retriever protocol with multiple backends.

Backends (selected automatically based on available dependencies):
- ``TfidfRetriever``     — pure-stdlib keyword scoring (always available)
- ``Bm25Retriever``      — BM25 sparse retrieval via bm25s when available
- ``EmbeddingRetriever`` — dense vector similarity via sentence-transformers
- ``HybridRetriever``    — reciprocal-rank fusion of sparse + embeddings

Post-retrieval re-ranking (optional, requires sentence-transformers):
- ``CrossEncoderReranker`` — cross-encoder re-scoring for improved precision

The top-level ``retrieve()`` function auto-selects the best backend and
applies re-ranking when available: hybrid retrieval → RRF fusion →
cross-encoder re-ranking → top-k results.
"""

from __future__ import annotations

from typing import cast

from hephaistos.logging import get_logger
from hephaistos.rag import optional_backends
from hephaistos.rag.hybrid import HybridRetriever
from hephaistos.rag.index import ArmoryIndex
from hephaistos.rag.query_transform import (
    PromptFn,
    QueryTransformerProtocol,
    TransformStrategy,
    create_transformer,
)
from hephaistos.rag.retrieval_types import RerankerProtocol, RetrieverProtocol, ScoredChunk
from hephaistos.rag.scoring import cosine_similarity, reciprocal_rank_fusion, tokenize
from hephaistos.rag.semantic import CrossEncoderReranker, EmbeddingRetriever
from hephaistos.rag.sparse import Bm25Retriever, TfidfRetriever

_log = get_logger("rag.retrieve")

_IDENTITY_CACHE_KEY = (TransformStrategy.IDENTITY.value, None)

_tokenize = tokenize
_cosine_similarity = cosine_similarity
_reciprocal_rank_fusion = reciprocal_rank_fusion
_EMBED_MODEL_ENV = "HEPHAISTOS_EMBED_MODEL"
_RERANK_MODEL_ENV = "HEPHAISTOS_RERANK_MODEL"
_MAX_QUERY_TOKENS = 160
_QUERY_PREFIX_TOKENS = 40
_QUERY_SUFFIX_TOKENS = 140
_MAX_QUERY_TOKEN_REPEATS = 2
_NEGATION_PENALTY = 0.65
_NEGATION_MARKERS = (
    " not ",
    " isn't ",
    " aren't ",
    " wasn't ",
    " weren't ",
    " does not ",
    " do not ",
    " did not ",
    " cannot ",
    " can't ",
    " unrelated to ",
    " different from ",
)
_SOURCE_MATCH_BOOST = 0.12
_SOURCE_MATCH_MAX_BOOST = 0.36
_SOURCE_INTENT_TOKENS = {
    "document",
    "documents",
    "exam",
    "file",
    "files",
    "howto",
    "indexed",
    "lecture",
    "material",
    "materials",
    "pdf",
    "pdfs",
    "project",
    "source",
    "sources",
}


def _is_sentence_transformers_available() -> bool:
    return optional_backends.sentence_transformers_available()


def _create_retriever(
    index: ArmoryIndex,
    embed_model: str | None = None,
    rerank_model: str | None = None,
    query_transformer: QueryTransformerProtocol | None = None,
) -> TfidfRetriever | Bm25Retriever | EmbeddingRetriever | HybridRetriever:
    """Create the best available retriever for the given index.

    Strategy:
    1. If sentence-transformers is available → ``HybridRetriever`` (sparse + embeddings)
       with an optional ``CrossEncoderReranker`` for post-retrieval re-scoring.
    2. Otherwise → ``Bm25Retriever`` when available, else ``TfidfRetriever``.

    A ``query_transformer`` can be attached to any retriever type.
    """
    if _is_sentence_transformers_available():
        reranker: RerankerProtocol | None = None
        try:
            reranker = CrossEncoderReranker(model_name=rerank_model)
        except Exception:
            reranker = None

        hybrid = HybridRetriever(
            index,
            embed_model=embed_model,
            reranker=reranker,
            query_transformer=query_transformer,
        )
        if hybrid.has_embeddings:
            return hybrid
    bm25 = Bm25Retriever(index)
    if bm25.available:
        return bm25
    return TfidfRetriever(index)


def _retriever_cache_key(
    transform_strategy: TransformStrategy,
    prompt_fn: PromptFn | None,
) -> tuple[str, int | None]:
    """Build a cache key for retrievers bound to a query-transform config."""
    prompt_key: int | None = None
    if transform_strategy in (TransformStrategy.HYDE, TransformStrategy.MULTI_QUERY):
        prompt_key = id(prompt_fn) if prompt_fn is not None else None
    return (transform_strategy.value, prompt_key)


def _normalize_query_for_retrieval(query: str) -> str:
    tokens = tokenize(query)
    if len(tokens) <= _MAX_QUERY_TOKENS:
        return query

    focused_tokens = [*tokens[:_QUERY_PREFIX_TOKENS], *tokens[-_QUERY_SUFFIX_TOKENS:]]
    counts: dict[str, int] = {}
    deduped: list[str] = []
    for token in focused_tokens:
        count = counts.get(token, 0)
        if count >= _MAX_QUERY_TOKEN_REPEATS:
            continue
        counts[token] = count + 1
        deduped.append(token)
    return " ".join(deduped) if deduped else query


def _has_negation_marker(text: str) -> bool:
    normalized = f" {text.lower()} "
    return any(marker in normalized for marker in _NEGATION_MARKERS)


def _query_is_negated(query: str) -> bool:
    return _has_negation_marker(query)


def _apply_negation_precision_penalty(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    """Down-rank negative contrast passages for affirmative factual queries.

    Sparse retrieval can over-rank a passage that says "X is not the answer"
    because it shares nearly every topical token with the question.  That kind
    of passage is useful context, but it should not outrank an affirmative
    answer for ordinary "what/which/how" questions.
    """
    if _query_is_negated(query):
        return results
    reranked: list[ScoredChunk] = []
    changed = False
    for result in results:
        if _has_negation_marker(result.chunk.text):
            reranked.append(
                ScoredChunk(chunk=result.chunk, score=result.score * _NEGATION_PENALTY)
            )
            changed = True
        else:
            reranked.append(result)
    if changed:
        reranked.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return reranked


def _apply_source_path_boost(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    query_tokens = set(tokenize(query))
    if not query_tokens or not results:
        return results
    if not (query_tokens & _SOURCE_INTENT_TOKENS):
        return results
    boosted: list[ScoredChunk] = []
    changed = False
    for result in results:
        source_tokens = set(tokenize(result.chunk.source))
        overlap = query_tokens & source_tokens
        if not overlap:
            boosted.append(result)
            continue
        boost = min(_SOURCE_MATCH_MAX_BOOST, _SOURCE_MATCH_BOOST * len(overlap))
        boosted.append(ScoredChunk(chunk=result.chunk, score=result.score + boost))
        changed = True
    if changed:
        boosted.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return boosted


def retrieve(
    query: str,
    index: ArmoryIndex,
    top_k: int = 5,
    *,
    transform_strategy: TransformStrategy = TransformStrategy.IDENTITY,
    prompt_fn: PromptFn | None = None,
    min_score: float = 0.0,
) -> list[ScoredChunk]:
    """Retrieve the top-k most relevant chunks for *query*.

    Automatically selects the best retriever backend based on available
    dependencies.  When *transform_strategy* is set to something other
    than ``IDENTITY``, the query is transformed before retrieval.

    LLM-based strategies (``HYDE``, ``MULTI_QUERY``) require *prompt_fn*
    to be provided — a callable that sends a prompt to the model and
    returns the text response.

    *min_score* filters out chunks whose relevance score falls below the
    threshold.  Set to 0.0 (default) to disable filtering.  Typical
    values: 0.1 for sparse retrieval, 0.15 for dense embeddings, 0.2
    when high precision is critical.  When all chunks score below the
    threshold an empty list is returned — the caller should inject a
    "no relevant documents" signal instead of garbage context.
    """
    # Build query transformer if requested
    transformer = None
    if transform_strategy != TransformStrategy.IDENTITY:
        transformer = create_transformer(transform_strategy, prompt_fn)

    cache_key = _retriever_cache_key(transform_strategy, prompt_fn)
    retriever = cast(
        "RetrieverProtocol | None",
        index._retriever_cache.get(cache_key),
    )
    if retriever is None:
        if cache_key == _IDENTITY_CACHE_KEY:
            retriever = cast(
                "RetrieverProtocol | None",
                index._retriever,
            )
        if retriever is None:
            retriever = _create_retriever(index, query_transformer=transformer)
            if cache_key == _IDENTITY_CACHE_KEY:
                index._retriever = retriever
        index._retriever_cache[cache_key] = retriever
    search_query = _normalize_query_for_retrieval(query)
    results = retriever.retrieve(search_query, top_k)
    results = _apply_negation_precision_penalty(search_query, results)
    results = _apply_source_path_boost(search_query, results)

    # Filter by minimum relevance score
    if min_score > 0.0 and results:
        before = len(results)
        results = [sc for sc in results if sc.score >= min_score]
        dropped = before - len(results)
        if dropped:
            _log.debug(
                "retrieve: dropped low-score chunks",
                extra={
                    "fields": {
                        "dropped": dropped,
                        "kept": len(results),
                        "min_score": min_score,
                    }
                },
            )

    _log.debug(
        "retrieve results",
        extra={
            "fields": {
                "query_len": len(query),
                "search_query_len": len(search_query),
                "top_k": top_k,
                "returned": len(results),
                "retriever": type(retriever).__name__,
                "transform_strategy": transform_strategy.value,
                "min_score": min_score,
            }
        },
    )
    return results
