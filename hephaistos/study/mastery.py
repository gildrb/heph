"""Shared deterministic mastery updates for recall workflows."""

from __future__ import annotations

from hephaistos.study.state import StudyRecallRating


def next_recall_mastery(
    current: float,
    rating: StudyRecallRating,
    hint_level_needed: int | None,
) -> float:
    """Return the next bounded mastery estimate after one recall attempt."""
    correctness = {
        StudyRecallRating.EASY: 1.0,
        StudyRecallRating.GOOD: 0.82,
        StudyRecallRating.HARD: 0.22,
        StudyRecallRating.NONE: 0.0,
    }[rating]
    if hint_level_needed is not None:
        correctness = max(0.0, correctness - min(0.35, hint_level_needed * 0.07))
    if current <= 0:
        return round(correctness, 4)
    return round((current * 0.65) + (correctness * 0.35), 4)
