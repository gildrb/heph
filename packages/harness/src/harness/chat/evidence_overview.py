"""Overview evidence sampling for broad material-summary turns."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from html import unescape

from harness.chat.evidence_text import (
    chunk_is_low_content,
    overview_chunk_has_structural_signal,
)
from harness.rag.chunker import Chunk, ChunkedDocument
from harness.rag.retrieval_types import ScoredChunk
from harness.rag.scoring import tokenize

OVERVIEW_CHUNK_LIMIT = 32
OVERVIEW_PRIMARY_SOURCE_LIMIT = 32
OVERVIEW_CITABLE_CHUNK_LIMIT = 10
OVERVIEW_CHUNKS_PER_DOCUMENT = 1
OVERVIEW_EXCERPT_CHAR_LIMIT = 260
OVERVIEW_CONTEXT_TOKEN_BUDGET = 2500
OVERVIEW_DOCUMENT_SCAN_LIMIT = 12
OVERVIEW_SUBSTANTIVE_MIN_SCORE = 16


def overview_scored_chunks(
    documents: Sequence[ChunkedDocument],
    chunks: Sequence[Chunk],
) -> list[ScoredChunk]:
    scored = _round_robin_overview_chunks(documents)
    if scored:
        return scored
    return _fallback_overview_chunks(chunks)


def _round_robin_overview_chunks(documents: Sequence[ChunkedDocument]) -> list[ScoredChunk]:
    scored: list[ScoredChunk] = []
    chunks_by_document = [
        _overview_document_chunks(document) for document in _overview_selected_documents(documents)
    ]
    for offset in range(OVERVIEW_CHUNKS_PER_DOCUMENT):
        if _append_overview_offset(scored, chunks_by_document, offset):
            return scored
    return scored


def _overview_selected_documents(
    documents: Sequence[ChunkedDocument],
) -> tuple[ChunkedDocument, ...]:
    ranked = tuple(sorted(documents, key=_overview_document_sort_key))
    return ranked[: min(OVERVIEW_PRIMARY_SOURCE_LIMIT, OVERVIEW_CHUNK_LIMIT)]


def _append_overview_offset(
    scored: list[ScoredChunk],
    chunks_by_document: Sequence[Sequence[Chunk]],
    offset: int,
) -> bool:
    for document_chunks in chunks_by_document:
        if offset < len(document_chunks):
            scored.append(_overview_scored_chunk(document_chunks[offset]))
        if len(scored) >= OVERVIEW_CHUNK_LIMIT:
            return True
    return False


def _overview_document_chunks(document: ChunkedDocument) -> tuple[Chunk, ...]:
    chunks = tuple(chunk for chunk in document.chunks if not chunk_is_low_content(chunk.text))
    return tuple(
        sorted(
            chunks,
            key=lambda chunk: _overview_chunk_sort_key(document.source, chunk),
        )
    )


def _overview_document_sort_key(
    document: ChunkedDocument,
) -> tuple[int, int, int, int, int, int, int, str]:
    chunks = _overview_document_chunks(document)
    if not chunks:
        return (1, 1, 1, 1, 1, 0, len(document.chunks), document.source.casefold())
    best_chunk = chunks[0]
    score_text = _overview_chunk_score_text(best_chunk.text)
    covered = _overview_chunk_looks_like_cover_page(score_text)
    substantive = _overview_chunk_content_score(score_text) >= OVERVIEW_SUBSTANTIVE_MIN_SCORE
    structural = substantive and overview_chunk_has_structural_signal(score_text)
    early = best_chunk.index < OVERVIEW_DOCUMENT_SCAN_LIMIT
    acceptable = substantive and not covered
    return (
        int(not early),
        int(not structural),
        int(not acceptable),
        int(_overview_chunk_has_dense_enumeration(score_text)),
        -_overview_chunk_content_score(score_text),
        best_chunk.index,
        len(document.chunks),
        document.source.casefold(),
    )


def _overview_chunk_sort_key(
    source: str,
    chunk: Chunk,
) -> tuple[int, int, int, int, int]:
    _ = source
    score_text = _overview_chunk_score_text(chunk.text)
    covered = _overview_chunk_looks_like_cover_page(score_text)
    substantive = _overview_chunk_content_score(score_text) >= OVERVIEW_SUBSTANTIVE_MIN_SCORE
    structural = substantive and overview_chunk_has_structural_signal(score_text)
    early = chunk.index < OVERVIEW_DOCUMENT_SCAN_LIMIT
    acceptable = substantive and not covered
    return (
        int(not early),
        int(not structural),
        int(not acceptable),
        int(_overview_chunk_has_dense_enumeration(score_text)),
        chunk.index,
    )


def _overview_chunk_content_score(text: str) -> int:
    token_count = len(set(tokenize(text)))
    punctuation_count = sum(text.count(mark) for mark in ".;:?!")
    section_bonus = 30 if "\f" in text else 0
    return min(token_count, 80) + min(punctuation_count, 12) * 4 + section_bonus


def _overview_chunk_has_dense_enumeration(text: str) -> bool:
    return len(re.findall(r"(?:^|\s)\d{1,3}[.)]", text)) >= 2


def _overview_chunk_score_text(text: str) -> str:
    sections = [section.strip() for section in text.split("\f") if section.strip()]
    return sections[-1] if len(sections) > 1 else text


def _overview_chunk_looks_like_cover_page(text: str) -> bool:
    normalized = " ".join(unescape(text).split())
    if not normalized:
        return True
    sentence_text = re.sub(r"\b\d{1,2}\.", "", normalized)
    return not any(mark in sentence_text for mark in ".!?;:")


def _fallback_overview_chunks(chunks: Sequence[Chunk]) -> list[ScoredChunk]:
    return [
        _overview_scored_chunk(chunk) for chunk in chunks if not chunk_is_low_content(chunk.text)
    ][:OVERVIEW_CHUNK_LIMIT]


def _overview_scored_chunk(chunk: Chunk) -> ScoredChunk:
    return ScoredChunk(chunk=_compact_overview_chunk(chunk), score=1.0)


def _compact_overview_chunk(chunk: Chunk) -> Chunk:
    text = " ".join(_overview_chunk_score_text(chunk.text).split())
    if len(text) <= OVERVIEW_EXCERPT_CHAR_LIMIT:
        return replace(chunk, text=text)
    return replace(
        chunk,
        text=text[: OVERVIEW_EXCERPT_CHAR_LIMIT - 17].rstrip() + "\n[... truncated]",
    )


__all__ = [
    "OVERVIEW_CITABLE_CHUNK_LIMIT",
    "OVERVIEW_CONTEXT_TOKEN_BUDGET",
    "overview_scored_chunks",
]
