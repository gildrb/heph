"""Tests for the deterministic study-loop controller."""

from __future__ import annotations

from hephaistos.study import (
    StudyAction,
    StudyFeedbackType,
    StudyPhase,
    StudyState,
    apply_turn_result,
    plan_turn,
)


def test_first_turn_plans_presentation() -> None:
    state = StudyState()

    plan = plan_turn(state, "Explain question 1")

    assert plan.action is StudyAction.PRESENT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == "Explain question 1"
    assert plan.allow_tools is True


def test_waiting_for_ready_refuses_more_reveal() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "show me the answer again")

    assert plan.action is StudyAction.REFUSE_REVEAL
    assert plan.phase is StudyPhase.WAITING_FOR_READY
    assert plan.allow_tools is False


def test_ready_signal_moves_to_recall() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "ready")
    next_state, cleaned = apply_turn_result(state, plan, "State it from memory.", [])

    assert cleaned == "State it from memory."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.READY


def test_assess_partial_keeps_item_active() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
    )

    plan = plan_turn(state, "I forgot the last step")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "PARTIAL: You omitted the final justification.",
        ["source/exam.md#chunk=0"],
    )

    assert cleaned == "You omitted the final justification."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "Q1"
    assert next_state.attempt_count == 1
    assert next_state.last_feedback_type is StudyFeedbackType.PARTIAL


def test_assess_correct_resets_for_next_item() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, "It equals 4 because ...")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "CORRECT: Correct. Move to the next item.",
        ["source/exam.md#chunk=0"],
    )

    assert cleaned == "Correct. Move to the next item."
    assert next_state.phase is StudyPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.retrieval_query == ""
    assert next_state.expected_source_refs == []
    assert next_state.attempt_count == 2
    assert next_state.last_feedback_type is StudyFeedbackType.CORRECT


def test_missing_assessment_prefix_defaults_to_partial() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "attempt")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "You are missing the setup.",
        [],
    )

    assert cleaned == "You are missing the setup."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.PARTIAL
    assert next_state.attempt_count == 1
