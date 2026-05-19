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
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from hephaistos.logging import get_logger
from hephaistos.rag import optional_backends
from hephaistos.rag.hybrid import (
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
    HybridRetriever,
)
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
from hephaistos.rag.sparse import Bm25Retriever, DocumentBm25Retriever, TfidfRetriever

_log = get_logger("rag.retrieve")

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
_NEGATION_QUERY_INTENT_TOKENS = frozenset(
    {
        "abstain",
        "abstention",
        "absent",
        "lack",
        "lacking",
        "missing",
        "unsupported",
        "unanswered",
    }
)
_NEGATION_SEGMENT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_NEGATION_QUERY_OVERLAP_MIN = 2
_POST_PROCESS_CANDIDATE_MULTIPLIER = 3
_POST_PROCESS_MIN_EXTRA_CANDIDATES = 4
_SOURCE_MATCH_BOOST = 0.12
_SOURCE_MATCH_MAX_BOOST = 0.36
_EXPLICIT_HINT_BOOST = 8.0
_QUOTED_HINT_RE = re.compile(r'"([^"]+)"')
_SOURCE_SECTION_HINT_RE = re.compile(r'\bsource\s+section\s+"([^"]+)"', re.IGNORECASE)
_COMPOUND_BOTH_FOCUS_RE = re.compile(r"\bboth\b:?\s*(?P<focus>.+)", re.IGNORECASE)
_COMPOUND_SPLIT_RE = re.compile(r"\s*,?\s+(?:and|und)\s+|[;]")
_MIN_COMPOUND_QUERY_TOKENS = 3
_MAX_COMPOUND_QUERY_PARTS = 4
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


@dataclass(frozen=True, slots=True)
class _CompoundMergeEntry:
    scored_chunk: ScoredChunk
    best_score: float
    first_list_index: int
    best_rank: int


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
    """Create the best available retriever for the given index.

    Strategy:
    1. If sentence-transformers is available → ``HybridRetriever`` (sparse + embeddings)
       with an optional ``CrossEncoderReranker`` for post-retrieval re-scoring.
    2. Otherwise → ``Bm25Retriever`` when available, else ``TfidfRetriever``.

    A ``query_transformer`` can be attached to any retriever type.
    """
    if retrieval_mode == RetrievalMode.TFIDF:
        return TfidfRetriever(index)
    if retrieval_mode == RetrievalMode.BM25:
        bm25_only = Bm25Retriever(index)
        if bm25_only.available:
            return bm25_only
        return TfidfRetriever(index)
    if retrieval_mode == RetrievalMode.BM25_DOCUMENT:
        bm25_document = DocumentBm25Retriever(index)
        if bm25_document.available:
            return bm25_document
        return TfidfRetriever(index)
    if retrieval_mode == RetrievalMode.DENSE:
        if _is_sentence_transformers_available():
            return EmbeddingRetriever(
                index,
                model_name=embed_model,
                query_prefix=embed_query_prefix,
                document_prefix=embed_document_prefix,
            )
        return TfidfRetriever(index)

    use_reranker = retrieval_mode in (RetrievalMode.AUTO, RetrievalMode.HYBRID_RERANK)
    if _is_sentence_transformers_available():
        reranker: RerankerProtocol | None = None
        if use_reranker:
            try:
                reranker = CrossEncoderReranker(model_name=rerank_model)
            except Exception:
                reranker = None

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
    bm25 = Bm25Retriever(index)
    if bm25.available:
        return bm25
    return TfidfRetriever(index)


def _retriever_cache_key(
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
) -> tuple[
    str,
    int | None,
    str,
    int,
    str | None,
    str | None,
    str,
    str,
    float,
    float,
    int,
    int,
    float,
]:
    """Build a cache key for retrievers bound to a query-transform config."""
    prompt_key: int | None = None
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


def _compound_query_variants(query: str) -> list[str]:
    normalized = " ".join(query.split())
    if not normalized:
        return [query]

    focus_match = _COMPOUND_BOTH_FOCUS_RE.search(normalized)
    if focus_match is None:
        return [normalized]

    raw_focus = focus_match.group("focus")
    parts = [_clean_compound_query_part(part) for part in _COMPOUND_SPLIT_RE.split(raw_focus)]
    query_parts = [part for part in parts if len(tokenize(part)) >= _MIN_COMPOUND_QUERY_TOKENS]
    if len(query_parts) < 2:
        return [normalized]
    return [normalized, *query_parts[:_MAX_COMPOUND_QUERY_PARTS]]


def _clean_compound_query_part(part: str) -> str:
    cleaned = part.strip(" \t\n\r,;:.?!")
    return " ".join(cleaned.split())


def _has_negation_marker(text: str) -> bool:
    normalized = f" {text.lower()} "
    return any(marker in normalized for marker in _NEGATION_MARKERS)


def _query_is_negated(query: str) -> bool:
    if _has_negation_marker(query):
        return True
    return bool(set(tokenize(query)) & _NEGATION_QUERY_INTENT_TOKENS)


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
    """Down-rank negative contrast passages for affirmative factual queries.

    Sparse retrieval can over-rank a passage that says "X is not the answer"
    because it shares nearly every topical token with the question.  That kind
    of passage is useful context, but it should not outrank an affirmative
    answer for ordinary "what/which/how" questions.
    """
    if _query_is_negated(query):
        return results
    query_tokens = set(tokenize(query))
    reranked: list[ScoredChunk] = []
    changed = False
    for result in results:
        if _has_query_relevant_negation(query_tokens, result.chunk.text):
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


def _normalized_hint_text(value: str) -> str:
    return " ".join(tokenize(value))


def _explicit_query_hints(query: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    quoted_hints: list[str] = []
    source_section_hints: list[str] = []
    source_section_matches = {
        match.group(1).strip() for match in _SOURCE_SECTION_HINT_RE.finditer(query)
    }
    for hint in source_section_matches:
        normalized = _normalized_hint_text(hint)
        if normalized:
            source_section_hints.append(normalized)
    for raw_hint in _QUOTED_HINT_RE.findall(query):
        hint = raw_hint.strip()
        if not hint or hint in source_section_matches:
            continue
        normalized = _normalized_hint_text(hint)
        if len(normalized.split()) >= 3:
            quoted_hints.append(normalized)
    return tuple(quoted_hints), tuple(source_section_hints)


def _apply_explicit_hint_boost(
    query: str,
    results: list[ScoredChunk],
) -> list[ScoredChunk]:
    quoted_hints, source_section_hints = _explicit_query_hints(query)
    if not results or (not quoted_hints and not source_section_hints):
        return results

    boosted: list[ScoredChunk] = []
    changed = False
    for result in results:
        score = result.score
        chunk_hint_text = _normalized_hint_text(
            " ".join(part for part in (result.chunk.heading, result.chunk.text) if part)
        )
        source_hint_text = _normalized_hint_text(result.chunk.source)
        if any(hint in chunk_hint_text for hint in quoted_hints):
            score += _EXPLICIT_HINT_BOOST
            changed = True
        if any(hint in source_hint_text for hint in source_section_hints):
            score += _EXPLICIT_HINT_BOOST
            changed = True
        boosted.append(ScoredChunk(chunk=result.chunk, score=score))
    if changed:
        boosted.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return boosted


def _retrieve_query_variants(
    retriever: RetrieverProtocol,
    query_variants: list[str],
    top_k: int,
) -> list[ScoredChunk]:
    if top_k <= 0:
        return []
    if len(query_variants) <= 1:
        return retriever.retrieve(query_variants[0], top_k)

    ranked_lists = [
        results for query in query_variants if (results := retriever.retrieve(query, top_k))
    ]
    if not ranked_lists:
        return []
    if len(ranked_lists) == 1:
        return ranked_lists[0][:top_k]
    return _merge_compound_query_results(ranked_lists, top_k)


def _merge_compound_query_results(
    ranked_lists: list[list[ScoredChunk]],
    top_k: int,
) -> list[ScoredChunk]:
    """Merge compound-query results while preserving each clause's top hit."""
    entries: dict[tuple[str, int], _CompoundMergeEntry] = {}
    promoted_keys: list[tuple[str, int]] = []
    promoted_seen: set[tuple[str, int]] = set()

    for list_index, ranked in enumerate(ranked_lists):
        if list_index > 0 and ranked:
            promoted_key = _scored_chunk_key(ranked[0])
            if promoted_key not in promoted_seen:
                promoted_keys.append(promoted_key)
                promoted_seen.add(promoted_key)
        for rank, scored_chunk in enumerate(ranked):
            key = _scored_chunk_key(scored_chunk)
            existing = entries.get(key)
            if existing is None:
                entries[key] = _CompoundMergeEntry(
                    scored_chunk=scored_chunk,
                    best_score=scored_chunk.score,
                    first_list_index=list_index,
                    best_rank=rank,
                )
                continue
            entries[key] = _CompoundMergeEntry(
                scored_chunk=existing.scored_chunk,
                best_score=max(existing.best_score, scored_chunk.score),
                first_list_index=min(existing.first_list_index, list_index),
                best_rank=min(existing.best_rank, rank),
            )

    promoted_entries = [
        _entry_to_scored_chunk(entries[key]) for key in promoted_keys if key in entries
    ]
    promoted_key_set = set(promoted_keys)
    remaining_entries = [entry for key, entry in entries.items() if key not in promoted_key_set]
    remaining_entries.sort(
        key=lambda entry: (
            entry.best_score,
            -entry.best_rank,
            -entry.first_list_index,
        ),
        reverse=True,
    )
    merged = [
        *promoted_entries,
        *[_entry_to_scored_chunk(entry) for entry in remaining_entries],
    ]
    return merged[:top_k]


def _scored_chunk_key(scored_chunk: ScoredChunk) -> tuple[str, int]:
    return scored_chunk.chunk.source, scored_chunk.chunk.index


def _entry_to_scored_chunk(entry: _CompoundMergeEntry) -> ScoredChunk:
    return ScoredChunk(chunk=entry.scored_chunk.chunk, score=entry.best_score)


def _diversify_sources(results: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    best_by_source: dict[str, ScoredChunk] = {}
    for result in results:
        existing = best_by_source.get(result.chunk.source)
        if existing is None or result.score > existing.score:
            best_by_source[result.chunk.source] = result
    diversified = list(best_by_source.values())
    diversified.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return diversified[:top_k]


def _post_process_candidate_top_k(
    index: ArmoryIndex,
    retriever: RetrieverProtocol,
    requested_top_k: int,
    retrieval_top_k: int,
) -> int:
    if isinstance(retriever, HybridRetriever):
        return retrieval_top_k
    if requested_top_k <= 0:
        return retrieval_top_k
    desired_top_k = max(
        retrieval_top_k,
        requested_top_k * _POST_PROCESS_CANDIDATE_MULTIPLIER,
        requested_top_k + _POST_PROCESS_MIN_EXTRA_CANDIDATES,
    )
    chunk_count = len(index.all_chunks)
    if chunk_count <= 0:
        return desired_top_k
    return min(chunk_count, desired_top_k)


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

    candidate_multiplier = max(1, candidate_multiplier)
    hybrid_sparse_weight = max(0.0, hybrid_sparse_weight)
    hybrid_dense_weight = max(0.0, hybrid_dense_weight)
    pseudo_feedback_docs = max(1, pseudo_feedback_docs)
    pseudo_feedback_terms = max(1, pseudo_feedback_terms)
    pseudo_feedback_weight = max(0.0, pseudo_feedback_weight)
    cache_key = _retriever_cache_key(
        transform_strategy,
        prompt_fn,
        retrieval_mode,
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
    requested_top_k = max(0, top_k)
    search_query = _normalize_query_for_retrieval(query)
    query_variants = _compound_query_variants(search_query)
    retrieval_top_k = (
        requested_top_k * candidate_multiplier if diversify_sources else requested_top_k
    )
    retrieval_top_k = _post_process_candidate_top_k(
        index,
        retriever,
        requested_top_k,
        retrieval_top_k,
    )
    results = _retrieve_query_variants(retriever, query_variants, retrieval_top_k)
    results = _apply_negation_precision_penalty(search_query, results)
    results = _apply_source_path_boost(search_query, results)
    results = _apply_explicit_hint_boost(search_query, results)
    if diversify_sources:
        results = _diversify_sources(results, requested_top_k)

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

    if not diversify_sources:
        results = results[:requested_top_k]

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
    return results
