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
    query_terms = _match_terms(normalized_query)
    matches = [
        FuzzyMatch(value=choice, score=score)
        for choice in choices
        if (score := _match_score(query, normalized_query, query_terms, key(choice))) >= min_score
    ]
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[:limit]


def _match_score(
    query: str,
    normalized_query: str,
    query_terms: set[str],
    candidate: str,
) -> float:
    normalized_candidate = candidate.casefold().strip()
    compact_query = _compact_match_text(normalized_query)
    compact_candidate = _compact_match_text(normalized_candidate)
    if compact_query and compact_candidate:
        if compact_query == compact_candidate:
            return 100.0
        if compact_query in compact_candidate:
            return 92.0
    if fuzz is not None:
        return max(
            float(fuzz.WRatio(query, candidate)),
            float(fuzz.WRatio(compact_query, compact_candidate)),
        )
    return _fallback_score(normalized_query, query_terms, candidate)


def _compact_match_text(value: str) -> str:
    return "".join(character for character in value if character.isalnum())


def _match_terms(value: str) -> set[str]:
    separated = "".join(character if character.isalnum() else " " for character in value)
    return set(separated.split())


def _fallback_score(normalized_query: str, query_terms: set[str], candidate: str) -> float:
    normalized_candidate = candidate.casefold().strip()
    if not normalized_query or not normalized_candidate:
        return 0.0
    if normalized_query == normalized_candidate:
        return 100.0
    if normalized_query in normalized_candidate:
        return 85.0
    compact_query = _compact_match_text(normalized_query)
    compact_candidate = _compact_match_text(normalized_candidate)
    if compact_query and compact_candidate:
        if compact_query == compact_candidate:
            return 100.0
        if compact_query in compact_candidate:
            return 92.0
    return _term_overlap_score(query_terms, normalized_candidate)


def _term_overlap_score(query_terms: set[str], normalized_candidate: str) -> float:
    if not query_terms:
        return 0.0
    candidate_terms = _match_terms(normalized_candidate)
    return 100.0 * (len(query_terms & candidate_terms) / len(query_terms))
