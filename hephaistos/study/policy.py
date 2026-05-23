"""Learning policy primitives.

The policy in this module is intentionally deterministic. It gives the chat
orchestrator a small, inspectable learning move instead of relying on a single
large prompt to decide how a learning session should proceed.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from hephaistos.study.state import (
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    RecallRating,
)

type LearningMoveKind = Literal[
    "answer",
    "ask_recall",
    "give_hint",
    "assess",
    "review_due",
    "diagnose_priority",
    "retrieve_more",
    "ask_clarifying_question",
    "abstain",
    "summarize",
    "worked_example",
    "contrastive_question",
    "schedule_review",
]
type LearningMoveDifficulty = Literal["easy", "medium", "hard"]
type SessionTypeMoveSpec = tuple[LearningMoveKind, str, LearningMoveDifficulty | None, str]
type ActionMoveSpec = tuple[LearningMoveKind, str, str]
type EvidenceAction = Literal[
    "answer",
    "retrieve_more",
    "ask_clarifying_question",
    "abstain",
    "give_partial_answer",
]
type LearningStrategy = Callable[[LearningPolicyInput, PracticeSessionType], LearningMove | None]


class PracticeSessionType(StrEnum):
    GENERAL = "general"
    EXAM = "exam"
    WEAK_TOPICS = "weak-topics"
    REVIEW = "review"
    SOCRATIC = "socratic"
    CRAM = "cram"
    DEEP = "deep"


@dataclass(frozen=True, slots=True)
class ReviewItem:
    item: str
    concept: str = ""
    failures: int = 0
    last_confidence: float | None = None


@dataclass(frozen=True, slots=True)
class TurnSummary:
    role: str
    text: str
    feedback: LearningFeedbackType = LearningFeedbackType.NONE
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class MemoryState:
    weak_topics: tuple[str, ...] = ()
    misconceptions: tuple[str, ...] = ()
    successful_interventions: tuple[str, ...] = ()
    failed_interventions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MaterialStatus:
    has_materials: bool = False
    has_indexed_evidence: bool = False
    evidence_refs: tuple[str, ...] = ()
    sampled_source_count: int = 0
    total_source_count: int = 0


@dataclass(frozen=True, slots=True)
class LearningPolicyInput:
    user_message: str
    session_goal: str | None
    time_budget_minutes: int | None
    learning_state: LearningState
    memory_state: MemoryState
    due_reviews: tuple[ReviewItem, ...]
    recent_turns: tuple[TurnSummary, ...]
    material_status: MaterialStatus
    intent: str = ""


@dataclass(frozen=True, slots=True)
class LearningMove:
    kind: LearningMoveKind
    reason: str
    requires_evidence: bool
    requires_user_commitment: bool
    difficulty: LearningMoveDifficulty | None
    target_topic: str | None
    expected_output_shape: str | None


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    sufficient: bool
    confidence: float
    supporting_refs: tuple[str, ...]
    missing_information: tuple[str, ...]
    conflicts: tuple[str, ...]
    source_diversity_score: float
    recommended_action: EvidenceAction


@dataclass(frozen=True, slots=True)
class LearnerAssessment:
    topic: str
    correctness: float
    reasoning_quality: float
    confidence: float | None
    calibration_gap: float | None
    misconception_tags: tuple[str, ...]
    hint_level_used: int | None
    next_action: LearningMoveKind


@dataclass(frozen=True, slots=True)
class PedagogyValidation:
    valid: bool
    issues: tuple[str, ...]
    rewrite_instruction: str | None
    suggested_next_action: str | None


@dataclass(frozen=True, slots=True)
class PolicyOutcome:
    move_type: LearningMoveKind
    topic: str
    correctness_delta: float
    confidence_delta: float
    mastery_delta: float
    time_cost_seconds: int
    frustration_signal: bool = False

    @property
    def score(self) -> float:
        time_penalty = min(0.4, self.time_cost_seconds / 1800)
        frustration_penalty = 0.25 if self.frustration_signal else 0.0
        return (
            self.correctness_delta
            + self.confidence_delta
            + self.mastery_delta
            - time_penalty
            - frustration_penalty
        )


_DRIVEN_LEARNING_INTENTS = frozenset(
    {"driven_learning_calibration", "topic_drill", "priority_request"}
)
_STUDY_INTENTS = frozenset({"driven_learning_calibration", "topic_drill"})
_SESSION_TYPE_CUES = (
    ("exam", PracticeSessionType.EXAM),
    ("weak", PracticeSessionType.WEAK_TOPICS),
    ("review", PracticeSessionType.REVIEW),
    ("socratic", PracticeSessionType.SOCRATIC),
    ("cram", PracticeSessionType.CRAM),
    ("deep", PracticeSessionType.DEEP),
)
_NEXT_ACTION_BY_FEEDBACK: dict[LearningFeedbackType, LearningMoveKind] = {
    LearningFeedbackType.CORRECT: "schedule_review",
    LearningFeedbackType.PARTIAL: "give_hint",
    LearningFeedbackType.WRONG: "ask_recall",
}
_CORRECTNESS_BY_FEEDBACK = {
    LearningFeedbackType.CORRECT: 1.0,
    LearningFeedbackType.PARTIAL: 0.55,
    LearningFeedbackType.WRONG: 0.0,
}
_REASONING_QUALITY_BY_RATING = {
    RecallRating.EASY: 0.9,
    RecallRating.GOOD: 0.75,
    RecallRating.HARD: 0.35,
    RecallRating.NONE: 0.0,
}
_CONFIDENCE_UNIT_DIVISORS = {"%": 100.0, "/10": 10.0, "/5": 5.0}
_CONFIDENCE_VALUE_DIVISORS: tuple[tuple[float, float], ...] = (
    (1.0, 1.0),
    (5.0, 5.0),
    (10.0, 10.0),
)


class LearningPolicy:
    def next_turn(self, input_data: LearningPolicyInput) -> LearningMove:
        if input_data.intent in _DRIVEN_LEARNING_INTENTS:
            return _driven_learning_move(input_data)
        return _material_learning_move(input_data)


def is_driven_learning_intent(intent: str) -> bool:
    return intent in _DRIVEN_LEARNING_INTENTS


def assess_evidence(
    refs: tuple[str, ...],
    *,
    source_only: bool = False,
    missing_hint: str = "more targeted indexed source evidence",
) -> EvidenceAssessment:
    if not refs:
        return _missing_evidence_assessment(source_only=source_only, missing_hint=missing_hint)
    if len(refs) == 1:
        return _single_ref_evidence_assessment(refs, source_only=source_only)
    return _multi_ref_evidence_assessment(refs)


def _missing_evidence_assessment(*, source_only: bool, missing_hint: str) -> EvidenceAssessment:
    return _evidence_assessment(
        sufficient=False,
        confidence=0.0,
        missing_information=(missing_hint,),
        recommended_action="abstain" if source_only else "retrieve_more",
    )


def _single_ref_evidence_assessment(
    refs: tuple[str, ...],
    *,
    source_only: bool,
) -> EvidenceAssessment:
    return _evidence_assessment(
        sufficient=not source_only,
        confidence=0.48 if source_only else 0.58,
        supporting_refs=refs,
        missing_information=("corroborating source span",),
        source_diversity_score=_source_diversity_score(refs),
        recommended_action="give_partial_answer" if source_only else "answer",
    )


def _multi_ref_evidence_assessment(refs: tuple[str, ...]) -> EvidenceAssessment:
    diversity = _source_diversity_score(refs)
    return _evidence_assessment(
        sufficient=True,
        confidence=min(0.95, 0.62 + 0.1 * len(refs) + 0.1 * diversity),
        supporting_refs=refs,
        source_diversity_score=diversity,
        recommended_action="answer",
    )


def _source_diversity_score(refs: tuple[str, ...]) -> float:
    sources = {ref.split("#chunk=", maxsplit=1)[0] for ref in refs}
    return min(1.0, len(sources) / 3) if refs else 0.0


def _evidence_assessment(
    *,
    sufficient: bool,
    confidence: float,
    recommended_action: EvidenceAction,
    supporting_refs: tuple[str, ...] = (),
    missing_information: tuple[str, ...] = (),
    source_diversity_score: float = 0.0,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        sufficient=sufficient,
        confidence=confidence,
        supporting_refs=supporting_refs,
        missing_information=missing_information,
        conflicts=(),
        source_diversity_score=source_diversity_score,
        recommended_action=recommended_action,
    )


def learner_assessment_from_state(
    state: LearningState,
    *,
    topic: str = "",
    hint_level_used: int | None = None,
) -> LearnerAssessment:
    correctness = _CORRECTNESS_BY_FEEDBACK.get(state.last_feedback_type, 0.0)
    reasoning_quality = _REASONING_QUALITY_BY_RATING[state.last_recall_rating]
    confidence = state.last_confidence
    calibration_gap = abs(confidence - correctness) if confidence is not None else None
    misconception_tags = ("high_confidence_gap",) if _high_confidence_gap(state) else ()
    return LearnerAssessment(
        topic=_learner_topic(state, topic),
        correctness=correctness,
        reasoning_quality=reasoning_quality,
        confidence=confidence,
        calibration_gap=calibration_gap,
        misconception_tags=misconception_tags,
        hint_level_used=hint_level_used,
        next_action=_learner_next_action(state),
    )


def _learner_topic(state: LearningState, requested_topic: str) -> str:
    return requested_topic or state.retrieval_query or state.current_item


def _learner_next_action(state: LearningState) -> LearningMoveKind:
    if _high_confidence_gap(state):
        return "contrastive_question"
    return _NEXT_ACTION_BY_FEEDBACK.get(state.last_feedback_type, "answer")


def validate_pedagogy(reply: str, move: LearningMove) -> PedagogyValidation:
    issues: list[str] = []
    normalized = reply.casefold()
    if move.requires_user_commitment and "confidence" not in normalized:
        issues.append("missing confidence request")
    if _looks_like_recall_answer_leak(normalized, move):
        issues.append("possible answer leakage during recall")
    if not issues:
        return PedagogyValidation(True, (), None, None)
    return PedagogyValidation(
        valid=False,
        issues=tuple(issues),
        rewrite_instruction=_pedagogy_rewrite_instruction(move),
        suggested_next_action=move.expected_output_shape,
    )


def _pedagogy_rewrite_instruction(move: LearningMove) -> str:
    if move.requires_user_commitment:
        return "Rewrite to require an attempt and confidence before revealing more."
    return "Rewrite to match the selected learning move without adding unsolicited guidance."


def _looks_like_recall_answer_leak(normalized_reply: str, move: LearningMove) -> bool:
    if move.kind not in {"ask_recall", "contrastive_question"}:
        return False
    return any(
        marker in normalized_reply for marker in ("the answer is", "solution:", "full solution")
    )


def move_for_plan(
    plan_action: LearningAction,
    state: LearningState,
    user_message: str,
    *,
    intent: str = "",
    evidence_refs: tuple[str, ...] = (),
    due_reviews: tuple[ReviewItem, ...] = (),
    memory_state: MemoryState | None = None,
) -> LearningMove:
    input_data = LearningPolicyInput(
        user_message=user_message,
        session_goal=state.session_goal or None,
        time_budget_minutes=state.time_budget_minutes,
        learning_state=state,
        memory_state=memory_state if memory_state is not None else MemoryState(),
        due_reviews=due_reviews,
        recent_turns=(),
        material_status=_material_status_from_refs(evidence_refs),
        intent=intent,
    )
    move = _move_from_action(plan_action, input_data)
    if move is not None:
        return move
    return LearningPolicy().next_turn(input_data)


def _material_status_from_refs(evidence_refs: tuple[str, ...]) -> MaterialStatus:
    source_count = len({ref.split("#chunk=", maxsplit=1)[0] for ref in evidence_refs})
    return MaterialStatus(
        has_materials=bool(evidence_refs),
        has_indexed_evidence=bool(evidence_refs),
        evidence_refs=evidence_refs,
        sampled_source_count=source_count,
        total_source_count=source_count,
    )


def append_policy_prompt(
    prompt: str,
    *,
    move: LearningMove,
    action: LearningAction,
) -> str:
    if not prompt or action is LearningAction.CHAT:
        return prompt

    lines = [
        "",
        "Learning policy:",
        f"- Move: {move.kind}; reason: {move.reason}",
    ]
    lines.extend(_move_policy_lines(move))
    lines.extend(_action_policy_lines(action, move=move))
    return f"{prompt}\n" + "\n".join(lines)


def _move_policy_lines(move: LearningMove) -> tuple[str, ...]:
    lines: list[str] = []
    if move.requires_user_commitment:
        lines.append("- Require the learner to commit and include confidence from 0-100%.")
    if move.expected_output_shape:
        lines.extend(
            (
                f"- Target response shape: {move.expected_output_shape}",
                "- Adapt the shape to the learner's language; do not copy English phrasing "
                "blindly.",
            )
        )
    return tuple(lines)


def _action_policy_lines(
    action: LearningAction,
    *,
    move: LearningMove,
) -> tuple[str, ...]:
    if action is LearningAction.SOURCE_QA:
        return ("- Source-only answer: do not add tutoring steps after the answer.",)
    if action is LearningAction.CALIBRATE:
        return _calibration_policy_lines()
    if action is LearningAction.ASSESS and _needs_contrastive_correction(move):
        return ("- Prefer a contrastive correction before another explanation.",)
    return ()


def _calibration_policy_lines() -> tuple[str, ...]:
    return (
        "- The whole response is the recall task; do not reveal the answer.",
        "- Start directly with the recall task; do not include internal labels.",
        "- Ask for the smallest necessary user input and begin immediately.",
    )


def _needs_contrastive_correction(move: LearningMove) -> bool:
    return move.kind == "contrastive_question" or "confidence" in move.reason


def normalize_confidence_value(raw_value: float, unit: str = "") -> float | None:
    divisor = _confidence_divisor(raw_value, unit)
    if divisor is None:
        return None
    confidence = raw_value / divisor
    return min(1.0, max(0.0, confidence))


def _confidence_divisor(raw_value: float, unit: str) -> float | None:
    if unit in _CONFIDENCE_UNIT_DIVISORS:
        return _CONFIDENCE_UNIT_DIVISORS[unit]
    for maximum, divisor in _CONFIDENCE_VALUE_DIVISORS:
        if raw_value <= maximum:
            return divisor
    return None


def parse_time_budget_minutes(text: str) -> int | None:
    match = re.search(r"\b(?P<value>\d{1,3})\s*(?P<unit>m|min|mins|minutes|h|hr|hour)s?\b", text)
    if match is None:
        return None
    value = int(match.group("value"))
    unit = match.group("unit")
    minutes = value * 60 if unit.startswith("h") else value
    return min(24 * 60, max(1, minutes))


def session_type_from_text(text: str) -> PracticeSessionType:
    normalized = text.casefold()
    for cue, session_type in _SESSION_TYPE_CUES:
        if cue in normalized:
            return session_type
    return PracticeSessionType.GENERAL


def _direct_answer_move(input_data: LearningPolicyInput) -> LearningMove:
    if input_data.learning_state.phase is LearningPhase.RECALL:
        return _move("assess", "direct-answer policy keeps the current recall loop in control")
    return _move("answer", "direct-answer policy should answer the user's direct request")


def _hint_preferred_over_contrast(memory_state: MemoryState) -> bool:
    return (
        "contrastive_question" in memory_state.failed_interventions
        and "give_hint" in memory_state.successful_interventions
    )


def _intervention_reason(
    memory_state: MemoryState,
    move_kind: LearningMoveKind,
    fallback: str,
) -> str:
    if move_kind in memory_state.successful_interventions:
        return f"{fallback}, and local policy outcomes favor {move_kind}"
    return fallback


def _due_review_move(input_data: LearningPolicyInput) -> LearningMove | None:
    if not input_data.due_reviews:
        return None
    topic = input_data.due_reviews[0].concept or input_data.due_reviews[0].item
    return _move(
        "review_due",
        "a scheduled material-backed review is due",
        target_topic=topic,
        requires_user_commitment=True,
        expected_output_shape="Ask one due active-recall question before explaining.",
    )


def _active_recall_move(state: LearningState) -> LearningMove | None:
    if state.phase is not LearningPhase.RECALL:
        return None
    if _high_confidence_gap(state):
        return _move(
            "contrastive_question",
            "high confidence with weak performance needs contrastive repair",
            target_topic=state.retrieval_query or state.current_item,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape=(
                "Give a minimal correction, then ask a contrastive recall question."
            ),
        )
    return _move(
        "assess",
        "the learner has an active recall item",
        target_topic=state.retrieval_query or state.current_item,
        requires_user_commitment=False,
        expected_output_shape="Assess, correct the smallest useful point, then ask one retry.",
    )


def _stored_memory_move(input_data: LearningPolicyInput) -> LearningMove | None:
    memory_state = input_data.memory_state
    if memory_state.misconceptions:
        if _hint_preferred_over_contrast(memory_state):
            return _learning_move(
                "give_hint",
                "local policy outcomes suggest a scaffolded hint works better than contrast",
                target_topic=memory_state.misconceptions[0],
                difficulty="easy",
                expected_output_shape="Give one hint level, then ask the learner to continue.",
            )
        return _learning_move(
            "contrastive_question",
            _intervention_reason(
                memory_state,
                "contrastive_question",
                "stored learner state shows a recurring misconception",
            ),
            target_topic=memory_state.misconceptions[0],
            difficulty="medium",
            expected_output_shape="Ask a contrastive question before giving another summary.",
        )
    if memory_state.weak_topics and input_data.intent in _STUDY_INTENTS:
        return _learning_move(
            "ask_recall",
            "stored learner state points to a weak topic",
            target_topic=memory_state.weak_topics[0],
            difficulty="medium",
            expected_output_shape="Ask one recall task on the weakest topic with confidence.",
        )
    return None


def _material_learning_move(input_data: LearningPolicyInput) -> LearningMove:
    for maybe_move in (
        _due_review_move(input_data),
        _active_recall_move(input_data.learning_state),
        _stored_memory_move(input_data),
        _missing_index_move(input_data.material_status),
        _explicit_study_move(input_data.intent),
    ):
        if maybe_move is not None:
            return maybe_move

    return _move(
        "answer",
        "learning policy should answer the user's material question",
        requires_evidence=True,
        expected_output_shape="Answer directly from evidence.",
    )


def _missing_index_move(material_status: MaterialStatus) -> LearningMove | None:
    if not material_status.has_materials or material_status.has_indexed_evidence:
        return None
    return _move(
        "retrieve_more",
        "material exists but indexed evidence is not available for this turn",
        requires_evidence=True,
        expected_output_shape=(
            "State the evidence gap and ask for a narrower source-grounded target."
        ),
    )


def _explicit_study_move(intent: str) -> LearningMove | None:
    if intent not in _STUDY_INTENTS:
        return None
    return _learning_move(
        "ask_recall",
        "the user asked to study, so active recall should come before more exposition",
        difficulty="easy",
        expected_output_shape="Ask one material-backed recall question with confidence.",
    )


def _driven_learning_move(input_data: LearningPolicyInput) -> LearningMove:
    state = input_data.learning_state
    session_type = session_type_from_text(state.practice_session_type or input_data.user_message)
    for strategy in _PRACTICE_STRATEGIES:
        if move := strategy(input_data, session_type):
            return move
    if state.phase is LearningPhase.RECALL:
        return _material_learning_move(input_data)
    return _learning_move(
        "ask_recall",
        "practice should drive the next useful active-learning step",
        expected_output_shape="State the session objective, then ask one recall task.",
    )


def _practice_review_move(
    input_data: LearningPolicyInput,
    session_type: PracticeSessionType,
) -> LearningMove | None:
    if not input_data.due_reviews and session_type is not PracticeSessionType.REVIEW:
        return None
    topic = (
        input_data.due_reviews[0].concept or input_data.due_reviews[0].item
        if input_data.due_reviews
        else None
    )
    return _learning_move(
        "review_due",
        "practice review prioritizes due recall before new explanation",
        target_topic=topic,
        expected_output_shape="Run the next due recall item and require confidence.",
    )


def _practice_weak_topic_move(
    input_data: LearningPolicyInput,
    session_type: PracticeSessionType,
) -> LearningMove | None:
    weak_topics = input_data.memory_state.weak_topics
    if session_type is not PracticeSessionType.WEAK_TOPICS or not weak_topics:
        return None
    if "contrastive_question" in input_data.memory_state.successful_interventions:
        return _learning_move(
            "contrastive_question",
            "local policy outcomes favor contrastive repair for this learner",
            target_topic=weak_topics[0],
            difficulty="medium",
            expected_output_shape="Ask a contrastive weak-topic diagnostic with confidence.",
        )
    return _learning_move(
        "ask_recall",
        "weak-topic practice should test the highest-priority weak topic first",
        target_topic=weak_topics[0],
        difficulty="medium",
        expected_output_shape="Start weak-topic repair with one diagnostic recall question.",
    )


def _practice_misconception_move(
    input_data: LearningPolicyInput,
    _session_type: PracticeSessionType,
) -> LearningMove | None:
    memory_state = input_data.memory_state
    if not memory_state.misconceptions:
        return None
    if _hint_preferred_over_contrast(memory_state):
        return _learning_move(
            "give_hint",
            "local policy outcomes suggest hint scaffolding before another contrast",
            target_topic=memory_state.misconceptions[0],
            difficulty="easy",
            expected_output_shape="Give one hint level, then ask the learner to continue.",
        )
    return _learning_move(
        "contrastive_question",
        _intervention_reason(
            memory_state,
            "contrastive_question",
            "practice is repairing a stored misconception",
        ),
        target_topic=memory_state.misconceptions[0],
        difficulty="medium",
        expected_output_shape="Ask a contrastive repair question and require confidence.",
    )


def _practice_session_type_move(
    _input_data: LearningPolicyInput,
    session_type: PracticeSessionType,
) -> LearningMove | None:
    spec = _PRACTICE_SESSION_TYPE_MOVES.get(session_type)
    if spec is None:
        return None
    kind, reason, difficulty, expected_output_shape = spec
    return _learning_move(
        kind,
        reason,
        difficulty=difficulty,
        expected_output_shape=expected_output_shape,
    )


_PRACTICE_STRATEGIES: tuple[LearningStrategy, ...] = (
    _practice_review_move,
    _practice_weak_topic_move,
    _practice_misconception_move,
    _practice_session_type_move,
)


_PRACTICE_SESSION_TYPE_MOVES: dict[PracticeSessionType, SessionTypeMoveSpec] = {
    PracticeSessionType.EXAM: (
        "diagnose_priority",
        "bounded exam prep should start by finding high-yield weak topics",
        "medium",
        "Give a bounded plan, then start a diagnostic recall question.",
    ),
    PracticeSessionType.CRAM: (
        "diagnose_priority",
        "bounded exam prep should start by finding high-yield weak topics",
        "medium",
        "Give a bounded plan, then start a diagnostic recall question.",
    ),
    PracticeSessionType.SOCRATIC: (
        "ask_recall",
        "socratic practice should ask before revealing",
        None,
        "Ask one targeted question and withhold the answer.",
    ),
    PracticeSessionType.DEEP: (
        "contrastive_question",
        "deep understanding benefits from why and contrastive questions",
        "hard",
        "Ask a why or contrastive transfer question with confidence.",
    ),
}


_ACTIVE_RECALL_ACTIONS = frozenset(
    {LearningAction.CALIBRATE, LearningAction.PROMPT_RECALL, LearningAction.SIMPLIFY}
)


def _move_from_action(
    action: LearningAction,
    input_data: LearningPolicyInput,
) -> LearningMove | None:
    if _is_recall_reprompt(action, input_data.learning_state):
        return _recall_reprompt_move(input_data)
    if action in _ACTIVE_RECALL_ACTIONS:
        return _active_recall_action_move(input_data)
    if spec := _ACTION_MOVE_SPECS.get(action):
        kind, reason, expected_output_shape = spec
        return _move(
            kind,
            reason,
            requires_evidence=True,
            expected_output_shape=expected_output_shape,
        )
    builder = _ACTION_MOVE_BUILDERS.get(action)
    return builder(input_data) if builder is not None else None


def _is_recall_reprompt(action: LearningAction, state: LearningState) -> bool:
    return action is LearningAction.PROMPT_RECALL and state.phase is LearningPhase.RECALL


def _recall_reprompt_move(_input_data: LearningPolicyInput) -> LearningMove:
    return _move(
        "ask_clarifying_question",
        "the learner asked to clarify or restate the active recall prompt",
        requires_evidence=False,
        requires_user_commitment=False,
    )


def _active_recall_action_move(_input_data: LearningPolicyInput) -> LearningMove:
    return _learning_move(
        "ask_recall",
        "the controller selected an active recall turn",
        expected_output_shape="Ask one recall task and request confidence from 0-100%.",
    )


def _present_action_move(input_data: LearningPolicyInput) -> LearningMove:
    if is_driven_learning_intent(input_data.intent):
        return _driven_learning_move(input_data)
    if input_data.intent == "chat":
        return _direct_answer_move(input_data)
    return _material_learning_move(input_data)


_ACTION_MOVE_SPECS: dict[LearningAction, ActionMoveSpec] = {
    LearningAction.PRIORITY: (
        "diagnose_priority",
        "priority analysis should reduce command burden and choose the next topic",
        "Recommend the next learning action and explain why it helps.",
    ),
    LearningAction.HINT: (
        "give_hint",
        "the learner requested help after an attempt",
        "Give one hint level only, then ask the learner to continue.",
    ),
    LearningAction.REVIEW: (
        "worked_example",
        "the learner needs minimum material before retrying recall",
        "Review one small cited evidence span, then prompt recall in the learner's language.",
    ),
    LearningAction.SOURCE_QA: (
        "answer",
        "the user asked a source-only question",
        "Answer directly from evidence without extra tutoring.",
    ),
}

_ACTION_MOVE_BUILDERS: dict[LearningAction, Callable[[LearningPolicyInput], LearningMove]] = {
    LearningAction.ASSESS: _material_learning_move,
    LearningAction.PRESENT: _present_action_move,
}


def _move(
    kind: LearningMoveKind,
    reason: str,
    *,
    requires_evidence: bool = False,
    requires_user_commitment: bool = False,
    difficulty: LearningMoveDifficulty | None = None,
    target_topic: str | None = None,
    expected_output_shape: str | None = None,
) -> LearningMove:
    return LearningMove(
        kind=kind,
        reason=reason,
        requires_evidence=requires_evidence,
        requires_user_commitment=requires_user_commitment,
        difficulty=difficulty,
        target_topic=target_topic,
        expected_output_shape=expected_output_shape,
    )


def _learning_move(
    kind: LearningMoveKind,
    reason: str,
    *,
    difficulty: LearningMoveDifficulty | None = None,
    target_topic: str | None = None,
    expected_output_shape: str | None = None,
) -> LearningMove:
    return _move(
        kind,
        reason,
        requires_evidence=True,
        requires_user_commitment=True,
        difficulty=difficulty,
        target_topic=target_topic,
        expected_output_shape=expected_output_shape,
    )


def _high_confidence_gap(state: LearningState) -> bool:
    return (
        state.last_confidence is not None
        and state.last_confidence >= 0.75
        and state.last_feedback_type in {LearningFeedbackType.PARTIAL, LearningFeedbackType.WRONG}
    )
