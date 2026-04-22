"""SM-2 spaced repetition scheduler — Anki-style interval computation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hephaistos.vocab.state import VocabCardState

_MIN_EASINESS = 1.3
_DEFAULT_EASINESS = 2.5
_MAX_INTERVAL_DAYS = 365


class Rating(IntEnum):
    """User recall rating mapped to SM-2 quality levels."""

    HARD = 3
    GOOD = 4
    EASY = 5


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    """Result of scheduling a card after a rating."""

    repetitions: int
    easiness: float
    interval_days: int


def _update_easiness(current: float, quality: int) -> float:
    """SM-2 easiness factor update."""
    new = current + 0.1 - (5.0 - quality) * (0.08 + (5.0 - quality) * 0.02)
    return max(_MIN_EASINESS, new)


def schedule_card(card: VocabCardState, rating: Rating) -> ScheduleResult:
    """Compute the next review state for a card given a user rating.

    Implements Anki's modified SM-2 algorithm:
    - Hard (quality 3): ease decreases, short interval
    - Good (quality 4): ease unchanged, standard interval
    - Easy (quality 5): ease increases, interval boosted

    Parameters
    ----------
    card :
        Current card state.
    rating :
        User's recall rating.

    Returns
    -------
    ScheduleResult
        New repetitions, easiness, and interval (in days).
    """
    quality = int(rating)
    easiness = _update_easiness(card.easiness, quality)
    repetitions = 0 if quality < 3 else card.repetitions + 1

    if repetitions <= 1:
        interval = 1
    elif repetitions == 2:
        interval = 6
    else:
        interval = max(1, math.ceil(card.interval * easiness))

    interval = min(interval, _MAX_INTERVAL_DAYS)

    return ScheduleResult(
        repetitions=repetitions,
        easiness=round(easiness, 4),
        interval_days=interval,
    )


def select_due_cards(cards: list[VocabCardState], *, limit: int = 0) -> list[VocabCardState]:
    """Return cards that are due for review, sorted by priority.

    Priority order:
    1. Overdue cards (most overdue first)
    2. New cards (never reviewed)

    Parameters
    ----------
    cards :
        All card states.
    limit :
        Maximum number of cards to return. 0 means no limit.
    """
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    due = [card for card in cards if card.next_review is None or card.next_review <= now]

    # Sort: overdue first (largest gap), then new cards.
    def _sort_key(c: VocabCardState) -> tuple[int, float]:
        if c.next_review is None:
            # New cards come after overdue ones.
            return (1, 0.0)
        # Negative timedelta so most overdue sorts first.
        overdue = (now - c.next_review).total_seconds()
        return (0, -overdue)

    due.sort(key=_sort_key)

    if limit > 0:
        due = due[:limit]
    return due
