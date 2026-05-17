"""Tests for hephaistos.chat.orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
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
    assess_turn_evidence,
    build_overview_context,
    build_priority_context,
    build_priority_turn_evidence,
    build_turn_evidence_from_overview,
    build_turn_evidence_from_query,
    build_turn_evidence_from_refs,
    ensure_rag_index,
    evidence_assessment_trace,
    evidence_refs,
    is_overview_query,
    parse_source_ref,
    query_demands_source_only_answer,
    resolve_turn_evidence,
)
from hephaistos.chat.orchestrator import (
    TurnOrchestrator,
    _evidence_notice,
    _evidence_notice_metadata,
    _insufficient_evidence_reply,
    _large_corpus_local_overview_reply,
    _localize_deterministic_reply,
    _model_normalized_study_plan,
    _needs_overview_fallback,
    _normalized_study_intent_from_payload,
    _overview_answer_has_bad_shape,
    _overview_fallback_reply,
    _overview_topic_is_useful,
    _overview_topic_items,
    _overview_topic_items_from_model_payload,
    _overview_topic_looks_like_metadata,
    _repair_pedagogy_shape,
    _run_bounded_internal_repairs,
    _study_autopilot_context,
    _user_visible_reply,
)
from hephaistos.chat.session import ChatSession
from hephaistos.rag import ArmoryIndex, ScoredChunk, TurnEvidence
from hephaistos.rag.chunker import Chunk, ChunkedDocument
from hephaistos.rag.context import EvidenceChunk
from hephaistos.study import (
    StudyAction,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
    StudyTurnPlan,
    material_overview_plan,
    plan_turn,
)
from hephaistos.study.priority import PriorityWebSearchResult
from hephaistos.study.schedule import load_study_schedule
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


def test_repair_pedagogy_shape_does_not_append_english_confidence_request() -> None:
    plan = plan_turn(
        StudyState(
            autonomy_mode=StudyAutonomyMode.GUIDED,
            phase=StudyPhase.WAITING_FOR_READY,
            current_item="compactness",
        ),
        "ready",
    )

    repaired = _repair_pedagogy_shape(plan, "Define compactness from memory.")

    assert repaired == "Define compactness from memory."
    assert "Include your confidence from 0-100%." not in repaired


def test_bounded_internal_repair_loop_does_not_append_english_pedagogy_scaffold() -> None:
    plan = plan_turn(
        StudyState(
            autonomy_mode=StudyAutonomyMode.GUIDED,
            phase=StudyPhase.WAITING_FOR_READY,
            current_item="compactness",
        ),
        "ready",
    )

    repaired, passes = _run_bounded_internal_repairs(
        plan,
        "Definiere Kompaktheit und nenne deine Sicherheit von 0-100%.",
        None,
    )

    assert passes <= 3
    assert repaired == "Definiere Kompaktheit und nenne deine Sicherheit von 0-100%."
    assert "Include your confidence from 0-100%." not in repaired
    assert "Next action:" not in repaired


def test_german_overview_repair_does_not_append_english_study_scaffold() -> None:
    plan = material_overview_plan("um was geht es in den dateien")
    reply = (
        "Die Dateien geben einen Überblick über die wichtigsten mathematischen "
        "Zusammenhänge und Übungsformen [E1] [E2]."
    )

    repaired, passes = _run_bounded_internal_repairs(plan, reply, None)

    assert passes <= 3
    assert repaired == reply
    assert "Include your confidence from 0-100%" not in repaired
    assert "Next action:" not in repaired
    assert "Say ready" not in repaired


def test_repair_pedagogy_shape_does_not_append_english_recommendation_reason() -> None:
    plan = plan_turn(StudyState(autonomy_mode=StudyAutonomyMode.GUIDED), "Explain compactness")

    repaired = _repair_pedagogy_shape(
        plan,
        "Compactness is source-backed. Next action: try one similar recall prompt.",
    )

    assert repaired == "Compactness is source-backed. Next action: try one similar recall prompt."
    assert "Why this helps:" not in repaired


def test_user_visible_reply_strips_inline_tool_call_markup() -> None:
    plan = _make_study_plan(action=StudyAction.PRESENT)
    raw = (
        '<tool_call name="search_materials">{"query":"what can i use this for","top_k":5}'
        "</tool_call>No searchable armory evidence was found."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert cleaned == "No searchable armory evidence was found."


def test_overview_user_visible_reply_strips_trailing_study_loop_boilerplate() -> None:
    plan = material_overview_plan("um was geht es in den dateien")
    raw = (
        "Die Dateien behandeln Mathematik fuer Informatiker [E1][E2].\n"
        "- Ein Schwerpunkt sind Reihen und Konvergenzkriterien [E1].\n"
        "- Ein weiterer Schwerpunkt sind Taylor-Polynome und Approximationen [E2].\n\n"
        "Am sinnvollsten ist jetzt, den kleinsten source-backed Block zu wiederholen. "
        "Danach Recall.\n\n"
        "Next action: Review the smallest source-backed piece, then ask for recall."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert "Die Dateien behandeln Mathematik" in cleaned
    assert "Taylor-Polynome" in cleaned
    assert "Am sinnvollsten" not in cleaned
    assert "Next action" not in cleaned
    assert "source-backed" not in cleaned


def test_overview_user_visible_reply_strips_short_uncited_recall_footer() -> None:
    plan = material_overview_plan("um was geht es in den dateien")
    raw = (
        "Der Korpus gibt eine quellenbelegte Orientierung zu Mathematik [E1][E2].\n"
        "1. Folgen und Reihen werden ueber Grenzwerte und Partialsummen vorbereitet [E1].\n"
        "2. Ableitungen und Approximationen verbinden Funktionen mit Rechenregeln [E2].\n\n"
        "Danach Recall."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert "Der Korpus gibt" in cleaned
    assert "Approximationen" in cleaned
    assert "Danach Recall" not in cleaned


def test_source_qa_user_visible_reply_strips_trailing_study_loop_footer() -> None:
    plan = _make_study_plan(action=StudyAction.SOURCE_QA)
    raw = (
        "Die Quelle verbindet Enzymkinetik mit Substratkonzentration und "
        "Reaktionsgeschwindigkeit [E1].\n\n"
        "Next action: Review the smallest source-backed piece, then ask for recall."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert "Enzymkinetik" in cleaned
    assert "Next action" not in cleaned
    assert "source-backed" not in cleaned


def test_source_qa_user_visible_reply_strips_inline_say_ready_footer() -> None:
    plan = _make_study_plan(action=StudyAction.SOURCE_QA)
    raw = (
        "Die Graphs-Vorlesung gehoert zu Algorithms, AI & Data Science II [E7]. "
        "Say ready when you want recall."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert cleaned == "Die Graphs-Vorlesung gehoert zu Algorithms, AI & Data Science II [E7]."
    assert "Say ready" not in cleaned


def test_source_qa_user_visible_reply_keeps_cited_active_recall_content() -> None:
    plan = _make_study_plan(action=StudyAction.SOURCE_QA)
    raw = (
        "Die Quelle beschreibt Lernmethoden [E1].\n"
        "- Active recall asks the user to produce an answer from memory [E1]."
    )

    cleaned = _user_visible_reply(plan, raw)

    assert cleaned == raw


def test_overview_bad_shape_rejects_chronological_walkthrough_without_dates() -> None:
    raw = (
        "The material is about applied mathematics and exam preparation [E1][E2].\n"
        "- First, it introduces sequences and limits [E1].\n"
        "- Then, it moves to series and convergence criteria [E2].\n"
        "- Later, it covers Taylor polynomials and approximation [E1]."
    )

    assert _overview_answer_has_bad_shape(raw, None)


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_deterministic_fallback_localization_rejects_added_citations(
    mock_stream: MagicMock,
) -> None:
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "fallback-localizer"
    mock_stream.return_value = iter(
        [CompletionDelta(content="Keine Antwort in den Quellen [E1].")]
    )

    reply = _localize_deterministic_reply(
        "The enabled armory sources do not contain an answer.",
        user_input="was steht dazu in den quellen?",
        config=config,
    )

    assert reply == "The enabled armory sources do not contain an answer."


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_deterministic_fallback_localization_preserves_quoted_phrases(
    mock_stream: MagicMock,
) -> None:
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "fallback-localizer"
    mock_stream.return_value = iter(
        [CompletionDelta(content='Der genaue Ausdruck ist "bernstein forge".')]
    )

    reply = _localize_deterministic_reply(
        'The exact phrase is "amber forge".',
        user_input="was ist die genaue phrase?",
        config=config,
    )

    assert reply == 'The exact phrase is "amber forge".'


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_deterministic_fallback_localization_preserves_assessment_labels(
    mock_stream: MagicMock,
) -> None:
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "fallback-localizer"
    mock_stream.return_value = iter(
        [CompletionDelta(content="TEILWEISE: Ich konnte keine Bewertung erzeugen.")]
    )

    reply = _localize_deterministic_reply(
        "PARTIAL: I could not generate a grounded assessment.",
        user_input="bewerte meine antwort",
        config=config,
    )

    assert reply == "PARTIAL: I could not generate a grounded assessment."


@pytest.mark.parametrize(
    (
        "intent",
        "user_input",
        "expected_action",
        "expected_query",
        "expected_allow_tools",
        "expected_buffer",
        "prompt_bits",
    ),
    [
        (
            "source_qa",
            "was sagt das material ueber enzymkinetik?",
            StudyAction.SOURCE_QA,
            "enzyme kinetics in the material",
            False,
            True,
            ("Execute SOURCE_QA", "User request: was sagt", "same language"),
        ),
        (
            "source_qa",
            "que dicen los apuntes sobre cinetica enzimatica?",
            StudyAction.SOURCE_QA,
            "enzyme kinetics in the notes",
            False,
            True,
            ("Execute SOURCE_QA", "User request: que dicen", "same language"),
        ),
        (
            "topic_presentation",
            "erklaer mir enzymkinetik",
            StudyAction.PRESENT,
            "enzyme kinetics",
            True,
            False,
            ("Execute the PRESENT phase", "User request: erklaer", "same language"),
        ),
        (
            "topic_presentation",
            "expliquez moi la cinetique enzymatique",
            StudyAction.PRESENT,
            "enzyme kinetics",
            True,
            False,
            ("Execute the PRESENT phase", "User request: expliquez", "same language"),
        ),
        (
            "topic_drill",
            "frag mich zu enzymkinetik ab",
            StudyAction.CALIBRATE,
            "enzyme kinetics",
            False,
            True,
            (
                "Execute CALIBRATE",
                "User request (language/topic signal",
                "user's language",
                "active-recall",
            ),
        ),
        (
            "topic_drill",
            "faz perguntas sobre cinetica enzimatica",
            StudyAction.CALIBRATE,
            "enzyme kinetics",
            False,
            True,
            (
                "Execute CALIBRATE",
                "User request (language/topic signal",
                "user's language",
                "active-recall",
            ),
        ),
    ],
)
@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_routes_non_english_material_intents(
    mock_stream: MagicMock,
    intent: str,
    user_input: str,
    expected_action: StudyAction,
    expected_query: str,
    expected_allow_tools: bool,
    expected_buffer: bool,
    prompt_bits: tuple[str, ...],
) -> None:
    base_plan = _make_study_plan(retrieval_query=user_input, allow_tools=True)
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    f'{{"intent":"{intent}",'
                    f'"canonical_english_request":"{expected_query}",'
                    '"confidence":0.94}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        StudyState(),
        user_input,
        config,
    )

    assert normalized_plan.action is expected_action
    assert normalized_plan.retrieval_query == expected_query
    assert normalized_plan.allow_tools is expected_allow_tools
    assert normalized_plan.buffer_response is expected_buffer
    assert all(bit in normalized_plan.prompt for bit in prompt_bits)
    intent_prompt = mock_stream.call_args.args[1].messages[0].content
    assert "English-first control signal" in intent_prompt
    assert "whatever language the user wrote" in intent_prompt
    assert (
        '"intent": "material_overview | source_qa | source_only_policy | '
        "topic_presentation | topic_drill | ready_for_recall | recall_clarification | "
        'recall_answer_attempt | chat"'
    ) in intent_prompt
    assert "topic_drill |\n" not in intent_prompt
    assert "German" not in intent_prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_keeps_low_confidence_plan(
    mock_stream: MagicMock,
) -> None:
    base_plan = _make_study_plan(retrieval_query="erzaehl mal ueber enzymkinetik")
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"topic_presentation",'
                    '"canonical_english_request":"enzyme kinetics",'
                    '"confidence":0.41}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        StudyState(),
        "erzaehl mal ueber enzymkinetik",
        config,
    )

    assert normalized_plan is base_plan


@pytest.mark.parametrize(
    ("raw_intent", "expected"),
    [
        ("source qa", "source_qa"),
        ("source-QA", "source_qa"),
        ("topic presentation", "topic_presentation"),
        ("topic/presentation", "topic_presentation"),
        ("topic drill", "topic_drill"),
        ("material overview", "material_overview"),
        ("source only policy", "source_only_policy"),
        ("ready for recall", "ready_for_recall"),
        ("recall clarification", "recall_clarification"),
        ("recall answer attempt", "recall_answer_attempt"),
    ],
)
def test_normalized_study_intent_accepts_label_spacing_variants(
    raw_intent: str,
    expected: str,
) -> None:
    normalized = _normalized_study_intent_from_payload(
        {
            "intent": raw_intent,
            "canonical_english_request": "enzyme kinetics",
            "confidence": "94%",
        }
    )

    assert normalized is not None
    assert normalized.intent == expected
    assert normalized.canonical_english_request == "enzyme kinetics"
    assert normalized.confidence == pytest.approx(0.94)


def test_normalized_study_intent_still_rejects_unsupported_label() -> None:
    normalized = _normalized_study_intent_from_payload(
        {
            "intent": "answer-the-user",
            "canonical_english_request": "enzyme kinetics",
            "confidence": 1.0,
        }
    )

    assert normalized is None


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_handles_standalone_source_only_policy(
    mock_stream: MagicMock,
) -> None:
    base_plan = _make_study_plan(
        retrieval_query="por favor no inventes informacion",
        allow_tools=True,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"source_only_policy",'
                    '"canonical_english_request":"do not use outside knowledge",'
                    '"confidence":0.93}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        StudyState(),
        "por favor no inventes informacion",
        config,
    )

    assert normalized_plan.action is StudyAction.CHAT
    assert normalized_plan.retrieval_query is None
    assert normalized_plan.allow_tools is False
    assert normalized_plan.direct_reply is not None
    assert "stick to enabled material" in normalized_plan.direct_reply


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_keeps_recall_answer_attempt(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.ASSESS,
        phase=StudyPhase.ASSESS,
        prompt="assess",
        retrieval_query="integration by parts",
        use_expected_source_refs=True,
        allow_tools=False,
        buffer_response=True,
    )
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="State integration by parts.",
        retrieval_query="integration by parts",
        expected_source_refs=["materials/calculus.md#chunk=0"],
        attempt_count=1,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"recall_answer_attempt",'
                    '"canonical_english_request":"integral u dv equals uv minus integral v du",'
                    '"confidence":0.95}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "Integral u dv equals uv minus integral v du. Confidence 80%",
        config,
    )

    assert normalized_plan is base_plan


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_reclassifies_recall_source_question(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.ASSESS,
        phase=StudyPhase.ASSESS,
        prompt="assess",
        retrieval_query="integration by parts",
        use_expected_source_refs=True,
        allow_tools=False,
        buffer_response=True,
    )
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="State integration by parts.",
        retrieval_query="integration by parts",
        expected_source_refs=["materials/calculus.md#chunk=0"],
        attempt_count=1,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"source_qa",'
                    '"canonical_english_request":"Bayes theorem in the notes",'
                    '"confidence":0.95}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "was sagen die quellen zu Bayes?",
        config,
    )

    assert normalized_plan.action is StudyAction.SOURCE_QA
    assert normalized_plan.phase is StudyPhase.PRESENTING
    assert normalized_plan.retrieval_query == "Bayes theorem in the notes"
    assert normalized_plan.allow_tools is False
    assert normalized_plan.buffer_response is True
    assert "Execute SOURCE_QA" in normalized_plan.prompt
    assert "User request: was sagen die quellen zu Bayes?" in normalized_plan.prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_reclassifies_recall_clarification(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.ASSESS,
        phase=StudyPhase.ASSESS,
        prompt="assess",
        retrieval_query="integration by parts",
        use_expected_source_refs=True,
        allow_tools=False,
        buffer_response=True,
    )
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="State integration by parts.",
        retrieval_query="integration by parts",
        expected_source_refs=["materials/calculus.md#chunk=0"],
        attempt_count=1,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"recall_clarification",'
                    '"canonical_english_request":'
                    '"repeat the prompt in the requested language",'
                    '"confidence":0.95}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "frag mich nochmal auf deutsch",
        config,
    )

    assert normalized_plan.action is StudyAction.PROMPT_RECALL
    assert normalized_plan.phase is StudyPhase.RECALL
    assert normalized_plan.retrieval_query is None
    assert normalized_plan.allow_tools is False
    assert "Execute RECALL_CLARIFICATION" in normalized_plan.prompt
    assert "User request: frag mich nochmal auf deutsch" in normalized_plan.prompt
    assert "Do not assess the user" in normalized_plan.prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_routes_chat_intent_without_material_search(
    mock_stream: MagicMock,
) -> None:
    base_plan = _make_study_plan(
        retrieval_query="que puedes hacer?",
        allow_tools=True,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"chat",'
                    '"canonical_english_request":"what can you do?",'
                    '"confidence":0.91}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        StudyState(),
        "que puedes hacer?",
        config,
    )

    assert normalized_plan.action is StudyAction.CHAT
    assert normalized_plan.retrieval_query is None
    assert normalized_plan.allow_tools is False
    assert "HEPH chat mode" in normalized_plan.prompt
    assert "que puedes hacer?" in normalized_plan.prompt
    assert "Execute the PRESENT phase" not in normalized_plan.prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_reclassifies_non_english_ready_wait_followup(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.REVIEW,
        phase=StudyPhase.PRESENTING,
        prompt="follow-up",
        retrieval_query="conditional probability",
        use_expected_source_refs=True,
        allow_tools=False,
    )
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"source_qa",'
                    '"canonical_english_request":"Bayes theorem in the notes",'
                    '"confidence":0.92}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "was sagen die notizen ueber den satz von bayes?",
        config,
    )

    assert normalized_plan.action is StudyAction.SOURCE_QA
    assert normalized_plan.retrieval_query == "Bayes theorem in the notes"
    assert normalized_plan.use_expected_source_refs is False
    assert "User request: was sagen die notizen" in normalized_plan.prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_reclassifies_non_english_ready_signal(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.REVIEW,
        phase=StudyPhase.PRESENTING,
        prompt="follow-up",
        retrieval_query="conditional probability",
        use_expected_source_refs=True,
        allow_tools=False,
    )
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Definiere bedingte Wahrscheinlichkeit.",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"ready_for_recall",'
                    '"canonical_english_request":"ready",'
                    '"confidence":0.96}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "ich bin bereit",
        config,
    )

    assert normalized_plan.action is StudyAction.PROMPT_RECALL
    assert normalized_plan.phase is StudyPhase.RECALL
    assert normalized_plan.retrieval_query is None
    assert normalized_plan.use_expected_source_refs is False
    assert normalized_plan.allow_tools is False
    assert "Execute RECALL" in normalized_plan.prompt
    assert "same language as the current item" in normalized_plan.prompt


@patch("hephaistos.chat.orchestrator.stream_completion")
def test_model_normalized_study_plan_does_not_reclassify_recall_assessment(
    mock_stream: MagicMock,
) -> None:
    base_plan = StudyTurnPlan(
        action=StudyAction.ASSESS,
        phase=StudyPhase.ASSESS,
        prompt="assess",
        retrieval_query="conditional probability",
        use_expected_source_refs=True,
        allow_tools=False,
        buffer_response=True,
    )
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )
    config = ChatConfig()
    config.base_url = "https://local.test/v1"
    config.model = "intent-normalizer"
    mock_stream.return_value = iter(
        [
            CompletionDelta(
                content=(
                    '{"intent":"recall_answer_attempt",'
                    '"canonical_english_request":"conditional probability answer",'
                    '"confidence":0.92}'
                )
            )
        ]
    )

    normalized_plan = _model_normalized_study_plan(
        base_plan,
        state,
        "die wahrscheinlichkeit unter einer bedingung",
        config,
    )

    assert normalized_plan is base_plan
    mock_stream.assert_called_once()


def test_study_autopilot_context_reads_schedule_learner_state(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="autopilot-context",
        armory_path=tmp_path,
    )
    store = load_study_schedule(tmp_path)
    store.record_review(
        "Contrast injective and surjective maps",
        concept="injective vs surjective",
        retrieval_query="functions",
        source_refs=["materials/lecture.md#chunk=3"],
        rating=StudyRecallRating.HARD,
        elapsed_seconds=90,
        confidence=0.9,
        error_type="wrong",
        intervention="contrastive_question",
        now=datetime(2024, 1, 1, tzinfo=UTC),
    )
    store.save()

    due_reviews, memory_state = _study_autopilot_context(session)

    assert due_reviews[0].concept == "injective vs surjective"
    assert memory_state.weak_topics == ("injective vs surjective",)
    assert memory_state.misconceptions == ("injective vs surjective",)
    assert memory_state.failed_interventions == ("contrastive_question",)


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
    plan = _make_study_plan(action=StudyAction.SOURCE_QA)
    assessment = assess_turn_evidence(plan, evidence)

    metadata = _evidence_notice_metadata(
        ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assessment,
        )
    )

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
    assert metadata["assessment"] == {
        "sufficient": True,
        "confidence": 0.887,
        "supporting_refs": ["materials/a.md#chunk=0", "materials/b.md#chunk=2"],
        "missing_information": [],
        "conflicts": [],
        "source_diversity_score": 0.667,
        "recommended_action": "answer",
    }


def test_evidence_notice_discloses_partial_source_only_support() -> None:
    evidence = _make_turn_evidence(_make_evidence_chunk("materials/a.md", 0, "E1"))
    plan = _make_study_plan(action=StudyAction.SOURCE_QA, retrieval_query="using only sources")
    assessment = assess_turn_evidence(plan, evidence)

    notice = _evidence_notice(
        ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=evidence,
            evidence_assessment=assessment,
        )
    )

    assert "Using 1 retrieved evidence excerpt: materials/a.md#chunk=0" in notice
    assert "Evidence sufficiency: give partial answer (48%)." in notice


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

    assert "These are the topics I found in the material:" in reply
    assert "Retrieved overview sample" not in reply
    assert "not an exhaustive summary" not in reply
    assert "indexed sources" not in reply
    assert "corpus-level claim" not in reply
    assert "document signal" not in reply.casefold()
    assert "Other material signals" not in reply
    assert "sampled" not in reply.casefold()
    assert "Choose a topic to explore next. In the shell, use ↑/↓ and press Enter." in reply
    assert "Recommended options:" in reply
    assert "graph algorithms [e1]" in reply.casefold()
    assert "recurrence [e1]" in reply.casefold()
    assert "[E2]" in reply
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


def test_overview_fallback_does_not_append_english_menu_for_non_latin_request() -> None:
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
            "materials/lecture-2.pdf",
            0,
            "E2",
            "Lecture notes. Dynamic programming uses recurrence relations to build solutions.",
        ),
    )

    reply = _overview_fallback_reply(plan, evidence, user_input="这些文件讲什么?")

    assert "[E1]" in reply
    assert "[E2]" in reply
    assert "These are the topics" not in reply
    assert "Choose a topic to explore next" not in reply
    assert "Recommended options" not in reply


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
        must_include=("topics", "Choose a topic"),
        must_not_include=("the files cover", "no evidence citations", "sampled orientation"),
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
            "These are the topics I found in the material [E1][E2].\n"
            "- Graph algorithms [E1].\n"
            "- Recurrence relations [E2].\n"
            "- Bayes theorem [E1].\n"
            "Use the shell menu to choose one cited topic for guided learning next."
        ),
        evidence,
    )


def test_overview_shape_rejects_uncited_or_too_thin_summaries() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/lecture.pdf", 0, "E1"),
        _make_evidence_chunk("materials/exam.pdf", 0, "E2"),
    )

    assert _overview_answer_has_bad_shape(
        "These are the topics I found in the material [E1].",
        evidence,
    )
    assert _overview_answer_has_bad_shape(
        "These are the topics I found in the material [E1][E2].\n"
        "- Lecture material appears in the material.\n"
        "- Exam material appears in the material.\n"
        "- Choose a topic to explore next.",
        evidence,
    )
    assert _overview_answer_has_bad_shape(
        "The material is about graph algorithms and recurrence relations [E1][E2].\n"
        "- Graph algorithms [E1].\n"
        "- Recurrence relations [E2].\n"
        "Next action: Review the smallest source-backed piece, then ask for recall.",
        evidence,
    )
    assert _overview_answer_has_bad_shape(
        "The material is about graph algorithms and recurrence relations [E1][E2].\n"
        "- Graph algorithms [E1].\n"
        "- Recurrence relations [E2].\n"
        "This is only a sample, not a non-exhaustive list of every source [E1].",
        evidence,
    )
    assert _overview_answer_has_bad_shape(
        "Der Korpus behandelt Mathematik fuer Informatiker 2 [E1][E2].\n"
        "- In den Folien vom 22. April geht es um Reihen und Potenzreihen [E1].\n"
        "- In den Folien vom 15. April geht es um Folgen und Grenzwerte [E2].\n"
        "- In den Folien vom 4. Mai geht es um Taylor-Polynome [E1].",
        evidence,
    )
    assert not _overview_answer_has_bad_shape(
        "These are the topics I found in the material [E1][E2].\n"
        "- Graph algorithms [E1].\n"
        "- Recurrence relations [E2].\n"
        "- Bayes theorem [E1].\n"
        "Use the shell menu to choose one cited topic for guided learning next.",
        evidence,
    )
    assert not _overview_answer_has_bad_shape(
        "Die Materialien geben eine quellenbelegte Orientierung zu Mathematik und "
        "Biochemie [E1] [E2].\n"
        "- Folgen und Reihen werden ueber Grenzwerte und Partialsummen vorbereitet [E1].\n"
        "- Enzymkinetik wird mit Reaktionsgeschwindigkeit und Proteinstruktur verbunden [E2].",
        evidence,
    )


def test_large_corpus_local_overview_is_concise_cited_and_not_boilerplate() -> None:
    plan = material_overview_plan("what is the material about")
    evidence = TurnEvidence(
        items=(
            _make_evidence_chunk(
                "materials/linear-algebra.md",
                0,
                "E1",
                "Lecture notes. Linear algebra studies vectors, matrices, bases, and rank.",
            ),
            _make_evidence_chunk(
                "materials/graph-search-exam.pdf",
                0,
                "E2",
                "Final exam. Explain breadth-first search and depth-first search. Points: 10.",
            ),
            _make_evidence_chunk(
                "materials/dynamic-programming-slides.pdf",
                0,
                "E3",
                "Lecture slides. Dynamic programming compares recursive and iterative methods.",
            ),
        ),
        sampled_source_count=32,
        total_source_count=382,
    )

    reply = _large_corpus_local_overview_reply(
        plan,
        evidence,
        user_input="what is the material about",
    )

    assert reply
    assert "- " in reply
    assert "[E1]" in reply
    assert "[E2]" in reply
    assert "Visible topics" not in reply
    assert "Sampled orientation" not in reply
    assert "non-exhaustive" not in reply
    assert not _overview_answer_has_bad_shape(reply, evidence)


def test_overview_shape_rejects_non_topic_menu_labels() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk("materials/lecture.pdf", 0, "E1"),
        _make_evidence_chunk("materials/exam.pdf", 0, "E2"),
    )

    assert _overview_answer_has_bad_shape(
        "These are the topics I found in the material [E1][E2].\n"
        "- Definition only [E1].\n"
        "- Administrative Header 2 [E1].\n"
        "- exam-style questions or structured assessment prompts [E2].\n"
        "Use the shell menu to choose one cited topic for guided learning next.",
        evidence,
    )


def test_overview_topic_metadata_filter_removes_title_page_person_names() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/lecture.pdf",
            0,
            "E1",
            "## Introduction to Biology\n\nAdministrative line\n\nAdministrative block\n\n2026",
        )
    )

    assert _overview_topic_looks_like_metadata("administrative line", evidence)
    assert not _overview_topic_looks_like_metadata("biology", evidence)


def test_overview_topic_filter_rejects_generic_lecture_scaffolding() -> None:
    assert not _overview_topic_is_useful("definition")
    assert not _overview_topic_is_useful("definitions")
    assert not _overview_topic_is_useful("theorems")
    assert not _overview_topic_is_useful("proofs")
    assert not _overview_topic_is_useful("today speaking")
    assert not _overview_topic_is_useful("last time")
    assert not _overview_topic_is_useful("table")
    assert not _overview_topic_is_useful("achtung")
    assert not _overview_topic_is_useful("Administrative Header 2")
    assert not _overview_topic_is_useful("exam-style questions or structured assessment prompts")
    assert not _overview_topic_is_useful("Let X be a set, then define a mapping")
    assert _overview_topic_is_useful("signal entropy")
    assert _overview_topic_is_useful("matrix multiplication")
    assert _overview_topic_is_useful("Bayes theorem")
    assert _overview_topic_is_useful("graph")


def test_overview_topic_items_use_general_definition_and_web_validation() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/signals.pdf",
            0,
            "E1",
            "Administrative Header 2 Sommersemester 2026. "
            "Signal entropy is a measure of uncertainty in observations.",
        ),
        _make_evidence_chunk(
            "materials/signals.pdf",
            1,
            "E2",
            "A carrier wave is a reference waveform for modulation.",
        ),
        _make_evidence_chunk(
            "materials/biology.pdf",
            2,
            "E3",
            "Protein folding is the process where a chain reaches its native structure.",
        ),
        _make_evidence_chunk(
            "materials/cs.pdf",
            3,
            "E4",
            "A hash table is a data structure for key value lookup.",
        ),
    )

    def web_searcher(query: str) -> tuple[PriorityWebSearchResult, ...]:
        supported = ("signal entropy", "carrier wave", "protein folding", "hash table")
        snippet = (
            "Course topic overview for signal entropy, carrier wave, protein folding, "
            "and hash table."
        )
        if not any(term in query.casefold() for term in supported):
            snippet = "Course topic overview for unrelated material."
        return (
            PriorityWebSearchResult(
                title="Course topic",
                url="https://example.test/topic",
                snippet=snippet,
            ),
        )

    topics = _overview_topic_items(evidence, web_searcher=web_searcher)
    labels = [topic.rsplit(" [", maxsplit=1)[0] for topic in topics]

    assert "Administrative Header 2" not in labels
    assert {"Signal entropy", "Carrier wave", "Protein folding", "Hash table"} <= set(labels)


def test_overview_topic_items_are_not_math_specific() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/biochem.md",
            0,
            "E1",
            "Enzyme kinetics is the study of reaction rates.",
        ),
        _make_evidence_chunk(
            "materials/biochem.md",
            1,
            "E2",
            "Protein folding is the process where a chain reaches its native structure.",
        ),
        _make_evidence_chunk(
            "materials/cs.md",
            0,
            "E3",
            "A hash table is a data structure for key value lookup.",
        ),
    )

    def web_searcher(query: str) -> tuple[PriorityWebSearchResult, ...]:
        supported = ("enzyme kinetics", "protein folding", "hash table")
        snippet = "Syllabus topics include enzyme kinetics, protein folding, and hash table."
        if not any(term in query.casefold() for term in supported):
            snippet = "Syllabus topics include unrelated review material."
        return (
            PriorityWebSearchResult(
                title="Course topic overview",
                url="https://example.test/topics",
                snippet=snippet,
            ),
        )

    labels = [
        topic.rsplit(" [", maxsplit=1)[0]
        for topic in _overview_topic_items(evidence, web_searcher=web_searcher)
    ]

    normalized_labels = {label.casefold() for label in labels}
    assert "enzyme kinetics" in normalized_labels
    assert "protein folding" in normalized_labels
    assert "hash table" in normalized_labels


def test_overview_model_topic_items_require_exact_evidence_quotes() -> None:
    evidence = _make_turn_evidence(
        _make_evidence_chunk(
            "materials/signals.pdf",
            0,
            "E1",
            "Signal entropy is a measure of uncertainty in observations.",
        )
    )
    payload: dict[str, object] = {
        "topics": [
            {
                "canonical_english": "quantum mechanics",
                "display_label": "Quantum mechanics",
                "evidence_id": "E1",
                "evidence_quote": "quantum mechanics",
            },
            {
                "canonical_english": "signal entropy",
                "display_label": "Signal entropy",
                "evidence_id": "E1",
                "evidence_quote": "Signal entropy",
            },
        ]
    }

    topics = _overview_topic_items_from_model_payload(payload, evidence)

    assert topics == ["Signal entropy [E1]"]


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

    assert "geometric series [e1]" in reply.casefold()
    assert "&lt;" not in reply
    assert "Practice one exam-style or exercise question" in reply
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
        assert plan.evidence_assessment is None

    def test_with_values(self) -> None:
        study_plan = _make_study_plan()
        evidence = _make_turn_evidence(_make_evidence_chunk())
        assessment = assess_turn_evidence(study_plan, evidence)
        plan = ResolvedTurnPlan(
            study_plan=study_plan,
            turn_evidence=evidence,
            evidence_assessment=assessment,
        )
        assert plan.study_plan is study_plan
        assert plan.turn_evidence is evidence
        assert plan.evidence_assessment is assessment

    def test_frozen(self) -> None:
        plan = ResolvedTurnPlan()
        with pytest.raises(AttributeError):
            plan.study_plan = _make_study_plan()  # ty:ignore[invalid-assignment]


def test_assess_turn_evidence_flags_weak_source_only_support() -> None:
    plan = _make_study_plan(
        action=StudyAction.SOURCE_QA,
        retrieval_query="Using only the indexed sources, what is the phrase?",
    )
    evidence = _make_turn_evidence(_make_evidence_chunk("materials/a.md", 0, "E1"))

    assessment = assess_turn_evidence(plan, evidence)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "give_partial_answer"
    assert assessment.supporting_refs == ("materials/a.md#chunk=0",)
    assert "corroborating source span" in assessment.missing_information


@pytest.mark.parametrize(
    "query",
    [
        "What do my notes say about Bayes theorem?",
        "Do the slides mention Lagrange multipliers?",
        "According to my lecture notes, what is the definition of entropy?",
        "Based on the PDF, what is the exact formula?",
        "If my uploaded documents do not contain it, do not guess.",
        "Can you check my notes for Bayes theorem?",
        "Find Lagrange multipliers in the slides.",
        "Summarize my notes on Bayes theorem.",
        "List the formulas from my lecture notes.",
        "What page mentions Lagrange multipliers?",
        "Which slide explains Lagrange multipliers?",
        "What does the textbook say about Bayes theorem?",
        "According to the reading, what is entropy?",
        "Can you check the workbook for Lagrange multipliers?",
        "Find eigenvalues in the worksheet.",
        "What does the assignment ask us to prove?",
        "Summarize the problem set on induction.",
        "Does the syllabus mention Bayes theorem?",
        "What does the mark scheme say about partial credit?",
        "Based on the paper, what is the method?",
        "Look through the article for the theorem.",
        "Rely only on the lecture notes for this.",
        "Stick to the source material.",
        "What does the source material say about entropy?",
        "Where did the slides explain Lagrange multipliers?",
        "What do the course notes say about Bayes theorem?",
        "According to the class notes, what is entropy?",
        "Based on the study guide, what is the formula?",
        "From the course pack, define entropy.",
        "Using the attached documents, what is the theorem?",
        "If the attached files do not contain it, do not guess.",
        "Show me where the slides explain Bayes theorem.",
        "Which document covers Bayes theorem?",
        "Which source says entropy is conserved?",
        "Can you cite the notes for the theorem?",
        "Point me to the lecture notes that define entropy.",
        "Base your answer on the textbook only.",
        "If my notes do not mention it, say so.",
        "If it is not in the slides, say so.",
    ],
)
def test_source_only_detection_accepts_common_material_references(query: str) -> None:
    assert query_demands_source_only_answer(query)


@pytest.mark.parametrize(
    "query",
    [
        "do not guess",
        "please do not guess",
        "don't guess",
        "don't hallucinate",
        "do not use outside knowledge",
        "no outside knowledge",
        "don't make it up",
        "say you don't know",
    ],
)
def test_source_only_detection_accepts_standalone_abstention_policy(query: str) -> None:
    assert query_demands_source_only_answer(query)


def test_assess_turn_evidence_keeps_empty_present_query_retrievable() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="what is this material about overall",
    )

    assessment = assess_turn_evidence(plan, None)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "retrieve_more"


def test_empty_present_retrieve_more_falls_back_to_overview_guidance() -> None:
    plan = _make_study_plan(
        action=StudyAction.PRESENT,
        retrieval_query="Do some math",
    )
    assessment = assess_turn_evidence(plan, None)
    resolved = ResolvedTurnPlan(
        study_plan=plan,
        turn_evidence=None,
        evidence_assessment=assessment,
    )

    reply = _insufficient_evidence_reply(plan, resolved)

    assert reply
    assert "need one clarification" not in reply.casefold()
    assert "material overview" in reply.casefold()
    assert "pick one source-backed topic" in reply.casefold()


def test_assess_turn_evidence_routes_assess_without_evidence_to_quiz_first() -> None:
    plan = _make_study_plan(
        action=StudyAction.ASSESS,
        retrieval_query="grade this recall answer against the source",
    )

    assessment = assess_turn_evidence(plan, None)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "quiz_first"


def test_evidence_assessment_trace_is_json_friendly() -> None:
    plan = _make_study_plan(action=StudyAction.SOURCE_QA)
    assessment = assess_turn_evidence(plan, None)

    trace = evidence_assessment_trace(assessment)

    assert trace == {
        "sufficient": False,
        "confidence": 0.0,
        "supporting_refs": [],
        "missing_information": ["source span that directly answers the source-only question"],
        "conflicts": [],
        "source_diversity_score": 0.0,
        "recommended_action": "abstain",
    }


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
        assert len(deltas) == 1
        assert "material-backed study" in deltas[0]
        assert "/autopilot on" in deltas[0]
        assert session.last_turn_evidence is None
        mock_stream.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    def test_plain_direct_reply_localizes_when_model_configured(
        self,
        mock_stream: MagicMock,
    ) -> None:
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        "Hey. Ich kann quellenbasiertes Lernen mit /exam, /priority "
                        "oder /autopilot on starten."
                    )
                )
            ]
        )
        session = _make_plain_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "localizer"
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("hey"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == [
            "Hey. Ich kann quellenbasiertes Lernen mit /exam, /priority "
            "oder /autopilot on starten."
        ]
        assert session.conversation.messages[-1].content == deltas[0]
        assert "/exam" in deltas[0]
        assert "/priority" in deltas[0]
        assert "/autopilot" in deltas[0]

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
    def test_plain_empty_model_response_yields_visible_fallback(
        self,
        mock_stream: MagicMock,
    ) -> None:
        mock_stream.return_value = iter([])
        session = _make_plain_session()
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("tell me what to do next"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["I could not generate a response. Please try again."]
        assert orch.last_reply == "I could not generate a response. Please try again."
        assert session.conversation.messages[-1].content == orch.last_reply

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
        assert reply_trace.kwargs["reply_excerpt"].startswith(
            "chunk1chunk2 - notes: evidence content [E1]"
        )
        assert reply_trace.kwargs["internal_passes"] >= 1
        assert reply_trace.kwargs["internal_pass_max"] == 3
        assert "learner_assessment" in reply_trace.kwargs
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

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_recall_reprompt_language_request_does_not_grade(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("Erklaere die Aufgabe noch einmal aus dem Gedaechtnis.")]
        )

        session = _make_study_session()
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="Explain integration by parts.",
            retrieval_query="integration by parts",
            attempt_count=1,
        )
        session.conversation.add(
            "assistant",
            "Solution: integrate u dv as uv minus the integral of v du.",
        )

        events = list(TurnOrchestrator(session).iter_events("ask me again in German"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        agent_conversation = mock_iter_agent.call_args.args[1]
        assert deltas == ["Erklaere die Aufgabe noch einmal aus dem Gedaechtnis."]
        assert "Execute RECALL_CLARIFICATION" in extra_prompt
        assert "User request: ask me again in German" in extra_prompt
        assert "Execute ASSESS" not in extra_prompt
        assert mock_iter_agent.call_args.kwargs["turn_evidence"] is None
        assert mock_iter_agent.call_args.kwargs["tool_schemas"] == []
        assert agent_conversation is not session.conversation
        assert [message.role for message in agent_conversation.messages] == ["user"]
        assert agent_conversation.messages[0].content == "ask me again in German"
        assert "Solution:" not in " ".join(
            message.content for message in agent_conversation.messages
        )
        assert session.study_state.phase is StudyPhase.RECALL
        assert session.study_state.attempt_count == 1

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_non_english_recall_clarification_uses_model_normalized_prompt(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("Erklaere die Aufgabe noch einmal aus dem Gedaechtnis.")]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"intent":"recall_clarification",'
                        '"canonical_english_request":'
                        '"repeat the prompt in the requested language",'
                        '"confidence":0.96}'
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="Explain integration by parts.",
            retrieval_query="integration by parts",
            attempt_count=1,
        )

        events = list(TurnOrchestrator(session).iter_events("frag mich nochmal auf deutsch"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert deltas == ["Erklaere die Aufgabe noch einmal aus dem Gedaechtnis."]
        assert resolved_plan.action is StudyAction.PROMPT_RECALL
        assert resolved_plan.phase is StudyPhase.RECALL
        assert "Execute RECALL_CLARIFICATION" in extra_prompt
        assert "User request: frag mich nochmal auf deutsch" in extra_prompt
        assert "Execute ASSESS" not in extra_prompt
        assert session.study_state.phase is StudyPhase.RECALL
        assert session.study_state.attempt_count == 1

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_non_english_ready_signal_uses_model_normalized_recall_transition(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("Gib die Definition jetzt aus dem Gedaechtnis wieder.")]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"intent":"ready_for_recall",'
                        '"canonical_english_request":"ready",'
                        '"confidence":0.97}'
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        session.study_state = StudyState(
            phase=StudyPhase.WAITING_FOR_READY,
            current_item="Definiere bedingte Wahrscheinlichkeit.",
            retrieval_query="conditional probability",
            expected_source_refs=["materials/notes.md#chunk=0"],
        )

        events = list(TurnOrchestrator(session).iter_events("ich bin bereit"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        assert deltas == ["Gib die Definition jetzt aus dem Gedaechtnis wieder."]
        assert resolved_plan.action is StudyAction.PROMPT_RECALL
        assert resolved_plan.retrieval_query is None
        assert "Execute RECALL" in extra_prompt
        assert "same language as the current item" in extra_prompt
        assert "SOURCE_FOLLOWUP" not in extra_prompt
        assert session.study_state.phase is StudyPhase.RECALL
        assert session.study_state.last_feedback_type is StudyFeedbackType.READY

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_non_english_source_only_policy_uses_model_normalized_direct_reply(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])
        mock_stream.side_effect = [
            iter(
                [
                    CompletionDelta(
                        content=(
                            '{"intent":"source_only_policy",'
                            '"canonical_english_request":"do not use outside knowledge",'
                            '"confidence":0.96}'
                        )
                    )
                ]
            ),
            iter(
                [
                    CompletionDelta(
                        content=(
                            "Entendido. Me quedare con el material activado y avisare "
                            "cuando las fuentes no sean suficientes."
                        )
                    )
                ]
            ),
        ]

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        events = list(TurnOrchestrator(session).iter_events("por favor no inventes informacion"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        assert deltas == [
            "Entendido. Me quedare con el material activado y avisare "
            "cuando las fuentes no sean suficientes."
        ]
        assert "Verstanden" not in deltas[0]
        assert resolved_plan.action is StudyAction.CHAT
        assert resolved_plan.direct_reply is not None
        assert resolved_plan.allow_tools is False
        assert session.study_state.last_feedback_type is StudyFeedbackType.NONE
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_recall_source_only_policy_is_not_assessed(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])
        mock_stream.side_effect = [
            iter(
                [
                    CompletionDelta(
                        content=(
                            '{"intent":"source_only_policy",'
                            '"canonical_english_request":"do not use outside knowledge",'
                            '"confidence":0.96}'
                        )
                    )
                ]
            ),
            iter(
                [
                    CompletionDelta(
                        content=(
                            "Entendido. Me quedare con el material activado y avisare "
                            "cuando las fuentes no sean suficientes."
                        )
                    )
                ]
            ),
        ]

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="State integration by parts.",
            retrieval_query="integration by parts",
            expected_source_refs=["materials/calculus.md#chunk=0"],
            attempt_count=2,
        )
        events = list(TurnOrchestrator(session).iter_events("por favor no inventes informacion"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        assert deltas == [
            "Entendido. Me quedare con el material activado y avisare "
            "cuando las fuentes no sean suficientes."
        ]
        assert "Verstanden" not in deltas[0]
        assert resolved_plan.action is StudyAction.CHAT
        assert resolved_plan.direct_reply is not None
        assert session.study_state.phase is StudyPhase.RECALL
        assert session.study_state.attempt_count == 2
        assert session.study_state.last_feedback_type is StudyFeedbackType.NONE
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_recall_source_question_uses_model_normalized_source_qa(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/notes.md",
                0,
                "E1",
                "Bayes theorem relates conditional probability to prior probability.",
            )
        )
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "Die Quellen verbinden Bayes mit bedingter Wahrscheinlichkeit [E1]."
                )
            ]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"intent":"source_qa",'
                        '"canonical_english_request":"Bayes theorem in the notes",'
                        '"confidence":0.96}'
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="State integration by parts.",
            retrieval_query="integration by parts",
            expected_source_refs=["materials/calculus.md#chunk=0"],
            attempt_count=2,
        )
        events = list(TurnOrchestrator(session).iter_events("was sagen die quellen zu Bayes?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert len(deltas) == 1
        assert deltas[0].startswith(
            "Die Quellen verbinden Bayes mit bedingter Wahrscheinlichkeit [E1]."
        )
        assert "- notes: Bayes theorem relates conditional probability" in deltas[0]
        assert resolved_plan.action is StudyAction.SOURCE_QA
        assert resolved_plan.retrieval_query == "Bayes theorem in the notes"
        assert "Execute SOURCE_QA" in extra_prompt
        assert "User request: was sagen die quellen zu Bayes?" in extra_prompt
        assert "Execute ASSESS" not in extra_prompt
        assert session.study_state.phase is StudyPhase.PRESENTING
        assert session.study_state.last_feedback_type is StudyFeedbackType.NONE

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_non_material_chat_intent_skips_material_search_plan(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("Ich kann dir beim Lernen mit Hephaistos helfen.")]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"intent":"chat",'
                        '"canonical_english_request":"what can you do?",'
                        '"confidence":0.96}'
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        events = list(TurnOrchestrator(session).iter_events("que puedes hacer?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        notices = [event for event in events if isinstance(event, NoticeEvent)]
        resolved_plan = mock_resolve_evidence.call_args.args[1]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert deltas == ["Ich kann dir beim Lernen mit Hephaistos helfen."]
        assert resolved_plan.action is StudyAction.CHAT
        assert resolved_plan.retrieval_query is None
        assert resolved_plan.allow_tools is False
        assert "HEPH chat mode" in extra_prompt
        assert "que puedes hacer?" in extra_prompt
        assert [event.message for event in notices if event.code == "writing"] == [
            "Writing a response."
        ]

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_recall_heph_self_request_uses_isolated_self_help_context(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Use /models to switch models.")])

        session = _make_study_session()
        session.study_state = StudyState(
            phase=StudyPhase.RECALL,
            current_item="Explain integration by parts.",
            retrieval_query="integration by parts",
            attempt_count=1,
        )
        session.conversation.add(
            "assistant",
            "Solution: integrate u dv as uv minus the integral of v du.",
        )

        events = list(TurnOrchestrator(session).iter_events("how do I switch models in Heph?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        agent_conversation = mock_iter_agent.call_args.args[1]
        assert deltas == ["Use /models to switch models."]
        assert "HEPH self-help mode" in extra_prompt
        assert "Execute ASSESS" not in extra_prompt
        assert mock_iter_agent.call_args.kwargs["turn_evidence"] is None
        assert mock_iter_agent.call_args.kwargs["tool_schemas"] == []
        assert agent_conversation is not session.conversation
        assert [message.role for message in agent_conversation.messages] == ["user"]
        assert agent_conversation.messages[0].content == "how do I switch models in Heph?"
        assert "Solution:" not in " ".join(
            message.content for message in agent_conversation.messages
        )
        assert session.study_state.phase is StudyPhase.RECALL
        assert session.study_state.attempt_count == 1

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
    def test_non_english_read_all_request_does_not_append_english_scope_suffix(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = material_overview_plan(
            "lies bitte alle dateien",
            retrieval_query="read through all the files",
        )
        evidence = TurnEvidence(
            items=(
                _make_evidence_chunk(
                    "materials/lecture-a.md",
                    0,
                    "E1",
                    "Reihen und Konvergenzkriterien stehen im Mittelpunkt.",
                ),
                _make_evidence_chunk(
                    "materials/lecture-b.md",
                    0,
                    "E2",
                    "Taylor-Polynome und lineare Approximationen werden behandelt.",
                ),
            ),
            sampled_source_count=2,
            total_source_count=5,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "Die Unterlagen geben einen Überblick über Analysis [E1] [E2].\n"
                    "- Reihen und Konvergenzkriterien sind ein Schwerpunkt [E1].\n"
                    "- Taylor-Polynome und lineare Approximationen kommen dazu [E2]."
                )
            ]
        )

        session = _make_study_session()
        events = list(TurnOrchestrator(session).iter_events("lies bitte alle dateien"))

        operations = [event for event in events if isinstance(event, MaterialOperationEvent)]
        assert operations[-1].operation == "read_all_scope"
        reply = "".join(event.delta for event in events if isinstance(event, AssistantDeltaEvent))
        assert "Read-all scope" not in reply
        assert "I did not read every file end to end" not in reply
        assert "heph index <armory>" not in reply
        assert "[E1]" in reply
        assert "[E2]" in reply
        assert session.conversation.messages[-1].content == reply

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_german_overview_samples_corpus_without_search_or_english_scaffold(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        evidence = TurnEvidence(
            items=(
                _make_evidence_chunk(
                    "materials/lecture-a.md",
                    0,
                    "E1",
                    "Reihen und Konvergenzkriterien stehen im Mittelpunkt.",
                ),
                _make_evidence_chunk(
                    "materials/lecture-b.md",
                    0,
                    "E2",
                    "Taylor-Polynome und lineare Approximationen werden behandelt.",
                ),
            ),
            sampled_source_count=2,
            total_source_count=4,
        )
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [
                AssistantDeltaEvent(
                    "Die Dateien geben einen Überblick über Analysis für Informatiker.\n"
                    "- Ein Schwerpunkt sind Reihen und Konvergenzkriterien [E1].\n"
                    "- Ein weiterer Schwerpunkt sind Approximationen mit "
                    "Taylor-Polynomen [E2].\n\n"
                    "Am sinnvollsten ist jetzt, den kleinsten source-backed Block zu "
                    "wiederholen. Danach Recall.\n\n"
                    "Next action: Review the smallest source-backed piece, then ask for recall."
                )
            ]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"intent":"material_overview",'
                        '"canonical_english_request":"what are the materials about",'
                        '"confidence":0.96}'
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "intent-normalizer"
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("um was geht es in den dateien"))

        operations = [
            event.operation for event in events if isinstance(event, MaterialOperationEvent)
        ]
        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        extra_prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert "sample_overview" in operations
        assert "search_index" not in operations
        assert len(deltas) == 1
        assert "Include your confidence from 0-100%" not in deltas[0]
        assert "Next action:" not in deltas[0]
        assert "Say ready" not in deltas[0]
        assert "Answer in the same language" in extra_prompt
        assert "Give the big picture first" in extra_prompt
        assert "User request: um was geht es in den dateien" in extra_prompt
        assert "Autonomous study policy" not in extra_prompt
        assert session.study_state.phase is StudyPhase.PRESENTING
        assert session.study_state.current_item == ""
        assert session.study_state.expected_source_refs == []
        normalized_plan = mock_resolve_evidence.call_args.args[1]
        assert normalized_plan.retrieval_query == "what are the materials about"
        intent_prompt = mock_stream.call_args_list[0].args[1].messages[0].content
        assert "English-first control signal" in intent_prompt

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
            "These are the topics I found in the material [E1] [E2].\n"
            "- Graph algorithms [E1].\n"
            "- Recurrence relations [E2].\n"
            "- Bayes theorem [E1].\n"
            "Use the shell menu to choose one cited topic for guided learning next."
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

    @patch("hephaistos.chat.orchestrator._build_overview_context")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_guided_overview_preserves_summary_and_appends_choice_menu(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_overview_context: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture-1.pdf",
                0,
                "E1",
                "## Signal entropy\nCourse slides on uncertainty measures.",
            ),
            _make_evidence_chunk(
                "materials/lecture-2.pdf",
                0,
                "E2",
                "## Carrier waves\nNotes on modulation references.",
            ),
            _make_evidence_chunk(
                "materials/lecture-3.pdf",
                0,
                "E3",
                "## Protein folding\nNotes on native structures and interactions.",
            ),
        )
        mock_resolve_evidence.return_value = evidence
        mock_overview_context.return_value = ""
        model_reply = (
            "The indexed materials are course slides and notes for a mixed study module "
            "in 2026 [E1][E2].\n"
            "- Signal entropy is a major topic [E1].\n"
            "- Carrier waves are covered in the notes [E2].\n"
            "- Protein folding appears through native structures [E3].\n\n"
            "Recommendation: ask a contrastive question next, such as "
            '"Which topic is different between signal entropy and carrier waves?" '
            "This is beneficial "
            "because it separates closely related ideas."
        )
        mock_iter_agent.return_value = iter([AssistantDeltaEvent(model_reply)])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what are the materials about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        final_reply = deltas[0]
        assert final_reply.startswith("The indexed materials are course slides and notes")
        assert "Recommendation: ask a contrastive question next" in final_reply
        assert "These are the topics I found in the material:" in final_reply
        assert (
            "Choose a topic to explore next. In the shell, use ↑/↓ and press Enter." in final_reply
        )
        assert "Recommended options:" in final_reply
        assert "Signal entropy [E1]" in final_reply
        assert "Carrier waves [E2]" in final_reply
        assert "Protein folding [E3]" in final_reply
        assert "I could not identify precise topics" not in final_reply
        assert orch.last_reply == final_reply

    @patch("hephaistos.chat.orchestrator._build_overview_context")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_guided_overview_validates_summary_before_appending_choice_menu(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_overview_context: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture-1.pdf",
                0,
                "E1",
                "## Signal entropy\nCourse slides on uncertainty measures.",
            ),
            _make_evidence_chunk(
                "materials/lecture-2.pdf",
                0,
                "E2",
                "## Carrier waves\nNotes on modulation references.",
            ),
        )
        mock_resolve_evidence.return_value = evidence
        mock_overview_context.return_value = ""
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("The materials cover core topics [E1][E2].")]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        with patch("hephaistos.chat.orchestrator.duckduckgo_search", return_value=()):
            events = list(orch.iter_events("what are the materials about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        final_reply = deltas[0]
        assert "The materials cover core topics" not in final_reply
        assert "These are the topics I found in the material:" in final_reply
        assert (
            "Choose a topic to explore next. In the shell, use ↑/↓ and press Enter." in final_reply
        )
        assert "Signal entropy [E1]" in final_reply
        assert "Carrier waves [E2]" in final_reply
        assert orch.last_reply == final_reply

    @patch("hephaistos.chat.orchestrator._build_overview_context")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    def test_guided_overview_no_topic_fallback_does_not_append_unvalidated_menu(
        self,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_overview_context: MagicMock,
    ) -> None:
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/lecture.pdf",
                0,
                "E1",
                "Lecture notes. Zephyrology concepts and fluxions are discussed.",
            )
        )
        mock_resolve_evidence.return_value = evidence
        mock_overview_context.return_value = ""
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("The files cover vague material [E1]. Say ready.")]
        )
        unrelated_result = PriorityWebSearchResult(
            title="unrelated cooking",
            url="https://example.test",
            snippet="recipe ingredients kitchen",
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        with patch(
            "hephaistos.chat.orchestrator.duckduckgo_search",
            return_value=(unrelated_result,),
        ):
            events = list(orch.iter_events("what are the materials about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        final_reply = deltas[0]
        assert "I could not identify precise topics" in final_reply
        assert "What the sample does show:" in final_reply
        assert "These are the topics I found in the material:" not in final_reply
        assert "Choose a topic to explore next" not in final_reply
        assert orch.last_reply == final_reply

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
        with patch("hephaistos.chat.orchestrator.duckduckgo_search", return_value=()):
            events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert deltas[0] != "The course is about computer science."
        assert orch.last_reply == deltas[0]
        assert "These are the topics I found" in orch.last_reply
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
        with patch("hephaistos.chat.orchestrator.duckduckgo_search", return_value=()):
            events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        notices = [event.message for event in events if isinstance(event, NoticeEvent)]
        assert len(deltas) == 1
        assert "The files cover" not in deltas[0]
        assert "Say ready when you want recall" not in deltas[0]
        assert "I could not identify precise topics" in deltas[0]
        assert "Choose a topic to explore next" not in deltas[0]
        assert "not an exhaustive summary" not in deltas[0]
        assert "[E1]" in deltas[0]
        assert "[E2]" in deltas[0]
        assert not any("No evidence citations" in notice for notice in notices)

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_overview_fallback_uses_model_normalized_topics_with_display_labels(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
        )
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/analysis.pdf",
                0,
                "E1",
                "Administrative Header. Signal entropy is introduced with examples.",
            ),
            _make_evidence_chunk(
                "materials/analysis.pdf",
                1,
                "E2",
                "Carrier waves are defined before modulation examples.",
            ),
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("The files cover vague course material [E1] [E2].")]
        )
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        '{"topics":['
                        '{"canonical_english":"signal entropy",'
                        '"display_label":"Signal entropy","evidence_id":"E1",'
                        '"evidence_quote":"Signal entropy"},'
                        '{"canonical_english":"carrier waves",'
                        '"display_label":"Carrier waves","evidence_id":"E2",'
                        '"evidence_quote":"Carrier waves"}'
                        "]}"
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "topic-normalizer"
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("Which topics should I study?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        final_reply = deltas[0]
        assert "The files cover vague course material" not in final_reply
        assert "Signal entropy [E1]" in final_reply
        assert "Carrier waves [E2]" in final_reply
        assert orch.last_reply == final_reply
        normalizer_conversation = mock_stream.call_args.args[1]
        system_prompt = normalizer_conversation.messages[0].content
        user_prompt = normalizer_conversation.messages[1].content
        assert "canonical topic names in English" in system_prompt
        assert "display label in the language" in system_prompt
        assert "User request: Which topics should I study?" in user_prompt
        assert "Evidence E1" in user_prompt
        assert "Evidence E2" in user_prompt

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_german_overview_fallback_uses_localized_model_repair(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
            allow_tools=False,
        )
        evidence = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/reihen.md",
                0,
                "E1",
                "Reihen und Konvergenzkriterien stehen im Mittelpunkt der Vorlesung.",
            ),
            _make_evidence_chunk(
                "materials/taylor.md",
                0,
                "E2",
                "Taylor-Polynome und lineare Approximationen werden als Werkzeuge behandelt.",
            ),
        )
        repaired_reply = (
            "Die Unterlagen geben einen Überblick über zentrale Analysis-Konzepte und "
            "Aufgabentypen [E1] [E2].\n"
            "- Ein Schwerpunkt sind Reihen und Kriterien, mit denen man ihre Konvergenz "
            "beurteilt [E1].\n"
            "- Ein weiterer Schwerpunkt sind Taylor-Polynome und lineare Approximationen "
            "als Werkzeuge für Funktionen [E2]."
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter(
            [AssistantDeltaEvent("The files cover vague course material [E1] [E2].")]
        )
        mock_stream.return_value = iter([CompletionDelta(content=repaired_reply)])

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "localized-overview-repair"
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("um was geht es in den dateien"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        final_reply = deltas[0]
        assert final_reply == repaired_reply
        assert "The files cover" not in final_reply
        assert "These are the topics" not in final_reply
        assert "Choose a topic" not in final_reply
        assert "Say ready" not in final_reply
        assert "Next action" not in final_reply
        assert "source-backed" not in final_reply
        system_prompt = mock_stream.call_args.args[1].messages[0].content
        assert "same language as the user's request" in system_prompt
        assert "Do not ask a recall question" in system_prompt
        assert "next-step/readiness/drill instructions" in system_prompt
        assert "internal evidence-grounding blocks" in system_prompt

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
        with patch("hephaistos.chat.orchestrator.duckduckgo_search", return_value=()):
            events = list(TurnOrchestrator(session).iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        completions = [event for event in events if isinstance(event, TurnCompleteEvent)]
        assert len(deltas) == 1
        assert len(completions) == 1
        assert "I could not identify precise topics" in deltas[0]
        assert "Choose a topic to explore next" not in deltas[0]
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
                    "These are the topics I found in the material [E1] [E2].\n"
                    "- Definitions and examples [E1].\n"
                    "- Exam-style method questions [E2].\n"
                    "- Choose a topic to explore next with the menu [E1]."
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
        with patch("hephaistos.chat.orchestrator.duckduckgo_search", return_value=()):
            events = list(orch.iter_events("what is the material about"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "I could not identify precise topics" in deltas[0]
        assert "Choose a topic to explore next" not in deltas[0]
        assert "exam-style questions or structured assessment prompts [E1]" in deltas[0]

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
        assert deltas == ["PARTIAL: I could not generate a grounded assessment. Please try again."]
        assert orch.last_reply == (
            "PARTIAL: I could not generate a grounded assessment. Please try again."
        )

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
        assert deltas == ["I could not generate a prompt. Please try again."]
        assert orch.last_reply == "I could not generate a prompt. Please try again."

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_study_turn_uses_completion_full_text_when_deltas_are_empty(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(action=StudyAction.CHAT)
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter(
            [
                TurnCompleteEvent(
                    full_text="Das ist eine normale Antwort.",
                    turn_index=2,
                    latency_ms=18.0,
                    finish_reason="stop",
                    tokens_remaining=500,
                )
            ]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("kurze frage"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        completions = [event for event in events if isinstance(event, TurnCompleteEvent)]
        assert deltas == ["Das ist eine normale Antwort."]
        assert completions[-1].full_text == "Das ist eine normale Antwort."
        assert completions[-1].turn_index == 2
        assert orch.last_reply == "Das ist eine normale Antwort."
        assert session.conversation.messages[-1].content == "Das ist eine normale Antwort."

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_buffered_study_turn_uses_completion_full_text_when_deltas_are_empty(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="what does the material say about enzyme kinetics?",
            buffer_response=True,
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/enzyme-notes.md",
                0,
                "E1",
                "Enzyme kinetics connects substrate concentration with reaction velocity.",
            )
        )
        mock_iter_agent.return_value = iter(
            [
                TurnCompleteEvent(
                    full_text="Enzyme kinetics connects substrate concentration with "
                    "reaction velocity [E1].",
                    turn_index=4,
                    latency_ms=12.0,
                    finish_reason="stop",
                    tokens_remaining=400,
                )
            ]
        )

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("what does the material say about enzyme kinetics?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        completions = [event for event in events if isinstance(event, TurnCompleteEvent)]
        assert len(deltas) == 1
        assert deltas[0].startswith(
            "Enzyme kinetics connects substrate concentration with reaction velocity [E1]."
        )
        assert "I could not generate" not in deltas[0]
        assert "enzyme notes" in deltas[0]
        assert completions[-1].full_text == deltas[0]
        assert completions[-1].turn_index == 4
        assert orch.last_reply == deltas[0]

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
    def test_source_qa_non_exact_empty_model_fallback_is_cited_without_english_wrapper(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="was sagen die quellen ueber enzyme kinetics?",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = _make_turn_evidence(
            _make_evidence_chunk(
                "materials/enzyme-notes.md",
                0,
                "E1",
                "Enzyme kinetics connects substrate concentration with reaction velocity.",
            )
        )
        mock_iter_agent.return_value = iter([])

        session = _make_study_session()
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("was sagen die quellen ueber enzyme kinetics?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == [
            "- enzyme notes: Enzyme kinetics connects substrate concentration with "
            "reaction velocity. [E1]"
        ]
        assert "The indexed sources provide this directly" not in deltas[0]
        assert orch.last_reply == deltas[0]

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_answer_without_evidence_ids_gets_auditable_bullets(
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
        assert "Evidence checked:" not in deltas[0]
        assert "Key evidence:" not in deltas[0]
        assert "- exam: Question about cancer. [E1]" in deltas[0]
        assert "- exam: Question about genetics. [E2]" in deltas[0]
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

        orch._finalize_successful_turn("hello", resolved, latency_ms=1.0)

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
        assert "prompt" not in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_qa_without_evidence_localizes_deterministic_fallback(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="what do the sources say about the sentinel phrase?",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([])
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        "Die aktivierten Armory-Quellen enthalten keine Antwort auf diese "
                        "Frage. Aktiviere das relevante Material mit /materials oder gib eine "
                        "spezifischere Quelle an."
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "fallback-localizer"
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("was steht dazu in den quellen?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert deltas[0].startswith("Die aktivierten Armory-Quellen")
        assert "/materials" in deltas[0]
        assert "enabled armory sources" not in deltas[0]
        assert (
            "Rewrite an internal English fallback"
            in mock_stream.call_args.args[1].messages[0].content
        )
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.stream_completion")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_direct_reply_localizes_without_losing_commands(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_stream: MagicMock,
    ) -> None:
        direct_reply = (
            "Use Hephaistos to study your own materials: ask a source-grounded question, "
            "run /exam for active recall, run /priority for a plan, or /autopilot on "
            "to let Heph drive the session."
        )
        mock_plan_turn.return_value = StudyTurnPlan(
            action=StudyAction.CHAT,
            phase=StudyPhase.PRESENTING,
            prompt="",
            allow_tools=False,
            direct_reply=direct_reply,
        )
        mock_resolve_evidence.return_value = None
        mock_stream.return_value = iter(
            [
                CompletionDelta(
                    content=(
                        "Nutze Hephaistos, um mit deinen eigenen Materialien zu lernen: "
                        "stelle eine quellenbasierte Frage, starte /exam fuer Active Recall, "
                        "nutze /priority fuer einen Plan oder /autopilot on, damit Heph die "
                        "Sitzung fuehrt."
                    )
                )
            ]
        )

        session = _make_study_session()
        session.config.base_url = "https://local.test/v1"
        session.config.model = "fallback-localizer"
        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("was kann heph tun?"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert deltas[0].startswith("Nutze Hephaistos")
        assert "/exam" in deltas[0]
        assert "/priority" in deltas[0]
        assert "/autopilot" in deltas[0]
        assert "Use Hephaistos" not in deltas[0]
        assert session.conversation.messages[-1].content == deltas[0]

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
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_source_only_partial_evidence_injects_sufficiency_gate(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.SOURCE_QA,
            retrieval_query="Using only the indexed sources, what is the sentinel phrase?",
        )
        evidence = _make_turn_evidence(_make_evidence_chunk("materials/a.md", 0, "E1"))
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = evidence
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("The source says X [E1].")])

        session = _make_study_session()
        list(TurnOrchestrator(session).iter_events("Using only the indexed sources, what is X?"))

        prompt = mock_iter_agent.call_args.kwargs["extra_system_prompt"]
        assert "Evidence sufficiency gate:" in prompt
        assert "Recommended action: give partial answer." in prompt

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_broad_present_query_routes_to_overview_guidance_before_generation(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is this material about overall",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("unused")])

        session = _make_study_session()
        events = list(TurnOrchestrator(session).iter_events("what is this material about overall"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "Start with a material overview" in deltas[0]
        assert "need one clarification" not in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    @patch("hephaistos.chat.orchestrator._resolve_turn_evidence")
    @patch("hephaistos.chat.orchestrator.plan_turn")
    def test_assess_without_evidence_routes_to_quiz_first_before_generation(
        self,
        mock_plan_turn: MagicMock,
        mock_resolve_evidence: MagicMock,
        mock_iter_agent: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.ASSESS,
            retrieval_query="grade this recall answer against the source",
        )
        mock_plan_turn.return_value = plan
        mock_resolve_evidence.return_value = None
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("unused")])

        session = _make_study_session()
        events = list(TurnOrchestrator(session).iter_events("answer"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "test your current understanding first" in deltas[0]
        mock_iter_agent.assert_not_called()

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    def test_simple_greeting_goes_to_model_when_armory_is_attached(
        self, mock_iter_agent: MagicMock
    ) -> None:
        session = _make_study_session()
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Hey! What can I help with?")])
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("hey"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["Hey! What can I help with?"]
        assert session.last_turn_evidence is None
        assert session.study_state.current_item == ""
        mock_iter_agent.assert_called_once()
        call_kwargs = mock_iter_agent.call_args.kwargs
        assert call_kwargs["turn_evidence"] is None
        assert call_kwargs["tool_schemas"] == []
        assert "HEPH chat mode" in call_kwargs["extra_system_prompt"]
        assert "available tools" not in call_kwargs["extra_system_prompt"]

    @patch("hephaistos.chat.orchestrator.iter_agent_events")
    def test_manual_greeting_goes_to_model_without_tools(self, mock_iter_agent: MagicMock) -> None:
        session = _make_study_session()
        session.study_state.autonomy_mode = StudyAutonomyMode.MANUAL
        mock_iter_agent.return_value = iter([AssistantDeltaEvent("Hey! What can I help with?")])
        orch = TurnOrchestrator(session)

        events = list(orch.iter_events("hey"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert deltas == ["Hey! What can I help with?"]
        mock_iter_agent.assert_called_once()
        call_kwargs = mock_iter_agent.call_args.kwargs
        assert call_kwargs["turn_evidence"] is None
        assert call_kwargs["tool_schemas"] == []
        assert "HEPH chat mode" in call_kwargs["extra_system_prompt"]
        assert "available tools" not in call_kwargs["extra_system_prompt"]
        assert "User request: hey" in call_kwargs["extra_system_prompt"]
        assert session.study_state.current_item == ""

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
        session.source_files = ("materials/L7_WorkspaceFixture-1_Fundamentalsatz.pdf",)
        index = ArmoryIndex(Path("/tmp/fake-armory"))
        index.unindexable_files = {
            "materials/L7_WorkspaceFixture-1_Fundamentalsatz.pdf": (
                "binary document; document conversion backend unavailable"
            )
        }
        session.rag_index = index

        orch = TurnOrchestrator(session)
        events = list(orch.iter_events("how does the fundamentalsatz work"))

        deltas = [event.delta for event in events if isinstance(event, AssistantDeltaEvent)]
        assert len(deltas) == 1
        assert "@L7_WorkspaceFixture-1_Fundamentalsatz.pdf" in deltas[0]
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
    def test_build_turn_evidence_from_generated_topic_prompt_uses_lexical_fallback(
        self,
        mock_ensure: MagicMock,
    ) -> None:
        text = (
            "Definition. A vector index is a retrieval structure that stores embeddings "
            "for nearest-neighbor lookup."
        )
        index = ArmoryIndex(Path("/tmp/fake-armory"))
        index.documents = [
            ChunkedDocument(
                source="materials/vector-index.md",
                chunks=[
                    _make_chunk("materials/vector-index.md", 0, "Administrative Header 2"),
                    _make_chunk("materials/vector-index.md", 1, text),
                ],
            )
        ]
        mock_ensure.return_value = index

        with patch("hephaistos.chat.evidence.retrieve", return_value=[]):
            session = _make_study_session()
            result = build_turn_evidence_from_query(
                session,
                "Explain vector indexes from the material in simple terms.",
            )

        assert result is not None
        assert any("vector index" in item.content for item in result.items)

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
                "## Biology lecture\n\nAdministrative line\n\n"
                "Administrative block\n\n12 April 2026",
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
        assert is_overview_query("what are the materials about")
        assert is_overview_query("Can you read through all the files")
        assert not is_overview_query("explain Dijkstra")

    @patch("hephaistos.chat.evidence.build_turn_evidence_from_overview")
    @patch("hephaistos.chat.evidence.build_turn_evidence_from_query")
    def test_resolve_turn_evidence_uses_overview_for_canonical_material_overview(
        self,
        mock_query: MagicMock,
        mock_overview: MagicMock,
    ) -> None:
        plan = _make_study_plan(
            action=StudyAction.PRESENT,
            retrieval_query="what is the material about",
            buffer_response=True,
            allow_tools=False,
        )
        evidence = _make_turn_evidence(_make_evidence_chunk())
        mock_overview.return_value = evidence

        session = _make_study_session()
        result = resolve_turn_evidence(session, plan)

        assert result is evidence
        mock_overview.assert_called_once_with(session)
        mock_query.assert_not_called()

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
