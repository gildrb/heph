"""Tests for classifier-driven chat orchestration."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import chat.evidence as evidence_module
import pytest
from _types import is_string_mapping
from ai.runtime import ChatConfig, CompletionDelta, Conversation, EngineError
from chat.agent_request import _learning_agent_request
from chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
)
from chat.evidence import (
    ResolvedTurnPlan,
    assess_turn_evidence,
    evidence_assessment_trace,
    evidence_refs,
    resolve_turn_evidence,
)
from chat.evidence_notices import _evidence_notice, _evidence_notice_metadata
from chat.intent_resolution import (
    _classified_user_intent,
    _resolved_user_intent,
    _stabilized_followup_intent_resolution,
    _stabilized_intent_for_named_material,
    _unresolved_followup_intent_resolution,
)
from chat.learning_reply import (
    _deterministic_learning_reply,
    _empty_learning_reply,
)
from chat.learning_signals import _learning_practice_context
from chat.material_state import (
    _missing_indexed_material_reply,
    _no_matching_indexed_evidence_reply,
)
from chat.model_text import _model_json_payload
from chat.orchestrator import TurnOrchestrator
from chat.overview_reply import (
    _needs_overview_fallback,
    _overview_fallback_reply,
)
from chat.prior_answer import (
    _learning_extra_system_prompt,
    _prior_answer_cited_claims,
    _prior_answer_prompt_context,
    _turn_contract_prompt_context,
)
from chat.reply_repair import (
    _run_bounded_internal_repairs,
    _should_buffer_learning_output,
    _user_visible_reply,
)
from chat.reply_text import (
    _localize_deterministic_reply,
    _unicode_math_reply,
)
from chat.session import ChatSession
from chat.turn_contract import (
    ANSWER_FORMAT_LIST,
    ANSWER_FORMAT_PLAIN,
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
    TurnIntentResolution,
)
from chat.turn_planning import (
    _apply_turn_contract_to_plan,
    _reset_unreplayable_followup_state,
    _resolved_turn_intent,
    _turn_contract_can_seed_followup,
    _turn_contract_with_prior_replay_state,
)
from chat.turn_predicates import _stored_turn_evidence
from chat.turn_query import _semantic_query_specificity
from rag import ArmoryIndex, Chunk, EvidenceChunk, ScoredChunk, TurnEvidence
from rag.chunker import ChunkedDocument
from study import (
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    LearningTurnPlan,
    RecallRating,
    material_overview_plan,
    material_topic_presentation_plan,
    plan_turn,
)
from study.schedule import load_recall_schedule


def _chunk(source: str = "notes.md", index: int = 0, text: str = "compactness material") -> Chunk:
    return Chunk(text=text, source=source, index=index, char_start=0, char_end=len(text))


def _evidence(
    evidence_id: str = "E1",
    source: str = "notes.md",
    index: int = 0,
    content: str = "compactness material",
) -> EvidenceChunk:
    return EvidenceChunk(
        evidence_id=evidence_id, chunk=_chunk(source, index, content), score=0.9, content=content
    )


def _turn_evidence(*items: EvidenceChunk, sampled: int = 0, total: int = 0) -> TurnEvidence:
    return TurnEvidence(items=tuple(items), sampled_source_count=sampled, total_source_count=total)


def _session(*, armory: bool = True) -> ChatSession:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="test-session",
        armory_path=Path("/tmp/test-armory") if armory else None,
    )
    object.__setattr__(session, "trace", MagicMock())
    if armory:
        session.source_file_count = 1
    return session


def _index(*documents: ChunkedDocument, unindexable: dict[str, str] | None = None) -> ArmoryIndex:
    index = ArmoryIndex(Path("/tmp/test-armory"))
    index.documents = list(documents)
    index.unindexable_files = unindexable or {}
    return index


def _document(
    source: str = "notes.md", text: str = "Compactness and open covers."
) -> ChunkedDocument:
    return ChunkedDocument(source=source, chunks=[_chunk(source, 0, text)], content_hash=source)


def _plan(
    action: LearningAction = LearningAction.PRESENT,
    *,
    retrieval_query: str | None = "compactness",
    retrieval_strategy: str = "",
    use_expected_source_refs: bool = False,
    requires_direct_evidence: bool = False,
    allow_tools: bool = True,
    buffer_response: bool = False,
) -> LearningTurnPlan:
    return LearningTurnPlan(
        action=action,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input=retrieval_query or "",
        retrieval_query=retrieval_query,
        retrieval_strategy=retrieval_strategy,
        use_expected_source_refs=use_expected_source_refs,
        requires_direct_evidence=requires_direct_evidence,
        allow_tools=allow_tools,
        buffer_response=buffer_response,
    )


def test_bounded_internal_repair_loop_does_not_append_english_pedagogy_scaffold() -> None:
    plan = plan_turn(
        LearningState(phase=LearningPhase.WAITING_FOR_READY, current_item="compactness"),
        "bereit",
        intent="ready_for_recall",
    )

    repaired, passes = _run_bounded_internal_repairs(
        plan,
        "Definiere Kompaktheit und nenne deine Sicherheit von 0-100%.",
        None,
        user_input="bereit",
        config=ChatConfig(),
    )

    assert passes <= 3
    assert repaired == "Definiere Kompaktheit und nenne deine Sicherheit von 0-100%."


def test_source_qa_repair_does_not_append_excerpts_when_reply_is_already_cited() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="compactness")
    evidence = _turn_evidence(
        _evidence(content="Compactness is defined using open covers in this material.")
    )

    repaired, passes = _run_bounded_internal_repairs(
        plan,
        "Compactness is defined using open covers [E1].",
        evidence,
        user_input="what is compactness?",
        config=ChatConfig(),
    )

    assert passes <= 2
    assert repaired == "Compactness is defined using open covers [E1]."


def test_source_qa_repair_uses_compact_model_repair_when_reply_has_no_citations() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="compactness")
    evidence = _turn_evidence(
        _evidence(content="Compactness is defined using open covers in this material.")
    )
    config = ChatConfig(base_url="https://local.test/v1", model="repair")

    with patch(
        "chat.model_text.stream_completion",
        return_value=iter(
            [CompletionDelta(content="Compactness uses open covers in this material [E1].")]
        ),
    ):
        repaired, _passes = _run_bounded_internal_repairs(
            plan,
            "Compactness is defined using open covers.",
            evidence,
            user_input="what is compactness?",
            config=config,
        )

    assert repaired == "Compactness uses open covers in this material [E1]."


def test_source_qa_repair_appends_citation_when_model_repair_unavailable() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="compactness")
    evidence = _turn_evidence(
        _evidence(content="Compactness is defined using open covers in this material.")
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "Compactness is defined using open covers in this material.",
        evidence,
        user_input="what is compactness?",
        config=ChatConfig(),
    )

    assert repaired == "Compactness is defined using open covers in this material. [E1]"


def test_repair_replaces_unverified_source_quotes_with_evidence_pointer() -> None:
    evidence = _turn_evidence(
        _evidence(
            content="The procedure says to report that the material does not contain the answer."
        )
    )

    repaired, _passes = _run_bounded_internal_repairs(
        _plan(action=LearningAction.SOURCE_QA),
        (
            "The source sentence is: "
            '"The current evidence does not contain a direct source answer." [E1]'
        ),
        evidence,
        user_input="Show the evidence.",
        config=ChatConfig(),
    )

    assert "The current evidence does not contain a direct source answer" not in repaired
    assert "The procedure says to report" in repaired


def test_source_qa_repair_compacts_oversized_cited_reply_before_model_repair() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(content="The source-backed point is short and directly cited.")
    )
    oversized = " ".join(["The source-backed point is short and directly cited [E1]."] * 30)

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        oversized,
        evidence,
        user_input="make it concise",
        config=ChatConfig(base_url="https://local.test/v1", model="repair"),
    )

    assert len(repaired) < len(oversized)
    assert len(repaired) <= 700
    assert "The source-backed point is short and directly cited [E1]." in repaired


def test_source_qa_repair_deterministically_compacts_oversized_cited_units() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence("E1", content="First supported point."),
        _evidence("E2", content="Second supported point."),
        _evidence("E3", content="Third supported point."),
    )
    oversized = "\n".join(
        (
            "First supported point. [E1]",
            "Second supported point. [E2]",
            "Third supported point. [E3]",
            " ".join(["First supported point. [E1]"] * 80),
        )
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        oversized,
        evidence,
        user_input="make it concise",
        config=ChatConfig(),
    )

    assert len(repaired) < 700
    assert "First supported point. [E1]" in repaired
    assert "Second supported point. [E2]" in repaired
    assert "Third supported point. [E3]" in repaired


def test_transform_prior_repair_does_not_append_evidence_inventory() -> None:
    plan = _plan(action=LearningAction.PRESENT)
    evidence = _turn_evidence(
        _evidence(content="The source-backed prompt asks for the shortest accurate version.")
    )
    contract = TurnContract(
        original_user_input="What is the shortest accurate version?",
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        citation_required=True,
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "Short version: identify the claim, then cite the supporting phrase.",
        evidence,
        user_input="What is the shortest accurate version?",
        config=ChatConfig(),
        contract=contract,
    )

    assert repaired == "Short version: identify the claim, then cite the supporting phrase."


def test_calibration_repair_adds_minimal_evidence_citation() -> None:
    plan = _plan(action=LearningAction.CALIBRATE)
    evidence = _turn_evidence(_evidence(content="The product rule uses both factors."))

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "What is the product rule idea? Answer from memory.",
        evidence,
        user_input="review me",
        config=ChatConfig(),
    )

    assert repaired == "What is the product rule idea? Answer from memory. [E1]"


def test_assessment_repair_adds_required_evidence_citation() -> None:
    plan = _plan(action=LearningAction.ASSESS)
    evidence = _turn_evidence(_evidence(content="A supporting rubric point."))

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "PARTIAL: Name the missing source-backed point.",
        evidence,
        user_input="assess",
        config=ChatConfig(),
    )

    assert repaired == "PARTIAL: Name the missing source-backed point. [E1]"


def test_source_qa_assessment_requires_direct_support_for_resolved_query() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="Which source mentions the amber lattice theorem?",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(
            content=(
                "The source explains how to report unsupported answers when no matching "
                "supporting phrase appears."
            )
        ),
        _evidence(
            "E2",
            "other.md",
            content="A separate source describes a worked example about rates of change.",
        ),
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"
    assert assessment.missing_information == (
        "direct source span for Which source mentions the amber lattice theorem?",
    )


def test_source_qa_assessment_does_not_aggregate_generic_support_across_sources() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="which document source contains the invented theorem phrase",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(
            content="The source gives a procedure for reporting when no supporting phrase appears."
        ),
        _evidence(
            "E2",
            "other.md",
            content="This document contains unrelated formula examples.",
        ),
        _evidence(
            "E3",
            "third.md",
            content="A separate note discusses ordinary theorem statements.",
        ),
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_backed_summary_request_does_not_force_locator_support() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="Switch to history and summarize one source-backed point.",
        retrieval_query="history Switch to history and summarize one source-backed point.",
    )
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "history.md",
            0,
            (
                "# History Source\nThe public library example describes a city choosing "
                "longer opening hours after community groups asked for evening access. "
                "The decision followed documented requests and a budget review."
            ),
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.recommended_action != "abstain"


def test_source_qa_direct_lookup_uses_original_request_when_query_is_condensed() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="Using only the sources, what is the amber forge retrieval phrase?",
        retrieval_query="amber forge retrieval phrase",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(
            content="The source gives a procedure for reporting when no supporting phrase appears."
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_qa_direct_support_scores_original_request_not_expanded_query() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="was ist l hopital?",
        retrieval_query="L'Hôpital's rule definition and conditions",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(
            content="Jeden dieser Grenzwerte kann man auf die Regel von l'Hospital zurückführen."
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.recommended_action != "abstain"


def test_expanded_source_qa_filter_scores_original_request_not_expanded_query() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="was ist l hopital?",
        retrieval_query="L'Hôpital's rule definition and conditions in calculus materials",
        requires_direct_evidence=True,
    )
    scored = [
        ScoredChunk(
            chunk=_chunk(
                "calculus.md",
                8,
                "Diese Grenzwerte kann man oft auf die Regel von l'Hospital zurückführen.",
            ),
            score=0.9,
        )
    ]

    relevant = evidence_module._source_qa_relevant_query_scored(plan, scored)

    assert relevant == scored


def test_source_qa_assessment_accepts_direct_source_support() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="product rule source")
    evidence = _turn_evidence(
        _evidence(content="The product rule source says both factors contribute.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is True


def test_source_qa_assessment_accepts_dominant_retrieval_support() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="source with strongest procedural wording explain procedure",
    )
    evidence = _turn_evidence(
        replace(
            _evidence(
                content=(
                    "The procedure source has three steps: read the claim, locate the "
                    "supporting phrase, and cite it."
                )
            ),
            score=1.0,
        ),
        replace(
            _evidence(
                "E2",
                content="A separate note describes a formula example.",
                index=1,
            ),
            score=0.2,
        ),
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is True
    assert assessment.recommended_action == "answer"


def test_source_qa_dominant_retrieval_support_requires_distinctive_terms() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt=(
            "User question: Using only the armory, what date was the fictional launch ceremony?"
        ),
        retrieval_query="armory materials fictional launch ceremony date",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        replace(
            _evidence(
                content=(
                    "This generated armory contains generic public materials for algorithms, "
                    "calculus, physics, learning methods, history, exercises, exams, formulas, "
                    "and grounded answering."
                )
            ),
            score=1.24,
        ),
        replace(
            _evidence(
                "E2",
                content="A study method source describes retrieval practice and feedback.",
                index=1,
            ),
            score=0.54,
        ),
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_qa_quoted_phrase_lookup_requires_phrase_terms() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt='User question: Which source mentions the invented theorem called "silver cactus"?',
        retrieval_query=(
            'Find any source in the materials that mentions the phrase "silver cactus"; '
            "identify which source contains it."
        ),
    )
    evidence = _turn_evidence(
        _evidence(content="The source gives a procedure for reporting unsupported answers."),
        _evidence(
            "E2",
            "other.md",
            content="A separate source discusses ordinary theorem statements.",
        ),
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_qa_detail_request_does_not_require_exact_lookup_support() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="one additional cited detail supporting the prior answer",
    )
    evidence = _turn_evidence(
        _evidence(content="Spacing makes the next recall attempt more diagnostic.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.recommended_action != "abstain"


def test_source_qa_reuse_prior_evidence_does_not_match_followup_words() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
    )
    plan = replace(
        plan,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=("notes.md#chunk=0",),
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(content="The prior source set contains the cited support span.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "give_partial_answer"


def test_direct_reuse_prior_source_qa_still_checks_current_question_support() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="How is the next item selected?",
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=("notes.md#chunk=0",),
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(content="A sequence is a mapping from natural numbers into a set.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_qa_definition_request_without_retrieval_query_requires_direct_support() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="Define the most technical term.",
        retrieval_query=None,
    )
    evidence = _turn_evidence(
        _evidence(content="Spacing makes the next recall attempt more diagnostic.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"
    assert assessment.missing_information == (
        "direct source span for Define the most technical term.",
    )


def test_source_qa_abstains_deterministically_when_direct_answer_is_missing() -> None:
    session = _session()
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="Which source mentions the amber lattice theorem?",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(content="The source explains how to report unsupported answers.")
    )
    contract = TurnContract(
        original_user_input="Which source mentions the amber lattice theorem?",
        resolved_intent="source_qa",
        canonical_request="Which source mentions the amber lattice theorem?",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
        turn_contract=contract,
    )

    deterministic = _deterministic_learning_reply(session, plan, resolved)

    assert deterministic is not None
    assert "current evidence does not contain a direct source answer" in deterministic.reply


def test_source_qa_abstain_overrides_prior_single_citation_quote() -> None:
    session = _session()
    session.conversation.add("user", "Explain the source point.")
    session.conversation.add("assistant", "The source point is grounded [E1].")
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the source point.",
        resolved_intent="source_qa",
        evidence_refs=("notes.md#chunk=0",),
    )
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="missing direct phrase",
        requires_direct_evidence=True,
    )
    evidence = _turn_evidence(
        _evidence(
            source="notes.md",
            content="The source point is grounded by an available note.",
        )
    )
    contract = TurnContract(
        original_user_input="Using only the sources, what is the missing direct phrase?",
        resolved_intent="source_qa",
        canonical_request="Using only the sources, what is the missing direct phrase?",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        citation_required=True,
        prior_answer_reference=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
        turn_contract=contract,
    )

    deterministic = _deterministic_learning_reply(session, plan, resolved)

    assert deterministic is not None
    assert "current evidence does not contain a direct source answer" in deterministic.reply
    assert "amber lattice theorem" not in deterministic.reply
    assert "[E1]" not in deterministic.reply
    assert deterministic.citation_required is False
    assert "visible source chunks" not in deterministic.reply


def test_broad_material_followup_uses_structural_evidence_overview() -> None:
    session = _session()
    plan = material_overview_plan("what else stands out")
    evidence = _turn_evidence(
        _evidence("E1", "algorithms.md", 0, "# Algorithms\nSelection sort picks items."),
        _evidence("E2", "calculus.md", 0, "# Calculus\nThe product rule uses both factors."),
        _evidence("E3", "exams.md", 0, "# Exams\nShort answers cite evidence."),
    )
    contract = TurnContract(
        original_user_input="What else stands out?",
        resolved_intent="material_overview",
        canonical_request="Ask for another broad material takeaway.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="additional material overview details",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
        turn_contract=contract,
    )

    deterministic = _deterministic_learning_reply(session, plan, resolved)

    assert deterministic is not None
    assert deterministic.reply.count("\n") <= 2
    assert "[E1]" in deterministic.reply
    assert "stands out" not in deterministic.reply


def test_broad_material_followup_skips_recently_cited_overview_items() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add(
        "assistant",
        "- Selection sort picks items [E1].\n"
        "- The product rule uses both factors [E2].\n"
        "- Exam answers cite evidence [E3].",
    )
    plan = material_overview_plan("what else stands out")
    evidence = _turn_evidence(
        _evidence("E1", "algorithms.md", 0, "# Algorithms\nSelection sort picks items."),
        _evidence("E2", "calculus.md", 0, "# Calculus\nThe product rule uses both factors."),
        _evidence("E3", "exams.md", 0, "# Exams\nShort answers cite evidence."),
        _evidence("E4", "exercises.md", 0, "# Exercises\nLearners annotate answers."),
        _evidence("E5", "formulas.md", 0, "# Formulas\nSlope measures rate of change."),
    )
    contract = TurnContract(
        original_user_input="What else stands out?",
        resolved_intent="material_overview",
        canonical_request="Ask for another broad material takeaway.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
        turn_contract=contract,
    )

    deterministic = _deterministic_learning_reply(session, plan, resolved)

    assert deterministic is not None
    assert "[E4]" in deterministic.reply
    assert "[E5]" in deterministic.reply
    assert "[E1]" not in deterministic.reply
    assert "[E2]" not in deterministic.reply
    assert "[E3]" not in deterministic.reply
    assert deterministic.source_refs == [
        "algorithms.md#chunk=0",
        "calculus.md#chunk=0",
        "exams.md#chunk=0",
        "exercises.md#chunk=0",
        "formulas.md#chunk=0",
    ]


def test_source_followup_with_evidence_uses_model_prompt_not_canned_reply() -> None:
    session = _session()
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="supporting phrase report material does not contain the answer",
    )
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "procedure.md",
            0,
            (
                "# Procedure\nIf no supporting phrase appears, report that the material "
                "does not contain the answer."
            ),
        )
    )
    contract = TurnContract(
        original_user_input="Which evidence block backs up the comparison?",
        resolved_intent="source_qa",
        canonical_request="Which evidence block supports the comparison?",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="supporting phrase report material does not contain the answer",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
        turn_contract=contract,
    )

    deterministic = _deterministic_learning_reply(session, plan, resolved)

    assert deterministic is None


def test_empty_reasoned_source_followup_does_not_fall_back_to_raw_excerpt() -> None:
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "calculus.md",
            0,
            "Damit folgt f(x) approximiert eine Funktion in der Nähe von x0.",
        )
    )
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="real-life applications of the prior cited material",
        requires_direct_evidence=False,
    )
    contract = TurnContract(
        original_user_input="When would I use this outside the course?",
        resolved_intent="source_qa",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("calculus.md#chunk=0",),
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _empty_learning_reply(
        plan,
        resolved,
        user_input="When would I use this outside the course?",
        config=ChatConfig(),
    )

    assert "Damit folgt" not in reply
    assert reply == "I could not generate a prompt."


def test_empty_direct_source_lookup_can_fall_back_to_source_excerpt() -> None:
    evidence = _turn_evidence(
        _evidence("E1", "source.md", 0, "The source directly states the requested detail.")
    )
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="requested detail",
        requires_direct_evidence=True,
    )
    contract = TurnContract(
        original_user_input="Which source directly states the requested detail?",
        resolved_intent="source_qa",
        direct_evidence_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _empty_learning_reply(
        plan,
        resolved,
        user_input="Which source directly states the requested detail?",
        config=ChatConfig(),
    )

    assert "requested detail" in reply
    assert "[E1]" in reply


def test_expanded_prior_evidence_preserves_prior_ids_for_reused_refs() -> None:
    prior_chunk = _chunk("prior.md", 0, "The prior source states the supported claim.")
    new_chunk = _chunk("new.md", 0, "A new source gives adjacent context.")
    scored = [
        ScoredChunk(chunk=new_chunk, score=1.0),
        ScoredChunk(chunk=prior_chunk, score=0.9),
    ]

    evidence = evidence_module._build_expanded_turn_evidence(
        scored,
        prior_refs=("first.md#chunk=0", "prior.md#chunk=0"),
        max_tokens=2000,
    )

    ids_by_ref = {
        f"{item.source}#chunk={item.chunk_index}": item.evidence_id for item in evidence.items
    }
    assert ids_by_ref["prior.md#chunk=0"] == "E2"
    assert ids_by_ref["new.md#chunk=0"] == "E3"


def test_retrieval_filters_repeated_short_duplicate_chunks() -> None:
    repeated = "Shared generated footer that carries no document-specific learning content."
    scored = [
        ScoredChunk(chunk=_chunk("a.md", 0, repeated), score=0.9),
        ScoredChunk(chunk=_chunk("b.md", 0, repeated), score=0.8),
        ScoredChunk(chunk=_chunk("c.md", 0, "A source-specific definition remains."), score=0.7),
    ]

    filtered = evidence_module._filter_low_content_chunks(scored)

    assert [item.chunk.source for item in filtered] == ["c.md"]


@pytest.mark.parametrize(
    ("payload", "prior_intent", "expected"),
    [
        ({"intent": "topic drill", "confidence": 0.9}, "", "topic_drill"),
        ({"intent": "source_qa", "confidence": "75%"}, "", "source_qa"),
        ({"intent": "unsupported", "confidence": 1.0}, "", ""),
        ({"intent": "chat", "confidence": 0.2}, "topic_presentation", "topic_presentation"),
        ({"intent": "chat", "confidence": 0.2}, "heph_help", ""),
    ],
)
def test_classified_user_intent_normalizes_model_json_payload(
    payload: dict[str, object],
    prior_intent: str,
    expected: str,
) -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch("chat.model_text._model_json_payload", return_value=payload) as model_json:
        intent = _classified_user_intent(
            "nochmal",
            config=config,
            conversation=Conversation(),
            prior_intent=prior_intent,
        )

    assert intent == expected
    model_json.assert_called_once()
    assert "Current user request:\nnochmal" in model_json.call_args.kwargs["user_prompt"]


def test_classified_user_intent_returns_empty_when_classifier_unavailable() -> None:
    assert _classified_user_intent("Explain", config=ChatConfig()) == ""


def test_resolved_user_intent_treats_classifier_engine_errors_as_low_confidence() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with (
        patch(
            "chat.model_text.stream_completion",
            side_effect=EngineError("timed out"),
        ),
    ):
        resolution = _resolved_user_intent(
            "Using only the sources, what does the material say?",
            config=config,
            conversation=Conversation(),
            prior_intent="source_qa",
        )

    assert resolution.intent == "source_qa"
    assert resolution.confidence == 0.0
    assert resolution.is_followup is True


def test_low_confidence_followup_reuses_prior_surface_instead_of_literal_request() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")
    prior_contract = TurnContract(
        original_user_input="Summarize the material.",
        resolved_intent="material_overview",
        canonical_request="Provide a compact overview of the material contents.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="material overview",
        evidence_refs=("materials/source.md#chunk=0",),
    )

    with (
        patch(
            "chat.model_text.stream_completion",
            side_effect=EngineError("timed out"),
        ),
    ):
        resolution = _resolved_user_intent(
            "How does that matter in practice?",
            config=config,
            conversation=Conversation(),
            prior_intent="material_overview",
            prior_contract=prior_contract,
        )

    assert resolution.intent == "material_overview"
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert resolution.retrieval_query == ""
    assert resolution.retrieval_query != "How does that matter in practice?"
    assert resolution.prior_answer_reference is True


def test_named_material_switch_uses_corpus_source_label_for_retrieval() -> None:
    index = _index(_document(source="materials/study-methods.md"))
    resolution = TurnIntentResolution(
        intent="material_overview",
        canonical_request="Switch to study methods and explain the learning advice.",
        is_followup=True,
        retrieval_strategy="overview",
        retrieval_query="what is the material about",
        confidence=0.9,
    )

    stabilized = _stabilized_intent_for_named_material(
        resolution,
        user_input="Switch to study methods and explain the learning advice.",
        index=index,
    )

    assert stabilized.intent == "topic_presentation"
    assert stabilized.retrieval_strategy == "retrieve"
    assert "study methods" in stabilized.retrieval_query


def test_named_material_switch_overrides_prior_followup_retrieval() -> None:
    index = _index(_document(source="materials/physics.md"))
    resolution = TurnIntentResolution(
        intent="source_qa",
        canonical_request="Ask what is decomposed in the named source.",
        is_followup=True,
        retrieval_strategy="expand_prior_evidence",
        retrieval_query="the prior cited calculus claim",
        confidence=0.9,
    )

    stabilized = _stabilized_intent_for_named_material(
        resolution,
        user_input="In the physics source, what is decomposed?",
        index=index,
    )

    assert stabilized.intent == "source_qa"
    assert stabilized.retrieval_strategy == "retrieve"
    assert "physics" in stabilized.retrieval_query
    assert "decomposed" in stabilized.retrieval_query


def test_resolved_user_intent_preserves_semantic_followup_query() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "source_qa",
            "canonical_english_request": (
                "Give another implication of compactness from the prior answer."
            ),
            "is_followup": True,
            "followup_target": "previous cited answer",
            "retrieval_strategy": "expand_prior_evidence",
            "retrieval_query": "additional implications of compactness in the material",
            "confidence": 0.95,
        },
    ):
        resolution = _resolved_user_intent(
            "what else?",
            config=config,
            conversation=Conversation(),
            prior_intent="source_qa",
        )

    assert resolution.intent == "source_qa"
    assert resolution.is_followup is True
    assert resolution.followup_target == "previous cited answer"
    assert resolution.retrieval_query == "additional implications of compactness in the material"
    assert resolution.retrieval_query != "what else?"


def test_resolved_user_intent_includes_prior_turn_contract_state() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")
    prior_contract = TurnContract(
        original_user_input="what is the material about",
        resolved_intent="material_overview",
        canonical_request="Summarize the material corpus.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="what is the material about",
        evidence_refs=(
            "source-a.md#chunk=0",
            "source-b.md#chunk=1",
            "source-c.md#chunk=2",
            "source-d.md#chunk=3",
            "source-e.md#chunk=4",
        ),
        citation_required=True,
        validation_result="ok",
    )

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "material_overview",
            "canonical_english_request": "Explain why the prior material overview matters.",
            "is_followup": True,
            "followup_target": "prior material overview",
            "answer_mode": ANSWER_MODE_REASON_FROM_PRIOR,
            "retrieval_strategy": RETRIEVAL_STRATEGY_REUSE_PRIOR,
            "retrieval_query": "",
            "confidence": 0.95,
        },
    ) as model_json:
        _resolved_user_intent(
            "why is that important?",
            config=config,
            conversation=Conversation(),
            prior_intent="material_overview",
            prior_contract=prior_contract,
        )

    user_prompt = model_json.call_args.kwargs["user_prompt"]
    assert "Prior turn:" in user_prompt
    assert "intent=material_overview" in user_prompt
    assert "retrieval=overview" in user_prompt
    assert "source-a.md#chunk=0" in user_prompt
    assert "+1 more" in user_prompt
    assert "Current user request:\nwhy is that important?" in user_prompt


def test_resolved_user_intent_preserves_prior_answer_transform_mode() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "material_overview",
            "canonical_english_request": "Present the previous overview in another language.",
            "is_followup": True,
            "followup_target": "previous material overview answer",
            "answer_mode": "transform_prior_answer",
            "retrieval_strategy": "reuse_prior_evidence",
            "retrieval_query": "",
            "confidence": 0.95,
        },
    ):
        resolution = _resolved_user_intent(
            "in another language",
            config=config,
            conversation=Conversation(),
            prior_intent="material_overview",
        )

    assert resolution.intent == "material_overview"
    assert resolution.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert resolution.retrieval_query == ""


def test_material_followup_does_not_enter_learning_scaffold_intent() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="scaffold_request",
            canonical_request="Make a two-step checklist from the evidence.",
            answer_format=ANSWER_FORMAT_LIST,
            retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
            confidence=0.94,
        ),
        user_input="Can you make a two-step learning checklist from the evidence?",
        prior_intent="source_qa",
    )

    assert resolution.intent == "source_qa"
    assert resolution.is_followup is True
    assert resolution.prior_answer_reference is True
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR


def test_low_confidence_followup_reuses_prior_answer_instead_of_literal_search() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")
    prior_contract = TurnContract(
        original_user_input="what is the material about?",
        resolved_intent="material_overview",
        canonical_request="Summarize the material corpus.",
        answer_format=ANSWER_FORMAT_LIST,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        evidence_refs=("notes.md#chunk=0",),
    )

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "material_overview",
            "confidence": 0.0,
        },
    ):
        resolution = _resolved_user_intent(
            "same thing",
            config=config,
            conversation=Conversation(),
            prior_intent="material_overview",
            prior_contract=prior_contract,
        )

    assert resolution.intent == "material_overview"
    assert resolution.is_followup is True
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert resolution.answer_format == ANSWER_FORMAT_LIST
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert resolution.retrieval_query == "Summarize the material corpus."


def test_low_confidence_substantive_followup_reuses_prior_context() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")
    prior_contract = TurnContract(
        original_user_input="what is the material about?",
        resolved_intent="material_overview",
        canonical_request="Summarize the material corpus.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        evidence_refs=("notes.md#chunk=0",),
    )

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "material_overview",
            "confidence": 0.0,
        },
    ):
        resolution = _resolved_user_intent(
            "Switch to a source-backed method summary.",
            config=config,
            conversation=Conversation(),
            prior_intent="material_overview",
            prior_contract=prior_contract,
        )

    assert resolution.intent == "material_overview"
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert resolution.retrieval_query == "Summarize the material corpus."
    assert resolution.retrieval_query != "Switch to a source-backed method summary."


def test_resolved_user_intent_preserves_prior_answer_reference() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "source_qa",
            "canonical_english_request": "Explain the source-backed claim in the prior answer.",
            "is_followup": True,
            "followup_target": "the prior cited claim",
            "retrieval_strategy": "expand_prior_evidence",
            "retrieval_query": "source-backed claim from the prior answer",
            "prior_answer_reference": True,
            "prior_answer_positions": [1, 3],
            "prior_answer_position_basis": "cited_claims",
            "confidence": 0.95,
        },
    ):
        resolution = _resolved_user_intent(
            "Where does the cited claim come from?",
            config=config,
            conversation=Conversation(),
            prior_intent="source_qa",
        )

    assert resolution.intent == "source_qa"
    assert resolution.is_followup is True
    assert resolution.prior_answer_reference is True
    assert resolution.prior_answer_positions == (1, 3)
    assert resolution.prior_answer_position_basis == "cited_claims"


def test_resolved_user_intent_preserves_table_format() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "chat.model_text._model_json_payload",
        return_value={
            "intent": "material_overview",
            "canonical_english_request": "Create a compact table about the material corpus.",
            "is_followup": False,
            "answer_format": "table",
            "retrieval_strategy": "overview",
            "retrieval_query": "material corpus topics and contents",
            "confidence": 0.95,
        },
    ):
        resolution = _resolved_user_intent(
            "create a table regarding the material",
            config=config,
            conversation=Conversation(),
            prior_intent="",
        )

    assert resolution.intent == "material_overview"
    assert resolution.answer_format == ANSWER_FORMAT_TABLE
    assert resolution.retrieval_strategy == "overview"


def test_model_json_payload_returns_none_without_model_config() -> None:
    assert _model_json_payload(None, system_prompt="system", user_prompt="user") is None
    assert _model_json_payload(ChatConfig(), system_prompt="system", user_prompt="user") is None


def test_model_json_payload_parses_streamed_json_fragment() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value='prefix {"intent": "chat", "confidence": 0.91} suffix',
    ):
        payload = _model_json_payload(config, system_prompt="system", user_prompt="user")

    assert payload == {"intent": "chat", "confidence": 0.91}


def test_armory_orchestrator_passes_classifier_intent_to_plan_turn_and_applies_result() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_plan_intent = "topic_presentation"
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence())

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(intent="topic_presentation"),
        ) as classify,
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            return_value=ResolvedTurnPlan(
                learning_plan=plan_turn(
                    LearningState(), "Explain compactness", intent="topic_presentation"
                ),
                turn_evidence=evidence,
                evidence_assessment=assess_turn_evidence(
                    plan_turn(LearningState(), "Explain compactness", intent="topic_presentation"),
                    evidence,
                ),
            ),
        ) as resolve,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Answer [E1]"),
                    TurnCompleteEvent("Answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("Explain compactness"))

    assert classify.call_args.kwargs["prior_intent"] == "topic_presentation"
    resolved_plan = resolve.call_args.args[0]
    assert resolved_plan.action is LearningAction.PRESENT
    assert resolved_plan.retrieval_query == "Explain compactness"
    assert session.learning_state.phase is LearningPhase.WAITING_FOR_READY
    assert session.last_plan_intent == "topic_presentation"
    assert any(isinstance(event, TurnCompleteEvent) for event in events)
    assert session.conversation.messages[-1].content.startswith("Check [E1]")


def test_armory_orchestrator_uses_mocked_model_payload_for_classifier_integration() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence())

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.model_text._model_json_payload",
            return_value={
                "intent": "source_qa",
                "canonical_english_request": "Where the material defines compactness.",
                "retrieval_query": "compactness definition",
                "confidence": 1.0,
            },
        ) as model_payload,
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Source answer [E1]"),
                    TurnCompleteEvent("Source answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("Where is compactness defined?"))

    assert model_payload.called
    assert session.learning_state.current_item == ""
    assert session.last_plan_intent == "source_qa"
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.original_user_input == "Where is compactness defined?"
    assert session.last_turn_contract.retrieval_query == "compactness definition"
    assert session.last_turn_contract.validation_result == "ok"
    record_session_event = cast("MagicMock", session.trace.record_session_event)
    reply_trace_calls = [
        call
        for call in record_session_event.call_args_list
        if call.args and call.args[0] == "reply"
    ]
    assert reply_trace_calls
    assert reply_trace_calls[-1].kwargs["turn_contract"]["validation_result"] == "ok"
    assert session.conversation.messages[-1].content.startswith("Check [E1]")


def test_successful_turn_contract_keeps_only_visible_cited_evidence_refs() -> None:
    session = _session()
    orchestrator = TurnOrchestrator(session)
    orchestrator.last_reply = "Only the second excerpt is used here [E2]."
    evidence = _turn_evidence(
        _evidence("E1", "first.md", 0, "The first excerpt is not cited."),
        _evidence("E2", "second.md", 3, "The second excerpt is cited."),
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=TurnContract(
            original_user_input="Use one excerpt.",
            resolved_intent="source_qa",
            retrieval_query="one excerpt",
            evidence_refs=("first.md#chunk=0", "second.md#chunk=3"),
            citation_required=True,
        ),
    )

    with (
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        orchestrator._finalize_successful_turn("Use one excerpt.", resolved, latency_ms=1.0)

    assert session.last_turn_contract is not None
    assert session.last_turn_contract.evidence_refs == ("second.md#chunk=3",)
    record_session_event = cast("MagicMock", session.trace.record_session_event)
    reply_trace = record_session_event.call_args.kwargs
    assert reply_trace["evidence_refs"] == ["second.md#chunk=3"]
    assert reply_trace["turn_contract"]["evidence_refs"] == ["second.md#chunk=3"]


def test_successful_turn_contract_preserves_uncited_turn_without_evidence_refs() -> None:
    session = _session()
    orchestrator = TurnOrchestrator(session)
    orchestrator.last_reply = (
        "The current evidence does not contain a direct source answer for this request."
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=TurnContract(
            original_user_input="Find the exact phrase.",
            resolved_intent="source_qa",
            retrieval_query="exact phrase",
            evidence_refs=("notes.md#chunk=0",),
            citation_required=False,
        ),
    )

    with (
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        orchestrator._finalize_successful_turn("Find the exact phrase.", resolved, latency_ms=1.0)

    assert session.last_turn_contract is not None
    assert session.last_turn_contract.original_user_input == "Find the exact phrase."
    assert session.last_turn_contract.evidence_refs == ()


def test_followup_can_reuse_prior_evidence_without_literal_retrieval_text() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_plan_intent = "source_qa"
    session.last_turn_contract = TurnContract(
        original_user_input="Where is compactness defined?",
        resolved_intent="source_qa",
        retrieval_query="compactness definition",
        evidence_refs=("notes.md#chunk=0",),
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence())

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="Explain another implication of the previous cited answer.",
                is_followup=True,
                followup_target="previous cited answer",
                retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Follow-up answer [E1]"),
                    TurnCompleteEvent("Follow-up answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("what else?"))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_query is None
    assert plan.evidence_refs == ("notes.md#chunk=0",)
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.original_user_input == "what else?"
    assert session.last_turn_contract.retrieval_query == ""
    assert session.last_turn_contract.evidence_refs == ("notes.md#chunk=0",)


def test_followup_literal_retrieval_query_expands_prior_evidence() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the definition.",
        resolved_intent="source_qa",
        canonical_request="Explain compactness from the notes.",
        retrieval_query="compactness definition",
        evidence_refs=("notes.md#chunk=0",),
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence())

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="Compare compactness with the prior cited topic.",
                is_followup=True,
                followup_target="previous cited topic",
                retrieval_query="Compare that with the topic before it.",
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Comparison answer [E1]"),
                    TurnCompleteEvent("Comparison answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("Compare that with the topic before it."))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_query == "Compare compactness with the prior cited topic."
    assert plan.evidence_refs == ("notes.md#chunk=0",)
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.retrieval_query == plan.retrieval_query
    assert session.last_turn_contract.evidence_refs == ("notes.md#chunk=0",)


def test_followup_semantic_retrieval_query_expands_prior_evidence() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_turn_contract = TurnContract(
        original_user_input="Quiz me on the retrieval practice source.",
        resolved_intent="ready_for_recall",
        canonical_request="Ask a recall prompt about feedback and spacing.",
        retrieval_query="feedback and spacing in recall practice",
        evidence_refs=("study-methods.md#chunk=0",),
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence(source="study-methods.md"))

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="priority_request",
                canonical_request=(
                    "Tell me what to revisit before continuing with the current recall prompt."
                ),
                is_followup=True,
                followup_target="the current recall prompt about feedback and spacing",
                retrieval_query="feedback and spacing in recall practice",
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Review feedback and spacing [E1]"),
                    TurnCompleteEvent("Review feedback and spacing [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("What should I revisit before continuing?"))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert plan.retrieval_query == "feedback and spacing in recall practice"
    assert plan.evidence_refs == ("study-methods.md#chunk=0",)


def test_followup_expands_broad_prior_overview_instead_of_reusing_it() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_turn_contract = TurnContract(
        original_user_input="What is the material about?",
        resolved_intent="material_overview",
        retrieval_strategy="overview",
        retrieval_query="what is the material about",
        evidence_refs=tuple(f"materials/source-{index}.md#chunk=0" for index in range(10)),
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence(source="materials/source-1.md"))

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="Explain the study-methods evidence about feedback.",
                is_followup=True,
                followup_target="study-methods evidence",
                retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Focused answer [E1]"),
                    TurnCompleteEvent("Focused answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("Explain that part more."))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert plan.retrieval_query == "Explain the study-methods evidence about feedback."
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.evidence_refs == ("materials/source-1.md#chunk=0",)


def test_followup_expands_compact_prior_overview_instead_of_requoting_it() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    contract = TurnContract(
        original_user_input="Continue from there.",
        resolved_intent="material_overview",
        canonical_request="Continue the material overview.",
        is_followup=True,
        followup_target="the prior material overview",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query="what is the material about",
            evidence_refs=(
                "materials/source-1.md#chunk=0",
                "materials/source-2.md#chunk=0",
                "materials/source-3.md#chunk=0",
            ),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert updated_plan.retrieval_query == "Continue the material overview."
    assert updated_contract.evidence_refs == (
        "materials/source-1.md#chunk=0",
        "materials/source-2.md#chunk=0",
        "materials/source-3.md#chunk=0",
    )


def test_answer_transform_followup_reuses_prior_evidence_without_source_search() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_plan_intent = "material_overview"
    prior_refs = tuple(f"materials/source-{index}.md#chunk=0" for index in range(10))
    session.last_turn_contract = TurnContract(
        original_user_input="What is the material about?",
        resolved_intent="material_overview",
        canonical_request="Give a concise overview of the material corpus.",
        retrieval_strategy="overview",
        retrieval_query="what is the material about",
        evidence_refs=prior_refs,
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence(source="materials/source-1.md"))

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        assert plan.retrieval_query is None
        assert plan.evidence_refs == prior_refs
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="material_overview",
                canonical_request="Translate the prior material overview into German.",
                is_followup=True,
                followup_target="prior material overview answer",
                answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
                retrieval_strategy="retrieve",
                retrieval_query="the previous overview of the materials and their topics",
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Deutsche Uebersicht [E1]"),
                    TurnCompleteEvent("Deutsche Uebersicht [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("auf deutsch"))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert plan.retrieval_query is None
    assert plan.evidence_refs == prior_refs
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
    assert session.last_turn_contract.retrieval_query == ""
    assert session.last_turn_contract.evidence_refs == ("materials/source-1.md#chunk=0",)


def test_relevance_followup_reasons_from_prior_evidence_without_source_search() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    prior_refs = ("materials/source-1.md#chunk=0", "materials/source-2.md#chunk=0")
    session.last_plan_intent = "material_overview"
    session.last_turn_contract = TurnContract(
        original_user_input="What is the material about?",
        resolved_intent="material_overview",
        canonical_request="Give a concise overview of the material corpus.",
        retrieval_strategy="overview",
        retrieval_query="what is the material about",
        evidence_refs=prior_refs,
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence(source="materials/source-1.md"))

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        assert plan.retrieval_query is None
        assert plan.evidence_refs == prior_refs
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request=(
                    "Explain why the prior material overview is important for learning."
                ),
                is_followup=True,
                followup_target="prior material overview",
                answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
                retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
                retrieval_query="importance of the prior material overview",
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Those topics matter as foundations [E1]."),
                    TurnCompleteEvent(
                        "Those topics matter as foundations [E1].",
                        0,
                        1.0,
                        "stop",
                        100,
                    ),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("why is that important?"))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert plan.retrieval_query is None
    assert plan.evidence_refs == prior_refs
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert session.last_turn_contract.retrieval_query == ""


def test_followup_expansion_uses_most_specific_semantic_query() -> None:
    session = _session()
    session.config.base_url = "https://local.test/v1"
    session.config.model = "classifier"
    session.last_turn_contract = TurnContract(
        original_user_input="Give an example from the material.",
        resolved_intent="source_qa",
        canonical_request="Give an example of grounded answers from the material.",
        retrieval_query="grounded answers examples",
        evidence_refs=tuple(f"materials/source-{index}.md#chunk=0" for index in range(10)),
    )
    orchestrator = TurnOrchestrator(session)
    evidence = _turn_evidence(_evidence(source="materials/source-1.md"))

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="Compare the last two points from the previous explanation.",
                is_followup=True,
                followup_target=(
                    "the last two points in the prior assistant explanation about using "
                    "the smallest supporting phrase and forming a grounded answer"
                ),
                retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            ),
        ),
        patch.object(
            TurnOrchestrator,
            "_resolve_timed_turn_plan",
            side_effect=resolve,
        ) as resolved,
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Focused answer [E1]"),
                    TurnCompleteEvent("Focused answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        list(orchestrator.iter_events("Compare the last two points."))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert plan.retrieval_query is not None
    assert "smallest supporting phrase" in plan.retrieval_query
    assert _semantic_query_specificity(plan.retrieval_query) > _semantic_query_specificity(
        "Compare the last two points from the previous explanation."
    )


def test_expand_prior_evidence_merges_prior_refs_with_query_results() -> None:
    session = _session()
    prior_chunk = _chunk(
        "materials/procedure.md",
        0,
        "Read the source claim, locate the smallest supporting phrase, and cite it.",
    )
    query_chunk = _chunk(
        "materials/exams.md",
        0,
        "One expected task is to compare two source areas without inventing facts.",
    )
    index = _index(
        ChunkedDocument(
            source=prior_chunk.source,
            chunks=[prior_chunk],
            content_hash="procedure",
        ),
        ChunkedDocument(
            source=query_chunk.source,
            chunks=[query_chunk],
            content_hash="exams",
        ),
    )
    plan = replace(
        _plan(action=LearningAction.SOURCE_QA, retrieval_query="compare source areas"),
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("materials/procedure.md#chunk=0",),
    )

    with (
        patch("chat.evidence.ensure_rag_index", return_value=index),
        patch(
            "chat.evidence._retrieve_query_scored_chunks",
            return_value=MagicMock(scored=[ScoredChunk(query_chunk, 0.7)]),
        ),
    ):
        evidence = resolve_turn_evidence(session, plan)

    assert evidence is not None
    assert evidence_refs(evidence)[:2] == [
        "materials/exams.md#chunk=0",
        "materials/procedure.md#chunk=0",
    ]


def test_expand_prior_source_qa_filters_query_results_to_resolved_query() -> None:
    session = _session()
    prior_chunk = _chunk(
        "materials/procedure.md",
        0,
        "Read the source claim, locate the smallest supporting phrase, and cite it.",
    )
    relevant_query_chunk = _chunk(
        "materials/study.md",
        0,
        "Retrieval practice asks the learner to recall before rereading the source.",
    )
    adjacent_query_chunk = _chunk(
        "materials/history.md",
        0,
        "A public library example describes evening access after a budget review.",
    )
    index = _index(
        ChunkedDocument(
            source=prior_chunk.source,
            chunks=[prior_chunk],
            content_hash="procedure",
        ),
        ChunkedDocument(
            source=relevant_query_chunk.source,
            chunks=[relevant_query_chunk],
            content_hash="study",
        ),
        ChunkedDocument(
            source=adjacent_query_chunk.source,
            chunks=[adjacent_query_chunk],
            content_hash="history",
        ),
    )
    plan = replace(
        _plan(
            action=LearningAction.SOURCE_QA,
            retrieval_query="example of retrieval practice from the materials",
        ),
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("materials/procedure.md#chunk=0",),
    )

    with (
        patch("chat.evidence.ensure_rag_index", return_value=index),
        patch(
            "chat.evidence._retrieve_query_scored_chunks",
            return_value=MagicMock(
                scored=[
                    ScoredChunk(adjacent_query_chunk, 0.9),
                    ScoredChunk(relevant_query_chunk, 0.8),
                ]
            ),
        ),
    ):
        evidence = resolve_turn_evidence(session, plan)

    assert evidence is not None
    refs = evidence_refs(evidence)
    assert "materials/study.md#chunk=0" in refs
    assert "materials/procedure.md#chunk=0" in refs
    assert "materials/history.md#chunk=0" not in refs


def test_turn_evidence_filters_low_content_chunks_from_refs_and_overview() -> None:
    session = _session()
    content_chunk = _chunk(
        "materials/notes.md",
        0,
        "The source-backed point is explicitly stated here.",
    )
    boilerplate_chunk = _chunk(
        "materials/notes.md",
        1,
        "Copyright 2026. This line is non-answer boilerplate.",
    )
    index = _index(
        ChunkedDocument(
            source="materials/notes.md",
            chunks=[content_chunk, boilerplate_chunk],
            content_hash="notes",
        ),
    )

    with patch("chat.evidence.ensure_rag_index", return_value=index):
        from_refs = resolve_turn_evidence(
            session,
            replace(
                _plan(action=LearningAction.SOURCE_QA, retrieval_query=None),
                retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
                evidence_refs=("materials/notes.md#chunk=1", "materials/notes.md#chunk=0"),
            ),
        )
        overview = resolve_turn_evidence(
            session,
            material_overview_plan("what is the material about"),
        )

    assert evidence_refs(from_refs) == ["materials/notes.md#chunk=0"]
    assert evidence_refs(overview) == ["materials/notes.md#chunk=0"]


def test_overview_sampler_prefers_substantive_primary_material() -> None:
    session = _session()
    title_chunk = _chunk(
        "materials/lecture.md",
        0,
        "Course title\nAuthor Name\n2026",
    )
    concept_chunk = _chunk(
        "materials/lecture.md",
        1,
        (
            "Limits connect function behavior with continuity, examples, local change, "
            "and later derivative arguments."
        ),
    )
    exercise_chunk = _chunk(
        "materials/assignment.md",
        0,
        "Exercise 1. Submit a written solution. Exercise 2. Check each result.",
    )
    index = _index(
        ChunkedDocument(
            source="materials/assignment.md",
            chunks=[exercise_chunk],
            content_hash="assignment",
        ),
        ChunkedDocument(
            source="materials/lecture.md",
            chunks=[title_chunk, concept_chunk],
            content_hash="lecture",
        ),
    )

    with patch("chat.evidence.ensure_rag_index", return_value=index):
        overview = resolve_turn_evidence(
            session,
            material_overview_plan("what is the material about"),
        )

    assert overview is not None
    refs = evidence_refs(overview)
    assert refs[0] == "materials/lecture.md#chunk=1"
    assert refs.index("materials/lecture.md#chunk=1") < refs.index(
        "materials/assignment.md#chunk=0"
    )


def test_overview_sampler_prefers_early_structural_content_over_dense_logistics() -> None:
    session = _session()
    heading_chunk = _chunk("materials/lecture.md", 0, "Course overview")
    logistics_chunk = _chunk(
        "materials/lecture.md",
        1,
        (
            "The session meets on Monday from 09:15 to 10:45, with office hours, "
            "submission windows, registration details, and contact information."
        ),
    )
    concept_chunk = _chunk(
        "materials/lecture.md",
        2,
        (
            "Definition: a function f: X → Y maps each x ∈ X to one value in Y, "
            "which later supports examples and problem-solving steps."
        ),
    )
    index = _index(
        ChunkedDocument(
            source="materials/lecture.md",
            chunks=[heading_chunk, logistics_chunk, concept_chunk],
            content_hash="lecture",
        ),
    )

    with patch("chat.evidence.ensure_rag_index", return_value=index):
        overview = resolve_turn_evidence(
            session,
            material_overview_plan("what is the material about"),
        )

    assert overview is not None
    assert evidence_refs(overview) == ["materials/lecture.md#chunk=2"]


def test_overview_sampler_keeps_secondary_material_to_tail_when_primary_is_available() -> None:
    session = _session()
    primary_documents = tuple(
        ChunkedDocument(
            source=f"materials/lecture-{index}.md",
            chunks=[
                _chunk(
                    f"materials/lecture-{index}.md",
                    0,
                    (
                        "Definition and method notes connect concepts, examples, proofs, "
                        f"and problem-solving steps for topic {index}."
                    ),
                )
            ],
            content_hash=f"lecture-{index}",
        )
        for index in range(12)
    )
    secondary_document = ChunkedDocument(
        source="materials/assignment.md",
        chunks=[
            _chunk(
                "materials/assignment.md",
                0,
                "Exercise sheet. Submit answers and justify each calculation.",
            )
        ],
        content_hash="assignment",
    )
    index = _index(*primary_documents, secondary_document)

    with patch("chat.evidence.ensure_rag_index", return_value=index):
        overview = resolve_turn_evidence(
            session,
            material_overview_plan("what is the material about"),
        )

    assert overview is not None
    refs = evidence_refs(overview)
    assert len(refs) <= 10
    assert all("assignment" not in ref for ref in refs)


def test_material_overview_followup_reuses_prior_overview_refs_before_query_expansion() -> None:
    session = _session()
    prior_chunk = _chunk(
        "materials/overview.md",
        0,
        "Definitions and methods provide a stable overview of the material.",
    )
    query_chunk = _chunk(
        "materials/random.md",
        0,
        "A query result fragment should not displace the overview evidence.",
    )
    index = _index(
        ChunkedDocument(
            source=prior_chunk.source,
            chunks=[prior_chunk],
            content_hash="overview",
        ),
        ChunkedDocument(
            source=query_chunk.source,
            chunks=[query_chunk],
            content_hash="random",
        ),
    )
    plan = replace(
        material_overview_plan("What else stands out?"),
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="prior broad overview follow-up",
        evidence_refs=("materials/overview.md#chunk=0",),
    )

    with (
        patch("chat.evidence.ensure_rag_index", return_value=index),
        patch("chat.evidence._retrieve_query_scored_chunks") as retrieve_query,
    ):
        overview = resolve_turn_evidence(session, plan)

    retrieve_query.assert_not_called()
    assert overview is not None
    assert evidence_refs(overview) == ["materials/overview.md#chunk=0"]


def test_specific_present_turn_with_overview_strategy_uses_query_evidence() -> None:
    session = _session()
    query_evidence = _turn_evidence(
        _evidence(
            "E1",
            "materials/exercises.md",
            content="Exercises ask learners to prove, compute, and justify results.",
        )
    )
    overview_evidence = _turn_evidence(
        _evidence(
            "E1",
            "materials/overview.md",
            content="The corpus overview covers broad lecture topics.",
        )
    )
    plan = _plan(
        action=LearningAction.PRESENT,
        retrieval_query="specific exercise work",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
    )

    with (
        patch(
            "chat.evidence.build_turn_evidence_from_query",
            return_value=query_evidence,
        ) as query,
        patch(
            "chat.evidence.build_turn_evidence_from_overview",
            return_value=overview_evidence,
        ) as overview,
    ):
        evidence = resolve_turn_evidence(session, plan)

    query.assert_called_once_with(session, "specific exercise work")
    overview.assert_not_called()
    assert evidence is query_evidence


def test_followup_broad_planning_intent_continues_prior_material_intent() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="priority_request",
            canonical_request="Explain why the prior cited point matters.",
            is_followup=True,
        ),
        prior_intent="source_qa",
    )

    assert resolution.intent == "source_qa"
    assert resolution.canonical_request == "Explain why the prior cited point matters."


def test_reasoning_followup_continues_prior_material_intent() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="chat",
            canonical_request="Explain why the prior answer matters.",
            is_followup=True,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        ),
        prior_intent="material_overview",
    )

    assert resolution.intent == "material_overview"
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR


def test_reasoning_mode_sets_followup_when_classifier_omits_flag() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="topic_presentation",
            canonical_request="Explain why the prior material overview matters.",
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        ),
        prior_intent="material_overview",
    )

    assert resolution.intent == "material_overview"
    assert resolution.is_followup is True
    assert resolution.prior_answer_reference is True


def test_prior_reference_source_qa_without_direct_lookup_reasons_from_prior() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="source_qa",
            canonical_request="Explain the practical use of the prior answer.",
            is_followup=True,
            followup_target="the prior answer",
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
            retrieval_query="Explain the practical use of the prior answer.",
            prior_answer_reference=True,
            confidence=0.96,
        ),
        user_input="Explain the practical use of the prior answer.",
        prior_intent="material_overview",
    )

    assert resolution.intent == "material_overview"
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert resolution.retrieval_query == ""
    assert resolution.prior_answer_reference is True


def test_direct_evidence_contract_overrides_broad_classifier_intent() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="material_overview",
            canonical_request="Summarize the requested source-backed point.",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            direct_evidence_required=True,
            confidence=0.95,
        ),
        prior_intent="source_qa",
    )

    assert resolution.intent == "source_qa"
    assert resolution.retrieval_strategy == "retrieve"
    assert resolution.retrieval_query == "Summarize the requested source-backed point."


def test_material_overview_format_request_is_not_prior_transform_without_reference() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="material_overview",
            canonical_request="Create a compact table about the materials.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            answer_format=ANSWER_FORMAT_TABLE,
        ),
        prior_intent="topic_presentation",
    )

    assert resolution.answer_mode == "answer_from_evidence"
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert resolution.retrieval_query == "Create a compact table about the materials."


def test_material_overview_format_request_does_not_expand_prior_topic() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="material_overview",
            canonical_request="Create a compact table about the materials.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            answer_format=ANSWER_FORMAT_TABLE,
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="previous topic",
            prior_answer_reference=True,
        ),
        prior_intent="topic_presentation",
    )

    assert resolution.answer_mode == "answer_from_evidence"
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert resolution.retrieval_query == "previous topic"


def test_plain_prior_transform_continues_prior_material_intent() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="chat",
            canonical_request="Translate the prior answer.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            prior_answer_reference=True,
        ),
        prior_intent="material_overview",
    )

    assert resolution.intent == "material_overview"
    assert resolution.is_followup is True
    assert resolution.prior_answer_reference is True


def test_plain_transform_without_prior_anchor_becomes_current_evidence_request() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="material_overview",
            canonical_request="Summarize a different material area with evidence.",
            is_followup=True,
            followup_target="the prior overview",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        ),
        prior_intent="material_overview",
    )

    assert resolution.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    assert resolution.prior_answer_reference is False


def test_contract_specific_query_overrides_broad_overview_plan_query() -> None:
    plan = material_overview_plan("what is the material about")
    contract = TurnContract(
        original_user_input="Switch to the requested source and summarize it.",
        resolved_intent="material_overview",
        canonical_request="Summarize the requested source area.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="requested source area key idea",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("notes.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_query == "requested source area key idea"
    assert updated_contract.retrieval_query == "requested source area key idea"


def test_current_topic_query_overrides_inherited_followup_query() -> None:
    plan = replace(
        _plan(
            action=LearningAction.SOURCE_QA,
            retrieval_query="previously summarized calculus topics",
        ),
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    )
    contract = TurnContract(
        original_user_input="was ist l hospital?",
        resolved_intent="topic_presentation",
        canonical_request="Explain L'Hôpital's rule.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="previously summarized calculus topics",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="what is the material about?",
            evidence_refs=("overview.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == "retrieve"
    assert updated_plan.retrieval_query == "Explain L'Hôpital's rule."
    assert updated_contract.retrieval_strategy == "retrieve"
    assert updated_contract.retrieval_query == "Explain L'Hôpital's rule."


def test_current_topic_query_overrides_generic_followup_target_query() -> None:
    plan = replace(
        _plan(
            action=LearningAction.PRESENT,
            retrieval_query="the current topic change request from the prior turn",
        ),
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="Now switch to the requested method and explain the central rule.",
        resolved_intent="topic_presentation",
        canonical_request="Explain the central rule of the requested method.",
        is_followup=True,
        followup_target="the current topic change request from the prior turn",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="the current topic change request from the prior turn",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("topic.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert updated_plan.retrieval_query == "Explain the central rule of the requested method."
    assert updated_contract.retrieval_query == "Explain the central rule of the requested method."


def test_followup_query_prefers_nonliteral_surface_when_available() -> None:
    plan = replace(
        _plan(
            action=LearningAction.SOURCE_QA,
            retrieval_query="Ask one recall question grounded in the source.",
        ),
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="Ask one recall question grounded in the source.",
        resolved_intent="source_qa",
        canonical_request="Ask one recall question grounded in the source.",
        is_followup=True,
        followup_target="the source material from the prior turn",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="Ask one recall question grounded in the source.",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("topic.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_query == "the source material from the prior turn"
    assert updated_contract.retrieval_query == "the source material from the prior turn"


def test_specific_topic_contract_cannot_keep_overview_retrieval_strategy() -> None:
    plan = material_topic_presentation_plan(
        "Switch to the requested method and explain the central rule.",
        retrieval_query="Switch to the requested method and explain the central rule.",
    )
    contract = TurnContract(
        original_user_input="Switch to the requested method and explain the central rule.",
        resolved_intent="topic_presentation",
        canonical_request="Explain the central rule of the requested method.",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="Switch to the requested method and explain the central rule.",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert (
        updated_plan.retrieval_query
        == "Switch to the requested method and explain the central rule."
    )
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE


def test_material_overview_table_contract_forces_overview_scope_even_when_followup() -> None:
    plan = replace(
        material_overview_plan("create a table regarding the material"),
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="previous topic",
    )
    contract = TurnContract(
        original_user_input="create a table regarding the material",
        resolved_intent="material_overview",
        canonical_request="Create a compact table about the materials.",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        answer_format=ANSWER_FORMAT_TABLE,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="previous topic",
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="what was the prior topic?",
            evidence_refs=("topic.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert updated_contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_contract.retrieval_query == updated_plan.retrieval_query
    assert updated_contract.prior_answer_reference is False


def test_initial_material_overview_contract_forces_corpus_overview_sampling() -> None:
    plan = material_overview_plan("what is the material about")
    contract = TurnContract(
        original_user_input="what is the material about",
        resolved_intent="material_overview",
        canonical_request="Provide an overview of the material contents.",
        followup_target="none",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="Provide an overview of the material contents",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_contract.retrieval_query == updated_plan.retrieval_query


def test_blank_classifier_contract_defers_to_default_overview_plan() -> None:
    plan = material_overview_plan("what do you think about the material?")
    contract = TurnContract(
        original_user_input="what do you think about the material?",
        confidence=0.0,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert updated_contract.resolved_intent == "material_overview"
    assert (
        updated_contract.canonical_request
        == "Provide a compact overview of the material contents."
    )
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_contract.retrieval_query == updated_plan.retrieval_query


def test_blank_classifier_uses_default_overview_plan_request() -> None:
    user_input = "create a table regarding the material"
    plan = material_overview_plan(user_input, retrieval_query=user_input)
    contract = TurnContract(original_user_input=user_input, confidence=0.0)

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert updated_plan.retrieval_query == user_input
    assert (
        updated_contract.canonical_request
        == "Provide a compact overview of the material contents."
    )
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_contract.retrieval_query == user_input


def test_unicode_math_reply_converts_bare_mathbb_without_touching_paths() -> None:
    reply = r"Use a, b \in \mathbb R and see materials/Folien_2026_04_13.pdf."
    double_struck_r = "\u211d"

    converted = _unicode_math_reply(reply)

    assert f"a, b \\in {double_struck_r}" in converted
    assert "materials/Folien_2026_04_13.pdf" in converted


def test_blank_contract_intent_is_filled_from_final_plan() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="explain the procedure")
    contract = TurnContract(
        original_user_input="explain the procedure",
        canonical_request="Explain the procedure.",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="explain the procedure",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.action is LearningAction.SOURCE_QA
    assert updated_contract.resolved_intent == "source_qa"


def test_initial_plain_overview_contract_uses_neutral_canonical_request() -> None:
    plan = material_overview_plan("what do you think about the material?")
    contract = TurnContract(
        original_user_input="what do you think about the material?",
        resolved_intent="material_overview",
        canonical_request="Give an opinion about the material.",
        answer_format=ANSWER_FORMAT_PLAIN,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="material opinion and quality",
        confidence=0.95,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert (
        updated_contract.canonical_request
        == "Provide a compact overview of the material contents."
    )
    assert updated_contract.retrieval_query == updated_plan.retrieval_query


def test_initial_material_overview_ignores_classifier_followup_target_text() -> None:
    plan = material_overview_plan("what do you think about the material?")
    contract = TurnContract(
        original_user_input="what do you think about the material?",
        resolved_intent="material_overview",
        canonical_request="Give an overall assessment of the material.",
        is_followup=False,
        followup_target="the current material corpus",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="overall assessment and contents of the material corpus",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_plan.uses_overview_sampling is True
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert updated_contract.retrieval_query == updated_plan.retrieval_query


def test_overview_retrieval_strategy_uses_corpus_sampler_even_with_model_query() -> None:
    session = _session()
    plan = replace(
        material_overview_plan("what is the material about"),
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="Provide an overview of the material contents",
    )
    overview_evidence = _turn_evidence(
        _evidence(source="a.md", content="Topic A uses definitions."),
        _evidence("E2", "b.md", content="Topic B uses examples."),
    )

    with patch(
        "chat.evidence.build_turn_evidence_from_overview",
        return_value=overview_evidence,
    ) as overview:
        resolved = resolve_turn_evidence(session, plan)

    assert resolved is overview_evidence
    assert overview.called


def test_expand_prior_contract_preserves_direct_evidence_contract() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="requested detail")
    contract = TurnContract(
        original_user_input="Add one more detail.",
        resolved_intent="source_qa",
        canonical_request="Add one more cited detail from the prior source context.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="requested detail",
        direct_evidence_required=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("notes.md#chunk=0",),
        ),
    )

    assert updated_plan.requires_direct_evidence is True
    assert updated_contract.direct_evidence_required is True


def test_source_qa_contract_requires_direct_evidence_by_structure() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="explain the procedure")
    contract = TurnContract(
        original_user_input="explain the procedure",
        resolved_intent="source_qa",
        canonical_request="Explain the procedure.",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="explain the procedure",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.requires_direct_evidence is True
    assert updated_contract.direct_evidence_required is True


def test_prior_followup_without_direct_requirement_reasons_from_prior_evidence() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="real world application")
    contract = TurnContract(
        original_user_input="When would I use that outside class?",
        resolved_intent="source_qa",
        canonical_request="Explain the practical use of the prior cited topic.",
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="practical use of the prior cited topic",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Why is that important?",
            resolved_intent="source_qa",
            evidence_refs=("analysis.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert updated_plan.evidence_refs == ("analysis.md#chunk=0",)
    assert updated_plan.requires_direct_evidence is False
    assert updated_contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert updated_contract.prior_answer_reference is True


def test_reason_from_prior_contract_does_not_keep_exact_source_requirement() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="assumption behind claim")
    contract = TurnContract(
        original_user_input="What assumption is behind the second cited claim?",
        resolved_intent="source_qa",
        canonical_request="Explain the assumption behind the prior cited claim.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="assumption behind prior cited claim",
        direct_evidence_required=True,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Compare the cited claims.",
            resolved_intent="source_qa",
            evidence_refs=("analysis.md#chunk=0",),
        ),
    )

    assert updated_plan.requires_direct_evidence is False
    assert updated_contract.direct_evidence_required is False


def test_direct_prior_followup_keeps_exact_source_requirement() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="source location")
    contract = TurnContract(
        original_user_input="Which source says that?",
        resolved_intent="source_qa",
        canonical_request="Find the direct source for the prior claim.",
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="direct source for the prior claim",
        direct_evidence_required=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Explain the result.",
            resolved_intent="source_qa",
            evidence_refs=("analysis.md#chunk=0",),
        ),
    )

    assert updated_plan.requires_direct_evidence is True
    assert updated_contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    assert updated_contract.direct_evidence_required is True


def test_prior_answer_reference_expands_prior_evidence_for_direct_lookup() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="method source passage")
    contract = TurnContract(
        original_user_input="Where does the cited method claim come from?",
        resolved_intent="source_qa",
        canonical_request="Find the source for the method claim in the prior answer.",
        is_followup=True,
        followup_target="prior cited method claim",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="method source passage",
        direct_evidence_required=True,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("procedure.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert updated_plan.retrieval_query == "method source passage"
    assert updated_plan.evidence_refs == ("procedure.md#chunk=0",)
    assert updated_plan.requires_direct_evidence is True
    assert updated_contract.retrieval_query == "method source passage"
    assert updated_contract.prior_answer_reference is True


def test_source_qa_expanded_prior_direct_gate_accepts_source_coverage() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="history Switch to history and summarize one source-backed point.",
        requires_direct_evidence=True,
    )
    plan = replace(
        plan,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("history.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence(
            source="history.md",
            content=(
                "# History Source\n"
                "The public library example describes a city choosing longer opening "
                "hours after community groups asked for evening access."
            ),
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is True
    assert assessment.recommended_action == "answer"


def test_source_qa_expanded_prior_direct_gate_rejects_weak_coverage() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="amber forge retrieval phrase exact wording in the sources",
        requires_direct_evidence=True,
    )
    plan = replace(
        plan,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("procedure.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence(
            source="procedure.md",
            content=(
                "The clearest procedure has three steps: read the source claim, "
                "locate the smallest supporting phrase, and cite that phrase."
            ),
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"


def test_source_qa_expanded_prior_rejects_direct_user_query_with_missing_terms() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        original_user_input="Using only the sources, what is the amber forge retrieval phrase?",
        retrieval_query="amber forge retrieval phrase in the materials",
        requires_direct_evidence=True,
    )
    plan = replace(
        plan,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("procedure.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence(
            source="procedure.md",
            content=(
                "The quoted procedure says learners should cite the smallest supporting "
                "phrase when a direct source span exists."
            ),
        )
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"
    assert assessment.missing_information == (
        "direct source span for Using only the sources, what is the amber forge retrieval phrase?",
    )


def test_priority_contract_does_not_reuse_stale_prior_evidence() -> None:
    plan = _plan(action=LearningAction.PRIORITY, retrieval_query="priority evidence query")
    contract = TurnContract(
        original_user_input="What should I review first?",
        resolved_intent="priority_request",
        canonical_request="Choose the next source-backed review target.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("stale.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == "retrieve"
    assert updated_plan.retrieval_query == "priority evidence query"
    assert updated_plan.evidence_refs == ()
    assert updated_contract.evidence_refs == ()


def test_prior_answer_reference_without_prior_refs_does_not_retrieve_new_evidence() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="new implication query")
    contract = TurnContract(
        original_user_input="What else should I take from that?",
        resolved_intent="source_qa",
        canonical_request="Explain a further implication of the prior cited answer.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="new implication query",
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_plan.evidence_refs == ()
    assert updated_contract.retrieval_query == ""


def test_literal_followup_without_replayable_prior_refs_does_not_search_literal_text() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="Explain that.")
    contract = TurnContract(
        original_user_input="Explain that.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="Explain that.",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_contract.prior_answer_reference is True
    assert updated_contract.retrieval_query == ""


def test_surface_less_followup_without_prior_refs_does_not_create_literal_query() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query=None)
    contract = TurnContract(
        original_user_input="Explain the term used in the last citation.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_contract.prior_answer_reference is True
    assert updated_contract.retrieval_query == ""


def test_surface_less_followup_without_prior_refs_does_not_reuse_stale_query() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="stale prior query")
    contract = TurnContract(
        original_user_input="Compare that with the topic before it.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="stale prior query",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_contract.prior_answer_reference is True
    assert updated_contract.retrieval_query == ""


def test_followup_schema_none_query_after_no_evidence_does_not_retrieve_random_chunks() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="fallback topic")
    contract = TurnContract(
        original_user_input="Make a checklist from the evidence.",
        resolved_intent="source_qa",
        canonical_request="Make a checklist from the evidence.",
        is_followup=True,
        followup_target="the prior evidence-backed answer",
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        answer_format=ANSWER_FORMAT_LIST,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="none",
        citation_required=True,
        direct_evidence_required=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Which document explains the missing topic?",
            resolved_intent="source_qa",
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_contract.prior_answer_reference is True
    assert updated_contract.evidence_refs == ()


def test_specific_material_target_does_not_force_corpus_overview_sampling() -> None:
    plan = _plan(
        action=LearningAction.PRESENT,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="what is the material about",
    )
    contract = TurnContract(
        original_user_input="Switch topics and summarize the key idea from the source.",
        resolved_intent="material_overview",
        canonical_request="Summarize the key idea from the requested topic source.",
        followup_target="the requested topic source",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert (
        updated_plan.retrieval_query == "Summarize the key idea from the requested topic source."
    )
    assert updated_contract.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE


def test_direct_reuse_followup_marks_prior_answer_reference() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query=None)
    contract = TurnContract(
        original_user_input="Which citation supports that?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        direct_evidence_required=True,
    )

    _updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="prior request",
            evidence_refs=("source.md#chunk=0",),
        ),
    )

    assert updated_contract.prior_answer_reference is True


def test_deterministic_missing_index_reply_still_applies_classified_plan() -> None:
    session = _session()
    session.source_file_count = 1
    session.rag_index = None
    orchestrator = TurnOrchestrator(session)

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(intent="source_qa"),
        ),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("Where is compactness defined?"))

    assistant_text = "".join(
        event.delta for event in events if isinstance(event, AssistantDeltaEvent)
    )
    assert "no searchable evidence is indexed yet" in assistant_text
    assert session.last_plan_intent == ""
    assert session.learning_state.last_feedback_type is LearningFeedbackType.NONE


def test_learning_practice_context_reads_schedule_learner_state(tmp_path: Path) -> None:
    session = _session()
    session.armory_path = tmp_path
    store = load_recall_schedule(tmp_path)
    store.record_review(
        "Define compactness",
        concept="compactness",
        retrieval_query="compactness",
        source_refs=["notes.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=90,
        confidence=0.9,
        hint_level_needed=2,
        intervention="contrastive_question",
        exam_importance=0.8,
        now=datetime.now(UTC) - timedelta(days=2),
    )
    for _ in range(2):
        store.record_policy_outcome(
            "contrastive_question",
            success=True,
            mastery_delta=0.1,
            confidence_delta=0.1,
            time_cost_seconds=60,
        )
    store.save()

    due_reviews, memory_state = _learning_practice_context(session)

    assert due_reviews[0].item == "Define compactness"
    assert memory_state.weak_topics == ("compactness",)
    assert memory_state.misconceptions == ("compactness",)
    assert memory_state.successful_interventions == ("contrastive_question",)


def test_evidence_notice_and_metadata_expose_retrieval_details() -> None:
    session = _session()
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(_evidence("E1"), _evidence("E2", "other.md", 1))
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=assess_turn_evidence(plan, evidence),
    )

    notice = _evidence_notice(resolved)
    metadata = _evidence_notice_metadata(resolved, session)

    assert "Using 2 retrieved evidence excerpts" in notice
    assert metadata["task"] == "source-qa"
    assert metadata["refs"] == ["notes.md#chunk=0", "other.md#chunk=1"]
    assessment = metadata["assessment"]

    assert is_string_mapping(assessment)
    assert assessment["sufficient"] is True


def test_evidence_notice_summarizes_overview_sources_and_hides_calibration() -> None:
    overview = ResolvedTurnPlan(
        learning_plan=material_overview_plan("overview"),
        turn_evidence=_turn_evidence(
            _evidence(source="a.md"), _evidence("E2", "b.md", 0), sampled=2, total=5
        ),
    )
    calibration = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.CALIBRATE),
        turn_evidence=_turn_evidence(_evidence()),
    )

    assert "from 2 of 5 indexed sources" in _evidence_notice(overview)
    assert _evidence_notice(calibration) == ""
    assert _evidence_notice_metadata(calibration) == {}


def test_calibration_evidence_is_stored_without_visible_notice() -> None:
    evidence = _turn_evidence(_evidence(content="The source-backed recall fact."))
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.CALIBRATE),
        turn_evidence=evidence,
    )

    assert _stored_turn_evidence(resolved) is evidence
    assert _evidence_notice(resolved) == ""


def test_missing_indexed_material_reply_reports_index_states() -> None:
    session = _session()
    session.source_file_count = 1
    plan = _plan(action=LearningAction.SOURCE_QA)

    session.rag_index = None
    assert "could not prepare the searchable materials index" in _missing_indexed_material_reply(
        session, plan.action
    )

    session.rag_index = _index()
    assert "no searchable evidence" in _missing_indexed_material_reply(session, plan.action)

    session.rag_index = _index(_document())
    session.disabled_source_files = {"notes.md"}
    assert "all indexed material" in _missing_indexed_material_reply(session, plan.action)

    session.disabled_source_files = set()
    assert _missing_indexed_material_reply(session, plan.action) == ""


def test_no_matching_indexed_evidence_reply_reports_ready_index_without_recreating_detection() -> (
    None
):
    session = _session()
    session.source_file_count = 1
    session.rag_index = _index(_document())

    reply = _no_matching_indexed_evidence_reply(
        session, _plan(action=LearningAction.SOURCE_QA, retrieval_query="compactness")
    )

    assert "did not retrieve matching evidence" in reply
    assert "compactness" in reply


def test_no_matching_indexed_evidence_reply_reports_resolved_request() -> None:
    session = _session()
    session.source_file_count = 1
    session.rag_index = _index(_document())
    contract = TurnContract(
        original_user_input="auf deutsch",
        resolved_intent="material_overview",
        canonical_request="Translate the prior material overview into German.",
        is_followup=True,
        followup_target="prior material overview answer",
    )

    reply = _no_matching_indexed_evidence_reply(
        session,
        _plan(
            action=LearningAction.SOURCE_QA,
            retrieval_query="the previous overview of the materials and their topics",
        ),
        contract,
    )

    assert "Translate the prior material overview into German." in reply
    assert "the previous overview of the materials and their topics" in reply
    assert "resolved request" in reply


def test_assess_turn_evidence_flags_weak_source_only_support() -> None:
    assessment = assess_turn_evidence(
        _plan(action=LearningAction.SOURCE_QA, retrieval_query=None),
        _turn_evidence(_evidence()),
    )

    assert assessment.sufficient is False
    assert assessment.recommended_action == "give_partial_answer"
    assert "corroborating source span" in assessment.missing_information
    assert evidence_assessment_trace(assessment)["recommended_action"] == "give_partial_answer"


def test_overview_fallback_reply_uses_model_repair_with_citations() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(_evidence(content="Main topic is compactness."))

    model_reply = (
        "These notes describe compactness through open cover conditions and related "
        "topological consequences, using the first sampled passage as grounded support [E1]. "
        "They also connect the definition to proof obligations and examples cited in the "
        "same extracted material [E1]."
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=model_reply):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == model_reply


def test_overview_fallback_compacts_rejected_citation_inventory_before_model_repair() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} connects definitions with examples and tasks.",
            )
            for index in range(1, 11)
        ),
        sampled=10,
        total=10,
    )
    rejected_reply = (
        "These materials cover definitions, methods, worked examples, review tasks, and "
        "problem-solving procedures across the sampled sources, with enough visible detail "
        "to describe the corpus as a compact cited overview "
        + "".join(f"[E{index}]" for index in range(1, 11))
        + "."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(),
            rejected_reply=rejected_reply,
        )

    repair_model.assert_not_called()
    assert reply.startswith("These materials cover definitions")
    assert reply.count("[E") <= 5
    assert "[E1]" in reply
    assert "[E10]" in reply


def test_overview_fallback_compacts_comma_separated_citation_inventory() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} connects definitions with examples and tasks.",
            )
            for index in range(1, 11)
        ),
        sampled=10,
        total=10,
    )
    rejected_reply = (
        "These materials cover definitions, methods, examples, tasks, and procedures "
        "across several sampled sources, so the corpus can be described as a compact "
        "source-grounded overview (" + ", ".join(f"[E{index}]" for index in range(1, 11)) + ")."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(),
            rejected_reply=rejected_reply,
        )

    repair_model.assert_not_called()
    assert reply.startswith("These materials cover definitions")
    assert reply.count("[E") <= 5
    assert ", [E" not in reply


def test_overview_shape_guard_accepts_bracketed_citation_groups() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "source-1.md", content="Topic one connects definitions to examples."),
        _evidence("E2", "source-2.md", content="Topic two explains problem-solving methods."),
        sampled=2,
        total=2,
    )
    reply = (
        "These sampled materials connect definitions to examples in one source and "
        "problem-solving methods in another source, giving a compact source-grounded "
        "overview of the two-part corpus [E1, E2]."
    )

    assert _needs_overview_fallback(plan, reply, evidence) is False


def test_overview_model_fallback_trims_long_cited_synthesis_block() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} gives a grounded concept or method.",
            )
            for index in range(1, 11)
        ),
        sampled=10,
        total=10,
    )
    model_reply = (
        "The material moves from core definitions and notation into examples, methods, "
        "and problem types, so it reads as a cumulative technical corpus "
        "[E1, E2, E3, E4, E5, E6, E7, E8, E9, E10].\n\n"
        "It also includes additional commentary that is useful but too long for a compact "
        "terminal answer [E1, E2, E3, E4]."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value=model_reply,
    ):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what do you think about the material?",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply="Too thin [E1].",
        )

    assert "additional commentary" not in reply
    assert reply.count("[E") == 5
    assert _needs_overview_fallback(plan, reply, evidence) is False


def test_overview_fallback_replaces_multi_group_inventory_with_evidence_cues() -> None:
    plan = material_overview_plan("overview")
    contents = (
        "Sequences are defined as maps from natural numbers into a set.",
        "Series are introduced through partial sums and convergence.",
        "Limits use epsilon-delta conditions for real functions.",
        "Continuity is stated by equality with the function limit.",
        "Derivatives are connected to tangents and differentiability.",
        "L'Hospital-style limits compare derivatives of two functions.",
        "Local extrema are defined with a neighborhood condition.",
        "Curve analysis exercises ask for monotonicity and extrema.",
    )
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=content,
            )
            for index, content in enumerate(contents, start=1)
        ),
        sampled=8,
        total=8,
    )
    rejected_reply = (
        "The material appears to be a broad course package with unsupported synthesis "
        "[E1][E2][E3][E4]. It also suggests a broad progression across the corpus "
        "[E5][E6][E7][E8]."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply=rejected_reply,
        )

    assert repair_model.call_count >= 1
    assert reply == ""


def test_overview_fallback_trims_long_rejected_citation_inventory_before_model_repair() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} connects definitions with examples and tasks.",
            )
            for index in range(1, 11)
        ),
        sampled=10,
        total=10,
    )
    rejected_reply = (
        "These materials cover definitions, methods, worked examples, review tasks, "
        "problem-solving procedures, and source-backed practice across the sampled corpus. "
        + "Additional visible detail is repeated to make this draft too long. " * 16
        + "".join(f"[E{index}]" for index in range(1, 11))
        + "."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply=rejected_reply,
        )

    repair_model.assert_not_called()
    assert reply.count("Additional visible detail") < rejected_reply.count(
        "Additional visible detail"
    )
    assert len(reply) <= 700
    assert 2 <= reply.count("[E") <= 5
    assert "[E1]" in reply
    assert "[E10]" in reply


def test_overview_fallback_keeps_leading_synthesis_when_rejected_draft_has_bullets() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} connects definitions with examples and tasks.",
            )
            for index in range(1, 13)
        ),
        sampled=12,
        total=12,
    )
    rejected_reply = (
        "These materials cover definitions, methods, worked examples, review tasks, and "
        "problem-solving procedures across the sampled corpus, giving enough evidence for "
        "a concise corpus-level answer without needing the later per-section inventory "
        + "".join(f"[E{index}]" for index in range(1, 13))
        + ".\n\n"
        "- Early excerpts introduce the first group of concepts with repeated explanatory "
        "detail that makes the draft too long [E1][E2][E3][E4].\n"
        "- Later excerpts add follow-on methods and applications with repeated explanatory "
        "detail that makes the draft too long [E5][E6][E7][E8].\n"
        "- Practice excerpts ask students to apply the material with repeated explanatory "
        "detail that makes the draft too long [E9][E10][E11][E12]."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply=rejected_reply,
        )

    repair_model.assert_not_called()
    assert reply.startswith("These materials cover definitions")
    assert "- Early excerpts" not in reply
    assert len(reply) <= 700
    assert 2 <= reply.count("[E") <= 5
    assert "[E1]" in reply
    assert "[E12]" in reply


def test_overview_table_fallback_trims_table_block_instead_of_preamble() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        *(
            _evidence(
                f"E{index}",
                f"source-{index}.md",
                content=f"Topic {index} connects definitions with examples and tasks.",
            )
            for index in range(1, 13)
        ),
        sampled=12,
        total=12,
    )
    contract = TurnContract(
        original_user_input="create a table regarding the material",
        resolved_intent="material_overview",
        canonical_request="Create a table about the materials.",
        answer_format=ANSWER_FORMAT_TABLE,
    )
    rejected_reply = (
        "Here is a compact table "
        + "".join(f"[E{index}]" for index in range(1, 13))
        + ".\n\n| Material | Topic |\n|---|---|\n"
        + "\n".join(f"| Source {index} | Topic {index} [E{index}] |" for index in range(1, 13))
        + "\n\n- Extra inventory [E1][E2][E3]."
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="create a table regarding the material",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply=rejected_reply,
            contract=contract,
        )

    repair_model.assert_not_called()
    assert reply.startswith("| Material | Topic |")
    assert "Here is a compact table" not in reply
    assert "Extra inventory" not in reply
    assert reply.count("\n|") <= 7
    assert 2 <= reply.count("[E") <= 8


def test_overview_table_fallback_splits_collapsed_pipe_table() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "source-1.md", content="Sequences use limits and convergence tests."),
        _evidence("E2", "source-2.md", content="Series are checked for convergence."),
        _evidence("E3", "source-3.md", content="Continuity is checked with limits."),
        sampled=3,
        total=3,
    )
    contract = TurnContract(
        original_user_input="create a table regarding the material",
        resolved_intent="material_overview",
        canonical_request="Create a table about the materials.",
        answer_format=ANSWER_FORMAT_TABLE,
    )
    rejected_reply = (
        "| Topic | Content | |---|---| | Sequences | Limits and convergence tests [E1] | "
        "| Series | Convergence checks [E2] | | Continuity | Limits and continuity [E3] |"
    )

    with patch(
        "chat.model_text._stream_one_shot_model_text",
        return_value="",
    ) as repair_model:
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="create a table regarding the material",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            rejected_reply=rejected_reply,
            contract=contract,
        )

    repair_model.assert_not_called()
    assert reply.startswith("| Topic | Content |\n| --- | --- |")
    assert "| Sequences | Limits and convergence tests [E1] |" in reply
    assert "| Series | Convergence checks [E2] |" in reply
    assert "| Continuity | Limits and continuity [E3] |" in reply


def test_overview_fallback_uses_deterministic_reply_when_model_repair_fails() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Main topic is compactness."),
        _evidence("E2", "examples.md", content="Examples connect the definition to proofs."),
        sampled=2,
        total=5,
    )

    with patch("chat.model_text._model_json_payload", return_value={"answer": "uncited"}):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_fallback_skips_title_metadata_for_substantive_cues() -> None:
    plan = material_overview_plan("what is the material about")
    evidence = _turn_evidence(
        _evidence(
            content=("Mathematics for Computer Science 2\nUniversity Example\n13 April 2026\n")
        ),
        _evidence(
            "E2",
            "lecture.md",
            content="Number systems and elementary functions are introduced as foundations.",
        ),
        sampled=2,
        total=2,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what is the material about",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_fallback_skips_byline_and_symbolic_fragments() -> None:
    plan = material_overview_plan("what is the material about")
    evidence = _turn_evidence(
        _evidence(
            content=(
                "Ada Lovelace Grace Hopper Alan Turing\n"
                "The notes introduce sequence convergence as a recurring method."
            ),
        ),
        _evidence(
            "E2",
            "formulas.md",
            content=(
                "| f(x) - c | < epsilon\nFunction limits are used to reason about continuity."
            ),
        ),
        _evidence(
            "E3",
            "series.md",
            content="Series examples connect partial sums with convergence tests.",
        ),
        _evidence(
            "E4",
            "derivatives.md",
            content="Derivatives support local approximation and critical-point analysis.",
        ),
        sampled=4,
        total=4,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what is the material about",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_fallback_prefers_primary_material_over_secondary_tasks() -> None:
    plan = material_overview_plan("what is the material about")
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "materials/exam.md",
            content=(
                "Question 1. Mark each page with the problem number. "
                "Question 2. Solve the listed exercises."
            ),
        ),
        _evidence(
            "E2",
            "materials/lecture-a.md",
            content="Sequences are introduced as ordered objects for convergence examples.",
        ),
        _evidence(
            "E3",
            "materials/lecture-b.md",
            content="Limits connect function behavior with continuity arguments.",
        ),
        _evidence(
            "E4",
            "materials/assignment.md",
            content="Exercise 1. Submit a written solution. Exercise 2. Check each result.",
        ),
        sampled=4,
        total=4,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what is the material about",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_fallback_skips_clipped_sentence_fragments() -> None:
    plan = material_overview_plan("what is the material about")
    evidence = _turn_evidence(
        _evidence(
            content=(
                "is a clipped continuation from an extracted paragraph.\n"
                "A complete concept sentence explains convergence through examples."
            ),
        ),
        _evidence(
            "E2",
            "limits.md",
            content=("Sei x in an interval, then the expression continues without a finite verb"),
        ),
        _evidence(
            "E3",
            "derivatives.md",
            content="Derivatives connect tangent-line approximations with local change.",
        ),
        sampled=3,
        total=3,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what is the material about",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_table_request_uses_table_fallback_instead_of_failure_notice() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Topic A connects definitions to examples."),
        _evidence("E2", "b.md", content="Topic B covers problem-solving procedures."),
        sampled=2,
        total=2,
    )
    contract = TurnContract(
        original_user_input="create a table regarding the material",
        resolved_intent="material_overview",
        canonical_request="Create a compact table about the material corpus.",
        answer_format=ANSWER_FORMAT_TABLE,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="create a table regarding the material",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            contract=contract,
        )

    assert "| Source | Grounded excerpt |" in reply
    assert "Topic A connects definitions to examples. [E1]" in reply
    assert "not reliable enough to show" not in reply


def test_overview_list_request_uses_list_fallback_instead_of_prose() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Topic A connects definitions to examples."),
        _evidence("E2", "b.md", content="Topic B covers problem-solving procedures."),
        sampled=2,
        total=2,
    )
    contract = TurnContract(
        original_user_input="make a checklist from the source evidence",
        resolved_intent="material_overview",
        canonical_request="Create a compact checklist from the material evidence.",
        answer_format=ANSWER_FORMAT_LIST,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="make a checklist from the source evidence",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
            contract=contract,
        )

    assert reply.startswith("1. Topic A connects definitions to examples. [E1]")
    assert "\n2. Topic B covers problem-solving procedures. [E2]" in reply
    assert "Visible material:" not in reply


def test_material_overview_contract_uses_overview_shape_guard_for_continuations() -> None:
    plan = _plan(
        action=LearningAction.PRESENT,
        retrieval_query="the prior broad overview of the materials corpus",
    )
    evidence = _turn_evidence(
        _evidence(content="Topic A"),
        _evidence("E2", "b.md", content="Topic B"),
        sampled=2,
        total=2,
    )
    contract = TurnContract(
        original_user_input="Go on.",
        resolved_intent="material_overview",
        canonical_request="Continue the overview of the materials.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
    )
    long_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. " + "Extra detail. " * 220
    )

    assert _needs_overview_fallback(plan, long_reply, evidence, contract=contract) is True


def test_material_overview_transform_followup_skips_overview_shape_guard() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Topic A"),
        _evidence("E2", "b.md", content="Topic B"),
        sampled=2,
        total=2,
    )
    contract = TurnContract(
        original_user_input="Add one concise cited detail.",
        resolved_intent="material_overview",
        canonical_request="Add one concise cited detail to the prior overview.",
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )

    assert _needs_overview_fallback(plan, "Topic A [E1].", evidence, contract=contract) is False


def test_overview_fallback_needed_for_bad_shape() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Topic A"),
        _evidence("E2", "b.md", content="Topic B"),
        sampled=2,
        total=2,
    )

    assert _needs_overview_fallback(plan, "One vague sentence [E1].", evidence) is True
    long_reply = " ".join(("supported",) * 161) + " [E1][E2]."
    assert _needs_overview_fallback(plan, long_reply, evidence) is True
    oversized_char_reply = (
        "These materials discuss Topic A [E1] and Topic B [E2]. " + "Detail. " * 120
    )
    assert _needs_overview_fallback(plan, oversized_char_reply, evidence) is True
    table_reply = "| Topic | Detail |\n|---|---|\n| A | Topic A [E1] |\n| B | Topic B [E2] |\n"
    assert _needs_overview_fallback(plan, table_reply, evidence) is False
    oversized_table_reply = "| Topic | Detail |\n|---|---|\n" + "\n".join(
        f"| Item {index} | Topic A [E1] and Topic B [E2] |" for index in range(9)
    )
    assert _needs_overview_fallback(plan, oversized_table_reply, evidence) is True
    uncited_tail_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. "
        "Detached next-step prose is not part of the grounded answer."
    )
    assert _needs_overview_fallback(plan, uncited_tail_reply, evidence) is True
    citation_dense_reply = (
        "These materials discuss Topic A with direct evidence from the first source "
        "[E1][E1][E1][E1][E1] and Topic B with direct evidence from the second source "
        "[E2][E2][E2][E2]."
    )
    assert _needs_overview_fallback(plan, citation_dense_reply, evidence) is True
    clipped_fragment_reply = (
        "is introduced as an unsupported sentence fragment [E1]. "
        "Topic B is still cited clearly [E2]."
    )
    assert _needs_overview_fallback(plan, clipped_fragment_reply, evidence) is True
    copied_inventory_reply = (
        "Topic A connects definitions to examples [E1]. "
        "Topic B covers problem-solving procedures [E2]."
    )
    assert _needs_overview_fallback(plan, copied_inventory_reply, evidence) is True
    long_uncited_lead_reply = (
        "This overview makes a broad synthesized assessment across many sampled sources before "
        "it supplies any citation, which leaves too much interpretive material outside the "
        "immediate source surface and should be compacted into evidence cues [E1][E2]."
    )
    assert _needs_overview_fallback(plan, long_uncited_lead_reply, evidence) is True
    contract = TurnContract(
        original_user_input="create a table about the material",
        answer_format=ANSWER_FORMAT_TABLE,
    )
    assert _needs_overview_fallback(plan, table_reply, evidence, contract=contract) is False
    requested_table = "| Topic | Detail |\n|---|---|\n" + "\n".join(
        (
            f"| Item {index} | Topic A with enough cited table detail [E1] and Topic B "
            "with additional concise source-backed context [E2] |"
        )
        for index in range(6)
    )
    assert len(requested_table) > 700
    assert _needs_overview_fallback(plan, requested_table, evidence, contract=contract) is False
    long_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. " + "Extra detail. " * 220
    )
    assert _needs_overview_fallback(plan, long_reply, evidence) is True
    good_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. Together, the "
        "sampled excerpts support a cautious multi-source overview without adding claims "
        "[E1][E2]."
    )

    assert _needs_overview_fallback(plan, good_reply, evidence) is False


def test_overview_shape_guard_requires_proportional_source_coverage() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "a.md", content="Topic A connects definitions to examples."),
        _evidence("E2", "b.md", content="Topic B covers problem-solving procedures."),
        _evidence("E3", "c.md", content="Topic C explains a formula relationship."),
        _evidence("E4", "d.md", content="Topic D gives a historical case."),
        _evidence("E5", "e.md", content="Topic E asks for a cited answer."),
        _evidence("E6", "f.md", content="Topic F asks for feedback after recall."),
        sampled=6,
        total=6,
    )
    narrow_reply = (
        "Topic A connects definitions to examples [E1], and Topic B has procedures [E2]."
    )
    covered_reply = (
        "Topic A connects definitions to examples, Topic B covers procedures, and Topic C "
        "explains a formula relationship. Together these excerpts provide a concise "
        "source-grounded overview of the sampled material [E1][E2][E3]."
    )

    assert _needs_overview_fallback(plan, narrow_reply, evidence) is True
    assert _needs_overview_fallback(plan, covered_reply, evidence) is False


def test_overview_deterministic_fallback_covers_representative_source_slice() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "a.md", content="Topic A connects definitions to examples."),
        _evidence("E2", "b.md", content="Topic B covers problem-solving procedures."),
        _evidence("E3", "c.md", content="Topic C explains a formula relationship."),
        _evidence("E4", "d.md", content="Topic D gives a historical case."),
        _evidence("E5", "e.md", content="Topic E asks for a cited answer."),
        _evidence("E6", "f.md", content="Topic F asks for feedback after recall."),
        sampled=6,
        total=6,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_deterministic_fallback_skips_repeated_cross_source_cues() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "a.md", content="Repeated corpus marker."),
        _evidence("E2", "b.md", content="Repeated corpus marker."),
        _evidence("E3", "c.md", content="Unique source content explains a task."),
        sampled=3,
        total=3,
    )

    with patch("chat.model_text._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == ""


def test_overview_fallback_uses_substantive_content_not_heading_inventory() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(
            content=(
                "# Contents\n"
                "Topic Alpha\n"
                "Topic Beta\n"
                "The first source explains how learners match claims to supporting evidence."
            ),
        ),
        _evidence(
            "E2",
            "b.md",
            content=(
                "# Index\n"
                "Topic Gamma\n"
                "The second source explains why examples should stay tied to cited material."
            ),
        ),
        sampled=2,
        total=2,
    )

    reply = _overview_fallback_reply(plan, evidence)

    assert reply == ""


def test_localize_deterministic_reply_rejects_added_citations_and_preserves_original() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="localizer")

    with patch(
        "chat.reply_text.stream_completion",
        return_value=iter([CompletionDelta(content="Übersetzt [E99]")]),
    ):
        reply = _localize_deterministic_reply(
            "Original fallback", user_input="auf Deutsch", config=config
        )

    assert reply == "Original fallback"


def test_user_visible_reply_strips_control_markup_and_unsolicited_followup() -> None:
    source_plan = _plan(action=LearningAction.SOURCE_QA)
    chat_plan = _plan(action=LearningAction.CHAT, retrieval_query=None)

    assert (
        _user_visible_reply(source_plan, "Answer [E1]. Say ready when you want recall.")
        == "Answer [E1]."
    )
    assert _user_visible_reply(chat_plan, '<tool_call name="x">hidden</tool_call>Hello') == "Hello"


def test_source_visible_reply_strips_uncited_tail_after_cited_answer() -> None:
    source_plan = _plan(action=LearningAction.SOURCE_QA)
    reply = (
        "The material prioritizes limits and continuity [E1].\n\n"
        "Detached trailing sentence with no citation."
    )

    assert (
        _user_visible_reply(source_plan, reply)
        == "The material prioritizes limits and continuity [E1]."
    )


def test_overview_visible_reply_preserves_full_draft_for_shape_validation() -> None:
    plan = material_overview_plan("what do you think about the material")
    reply = (
        "- First visible outline point [E1]\n\n"
        "This longer uncited section should still be visible to the overview shape guard "
        "instead of being silently clipped before validation."
    )

    assert _user_visible_reply(plan, reply) == reply


def test_internal_repair_expands_citation_only_answer() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(content="The procedure says to locate the smallest supporting phrase.")
    )
    config = ChatConfig(base_url="https://local.test/v1", model="repair")

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "[E1]",
        evidence,
        user_input="what does it say?",
        config=config,
    )

    assert (
        repaired
        == "Check [E1]: “The procedure says to locate the smallest supporting phrase.” [E1]."
    )


def test_internal_repair_expands_thin_source_pointer() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(
            "E3",
            content=(
                "# Procedure\n"
                "The source claim should be matched to the smallest supporting phrase."
            ),
        )
    )
    config = ChatConfig(base_url="https://local.test/v1", model="repair")

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "The last answer is supported by [E3],",
        evidence,
        user_input="Which citation supports the last answer?",
        config=config,
    )

    assert repaired == (
        "Check [E3]: “The source claim should be matched to the smallest supporting phrase.” [E3]."
    )


def test_internal_repair_replaces_thin_source_pointer_with_top_evidence() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence("E1", content="The procedure gives a directly relevant support phrase."),
        _evidence("E2", content="An unrelated adjacent note."),
    )
    config = ChatConfig(base_url="https://local.test/v1", model="repair")

    with patch(
        "chat.model_text.stream_completion",
        return_value=iter(
            [
                CompletionDelta(
                    content="The procedure gives a directly relevant support phrase [E1]."
                )
            ]
        ),
    ):
        repaired, _passes = _run_bounded_internal_repairs(
            plan,
            "The comparison is backed by **[E2]",
            evidence,
            user_input="which source supports it?",
            config=config,
        )

    assert repaired == "The procedure gives a directly relevant support phrase [E1]."


def test_internal_repair_expands_table_to_cover_multiple_evidence_sources() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "first.md",
            content="# First Source\nThe first source provides one visible grounded point.",
        ),
        _evidence(
            "E2",
            "second.md",
            content="# Second Source\nThe second source provides another visible grounded point.",
        ),
    )
    contract = TurnContract(
        original_user_input="Put this in a table.",
        resolved_intent="source_qa",
        canonical_request="Represent the current source-backed answer as a table.",
        answer_format=ANSWER_FORMAT_TABLE,
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "| Source | Point |\n|---|---|\n| first.md | One visible grounded point [E1] |",
        evidence,
        user_input="Put this in a table.",
        config=ChatConfig(),
        contract=contract,
    )

    assert "first.md" in repaired
    assert "second.md" in repaired
    assert "[E1]" in repaired
    assert "[E2]" in repaired


def test_internal_table_repair_keeps_single_source_table_when_only_one_source_available() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "first.md",
            content="# First Source\nThe first source provides one visible grounded point.",
        )
    )
    reply = "| Source | Point |\n|---|---|\n| first.md | One visible grounded point [E1] |"
    contract = TurnContract(
        original_user_input="Put this in a table.",
        resolved_intent="source_qa",
        canonical_request="Represent the current source-backed answer as a table.",
        answer_format=ANSWER_FORMAT_TABLE,
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        reply,
        evidence,
        user_input="Put this in a table.",
        config=ChatConfig(),
        contract=contract,
    )

    assert repaired == reply


def test_internal_table_repair_preserves_markdown_table_shape_when_long() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "first.md",
            content="# First Source\nThe first source provides one visible grounded point.",
        ),
        _evidence(
            "E2",
            "second.md",
            content="# Second Source\nThe second source provides another visible grounded point.",
        ),
    )
    row_text = (
        "One compact but still descriptive source-backed table cell with enough plain text "
        "to exceed the generic prose compaction threshold."
    )
    reply = "| Source | Point |\n|---|---|\n" + "\n".join(
        (
            f"| first.md | {row_text} [E1] |",
            f"| second.md | {row_text} [E2] |",
            f"| first.md | {row_text} [E1] |",
            f"| second.md | {row_text} [E2] |",
            f"| first.md | {row_text} [E1] |",
            f"| second.md | {row_text} [E2] |",
        )
    )
    assert len(reply) > 700
    contract = TurnContract(
        original_user_input="Put this in a table.",
        resolved_intent="source_qa",
        canonical_request="Represent the current source-backed answer as a table.",
        answer_format=ANSWER_FORMAT_TABLE,
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        reply,
        evidence,
        user_input="Put this in a table.",
        config=ChatConfig(),
        contract=contract,
    )

    assert repaired == reply
    assert "|---|---|" in repaired


def test_source_qa_user_visible_reply_keeps_cited_active_recall_content() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)

    reply = _user_visible_reply(plan, "The source asks an active recall question [E1].")

    assert reply == "The source asks an active recall question [E1]."


def test_source_qa_user_visible_reply_normalizes_escaped_citation_brackets() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)

    reply = _user_visible_reply(plan, r"The source says this \[E1\].")

    assert reply == "The source says this [E1]."


def test_source_qa_user_visible_reply_normalizes_private_use_citation_markup() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)

    reply = _user_visible_reply(plan, "The source says this \ue200cite:E1\ue201.")

    assert reply == "The source says this [E1]."


def test_source_qa_user_visible_reply_normalizes_private_use_citation_event_markup() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)

    reply = _user_visible_reply(plan, "The source says this \ue200cite\ue202E1\ue201.")

    assert reply == "The source says this [E1]."


def test_source_grounded_agent_request_keeps_compact_prior_context() -> None:
    session = _session()
    session.conversation.add("user", "previous question")
    session.conversation.add("assistant", "Previous answer with stale citation [E1].")
    contract = TurnContract(
        original_user_input="What does the source say?",
        resolved_intent="source_qa",
        canonical_request="Answer from the current retrieved evidence.",
        is_followup=True,
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.SOURCE_QA),
        LearningState(),
        "What does the source say?",
        session,
        contract,
    )

    assert [message.role for message in request.conversation.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert request.conversation.messages[1].content == "Previous answer with stale citation."
    assert request.conversation.messages[-1].content == "What does the source say?"


def test_material_review_agent_request_keeps_compact_prior_context() -> None:
    session = _session()
    session.conversation.add("user", "previous question")
    session.conversation.add("assistant", "Previous answer with stale citation [E1].")
    contract = TurnContract(
        original_user_input="Make a learning checklist from the evidence.",
        resolved_intent="topic_presentation",
        canonical_request="Create a checklist from the current retrieved evidence.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.REVIEW),
        LearningState(),
        "Make a learning checklist from the evidence.",
        session,
        contract,
    )

    assert [message.role for message in request.conversation.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert "stale citation" in request.conversation.messages[1].content
    assert "prior E" not in request.conversation.messages[1].content
    assert request.conversation.messages[-1].content == (
        "Make a learning checklist from the evidence."
    )


def test_calibration_agent_request_isolates_stale_topic_history() -> None:
    session = _session()
    session.conversation.add("user", "old quiz")
    session.conversation.add("assistant", "What does an older unrelated rule require? [E1]")
    contract = TurnContract(
        original_user_input="Quiz me with one source-backed recall prompt.",
        resolved_intent="topic_drill",
        canonical_request="Ask one source-backed recall prompt.",
        is_followup=True,
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.CALIBRATE),
        LearningState(),
        "Quiz me with one source-backed recall prompt.",
        session,
        contract,
    )

    assert [message.role for message in request.conversation.messages] == ["user"]
    assert (
        request.conversation.messages[0].content == "Quiz me with one source-backed recall prompt."
    )


def test_prior_answer_transform_keeps_prior_answer_context() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "A compact overview [E1].")
    contract = TurnContract(
        original_user_input="in another language",
        resolved_intent="material_overview",
        canonical_request="Translate the prior answer.",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.SOURCE_QA),
        LearningState(),
        "in another language",
        session,
        contract,
    )

    assert [message.role for message in request.conversation.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert request.conversation.messages[1].content == "A compact overview."
    assert request.conversation.messages[-1].content == "in another language"


def test_substantive_prior_transform_becomes_reasoning_followup() -> None:
    prior = TurnContract(
        original_user_input="What is the material about?",
        resolved_intent="material_overview",
        canonical_request="Summarize the material.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query="material overview",
        evidence_refs=("materials/topic.md#chunk=0",),
    )
    plan = _plan(
        action=LearningAction.PRESENT,
        retrieval_query="material overview",
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )
    contract = TurnContract(
        original_user_input="When would I use this outside the course?",
        resolved_intent="material_overview",
        canonical_request="Explain practical real-world use of the prior material.",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=prior.evidence_refs,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=prior,
    )

    assert updated_contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert updated_contract.prior_answer_reference is True
    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert "practical real-world use" in (updated_plan.retrieval_query or "")


def test_reasoned_relevance_mode_keeps_recent_history_and_contract_guidance() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers foundations [E1].")
    contract = TurnContract(
        original_user_input="why is that important?",
        resolved_intent="source_qa",
        canonical_request="Explain why the prior material overview matters.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.SOURCE_QA),
        LearningState(),
        "why is that important?",
        session,
        contract,
    )
    context = _turn_contract_prompt_context(contract)

    assert [message.role for message in request.conversation.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert request.conversation.messages[1].content == "It covers foundations."
    assert request.conversation.messages[-1].content == "why is that important?"
    assert "reason_from_prior_evidence" in context
    assert "Referenced-answer reasoning" in context


def test_material_followup_keeps_recent_context_even_without_followup_contract() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers foundations [E1].")
    session.conversation.add("user", "Why is that important?")
    session.conversation.add("assistant", "It supports later applications [E2].")
    session.conversation.add("user", "When would I use it outside the course?")
    contract = TurnContract(
        original_user_input="When would I use it outside the course?",
        resolved_intent="source_qa",
        canonical_request="Explain the real-world use of the current material.",
        evidence_refs=("materials/current.md#chunk=0",),
    )

    request = _learning_agent_request(
        _plan(action=LearningAction.SOURCE_QA),
        LearningState(),
        "When would I use it outside the course?",
        session,
        contract,
    )

    assert [message.role for message in request.conversation.messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
    ]
    assert request.conversation.messages[1].content == "It covers foundations."
    assert request.conversation.messages[3].content == "It supports later applications."
    assert request.conversation.messages[-1].content == "When would I use it outside the course?"


def test_reasoned_relevance_prompt_uses_prior_answer_as_premise() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers sequences and derivatives [E1].")
    contract = TurnContract(
        original_user_input="why is that important?",
        resolved_intent="material_overview",
        canonical_request="Explain why the prior material overview matters.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.PRESENT),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    prompt = _learning_extra_system_prompt(
        session,
        _plan(action=LearningAction.PRESENT),
        resolved,
        user_input="why is that important?",
    )

    assert "Answer the user's reasoning/application request directly" in prompt
    assert "Use this only to resolve references" not in prompt
    assert "It covers sequences and derivatives" in prompt
    assert "prior E" not in prompt


def test_fresh_material_overview_prompt_drops_prior_answer_replay() -> None:
    contract = TurnContract(
        original_user_input="create a table regarding the material",
        resolved_intent="material_overview",
        canonical_request="Create a table about the material corpus.",
        answer_format=ANSWER_FORMAT_TABLE,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        prior_turn_original_user_input="What is l'Hospital?",
        prior_answer_excerpt="The prior answer was about l'Hospital [E1].",
    )

    context = _turn_contract_prompt_context(contract)

    assert "retrieval=overview" in context
    assert "Prior answer" not in context
    assert "l'Hospital" not in context


def test_reasoned_relevance_turn_does_not_use_overview_fallback() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "source-1.md", content="Sequences and convergence."),
        _evidence("E2", "source-2.md", content="Derivatives and function analysis."),
    )
    contract = TurnContract(
        original_user_input="why is that important?",
        resolved_intent="material_overview",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=("source-1.md#chunk=0", "source-2.md#chunk=0"),
    )

    assert not _needs_overview_fallback(plan, "Too thin [E1].", evidence, contract=contract)


def test_fresh_overview_uses_shape_guard_even_when_contract_claims_prior_reasoning() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence("E1", "source-1.md", content="Sequences and convergence."),
        _evidence("E2", "source-2.md", content="Derivatives and function analysis."),
    )
    contract = TurnContract(
        original_user_input="what do you think about the material?",
        resolved_intent="material_overview",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        prior_turn_evidence_refs=(),
    )

    assert _needs_overview_fallback(plan, "Too thin [E1].", evidence, contract=contract)


def test_source_grounded_turns_buffer_until_postprocessed() -> None:
    assert _should_buffer_learning_output(_plan(action=LearningAction.PRESENT))
    assert _should_buffer_learning_output(_plan(action=LearningAction.SOURCE_QA))
    assert _should_buffer_learning_output(_plan(action=LearningAction.CHAT))
    assert not _should_buffer_learning_output(_plan(action=LearningAction.WAIT_READY_REMINDER))


def test_resolved_turn_intent_prefers_contract_state() -> None:
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.PRESENT),
        turn_contract=TurnContract(
            original_user_input="auf deutsch",
            resolved_intent="material_overview",
        ),
    )

    assert _resolved_turn_intent(resolved) == "material_overview"


def test_learning_extra_system_prompt_includes_prior_answer_for_followup() -> None:
    session = _session()
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers sequences and series [E1].")
    session.conversation.add("user", "Define the most technical term from that answer.")
    contract = TurnContract(
        original_user_input="Define the most technical term from that answer.",
        resolved_intent="source_qa",
        canonical_request="Define a term from the prior assistant answer.",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    prompt = _learning_extra_system_prompt(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
        user_input="Define the most technical term from that answer.",
    )

    assert "Prior assistant reply" in prompt
    assert "reference context only" in prompt
    assert "cited_claims=1" not in prompt
    assert "It covers sequences and series" in prompt
    assert "prior E" not in prompt
    assert "If this is a pure rewrite" in prompt
    assert "sequences and series" in prompt


def test_turn_contract_with_prior_replay_state_captures_prior_answer_and_refs() -> None:
    conversation = Conversation()
    conversation.add("user", "What is the material about?")
    conversation.add("assistant", "It covers sequences and series [E1].")
    conversation.add("user", "What else?")
    prior_contract = TurnContract(
        original_user_input="What is the material about?",
        resolved_intent="material_overview",
        canonical_request="Summarize the material.",
        evidence_refs=("materials/overview.md#chunk=0",),
        validation_result="ok",
    )
    contract = TurnContract(
        original_user_input="What else?",
        resolved_intent="source_qa",
        canonical_request="Continue the prior overview.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    )

    enriched = _turn_contract_with_prior_replay_state(
        contract,
        prior_contract=prior_contract,
        conversation=conversation,
        user_input="What else?",
    )

    assert enriched.prior_turn_original_user_input == "What is the material about?"
    assert enriched.prior_turn_resolved_intent == "material_overview"
    assert enriched.prior_turn_canonical_request == "Summarize the material."
    assert enriched.prior_turn_evidence_refs == ("materials/overview.md#chunk=0",)
    assert enriched.prior_answer_excerpt == "It covers sequences and series [E1]."


def test_turn_contract_serializes_prior_replay_state() -> None:
    contract = TurnContract(
        original_user_input="What else?",
        resolved_intent="source_qa",
        canonical_request="Continue the prior overview.",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        evidence_refs=("materials/current.md#chunk=0",),
        prior_turn_original_user_input="What is the material about?",
        prior_turn_resolved_intent="material_overview",
        prior_turn_canonical_request="Summarize the material.",
        prior_turn_evidence_refs=("materials/overview.md#chunk=0",),
        prior_answer_excerpt="It covers sequences and series [E1].",
        validation_result="ok",
    )

    loaded = TurnContract.from_dict(contract.to_dict())

    assert loaded == contract


def test_prior_answer_context_summarizes_cited_structure_without_source_status() -> None:
    conversation = Conversation()
    conversation.add("user", "What stands out?")
    conversation.add(
        "assistant",
        "The source defines a sorted prefix [E1].\n- A component is not an extra force [E2].",
    )
    contract = TurnContract(
        original_user_input="Compare the first and third cited ideas.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1, 3),
        prior_answer_position_basis="cited_claims",
    )

    context = _prior_answer_prompt_context(
        conversation,
        user_input="Compare the first and third cited ideas.",
        contract=contract,
    )

    assert "cited_claims=2" in context
    assert "list_items=1" in context
    assert "The source defines a sorted prefix" in context
    assert "A component is not an extra force" in context
    assert "prior E" not in context


def test_prior_answer_reference_context_prefers_most_recent_answer() -> None:
    conversation = Conversation()
    conversation.add("user", "Explain slowly.")
    conversation.add("assistant", "Older point A [E1]. Older point B [E1].")
    conversation.add("user", "Give an example.")
    conversation.add(
        "assistant",
        "- Recent point one [E1]\n- Recent point two [E1]",
    )
    contract = TurnContract(
        original_user_input="Compare the last two points.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1, 2),
        prior_answer_position_basis="list_items",
    )

    context = _prior_answer_prompt_context(
        conversation,
        user_input="Compare the last two points.",
        contract=contract,
    )

    assert "Recent point one" in context
    assert "Recent point two" in context
    assert "Older point" not in context
    assert "Prior answer structure" in context
    assert "list_items=2" in context


def test_prior_answer_cited_claims_keep_sentence_before_adjacent_citations() -> None:
    claims = _prior_answer_cited_claims(
        "The first claim is separate [E1]. The second claim has two refs [E2][E3]."
    )

    assert claims == (
        "The first claim is separate",
        "The second claim has two refs",
    )


def test_prior_answer_cited_claims_allow_next_sentence_after_citation_group() -> None:
    claims = _prior_answer_cited_claims(
        "First supported sentence [E1][E2] Second supported sentence [E3]."
    )

    assert claims == (
        "First supported sentence",
        "Second supported sentence",
    )


def test_prior_answer_cited_claims_keep_sentence_before_post_punctuation_citation() -> None:
    claims = _prior_answer_cited_claims("The cited sentence ends before the citation. [E4]")

    assert claims == ("The cited sentence ends before the citation",)


def test_prior_answer_cited_claims_do_not_split_inside_inline_paths() -> None:
    claims = _prior_answer_cited_claims(
        "It came from `materials/examples/history.md`, which contains the library example. [E1]"
    )

    assert claims == (
        "It came from `materials/examples/history.md`, which contains the library example",
    )


def test_prior_answer_reference_context_uses_latest_answer_without_requested_structure() -> None:
    conversation = Conversation()
    conversation.add("user", "Explain the source.")
    conversation.add(
        "assistant",
        "First cited idea [E1]. Second cited idea [E2].",
    )
    conversation.add("user", "Compare the first and third cited ideas.")
    conversation.add(
        "assistant",
        "That prior-answer position is absent: position 3 is not available.",
    )
    contract = TurnContract(
        original_user_input="What assumption is behind the second cited claim?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(2,),
        prior_answer_position_basis="cited_claims",
    )

    context = _prior_answer_prompt_context(
        conversation,
        user_input="What assumption is behind the second cited claim?",
        contract=contract,
    )

    assert "position 3 is not available" in context
    assert "cited_claims=0" in context
    assert "First cited idea" not in context
    assert "Second cited idea" not in context


def test_prior_answer_reference_missing_position_gets_deterministic_reply() -> None:
    session = _session()
    session.conversation.add("user", "Give a limitation.")
    session.conversation.add(
        "assistant",
        "The simple approach is clear but not fastest for large lists [E1].",
    )
    evidence = _turn_evidence(
        _evidence(
            source="algorithms.md",
            content="The simple version is clear but not the fastest choice for large lists.",
        )
    )
    contract = TurnContract(
        original_user_input="Compare the first and third cited ideas.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1, 3),
        prior_answer_position_basis="cited_claims",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "position 3 is not available" in reply.reply
    assert "Available cited position 1" not in reply.reply
    assert "[E1]" not in reply.reply
    assert reply.source_refs is None


def test_prior_answer_missing_list_position_uses_latest_cited_answer() -> None:
    session = _session()
    session.conversation.add("user", "Give two points.")
    session.conversation.add(
        "assistant",
        "- Older point one [E1]\n- Older point two [E2]",
    )
    session.conversation.add("user", "Is that important?")
    session.conversation.add(
        "assistant",
        "The latest answer contains one cited claim [E3].",
    )
    evidence = _turn_evidence(
        _evidence(
            source="latest.md",
            content="The latest answer contains one cited claim.",
        )
    )
    contract = TurnContract(
        original_user_input="What does the second point mean?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(2,),
        prior_answer_position_basis="list_items",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "position 2 is not available" in reply.reply
    assert "Older point" not in reply.reply
    assert "Available cited position 1" not in reply.reply
    assert "[E1]" not in reply.reply


def test_prior_answer_list_position_can_fallback_to_cited_claim_structure() -> None:
    session = _session()
    session.conversation.add("user", "Explain the source.")
    session.conversation.add(
        "assistant",
        "The first cited claim has no markdown bullet. [E1]",
    )
    contract = TurnContract(
        original_user_input="What does bullet 1 depend on?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1,),
        prior_answer_position_basis="list_items",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    assert (
        _deterministic_learning_reply(
            session,
            _plan(action=LearningAction.SOURCE_QA),
            resolved,
        )
        is None
    )


def test_prior_answer_transform_with_available_cited_claim_does_not_emit_absence_reply() -> None:
    session = _session()
    session.conversation.add("user", "Explain it.")
    session.conversation.add("assistant", "The latest answer has one cited sentence [E1].")
    contract = TurnContract(
        original_user_input="Explain the first point differently.",
        resolved_intent="source_qa",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1,),
        prior_answer_position_basis="cited_claims",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    assert (
        _deterministic_learning_reply(
            session,
            _plan(action=LearningAction.SOURCE_QA),
            resolved,
        )
        is None
    )


def test_prior_answer_list_transform_uses_cited_evidence_snippets() -> None:
    session = _session()
    contract = TurnContract(
        original_user_input="Turn the evidence into a two-step checklist.",
        resolved_intent="topic_presentation",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        answer_format=ANSWER_FORMAT_LIST,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    evidence = _turn_evidence(
        _evidence("E1", "first.md", content="First supported operation keeps its number 1/8."),
        _evidence("E2", "second.md", content="Second supported operation keeps its number 1/4."),
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "First supported operation keeps its number 1/8. [E1]" in reply.reply
    assert "Second supported operation keeps its number 1/4. [E2]" in reply.reply


def test_prior_answer_list_transform_with_single_evidence_uses_model() -> None:
    session = _session()
    contract = TurnContract(
        original_user_input="Turn the evidence into a two-step checklist.",
        resolved_intent="topic_presentation",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        answer_format=ANSWER_FORMAT_LIST,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(
            _evidence("E1", "single.md", content="Select the smallest item, then place it next.")
        ),
        turn_contract=contract,
    )

    assert (
        _deterministic_learning_reply(
            session,
            _plan(action=LearningAction.SOURCE_QA),
            resolved,
        )
        is None
    )


def test_prior_answer_transform_without_source_structure_gets_absence_reply() -> None:
    session = _session()
    session.conversation.add("user", "Try the lookup.")
    session.conversation.add(
        "assistant",
        "The current evidence does not contain a direct source answer for this request.",
    )
    contract = TurnContract(
        original_user_input="Restate the previous answer using only source-backed claims.",
        resolved_intent="source_qa",
        is_followup=True,
        answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "does not contain a cited material claim" in reply.reply
    assert reply.citation_required is False


def test_prior_answer_reasoning_missing_cited_claim_gets_absence_reply() -> None:
    session = _session()
    session.conversation.add("user", "Explain it.")
    session.conversation.add("assistant", "The latest answer has one cited sentence [E1].")
    evidence = _turn_evidence(_evidence(content="The latest answer has one cited sentence."))
    contract = TurnContract(
        original_user_input="What assumption is behind the second cited claim?",
        resolved_intent="source_qa",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(2,),
        prior_answer_position_basis="cited_claims",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "position 2 is not available" in reply.reply
    assert reply.citation_required is False


def test_prior_answer_reasoning_with_no_prior_structure_gets_absence_reply() -> None:
    session = _session()
    session.conversation.add("user", "Explain the source.")
    session.conversation.add(
        "assistant",
        "First cited idea [E1]. Second cited idea [E2].",
    )
    session.conversation.add("user", "Continue from it.")
    session.conversation.add(
        "assistant",
        "The prior answer does not contain a cited material claim to extend.",
    )
    contract = TurnContract(
        original_user_input="What assumption is behind the second cited claim?",
        resolved_intent="source_qa",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(2,),
        prior_answer_position_basis="cited_claims",
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "position 2 is not available" in reply.reply
    assert reply.citation_required is False


def test_prior_answer_absence_guard_does_not_mask_cited_prior_reply() -> None:
    session = _session()
    session.conversation.add("user", "Show the cited source.")
    session.conversation.add("assistant", "[E1].")
    contract = TurnContract(
        original_user_input="What does that citation mean?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    assert (
        _deterministic_learning_reply(
            session,
            _plan(action=LearningAction.SOURCE_QA),
            resolved,
        )
        is None
    )


def test_prior_answer_list_reference_without_positions_gets_absence_reply() -> None:
    session = _session()
    session.conversation.add("user", "Give an example.")
    session.conversation.add(
        "assistant",
        "The latest answer has one cited sentence [E1].",
    )
    evidence = _turn_evidence(_evidence(content="The latest answer has one cited sentence."))
    contract = TurnContract(
        original_user_input="Compare the last two points.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_position_basis="list_items",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "separate list/table point" in reply.reply
    assert "position 2 is not available" in reply.reply
    assert "list_items" not in reply.reply
    assert "[E1]" not in reply.reply


def test_prior_answer_position_guard_ignores_informal_point_positions() -> None:
    session = _session()
    session.conversation.add("user", "Give an example.")
    session.conversation.add("assistant", "One sentence contains two informal points [E1].")
    contract = TurnContract(
        original_user_input="Compare the last two points.",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        prior_answer_positions=(1, 2),
        prior_answer_position_basis="none",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=_turn_evidence(_evidence()),
        turn_contract=contract,
    )

    assert (
        _deterministic_learning_reply(
            session,
            _plan(action=LearningAction.SOURCE_QA),
            resolved,
        )
        is None
    )


def test_prior_answer_citation_check_maps_prior_id_through_stored_source_ref() -> None:
    session = _session()
    session.conversation.add("user", "Explain the procedure.")
    session.conversation.add("assistant", "The prior answer cites the procedure source [E1].")
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the procedure.",
        resolved_intent="source_qa",
        evidence_refs=("procedure.md#chunk=0",),
    )
    current_evidence = _turn_evidence(
        _evidence(
            "E1",
            "unrelated.md",
            content="This unrelated source happens to have the current E1 id.",
        ),
        _evidence(
            "E2",
            "procedure.md",
            content="The procedure source states the cited procedure directly.",
        ),
    )
    contract = TurnContract(
        original_user_input="Which evidence block backs that up?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=current_evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert "[E2]" in reply.reply
    assert "unrelated" not in reply.reply


def test_prior_answer_citation_check_quotes_source_without_meta_claim() -> None:
    session = _session()
    session.conversation.add("user", "Explain the procedure.")
    session.conversation.add("assistant", "The prior answer cites the procedure source [E1].")
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the procedure.",
        resolved_intent="source_qa",
        evidence_refs=("procedure.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence(
            "E1",
            "procedure.md",
            content="The procedure source states the cited procedure directly.",
        )
    )
    contract = TurnContract(
        original_user_input="Which evidence block backs that up?",
        resolved_intent="source_qa",
        is_followup=True,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert reply.reply == "“The procedure source states the cited procedure directly.” [E1]."
    assert "prior answer" not in reply.reply


def test_reasoned_prior_citation_check_uses_quoted_target_phrase() -> None:
    session = _session()
    session.conversation.add("user", "Explain the rule.")
    session.conversation.add("assistant", "The rule follows from linearity [E1].")
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the rule.",
        resolved_intent="source_qa",
        evidence_refs=("rule.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence("E1", "rule.md", content="The source says this follows from linearity.")
    )
    contract = TurnContract(
        original_user_input="Which citation supports the last answer?",
        resolved_intent="source_qa",
        canonical_request='Which citation supports "linearity"?',
        is_followup=True,
        followup_target='the prior cited phrase "linearity"',
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
        direct_evidence_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is not None
    assert reply.reply == "“The source says this follows from linearity.” [E1]."


def test_direct_prior_reasoning_with_single_citation_keeps_model_answer_path() -> None:
    session = _session()
    session.conversation.add("user", "Explain the cited idea.")
    session.conversation.add("assistant", "The cited idea is stated once [E1].")
    session.last_turn_contract = TurnContract(
        original_user_input="Explain the cited idea.",
        resolved_intent="source_qa",
        evidence_refs=("idea.md#chunk=0",),
    )
    evidence = _turn_evidence(
        _evidence("E1", "idea.md", content="The source states the cited idea once.")
    )
    contract = TurnContract(
        original_user_input="Compare the prior cited ideas.",
        resolved_intent="source_qa",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
        citation_required=True,
        direct_evidence_required=True,
    )
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_evidence=evidence,
        turn_contract=contract,
    )

    reply = _deterministic_learning_reply(
        session,
        _plan(action=LearningAction.SOURCE_QA),
        resolved,
    )

    assert reply is None


def test_iter_armory_turn_events_emits_material_operations_for_stored_refs() -> None:
    session = _session()
    session.learning_state = LearningState(
        phase=LearningPhase.RECALL,
        current_item="compactness",
        retrieval_query="compactness",
        expected_source_refs=["notes.md#chunk=0"],
    )
    session.rag_index = _index(_document())
    orchestrator = TurnOrchestrator(session)
    resolved = ResolvedTurnPlan(
        learning_plan=plan_turn(session.learning_state, "review", intent="material_review"),
        turn_evidence=_turn_evidence(_evidence()),
    )

    with (
        patch(
            "chat.intent_resolution._classified_user_intent",
            return_value="material_review",
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", return_value=resolved),
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Review [E1]"),
                    TurnCompleteEvent("Review [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("review"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert "open_stored_evidence" in operations
    assert any(isinstance(event, NoticeEvent) and event.code == "evidence" for event in events)


def test_iter_armory_turn_events_samples_corpus_for_initial_material_overview() -> None:
    session = _session()
    session.rag_index = _index(_document())
    orchestrator = TurnOrchestrator(session)
    resolved_plans: list[LearningTurnPlan] = []

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        resolved_plans.append(plan)
        evidence = _turn_evidence(
            _evidence(source="intro.md", content="Course overview."),
            sampled=1,
            total=1,
        )
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="material_overview",
                canonical_request="Provide an overview of the material contents.",
                retrieval_query="Provide an overview of the material contents",
                confidence=1.0,
            ),
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Overview [E1]"),
                    TurnCompleteEvent("Overview [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("what is the material about"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert resolved_plans[0].retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert "sample_overview" in operations
    assert "search_index" not in operations


def test_initial_overview_keeps_default_material_route_when_classifier_query_drifts() -> None:
    session = _session()
    session.rag_index = _index(_document())
    orchestrator = TurnOrchestrator(session)
    resolved_plans: list[LearningTurnPlan] = []

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        resolved_plans.append(plan)
        evidence = _turn_evidence(
            _evidence(source="intro.md", content="Course concepts and methods."),
            sampled=1,
            total=1,
        )
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="What is the material about?",
                retrieval_query="broad corpus contents and themes",
                direct_evidence_required=True,
                confidence=0.98,
            ),
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Overview [E1]"),
                    TurnCompleteEvent("Overview [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("what is the material about"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert resolved_plans[0].action is LearningAction.PRESENT
    assert resolved_plans[0].retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert "sample_overview" in operations


def test_initial_specific_question_keeps_source_route_when_query_preserves_user_terms() -> None:
    session = _session()
    session.rag_index = _index(_document())
    orchestrator = TurnOrchestrator(session)
    resolved_plans: list[LearningTurnPlan] = []

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        resolved_plans.append(plan)
        evidence = _turn_evidence(
            _evidence(source="notes.md", content="Compactness is defined by finite subcovers."),
            sampled=1,
            total=1,
        )
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assess_turn_evidence(plan, evidence),
        )

    with (
        patch(
            "chat.intent_resolution._resolved_user_intent",
            return_value=TurnIntentResolution(
                intent="source_qa",
                canonical_request="What is compactness?",
                retrieval_query="compactness definition",
                direct_evidence_required=True,
                confidence=0.98,
            ),
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Compactness uses finite subcovers [E1]."),
                    TurnCompleteEvent(
                        "Compactness uses finite subcovers [E1].",
                        0,
                        1.0,
                        "stop",
                        100,
                    ),
                ]
            ),
        ),
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("what is compactness"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert resolved_plans[0].action is LearningAction.SOURCE_QA
    assert resolved_plans[0].retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert "sample_overview" not in operations


def test_trace_successful_reply_uses_contract_retrieval_query_surface() -> None:
    session = _session()
    orchestrator = TurnOrchestrator(session)
    orchestrator.last_reply = "Grounded answer [E1]."
    evidence = _turn_evidence(_evidence(content="The source backs the answer."))
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA, retrieval_query=None),
        turn_evidence=evidence,
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="source_qa",
            retrieval_query="",
        ),
    )

    orchestrator._trace_successful_reply(
        resolved,
        evidence,
        latency_ms=12.3,
        notice="",
    )

    record_session_event = cast("MagicMock", session.trace.record_session_event)
    kwargs = record_session_event.call_args.kwargs
    contract = kwargs["turn_contract"]
    assert kwargs["retrieval_query"] == ""
    assert is_string_mapping(contract)
    assert kwargs["retrieval_query"] == contract["retrieval_query"]


def test_no_evidence_turn_does_not_replace_followup_anchor() -> None:
    session = _session()
    previous = TurnContract(
        original_user_input="Explain the source point.",
        resolved_intent="source_qa",
        evidence_refs=("materials/source.md#chunk=0",),
    )
    session.last_turn_contract = previous
    session.last_plan_intent = "source_qa"
    orchestrator = TurnOrchestrator(session)
    orchestrator.last_reply = "The current evidence does not contain a direct source answer."
    resolved = ResolvedTurnPlan(
        learning_plan=_plan(action=LearningAction.SOURCE_QA),
        turn_contract=TurnContract(
            original_user_input="Unsupported lookup.",
            resolved_intent="source_qa",
            evidence_refs=(),
        ),
    )

    with (
        patch("chat.turn_finalization.verify_response", return_value=""),
        patch("chat.turn_finalization.schedule_memory_extraction"),
        patch("chat.turn_finalization.save_usage"),
    ):
        orchestrator._finalize_successful_turn("Unsupported lookup.", resolved, latency_ms=1.0)

    assert session.last_turn_contract is previous
    assert session.last_plan_intent == "source_qa"


def test_prior_replay_state_uses_recent_cited_answer_after_uncited_abstain() -> None:
    conversation = Conversation()
    conversation.add("user", "Explain the source point.")
    conversation.add("assistant", "The source point is grounded [E1].")
    conversation.add("user", "Unsupported lookup.")
    conversation.add(
        "assistant",
        "The current evidence does not contain a direct source answer.",
    )

    contract = _turn_contract_with_prior_replay_state(
        TurnContract(
            original_user_input="Continue from the cited evidence.",
            resolved_intent="source_qa",
            is_followup=True,
            prior_answer_reference=True,
        ),
        prior_contract=TurnContract(
            original_user_input="Explain the source point.",
            resolved_intent="source_qa",
            evidence_refs=("materials/source.md#chunk=0",),
        ),
        conversation=conversation,
        user_input="Continue from the cited evidence.",
    )

    assert contract.prior_answer_excerpt == "The source point is grounded [E1]."


def test_unreplayable_followup_does_not_reuse_stale_retrieval_query() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="prior topic retrieval",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="Give a cited example.",
        resolved_intent="source_qa",
        canonical_request="Give a cited example.",
        is_followup=True,
        retrieval_query="prior topic retrieval",
        prior_turn_original_user_input="Explain the prior topic.",
        prior_turn_resolved_intent="source_qa",
        prior_turn_canonical_request="Explain the prior topic.",
        prior_answer_excerpt="The prior answer did not include a citation.",
    )

    reset_plan, reset_contract = _reset_unreplayable_followup_state(plan, contract)

    assert reset_plan.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    assert reset_plan.retrieval_query is None
    assert reset_contract.is_followup is False
    assert reset_contract.retrieval_query == ""
    assert reset_contract.prior_turn_original_user_input == ""


def test_unreplayable_first_turn_uses_current_canonical_query() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="initial retrieval",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="What does that mean?",
        resolved_intent="source_qa",
        canonical_request="Explain the current referenced definition.",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_query="initial retrieval",
        prior_answer_excerpt="The prior answer did not include a citation.",
    )

    reset_plan, reset_contract = _reset_unreplayable_followup_state(plan, contract)

    assert reset_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert reset_plan.retrieval_query == "Explain the current referenced definition."
    assert reset_plan.requires_direct_evidence is True
    assert reset_contract.is_followup is False
    assert reset_contract.retrieval_query == reset_plan.retrieval_query


def test_priority_followup_with_prior_reference_reuses_prior_evidence() -> None:
    plan = _plan(
        action=LearningAction.PRIORITY,
        retrieval_query="global priority retrieval",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="Which prior citation is strongest?",
        resolved_intent="priority_request",
        canonical_request="Which prior citation is strongest?",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="global priority retrieval",
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Restate the source-backed claim.",
            resolved_intent="source_qa",
            canonical_request="Restate the source-backed claim.",
            evidence_refs=("materials/source-1.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_plan.evidence_refs == ("materials/source-1.md#chunk=0",)
    assert updated_contract.retrieval_query == ""
    assert updated_contract.evidence_refs == updated_plan.evidence_refs


def test_reused_prior_evidence_ignores_literal_followup_direct_evidence_flag() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )
    contract = TurnContract(
        original_user_input="Give another angle.",
        resolved_intent="source_qa",
        canonical_request="Continue the prior cited material answer.",
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        direct_evidence_required=True,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Summarize the material.",
            resolved_intent="material_overview",
            canonical_request="Summarize the material.",
            evidence_refs=("materials/source-1.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.evidence_refs == ("materials/source-1.md#chunk=0",)
    assert updated_plan.requires_direct_evidence is False
    assert updated_contract.direct_evidence_required is False


def test_fresh_source_request_does_not_reuse_stale_prior_evidence() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )
    contract = TurnContract(
        original_user_input="Using only the sources, what is the amber forge retrieval phrase?",
        resolved_intent="source_qa",
        canonical_request="Using only the sources, what is the amber forge retrieval phrase?",
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        direct_evidence_required=True,
        prior_answer_reference=False,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Where did that come from?",
            resolved_intent="source_qa",
            canonical_request="Show the source for the prior cited claim.",
            evidence_refs=("materials/algorithms.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert updated_plan.retrieval_query == contract.canonical_request
    assert updated_plan.requires_direct_evidence is True
    assert updated_contract.evidence_refs == ("materials/algorithms.md#chunk=0",)
    assert updated_contract.direct_evidence_required is True


def test_specific_followup_keeps_content_rich_current_query_over_stale_prior_query() -> None:
    user_input = "Using only the sources, what is the amber forge retrieval phrase?"
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="Find the source of the quoted claim from the prior answer.",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    )
    contract = TurnContract(
        original_user_input=user_input,
        resolved_intent="source_qa",
        canonical_request=user_input,
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query="Find the source of the quoted claim from the prior answer.",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Where did that come from?",
            resolved_intent="source_qa",
            canonical_request="Find the source of the previous claim.",
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            evidence_refs=("materials/algorithms.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert updated_plan.retrieval_query == user_input
    assert updated_contract.retrieval_query == user_input


def test_prior_answer_followup_does_not_become_exact_span_lookup() -> None:
    user_input = "Explain the practical value of that answer."
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=user_input,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    )
    contract = TurnContract(
        original_user_input=user_input,
        resolved_intent="source_qa",
        canonical_request=user_input,
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        retrieval_query=user_input,
        direct_evidence_required=True,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            evidence_refs=("materials/overview.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_plan.requires_direct_evidence is False
    assert updated_contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert updated_contract.direct_evidence_required is False


def test_source_request_after_unsupported_turn_retrieves_current_query() -> None:
    user_input = "Give a concrete example tied to a citation."
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
    )
    contract = TurnContract(
        original_user_input=user_input,
        resolved_intent="source_qa",
        canonical_request=user_input,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
        retrieval_query="",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="unsupported source question",
            resolved_intent="source_qa",
            canonical_request="unsupported source question",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            evidence_refs=(),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert updated_plan.retrieval_query == user_input
    assert updated_contract.direct_evidence_required is True


def test_source_request_without_prior_surface_retrieves_current_query() -> None:
    user_input = "Using only the sources, what is the amber forge retrieval phrase?"
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
    )
    contract = TurnContract(
        original_user_input=user_input,
        resolved_intent="source_qa",
        canonical_request=user_input,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
        retrieval_query="",
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=None,
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert updated_plan.retrieval_query == user_input
    assert updated_contract.retrieval_query == user_input


def test_unreplayable_content_rich_followup_keeps_current_query() -> None:
    user_input = "In the algorithms source, how is the next item selected?"
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=user_input,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input=user_input,
        resolved_intent="source_qa",
        canonical_request=user_input,
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query=user_input,
        prior_turn_original_user_input="What does bullet 1 depend on?",
    )

    updated_plan, updated_contract = _reset_unreplayable_followup_state(plan, contract)

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    assert updated_plan.retrieval_query == user_input
    assert updated_contract.is_followup is False
    assert updated_contract.retrieval_query == user_input


def test_short_vague_followup_does_not_become_direct_lookup() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )
    contract = TurnContract(
        original_user_input="What else stands out?",
        resolved_intent="source_qa",
        canonical_request="What other notable points stand out from the material?",
        is_followup=True,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            evidence_refs=("materials/algorithms.md#chunk=0",),
        ),
    )

    assert updated_plan.evidence_refs == ("materials/algorithms.md#chunk=0",)
    assert updated_contract.direct_evidence_required is False


def test_followup_can_reuse_replay_refs_when_previous_turn_had_no_current_refs() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
    )
    contract = TurnContract(
        original_user_input="Continue from that answer.",
        resolved_intent="source_qa",
        canonical_request="Continue from the prior cited answer.",
        is_followup=True,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        prior_answer_reference=True,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Prior transform.",
            resolved_intent="source_qa",
            evidence_refs=(),
            prior_answer_reference=True,
            prior_turn_evidence_refs=("materials/source.md#chunk=0",),
        ),
    )

    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.evidence_refs == ("materials/source.md#chunk=0",)
    assert updated_contract.evidence_refs == ("materials/source.md#chunk=0",)


def test_unresolved_followup_keeps_prior_evidence_surface() -> None:
    default_plan = material_overview_plan("Make a compact derived shape.")
    resolution = _unresolved_followup_intent_resolution(
        TurnIntentResolution(),
        user_input="Make a compact derived shape.",
        default_plan=default_plan,
        prior_contract=TurnContract(
            original_user_input="Prior request.",
            resolved_intent="source_qa",
            evidence_refs=("materials/source-1.md#chunk=0",),
        ),
    )
    plan = plan_turn(LearningState(), "Make a compact derived shape.", intent=resolution.intent)
    contract = TurnContract(
        original_user_input="Make a compact derived shape.",
        resolved_intent=resolution.intent,
        canonical_request=resolution.canonical_request,
        is_followup=resolution.is_followup,
        followup_target=resolution.followup_target,
        answer_mode=resolution.answer_mode,
        answer_format=resolution.answer_format,
        retrieval_strategy=resolution.retrieval_strategy,
        retrieval_query=resolution.retrieval_query,
        direct_evidence_required=resolution.direct_evidence_required,
        prior_answer_reference=resolution.prior_answer_reference,
    )

    updated_plan, updated_contract = _apply_turn_contract_to_plan(
        plan,
        contract,
        prior_contract=TurnContract(
            original_user_input="Prior request.",
            evidence_refs=("materials/source-1.md#chunk=0",),
        ),
    )

    assert resolution.intent == "source_qa"
    assert resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    assert updated_plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    assert updated_plan.retrieval_query is None
    assert updated_plan.evidence_refs == ("materials/source-1.md#chunk=0",)
    assert updated_contract.retrieval_query == ""


def test_plain_orchestrator_does_not_classify_without_armory() -> None:
    session = _session(armory=False)
    orchestrator = TurnOrchestrator(session)

    with (
        patch("chat.intent_resolution._classified_user_intent") as classify,
        patch(
            "chat.turn_execution.stream_completion",
            return_value=iter([CompletionDelta(content="plain")]),
        ) as stream,
    ):
        events = list(orchestrator.iter_events("hello"))

    classify.assert_not_called()
    stream.assert_called_once()
    assert session.last_reply if hasattr(session, "last_reply") else True
    assert any(isinstance(event, TurnCompleteEvent) for event in events)
    assert session.conversation.messages[-1].content == "plain"


def test_orchestrator_rolls_back_on_engine_error() -> None:
    session = _session()
    original_state = session.learning_state.clone()
    orchestrator = TurnOrchestrator(session)

    with (
        patch(
            "chat.intent_resolution._classified_user_intent",
            return_value="topic_presentation",
        ),
        patch.object(
            TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=EngineError("boom")
        ),
        pytest.raises(EngineError, match="boom"),
    ):
        list(orchestrator.iter_events("Explain compactness"))

    assert session.conversation.messages == []
    assert session.learning_state.to_dict() == original_state.to_dict()
    record_session_event = cast("MagicMock", session.trace.record_session_event)
    record_session_event.assert_called_with(
        "turn_error",
        original_user_input="Explain compactness",
        error="boom",
        latency_ms=pytest.approx(0, abs=1000),
    )


def test_evidence_refs_renders_refs_from_turn_evidence() -> None:
    assert evidence_refs(_turn_evidence(_evidence("E1", "notes.md", 7))) == ["notes.md#chunk=7"]
    assert evidence_refs(None) == []


def test_turn_contract_prompt_blocks_prior_quoted_phrases_without_current_evidence() -> None:
    context = _turn_contract_prompt_context(
        TurnContract(
            original_user_input="What should I notice there?",
            resolved_intent="source_qa",
            is_followup=True,
            followup_target="previous answer",
            evidence_refs=("notes.md#chunk=0",),
            citation_required=True,
        )
    )

    assert "mode=answer_from_evidence" in context
    assert "fmt=plain" in context
    assert "current evidence" in context
    assert "Cite source claims" in context
    assert "Conversation text resolves references" in context
    assert "keep inference brief and clearly separated" in context
    assert "keep compact" in context
    assert "no offers" in context
    assert "next-step prompts" in context


def test_prior_answer_context_does_not_emit_fake_current_citation_ids() -> None:
    conversation = Conversation()
    conversation.add("user", "What stands out?")
    conversation.add(
        "assistant",
        "The first point is supported. [E1] The second point follows. [E2]",
    )
    context = _prior_answer_prompt_context(
        conversation,
        user_input="Which citation supports that?",
        contract=TurnContract(
            original_user_input="Which citation supports that?",
            is_followup=True,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
            citation_required=True,
        ),
    )

    assert "prior E" not in context
    assert "first point" in context
    assert "second point" in context


def test_retrieve_material_overview_intent_does_not_use_strict_overview_fallback() -> None:
    plan = _plan(
        action=LearningAction.PRESENT,
        retrieval_query="source backed procedure",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
    )
    contract = TurnContract(
        original_user_input="Use the source with procedural wording.",
        resolved_intent="material_overview",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="source backed procedure",
        citation_required=True,
    )
    evidence = _turn_evidence(_evidence(content="A cited procedure is available."))

    assert not _needs_overview_fallback(plan, "uncited draft", evidence, contract=contract)


def test_turn_contract_with_replayed_prior_refs_can_seed_followups() -> None:
    contract = TurnContract(
        original_user_input="Ask one recall question grounded in the source.",
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        prior_answer_reference=True,
        prior_turn_evidence_refs=("source.md#chunk=0",),
    )

    assert _turn_contract_can_seed_followup(contract, visible_evidence=None)
