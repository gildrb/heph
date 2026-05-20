from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from hephaistos._types import is_object_list, is_string_mapping


class StudyPhase(StrEnum):
    PRESENTING = "presenting"
    WAITING_FOR_READY = "waiting_for_ready"
    RECALL = "recall"
    ASSESS = "assess"


class StudyAutonomyMode(StrEnum):
    MANUAL = "manual"
    GUIDED = "guided"
    AUTOPILOT = "autopilot"


class StudyAction(StrEnum):
    CHAT = "chat"
    CALIBRATE = "calibrate"
    PRIORITY = "priority"
    SOURCE_QA = "source_qa"
    PRESENT = "present"
    WAIT_READY_REMINDER = "wait_ready_reminder"
    PROMPT_RECALL = "prompt_recall"
    ASSESS = "assess"
    REFUSE_REVEAL = "refuse_reveal"
    HINT = "hint"
    SIMPLIFY = "simplify"
    REVIEW = "review"


class StudyFeedbackType(StrEnum):
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


class StudyRecallRating(StrEnum):
    NONE = "none"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(slots=True)
class StudyState:
    phase: StudyPhase = StudyPhase.PRESENTING
    current_item: str = ""
    expected_source_refs: list[str] = field(default_factory=list)
    attempt_count: int = 0
    last_feedback_type: StudyFeedbackType = StudyFeedbackType.NONE
    retrieval_query: str = ""
    recall_started_at: datetime | None = None
    last_recall_seconds: int | None = None
    last_recall_rating: StudyRecallRating = StudyRecallRating.NONE
    last_confidence: float | None = None
    hint_level: int = 0
    autonomy_mode: StudyAutonomyMode = StudyAutonomyMode.GUIDED
    session_goal: str = ""
    time_budget_minutes: int | None = None
    autopilot_session_type: str = ""
    autopilot_started_at: datetime | None = None
    autopilot_turns: int = 0
    autopilot_stop_reason: str = ""

    def clone(self) -> StudyState:
        return StudyState.from_dict(self.to_dict())

    def clear_autopilot_session(self) -> None:
        self.session_goal = ""
        self.time_budget_minutes = None
        self.autopilot_session_type = ""
        self.autopilot_started_at = None
        self.autopilot_turns = 0
        self.autopilot_stop_reason = ""

    def start_autopilot_session(
        self,
        *,
        session_type: str,
        session_goal: str,
        time_budget_minutes: int | None,
    ) -> None:
        self.autonomy_mode = StudyAutonomyMode.AUTOPILOT
        self.session_goal = session_goal
        self.time_budget_minutes = time_budget_minutes
        self.autopilot_session_type = session_type
        self.autopilot_started_at = datetime.now(UTC)
        self.autopilot_turns = 0
        self.autopilot_stop_reason = ""

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
            "autonomy_mode": self.autonomy_mode.value,
            "session_goal": self.session_goal,
            "time_budget_minutes": self.time_budget_minutes,
            "autopilot_session_type": self.autopilot_session_type,
            "autopilot_started_at": (
                self.autopilot_started_at.isoformat()
                if self.autopilot_started_at is not None
                else ""
            ),
            "autopilot_turns": self.autopilot_turns,
            "autopilot_stop_reason": self.autopilot_stop_reason,
        }

    @classmethod
    def from_dict(cls, data: object | None) -> StudyState:
        if not is_string_mapping(data):
            return cls()

        raw_refs = data.get("expected_source_refs")
        expected_source_refs = (
            [ref for ref in raw_refs if isinstance(ref, str)] if is_object_list(raw_refs) else []
        )

        raw_confidence = data.get("last_confidence")
        last_confidence = (
            float(raw_confidence)
            if isinstance(raw_confidence, int | float)
            and not isinstance(raw_confidence, bool)
            and 0 <= raw_confidence <= 1
            else None
        )

        return cls(
            phase=_parse_enum(StudyPhase, data.get("phase"), StudyPhase.PRESENTING),
            current_item=_parse_string(data.get("current_item")),
            expected_source_refs=expected_source_refs,
            attempt_count=_parse_nonnegative_int(data.get("attempt_count")) or 0,
            last_feedback_type=_parse_enum(
                StudyFeedbackType,
                data.get("last_feedback_type"),
                StudyFeedbackType.NONE,
            ),
            retrieval_query=_parse_string(data.get("retrieval_query")),
            recall_started_at=_parse_datetime(data.get("recall_started_at")),
            last_recall_seconds=_parse_nonnegative_int(data.get("last_recall_seconds")),
            last_recall_rating=_parse_enum(
                StudyRecallRating,
                data.get("last_recall_rating"),
                StudyRecallRating.NONE,
            ),
            last_confidence=last_confidence,
            hint_level=min(5, _parse_nonnegative_int(data.get("hint_level")) or 0),
            autonomy_mode=_parse_enum(
                StudyAutonomyMode,
                data.get("autonomy_mode"),
                StudyAutonomyMode.GUIDED,
            ),
            session_goal=_parse_string(data.get("session_goal")),
            time_budget_minutes=_parse_nonnegative_int(data.get("time_budget_minutes")) or None,
            autopilot_session_type=_parse_string(data.get("autopilot_session_type")),
            autopilot_started_at=_parse_datetime(data.get("autopilot_started_at")),
            autopilot_turns=_parse_nonnegative_int(data.get("autopilot_turns")) or 0,
            autopilot_stop_reason=_parse_string(data.get("autopilot_stop_reason")),
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


def _parse_nonnegative_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
