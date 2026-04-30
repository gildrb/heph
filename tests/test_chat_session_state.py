"""Tests for persisted study-session state."""

from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import SessionError, create_session, resume_session, save_session
from hephaistos.study import StudyFeedbackType, StudyPhase


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "source").mkdir(exist_ok=True)
    (armory / "source" / "exam.md").write_text("# Exam\n\nQ1\n\nAnswer: 4\n")
    return armory


def test_save_and_resume_preserves_study_state(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
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


def test_session_source_scan_respects_armory_ignore(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / ".hephaistosignore").write_text(
        "source/ignored.md\nlibrary/private/\n",
        encoding="utf-8",
    )
    (armory / "source" / "visible.md").write_text("# Visible\n\nUseful material.\n")
    (armory / "source" / "ignored.md").write_text("# Ignored\n\nDo not expose.\n")
    private = armory / "library" / "private"
    private.mkdir()
    (private / "notes.md").write_text("# Private\n\nDo not expose.\n")

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    assert session.source_file_count == 1
    assert session.source_files == ("source/visible.md",)
    system_prompt = session.conversation.messages[0].content
    assert "source/visible.md" in system_prompt
    assert "source/ignored.md" not in system_prompt
    assert "library/private/notes.md" not in system_prompt


def test_ignored_sources_do_not_make_armory_startable(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / ".hephaistosignore").write_text("source/ignored.md\n", encoding="utf-8")
    (armory / "source" / "ignored.md").write_text("# Ignored\n\nOnly ignored material.\n")

    with pytest.raises(SessionError, match="no study materials"):
        create_session(
            ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
            armory,
        )
