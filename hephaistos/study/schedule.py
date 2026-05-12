"""Persistent study-item scheduling driven by recall timing."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import log
from pathlib import Path
from typing import TypedDict

from hephaistos._types import is_string_mapping
from hephaistos.study.state import StudyRecallRating

_SCHEDULE_FILE = "study_schedule.json"
_DEFAULT_DIFFICULTY = 5.0
_DEFAULT_STABILITY = 1.0
_MAX_INTERVAL_DAYS = 365
_DESIRED_RETENTION = 0.9
_FAST_RECALL_SECONDS = 30
_SLOW_RECALL_SECONDS = 120


class StudyItemPayload(TypedDict, total=False):
    item: str
    concept: str
    retrieval_query: str
    source_refs: list[str]
    reviews: int
    failures: int
    difficulty: float
    stability: float
    last_recall_seconds: int
    last_rating: str
    last_correct: bool
    last_confidence: float
    last_retrieval_success: bool
    last_transfer_success: bool
    error_type: str
    exam_importance: float
    last_review: str
    next_review: str


@dataclass(slots=True)
class StudyItemState:
    """Scheduling state for one material-backed study item."""

    item: str
    concept: str = ""
    retrieval_query: str = ""
    source_refs: list[str] | None = None
    reviews: int = 0
    failures: int = 0
    difficulty: float = _DEFAULT_DIFFICULTY
    stability: float = _DEFAULT_STABILITY
    last_recall_seconds: int | None = None
    last_rating: StudyRecallRating = StudyRecallRating.NONE
    last_correct: bool = False
    last_confidence: float | None = None
    last_retrieval_success: bool = False
    last_transfer_success: bool = False
    error_type: str = ""
    exam_importance: float = 0.0
    last_review: datetime | None = None
    next_review: datetime | None = None

    def retrievability(self, *, now: datetime | None = None) -> float:
        """Estimate recall probability using the FSRS forgetting curve shape."""
        if self.last_review is None:
            return 0.0
        current_time = now or datetime.now(UTC)
        elapsed_days = max(0.0, (current_time - self.last_review).total_seconds() / 86400)
        return _retrievability(self.stability, elapsed_days)

    @property
    def key(self) -> str:
        refs = "|".join(self.source_refs or [])
        return f"{self.retrieval_query or self.item}:{refs}"

    def to_dict(self) -> StudyItemPayload:
        payload: StudyItemPayload = {
            "item": self.item,
            "concept": self.concept,
            "retrieval_query": self.retrieval_query,
            "source_refs": list(self.source_refs or []),
            "reviews": self.reviews,
            "failures": self.failures,
            "difficulty": self.difficulty,
            "stability": self.stability,
            "last_rating": self.last_rating.value,
            "last_correct": self.last_correct,
            "last_retrieval_success": self.last_retrieval_success,
            "last_transfer_success": self.last_transfer_success,
            "error_type": self.error_type,
            "exam_importance": self.exam_importance,
        }
        if self.last_recall_seconds is not None:
            payload["last_recall_seconds"] = self.last_recall_seconds
        if self.last_confidence is not None:
            payload["last_confidence"] = self.last_confidence
        if self.last_review is not None:
            payload["last_review"] = self.last_review.isoformat()
        if self.next_review is not None:
            payload["next_review"] = self.next_review.isoformat()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> StudyItemState:
        raw_refs = data.get("source_refs", [])
        refs = (
            [ref for ref in raw_refs if isinstance(ref, str)] if isinstance(raw_refs, list) else []
        )
        raw_rating = data.get("last_rating", "")
        rating = StudyRecallRating.NONE
        if isinstance(raw_rating, str):
            with contextlib.suppress(ValueError):
                rating = StudyRecallRating(raw_rating)
        raw_seconds = data.get("last_recall_seconds")
        return cls(
            item=_str_or(data.get("item"), ""),
            concept=_str_or(data.get("concept"), ""),
            retrieval_query=_str_or(data.get("retrieval_query"), ""),
            source_refs=refs,
            reviews=_int_or(data.get("reviews"), 0),
            failures=_int_or(data.get("failures"), 0),
            difficulty=_float_or(data.get("difficulty"), _DEFAULT_DIFFICULTY),
            stability=_float_or(data.get("stability"), _DEFAULT_STABILITY),
            last_recall_seconds=raw_seconds if isinstance(raw_seconds, int) else None,
            last_rating=rating,
            last_correct=_bool_or(data.get("last_correct"), rating is StudyRecallRating.EASY),
            last_confidence=_optional_bounded_float(data.get("last_confidence"), 0.0, 1.0),
            last_retrieval_success=_bool_or(data.get("last_retrieval_success"), bool(refs)),
            last_transfer_success=_bool_or(data.get("last_transfer_success"), False),
            error_type=_str_or(data.get("error_type"), ""),
            exam_importance=_bounded_float_or(data.get("exam_importance"), 0.0, 0.0, 1.0),
            last_review=_parse_datetime(data.get("last_review")),
            next_review=_parse_datetime(data.get("next_review")),
        )


class StudyScheduleStore:
    """Armory-local store for material-backed study review state."""

    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.items: dict[str, StudyItemState] = {}
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaistos" / _SCHEDULE_FILE

    @property
    def item_list(self) -> list[StudyItemState]:
        return list(self.items.values())

    def due_items(self, *, now: datetime | None = None, limit: int = 0) -> list[StudyItemState]:
        current_time = now or datetime.now(UTC)
        due = [
            item
            for item in self.items.values()
            if item.next_review is not None and item.next_review <= current_time
        ]
        due.sort(
            key=lambda item: (
                item.next_review or current_time,
                -item.exam_importance,
                -item.failures,
                -item.difficulty,
            )
        )
        if limit > 0:
            return due[:limit]
        return due

    def load(self) -> bool:
        if not self._path.is_file():
            return False
        with contextlib.suppress(json.JSONDecodeError, OSError):
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not is_string_mapping(raw):
                return False
            raw_items = raw.get("items", {})
            if is_string_mapping(raw_items):
                self.items = {
                    key: StudyItemState.from_dict(value)
                    for key, value in raw_items.items()
                    if is_string_mapping(value)
                }
                return True
        return False

    def save(self) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            "items": {key: item.to_dict() for key, item in sorted(self.items.items())},
        }
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        self._dirty = False
        return self._path

    def record_review(
        self,
        item: str,
        *,
        concept: str = "",
        retrieval_query: str,
        source_refs: list[str],
        rating: StudyRecallRating,
        elapsed_seconds: int | None,
        confidence: float | None = None,
        retrieval_success: bool | None = None,
        transfer_success: bool | None = None,
        error_type: str = "",
        exam_importance: float = 0.0,
        now: datetime | None = None,
    ) -> StudyItemState:
        current_time = now or datetime.now(UTC)
        bounded_exam_importance = min(1.0, max(0.0, exam_importance))
        state = StudyItemState(
            item=item,
            concept=concept,
            retrieval_query=retrieval_query,
            source_refs=source_refs,
            error_type=error_type,
            exam_importance=bounded_exam_importance,
        )
        existing = self.items.get(state.key)
        if existing is not None:
            state = existing
            state.item = item
            state.concept = concept or state.concept
            state.retrieval_query = retrieval_query
            state.source_refs = list(source_refs)
            state.error_type = error_type or state.error_type
            state.exam_importance = max(state.exam_importance, bounded_exam_importance)

        state.reviews += 1
        state.last_rating = rating
        state.last_correct = rating in {StudyRecallRating.EASY, StudyRecallRating.GOOD}
        if not state.last_correct:
            state.failures += 1
        state.last_recall_seconds = elapsed_seconds
        state.last_confidence = confidence
        state.last_retrieval_success = (
            bool(source_refs) if retrieval_success is None else retrieval_success
        )
        state.last_transfer_success = (
            state.last_correct and _looks_like_transfer_item(item)
            if transfer_success is None
            else transfer_success
        )
        state.last_review = current_time
        state.difficulty = _next_difficulty(state.difficulty, rating, elapsed_seconds)
        state.stability = _next_stability(state.stability, rating, elapsed_seconds)
        state.next_review = current_time + _review_interval(state.stability, rating)
        self.items[state.key] = state
        self._dirty = True
        return state


def load_study_schedule(armory_path: Path) -> StudyScheduleStore:
    store = StudyScheduleStore(armory_path)
    store.load()
    return store


def save_study_schedule(store: StudyScheduleStore) -> Path:
    if store._dirty:
        return store.save()
    return store._path


def _next_difficulty(
    current: float,
    rating: StudyRecallRating,
    elapsed_seconds: int | None = None,
) -> float:
    delta = _difficulty_delta(rating)
    if elapsed_seconds is not None and elapsed_seconds >= _SLOW_RECALL_SECONDS:
        delta += 0.25
    elif elapsed_seconds is not None and elapsed_seconds <= _FAST_RECALL_SECONDS:
        delta -= 0.1
    return min(10.0, max(1.0, round(current + delta, 3)))


def _next_stability(
    current: float,
    rating: StudyRecallRating,
    elapsed_seconds: int | None,
) -> float:
    speed_factor = _elapsed_stability_factor(elapsed_seconds)
    multiplier = {
        StudyRecallRating.EASY: 2.6,
        StudyRecallRating.GOOD: 1.8,
        StudyRecallRating.HARD: 0.6,
        StudyRecallRating.NONE: 1.0,
    }[rating]
    return max(0.25, min(float(_MAX_INTERVAL_DAYS), round(current * multiplier * speed_factor, 3)))


def _review_interval(stability: float, rating: StudyRecallRating) -> timedelta:
    if rating is StudyRecallRating.HARD:
        return timedelta(days=1)
    if rating is StudyRecallRating.NONE:
        return timedelta(0)
    return timedelta(days=_interval_days_for_retention(stability, _DESIRED_RETENTION))


def _difficulty_delta(rating: StudyRecallRating) -> float:
    return {
        StudyRecallRating.EASY: -0.45,
        StudyRecallRating.GOOD: -0.15,
        StudyRecallRating.HARD: 0.65,
        StudyRecallRating.NONE: 0.0,
    }[rating]


def _elapsed_stability_factor(elapsed_seconds: int | None) -> float:
    if elapsed_seconds is None:
        return 1.0
    if elapsed_seconds <= _FAST_RECALL_SECONDS:
        return 1.15
    if elapsed_seconds >= _SLOW_RECALL_SECONDS:
        return 0.75
    return 1.0


def _interval_days_for_retention(stability: float, desired_retention: float) -> int:
    retention = min(0.99, max(0.7, desired_retention))
    days = stability * log(retention) / log(0.9)
    return min(_MAX_INTERVAL_DAYS, max(1, round(days)))


def _retrievability(stability: float, elapsed_days: float) -> float:
    if stability <= 0:
        return 0.0
    return max(0.0, min(1.0, 0.9 ** (elapsed_days / stability)))


def _looks_like_transfer_item(item: str) -> bool:
    lowered = item.casefold()
    return any(
        marker in lowered
        for marker in (
            "apply",
            "application",
            "scenario",
            "compare",
            "contrast",
            "why",
            "explain why",
        )
    )


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    with contextlib.suppress(ValueError):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _int_or(value: object, default: int) -> int:
    return value if isinstance(value, int) else default


def _bool_or(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _float_or(value: object, default: float) -> float:
    return float(value) if isinstance(value, int | float) else default


def _bounded_float_or(value: object, default: float, minimum: float, maximum: float) -> float:
    parsed = _float_or(value, default)
    return min(maximum, max(minimum, parsed))


def _optional_bounded_float(value: object, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return min(maximum, max(minimum, float(value)))


def _str_or(value: object, default: str) -> str:
    return value if isinstance(value, str) else default
