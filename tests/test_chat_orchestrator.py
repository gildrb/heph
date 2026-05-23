"""Tests for classifier-driven chat orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hephaistos._types import is_string_mapping
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
)
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
    assess_turn_evidence,
    build_overview_context,
    evidence_assessment_trace,
    evidence_refs,
    is_overview_query,
)
from hephaistos.chat.orchestrator import (
    TurnOrchestrator,
    _classified_user_intent,
    _evidence_notice,
    _evidence_notice_metadata,
    _learning_practice_context,
    _localize_deterministic_reply,
    _missing_indexed_material_reply,
    _model_json_payload,
    _needs_overview_fallback,
    _no_matching_indexed_evidence_reply,
    _overview_fallback_reply,
    _overview_topic_items_from_model_payload,
    _run_bounded_internal_repairs,
    _user_visible_reply,
)
from hephaistos.chat.session import ChatSession
from hephaistos.rag import ArmoryIndex, Chunk, EvidenceChunk, TurnEvidence
from hephaistos.rag.chunker import ChunkedDocument
from hephaistos.runtime import ChatConfig, CompletionDelta, Conversation, EngineError
from hephaistos.study import (
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    LearningTurnPlan,
    RecallRating,
    material_overview_plan,
    plan_turn,
)
from hephaistos.study.schedule import load_recall_schedule


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
        "hephaistos.chat.orchestrator._model_json_payload", return_value=payload
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


def test_model_json_payload_returns_none_without_model_config() -> None:
    assert _model_json_payload(None, system_prompt="system", user_prompt="user") is None
    assert _model_json_payload(ChatConfig(), system_prompt="system", user_prompt="user") is None


def test_model_json_payload_parses_streamed_json_fragment() -> None:
    config = ChatConfig(base_url="https://local.test/v1", model="classifier")

    with patch(
        "hephaistos.chat.orchestrator._stream_one_shot_model_text",
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
            "hephaistos.chat.orchestrator._classified_user_intent",
            return_value="topic_presentation",
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
            "hephaistos.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Answer [E1]"),
                    TurnCompleteEvent("Answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaistos.chat.orchestrator.verify_response", return_value=""),
        patch("hephaistos.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaistos.chat.orchestrator.save_usage"),
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
            "hephaistos.chat.orchestrator._model_json_payload",
            return_value={"intent": "source_qa", "confidence": 1.0},
        ) as model_payload,
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "hephaistos.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Source answer [E1]"),
                    TurnCompleteEvent("Source answer [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaistos.chat.orchestrator.verify_response", return_value=""),
        patch("hephaistos.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaistos.chat.orchestrator.save_usage"),
    ):
        list(orchestrator.iter_events("Where is compactness defined?"))

    assert model_payload.called
    assert session.learning_state.current_item == ""
    assert session.last_plan_intent == "source_qa"
    assert session.conversation.messages[-1].content.startswith("Source answer [E1]")


def test_deterministic_missing_index_reply_still_applies_classified_plan() -> None:
    session = _session()
    session.source_file_count = 1
    session.rag_index = None
    orchestrator = TurnOrchestrator(session)

    with (
        patch("hephaistos.chat.orchestrator._classified_user_intent", return_value="source_qa"),
        patch("hephaistos.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaistos.chat.orchestrator.save_usage"),
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


def test_assess_turn_evidence_flags_weak_source_only_support() -> None:
    assessment = assess_turn_evidence(
        _plan(action=LearningAction.SOURCE_QA),
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

    with patch("hephaistos.chat.evidence.ensure_rag_index", return_value=session.rag_index):
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

    with patch(
        "hephaistos.chat.orchestrator._stream_one_shot_model_text", return_value=model_reply
    ):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert reply == model_reply


def test_overview_fallback_uses_deterministic_reply_when_model_repair_fails() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(_evidence(content="Main topic is compactness."), sampled=1, total=1)

    with patch(
        "hephaistos.chat.orchestrator._model_json_payload", return_value={"answer": "uncited"}
    ):
        reply = _overview_fallback_reply(
            plan,
            evidence,
            user_input="overview",
            config=ChatConfig(base_url="https://local.test/v1", model="repair"),
        )

    assert "Sample refs: [E1]" in reply
    assert "will not infer topics from filenames" in reply


def test_overview_fallback_needed_for_bad_shape() -> None:
    plan = material_overview_plan("overview")
    evidence = _turn_evidence(
        _evidence(content="Topic A"),
        _evidence("E2", "b.md", content="Topic B"),
        sampled=2,
        total=2,
    )

    assert _needs_overview_fallback(plan, "One vague sentence [E1].", evidence) is True
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
        "hephaistos.chat.orchestrator.stream_completion",
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
            "hephaistos.chat.orchestrator._classified_user_intent", return_value="material_review"
        ),
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", return_value=resolved),
        patch(
            "hephaistos.chat.orchestrator.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Review [E1]"),
                    TurnCompleteEvent("Review [E1]", 0, 1.0, "stop", 100),
                ]
            ),
        ),
        patch("hephaistos.chat.orchestrator.verify_response", return_value=""),
        patch("hephaistos.chat.orchestrator.schedule_memory_extraction"),
        patch("hephaistos.chat.orchestrator.save_usage"),
    ):
        events = list(orchestrator.iter_events("review"))

    operations = [event.operation for event in events if isinstance(event, MaterialOperationEvent)]
    assert "open_stored_evidence" in operations
    assert any(isinstance(event, NoticeEvent) and event.code == "evidence" for event in events)


def test_plain_orchestrator_does_not_classify_without_armory() -> None:
    session = _session(armory=False)
    orchestrator = TurnOrchestrator(session)

    with (
        patch("hephaistos.chat.orchestrator._classified_user_intent") as classify,
        patch(
            "hephaistos.chat.orchestrator.stream_completion",
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
            "hephaistos.chat.orchestrator._classified_user_intent",
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
