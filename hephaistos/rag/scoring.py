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
type _PluralRule = tuple[int, str | tuple[str, ...], int, str]
_PLURAL_RULES: tuple[_PluralRule, ...] = (
    (5, "ies", 3, "y"),
    (5, ("sses", "shes", "ches", "xes", "zes"), 2, ""),
    (4, "s", 1, ""),
)


def tokenize(text: str) -> list[str]:
    normalized: list[str] = []
    for token in _WORD_RE.findall(text.lower()):
        if not _keep_token(token):
            continue
        normalized.append(token)
        if (plural_variant := _plural_variant(token)) is not None:
            normalized.append(plural_variant)
    return normalized


def _keep_token(token: str) -> bool:
    return token not in _STOP_WORDS and (len(token) > 1 or token.isdigit())


def _plural_variant(token: str) -> str | None:
    for min_length, suffix, trim, replacement in _PLURAL_RULES:
        if _matches_plural_rule(token, min_length=min_length, suffix=suffix):
            return _kept_variant(token, token[:-trim] + replacement)
    return None


def _matches_plural_rule(
    token: str,
    *,
    min_length: int,
    suffix: str | tuple[str, ...],
) -> bool:
    return len(token) > min_length and token.endswith(suffix) and not token.endswith("ss")


def _kept_variant(token: str, variant: str) -> str | None:
    if variant == token or not _keep_token(variant):
        return None
    return variant


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
        weight = _rrf_weight(weights, list_index)
        if weight == 0.0:
            continue
        for rank, scored_chunk in enumerate(ranked):
            _merge_rrf_result(merged, scored_chunk, score_delta=weight / (k + rank + 1))

    results = [
        ScoredChunk(chunk=scored_chunk.chunk, score=score)
        for score, scored_chunk in merged.values()
    ]
    results.sort(key=lambda scored_chunk: scored_chunk.score, reverse=True)
    return results


def _rrf_weight(weights: Sequence[float] | None, list_index: int) -> float:
    return 1.0 if weights is None else max(0.0, float(weights[list_index]))


def _merge_rrf_result(
    merged: dict[tuple[str, int], tuple[float, ScoredChunk]],
    scored_chunk: ScoredChunk,
    *,
    score_delta: float,
) -> None:
    key = (scored_chunk.chunk.source, scored_chunk.chunk.index)
    current = merged.get(key)
    if current is None:
        merged[key] = (score_delta, scored_chunk)
        return
    current_score, best_scored_chunk = current
    merged[key] = (current_score + score_delta, best_scored_chunk)
