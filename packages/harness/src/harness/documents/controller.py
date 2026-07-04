"""Deterministic controller for the recall-loop state machine."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from harness.documents.assessment import (
    derive_recall_rating,
    elapsed_recall_seconds,
    parse_assessment_reply,
    strip_assistant_confidence_values,
)
from harness.documents.policy import (
    MemoryState,
    ReviewItem,
    append_policy_prompt,
    move_for_plan,
)
from harness.documents.prompt_plans import (
    DocumentTurnPlan,
    _chat_prompt_plan,
    _material_review_plan,
    _normalize,
    _open_material_plan_for_intent,
    _practice_calibration_plan,
    _practice_stop_prompt,
    _priority_plan,
    _prompt_recall_plan,
    _recall_assessment_plan,
    _recall_hint_plan,
    _recall_review_plan,
    _recall_scaffold_plan,
    _refuse_reveal_plan,
    _source_followup_prompt,
    _turn_plan,
    _waiting_prompt,
    heph_action_plan,
    heph_help_plan,
    material_overview_plan,
    plain_chat_plan,
    recall_clarification_plan,
)
from harness.documents.state import (
    DocumentAction,
    RecallFeedbackType,
    RecallPhase,
    RecallRating,
    RecallState,
)

type TurnResult = tuple[RecallState, str]

_MAX_PRACTICE_TURNS = 24
_OPEN_MATERIAL_INTENTS = frozenset(
    {"material_overview", "source_qa", "topic_presentation", "topic_drill"}
)


def plan_turn(
    state: RecallState,
    user_input: str,
    *,
    intent: str = "",
    due_reviews: tuple[ReviewItem, ...] = (),
    memory_state: MemoryState | None = None,
) -> DocumentTurnPlan:
    effective_memory = memory_state if memory_state is not None else MemoryState()
    bounded_plan = (
        None
        if intent in {"heph_action", "heph_help"}
        else _practice_stop_plan(
            state,
            due_reviews=due_reviews,
            memory_state=effective_memory,
        )
    )
    if bounded_plan is not None:
        return bounded_plan
    plan = _plan_for_intent(state, user_input, intent)
    return _with_document_policy(
        plan,
        state,
        user_input,
        intent=intent,
        due_reviews=due_reviews,
        memory_state=effective_memory,
    )


def _with_document_policy(
    plan: DocumentTurnPlan,
    state: RecallState,
    user_input: str,
    *,
    intent: str,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> DocumentTurnPlan:
    move = move_for_plan(
        plan.action,
        state,
        user_input,
        intent=intent,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    skip_policy_prompt = _material_answer_skips_document_policy(plan)
    prompt = (
        plan.prompt
        if skip_policy_prompt
        else append_policy_prompt(
            plan.prompt,
            move=move,
            action=plan.action,
        )
    )
    return replace(
        plan,
        prompt=prompt,
        allow_tools=plan.allow_tools,
        document_move=None if skip_policy_prompt else move,
    )


def _is_material_overview_plan(plan: DocumentTurnPlan) -> bool:
    return plan.action is DocumentAction.PRESENT and plan.uses_overview_sampling


def _material_answer_skips_document_policy(plan: DocumentTurnPlan) -> bool:
    return _is_material_overview_plan(plan) or plan.action in {
        DocumentAction.PRESENT,
        DocumentAction.SOURCE_QA,
        DocumentAction.PRIORITY,
        DocumentAction.REVIEW,
        DocumentAction.SIMPLIFY,
    }


def _plan_for_intent(
    state: RecallState,
    user_input: str,
    intent: str,
) -> DocumentTurnPlan:
    if state.current_item:
        recall_plan = _plan_recall_loop_intent(state, user_input, intent)
        if recall_plan is not None:
            return recall_plan
    return _plan_open_intent(state, user_input, intent)


def _plan_recall_loop_intent(
    state: RecallState,
    user_input: str,
    intent: str,
) -> DocumentTurnPlan | None:
    item = state.current_item
    phase = state.phase
    source_query = state.retrieval_query or item
    if phase is RecallPhase.WAITING_FOR_READY:
        return _plan_waiting_intent(state, user_input, intent, source_query)
    if phase is RecallPhase.RECALL:
        return _plan_recall_phase_intent(state, user_input, intent, source_query)
    return None


def _plan_waiting_intent(
    state: RecallState,
    user_input: str,
    intent: str,
    source_query: str,
) -> DocumentTurnPlan:
    item = state.current_item
    if intent == "ready_for_recall":
        return _prompt_recall_plan(item)
    if intent == "reveal_request":
        return _refuse_reveal_plan(item, phase=RecallPhase.WAITING_FOR_READY)
    if intent == "skip_request":
        return material_overview_plan(user_input or f"different material-backed item from {item}")
    if intent == "wait":
        return _turn_plan(
            DocumentAction.WAIT_READY_REMINDER,
            _waiting_prompt(),
            phase=RecallPhase.WAITING_FOR_READY,
        )
    if common_plan := _active_recall_common_intent_plan(state, user_input, intent):
        return common_plan
    return _material_review_plan(
        prompt=_source_followup_prompt(item, user_input),
        retrieval_query=source_query,
    )


def _plan_recall_phase_intent(
    state: RecallState,
    user_input: str,
    intent: str,
    source_query: str,
) -> DocumentTurnPlan:
    item = state.current_item
    if intent == "reveal_request":
        return _refuse_reveal_plan(item, phase=RecallPhase.RECALL)
    if intent == "skip_request":
        return material_overview_plan(user_input or f"different material-backed item from {item}")
    if intent == "hint_request" and state.attempt_count > 0:
        return _recall_hint_plan(state, source_query)
    if intent == "scaffold_request":
        return _recall_scaffold_plan(state, source_query)
    if intent == "material_review":
        return _recall_review_plan(state, source_query)
    if intent == "recall_clarification":
        return recall_clarification_plan(user_input, current_item=item)
    if common_plan := _active_recall_common_intent_plan(state, user_input, intent):
        return common_plan
    return _recall_assessment_plan(state, user_input, source_query)


def _active_recall_common_intent_plan(
    state: RecallState,
    user_input: str,
    intent: str,
) -> DocumentTurnPlan | None:
    if intent in _OPEN_MATERIAL_INTENTS:
        return _open_material_plan_for_intent(user_input, intent)
    if intent == "priority_request":
        return _priority_plan(user_input, phase=state.phase)
    if intent == "heph_action":
        return heph_action_plan(user_input, phase=state.phase)
    if intent == "heph_help":
        return heph_help_plan(user_input, phase=state.phase)
    if intent == "chat":
        return plain_chat_plan(user_input, phase=state.phase)
    return None


def _plan_open_intent(
    state: RecallState,
    user_input: str,
    intent: str,
) -> DocumentTurnPlan:
    if intent == "heph_action":
        return heph_action_plan(user_input, phase=state.phase)
    if intent == "heph_help":
        return heph_help_plan(user_input, phase=state.phase)
    if intent == "chat":
        return plain_chat_plan(user_input, phase=state.phase)
    if intent == "priority_request":
        return _priority_plan(user_input, phase=state.phase)
    if intent == "driven_recall_calibration":
        return _practice_calibration_plan(state, user_input)
    if intent in {"source_qa", "topic_presentation", "topic_drill", "material_overview"}:
        return _open_material_plan_for_intent(user_input, intent)
    if _practice_session_active(state) and state.phase is RecallPhase.PRESENTING:
        return _practice_calibration_plan(state, user_input)
    query = _normalize(user_input) or None
    return material_overview_plan(
        user_input,
        retrieval_query=query,
    )


def _practice_session_active(state: RecallState) -> bool:
    return bool(state.practice_started_at or state.practice_session_type or state.practice_turns)


def _practice_stop_plan(
    state: RecallState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> DocumentTurnPlan | None:
    if not _practice_session_active(state):
        return None
    reason = _practice_stop_reason(
        state,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    if not reason:
        return None
    return _chat_prompt_plan(_practice_stop_prompt(reason), phase=state.phase)


def _practice_stop_reason(
    state: RecallState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
    now: datetime | None = None,
) -> str:
    if state.practice_turns >= _MAX_PRACTICE_TURNS:
        return "maximum turn budget reached"
    if state.practice_stop_reason:
        return state.practice_stop_reason
    return (
        _practice_time_stop_reason(state, now=now)
        or _practice_completion_stop_reason(
            state,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        or _practice_fatigue_stop_reason(state)
    )


def _practice_time_stop_reason(state: RecallState, *, now: datetime | None = None) -> str:
    return "time budget reached" if _practice_time_budget_reached(state, now=now) else ""


def _practice_completion_stop_reason(
    state: RecallState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> str:
    return _practice_session_completion_reason(
        state,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )


def _practice_fatigue_stop_reason(state: RecallState) -> str:
    return "learner fatigue or frustration detected" if _practice_fatigue_detected(state) else ""


def _practice_time_budget_reached(state: RecallState, *, now: datetime | None = None) -> bool:
    if state.time_budget_minutes is None or state.practice_started_at is None:
        return False
    current_time = now or datetime.now(UTC)
    started = state.practice_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return current_time - started >= timedelta(minutes=state.time_budget_minutes)


def _practice_session_completion_reason(
    state: RecallState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> str:
    session_type = state.practice_session_type.casefold()
    learner_state_active = bool(due_reviews or memory_state.weak_topics)
    if _review_session_complete(session_type, state, due_reviews):
        return "due cards completed"
    if _exam_session_complete(session_type, state, learner_state_active):
        return "exam plan completed"
    if _mastery_target_reached(state, memory_state, learner_state_active):
        return "mastery target reached"
    return ""


def _review_session_complete(
    session_type: str,
    state: RecallState,
    due_reviews: tuple[ReviewItem, ...],
) -> bool:
    return session_type == "review" and state.practice_turns > 0 and not due_reviews


def _exam_session_complete(
    session_type: str,
    state: RecallState,
    learner_state_active: bool,
) -> bool:
    return (
        session_type in {"exam", "cram"} and state.practice_turns >= 6 and not learner_state_active
    )


def _mastery_target_reached(
    state: RecallState,
    memory_state: MemoryState,
    learner_state_active: bool,
) -> bool:
    return (
        state.practice_turns >= 4 and not learner_state_active and not memory_state.misconceptions
    )


def _practice_fatigue_detected(state: RecallState) -> bool:
    return (
        state.last_feedback_type in {RecallFeedbackType.WRONG, RecallFeedbackType.PARTIAL}
        and state.hint_level >= 4
    )


def _clear_recall_target(
    state: RecallState,
    *,
    feedback: RecallFeedbackType,
    phase: RecallPhase = RecallPhase.PRESENTING,
    reset_hint: bool = True,
) -> None:
    state.phase = phase
    state.current_item = ""
    state.retrieval_query = ""
    state.expected_source_refs = []
    state.attempt_count = 0
    state.last_feedback_type = feedback
    state.recall_started_at = None
    if reset_hint:
        state.hint_level = 0


def _enter_sourced_step(
    state: RecallState,
    *,
    phase: RecallPhase,
    current_item: str,
    retrieval_query: str,
    source_refs: list[str],
    feedback: RecallFeedbackType,
    recall_started_at: datetime | None,
    hint_level: int | None = None,
) -> None:
    state.phase = phase
    state.current_item = current_item
    state.retrieval_query = retrieval_query
    state.expected_source_refs = list(source_refs)
    state.attempt_count = 0
    state.last_feedback_type = feedback
    state.recall_started_at = recall_started_at
    if recall_started_at is not None:
        state.last_recall_seconds = None
        state.last_recall_rating = RecallRating.NONE
    if hint_level is not None:
        state.hint_level = hint_level


def apply_turn_result(
    state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    *,
    now: datetime | None = None,
) -> tuple[RecallState, str]:
    current_time = now or datetime.now(UTC)
    next_state = state.clone()
    _increment_practice_turn_count(state, next_state, plan)

    if plan.action is DocumentAction.ASSESS:
        return _apply_assess_result(next_state, state, plan, reply, source_refs, current_time)
    if result := _apply_non_assess_result(
        state,
        next_state,
        plan,
        reply,
        source_refs,
        current_time,
    ):
        return result
    return next_state, reply


def _increment_practice_turn_count(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
) -> None:
    if state.practice_started_at is not None and plan.action is not DocumentAction.CHAT:
        next_state.practice_turns = state.practice_turns + 1


def _apply_non_assess_result(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult | None:
    return (
        _apply_simple_turn_result(next_state, plan, reply, source_refs, current_time)
        or _apply_recall_control_result(state, next_state, plan, reply, source_refs, current_time)
        or _apply_sourced_action_result(state, next_state, plan, reply, source_refs, current_time)
    )


def _apply_simple_turn_result(
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult | None:
    if plan.action is DocumentAction.CHAT:
        return _apply_chat_result(next_state, reply)
    if plan.action is DocumentAction.PRIORITY:
        return _apply_priority_result(next_state, reply)
    if plan.action is DocumentAction.SOURCE_QA:
        return _apply_source_qa_result(next_state, reply)
    if plan.action is DocumentAction.CALIBRATE:
        return _apply_calibrate_result(next_state, plan, reply, source_refs, current_time)
    return None


def _apply_chat_result(
    next_state: RecallState,
    reply: str,
) -> TurnResult:
    next_state.last_feedback_type = RecallFeedbackType.NONE
    return next_state, reply


def _apply_priority_result(next_state: RecallState, reply: str) -> TurnResult:
    next_state.phase = RecallPhase.PRESENTING
    next_state.last_feedback_type = RecallFeedbackType.NONE
    return next_state, reply


def _apply_source_qa_result(next_state: RecallState, reply: str) -> TurnResult:
    _clear_recall_target(next_state, feedback=RecallFeedbackType.NONE, reset_hint=False)
    return next_state, reply


_SOURCED_STEP_ACTIONS = frozenset(
    {
        DocumentAction.PRESENT,
        DocumentAction.SIMPLIFY,
        DocumentAction.REVIEW,
    }
)


def _apply_sourced_action_result(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult | None:
    if plan.action not in _SOURCED_STEP_ACTIONS:
        return None
    return _apply_sourced_step_result(
        state,
        next_state,
        plan,
        reply,
        source_refs,
        current_time,
    )


def _apply_sourced_step_result(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult:
    next_retrieval_query = plan.retrieval_query or state.retrieval_query
    if plan.action is DocumentAction.PRESENT:
        return _apply_present_result(
            state,
            next_state,
            plan,
            reply,
            source_refs,
            next_retrieval_query,
        )
    if plan.action is DocumentAction.SIMPLIFY:
        return _apply_simplify_result(
            state,
            next_state,
            reply,
            source_refs,
            next_retrieval_query,
            current_time,
        )
    return _apply_review_result(
        state,
        next_state,
        reply,
        source_refs,
        next_retrieval_query,
    )


def _apply_recall_control_result(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[RecallState, str] | None:
    if plan.action is DocumentAction.PROMPT_RECALL:
        return _apply_prompt_recall_result(next_state, reply, current_time)
    if plan.action is DocumentAction.WAIT_READY_REMINDER:
        return _apply_wait_ready_reminder_result(next_state, reply)
    if plan.action is DocumentAction.REFUSE_REVEAL:
        return _apply_refuse_reveal_result(state, next_state, reply)
    if plan.action is DocumentAction.HINT:
        return _apply_hint_result(state, next_state, reply, source_refs)
    return None


def _apply_prompt_recall_result(
    next_state: RecallState,
    reply: str,
    current_time: datetime,
) -> TurnResult:
    next_state.phase = RecallPhase.RECALL
    next_state.last_feedback_type = RecallFeedbackType.READY
    next_state.recall_started_at = current_time
    next_state.last_recall_seconds = None
    next_state.last_recall_rating = RecallRating.NONE
    next_state.hint_level = 0
    return next_state, reply


def _apply_wait_ready_reminder_result(next_state: RecallState, reply: str) -> TurnResult:
    next_state.phase = RecallPhase.WAITING_FOR_READY
    next_state.last_feedback_type = RecallFeedbackType.WAITING
    return next_state, reply


def _apply_refuse_reveal_result(
    state: RecallState,
    next_state: RecallState,
    reply: str,
) -> TurnResult:
    next_state.phase = state.phase
    next_state.last_feedback_type = RecallFeedbackType.REFUSED
    return next_state, strip_assistant_confidence_values(reply)


def _apply_hint_result(
    state: RecallState,
    next_state: RecallState,
    reply: str,
    source_refs: list[str],
) -> TurnResult:
    next_state.phase = RecallPhase.RECALL
    next_state.last_feedback_type = RecallFeedbackType.HINT
    next_state.hint_level = min(5, state.hint_level + 1)
    if source_refs:
        next_state.expected_source_refs = list(source_refs)
    return next_state, reply


def _apply_calibrate_result(
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[RecallState, str]:
    if source_refs:
        _enter_recall_from_reply(
            next_state,
            reply=reply,
            retrieval_query=plan.retrieval_query,
            source_refs=source_refs,
            feedback=RecallFeedbackType.CALIBRATING,
            current_time=current_time,
            hint_level=0,
        )
    else:
        _mark_insufficient_evidence(next_state)
    return next_state, reply


def _apply_present_result(
    state: RecallState,
    next_state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[RecallState, str]:
    if _is_material_overview_plan(plan):
        _clear_recall_target(
            next_state,
            feedback=RecallFeedbackType.NONE if source_refs else RecallFeedbackType.NO_SOURCE,
        )
        if not source_refs:
            _set_insufficient_evidence_stop_reason(next_state)
        return next_state, reply
    if source_refs:
        _enter_presented_step(next_state, state, plan, source_refs, next_retrieval_query)
    else:
        _mark_insufficient_evidence(next_state)
    return next_state, reply


def _enter_presented_step(
    next_state: RecallState,
    state: RecallState,
    plan: DocumentTurnPlan,
    source_refs: list[str],
    next_retrieval_query: str,
) -> None:
    _enter_sourced_step(
        next_state,
        phase=RecallPhase.WAITING_FOR_READY,
        current_item=plan.retrieval_query or state.current_item,
        retrieval_query=next_retrieval_query,
        source_refs=source_refs,
        feedback=RecallFeedbackType.PRESENTED,
        recall_started_at=None,
        hint_level=0,
    )


def _apply_simplify_result(
    state: RecallState,
    next_state: RecallState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
    current_time: datetime,
) -> tuple[RecallState, str]:
    if source_refs:
        _enter_recall_from_reply(
            next_state,
            reply=reply,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=RecallFeedbackType.EASIER,
            current_time=current_time,
            hint_level=min(5, state.hint_level + 1),
        )
    else:
        _mark_insufficient_evidence(next_state, phase=RecallPhase.RECALL)
    return next_state, reply


def _enter_recall_from_reply(
    state: RecallState,
    *,
    reply: str,
    retrieval_query: str | None,
    source_refs: list[str],
    feedback: RecallFeedbackType,
    current_time: datetime,
    hint_level: int,
) -> None:
    current_item = _normalize(reply)
    _enter_sourced_step(
        state,
        phase=RecallPhase.RECALL,
        current_item=current_item,
        retrieval_query=retrieval_query or current_item,
        source_refs=source_refs,
        feedback=feedback,
        recall_started_at=current_time,
        hint_level=hint_level,
    )


def _apply_review_result(
    state: RecallState,
    next_state: RecallState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[RecallState, str]:
    if source_refs:
        _enter_sourced_step(
            next_state,
            phase=RecallPhase.WAITING_FOR_READY,
            current_item=state.current_item,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=RecallFeedbackType.REVIEWING,
            recall_started_at=None,
        )
    else:
        _mark_insufficient_evidence(next_state, phase=RecallPhase.RECALL)
    return next_state, reply


def _mark_insufficient_evidence(
    state: RecallState,
    *,
    phase: RecallPhase | None = None,
) -> None:
    if phase is None:
        _clear_recall_target(state, feedback=RecallFeedbackType.NO_SOURCE)
    else:
        state.phase = phase
        state.last_feedback_type = RecallFeedbackType.NO_SOURCE
    _set_insufficient_evidence_stop_reason(state)


def _set_insufficient_evidence_stop_reason(state: RecallState) -> None:
    _set_practice_stop_reason(state, "evidence is insufficient")


def _apply_assess_result(
    next_state: RecallState,
    state: RecallState,
    plan: DocumentTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[RecallState, str]:
    feedback, cleaned_reply = parse_assessment_reply(reply)
    elapsed_seconds = elapsed_recall_seconds(state.recall_started_at, current_time)
    next_state.attempt_count = state.attempt_count + 1
    if source_refs:
        next_state.expected_source_refs = list(source_refs)
    next_state.last_feedback_type = feedback
    next_state.last_recall_seconds = elapsed_seconds
    next_state.last_recall_rating = derive_recall_rating(feedback, elapsed_seconds)
    next_state.last_confidence = plan.stated_confidence
    if feedback is RecallFeedbackType.CORRECT:
        _clear_recall_target(next_state, feedback=feedback)
        next_state.attempt_count = state.attempt_count + 1
    else:
        next_state.phase = RecallPhase.RECALL
        next_state.recall_started_at = current_time
        if _practice_assessment_fatigue(state, feedback):
            _set_practice_stop_reason(next_state, "learner fatigue or frustration detected")
    if not source_refs:
        _set_practice_stop_reason(next_state, "evidence is insufficient")
    return next_state, cleaned_reply


def _practice_assessment_fatigue(
    state: RecallState,
    feedback: RecallFeedbackType,
) -> bool:
    return (
        feedback is RecallFeedbackType.WRONG
        and state.hint_level >= 4
        and state.practice_started_at is not None
    )


def _set_practice_stop_reason(state: RecallState, reason: str) -> None:
    if state.practice_started_at is None:
        return
    if state.practice_stop_reason:
        return
    state.practice_stop_reason = reason
