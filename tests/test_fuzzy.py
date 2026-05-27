"""Tests for human-facing fuzzy matching helpers."""

from __future__ import annotations

from unittest import mock

from hephaion.matching import ranked_matches


def test_ranked_matches_returns_best_match_first() -> None:
    choices = ["binary search", "merge sort", "python basics"]

    # Use a query whose words overlap with the target (fallback has no typo
    # tolerance, so exact word overlap is required).
    matches = ranked_matches("binary", choices, key=lambda value: value, min_score=40.0)

    assert matches
    assert matches[0].value == "binary search"


def test_ranked_matches_respects_score_cutoff() -> None:
    matches = ranked_matches("zzzz", ["binary search"], key=lambda value: value, min_score=95.0)

    assert matches == []


class TestRapidfuzzFallback:
    """Verify fuzzy matching works when rapidfuzz is not installed."""

    def test_fallback_exact_match_passes_high_cutoff(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches("hello", ["hello"], key=lambda value: value, min_score=100.0)
            assert matches

    def test_fallback_substring_passes_expected_cutoff(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches(
                "hello", ["hello world"], key=lambda value: value, min_score=85.0
            )
            assert matches

    def test_fallback_word_overlap_partial(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches(
                "binary search",
                ["binary tree search"],
                key=lambda value: value,
                min_score=90.0,
            )
            assert matches

    def test_fallback_no_match_respects_cutoff(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches("xyz", ["abc"], key=lambda value: value, min_score=10.0)
            assert matches == []

    def test_fallback_empty_query_returns_no_matches(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches("", ["something"], key=lambda value: value)
            assert matches == []

    def test_fallback_empty_candidate_respects_cutoff(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            matches = ranked_matches("something", [""], key=lambda value: value, min_score=1.0)
            assert matches == []

    def test_ranked_matches_works_without_rapidfuzz(self) -> None:
        with mock.patch("hephaion.matching.fuzz", None):
            choices = ["binary search", "merge sort", "python basics"]
            matches = ranked_matches("binary", choices, key=lambda v: v, min_score=10.0)
            assert matches
            assert matches[0].value == "binary search"
