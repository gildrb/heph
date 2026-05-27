"""Tests for classifier-driven chat orchestration."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import hephaion.chat.evidence as evidence_module
from hephaion._types import is_string_mapping
from hephaion.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
)
from hephaion.chat.evidence import (
    ResolvedTurnPlan,
    assess_turn_evidence,
    build_overview_context,
    evidence_assessment_trace,
    evidence_refs,
    is_overview_query,
    resolve_turn_evidence,
)
from hephaion.chat.orchestrator import (
    TurnOrchestrator,
    _apply_turn_contract_to_plan,
    _classified_user_intent,
    _deterministic_learning_reply,
    _evidence_notice,
    _evidence_notice_metadata,
    _learning_agent_request,
    _learning_practice_context,
    _localize_deterministic_reply,
    _missing_indexed_material_reply,
    _model_json_payload,
    _needs_overview_fallback,
    _no_matching_indexed_evidence_reply,
    _overview_fallback_reply,
    _overview_topic_items_from_model_payload,
    _resolved_user_intent,
    _run_bounded_internal_repairs,
    _semantic_query_specificity,
    _stabilized_followup_intent_resolution,
    _stored_turn_evidence,
    _turn_contract_prompt_context,
    _user_visible_reply,
)
from hephaion.chat.session import ChatSession
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
    TurnIntentResolution,
)
from hephaion.rag import ArmoryIndex, Chunk, EvidenceChunk, ScoredChunk, TurnEvidence
from hephaion.rag.chunker import ChunkedDocument
from hephaion.runtime import ChatConfig, CompletionDelta, Conversation, EngineError
from hephaion.study import (
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    LearningTurnPlan,
    RecallRating,
    material_overview_plan,
    plan_turn,
)
from hephaion.study.schedule import load_recall_schedule


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
    use_expected_source_refs: bool = False,
    allow_tools: bool = True,
    buffer_response: bool = False,
) -> LearningTurnPlan:
    return LearningTurnPlan(
        action=action,
        phase=LearningPhase.PRESENTING,
        prompt="test prompt",
        retrieval_query=retrieval_query,
        use_expected_source_refs=use_expected_source_refs,
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
    )

    assert passes <= 2
    assert repaired == "Compactness is defined using open covers [E1]."


def test_source_qa_repair_appends_excerpts_when_reply_has_no_citations() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="compactness")
    evidence = _turn_evidence(
        _evidence(content="Compactness is defined using open covers in this material.")
    )

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "Compactness is defined using open covers.",
        evidence,
    )

    assert "- notes: Compactness is defined using open covers in this material. [E1]" in repaired


def test_calibration_repair_adds_minimal_evidence_citation() -> None:
    plan = _plan(action=LearningAction.CALIBRATE)
    evidence = _turn_evidence(_evidence(content="The product rule uses both factors."))

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "What is the product rule idea? Answer from memory.",
        evidence,
    )

    assert repaired == "What is the product rule idea? Answer from memory. [E1]"


def test_assessment_repair_adds_required_evidence_citation() -> None:
    plan = _plan(action=LearningAction.ASSESS)
    evidence = _turn_evidence(_evidence(content="A supporting rubric point."))

    repaired, _passes = _run_bounded_internal_repairs(
        plan,
        "PARTIAL: Name the missing source-backed point.",
        evidence,
    )

    assert repaired == "PARTIAL: Name the missing source-backed point. [E1]"


def test_source_qa_assessment_requires_direct_support_for_resolved_query() -> None:
    plan = _plan(
        action=LearningAction.SOURCE_QA,
        retrieval_query="Which source mentions the amber lattice theorem?",
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


def test_source_qa_assessment_accepts_direct_source_support() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA, retrieval_query="product rule source")
    evidence = _turn_evidence(
        _evidence(content="The product rule source says both factors contribute.")
    )

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is True


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


def test_source_qa_definition_request_without_retrieval_query_requires_direct_support() -> None:
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="Execute SOURCE_QA.\nUser question: Define the most technical term.",
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
    assert "did not retrieve a direct cited answer" in deterministic.reply
    assert "amber lattice theorem" in deterministic.reply
    assert "[E1]" in deterministic.reply
    assert "visible source chunks" not in deterministic.reply


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

    with patch(
        "hephaion.chat.orchestrator._model_json_payload", return_value=payload
    ) as model_json:
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


def test_resolved_user_intent_preserves_semantic_followup_query() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "hephaion.chat.orchestrator._model_json_payload",
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


def test_resolved_user_intent_preserves_prior_answer_transform_mode() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "hephaion.chat.orchestrator._model_json_payload",
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


def test_resolved_user_intent_preserves_table_format() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "hephaion.chat.orchestrator._model_json_payload",
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
        "hephaion.chat.orchestrator._stream_one_shot_model_text",
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Answer [E1]"),
                    TurnCompleteEvent("Answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
    ):
        events = list(orchestrator.iter_events("Explain compactness"))

    assert classify.call_args.kwargs["prior_intent"] == "topic_presentation"
    resolved_plan = resolve.call_args.args[0]
    assert resolved_plan.action is LearningAction.PRESENT
    assert resolved_plan.retrieval_query == "Explain compactness"
    assert session.learning_state.phase is LearningPhase.WAITING_FOR_READY
    assert session.last_plan_intent == "topic_presentation"
    assert any(isinstance(event, TurnCompleteEvent) for event in events)
    assert session.conversation.messages[-1].content == "Answer [E1]"


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
            "hephaion.chat.orchestrator._model_json_payload",
            return_value={
                "intent": "source_qa",
                "canonical_english_request": "Where the material defines compactness.",
                "retrieval_query": "compactness definition",
                "confidence": 1.0,
            },
        ) as model_payload,
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Source answer [E1]"),
                    TurnCompleteEvent("Source answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
    ):
        list(orchestrator.iter_events("Where is compactness defined?"))

    assert model_payload.called
    assert session.learning_state.current_item == ""
    assert session.last_plan_intent == "source_qa"
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.original_user_input == "Where is compactness defined?"
    assert session.last_turn_contract.retrieval_query == "compactness definition"
    assert session.conversation.messages[-1].content.startswith("Source answer [E1]")


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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Follow-up answer [E1]"),
                    TurnCompleteEvent("Follow-up answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Comparison answer [E1]"),
                    TurnCompleteEvent("Comparison answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Review feedback and spacing [E1]"),
                    TurnCompleteEvent("Review feedback and spacing [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Focused answer [E1]"),
                    TurnCompleteEvent("Focused answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
    ):
        list(orchestrator.iter_events("Explain that part more."))

    plan = resolved.call_args.args[0]
    assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
    assert plan.retrieval_query == "Explain the study-methods evidence about feedback."
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.evidence_refs == ("materials/source-1.md#chunk=0",)


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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Deutsche Uebersicht [E1]"),
                    TurnCompleteEvent("Deutsche Uebersicht [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
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
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
            "hephaion.chat.orchestrator._resolved_user_intent",
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
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Focused answer [E1]"),
                    TurnCompleteEvent("Focused answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
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
        patch("hephaion.chat.evidence.ensure_rag_index", return_value=index),
        patch(
            "hephaion.chat.evidence._retrieve_query_scored_chunks",
            return_value=MagicMock(scored=[ScoredChunk(query_chunk, 0.7)]),
        ),
    ):
        evidence = resolve_turn_evidence(session, plan)

    assert evidence is not None
    assert evidence_refs(evidence)[:2] == [
        "materials/exams.md#chunk=0",
        "materials/procedure.md#chunk=0",
    ]


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

    with patch("hephaion.chat.evidence.ensure_rag_index", return_value=index):
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


def test_deterministic_missing_index_reply_still_applies_classified_plan() -> None:
    session = _session()
    session.source_file_count = 1
    session.rag_index = None
    orchestrator = TurnOrchestrator(session)

    with (
        patch(
            "hephaion.chat.orchestrator._resolved_user_intent",
            return_value=TurnIntentResolution(intent="source_qa"),
        ),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
    ):
        events = list(orchestrator.iter_events("Where is compactness defined?"))

    assistant_text = "".join(
        event.delta for event in events if isinstance(event, AssistantDeltaEvent)
    )
    assert "no searchable evidence is indexed yet" in assistant_text
    assert session.last_plan_intent == "source_qa"
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


def test_build_overview_context_uses_enabled_index_without_keyword_intent_detection() -> None:
    session = _session()
    session.rag_index = _index(
        _document("notes.md", "Open covers define compactness."),
        _document("disabled.md", "Hidden text."),
    )
    session.disabled_source_files = {"disabled.md"}

    with patch("hephaion.chat.evidence.ensure_rag_index", return_value=session.rag_index):
        context = build_overview_context(session)

    assert "Deterministic local corpus overview" in context
    assert "indexed_documents=1" in context
    assert "notes.md" in context
    assert "disabled.md" not in context


def test_overview_query_checks_only_canonical_query() -> None:
    assert is_overview_query("what is the material about") is True
    assert is_overview_query("what are these files about") is False


def test_overview_fallback_reply_uses_model_repair_with_citations() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(_evidence(content="Main topic is compactness."))

    model_reply = (
        "These notes describe compactness through open cover conditions and related "
        "topological consequences, using the first sampled passage as grounded support [E1]. "
        "They also connect the definition to proof obligations and examples cited in the "
        "same extracted material [E1]."
    )

    with patch("hephaion.chat.orchestrator._stream_one_shot_model_text", return_value=model_reply):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == model_reply


def test_overview_fallback_uses_deterministic_reply_when_model_repair_fails() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Main topic is compactness."),
        _evidence("E2", "examples.md", content="Examples connect the definition to proofs."),
        sampled=2,
        total=5,
    )

    with patch(
        "hephaion.chat.orchestrator._model_json_payload", return_value={"answer": "uncited"}
    ):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert "Main topic is compactness. [E1]" in reply
    assert "Examples connect the definition to proofs. [E2]" in reply
    assert "The indexed materials are available" not in reply
    assert "sampled overview" not in reply
    assert "not reliable enough to show" not in reply


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

    with patch("hephaion.chat.orchestrator._stream_one_shot_model_text", return_value=""):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="what is the material about",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert "Number systems and elementary functions" in reply
    assert "University Example" not in reply
    assert "not reliable enough to show" not in reply


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

    with patch("hephaion.chat.orchestrator._stream_one_shot_model_text", return_value=""):
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
    table_reply = "| Topic | Detail |\n|---|---|\n| A | Topic A [E1] |\n| B | Topic B [E2] |\n"
    assert _needs_overview_fallback(plan, table_reply, evidence) is False
    oversized_table_reply = "| Topic | Detail |\n|---|---|\n" + "\n".join(
        f"| Item {index} | Topic A [E1] and Topic B [E2] |" for index in range(9)
    )
    assert _needs_overview_fallback(plan, oversized_table_reply, evidence) is True
    contract = TurnContract(
        original_user_input="create a table about the material",
        answer_format=ANSWER_FORMAT_TABLE,
    )
    assert _needs_overview_fallback(plan, table_reply, evidence, contract=contract) is False
    long_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. " + "Extra detail. " * 220
    )
    assert _needs_overview_fallback(plan, long_reply, evidence) is True
    good_reply = (
        "These materials discuss Topic A with direct evidence from the first source [E1] "
        "and Topic B with direct evidence from the second source [E2]. Together, the "
        "sampled excerpts support a cautious multi-source overview without adding claims."
    )

    assert _needs_overview_fallback(plan, good_reply, evidence) is False


def test_overview_topic_items_from_model_payload_requires_exact_quotes() -> None:
    evidence = _turn_evidence(_evidence(content="Compactness appears in open cover arguments."))
    payload: dict[str, object] = {
        "topics": [
            {
                "canonical_english": "Compactness",
                "display_label": "Compactness",
                "evidence_id": "E1",
                "evidence_quote": "Compactness appears",
            },
            {
                "canonical_english": "Invented",
                "display_label": "Invented",
                "evidence_id": "E1",
                "evidence_quote": "not present",
            },
        ]
    }

    assert _overview_topic_items_from_model_payload(payload, evidence) == ["Compactness [E1]"]


def test_localize_deterministic_reply_rejects_added_citations_and_preserves_original() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="localizer")

    with patch(
        "hephaion.chat.orchestrator.stream_completion",
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
    assert _user_visible_reply(chat_plan, "Answer. Would you like a quiz next?") == "Answer."


def test_source_qa_user_visible_reply_keeps_cited_active_recall_content() -> None:
    plan = _plan(action=LearningAction.SOURCE_QA)

    reply = _user_visible_reply(plan, "The source asks an active recall question [E1].")

    assert reply == "The source asks an active recall question [E1]."


def test_source_grounded_agent_request_isolates_stale_citation_history() -> None:
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

    assert [message.role for message in request.conversation.messages] == ["user"]
    assert request.conversation.messages[0].content == "What does the source say?"


def test_material_review_agent_request_isolates_stale_citation_history() -> None:
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

    assert [message.role for message in request.conversation.messages] == ["user"]
    assert (
        request.conversation.messages[0].content == "Make a learning checklist from the evidence."
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


def test_prior_answer_transform_uses_current_evidence_without_stale_citation_history() -> None:
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

    assert [message.role for message in request.conversation.messages] == ["user"]
    assert request.conversation.messages[0].content == "in another language"


def test_reasoned_relevance_mode_isolates_history_and_keeps_contract_guidance() -> None:
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

    assert [message.role for message in request.conversation.messages] == ["user"]
    assert request.conversation.messages[0].content == "why is that important?"
    assert "reasoned implications" in context
    assert "practical importance or use cases" in context


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
            "hephaion.chat.orchestrator._classified_user_intent", return_value="material_review"
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", return_value=resolved),
        patch(
            "hephaion.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Review [E1]"),
                    TurnCompleteEvent("Review [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaion.chat.orchestrator.verify_response", return_value=""),
        patch("hephaion.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaion.chat.orchestrator.save_usage"),
    ):
        events = list(orchestrator.iter_events("review"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert "open_stored_evidence" in operations
    assert any(isinstance(event, NoticeEvent) and event.code == "evidence" for event in events)


def test_plain_orchestrator_does_not_classify_without_armory() -> None:
    session = _session(armory=False)
    orchestrator = TurnOrchestrator(session)

    with (
        patch("hephaion.chat.orchestrator._classified_user_intent") as classify,
        patch(
            "hephaion.chat.orchestrator.stream_completion",
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
            "hephaion.chat.orchestrator._classified_user_intent",
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

    assert "quoted phrases" in context
    assert "unless the current evidence contains those words" in context
    assert "without affirming user-provided descriptors" in context
    assert "invented during the conversation are not source evidence" in context
    assert "Do not infer the purpose or learning effect" in context
    assert "Use 'direct evidence' only" in context
    assert "not material order" in context
    assert "Evidence IDs such as [E1] and [E7] are authoritative only" in context
    assert "Reused prior evidence may keep its old ID" in context
    assert "Answer mode: answer_from_evidence" in context
    assert "one or two short sentences" in context
    assert "Use quotation marks only for words copied exactly" in context
    assert "the source label and citation do not match" in context
    assert "do not claim the whole armory or all sources lack" in context
    assert "evidence-bundle judgement" in context
    assert "do not claim the sources themselves rank" in context
