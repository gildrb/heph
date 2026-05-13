"""Autonomous study policy primitives.

The policy in this module is intentionally deterministic. It gives the chat
orchestrator a small, inspectable study move instead of relying on a single
large prompt to decide how a learning session should proceed.
"""

from __future__ import annotations

import re
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
type EvidenceAction = Literal[
    "answer",
    "retrieve_more",
    "ask_clarifying_question",
    "abstain",
    "give_partial_answer",
    "quiz_first",
]


class AutopilotSessionType(StrEnum):
    """Named bounded autopilot session profiles."""

    GENERAL = "general"
    EXAM = "exam"
    WEAK_TOPICS = "weak-topics"
    REVIEW = "review"
    SOCRATIC = "socratic"
    CRAM = "cram"
    DEEP = "deep"


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """Compact due-review signal for the policy."""

    item: str
    concept: str = ""
    failures: int = 0
    last_confidence: float | None = None


@dataclass(frozen=True, slots=True)
class TurnSummary:
    """Small prior-turn summary used by the policy when available."""

    role: str
    text: str
    feedback: StudyFeedbackType = StudyFeedbackType.NONE
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class MemoryState:
    """Learner-memory signal consumed by the autonomy policy."""

    weak_topics: tuple[str, ...] = ()
    misconceptions: tuple[str, ...] = ()
    successful_interventions: tuple[str, ...] = ()
    failed_interventions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MaterialStatus:
    """Summary of the currently enabled material index."""

    has_materials: bool = False
    has_indexed_evidence: bool = False
    evidence_refs: tuple[str, ...] = ()
    sampled_source_count: int = 0
    total_source_count: int = 0


@dataclass(frozen=True, slots=True)
class AutopilotInput:
    """Inputs used by the policy to choose one study move."""

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
    """The next pedagogical move selected for a turn."""

    kind: StudyMoveKind
    reason: str
    requires_evidence: bool
    requires_user_commitment: bool
    difficulty: StudyMoveDifficulty | None
    target_topic: str | None
    expected_output_shape: str | None


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    """Conservative material sufficiency judgement for a turn."""

    sufficient: bool
    confidence: float
    supporting_refs: tuple[str, ...]
    missing_information: tuple[str, ...]
    conflicts: tuple[str, ...]
    source_diversity_score: float
    recommended_action: EvidenceAction


@dataclass(frozen=True, slots=True)
class LearnerAssessment:
    """Separated correctness and confidence signal for the learner model."""

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
    """Local validator output for response-shape checks."""

    valid: bool
    issues: tuple[str, ...]
    rewrite_instruction: str | None
    suggested_next_action: str | None


@dataclass(frozen=True, slots=True)
class ChoiceAssessment:
    """Assessment of a learner's study-path choice and self-diagnosis."""

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
    """One observed intervention outcome for harness-level reinforcement."""

    move_type: StudyMoveKind
    topic: str
    correctness_delta: float
    confidence_delta: float
    mastery_delta: float
    time_cost_seconds: int
    frustration_signal: bool = False

    @property
    def score(self) -> float:
        """Return a simple local policy score for future move selection."""
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


class StudyAutopilot:
    """Deterministic next-move policy for manual, guided, and autopilot modes."""

    def next_turn(self, input_data: AutopilotInput) -> StudyMove:
        """Choose the next useful study move."""
        mode = input_data.mode
        if mode is StudyAutonomyMode.MANUAL:
            return _manual_move(input_data)
        if mode is StudyAutonomyMode.AUTOPILOT:
            return _autopilot_move(input_data)
        return _guided_move(input_data)


def infer_turn_mode(state: StudyState, user_message: str) -> StudyAutonomyMode:
    """Resolve explicit persistent mode plus lightweight language inference."""
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
    """Score whether retrieved evidence is enough to answer safely."""
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
    """Build a separated correctness/confidence learner signal from study state."""
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
        next_action=_next_action_from_feedback(state),
    )


def validate_pedagogy(reply: str, move: StudyMove, mode: StudyAutonomyMode) -> PedagogyValidation:
    """Check basic response-shape requirements for the selected study move."""
    issues: list[str] = []
    normalized = reply.casefold()
    if move.requires_user_commitment and "confidence" not in normalized:
        issues.append("missing confidence request")
    if move.kind in {"ask_recall", "contrastive_question"} and _looks_like_answer_leak(reply):
        issues.append("possible answer leakage during recall")
    if mode is not StudyAutonomyMode.MANUAL and not _has_next_action(reply, move):
        issues.append("missing explicit next action")
    if (
        mode is StudyAutonomyMode.GUIDED
        and move.expected_output_shape is not None
        and "recommend" in move.expected_output_shape.casefold()
        and not _has_recommendation_rationale(reply)
    ):
        issues.append("missing recommendation rationale")
    if not issues:
        return PedagogyValidation(True, (), None, None)
    return PedagogyValidation(
        valid=False,
        issues=tuple(issues),
        rewrite_instruction=_rewrite_instruction(move),
        suggested_next_action=move.expected_output_shape,
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
    """Select a study move using a controller action as the strongest signal."""
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
    """Append concise mode and next-action instructions to a model prompt."""
    if not prompt or mode is StudyAutonomyMode.MANUAL or action is StudyAction.CHAT:
        return prompt

    lines = [
        "",
        "Autonomous study policy:",
        f"- Mode: {mode.value}.",
        f"- Selected study move: {move.kind}.",
        f"- Reason: {move.reason}",
    ]
    if mode is StudyAutonomyMode.GUIDED:
        lines.extend(
            [
                "- Guided mode should leave the learner in control while recommending "
                "the next useful study step.",
                "- Include a short reason why the recommendation is beneficial.",
                "- Do not require extra commands when one clear recommendation is enough.",
            ]
        )
    if mode is StudyAutonomyMode.AUTOPILOT:
        lines.extend(
            [
                "- You are HEPH AUTOPILOT: drive the study workflow while the learner "
                "does the thinking.",
                "- Choose the next best academic action yourself unless one concise "
                "clarification is essential.",
                "- Prefer active recall, prediction, comparison, or application before "
                "passive explanation.",
                "- Retrieve and verify source-dependent claims; never fabricate citations.",
                "- Track correctness, confidence, misconceptions, weak topics, and due review.",
                "- Schedule or mark review after mistakes, low confidence, fragile success, "
                "or exam-relevant learning.",
                "- Use exactly one primary pedagogical move in the response.",
                "- End with the next concrete learner action, not a vague offer.",
            ]
        )
    if move.requires_user_commitment:
        lines.append("- Require the learner to commit and include confidence from 0-100%.")
    if move.expected_output_shape:
        lines.append(f"- End with this response shape: {move.expected_output_shape}")
    if move.kind == "offer_choices":
        lines.extend(
            [
                "- Offer choices only when there is a real pedagogical fork.",
                "- Require: option, reason, confidence from 0-100%, and weakest point.",
                "- Assess the learner's self-diagnosis before accepting the chosen path.",
                "- Override a weak choice when the reason conflicts with the learning signal.",
            ]
        )
    if action is StudyAction.SOURCE_QA:
        lines.append("- Source-only answer: do not add a study-choice block after the answer.")
    if action is StudyAction.CALIBRATE:
        lines.append("- The whole response is the recall task; do not reveal the answer.")
        if mode is StudyAutonomyMode.AUTOPILOT:
            lines.extend(
                [
                    "- Start directly with the recall task; do not include internal labels.",
                    "- Ask for the smallest necessary user input and begin immediately.",
                ]
            )
    if action is StudyAction.ASSESS and _high_confidence_gap_from_move(move):
        lines.append("- Prefer a contrastive correction before another explanation.")
    return f"{prompt}\n" + "\n".join(lines)


def choice_prompt(reason: str, options: tuple[str, ...]) -> str:
    """Build a productive-friction choice prompt."""
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
    """Assess whether a learner choice includes metacognitive evidence."""
    selected = _parse_choice_option(text)
    confidence = _parse_choice_confidence(text)
    has_reason = bool(_CHOICE_REASON_RE.search(text))
    self_diagnosis = _parse_self_diagnosis(text)
    issues: list[str] = []
    if selected is None:
        issues.append("missing option")
    if not has_reason:
        issues.append("missing reason")
    if confidence is None:
        issues.append("missing confidence")
    if not self_diagnosis:
        issues.append("missing weakest-point self-diagnosis")

    normalized_recommendation = _normalize_option(recommended_option)
    should_override = (
        selected is not None
        and normalized_recommendation is not None
        and selected != normalized_recommendation
        and (not has_reason or confidence is None or confidence < 0.5 or not self_diagnosis)
    )
    if should_override:
        issues.append("weak justification for non-recommended option")

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


def normalize_confidence_value(raw_value: float, unit: str = "") -> float | None:
    """Normalize common learner confidence formats onto a 0-1 scale."""
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
    """Parse a compact time budget such as ``45m`` or ``1h``."""
    match = re.search(r"\b(?P<value>\d{1,3})\s*(?P<unit>m|min|mins|minutes|h|hr|hour)s?\b", text)
    if match is None:
        return None
    value = int(match.group("value"))
    unit = match.group("unit")
    minutes = value * 60 if unit.startswith("h") else value
    return min(24 * 60, max(1, minutes))


def session_type_from_text(text: str) -> AutopilotSessionType:
    """Infer a named autopilot session profile from command text."""
    normalized = text.casefold()
    if "exam" in normalized:
        return AutopilotSessionType.EXAM
    if "weak" in normalized:
        return AutopilotSessionType.WEAK_TOPICS
    if "review" in normalized:
        return AutopilotSessionType.REVIEW
    if "socratic" in normalized:
        return AutopilotSessionType.SOCRATIC
    if "cram" in normalized:
        return AutopilotSessionType.CRAM
    if "deep" in normalized:
        return AutopilotSessionType.DEEP
    return AutopilotSessionType.GENERAL


def _manual_move(input_data: AutopilotInput) -> StudyMove:
    if input_data.study_state.phase is StudyPhase.RECALL:
        return _move("assess", "manual mode keeps the current recall loop in control")
    return _move("answer", "manual mode should answer the user's direct request")


def _intervention_succeeded(memory_state: MemoryState, move_kind: StudyMoveKind) -> bool:
    return move_kind in memory_state.successful_interventions


def _intervention_failed(memory_state: MemoryState, move_kind: StudyMoveKind) -> bool:
    return move_kind in memory_state.failed_interventions


def _intervention_reason(
    memory_state: MemoryState,
    move_kind: StudyMoveKind,
    fallback: str,
) -> str:
    if _intervention_succeeded(memory_state, move_kind):
        return f"{fallback}, and local policy outcomes favor {move_kind}"
    return fallback


def _guided_move(input_data: AutopilotInput) -> StudyMove:
    state = input_data.study_state
    if input_data.due_reviews:
        topic = input_data.due_reviews[0].concept or input_data.due_reviews[0].item
        return _move(
            "review_due",
            "a scheduled material-backed review is due",
            target_topic=topic,
            requires_user_commitment=True,
            expected_output_shape="Ask one due active-recall question before explaining.",
        )
    if state.phase is StudyPhase.RECALL:
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
    if _CHOICE_RE.search(input_data.user_message) or _CHOICE_RESPONSE_RE.search(
        input_data.user_message
    ):
        recommended = _recommended_choice_option(input_data)
        choice_assessment = assess_choice_response(
            input_data.user_message,
            recommended_option=recommended,
        )
        if choice_assessment.selected_option is not None:
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
                    reason="guided mode follows the learner's justified study-path choice",
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
        return _move(
            "offer_choices",
            "the user is choosing a study path",
            requires_user_commitment=True,
            expected_output_shape="Offer choices that require reason, confidence, and weakness.",
        )
    if input_data.memory_state.misconceptions:
        if _intervention_failed(input_data.memory_state, "contrastive_question") and (
            _intervention_succeeded(input_data.memory_state, "give_hint")
        ):
            return _move(
                "give_hint",
                "local policy outcomes suggest a scaffolded hint works better than contrast",
                target_topic=input_data.memory_state.misconceptions[0],
                requires_evidence=True,
                requires_user_commitment=True,
                difficulty="easy",
                expected_output_shape="Give one hint level, then ask the learner to continue.",
            )
        return _move(
            "contrastive_question",
            _intervention_reason(
                input_data.memory_state,
                "contrastive_question",
                "stored learner state shows a recurring misconception",
            ),
            target_topic=input_data.memory_state.misconceptions[0],
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Ask a contrastive question before giving another summary.",
        )
    if input_data.memory_state.weak_topics and _STUDY_RE.search(input_data.user_message):
        return _move(
            "ask_recall",
            "stored learner state points to a weak topic",
            target_topic=input_data.memory_state.weak_topics[0],
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Ask one recall task on the weakest topic with confidence.",
        )
    if (
        input_data.material_status.has_materials
        and not input_data.material_status.has_indexed_evidence
    ):
        return _move(
            "retrieve_more",
            "material exists but indexed evidence is not available for this turn",
            requires_evidence=True,
            expected_output_shape=(
                "State the evidence gap and ask for a narrower source-backed target."
            ),
        )
    if _STUDY_RE.search(input_data.user_message):
        return _move(
            "ask_recall",
            "the user asked to study, so active recall should come before more exposition",
            requires_evidence=True,
            requires_user_commitment=True,
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
    if input_data.due_reviews or session_type is AutopilotSessionType.REVIEW:
        topic = ""
        if input_data.due_reviews:
            topic = input_data.due_reviews[0].concept or input_data.due_reviews[0].item
        return _move(
            "review_due",
            "autopilot review prioritizes due recall before new explanation",
            target_topic=topic or None,
            requires_evidence=True,
            requires_user_commitment=True,
            expected_output_shape="Run the next due recall item and require confidence.",
        )
    if session_type is AutopilotSessionType.WEAK_TOPICS and input_data.memory_state.weak_topics:
        if _intervention_succeeded(input_data.memory_state, "contrastive_question"):
            return _move(
                "contrastive_question",
                "local policy outcomes favor contrastive repair for this learner",
                target_topic=input_data.memory_state.weak_topics[0],
                requires_evidence=True,
                requires_user_commitment=True,
                difficulty="medium",
                expected_output_shape="Ask a contrastive weak-topic diagnostic with confidence.",
            )
        return _move(
            "ask_recall",
            "weak-topic autopilot should test the highest-priority weak topic first",
            target_topic=input_data.memory_state.weak_topics[0],
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Start weak-topic repair with one diagnostic recall question.",
        )
    if input_data.memory_state.misconceptions:
        if _intervention_failed(input_data.memory_state, "contrastive_question") and (
            _intervention_succeeded(input_data.memory_state, "give_hint")
        ):
            return _move(
                "give_hint",
                "local policy outcomes suggest hint scaffolding before another contrast",
                target_topic=input_data.memory_state.misconceptions[0],
                requires_evidence=True,
                requires_user_commitment=True,
                difficulty="easy",
                expected_output_shape="Give one hint level, then ask the learner to continue.",
            )
        return _move(
            "contrastive_question",
            _intervention_reason(
                input_data.memory_state,
                "contrastive_question",
                "autopilot is repairing a stored misconception",
            ),
            target_topic=input_data.memory_state.misconceptions[0],
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Ask a contrastive repair question and require confidence.",
        )
    if session_type in {AutopilotSessionType.EXAM, AutopilotSessionType.CRAM}:
        return _move(
            "diagnose_priority",
            "bounded exam prep should start by finding high-yield weak topics",
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Give a bounded plan, then start a diagnostic recall question.",
        )
    if session_type is AutopilotSessionType.SOCRATIC:
        return _move(
            "ask_recall",
            "Socratic mode should ask before revealing",
            requires_evidence=True,
            requires_user_commitment=True,
            expected_output_shape="Ask one targeted question and withhold the answer.",
        )
    if session_type is AutopilotSessionType.DEEP:
        return _move(
            "contrastive_question",
            "deep understanding benefits from why and contrastive questions",
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="hard",
            expected_output_shape="Ask a why or contrastive transfer question with confidence.",
        )
    if state.phase is StudyPhase.RECALL:
        return _guided_move(input_data)
    return _move(
        "ask_recall",
        "autopilot should drive the next useful active-learning step",
        requires_evidence=True,
        requires_user_commitment=True,
        expected_output_shape="State the session objective, then ask one recall task.",
    )


def _move_from_action(action: StudyAction, input_data: AutopilotInput) -> StudyMove | None:
    if action in {StudyAction.CALIBRATE, StudyAction.PROMPT_RECALL, StudyAction.SIMPLIFY}:
        return _move(
            "ask_recall",
            "the controller selected an active recall turn",
            requires_evidence=True,
            requires_user_commitment=True,
            expected_output_shape="Ask one recall task and request confidence from 0-100%.",
        )
    if action is StudyAction.PRIORITY:
        return _move(
            "diagnose_priority",
            "priority analysis should reduce command burden and choose the next topic",
            requires_evidence=True,
            requires_user_commitment=False,
            expected_output_shape="Recommend the next study action and explain why it helps.",
        )
    if action is StudyAction.ASSESS:
        return _guided_move(input_data)
    if action is StudyAction.HINT:
        return _move(
            "give_hint",
            "the learner requested help after an attempt",
            requires_evidence=True,
            expected_output_shape="Give one hint level only, then ask the learner to continue.",
        )
    if action is StudyAction.REVIEW:
        return _move(
            "worked_example",
            "the learner needs minimum material before retrying recall",
            requires_evidence=True,
            expected_output_shape="Review the smallest source-backed piece, then ask for recall.",
        )
    if action is StudyAction.SOURCE_QA:
        return _move(
            "answer",
            "the user asked a source-only question",
            requires_evidence=True,
            expected_output_shape="Answer directly from evidence without extra tutoring.",
        )
    if action is StudyAction.PRESENT:
        if input_data.mode is StudyAutonomyMode.AUTOPILOT:
            return _autopilot_move(input_data)
        if input_data.mode is StudyAutonomyMode.MANUAL:
            return _manual_move(input_data)
        return _guided_move(input_data)
    return None


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


def _recommended_choice_option(input_data: AutopilotInput) -> str:
    state = input_data.study_state
    if input_data.memory_state.misconceptions or _high_confidence_gap(state):
        return "C"
    if state.last_feedback_type in {StudyFeedbackType.PARTIAL, StudyFeedbackType.WRONG}:
        return "C"
    return "A"


def _move_for_choice_option(
    input_data: AutopilotInput,
    option: str,
    *,
    reason: str,
) -> StudyMove:
    normalized = option.upper()
    if normalized == "A":
        return _move(
            "ask_recall",
            reason,
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="medium",
            expected_output_shape="Ask one targeted recall question and require confidence.",
        )
    if normalized == "B":
        return _move(
            "worked_example",
            reason,
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="easy",
            expected_output_shape=(
                "Give one concise worked step, then ask a similar recall check with confidence."
            ),
        )
    if _intervention_failed(
        input_data.memory_state,
        "contrastive_question",
    ) and _intervention_succeeded(
        input_data.memory_state,
        "give_hint",
    ):
        return _move(
            "give_hint",
            reason,
            requires_evidence=True,
            requires_user_commitment=True,
            difficulty="easy",
            expected_output_shape="Give one hint level, then ask the learner to continue.",
        )
    return _move(
        "contrastive_question",
        reason,
        requires_evidence=True,
        requires_user_commitment=True,
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


def _next_action_from_feedback(state: StudyState) -> StudyMoveKind:
    if _high_confidence_gap(state):
        return "contrastive_question"
    if state.last_feedback_type is StudyFeedbackType.CORRECT:
        return "schedule_review"
    if state.last_feedback_type is StudyFeedbackType.PARTIAL:
        return "give_hint"
    if state.last_feedback_type is StudyFeedbackType.WRONG:
        return "ask_recall"
    return "answer"


def _looks_like_answer_leak(reply: str) -> bool:
    normalized = reply.casefold()
    return any(marker in normalized for marker in ("the answer is", "solution:", "full solution"))


def _has_next_action(reply: str, move: StudyMove) -> bool:
    normalized = reply.casefold()
    return (
        "next" in normalized
        or move.kind in normalized
        or "try this" in normalized
        or "answer from memory" in normalized
    )


def _has_recommendation_rationale(reply: str) -> bool:
    return bool(_RATIONALE_RE.search(reply))


def _rewrite_instruction(move: StudyMove) -> str:
    if move.requires_user_commitment:
        return "Rewrite to require an attempt and confidence before revealing more."
    return "Rewrite to match the selected study move and include one clear next step."


def _high_confidence_gap_from_move(move: StudyMove) -> bool:
    return move.kind == "contrastive_question" or "confidence" in move.reason


def _parse_choice_option(text: str) -> str | None:
    match = _CHOICE_OPTION_RE.search(text)
    if match is None:
        return None
    return match.group("option").upper()


def _normalize_option(value: str | None) -> str | None:
    if value is None:
        return None
    match = _CHOICE_OPTION_RE.search(value)
    if match is None:
        return None
    return match.group("option").upper()


def _parse_choice_confidence(text: str) -> float | None:
    match = _CHOICE_CONFIDENCE_RE.search(text)
    if match is None:
        return None
    raw_value = float(match.group("value"))
    unit = match.group("unit") or ""
    return normalize_confidence_value(raw_value, unit)


def _parse_self_diagnosis(text: str) -> str:
    if not _CHOICE_WEAKNESS_RE.search(text):
        return ""
    normalized = " ".join(text.strip().split())
    if len(normalized) <= 160:
        return normalized
    return normalized[:159].rstrip() + "…"
