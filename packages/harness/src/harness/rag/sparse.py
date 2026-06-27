"""Sparse RAG retrievers: TF-IDF and BM25."""

from __future__ import annotations

import contextlib
import heapq
import math
import shutil
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from ai.logging import get_logger

from harness._types import is_string_mapping
from harness.rag import optional_backends
from harness.rag.chunker import Chunk
from harness.rag.index import ArmoryIndex
from harness.rag.optional_backends import Bm25Protocol, SklearnVectorizerProtocol
from harness.rag.retrieval_types import ScoredChunk
from harness.rag.scoring import object_rows, sklearn_scores, tokenize

_log = get_logger("harness.rag.sparse")
_TFIDF_CACHE_KEY = "tfidf_v8"
_BM25_TOKEN_CACHE_KEY = "bm25_tokens_v8"
_BM25_BACKEND_CACHE_KEY = "bm25s_v2"
_BM25_DOCUMENT_BACKEND_CACHE_KEY = "bm25s_document_v1"
_SOURCE_PATH_WEIGHT = 1


def _chunk_search_text(chunk_text: str, source: str, heading: str) -> str:
    if len(tokenize(chunk_text)) < 3:
        return chunk_text
    content = "\n".join(part for part in (heading, chunk_text) if part)
    source_terms = "\n".join(source for _ in range(_SOURCE_PATH_WEIGHT))
    return f"{content}\n{source_terms}"


def _bm25_backend_cache_dir(index: ArmoryIndex, cache_key: str) -> Path:
    return index.armory_path / ".harness" / f"retriever_{index.content_hash}_{cache_key}"


def _load_bm25_backend_cache(index: ArmoryIndex, cache_key: str) -> object | None:
    bm25_factory = optional_backends.bm25_class()
    if bm25_factory is None or not hasattr(bm25_factory, "load"):
        return None
    cache_dir = _bm25_backend_cache_dir(index, cache_key)
    if not cache_dir.is_dir():
        return None
    try:
        return bm25_factory.load(
            cache_dir,
            load_corpus=False,
            mmap=True,
        )
    except Exception:
        _log.warning("bm25 backend cache load failed", exc_info=True)
        return None


def _save_bm25_backend_cache(index: ArmoryIndex, cache_key: str, retriever: object) -> None:
    if not hasattr(retriever, "save"):
        return
    bm25_retriever = cast("Bm25Protocol", retriever)
    cache_dir = _bm25_backend_cache_dir(index, cache_key)
    tmp_path = cache_dir.with_name(f"{cache_dir.name}.tmp")
    try:
        if tmp_path.exists():
            shutil.rmtree(tmp_path)
        bm25_retriever.save(tmp_path, corpus=None)
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        tmp_path.rename(cache_dir)
    except Exception:
        with contextlib.suppress(OSError):
            if tmp_path.exists():
                shutil.rmtree(tmp_path)
        _log.warning("bm25 backend cache save failed", exc_info=True)


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
    documents = [tokens for tokens in corpus_tokens if tokens]
    if not documents:
        return {}, 0.0
    document_count = len(corpus_tokens)
    avg_doc_len = sum(len(tokens) for tokens in corpus_tokens) / document_count
    return _bm25_stdlib_idf(corpus_tokens), avg_doc_len


def _build_bm25_backend(
    index: ArmoryIndex,
    corpus_tokens: list[list[str]],
    cache_key: str,
    *,
    warning: str,
) -> object | None:
    if not any(corpus_tokens):
        return None
    bm25_factory = optional_backends.bm25_class()
    if bm25_factory is None:
        return None
    try:
        retriever = bm25_factory()
        retriever.index(corpus_tokens, show_progress=False)
    except Exception:
        _log.warning(warning, exc_info=True)
        return None
    _save_bm25_backend_cache(index, cache_key, retriever)
    return retriever


def _bm25_backend_results(
    retriever: object,
    chunks: list[Chunk],
    query_tokens: list[str],
    top_k: int,
) -> list[ScoredChunk]:
    result_count = min(top_k, len(chunks))
    if result_count <= 0:
        return []
    bm25_retriever = cast("Bm25Protocol", retriever)
    results, scores = bm25_retriever.retrieve([query_tokens], k=result_count, show_progress=False)
    result_rows = object_rows(results)
    score_rows = object_rows(scores)
    if not result_rows or not score_rows:
        return []

    scored: list[ScoredChunk] = []
    for raw_idx, raw_score in zip(result_rows[0], score_rows[0], strict=False):
        if not isinstance(raw_idx, int) or not isinstance(raw_score, int | float):
            continue
        if raw_score <= 0 or raw_idx < 0 or raw_idx >= len(chunks):
            continue
        scored.append(ScoredChunk(chunk=chunks[raw_idx], score=float(raw_score)))
    return scored


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
    query_terms = set(query_tokens)
    scored: list[ScoredChunk] = []
    for index, tokens in enumerate(corpus_tokens):
        if not tokens:
            continue
        frequencies = Counter(tokens)
        length_ratio = len(tokens) / avg_doc_len
        score = 0.0
        for term in query_terms:
            frequency = frequencies.get(term, 0)
            if frequency <= 0:
                continue
            denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * length_ratio)
            score += idf.get(term, 0.0) * (frequency * 2.5) / denominator
        if score > 0:
            scored.append(ScoredChunk(chunk=chunks[index], score=score))
    scored.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return scored[:top_k]


class TfidfRetriever:
    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks: list[Chunk] = index.all_chunks
        self._vectorizer: SklearnVectorizerProtocol | None = None
        self._matrix: object | None = None
        self._idf: dict[str, float] = {}
        self._chunk_freqs: list[Counter[str]] = []
        if self._chunks:
            cached_state = index.load_retriever_state(_TFIDF_CACHE_KEY)
            if cached_state is not None and self._load_idf_state(cached_state):
                return
            if optional_backends.has_sklearn():
                try:
                    self._build_sklearn()
                    return
                except Exception:
                    self._build_idf()
            else:
                self._build_idf()
            self._save_idf_state(index)

    def _load_idf_state(self, state: dict[str, object]) -> bool:
        raw_idf = state.get("idf")
        raw_chunk_freqs = state.get("chunk_freqs")
        if not is_string_mapping(raw_idf) or not isinstance(raw_chunk_freqs, list):
            return False

        idf: dict[str, float] = {}
        for term, raw_value in raw_idf.items():
            if not isinstance(raw_value, int | float):
                return False
            idf[term] = float(raw_value)

        chunk_freqs: list[Counter[str]] = []
        for raw_freq in raw_chunk_freqs:
            if not is_string_mapping(raw_freq):
                return False
            freq: Counter[str] = Counter()
            for term, raw_count in raw_freq.items():
                if not isinstance(raw_count, int):
                    return False
                freq[term] = raw_count
            chunk_freqs.append(freq)

        if len(chunk_freqs) != len(self._chunks):
            return False
        self._idf = idf
        self._chunk_freqs = chunk_freqs
        return True

    def _save_idf_state(self, index: ArmoryIndex) -> None:
        index.save_retriever_state(
            _TFIDF_CACHE_KEY,
            {
                "idf": dict(self._idf),
                "chunk_freqs": [dict(freq) for freq in self._chunk_freqs],
            },
        )

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
        vectorizer_factory = optional_backends.sklearn_tfidf_vectorizer()
        assert vectorizer_factory is not None
        texts = [
            _chunk_search_text(chunk.text, chunk.source, chunk.heading) for chunk in self._chunks
        ]
        self._vectorizer = vectorizer_factory(
            stop_words="english",
            sublinear_tf=True,
            max_features=10000,
            token_pattern=r"(?u)\b[a-zA-Z0-9]{2,}\b",
        )
        self._matrix = self._vectorizer.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
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
        top_indices = heapq.nlargest(top_k, range(len(scores)), key=lambda idx: scores[idx])
        scored: list[ScoredChunk] = []
        for idx in top_indices:
            score = scores[idx]
            if score > 0:
                scored.append(ScoredChunk(chunk=self._chunks[idx], score=score))
        return scored

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
    def __init__(self, index: ArmoryIndex) -> None:
        self._chunks = index.all_chunks
        self._retriever: object | None = None
        self._corpus_tokens: list[list[str]] = []
        self._idf: dict[str, float] = {}
        self._avg_doc_len = 0.0
        if self._chunks:
            self._load_backend_cache(index)
            if self._retriever is not None:
                return
            cached_state = index.load_retriever_state(_BM25_TOKEN_CACHE_KEY)
            if cached_state is not None and self._load_corpus_tokens(cached_state):
                self._build_retriever(index)
                if self._retriever is None:
                    self._idf, self._avg_doc_len = _bm25_stdlib_state(self._corpus_tokens)
            else:
                self._build(index)

    @property
    def available(self) -> bool:
        return self._retriever is not None or bool(self._idf)

    def _load_corpus_tokens(self, state: dict[str, object]) -> bool:
        raw_corpus_tokens = state.get("corpus_tokens")
        if not isinstance(raw_corpus_tokens, list):
            return False
        corpus_tokens: list[list[str]] = []
        for raw_tokens in raw_corpus_tokens:
            if not isinstance(raw_tokens, list):
                return False
            tokens: list[str] = []
            for raw_token in raw_tokens:
                if not isinstance(raw_token, str):
                    return False
                tokens.append(raw_token)
            corpus_tokens.append(tokens)
        if len(corpus_tokens) != len(self._chunks):
            return False
        self._corpus_tokens = corpus_tokens
        return True

    def _build(self, index: ArmoryIndex) -> None:
        self._corpus_tokens = [
            tokenize(_chunk_search_text(chunk.text, chunk.source, chunk.heading))
            for chunk in self._chunks
        ]
        index.save_retriever_state(_BM25_TOKEN_CACHE_KEY, {"corpus_tokens": self._corpus_tokens})
        self._build_retriever(index)
        if self._retriever is None:
            self._idf, self._avg_doc_len = _bm25_stdlib_state(self._corpus_tokens)
        else:
            self._corpus_tokens = []

    def _build_retriever(self, index: ArmoryIndex) -> None:
        if not any(self._corpus_tokens):
            return
        if self._load_backend_cache(index):
            return
        self._retriever = _build_bm25_backend(
            index,
            self._corpus_tokens,
            _BM25_BACKEND_CACHE_KEY,
            warning="bm25 build failed; falling back to tf-idf",
        )

    def _load_backend_cache(self, index: ArmoryIndex) -> bool:
        self._retriever = _load_bm25_backend_cache(index, _BM25_BACKEND_CACHE_KEY)
        return self._retriever is not None

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        if not self._chunks:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        if self._retriever is None:
            return _bm25_stdlib_results(
                self._chunks,
                self._corpus_tokens,
                query_tokens,
                idf=self._idf,
                avg_doc_len=self._avg_doc_len,
                top_k=top_k,
            )
        return _bm25_backend_results(self._retriever, self._chunks, query_tokens, top_k)


class DocumentBm25Retriever:
    """BM25 retriever that ranks whole source documents instead of chunks.

    Enterprise-style RAG benchmarks often score document identifiers, and their
    BM25 baselines commonly index one concatenated ``title + content`` field per
    source. This retriever preserves Heph chunk references for context
    injection, but its sparse corpus has exactly one row per indexed document.
    """

    def __init__(self, index: ArmoryIndex) -> None:
        self._index = index
        self._documents = [document for document in index.documents if document.chunks]
        self._chunks = [document.chunks[0] for document in self._documents]
        self._retriever: object | None = None
        self._corpus_tokens: list[list[str]] = []
        self._idf: dict[str, float] = {}
        self._avg_doc_len = 0.0
        if self._documents:
            self._retriever = _load_bm25_backend_cache(index, _BM25_DOCUMENT_BACKEND_CACHE_KEY)
            if self._retriever is not None:
                return
            self._build(index)

    @property
    def available(self) -> bool:
        return self._retriever is not None or bool(self._idf)

    def _build(self, index: ArmoryIndex) -> None:
        document_texts: list[str] = []
        for document in self._documents:
            material_path = index.armory_path / document.source
            try:
                if material_path.is_file():
                    document_texts.append(material_path.read_text(encoding="utf-8"))
                    continue
            except OSError:
                pass

            parts: list[str] = []
            previous_heading = ""
            for chunk in sorted(document.chunks, key=lambda item: item.index):
                if chunk.heading and chunk.heading != previous_heading:
                    parts.append(chunk.heading)
                    previous_heading = chunk.heading
                parts.append(chunk.text)
            document_texts.append("\n\n".join(parts))

        self._corpus_tokens = [tokenize(text) for text in document_texts]
        self._build_retriever(index)
        if self._retriever is None:
            self._idf, self._avg_doc_len = _bm25_stdlib_state(self._corpus_tokens)
        else:
            self._corpus_tokens = []

    def _build_retriever(self, index: ArmoryIndex) -> None:
        self._retriever = _build_bm25_backend(
            index,
            self._corpus_tokens,
            _BM25_DOCUMENT_BACKEND_CACHE_KEY,
            warning="document bm25 build failed; falling back to stdlib bm25",
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        if not self._documents:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        if self._retriever is None:
            return _bm25_stdlib_results(
                self._chunks,
                self._corpus_tokens,
                query_tokens,
                idf=self._idf,
                avg_doc_len=self._avg_doc_len,
                top_k=top_k,
            )
        return _bm25_backend_results(self._retriever, self._chunks, query_tokens, top_k)
