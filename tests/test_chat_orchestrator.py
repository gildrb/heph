"""Tests for hephaistos.chat.orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from hephaistos.chat.engine import (
    ChatConfig,
    CompletionDelta,
    Conversation,
    EngineError,
    StreamRecoveryError,
)
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
)
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
    adaptive_rag_budget,
    build_overview_context,
    build_priority_context,
    build_priority_turn_evidence,
    build_turn_evidence_from_overview,
    build_turn_evidence_from_query,
    build_turn_evidence_from_refs,
    ensure_rag_index,
    evidence_refs,
    is_overview_query,
    parse_source_ref,
    resolve_turn_evidence,
)
from hephaistos.chat.orchestrator import (
    TurnOrchestrator,
    _evidence_notice,
    _evidence_notice_metadata,
    _needs_overview_fallback,
    _overview_answer_has_bad_shape,
    _overview_fallback_reply,
    _overview_topic_is_useful,
    _overview_topic_looks_like_metadata,
)
from hephaistos.chat.session import ChatSession
from hephaistos.rag import ArmoryIndex, ScoredChunk, TurnEvidence
from hephaistos.rag.chunker import Chunk, ChunkedDocument
from hephaistos.rag.context import EvidenceChunk
from hephaistos.study import StudyAction, StudyPhase, StudyTurnPlan
from hephaistos.study.schedule import load_study_schedule
from hephaistos.study.state import StudyState
from scripts import benchmark_answers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(source: str = "source.py", index: int = 0, text: str = "sample content") -> Chunk:
    return Chunk(
        text=text,
        source=source,
        index=index,
        char_start=0,
        char_end=len(text),
    )


def _make_evidence_chunk(
    source: str = "source.py",
    index: int = 0,
    evidence_id: str = "E1",
    content: str = "evidence content",
) -> EvidenceChunk:
    chunk = _make_chunk(source, index, content)
    return EvidenceChunk(
        evidence_id=evidence_id,
        chunk=chunk,
        score=0.9,
        content=content,
    )


def _make_turn_evidence(
    *items: EvidenceChunk,
) -> TurnEvidence:
    return TurnEvidence(items=tuple(items))


def _make_plain_session() -> ChatSession:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="test-session",
    )
    # Replace trace with mock to avoid file I/O
    object.__setattr__(session, "trace", MagicMock())
    return session


def _make_study_session() -> ChatSession:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="test-study-session",
        armory_path=Path("/tmp/fake-armory"),
    )
    object.__setattr__(session, "trace", MagicMock())
    return session


def _make_study_plan(
    *,
    action: StudyAction = StudyAction.PRESENT,
    retrieval_query: str | None = None,
    use_expected_source_refs: bool = False,
    allow_tools: bool = True,
    buffer_response: bool = False,
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=action,
        phase=StudyPhase.PRESENTING,
        prompt="test prompt",
        retrieval_query=retrieval_query,
        use_expected_source_refs=use_expected_source_refs,
        allow_tools=allow_tools,
        buffer_response=buffer_response,
    )


def test_build_turn_evidence_from_query_excludes_disabled_materials() -> None:
    enabled = ScoredChunk(chunk=_make_chunk("materials/enabled.md"), score=0.9)
    disabled = ScoredChunk(chunk=_make_chunk("materials/disabled.md"), score=0.8)
    expected = _make_turn_evidence(_make_evidence_chunk("materials/enabled.md"))
    session = _make_study_session()
    session.disabled_source_files.add("materials/disabled.md")

    with (
        patch("hephaistos.chat.evidence.ensure_rag_index", return_value=MagicMock()),
        patch("hephaistos.chat.evidence.retrieve", return_value=[enabled, disabled]),
        patch("hephaistos.chat.evidence.build_turn_evidence", return_value=expected) as mock_build,
    ):
        result = build_turn_evidence_from_query(session, "test query")

    assert result is expected
    assert mock_build.call_args.args[0] == [enabled]


def test_evidence_notice_summarizes_visible_evidence_refs() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/a.md", 0, "E1"),
        _make_evidence_chunk("materials/b.md", 2, "E2"),
    )

    notice = _evidence_notice(ResolvedTurnPlan(turn_evidence=evidence))

    assert notice == (
        "Using 2 retrieved evidence excerpts: materials/a.md#chunk=0, materials/b.md#chunk=2"
    )


def test_evidence_notice_metadata_exposes_reviewable_evidence() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/a.md", 0, "E1", "First reviewed excerpt."),
        _make_evidence_chunk("materials/b.md", 2, "E2", "Second reviewed excerpt."),
    )

    metadata = _evidence_notice_metadata(ResolvedTurnPlan(turn_evidence=evidence))

    assert metadata["refs"] == ["materials/a.md#chunk=0", "materials/b.md#chunk=2"]
    assert metadata["coverage"] == {
        "evidence_blocks": 2,
        "sampled_sources": 2,
        "total_sources": 2,
    }
    assert metadata["items"] == [
        {
            "evidence_id": "E1",
            "ref": "materials/a.md#chunk=0",
            "score": 0.9,
            "text_excerpt": "First reviewed excerpt.",
        },
        {
            "evidence_id": "E2",
            "ref": "materials/b.md#chunk=2",
            "score": 0.9,
            "text_excerpt": "Second reviewed excerpt.",
        },
    ]


def test_evidence_notice_summarizes_overview_sources() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/lecture-a.pdf", 0, "E1"),
        _make_evidence_chunk("materials/lecture-a.pdf", 1, "E2"),
        _make_evidence_chunk("materials/past-exam.pdf", 0, "E3"),
    )
    evidence = TurnEvidence(
        items=evidence.items,
        sampled_source_count=2,
        total_source_count=9,
    )
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )

    notice = _evidence_notice(ResolvedTurnPlan(study_plan=plan, turn_evidence=evidence))

    assert notice == (
        "Using 3 overview evidence excerpts from 2 of 9 indexed sources: "
        "@lecture-a.pdf, @past-exam.pdf"
    )


def test_evidence_notice_hides_calibration_evidence() -> None:
    evidence = _make_turn_evidence(_make_evidence_chunk("materials/a.md", 0, "E1"))
    plan = _make_study_plan(action=StudyAction.CALIBRATE)

    assert _evidence_notice(ResolvedTurnPlan(study_plan=plan, turn_evidence=evidence)) == ""


def test_overview_fallback_reply_summarizes_materials_with_citations() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture.pdf",
            0,
            "E1",
            "Vorlesung. Table of contents. Folien for graph algorithms and recurrence.",
        ),
        _make_evidence_chunk(
            "materials/exam.pdf",
            0,
            "E2",
            "Klausur. Aufgabe 1. Question 2. Punkte.",
        ),
    )
    evidence = TurnEvidence(
        items=evidence.items,
        sampled_source_count=2,
        total_source_count=9,
    )

    reply = _overview_fallback_reply(plan, evidence)

    assert "Sampled orientation: 2 of 9 indexed sources" in reply
    assert "Retrieved overview sample" not in reply
    assert "not an exhaustive summary" not in reply
    assert "\n- Document signal:" in reply
    assert "\n- Sampled mix:" in reply
    assert "\n- Example evidence:" in reply
    assert "\n- Visible topics:" in reply
    assert "\n- Best next use:" in reply
    assert "@lecture.pdf: lecture or slide material [E1]" in reply
    assert "lecture or slide material [E1]" in reply
    assert "[E2]" in reply
    assert "@lecture.pdf: Vorlesung. Table of contents." in reply
    assert "@lecture.pdf: Vorlesung. Table of contents." in reply
    assert "[E1]" in reply


def test_overview_fallback_uses_document_headings_as_generic_topics() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture-1.pdf",
            0,
            "E1",
            "## Enzyme Kinetics\nDefinition. Michaelis-Menten models reaction rates.",
        ),
        _make_evidence_chunk(
            "materials/lecture-2.pdf",
            0,
            "E2",
            "## Protein Folding\nThe lecture discusses native states and denaturation.",
        ),
    )

    reply = _overview_fallback_reply(plan, evidence)

    assert "Enzyme Kinetics [E1]" in reply
    assert "Protein Folding [E2]" in reply


def test_overview_fallback_satisfies_answer_shape_contract() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture.pdf",
            0,
            "E1",
            "Lecture overview. Table of contents. Graph algorithms and recurrence.",
        ),
        _make_evidence_chunk(
            "materials/exam.pdf",
            0,
            "E2",
            "Final exam. Question 2. Points: 10.",
        ),
    )
    reply = _overview_fallback_reply(plan, evidence)
    case = benchmark_answers.AnswerCase(
        case_id="overview-fallback",
        answer=reply,
        evidence=evidence,
        expected_citations=("E1", "E2"),
        must_include=("Sampled orientation", "Best next use"),
        must_not_include=("the files cover", "no evidence citations"),
        min_words=24,
        max_words=190,
        min_citation_count=2,
        min_distinct_sources=2,
        min_bullet_count=2,
        min_cited_bullet_count=2,
    )

    result = benchmark_answers.evaluate_case(case)

    assert result.passed
    assert result.shape_failures == ()


def test_overview_fallback_needed_for_vague_or_range_cited_answer() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture.pdf",
            0,
            "E1",
            "Lecture overview. Table of contents.",
        ),
        _make_evidence_chunk(
            "materials/exam.pdf",
            0,
            "E2",
            "Final exam. Question 1. Points: 10.",
        ),
    )

    assert _needs_overview_fallback(
        plan,
        "The files cover mathematics topics. Cited evidence: [E1]-[E2]",
        evidence,
    )
    assert not _needs_overview_fallback(
        plan,
        (
            "Sampled orientation two indexed sources for study [E1][E2].\n"
            "- Document signals: the material includes a lecture overview [E1].\n"
            "- Assessment signals: the material includes a final exam question [E2].\n"
            "- Best next use: ask about a topic or problem and I will use the index [E1]."
        ),
        evidence,
    )


def test_overview_shape_rejects_uncited_or_too_thin_summaries() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/lecture.pdf", 0, "E1"),
        _make_evidence_chunk("materials/exam.pdf", 0, "E2"),
    )

    assert _overview_answer_has_bad_shape(
        "Sampled orientation math [E1].",
        evidence,
    )
    assert _overview_answer_has_bad_shape(
        "Sampled orientation two sources [E1][E2].\n"
        "- Document signals: lecture material appears in the material.\n"
        "- Assessment signals: exam material appears in the material.\n"
        "- Best next use: ask about a topic.",
        evidence,
    )
    assert not _overview_answer_has_bad_shape(
        "Sampled orientation two indexed sources for study [E1][E2].\n"
        "- Document signals: lecture material appears in the material [E1].\n"
        "- Assessment signals: exam material appears in the material [E2].\n"
        "- Best next use: ask about a topic and I will use the indexed evidence [E1].",
        evidence,
    )


def test_overview_topic_metadata_filter_removes_title_page_person_names() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture.pdf",
            0,
            "E1",
            "## Introduction to Biology\n\nAda Lovelace\n\nUniversity of Example\n\n2026",
        )
    )

    assert _overview_topic_looks_like_metadata("ada lovelace", evidence)
    assert not _overview_topic_looks_like_metadata("biology", evidence)


def test_overview_topic_filter_rejects_generic_lecture_scaffolding() -> None:
    assert not _overview_topic_is_useful("definition")
    assert not _overview_topic_is_useful("heute sprechen")
    assert not _overview_topic_is_useful("letztes mal")
    assert not _overview_topic_is_useful("mal haben")
    assert not _overview_topic_is_useful("table")
    assert _overview_topic_is_useful("geometrische reihe")
    assert _overview_topic_is_useful("matrix multiplication")
    assert _overview_topic_is_useful("ableitungen")


def test_overview_fallback_unescapes_content_and_filters_exam_noise_topics() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is the material about",
    )
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/slides.pdf",
            0,
            "E1",
            "Lecture notes. Geometric series. For | q | &lt; 1 the series converges.",
        ),
        _make_evidence_chunk(
            "materials/assessment.pdf",
            0,
            "E2",
            """
            Summer semester 2023
            - (a) Determine all critical points of f on D.
            - (b) Decide whether they are local minima or local maxima.
            Joshua Example
            """,
        ),
    )

    reply = _overview_fallback_reply(plan, evidence)

    assert "| q | < 1" in reply
    assert "&lt;" not in reply
    assert "past exam or exam-style material" in reply
    assert "critical points" not in reply.casefold()
    assert "joshua example" not in reply.casefold()


# ---------------------------------------------------------------------------
# TestResolvedTurnPlan
# ---------------------------------------------------------------------------


class TestResolvedTurnPlan:
    def test_defaults(self) -> None:
        plan = ResolvedTurnPlan()
        assert plan.study_plan is None
        assert plan.turn_evidence is None

    def test_with_values(self) -> None:
        study_plan = _make_study_plan()
        evidence = _make_turn_evidence(_make_evidence_chunk())
        plan = ResolvedTurnPlan(study_plan=study_plan, turn_evidence=evidence)
        assert plan.study_plan is study_plan
        assert plan.turn_evidence is evidence

    def test_frozen(self) -> None:
        plan = ResolvedTurnPlan()
        with pytest.raises(AttributeError):
            plan.study_plan = _make_study_plan()  # type: ignore[misc]  # ty:ignore[invalid-assignment]


# ---------------------------------------------------------------------------
# TestEvidenceRefs
# ---------------------------------------------------------------------------


class TestEvidenceRefs:
    def test_none_returns_empty(self) -> None:
        assert evidence_refs(None) == []

    def test_empty_turn_evidence(self) -> None:
        assert evidence_refs(TurnEvidence()) == []

    def test_with_items(self) -> None:
        ec1 = _make_evidence_chunk(source="foo.py", index=0, evidence_id="E1")
        ec2 = _make_evidence_chunk(source="bar.py", index=3, evidence_id="E2")
        evidence = _make_turn_evidence(ec1, ec2)
        refs = evidence_refs(evidence)
        assert refs == ["foo.py#chunk=0", "bar.py#chunk=3"]


# ---------------------------------------------------------------------------
# TestParseSourceRef
# ---------------------------------------------------------------------------


class TestParseSourceRef:
    def test_valid_ref(self) -> None:
        result = parse_source_ref("source.py#chunk=3")
        assert result == ("source.py", 3)

    def test_no_chunk(self) -> None:
        assert parse_source_ref("source.py") is None

    def test_invalid_format(self) -> None:
        assert parse_source_ref("garbage") is None

    def test_empty_string(self) -> None:
        assert parse_source_ref("") is None

    @pytest.mark.parametrize(
        "ref",
        ["#chunk=0", "source.py#chunk=", "source.py#chunk=abc", "source.py#chunk=-1"],
    )
    def test_malformed_refs(self, ref: str) -> None:
        assert parse_source_ref(ref) is None


# ---------------------------------------------------------------------------
# TestTurnOrchestratorPlain
# ---------------------------------------------------------------------------


class TestTurnOrchestratorPlain:
    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_greeting_is_direct_without_model(self, mock_stream: MagicMock) -> None:
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("hey"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["Hey."]
        assert session.last_turn_evidence is None
        mock_stream.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_yields_deltas(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter(
            [
                CompletionDelta(content="Hello"),
                CompletionDelta(content=" world"),
            ]
        )
        session = _make_plain_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("tell me what to do next"))
        deltas = [event for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 2
        assert deltas[0].delta == "Hello"
        assert deltas[1].delta == " world"

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_accumulates_last_reply(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter(
            [
                CompletionDelta(content="Hello"),
                CompletionDelta(content=" world"),
            ]
        )
        session = _make_plain_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("tell me what to do next"))
        assert orch.last_reply == "Hello world"

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_adds_user_message(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter([CompletionDelta(content="reply")])
        session = _make_plain_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("user text"))
        roles = [m.role for m in session.conversation.messages]
        assert "user" in roles
        user_msg = session.conversation.messages[0]
        assert user_msg.content == "user text"

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_empty_deltas_skipped(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter(
            [
                CompletionDelta(content=""),
                CompletionDelta(content="real"),
                CompletionDelta(content=None),
            ]
        )
        session = _make_plain_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("tell me what to do next"))
        # Only "real" should produce an event; empty string and None are skipped
        deltas = [event for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert deltas[0].delta == "real"

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_no_notice_when_no_evidence(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter([CompletionDelta(content="reply")])
        session = _make_plain_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("hi"))
        assert not any(isinstance(e, NoticeEvent) for e in events)


# ---------------------------------------------------------------------------
# TestTurnOrchestratorStudy
# ---------------------------------------------------------------------------


class TestTurnOrchestratorStudy:
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_resolves_plan(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan()
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("response")])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("test input"))

        mock_plan_turn.assert_called_once()
        mock_resolve_evidence.assert_called_once_with(session, plan)

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_yields_events(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan()
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk("materials/notes.md", 0, "E1")
        )

        delta1 = AssistantDeltaEvent("chunk1")
        delta2 = AssistantDeltaEvent("chunk2")
        mock_iter_agent.return_value = iter([delta1, delta2])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("test input"))

        # Two delta events from iter_agent_events
        assert any(e.delta == "chunk1" for e in events if isinstance(e, AssistantDeltaEvent))
        assert any(e.delta == "chunk2" for e in events if isinstance(e, AssistantDeltaEvent))
        notices = [event for event in events if isinstance(event, NoticeEvent)]
        assert any("Using 1 retrieved evidence excerpt" in event.message for event in notices)
        assert any(event.code == "writing" for event in notices)
        trace = cast("MagicMock", session.trace)
        reply_trace = trace.record_session_event.call_args
        assert reply_trace.args == ("reply",)
        assert reply_trace.kwargs["reply_excerpt"].startswith("chunk1chunk2 Evidence checked:")
        assert reply_trace.kwargs["evidence_refs"] == ["materials/notes.md#chunk=0"]
        assert reply_trace.kwargs["evidence_coverage"] == {
            "evidence_blocks": 1,
            "sampled_sources": 1,
            "total_sources": 1,
        }
        assert reply_trace.kwargs["evidence_items"] == [
            {
                "evidence_id": "E1",
                "ref": "materials/notes.md#chunk=0",
                "score": 0.9,
                "text_excerpt": "evidence content",
            }
        ]

    @patch("hephaistos.chat.orchestrator.apply_turn_result")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_applies_turn_result(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_apply: MagicMock,
    ) -> None:
        plan = _make_study_plan()
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("agent reply")])

        new_state = StudyState(phase=StudyPhase.ASSESS)
        mock_apply.return_value = (new_state, "final reply")

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("test input"))

        mock_apply.assert_called_once()
        call_args = mock_apply.call_args
        assert call_args[0][1] is plan  # plan argument
        assert call_args[0][2] == "agent reply"  # raw reply

    @patch("hephaistos.chat.orchestrator.verify_response")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_verification_notice(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        plan = _make_study_plan()
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("agent reply")])

        # Return a non-empty notice string to trigger NoticeEvent
        mock_verify.return_value = "\u26a0 No evidence citations found"

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("test input"))

        notices = [e for e in events if isinstance(e, NoticeEvent)]
        assert any(event.code == "writing" for event in notices)
        assert any("No evidence citations" in event.message for event in notices)

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_turn_shows_reading_evidence_and_writing_notices(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(retrieval_query="integration by parts")
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk("materials/calculus.md", 0, "E1")
        )
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Use product rule [E1].")])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Explain integration by parts"))

        notices = [event for event in events if isinstance(event, NoticeEvent)]
        assert [event.code for event in notices[:3]] == ["reading", "evidence", "writing"]
        assert notices[0].message == "Preparing the material index and reading relevant evidence."
        assert notices[2].message == "Writing a grounded response."

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_turn_emits_material_operations_before_answer(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        tmp_path: Path,
    ) -> None:
        plan = _make_study_plan(retrieval_query="integration by parts")
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/calculus.md",
                2,
                "E1",
                "Integration by parts transfers a derivative between factors.",
            )
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Use product rule [E1].")])

        session = _make_study_session()
        index = ArmoryIndex(tmp_path)
        index.documents = [
            ChunkedDocument(
                source="materials/calculus.md",
                chunks=[_make_chunk("materials/calculus.md", 2)],
            )
        ]
        session.rag_index = index
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("Explain integration by parts"))

        operation_events = [event for event in events if isinstance(event, MaterialOperationEvent)]
        assert [event.operation for event in operation_events] == [
            "index_ready",
            "search_index",
            "read_excerpt",
        ]
        assert operation_events[0].metadata == {
            "indexed_sources": 1,
            "indexed_chunks": 1,
        }
        assert operation_events[2].metadata["ref"] == "materials/calculus.md#chunk=2"
        first_answer_index = next(
            position
            for position, event in enumerate(events)
            if isinstance(event, AssistantDeltaEvent)
        )
        assert all(events.index(event) < first_answer_index for event in operation_events)
        trace = cast("MagicMock", session.trace)
        assert trace.record_material_operation.call_count == 3
        assert trace.record_material_operation.call_args_list[1].kwargs["operation"] == (
            "search_index"
        )

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_waiting_followup_opens_stored_evidence_before_answer(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.md",
                0,
                "E1",
                "Markov chains explain sampling from complex state spaces.",
            )
        )
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("It is interesting because Markov chains support sampling [E1].")]
        )

        session = _make_study_session()
        session.study_state = StudyState(
            phase=StudyPhase.WAITING_FOR_READY,
            current_item="what is the material about",
            retrieval_query="what is the material about",
            expected_source_refs=["materials/lecture.md#chunk=0"],
        )
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("interesting"))

        operation_events = [event for event in events if isinstance(event, MaterialOperationEvent)]
        assert [event.operation for event in operation_events] == [
            "open_stored_evidence",
            "read_excerpt",
        ]
        assert operation_events[0].metadata["refs"] == ["materials/lecture.md#chunk=0"]
        assert mock_iter_agent.call_args.kwargs["tool_schemas"] == []
        first_answer_index = next(
            position
            for position, event in enumerate(events)
            if isinstance(event, AssistantDeltaEvent)
        )
        assert all(events.index(event) < first_answer_index for event in operation_events)
        assert session.study_state.phase is StudyPhase.WAITING_FOR_READY
        assert session.study_state.current_item == "what is the material about"

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_read_all_request_discloses_sample_scope(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(retrieval_query="read through all the files", buffer_response=True)
        evidence = TurnEvidence(
            items=(
                _make_evidence_chunk("materials/lecture-a.md", 0, "E1"),
                _make_evidence_chunk("materials/lecture-b.md", 0, "E2"),
            ),
            sampled_source_count=2,
            total_source_count=5,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Here is a synthesis [E1][E2].")])

        session = _make_study_session()
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("Can you read through all the files?"))

        operations = [event for event in events if isinstance(event, MaterialOperationEvent)]
        assert operations[-1].operation == "read_all_scope"
        assert operations[-1].metadata["command"] == "heph index <armory>"
        reply = "".join(event.delta for event in events if isinstance(event, AssistantDeltaEvent))
        assert "I did not read every file end to end" in reply
        assert "heph index <armory>" in reply
        assert session.conversation.messages[-1].content == reply

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_turn_shows_corpus_overview_notices(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = TurnEvidence(
            items=(
                _make_evidence_chunk("materials/lecture.pdf", 0, "E1"),
                _make_evidence_chunk("materials/exam.pdf", 0, "E2"),
            ),
            sampled_source_count=2,
            total_source_count=9,
        )
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "Retrieved overview sample: lecture and exam signals [E1][E2].\n"
                    "- Scope: not an exhaustive summary [E1]."
                )
            ]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what is the material about"))

        notices = [event for event in events if isinstance(event, NoticeEvent)]
        assert [event.code for event in notices[:3]] == ["reading", "evidence", "writing"]
        assert notices[0].message == (
            "Preparing the material index and reading enabled evidence for a corpus overview."
        )
        assert notices[1].message == (
            "Using 2 overview evidence excerpts from 2 of 9 indexed sources: "
            "@lecture.pdf, @exam.pdf"
        )
        assert notices[1].metadata["coverage"] == {
            "evidence_blocks": 2,
            "sampled_sources": 2,
            "total_sources": 9,
        }
        assert notices[1].metadata["refs"] == [
            "materials/lecture.pdf#chunk=0",
            "materials/exam.pdf#chunk=0",
        ]
        assert notices[2].message == "Writing a grounded corpus overview."
        trace = cast("MagicMock", session.trace)
        reply_trace = trace.record_session_event.call_args
        assert reply_trace.kwargs["evidence_coverage"] == {
            "evidence_blocks": 2,
            "sampled_sources": 2,
            "total_sources": 9,
        }

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._build_priority_context")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_priority_turn_injects_deterministic_priority_context(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_priority_context: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.PRIORITY)
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk("materials/graphs.md", 0, "E1")
        )
        mock_priority_context.return_value = "Deterministic local priority scan over all chunks."
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Prioritize graphs [E1].")])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("What should I prioritize?"))

        kwargs = mock_iter_agent.call_args.kwargs
        assert kwargs["extra_system_prompt"] == (
            "test prompt\n\nDeterministic local priority scan over all chunks."
        )

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._build_overview_context")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_turn_calls_model_before_considering_fallback(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_overview_context: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk("materials/overview.md", 0, "E1"),
            _make_evidence_chunk("materials/problems.md", 0, "E2"),
        )
        mock_overview_context.return_value = "Deterministic local corpus overview."
        model_reply = (
            "Sampled orientation from the retrieved evidence.\n"
            "- Lecture evidence introduces graph concepts, definitions, and worked "
            "examples [E1].\n"
            "- Practice material asks students to solve related problems from the same "
            "topic [E2].\n"
            "- The useful next step is a targeted graph question grounded in these "
            "excerpts [E1] [E2]."
        )
        mock_iter_agent.return_value = iter([AssistantDeltaEvent(model_reply)])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        list(orch.iter_events("what is the material about"))

        mock_iter_agent.assert_called_once()
        mock_overview_context.assert_called_once()
        assert orch.last_reply == model_reply
        assert mock_iter_agent.call_args.kwargs["extra_system_prompt"].endswith(
            "Deterministic local corpus overview."
        )

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_turn_replaces_uncited_model_reply_with_local_fallback(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.pdf",
                0,
                "E1",
                "Vorlesung. Table of contents. Folien for graph algorithms.",
            )
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("The course is about computer science.")]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert deltas[0] != "The course is about computer science."
        assert orch.last_reply == deltas[0]
        assert "Sampled orientation" in orch.last_reply
        assert "[E1]" in orch.last_reply
        assert session.conversation.messages[-1].content == orch.last_reply
        trace = cast("MagicMock", session.trace)
        reply_trace = trace.record_session_event.call_args
        assert reply_trace.kwargs["study_task"] == "material-overview"
        assert reply_trace.kwargs["retrieval_query"] == "what is the material about"

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_turn_replaces_vague_cited_model_reply_without_false_warning(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.pdf",
                0,
                "E1",
                "Lecture notes. Table of contents. Definitions, theorems, and examples.",
            ),
            _make_evidence_chunk(
                "materials/past-exam.pdf",
                0,
                "E2",
                "Past exam. Question 1. Prove a theorem and solve the exercise.",
            ),
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "The files cover course material with lectures and an exam [E1] [E2]. "
                    "Say ready when you want recall."
                )
            ]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        notices = [event.message for event in events if isinstance(event, NoticeEvent)]
        assert len(deltas) == 1
        assert "The files cover" not in deltas[0]
        assert "Say ready when you want recall" not in deltas[0]
        assert "Sampled orientation" in deltas[0]
        assert "not an exhaustive summary" not in deltas[0]
        assert "[E1]" in deltas[0]
        assert "[E2]" in deltas[0]
        assert not any("No evidence citations" in notice for notice in notices)

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_fallback_replaces_turn_complete_text(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.pdf",
                0,
                "E1",
                "Lecture notes. Table of contents. Definitions, theorems, and examples.",
            ),
            _make_evidence_chunk(
                "materials/past-exam.pdf",
                0,
                "E2",
                "Past exam. Question 1. Prove a theorem and solve the exercise.",
            ),
        )
        raw_reply = "The files cover vague course material [E1] [E2]. Say ready."
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(raw_reply),
                TurnCompleteEvent(
                    full_text=raw_reply,
                    turn_index=3,
                    latency_ms=12.5,
                    finish_reason="stop",
                    tokens_remaining=999,
                ),
            ]
        )

        session = _make_study_session()
        events = list(TurnOrchestrator(session).iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        completions = [event for event in events if isinstance(event, TurnCompleteEvent)]
        assert len(deltas) == 1
        assert len(completions) == 1
        assert "Sampled orientation" in deltas[0]
        assert completions[0].full_text == deltas[0]
        assert "The files cover" not in completions[0].full_text
        assert completions[0].turn_index == 3

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_turn_calls_model_with_material_tools_enabled(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            allow_tools=True,
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.pdf",
                0,
                "E1",
                "Lecture notes. Table of contents. Definitions, examples, and proofs.",
            ),
            _make_evidence_chunk(
                "materials/exam.pdf",
                0,
                "E2",
                "Past exam. Question 1. Explain a method. Points: 10.",
            ),
        )
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "Sampled orientation from the retrieved evidence.\n"
                    "- Lecture material introduces definitions and examples [E1].\n"
                    "- Exam material asks method questions with points [E2].\n"
                    "- Together, the excerpts support targeted review of definitions and "
                    "exam-style methods [E1] [E2]."
                )
            ]
        )

        session = _make_study_session()
        list(TurnOrchestrator(session).iter_events("what is the material about"))

        mock_iter_agent.assert_called_once()
        assert mock_iter_agent.call_args.kwargs["tool_schemas"] is None

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_empty_overview_turn_uses_local_fallback(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/exam.pdf",
                0,
                "E1",
                "Klausur. Aufgabe 1. Question 2. Punkte.",
            )
        )
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "Sampled orientation" in deltas[0]
        assert "past exam or exam-style material [E1]" in deltas[0]

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_buffered_study_turn_yields_fallback_when_model_is_empty(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.ASSESS, buffer_response=True)
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(_make_evidence_chunk())
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("test input"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["I could not generate a grounded assessment. Please try again."]
        assert orch.last_reply == "I could not generate a grounded assessment. Please try again."

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_prompt_yields_fallback_when_model_is_empty(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.CALIBRATE, buffer_response=False)
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Can you ask me a really easy question"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["I could not generate a study prompt. Please try again."]
        assert orch.last_reply == "I could not generate a study prompt. Please try again."

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_qa_uses_evidence_fallback_when_model_is_empty(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query=(
                "Using the source files, what is the QA sentinel phrase? "
                "Answer with the exact phrase."
            ),
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            EvidenceChunk(
                evidence_id="E1",
                chunk=_make_chunk("materials/rag-target.md", 0),
                score=0.9,
                content=(
                    "The QA sentinel fact is: Hephaistos retrieval should mention "
                    "the phrase amber forge when asked about the sentinel."
                ),
            )
        )
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Using the source files, what is the QA sentinel phrase?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ['"amber forge" [E1]']
        assert orch.last_reply == '"amber forge" [E1]'
        assert session.study_state.current_item == ""

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_answer_without_evidence_ids_gets_auditable_footer(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="Using the sources, what does the exam test?",
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk("materials/exam.pdf", 0, "E1", "Question about cancer."),
            _make_evidence_chunk("materials/exam.pdf", 1, "E2", "Question about genetics."),
        )
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("It tests cancer and genetics.")])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Using the sources, what does the exam test?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert "Evidence checked:" in deltas[0]
        assert "[E1]" in deltas[0]
        assert "[E2]" in deltas[0]

    @patch("hephaistos.chat.orchestrator.schedule_memory_extraction")
    def test_feature_flag_can_disable_memory_extraction(
        self,
        mock_schedule_memory: MagicMock,
    ) -> None:
        session = _make_study_session()
        session.config.feature_flags = frozenset({"disable_memory_extraction"})
        orch = TurnOrchestrator(session)
        resolved = ResolvedTurnPlan()

        orch._finalize_successful_turn("hello", resolved, latency_ms=1.0)  # type: ignore[reportPrivateUsage]

        mock_schedule_memory.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_qa_without_evidence_uses_source_specific_fallback(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="Using the source files, what is the sentinel phrase?",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Using the source files, what is the sentinel phrase?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "enabled armory sources do not contain an answer" in deltas[0]
        assert "/materials" in deltas[0]
        assert "study prompt" not in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_only_present_without_evidence_abstains_before_tools(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query=(
                "Using only the indexed sources, what is the amber forge retrieval phrase? "
                "If the sources do not contain it, do not guess."
            ),
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Using only the indexed sources, what is amber forge?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "enabled armory sources do not contain an answer" in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    def test_simple_greeting_is_direct_and_ungrounded(self, mock_iter_agent: MagicMock) -> None:
        session = _make_study_session()
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("hey"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["Hey."]
        assert session.last_turn_evidence is None
        assert session.study_state.current_item == ""
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.verify_response")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_easy_question_does_not_attach_visible_evidence(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        hidden_evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_resolve_evidence.return_value = hidden_evidence
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("What is 2 + 2? [E1]")])
        session = _make_study_session()
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("Can you ask me a really easy question"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["What is 2 + 2?"]
        notices = [event for event in events if isinstance(event, NoticeEvent)]
        assert notices == []
        assert session.last_turn_evidence is None
        mock_resolve_evidence.assert_called_once()
        assert mock_iter_agent.call_args.kwargs["turn_evidence"] is hidden_evidence
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert "genuinely easy" in extra_prompt
        mock_verify.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_easy_question_does_not_require_loaded_index(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("What is 2 + 2?")])
        session = _make_study_session()
        session.rag_index = None
        session.source_files = ("materials/notes.md",)
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("Can you ask me a really easy question"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["What is 2 + 2?"]
        assert "materials index could not be loaded" not in orch.last_reply

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_assessment_records_study_schedule(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = StudyTurnPlan(
            action=StudyAction.ASSESS,
            phase=StudyPhase.ASSESS,
            prompt="assess",
            retrieval_query="Q1",
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(_make_evidence_chunk())
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("CORRECT: Correct.")])

        session = _make_study_session()
        assert session.armory_path is not None
        session.armory_path.mkdir(parents=True, exist_ok=True)
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="Q1",
            retrieval_query="Q1",
        )
        orch = TurnOrchestrator(session)

        list(orch.iter_events("answer"))

        store = load_study_schedule(session.armory_path)
        assert len(store.item_list) == 1
        assert store.item_list[0].item == "Q1"
        assert store.item_list[0].concept == "Q1"
        assert store.item_list[0].error_type == "correct"

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_refuses_outside_knowledge_when_materials_are_unindexed(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.PRESENT, retrieval_query="fundamentalsatz")
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None

        session = _make_study_session()
        session.source_file_count = 1
        session.source_files = ("materials/L7_MfI-1_Fundamentalsatz.pdf",)
        index = ArmoryIndex(Path("/tmp/fake-armory"))
        index.unindexable_files = {
            "materials/L7_MfI-1_Fundamentalsatz.pdf": (
                "binary document; document conversion backend unavailable"
            )
        }
        session.rag_index = index

        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("how does the fundamentalsatz work"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "@L7_MfI-1_Fundamentalsatz.pdf" in deltas[0]
        assert "PDF/document conversion is unavailable" in deltas[0]
        assert "cannot answer from outside knowledge" in deltas[0]
        assert "heph index <armory>" in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_reports_conversion_timeout_without_manual_index_requirement(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.PRESENT, retrieval_query="limits")
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None

        session = _make_study_session()
        session.source_file_count = 1
        session.source_files = ("materials/lecture.pdf",)
        index = ArmoryIndex(Path("/tmp/fake-armory"))
        index.unindexable_files = {
            "materials/lecture.pdf": "document conversion timed out after 2 second(s)"
        }
        session.rag_index = index

        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what are the limits about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "@lecture.pdf" in deltas[0]
        assert "document conversion timed out" in deltas[0]
        assert "cannot answer from outside knowledge" in deltas[0]
        assert "Rebuild the materials index" not in deltas[0]
        mock_iter_agent.assert_not_called()


# ---------------------------------------------------------------------------
# TestTurnOrchestratorErrors
# ---------------------------------------------------------------------------


class TestTurnOrchestratorErrors:
    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_rollback_on_engine_error(self, mock_stream: MagicMock) -> None:
        mock_stream.side_effect = EngineError("test error")
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        with pytest.raises(EngineError):
            list(orch.iter_events("test"))

        # Only the original messages should remain (rollback happened)
        assert all(m.role != "user" for m in session.conversation.messages)

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_rollback_on_stream_recovery_error(self, mock_stream: MagicMock) -> None:
        mock_stream.side_effect = StreamRecoveryError("partial content")
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        with pytest.raises(StreamRecoveryError):
            list(orch.iter_events("test"))

        assert all(m.role != "user" for m in session.conversation.messages)

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_rollback_on_generic_exception(self, mock_stream: MagicMock) -> None:
        mock_stream.side_effect = RuntimeError("unexpected")
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        with pytest.raises(RuntimeError, match="unexpected"):
            list(orch.iter_events("test"))

        assert all(m.role != "user" for m in session.conversation.messages)

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_rollback_preserves_original_messages(self, mock_stream: MagicMock) -> None:
        mock_stream.side_effect = EngineError("fail")
        session = _make_plain_session()
        session.conversation.add("system", "system prompt")
        original = list(session.conversation.messages)
        orch = TurnOrchestrator(session)

        with pytest.raises(EngineError):
            list(orch.iter_events("test"))

        assert session.conversation.messages == original

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_error_re_raised(self, mock_stream: MagicMock) -> None:
        error = EngineError("original error")
        mock_stream.side_effect = error
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        with pytest.raises(EngineError, match="original error"):
            list(orch.iter_events("test"))


# ---------------------------------------------------------------------------
# TestHelperFunctions
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    def testensure_rag_index_no_armory(self) -> None:
        session = _make_plain_session()
        assert ensure_rag_index(session) is None

    @patch("hephaistos.chat.evidence.load_or_build")
    def testensure_rag_index_loads(self, mock_load: MagicMock) -> None:
        mock_index = MagicMock()
        mock_load.return_value = mock_index
        session = _make_study_session()
        result = ensure_rag_index(session)
        assert result is mock_index
        mock_load.assert_called_once_with(session.armory_path)

    @patch("hephaistos.chat.evidence.load_or_build")
    def testensure_rag_index_cached(self, mock_load: MagicMock) -> None:
        mock_index = MagicMock()
        mock_index.is_stale.return_value = False
        mock_load.return_value = mock_index
        session = _make_study_session()
        # First call loads
        ensure_rag_index(session)
        # Second call should use cache
        ensure_rag_index(session)
        mock_load.assert_called_once()

    @patch("hephaistos.chat.evidence.load_or_build")
    def testensure_rag_index_reloads_stale_cached_index(self, mock_load: MagicMock) -> None:
        stale_index = MagicMock()
        stale_index.is_stale.return_value = True
        fresh_index = MagicMock()
        fresh_index.is_stale.return_value = False
        mock_load.return_value = fresh_index
        session = _make_study_session()
        session.rag_index = stale_index

        result = ensure_rag_index(session)

        assert result is fresh_index
        mock_load.assert_called_once_with(session.armory_path)

    @patch("hephaistos.chat.evidence.ContextBudget")
    def testadaptive_rag_budget_minimum(self, mock_budget_cls: MagicMock) -> None:
        mock_budget = MagicMock()
        mock_budget.tokens_remaining.return_value = 10
        mock_budget_cls.return_value = mock_budget
        session = _make_plain_session()
        budget = adaptive_rag_budget(session)
        assert budget >= 200

    @patch("hephaistos.chat.evidence.ContextBudget")
    def testadaptive_rag_budget_capped(self, mock_budget_cls: MagicMock) -> None:
        mock_budget = MagicMock()
        # Very large remaining → should be capped by rag_context_budget
        mock_budget.tokens_remaining.return_value = 1_000_000
        mock_budget_cls.return_value = mock_budget
        session = _make_plain_session()
        budget = adaptive_rag_budget(session)
        assert budget <= session.config.rag_context_budget

    @patch("hephaistos.chat.evidence.build_turn_evidence")
    @patch("hephaistos.chat.evidence.retrieve")
    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_query_success(
        self,
        mock_ensure: MagicMock,
        mock_retrieve: MagicMock,
        mock_build: MagicMock,
    ) -> None:
        mock_index = MagicMock()
        mock_ensure.return_value = mock_index
        chunk = _make_chunk()
        scored = [ScoredChunk(chunk=chunk, score=0.9)]
        mock_retrieve.return_value = scored
        expected = _make_turn_evidence(_make_evidence_chunk())
        mock_build.return_value = expected

        session = _make_study_session()
        result = build_turn_evidence_from_query(session, "test query")
        assert result is expected
        mock_retrieve.assert_called_once()

    @patch("hephaistos.chat.evidence.build_turn_evidence")
    @patch("hephaistos.chat.evidence.retrieve")
    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_source_only_query_drops_weak_noise(
        self,
        mock_ensure: MagicMock,
        mock_retrieve: MagicMock,
        mock_build: MagicMock,
    ) -> None:
        mock_index = MagicMock()
        mock_ensure.return_value = mock_index
        chunk = _make_chunk(text="Unrelated low-overlap C pointer declaration material.")
        mock_retrieve.return_value = [ScoredChunk(chunk=chunk, score=0.11)]

        session = _make_study_session()
        result = build_turn_evidence_from_query(
            session,
            "Using only the indexed sources, what is the amber forge retrieval phrase? "
            "If the sources do not contain it, do not guess.",
        )

        assert result is None
        mock_build.assert_not_called()

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_query_no_results(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        mock_index = MagicMock()
        mock_ensure.return_value = mock_index
        # Patch retrieve at module level
        with patch("hephaistos.chat.evidence.retrieve", return_value=[]):
            session = _make_study_session()
            result = build_turn_evidence_from_query(session, "test query")
        assert result is None

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_query_error(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        mock_index = MagicMock()
        mock_ensure.return_value = mock_index
        with patch("hephaistos.chat.evidence.retrieve", side_effect=RuntimeError("fail")):
            session = _make_study_session()
            result = build_turn_evidence_from_query(session, "test query")
        assert result is None

    @patch("hephaistos.chat.evidence.build_turn_evidence")
    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_refs_success(
        self,
        mock_ensure: MagicMock,
        mock_build: MagicMock,
    ) -> None:
        mock_index = MagicMock()
        chunk = _make_chunk("source.py", 3)
        type(mock_index).all_chunks = PropertyMock(return_value=[chunk])
        mock_ensure.return_value = mock_index

        expected = _make_turn_evidence(_make_evidence_chunk("source.py", 3))
        mock_build.return_value = expected

        session = _make_study_session()
        result = build_turn_evidence_from_refs(session, ["source.py#chunk=3"])
        assert result is expected

    @patch("hephaistos.chat.evidence.build_turn_evidence")
    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_refs_filters_disabled_sources(
        self,
        mock_ensure: MagicMock,
        mock_build: MagicMock,
    ) -> None:
        enabled = _make_chunk("materials/enabled.md", 0)
        disabled = _make_chunk("materials/disabled.md", 0)
        mock_index = MagicMock()
        type(mock_index).all_chunks = PropertyMock(return_value=[enabled, disabled])
        mock_ensure.return_value = mock_index
        expected = _make_turn_evidence(_make_evidence_chunk("materials/enabled.md", 0))
        mock_build.return_value = expected
        session = _make_study_session()
        session.disabled_source_files.add("materials/disabled.md")

        result = build_turn_evidence_from_refs(
            session,
            ["materials/enabled.md#chunk=0", "materials/disabled.md#chunk=0"],
        )

        assert result is expected
        assert [sc.chunk for sc in mock_build.call_args.args[0]] == [enabled]

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_refs_error(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        mock_ensure.side_effect = RuntimeError("fail")
        session = _make_study_session()
        result = build_turn_evidence_from_refs(session, ["source.py#chunk=0"])
        assert result is None

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_overview_samples_across_documents_first(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        documents = []
        for letter in ("a", "b", "c", "d", "e", "f", "g"):
            doc = MagicMock()
            doc.source = f"materials/{letter}.md"
            doc.chunks = [
                _make_chunk(f"materials/{letter}.md", 0),
                _make_chunk(f"materials/{letter}.md", 1),
            ]
            documents.append(doc)
        mock_index = MagicMock()
        mock_index.documents = documents
        mock_index.all_chunks = [chunk for document in documents for chunk in document.chunks]
        mock_ensure.return_value = mock_index

        session = _make_study_session()
        result = build_turn_evidence_from_overview(session)

        assert result is not None
        assert result.sampled_source_count == 7
        assert result.total_source_count == 7
        assert evidence_refs(result) == [
            "materials/a.md#chunk=0",
            "materials/b.md#chunk=0",
            "materials/c.md#chunk=0",
            "materials/d.md#chunk=0",
            "materials/e.md#chunk=0",
            "materials/f.md#chunk=0",
            "materials/g.md#chunk=0",
            "materials/a.md#chunk=1",
            "materials/b.md#chunk=1",
            "materials/c.md#chunk=1",
            "materials/d.md#chunk=1",
            "materials/e.md#chunk=1",
        ]

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_overview_compacts_long_chunks_for_source_coverage(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        documents = []
        for index in range(6):
            source = f"materials/source-{index}.md"
            doc = MagicMock()
            doc.source = source
            doc.chunks = [_make_chunk(source, 0, f"Heading {index}. " + ("long text " * 1000))]
            documents.append(doc)
        mock_index = MagicMock()
        mock_index.documents = documents
        mock_index.all_chunks = [document.chunks[0] for document in documents]
        mock_ensure.return_value = mock_index

        session = _make_study_session()
        session.config.rag_context_budget = 600

        result = build_turn_evidence_from_overview(session)

        assert result is not None
        assert result.sampled_source_count >= 2
        assert result.total_source_count == 6
        assert len({item.source for item in result.items}) >= 2
        assert all(len(item.content) <= 700 for item in result.items)

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_overview_covers_nine_long_sources_by_default(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        documents = []
        for index in range(9):
            source = f"materials/lecture-{index}.pdf"
            doc = MagicMock()
            doc.source = source
            doc.chunks = [_make_chunk(source, 0, f"Document {index}. " + ("details " * 900))]
            documents.append(doc)
        mock_index = MagicMock()
        mock_index.documents = documents
        mock_index.all_chunks = [document.chunks[0] for document in documents]
        mock_ensure.return_value = mock_index

        result = build_turn_evidence_from_overview(_make_study_session())

        assert result is not None
        assert result.sampled_source_count == 9
        assert result.total_source_count == 9
        assert len({item.source for item in result.items}) == 9

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_overview_samples_broad_real_corpus(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        documents = []
        for index in range(58):
            source = f"materials/document-{index}.pdf"
            doc = MagicMock()
            doc.source = source
            doc.chunks = [
                _make_chunk(
                    source,
                    0,
                    f"## Topic {index}\nConcise indexed source signal for document {index}.",
                )
            ]
            documents.append(doc)
        mock_index = MagicMock()
        mock_index.documents = documents
        mock_index.all_chunks = [document.chunks[0] for document in documents]
        mock_ensure.return_value = mock_index

        result = build_turn_evidence_from_overview(_make_study_session())

        assert result is not None
        assert result.total_source_count == 58
        assert result.sampled_source_count >= 24
        assert len({item.source for item in result.items}) >= 24

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_overview_filters_disabled_sources(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        doc1 = MagicMock()
        doc1.source = "materials/enabled.md"
        doc1.chunks = [_make_chunk("materials/enabled.md", 0)]
        doc2 = MagicMock()
        doc2.source = "materials/disabled.md"
        doc2.chunks = [_make_chunk("materials/disabled.md", 0)]
        mock_index = MagicMock()
        mock_index.documents = [doc1, doc2]
        mock_index.all_chunks = doc1.chunks + doc2.chunks
        mock_ensure.return_value = mock_index
        session = _make_study_session()
        session.disabled_source_files.add("materials/disabled.md")

        result = build_turn_evidence_from_overview(session)

        assert result is not None
        assert evidence_refs(result) == ["materials/enabled.md#chunk=0"]

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_turn_evidence_from_overview_skips_front_matter_when_content_exists(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        doc = MagicMock()
        doc.source = "materials/lecture.md"
        doc.chunks = [
            _make_chunk(
                "materials/lecture.md",
                0,
                "## Biology 101\n\nAda Lovelace\n\nUniversity of Example\n\n12 April 2026",
            ),
            _make_chunk(
                "materials/lecture.md",
                1,
                "## Cellular respiration\n\nDefinition. ATP production and electron transport.",
            ),
        ]
        mock_index = MagicMock()
        mock_index.documents = [doc]
        mock_index.all_chunks = doc.chunks
        mock_ensure.return_value = mock_index

        result = build_turn_evidence_from_overview(_make_study_session())

        assert result is not None
        assert evidence_refs(result) == ["materials/lecture.md#chunk=1"]

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_priority_turn_evidence_uses_whole_enabled_corpus(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        exam = _make_chunk(
            "materials/exam-2024.md",
            0,
            "Question 1. Explain Dijkstra shortest paths. [10 marks]",
        )
        lecture = _make_chunk(
            "materials/lecture-graphs.md",
            0,
            "Dijkstra shortest paths uses a priority queue for graph distances.",
        )
        disabled = _make_chunk(
            "materials/disabled.md",
            0,
            "Dijkstra appears here but this source is disabled.",
        )
        mock_index = MagicMock()
        mock_index.all_chunks = [exam, lecture, disabled]
        mock_ensure.return_value = mock_index
        session = _make_study_session()
        session.disabled_source_files.add("materials/disabled.md")

        result = build_priority_turn_evidence(session)

        assert result is not None
        refs = evidence_refs(result)
        assert "materials/exam-2024.md#chunk=0" in refs
        assert "materials/lecture-graphs.md#chunk=0" in refs
        assert "materials/disabled.md#chunk=0" not in refs

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_priority_context_uses_deterministic_scan(self, mock_ensure: MagicMock) -> None:
        exam = _make_chunk(
            "materials/exam-2024.md",
            0,
            "Question 1. Explain Dijkstra shortest paths. [10 marks]",
        )
        lecture = _make_chunk(
            "materials/lecture-graphs.md",
            0,
            "Dijkstra shortest paths uses a priority queue for graph distances.",
        )
        mock_index = MagicMock()
        mock_index.all_chunks = [exam, lecture]
        mock_ensure.return_value = mock_index

        context = build_priority_context(_make_study_session())

        assert "Deterministic local priority scan" in context
        assert "Local priority scan from indexed materials" in context
        assert "dijkstra shortest" in context
        assert "Do not infer priorities from filenames" in context

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def test_build_overview_context_uses_content_roles_and_topics(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        exam_doc = MagicMock()
        exam_doc.source = "materials/document-a.pdf"
        exam_doc.chunks = [
            _make_chunk(
                "materials/document-a.pdf",
                0,
                "Klausur. Bearbeitungszeit 90 Minuten. Aufgabe 1: 10 Punkte.",
            )
        ]
        slides_doc = MagicMock()
        slides_doc.source = "materials/document-b.pdf"
        slides_doc.chunks = [
            _make_chunk(
                "materials/document-b.pdf",
                0,
                "Vorlesung overview. Inhaltsverzeichnis. Folien zur Übungsgruppe.",
            )
        ]
        mock_index = MagicMock()
        mock_index.documents = [exam_doc, slides_doc]
        mock_ensure.return_value = mock_index

        context = build_overview_context(_make_study_session())

        assert "Deterministic local corpus overview" in context
        assert "indexed_documents=2" in context
        assert "past_exam=1" in context
        assert "slides=1" in context
        assert "materials/document-a.pdf: past_exam" in context
        assert "materials/document-b.pdf: slides" in context
        assert "Topic scan from enabled indexed text" in context
        assert "do not infer from filenames" in context

    def test_is_overview_query_matches_material_overview(self) -> None:
        assert is_overview_query("what is the material about")
        assert is_overview_query("Can you read through all the files")
        assert not is_overview_query("explain Dijkstra")

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_refs")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def testresolve_turn_evidence_uses_refs(
        self,
        mock_query: MagicMock,
        mock_refs: MagicMock,
    ) -> None:
        plan = _make_study_plan(use_expected_source_refs=True)
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_refs.return_value = evidence

        session = _make_study_session()
        session.study_state.expected_source_refs = ["source.py#chunk=0"]
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_refs.assert_called_once()
        mock_query.assert_not_called()

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_overview")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def test_resolve_turn_evidence_uses_hidden_overview_for_calibration(
        self,
        mock_query: MagicMock,
        mock_overview: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_overview.return_value = evidence
        plan = StudyTurnPlan(
            action=StudyAction.CALIBRATE,
            phase=StudyPhase.RECALL,
            prompt="calibrate",
        )

        session = _make_study_session()
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_overview.assert_called_once_with(session)
        mock_query.assert_not_called()

    @patch("hephaistos.chat.evidence.build_priority_turn_evidence")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_overview")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def test_resolve_turn_evidence_uses_priority_analyzer_for_priority(
        self,
        mock_query: MagicMock,
        mock_overview: MagicMock,
        mock_priority: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_priority.return_value = evidence
        plan = _make_study_plan(action=StudyAction.PRIORITY)

        session = _make_study_session()
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_priority.assert_called_once_with(session)
        mock_overview.assert_not_called()
        mock_query.assert_not_called()

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_overview")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def testresolve_turn_evidence_uses_overview_for_generic_material_summary(
        self,
        mock_query: MagicMock,
        mock_overview: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_overview.return_value = evidence
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
        )

        session = _make_study_session()
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_overview.assert_called_once_with(session)
        mock_query.assert_not_called()

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_overview")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def test_resolve_turn_evidence_uses_overview_for_simple_material_explanation(
        self,
        mock_query: MagicMock,
        mock_overview: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_overview.return_value = evidence
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="explain the material simply",
        )

        session = _make_study_session()
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_overview.assert_called_once_with(session)
        mock_query.assert_not_called()

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_refs")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def testresolve_turn_evidence_falls_back_to_query(
        self,
        mock_query: MagicMock,
        mock_refs: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            use_expected_source_refs=True,
            retrieval_query="search query",
        )
        # refs path returns None
        mock_refs.return_value = None
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_query.return_value = evidence

        session = _make_study_session()
        session.study_state.expected_source_refs = ["source.py#chunk=0"]
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_refs.assert_called_once()
        mock_query.assert_called_once_with(session, "search query")
