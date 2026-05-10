"""Deterministic controller for the study-loop state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from hephaistos.logging import get_logger
from hephaistos.study.overview import OVERVIEW_REQUEST_RE
from hephaistos.study.state import (
    StudyAction,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
)

_log = get_logger("study.controller")

_READY_RE = re.compile(
    r"^(?:ready|go|start|yes|y|ok|okay|i(?: am|'m)? ready|lets go|let's go)\b",
    re.IGNORECASE,
)
_INITIAL_CALIBRATION_RE = re.compile(
    r"^(?:"
    r"start|begin|"
    r"study|study with me|let'?s study|"
    r"quiz me|test me|ask me .*question.*|ask me something|"
    r"what should i study(?: next)?|what do i study(?: next)?"
    r")\??$",
    re.IGNORECASE,
)
_GREETING_RE = re.compile(r"^(?:hi|hey|hello|yo|sup)\.?!?$", re.IGNORECASE)
_THANKS_RE = re.compile(r"^(?:thanks|thank you|thx)\.?!?$", re.IGNORECASE)
_EXAM_DRILL_RE = re.compile(r"\b(?:exam|past exam|past paper|exam-style|timed)\b", re.IGNORECASE)
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
_SOURCE_QA_RE = re.compile(
    r"\b(?:"
    r"using (?:the )?source files?|"
    r"from (?:the )?(?:source|sources|materials?)|"
    r"according to (?:the )?(?:source|sources|materials?)|"
    r"answer with (?:just )?(?:the )?exact|"
    r"exact phrase|exact wording"
    r")\b",
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
    direct_reply: str | None = None


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
    return bool(_INITIAL_CALIBRATION_RE.fullmatch(text)) or bool(
        re.fullmatch(
            r"(?:can|could|would) you ask me .*question.*\??",
            text,
            re.IGNORECASE,
        )
    )


def _is_simple_greeting(user_input: str) -> bool:
    return bool(_GREETING_RE.fullmatch(_normalize(user_input)))


def _direct_chat_reply(user_input: str) -> str | None:
    text = _normalize(user_input)
    if _GREETING_RE.fullmatch(text):
        return "Hey."
    if _THANKS_RE.fullmatch(text):
        return "You're welcome."
    return None


def _is_overview_request(text: str) -> bool:
    return bool(OVERVIEW_REQUEST_RE.search(_normalize(text)))


def _is_reveal_request(text: str) -> bool:
    return bool(_REVEAL_RE.search(text) or _SHORT_REVEAL_RE.fullmatch(text))


def _is_source_qa_request(text: str) -> bool:
    return bool(_SOURCE_QA_RE.search(_normalize(text)))


def _calibration_prompt() -> str:
    return (
        "Controlled study state machine. Execute CALIBRATE.\n"
        "Rules:\n"
        "- Use the retrieved material to ask exactly one diagnostic recall question.\n"
        "- The question must test understanding of a concept, procedure, or "
        "relationship from the material — not surface-level document metadata.\n"
        "- FORBIDDEN question types (these never test knowledge):\n"
        "  * Titles of documents, chapters, sections, or slides.\n"
        "  * Author names, dates, or institutional affiliations.\n"
        "  * Page numbers, section numbers, or slide numbers.\n"
        "  * File names, folder names, or file paths.\n"
        "  * Headings or subheadings as standalone answers.\n"
        "- Instead, ask about definitions, cause-effect relationships, key steps "
        "in a procedure, comparisons between concepts, or applications of a "
        "principle.\n"
        "- Prefer an introductory, concrete item a new student can attempt.\n"
        "- If the student asked for an easy question, make it genuinely easy and "
        "prerequisite-level.\n"
        "- If the student asked for an exam-style or timed question, include one "
        "reasonable time limit and require them to reason their answer from memory.\n"
        "- Do not present the solution or method.\n"
        "- Do not include evidence IDs, citations, source labels, or answer-location hints "
        "in the question.\n"
        "- End with exactly: Answer from memory, or say easier or review material.\n"
        "- If no retrieved source material is available, ask which material or topic "
        "to start with."
    )


def _priority_prompt() -> str:
    return (
        "Controlled study state machine. Execute PRIORITY.\n"
        "Rules:\n"
        "- First build an explicit source inventory: which files are lecture material, "
        "which files are past exams, and why.\n"
        "- Mentions are not importance. Repeated headers, lecturer names, universities, "
        "course titles, dates, file names, and administrative text are not study topics.\n"
        "- Treat past exams as the strongest priority signal. Extract exam questions and "
        "visible point values before ranking topics.\n"
        "- Rank mathematical or pedagogical concepts only. If a candidate is metadata, "
        "discard it even if it appears many times.\n"
        "- Separate direct source evidence, deterministic tool/context findings, and "
        "unknowns. Cite evidence IDs for direct material claims.\n"
        "- Include missing prerequisites the student should review first.\n"
        "- Do not ask a recall question and do not start an exam drill.\n"
        "- If the retrieved evidence is too thin to infer priorities, say so and list "
        "what materials are needed."
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
        "- If no retrieved source material is available, say no searchable armory "
        "evidence was found for this item. Do not answer from outside knowledge. "
        "Ask for a more specific material-backed prompt or for the material to be indexed.\n"
        "- Do not switch into assessment or extra tutoring."
    )


def _source_qa_prompt(query: str) -> str:
    return (
        "Controlled study state machine. Execute SOURCE_QA.\n"
        f"User question: {query}\n"
        "Rules:\n"
        "- Answer the user's question directly using only the retrieved source material.\n"
        "- If the user asks for an exact phrase, quote only the exact phrase plus citations.\n"
        "- Cite evidence IDs for source-backed claims.\n"
        "- Do not ask a recall question.\n"
        "- Do not end with readiness, drill, or study-loop instructions.\n"
        "- If no retrieved source material answers the question, say that the armory sources "
        "do not contain the answer and ask for more specific material."
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
        "- The question must test understanding — not document titles, author names, "
        "dates, page numbers, file names, headings, or other surface metadata.\n"
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
        direct_reply = _direct_chat_reply(user_input)
        if direct_reply is not None:
            return StudyTurnPlan(
                action=StudyAction.CHAT,
                phase=state.phase,
                prompt="",
                allow_tools=False,
                direct_reply=direct_reply,
            )
        if "priorit" in text.lower():
            return StudyTurnPlan(
                action=StudyAction.PRIORITY,
                phase=state.phase,
                prompt=_priority_prompt(),
                retrieval_query="exam priority topics prerequisites past exams materials overview",
                allow_tools=False,
            )
        if _needs_initial_calibration(user_input):
            prompt = _calibration_prompt()
            if _EXAM_DRILL_RE.search(text):
                prompt = (
                    f"{prompt}\n"
                    "- This is an active-recall exam drill: do not show the result, "
                    "answer key, rubric, source explanation, source IDs, or citations until "
                    "after the student's attempt has been assessed."
                )
            return StudyTurnPlan(
                action=StudyAction.CALIBRATE,
                phase=StudyPhase.RECALL,
                prompt=prompt,
                allow_tools=False,
                buffer_response=True,
            )
        query = _derive_presentation_query(user_input, state)
        if _is_source_qa_request(query):
            return StudyTurnPlan(
                action=StudyAction.SOURCE_QA,
                phase=StudyPhase.PRESENTING,
                prompt=_source_qa_prompt(query),
                retrieval_query=query,
                allow_tools=False,
            )
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_present_prompt(query),
            retrieval_query=query,
            allow_tools=not _is_overview_request(query),
        )

    if _SKIP_RE.search(text):
        query = _derive_presentation_query(user_input, state)
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_present_prompt(query),
            retrieval_query=query,
            allow_tools=not _is_overview_request(query),
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
        allow_tools=not _is_overview_request(query),
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


def _recall_elapsed_seconds(state: StudyState, now: datetime) -> int | None:
    started = state.recall_started_at
    if started is None:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    elapsed = now - started
    return max(0, int(elapsed.total_seconds()))


def _derive_recall_rating(
    feedback: StudyFeedbackType,
    elapsed_seconds: int | None,
) -> StudyRecallRating:
    """Map correctness and response time into a scheduler-friendly effort signal."""
    if feedback is StudyFeedbackType.WRONG:
        return StudyRecallRating.HARD
    if feedback is StudyFeedbackType.PARTIAL:
        if elapsed_seconds is not None and elapsed_seconds <= 30:
            return StudyRecallRating.GOOD
        return StudyRecallRating.HARD
    if feedback is StudyFeedbackType.CORRECT:
        if elapsed_seconds is None:
            return StudyRecallRating.GOOD
        if elapsed_seconds <= 30:
            return StudyRecallRating.EASY
        if elapsed_seconds <= 120:
            return StudyRecallRating.GOOD
        return StudyRecallRating.HARD
    return StudyRecallRating.NONE


def apply_turn_result(
    state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    *,
    now: datetime | None = None,
) -> tuple[StudyState, str]:
    """Advance the state machine after a successful model reply."""
    current_time = now or datetime.now(UTC)
    next_state = state.clone()

    if plan.action is StudyAction.CHAT:
        next_state.last_feedback_type = StudyFeedbackType.NONE
        return next_state, plan.direct_reply or reply

    if plan.action is StudyAction.PRIORITY:
        next_state.phase = StudyPhase.PRESENTING
        next_state.last_feedback_type = StudyFeedbackType.NONE
        return next_state, reply

    if plan.action is StudyAction.SOURCE_QA:
        next_state.phase = StudyPhase.PRESENTING
        next_state.current_item = ""
        next_state.retrieval_query = ""
        next_state.expected_source_refs = []
        next_state.attempt_count = 0
        next_state.last_feedback_type = StudyFeedbackType.NONE
        next_state.recall_started_at = None
        return next_state, reply

    if plan.action is StudyAction.CALIBRATE:
        if source_refs:
            next_state.phase = StudyPhase.RECALL
            next_state.current_item = _normalize(reply)
            next_state.retrieval_query = plan.retrieval_query or next_state.current_item
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.CALIBRATING
            next_state.recall_started_at = current_time
            next_state.last_recall_seconds = None
            next_state.last_recall_rating = StudyRecallRating.NONE
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
            next_state.recall_started_at = None
        return next_state, reply

    if plan.action is StudyAction.PRESENT:
        if source_refs:
            next_state.phase = StudyPhase.WAITING_FOR_READY
            next_state.current_item = plan.retrieval_query or state.current_item
            next_state.retrieval_query = plan.retrieval_query or state.retrieval_query
            next_state.expected_source_refs = list(source_refs)
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.PRESENTED
            next_state.recall_started_at = None
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
            next_state.recall_started_at = None
        return next_state, reply

    if plan.action is StudyAction.PROMPT_RECALL:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.READY
        next_state.recall_started_at = current_time
        next_state.last_recall_seconds = None
        next_state.last_recall_rating = StudyRecallRating.NONE
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
            next_state.recall_started_at = current_time
            next_state.last_recall_seconds = None
            next_state.last_recall_rating = StudyRecallRating.NONE
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
            next_state.recall_started_at = None
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        return next_state, reply

    if plan.action is StudyAction.ASSESS:
        feedback, cleaned_reply = _parse_assessment_reply(reply)
        elapsed_seconds = _recall_elapsed_seconds(state, current_time)
        next_state.attempt_count = state.attempt_count + 1
        if source_refs:
            next_state.expected_source_refs = list(source_refs)
        next_state.last_feedback_type = feedback
        next_state.last_recall_seconds = elapsed_seconds
        next_state.last_recall_rating = _derive_recall_rating(feedback, elapsed_seconds)
        if feedback is StudyFeedbackType.CORRECT:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.recall_started_at = None
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.recall_started_at = current_time
        return next_state, cleaned_reply

    return next_state, reply
