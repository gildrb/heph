"""Tests for human-facing fuzzy matching helpers."""

from __future__ import annotations

from hephaistos.fuzzy import ranked_matches


def test_ranked_matches_returns_best_match_first() -> None:
    choices = ["binary search", "merge sort", "python basics"]

    matches = ranked_matches("binry serch", choices, key=lambda value: value, min_score=40.0)

    assert matches
    assert matches[0].value == "binary search"


def test_ranked_matches_respects_score_cutoff() -> None:
    matches = ranked_matches("zzzz", ["binary search"], key=lambda value: value, min_score=95.0)

    assert matches == []
