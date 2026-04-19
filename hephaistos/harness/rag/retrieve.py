"""Retrieval engine: pluggable retriever protocol with multiple backends.

Backends (selected automatically based on available dependencies):
- ``TfidfRetriever``     — pure-stdlib keyword scoring (always available)
- ``EmbeddingRetriever`` — dense vector similarity via sentence-transformers
- ``HybridRetriever``    — reciprocal-rank fusion of TF-IDF + embeddings

Post-retrieval re-ranking (optional, requires sentence-transformers):
- ``CrossEncoderReranker`` — cross-encoder re-scoring for improved precision

The top-level ``retrieve()`` function auto-selects the best backend and
applies re-ranking when available: hybrid retrieval → RRF fusion →
cross-encoder re-ranking → top-k results.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer as _SklearnTfidfVectorizer

    _has_sklearn = True
except ImportError:
    _has_sklearn = False
    np = None  # type: ignore[assignment]
    _SklearnTfidfVectorizer = None  # type: ignore[assignment,misc]

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.index import ArmoryIndex
from hephaistos.harness.rag.query_transform import (
    PromptFn,
    QueryTransformerProtocol,
    TransformStrategy,
    create_transformer,
)
from hephaistos.logging import get_logger

_log = get_logger("rag.retrieve")

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")
_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "and",
        "but",
        "or",
        "not",
        "no",
        "nor",
        "so",
        "if",
        "then",
        "than",
        "too",
        "very",
        "just",
        "about",
        "also",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "she",
        "they",
        "them",
        "their",
        "what",
        "which",
        "who",
        "how",
        "when",
        "where",
        "why",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "any",
        "up",
        "out",
    }
)


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@runtime_checkable
class RetrieverProtocol(Protocol):
    """Minimal interface every retriever must implement."""

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]: ...


@runtime_checkable
class RerankerProtocol(Protocol):
    """Interface for post-retrieval re-rankers.

    A re-ranker takes a list of candidate ``ScoredChunk`` objects produced by
    a retriever and re-scores them (typically with a cross-encoder) to
    improve precision.  The returned list is sorted by the new scores.
    """

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]: ...


def _tokenize(text: str) -> list[str]:
    tokens = _WORD_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


class TfidfRetriever:
    """TF-IDF cosine-similarity retriever over an ``ArmoryIndex``.

    Uses scikit-learn's ``TfidfVectorizer`` when available (sublinear TF
    scaling, proper L2 normalization).  Falls back to a hand-rolled stdlib
    implementation otherwise.
    """

    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._vectorizer: _SklearnTfidfVectorizer | None = None  # type: ignore[type-arg]
        self._matrix = None
        self._idf: dict[str, float] = {}
        self._chunk_freqs: list[Counter] = []
        if self._chunks:
            if _has_sklearn:
                try:
                    self._build_sklearn()
                except Exception:
                    self._build_idf()
            else:
                self._build_idf()

    def _build_idf(self) -> None:
        doc_count = len(self._chunks)
        df: dict[str, int] = {}

        for chunk in self._chunks:
            freq = Counter(_tokenize(chunk.text))
            self._chunk_freqs.append(freq)
            for term in freq:
                df[term] = df.get(term, 0) + 1

        self._idf = {
            term: math.log((doc_count + 1) / (count + 1)) + 1 for term, count in df.items()
        }

    def _build_sklearn(self) -> None:
        """Build TF-IDF matrix using scikit-learn (preferred when available)."""
        assert _SklearnTfidfVectorizer is not None  # guarded by _HAS_SKLEARN
        texts = [c.text for c in self._chunks]
        self._vectorizer = _SklearnTfidfVectorizer(
            stop_words="english",
            sublinear_tf=True,
            max_features=10000,
            token_pattern=r"(?u)\b[a-zA-Z0-9]{2,}\b",
        )
        self._matrix = self._vectorizer.fit_transform(texts)  # type: ignore[union-attr]

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return the top-k chunks most relevant to *query*."""
        if not self._chunks:
            return []
        if self._matrix is not None:
            return self._retrieve_sklearn(query, top_k)
        return self._retrieve_stdlib(query, top_k)

    def _retrieve_sklearn(self, query: str, top_k: int) -> list[ScoredChunk]:
        """Retrieve using scikit-learn TF-IDF vectors and cosine similarity."""
        assert self._vectorizer is not None
        assert self._matrix is not None
        query_vec = self._vectorizer.transform([query])
        # TfidfVectorizer produces L2-normalized vectors by default,
        # so dot product == cosine similarity.
        scores = (query_vec @ self._matrix.T).toarray().flatten()  # type: ignore[union-attr]
        top_indices = np.argsort(scores)[::-1][:top_k]  # type: ignore[union-attr]
        return [
            ScoredChunk(chunk=self._chunks[idx], score=float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0
        ]

    def _retrieve_stdlib(self, query: str, top_k: int) -> list[ScoredChunk]:
        """Retrieve using the hand-rolled TF-IDF implementation (fallback)."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_freq = Counter(query_tokens)
        query_terms = set(query_tokens)

        scored: list[ScoredChunk] = []
        for i, chunk_freq in enumerate(self._chunk_freqs):
            score = self._tfidf_score(chunk_freq, query_freq, query_terms)
            if score > 0:
                scored.append(ScoredChunk(chunk=self._chunks[i], score=score))

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]

    def _tfidf_score(
        self,
        chunk_freq: Counter,
        query_freq: Counter,
        query_terms: set[str],
    ) -> float:
        dot = 0.0
        chunk_norm_sq = 0.0
        query_norm_sq = 0.0

        for term, tf in chunk_freq.items():
            idf = self._idf.get(term, 1.0)
            tfidf = tf * idf
            chunk_norm_sq += tfidf * tfidf
            if term in query_terms:
                q_tf = query_freq[term]
                dot += tfidf * q_tf

        for tf in query_freq.values():
            query_norm_sq += tf * tf

        if chunk_norm_sq == 0 or query_norm_sq == 0:
            return 0.0

        return dot / (math.sqrt(chunk_norm_sq) * math.sqrt(query_norm_sq))


_EMBED_MODEL_ENV = "HEPHAISTOS_EMBED_MODEL"
_EMBED_MODEL_DEFAULT = "all-MiniLM-L6-v2"

_RERANK_MODEL_ENV = "HEPHAISTOS_RERANK_MODEL"
_RERANK_MODEL_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _is_sentence_transformers_available() -> bool:
    """Return True if sentence-transformers can be imported."""
    try:
        import sentence_transformers  # type: ignore[UnusedImport]  # noqa: F401, RUF100

        return True
    except ImportError:
        return False


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingRetriever:
    """Dense vector retriever using sentence-transformers embeddings.

    Chunks are encoded into vectors on first retrieval; subsequent queries
    reuse the cached embeddings.  Falls back gracefully if the library or
    model cannot be loaded.
    """

    def __init__(
        self,
        index: ArmoryIndex,
        model_name: str | None = None,
    ) -> None:
        self._chunks = index.all_chunks
        self._model_name = model_name or os.environ.get(
            _EMBED_MODEL_ENV,
            _EMBED_MODEL_DEFAULT,
        )
        self._embeddings: list[list[float]] | None = None
        self._model = None  # lazy-loaded

    def _ensure_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self._model_name)
        return self._model

    def _ensure_embeddings(self) -> list[list[float]]:
        """Build chunk embeddings if not yet computed."""
        if self._embeddings is not None:
            return self._embeddings

        if not self._chunks:
            self._embeddings = []
            return self._embeddings

        model = self._ensure_model()
        texts = [c.text for c in self._chunks]
        vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        self._embeddings = [row.tolist() for row in vectors]
        return self._embeddings

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return the top-k chunks by embedding cosine similarity."""
        if not self._chunks:
            return []

        embeddings = self._ensure_embeddings()
        model = self._ensure_model()
        query_vec = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        query_embedding = query_vec[0].tolist()
        scored: list[ScoredChunk] = []
        for i, chunk_embedding in enumerate(embeddings):
            sim = _cosine_similarity(query_embedding, chunk_embedding)
            if sim > 0:
                scored.append(ScoredChunk(chunk=self._chunks[i], score=sim))

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]


class CrossEncoderReranker:
    """Cross-encoder re-ranker for improved retrieval precision.

    Uses a ``sentence_transformers.CrossEncoder`` model to jointly encode
    ``(query, chunk_text)`` pairs, producing a relevance score that is
    typically far more accurate than bi-encoder similarity alone.

    The model is lazy-loaded on first use.  Falls back to a no-op (returns
    candidates unchanged, truncated to *top_k*) if the library cannot be
    imported.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.environ.get(
            _RERANK_MODEL_ENV,
            _RERANK_MODEL_DEFAULT,
        )
        self._model = None  # lazy-loaded

    @property
    def model_name(self) -> str:
        """Name of the cross-encoder model."""
        return self._model_name

    def _ensure_model(self):
        """Lazy-load the CrossEncoder model."""
        if self._model is not None:
            return self._model
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self._model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Re-score *candidates* with the cross-encoder and return *top_k*.

        Each candidate's ``score`` is replaced by the cross-encoder
        relevance score.  Results are sorted descending by the new score.
        """
        if not candidates:
            return []

        model = self._ensure_model()
        pairs = [(query, sc.chunk.text) for sc in candidates]
        scores = model.predict(pairs)
        scored = [
            ScoredChunk(chunk=candidates[i].chunk, score=float(scores[i]))
            for i in range(len(candidates))
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]


def _reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    *,
    k: int = 60,
) -> list[ScoredChunk]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion (RRF).

    Each chunk is identified by ``(source, index)``.  The RRF score is
    ``sum(1 / (k + rank_i))`` across all lists where the chunk appears.

    The returned ``ScoredChunk.score`` is the RRF score.  The ``chunk``
    object comes from the first list that contained it.
    """
    merged: dict[tuple[str, int], tuple[float, ScoredChunk]] = {}

    for ranked in ranked_lists:
        for rank, sc in enumerate(ranked):
            key = (sc.chunk.source, sc.chunk.index)
            rrf_delta = 1.0 / (k + rank + 1)  # +1 for 0-based rank
            if key in merged:
                current_score, best_sc = merged[key]
                merged[key] = (current_score + rrf_delta, best_sc)
            else:
                merged[key] = (rrf_delta, sc)

    results = [
        ScoredChunk(chunk=sc.chunk, score=score)
        for (_, score, sc) in ((key, score, sc) for key, (score, sc) in merged.items())
    ]
    results.sort(key=lambda s: s.score, reverse=True)
    return results


class HybridRetriever:
    """Hybrid retriever combining TF-IDF and embedding retrieval via RRF.

    Runs both retrievers, then merges results with reciprocal rank fusion.
    If ``sentence-transformers`` is not available, silently falls back to
    pure TF-IDF retrieval.
    """

    def __init__(
        self,
        index: ArmoryIndex,
        embed_model: str | None = None,
        reranker: RerankerProtocol | None = None,
        *,
        candidate_multiplier: int = 3,
        query_transformer: QueryTransformerProtocol | None = None,
    ) -> None:
        self._tfidf = TfidfRetriever(index)
        self._embedding: EmbeddingRetriever | None = None
        self._reranker = reranker
        self._candidate_multiplier = candidate_multiplier
        self._query_transformer = query_transformer

        if _is_sentence_transformers_available():
            try:
                self._embedding = EmbeddingRetriever(index, model_name=embed_model)
            except Exception:
                # If the model can't be loaded, fall back gracefully
                self._embedding = None

    @property
    def has_embeddings(self) -> bool:
        """Whether the embedding backend is active."""
        return self._embedding is not None

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Retrieve via TF-IDF + embeddings, fused with RRF, then re-ranked.

        When a query transformer is attached, the query is first transformed
        into one or more alternative queries.  Results from all queries are
        merged with Reciprocal Rank Fusion before re-ranking.
        """
        # --- Query transformation ---
        if self._query_transformer is not None:
            queries = self._query_transformer.transform(query)
        else:
            queries = [query]

        pool = top_k * self._candidate_multiplier

        if len(queries) == 1:
            # Single query — standard retrieval path
            candidates = self._retrieve_single(queries[0], pool)
        else:
            # Multiple queries — retrieve for each, then fuse all results
            all_results: list[list[ScoredChunk]] = []
            for q in queries:
                results = self._retrieve_single(q, pool)
                if results:
                    all_results.append(results)

            if not all_results:
                return []

            if len(all_results) == 1:
                candidates = all_results[0]
            else:
                candidates = _reciprocal_rank_fusion(all_results)

        # Apply cross-encoder re-ranker if available
        if self._reranker is not None:
            if not candidates:
                return []
            return self._reranker.rerank(query, candidates, top_k=top_k)

        return candidates[:top_k]

    def _retrieve_single(self, query: str, pool: int) -> list[ScoredChunk]:
        """Run TF-IDF + (optional) embedding retrieval for a single query."""
        if self._embedding is None:
            return self._tfidf.retrieve(query, top_k=pool)

        tfidf_results = self._tfidf.retrieve(query, top_k=pool)
        embed_results = self._embedding.retrieve(query, top_k=pool)

        if not tfidf_results and not embed_results:
            return []
        if not tfidf_results:
            return embed_results
        if not embed_results:
            return tfidf_results

        return _reciprocal_rank_fusion([tfidf_results, embed_results])


def _create_retriever(
    index: ArmoryIndex,
    embed_model: str | None = None,
    rerank_model: str | None = None,
    query_transformer: QueryTransformerProtocol | None = None,
) -> TfidfRetriever | EmbeddingRetriever | HybridRetriever:
    """Create the best available retriever for the given index.

    Strategy:
    1. If sentence-transformers is available → ``HybridRetriever`` (TF-IDF + embeddings)
       with an optional ``CrossEncoderReranker`` for post-retrieval re-scoring.
    2. Otherwise → ``TfidfRetriever`` (pure keyword matching)

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
    return TfidfRetriever(index)


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

    retriever = _create_retriever(index, query_transformer=transformer)
    results = retriever.retrieve(query, top_k)

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
                "top_k": top_k,
                "returned": len(results),
                "retriever": type(retriever).__name__,
                "transform_strategy": transform_strategy.value,
                "min_score": min_score,
            }
        },
    )
    return results
