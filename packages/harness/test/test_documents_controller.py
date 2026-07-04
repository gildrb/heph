"""Tests for the intent-classifier-driven document controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from harness.chat.intent import MODEL_NORMALIZED_INTENTS
from harness.documents import (
    DocumentAction,
    DocumentMove,
    DocumentTurnPlan,
    MemoryState,
    RecallFeedbackType,
    RecallPhase,
    RecallRating,
    RecallState,
    ReviewItem,
    apply_turn_result,
    assess_evidence,
    heph_help_plan,
    is_driven_recall_intent,
    material_overview_plan,
    material_source_qa_plan,
    material_topic_drill_plan,
    material_topic_presentation_plan,
    plain_chat_plan,
    plan_turn,
    recall_clarification_plan,
    validate_pedagogy,
)

ActionRow = tuple[RecallPhase, bool, str, DocumentAction, RecallPhase]
DOCUMENT_CONTROLLER_INTENTS = tuple(
    intent for intent in MODEL_NORMALIZED_INTENTS if intent != "heph_action"
)


_DISPATCH_EXPECTATIONS: tuple[ActionRow, ...] = (
    (
        RecallPhase.PRESENTING,
        False,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "source_qa",
        DocumentAction.SOURCE_QA,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "topic_drill",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "hint_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        False,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (RecallPhase.PRESENTING, False, "wait", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.PRESENTING, False, "heph_help", DocumentAction.CHAT, RecallPhase.PRESENTING),
    (RecallPhase.PRESENTING, False, "chat", DocumentAction.CHAT, RecallPhase.PRESENTING),
    (
        RecallPhase.PRESENTING,
        True,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "source_qa",
        DocumentAction.SOURCE_QA,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "topic_drill",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "hint_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.PRESENTING,
        True,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (RecallPhase.PRESENTING, True, "wait", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.PRESENTING, True, "heph_help", DocumentAction.CHAT, RecallPhase.PRESENTING),
    (RecallPhase.PRESENTING, True, "chat", DocumentAction.CHAT, RecallPhase.PRESENTING),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "source_qa",
        DocumentAction.SOURCE_QA,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "topic_drill",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "hint_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "wait",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "heph_help",
        DocumentAction.CHAT,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        False,
        "chat",
        DocumentAction.CHAT,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "source_qa",
        DocumentAction.SOURCE_QA,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "source_only_policy",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "topic_drill",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "ready_for_recall",
        DocumentAction.PROMPT_RECALL,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "recall_clarification",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "recall_answer_attempt",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "reveal_request",
        DocumentAction.REFUSE_REVEAL,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "hint_request",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "scaffold_request",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "material_review",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "driven_recall_calibration",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "wait",
        DocumentAction.WAIT_READY_REMINDER,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "heph_help",
        DocumentAction.CHAT,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.WAITING_FOR_READY,
        True,
        "chat",
        DocumentAction.CHAT,
        RecallPhase.WAITING_FOR_READY,
    ),
    (
        RecallPhase.RECALL,
        False,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.RECALL, False, "source_qa", DocumentAction.SOURCE_QA, RecallPhase.PRESENTING),
    (
        RecallPhase.RECALL,
        False,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.RECALL, False, "topic_drill", DocumentAction.CALIBRATE, RecallPhase.RECALL),
    (
        RecallPhase.RECALL,
        False,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "hint_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        False,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.RECALL,
        False,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (RecallPhase.RECALL, False, "wait", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.RECALL, False, "heph_help", DocumentAction.CHAT, RecallPhase.RECALL),
    (RecallPhase.RECALL, False, "chat", DocumentAction.CHAT, RecallPhase.RECALL),
    (
        RecallPhase.RECALL,
        True,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.RECALL, True, "source_qa", DocumentAction.SOURCE_QA, RecallPhase.PRESENTING),
    (
        RecallPhase.RECALL,
        True,
        "source_only_policy",
        DocumentAction.ASSESS,
        RecallPhase.ASSESS,
    ),
    (
        RecallPhase.RECALL,
        True,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.RECALL, True, "topic_drill", DocumentAction.CALIBRATE, RecallPhase.RECALL),
    (RecallPhase.RECALL, True, "ready_for_recall", DocumentAction.ASSESS, RecallPhase.ASSESS),
    (
        RecallPhase.RECALL,
        True,
        "recall_clarification",
        DocumentAction.PROMPT_RECALL,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.RECALL,
        True,
        "recall_answer_attempt",
        DocumentAction.ASSESS,
        RecallPhase.ASSESS,
    ),
    (
        RecallPhase.RECALL,
        True,
        "reveal_request",
        DocumentAction.REFUSE_REVEAL,
        RecallPhase.RECALL,
    ),
    (RecallPhase.RECALL, True, "hint_request", DocumentAction.HINT, RecallPhase.ASSESS),
    (RecallPhase.RECALL, True, "skip_request", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (
        RecallPhase.RECALL,
        True,
        "scaffold_request",
        DocumentAction.SIMPLIFY,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.RECALL,
        True,
        "material_review",
        DocumentAction.REVIEW,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.RECALL,
        True,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.RECALL,
    ),
    (
        RecallPhase.RECALL,
        True,
        "driven_recall_calibration",
        DocumentAction.ASSESS,
        RecallPhase.ASSESS,
    ),
    (RecallPhase.RECALL, True, "wait", DocumentAction.ASSESS, RecallPhase.ASSESS),
    (RecallPhase.RECALL, True, "heph_help", DocumentAction.CHAT, RecallPhase.RECALL),
    (RecallPhase.RECALL, True, "chat", DocumentAction.CHAT, RecallPhase.RECALL),
    (
        RecallPhase.ASSESS,
        False,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.ASSESS, False, "source_qa", DocumentAction.SOURCE_QA, RecallPhase.PRESENTING),
    (
        RecallPhase.ASSESS,
        False,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.ASSESS, False, "topic_drill", DocumentAction.CALIBRATE, RecallPhase.RECALL),
    (
        RecallPhase.ASSESS,
        False,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "hint_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "skip_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.ASSESS,
    ),
    (
        RecallPhase.ASSESS,
        False,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (RecallPhase.ASSESS, False, "wait", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.ASSESS, False, "heph_help", DocumentAction.CHAT, RecallPhase.ASSESS),
    (RecallPhase.ASSESS, False, "chat", DocumentAction.CHAT, RecallPhase.ASSESS),
    (
        RecallPhase.ASSESS,
        True,
        "material_overview",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.ASSESS, True, "source_qa", DocumentAction.SOURCE_QA, RecallPhase.PRESENTING),
    (
        RecallPhase.ASSESS,
        True,
        "source_only_policy",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "topic_presentation",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.ASSESS, True, "topic_drill", DocumentAction.CALIBRATE, RecallPhase.RECALL),
    (
        RecallPhase.ASSESS,
        True,
        "ready_for_recall",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "recall_clarification",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "recall_answer_attempt",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "reveal_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (RecallPhase.ASSESS, True, "hint_request", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.ASSESS, True, "skip_request", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (
        RecallPhase.ASSESS,
        True,
        "scaffold_request",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "material_review",
        DocumentAction.PRESENT,
        RecallPhase.PRESENTING,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "priority_request",
        DocumentAction.PRIORITY,
        RecallPhase.ASSESS,
    ),
    (
        RecallPhase.ASSESS,
        True,
        "driven_recall_calibration",
        DocumentAction.CALIBRATE,
        RecallPhase.RECALL,
    ),
    (RecallPhase.ASSESS, True, "wait", DocumentAction.PRESENT, RecallPhase.PRESENTING),
    (RecallPhase.ASSESS, True, "heph_help", DocumentAction.CHAT, RecallPhase.ASSESS),
    (RecallPhase.ASSESS, True, "chat", DocumentAction.CHAT, RecallPhase.ASSESS),
)


def _state(
    phase: RecallPhase = RecallPhase.PRESENTING, *, current_item: bool = False
) -> RecallState:
    return RecallState(
        phase=phase,
        current_item="compactness" if current_item else "",
        retrieval_query="compactness" if current_item else "",
        expected_source_refs=["notes.md#chunk=1"] if current_item else [],
        attempt_count=1,
        hint_level=1,
    )


@pytest.mark.parametrize(
    ("phase", "current_item", "intent", "expected_action", "expected_phase"),
    list(_DISPATCH_EXPECTATIONS),
)
def test_plan_turn_dispatches_for_each_state_item_intent_combination(
    phase: RecallPhase,
    current_item: bool,
    intent: str,
    expected_action: DocumentAction,
    expected_phase: RecallPhase,
) -> None:
    assert intent in MODEL_NORMALIZED_INTENTS

    plan = plan_turn(
        _state(phase, current_item=current_item), "Explain compactness", intent=intent
    )

    assert plan.action is expected_action
    assert plan.phase is expected_phase


def test_dispatch_table_covers_every_model_intent_for_each_phase_and_item_state() -> None:
    covered = {
        (phase, current_item, intent)
        for phase, current_item, intent, _, _ in _DISPATCH_EXPECTATIONS
    }
    expected = {
        (phase, current_item, intent)
        for phase in RecallPhase
        for current_item in (False, True)
        for intent in DOCUMENT_CONTROLLER_INTENTS
    }

    assert covered == expected


def test_plan_turn_passes_explicit_driven_intent_to_policy() -> None:
    plan = plan_turn(RecallState(), "Start active practice", intent="driven_recall_calibration")

    assert plan.action is DocumentAction.CALIBRATE
    assert plan.document_move is not None
    assert plan.document_move.kind == "ask_recall"
    assert "Document policy" in plan.prompt
    assert "Practice goal: material review" in plan.prompt


def test_material_answer_turns_skip_document_policy_scaffold() -> None:
    plan = plan_turn(
        RecallState(phase=RecallPhase.WAITING_FOR_READY, current_item="compactness"),
        "Explain the cited source",
        intent="topic_presentation",
    )

    assert plan.action is DocumentAction.PRESENT
    assert plan.document_move is None
    assert "Document policy" not in plan.prompt
    assert "confidence" not in plan.prompt.casefold()


@pytest.mark.parametrize(
    ("intent", "expected"),
    [
        ("driven_recall_calibration", True),
        ("topic_drill", True),
        ("priority_request", True),
        ("topic_presentation", False),
        ("chat", False),
        ("", False),
    ],
)
def test_is_driven_recall_intent_uses_intent_set(intent: str, expected: bool) -> None:
    assert is_driven_recall_intent(intent) is expected


@pytest.mark.parametrize(
    ("intent", "expected_action", "expected_query", "expected_prompt"),
    [
        (
            "material_overview",
            DocumentAction.PRESENT,
            "Explain compactness",
            "Execute MATERIAL_OVERVIEW",
        ),
        ("source_qa", DocumentAction.SOURCE_QA, "Explain compactness", "Execute SOURCE_QA"),
        (
            "topic_presentation",
            DocumentAction.PRESENT,
            "Explain compactness",
            "Execute the PRESENT phase",
        ),
        ("topic_drill", DocumentAction.CALIBRATE, "Explain compactness", "Execute CALIBRATE"),
    ],
)
def test_open_material_intents_select_material_prompt_builders(
    intent: str,
    expected_action: DocumentAction,
    expected_query: str | None,
    expected_prompt: str,
) -> None:
    plan = plan_turn(RecallState(), "Explain compactness", intent=intent)

    assert plan.action is expected_action
    assert plan.retrieval_query == expected_query
    assert expected_prompt in plan.prompt


@pytest.mark.parametrize(
    ("builder_plan", "expected_action", "expected_prompt"),
    [
        (
            material_overview_plan("What is in the files?"),
            DocumentAction.PRESENT,
            "Execute MATERIAL_OVERVIEW",
        ),
        (
            material_source_qa_plan(
                "Where is compactness defined?", retrieval_query="compactness"
            ),
            DocumentAction.SOURCE_QA,
            "Execute SOURCE_QA",
        ),
        (
            material_topic_presentation_plan("Explain it", retrieval_query="compactness"),
            DocumentAction.PRESENT,
            "Execute the PRESENT phase",
        ),
        (
            material_topic_drill_plan("Quiz me", retrieval_query="compactness", exam_style=True),
            DocumentAction.CALIBRATE,
            "Execute CALIBRATE",
        ),
        (
            recall_clarification_plan("repeat it", current_item="compactness"),
            DocumentAction.PROMPT_RECALL,
            "Execute RECALL_CLARIFICATION",
        ),
        (plain_chat_plan("hello"), DocumentAction.CHAT, "Execute CHAT"),
        (heph_help_plan("what is heph?"), DocumentAction.CHAT, "Execute HEPH_HELP"),
    ],
)
def test_public_plan_builders_emit_expected_action_and_prompt(
    builder_plan: DocumentTurnPlan,
    expected_action: DocumentAction,
    expected_prompt: str,
) -> None:
    assert builder_plan.action is expected_action
    assert expected_prompt in builder_plan.prompt


def test_heph_help_prompt_uses_operational_product_context() -> None:
    plan = heph_help_plan("tell me more")

    assert "Heph Assistant Atlas" in plan.prompt
    assert "heph armory init" in plan.prompt
    assert "/models" in plan.prompt
    assert "Be operational" in plan.prompt
    assert "advance the answer with new specifics" in plan.prompt


def test_material_overview_prompt_shapes_answer_before_validation() -> None:
    plan = material_overview_plan("What is in the files?")

    assert "Execute MATERIAL_OVERVIEW" in plan.prompt
    assert "Write 1-2 short cited sentences" in plan.prompt
    assert "State only topics, methods, examples, tasks, or problem types" in plan.prompt
    assert "No unsolicited quality judgments" in plan.prompt
    assert "Cite factual claims next to their support" in plan.prompt
    assert "Do not copy source lines" in plan.prompt


def test_topic_drill_exam_builder_hides_answer_key() -> None:
    plan = material_topic_drill_plan(
        "Exam question", retrieval_query="compactness", exam_style=True
    )

    assert plan.action is DocumentAction.CALIBRATE
    assert "do not show the result, answer key" in plan.prompt


def test_calibration_prompt_does_not_invite_unsourced_exam_constraints() -> None:
    plan = plan_turn(RecallState(), "Make an exam-style question", intent="topic_drill")

    assert "do not invent time limits, point values, labels, or answer instructions" in plan.prompt
    assert "include one reasonable" not in plan.prompt


def test_priority_prompt_blocks_unsourced_rank_labels_and_category_names() -> None:
    plan = plan_turn(RecallState(), "What should I review first?", intent="priority_request")

    assert "do not use ranked/order labels" in plan.prompt
    assert "Do not create umbrella category names" in plan.prompt


def test_material_overview_result_does_not_enter_ready_loop() -> None:
    plan = plan_turn(RecallState(), "Overview", intent="material_overview")

    next_state, visible_reply = apply_turn_result(
        RecallState(),
        plan,
        "Corpus overview [E1]",
        ["notes.md#chunk=1"],
    )

    assert visible_reply == "Corpus overview [E1]"
    assert next_state.phase is RecallPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.last_feedback_type is RecallFeedbackType.NONE


def test_apply_present_result_enters_waiting_loop_with_sources() -> None:
    state = RecallState()
    plan = plan_turn(state, "Explain compactness", intent="topic_presentation")

    next_state, _ = apply_turn_result(
        state, plan, "Compactness means every cover has a subcover.", ["notes.md#chunk=1"]
    )

    assert next_state.phase is RecallPhase.WAITING_FOR_READY
    assert next_state.current_item == "Explain compactness"
    assert next_state.retrieval_query == "Explain compactness"
    assert next_state.expected_source_refs == ["notes.md#chunk=1"]
    assert next_state.last_feedback_type is RecallFeedbackType.PRESENTED


def test_apply_present_result_without_sources_marks_no_source() -> None:
    state = RecallState()
    plan = plan_turn(state, "Explain compactness", intent="topic_presentation")

    next_state, _ = apply_turn_result(state, plan, "No evidence found.", [])

    assert next_state.phase is RecallPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.last_feedback_type is RecallFeedbackType.NO_SOURCE


def test_apply_calibration_result_enters_recall_with_model_question() -> None:
    state = RecallState()
    plan = plan_turn(state, "Quiz me on compactness", intent="topic_drill")
    now = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)

    next_state, _ = apply_turn_result(
        state,
        plan,
        "What does compactness require?",
        ["notes.md#chunk=2"],
        now=now,
    )

    assert next_state.phase is RecallPhase.RECALL
    assert next_state.current_item == "What does compactness require?"
    assert next_state.retrieval_query == "Quiz me on compactness"
    assert next_state.expected_source_refs == ["notes.md#chunk=2"]
    assert next_state.last_feedback_type is RecallFeedbackType.CALIBRATING
    assert next_state.recall_started_at == now


def test_waiting_ready_intent_prompts_recall_and_updates_state() -> None:
    state = _state(RecallPhase.WAITING_FOR_READY, current_item=True)
    plan = plan_turn(state, "I am ready", intent="ready_for_recall")
    now = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)

    next_state, _ = apply_turn_result(state, plan, "Answer from memory.", [], now=now)

    assert plan.action is DocumentAction.PROMPT_RECALL
    assert next_state.phase is RecallPhase.RECALL
    assert next_state.last_feedback_type is RecallFeedbackType.READY
    assert next_state.recall_started_at == now
    assert next_state.hint_level == 0


def test_waiting_wait_intent_reminds_without_advancing() -> None:
    state = _state(RecallPhase.WAITING_FOR_READY, current_item=True)
    plan = plan_turn(state, "wait", intent="wait")

    next_state, _ = apply_turn_result(state, plan, "Say when ready.", [])

    assert plan.action is DocumentAction.WAIT_READY_REMINDER
    assert next_state.phase is RecallPhase.WAITING_FOR_READY
    assert next_state.last_feedback_type is RecallFeedbackType.WAITING


@pytest.mark.parametrize("phase", [RecallPhase.WAITING_FOR_READY, RecallPhase.RECALL])
def test_reveal_intent_is_refused_in_active_recall_loop(phase: RecallPhase) -> None:
    state = _state(phase, current_item=True)
    plan = plan_turn(state, "show answer", intent="reveal_request")

    next_state, _ = apply_turn_result(state, plan, "Try first.", [])

    assert plan.action is DocumentAction.REFUSE_REVEAL
    assert next_state.phase is phase
    assert next_state.last_feedback_type is RecallFeedbackType.REFUSED


def test_reveal_refusal_does_not_store_assistant_generated_confidence() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)
    plan = plan_turn(state, "show answer", intent="reveal_request")

    _, visible_reply = apply_turn_result(
        state,
        plan,
        "Try the recall attempt first. Confidence: 96%.",
        [],
    )

    assert visible_reply == "Try the recall attempt first."


def test_recall_answer_intent_assesses_and_tracks_confidence() -> None:
    started = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)
    state = _state(RecallPhase.RECALL, current_item=True)
    state.recall_started_at = started
    plan = plan_turn(
        state, "It is closed and bounded; confidence 80%", intent="recall_answer_attempt"
    )

    next_state, visible_reply = apply_turn_result(
        state,
        plan,
        "PARTIAL: Good start; missing open-cover condition.",
        ["notes.md#chunk=1"],
        now=started + timedelta(seconds=20),
    )

    assert plan.stated_confidence == 0.8
    assert visible_reply == "PARTIAL: Good start; missing open-cover condition."
    assert next_state.phase is RecallPhase.RECALL
    assert next_state.attempt_count == 2
    assert next_state.last_feedback_type is RecallFeedbackType.PARTIAL
    assert next_state.last_recall_seconds == 20
    assert next_state.last_recall_rating is RecallRating.GOOD
    assert next_state.last_confidence == 0.8


def test_recall_assessment_prompt_blocks_unsourced_term_definitions() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)
    plan = plan_turn(state, "Add one concise cited detail.", intent="recall_answer_attempt")

    assert "Do not define or explain a term merely because the material uses it" in plan.prompt


def test_correct_assessment_clears_recall_target_and_keeps_attempt_count() -> None:
    started = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)
    state = _state(RecallPhase.RECALL, current_item=True)
    state.recall_started_at = started
    plan = plan_turn(state, "Open covers; confidence 5/5", intent="recall_answer_attempt")

    next_state, visible_reply = apply_turn_result(
        state,
        plan,
        "CORRECT:\nScore: complete",
        ["notes.md#chunk=1"],
        now=started + timedelta(seconds=140),
    )

    assert visible_reply == "CORRECT:\nScore: complete"
    assert next_state.phase is RecallPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.attempt_count == 2
    assert next_state.last_feedback_type is RecallFeedbackType.CORRECT
    assert next_state.last_recall_rating is RecallRating.HARD
    assert next_state.last_confidence == 1.0
    assert next_state.hint_level == 0


def test_missing_assessment_prefix_defaults_to_partial() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)
    plan = plan_turn(state, "attempt", intent="recall_answer_attempt")

    next_state, visible_reply = apply_turn_result(state, plan, "Needs the theorem name.", [])

    assert visible_reply == "PARTIAL: Needs the theorem name."
    assert next_state.last_feedback_type is RecallFeedbackType.PARTIAL
    assert next_state.practice_stop_reason == ""


def test_recall_hint_requires_prior_attempt_then_updates_hint_level() -> None:
    no_attempt = _state(RecallPhase.RECALL, current_item=True)
    no_attempt.attempt_count = 0
    attempt = _state(RecallPhase.RECALL, current_item=True)
    attempt.attempt_count = 1

    no_attempt_plan = plan_turn(no_attempt, "hint", intent="hint_request")
    hint_plan = plan_turn(attempt, "hint", intent="hint_request")
    next_state, _ = apply_turn_result(
        attempt, hint_plan, "Think about covers.", ["notes.md#chunk=3"]
    )

    assert no_attempt_plan.action is DocumentAction.ASSESS
    assert hint_plan.action is DocumentAction.HINT
    assert hint_plan.phase is RecallPhase.ASSESS
    assert next_state.phase is RecallPhase.RECALL
    assert next_state.hint_level == 2
    assert next_state.last_feedback_type is RecallFeedbackType.HINT
    assert next_state.expected_source_refs == ["notes.md#chunk=3"]


def test_scaffold_and_review_intents_use_stored_source_refs() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)

    scaffold_plan = plan_turn(state, "make it easier", intent="scaffold_request")
    review_plan = plan_turn(state, "review material", intent="material_review")

    assert scaffold_plan.action is DocumentAction.SIMPLIFY
    assert scaffold_plan.use_expected_source_refs is True
    assert review_plan.action is DocumentAction.REVIEW
    assert review_plan.use_expected_source_refs is True


def test_apply_scaffold_and_review_results_transition_back_through_recall_loop() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)
    scaffold_plan = plan_turn(state, "make it easier", intent="scaffold_request")
    scaffolded, _ = apply_turn_result(
        state,
        scaffold_plan,
        "What is the cover condition?",
        ["notes.md#chunk=4"],
    )
    review_plan = plan_turn(scaffolded, "review", intent="material_review")
    reviewed, _ = apply_turn_result(
        scaffolded, review_plan, "Compactness review [E1]", ["notes.md#chunk=5"]
    )

    assert scaffolded.phase is RecallPhase.RECALL
    assert scaffolded.current_item == "What is the cover condition?"
    assert scaffolded.last_feedback_type is RecallFeedbackType.EASIER
    assert scaffolded.hint_level == 2
    assert reviewed.phase is RecallPhase.WAITING_FOR_READY
    assert reviewed.current_item == scaffolded.current_item
    assert reviewed.last_feedback_type is RecallFeedbackType.REVIEWING
    assert reviewed.expected_source_refs == ["notes.md#chunk=5"]


def test_source_qa_result_clears_active_item_without_resetting_hint() -> None:
    state = _state(RecallPhase.RECALL, current_item=True)
    state.hint_level = 3
    plan = plan_turn(state, "Where is this stated?", intent="source_qa")

    next_state, _ = apply_turn_result(state, plan, "It is in [E1].", ["notes.md#chunk=1"])

    assert next_state.phase is RecallPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.last_feedback_type is RecallFeedbackType.NONE
    assert next_state.hint_level == 3


def test_chat_and_priority_results_do_not_enter_recall_loop() -> None:
    chat_plan = plan_turn(RecallState(), "hello", intent="chat")
    priority_plan = plan_turn(RecallState(), "what matters most?", intent="priority_request")

    chat_state, _ = apply_turn_result(RecallState(), chat_plan, "hello", [])
    priority_state, _ = apply_turn_result(
        RecallState(), priority_plan, "Priority [E1]", ["notes.md#chunk=1"]
    )

    assert chat_state.last_feedback_type is RecallFeedbackType.NONE
    assert priority_state.phase is RecallPhase.PRESENTING
    assert priority_state.last_feedback_type is RecallFeedbackType.NONE


def test_priority_prompt_avoids_unsupported_rankings_and_prerequisites() -> None:
    plan = plan_turn(RecallState(), "what should I review first?", intent="priority_request")

    assert "Give up to 3 cited review candidates" in plan.prompt
    assert "rank them only when the evidence states" in plan.prompt
    assert "Mention prerequisites only when retrieved evidence names them" in plan.prompt


def test_practice_boundaries_return_chat_completion_plan() -> None:
    timed_out = RecallState(
        time_budget_minutes=10,
        practice_started_at=datetime.now(UTC) - timedelta(minutes=11),
    )
    review_done = RecallState(practice_session_type="review", practice_turns=2)
    mastered = RecallState(practice_turns=4)

    assert "time budget reached" in plan_turn(timed_out, "next", intent="topic_drill").prompt
    assert (
        "due cards completed"
        in plan_turn(
            review_done,
            "next",
            intent="topic_drill",
            due_reviews=(),
            memory_state=MemoryState(),
        ).prompt
    )
    assert (
        "mastery target reached"
        in plan_turn(
            mastered,
            "next",
            intent="topic_drill",
            due_reviews=(),
            memory_state=MemoryState(),
        ).prompt
    )


def test_recall_state_round_trips_practice_fields() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = RecallState(
        last_confidence=0.6,
        session_goal="exam preparation",
        time_budget_minutes=45,
        practice_session_type="exam",
        practice_started_at=started,
        practice_turns=3,
        practice_stop_reason="mastery target reached",
        hint_level=2,
    )

    loaded = RecallState.from_dict(state.to_dict())

    assert loaded.last_confidence == 0.6
    assert loaded.session_goal == "exam preparation"
    assert loaded.time_budget_minutes == 45
    assert loaded.practice_session_type == "exam"
    assert loaded.practice_started_at == started
    assert loaded.practice_turns == 3
    assert loaded.practice_stop_reason == "mastery target reached"
    assert loaded.hint_level == 2


def test_evidence_assessment_and_pedagogy_validation_still_cover_policy_shapes() -> None:
    source_only = assess_evidence(("notes.md#chunk=1",), source_only=True)
    move = DocumentMove(
        kind="ask_recall",
        reason="test",
        requires_evidence=True,
        requires_user_commitment=True,
        difficulty="easy",
        target_topic="compactness",
        expected_output_shape="Ask one recall question.",
    )

    invalid = validate_pedagogy("The answer is compactness.", move)

    assert source_only.sufficient is False
    assert source_only.recommended_action == "give_partial_answer"
    assert invalid.valid is False
    assert set(invalid.issues) == {
        "missing confidence request",
        "possible answer leakage during recall",
    }


def test_due_reviews_and_memory_state_feed_policy_for_explicit_driven_intent() -> None:
    due = (ReviewItem(item="card one", concept="compactness"),)
    plan = plan_turn(
        RecallState(practice_session_type="review"),
        "practice",
        intent="driven_recall_calibration",
        due_reviews=due,
        memory_state=MemoryState(weak_topics=("limits",)),
    )

    assert plan.document_move is not None
    assert plan.document_move.kind == "ask_recall"
    assert plan.document_move.target_topic is None
    assert "Ask one recall task" in plan.prompt
