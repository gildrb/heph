"""Explicit study-session state for the drill loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.study.exam_session import ExamSession
from hephaistos.study.milestones import MilestoneTracker


class StudyPhase(StrEnum):
    """Stable phases in the study loop."""

    PRESENTING = "presenting"
    WAITING_FOR_READY = "waiting_for_ready"
    RECALL = "recall"
    ASSESS = "assess"


class StudyAutonomyMode(StrEnum):
    """How strongly Hephaistos should steer the study session."""

    MANUAL = "manual"
    GUIDED = "guided"
    AUTOPILOT = "autopilot"


class StudyAction(StrEnum):
    """Controller actions for a single user turn."""

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
    """Coarse feedback emitted by the controller after a turn."""

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
    """Recall effort derived from correctness and response latency."""

    NONE = "none"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(slots=True)
class StudyState:
    """Persistent study-loop state stored with the chat session."""

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
    exam_session: ExamSession | None = None
    milestone_tracker: MilestoneTracker | None = None

    def clone(self) -> StudyState:
        """Return a deep-enough copy for rollback and persistence."""
        return StudyState.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        """Serialize for chat persistence."""
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
            "exam_session": (
                self.exam_session.to_dict() if self.exam_session is not None else None
            ),
            "milestone_tracker": (
                self.milestone_tracker.to_dict() if self.milestone_tracker is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: object | None) -> StudyState:
        """Deserialize persisted state, falling back safely on bad input."""
        if not is_string_mapping(data):
            return cls()

        phase = StudyPhase.PRESENTING
        raw_phase = data.get("phase")
        if isinstance(raw_phase, str):
            try:
                phase = StudyPhase(raw_phase)
            except ValueError:
                phase = StudyPhase.PRESENTING

        feedback = StudyFeedbackType.NONE
        raw_feedback = data.get("last_feedback_type")
        if isinstance(raw_feedback, str):
            try:
                feedback = StudyFeedbackType(raw_feedback)
            except ValueError:
                feedback = StudyFeedbackType.NONE

        raw_refs = data.get("expected_source_refs")
        expected_source_refs = (
            [ref for ref in raw_refs if isinstance(ref, str)] if is_object_list(raw_refs) else []
        )

        raw_attempt = data.get("attempt_count", 0)
        attempt_count = raw_attempt if isinstance(raw_attempt, int) and raw_attempt >= 0 else 0

        raw_item = data.get("current_item", "")
        current_item = raw_item if isinstance(raw_item, str) else ""

        raw_query = data.get("retrieval_query", "")
        retrieval_query = raw_query if isinstance(raw_query, str) else ""

        recall_started_at = _parse_datetime(data.get("recall_started_at"))

        raw_last_recall_seconds = data.get("last_recall_seconds")
        last_recall_seconds = (
            raw_last_recall_seconds
            if isinstance(raw_last_recall_seconds, int) and raw_last_recall_seconds >= 0
            else None
        )

        recall_rating = StudyRecallRating.NONE
        raw_recall_rating = data.get("last_recall_rating")
        if isinstance(raw_recall_rating, str):
            try:
                recall_rating = StudyRecallRating(raw_recall_rating)
            except ValueError:
                recall_rating = StudyRecallRating.NONE

        raw_confidence = data.get("last_confidence")
        last_confidence = (
            float(raw_confidence)
            if isinstance(raw_confidence, int | float)
            and not isinstance(raw_confidence, bool)
            and 0 <= raw_confidence <= 1
            else None
        )

        raw_hint_level = data.get("hint_level", 0)
        hint_level = (
            raw_hint_level
            if isinstance(raw_hint_level, int) and not isinstance(raw_hint_level, bool)
            else 0
        )
        hint_level = min(5, max(0, hint_level))

        autonomy_mode = StudyAutonomyMode.GUIDED
        raw_autonomy_mode = data.get("autonomy_mode")
        if isinstance(raw_autonomy_mode, str):
            try:
                autonomy_mode = StudyAutonomyMode(raw_autonomy_mode)
            except ValueError:
                autonomy_mode = StudyAutonomyMode.GUIDED

        raw_goal = data.get("session_goal", "")
        session_goal = raw_goal if isinstance(raw_goal, str) else ""

        raw_budget = data.get("time_budget_minutes")
        time_budget_minutes = (
            raw_budget if isinstance(raw_budget, int) and raw_budget > 0 else None
        )

        raw_session_type = data.get("autopilot_session_type", "")
        autopilot_session_type = raw_session_type if isinstance(raw_session_type, str) else ""

        autopilot_started_at = _parse_datetime(data.get("autopilot_started_at"))

        raw_autopilot_turns = data.get("autopilot_turns", 0)
        autopilot_turns = (
            raw_autopilot_turns
            if isinstance(raw_autopilot_turns, int) and raw_autopilot_turns >= 0
            else 0
        )

        raw_stop_reason = data.get("autopilot_stop_reason", "")
        autopilot_stop_reason = raw_stop_reason if isinstance(raw_stop_reason, str) else ""

        exam_session = ExamSession.from_dict(data.get("exam_session"))
        milestone_tracker = MilestoneTracker.from_dict(data.get("milestone_tracker"))

        return cls(
            phase=phase,
            current_item=current_item,
            expected_source_refs=expected_source_refs,
            attempt_count=attempt_count,
            last_feedback_type=feedback,
            retrieval_query=retrieval_query,
            recall_started_at=recall_started_at,
            last_recall_seconds=last_recall_seconds,
            last_recall_rating=recall_rating,
            last_confidence=last_confidence,
            hint_level=hint_level,
            autonomy_mode=autonomy_mode,
            session_goal=session_goal,
            time_budget_minutes=time_budget_minutes,
            autopilot_session_type=autopilot_session_type,
            autopilot_started_at=autopilot_started_at,
            autopilot_turns=autopilot_turns,
            autopilot_stop_reason=autopilot_stop_reason,
            exam_session=exam_session,
            milestone_tracker=milestone_tracker,
        )


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
