from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from harness._types import is_object_list, is_string_mapping


class RecallPhase(StrEnum):
    PRESENTING = "presenting"
    WAITING_FOR_READY = "waiting_for_ready"
    RECALL = "recall"
    ASSESS = "assess"


class DocumentAction(StrEnum):
    CHAT = "chat"
    SOURCE_QA = "source_qa"
    PRESENT = "present"


class RecallFeedbackType(StrEnum):
    NONE = "none"
    CALIBRATING = "calibrating"
    NO_SOURCE = "no_source"
    PRESENTED = "presented"
    WAITING = "waiting"
    READY = "ready"
    REFUSED = "refused"
    HINT = "hint"
    EASIER = "easier"
    REVIEWING = "reviewing"
    CORRECT = "correct"
    PARTIAL = "partial"
    WRONG = "wrong"


class RecallRating(StrEnum):
    NONE = "none"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(slots=True)
class RecallState:
    phase: RecallPhase = RecallPhase.PRESENTING
    current_item: str = ""
    expected_source_refs: list[str] = field(default_factory=list)
    attempt_count: int = 0
    last_feedback_type: RecallFeedbackType = RecallFeedbackType.NONE
    retrieval_query: str = ""
    recall_started_at: datetime | None = None
    last_recall_seconds: int | None = None
    last_recall_rating: RecallRating = RecallRating.NONE
    last_confidence: float | None = None
    hint_level: int = 0
    session_goal: str = ""
    time_budget_minutes: int | None = None

    def clone(self) -> RecallState:
        return RecallState.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase.value,
            "current_item": self.current_item,
            "expected_source_refs": list(self.expected_source_refs),
            "attempt_count": self.attempt_count,
            "last_feedback_type": self.last_feedback_type.value,
            "retrieval_query": self.retrieval_query,
            "recall_started_at": (
                self.recall_started_at.isoformat() if self.recall_started_at is not None else ""
            ),
            "last_recall_seconds": self.last_recall_seconds,
            "last_recall_rating": self.last_recall_rating.value,
            "last_confidence": self.last_confidence,
            "hint_level": self.hint_level,
            "session_goal": self.session_goal,
            "time_budget_minutes": self.time_budget_minutes,
        }

    @classmethod
    def from_dict(cls, data: object | None) -> RecallState:
        if not is_string_mapping(data):
            return cls()
        return cls(
            phase=_parse_enum(RecallPhase, data.get("phase"), RecallPhase.PRESENTING),
            current_item=_parse_string(data.get("current_item")),
            expected_source_refs=_parse_string_list(data.get("expected_source_refs")),
            attempt_count=_parse_nonnegative_int(data.get("attempt_count")) or 0,
            last_feedback_type=_parse_enum(
                RecallFeedbackType,
                data.get("last_feedback_type"),
                RecallFeedbackType.NONE,
            ),
            retrieval_query=_parse_string(data.get("retrieval_query")),
            recall_started_at=_parse_datetime(data.get("recall_started_at")),
            last_recall_seconds=_parse_nonnegative_int(data.get("last_recall_seconds")),
            last_recall_rating=_parse_enum(
                RecallRating,
                data.get("last_recall_rating"),
                RecallRating.NONE,
            ),
            last_confidence=_parse_bounded_float(data.get("last_confidence")),
            hint_level=min(5, _parse_nonnegative_int(data.get("hint_level")) or 0),
            session_goal=_parse_string(data.get("session_goal")),
            time_budget_minutes=_parse_nonnegative_int(data.get("time_budget_minutes")) or None,
        )


def _parse_enum[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: object,
    default: EnumT,
) -> EnumT:
    if not isinstance(value, str):
        return default
    try:
        return enum_type(value)
    except ValueError:
        return default


def _parse_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _parse_string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if is_object_list(value) else []


def _parse_nonnegative_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _parse_bounded_float(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool) and 0 <= value <= 1:
        return float(value)
    return None


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
