"""Small fuzzy matching helpers for human-facing selectors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

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
    normalized_query = query.casefold().strip()
    query_terms = set(normalized_query.split())
    matches: list[FuzzyMatch[T]] = []
    for choice in choices:
        candidate = key(choice)
        if fuzz is not None:
            score = float(fuzz.WRatio(query, candidate))
        else:
            normalized_candidate = candidate.casefold().strip()
            if not normalized_query or not normalized_candidate:
                score = 0.0
            elif normalized_query == normalized_candidate:
                score = 100.0
            elif normalized_query in normalized_candidate:
                score = 85.0
            elif query_terms:
                candidate_terms = set(normalized_candidate.split())
                score = 100.0 * (len(query_terms & candidate_terms) / len(query_terms))
            else:
                score = 0.0
        if score >= min_score:
            matches.append(FuzzyMatch(value=choice, score=score))
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[:limit]
