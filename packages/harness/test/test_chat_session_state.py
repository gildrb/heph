"""Tests for persisted learning-session state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from harness.armory.storage import initialize
from harness.chat.session import (
    create_session,
    fork_session_at_turn,
    record_turn_snapshot,
    resume_session,
    save_session,
)
from harness.chat.turn_contract import (
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_TRANSFORM_PRIOR,
    TurnContract,
)
from harness.memory import MemoryStore
from harness.rag import Chunk, EvidenceChunk, TurnEvidence
from harness.rag.health import ExtractionHealthIssue
from harness.study import (
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


def test_save_and_resume_preserves_turn_history_with_evidence(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    evidence = TurnEvidence(
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
    contract = TurnContract(
        original_user_input="What is Q1?",
        resolved_intent="source_qa",
        evidence_refs=("materials/exam.md#chunk=0",),
        citation_required=True,
    )
    session.conversation.add("user", "What is Q1?")
    session.conversation.add("assistant", "Q1 asks for four. [E1]")

    record_turn_snapshot(
        session,
        user_input="What is Q1?",
        assistant_reply="Q1 asks for four. [E1]",
        evidence=evidence,
        plan_intent="source_qa",
        contract=contract,
    )
    save_session(session)

    resumed = resume_session(session.config, armory, session.session_id)
    assert len(resumed.turn_history) == 1
    snapshot = resumed.turn_history[0]
    assert snapshot.turn_id == "T1"
    assert snapshot.user_input == "What is Q1?"
    assert snapshot.assistant_reply == "Q1 asks for four. [E1]"
    assert snapshot.plan_intent == "source_qa"
    assert snapshot.contract == contract
    assert snapshot.evidence is not None
    assert "[E1] materials/exam.md" in snapshot.evidence.render()


def test_fork_session_at_turn_restores_chat_and_last_evidence(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )
    first_evidence = TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text="First fact.",
                    source="materials/exam.md",
                    index=0,
                    char_start=0,
                    char_end=11,
                    heading="Exam",
                    heading_level=1,
                ),
                score=0.9,
                content="First fact.",
            ),
        ),
        sampled_source_count=1,
        total_source_count=1,
    )
    first_contract = TurnContract(
        original_user_input="First?",
        resolved_intent="source_qa",
        evidence_refs=("materials/exam.md#chunk=0",),
    )
    session.conversation.add("user", "First?")
    session.conversation.add("assistant", "First answer. [E1]")
    record_turn_snapshot(
        session,
        user_input="First?",
        assistant_reply="First answer. [E1]",
        evidence=first_evidence,
        plan_intent="source_qa",
        contract=first_contract,
    )
    session.conversation.add("user", "Second?")
    session.conversation.add("assistant", "Second answer.")
    record_turn_snapshot(
        session,
        user_input="Second?",
        assistant_reply="Second answer.",
        evidence=None,
        plan_intent="source_qa",
        contract=None,
    )
    session.dirty = True

    branched = fork_session_at_turn(session, "T1")

    assert branched.session_id != session.session_id
    assert [message.role for message in branched.conversation.messages] == [
        "system",
        "user",
        "assistant",
    ]
    assert branched.conversation.messages[-2].content == "First?"
    assert branched.conversation.messages[-1].content == "First answer. [E1]"
    assert branched.last_turn_evidence == first_evidence
    assert branched.last_turn_contract == first_contract
    assert branched.last_plan_intent == "source_qa"
    assert [snapshot.turn_id for snapshot in branched.turn_history] == ["T1"]
    assert branched.dirty is True
    assert (armory / ".harness" / "chats" / f"{session.session_id}.json").exists()


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

    session_file = armory / ".harness" / "chats" / f"{session.session_id}.json"
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

    monkeypatch.setattr("harness.chat.session._scan_extraction_health_issues", fake_scan)

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
    (armory / ".harnessignore").write_text(
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


def test_ignored_sources_start_empty_armory_without_material_context(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / ".harnessignore").write_text("materials/ignored.md\n", encoding="utf-8")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n\nOnly ignored material.\n")

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    assert session.armory_path == armory
    assert session.source_file_count == 0
    assert session.source_files == ()
    system_prompt = session.conversation.messages[0].content
    assert f"Armory workspace: {armory}" in system_prompt
    assert "materials/ignored.md" not in system_prompt


def test_create_session_does_not_auto_execute_armory_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_TRUST_ARMORY_PLUGINS", raising=False)
    armory = _make_armory(tmp_path)
    marker = armory / "plugin_executed"
    plugin = armory / ".harness" / "tools" / "probe.py"
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
    armory = _make_armory(tmp_path)
    monkeypatch.setenv("HARNESS_TRUST_ARMORY_PLUGINS", str(armory.resolve()))
    marker = armory / "plugin_executed"
    plugin = armory / ".harness" / "tools" / "probe.py"
    plugin.write_text(
        "from pathlib import Path\n"
        "from harness.agent.tools import ToolSpec\n"
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
        "                    'additionalProperties': False,\n"
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


def test_global_truthy_env_does_not_trust_armory_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    monkeypatch.setenv("HARNESS_TRUST_ARMORY_PLUGINS", "1")
    marker = armory / "plugin_executed"
    plugin = armory / ".harness" / "tools" / "probe.py"
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


def test_armory_memory_is_skipped_in_system_context_without_path_trust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_TRUST_ARMORY_MEMORY", raising=False)
    armory = _make_armory(tmp_path)
    memory = MemoryStore(armory)
    memory.add("style", "Use compact answers.", confidence="verified")
    memory.save()

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    system_prompt = session.conversation.messages[0].content
    assert "Armory memory snapshot" not in system_prompt
    assert "Use compact answers." not in system_prompt


def test_armory_memory_enters_system_context_with_path_trust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    monkeypatch.setenv("HARNESS_TRUST_ARMORY_MEMORY", str(armory.resolve()))
    memory = MemoryStore(armory)
    memory.add("style", "Use compact answers.", confidence="verified")
    memory.save()

    session = create_session(
        ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
        armory,
    )

    system_prompt = session.conversation.messages[0].content
    assert "Armory memory snapshot" in system_prompt
    assert "Use compact answers." in system_prompt
