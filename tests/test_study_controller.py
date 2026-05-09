"""Tests for the deterministic study-loop controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hephaistos.study import (
    StudyAction,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
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


def test_first_turn_material_overview_disables_tools() -> None:
    state = StudyState()

    plan = plan_turn(state, "what is the material about")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "what is the material about"
    assert plan.allow_tools is False


def test_first_turn_explain_material_simply_uses_overview() -> None:
    state = StudyState()

    plan = plan_turn(state, "explain the material simply")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "explain the material simply"
    assert plan.allow_tools is False


def test_explicit_source_question_answers_without_entering_recall_loop() -> None:
    state = StudyState()

    plan = plan_turn(
        state,
        "Using the source files, what is the QA sentinel phrase? Answer with the exact phrase.",
    )
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        'The QA sentinel phrase is "amber forge" [E1].',
        ["materials/rag-target.md#chunk=0"],
    )

    assert plan.action is StudyAction.SOURCE_QA
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query is not None
    assert plan.allow_tools is False
    assert "Do not end with readiness" in plan.prompt
    assert cleaned == 'The QA sentinel phrase is "amber forge" [E1].'
    assert next_state.phase is StudyPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.expected_source_refs == []


@pytest.mark.parametrize(
    ("message", "reply"),
    [
        ("hey", "Hey."),
        ("hello!", "Hey."),
        ("thanks", "You're welcome."),
        ("thank you", "You're welcome."),
    ],
)
def test_initial_casual_message_gets_plain_reply(message: str, reply: str) -> None:
    state = StudyState()

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CHAT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert plan.direct_reply == reply

    next_state, cleaned = apply_turn_result(state, plan, "", [])

    assert cleaned == reply
    assert next_state.current_item == ""
    assert next_state.last_feedback_type is StudyFeedbackType.NONE


def test_easy_question_starts_calibration() -> None:
    state = StudyState()

    plan = plan_turn(state, "Can you ask me a really easy question")

    assert plan.action is StudyAction.CALIBRATE
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "Execute CALIBRATE" in plan.prompt
    assert "genuinely easy" in plan.prompt
    # Calibration must explicitly forbid trivial metadata questions
    assert "FORBIDDEN" in plan.prompt
    assert "Titles of documents" in plan.prompt


def test_exam_question_prompt_requires_timing_and_no_solution() -> None:
    state = StudyState()

    plan = plan_turn(state, "Ask me one random exam-style question from my past exams")

    assert plan.action is StudyAction.CALIBRATE
    assert plan.buffer_response is True
    assert "reasonable time limit" in plan.prompt
    assert "reason their answer from memory" in plan.prompt
    assert "do not show the result" in plan.prompt
    assert "answer key" in plan.prompt
    assert "source IDs" in plan.prompt
    assert "citations" in plan.prompt


def test_priority_request_does_not_start_recall_item() -> None:
    state = StudyState()

    plan = plan_turn(state, "Figure out my priorities")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "Prioritize recurrence relations first [E1].",
        ["materials/exam.md#chunk=0"],
    )

    assert plan.action is StudyAction.PRIORITY
    assert (
        plan.retrieval_query == "exam priority topics prerequisites past exams materials overview"
    )
    assert "Do not ask a recall question" in plan.prompt
    assert cleaned == "Prioritize recurrence relations first [E1]."
    assert next_state.current_item == ""
    assert next_state.phase is StudyPhase.PRESENTING


def test_calibration_prompt_forbids_metadata_questions() -> None:
    """Calibration prompt must contain constraints against surface metadata."""
    state = StudyState()
    plan = plan_turn(state, "quiz me")

    for forbidden in ("Titles of documents", "Author names", "File names"):
        assert forbidden in plan.prompt, f"Calibration prompt missing constraint: {forbidden}"


def test_calibration_result_starts_recall_from_model_question() -> None:
    state = StudyState()
    plan = plan_turn(state, "quiz me")

    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "What does the source say an index stores?",
        ["materials/notes.md#chunk=0"],
    )

    assert cleaned == "What does the source say an index stores?"
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "What does the source say an index stores?"
    assert next_state.expected_source_refs == ["materials/notes.md#chunk=0"]
    assert next_state.attempt_count == 0
    assert next_state.last_feedback_type is StudyFeedbackType.CALIBRATING


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
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    next_state, cleaned = apply_turn_result(state, plan, "State it from memory.", [], now=now)

    assert cleaned == "State it from memory."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.READY
    assert next_state.recall_started_at == now


def test_assess_partial_keeps_item_active() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
        recall_started_at=started,
    )

    plan = plan_turn(state, "I forgot the last step")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "PARTIAL: You omitted the final justification.",
        ["source/exam.md#chunk=0"],
        now=started + timedelta(seconds=45),
    )

    assert cleaned == "You omitted the final justification."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "Q1"
    assert next_state.attempt_count == 1
    assert next_state.last_feedback_type is StudyFeedbackType.PARTIAL
    assert next_state.last_recall_seconds == 45
    assert next_state.last_recall_rating is StudyRecallRating.HARD
    assert next_state.recall_started_at == started + timedelta(seconds=45)


def test_assess_correct_resets_for_next_item() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
        attempt_count=1,
        recall_started_at=started,
    )

    plan = plan_turn(state, "It equals 4 because ...")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "CORRECT: Correct. Move to the next item.",
        ["source/exam.md#chunk=0"],
        now=started + timedelta(seconds=18),
    )

    assert cleaned == "Correct. Move to the next item."
    assert next_state.phase is StudyPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.retrieval_query == ""
    assert next_state.expected_source_refs == []
    assert next_state.attempt_count == 2
    assert next_state.last_feedback_type is StudyFeedbackType.CORRECT
    assert next_state.last_recall_seconds == 18
    assert next_state.last_recall_rating is StudyRecallRating.EASY
    assert next_state.recall_started_at is None


def test_slow_correct_recall_is_hard_for_scheduler_signal() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        recall_started_at=started,
    )

    plan = plan_turn(state, "Eventually, the answer is 4")
    next_state, _cleaned = apply_turn_result(
        state,
        plan,
        "CORRECT: Correct. Move to the next item.",
        [],
        now=started + timedelta(minutes=3),
    )

    assert next_state.last_feedback_type is StudyFeedbackType.CORRECT
    assert next_state.last_recall_seconds == 180
    assert next_state.last_recall_rating is StudyRecallRating.HARD


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


def test_skip_without_current_item_requests_next_material_backed_item() -> None:
    state = StudyState()

    plan = plan_turn(state, "skip")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "next material-backed study item"


def test_skip_with_current_item_requests_different_material_backed_item() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "skip")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "different material-backed item from Q1"


def test_waiting_for_ready_reminder_keeps_waiting_state() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "what now?")
    next_state, cleaned = apply_turn_result(state, plan, "Say ready when you want recall.", [])

    assert plan.action is StudyAction.WAIT_READY_REMINDER
    assert cleaned == "Say ready when you want recall."
    assert next_state.phase is StudyPhase.WAITING_FOR_READY
    assert next_state.last_feedback_type is StudyFeedbackType.WAITING


def test_recall_phase_refuses_reveal_requests() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "tell me the full answer")
    next_state, cleaned = apply_turn_result(state, plan, "No. Attempt recall first.", [])

    assert plan.action is StudyAction.REFUSE_REVEAL
    assert plan.phase is StudyPhase.RECALL
    assert cleaned == "No. Attempt recall first."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.REFUSED


def test_recall_attempt_that_mentions_answer_is_assessed() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "the answer is 4 because I squared 2")

    assert plan.action is StudyAction.ASSESS
    assert plan.phase is StudyPhase.ASSESS


def test_recall_phase_can_request_easier_question_when_too_hard() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
    )

    plan = plan_turn(state, "too hard")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "What is the first definition used in Q1?",
        ["source/exam.md#chunk=0"],
    )

    assert plan.action is StudyAction.SIMPLIFY
    assert plan.use_expected_source_refs is True
    assert plan.allow_tools is False
    assert cleaned == "What is the first definition used in Q1?"
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "What is the first definition used in Q1?"
    assert next_state.attempt_count == 0
    assert next_state.last_feedback_type is StudyFeedbackType.EASIER


def test_simplify_prompt_forbids_metadata_questions() -> None:
    """Simplify prompt must contain constraints against surface metadata."""
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
    )

    plan = plan_turn(state, "too hard")

    assert "not document titles" in plan.prompt
    assert "surface metadata" in plan.prompt


def test_recall_phase_can_review_material_when_student_requests_it() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
        attempt_count=2,
    )

    plan = plan_turn(state, "review material")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "Review the setup. Say ready when you want recall.",
        ["source/exam.md#chunk=0"],
    )

    assert plan.action is StudyAction.REVIEW
    assert plan.use_expected_source_refs is True
    assert cleaned == "Review the setup. Say ready when you want recall."
    assert next_state.phase is StudyPhase.WAITING_FOR_READY
    assert next_state.current_item == "Q1"
    assert next_state.attempt_count == 0
    assert next_state.last_feedback_type is StudyFeedbackType.REVIEWING


def test_hint_requests_require_a_prior_attempt() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        attempt_count=0,
    )

    plan = plan_turn(state, "hint please")

    assert plan.action is StudyAction.ASSESS
    assert plan.use_expected_source_refs is True


def test_hint_requests_after_an_attempt_return_hint_plan() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        attempt_count=1,
    )

    plan = plan_turn(state, "hint please")

    assert plan.action is StudyAction.HINT
    assert plan.phase is StudyPhase.ASSESS
    assert plan.retrieval_query == "Q1"
    assert plan.use_expected_source_refs is True
    assert plan.allow_tools is False


def test_present_result_without_source_refs_resets_current_item() -> None:
    state = StudyState()
    plan = plan_turn(state, "Explain question 1")

    next_state, cleaned = apply_turn_result(state, plan, "No grounded source found.", [])

    assert cleaned == "No grounded source found."
    assert next_state.phase is StudyPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.retrieval_query == ""
    assert next_state.expected_source_refs == []
    assert next_state.last_feedback_type is StudyFeedbackType.NO_SOURCE


def test_hint_result_updates_expected_source_refs_when_present() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["old-ref"],
        attempt_count=1,
    )
    plan = plan_turn(state, "need a hint")

    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "Start with the first substitution.",
        ["source/exam.md#chunk=1"],
    )

    assert cleaned == "Start with the first substitution."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.expected_source_refs == ["source/exam.md#chunk=1"]
    assert next_state.last_feedback_type is StudyFeedbackType.HINT


def test_empty_assessment_body_uses_feedback_fallback_message() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "attempt")
    next_state, cleaned = apply_turn_result(state, plan, "WRONG:", [])

    assert cleaned == "Start again from the first step only."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.WRONG
    assert next_state.attempt_count == 1
