"""Retrieval engine: pluggable retriever protocol with multiple backends.

Backends (selected automatically based on available dependencies):
- ``TfidfRetriever``     — pure-stdlib keyword scoring (always available)
- ``Bm25Retriever``      — BM25 sparse chunk retrieval via bm25s when available
- ``DocumentBm25Retriever`` — BM25 sparse document retrieval
- ``EmbeddingRetriever`` — dense vector similarity via sentence-transformers
- ``HybridRetriever``    — reciprocal-rank fusion of sparse + embeddings

Post-retrieval re-ranking (optional, requires sentence-transformers):
- ``CrossEncoderReranker`` — cross-encoder re-scoring for improved precision

The top-level ``retrieve()`` function auto-selects the best backend and
applies re-ranking when available: hybrid retrieval → RRF fusion →
cross-encoder re-ranking → top-k results.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import StrEnum
from typing import cast

from heph_ai.logging import get_logger

from hephaion.rag import optional_backends
from hephaion.rag.hybrid import (
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
    HybridRetriever,
)
from hephaion.rag.index import ArmoryIndex
from hephaion.rag.query_transform import (
    PromptFn,
    QueryTransformerProtocol,
    TransformStrategy,
    create_transformer,
)
from hephaion.rag.retrieval_types import (
    RerankerProtocol,
    RetrieverCacheKey,
    RetrieverProtocol,
    ScoredChunk,
)
from hephaion.rag.retrieve_compound import (
    _compound_query_variants,
    _merge_compound_query_results,
)
from hephaion.rag.scoring import tokenize
from hephaion.rag.semantic import CrossEncoderReranker, EmbeddingRetriever
from hephaion.rag.sparse import Bm25Retriever, DocumentBm25Retriever, TfidfRetriever

_log = get_logger("rag.retrieve")

_MAX_QUERY_TOKENS = 160
_QUERY_PREFIX_TOKENS = 40
_QUERY_SUFFIX_TOKENS = 140
_MAX_QUERY_TOKEN_REPEATS = 2
_MIN_NEAR_TOKEN_LENGTH = 5
_MAX_NEAR_TOKEN_VARIANTS = 12
_MAX_NEAR_TOKEN_VARIANTS_PER_TOKEN = 2
_NEGATION_PENALTY = 0.65
_NEGATION_MARKER_RE = re.compile(r"\b(?:no|not|never|without)\b", re.IGNORECASE)
_NEGATION_SEGMENT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_NEGATION_QUERY_OVERLAP_MIN = 2
_POST_PROCESS_CANDIDATE_MULTIPLIER = 2
_POST_PROCESS_MIN_EXTRA_CANDIDATES = 1
_SOURCE_MATCH_BOOST = 0.12
_SOURCE_MATCH_MAX_BOOST = 0.36
_EXPLICIT_HINT_BOOST = 8.0
_QUOTED_HINT_RE = re.compile(r'"([^"]+)"')
type _ScoreTransform = Callable[[ScoredChunk], float]


class RetrievalMode(StrEnum):
    AUTO = "auto"
    BM25 = "bm25"
    BM25_DOCUMENT = "bm25-document"
    DENSE = "dense"
    HYBRID = "hybrid"
    HYBRID_PRF = "hybrid-prf"
    HYBRID_RERANK = "hybrid-rerank"
    TFIDF = "tfidf"


_IDENTITY_CACHE_KEY = (
    TransformStrategy.IDENTITY.value,
    None,
    RetrievalMode.AUTO.value,
    3,
    None,
    None,
    "",
    "",
    1.0,
    1.0,
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
)


def _is_sentence_transformers_available() -> bool:
    return optional_backends.sentence_transformers_available()


def _create_retriever(
    index: ArmoryIndex,
    embed_model: str | None = None,
    embed_query_prefix: str = "",
    embed_document_prefix: str = "",
    rerank_model: str | None = None,
    query_transformer: QueryTransformerProtocol | None = None,
    retrieval_mode: RetrievalMode = RetrievalMode.AUTO,
    candidate_multiplier: int = 3,
    hybrid_sparse_weight: float = 1.0,
    hybrid_dense_weight: float = 1.0,
    pseudo_feedback_docs: int = DEFAULT_PSEUDO_FEEDBACK_DOCS,
    pseudo_feedback_terms: int = DEFAULT_PSEUDO_FEEDBACK_TERMS,
    pseudo_feedback_weight: float = DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
) -> TfidfRetriever | Bm25Retriever | DocumentBm25Retriever | EmbeddingRetriever | HybridRetriever:
    sparse_retriever = _explicit_sparse_retriever(index, retrieval_mode)
    if sparse_retriever is not None:
        return sparse_retriever
    if dense_retriever := _explicit_dense_retriever(
        index,
        retrieval_mode,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
    ):
        return dense_retriever
    if hybrid := _hybrid_retriever(
        index,
        retrieval_mode,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        query_transformer=query_transformer,
        candidate_multiplier=candidate_multiplier,
        hybrid_sparse_weight=hybrid_sparse_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
    ):
        return hybrid
    return _available_sparse_or_tfidf(index, Bm25Retriever(index))


def _explicit_sparse_retriever(
    index: ArmoryIndex,
    retrieval_mode: RetrievalMode,
) -> TfidfRetriever | Bm25Retriever | DocumentBm25Retriever | None:
    if retrieval_mode == RetrievalMode.TFIDF:
        return TfidfRetriever(index)
    if retrieval_mode == RetrievalMode.BM25:
        return _available_sparse_or_tfidf(index, Bm25Retriever(index))
    if retrieval_mode == RetrievalMode.BM25_DOCUMENT:
        return _available_sparse_or_tfidf(index, DocumentBm25Retriever(index))
    return None


def _explicit_dense_retriever(
    index: ArmoryIndex,
    retrieval_mode: RetrievalMode,
    *,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
) -> EmbeddingRetriever | None:
    if retrieval_mode != RetrievalMode.DENSE or not _is_sentence_transformers_available():
        return None
    return EmbeddingRetriever(
        index,
        model_name=embed_model,
        query_prefix=embed_query_prefix,
        document_prefix=embed_document_prefix,
    )


def _hybrid_retriever(
    index: ArmoryIndex,
    retrieval_mode: RetrievalMode,
    *,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
    query_transformer: QueryTransformerProtocol | None,
    candidate_multiplier: int,
    hybrid_sparse_weight: float,
    hybrid_dense_weight: float,
    pseudo_feedback_docs: int,
    pseudo_feedback_terms: int,
    pseudo_feedback_weight: float,
) -> HybridRetriever | None:
    if not _is_sentence_transformers_available():
        return None
    reranker = _hybrid_reranker(retrieval_mode, rerank_model)
    hybrid = HybridRetriever(
        index,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        reranker=reranker,
        candidate_multiplier=candidate_multiplier,
        sparse_weight=hybrid_sparse_weight,
        dense_weight=hybrid_dense_weight,
        pseudo_feedback=retrieval_mode == RetrievalMode.HYBRID_PRF,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
        query_transformer=query_transformer,
    )
    if hybrid.has_embeddings or (
        retrieval_mode == RetrievalMode.HYBRID_PRF and hybrid_dense_weight == 0.0
    ):
        return hybrid
    return None


def _hybrid_reranker(
    retrieval_mode: RetrievalMode,
    rerank_model: str | None,
) -> RerankerProtocol | None:
    if retrieval_mode not in (RetrievalMode.AUTO, RetrievalMode.HYBRID_RERANK):
        return None
    try:
        return CrossEncoderReranker(model_name=rerank_model)
    except Exception:
        return None


def _retriever_cache_key(
    *,
    transform_strategy: TransformStrategy,
    prompt_fn: PromptFn | None,
    retrieval_mode: RetrievalMode,
    candidate_multiplier: int,
    embed_model: str | None,
    rerank_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    hybrid_sparse_weight: float,
    hybrid_dense_weight: float,
    pseudo_feedback_docs: int,
    pseudo_feedback_terms: int,
    pseudo_feedback_weight: float,
) -> RetrieverCacheKey:
    prompt_key = None
    if transform_strategy in (TransformStrategy.HYDE, TransformStrategy.MULTI_QUERY):
        prompt_key = id(prompt_fn) if prompt_fn is not None else None
    return (
        transform_strategy.value,
        prompt_key,
        retrieval_mode.value,
        candidate_multiplier,
        embed_model,
        rerank_model,
        embed_query_prefix,
        embed_document_prefix,
        hybrid_sparse_weight,
        hybrid_dense_weight,
        pseudo_feedback_docs,
        pseudo_feedback_terms,
        pseudo_feedback_weight,
    )


def _cached_retriever(
    index: ArmoryIndex,
    cache_key: RetrieverCacheKey,
    *,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
    transformer: QueryTransformerProtocol | None,
    retrieval_mode: RetrievalMode,
    candidate_multiplier: int,
    hybrid_sparse_weight: float,
    hybrid_dense_weight: float,
    pseudo_feedback_docs: int,
    pseudo_feedback_terms: int,
    pseudo_feedback_weight: float,
) -> RetrieverProtocol:
    retriever = cast("RetrieverProtocol | None", index._retriever_cache.get(cache_key))
    if retriever is not None:
        return retriever

    if cache_key == _IDENTITY_CACHE_KEY:
        retriever = cast("RetrieverProtocol | None", index._retriever)
        if retriever is not None:
            index._retriever_cache[cache_key] = retriever
            return retriever

    retriever = _create_retriever(
        index,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        query_transformer=transformer,
        retrieval_mode=retrieval_mode,
        candidate_multiplier=candidate_multiplier,
        hybrid_sparse_weight=hybrid_sparse_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
    )
    if cache_key == _IDENTITY_CACHE_KEY:
        index._retriever = retriever
    index._retriever_cache[cache_key] = retriever
    return retriever


def _available_sparse_or_tfidf(
    index: ArmoryIndex,
    retriever: Bm25Retriever | DocumentBm25Retriever,
) -> TfidfRetriever | Bm25Retriever | DocumentBm25Retriever:
    return retriever if retriever.available else TfidfRetriever(index)


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


def _expand_query_with_corpus_token_variants(query: str, index: ArmoryIndex) -> str:
    query_tokens = _near_matchable_query_tokens(query)
    if not query_tokens:
        return query

    variants: list[str] = []
    variant_counts: dict[str, int] = {}
    for corpus_token in _corpus_tokens(index):
        if len(variants) >= _MAX_NEAR_TOKEN_VARIANTS:
            break
        if corpus_token in query_tokens or not _near_matchable_token(corpus_token):
            continue
        matched_query_token = _matching_query_token(corpus_token, query_tokens)
        if matched_query_token is None:
            continue
        count = variant_counts.get(matched_query_token, 0)
        if count >= _MAX_NEAR_TOKEN_VARIANTS_PER_TOKEN:
            continue
        variants.append(corpus_token)
        variant_counts[matched_query_token] = count + 1

    return f"{query} {' '.join(variants)}" if variants else query


def _near_matchable_query_tokens(query: str) -> tuple[str, ...]:
    seen: set[str] = set()
    tokens: list[str] = []
    for token in tokenize(query):
        if token in seen or not _near_matchable_token(token):
            continue
        seen.add(token)
        tokens.append(token)
    return tuple(tokens)


def _near_matchable_token(token: str) -> bool:
    return len(token) >= _MIN_NEAR_TOKEN_LENGTH


def _corpus_tokens(index: ArmoryIndex) -> tuple[str, ...]:
    seen: set[str] = set()
    tokens: list[str] = []
    for chunk in index.all_chunks:
        chunk_text = " ".join(part for part in (chunk.source, chunk.heading, chunk.text) if part)
        for token in tokenize(chunk_text):
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tuple(tokens)


def _matching_query_token(corpus_token: str, query_tokens: tuple[str, ...]) -> str | None:
    return next(
        (
            query_token
            for query_token in query_tokens
            if _near_token_match(query_token, corpus_token)
        ),
        None,
    )


def _near_token_match(left: str, right: str) -> bool:
    if left == right or abs(len(left) - len(right)) > 1:
        return False
    if len(left) == len(right):
        return _same_length_token_distance_at_most_one(left, right)
    shorter, longer = (left, right) if len(left) < len(right) else (right, left)
    return _single_insert_or_delete_token_match(shorter, longer)


def _same_length_token_distance_at_most_one(left: str, right: str) -> bool:
    mismatches = 0
    for left_char, right_char in zip(left, right, strict=True):
        if left_char == right_char:
            continue
        mismatches += 1
        if mismatches > 1:
            return False
    return mismatches == 1


def _single_insert_or_delete_token_match(shorter: str, longer: str) -> bool:
    skipped = False
    shorter_index = 0
    for longer_char in longer:
        if shorter_index < len(shorter) and shorter[shorter_index] == longer_char:
            shorter_index += 1
            continue
        if skipped:
            return False
        skipped = True
    return True


def _has_negation_marker(text: str) -> bool:
    return bool(_NEGATION_MARKER_RE.search(text))


def _has_query_relevant_negation(query_tokens: set[str], text: str) -> bool:
    if not query_tokens:
        return _has_negation_marker(text)

    overlap_threshold = min(_NEGATION_QUERY_OVERLAP_MIN, len(query_tokens))
    for segment in _NEGATION_SEGMENT_RE.split(text):
        if not _has_negation_marker(segment):
            continue
        segment_tokens = set(tokenize(segment))
        if len(query_tokens & segment_tokens) >= overlap_threshold:
            return True
    return False


def _apply_negation_precision_penalty(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    query_tokens = set(tokenize(query))
    if _has_negation_marker(query):
        return results
    return _rerank_with_score_transform(
        results,
        lambda result: (
            result.score * _NEGATION_PENALTY
            if _has_query_relevant_negation(query_tokens, result.chunk.text)
            else result.score
        ),
    )


def _apply_source_path_boost(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    query_tokens = set(tokenize(query))
    if not results or not query_tokens:
        return results
    return _rerank_with_score_transform(
        results,
        lambda result: result.score + _source_path_boost(result, query_tokens),
    )


def _source_path_boost(result: ScoredChunk, query_tokens: set[str]) -> float:
    overlap = query_tokens & set(tokenize(result.chunk.source))
    return min(_SOURCE_MATCH_MAX_BOOST, _SOURCE_MATCH_BOOST * len(overlap)) if overlap else 0.0


def _normalized_hint_text(value: str) -> str:
    return " ".join(tokenize(value))


def _explicit_query_hints(query: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (_quoted_query_hints(query), ())


def _quoted_query_hints(query: str) -> tuple[str, ...]:
    return tuple(
        normalized
        for raw_hint in _QUOTED_HINT_RE.findall(query)
        if (normalized := _normalized_quoted_hint(raw_hint))
    )


def _normalized_quoted_hint(raw_hint: str) -> str:
    hint = raw_hint.strip()
    if not hint:
        return ""
    normalized = _normalized_hint_text(hint)
    return normalized if len(normalized.split()) >= 3 else ""


def _apply_explicit_hint_boost(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    quoted_hints, source_section_hints = _explicit_query_hints(query)
    if not results or (not quoted_hints and not source_section_hints):
        return results

    return _rerank_with_score_transform(
        results,
        lambda result: (
            result.score
            + _explicit_hint_bonus(
                result,
                quoted_hints=quoted_hints,
                source_section_hints=source_section_hints,
            )
        ),
    )


def _rerank_with_score_transform(
    results: list[ScoredChunk],
    score_transform: _ScoreTransform,
) -> list[ScoredChunk]:
    reranked = [
        ScoredChunk(chunk=result.chunk, score=score_transform(result)) for result in results
    ]
    if any(new.score != old.score for old, new in zip(results, reranked, strict=True)):
        reranked.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return reranked


def _explicit_hint_bonus(
    result: ScoredChunk,
    *,
    quoted_hints: tuple[str, ...],
    source_section_hints: tuple[str, ...],
) -> float:
    return _hint_bonus(_chunk_hint_text(result), quoted_hints) + _hint_bonus(
        _normalized_hint_text(result.chunk.source), source_section_hints
    )


def _chunk_hint_text(result: ScoredChunk) -> str:
    return _normalized_hint_text(
        " ".join(part for part in (result.chunk.heading, result.chunk.text) if part)
    )


def _hint_bonus(text: str, hints: tuple[str, ...]) -> float:
    return _EXPLICIT_HINT_BOOST if any(hint in text for hint in hints) else 0.0


def _retrieval_pool_size(
    index: ArmoryIndex,
    retriever: RetrieverProtocol,
    *,
    requested_top_k: int,
    candidate_multiplier: int,
    diversify_sources: bool,
) -> int:
    if requested_top_k <= 0:
        return 0

    pool_size = requested_top_k * candidate_multiplier if diversify_sources else requested_top_k
    if isinstance(retriever, HybridRetriever):
        return pool_size

    pool_size = max(
        pool_size,
        requested_top_k * _POST_PROCESS_CANDIDATE_MULTIPLIER,
        requested_top_k + _POST_PROCESS_MIN_EXTRA_CANDIDATES,
    )
    chunk_count = len(index.all_chunks)
    return min(chunk_count, pool_size) if chunk_count > 0 else pool_size


def _retrieve_query_variants(
    retriever: RetrieverProtocol,
    query_variants: list[str],
    top_k: int,
) -> list[ScoredChunk]:
    if top_k <= 0:
        return []
    if len(query_variants) <= 1:
        return retriever.retrieve(query_variants[0], top_k)

    ranked_lists = _non_empty_variant_results(retriever, query_variants, top_k)
    if len(ranked_lists) > 1:
        return _merge_compound_query_results(ranked_lists, top_k)
    if ranked_lists:
        return ranked_lists[0][:top_k]
    return []


def _non_empty_variant_results(
    retriever: RetrieverProtocol,
    query_variants: list[str],
    top_k: int,
) -> list[list[ScoredChunk]]:
    return [
        results
        for query_variant in query_variants
        if (results := retriever.retrieve(query_variant, top_k))
    ]


def _diversify_by_source(results: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    best_by_source: dict[str, ScoredChunk] = {}
    for result in results:
        existing = best_by_source.get(result.chunk.source)
        if existing is None or result.score > existing.score:
            best_by_source[result.chunk.source] = result
    return sorted(
        best_by_source.values(),
        key=lambda scored_chunk: scored_chunk.score,
        reverse=True,
    )[:top_k]


def retrieve(
    query: str,
    index: ArmoryIndex,
    top_k: int = 5,
    *,
    transform_strategy: TransformStrategy = TransformStrategy.IDENTITY,
    prompt_fn: PromptFn | None = None,
    min_score: float = 0.0,
    retrieval_mode: RetrievalMode = RetrievalMode.AUTO,
    candidate_multiplier: int = 3,
    diversify_sources: bool = False,
    embed_model: str | None = None,
    embed_query_prefix: str = "",
    embed_document_prefix: str = "",
    rerank_model: str | None = None,
    hybrid_sparse_weight: float = 1.0,
    hybrid_dense_weight: float = 1.0,
    pseudo_feedback_docs: int = DEFAULT_PSEUDO_FEEDBACK_DOCS,
    pseudo_feedback_terms: int = DEFAULT_PSEUDO_FEEDBACK_TERMS,
    pseudo_feedback_weight: float = DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
) -> list[ScoredChunk]:
    transformer = None
    if transform_strategy != TransformStrategy.IDENTITY:
        transformer = create_transformer(transform_strategy, prompt_fn)

    candidate_multiplier = max(1, candidate_multiplier)
    hybrid_sparse_weight = max(0.0, hybrid_sparse_weight)
    hybrid_dense_weight = max(0.0, hybrid_dense_weight)
    pseudo_feedback_docs = max(1, pseudo_feedback_docs)
    pseudo_feedback_terms = max(1, pseudo_feedback_terms)
    pseudo_feedback_weight = max(0.0, pseudo_feedback_weight)
    cache_key = _retriever_cache_key(
        transform_strategy=transform_strategy,
        prompt_fn=prompt_fn,
        retrieval_mode=retrieval_mode,
        candidate_multiplier=candidate_multiplier,
        embed_model=embed_model,
        rerank_model=rerank_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        hybrid_sparse_weight=hybrid_sparse_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
    )
    retriever = _cached_retriever(
        index,
        cache_key,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        transformer=transformer,
        retrieval_mode=retrieval_mode,
        candidate_multiplier=candidate_multiplier,
        hybrid_sparse_weight=hybrid_sparse_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
    )
    requested_top_k = max(0, top_k)
    base_search_query = _normalize_query_for_retrieval(query)
    search_query = _normalize_query_for_retrieval(
        _expand_query_with_corpus_token_variants(base_search_query, index)
    )
    query_variants = _compound_query_variants(base_search_query)
    if query_variants[0] != search_query:
        query_variants = [search_query, *query_variants]
    retrieval_top_k = _retrieval_pool_size(
        index,
        retriever,
        requested_top_k=requested_top_k,
        candidate_multiplier=candidate_multiplier,
        diversify_sources=diversify_sources,
    )
    results = _retrieve_query_variants(retriever, query_variants, retrieval_top_k)
    results = _apply_negation_precision_penalty(search_query, results)
    results = _apply_source_path_boost(search_query, results)
    results = _apply_explicit_hint_boost(search_query, results)
    if diversify_sources:
        results = _diversify_by_source(results, requested_top_k)

    results = _filter_min_score(results, min_score)

    if not diversify_sources:
        results = results[:requested_top_k]

    _log_retrieve_results(
        query=query,
        search_query=search_query,
        query_variants=query_variants,
        top_k=top_k,
        retrieval_top_k=retrieval_top_k,
        results=results,
        diversify_sources=diversify_sources,
        retriever=retriever,
        retrieval_mode=retrieval_mode,
        candidate_multiplier=candidate_multiplier,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        hybrid_sparse_weight=hybrid_sparse_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        pseudo_feedback_docs=pseudo_feedback_docs,
        pseudo_feedback_terms=pseudo_feedback_terms,
        pseudo_feedback_weight=pseudo_feedback_weight,
        transform_strategy=transform_strategy,
        min_score=min_score,
    )
    return results


def _filter_min_score(results: list[ScoredChunk], min_score: float) -> list[ScoredChunk]:
    if min_score <= 0.0 or not results:
        return results

    filtered = [scored_chunk for scored_chunk in results if scored_chunk.score >= min_score]
    _log_min_score_filter(results, filtered, min_score)
    return filtered


def _log_min_score_filter(
    before: list[ScoredChunk],
    after: list[ScoredChunk],
    min_score: float,
) -> None:
    dropped = len(before) - len(after)
    if dropped:
        _log_dropped_low_score_chunks(dropped, kept=len(after), min_score=min_score)


def _log_dropped_low_score_chunks(dropped: int, *, kept: int, min_score: float) -> None:
    _log.debug(
        "retrieve: dropped low-score chunks",
        extra={
            "fields": {
                "dropped": dropped,
                "kept": kept,
                "min_score": min_score,
            }
        },
    )


def _log_retrieve_results(
    *,
    query: str,
    search_query: str,
    query_variants: list[str],
    top_k: int,
    retrieval_top_k: int,
    results: list[ScoredChunk],
    diversify_sources: bool,
    retriever: RetrieverProtocol,
    retrieval_mode: RetrievalMode,
    candidate_multiplier: int,
    embed_query_prefix: str,
    embed_document_prefix: str,
    hybrid_sparse_weight: float,
    hybrid_dense_weight: float,
    pseudo_feedback_docs: int,
    pseudo_feedback_terms: int,
    pseudo_feedback_weight: float,
    transform_strategy: TransformStrategy,
    min_score: float,
) -> None:
    _log.debug(
        "retrieve results",
        extra={
            "fields": {
                "query_len": len(query),
                "search_query_len": len(search_query),
                "query_variants": len(query_variants),
                "top_k": top_k,
                "retrieval_top_k": retrieval_top_k,
                "returned": len(results),
                "diversify_sources": diversify_sources,
                "retriever": type(retriever).__name__,
                "retrieval_mode": retrieval_mode.value,
                "candidate_multiplier": candidate_multiplier,
                "embed_query_prefix": embed_query_prefix,
                "embed_document_prefix": embed_document_prefix,
                "hybrid_sparse_weight": hybrid_sparse_weight,
                "hybrid_dense_weight": hybrid_dense_weight,
                "pseudo_feedback_docs": pseudo_feedback_docs,
                "pseudo_feedback_terms": pseudo_feedback_terms,
                "pseudo_feedback_weight": pseudo_feedback_weight,
                "transform_strategy": transform_strategy.value,
                "min_score": min_score,
            }
        },
    )
