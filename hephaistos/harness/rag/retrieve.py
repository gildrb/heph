"""Retrieval engine: TF-IDF keyword scoring over chunk index.

V1 uses pure-stdlib TF-IDF. The ``Retriever`` protocol is designed so a
future embedding-based implementation can be swapped in as a drop-in
replacement.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.index import ArmoryIndex

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "but", "or",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "also", "this", "that", "these", "those", "it",
    "its", "i", "me", "my", "we", "our", "you", "your", "he", "she",
    "they", "them", "their", "what", "which", "who", "how", "when",
    "where", "why", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "any", "up", "out",
})


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float


class Retriever:
    """TF-IDF retriever over an ``ArmoryIndex``."""

    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._idf: dict[str, float] = {}
        self._chunk_freqs: list[Counter] = []
        if self._chunks:
            self._build_idf()

    def _tokenize(self, text: str) -> list[str]:
        tokens = _WORD_RE.findall(text.lower())
        return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

    def _build_idf(self) -> None:
        doc_count = len(self._chunks)
        df: dict[str, int] = {}

        for chunk in self._chunks:
            freq = Counter(self._tokenize(chunk.text))
            self._chunk_freqs.append(freq)
            for term in freq:
                df[term] = df.get(term, 0) + 1

        self._idf = {
            term: math.log((doc_count + 1) / (count + 1)) + 1
            for term, count in df.items()
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Return the top-k chunks most relevant to *query*."""
        if not self._chunks:
            return []

        query_tokens = self._tokenize(query)
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
        """Compute TF-IDF cosine similarity between chunk and query."""
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

        for term, tf in query_freq.items():
            query_norm_sq += tf * tf

        if chunk_norm_sq == 0 or query_norm_sq == 0:
            return 0.0

        return dot / (math.sqrt(chunk_norm_sq) * math.sqrt(query_norm_sq))


def retrieve(
    query: str,
    index: ArmoryIndex,
    top_k: int = 5,
) -> list[ScoredChunk]:
    """Convenience function: create a retriever and return top-k chunks."""
    retriever = Retriever(index)
    return retriever.retrieve(query, top_k)
