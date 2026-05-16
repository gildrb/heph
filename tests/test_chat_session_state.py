"""Tests for persisted study-session state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import SessionError, create_session, resume_session, save_session
from hephaistos.rag.health import ExtractionHealthIssue
from hephaistos.study import (
    ExamSession,
    ExamSessionItem,
    Milestone,
    MilestoneTracker,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
)


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
    session.study_state.autonomy_mode = StudyAutonomyMode.AUTOPILOT
    session.study_state.session_goal = "exam preparation"
    session.study_state.time_budget_minutes = 45
    session.study_state.autopilot_session_type = "exam"

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
    assert resumed.study_state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    assert resumed.study_state.session_goal == "exam preparation"
    assert resumed.study_state.time_budget_minutes == 45
    assert resumed.study_state.autopilot_session_type == "exam"


def test_save_and_resume_preserves_exam_session_and_milestones(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    session.study_state.exam_session = ExamSession(
        items=[
            ExamSessionItem(
                question="Explain Dijkstra.",
                source_ref="materials/exam.md#chunk=0",
                marks=10,
                status="partial",
                answer="shortest paths",
                feedback="needs edge relaxation",
            )
        ],
        active_index=0,
        started_at=datetime(2026, 5, 9, 12, 30, tzinfo=UTC),
        completed_count=1,
    )
    session.study_state.milestone_tracker = MilestoneTracker(
        milestones=[Milestone(name="Dijkstra", status="in_progress", progress=0.5)]
    )

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.study_state.exam_session is not None
    assert resumed.study_state.exam_session.active_index == 0
    assert resumed.study_state.exam_session.started_at == datetime(2026, 5, 9, 12, 30, tzinfo=UTC)
    assert resumed.study_state.exam_session.completed_count == 1
    assert resumed.study_state.exam_session.items[0].answer == "shortest paths"
    assert resumed.study_state.exam_session.items[0].feedback == "needs edge relaxation"
    assert resumed.study_state.exam_session.items[0].marks == 10
    assert resumed.study_state.milestone_tracker is not None
    assert resumed.study_state.milestone_tracker.milestones[0].name == "Dijkstra"
    assert resumed.study_state.milestone_tracker.milestones[0].progress == 0.5


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


def test_create_session_includes_extraction_health_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)

    def fake_scan(_armory_path: Path) -> tuple[ExtractionHealthIssue, ...]:
        return (
            ExtractionHealthIssue(
                source="materials/exam.md",
                forbidden_text_present=("formula-not-decoded",),
            ),
        )

    monkeypatch.setattr("hephaistos.chat.session._scan_extraction_health_issues", fake_scan)

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    system_prompt = session.conversation.messages[0].content
    assert "WARNING: The following indexed files contain extraction health issues" in system_prompt
    assert "materials/exam.md" in system_prompt
    assert "formula-not-decoded" in system_prompt
    assert "Do NOT answer from affected files" in system_prompt


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


def test_create_session_does_not_auto_execute_armory_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAISTOS_TRUST_ARMORY_PLUGINS", raising=False)
    armory = _make_armory(tmp_path)
    marker = armory / "plugin_executed"
    plugin = armory / ".hephaistos" / "tools" / "probe.py"
    plugin.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def register(registry):\n"
        "    pass\n",
        encoding="utf-8",
    )

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    assert not marker.exists()
    assert session.tool_registry.get_handler("probe") is None


def test_create_session_loads_armory_plugins_after_explicit_trust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAISTOS_TRUST_ARMORY_PLUGINS", "1")
    armory = _make_armory(tmp_path)
    marker = armory / "plugin_executed"
    plugin = armory / ".hephaistos" / "tools" / "probe.py"
    plugin.write_text(
        "from pathlib import Path\n"
        "from hephaistos.agent.tools import ToolSpec\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def register(registry):\n"
        "    registry.register(ToolSpec(\n"
        "        schema={\n"
        "            'type': 'function',\n"
        "            'function': {\n"
        "                'name': 'probe',\n"
        "                'description': 'Probe tool',\n"
        "                'parameters': {\n"
        "                    'type': 'object',\n"
        "                    'properties': {},\n"
        "                    'required': [],\n"
        "                },\n"
        "            },\n"
        "        },\n"
        "        handler=lambda **kw: 'ok',\n"
        "    ))\n",
        encoding="utf-8",
    )

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    assert marker.read_text(encoding="utf-8") == "executed"
    handler = session.tool_registry.get_handler("probe")
    assert handler is not None
    assert handler() == "ok"
