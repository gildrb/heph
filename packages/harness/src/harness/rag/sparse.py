"""Stdlib-only sparse RAG retrievers."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from typing import cast

from harness._types import is_string_mapping
from harness.rag.chunker import Chunk
from harness.rag.index import ArmoryIndex
from harness.rag.retrieval_types import ScoredChunk
from harness.rag.scoring import tokenize

_TFIDF_CACHE_KEY = "tfidf_v8"
_BM25_TOKEN_CACHE_KEY = "bm25_tokens_v8"
_SOURCE_PATH_WEIGHT = 1


def _chunk_search_text(chunk_text: str, source: str, heading: str) -> str:
    if len(tokenize(chunk_text)) < 3:
        return chunk_text
    content = "\n".join(part for part in (heading, chunk_text) if part)
    return f"{content}\n{source}\n" * _SOURCE_PATH_WEIGHT


def _bm25_stdlib_idf(corpus_tokens: Sequence[list[str]]) -> dict[str, float]:
    document_count = len(corpus_tokens)
    document_frequency: dict[str, int] = {}
    for tokens in corpus_tokens:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return {
        token: math.log(1 + (document_count - frequency + 0.5) / (frequency + 0.5))
        for token, frequency in document_frequency.items()
    }


def _bm25_stdlib_state(corpus_tokens: list[list[str]]) -> tuple[dict[str, float], float]:
    if not corpus_tokens or not any(corpus_tokens):
        return {}, 0.0
    return _bm25_stdlib_idf(corpus_tokens), sum(map(len, corpus_tokens)) / len(corpus_tokens)


def _bm25_stdlib_results(
    chunks: list[Chunk],
    corpus_tokens: list[list[str]],
    query_tokens: list[str],
    *,
    idf: dict[str, float],
    avg_doc_len: float,
    top_k: int,
) -> list[ScoredChunk]:
    if not idf or avg_doc_len <= 0:
        return []
    scored: list[ScoredChunk] = []
    for index, tokens in enumerate(corpus_tokens):
        if not tokens:
            continue
        frequencies = Counter(tokens)
        length_ratio = len(tokens) / avg_doc_len
        score = 0.0
        for term in set(query_tokens):
            frequency = frequencies.get(term, 0)
            if frequency:
                denominator = frequency + 1.5 * (0.25 + 0.75 * length_ratio)
                score += idf.get(term, 0.0) * (frequency * 2.5) / denominator
        if score > 0:
            scored.append(ScoredChunk(chunk=chunks[index], score=score))
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def _load_frequency(raw: object) -> Counter[str] | None:
    if not is_string_mapping(raw) or any(not isinstance(value, int) for value in raw.values()):
        return None
    return Counter({key: int(cast("int", value)) for key, value in raw.items()})


def _load_idf(raw: object) -> dict[str, float] | None:
    if not is_string_mapping(raw):
        return None
    values = {term: float(value) for term, value in raw.items() if isinstance(value, int | float)}
    return values if len(values) == len(raw) else None


class TfidfRetriever:
    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._idf: dict[str, float] = {}
        self._chunk_freqs: list[Counter[str]] = []
        if not self._chunks:
            return
        cached = index.load_retriever_state(_TFIDF_CACHE_KEY)
        if cached is None or not self._load_state(cached):
            self._build()
            index.save_retriever_state(
                _TFIDF_CACHE_KEY,
                {
                    "idf": dict(self._idf),
                    "chunk_freqs": [dict(freq) for freq in self._chunk_freqs],
                },
            )

    def _load_state(self, state: dict[str, object]) -> bool:
        raw_idf, raw_freqs = state.get("idf"), state.get("chunk_freqs")
        if not is_string_mapping(raw_idf) or not isinstance(raw_freqs, list):
            return False
        idf = _load_idf(raw_idf)
        if idf is None:
            return False
        self._idf = idf
        frequencies = [_load_frequency(raw) for raw in raw_freqs]
        if any(frequency is None for frequency in frequencies):
            return False
        typed_frequencies = [frequency for frequency in frequencies if frequency is not None]
        if len(typed_frequencies) != len(self._chunks):
            return False
        self._chunk_freqs = typed_frequencies
        return True

    def _build(self) -> None:
        document_frequency: Counter[str] = Counter()
        for chunk in self._chunks:
            frequency = Counter(
                tokenize(_chunk_search_text(chunk.text, chunk.source, chunk.heading))
            )
            self._chunk_freqs.append(frequency)
            document_frequency.update(frequency.keys())
        count = len(self._chunks)
        self._idf = {
            term: math.log((count + 1) / (freq + 1)) + 1
            for term, freq in document_frequency.items()
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        if not self._chunks:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_frequency = Counter(query_tokens)
        query_terms = set(query_tokens)
        scored: list[ScoredChunk] = []
        for index, frequency in enumerate(self._chunk_freqs):
            dot = chunk_norm = 0.0
            for term, tf in frequency.items():
                weight = tf * self._idf.get(term, 1.0)
                chunk_norm += weight * weight
                if term in query_terms:
                    dot += weight * query_frequency[term]
            query_norm = sum(tf * tf for tf in query_frequency.values())
            if chunk_norm and query_norm:
                score = dot / math.sqrt(chunk_norm * query_norm)
                if score > 0:
                    scored.append(ScoredChunk(chunk=self._chunks[index], score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class Bm25Retriever:
    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._corpus_tokens: list[list[str]] = []
        self._idf: dict[str, float] = {}
        self._avg_doc_len = 0.0
        if self._chunks:
            cached = index.load_retriever_state(_BM25_TOKEN_CACHE_KEY)
            if cached is None or not self._load_tokens(cached):
                self._corpus_tokens = [
                    tokenize(_chunk_search_text(chunk.text, chunk.source, chunk.heading))
                    for chunk in self._chunks
                ]
                index.save_retriever_state(
                    _BM25_TOKEN_CACHE_KEY, {"corpus_tokens": self._corpus_tokens}
                )
            self._idf, self._avg_doc_len = _bm25_stdlib_state(self._corpus_tokens)

    def _load_tokens(self, state: dict[str, object]) -> bool:
        raw = state.get("corpus_tokens")
        if not isinstance(raw, list):
            return False
        tokens: list[list[str]] = []
        for row in raw:
            if not isinstance(row, list) or any(not isinstance(item, str) for item in row):
                return False
            tokens.append([cast("str", item) for item in row])
        if len(tokens) != len(self._chunks):
            return False
        self._corpus_tokens = tokens
        return True

    @property
    def available(self) -> bool:
        return bool(self._idf)

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        return _bm25_stdlib_results(
            self._chunks,
            self._corpus_tokens,
            tokenize(query),
            idf=self._idf,
            avg_doc_len=self._avg_doc_len,
            top_k=top_k,
        )


class DocumentBm25Retriever(Bm25Retriever):
    """BM25 over one concatenated text field per source document."""

    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = [document.chunks[0] for document in index.documents if document.chunks]
        self._corpus_tokens = []
        self._idf = {}
        self._avg_doc_len = 0.0
        if self._chunks:
            self._corpus_tokens = [
                tokenize(
                    "\n\n".join(
                        chunk.text
                        for chunk in sorted(document.chunks, key=lambda item: item.index)
                    )
                )
                for document in index.documents
                if document.chunks
            ]
            self._idf, self._avg_doc_len = _bm25_stdlib_state(self._corpus_tokens)
