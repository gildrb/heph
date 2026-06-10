"""Per-card persistence model for vocabulary scheduling state."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from ai.logging import get_logger

from hephaion._types import is_string_mapping
from hephaion.armory.state_files import read_armory_state_text, write_armory_state_text
from hephaion.vocab.parser import VocabCard, VocabDeck

_log = get_logger("hephaion.vocab.state")

_SCHEDULE_FILE = "vocab_schedule.json"
_SCHEDULE_REL_PATH = f".hephaion/{_SCHEDULE_FILE}"

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


def _string_field(data: Mapping[str, object], key: str) -> str:
    value = data.get(key, "")
    return value if isinstance(value, str) else ""


def _int_field(data: Mapping[str, object], key: str) -> int:
    value = data.get(key, 0)
    return value if isinstance(value, int) else 0


def _float_field(data: Mapping[str, object], key: str, default: float) -> float:
    value = data.get(key, default)
    return float(value) if isinstance(value, int | float) else default


def _datetime_field(data: Mapping[str, object], key: str) -> datetime | None:
    value = data.get(key)
    if not isinstance(value, str):
        return None
    with contextlib.suppress(ValueError):
        return datetime.fromisoformat(value)
    return None


@dataclass(slots=True)
class VocabCardState:
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
        return cls(
            front=_string_field(data, "front"),
            back=_string_field(data, "back"),
            source_file=_string_field(data, "source_file"),
            repetitions=_int_field(data, "repetitions"),
            easiness=_float_field(data, "easiness", _DEFAULT_EASINESS),
            interval=_int_field(data, "interval"),
            last_review=_datetime_field(data, "last_review"),
            next_review=_datetime_field(data, "next_review"),
        )

    @classmethod
    def from_card(cls, card: VocabCard) -> VocabCardState:
        return cls(front=card.front, back=card.back, source_file=card.source_file)


class VocabScheduleStore:
    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.cards: dict[str, VocabCardState] = {}
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaion" / _SCHEDULE_FILE

    @property
    def card_list(self) -> list[VocabCardState]:
        return list(self.cards.values())

    def load(self) -> bool:
        if not self._path.is_file():
            return False
        try:
            raw_data = json.loads(read_armory_state_text(self.armory_path, _SCHEDULE_REL_PATH))
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
        data = {
            "version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            "cards": {key: state.to_dict() for key, state in self.cards.items()},
        }
        path = write_armory_state_text(
            self.armory_path,
            _SCHEDULE_REL_PATH,
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
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
        return path

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
                synced_cards[key] = replace(existing, front=card.front, back=card.back)
                changed = True
                continue

            synced_cards[key] = existing

        changed = changed or len(synced_cards) != len(self.cards)

        self.cards = synced_cards
        if changed:
            self._dirty = True
        return added

    def update_card(self, state: VocabCardState) -> None:
        self.cards[state.key] = state
        self._dirty = True

    def reset_all(self) -> None:
        for state in self.cards.values():
            state.repetitions = 0
            state.easiness = _DEFAULT_EASINESS
            state.interval = 0
            state.last_review = None
            state.next_review = None
        self._dirty = True

    def stats(self) -> dict[str, int]:
        now = datetime.now(UTC)
        total = len(self.cards)
        new = sum(1 for c in self.cards.values() if c.is_new)
        due = sum(1 for c in self.cards.values() if c.next_review is None or c.next_review <= now)
        mastered = sum(1 for c in self.cards.values() if c.repetitions >= 5)
        return {"total": total, "new": new, "due": due, "mastered": mastered}


def load_schedule(armory_path: Path) -> VocabScheduleStore:
    store = VocabScheduleStore(armory_path)
    store.load()
    return store


def save_schedule(store: VocabScheduleStore) -> Path:
    return store.save() if store._dirty else store._path
