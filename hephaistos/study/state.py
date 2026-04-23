"""Explicit study-session state for the drill loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from hephaistos._types import is_object_list, is_string_mapping


class StudyPhase(StrEnum):
    """Stable phases in the study loop."""

    PRESENTING = "presenting"
    WAITING_FOR_READY = "waiting_for_ready"
    RECALL = "recall"
    ASSESS = "assess"


class StudyAction(StrEnum):
    """Controller actions for a single user turn."""

    PRESENT = "present"
    WAIT_READY_REMINDER = "wait_ready_reminder"
    PROMPT_RECALL = "prompt_recall"
    ASSESS = "assess"
    REFUSE_REVEAL = "refuse_reveal"
    HINT = "hint"


class StudyFeedbackType(StrEnum):
    """Coarse feedback emitted by the controller after a turn."""

    NONE = "none"
    NO_SOURCE = "no_source"
    PRESENTED = "presented"
    WAITING = "waiting"
    READY = "ready"
    REFUSED = "refused"
    HINT = "hint"
    CORRECT = "correct"
    PARTIAL = "partial"
    WRONG = "wrong"


@dataclass(slots=True)
class StudyState:
    """Persistent study-loop state stored with the chat session."""

    phase: StudyPhase = StudyPhase.PRESENTING
    current_item: str = ""
    expected_source_refs: list[str] = field(default_factory=list)
    attempt_count: int = 0
    last_feedback_type: StudyFeedbackType = StudyFeedbackType.NONE
    retrieval_query: str = ""

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

        return cls(
            phase=phase,
            current_item=current_item,
            expected_source_refs=expected_source_refs,
            attempt_count=attempt_count,
            last_feedback_type=feedback,
            retrieval_query=retrieval_query,
        )
