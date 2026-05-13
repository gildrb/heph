"""Tests for the deterministic study-loop controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hephaistos.study import (
    MemoryState,
    StudyAction,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
    apply_turn_result,
    assess_choice_response,
    assess_evidence,
    choice_prompt,
    plan_turn,
    validate_pedagogy,
)


def test_first_turn_plans_presentation() -> None:
    state = StudyState()

    plan = plan_turn(state, "Explain question 1")

    assert plan.action is StudyAction.PRESENT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == "Explain question 1"
    assert plan.allow_tools is True


def test_study_state_round_trips_confidence() -> None:
    state = StudyState(last_confidence=0.6)

    loaded = StudyState.from_dict(state.to_dict())

    assert loaded.last_confidence == 0.6


def test_study_state_round_trips_autonomy_session() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        session_goal="exam preparation",
        time_budget_minutes=45,
        autopilot_session_type="exam",
        autopilot_started_at=started,
        autopilot_turns=3,
        autopilot_stop_reason="mastery target reached",
        hint_level=2,
    )

    loaded = StudyState.from_dict(state.to_dict())

    assert loaded.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    assert loaded.session_goal == "exam preparation"
    assert loaded.time_budget_minutes == 45
    assert loaded.autopilot_session_type == "exam"
    assert loaded.autopilot_started_at == started
    assert loaded.autopilot_turns == 3
    assert loaded.autopilot_stop_reason == "mastery target reached"
    assert loaded.hint_level == 2


def test_autopilot_time_budget_returns_completion_reply() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        time_budget_minutes=10,
        autopilot_started_at=datetime.now(UTC) - timedelta(minutes=11),
    )

    plan = plan_turn(state, "next")

    assert plan.action is StudyAction.CHAT
    assert plan.direct_reply is not None
    assert "time budget reached" in plan.direct_reply


def test_autopilot_review_stops_when_due_cards_complete() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        autopilot_session_type="review",
        autopilot_turns=2,
    )

    plan = plan_turn(state, "next", due_reviews=(), memory_state=MemoryState())

    assert plan.action is StudyAction.CHAT
    assert plan.direct_reply is not None
    assert "due cards completed" in plan.direct_reply


def test_autopilot_stops_when_mastery_target_reached() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        autopilot_turns=4,
    )

    plan = plan_turn(state, "next", due_reviews=(), memory_state=MemoryState())

    assert plan.action is StudyAction.CHAT
    assert plan.direct_reply is not None
    assert "mastery target reached" in plan.direct_reply


def test_guided_plan_attaches_study_move_policy() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)

    plan = plan_turn(state, "help me study Bayes theorem")

    assert plan.autonomy_mode is StudyAutonomyMode.GUIDED
    assert plan.study_move is not None
    assert plan.study_move.kind == "ask_recall"
    assert "Autonomous study policy" in plan.prompt
    assert "confidence from 0-100%" in plan.prompt


def test_just_answer_temporarily_uses_manual_mode() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)

    plan = plan_turn(state, "just answer this from the source")

    assert plan.autonomy_mode is StudyAutonomyMode.MANUAL
    assert "Autonomous study policy" not in plan.prompt


def test_evidence_assessment_abstains_for_source_only_without_refs() -> None:
    assessment = assess_evidence((), source_only=True)

    assert assessment.sufficient is False
    assert assessment.recommended_action == "abstain"
    assert assessment.missing_information


def test_pedagogy_validation_flags_missing_confidence_for_recall() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)
    plan = plan_turn(state, "quiz me")
    assert plan.study_move is not None

    validation = validate_pedagogy(
        "Try defining the theorem from memory.",
        plan.study_move,
        plan.autonomy_mode,
    )

    assert validation.valid is False
    assert "missing confidence request" in validation.issues


def test_choice_prompt_requires_reason_confidence_and_weakness() -> None:
    prompt = choice_prompt(
        "There is a real study fork.",
        ("Active recall question", "Worked example", "Prerequisite repair"),
    )

    assert "Choose one path, but include your reasoning" in prompt
    assert "A. Active recall question" in prompt
    assert "confidence from 0-100%" in prompt
    assert "weakest point" in prompt


def test_choice_assessment_accepts_metacognitive_choice() -> None:
    assessment = assess_choice_response(
        "Option B because examples expose my weak point. Confidence: 70%. "
        "My weakest point is setup.",
        recommended_option="B",
    )

    assert assessment.valid is True
    assert assessment.selected_option == "B"
    assert assessment.confidence == 0.7
    assert assessment.has_reason is True
    assert assessment.should_override is False


def test_choice_assessment_recommends_overriding_weak_choice() -> None:
    assessment = assess_choice_response("A", recommended_option="C")

    assert assessment.valid is False
    assert assessment.selected_option == "A"
    assert assessment.recommendation == "C"
    assert assessment.should_override is True
    assert "missing reason" in assessment.issues
    assert "weak justification for non-recommended option" in assessment.issues


def test_choice_policy_prompt_overrides_passive_options() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)

    plan = plan_turn(state, "Which option should I choose next?")

    assert plan.study_move is not None
    assert plan.study_move.kind == "offer_choices"
    assert "Require: option, reason, confidence from 0-100%, and weakest point." in plan.prompt
    assert "Override a weak choice" in plan.prompt


def test_choice_reply_selects_worked_example_when_justified() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)

    plan = plan_turn(
        state,
        "Option B because I need one concrete example first. Confidence: 72%. "
        "My weakest point is applying the setup.",
    )

    assert plan.study_move is not None
    assert plan.study_move.kind == "worked_example"
    assert (
        "guided mode follows the learner's justified study-path choice" in plan.study_move.reason
    )


def test_choice_reply_overrides_weak_non_recommended_path() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.GUIDED,
        last_feedback_type=StudyFeedbackType.WRONG,
    )

    plan = plan_turn(state, "Option A")

    assert plan.study_move is not None
    assert plan.study_move.kind == "contrastive_question"
    assert "overrides to the stronger pedagogical option" in plan.study_move.reason


def test_policy_uses_local_intervention_outcomes_for_next_move() -> None:
    plan = plan_turn(
        StudyState(autonomy_mode=StudyAutonomyMode.GUIDED),
        "help me study",
        memory_state=MemoryState(
            misconceptions=("Bayes theorem",),
            successful_interventions=("give_hint",),
            failed_interventions=("contrastive_question",),
        ),
    )

    assert plan.study_move is not None
    assert plan.study_move.kind == "give_hint"
    assert plan.study_move.target_topic == "Bayes theorem"
    assert "local policy outcomes" in plan.study_move.reason


def test_first_turn_material_overview_uses_internal_evidence_without_llm_tools() -> None:
    state = StudyState()

    plan = plan_turn(state, "what is the material about")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "what is the material about"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute MATERIAL_OVERVIEW" in plan.prompt
    assert "not as the entire corpus" in plan.prompt
    assert "Do not infer from filenames" in plan.prompt
    assert "Use material tools to inspect indexed sources" not in plan.prompt
    assert "Do not paste long source excerpts" in plan.prompt


def test_source_worded_material_overview_still_uses_overview_plan() -> None:
    state = StudyState()

    plan = plan_turn(
        state,
        "Using the indexed sources, give a concise grounded overview of the enabled material.",
    )

    assert plan.action is StudyAction.PRESENT
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute MATERIAL_OVERVIEW" in plan.prompt


def test_first_turn_explain_material_simply_uses_overview() -> None:
    state = StudyState()

    plan = plan_turn(state, "explain the material simply")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "explain the material simply"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "document types" in plan.prompt


def test_read_through_all_files_uses_overview() -> None:
    state = StudyState()

    plan = plan_turn(state, "Can you read through all the files")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "Can you read through all the files"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute MATERIAL_OVERVIEW" in plan.prompt


def test_read_through_files_interrupts_ready_wait_with_overview() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="what are the materials about",
        retrieval_query="what are the materials about",
        expected_source_refs=["materials/a.md#chunk=0"],
    )

    plan = plan_turn(state, "Can you read through all the files")

    assert plan.action is StudyAction.PRESENT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.buffer_response is True
    assert plan.allow_tools is False
    assert "Execute MATERIAL_OVERVIEW" in plan.prompt


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
        (
            "hey",
            "Hey. I can run material-backed study with /exam, /priority, or /autopilot on.",
        ),
        (
            "hello!",
            "Hey. I can run material-backed study with /exam, /priority, or /autopilot on.",
        ),
        (
            "What can I use this for?",
            "Use Hephaistos to study your own materials: ask a source-backed question, run "
            "/exam for active recall, run /priority for a plan, or /autopilot on to start a "
            "bounded guided session.",
        ),
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

    plan = plan_turn(state, "It equals 4 because ... Confidence: 80%.")
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
    assert next_state.last_confidence == 0.8
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


@pytest.mark.parametrize("followup", ["interesting", "why", "ok why"])
def test_waiting_for_ready_followups_use_stored_evidence(followup: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="what is the material about",
        retrieval_query="what is the material about",
        expected_source_refs=["materials/lecture.md#chunk=0"],
    )

    plan = plan_turn(state, followup)

    assert plan.action is StudyAction.REVIEW
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.use_expected_source_refs is True
    assert plan.retrieval_query == "what is the material about"
    assert plan.allow_tools is False
    assert "SOURCE_FOLLOWUP" in plan.prompt
    assert "not as a readiness signal" in plan.prompt


def test_im_ready_moves_waiting_state_to_recall() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "im ready")

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert "Execute RECALL" in plan.prompt


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


def test_recall_clarification_is_not_assessed_as_attempt() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "which answer")

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert "RECALL_CLARIFICATION" in plan.prompt


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
    assert "retrieved source span" in plan.prompt
    assert "Do not invent prerequisite questions" in plan.prompt


def test_calibration_prompt_requires_grounded_questions() -> None:
    state = StudyState()

    plan = plan_turn(state, "quiz me")

    assert plan.action is StudyAction.CALIBRATE
    assert "retrieved source span" in plan.prompt
    assert "past-exam pattern" in plan.prompt
    assert "never invent unsupported questions" in plan.prompt


def test_assessment_prompt_requires_source_backed_feedback_shape() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Explain the mechanism.",
        retrieval_query="Explain the mechanism.",
        expected_source_refs=["source/exam.md#chunk=0"],
    )

    plan = plan_turn(state, "It works because the receptor opens.")

    assert plan.action is StudyAction.ASSESS
    assert "retrieved material only" in plan.prompt
    assert "source of truth" in plan.prompt
    assert "Score:" in plan.prompt
    assert "Missing:" in plan.prompt
    assert "Misconception:" in plan.prompt
    assert "Correction:" in plan.prompt
    assert "Confidence:" in plan.prompt
    assert "default to PARTIAL:" in plan.prompt


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


def test_hint_prompt_uses_ladder_level_one_for_first_hint() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        attempt_count=1,
        hint_level=0,
    )

    plan = plan_turn(state, "hint please")

    assert plan.action is StudyAction.HINT
    assert "Hint level: 1" in plan.prompt
    assert "orienting hint" in plan.prompt
    assert "Do not reveal later steps" in plan.prompt


def test_hint_prompt_uses_ladder_level_four_for_deeper_scaffold() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        attempt_count=1,
        hint_level=3,
    )

    plan = plan_turn(state, "hint please")

    assert plan.action is StudyAction.HINT
    assert "Hint level: 4" in plan.prompt
    assert "partial worked step" in plan.prompt


def test_hint_prompt_uses_ladder_level_five_for_full_solution() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        attempt_count=1,
        hint_level=4,
    )

    plan = plan_turn(state, "hint please")

    assert plan.action is StudyAction.HINT
    assert "Hint level: 5" in plan.prompt
    assert "full solution with explanation" in plan.prompt


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


def test_autopilot_no_source_marks_stop_reason() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.AUTOPILOT)
    plan = plan_turn(state, "Explain question 1")

    next_state, _cleaned = apply_turn_result(state, plan, "No grounded source found.", [])

    assert next_state.autopilot_stop_reason == "evidence is insufficient"


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
    assert next_state.hint_level == 1


def test_hint_level_resets_after_correct_assessment() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        hint_level=2,
        recall_started_at=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
    )
    plan = plan_turn(state, "answer confidence 80%")

    next_state, _cleaned = apply_turn_result(
        state,
        plan,
        "CORRECT: Good.",
        ["source/exam.md#chunk=1"],
        now=datetime(2026, 5, 9, 12, 0, 20, tzinfo=UTC),
    )

    assert next_state.hint_level == 0
    assert next_state.last_recall_rating is StudyRecallRating.EASY


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


def test_autopilot_wrong_after_many_hints_marks_frustration_stop_reason() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        hint_level=4,
    )
    plan = plan_turn(state, "attempt")

    next_state, _cleaned = apply_turn_result(
        state,
        plan,
        "WRONG: Start over from first principles.",
        ["source/exam.md#chunk=0"],
    )

    assert next_state.autopilot_stop_reason == "learner fatigue or frustration detected"
