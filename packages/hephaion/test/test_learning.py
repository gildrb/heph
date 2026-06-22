"""Tests for structural answer-attempt guard contracts."""

from __future__ import annotations

from pathlib import Path

from ai.runtime import ChatConfig, Conversation
from hephaion.agent.citation import VerificationResult
from hephaion.chat.events import AssistantDeltaEvent
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.learning_reply import _source_qa_abstain_reply
from hephaion.chat.session import ChatSession
from hephaion.chat.turn_contract import (
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from hephaion.chat.turn_finalization import TurnFinalizationMixin
from hephaion.chat.turn_orchestrator import TurnOrchestrator
from hephaion.chat.turn_outputs import _LearningAgentOutput
from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation, build_attempt_observation
from hephaion.learning.observation_audit import (
    audit_observation_probes,
    randomized_observation_probes,
)
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.study.policy import EvidenceAssessment
from hephaion.study.prompt_plans import LearningTurnPlan
from hephaion.study.state import LearningAction, LearningPhase


class _FinalizationProbe(TurnFinalizationMixin):
    def __init__(self, session: ChatSession) -> None:
        self.session = session
        self.last_reply = "The note says this [E2]."
        self.last_internal_passes = 0
        self._last_reply_citation_required = True
        self._learning_action_override = None
        self._learning_followup_seed_blocked = False


def _chunk(source: str = "notes.md", index: int = 0) -> Chunk:
    return Chunk(
        text="Evidence text",
        source=source,
        index=index,
        char_start=0,
        char_end=13,
    )


def _turn_evidence_with_content(evidence_id: str, source: str, content: str) -> TurnEvidence:
    return TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id=evidence_id,
                chunk=Chunk(
                    text=content,
                    source=source,
                    index=0,
                    char_start=0,
                    char_end=len(content),
                ),
                score=0.9,
                content=content,
            ),
        ),
        sampled_source_count=1,
        total_source_count=1,
    )


def test_source_qa_abstain_uses_cited_partial_progress_when_evidence_is_relevant() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "topic.md",
        "The material lists polynomial functions together with roots and limits.",
    )
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="",
        retrieval_query="polynomial functions",
        original_user_input="What does the material say about polynomial functions?",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=False,
            confidence=0.35,
            supporting_refs=("E1",),
            missing_information=("full direct explanation",),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="abstain",
        ),
    )

    reply = _source_qa_abstain_reply(plan, resolved)

    assert "polynomial functions" in reply
    assert "[E1]" in reply
    assert "fuller direct source explanation" in reply
    assert reply != (
        "The current evidence does not contain a direct source answer for this request."
    )


def test_observation_audit_core_signals_drive_static_policy() -> None:
    results = audit_observation_probes(seed=41)
    failures = tuple(
        (
            result.probe.name,
            result.chosen_action.value,
            result.probe.expected_action.value,
            result.probe.active_feature_names,
        )
        for result in results
        if not result.passed
    )

    assert not failures


def test_observation_audit_randomizes_probe_order_by_seed() -> None:
    first = tuple(probe.name for probe in randomized_observation_probes(seed=41))
    repeated = tuple(probe.name for probe in randomized_observation_probes(seed=41))
    second = tuple(probe.name for probe in randomized_observation_probes(seed=42))

    assert first == repeated
    assert first != second


def test_off_topic_observation_drives_abstain() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "exam.md",
        "Only paper notes are allowed during the exam.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Only paper notes are allowed during the exam [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="Explain selection sort and the product rule from the prior topics.",
        answer_relevance_required=True,
    )

    assert observation.off_topic_answer
    assert observation.unsupported_claim_count == 1
    assert StaticAttemptPolicy().choose(observation) is AttemptAction.ABSTAIN


def test_bad_overview_shape_drives_stricter_retry() -> None:
    observation = AttemptObservation(
        intent="material_overview",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        citation_required=True,
        evidence_count=10,
        distinct_source_count=6,
        sampled_source_count=10,
        total_source_count=10,
        top_score=1.0,
        evidence_sufficient=True,
        evidence_confidence=0.95,
        evidence_recommended_action="answer",
        has_citations=True,
        citation_count=6,
        all_citations_verified=True,
        answer_shape_failed=True,
        reply_chars=350,
        latency_ms=9800.0,
        cost_usd=0.002,
        internal_passes=2,
    )

    assert StaticAttemptPolicy().choose(observation) is (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
    )


def test_answer_relevance_scores_cited_evidence_not_uncited_context() -> None:
    evidence = TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text="Gegeben sind n Zahlen x1, ...",
                    source="exercise.md",
                    index=0,
                    char_start=0,
                    char_end=27,
                ),
                score=0.9,
                content="Gegeben sind n Zahlen x1, ...",
            ),
            EvidenceChunk(
                evidence_id="E2",
                chunk=Chunk(
                    text=(
                        "The prior overview covers number systems, polynomial properties, "
                        "limits, continuity, sequences, series, extrema, and group theory."
                    ),
                    source="overview.md",
                    index=1,
                    char_start=0,
                    char_end=120,
                ),
                score=0.8,
                content=(
                    "The prior overview covers number systems, polynomial properties, "
                    "limits, continuity, sequences, series, extrema, and group theory."
                ),
            ),
        ),
        sampled_source_count=2,
        total_source_count=2,
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E2",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Gegeben sind n Zahlen x1, ... [E1]",
        latency_ms=10.0,
        internal_passes=1,
        request_text=(
            "Explain why the prior overview covers number systems, polynomial properties, "
            "limits, continuity, sequences, series, extrema, and group theory."
        ),
        answer_relevance_required=True,
    )

    assert observation.off_topic_answer
    assert observation.answer_relevance_score < 0.12
    assert StaticAttemptPolicy().choose(observation) is AttemptAction.ABSTAIN


def test_answer_relevance_allows_source_backed_paraphrase() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "analysis.md",
        "The derivative measures a function's rate of change.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="It is the rate of change for a function [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="What does derivative mean?",
        answer_relevance_required=True,
    )

    assert not observation.off_topic_answer
    assert observation.answer_relevance_score >= 0.12
    assert StaticAttemptPolicy().choose(observation) is AttemptAction.ACCEPT


def test_answer_relevance_rejects_unrelated_reply_with_relevant_citation() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "algorithms.md",
        "Selection sort repeatedly selects the smallest remaining item.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Only paper notes are allowed during the exam [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="Explain selection sort.",
        answer_relevance_required=True,
    )

    assert observation.off_topic_answer
    assert observation.answer_relevance_score < 0.12
    assert StaticAttemptPolicy().choose(observation) is AttemptAction.ABSTAIN


def test_structural_relevance_guard_replaces_off_topic_prior_followup(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What do these topics mean and do?")
    session.conversation.add("assistant", "Only paper notes are allowed during the exam [E1].")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Only paper notes are allowed during the exam [E1]."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What do these topics mean and do?",
            resolved_intent="material_overview",
            canonical_request="Explain selection sort and the product rule.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort product rule",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt="It covers selection sort and the product rule.",
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn(
        "What do these topics mean and do?",
        resolved,
        latency_ms=10.0,
    )

    assert "does not contain a direct source answer" in probe.last_reply
    assert "paper notes" not in session.conversation.messages[-1].content
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None


def test_structural_relevance_guard_does_not_seed_rejected_prior_transform(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What does that mean?")
    session.conversation.add("assistant", "Only paper notes are allowed during the exam [E1].")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Only paper notes are allowed during the exam [E1]."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain selection sort and the product rule in simpler terms.",
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            retrieval_query="",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt="It covers selection sort and the product rule.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)

    assert "does not contain a direct source answer" in probe.last_reply
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None
    assert session.turn_history[-1].evidence is None
    assert session.turn_history[-1].contract is None


def test_structural_validation_guard_replaces_uncited_required_answer(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add(
        "assistant",
        "I could not produce a grounded material overview from the current model output.",
    )
    probe = _FinalizationProbe(session)
    probe.last_reply = "I could not produce a grounded material overview from the current output."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.PRIORITY,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "The material covers polynomial roots and continuity.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            citation_required=True,
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn(
        "What is the material about?",
        resolved,
        latency_ms=10.0,
    )

    assert "verifiable citations" in probe.last_reply
    assert session.conversation.messages[-1].content == probe.last_reply
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None


def test_structural_validation_guard_is_not_overwritten_by_relevance_guard(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "Explain selection sort.")
    session.conversation.add("assistant", "Selection sort selects the smallest item [E1].")
    session.conversation.add("user", "What does that mean?")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Selection sort repeatedly picks the smallest remaining item."
    session.conversation.add("assistant", probe.last_reply)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "sorting.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain selection sort in simpler terms.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
            prior_answer_reference=True,
        ),
    )

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)

    assert "verifiable citations" in probe.last_reply
    assert "does not contain a direct source answer" not in probe.last_reply
    assert session.conversation.messages[-1].content == probe.last_reply


def test_structural_relevance_guard_replaces_reply_before_emit(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What do these topics mean and do?")
    bad_reply = "Only paper notes are allowed during the exam [E1]."
    orchestrator = TurnOrchestrator(session)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What do these topics mean and do?",
            resolved_intent="material_overview",
            canonical_request="Explain selection sort and the product rule.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort product rule",
            citation_required=True,
            prior_answer_reference=True,
        ),
    )

    events = list(
        orchestrator._iter_agent_learning_reply_events(
            _LearningAgentOutput(
                streamed_reply=bad_reply,
                raw_reply=bad_reply,
                visible_reply=bad_reply,
                completion_event=None,
            ),
            resolved,
            session.learning_state.clone(),
            user_input="What do these topics mean and do?",
        )
    )

    first_delta = next(event for event in events if isinstance(event, AssistantDeltaEvent))
    assert "does not contain a direct source answer" in first_delta.delta
    assert "paper notes" not in first_delta.delta
    assert session.conversation.messages[-1].content == first_delta.delta


def test_structural_relevance_guard_keeps_learning_state_on_rewrite(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    original_state = session.learning_state.clone()
    session.conversation.add("user", "Teach me selection sort.")
    bad_reply = "Only paper notes are allowed during the exam [E1]."
    orchestrator = TurnOrchestrator(session)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.PRESENT,
            phase=LearningPhase.PRESENTING,
            prompt="",
            retrieval_query="selection sort",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="Teach me selection sort.",
            resolved_intent="topic_presentation",
            canonical_request="Teach selection sort.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
        ),
    )

    events = list(
        orchestrator._iter_agent_learning_reply_events(
            _LearningAgentOutput(
                streamed_reply=bad_reply,
                raw_reply=bad_reply,
                visible_reply=bad_reply,
                completion_event=None,
            ),
            resolved,
            original_state,
            user_input="Teach me selection sort.",
        )
    )

    first_delta = next(event for event in events if isinstance(event, AssistantDeltaEvent))
    assert "does not contain a direct source answer" in first_delta.delta
    assert session.learning_state.to_dict() == original_state.to_dict()


def test_structural_relevance_guard_allows_concise_prior_transform(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    long_prior = " ".join(
        (
            "selection sort product rule continuity sequences series extrema group theory",
            "number systems polynomial roots limits subgroups cyclic groups definitions",
        )
        * 12
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", f"{long_prior} [E1].")
    session.conversation.add("user", "Rewrite selection sort in one sentence.")
    concise_reply = "Selection sort repeatedly selects the smallest remaining item [E1]."
    session.conversation.add("assistant", concise_reply)
    probe = _FinalizationProbe(session)
    probe.last_reply = concise_reply
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="Rewrite selection sort in one sentence.",
            resolved_intent="material_followup",
            canonical_request="Rewrite selection sort as one sentence.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt=long_prior,
        ),
    )

    probe._finalize_successful_turn(
        "Rewrite selection sort in one sentence.",
        resolved,
        latency_ms=10.0,
    )

    assert probe.last_reply == concise_reply
    assert session.conversation.messages[-1].content == concise_reply
    assert session.last_turn_contract is not None


def test_structural_relevance_guard_allows_vague_prior_transform(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    prior_reply = "Selection sort repeatedly selects the smallest remaining item [E1]."
    session.conversation.add("user", "What is selection sort?")
    session.conversation.add("assistant", prior_reply)
    session.conversation.add("user", "What does that mean?")
    concise_reply = "Selection sort repeatedly picks the smallest remaining item [E1]."
    session.conversation.add("assistant", concise_reply)
    probe = _FinalizationProbe(session)
    probe.last_reply = concise_reply
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain the prior answer in simpler terms.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt=prior_reply,
        ),
    )

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)

    assert probe.last_reply == concise_reply
    assert session.conversation.messages[-1].content == concise_reply
    assert session.last_turn_contract is not None


def test_static_policy_chooses_retry_action_for_failed_citation_validation() -> None:
    observation = AttemptObservation(
        citation_required=True,
        evidence_count=1,
        evidence_sufficient=True,
        has_citations=True,
        citation_count=1,
        all_citations_verified=False,
        unverified_citation_count=1,
        reply_chars=120,
    )

    action = StaticAttemptPolicy().choose(observation)

    assert action is AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
