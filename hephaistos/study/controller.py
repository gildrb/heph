"""Deterministic controller for the study-loop state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from hephaistos.logging import get_logger
from hephaistos.study.autopilot import (
    MemoryState,
    ReviewItem,
    StudyMove,
    append_policy_prompt,
    infer_turn_mode,
    move_for_plan,
    normalize_confidence_value,
)
from hephaistos.study.overview import OVERVIEW_REQUEST_RE
from hephaistos.study.state import (
    StudyAction,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    StudyState,
)

_log = get_logger("study.controller")

_READY_RE = re.compile(
    r"^(?:"
    r"ready|go|go ahead|start|yes|y|ok|okay|"
    r"i\s*(?:am|'m|m)?\s+ready|"
    r"lets go|let's go"
    r")(?:[.!?]|\s+now)?$",
    re.IGNORECASE,
)
_WAITING_PROCEDURE_RE = re.compile(
    r"^(?:"
    r"what now|now what|what next|next step|what should i do|what do i do next|"
    r"not ready|not yet|wait|wait for now|later|hold on|"
    r"i\s*(?:am|'m|m)?\s+not\s+ready|"
    r"no"
    r")[.!?]?$",
    re.IGNORECASE,
)
_RECALL_CLARIFICATION_RE = re.compile(
    r"\b(?:"
    r"which (?:answer|question|one)|"
    r"what (?:answer|question|do you want|should i answer|am i answering)|"
    r"answer what|"
    r"repeat (?:the )?(?:question|prompt)|"
    r"say (?:the )?(?:question|prompt) again"
    r")\b",
    re.IGNORECASE,
)
_RECALL_REPROMPT_RE = re.compile(
    r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
    r"(?:ask|repeat|restate|rephrase|say|read|write|translate|traduc\w*)\b"
    r"(?=[^.!?]*(?:again|once more|one more time|question|prompt|item|task|exercise|"
    r"(?:in|auf|en|em)\s+[\w-]+|language|sprache|idioma|langue|lingua))",
    re.IGNORECASE,
)
_RECALL_SHORT_REPROMPT_RE = re.compile(
    r"^(?:again|once more|one more time|nochmal|noch einmal)"
    r"(?:\s+(?:in|auf|en|em)\s+[\w-]+)?"
    r"(?:\s+(?:please|bitte))?[.!?]?$",
    re.IGNORECASE,
)
_RECALL_LANGUAGE_ONLY_RE = re.compile(
    r"^(?:in|auf|en|em)\s+[\w-]+"
    r"(?:\s+(?:please|bitte|por\s+favor))?[.!?]?$",
    re.IGNORECASE,
)
_RECALL_GERMAN_REPROMPT_RE = re.compile(
    r"^\s*(?:bitte\s+)?(?:frag|frage|wiederhol|wiederhole|stell)\b"
    r"(?=[^.!?]*(?:mich|frage|aufgabe|nochmal|noch einmal|deutsch|englisch))",
    re.IGNORECASE,
)
_RECALL_QUESTION_PUNCT_RE = re.compile(r"[?\u00bf\u061f\uff1f]")
_RECALL_ANSWER_CLAIM_RE = re.compile(
    r"\b(?:the\s+)?answer\s+(?:is|=)|\bconfidence\b|(?<!\w)[A-D][.)]\s+\w+",
    re.IGNORECASE,
)
_HEPH_SELF_RE = re.compile(
    r"\b(?:"
    r"heph|hephaistos|this\s+(?:tool|app|cli)|you|yourself|your\s+commands?|"
    r"armory|armories|autopilot|guided\s+mode|manual\s+mode|model\s+picker|"
    r"login|privacy|diagnostics|settings"
    r")\b",
    re.IGNORECASE,
)
_HEPH_SELF_INTENT_RE = re.compile(
    r"\b(?:"
    r"what\s+can|what\s+do|who\s+are|how\s+(?:do|can|should)|help|commands?|"
    r"use|work|switch|change|configure|set\s+up|turn\s+(?:on|off)|explain"
    r")\b",
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
_PRODUCT_HELP_RE = re.compile(
    r"\b(?:"
    r"what can i use (?:this|hephaistos) for|"
    r"what can you do|"
    r"how can you help|"
    r"what do you do"
    r")\b",
    re.IGNORECASE,
)
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
    r"translate (?:the )?(?:answer|solution)|"
    r"reveal(?: the)?(?: answer| solution)?|"
    r"explain again|full answer|full solution"
    r")\b",
    re.IGNORECASE,
)
_SHORT_REVEAL_RE = re.compile(r"^(?:answer|solution)\s*(?:please|\?)?$", re.IGNORECASE)
_HINT_RE = re.compile(r"\b(?:hint|nudge|clue)\b", re.IGNORECASE)
_TOO_HARD_RE = re.compile(
    r"\b(?:too hard|too difficult|easier|simpler|not sure|unsure|not prepared|"
    r"i don'?t know|dunno|no idea|lost|stuck|can'?t answer|cannot answer)\b",
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
    r"using (?:the )?indexed (?:source|sources|materials?|documents?)|"
    r"from (?:the )?(?:source|sources|materials?)|"
    r"from (?:the )?indexed (?:source|sources|materials?|documents?)|"
    r"according to (?:the )?(?:source|sources|materials?)|"
    r"according to (?:the )?indexed (?:source|sources|materials?|documents?)|"
    r"answer with (?:just )?(?:the )?exact|"
    r"exact phrase|exact wording"
    r")\b",
    re.IGNORECASE,
)
_ASSESS_PREFIX_RE = re.compile(r"^\s*(CORRECT|PARTIAL|WRONG)\s*[:\-]?\s*", re.IGNORECASE)
_CONFIDENCE_RE = re.compile(
    r"\b(?:confidence|confident|sure)(?:\s+is)?\s*[:=]?\s*"
    r"(?P<value>\d+(?:[.]\d+)?)\s*"
    r"(?P<unit>%|/10|/5)?(?=\s|[.,;:!?]|$)",
    re.IGNORECASE,
)
_MAX_AUTOPILOT_TURNS = 24


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
    stated_confidence: float | None = None
    autonomy_mode: StudyAutonomyMode = StudyAutonomyMode.GUIDED
    study_move: StudyMove | None = None


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


def _is_light_chat_request(user_input: str) -> bool:
    text = _normalize(user_input)
    return bool(
        _GREETING_RE.fullmatch(text) or _THANKS_RE.fullmatch(text) or _PRODUCT_HELP_RE.search(text)
    )


def _direct_chat_reply(user_input: str) -> str | None:
    text = _normalize(user_input)
    if _GREETING_RE.fullmatch(text):
        return "Hey. I can run material-backed study with /exam, /priority, or /autopilot on."
    if _PRODUCT_HELP_RE.search(text):
        return (
            "Use Hephaistos to study your own materials: ask a source-backed question, "
            "run /exam for active recall, run /priority for a plan, or /autopilot on "
            "to let Heph drive the session."
        )
    if _THANKS_RE.fullmatch(text):
        return "You're welcome."
    return None


def _is_overview_request(text: str) -> bool:
    return bool(OVERVIEW_REQUEST_RE.search(_normalize(text)))


def _is_reveal_request(text: str) -> bool:
    return bool(_REVEAL_RE.search(text) or _SHORT_REVEAL_RE.fullmatch(text))


def _is_source_qa_request(text: str) -> bool:
    return bool(_SOURCE_QA_RE.search(_normalize(text)))


def _is_ready_signal(text: str) -> bool:
    return bool(_READY_RE.fullmatch(_normalize(text)))


def _is_waiting_procedure_request(text: str) -> bool:
    return bool(_WAITING_PROCEDURE_RE.fullmatch(_normalize(text)))


def _is_recall_clarification_request(text: str) -> bool:
    normalized = _normalize(text)
    has_question_punct = _RECALL_QUESTION_PUNCT_RE.search(normalized) is not None
    looks_like_answer_claim = _RECALL_ANSWER_CLAIM_RE.search(normalized) is not None
    return bool(
        _RECALL_CLARIFICATION_RE.search(normalized)
        or _RECALL_REPROMPT_RE.search(normalized)
        or _RECALL_SHORT_REPROMPT_RE.fullmatch(normalized)
        or _RECALL_LANGUAGE_ONLY_RE.fullmatch(normalized)
        or _RECALL_GERMAN_REPROMPT_RE.search(normalized)
        or (has_question_punct and not looks_like_answer_claim)
    )


def _is_heph_self_request(text: str) -> bool:
    normalized = _normalize(text)
    return bool(_HEPH_SELF_RE.search(normalized) and _HEPH_SELF_INTENT_RE.search(normalized))


def _material_request_plan(
    state: StudyState,
    user_input: str,
    *,
    phase: StudyPhase = StudyPhase.PRESENTING,
) -> StudyTurnPlan | None:
    """Return a material-backed plan for explicit new requests.

    This is used when the study loop is waiting for ``ready`` but the student
    asks a fresh material question instead. Those requests should restart
    evidence retrieval rather than falling through to the ready reminder.
    """
    text = _normalize(user_input)
    if "priorit" in text.lower():
        return StudyTurnPlan(
            action=StudyAction.PRIORITY,
            phase=phase,
            prompt=_priority_prompt(),
            retrieval_query="exam priority topics prerequisites past exams materials overview",
            allow_tools=False,
        )
    query = _derive_presentation_query(user_input, state)
    if _is_overview_request(query):
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_overview_prompt(query),
            retrieval_query=query,
            allow_tools=False,
            buffer_response=True,
        )
    if _is_source_qa_request(query):
        return StudyTurnPlan(
            action=StudyAction.SOURCE_QA,
            phase=StudyPhase.PRESENTING,
            prompt=_source_qa_prompt(query),
            retrieval_query=query,
            allow_tools=False,
            buffer_response=True,
        )
    return None


def _calibration_prompt() -> str:
    return (
        "Controlled study state machine. Execute CALIBRATE.\n"
        "Rules:\n"
        "- Use the retrieved material to ask exactly one diagnostic recall question.\n"
        "- The question must be grounded in at least one retrieved source span, "
        "past-exam pattern, rubric point, or mark-scheme point.\n"
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
        "- Internally preserve the source grounding for later assessment; never invent "
        "unsupported questions from general model knowledge.\n"
        "- End with exactly: Answer from memory, or say easier or review material.\n"
        "- If no retrieved source material is available, ask which material or topic "
        "to start with."
    )


def _priority_prompt() -> str:
    return (
        "Controlled study state machine. Execute PRIORITY.\n"
        "Rules:\n"
        "- Analyze the retrieved materials and past exams only.\n"
        "- Identify the highest-priority topics by recurrence, exam weighting signals, "
        "and prerequisite value.\n"
        "- Separate direct evidence from inference. Cite evidence IDs for direct claims.\n"
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


def _overview_prompt(query: str) -> str:
    return (
        "Controlled study state machine. Execute MATERIAL_OVERVIEW.\n"
        f"User request: {query}\n"
        "Rules:\n"
        "- Treat the retrieved evidence as a sample across the enabled corpus, not as the "
        "entire corpus.\n"
        "- Identify the subject, document types, and major topic clusters only from cited "
        "evidence.\n"
        "- Mention whether the evidence appears to include lectures, exercises, exams, "
        "notes, or other document roles when the evidence supports it.\n"
        "- Do not infer from filenames, lecturer names, language, institution, or outside "
        "knowledge.\n"
        "- If the retrieved sample is too thin to summarize the whole corpus, say what is "
        "covered by the sample and what remains uncertain.\n"
        "- Synthesize the material in your own words. Do not paste long source excerpts; quote "
        "only short exact wording when it materially helps the answer.\n"
        "- Include at least two concise bullet lines, and cite each bullet with evidence IDs.\n"
        "- Cite at least two distinct evidence sources when the retrieved evidence provides "
        "them.\n"
        "- Be explicit about whether the answer is a sampled orientation or a complete "
        "corpus-level conclusion.\n"
        "- Cite evidence IDs for every factual claim.\n"
        "- Do not ask a recall question.\n"
        "- Do not end with readiness, drill, or study-loop instructions."
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


def _manual_chat_prompt(query: str) -> str:
    return (
        "HEPH chat mode.\n"
        f"User request: {query}\n"
        "Rules:\n"
        "- Behave like a normal conversational assistant with access to the current "
        "armory's memory and materials.\n"
        "- Use retrieved armory evidence when it is relevant, and cite evidence IDs for "
        "claims based on the armory.\n"
        "- You may supplement with general knowledge when the user is not asking for a "
        "source-only or armory-only answer; clearly separate general knowledge from "
        "armory-backed claims.\n"
        "- Do not force a ready/recall loop, require confidence, or turn the exchange "
        "into a quiz unless the user explicitly asks.\n"
        "- If the user asks for study help, answer helpfully and let the user choose "
        "whether to drill, review, or continue chatting."
    )


def _heph_self_prompt(query: str) -> str:
    return (
        "HEPH self-help mode.\n"
        f"User request: {query}\n"
        "Rules:\n"
        "- Answer as Hephaistos about Hephaistos: the local-first study CLI, armories, "
        "materials, chat, source-grounded answers, active recall, /priority, /exam, "
        "/autopilot, /manual, /guided, /models, /login, /settings, privacy, and diagnostics.\n"
        "- Do not treat the user message as a recall attempt, even during an active drill.\n"
        "- Do not grade the learner, require confidence, or reveal any active study answer.\n"
        "- Do not use armory material, citations, retrieved evidence, or tool output.\n"
        "- If the request is outside what Hephaistos can do, say so and point to /help or "
        "the relevant slash command.\n"
        "- Keep the answer concise and practical."
    )


def _autopilot_calibration_prompt(query: str, state: StudyState) -> str:
    goal = state.session_goal or "autonomous study"
    session_type = state.autopilot_session_type or "general"
    return (
        "HEPH AUTOPILOT calibration.\n"
        f"Session type (internal): {session_type}\n"
        f"Session goal (internal, do not restate): {goal}\n"
        f"User request: {query}\n"
        "Rules:\n"
        "- Do not explain Autopilot or print internal planning labels.\n"
        "- Start directly with the learner-facing task.\n"
        "- Use the retrieved source material to ask exactly one diagnostic recall, "
        "prediction, application, or comparison question.\n"
        "- The question must test understanding, not document metadata.\n"
        "- Do not reveal the answer, method, answer key, source IDs, or citations.\n"
        "- Require the learner to answer from memory and include confidence from 0-100%.\n"
        "- If source material is unavailable or too thin, ask the smallest necessary "
        "clarifying question instead of inventing a task.\n"
        "- End with exactly: Your turn: answer from memory and give confidence from 0-100%."
    )


def _source_followup_prompt(item: str, user_input: str) -> str:
    return (
        "Controlled study state machine. Execute SOURCE_FOLLOWUP.\n"
        f"Current material focus: {item}\n"
        f"Student follow-up: {user_input}\n"
        "Rules:\n"
        "- Treat the follow-up as a real source-backed question or reaction, not as a "
        "readiness signal and not as a recall attempt.\n"
        "- Use the stored or retrieved material evidence before answering.\n"
        "- If the follow-up is an acknowledgement such as 'interesting', explain one "
        "specific source-backed reason the material is interesting or important.\n"
        "- If the follow-up asks why, answer the why-question directly from the evidence.\n"
        "- Cite evidence IDs for source-backed claims.\n"
        "- Do not assess the student.\n"
        "- Do not ask a recall question.\n"
        "- Do not end with readiness, drill, or study-loop instructions."
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


def _recall_clarification_prompt(item: str, request: str) -> str:
    return (
        "Controlled study state machine. Execute RECALL_CLARIFICATION.\n"
        f"Current item: {item}\n"
        f"Student request: {request}\n"
        "Rules:\n"
        "- The student is asking what to answer, not attempting the answer.\n"
        "- If the student asks to repeat, rephrase, translate, or use a language, honor "
        "that request for the prompt only.\n"
        "- Restate what they should recall from memory without revealing the solution.\n"
        "- Do not assess the student.\n"
        "- Do not include answer content, grading, scores, or correctness labels.\n"
        "- Keep it to one or two short sentences."
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


def _hint_prompt(item: str, hint_level: int) -> str:
    bounded_level = min(5, max(1, hint_level))
    level_instruction = {
        1: "- Give exactly one orienting hint.",
        2: "- Give exactly one relevant definition or formula hint.",
        3: "- Give exactly one next-step procedural hint.",
        4: "- Give exactly one partial worked step.",
        5: "- Give the strongest scaffold that still leaves the learner to complete the answer.",
    }[bounded_level]
    leakage_rule = (
        "- Do not reveal later steps or the full answer."
        if bounded_level < 5
        else "- This is the final ladder level; do not state the final answer directly."
    )
    return (
        "Controlled study state machine. Execute HINT.\n"
        f"Current item: {item}\n"
        f"Hint level: {bounded_level}\n"
        "Rules:\n"
        "- Use only the stored material context for this item.\n"
        f"{level_instruction}\n"
        f"{leakage_rule}\n"
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
        "- Ground the easier question in a retrieved source span, past-exam pattern, "
        "rubric point, or mark-scheme point.\n"
        "- Ask exactly one easier prerequisite recall question.\n"
        "- The question must test understanding — not document titles, author names, "
        "dates, page numbers, file names, headings, or other surface metadata.\n"
        "- Do not reveal the answer to either question.\n"
        "- Do not invent prerequisite questions from general model knowledge.\n"
        "- End with exactly: Answer from memory, or say review material.\n"
        "- If no grounded material context is available, say no easier grounded question "
        "is available."
    )


def _autopilot_scaffold_prompt(item: str) -> str:
    return (
        "HEPH AUTOPILOT scaffold step.\n"
        f"Previous item: {item}\n"
        "Rules:\n"
        "- The learner signaled that they are not ready or not sure.\n"
        "- Do not grade the learner and do not mark the attempt wrong.\n"
        "- Use only the stored material context for this item.\n"
        "- Give the smallest useful scaffold: a sentence starter, one partial setup, "
        "or a 1-3 blank fill-the-gaps prompt.\n"
        "- Keep the full answer hidden; reveal only enough structure for the learner "
        "to make a real next attempt.\n"
        "- Ground the scaffold in a retrieved source span, past-exam pattern, rubric "
        "point, or mark-scheme point.\n"
        "- Ask exactly one easier action the learner can complete now.\n"
        "- End with exactly: Fill the gap or continue the starter, then give confidence "
        "from 0-100%.\n"
        "- If no grounded material context is available, say no grounded scaffold is "
        "available and ask which subtopic to review first."
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
        "- Treat retrieved material, rubrics, mark schemes, and past-exam patterns as "
        "the source of truth. General model knowledge may only clarify wording; it "
        "must not add expected points or override the material.\n"
        "- Start the reply with exactly one label: CORRECT:, PARTIAL:, or WRONG:.\n"
        "- After the label, use this compact structure when evidence is available:\n"
        "  Score: <earned>/<available or expected points>.\n"
        "  Got: <source-backed points the student included>.\n"
        "  Missing: <rubric/source-backed points still needed>.\n"
        "  Misconception: <incorrect idea and why the source contradicts it, or none>.\n"
        "  Correction: <minimal source-backed correction with evidence IDs>.\n"
        "  Try again: <one next retrieval prompt>.\n"
        "  Confidence: <whether the student's confidence seems calibrated, if stated>.\n"
        "- CORRECT: keep the structure brief and do not restate a full solution.\n"
        "- PARTIAL: identify missing source-backed points without revealing unrelated "
        "extra material.\n"
        "- WRONG: correct the misconception or first wrong step immediately, then give "
        "one focused retrieval prompt. Do not let the student continue with a false idea.\n"
        "- Cite evidence IDs for rubric points, missing points, misconceptions, and "
        "corrections whenever IDs are available.\n"
        "- If the uploaded material does not contain enough evidence to assess "
        "confidently, say so clearly and default to PARTIAL:.\n"
        "- Be factual and direct. No praise. No generic encouragement.\n"
        "- If material evidence is missing, default to PARTIAL: "
        "and say grounded assessment is unavailable."
    )


def plan_turn(
    state: StudyState,
    user_input: str,
    *,
    due_reviews: tuple[ReviewItem, ...] = (),
    memory_state: MemoryState | None = None,
    allow_direct_chat: bool = True,
) -> StudyTurnPlan:
    """Return the deterministic handling plan plus autonomy policy metadata."""
    effective_memory = memory_state if memory_state is not None else MemoryState()
    bounded_plan = _autopilot_stop_plan(
        state,
        due_reviews=due_reviews,
        memory_state=effective_memory,
    )
    if bounded_plan is not None:
        return bounded_plan
    plan = _plan_turn_mode_aware(state, user_input, allow_direct_chat=allow_direct_chat)
    mode = infer_turn_mode(state, user_input)
    move = move_for_plan(
        plan.action,
        state,
        user_input,
        due_reviews=due_reviews,
        memory_state=effective_memory,
    )
    prompt = append_policy_prompt(
        plan.prompt,
        mode=mode,
        move=move,
        action=plan.action,
    )
    allow_tools = (
        plan.allow_tools
        and state.autonomy_mode is not StudyAutonomyMode.AUTOPILOT
        and mode is not StudyAutonomyMode.AUTOPILOT
    )
    return replace(
        plan,
        prompt=prompt,
        allow_tools=allow_tools,
        autonomy_mode=mode,
        study_move=move,
    )


def _plan_turn_mode_aware(
    state: StudyState,
    user_input: str,
    *,
    allow_direct_chat: bool,
) -> StudyTurnPlan:
    mode = infer_turn_mode(state, user_input)
    if mode is StudyAutonomyMode.MANUAL:
        return _plan_turn_manual(state, user_input)
    if mode is StudyAutonomyMode.AUTOPILOT:
        return _plan_turn_autopilot(state, user_input, allow_direct_chat=allow_direct_chat)
    return _plan_turn_base(state, user_input, allow_direct_chat=allow_direct_chat)


def _autopilot_stop_plan(
    state: StudyState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> StudyTurnPlan | None:
    if state.autonomy_mode is not StudyAutonomyMode.AUTOPILOT:
        return None
    reason = _autopilot_stop_reason(
        state,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    if not reason:
        return None
    reply = (
        f"Autopilot session complete: {reason}. "
        "Next useful step: review the scheduled weak items or start a new bounded session."
    )
    return StudyTurnPlan(
        action=StudyAction.CHAT,
        phase=state.phase,
        prompt="",
        allow_tools=False,
        direct_reply=reply,
        autonomy_mode=StudyAutonomyMode.AUTOPILOT,
    )


def _autopilot_stop_reason(
    state: StudyState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
    now: datetime | None = None,
) -> str:
    if state.autopilot_turns >= _MAX_AUTOPILOT_TURNS:
        return "maximum turn budget reached"
    if state.autopilot_stop_reason:
        return state.autopilot_stop_reason
    if state.time_budget_minutes is None or state.autopilot_started_at is None:
        session_type = state.autopilot_session_type.casefold()
        if session_type == "review" and state.autopilot_turns > 0 and not due_reviews:
            return "due cards completed"
        if (
            session_type in {"exam", "cram"}
            and state.autopilot_turns >= 6
            and not due_reviews
            and not memory_state.weak_topics
        ):
            return "exam plan completed"
        if (
            state.autopilot_turns >= 4
            and not due_reviews
            and not memory_state.weak_topics
            and not memory_state.misconceptions
        ):
            return "mastery target reached"
        if (
            state.last_feedback_type in {StudyFeedbackType.WRONG, StudyFeedbackType.PARTIAL}
            and state.hint_level >= 4
        ):
            return "learner fatigue or frustration detected"
        return ""
    current_time = now or datetime.now(UTC)
    started = state.autopilot_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    if current_time - started >= timedelta(minutes=state.time_budget_minutes):
        return "time budget reached"
    session_type = state.autopilot_session_type.casefold()
    if session_type == "review" and state.autopilot_turns > 0 and not due_reviews:
        return "due cards completed"
    if (
        session_type in {"exam", "cram"}
        and state.autopilot_turns >= 6
        and not due_reviews
        and not memory_state.weak_topics
    ):
        return "exam plan completed"
    if (
        state.autopilot_turns >= 4
        and not due_reviews
        and not memory_state.weak_topics
        and not memory_state.misconceptions
    ):
        return "mastery target reached"
    if (
        state.last_feedback_type in {StudyFeedbackType.WRONG, StudyFeedbackType.PARTIAL}
        and state.hint_level >= 4
    ):
        return "learner fatigue or frustration detected"
    return ""


def _plan_turn_manual(state: StudyState, user_input: str) -> StudyTurnPlan:
    """Manual mode answers direct requests without enrolling the user in a loop."""
    text = _normalize(user_input)
    if "priorit" in text.lower():
        return StudyTurnPlan(
            action=StudyAction.PRIORITY,
            phase=state.phase,
            prompt=_priority_prompt(),
            retrieval_query="exam priority topics prerequisites past exams materials overview",
            allow_tools=False,
        )
    if _needs_initial_calibration(user_input):
        return StudyTurnPlan(
            action=StudyAction.CALIBRATE,
            phase=StudyPhase.RECALL,
            prompt=_calibration_prompt(),
            allow_tools=False,
            buffer_response=True,
        )

    if _is_light_chat_request(user_input):
        return StudyTurnPlan(
            action=StudyAction.CHAT,
            phase=StudyPhase.PRESENTING,
            prompt=_manual_chat_prompt(text),
            allow_tools=False,
        )

    query = _derive_presentation_query(user_input, state)
    if _is_source_qa_request(query):
        return StudyTurnPlan(
            action=StudyAction.SOURCE_QA,
            phase=StudyPhase.PRESENTING,
            prompt=_source_qa_prompt(query),
            retrieval_query=query,
            allow_tools=False,
            buffer_response=True,
        )
    return StudyTurnPlan(
        action=StudyAction.CHAT,
        phase=StudyPhase.PRESENTING,
        prompt=_manual_chat_prompt(query),
        retrieval_query=query,
        allow_tools=True,
    )


def _plan_turn_autopilot(
    state: StudyState,
    user_input: str,
    *,
    allow_direct_chat: bool,
) -> StudyTurnPlan:
    """Autopilot chooses the next learning action instead of presenting passively."""
    if state.current_item:
        return _plan_turn_base(state, user_input, allow_direct_chat=allow_direct_chat)

    text = _normalize(user_input)
    direct_reply = _direct_chat_reply(user_input) if allow_direct_chat else None
    if (
        direct_reply is None
        and not allow_direct_chat
        and _is_light_chat_request(user_input)
        and not _is_simple_greeting(user_input)
    ):
        return StudyTurnPlan(
            action=StudyAction.CHAT,
            phase=StudyPhase.PRESENTING,
            prompt=_manual_chat_prompt(text),
            allow_tools=False,
        )
    if direct_reply is not None and not _is_simple_greeting(user_input):
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

    query = _derive_presentation_query(user_input, state)
    if _is_overview_request(query):
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_overview_prompt(query),
            retrieval_query=query,
            allow_tools=False,
            buffer_response=True,
        )
    if _is_source_qa_request(query):
        return StudyTurnPlan(
            action=StudyAction.SOURCE_QA,
            phase=StudyPhase.PRESENTING,
            prompt=_source_qa_prompt(query),
            retrieval_query=query,
            allow_tools=False,
            buffer_response=True,
        )

    retrieval_query = (
        None if _is_autopilot_bootstrap(query) or _needs_initial_calibration(query) else query
    )
    return StudyTurnPlan(
        action=StudyAction.CALIBRATE,
        phase=StudyPhase.RECALL,
        prompt=_autopilot_calibration_prompt(query, state),
        retrieval_query=retrieval_query,
        allow_tools=False,
        buffer_response=True,
    )


def _is_autopilot_bootstrap(text: str) -> bool:
    normalized = _normalize(text).casefold()
    return normalized.startswith("start ") and " autopilot study session" in normalized


def _plan_turn_base(
    state: StudyState,
    user_input: str,
    *,
    allow_direct_chat: bool = True,
) -> StudyTurnPlan:
    """Return the deterministic handling plan for one user turn."""
    text = _normalize(user_input)

    if not state.current_item:
        if not allow_direct_chat and _is_light_chat_request(user_input):
            return StudyTurnPlan(
                action=StudyAction.CHAT,
                phase=StudyPhase.PRESENTING,
                prompt=_manual_chat_prompt(text),
                allow_tools=False,
            )
        direct_reply = _direct_chat_reply(user_input) if allow_direct_chat else None
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
        if _is_heph_self_request(text):
            return StudyTurnPlan(
                action=StudyAction.CHAT,
                phase=state.phase,
                prompt=_heph_self_prompt(text),
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
        is_overview = _is_overview_request(query)
        if is_overview:
            return StudyTurnPlan(
                action=StudyAction.PRESENT,
                phase=StudyPhase.PRESENTING,
                prompt=_overview_prompt(query),
                retrieval_query=query,
                allow_tools=False,
                buffer_response=True,
            )
        if _is_source_qa_request(query):
            return StudyTurnPlan(
                action=StudyAction.SOURCE_QA,
                phase=StudyPhase.PRESENTING,
                prompt=_source_qa_prompt(query),
                retrieval_query=query,
                allow_tools=False,
                buffer_response=True,
            )
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_overview_prompt(query) if is_overview else _present_prompt(query),
            retrieval_query=query,
            allow_tools=not is_overview,
            buffer_response=is_overview,
        )

    if _SKIP_RE.search(text):
        query = _derive_presentation_query(user_input, state)
        is_overview = _is_overview_request(query)
        return StudyTurnPlan(
            action=StudyAction.PRESENT,
            phase=StudyPhase.PRESENTING,
            prompt=_overview_prompt(query) if is_overview else _present_prompt(query),
            retrieval_query=query,
            allow_tools=not is_overview,
            buffer_response=is_overview,
        )

    if state.phase == StudyPhase.WAITING_FOR_READY:
        if material_plan := _material_request_plan(state, user_input):
            return material_plan
        if _is_ready_signal(text):
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
        if not _is_waiting_procedure_request(text):
            return StudyTurnPlan(
                action=StudyAction.REVIEW,
                phase=StudyPhase.PRESENTING,
                prompt=_source_followup_prompt(state.current_item, user_input),
                retrieval_query=state.retrieval_query or state.current_item,
                use_expected_source_refs=True,
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
        if _is_heph_self_request(text):
            return StudyTurnPlan(
                action=StudyAction.CHAT,
                phase=StudyPhase.RECALL,
                prompt=_heph_self_prompt(text),
                allow_tools=False,
            )
        if _is_recall_clarification_request(text):
            return StudyTurnPlan(
                action=StudyAction.PROMPT_RECALL,
                phase=StudyPhase.RECALL,
                prompt=_recall_clarification_prompt(state.current_item, text),
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
            prompt = (
                _autopilot_scaffold_prompt(state.current_item)
                if state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
                else _simplify_prompt(state.current_item)
            )
            return StudyTurnPlan(
                action=StudyAction.SIMPLIFY,
                phase=StudyPhase.RECALL,
                prompt=prompt,
                retrieval_query=state.retrieval_query or state.current_item,
                use_expected_source_refs=True,
                allow_tools=False,
            )
        if _HINT_RE.search(text) and state.attempt_count > 0:
            return StudyTurnPlan(
                action=StudyAction.HINT,
                phase=StudyPhase.ASSESS,
                prompt=_hint_prompt(state.current_item, state.hint_level + 1),
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
            stated_confidence=_parse_stated_confidence(text),
        )

    query = _derive_presentation_query(user_input, state)
    is_overview = _is_overview_request(query)
    return StudyTurnPlan(
        action=StudyAction.PRESENT,
        phase=StudyPhase.PRESENTING,
        prompt=_overview_prompt(query) if is_overview else _present_prompt(query),
        retrieval_query=query,
        allow_tools=not is_overview,
        buffer_response=is_overview,
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


def _parse_stated_confidence(text: str) -> float | None:
    match = _CONFIDENCE_RE.search(text)
    if match is None:
        return None
    raw_value = float(match.group("value"))
    unit = match.group("unit") or ""
    return normalize_confidence_value(raw_value, unit)


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
    if state.autonomy_mode is StudyAutonomyMode.AUTOPILOT and plan.action is not StudyAction.CHAT:
        next_state.autopilot_turns = state.autopilot_turns + 1

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
            next_state.hint_level = 0
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
            next_state.recall_started_at = None
            next_state.hint_level = 0
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
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
            next_state.hint_level = 0
        else:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.attempt_count = 0
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
            next_state.recall_started_at = None
            next_state.hint_level = 0
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
        return next_state, reply

    if plan.action is StudyAction.PROMPT_RECALL:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.READY
        next_state.recall_started_at = current_time
        next_state.last_recall_seconds = None
        next_state.last_recall_rating = StudyRecallRating.NONE
        next_state.hint_level = 0
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
        next_state.hint_level = min(5, state.hint_level + 1)
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
            next_state.hint_level = min(5, state.hint_level + 1)
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
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
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
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
        next_state.last_confidence = plan.stated_confidence
        if feedback is StudyFeedbackType.CORRECT:
            next_state.phase = StudyPhase.PRESENTING
            next_state.current_item = ""
            next_state.retrieval_query = ""
            next_state.expected_source_refs = []
            next_state.recall_started_at = None
            next_state.hint_level = 0
        else:
            next_state.phase = StudyPhase.RECALL
            next_state.recall_started_at = current_time
            if (
                feedback is StudyFeedbackType.WRONG
                and state.hint_level >= 4
                and state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
            ):
                _set_autopilot_stop_reason(next_state, "learner fatigue or frustration detected")
        if not source_refs:
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
        return next_state, cleaned_reply

    return next_state, reply


def _set_autopilot_stop_reason(state: StudyState, reason: str) -> None:
    if state.autonomy_mode is not StudyAutonomyMode.AUTOPILOT:
        return
    if state.autopilot_stop_reason:
        return
    state.autopilot_stop_reason = reason
