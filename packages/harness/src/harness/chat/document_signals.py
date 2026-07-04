"""Document trace payloads, review signals, and policy intervention helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.chat.turn_predicates import _overview_turn
from harness.documents.policy import (
    MemoryState,
    PolicyOutcome,
    ReviewItem,
    learner_assessment_from_state,
    validate_pedagogy,
)
from harness.documents.schedule import load_recall_schedule
from harness.documents.state import DocumentAction, RecallFeedbackType

if TYPE_CHECKING:
    from harness.chat.evidence import ResolvedTurnPlan
    from harness.chat.session import ChatSession
    from harness.documents.policy import DocumentMoveKind
    from harness.documents.prompt_plans import DocumentTurnPlan
    from harness.documents.schedule import RecallItemState, RecallScheduleStore
    from harness.documents.state import RecallState

_TRACE_TASK_BY_ACTION = {
    DocumentAction.PRIORITY: "priority",
    DocumentAction.SOURCE_QA: "source-qa",
    DocumentAction.CALIBRATE: "calibration",
    DocumentAction.ASSESS: "active-recall-assessment",
    DocumentAction.HINT: "hint",
}


def _learner_assessment_trace(
    plan: DocumentTurnPlan | None,
    state: RecallState,
) -> dict[str, object]:
    if plan is None:
        return {}
    assessment = learner_assessment_from_state(
        state,
        topic=state.retrieval_query or state.current_item,
        hint_level_used=state.hint_level if state.hint_level > 0 else None,
    )
    confidence = round(assessment.confidence, 3) if assessment.confidence is not None else None
    calibration_gap = (
        round(assessment.calibration_gap, 3) if assessment.calibration_gap is not None else None
    )
    return {
        "topic": assessment.topic,
        "correctness": round(assessment.correctness, 3),
        "reasoning_quality": round(assessment.reasoning_quality, 3),
        "confidence": confidence,
        "calibration_gap": calibration_gap,
        "misconception_tags": list(assessment.misconception_tags),
        "hint_level_used": assessment.hint_level_used,
        "next_action": assessment.next_action,
    }


def _document_move_kind(plan: DocumentTurnPlan) -> DocumentMoveKind:
    return plan.document_move.kind if plan.document_move is not None else "assess"


def _positive_hint_level(state: RecallState) -> int | None:
    return state.hint_level if state.hint_level > 0 else None


def _exam_importance(state: RecallState) -> float:
    return 1.0 if state.expected_source_refs else 0.0


def _pedagogy_validation_trace(plan: DocumentTurnPlan | None, reply: str) -> dict[str, object]:
    if plan is None or plan.document_move is None:
        return {}
    validation = validate_pedagogy(reply, plan.document_move)
    return {
        "valid": validation.valid,
        "issues": list(validation.issues),
        "rewrite_instruction": validation.rewrite_instruction or "",
        "suggested_next_action": validation.suggested_next_action or "",
        "move": plan.document_move.kind,
    }


def _trace_task(plan: DocumentTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material-overview"
    return _TRACE_TASK_BY_ACTION.get(plan.action, plan.action.value)


def _trace_turn_retrieval_query(resolved: ResolvedTurnPlan) -> str:
    if resolved.turn_contract is not None:
        return resolved.turn_contract.retrieval_query
    if resolved.document_plan is None or resolved.document_plan.retrieval_query is None:
        return ""
    return resolved.document_plan.retrieval_query


def _recall_practice_context(session: ChatSession) -> tuple[tuple[ReviewItem, ...], MemoryState]:
    if session.armory_path is None:
        return (), MemoryState()
    store = load_recall_schedule(session.armory_path)
    due_reviews = _due_review_items(store.due_items(limit=5))
    weak_items = _weak_recall_items(store.item_list)
    weak_topics = _recall_item_topics(weak_items)
    misconceptions = _recall_item_topics(_misconception_items(weak_items))
    successful_interventions, failed_interventions = _document_policy_interventions(store)
    return due_reviews, MemoryState(
        weak_topics=weak_topics[:5],
        misconceptions=misconceptions[:5],
        successful_interventions=successful_interventions,
        failed_interventions=failed_interventions,
    )


def _previous_review_metrics(
    previous: RecallItemState | None,
) -> tuple[float, float | None, float]:
    if previous is None:
        return 0.0, None, 0.0
    return previous.mastery, previous.last_confidence, 1.0 if previous.last_correct else 0.0


def _review_confidence_delta(
    state: RecallItemState,
    previous_confidence: float | None,
) -> float:
    if state.last_confidence is None or previous_confidence is None:
        return 0.0
    return state.last_confidence - previous_confidence


def _review_correctness_delta(
    state: RecallItemState,
    previous: RecallItemState | None,
    previous_correctness: float,
) -> float:
    if previous is None and not state.last_correct:
        return -1.0
    current_correctness = 1.0 if state.last_correct else 0.0
    return current_correctness - previous_correctness


def _policy_outcome_from_review(
    original_recall_state: RecallState,
    session_recall_state: RecallState,
    state: RecallItemState,
    previous: RecallItemState | None,
    intervention: DocumentMoveKind,
) -> PolicyOutcome:
    previous_mastery, previous_confidence, previous_correctness = _previous_review_metrics(
        previous
    )
    return PolicyOutcome(
        move_type=intervention,
        topic=original_recall_state.retrieval_query or original_recall_state.current_item,
        correctness_delta=_review_correctness_delta(state, previous, previous_correctness),
        confidence_delta=_review_confidence_delta(state, previous_confidence),
        mastery_delta=state.mastery - previous_mastery,
        time_cost_seconds=state.last_recall_seconds or 0,
        frustration_signal=(
            session_recall_state.last_feedback_type is RecallFeedbackType.WRONG
            and original_recall_state.hint_level >= 3
        ),
    )


def _due_review_items(items: list[RecallItemState]) -> tuple[ReviewItem, ...]:
    return tuple(
        ReviewItem(
            item=item.item,
            concept=item.concept,
            failures=item.failures,
            last_confidence=item.last_confidence,
        )
        for item in items
    )


def _weak_recall_items(items: list[RecallItemState]) -> list[RecallItemState]:
    return sorted(
        (item for item in items if _recall_item_is_weak(item)),
        key=lambda item: (-item.failures, item.mastery, -item.exam_importance),
    )


def _recall_item_is_weak(item: RecallItemState) -> bool:
    repair_actions = {"contrastive_question", "give_hint", "prerequisite_repair"}
    return item.failures > 0 or item.mastery < 0.55 or item.next_best_action in repair_actions


def _misconception_items(items: list[RecallItemState]) -> list[RecallItemState]:
    return [
        item
        for item in items
        if item.next_best_action == "contrastive_question" or item.common_errors
    ]


def _recall_item_topics(items: list[RecallItemState]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.concept or item.retrieval_query or item.item for item in items)
    )


def _document_policy_interventions(
    store: RecallScheduleStore,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    successful_interventions, failed_interventions = _stored_document_interventions(store)
    _extend_policy_stat_interventions(
        store,
        successful_interventions=successful_interventions,
        failed_interventions=failed_interventions,
    )
    return (
        tuple(dict.fromkeys(successful_interventions)),
        tuple(dict.fromkeys(failed_interventions)),
    )


def _stored_document_interventions(store: RecallScheduleStore) -> tuple[list[str], list[str]]:
    successful_interventions: list[str] = []
    failed_interventions: list[str] = []
    for item in store.item_list:
        successful_interventions.extend(item.successful_interventions or [])
        failed_interventions.extend(item.failed_interventions or [])
    return successful_interventions, failed_interventions


def _extend_policy_stat_interventions(
    store: RecallScheduleStore,
    *,
    successful_interventions: list[str],
    failed_interventions: list[str],
) -> None:
    for move_type, stats in store.policy_stats.items():
        if stats.success_rate >= 0.6 and stats.uses >= 2:
            successful_interventions.append(move_type)
        elif stats.uses >= 2:
            failed_interventions.append(move_type)


def _matching_recall_item(
    items: list[RecallItemState],
    *,
    item: str,
    retrieval_query: str,
) -> RecallItemState | None:
    for candidate in items:
        if candidate.item == item and candidate.retrieval_query == retrieval_query:
            return candidate
    return None
