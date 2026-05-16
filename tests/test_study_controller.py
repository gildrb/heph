"""Tests for the deterministic study-loop controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hephaistos.study import (
    ExamSession,
    ExamSessionItem,
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
    manual_chat_plan,
    material_topic_drill_plan,
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
    assert "signal when they are ready for recall" in plan.prompt
    assert "Do not require a specific English word such as `ready`" in plan.prompt
    assert "type the literal command `ready`" not in plan.prompt
    assert "End with exactly: Say ready when you want recall" not in plan.prompt


def test_manual_chat_plan_is_non_material_specific() -> None:
    plan = manual_chat_plan("que puedes hacer?")

    assert plan.action is StudyAction.CHAT
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert plan.direct_reply is None
    assert "HEPH chat mode" in plan.prompt
    assert "same language as the user's request" in plan.prompt
    assert "que puedes hacer?" in plan.prompt


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


def test_autopilot_start_turn_disables_agent_tools() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        session_goal="exam preparation",
        autopilot_session_type="exam",
        autopilot_started_at=datetime.now(UTC),
    )

    plan = plan_turn(
        state,
        "Start an autopilot study session from my materials using the exam profile. "
        "Use exam preparation as the session goal.",
    )

    assert plan.action is StudyAction.CALIBRATE
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert plan.autonomy_mode is StudyAutonomyMode.AUTOPILOT


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
    assert "why the recommendation is beneficial" in plan.prompt
    assert "Treat the response shape as semantic guidance" in plan.prompt
    assert "adapt the wording to the learner's language" in plan.prompt


def test_manual_mode_answers_direct_requests_without_study_loop() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.MANUAL)

    plan = plan_turn(state, "Explain Bayes theorem")

    assert plan.action is StudyAction.CHAT
    assert plan.autonomy_mode is StudyAutonomyMode.MANUAL
    assert plan.retrieval_query == "Explain Bayes theorem"
    assert "same language as the user's request" in plan.prompt
    assert "normal conversational assistant" in plan.prompt
    assert "Do not force a ready/recall loop" in plan.prompt
    assert "Say ready when you want recall" not in plan.prompt
    assert "Autonomous study policy" not in plan.prompt


def test_manual_mode_does_not_escalate_study_language_to_guided() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.MANUAL)

    plan = plan_turn(state, "help me study Bayes theorem")

    assert plan.autonomy_mode is StudyAutonomyMode.MANUAL
    assert plan.action is StudyAction.CHAT


@pytest.mark.parametrize("message", ["hey", "hello!", "thanks", "What can I use this for?"])
def test_manual_mode_light_chat_goes_to_model_without_tools(message: str) -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.MANUAL)

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CHAT
    assert plan.autonomy_mode is StudyAutonomyMode.MANUAL
    assert plan.direct_reply is None
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "HEPH chat mode" in plan.prompt
    assert "same language as the user's request" in plan.prompt
    assert "available tools" not in plan.prompt


@pytest.mark.parametrize("message", ["hey", "hello!", "thanks", "What can I use this for?"])
def test_armory_harness_light_chat_disables_tools_with_canned_replies(message: str) -> None:
    state = StudyState()

    plan = plan_turn(state, message, allow_direct_chat=False)

    assert plan.action is StudyAction.CHAT
    assert plan.direct_reply is None
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "HEPH chat mode" in plan.prompt
    assert "available tools" not in plan.prompt


def test_manual_mode_does_not_resume_prior_ready_loop() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.MANUAL,
        phase=StudyPhase.RECALL,
        current_item="Define conditional probability.",
        retrieval_query="conditional probability",
        expected_source_refs=["source/notes.md#chunk=0"],
    )

    plan = plan_turn(state, "what is the answer?")

    assert plan.action is StudyAction.CHAT
    assert plan.phase is StudyPhase.PRESENTING
    assert "Do not force a ready/recall loop" in plan.prompt


def test_guided_recommendations_require_a_reason() -> None:
    state = StudyState(autonomy_mode=StudyAutonomyMode.GUIDED)
    plan = plan_turn(state, "Explain Bayes theorem")
    assert plan.study_move is not None

    validation = validate_pedagogy(
        "Here is the source-backed answer. Next action: review one similar example.",
        plan.study_move,
        plan.autonomy_mode,
    )

    assert validation.valid is False
    assert "missing recommendation rationale" in validation.issues


def test_autopilot_first_turn_drives_a_diagnostic() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        session_goal="exam preparation",
        autopilot_session_type="exam",
    )

    plan = plan_turn(state, "Explain Bayes theorem")

    assert plan.action is StudyAction.CALIBRATE
    assert plan.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    assert plan.retrieval_query == "Explain Bayes theorem"
    assert plan.study_move is not None
    assert plan.study_move.kind == "ask_recall"
    assert "HEPH AUTOPILOT calibration" in plan.prompt
    assert "drive the study workflow" in plan.prompt
    assert "Start directly with the recall task" in plan.prompt
    assert "do not reveal the answer" in plan.prompt.lower()
    assert "confidence from 0-100%" in plan.prompt


def test_autopilot_command_bootstrap_uses_corpus_diagnostic() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        session_goal="autonomous study",
        autopilot_session_type="general",
    )

    plan = plan_turn(
        state,
        "Start an autopilot study session from my materials using the general profile. "
        "Use autonomous study as the session goal.",
    )

    assert plan.action is StudyAction.CALIBRATE
    assert plan.retrieval_query is None
    assert "Use the retrieved source material to ask exactly one diagnostic" in plan.prompt
    assert "Use only the provided source material" in plan.prompt
    assert "student's language" in plan.prompt
    assert "Do not hard-code an English closing instruction" in plan.prompt
    assert "provided canonical source label" in plan.prompt


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
    assert "do not explain retrieval sampling mechanics" in plan.prompt
    assert "generic sampling or completeness disclaimer" in plan.prompt
    assert "non-exhaustive list" in plan.prompt
    assert "Do not infer from filenames" in plan.prompt
    assert "semester labels" in plan.prompt
    assert "course administration metadata" in plan.prompt
    assert "Use material tools to inspect indexed sources" not in plan.prompt
    assert "Do not paste long source excerpts" in plan.prompt
    assert "next-step, evidence-grounding-block" in plan.prompt


def test_material_overview_result_does_not_enter_ready_loop() -> None:
    state = StudyState()
    plan = plan_turn(state, "what is the material about")

    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "The material covers graph algorithms and exams [E1].",
        ["materials/algorithms.md#chunk=0"],
    )

    assert cleaned == "The material covers graph algorithms and exams [E1]."
    assert next_state.phase is StudyPhase.PRESENTING
    assert next_state.current_item == ""
    assert next_state.retrieval_query == ""
    assert next_state.expected_source_refs == []
    assert next_state.last_feedback_type is StudyFeedbackType.NONE


def test_non_english_material_overview_is_left_for_model_intent_normalization() -> None:
    state = StudyState()

    plan = plan_turn(state, "um was geht es in den dateien")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "um was geht es in den dateien"
    assert plan.allow_tools is True
    assert plan.buffer_response is False
    assert "Execute MATERIAL_OVERVIEW" not in plan.prompt


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
    assert plan.retrieval_query == "what is the material about"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "User request: explain the material simply" in plan.prompt
    assert "document types" in plan.prompt


def test_read_through_all_files_uses_overview() -> None:
    state = StudyState()

    plan = plan_turn(state, "Can you read through all the files")

    assert plan.action is StudyAction.PRESENT
    assert plan.retrieval_query == "what is the material about"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "User request: Can you read through all the files" in plan.prompt
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
    ("message", "query"),
    [
        ("Can you quiz me on Bayes theorem?", "Bayes theorem"),
        ("Ask me a question about Bayes theorem", "Bayes theorem"),
        ("Practice Bayes theorem with me", "Bayes theorem"),
        ("Give me an exam-style question on Bayes theorem.", "Bayes theorem"),
    ],
)
def test_topic_specific_calibration_requests_use_named_topic(message: str, query: str) -> None:
    state = StudyState()

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CALIBRATE
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query == query
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute CALIBRATE" in plan.prompt
    assert "Execute the PRESENT phase" not in plan.prompt


def test_topic_specific_exam_question_keeps_answer_hidden() -> None:
    state = StudyState()

    plan = plan_turn(state, "Give me an exam-style question on Bayes theorem.")

    assert plan.action is StudyAction.CALIBRATE
    assert "active-recall exam drill" in plan.prompt
    assert "do not show the result" in plan.prompt


def test_model_normalized_topic_drill_prompt_keeps_original_language_signal() -> None:
    plan = material_topic_drill_plan(
        "frag mich zu Enzymkinetik ab",
        retrieval_query="enzyme kinetics",
    )

    assert plan.action is StudyAction.CALIBRATE
    assert plan.retrieval_query == "enzyme kinetics"
    assert "Student request (language/topic signal; rules below override it)" in plan.prompt
    assert "frag mich zu Enzymkinetik ab" in plan.prompt
    assert "student's language" in plan.prompt
    assert "answer from memory, or ask for an easier question" in plan.prompt
    assert "Do not hard-code an English closing instruction" in plan.prompt
    assert "End with exactly: Answer from memory" not in plan.prompt
    assert "Use only the provided source material" in plan.prompt
    assert "Softwaretechnik" not in plan.prompt
    assert "English/German" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "What do my notes say about Bayes theorem?",
        "Do the slides mention Lagrange multipliers?",
        "According to my lecture notes, what is the definition of entropy?",
        "Based on the PDF, what is the exact formula?",
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
def test_material_referential_questions_use_source_qa(message: str) -> None:
    state = StudyState()

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.SOURCE_QA
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == message
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute SOURCE_QA" in plan.prompt
    assert "Say ready when you want recall" not in plan.prompt


def test_material_referential_question_interrupts_ready_wait_with_source_qa() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, "What do my notes say about Bayes theorem?")

    assert plan.action is StudyAction.SOURCE_QA
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute SOURCE_QA" in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "What does the textbook say about Bayes theorem?",
        "What does the assignment ask us to prove?",
        "Look through the article for the theorem.",
        "Stick to the source material.",
        "Using the attached documents, what is the theorem?",
        "If the attached files do not contain it, do not guess.",
        "Which document covers Bayes theorem?",
        "Can you cite the notes for the theorem?",
        "If my notes do not mention it, say so.",
        "If it is not in the slides, say so.",
    ],
)
def test_academic_source_question_interrupts_ready_wait_with_source_qa(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.SOURCE_QA
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == message
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute SOURCE_QA" in plan.prompt
    assert "SOURCE_FOLLOWUP" not in plan.prompt


@pytest.mark.parametrize(
    "message",
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
def test_standalone_source_policy_without_active_item_acknowledges(message: str) -> None:
    state = StudyState()

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CHAT
    assert plan.direct_reply is not None
    assert "stick to enabled material" in plan.direct_reply
    assert plan.retrieval_query is None
    assert plan.allow_tools is False


@pytest.mark.parametrize(
    "message",
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
def test_standalone_source_policy_does_not_reset_ready_wait(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.REVIEW
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == "conditional probability"
    assert plan.use_expected_source_refs is True
    assert "SOURCE_FOLLOWUP" in plan.prompt
    assert "same language as the student's follow-up" in plan.prompt
    assert "Execute SOURCE_QA" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Can you quiz me on Bayes theorem?",
        "Ask me a question about Bayes theorem",
        "Practice Bayes theorem with me",
    ],
)
def test_topic_specific_drill_interrupts_ready_wait_with_calibration(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CALIBRATE
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query == "Bayes theorem"
    assert plan.use_expected_source_refs is False
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute CALIBRATE" in plan.prompt
    assert "SOURCE_FOLLOWUP" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Explain Bayes theorem",
        "Teach me derivatives",
        "Can you help me study eigenvalues?",
        "Can you compare Bayes theorem and conditional probability?",
        "Compare Bayes theorem with conditional probability",
        "What are the differences between Bayes theorem and conditional probability?",
        "Can you give me an example of Bayes theorem?",
        "Do Bayes theorem",
        "Let's do Bayes theorem",
        "Can we do Bayes theorem?",
        "I want to study Bayes theorem",
        "I would like to study Bayes theorem",
        "Work on Bayes theorem with me",
        "Move to eigenvalues",
        "Switch to Lagrange multipliers",
        "Start derivatives",
        "Next topic: entropy",
    ],
)
def test_new_topic_question_interrupts_ready_wait_with_fresh_presentation(
    message: str,
) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.PRESENT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == message
    assert plan.use_expected_source_refs is False
    assert plan.allow_tools is True
    assert "Execute the PRESENT phase" in plan.prompt
    assert "SOURCE_FOLLOWUP" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Explain the question again",
        "Teach me this again",
        "Can you compare this with that?",
        "Can you give me an example of the question?",
        "Let's do this again",
    ],
)
def test_followup_referents_do_not_start_fresh_topic_in_ready_wait(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.REVIEW
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == "conditional probability"
    assert plan.use_expected_source_refs is True
    assert "SOURCE_FOLLOWUP" in plan.prompt
    assert "same language as the student's follow-up" in plan.prompt
    assert "Execute the PRESENT phase" not in plan.prompt


def test_material_referential_question_interrupts_recall_with_source_qa() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, "What do my notes say about Bayes theorem?")

    assert plan.action is StudyAction.SOURCE_QA
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == "What do my notes say about Bayes theorem?"
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute SOURCE_QA" in plan.prompt
    assert "Execute ASSESS" not in plan.prompt
    assert "Execute RECALL_CLARIFICATION" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Can you quiz me on Bayes theorem?",
        "Ask me a question about Bayes theorem",
        "Practice Bayes theorem with me",
    ],
)
def test_topic_specific_drill_interrupts_recall_with_calibration(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.CALIBRATE
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query == "Bayes theorem"
    assert plan.use_expected_source_refs is False
    assert plan.allow_tools is False
    assert plan.buffer_response is True
    assert "Execute CALIBRATE" in plan.prompt
    assert "Execute ASSESS" not in plan.prompt
    assert "Execute RECALL_CLARIFICATION" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Explain Bayes theorem",
        "Can you compare Bayes theorem and conditional probability?",
        "Compare Bayes theorem with conditional probability",
        "What are the differences between Bayes theorem and conditional probability?",
        "Can you give me an example of Bayes theorem?",
        "Do Bayes theorem",
        "Let's do Bayes theorem",
        "Can we do Bayes theorem?",
        "I want to study Bayes theorem",
        "I would like to study Bayes theorem",
        "Work on Bayes theorem with me",
        "Move to eigenvalues",
        "Switch to Lagrange multipliers",
        "Start derivatives",
        "Next topic: entropy",
    ],
)
def test_new_topic_question_interrupts_recall_with_fresh_presentation(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.PRESENT
    assert plan.phase is StudyPhase.PRESENTING
    assert plan.retrieval_query == message
    assert plan.use_expected_source_refs is False
    assert plan.allow_tools is True
    assert "Execute the PRESENT phase" in plan.prompt
    assert "Execute ASSESS" not in plan.prompt


def test_explain_question_again_in_recall_reprompts_without_assessing() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, "Explain the question again")

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "Execute RECALL_CLARIFICATION" in plan.prompt
    assert "Execute the PRESENT phase" not in plan.prompt
    assert "Execute ASSESS" not in plan.prompt


def test_lets_do_this_again_in_recall_reprompts_without_assessing() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, "Let's do this again")

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "Execute RECALL_CLARIFICATION" in plan.prompt
    assert "Execute the PRESENT phase" not in plan.prompt
    assert "Execute ASSESS" not in plan.prompt


@pytest.mark.parametrize(
    "message",
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
def test_standalone_source_policy_in_recall_reprompts_without_assessing(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="define conditional probability",
        retrieval_query="conditional probability",
        expected_source_refs=["materials/notes.md#chunk=0"],
        attempt_count=1,
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "Execute RECALL_CLARIFICATION" in plan.prompt
    assert "Execute SOURCE_QA" not in plan.prompt
    assert "Execute ASSESS" not in plan.prompt


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
            "Use Hephaistos to study your own materials: ask a source-grounded question, run "
            "/exam for active recall, run /priority for a plan, or /autopilot on to let Heph "
            "drive the session.",
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
    assert "active-recall questions, not passive summaries" in plan.prompt
    assert "Each question must ask exactly one thing" in plan.prompt
    assert "trade-offs" in plan.prompt
    assert "copyright text" in plan.prompt
    assert "English term and a local-language technical term" in plan.prompt
    assert "Keep expected answers concise but exam-useful" in plan.prompt
    assert "filenames, chunk IDs, dates, or instructor metadata" in plan.prompt


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
    assert "User request: Figure out my priorities" in plan.prompt
    assert "same language as the student's request" in plan.prompt
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


@pytest.mark.parametrize("message", ["show me the answer again", "explain again"])
def test_waiting_for_ready_refuses_more_reveal(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, message)

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


def test_non_english_ready_signal_is_not_hard_coded_in_controller() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Definiere bedingte Wahrscheinlichkeit.",
        retrieval_query="conditional probability",
    )

    plan = plan_turn(state, "ich bin bereit")

    assert plan.action is StudyAction.REVIEW
    assert "SOURCE_FOLLOWUP" in plan.prompt


def test_recall_prompt_localizes_short_memory_instruction() -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Definiere eine Folge mit Definitionsmenge und Folgenglied.",
        retrieval_query="folge definition",
    )

    plan = plan_turn(state, "ready")

    assert plan.action is StudyAction.PROMPT_RECALL
    assert "same language as the current item" in plan.prompt
    assert "Do not hard-code an English recall sentence" in plan.prompt


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

    assert cleaned == "PARTIAL: You omitted the final justification."
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

    assert cleaned == "CORRECT: Correct. Move to the next item."
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


def test_exam_session_summary_is_added_only_when_session_becomes_complete() -> None:
    started = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q2",
        retrieval_query="Q2",
        expected_source_refs=["source/exam.md#chunk=1"],
        recall_started_at=started,
        exam_session=ExamSession(
            items=[
                ExamSessionItem(
                    question="Q1",
                    source_ref="source/exam.md#chunk=0",
                    status="correct",
                ),
                ExamSessionItem(
                    question="Q2",
                    source_ref="source/exam.md#chunk=1",
                    status="active",
                ),
            ],
            active_index=1,
            completed_count=1,
        ),
    )

    plan = plan_turn(state, "The recalled answer is Q2. Confidence: 80%.")
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "CORRECT: Correct. Move to the next item.",
        ["source/exam.md#chunk=1"],
        now=started + timedelta(seconds=10),
    )

    assert "Exam session summary" in cleaned
    next_state.phase = StudyPhase.RECALL
    next_state.current_item = "Q2"
    next_state.retrieval_query = "Q2"
    next_state.expected_source_refs = ["source/exam.md#chunk=1"]
    next_state.recall_started_at = started + timedelta(seconds=20)

    plan = plan_turn(next_state, "The answer remains Q2. Confidence: 80%.")
    _final_state, cleaned_again = apply_turn_result(
        next_state,
        plan,
        "CORRECT: Still correct.",
        ["source/exam.md#chunk=1"],
        now=started + timedelta(seconds=30),
    )

    assert "Exam session summary" not in cleaned_again


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

    assert cleaned == "PARTIAL: You are missing the setup."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.last_feedback_type is StudyFeedbackType.PARTIAL
    assert next_state.attempt_count == 1


def test_structured_assessment_reply_preserves_label_and_sections() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "attempt")
    _next_state, cleaned = apply_turn_result(
        state,
        plan,
        "PARTIAL:\n"
        "Score: 1/2.\n"
        "Got: You recalled the definition.\n"
        "Missing: You missed the condition.",
        [],
    )

    assert cleaned.startswith("PARTIAL:\nScore: 1/2.")
    assert "Got: You recalled the definition." in cleaned
    assert "Missing: You missed the condition." in cleaned


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


@pytest.mark.parametrize(
    "message",
    [
        "what now?",
        "not ready yet",
        "I'm not ready yet",
        "give me a minute",
        "one sec",
        "one second",
        "hold on a second",
        "wait a minute",
        "later please",
        "pause",
    ],
)
def test_waiting_for_ready_reminder_keeps_waiting_state(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.WAITING_FOR_READY,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, message)
    next_state, cleaned = apply_turn_result(state, plan, "Say ready when you want recall.", [])

    assert plan.action is StudyAction.WAIT_READY_REMINDER
    assert "SOURCE_FOLLOWUP" not in plan.prompt
    assert "signal when they are ready for recall" in plan.prompt
    assert "Do not require a specific English word such as `ready`" in plan.prompt
    assert "type the literal command `ready`" not in plan.prompt
    assert "Tell the student to say ready" not in plan.prompt
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
        current_item="Definiere eine Folge.",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "tell me the full answer")
    next_state, cleaned = apply_turn_result(state, plan, "No. Attempt recall first.", [])

    assert plan.action is StudyAction.REFUSE_REVEAL
    assert plan.phase is StudyPhase.RECALL
    assert "same language as the current item" in plan.prompt
    assert "Do not hard-code an English refusal" in plan.prompt
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
    assert plan.study_move is not None
    assert plan.study_move.kind == "ask_clarifying_question"
    assert "RECALL_CLARIFICATION" in plan.prompt


@pytest.mark.parametrize(
    "student_request",
    [
        "ask me again in German",
        "can you ask that in German again?",
        "in German please",
        "again in German please",
        "again in Spanish please",
        "¿Puedes preguntarme otra vez en espanol?",
    ],
)
def test_recall_reprompt_language_request_is_not_assessed(student_request: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Explain integration by parts.",
        retrieval_query="integration by parts",
        attempt_count=2,
    )

    plan = plan_turn(state, student_request)
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "Erklaere die Aufgabe noch einmal aus dem Gedaechtnis.",
        [],
    )

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert "RECALL_CLARIFICATION" in plan.prompt
    assert "translate, or use a language" in plan.prompt
    assert "Do not include answer content, grading, scores" in plan.prompt
    assert "same language as the student's clarification request" in plan.prompt
    assert "Do not hard-code an English recall sentence" in plan.prompt
    assert cleaned == "Erklaere die Aufgabe noch einmal aus dem Gedaechtnis."
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "Explain integration by parts."
    assert next_state.attempt_count == 2


@pytest.mark.parametrize(
    "student_request",
    [
        "what can Heph do?",
        "how do I switch models in Hephaistos?",
        "can you explain /autopilot?",
        "what can you do?",
        "how can you help?",
    ],
)
def test_recall_heph_self_request_is_chat_not_assessment(student_request: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Explain integration by parts.",
        retrieval_query="integration by parts",
        attempt_count=2,
    )

    plan = plan_turn(state, student_request)

    assert plan.action is StudyAction.CHAT
    assert plan.phase is StudyPhase.RECALL
    assert plan.retrieval_query is None
    assert plan.allow_tools is False
    assert "HEPH self-help mode" in plan.prompt
    assert "same language as the user's request" in plan.prompt
    assert "Do not treat the user message as a recall attempt" in plan.prompt
    assert "Do not use armory material" in plan.prompt


def test_recall_translate_answer_request_is_refused_not_reprompted() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Explain integration by parts.",
        retrieval_query="integration by parts",
    )

    plan = plan_turn(state, "translate the answer into Spanish")

    assert plan.action is StudyAction.REFUSE_REVEAL
    assert plan.phase is StudyPhase.RECALL


def test_recall_attempt_with_language_words_is_still_assessed() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Explain the German terminology in the theorem.",
        retrieval_query="German terminology",
    )

    plan = plan_turn(state, "I would write the answer in German as Begriff and Beispiel")

    assert plan.action is StudyAction.ASSESS
    assert plan.phase is StudyPhase.ASSESS


def test_recall_attempt_that_mentions_answer_is_assessed() -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, "the answer is 4 because I squared 2")

    assert plan.action is StudyAction.ASSESS
    assert plan.phase is StudyPhase.ASSESS


@pytest.mark.parametrize(
    "message",
    [
        "Is it 4?",
        "Maybe 4?",
        "I think it is 4?",
        "Could it be entropy?",
        "Bayes theorem?",
        "A?",
        "My answer would be conditional probability?",
    ],
)
def test_recall_tentative_answer_questions_are_assessed(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.ASSESS
    assert plan.phase is StudyPhase.ASSESS
    assert "Execute RECALL_CLARIFICATION" not in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "Which answer?",
        "What answer do you want?",
        "What question am I answering?",
    ],
)
def test_recall_answer_clarification_questions_still_reprompt(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
    )

    plan = plan_turn(state, message)

    assert plan.action is StudyAction.PROMPT_RECALL
    assert plan.phase is StudyPhase.RECALL
    assert "Execute RECALL_CLARIFICATION" in plan.prompt


@pytest.mark.parametrize(
    "message",
    [
        "too hard",
        "I do not understand",
        "I don't understand this",
        "I'm confused",
        "I need help",
        "help me please",
        "I don't understand?",
        "Can you explain this?",
        "Why is that true?",
        "How do I approach this?",
        "What is the first step?",
        "Can you walk me through this?",
        "Break this down please",
    ],
)
def test_recall_phase_help_request_scaffolds_instead_of_assessing(message: str) -> None:
    state = StudyState(
        phase=StudyPhase.RECALL,
        current_item="Q1",
        retrieval_query="Q1",
        expected_source_refs=["source/exam.md#chunk=0"],
    )

    plan = plan_turn(state, message)
    next_state, cleaned = apply_turn_result(
        state,
        plan,
        "What is the first definition used in Q1?",
        ["source/exam.md#chunk=0"],
    )

    assert plan.action is StudyAction.SIMPLIFY
    assert plan.use_expected_source_refs is True
    assert plan.allow_tools is False
    assert "Execute ASSESS" not in plan.prompt
    assert "HEPH self-help mode" not in plan.prompt
    assert cleaned == "What is the first definition used in Q1?"
    assert next_state.phase is StudyPhase.RECALL
    assert next_state.current_item == "What is the first definition used in Q1?"
    assert next_state.attempt_count == 0
    assert next_state.last_feedback_type is StudyFeedbackType.EASIER


def test_autopilot_not_sure_scaffolds_instead_of_grading() -> None:
    state = StudyState(
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
        phase=StudyPhase.RECALL,
        current_item="Define a sequence with domain and nth-term notation.",
        retrieval_query="sequence definition",
        expected_source_refs=["materials/notes.md#chunk=0"],
    )

    plan = plan_turn(state, "not sure")

    assert plan.action is StudyAction.SIMPLIFY
    assert plan.phase is StudyPhase.RECALL
    assert plan.use_expected_source_refs is True
    assert "Do not grade the learner" in plan.prompt
    assert "fill-the-gaps" in plan.prompt
    assert "confidence from 0-100%" in plan.prompt
    assert "student's language" in plan.prompt
    assert "Do not hard-code an English closing instruction" in plan.prompt
    assert "End with exactly: Fill the gap" not in plan.prompt


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
    assert "same language as the question" in plan.prompt
    assert "End with exactly: Answer from memory" not in plan.prompt


def test_calibration_prompt_requires_grounded_questions() -> None:
    state = StudyState()

    plan = plan_turn(state, "quiz me")

    assert plan.action is StudyAction.CALIBRATE
    assert "retrieved source span" in plan.prompt
    assert "past-exam pattern" in plan.prompt
    assert "never invent unsupported questions" in plan.prompt
    assert "student's language" in plan.prompt
    assert "End with exactly: Answer from memory" not in plan.prompt


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
    assert "signal when they are ready for recall" in plan.prompt
    assert "Do not require a specific English word such as `ready`" in plan.prompt
    assert "type the literal command `ready`" not in plan.prompt
    assert "End with exactly: Say ready when you want recall" not in plan.prompt
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
    assert "same language as the current item" in plan.prompt
    assert "Do not hard-code an English hint" in plan.prompt


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


def test_hint_prompt_level_five_still_hides_direct_answer() -> None:
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
    assert "strongest scaffold" in plan.prompt
    assert "do not state the final answer directly" in plan.prompt


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

    assert cleaned == "WRONG: Start again from the first step only."
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
