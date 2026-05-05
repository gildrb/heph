"""Deterministic controller for the study-loop state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass

from hephaistos.logging import get_logger
from hephaistos.study.state import StudyAction, StudyFeedbackType, StudyPhase, StudyState

_log = get_logger("study.controller")

_READY_RE = re.compile(
    r"^(?:ready|go|start|yes|y|ok|okay|i(?: am|'m)? ready|lets go|let's go)\b",
    re.IGNORECASE,
)
_INITIAL_CALIBRATION_RE = re.compile(
    r"^(?:"
    r"hi|hey|hello|yo|start|begin|"
    r"study|study with me|let'?s study|"
    r"quiz me|test me|ask me something|"
    r"what should i study(?: next)?|what do i study(?: next)?"
    r")\??$",
    re.IGNORECASE,
)
_SKIP_RE = re.compile(
    r"\b(?:skip|pass|next|move on|different question|another question|new question)\b",
    re.IGNORECASE,
)
_REVEAL_RE = re.compile(
    r"\b(?:"
    r"show (?:me )?(?:the )?(?:full )?(?:answer|solution)|"
    r"tell me (?:the )?(?:full )?(?:answer|solution)|"
    r"give me (?:the )?(?:full )?(?:answer|solution)|"
    r"reveal(?: the)?(?: answer| solution)?|"
    r"explain again|full answer|full solution"
    r")\b",
    re.IGNORECASE,
)
_SHORT_REVEAL_RE = re.compile(r"^(?:answer|solution)\s*(?:please|\?)?$", re.IGNORECASE)
_HINT_RE = re.compile(r"\b(?:hint|nudge|clue)\b", re.IGNORECASE)
_TOO_HARD_RE = re.compile(
    r"\b(?:too hard|too difficult|easier|simpler|i don'?t know|dunno|"
    r"no idea|lost|stuck|can'?t answer|cannot answer)\b",
    re.IGNORECASE,
)
_REVIEW_MATERIAL_RE = re.compile(
    r"\b(?:review|look at (?:the )?material|study (?:the )?material|"
    r"show (?:me )?(?:the )?material|teach me|walk me through)\b",
    re.IGNORECASE,
)
_ASSESS_PREFIX_RE = re.compile(r"^\s*(CORRECT|PARTIAL|WRONG)\s*[:\-]?\s*", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class StudyTurnPlan:
    """Controller output for a single user turn."""

    action: StudyAction
    phase: StudyPhase
    prompt: str
    retrieval_query: str | None = None
    use_expected_source_refs: bool = False
    allow_tools: bool = True
    buffer_response: bool = False


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def _derive_presentation_query(user_input: str, state: StudyState) -> str:
    cleaned = _normalize(user_input)
    if cleaned and not _SKIP_RE.fullmatch(cleaned.lower()):
        return cleaned
    if state.current_item:
        return f"different material-backed item from {state.current_item}"
    return "next material-backed study item"


def _needs_initial_calibration(user_input: str) -> bool:
    text = _normalize(user_input)
    return bool(_INITIAL_CALIBRATION_RE.fullmatch(text))


def _is_reveal_request(text: str) -> bool:
    return bool(_REVEAL_RE.search(text) or _SHORT_REVEAL_RE.fullmatch(text))


def _calibration_prompt() -> str:
    return (
        "Controlled study state machine. Execute CALIBRATE.\n"
        "Rules:\n"
        "- Use the retrieved material to ask exactly one diagnostic recall question.\n"
        "- Prefer an introductory, concrete item a new student can attempt.\n"
        "- Do not present the solution or method.\n"
        "- Cite evidence IDs only if you state a factual setup from the material.\n"
        "- End with exactly: Answer from memory, or say easier or review material.\n"
        "- If no retrieved source material is available, ask which material or topic "
        "to start with."
    )


def _present_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute the PRESENT phase.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Use only the retrieved material for this item.\n"
        "- Present the complete solution or method once, concisely.\n"
        "- Cite evidence IDs whenever you state a factual step or value.\n"
        "- End with exactly: Say ready when you want recall.\n"
        "- If no retrieved source material is available, say the armory does not "
        "cover this item and ask for a more specific material-backed prompt.\n"
        "- Do not switch into assessment or extra tutoring."
    )


def _waiting_prompt() -> str:
    return (
        "Controlled study state machine. Execute WAITING_FOR_READY.\n"
        "Rules:\n"
        "- Do not reveal any more of the solution.\n"
        "- Tell the student to say ready when they want recall.\n"
        "- Keep it to one short sentence."
    )


def _recall_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute RECALL.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Do not answer the item.\n"
        "- Tell the student to reproduce the solution from memory now.\n"
        "- Keep it to one short sentence."
    )


def _refusal_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute REFUSE_REVEAL.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Do not reveal new solution content.\n"
        "- Briefly refuse and tell the student to attempt recall first.\n"
        "- Keep it to one or two short sentences."
    )


def _hint_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute HINT.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Use only the stored material context for this item.\n"
        "- Give exactly one first-step hint.\n"
        "- Do not reveal later steps or the full answer.\n"
        "- If no grounded material context is available, say no grounded hint is available.\n"
        "- Keep it to one short sentence."
    )


def _simplify_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute SIMPLIFY.\n"
        f"Previous item: {item}\n"
        "Rules:\n"
        "- The previous recall item was too hard.\n"
        "- Use only the stored material context for this item.\n"
        "- Ask exactly one easier prerequisite recall question.\n"
        "- Do not reveal the answer to either question.\n"
        "- End with exactly: Answer from memory, or say review material.\n"
        "- If no grounded material context is available, say no easier grounded question "
        "is available."
    )


def _review_prompt(item: str) -> str:
    return (
        "Controlled study state machine. Execute REVIEW.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- The student needs to look at the material before attempting recall.\n"
        "- Use only the stored material context for this item.\n"
        "- Present the minimum source-backed explanation needed to restart.\n"
        "- Cite evidence IDs whenever you state a factual step or value.\n"
        "- End with exactly: Say ready when you want recall.\n"
        "- If no grounded material context is available, say no grounded review is available."
    )


def _assess_prompt(item: str, attempt_count: int) -> str:
    return (
        "Controlled study state machine. Execute ASSESS.\n"
        f"Current item: {item}\n"
        f"Attempt number: {attempt_count + 1}\n"
        "Rules:\n"
        "- Evaluate the student's attempt against the retrieved material only.\n"
        "- Start the reply with exactly one label: CORRECT:, PARTIAL:, or WRONG:.\n"
        "- CORRECT: one short sentence only. Do not restate the solution.\n"
        "- PARTIAL: state only what is missing in one sentence. "
        "Do not fill in the missing content.\n"
        "- WRONG: give only the first-step hint in one sentence. Do not reveal later steps.\n"
        "- No praise. No encouragement. No extra exposition.\n"
        "- If material evidence is missing, default to PARTIAL: "
        "and say grounded assessment is unavailable."
    )


def plan_turn(state: StudyState, user_input: str) -> StudyTurnPlan:
    """Return the deterministic handling plan for one user turn."""
    text = _normalize(user_input)

    if not state.current_item:
        if _needs_initial_calibration(user_input):
            return StudyTurnPlan(
                action=StudyAction.CALIBRATE,
                phase=StudyPhase.RECALL,
                prompt=_calibration_prompt(),
                allow_tools=False,
            )
        query = _derive_presentation_query(user_input, state)
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_present_prompt(query),
            retrieval_query=query,
            allow_tools=True,
        )

    if _SKIP_RE.search(text):
        query = _derive_presentation_query(user_input, state)
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_present_prompt(query),
            retrieval_query=query,
            allow_tools=True,
        )

    if state.phase == StudyPhase.WAITING_FOR_READY:
        if _READY_RE.search(text):
            return StudyTurnPlan(
                action=StudyAction.PROMPT_RECALL,
                phase=StudyPhase.RECALL,
                prompt=_recall_prompt(state.current_item),
                allow_tools=False,
            )
        if _is_reveal_request(text):
            return StudyTurnPlan(
                action=StudyAction.REFUSE_REVEAL,
                phase=StudyPhase.WAITING_FOR_READY,
                prompt=_refusal_prompt(state.current_item),
                allow_tools=False,
            )
        return StudyTurnPlan(
            action=StudyAction.WAIT_READY_REMINDER,
            phase=StudyPhase.WAITING_FOR_READY,
            prompt=_waiting_prompt(),
            allow_tools=False,
        )

    if state.phase == StudyPhase.RECALL:
        if _is_reveal_request(text):
            return StudyTurnPlan(
                action=StudyAction.REFUSE_REVEAL,
                phase=StudyPhase.RECALL,
                prompt=_refusal_prompt(state.current_item),
                allow_tools=False,
            )
        if _REVIEW_MATERIAL_RE.search(text):
            return StudyTurnPlan(
                action=StudyAction.REVIEW,
                phase=StudyPhase.PRESENTING,
                prompt=_review_prompt(state.current_item),
                retrieval_query=state.retrieval_query or state.current_item,
                use_expected_source_refs=True,
                allow_tools=False,
            )
        if _TOO_HARD_RE.search(text):
            return StudyTurnPlan(
                action=StudyAction.SIMPLIFY,
                phase=StudyPhase.RECALL,
                prompt=_simplify_prompt(state.current_item),
                retrieval_query=state.retrieval_query or state.current_item,
                use_expected_source_refs=True,
                allow_tools=False,
            )
        if _HINT_RE.search(text) and state.attempt_count > 0:
            return StudyTurnPlan(
                action=StudyAction.HINT,
                phase=StudyPhase.ASSESS,
                prompt=_hint_prompt(state.current_item),
                retrieval_query=state.retrieval_query or state.current_item,
                use_expected_source_refs=True,
                allow_tools=False,
            )
        return StudyTurnPlan(
            action=StudyAction.ASSESS,
            phase=StudyPhase.ASSESS,
            prompt=_assess_prompt(state.current_item, state.attempt_count),
            retrieval_query=state.retrieval_query or state.current_item,
            use_expected_source_refs=True,
            allow_tools=False,
            buffer_response=True,
        )

    query = _derive_presentation_query(user_input, state)
    return StudyTurnPlan(
        action=StudyAction.PRESENT,
        phase=StudyPhase.PRESENTING,
        prompt=_present_prompt(query),
        retrieval_query=query,
        allow_tools=True,
    )


def _fallback_assessment_message(feedback: StudyFeedbackType) -> str:
    if feedback is StudyFeedbackType.CORRECT:
        return "Correct. Move to the next item."
    if feedback is StudyFeedbackType.WRONG:
        return "Start again from the first step only."
    return "Your attempt is incomplete. Try again from memory."


def _parse_assessment_reply(reply: str) -> tuple[StudyFeedbackType, str]:
    match = _ASSESS_PREFIX_RE.match(reply)
    if not match:
        _log.warning("assessment reply missing prefix; defaulting to PARTIAL")
        cleaned = reply.strip() or _fallback_assessment_message(StudyFeedbackType.PARTIAL)
        return StudyFeedbackType.PARTIAL, cleaned

    label = match.group(1).upper()
    cleaned = _ASSESS_PREFIX_RE.sub("", reply, count=1).strip()
    feedback = {
        "CORRECT": StudyFeedbackType.CORRECT,
        "PARTIAL": StudyFeedbackType.PARTIAL,
        "WRONG": StudyFeedbackType.WRONG,
    }[label]
    return feedback, cleaned or _fallback_assessment_message(feedback)


def apply_turn_result(
    state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
) -> tuple[StudyState, str]:
    """Advance the state machine after a successful model reply."""
    next_state = state.clone()

    if plan.action is StudyAction.CALIBRATE:
        if source_refs:
            next_state.phase = StudyPhase.RECALL
            next_state.current_item = _normalize(reply)
            next_state.retrieval_query = plan.retrieval_query or next_state.current_item
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.CALIBRATING
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        return next_state, reply

    if plan.action is StudyAction.PRESENT:
        if source_refs:
            next_state.phase = StudyPhase.WAITING_FOR_READY
            next_state.current_item = plan.retrieval_query or state.current_item
            next_state.retrieval_query = plan.retrieval_query or state.retrieval_query
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.PRESENTED
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        return next_state, reply

    if plan.action is StudyAction.PROMPT_RECALL:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.READY
        return next_state, reply

    if plan.action is StudyAction.WAIT_READY_REMINDER:
        next_state.phase = StudyPhase.WAITING_FOR_READY
        next_state.last_feedback_type = StudyFeedbackType.WAITING
        return next_state, reply

    if plan.action is StudyAction.REFUSE_REVEAL:
        next_state.phase = state.phase
        next_state.last_feedback_type = StudyFeedbackType.REFUSED
        return next_state, reply

    if plan.action is StudyAction.HINT:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.HINT
        if source_refs:
            next_state.expected_source_refs = list(source_refs)
        return next_state, reply

    if plan.action is StudyAction.SIMPLIFY:
        if source_refs:
            next_state.phase = StudyPhase.RECALL
            next_state.current_item = _normalize(reply)
            next_state.retrieval_query = plan.retrieval_query or state.retrieval_query
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.EASIER
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        return next_state, reply

    if plan.action is StudyAction.REVIEW:
        if source_refs:
            next_state.phase = StudyPhase.WAITING_FOR_READY
            next_state.current_item = state.current_item
            next_state.retrieval_query = plan.retrieval_query or state.retrieval_query
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.REVIEWING
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        return next_state, reply

    if plan.action is StudyAction.ASSESS:
        feedback, cleaned_reply = _parse_assessment_reply(reply)
        next_state.attempt_count = state.attempt_count + 1
        if source_refs:
            next_state.expected_source_refs = list(source_refs)
        next_state.last_feedback_type = feedback
        if feedback is StudyFeedbackType.CORRECT:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
        else:
            next_state.phase = StudyPhase.RECALL
        return next_state, cleaned_reply

    return next_state, reply
