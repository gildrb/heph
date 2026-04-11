"""Tests for persisted study-session state."""

from __future__ import annotations

from pathlib import Path

from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_session, resume_session, save_session
from hephaistos.study import StudyFeedbackType, StudyPhase


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "source").mkdir(exist_ok=True)
    (armory / "source" / "exam.md").write_text("# Exam\n\nQ1\n\nAnswer: 4\n")
    return armory


def test_save_and_resume_preserves_study_state(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(ChatConfig(), armory)
    session.study_state.phase = StudyPhase.RECALL
    session.study_state.current_item = "Q1"
    session.study_state.retrieval_query = "Q1"
    session.study_state.expected_source_refs = ["source/exam.md#chunk=0"]
    session.study_state.attempt_count = 3
    session.study_state.last_feedback_type = StudyFeedbackType.PARTIAL

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.study_state.phase is StudyPhase.RECALL
    assert resumed.study_state.current_item == "Q1"
    assert resumed.study_state.retrieval_query == "Q1"
    assert resumed.study_state.expected_source_refs == ["source/exam.md#chunk=0"]
    assert resumed.study_state.attempt_count == 3
    assert resumed.study_state.last_feedback_type is StudyFeedbackType.PARTIAL
