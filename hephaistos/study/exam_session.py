"""Persistent exam-session state helpers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from hephaistos._types import is_string_mapping
from hephaistos.study.exam import ExamQuestion

EXAM_SESSION_PENDING = "pending"
EXAM_SESSION_ACTIVE = "active"
EXAM_SESSION_CORRECT = "correct"
EXAM_SESSION_PARTIAL = "partial"
EXAM_SESSION_WRONG = "wrong"
EXAM_SESSION_COMPLETED_STATUSES = frozenset(
    {EXAM_SESSION_CORRECT, EXAM_SESSION_PARTIAL, EXAM_SESSION_WRONG}
)
_EXAM_SESSION_STATUSES = frozenset(
    {
        EXAM_SESSION_PENDING,
        EXAM_SESSION_ACTIVE,
        EXAM_SESSION_CORRECT,
        EXAM_SESSION_PARTIAL,
        EXAM_SESSION_WRONG,
    }
)


@dataclass(slots=True)
class ExamSessionItem:
    """One question in a persistent exam session."""

    question: str
    source_ref: str
    marks: int | None = None
    status: str = EXAM_SESSION_PENDING
    answer: str = ""
    feedback: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "source_ref": self.source_ref,
            "marks": self.marks,
            "status": self.status,
            "answer": self.answer,
            "feedback": self.feedback,
        }

    @classmethod
    def from_dict(cls, data: object) -> ExamSessionItem | None:
        if not is_string_mapping(data):
            return None
        raw_question = data.get("question")
        raw_source_ref = data.get("source_ref")
        if not isinstance(raw_question, str) or not isinstance(raw_source_ref, str):
            return None
        raw_marks = data.get("marks")
        marks = raw_marks if isinstance(raw_marks, int) else None
        raw_status = data.get("status")
        status = raw_status if isinstance(raw_status, str) else EXAM_SESSION_PENDING
        if status not in _EXAM_SESSION_STATUSES:
            status = EXAM_SESSION_PENDING
        raw_answer = data.get("answer")
        raw_feedback = data.get("feedback")
        return cls(
            question=raw_question,
            source_ref=raw_source_ref,
            marks=marks,
            status=status,
            answer=raw_answer if isinstance(raw_answer, str) else "",
            feedback=raw_feedback if isinstance(raw_feedback, str) else "",
        )


@dataclass(slots=True)
class ExamSession:
    """Persistent state for a multi-question exam drill."""

    items: list[ExamSessionItem] = field(default_factory=list)
    active_index: int | None = None
    started_at: datetime | None = None
    completed_count: int = 0

    @property
    def active_item(self) -> ExamSessionItem | None:
        if self.active_index is None:
            return None
        if not 0 <= self.active_index < len(self.items):
            return None
        return self.items[self.active_index]

    @property
    def is_complete(self) -> bool:
        return bool(self.items) and self.completed_count >= len(self.items)

    def to_dict(self) -> dict[str, object]:
        return {
            "items": [item.to_dict() for item in self.items],
            "active_index": self.active_index,
            "started_at": self.started_at.isoformat() if self.started_at is not None else None,
            "completed_count": self.completed_count,
        }

    @classmethod
    def from_dict(cls, data: object) -> ExamSession | None:
        if not is_string_mapping(data):
            return None
        raw_items = data.get("items")
        items: list[ExamSessionItem] = []
        if isinstance(raw_items, list):
            for raw_item in raw_items:
                item = ExamSessionItem.from_dict(raw_item)
                if item is not None:
                    items.append(item)
        raw_active_index = data.get("active_index")
        active_index = raw_active_index if isinstance(raw_active_index, int) else None
        if active_index is not None and not 0 <= active_index < len(items):
            active_index = None
        raw_started_at = data.get("started_at")
        started_at = _datetime_from_iso(raw_started_at)
        raw_completed_count = data.get("completed_count")
        completed_count = (
            raw_completed_count
            if isinstance(raw_completed_count, int)
            else _completed_count(items)
        )
        completed_count = max(0, min(completed_count, len(items)))
        return cls(
            items=items,
            active_index=active_index,
            started_at=started_at,
            completed_count=completed_count,
        )


def exam_session_from_questions(
    questions: list[ExamQuestion], *, now: datetime | None = None
) -> ExamSession:
    """Create an active session from extracted exam questions."""
    items = [
        ExamSessionItem(
            question=question.question,
            source_ref=question.source_ref,
            marks=question.marks,
        )
        for question in questions
    ]
    session = ExamSession(
        items=items,
        active_index=0 if items else None,
        started_at=now or datetime.now(UTC),
        completed_count=0,
    )
    if session.active_item is not None:
        session.active_item.status = EXAM_SESSION_ACTIVE
    return session


def activate_exam_session_item(session: ExamSession, index: int) -> ExamSession:
    """Return a copy with the requested item marked active."""
    if not 0 <= index < len(session.items):
        return session
    items = [replace(item) for item in session.items]
    for item in items:
        if item.status == EXAM_SESSION_ACTIVE:
            item.status = EXAM_SESSION_PENDING
    if items[index].status not in EXAM_SESSION_COMPLETED_STATUSES:
        items[index].status = EXAM_SESSION_ACTIVE
    return ExamSession(
        items=items,
        active_index=index,
        started_at=session.started_at,
        completed_count=_completed_count(items),
    )


def update_active_exam_session_item(
    session: ExamSession,
    *,
    status: str,
    answer: str,
    feedback: str,
) -> ExamSession:
    """Return a copy with the active item assessment result recorded."""
    if session.active_index is None or not 0 <= session.active_index < len(session.items):
        return session
    normalized_status = status if status in _EXAM_SESSION_STATUSES else EXAM_SESSION_PARTIAL
    items = [replace(item) for item in session.items]
    item = items[session.active_index]
    item.status = normalized_status
    item.answer = answer
    item.feedback = feedback
    next_active = session.active_index
    return ExamSession(
        items=items,
        active_index=next_active,
        started_at=session.started_at,
        completed_count=_completed_count(items),
    )


def next_exam_session_index(session: ExamSession) -> int | None:
    """Return the next exam question index, preferring unanswered items."""
    if not session.items:
        return None
    start = session.active_index if session.active_index is not None else -1
    for index in range(start + 1, len(session.items)):
        if session.items[index].status not in EXAM_SESSION_COMPLETED_STATUSES:
            return index
    return None


def _completed_count(items: list[ExamSessionItem]) -> int:
    return sum(1 for item in items if item.status in EXAM_SESSION_COMPLETED_STATUSES)


def _datetime_from_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
