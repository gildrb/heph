"""Shared deterministic mastery updates for recall workflows."""

from __future__ import annotations

from hephaion.study.state import RecallRating


def next_recall_mastery(
    current: float,
    rating: RecallRating,
    hint_level_needed: int | None,
) -> float:
    correctness = {
        RecallRating.EASY: 1.0,
        RecallRating.GOOD: 0.82,
        RecallRating.HARD: 0.22,
        RecallRating.NONE: 0.0,
    }[rating]
    if hint_level_needed is not None:
        correctness = max(0.0, correctness - min(0.35, hint_level_needed * 0.07))
    if current <= 0:
        return round(correctness, 4)
    return round((current * 0.65) + (correctness * 0.35), 4)
