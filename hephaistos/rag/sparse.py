"""Sparse RAG retrievers: TF-IDF and BM25."""

from __future__ import annotations

import math
from collections import Counter
from typing import cast

from hephaistos.logging import get_logger
from hephaistos.rag import optional_backends
from hephaistos.rag.index import ArmoryIndex
from hephaistos.rag.optional_backends import Bm25Protocol, SklearnVectorizerProtocol
from hephaistos.rag.retrieval_types import ScoredChunk
from hephaistos.rag.scoring import object_rows, sklearn_scores, tokenize

_log = get_logger("rag.sparse")


def _chunk_search_text(chunk_text: str, source: str, heading: str) -> str:
    """Return the text used for sparse retrieval scoring."""
    if len(tokenize(chunk_text)) < 3:
        return chunk_text
    content = "\n".join(part for part in (heading, chunk_text) if part)
    return f"{content}\n{source}"


class TfidfRetriever:
    """TF-IDF cosine-similarity retriever over an ``ArmoryIndex``."""

    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._vectorizer: SklearnVectorizerProtocol | None = None
        self._matrix: object | None = None
        self._idf: dict[str, float] = {}
        self._chunk_freqs: list[Counter[str]] = []
        if self._chunks:
            if optional_backends.HAS_SKLEARN:
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
            freq = Counter(tokenize(_chunk_search_text(chunk.text, chunk.source, chunk.heading)))
            self._chunk_freqs.append(freq)
            for term in freq:
                df[term] = df.get(term, 0) + 1

        self._idf = {
            term: math.log((doc_count + 1) / (count + 1)) + 1 for term, count in df.items()
        }

    def _build_sklearn(self) -> None:
        """Build TF-IDF matrix using scikit-learn when available."""
        assert optional_backends.SKLEARN_TFIDF_VECTORIZER is not None
        texts = [
            _chunk_search_text(chunk.text, chunk.source, chunk.heading) for chunk in self._chunks
        ]
        self._vectorizer = optional_backends.SKLEARN_TFIDF_VECTORIZER(
            stop_words="english",
            sublinear_tf=True,
            max_features=10000,
            token_pattern=r"(?u)\b[a-zA-Z0-9]{2,}\b",
        )
        self._matrix = self._vectorizer.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return the top-k chunks most relevant to *query*."""
        if not self._chunks:
            return []
        if self._matrix is not None:
            return self._retrieve_sklearn(query, top_k)
        return self._retrieve_stdlib(query, top_k)

    def _retrieve_sklearn(self, query: str, top_k: int) -> list[ScoredChunk]:
        assert self._vectorizer is not None
        assert self._matrix is not None
        query_vec = self._vectorizer.transform([query])
        scores = sklearn_scores(query_vec, self._matrix)
        top_indices = sorted(range(len(scores)), key=lambda idx: float(scores[idx]), reverse=True)[
            :top_k
        ]
        return [
            ScoredChunk(chunk=self._chunks[idx], score=float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0
        ]

    def _retrieve_stdlib(self, query: str, top_k: int) -> list[ScoredChunk]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        query_freq = Counter(query_tokens)
        query_terms = set(query_tokens)

        scored: list[ScoredChunk] = []
        for i, chunk_freq in enumerate(self._chunk_freqs):
            score = self._tfidf_score(chunk_freq, query_freq, query_terms)
            if score > 0:
                scored.append(ScoredChunk(chunk=self._chunks[i], score=score))

        scored.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
        return scored[:top_k]

    def _tfidf_score(
        self,
        chunk_freq: Counter[str],
        query_freq: Counter[str],
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
                dot += tfidf * query_freq[term]

        for tf in query_freq.values():
            query_norm_sq += tf * tf

        if chunk_norm_sq == 0 or query_norm_sq == 0:
            return 0.0

        return dot / (math.sqrt(chunk_norm_sq) * math.sqrt(query_norm_sq))


class Bm25Retriever:
    """Sparse BM25 retriever using the optional ``bm25s`` package."""

    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._retriever: object | None = None
        self._corpus_tokens: list[list[str]] = []
        if self._chunks and optional_backends.BM25_CLASS is not None:
            self._build()

    @property
    def available(self) -> bool:
        """Whether the BM25 backend was built successfully."""
        return self._retriever is not None

    def _build(self) -> None:
        assert optional_backends.BM25_CLASS is not None
        self._corpus_tokens = [
            tokenize(_chunk_search_text(chunk.text, chunk.source, chunk.heading))
            for chunk in self._chunks
        ]
        if not any(self._corpus_tokens):
            return
        try:
            retriever = optional_backends.BM25_CLASS()
            retriever.index(self._corpus_tokens, show_progress=False)
        except Exception:
            _log.warning("bm25 build failed; falling back to tf-idf", exc_info=True)
            return
        self._retriever = retriever

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return the top-k chunks by BM25 score."""
        if self._retriever is None or not self._chunks:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        result_count = min(top_k, len(self._chunks))
        if result_count <= 0:
            return []
        retriever = cast("Bm25Protocol", self._retriever)
        results, scores = retriever.retrieve([query_tokens], k=result_count, show_progress=False)
        result_rows = object_rows(results)
        score_rows = object_rows(scores)
        if not result_rows or not score_rows:
            return []

        scored: list[ScoredChunk] = []
        for raw_idx, raw_score in zip(result_rows[0], score_rows[0], strict=False):
            if not isinstance(raw_idx, int) or not isinstance(raw_score, int | float):
                continue
            if raw_score <= 0:
                continue
            if raw_idx < 0 or raw_idx >= len(self._chunks):
                continue
            scored.append(ScoredChunk(chunk=self._chunks[raw_idx], score=float(raw_score)))
        return scored
