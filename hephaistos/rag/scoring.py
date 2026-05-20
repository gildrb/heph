"""Shared scoring helpers for RAG retrieval backends."""

from __future__ import annotations

import re
from collections.abc import Sequence

from hephaistos.rag.retrieval_types import ScoredChunk
from hephaistos.rag.vector import (
    cosine_similarity,
    embedding_rows,
    float_list,
    object_rows,
    sklearn_scores,
)

__all__ = [
    "cosine_similarity",
    "embedding_rows",
    "float_list",
    "object_rows",
    "reciprocal_rank_fusion",
    "sklearn_scores",
    "tokenize",
]

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


def tokenize(text: str) -> list[str]:
    tokens = _WORD_RE.findall(text.lower())
    normalized: list[str] = []
    for token in tokens:
        if token in _STOP_WORDS or (len(token) <= 1 and not token.isdigit()):
            continue
        normalized.append(token)
        stem = token
        if len(token) > 5 and token.endswith("ies"):
            stem = token[:-3] + "y"
        elif len(token) > 5 and token.endswith(("sses", "shes", "ches", "xes", "zes")):
            stem = token[:-2]
        elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            stem = token[:-1]
        if stem != token and stem not in _STOP_WORDS and len(stem) > 1:
            normalized.append(stem)
    return normalized


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    *,
    k: int = 60,
    weights: Sequence[float] | None = None,
) -> list[ScoredChunk]:
    if weights is not None and len(weights) != len(ranked_lists):
        raise ValueError("RRF weights must match the number of ranked lists")
    merged: dict[tuple[str, int], tuple[float, ScoredChunk]] = {}

    for list_index, ranked in enumerate(ranked_lists):
        weight = 1.0 if weights is None else max(0.0, float(weights[list_index]))
        if weight == 0.0:
            continue
        for rank, scored_chunk in enumerate(ranked):
            key = (scored_chunk.chunk.source, scored_chunk.chunk.index)
            rrf_delta = weight / (k + rank + 1)
            if key in merged:
                current_score, best_scored_chunk = merged[key]
                merged[key] = (current_score + rrf_delta, best_scored_chunk)
            else:
                merged[key] = (rrf_delta, scored_chunk)

    results = [
        ScoredChunk(chunk=scored_chunk.chunk, score=score)
        for score, scored_chunk in merged.values()
    ]
    results.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return results
