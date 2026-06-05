from __future__ import annotations

import contextlib
import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import log
from pathlib import Path
from typing import TypedDict

from _types import is_object_list, is_string_mapping

from study.mastery import next_recall_mastery
from study.state import RecallRating

_RECALL_SCHEDULE_FILE = "recall_schedule.json"
_LEGACY_RECALL_SCHEDULE_FILE = "study_schedule.json"
_DEFAULT_DIFFICULTY = 5.0
_DEFAULT_STABILITY = 1.0
_MAX_INTERVAL_DAYS = 365
_DESIRED_RETENTION = 0.9
_FAST_RECALL_SECONDS = 30
_SLOW_RECALL_SECONDS = 120
_TRANSFER_PROMPT_RE = re.compile(
    r"\b(?:apply|transfer|use)\b|\bnew\s+(?:case|example|scenario|situation)\b",
    re.IGNORECASE,
)
type _NextActionRule = tuple[Callable[[RecallRating, float, float | None, int | None], bool], str]


class RecallItemPayload(TypedDict, total=False):
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
    mastery: float
    calibration_gap: float
    hint_level_needed: int
    solved_after_hint: bool
    common_errors: list[str]
    successful_interventions: list[str]
    failed_interventions: list[str]
    next_best_action: str
    exam_importance: float
    last_review: str
    next_review: str


class PolicyMoveStatsPayload(TypedDict):
    uses: int
    successes: int
    total_mastery_delta: float
    total_confidence_delta: float
    total_time_seconds: int
    frustration_count: int


@dataclass(slots=True)
class _SchedulePayload:
    items: dict[str, RecallItemState]
    policy_stats: dict[str, PolicyMoveStats]


@dataclass(slots=True)
class RecallItemState:
    item: str
    concept: str = ""
    retrieval_query: str = ""
    source_refs: list[str] | None = None
    reviews: int = 0
    failures: int = 0
    difficulty: float = _DEFAULT_DIFFICULTY
    stability: float = _DEFAULT_STABILITY
    last_recall_seconds: int | None = None
    last_rating: RecallRating = RecallRating.NONE
    last_correct: bool = False
    last_confidence: float | None = None
    last_retrieval_success: bool = False
    last_transfer_success: bool = False
    error_type: str = ""
    mastery: float = 0.0
    calibration_gap: float | None = None
    hint_level_needed: int | None = None
    solved_after_hint: bool = False
    common_errors: list[str] | None = None
    successful_interventions: list[str] | None = None
    failed_interventions: list[str] | None = None
    next_best_action: str = ""
    exam_importance: float = 0.0
    last_review: datetime | None = None
    next_review: datetime | None = None

    def retrievability(self, *, now: datetime | None = None) -> float:
        if self.last_review is None:
            return 0.0
        current_time = now or datetime.now(UTC)
        elapsed_days = max(0.0, (current_time - self.last_review).total_seconds() / 86400)
        if self.stability <= 0:
            return 0.0
        return max(0.0, min(1.0, 0.9 ** (elapsed_days / self.stability)))

    @property
    def key(self) -> str:
        refs = "|".join(self.source_refs or [])
        return f"{self.retrieval_query or self.item}:{refs}"

    def to_dict(self) -> RecallItemPayload:
        payload: RecallItemPayload = {
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
            "mastery": self.mastery,
            "solved_after_hint": self.solved_after_hint,
            "common_errors": list(self.common_errors or []),
            "successful_interventions": list(self.successful_interventions or []),
            "failed_interventions": list(self.failed_interventions or []),
            "next_best_action": self.next_best_action,
            "exam_importance": self.exam_importance,
        }
        payload.update(_optional_recall_item_payload(self))
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> RecallItemState:
        refs = _string_list(data.get("source_refs"))
        raw_rating = data.get("last_rating", "")
        rating = RecallRating.NONE
        if isinstance(raw_rating, str):
            with contextlib.suppress(ValueError):
                rating = RecallRating(raw_rating)
        raw_seconds = data.get("last_recall_seconds")
        raw_hint_level = data.get("hint_level_needed")
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
            last_correct=_bool_or(data.get("last_correct"), rating is RecallRating.EASY),
            last_confidence=_optional_bounded_float(data.get("last_confidence"), 0.0, 1.0),
            last_retrieval_success=_bool_or(data.get("last_retrieval_success"), bool(refs)),
            last_transfer_success=_bool_or(data.get("last_transfer_success"), False),
            error_type=_str_or(data.get("error_type"), ""),
            mastery=_bounded_float_or(data.get("mastery"), 0.0, 0.0, 1.0),
            calibration_gap=_optional_bounded_float(data.get("calibration_gap"), 0.0, 1.0),
            hint_level_needed=(
                raw_hint_level if isinstance(raw_hint_level, int) and raw_hint_level >= 0 else None
            ),
            solved_after_hint=_bool_or(data.get("solved_after_hint"), False),
            common_errors=_string_list(data.get("common_errors")),
            successful_interventions=_string_list(data.get("successful_interventions")),
            failed_interventions=_string_list(data.get("failed_interventions")),
            next_best_action=_str_or(data.get("next_best_action"), ""),
            exam_importance=_bounded_float_or(data.get("exam_importance"), 0.0, 0.0, 1.0),
            last_review=_parse_datetime(data.get("last_review")),
            next_review=_parse_datetime(data.get("next_review")),
        )


def _optional_recall_item_payload(state: RecallItemState) -> RecallItemPayload:
    return {
        **_optional_recall_metrics_payload(state),
        **_optional_recall_dates_payload(state),
    }


def _optional_recall_metrics_payload(state: RecallItemState) -> RecallItemPayload:
    payload: RecallItemPayload = {}
    if state.last_recall_seconds is not None:
        payload["last_recall_seconds"] = state.last_recall_seconds
    if state.last_confidence is not None:
        payload["last_confidence"] = state.last_confidence
    if state.calibration_gap is not None:
        payload["calibration_gap"] = state.calibration_gap
    if state.hint_level_needed is not None:
        payload["hint_level_needed"] = state.hint_level_needed
    return payload


def _optional_recall_dates_payload(state: RecallItemState) -> RecallItemPayload:
    payload: RecallItemPayload = {}
    if state.last_review is not None:
        payload["last_review"] = state.last_review.isoformat()
    if state.next_review is not None:
        payload["next_review"] = state.next_review.isoformat()
    return payload


@dataclass(slots=True)
class PolicyMoveStats:
    uses: int = 0
    successes: int = 0
    total_mastery_delta: float = 0.0
    total_confidence_delta: float = 0.0
    total_time_seconds: int = 0
    frustration_count: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.uses if self.uses > 0 else 0.0

    @property
    def avg_mastery_delta(self) -> float:
        return self.total_mastery_delta / self.uses if self.uses > 0 else 0.0

    def to_dict(self) -> PolicyMoveStatsPayload:
        return {
            "uses": self.uses,
            "successes": self.successes,
            "total_mastery_delta": round(self.total_mastery_delta, 4),
            "total_confidence_delta": round(self.total_confidence_delta, 4),
            "total_time_seconds": self.total_time_seconds,
            "frustration_count": self.frustration_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PolicyMoveStats:
        return cls(
            uses=_int_or(data.get("uses"), 0),
            successes=_int_or(data.get("successes"), 0),
            total_mastery_delta=_float_or(data.get("total_mastery_delta"), 0.0),
            total_confidence_delta=_float_or(data.get("total_confidence_delta"), 0.0),
            total_time_seconds=_int_or(data.get("total_time_seconds"), 0),
            frustration_count=_int_or(data.get("frustration_count"), 0),
        )


class RecallScheduleStore:
    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path
        self.items: dict[str, RecallItemState] = {}
        self.policy_stats: dict[str, PolicyMoveStats] = {}
        self._dirty = False

    @property
    def _path(self) -> Path:
        return self.armory_path / ".hephaion" / _RECALL_SCHEDULE_FILE

    @property
    def _legacy_path(self) -> Path:
        return self.armory_path / ".hephaion" / _LEGACY_RECALL_SCHEDULE_FILE

    @property
    def _read_path(self) -> Path:
        return self._path if self._path.is_file() else self._legacy_path

    @property
    def item_list(self) -> list[RecallItemState]:
        return list(self.items.values())

    def due_items(self, *, now: datetime | None = None, limit: int = 0) -> list[RecallItemState]:
        current_time = now or datetime.now(UTC)
        due = sorted(
            _due_recall_items(self.items.values(), current_time),
            key=lambda item: _due_item_sort_key(item, current_time),
        )
        return due[:limit] if limit > 0 else due

    def load(self) -> bool:
        path = self._read_path
        if not path.is_file():
            return False
        with contextlib.suppress(json.JSONDecodeError, OSError):
            payload = _schedule_payload(json.loads(path.read_text(encoding="utf-8")))
            if payload is None:
                return False
            self.items = payload.items
            self.policy_stats = payload.policy_stats
            return True
        return False

    def save(self) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "updated_at": datetime.now(UTC).isoformat(),
            "items": {key: item.to_dict() for key, item in sorted(self.items.items())},
            "policy_stats": {
                key: stats.to_dict() for key, stats in sorted(self.policy_stats.items())
            },
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
        rating: RecallRating,
        elapsed_seconds: int | None,
        confidence: float | None = None,
        hint_level_needed: int | None = None,
        retrieval_success: bool | None = None,
        transfer_success: bool | None = None,
        error_type: str = "",
        intervention: str = "",
        exam_importance: float = 0.0,
        now: datetime | None = None,
    ) -> RecallItemState:
        current_time = now or datetime.now(UTC)
        state = self._review_state(
            item=item,
            concept=concept,
            retrieval_query=retrieval_query,
            source_refs=source_refs,
            error_type=error_type,
            exam_importance=exam_importance,
        )
        _record_recall_result(
            state,
            rating=rating,
            elapsed_seconds=elapsed_seconds,
            confidence=confidence,
            source_refs=source_refs,
            retrieval_success=retrieval_success,
        )
        state.last_transfer_success = _transfer_success(
            item,
            correct=state.last_correct,
            explicit=transfer_success,
        )
        state.hint_level_needed = hint_level_needed
        state.solved_after_hint = state.last_correct and hint_level_needed is not None
        _record_error_and_intervention(
            state,
            error_type=error_type,
            intervention=intervention,
        )
        state.mastery = next_recall_mastery(state.mastery, rating, hint_level_needed)
        state.calibration_gap = (
            round(abs(confidence - state.mastery), 4) if confidence is not None else None
        )
        state.next_best_action = _next_best_action(
            rating,
            mastery=state.mastery,
            confidence=confidence,
            hint_level_needed=hint_level_needed,
        )
        state.last_review = current_time
        state.difficulty, state.stability = _next_difficulty_and_stability(
            state,
            rating=rating,
            elapsed_seconds=elapsed_seconds,
        )
        state.next_review = current_time + _review_interval(rating, state.stability)
        self.items[state.key] = state
        self._dirty = True
        return state

    def _review_state(
        self,
        *,
        item: str,
        concept: str,
        retrieval_query: str,
        source_refs: list[str],
        error_type: str,
        exam_importance: float,
    ) -> RecallItemState:
        bounded_exam_importance = _clamp(exam_importance, 0.0, 1.0)
        state = RecallItemState(
            item=item,
            concept=concept,
            retrieval_query=retrieval_query,
            source_refs=source_refs,
            error_type=error_type,
            exam_importance=bounded_exam_importance,
        )
        existing = self.items.get(state.key)
        if existing is None:
            return state
        existing.item = item
        existing.concept = concept or existing.concept
        existing.retrieval_query = retrieval_query
        existing.source_refs = list(source_refs)
        existing.error_type = error_type or existing.error_type
        existing.exam_importance = max(existing.exam_importance, bounded_exam_importance)
        return existing

    def record_policy_outcome(
        self,
        move_type: str,
        *,
        success: bool,
        mastery_delta: float,
        confidence_delta: float,
        time_cost_seconds: int,
        frustration_signal: bool = False,
    ) -> PolicyMoveStats:
        move_type = move_type or "unknown"
        stats = self.policy_stats.setdefault(move_type, PolicyMoveStats())
        stats.uses += 1
        if success:
            stats.successes += 1
        stats.total_mastery_delta += mastery_delta
        stats.total_confidence_delta += confidence_delta
        stats.total_time_seconds += max(0, time_cost_seconds)
        if frustration_signal:
            stats.frustration_count += 1
        self._dirty = True
        return stats


def load_recall_schedule(armory_path: Path) -> RecallScheduleStore:
    store = RecallScheduleStore(armory_path)
    store.load()
    return store


def save_recall_schedule(store: RecallScheduleStore) -> Path:
    return store.save() if store._dirty else store._path


def _due_recall_items(
    items: Iterable[RecallItemState],
    current_time: datetime,
) -> list[RecallItemState]:
    return [
        item for item in items if item.next_review is not None and item.next_review <= current_time
    ]


def _due_item_sort_key(
    item: RecallItemState,
    current_time: datetime,
) -> tuple[datetime, float, int, float]:
    return (
        item.next_review or current_time,
        -item.exam_importance,
        -item.failures,
        -item.difficulty,
    )


def _schedule_payload(raw: object) -> _SchedulePayload | None:
    if not is_string_mapping(raw):
        return None
    return _SchedulePayload(
        items=_schedule_items(raw.get("items", {})),
        policy_stats=_policy_stats(raw.get("policy_stats", {})),
    )


def _schedule_items(raw_items: object) -> dict[str, RecallItemState]:
    if not is_string_mapping(raw_items):
        return {}
    return {
        key: RecallItemState.from_dict(value)
        for key, value in raw_items.items()
        if is_string_mapping(value)
    }


def _policy_stats(raw_policy_stats: object) -> dict[str, PolicyMoveStats]:
    if not is_string_mapping(raw_policy_stats):
        return {}
    return {
        key: PolicyMoveStats.from_dict(value)
        for key, value in raw_policy_stats.items()
        if is_string_mapping(value)
    }


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
    if isinstance(value, bool) or not isinstance(value, int | float):
        return default
    return float(value)


def _bounded_float_or(value: object, default: float, minimum: float, maximum: float) -> float:
    parsed = _float_or(value, default)
    return _clamp(parsed, minimum, maximum)


def _optional_bounded_float(value: object, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return _clamp(float(value), minimum, maximum)


def _string_list(value: object) -> list[str]:
    if not is_object_list(value):
        return []
    return [item for item in value if isinstance(item, str)]


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _str_or(value: object, default: str) -> str:
    return value if isinstance(value, str) else default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _transfer_success(
    item: str,
    *,
    correct: bool,
    explicit: bool | None,
) -> bool:
    if explicit is not None:
        return explicit
    return correct and bool(_TRANSFER_PROMPT_RE.search(item))


def _record_error_and_intervention(
    state: RecallItemState,
    *,
    error_type: str,
    intervention: str,
) -> None:
    _ensure_review_lists(state)
    if _recordable_error(error_type, correct=state.last_correct):
        assert state.common_errors is not None
        _append_unique(state.common_errors, error_type)
    if not intervention:
        return
    _append_unique(_intervention_bucket(state), intervention)


def _record_recall_result(
    state: RecallItemState,
    *,
    rating: RecallRating,
    elapsed_seconds: int | None,
    confidence: float | None,
    source_refs: list[str],
    retrieval_success: bool | None,
) -> None:
    state.reviews += 1
    state.last_rating = rating
    state.last_correct = rating in {RecallRating.EASY, RecallRating.GOOD}
    if not state.last_correct:
        state.failures += 1
    state.last_recall_seconds = elapsed_seconds
    state.last_confidence = confidence
    state.last_retrieval_success = (
        bool(source_refs) if retrieval_success is None else retrieval_success
    )


def _ensure_review_lists(state: RecallItemState) -> None:
    state.common_errors = state.common_errors or []
    state.successful_interventions = state.successful_interventions or []
    state.failed_interventions = state.failed_interventions or []


def _recordable_error(error_type: str, *, correct: bool) -> bool:
    return bool(error_type) and error_type not in {"", "none", "correct"} and not correct


def _intervention_bucket(state: RecallItemState) -> list[str]:
    if state.last_correct:
        assert state.successful_interventions is not None
        return state.successful_interventions
    assert state.failed_interventions is not None
    return state.failed_interventions


def _next_best_action(
    rating: RecallRating,
    *,
    mastery: float,
    confidence: float | None,
    hint_level_needed: int | None,
) -> str:
    for rule, action in _NEXT_ACTION_RULES:
        if rule(rating, mastery, confidence, hint_level_needed):
            return action
    return "ask_recall"


def _has_high_confidence_gap(
    _rating: RecallRating,
    mastery: float,
    confidence: float | None,
    _hint_level_needed: int | None,
) -> bool:
    return confidence is not None and confidence >= 0.75 and mastery < 0.55


def _needs_hint(
    rating: RecallRating,
    _mastery: float,
    _confidence: float | None,
    hint: int | None,
) -> bool:
    return rating is RecallRating.HARD and hint is None


def _needs_prerequisite_repair(
    rating: RecallRating,
    _mastery: float,
    _confidence: float | None,
    _hint_level_needed: int | None,
) -> bool:
    return rating is RecallRating.HARD


def _needs_recall(
    rating: RecallRating,
    mastery: float,
    _confidence: float | None,
    _hint: int | None,
) -> bool:
    return rating is RecallRating.GOOD and mastery < 0.75


def _ready_for_harder_question(
    rating: RecallRating,
    _mastery: float,
    confidence: float | None,
    _hint_level_needed: int | None,
) -> bool:
    return rating is RecallRating.EASY and confidence is not None and confidence >= 0.75


def _ready_for_interleaving(
    rating: RecallRating,
    _mastery: float,
    _confidence: float | None,
    _hint_level_needed: int | None,
) -> bool:
    return rating is RecallRating.EASY


_NEXT_ACTION_RULES: tuple[_NextActionRule, ...] = (
    (_has_high_confidence_gap, "contrastive_question"),
    (_needs_hint, "give_hint"),
    (_needs_prerequisite_repair, "prerequisite_repair"),
    (_needs_recall, "ask_recall"),
    (_ready_for_harder_question, "move_to_harder_question"),
    (_ready_for_interleaving, "interleave_related_topic"),
)


def _next_difficulty_and_stability(
    state: RecallItemState,
    *,
    rating: RecallRating,
    elapsed_seconds: int | None,
) -> tuple[float, float]:
    difficulty_delta = {
        RecallRating.EASY: -0.45,
        RecallRating.GOOD: -0.15,
        RecallRating.HARD: 0.65,
        RecallRating.NONE: 0.0,
    }[rating]
    speed_factor = 1.0
    if elapsed_seconds is not None and elapsed_seconds <= _FAST_RECALL_SECONDS:
        difficulty_delta -= 0.1
        speed_factor = 1.15
    elif elapsed_seconds is not None and elapsed_seconds >= _SLOW_RECALL_SECONDS:
        difficulty_delta += 0.25
        speed_factor = 0.75
    stability_multiplier = {
        RecallRating.EASY: 2.6,
        RecallRating.GOOD: 1.8,
        RecallRating.HARD: 0.6,
        RecallRating.NONE: 1.0,
    }[rating]
    difficulty = _clamp(round(state.difficulty + difficulty_delta, 3), 1.0, 10.0)
    stability = _clamp(
        round(state.stability * stability_multiplier * speed_factor, 3),
        0.25,
        float(_MAX_INTERVAL_DAYS),
    )
    return difficulty, stability


def _review_interval(rating: RecallRating, stability: float) -> timedelta:
    if rating is RecallRating.HARD:
        return timedelta(days=1)
    if rating is RecallRating.NONE:
        return timedelta(0)
    retention = _clamp(_DESIRED_RETENTION, 0.7, 0.99)
    days = stability * log(retention) / log(0.9)
    return timedelta(days=min(_MAX_INTERVAL_DAYS, max(1, round(days))))
