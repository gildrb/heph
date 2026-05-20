"""Deterministic controller for the recall-loop state machine."""

from __future__ import annotations

import re
from collections.abc import Callable
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
from hephaistos.study.intent import (
    is_material_source_request,
    is_new_material_topic_request,
    is_source_only_policy,
    is_standalone_source_only_policy,
    material_drill_query,
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

type TurnResult = tuple[StudyState, str]
type TurnResultHandler = Callable[
    [StudyState, StudyState, StudyTurnPlan, str, list[str], datetime],
    TurnResult,
]

_SAME_LANGUAGE_USER_RULE = "- Answer in the same language as the user's request when clear.\n"
_SAME_LANGUAGE_REQUEST_RULE = "- Answer in the same language as the user's request.\n"
_SAME_LANGUAGE_ITEM_RULE = (
    "- Answer in the same language as the current item or the user's recent request when clear.\n"
)
_NO_ENGLISH_READY_RULE = (
    "- Do not require a specific English word such as `ready` when the user wrote "
    "in another language.\n"
)
_NO_ENGLISH_CLOSING_RULE = (
    "- Do not hard-code an English closing instruction when the user wrote in another language.\n"
)
_NO_ENGLISH_RECALL_RULE = (
    "- Do not hard-code an English recall sentence when the study exchange is in "
    "another language.\n"
)
_NO_ASSESS_USER_RULE = "- Do not assess the user.\n"
_NO_RECALL_QUESTION_RULE = "- Do not ask a recall question.\n"
_NO_RECALL_LOOP_END_RULE = "- Do not end with readiness, drill, or recall-loop instructions.\n"
_STORED_MATERIAL_CONTEXT_RULE = "- Use only the stored material context for this item.\n"
_PRIORITY_RETRIEVAL_QUERY = "exam priority topics prerequisites past exams materials overview"

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
    r"not ready(?: yet)?|not yet|wait|wait for now|wait a minute|"
    r"later(?: please)?|hold on(?: a (?:sec|second|minute))?|"
    r"give me a minute|one sec(?:ond)?|pause|"
    r"i\s*(?:am|'m|m)?\s+not\s+ready(?: yet)?|"
    r"no"
    r")[.!?]?$",
    re.IGNORECASE,
)
_RECALL_CLARIFICATION_RE = re.compile(
    r"\b(?:"
    r"which (?:answer|question|one)|"
    r"explain (?:the )?(?:question|prompt)(?: again)?|"
    r"what (?:answer|question|do you want|should i answer|am i answering)|"
    r"answer what|"
    r"(?:do not|don'?t) guess|"
    r"let'?s do (?:this|that|it)(?: again)?|"
    r"repeat (?:the )?(?:question|prompt)|"
    r"say (?:the )?(?:question|prompt) again"
    r")\b",
    re.IGNORECASE,
)
_RECALL_REPROMPT_RE = re.compile(
    r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
    r"(?:ask|repeat|restate|rephrase|say|read|write|translate)\b"
    r"(?=[^.!?]*(?:again|once more|one more time|question|prompt|item|task|exercise|"
    r"in\s+[\w-]+|language))",
    re.IGNORECASE,
)
_RECALL_SHORT_REPROMPT_RE = re.compile(
    r"^(?:again|once more|one more time)"
    r"(?:\s+in\s+[\w-]+)?"
    r"(?:\s+please)?[.!?]?$",
    re.IGNORECASE,
)
_RECALL_LANGUAGE_ONLY_RE = re.compile(
    r"^in\s+[\w-]+"
    r"(?:\s+please)?[.!?]?$",
    re.IGNORECASE,
)
_RECALL_QUESTION_PUNCT_RE = re.compile(r"[?\u00bf\u061f\uff1f]")
_RECALL_ANSWER_CLAIM_RE = re.compile(
    r"\b(?:the\s+)?answer\s+(?:is|=)|\bconfidence\b|(?<!\w)[A-D][.)]\s+\w+",
    re.IGNORECASE,
)
_RECALL_TENTATIVE_ANSWER_RE = re.compile(
    r"^\s*(?:"
    r"(?:is|are|was|were)\s+(?:it|this|that|the\s+answer)\s+\S.+|"
    r"(?:could|would|should|can)\s+(?:it|this|that|the\s+answer)\s+be\s+\S.+|"
    r"(?:maybe|perhaps|probably)\s+\S.+|"
    r"i\s+(?:think|guess|believe|would\s+say|suspect)\s+\S.+|"
    r"my\s+answer\s+(?:is|would\s+be)\s+\S.+"
    r")\s*[.?!]?\s*$",
    re.IGNORECASE,
)
_RECALL_SHORT_ANSWER_RE = re.compile(
    r"^\s*(?!(?:why|what|which|who|where|when|how|again|yes|no)\b)"
    r"(?:[A-D][.)]?|[\wÀ-ÖØ-öø-ÿ][\wÀ-ÖØ-öø-ÿ0-9_+*/=.,:;'\s-]{1,80})\?\s*$",
    re.IGNORECASE,
)
_HEPH_SELF_RE = re.compile(
    r"\b(?:"
    r"heph|hephaistos|this\s+(?:tool|app|cli)|yourself|your\s+commands?|"
    r"armory|armories|autopilot|guided\s+mode|manual\s+mode|model\s+picker|"
    r"login|privacy|diagnostics|settings"
    r")\b",
    re.IGNORECASE,
)
_HEPH_PRONOUN_SELF_REQUEST_RE = re.compile(
    r"\b(?:"
    r"what\s+can\s+you\s+do|"
    r"what\s+do\s+you\s+do|"
    r"who\s+are\s+you|"
    r"how\s+do\s+you\s+work|"
    r"how\s+can\s+you\s+help(?:\s+me)?|"
    r"how\s+(?:do|can|should)\s+(?:i|we)\s+(?:use|work\s+with)\s+you|"
    r"what\s+commands?\s+(?:can\s+i\s+use|do\s+you\s+have)|"
    r"show\s+me\s+your\s+commands?"
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
    r"i don'?t know|dunno|no idea|lost|stuck|can'?t answer|cannot answer|"
    r"i (?:do not|don'?t|cannot|can'?t) understand|i don'?t get (?:it|this)|"
    r"i(?: am|'m)? confused|confused|need help|help me)\b",
    re.IGNORECASE,
)
_RECALL_SCAFFOLD_RE = re.compile(
    r"\b(?:"
    r"(?:can|could|would)\s+you\s+(?:please\s+)?"
    r"(?:explain|walk\s+me\s+through|show\s+me\s+how\s+to\s+"
    r"(?:start|approach|think)|help\s+me\s+(?:start|approach|understand)|"
    r"break\s+(?:this|that|it)\s+down)|"
    r"(?:explain|walk\s+me\s+through)\s+(?:this|that|it|the\s+"
    r"(?:problem|item|exercise|concept))|"
    r"break\s+(?:this|that|it)\s+down|"
    r"break\s+down\s+(?:this|that|it|the\s+(?:problem|item|exercise|concept))|"
    r"why\s+(?:is|are|does|do|did)\s+(?:this|that|it|the\s+.{1,80})|"
    r"how\s+(?:do|should|can)\s+i\s+"
    r"(?:start|begin|approach|think\s+about|solve|work\s+through|answer)|"
    r"where\s+(?:do|should|can)\s+i\s+start|"
    r"what(?:'s|\s+is)\s+the\s+first\s+step|"
    r"show\s+me\s+how\s+to\s+start|"
    r"give\s+me\s+(?:a\s+)?(?:scaffold|starting\s+point)"
    r")\b",
    re.IGNORECASE,
)
_REVIEW_MATERIAL_RE = re.compile(
    r"\b(?:review|look at (?:the )?material|study (?:the )?material|"
    r"show (?:me )?(?:the )?material|teach me|walk me through)\b",
    re.IGNORECASE,
)
_ASSESS_PREFIX_RE = re.compile(r"^\s*(CORRECT|PARTIAL|WRONG)\s*[:\-]?\s*", re.IGNORECASE)
_ASSESS_SECTION_RE = re.compile(
    r"^(?:Score|Got|Missing|Misconception|Correction|Try again|Confidence):",
    re.IGNORECASE,
)
_CONFIDENCE_RE = re.compile(
    r"\b(?:confidence|confident|sure)(?:\s+is)?\s*[:=]?\s*"
    r"(?P<value>\d+(?:[.]\d+)?)\s*"
    r"(?P<unit>%|/10|/5)?(?=\s|[.,;:!?]|$)",
    re.IGNORECASE,
)
_ACTIVE_RECALL_QUESTION_CONTRACT = (
    "- Use only the provided source material; do not invent facts beyond normal wording "
    "or clarification.\n"
    "- Write learner-facing questions in the user's language while preserving source "
    "technical terms.\n"
    "- Make active-recall questions, not passive summaries.\n"
    "- Each question must ask exactly one thing.\n"
    "- Prefer conceptual distinctions, definitions, steps, trade-offs, and "
    "when/why questions.\n"
    "- Avoid trivia such as slide numbers, instructor names, copyright text, dates, "
    "and decorative examples.\n"
    "- When the material uses both an English term and a local-language technical term "
    "for the same concept, include both terms in the question.\n"
    "- Keep expected answers concise but exam-useful.\n"
    "- If a generated question schema includes a source field, set it exactly to the "
    "provided canonical source label; do not substitute filenames, chunk IDs, dates, "
    "or instructor metadata."
)
_MAX_AUTOPILOT_TURNS = 24


@dataclass(frozen=True, slots=True)
class StudyTurnPlan:
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
    return (
        material_drill_query(text) is not None
        or bool(_INITIAL_CALIBRATION_RE.fullmatch(text))
        or bool(
            re.fullmatch(
                r"(?:can|could|would) you ask me .*question.*\??",
                text,
                re.IGNORECASE,
            )
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
            "Use Heph to study your own materials: ask a source-grounded question, "
            "run /exam for active recall, run /priority for a plan, or /autopilot on "
            "to let Heph drive the session."
        )
    if is_standalone_source_only_policy(text):
        return (
            "Understood. I will stick to enabled material and say when the sources "
            "are insufficient."
        )
    if _THANKS_RE.fullmatch(text):
        return "You're welcome."
    return None


def _is_overview_request(text: str) -> bool:
    return bool(OVERVIEW_REQUEST_RE.search(_normalize(text)))


def _is_reveal_request(text: str) -> bool:
    return bool(_REVEAL_RE.search(text) or _SHORT_REVEAL_RE.fullmatch(text))


def _is_recall_clarification_request(text: str) -> bool:
    normalized = _normalize(text)
    has_question_punct = _RECALL_QUESTION_PUNCT_RE.search(normalized) is not None
    looks_like_answer_claim = (
        _RECALL_ANSWER_CLAIM_RE.search(normalized) is not None
        or _RECALL_TENTATIVE_ANSWER_RE.fullmatch(normalized) is not None
        or _RECALL_SHORT_ANSWER_RE.fullmatch(normalized) is not None
    )
    return bool(
        is_source_only_policy(normalized)
        or _RECALL_CLARIFICATION_RE.search(normalized)
        or _RECALL_REPROMPT_RE.search(normalized)
        or _RECALL_SHORT_REPROMPT_RE.fullmatch(normalized)
        or _RECALL_LANGUAGE_ONLY_RE.fullmatch(normalized)
        or (has_question_punct and not looks_like_answer_claim)
    )


def _is_heph_self_request(text: str) -> bool:
    normalized = _normalize(text)
    return bool(
        _HEPH_PRONOUN_SELF_REQUEST_RE.search(normalized)
        or (_HEPH_SELF_RE.search(normalized) and _HEPH_SELF_INTENT_RE.search(normalized))
    )


def _is_recall_scaffold_request(text: str) -> bool:
    normalized = _normalize(text)
    if (
        _RECALL_CLARIFICATION_RE.search(normalized)
        or _RECALL_REPROMPT_RE.search(normalized)
        or _RECALL_SHORT_REPROMPT_RE.fullmatch(normalized)
        or _RECALL_LANGUAGE_ONLY_RE.fullmatch(normalized)
    ):
        return False
    return bool(_RECALL_SCAFFOLD_RE.search(normalized))


def _material_request_plan(
    state: StudyState,
    user_input: str,
    *,
    phase: StudyPhase = StudyPhase.PRESENTING,
) -> StudyTurnPlan | None:
    text = _normalize(user_input)
    if "priorit" in text.lower():
        return _priority_plan(user_input, phase=phase)
    if drill_query := material_drill_query(user_input):
        return material_topic_drill_plan(user_input, retrieval_query=drill_query)
    query = _derive_presentation_query(user_input, state)
    if _is_overview_request(query):
        return material_overview_plan(query)
    if is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    if is_new_material_topic_request(query):
        return material_topic_presentation_plan(query, retrieval_query=query)
    return None


def _calibration_prompt(*, user_request: str | None = None) -> str:
    request_line = ""
    if user_request:
        request_line = (
            "User request (language/topic signal; rules below override it): "
            f"{_normalize(user_request)}\n"
        )
    return (
        "Execute CALIBRATE.\n"
        f"{request_line}"
        "Rules:\n"
        "- Use the retrieved material to ask exactly one diagnostic recall question.\n"
        "- The question must be grounded in at least one retrieved source span, "
        "past-exam pattern, rubric point, or mark-scheme point.\n"
        "- The question must test understanding of a concept, procedure, or "
        "relationship from the material — not surface-level document metadata.\n"
        "Question quality contract:\n"
        f"{_ACTIVE_RECALL_QUESTION_CONTRACT}\n"
        "- FORBIDDEN question types (these never test knowledge):\n"
        "  * Titles of documents, chapters, sections, or slides.\n"
        "  * Author names, dates, or institutional affiliations.\n"
        "  * Page numbers, section numbers, or slide numbers.\n"
        "  * File names, folder names, or file paths.\n"
        "  * Headings or subheadings as standalone answers.\n"
        "- Instead, ask about definitions, cause-effect relationships, key steps "
        "in a procedure, comparisons between concepts, or applications of a "
        "principle.\n"
        "- Prefer an introductory, concrete item a first-time user can attempt.\n"
        "- If the user asked for an easy question, make it genuinely easy and "
        "prerequisite-level.\n"
        "- If the user asked for an exam-style or timed question, include one "
        "reasonable time limit and require them to reason their answer from memory.\n"
        "- Do not present the solution or method.\n"
        "- Do not include evidence IDs, citations, source labels, or answer-location hints "
        "in the question.\n"
        "- Internally preserve the source grounding for later assessment; never invent "
        "unsupported questions from general model knowledge.\n"
        "- End with one short learner-facing instruction in the user's language asking "
        "them to answer from memory, or ask for an easier question or material review.\n"
        f"{_NO_ENGLISH_CLOSING_RULE}"
        "- If no retrieved source material is available, ask which material or topic "
        "to start with."
    )


def _priority_prompt(user_request: str = "") -> str:
    request_line = f"User request: {user_request}\n" if user_request else ""
    return (
        "Execute PRIORITY.\n"
        f"{request_line}"
        "Rules:\n"
        f"{_SAME_LANGUAGE_USER_RULE}"
        "- Analyze the retrieved materials and past exams only.\n"
        "- Identify the highest-priority topics by recurrence, exam weighting signals, "
        "and prerequisite value.\n"
        "- Separate direct evidence from inference. Cite evidence IDs for direct claims.\n"
        "- Include missing prerequisites the user should review first.\n"
        f"{_NO_RECALL_QUESTION_RULE.rstrip()} and do not start an exam drill.\n"
        "- If the retrieved evidence is too thin to infer priorities, say so and list "
        "what materials are needed."
    )


def _priority_plan(user_input: str, *, phase: StudyPhase) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.PRIORITY,
        phase=phase,
        prompt=_priority_prompt(user_input),
        retrieval_query=_PRIORITY_RETRIEVAL_QUERY,
        allow_tools=False,
    )


def _direct_reply_plan(
    reply: str,
    *,
    phase: StudyPhase,
    autonomy_mode: StudyAutonomyMode = StudyAutonomyMode.GUIDED,
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.CHAT,
        phase=phase,
        prompt="",
        allow_tools=False,
        direct_reply=reply,
        autonomy_mode=autonomy_mode,
    )


def _chat_prompt_plan(prompt: str, *, phase: StudyPhase) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.CHAT,
        phase=phase,
        prompt=prompt,
        allow_tools=False,
    )


def _prompt_recall_plan(item: str) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.PROMPT_RECALL,
        phase=StudyPhase.RECALL,
        prompt=_recall_prompt(item),
        allow_tools=False,
    )


def _refuse_reveal_plan(item: str, *, phase: StudyPhase) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.REFUSE_REVEAL,
        phase=phase,
        prompt=_refusal_prompt(item),
        allow_tools=False,
    )


def _material_review_plan(
    prompt: str,
    retrieval_query: str,
    phase: StudyPhase = StudyPhase.PRESENTING,
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.REVIEW,
        phase=phase,
        prompt=prompt,
        retrieval_query=retrieval_query,
        use_expected_source_refs=True,
        allow_tools=False,
    )


def _present_query_plan(state: StudyState, user_input: str) -> StudyTurnPlan:
    query = _derive_presentation_query(user_input, state)
    if _is_overview_request(query):
        return material_overview_plan(query)
    return material_topic_presentation_plan(query, retrieval_query=query)


def _present_prompt(item: str, *, user_request: str | None = None) -> str:
    request_line = ""
    if user_request and _normalize(user_request) != _normalize(item):
        request_line = f"User request: {user_request}\n"
    return (
        "Execute the PRESENT phase.\n"
        f"Current item: {item}\n"
        f"{request_line}"
        "Rules:\n"
        f"{_SAME_LANGUAGE_REQUEST_RULE}"
        "- Use only the retrieved material for this item.\n"
        "- Present the complete solution or method once, concisely.\n"
        "- Cite evidence IDs whenever you state a factual step or value.\n"
        "- End with one short learner-facing instruction in the user's language asking "
        "them to signal when they are ready for recall.\n"
        f"{_NO_ENGLISH_READY_RULE}"
        "- If no retrieved source material is available, say no searchable armory "
        "evidence was found for this item. Do not answer from outside knowledge. "
        "Ask for a more specific material-backed prompt or for the material to be indexed.\n"
        "- Do not switch into assessment or extra tutoring."
    )


def _overview_prompt(query: str) -> str:
    return (
        "Execute MATERIAL_OVERVIEW.\n"
        f"User request: {query}\n"
        "Rules:\n"
        f"{_SAME_LANGUAGE_REQUEST_RULE}"
        "- Give the big picture first: domain, document types, major topic clusters, "
        "and how the topics relate.\n"
        "- Use only cited retrieved evidence. Do not infer from filenames, dates, "
        "semester labels, lecturers, institutions, language, or outside knowledge.\n"
        "- Avoid course administration metadata and do not explain retrieval sampling mechanics.\n"
        "- Synthesize in your own words. Do not paste long source excerpts; quote only "
        "short exact wording when useful.\n"
        "- Use at least two concise cited bullets when evidence supports them, and cite "
        "evidence IDs for every factual claim.\n"
        "- If evidence is thin, state only the supported subject and document roles; "
        "do not add a generic sampling or completeness disclaimer.\n"
        "- Do not end with readiness, drill, next-step, evidence-grounding-block, "
        "sample-scope, non-exhaustive list, or completeness caveats."
    )


def material_overview_plan(
    user_request: str,
    *,
    retrieval_query: str = "what is the material about",
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.PRESENT,
        phase=StudyPhase.PRESENTING,
        prompt=_overview_prompt(user_request),
        retrieval_query=retrieval_query,
        allow_tools=False,
        buffer_response=True,
    )


def material_topic_presentation_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> StudyTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return StudyTurnPlan(
        action=StudyAction.PRESENT,
        phase=StudyPhase.PRESENTING,
        prompt=_present_prompt(query, user_request=user_request),
        retrieval_query=query,
        allow_tools=True,
    )


def material_topic_drill_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> StudyTurnPlan:
    prompt = _calibration_prompt(user_request=user_request)
    if _EXAM_DRILL_RE.search(_normalize(user_request)):
        prompt = (
            f"{prompt}\n"
            "- This is an active-recall exam drill: do not show the result, answer key, "
            "rubric, source explanation, source IDs, or citations until after the user's "
            "attempt has been assessed."
        )
    return StudyTurnPlan(
        action=StudyAction.CALIBRATE,
        phase=StudyPhase.RECALL,
        prompt=prompt,
        retrieval_query=_normalize(retrieval_query) or None,
        allow_tools=False,
        buffer_response=True,
    )


def material_source_qa_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> StudyTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return StudyTurnPlan(
        action=StudyAction.SOURCE_QA,
        phase=StudyPhase.PRESENTING,
        prompt=_source_qa_prompt(query, user_request=user_request),
        retrieval_query=query,
        allow_tools=False,
        buffer_response=True,
    )


def recall_clarification_plan(
    user_request: str,
    *,
    current_item: str,
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.PROMPT_RECALL,
        phase=StudyPhase.RECALL,
        prompt=_recall_clarification_prompt(current_item, _normalize(user_request)),
        allow_tools=False,
    )


def manual_chat_plan(
    user_request: str,
    *,
    phase: StudyPhase = StudyPhase.PRESENTING,
) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.CHAT,
        phase=phase,
        prompt=_manual_chat_prompt(_normalize(user_request)),
        allow_tools=False,
    )


def _source_qa_prompt(query: str, *, user_request: str | None = None) -> str:
    request_line = ""
    if user_request and _normalize(user_request) != _normalize(query):
        request_line = f"User request: {user_request}\n"
    return (
        "Execute SOURCE_QA.\n"
        f"User question: {query}\n"
        f"{request_line}"
        "Rules:\n"
        f"{_SAME_LANGUAGE_REQUEST_RULE}"
        "- Answer the user's question directly using only the retrieved source material.\n"
        "- If the user asks for an exact phrase, quote only the exact phrase plus citations.\n"
        "- Cite evidence IDs for claims grounded in source material.\n"
        f"{_NO_RECALL_QUESTION_RULE}"
        f"{_NO_RECALL_LOOP_END_RULE}"
        "- If no retrieved source material answers the question, say that the armory sources "
        "do not contain the answer and ask for more specific material."
    )


def _manual_chat_prompt(query: str) -> str:
    return (
        "HEPH chat mode.\n"
        f"User request: {query}\n"
        "Rules:\n"
        f"{_SAME_LANGUAGE_USER_RULE}"
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
        f"{_SAME_LANGUAGE_USER_RULE}"
        "- Answer as Heph about Heph: the local document harness, armories, "
        "materials, chat, source-grounded answers, active recall, /priority, /exam, "
        "/autopilot, /manual, /guided, /models, /login, /settings, privacy, and diagnostics.\n"
        "- Do not treat the user message as a recall attempt, even during an active drill.\n"
        "- Do not grade the learner, require confidence, or reveal any active study answer.\n"
        "- Do not use armory material, citations, retrieved evidence, or tool output.\n"
        "- If the request is outside what Heph can do, say so and point to /help or "
        "the relevant slash command.\n"
        "- Keep the answer concise and practical."
    )


def _autopilot_calibration_prompt(query: str, state: StudyState) -> str:
    goal = state.session_goal or "guided material review"
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
        "Question quality contract:\n"
        f"{_ACTIVE_RECALL_QUESTION_CONTRACT}\n"
        "- Do not reveal the answer, method, answer key, source IDs, or citations.\n"
        "- Require the learner to answer from memory and include confidence from 0-100%.\n"
        "- If source material is unavailable or too thin, ask the smallest necessary "
        "clarifying question instead of inventing a task.\n"
        "- End with one short learner-facing instruction in the user's language asking them "
        "to answer from memory and give confidence from 0-100%.\n"
        "- Do not hard-code an English closing instruction when the user wrote in another "
        "language."
    )


def _source_followup_prompt(item: str, user_input: str) -> str:
    return (
        "Execute SOURCE_FOLLOWUP.\n"
        f"Current material focus: {item}\n"
        f"User follow-up: {user_input}\n"
        "Rules:\n"
        "- Answer in the same language as the user's follow-up when clear.\n"
        "- Treat the follow-up as a real question or reaction about the cited material, not as a "
        "readiness signal and not as a recall attempt.\n"
        "- Use the stored or retrieved material evidence before answering.\n"
        "- If the follow-up is an acknowledgement such as 'interesting', explain one "
        "specific reason grounded in the material for why it is interesting or important.\n"
        "- If the follow-up asks why, answer the why-question directly from the evidence.\n"
        "- Cite evidence IDs for claims grounded in source material.\n"
        f"{_NO_ASSESS_USER_RULE}"
        f"{_NO_RECALL_QUESTION_RULE}"
        f"{_NO_RECALL_LOOP_END_RULE.rstrip()}"
    )


def _waiting_prompt() -> str:
    return (
        "Execute WAITING_FOR_READY.\n"
        "Rules:\n"
        "- Do not reveal any more of the solution.\n"
        "- Tell the user, in their language when clear, to signal when they are ready "
        "for recall.\n"
        f"{_NO_ENGLISH_READY_RULE}"
        "- Keep it to one short sentence."
    )


def _recall_prompt(item: str) -> str:
    return (
        "Execute RECALL.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Do not answer the item.\n"
        "- Tell the user to reproduce the solution from memory now.\n"
        f"{_SAME_LANGUAGE_ITEM_RULE}"
        f"{_NO_ENGLISH_RECALL_RULE}"
        "- Keep it to one short sentence."
    )


def _recall_clarification_prompt(item: str, request: str) -> str:
    return (
        "Execute RECALL_CLARIFICATION.\n"
        f"Current item: {item}\n"
        f"User request: {request}\n"
        "Rules:\n"
        "- The user is asking what to answer, not attempting the answer.\n"
        "- If the user asks to repeat, rephrase, translate, or use a language, honor "
        "that request for the prompt only.\n"
        "- Restate what they should recall from memory without revealing the solution.\n"
        f"{_NO_ASSESS_USER_RULE}"
        "- Do not include answer content, grading, scores, or correctness labels.\n"
        "- Answer in the same language as the user's clarification request when clear.\n"
        "- Do not hard-code an English recall sentence when the user asked in another language.\n"
        "- Keep it to one or two short sentences."
    )


def _refusal_prompt(item: str) -> str:
    return (
        "Execute REFUSE_REVEAL.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- Do not reveal new solution content.\n"
        "- Briefly refuse and tell the user to attempt recall first.\n"
        f"{_SAME_LANGUAGE_ITEM_RULE}"
        "- Do not hard-code an English refusal when the study exchange is in another "
        "language.\n"
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
        "Execute HINT.\n"
        f"Current item: {item}\n"
        f"Hint level: {bounded_level}\n"
        "Rules:\n"
        f"{_STORED_MATERIAL_CONTEXT_RULE}"
        f"{level_instruction}\n"
        f"{leakage_rule}\n"
        "- If no grounded material context is available, say no grounded hint is available.\n"
        f"{_SAME_LANGUAGE_ITEM_RULE}"
        "- Do not hard-code an English hint when the study exchange is in another language.\n"
        "- Keep it to one short sentence."
    )


def _simplify_prompt(item: str) -> str:
    return (
        "Execute SIMPLIFY.\n"
        f"Previous item: {item}\n"
        "Rules:\n"
        "- The previous recall item was too hard.\n"
        f"{_STORED_MATERIAL_CONTEXT_RULE}"
        "- Ground the easier question in a retrieved source span, past-exam pattern, "
        "rubric point, or mark-scheme point.\n"
        "- Ask exactly one easier prerequisite recall question.\n"
        "Question quality contract:\n"
        f"{_ACTIVE_RECALL_QUESTION_CONTRACT}\n"
        "- The question must test understanding — not document titles, author names, "
        "dates, page numbers, file names, headings, or other surface metadata.\n"
        "- Do not reveal the answer to either question.\n"
        "- Do not invent prerequisite questions from general model knowledge.\n"
        "- End with one short learner-facing instruction in the same language as the question "
        "asking the user to answer from memory or ask to review material.\n"
        f"{_NO_ENGLISH_CLOSING_RULE}"
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
        f"{_STORED_MATERIAL_CONTEXT_RULE}"
        "- Give the smallest useful scaffold: a sentence starter, one partial setup, "
        "or a 1-3 blank fill-the-gaps prompt.\n"
        "- Keep the full answer hidden; reveal only enough structure for the learner "
        "to make a real next attempt.\n"
        "- Ground the scaffold in a retrieved source span, past-exam pattern, rubric "
        "point, or mark-scheme point.\n"
        "- Ask exactly one easier action the learner can complete now.\n"
        "- End with one short learner-facing instruction in the user's language asking "
        "them to fill the gap or continue the starter, then give confidence from 0-100%.\n"
        f"{_NO_ENGLISH_CLOSING_RULE}"
        "- If no grounded material context is available, say no grounded scaffold is "
        "available and ask which subtopic to review first."
    )


def _review_prompt(item: str) -> str:
    return (
        "Execute REVIEW.\n"
        f"Current item: {item}\n"
        "Rules:\n"
        "- The user needs to look at the material before attempting recall.\n"
        f"{_STORED_MATERIAL_CONTEXT_RULE}"
        "- Present the minimum cited-material explanation needed to restart.\n"
        "- Cite evidence IDs whenever you state a factual step or value.\n"
        "- End with one short learner-facing instruction in the user's language asking "
        "them to signal when they are ready for recall.\n"
        f"{_NO_ENGLISH_READY_RULE}"
        "- If no grounded material context is available, say no grounded review is available."
    )


def _assess_prompt(item: str, attempt_count: int) -> str:
    return (
        "Execute ASSESS.\n"
        f"Current item: {item}\n"
        f"Attempt number: {attempt_count + 1}\n"
        "Rules:\n"
        "- Evaluate the user's attempt against the retrieved material only.\n"
        "- Treat retrieved material, rubrics, mark schemes, and past-exam patterns as "
        "the source of truth. General model knowledge may only clarify wording; it "
        "must not add expected points or override the material.\n"
        "- Start the reply with exactly one label: CORRECT:, PARTIAL:, or WRONG:.\n"
        "- After the label, use this compact structure when evidence is available:\n"
        "  Score: <earned>/<available or expected points>.\n"
        "  Got: <material-supported points the user included>.\n"
        "  Missing: <rubric or material-supported points still needed>.\n"
        "  Misconception: <incorrect idea and why the source contradicts it, or none>.\n"
        "  Correction: <minimal cited correction with evidence IDs>.\n"
        "  Try again: <one next retrieval prompt>.\n"
        "  Confidence: <whether the user's confidence seems calibrated, if stated>.\n"
        "- CORRECT: keep the structure brief and do not restate a full solution.\n"
        "- PARTIAL: identify missing required points without revealing unrelated "
        "extra material.\n"
        "- WRONG: correct the misconception or first wrong step immediately, then give "
        "one focused retrieval prompt. Do not let the user continue with a false idea.\n"
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
    is_material_overview = _is_material_overview_plan(plan)
    prompt = (
        plan.prompt
        if is_material_overview
        else append_policy_prompt(
            plan.prompt,
            mode=mode,
            move=move,
            action=plan.action,
        )
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
        study_move=None if is_material_overview else move,
    )


def _is_material_overview_plan(plan: StudyTurnPlan) -> bool:
    return plan.action is StudyAction.PRESENT and (
        "Execute MATERIAL_OVERVIEW" in plan.prompt
        or (plan.retrieval_query is not None and _is_overview_request(plan.retrieval_query))
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
    return _direct_reply_plan(
        reply,
        phase=state.phase,
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
    if _autopilot_time_budget_reached(state, now=now):
        return "time budget reached"
    if reason := _autopilot_session_completion_reason(
        state,
        due_reviews=due_reviews,
        memory_state=memory_state,
    ):
        return reason
    if _autopilot_fatigue_detected(state):
        return "learner fatigue or frustration detected"
    return ""


def _autopilot_time_budget_reached(state: StudyState, *, now: datetime | None = None) -> bool:
    if state.time_budget_minutes is None or state.autopilot_started_at is None:
        return False
    current_time = now or datetime.now(UTC)
    started = state.autopilot_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return current_time - started >= timedelta(minutes=state.time_budget_minutes)


def _autopilot_session_completion_reason(
    state: StudyState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> str:
    session_type = state.autopilot_session_type.casefold()
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
    state: StudyState,
    due_reviews: tuple[ReviewItem, ...],
) -> bool:
    return session_type == "review" and state.autopilot_turns > 0 and not due_reviews


def _exam_session_complete(
    session_type: str,
    state: StudyState,
    learner_state_active: bool,
) -> bool:
    return (
        session_type in {"exam", "cram"}
        and state.autopilot_turns >= 6
        and not learner_state_active
    )


def _mastery_target_reached(
    state: StudyState,
    memory_state: MemoryState,
    learner_state_active: bool,
) -> bool:
    return (
        state.autopilot_turns >= 4 and not learner_state_active and not memory_state.misconceptions
    )


def _autopilot_fatigue_detected(state: StudyState) -> bool:
    return (
        state.last_feedback_type in {StudyFeedbackType.WRONG, StudyFeedbackType.PARTIAL}
        and state.hint_level >= 4
    )


def _plan_turn_manual(state: StudyState, user_input: str) -> StudyTurnPlan:
    text = _normalize(user_input)
    if "priorit" in text.lower():
        return _priority_plan(user_input, phase=state.phase)
    if _needs_initial_calibration(user_input):
        drill_query = material_drill_query(user_input)
        return material_topic_drill_plan(user_input, retrieval_query=drill_query or "")

    if _is_light_chat_request(user_input):
        return manual_chat_plan(text)

    query = _derive_presentation_query(user_input, state)
    if is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
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
    if state.current_item:
        return _plan_turn_base(state, user_input, allow_direct_chat=allow_direct_chat)

    if direct_plan := _autopilot_direct_plan(state, user_input, allow_direct_chat):
        return direct_plan

    text = _normalize(user_input)
    if "priorit" in text.lower():
        return _priority_plan(user_input, phase=state.phase)

    query = _derive_presentation_query(user_input, state)
    if query_plan := _autopilot_query_plan(query):
        return query_plan

    return _autopilot_calibration_plan(query, state)


def _autopilot_direct_plan(
    state: StudyState,
    user_input: str,
    allow_direct_chat: bool,
) -> StudyTurnPlan | None:
    direct_reply = _direct_chat_reply(user_input) if allow_direct_chat else None
    simple_greeting = _is_simple_greeting(user_input)
    if direct_reply is not None and not simple_greeting:
        return _direct_reply_plan(direct_reply, phase=state.phase)
    if direct_reply is None and not allow_direct_chat and _is_light_chat_request(user_input):
        return None if simple_greeting else manual_chat_plan(_normalize(user_input))
    return None


def _autopilot_query_plan(query: str) -> StudyTurnPlan | None:
    if _is_overview_request(query):
        return material_overview_plan(query)
    if not _is_autopilot_bootstrap(query) and is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    return None


def _autopilot_calibration_plan(query: str, state: StudyState) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.CALIBRATE,
        phase=StudyPhase.RECALL,
        prompt=_autopilot_calibration_prompt(query, state),
        retrieval_query=_autopilot_calibration_retrieval_query(query),
        allow_tools=False,
        buffer_response=True,
    )


def _is_autopilot_bootstrap(query: str) -> bool:
    normalized_query = _normalize(query).casefold()
    return normalized_query.startswith("start ") and " autopilot session" in normalized_query


def _autopilot_calibration_retrieval_query(query: str) -> str | None:
    if _is_autopilot_bootstrap(query):
        return None
    if drill_query := material_drill_query(query):
        return drill_query
    if _needs_initial_calibration(query):
        return None
    return query


def _plan_turn_base(
    state: StudyState,
    user_input: str,
    *,
    allow_direct_chat: bool = True,
) -> StudyTurnPlan:
    text = _normalize(user_input)

    if not state.current_item:
        return _plan_turn_without_current_item(
            state,
            user_input,
            text,
            allow_direct_chat=allow_direct_chat,
        )

    if _SKIP_RE.search(text):
        return _present_query_plan(state, user_input)

    source_query = state.retrieval_query or state.current_item

    if state.phase == StudyPhase.WAITING_FOR_READY:
        return _plan_waiting_for_ready_turn(state, user_input, text, source_query)

    if state.phase == StudyPhase.RECALL:
        return _plan_recall_turn(state, user_input, text, source_query)

    return _present_query_plan(state, user_input)


def _plan_turn_without_current_item(
    state: StudyState,
    user_input: str,
    text: str,
    *,
    allow_direct_chat: bool,
) -> StudyTurnPlan:
    if direct_plan := _without_current_direct_plan(state, user_input, text, allow_direct_chat):
        return direct_plan

    query = _derive_presentation_query(user_input, state)
    return _without_current_query_plan(query)


def _without_current_direct_plan(
    state: StudyState,
    user_input: str,
    text: str,
    allow_direct_chat: bool,
) -> StudyTurnPlan | None:
    if not allow_direct_chat and _is_light_chat_request(user_input):
        return manual_chat_plan(text)
    direct_reply = _direct_chat_reply(user_input) if allow_direct_chat else None
    if direct_reply is not None:
        return _direct_reply_plan(direct_reply, phase=state.phase)
    if "priorit" in text.lower():
        return _priority_plan(user_input, phase=state.phase)
    if _is_heph_self_request(text):
        return _chat_prompt_plan(_heph_self_prompt(text), phase=state.phase)
    if _needs_initial_calibration(user_input):
        drill_query = material_drill_query(user_input)
        return material_topic_drill_plan(user_input, retrieval_query=drill_query or "")
    return None


def _without_current_query_plan(query: str) -> StudyTurnPlan:
    if _is_overview_request(query):
        return material_overview_plan(query)
    if is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    return material_topic_presentation_plan(query, retrieval_query=query)


def _plan_waiting_for_ready_turn(
    state: StudyState,
    user_input: str,
    text: str,
    source_query: str,
) -> StudyTurnPlan:
    if material_plan := _material_request_plan(state, user_input):
        return material_plan
    if _READY_RE.fullmatch(text):
        return _prompt_recall_plan(state.current_item)
    if _is_reveal_request(text):
        return _refuse_reveal_plan(state.current_item, phase=StudyPhase.WAITING_FOR_READY)
    if not _WAITING_PROCEDURE_RE.fullmatch(text):
        return _material_review_plan(
            prompt=_source_followup_prompt(state.current_item, user_input),
            retrieval_query=source_query,
        )
    return StudyTurnPlan(
        action=StudyAction.WAIT_READY_REMINDER,
        phase=StudyPhase.WAITING_FOR_READY,
        prompt=_waiting_prompt(),
        allow_tools=False,
    )


def _plan_recall_turn(
    state: StudyState,
    user_input: str,
    text: str,
    source_query: str,
) -> StudyTurnPlan:
    if control_plan := _recall_control_plan(state, user_input, text):
        return control_plan
    if learning_plan := _recall_learning_plan(state, text, source_query):
        return learning_plan
    return _recall_assessment_plan(state, text, source_query)


def _recall_control_plan(
    state: StudyState,
    user_input: str,
    text: str,
) -> StudyTurnPlan | None:
    if _is_reveal_request(text):
        return _refuse_reveal_plan(state.current_item, phase=StudyPhase.RECALL)
    if _is_heph_self_request(text):
        return _chat_prompt_plan(_heph_self_prompt(text), phase=StudyPhase.RECALL)
    if material_plan := _material_request_plan(state, user_input):
        return material_plan
    return None


def _recall_learning_plan(
    state: StudyState,
    text: str,
    source_query: str,
) -> StudyTurnPlan | None:
    if _is_recall_scaffold_request(text) or _TOO_HARD_RE.search(text):
        return _recall_scaffold_plan(state, source_query)
    if _is_recall_clarification_request(text):
        return recall_clarification_plan(text, current_item=state.current_item)
    if _REVIEW_MATERIAL_RE.search(text):
        return _material_review_plan(
            prompt=_review_prompt(state.current_item),
            retrieval_query=source_query,
        )
    if _HINT_RE.search(text) and state.attempt_count > 0:
        return _recall_hint_plan(state, source_query)
    return None


def _recall_scaffold_plan(state: StudyState, source_query: str) -> StudyTurnPlan:
    prompt = (
        _autopilot_scaffold_prompt(state.current_item)
        if state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
        else _simplify_prompt(state.current_item)
    )
    return StudyTurnPlan(
        action=StudyAction.SIMPLIFY,
        phase=StudyPhase.RECALL,
        prompt=prompt,
        retrieval_query=source_query,
        use_expected_source_refs=True,
        allow_tools=False,
    )


def _recall_hint_plan(state: StudyState, source_query: str) -> StudyTurnPlan:
    return StudyTurnPlan(
        action=StudyAction.HINT,
        phase=StudyPhase.ASSESS,
        prompt=_hint_prompt(state.current_item, state.hint_level + 1),
        retrieval_query=source_query,
        use_expected_source_refs=True,
        allow_tools=False,
    )


def _recall_assessment_plan(state: StudyState, text: str, source_query: str) -> StudyTurnPlan:
    confidence_match = _CONFIDENCE_RE.search(text)
    return StudyTurnPlan(
        action=StudyAction.ASSESS,
        phase=StudyPhase.ASSESS,
        prompt=_assess_prompt(state.current_item, state.attempt_count),
        retrieval_query=source_query,
        use_expected_source_refs=True,
        allow_tools=False,
        buffer_response=True,
        stated_confidence=(
            normalize_confidence_value(
                float(confidence_match.group("value")),
                confidence_match.group("unit") or "",
            )
            if confidence_match is not None
            else None
        ),
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
        return StudyFeedbackType.PARTIAL, _assessment_visible_reply("PARTIAL", cleaned)

    label = match.group(1).upper()
    cleaned = _ASSESS_PREFIX_RE.sub("", reply, count=1).strip()
    feedback = {
        "CORRECT": StudyFeedbackType.CORRECT,
        "PARTIAL": StudyFeedbackType.PARTIAL,
        "WRONG": StudyFeedbackType.WRONG,
    }[label]
    body = cleaned or _fallback_assessment_message(feedback)
    return feedback, _assessment_visible_reply(label, body)


def _assessment_visible_reply(label: str, body: str) -> str:
    cleaned = body.strip()
    if _ASSESS_SECTION_RE.match(cleaned):
        return f"{label}:\n{cleaned}"
    return f"{label}: {cleaned}"


def _derive_recall_rating(
    feedback: StudyFeedbackType,
    elapsed_seconds: int | None,
) -> StudyRecallRating:
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


def _clear_recall_target(
    state: StudyState,
    *,
    feedback: StudyFeedbackType,
    phase: StudyPhase = StudyPhase.PRESENTING,
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
    state: StudyState,
    *,
    phase: StudyPhase,
    current_item: str,
    retrieval_query: str,
    source_refs: list[str],
    feedback: StudyFeedbackType,
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
        state.last_recall_rating = StudyRecallRating.NONE
    if hint_level is not None:
        state.hint_level = hint_level


def apply_turn_result(
    state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    *,
    now: datetime | None = None,
) -> tuple[StudyState, str]:
    current_time = now or datetime.now(UTC)
    next_state = state.clone()
    if state.autonomy_mode is StudyAutonomyMode.AUTOPILOT and plan.action is not StudyAction.CHAT:
        next_state.autopilot_turns = state.autopilot_turns + 1

    if early_result := _apply_simple_turn_result(
        next_state,
        plan,
        reply,
        source_refs,
        current_time,
    ):
        return early_result

    if control_result := _apply_recall_control_result(
        state,
        next_state,
        plan,
        reply,
        source_refs,
        current_time,
    ):
        return control_result

    handler = _TURN_RESULT_HANDLERS.get(plan.action)
    return (
        handler(state, next_state, plan, reply, source_refs, current_time)
        if handler is not None
        else (next_state, reply)
    )


def _apply_simple_turn_result(
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult | None:
    if plan.action is StudyAction.CHAT:
        next_state.last_feedback_type = StudyFeedbackType.NONE
        return next_state, plan.direct_reply or reply
    if plan.action is StudyAction.PRIORITY:
        next_state.phase = StudyPhase.PRESENTING
        next_state.last_feedback_type = StudyFeedbackType.NONE
        return next_state, reply
    if plan.action is StudyAction.SOURCE_QA:
        _clear_recall_target(next_state, feedback=StudyFeedbackType.NONE, reset_hint=False)
        return next_state, reply
    if plan.action is StudyAction.CALIBRATE:
        return _apply_calibrate_result(next_state, plan, reply, source_refs, current_time)
    return None


def _apply_present_turn_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    _current_time: datetime,
) -> TurnResult:
    return _apply_present_result(
        state,
        next_state,
        plan,
        reply,
        source_refs,
        plan.retrieval_query or state.retrieval_query,
    )


def _apply_simplify_turn_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult:
    return _apply_simplify_result(
        state,
        next_state,
        reply,
        source_refs,
        plan.retrieval_query or state.retrieval_query,
        current_time,
    )


def _apply_review_turn_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    _current_time: datetime,
) -> TurnResult:
    return _apply_review_result(
        state,
        next_state,
        reply,
        source_refs,
        plan.retrieval_query or state.retrieval_query,
    )


def _apply_assess_turn_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult:
    return _apply_assess_result(next_state, state, plan, reply, source_refs, current_time)


_TURN_RESULT_HANDLERS: dict[StudyAction, TurnResultHandler] = {
    StudyAction.PRESENT: _apply_present_turn_result,
    StudyAction.SIMPLIFY: _apply_simplify_turn_result,
    StudyAction.REVIEW: _apply_review_turn_result,
    StudyAction.ASSESS: _apply_assess_turn_result,
}


def _apply_recall_control_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[StudyState, str] | None:
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
    return None


def _apply_calibrate_result(
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[StudyState, str]:
    if source_refs:
        current_item = _normalize(reply)
        _enter_sourced_step(
            next_state,
            phase=StudyPhase.RECALL,
            current_item=current_item,
            retrieval_query=plan.retrieval_query or current_item,
            source_refs=source_refs,
            feedback=StudyFeedbackType.CALIBRATING,
            recall_started_at=current_time,
            hint_level=0,
        )
    else:
        _clear_recall_target(next_state, feedback=StudyFeedbackType.NO_SOURCE)
        _set_autopilot_stop_reason(next_state, "evidence is insufficient")
    return next_state, reply


def _apply_present_result(
    state: StudyState,
    next_state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[StudyState, str]:
    if _is_material_overview_plan(plan):
        _clear_recall_target(
            next_state,
            feedback=StudyFeedbackType.NONE if source_refs else StudyFeedbackType.NO_SOURCE,
        )
        if not source_refs:
            _set_autopilot_stop_reason(next_state, "evidence is insufficient")
        return next_state, reply
    if source_refs:
        _enter_sourced_step(
            next_state,
            phase=StudyPhase.WAITING_FOR_READY,
            current_item=plan.retrieval_query or state.current_item,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=StudyFeedbackType.PRESENTED,
            recall_started_at=None,
            hint_level=0,
        )
    else:
        _clear_recall_target(next_state, feedback=StudyFeedbackType.NO_SOURCE)
        _set_autopilot_stop_reason(next_state, "evidence is insufficient")
    return next_state, reply


def _apply_simplify_result(
    state: StudyState,
    next_state: StudyState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
    current_time: datetime,
) -> tuple[StudyState, str]:
    if source_refs:
        _enter_sourced_step(
            next_state,
            phase=StudyPhase.RECALL,
            current_item=_normalize(reply),
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=StudyFeedbackType.EASIER,
            recall_started_at=current_time,
            hint_level=min(5, state.hint_level + 1),
        )
    else:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        _set_autopilot_stop_reason(next_state, "evidence is insufficient")
    return next_state, reply


def _apply_review_result(
    state: StudyState,
    next_state: StudyState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[StudyState, str]:
    if source_refs:
        _enter_sourced_step(
            next_state,
            phase=StudyPhase.WAITING_FOR_READY,
            current_item=state.current_item,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=StudyFeedbackType.REVIEWING,
            recall_started_at=None,
        )
    else:
        next_state.phase = StudyPhase.RECALL
        next_state.last_feedback_type = StudyFeedbackType.NO_SOURCE
        _set_autopilot_stop_reason(next_state, "evidence is insufficient")
    return next_state, reply


def _apply_assess_result(
    next_state: StudyState,
    state: StudyState,
    plan: StudyTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[StudyState, str]:
    feedback, cleaned_reply = _parse_assessment_reply(reply)
    elapsed_seconds = _elapsed_recall_seconds(state.recall_started_at, current_time)
    next_state.attempt_count = state.attempt_count + 1
    if source_refs:
        next_state.expected_source_refs = list(source_refs)
    next_state.last_feedback_type = feedback
    next_state.last_recall_seconds = elapsed_seconds
    next_state.last_recall_rating = _derive_recall_rating(feedback, elapsed_seconds)
    next_state.last_confidence = plan.stated_confidence
    if feedback is StudyFeedbackType.CORRECT:
        _clear_recall_target(next_state, feedback=feedback)
        next_state.attempt_count = state.attempt_count + 1
    else:
        next_state.phase = StudyPhase.RECALL
        next_state.recall_started_at = current_time
        if _autopilot_assessment_fatigue(state, feedback):
            _set_autopilot_stop_reason(next_state, "learner fatigue or frustration detected")
    if not source_refs:
        _set_autopilot_stop_reason(next_state, "evidence is insufficient")
    return next_state, cleaned_reply


def _elapsed_recall_seconds(
    recall_started_at: datetime | None,
    current_time: datetime,
) -> int | None:
    if recall_started_at is None:
        return None
    if recall_started_at.tzinfo is None:
        recall_started_at = recall_started_at.replace(tzinfo=UTC)
    return max(0, int((current_time - recall_started_at).total_seconds()))


def _autopilot_assessment_fatigue(
    state: StudyState,
    feedback: StudyFeedbackType,
) -> bool:
    return (
        feedback is StudyFeedbackType.WRONG
        and state.hint_level >= 4
        and state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    )


def _set_autopilot_stop_reason(state: StudyState, reason: str) -> None:
    if state.autonomy_mode is not StudyAutonomyMode.AUTOPILOT:
        return
    if state.autopilot_stop_reason:
        return
    state.autopilot_stop_reason = reason
