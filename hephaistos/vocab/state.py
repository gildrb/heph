"""Per-card persistence model for vocabulary scheduling state."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from hephaistos._types import is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.vocab.parser import VocabCard, VocabDeck

_log = get_logger("vocab.state")

_SCHEDULE_FILE = "vocab_schedule.json"

_DEFAULT_EASINESS = 2.5


class VocabCardStatePayload(TypedDict, total=False):
    front: str
    back: str
    source_file: str
    repetitions: int
    easiness: float
    interval: int
    last_review: str
    next_review: str


def _make_card_key(source_file: str, front: str) -> str:
    return f"{source_file}:{front}"


@dataclass(slots=True)
class VocabCardState:
    """Persistent scheduling state for a single vocabulary card."""

    front: str
    back: str
    source_file: str
    repetitions: int = 0
    easiness: float = _DEFAULT_EASINESS
    interval: int = 0
    last_review: datetime | None = None
    next_review: datetime | None = None

    @property
    def key(self) -> str:
        return _make_card_key(self.source_file, self.front)

    @property
    def is_new(self) -> bool:
        return self.repetitions == 0

    def to_dict(self) -> VocabCardStatePayload:
        payload: VocabCardStatePayload = {
            "front": self.front,
            "back": self.back,
            "source_file": self.source_file,
            "repetitions": self.repetitions,
            "easiness": self.easiness,
            "interval": self.interval,
        }
        if self.last_review is not None:
            payload["last_review"] = self.last_review.isoformat()
        if self.next_review is not None:
            payload["next_review"] = self.next_review.isoformat()
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> VocabCardState:
        last_review: datetime | None = None
        raw_last = data.get("last_review")
        if isinstance(raw_last, str):
            with contextlib.suppress(ValueError):
                last_review = datetime.fromisoformat(raw_last)

        next_review: datetime | None = None
        raw_next = data.get("next_review")
        if isinstance(raw_next, str):
            with contextlib.suppress(ValueError):
                next_review = datetime.fromisoformat(raw_next)

        raw_front = data.get("front", "")
        front = raw_front if isinstance(raw_front, str) else ""
        raw_back = data.get("back", "")
        back = raw_back if isinstance(raw_back, str) else ""
        raw_source_file = data.get("source_file", "")
        source_file = raw_source_file if isinstance(raw_source_file, str) else ""
        raw_repetitions = data.get("repetitions", 0)
        repetitions = raw_repetitions if isinstance(raw_repetitions, int) else 0
        raw_easiness = data.get("easiness", _DEFAULT_EASINESS)
        easiness = (
            float(raw_easiness) if isinstance(raw_easiness, int | float) else _DEFAULT_EASINESS
        )
        raw_interval = data.get("interval", 0)
        interval = raw_interval if isinstance(raw_interval, int) else 0
        return cls(
            front=front,
            back=back,
            source_file=source_file,
            repetitions=repetitions,
            easiness=easiness,
            interval=interval,
            last_review=last_review,
            next_review=next_review,
        )

    @classmethod
    def from_card(cls, card: VocabCard) -> VocabCardState:
        return cls(front=card.front, back=card.back, source_file=card.source_file)


class VocabScheduleStore:
    """Persistent store for vocabulary scheduling, stored per-armory."""

    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.cards: dict[str, VocabCardState] = {}
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaistos" / _SCHEDULE_FILE

    @property
    def card_list(self) -> list[VocabCardState]:
        return list(self.cards.values())

    def load(self) -> bool:
        """Load schedule from disk. Returns False if no file exists."""
        if not self._path.is_file():
            return False
        try:
            raw_data = json.loads(self._path.read_text(encoding="utf-8"))
            if not is_string_mapping(raw_data):
                return False
            raw_cards = raw_data.get("cards", {})
            if is_string_mapping(raw_cards):
                for raw_key, raw_value in raw_cards.items():
                    if is_string_mapping(raw_value):
                        self.cards[raw_key] = VocabCardState.from_dict(raw_value)
            _log.info(
                "vocab schedule loaded",
                extra={
                    "fields": {
                        "armory": str(self.armory_path),
                        "cards": len(self.cards),
                    }
                },
            )
            return True
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("vocab schedule load failed", extra={"fields": {"error": str(exc)}})
            return False

    def save(self) -> Path:
        """Persist schedule to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            "cards": {key: state.to_dict() for key, state in self.cards.items()},
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._dirty = False
        _log.info(
            "vocab schedule saved",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "cards": len(self.cards),
                }
            },
        )
        return self._path

    def sync_with_deck(self, deck: VocabDeck) -> int:
        """Reconcile the schedule with the latest deck contents.

        Returns the number of newly added cards. Existing cards keep their
        scheduling progress, but their prompt/answer metadata is refreshed
        from the latest deck contents. Cards that no longer exist in the
        deck are removed from the schedule.
        """
        added = 0
        changed = False
        synced_cards: dict[str, VocabCardState] = {}

        for card in deck.cards:
            key = _make_card_key(card.source_file, card.front)
            existing = synced_cards.get(key) or self.cards.get(key)
            if existing is None:
                synced_cards[key] = VocabCardState.from_card(card)
                added += 1
                changed = True
                continue

            if existing.back != card.back:
                synced_cards[key] = VocabCardState(
                    front=card.front,
                    back=card.back,
                    source_file=card.source_file,
                    repetitions=existing.repetitions,
                    easiness=existing.easiness,
                    interval=existing.interval,
                    last_review=existing.last_review,
                    next_review=existing.next_review,
                )
                changed = True
                continue

            synced_cards[key] = existing

        if len(synced_cards) != len(self.cards):
            changed = True

        self.cards = synced_cards
        if changed:
            self._dirty = True
        return added

    def update_card(self, state: VocabCardState) -> None:
        """Update a card's scheduling state."""
        self.cards[state.key] = state
        self._dirty = True

    def reset_all(self) -> None:
        """Reset all cards to new (unscheduled) state."""
        for state in self.cards.values():
            state.repetitions = 0
            state.easiness = _DEFAULT_EASINESS
            state.interval = 0
            state.last_review = None
            state.next_review = None
        self._dirty = True

    def stats(self) -> dict[str, int]:
        """Return summary statistics."""
        now = datetime.now(UTC)
        total = len(self.cards)
        new = sum(1 for c in self.cards.values() if c.is_new)
        due = sum(1 for c in self.cards.values() if c.next_review is None or c.next_review <= now)
        mastered = sum(1 for c in self.cards.values() if c.repetitions >= 5)
        return {"total": total, "new": new, "due": due, "mastered": mastered}


def load_schedule(armory_path: Path) -> VocabScheduleStore:
    """Load vocabulary schedule for an armory."""
    store = VocabScheduleStore(armory_path)
    store.load()
    return store


def save_schedule(store: VocabScheduleStore) -> Path:
    """Save schedule if it has changed."""
    if store._dirty:
        return store.save()
    return store._path
