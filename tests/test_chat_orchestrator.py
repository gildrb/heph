"""Tests for hephaistos.chat.orchestrator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from hephaistos.chat.engine import (
    ChatConfig,
    CompletionDelta,
    Conversation,
    EngineError,
    StreamRecoveryError,
)
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
    adaptive_rag_budget,
    build_turn_evidence_from_query,
    build_turn_evidence_from_refs,
    ensure_rag_index,
    evidence_refs,
    parse_source_ref,
    resolve_turn_evidence,
)
from hephaistos.chat.orchestrator import TurnOrchestrator
from hephaistos.chat.session import ChatSession
from hephaistos.rag import ScoredChunk, TurnEvidence
from hephaistos.rag.chunker import Chunk
from hephaistos.rag.context import EvidenceChunk
from hephaistos.study import StudyAction, StudyPhase, StudyTurnPlan
from hephaistos.study.state import StudyState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(source: str = "source.py", index: int = 0) -> Chunk:
    return Chunk(
        text="sample content",
        source=source,
        index=index,
        char_start=0,
        char_end=15,
    )


def _make_evidence_chunk(
    source: str = "source.py",
    index: int = 0,
    evidence_id: str = "E1",
) -> EvidenceChunk:
    return EvidenceChunk(
        evidence_id=evidence_id,
        chunk=_make_chunk(source, index),
        score=0.9,
        content="evidence content",
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


# ---------------------------------------------------------------------------
# TestTurnOrchestratorPlain
# ---------------------------------------------------------------------------


class TestTurnOrchestratorPlain:
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
        events = list(orch.iter_events("hi"))
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
        list(orch.iter_events("hi"))
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
        events = list(orch.iter_events("hi"))
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
        mock_resolve_evidence.return_value = None

        delta1 = AssistantDeltaEvent("chunk1")
        delta2 = AssistantDeltaEvent("chunk2")
        mock_iter_agent.return_value = iter([delta1, delta2])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("test input"))

        # Two delta events from iter_agent_events
        assert any(e.delta == "chunk1" for e in events if isinstance(e, AssistantDeltaEvent))
        assert any(e.delta == "chunk2" for e in events if isinstance(e, AssistantDeltaEvent))

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
        assert len(notices) == 1
        assert "No evidence citations" in notices[0].message


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
        mock_load.return_value = mock_index
        session = _make_study_session()
        # First call loads
        ensure_rag_index(session)
        # Second call should use cache
        ensure_rag_index(session)
        mock_load.assert_called_once()

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

    @patch("hephaistos.chat.evidence.ensure_rag_index")
    def testbuild_turn_evidence_from_refs_error(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        mock_ensure.side_effect = RuntimeError("fail")
        session = _make_study_session()
        result = build_turn_evidence_from_refs(session, ["source.py#chunk=0"])
        assert result is None

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
