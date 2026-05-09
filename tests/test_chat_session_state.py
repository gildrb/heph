"""Tests for persisted study-session state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import SessionError, create_session, resume_session, save_session
from hephaistos.study import StudyFeedbackType, StudyPhase, StudyRecallRating


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "materials").mkdir(exist_ok=True)
    (armory / "materials" / "exam.md").write_text("# Exam\n\nQ1\n\nAnswer: 4\n")
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
    session.study_state.expected_source_refs = ["materials/exam.md#chunk=0"]
    session.study_state.attempt_count = 3
    session.study_state.last_feedback_type = StudyFeedbackType.PARTIAL
    session.study_state.recall_started_at = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    session.study_state.last_recall_seconds = 75
    session.study_state.last_recall_rating = StudyRecallRating.HARD

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.study_state.phase is StudyPhase.RECALL
    assert resumed.study_state.current_item == "Q1"
    assert resumed.study_state.retrieval_query == "Q1"
    assert resumed.study_state.expected_source_refs == ["materials/exam.md#chunk=0"]
    assert resumed.study_state.attempt_count == 3
    assert resumed.study_state.last_feedback_type is StudyFeedbackType.PARTIAL
    assert resumed.study_state.recall_started_at == datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    assert resumed.study_state.last_recall_seconds == 75
    assert resumed.study_state.last_recall_rating is StudyRecallRating.HARD


def test_resume_preserves_only_existing_disabled_sources(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    stale_source = armory / "materials" / "stale.md"
    stale_source.write_text("# Stale\n\nDeleted later.\n")
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    session.disabled_source_files.update({"materials/exam.md", "materials/stale.md"})
    save_session(session)
    stale_source.unlink()

    resumed = resume_session(session.config, armory, session.session_id)

    assert resumed.disabled_source_files == {"materials/exam.md"}


def test_resume_refreshes_stale_system_prompt(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    save_session(session)

    session_file = armory / ".hephaistos" / "chats" / f"{session.session_id}.json"
    saved = session_file.read_text(encoding="utf-8")
    session_file.write_text(
        saved.replace(session.conversation.messages[0].content, "stale system prompt"),
        encoding="utf-8",
    )

    resumed = resume_session(session.config, armory, session.session_id)

    assert resumed.conversation.messages[0].role == "system"
    assert resumed.conversation.messages[0].content != "stale system prompt"
    assert "materials/exam.md" in resumed.conversation.messages[0].content


def test_session_source_scan_respects_armory_ignore(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / ".hephaistosignore").write_text(
        "materials/ignored.md\nmaterials/private/\n",
        encoding="utf-8",
    )
    (armory / "materials" / "visible.md").write_text("# Visible\n\nUseful material.\n")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n\nDo not expose.\n")
    private = armory / "materials" / "private"
    private.mkdir()
    (private / "notes.md").write_text("# Private\n\nDo not expose.\n")

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    assert session.source_file_count == 1
    assert session.source_files == ("materials/visible.md",)
    system_prompt = session.conversation.messages[0].content
    assert "materials/visible.md" in system_prompt
    assert "materials/ignored.md" not in system_prompt
    assert "materials/private/notes.md" not in system_prompt


def test_ignored_sources_do_not_make_armory_startable(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / ".hephaistosignore").write_text("materials/ignored.md\n", encoding="utf-8")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n\nOnly ignored material.\n")

    with pytest.raises(SessionError) as exc_info:
        create_session(
            ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
            armory,
        )

    message = str(exc_info.value)
    assert "has no study materials" in message
    assert f"Add files to: {armory / 'materials'}" in message
    assert f"heph {armory.name}" in message
