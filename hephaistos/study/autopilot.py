"""Autonomous study policy primitives.

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
    StudyAction,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
)

type StudyMoveKind = Literal[
    "answer",
    "ask_recall",
    "give_hint",
    "assess",
    "offer_choices",
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
type StudyMoveDifficulty = Literal["easy", "medium", "hard"]
type SessionTypeMoveSpec = tuple[StudyMoveKind, str, StudyMoveDifficulty | None, str]
type EvidenceAction = Literal[
    "answer",
    "retrieve_more",
    "ask_clarifying_question",
    "abstain",
    "give_partial_answer",
    "quiz_first",
]
type ActionMoveBuilder = Callable[[AutopilotInput], StudyMove]
type AutopilotStrategy = Callable[[AutopilotInput, AutopilotSessionType], StudyMove | None]


class AutopilotSessionType(StrEnum):
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
    feedback: StudyFeedbackType = StudyFeedbackType.NONE
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
class AutopilotInput:
    user_message: str
    mode: StudyAutonomyMode
    session_goal: str | None
    time_budget_minutes: int | None
    study_state: StudyState
    memory_state: MemoryState
    due_reviews: tuple[ReviewItem, ...]
    recent_turns: tuple[TurnSummary, ...]
    material_status: MaterialStatus


@dataclass(frozen=True, slots=True)
class StudyMove:
    kind: StudyMoveKind
    reason: str
    requires_evidence: bool
    requires_user_commitment: bool
    difficulty: StudyMoveDifficulty | None
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
    next_action: StudyMoveKind


@dataclass(frozen=True, slots=True)
class PedagogyValidation:
    valid: bool
    issues: tuple[str, ...]
    rewrite_instruction: str | None
    suggested_next_action: str | None


@dataclass(frozen=True, slots=True)
class ChoiceAssessment:
    selected_option: str | None
    has_reason: bool
    confidence: float | None
    self_diagnosis: str
    valid: bool
    issues: tuple[str, ...]
    should_override: bool
    recommendation: str | None


@dataclass(frozen=True, slots=True)
class PolicyOutcome:
    move_type: StudyMoveKind
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


_JUST_ANSWER_RE = re.compile(r"\b(?:just|only)\s+answer\b|\bno\s+(?:quiz|tutor|drill)\b")
_AUTOPILOT_RE = re.compile(
    r"\b(?:autopilot|prepare me|exam prep|cram|study plan|drive the session)\b",
    re.IGNORECASE,
)
_STUDY_RE = re.compile(
    r"\b(?:help me study|study with me|quiz me|test me|what should i study)\b",
    re.IGNORECASE,
)
_CHOICE_RE = re.compile(r"\b(?:choose|choice|option|a/b|multiple[- ]choice)\b", re.IGNORECASE)
_CHOICE_OPTION_RE = re.compile(
    r"\b(?:option\s*)?(?P<option>[A-D])(?:[.)])?\b",
    re.IGNORECASE,
)
_CHOICE_RESPONSE_RE = re.compile(r"^\s*(?:option\s*)?[A-D](?:[.)]|\b)", re.IGNORECASE)
_CHOICE_CONFIDENCE_RE = re.compile(
    r"\b(?:confidence|confident|sure)(?:\s+is)?\s*[:=]?\s*"
    r"(?P<value>\d+(?:[.]\d+)?)\s*"
    r"(?P<unit>%|/10|/5)?(?=\s|[.,;:!?]|$)",
    re.IGNORECASE,
)
_CHOICE_REASON_RE = re.compile(r"\b(?:because|reason|why|since)\b", re.IGNORECASE)
_CHOICE_WEAKNESS_RE = re.compile(
    r"\b(?:weakest|weakness|weak point|struggle|confus(?:e|ed|ing)|unsure)\b",
    re.IGNORECASE,
)
_RATIONALE_RE = re.compile(
    r"\b(?:because|reason|helps?|beneficial|benefit|so that|so you|useful)\b",
    re.IGNORECASE,
)
_SESSION_TYPE_CUES = (
    ("exam", AutopilotSessionType.EXAM),
    ("weak", AutopilotSessionType.WEAK_TOPICS),
    ("review", AutopilotSessionType.REVIEW),
    ("socratic", AutopilotSessionType.SOCRATIC),
    ("cram", AutopilotSessionType.CRAM),
    ("deep", AutopilotSessionType.DEEP),
)
_NEXT_ACTION_BY_FEEDBACK: dict[StudyFeedbackType, StudyMoveKind] = {
    StudyFeedbackType.CORRECT: "schedule_review",
    StudyFeedbackType.PARTIAL: "give_hint",
    StudyFeedbackType.WRONG: "ask_recall",
}


class StudyAutopilot:
    def next_turn(self, input_data: AutopilotInput) -> StudyMove:
        mode = input_data.mode
        if mode is StudyAutonomyMode.MANUAL:
            return _manual_move(input_data)
        if mode is StudyAutonomyMode.AUTOPILOT:
            return _autopilot_move(input_data)
        return _guided_move(input_data)


def infer_turn_mode(state: StudyState, user_message: str) -> StudyAutonomyMode:
    text = user_message.casefold()
    if _JUST_ANSWER_RE.search(text):
        return StudyAutonomyMode.MANUAL
    if _AUTOPILOT_RE.search(text):
        return StudyAutonomyMode.AUTOPILOT
    if state.autonomy_mode is StudyAutonomyMode.MANUAL:
        return StudyAutonomyMode.MANUAL
    if _STUDY_RE.search(text) and state.autonomy_mode is not StudyAutonomyMode.AUTOPILOT:
        return StudyAutonomyMode.GUIDED
    return state.autonomy_mode


def assess_evidence(
    refs: tuple[str, ...],
    *,
    source_only: bool = False,
    missing_hint: str = "more targeted indexed source evidence",
) -> EvidenceAssessment:
    sources = {ref.split("#chunk=", maxsplit=1)[0] for ref in refs}
    diversity = min(1.0, len(sources) / 3) if refs else 0.0
    if not refs:
        return EvidenceAssessment(
            sufficient=False,
            confidence=0.0,
            supporting_refs=(),
            missing_information=(missing_hint,),
            conflicts=(),
            source_diversity_score=0.0,
            recommended_action="abstain" if source_only else "retrieve_more",
        )
    if len(refs) == 1:
        return EvidenceAssessment(
            sufficient=not source_only,
            confidence=0.48 if source_only else 0.58,
            supporting_refs=refs,
            missing_information=("corroborating source span",),
            conflicts=(),
            source_diversity_score=diversity,
            recommended_action="give_partial_answer" if source_only else "answer",
        )
    return EvidenceAssessment(
        sufficient=True,
        confidence=min(0.95, 0.62 + 0.1 * len(refs) + 0.1 * diversity),
        supporting_refs=refs,
        missing_information=(),
        conflicts=(),
        source_diversity_score=diversity,
        recommended_action="answer",
    )


def learner_assessment_from_state(
    state: StudyState,
    *,
    topic: str = "",
    hint_level_used: int | None = None,
) -> LearnerAssessment:
    correctness = {
        StudyFeedbackType.CORRECT: 1.0,
        StudyFeedbackType.PARTIAL: 0.55,
        StudyFeedbackType.WRONG: 0.0,
    }.get(state.last_feedback_type, 0.0)
    reasoning_quality = {
        StudyRecallRating.EASY: 0.9,
        StudyRecallRating.GOOD: 0.75,
        StudyRecallRating.HARD: 0.35,
        StudyRecallRating.NONE: 0.0,
    }[state.last_recall_rating]
    confidence = state.last_confidence
    calibration_gap = abs(confidence - correctness) if confidence is not None else None
    misconception_tags = ("high_confidence_gap",) if _high_confidence_gap(state) else ()
    return LearnerAssessment(
        topic=topic or state.retrieval_query or state.current_item,
        correctness=correctness,
        reasoning_quality=reasoning_quality,
        confidence=confidence,
        calibration_gap=calibration_gap,
        misconception_tags=misconception_tags,
        hint_level_used=hint_level_used,
        next_action=(
            "contrastive_question"
            if _high_confidence_gap(state)
            else _NEXT_ACTION_BY_FEEDBACK.get(state.last_feedback_type, "answer")
        ),
    )


def validate_pedagogy(reply: str, move: StudyMove, mode: StudyAutonomyMode) -> PedagogyValidation:
    issues: list[str] = []
    normalized = reply.casefold()
    if move.requires_user_commitment and "confidence" not in normalized:
        issues.append("missing confidence request")
    if _looks_like_recall_answer_leak(normalized, move):
        issues.append("possible answer leakage during recall")
    if _missing_next_action(normalized, move, mode):
        issues.append("missing explicit next action")
    if _missing_guided_rationale(reply, move, mode):
        issues.append("missing recommendation rationale")
    if not issues:
        return PedagogyValidation(True, (), None, None)
    return PedagogyValidation(
        valid=False,
        issues=tuple(issues),
        rewrite_instruction=(
            "Rewrite to require an attempt and confidence before revealing more."
            if move.requires_user_commitment
            else "Rewrite to match the selected learning move and include one clear next step."
        ),
        suggested_next_action=move.expected_output_shape,
    )


def _looks_like_recall_answer_leak(normalized_reply: str, move: StudyMove) -> bool:
    if move.kind not in {"ask_recall", "contrastive_question"}:
        return False
    return any(
        marker in normalized_reply for marker in ("the answer is", "solution:", "full solution")
    )


def _missing_next_action(
    normalized_reply: str,
    move: StudyMove,
    mode: StudyAutonomyMode,
) -> bool:
    if mode is StudyAutonomyMode.MANUAL or move.kind == "ask_clarifying_question":
        return False
    return not (
        "next" in normalized_reply
        or move.kind in normalized_reply
        or "try this" in normalized_reply
        or "answer from memory" in normalized_reply
    )


def _missing_guided_rationale(
    reply: str,
    move: StudyMove,
    mode: StudyAutonomyMode,
) -> bool:
    return (
        mode is StudyAutonomyMode.GUIDED
        and move.expected_output_shape is not None
        and "recommend" in move.expected_output_shape.casefold()
        and _RATIONALE_RE.search(reply) is None
    )


def move_for_plan(
    plan_action: StudyAction,
    state: StudyState,
    user_message: str,
    *,
    evidence_refs: tuple[str, ...] = (),
    due_reviews: tuple[ReviewItem, ...] = (),
    memory_state: MemoryState | None = None,
) -> StudyMove:
    material_status = MaterialStatus(
        has_materials=bool(evidence_refs),
        has_indexed_evidence=bool(evidence_refs),
        evidence_refs=evidence_refs,
        sampled_source_count=len({ref.split("#chunk=", maxsplit=1)[0] for ref in evidence_refs}),
        total_source_count=len({ref.split("#chunk=", maxsplit=1)[0] for ref in evidence_refs}),
    )
    input_data = AutopilotInput(
        user_message=user_message,
        mode=infer_turn_mode(state, user_message),
        session_goal=state.session_goal or None,
        time_budget_minutes=state.time_budget_minutes,
        study_state=state,
        memory_state=memory_state if memory_state is not None else MemoryState(),
        due_reviews=due_reviews,
        recent_turns=(),
        material_status=material_status,
    )
    move = _move_from_action(plan_action, input_data)
    if move is not None:
        return move
    return StudyAutopilot().next_turn(input_data)


def append_policy_prompt(
    prompt: str,
    *,
    mode: StudyAutonomyMode,
    move: StudyMove,
    action: StudyAction,
) -> str:
    if not prompt or mode is StudyAutonomyMode.MANUAL or action is StudyAction.CHAT:
        return prompt

    lines = [
        "",
        "Study policy:",
        f"- Mode: {mode.value}.",
        f"- Move: {move.kind}; reason: {move.reason}",
    ]
    lines.extend(_mode_policy_lines(mode))
    lines.extend(_move_policy_lines(move))
    lines.extend(_action_policy_lines(action, mode=mode, move=move))
    return f"{prompt}\n" + "\n".join(lines)


def _mode_policy_lines(mode: StudyAutonomyMode) -> tuple[str, ...]:
    if mode is StudyAutonomyMode.GUIDED:
        return ("- Recommend the next useful step while leaving the learner in control.",)
    if mode is StudyAutonomyMode.AUTOPILOT:
        return (
            "- Drive the workflow; choose the next academic action unless clarification "
            "is essential.",
            "- Use one primary pedagogical move and end with a concrete learner action.",
        )
    return ()


def _move_policy_lines(move: StudyMove) -> tuple[str, ...]:
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
    if move.kind == "offer_choices":
        lines.append("- Require: option, reason, confidence from 0-100%, and weakest point.")
    return tuple(lines)


def _action_policy_lines(
    action: StudyAction,
    *,
    mode: StudyAutonomyMode,
    move: StudyMove,
) -> tuple[str, ...]:
    if action is StudyAction.SOURCE_QA:
        return ("- Source-only answer: do not add a learning-choice block after the answer.",)
    if action is StudyAction.CALIBRATE:
        return _calibration_policy_lines(mode)
    if action is StudyAction.ASSESS and _needs_contrastive_correction(move):
        return ("- Prefer a contrastive correction before another explanation.",)
    return ()


def _calibration_policy_lines(mode: StudyAutonomyMode) -> tuple[str, ...]:
    lines = ["- The whole response is the recall task; do not reveal the answer."]
    if mode is StudyAutonomyMode.AUTOPILOT:
        lines.extend(
            (
                "- Start directly with the recall task; do not include internal labels.",
                "- Ask for the smallest necessary user input and begin immediately.",
            )
        )
    return tuple(lines)


def _needs_contrastive_correction(move: StudyMove) -> bool:
    return move.kind == "contrastive_question" or "confidence" in move.reason


def choice_prompt(reason: str, options: tuple[str, ...]) -> str:
    rendered = "\n".join(f"{chr(65 + index)}. {option}" for index, option in enumerate(options))
    return (
        f"{reason}\n\n"
        "Choose one path, but include your reasoning:\n"
        f"{rendered}\n\n"
        "Reply with option, why you chose it, confidence from 0-100%, "
        "and what you think your weakest point is."
    )


def assess_choice_response(
    text: str,
    *,
    recommended_option: str | None = None,
) -> ChoiceAssessment:
    selected = _choice_selected_option(text)
    confidence = _choice_confidence(text)
    has_reason = bool(_CHOICE_REASON_RE.search(text))
    self_diagnosis = _choice_self_diagnosis(text)

    normalized_recommendation = _choice_selected_option(recommended_option or "")
    should_override = _should_override_choice(
        selected=selected,
        recommended=normalized_recommendation,
        has_reason=has_reason,
        confidence=confidence,
        self_diagnosis=self_diagnosis,
    )
    issues = _choice_response_issues(
        selected=selected,
        has_reason=has_reason,
        confidence=confidence,
        self_diagnosis=self_diagnosis,
        should_override=should_override,
    )

    return ChoiceAssessment(
        selected_option=selected,
        has_reason=has_reason,
        confidence=confidence,
        self_diagnosis=self_diagnosis,
        valid=not issues,
        issues=tuple(issues),
        should_override=should_override,
        recommendation=normalized_recommendation,
    )


def _choice_response_issues(
    *,
    selected: str | None,
    has_reason: bool,
    confidence: float | None,
    self_diagnosis: str,
    should_override: bool,
) -> tuple[str, ...]:
    issues: list[str] = []
    if selected is None:
        issues.append("missing option")
    if not has_reason:
        issues.append("missing reason")
    if confidence is None:
        issues.append("missing confidence")
    if not self_diagnosis:
        issues.append("missing weakest-point self-diagnosis")
    if should_override:
        issues.append("weak justification for non-recommended option")
    return tuple(issues)


def _should_override_choice(
    *,
    selected: str | None,
    recommended: str | None,
    has_reason: bool,
    confidence: float | None,
    self_diagnosis: str,
) -> bool:
    weak_justification = not has_reason or confidence is None or confidence < 0.5
    return (
        selected is not None
        and recommended is not None
        and selected != recommended
        and (weak_justification or not self_diagnosis)
    )


def _choice_selected_option(text: str) -> str | None:
    match = _CHOICE_OPTION_RE.search(text)
    return match.group("option").upper() if match is not None else None


def _choice_confidence(text: str) -> float | None:
    match = _CHOICE_CONFIDENCE_RE.search(text)
    if match is None:
        return None
    return normalize_confidence_value(float(match.group("value")), match.group("unit") or "")


def _choice_self_diagnosis(text: str) -> str:
    if _CHOICE_WEAKNESS_RE.search(text) is None:
        return ""
    self_diagnosis = " ".join(text.strip().split())
    if len(self_diagnosis) > 160:
        return self_diagnosis[:159].rstrip() + "…"
    return self_diagnosis


def normalize_confidence_value(raw_value: float, unit: str = "") -> float | None:
    if unit == "%":
        confidence = raw_value / 100
    elif unit == "/10":
        confidence = raw_value / 10
    elif unit == "/5":
        confidence = raw_value / 5
    elif raw_value <= 1:
        confidence = raw_value
    elif raw_value <= 5:
        confidence = raw_value / 5
    elif raw_value <= 10:
        confidence = raw_value / 10
    else:
        return None
    return min(1.0, max(0.0, confidence))


def parse_time_budget_minutes(text: str) -> int | None:
    match = re.search(r"\b(?P<value>\d{1,3})\s*(?P<unit>m|min|mins|minutes|h|hr|hour)s?\b", text)
    if match is None:
        return None
    value = int(match.group("value"))
    unit = match.group("unit")
    minutes = value * 60 if unit.startswith("h") else value
    return min(24 * 60, max(1, minutes))


def session_type_from_text(text: str) -> AutopilotSessionType:
    normalized = text.casefold()
    for cue, session_type in _SESSION_TYPE_CUES:
        if cue in normalized:
            return session_type
    return AutopilotSessionType.GENERAL


def _manual_move(input_data: AutopilotInput) -> StudyMove:
    if input_data.study_state.phase is StudyPhase.RECALL:
        return _move("assess", "manual mode keeps the current recall loop in control")
    return _move("answer", "manual mode should answer the user's direct request")


def _hint_preferred_over_contrast(memory_state: MemoryState) -> bool:
    return (
        "contrastive_question" in memory_state.failed_interventions
        and "give_hint" in memory_state.successful_interventions
    )


def _intervention_reason(
    memory_state: MemoryState,
    move_kind: StudyMoveKind,
    fallback: str,
) -> str:
    if move_kind in memory_state.successful_interventions:
        return f"{fallback}, and local policy outcomes favor {move_kind}"
    return fallback


def _due_review_move(input_data: AutopilotInput) -> StudyMove | None:
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


def _active_recall_move(state: StudyState) -> StudyMove | None:
    if state.phase is not StudyPhase.RECALL:
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


def _recommended_choice_option(input_data: AutopilotInput) -> str:
    state = input_data.study_state
    repair_signal = (
        input_data.memory_state.misconceptions
        or _high_confidence_gap(state)
        or state.last_feedback_type in {StudyFeedbackType.PARTIAL, StudyFeedbackType.WRONG}
    )
    return "C" if repair_signal else "A"


def _choice_reply_move(input_data: AutopilotInput) -> StudyMove | None:
    if not (
        _CHOICE_RE.search(input_data.user_message)
        or _CHOICE_RESPONSE_RE.search(input_data.user_message)
    ):
        return None

    choice_assessment = assess_choice_response(
        input_data.user_message,
        recommended_option=_recommended_choice_option(input_data),
    )
    if choice_assessment.selected_option is None:
        return _move(
            "offer_choices",
            "the user is choosing a study path",
            requires_user_commitment=True,
            expected_output_shape="Offer choices that require reason, confidence, and weakness.",
        )
    if choice_assessment.should_override and choice_assessment.recommendation is not None:
        return _move_for_choice_option(
            input_data,
            choice_assessment.recommendation,
            reason=(
                "the selected path conflicts with the learner signal, so guided mode "
                "overrides to the stronger pedagogical option"
            ),
        )
    if choice_assessment.valid:
        return _move_for_choice_option(
            input_data,
            choice_assessment.selected_option,
            reason="guided mode follows the learner's justified learning-path choice",
        )
    issues = ", ".join(choice_assessment.issues)
    return _move(
        "offer_choices",
        f"the choice reply is incomplete ({issues})",
        requires_user_commitment=True,
        expected_output_shape=(
            "Require option, reason, confidence 0-100%, and weakest-point diagnosis."
        ),
    )


def _stored_memory_move(input_data: AutopilotInput) -> StudyMove | None:
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
    if memory_state.weak_topics and _STUDY_RE.search(input_data.user_message):
        return _learning_move(
            "ask_recall",
            "stored learner state points to a weak topic",
            target_topic=memory_state.weak_topics[0],
            difficulty="medium",
            expected_output_shape="Ask one recall task on the weakest topic with confidence.",
        )
    return None


def _guided_move(input_data: AutopilotInput) -> StudyMove:
    for maybe_move in (
        _due_review_move(input_data),
        _active_recall_move(input_data.study_state),
        _choice_reply_move(input_data),
        _stored_memory_move(input_data),
    ):
        if maybe_move is not None:
            return maybe_move

    if (
        input_data.material_status.has_materials
        and not input_data.material_status.has_indexed_evidence
    ):
        return _move(
            "retrieve_more",
            "material exists but indexed evidence is not available for this turn",
            requires_evidence=True,
            expected_output_shape=(
                "State the evidence gap and ask for a narrower source-grounded target."
            ),
        )
    if _STUDY_RE.search(input_data.user_message):
        return _learning_move(
            "ask_recall",
            "the user asked to study, so active recall should come before more exposition",
            difficulty="easy",
            expected_output_shape="Ask one material-backed recall question with confidence.",
        )
    return _move(
        "answer",
        "guided mode should answer and then recommend the next study action",
        requires_evidence=True,
        expected_output_shape=(
            "Answer from evidence, then add one recommended next step and why it helps."
        ),
    )


def _autopilot_move(input_data: AutopilotInput) -> StudyMove:
    state = input_data.study_state
    session_type = session_type_from_text(state.autopilot_session_type or input_data.user_message)
    for strategy in _AUTOPILOT_STRATEGIES:
        if move := strategy(input_data, session_type):
            return move
    if state.phase is StudyPhase.RECALL:
        return _guided_move(input_data)
    return _learning_move(
        "ask_recall",
        "autopilot should drive the next useful active-learning step",
        expected_output_shape="State the session objective, then ask one recall task.",
    )


def _autopilot_review_move(
    input_data: AutopilotInput,
    session_type: AutopilotSessionType,
) -> StudyMove | None:
    if not input_data.due_reviews and session_type is not AutopilotSessionType.REVIEW:
        return None
    topic = (
        input_data.due_reviews[0].concept or input_data.due_reviews[0].item
        if input_data.due_reviews
        else None
    )
    return _learning_move(
        "review_due",
        "autopilot review prioritizes due recall before new explanation",
        target_topic=topic,
        expected_output_shape="Run the next due recall item and require confidence.",
    )


def _autopilot_weak_topic_move(
    input_data: AutopilotInput,
    session_type: AutopilotSessionType,
) -> StudyMove | None:
    weak_topics = input_data.memory_state.weak_topics
    if session_type is not AutopilotSessionType.WEAK_TOPICS or not weak_topics:
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
        "weak-topic autopilot should test the highest-priority weak topic first",
        target_topic=weak_topics[0],
        difficulty="medium",
        expected_output_shape="Start weak-topic repair with one diagnostic recall question.",
    )


def _autopilot_misconception_move(
    input_data: AutopilotInput,
    _session_type: AutopilotSessionType,
) -> StudyMove | None:
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
            "autopilot is repairing a stored misconception",
        ),
        target_topic=memory_state.misconceptions[0],
        difficulty="medium",
        expected_output_shape="Ask a contrastive repair question and require confidence.",
    )


def _autopilot_session_type_move(
    _input_data: AutopilotInput,
    session_type: AutopilotSessionType,
) -> StudyMove | None:
    spec = _AUTOPILOT_SESSION_TYPE_MOVES.get(session_type)
    if spec is None:
        return None
    kind, reason, difficulty, expected_output_shape = spec
    return _learning_move(
        kind,
        reason,
        difficulty=difficulty,
        expected_output_shape=expected_output_shape,
    )


_AUTOPILOT_STRATEGIES: tuple[AutopilotStrategy, ...] = (
    _autopilot_review_move,
    _autopilot_weak_topic_move,
    _autopilot_misconception_move,
    _autopilot_session_type_move,
)


_AUTOPILOT_SESSION_TYPE_MOVES: dict[AutopilotSessionType, SessionTypeMoveSpec] = {
    AutopilotSessionType.EXAM: (
        "diagnose_priority",
        "bounded exam prep should start by finding high-yield weak topics",
        "medium",
        "Give a bounded plan, then start a diagnostic recall question.",
    ),
    AutopilotSessionType.CRAM: (
        "diagnose_priority",
        "bounded exam prep should start by finding high-yield weak topics",
        "medium",
        "Give a bounded plan, then start a diagnostic recall question.",
    ),
    AutopilotSessionType.SOCRATIC: (
        "ask_recall",
        "Socratic mode should ask before revealing",
        None,
        "Ask one targeted question and withhold the answer.",
    ),
    AutopilotSessionType.DEEP: (
        "contrastive_question",
        "deep understanding benefits from why and contrastive questions",
        "hard",
        "Ask a why or contrastive transfer question with confidence.",
    ),
}


_ACTIVE_RECALL_ACTIONS = frozenset(
    {StudyAction.CALIBRATE, StudyAction.PROMPT_RECALL, StudyAction.SIMPLIFY}
)


def _move_from_action(action: StudyAction, input_data: AutopilotInput) -> StudyMove | None:
    if _is_recall_reprompt(action, input_data.study_state):
        return _recall_reprompt_move(input_data)
    if action in _ACTIVE_RECALL_ACTIONS:
        return _active_recall_action_move(input_data)
    builder = _ACTION_MOVE_BUILDERS.get(action)
    return builder(input_data) if builder is not None else None


def _is_recall_reprompt(action: StudyAction, state: StudyState) -> bool:
    return action is StudyAction.PROMPT_RECALL and state.phase is StudyPhase.RECALL


def _recall_reprompt_move(_input_data: AutopilotInput) -> StudyMove:
    return _move(
        "ask_clarifying_question",
        "the learner asked to clarify or restate the active recall prompt",
        requires_evidence=False,
        requires_user_commitment=False,
    )


def _active_recall_action_move(_input_data: AutopilotInput) -> StudyMove:
    return _learning_move(
        "ask_recall",
        "the controller selected an active recall turn",
        expected_output_shape="Ask one recall task and request confidence from 0-100%.",
    )


def _priority_action_move(_input_data: AutopilotInput) -> StudyMove:
    return _move(
        "diagnose_priority",
        "priority analysis should reduce command burden and choose the next topic",
        requires_evidence=True,
        requires_user_commitment=False,
        expected_output_shape="Recommend the next study action and explain why it helps.",
    )


def _hint_action_move(_input_data: AutopilotInput) -> StudyMove:
    return _move(
        "give_hint",
        "the learner requested help after an attempt",
        requires_evidence=True,
        expected_output_shape="Give one hint level only, then ask the learner to continue.",
    )


def _review_action_move(_input_data: AutopilotInput) -> StudyMove:
    return _move(
        "worked_example",
        "the learner needs minimum material before retrying recall",
        requires_evidence=True,
        expected_output_shape=(
            "Review one small cited evidence span, then prompt recall in the learner's language."
        ),
    )


def _source_qa_action_move(_input_data: AutopilotInput) -> StudyMove:
    return _move(
        "answer",
        "the user asked a source-only question",
        requires_evidence=True,
        expected_output_shape="Answer directly from evidence without extra tutoring.",
    )


def _present_action_move(input_data: AutopilotInput) -> StudyMove:
    if input_data.mode is StudyAutonomyMode.AUTOPILOT:
        return _autopilot_move(input_data)
    if input_data.mode is StudyAutonomyMode.MANUAL:
        return _manual_move(input_data)
    return _guided_move(input_data)


_ACTION_MOVE_BUILDERS: dict[StudyAction, ActionMoveBuilder] = {
    StudyAction.PRIORITY: _priority_action_move,
    StudyAction.ASSESS: _guided_move,
    StudyAction.HINT: _hint_action_move,
    StudyAction.REVIEW: _review_action_move,
    StudyAction.SOURCE_QA: _source_qa_action_move,
    StudyAction.PRESENT: _present_action_move,
}


def _move(
    kind: StudyMoveKind,
    reason: str,
    *,
    requires_evidence: bool = False,
    requires_user_commitment: bool = False,
    difficulty: StudyMoveDifficulty | None = None,
    target_topic: str | None = None,
    expected_output_shape: str | None = None,
) -> StudyMove:
    return StudyMove(
        kind=kind,
        reason=reason,
        requires_evidence=requires_evidence,
        requires_user_commitment=requires_user_commitment,
        difficulty=difficulty,
        target_topic=target_topic,
        expected_output_shape=expected_output_shape,
    )


def _learning_move(
    kind: StudyMoveKind,
    reason: str,
    *,
    difficulty: StudyMoveDifficulty | None = None,
    target_topic: str | None = None,
    expected_output_shape: str | None = None,
) -> StudyMove:
    return _move(
        kind,
        reason,
        requires_evidence=True,
        requires_user_commitment=True,
        difficulty=difficulty,
        target_topic=target_topic,
        expected_output_shape=expected_output_shape,
    )


def _move_for_choice_option(
    input_data: AutopilotInput,
    option: str,
    *,
    reason: str,
) -> StudyMove:
    normalized = option.upper()
    if normalized == "A":
        return _learning_move(
            "ask_recall",
            reason,
            difficulty="medium",
            expected_output_shape="Ask one targeted recall question and require confidence.",
        )
    if normalized == "B":
        return _learning_move(
            "worked_example",
            reason,
            difficulty="easy",
            expected_output_shape=(
                "Give one concise worked step, then ask a similar recall check with confidence."
            ),
        )
    if _hint_preferred_over_contrast(input_data.memory_state):
        return _learning_move(
            "give_hint",
            reason,
            difficulty="easy",
            expected_output_shape="Give one hint level, then ask the learner to continue.",
        )
    return _learning_move(
        "contrastive_question",
        reason,
        difficulty="medium",
        target_topic=(
            input_data.memory_state.misconceptions[0]
            if input_data.memory_state.misconceptions
            else None
        ),
        expected_output_shape=(
            "Ask one prerequisite or contrastive repair question with confidence."
        ),
    )


def _high_confidence_gap(state: StudyState) -> bool:
    return (
        state.last_confidence is not None
        and state.last_confidence >= 0.75
        and state.last_feedback_type in {StudyFeedbackType.PARTIAL, StudyFeedbackType.WRONG}
    )
