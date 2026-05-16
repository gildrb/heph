"""Study sidebar navigation state helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from hephaistos.study.exam_session import activate_exam_session_item
from hephaistos.study.state import (
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
)


def study_sidebar_count(state: StudyState) -> int:
    exam_session = state.exam_session
    if exam_session is not None:
        return len(exam_session.items)
    milestone_tracker = state.milestone_tracker
    if milestone_tracker is not None:
        return len(milestone_tracker.milestones)
    return 0


def next_study_sidebar_selection(
    state: StudyState,
    selected_index: int | None,
    delta: int,
) -> int | None:
    count = study_sidebar_count(state)
    if count <= 0:
        return None
    current = selected_index
    if current is None:
        exam_session = state.exam_session
        current = exam_session.active_index if exam_session is not None else 0
        if current is None:
            current = 0
    return min(count - 1, max(0, current + delta))


def milestone_sidebar_topic(state: StudyState, index: int) -> str | None:
    milestone_tracker = state.milestone_tracker
    if milestone_tracker is None or not 0 <= index < len(milestone_tracker.milestones):
        return None
    return milestone_tracker.milestones[index].name


def activate_exam_sidebar_item(state: StudyState, index: int) -> bool:
    exam_session = state.exam_session
    if exam_session is None or not 0 <= index < len(exam_session.items):
        return False
    state.exam_session = activate_exam_session_item(exam_session, index)
    active_item = state.exam_session.active_item
    if active_item is None:
        return False
    state.phase = StudyPhase.RECALL
    state.current_item = active_item.question
    state.expected_source_refs = [active_item.source_ref]
    state.attempt_count = 0
    state.last_feedback_type = StudyFeedbackType.CALIBRATING
    state.retrieval_query = active_item.question
    state.recall_started_at = datetime.now(UTC)
    state.last_recall_seconds = None
    state.last_recall_rating = StudyRecallRating.NONE
    state.hint_level = 0
    return True
