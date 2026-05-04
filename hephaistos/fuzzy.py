"""Small fuzzy matching helpers for human-facing selectors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

try:
    from rapidfuzz import fuzz  # ty: ignore
except ImportError:
    fuzz = None  # type: ignore[assignment]

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class FuzzyMatch[T]:
    """A ranked fuzzy match result."""

    value: T
    score: float


def ranked_matches[T](
    query: str,
    choices: list[T],
    *,
    key: Callable[[T], str],
    limit: int = 5,
    min_score: float = 60.0,
) -> list[FuzzyMatch[T]]:
    """Return ranked fuzzy matches for *query*.

    Callers keep ownership of ambiguity handling; this helper only ranks.
    """
    if not query.strip() or not choices:
        return []
    matches: list[FuzzyMatch[T]] = []
    for choice in choices:
        score = _score(query, key(choice))
        if score >= min_score:
            matches.append(FuzzyMatch(value=choice, score=score))
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[:limit]


def _score(query: str, candidate: str) -> float:
    """Score a fuzzy match, falling back to simple substring checks."""
    if fuzz is not None:
        return float(fuzz.WRatio(query, candidate))  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    normalized_query = query.casefold().strip()
    normalized_candidate = candidate.casefold().strip()
    if not normalized_query or not normalized_candidate:
        return 0.0
    if normalized_query == normalized_candidate:
        return 100.0
    if normalized_query in normalized_candidate:
        return 85.0
    query_terms = set(normalized_query.split())
    candidate_terms = set(normalized_candidate.split())
    if not query_terms:
        return 0.0
    return 100.0 * (len(query_terms & candidate_terms) / len(query_terms))
