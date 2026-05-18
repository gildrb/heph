"""Shared scoring helpers for RAG retrieval backends."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from typing import Protocol, cast, runtime_checkable

from hephaistos.rag.retrieval_types import ScoredChunk

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


@runtime_checkable
class ToListProtocol(Protocol):
    def tolist(self) -> object: ...


def tokenize(text: str) -> list[str]:
    tokens = _WORD_RE.findall(text.lower())
    normalized: list[str] = []
    for token in tokens:
        if token in _STOP_WORDS or (len(token) <= 1 and not token.isdigit()):
            continue
        normalized.append(token)
        stem = _light_stem(token)
        if stem != token and stem not in _STOP_WORDS and len(stem) > 1:
            normalized.append(stem)
    return normalized


def _light_stem(token: str) -> str:
    """Conservative suffix normalization for sparse retrieval recall."""
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith(("sses", "shes", "ches", "xes", "zes")):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def float_list(values: object) -> list[float]:
    if isinstance(values, ToListProtocol):
        values = values.tolist()
    if not isinstance(values, list):
        return []
    result: list[float] = []
    typed_values = cast("list[object]", values)
    for value in typed_values:
        if not isinstance(value, int | float):
            return []
        result.append(float(value))
    return result


def embedding_rows(values: object) -> list[list[float]]:
    if isinstance(values, ToListProtocol):
        values = values.tolist()
    if not isinstance(values, list):
        return []
    rows: list[list[float]] = []
    typed_values = cast("list[object]", values)
    for row in typed_values:
        typed_row = float_list(row)
        if typed_row:
            rows.append(typed_row)
    return rows


def object_rows(values: object) -> list[list[object]]:
    if isinstance(values, ToListProtocol):
        values = values.tolist()
    if not isinstance(values, list):
        return []
    typed_values = cast("list[object]", values)
    return [cast("list[object]", row) for row in typed_values if isinstance(row, list)]


def sklearn_scores(query_vector: object, matrix: object) -> list[float]:
    transposed = getattr(matrix, "T", None)
    matmul = getattr(query_vector, "__matmul__", None)
    if transposed is None or not callable(matmul):
        return []
    raw_scores = matmul(transposed)
    toarray = getattr(raw_scores, "toarray", None)
    if not callable(toarray):
        return []
    flattened = toarray()
    flatten = getattr(flattened, "flatten", None)
    if callable(flatten):
        flattened = flatten()
    return float_list(flattened)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    *,
    k: int = 60,
    weights: Sequence[float] | None = None,
) -> list[ScoredChunk]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion (RRF)."""
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
