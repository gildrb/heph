"""Tests for persisted learning-session state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from hephaion.armory.storage import initialize
from hephaion.chat.session import SessionError, create_session, resume_session, save_session
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_TRANSFORM_PRIOR,
    TurnContract,
)
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.rag.health import ExtractionHealthIssue
from hephaion.runtime import ChatConfig
from hephaion.study import (
    LearningFeedbackType,
    LearningPhase,
    RecallRating,
)


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "materials").mkdir(exist_ok=True)
    (armory / "materials" / "exam.md").write_text("# Exam\n\nQ1\n\nAnswer: 4\n")
    return armory


def test_save_and_resume_preserves_learning_state(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    session.learning_state.phase = LearningPhase.RECALL
    session.learning_state.current_item = "Q1"
    session.learning_state.retrieval_query = "Q1"
    session.learning_state.expected_source_refs = ["materials/exam.md#chunk=0"]
    session.learning_state.attempt_count = 3
    session.learning_state.last_feedback_type = LearningFeedbackType.PARTIAL
    session.learning_state.recall_started_at = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    session.learning_state.last_recall_seconds = 75
    session.learning_state.last_recall_rating = RecallRating.HARD
    session.learning_state.session_goal = "exam preparation"
    session.learning_state.time_budget_minutes = 45
    session.learning_state.practice_session_type = "exam"

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.learning_state.phase is LearningPhase.RECALL
    assert resumed.learning_state.current_item == "Q1"
    assert resumed.learning_state.retrieval_query == "Q1"
    assert resumed.learning_state.expected_source_refs == ["materials/exam.md#chunk=0"]
    assert resumed.learning_state.attempt_count == 3
    assert resumed.learning_state.last_feedback_type is LearningFeedbackType.PARTIAL
    assert resumed.learning_state.recall_started_at == datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    assert resumed.learning_state.last_recall_seconds == 75
    assert resumed.learning_state.last_recall_rating is RecallRating.HARD
    assert resumed.learning_state.session_goal == "exam preparation"
    assert resumed.learning_state.time_budget_minutes == 45
    assert resumed.learning_state.practice_session_type == "exam"


def test_save_and_resume_preserves_last_turn_contract(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    session.last_plan_intent = "source_qa"
    session.last_turn_contract = TurnContract(
        original_user_input="What else?",
        resolved_intent="source_qa",
        canonical_request="Explain another consequence from the prior cited answer.",
        is_followup=True,
        followup_target="previous answer",
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        answer_format=ANSWER_FORMAT_TABLE,
        retrieval_strategy="reuse_prior_evidence",
        retrieval_query="",
        evidence_refs=("materials/exam.md#chunk=0",),
        citation_required=True,
        validation_result="ok",
        confidence=0.92,
    )

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.last_plan_intent == "source_qa"
    assert resumed.last_turn_contract == session.last_turn_contract


def test_save_and_resume_preserves_last_turn_evidence(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    session.last_turn_evidence = TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text="Q1 asks for the value four.",
                    source="materials/exam.md",
                    index=0,
                    char_start=0,
                    char_end=27,
                    heading="Exam",
                    heading_level=1,
                ),
                score=0.87,
                content="Q1 asks for the value four.",
            ),
        ),
        sampled_source_count=1,
        total_source_count=1,
    )

    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert resumed.last_turn_evidence == session.last_turn_evidence
    assert resumed.last_turn_evidence is not None
    assert "[E1] materials/exam.md" in resumed.last_turn_evidence.render()


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

    session_file = armory / ".hephaion" / "chats" / f"{session.session_id}.json"
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

    monkeypatch.setattr("hephaion.chat.session._scan_extraction_health_issues", fake_scan)

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
    (armory / ".hephaionignore").write_text(
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
    (armory / ".hephaionignore").write_text("materials/ignored.md\n", encoding="utf-8")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n\nOnly ignored material.\n")

    with pytest.raises(SessionError) as exc_info:
        create_session(
            ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
            armory,
        )

    message = str(exc_info.value)
    assert "has no materials" in message
    assert f"Add files to: {armory / 'materials'}" in message
    assert f"heph {armory.name}" in message


def test_create_session_does_not_auto_execute_armory_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAION_TRUST_ARMORY_PLUGINS", raising=False)
    armory = _make_armory(tmp_path)
    marker = armory / "plugin_executed"
    plugin = armory / ".hephaion" / "tools" / "probe.py"
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
    monkeypatch.setenv("HEPHAION_TRUST_ARMORY_PLUGINS", "1")
    armory = _make_armory(tmp_path)
    marker = armory / "plugin_executed"
    plugin = armory / ".hephaion" / "tools" / "probe.py"
    plugin.write_text(
        "from pathlib import Path\n"
        "from hephaion.agent.tools import ToolSpec\n"
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
