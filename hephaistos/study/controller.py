"""Deterministic controller for the recall-loop state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from hephaistos.logging import get_logger
from hephaistos.product.context import heph_product_context
from hephaistos.study.intent import (
    is_material_source_request,
    is_new_material_topic_request,
    is_source_only_policy,
    is_standalone_source_only_policy,
    material_drill_query,
)
from hephaistos.study.overview import OVERVIEW_REQUEST_RE
from hephaistos.study.policy import (
    LearningMove,
    MemoryState,
    ReviewItem,
    append_policy_prompt,
    is_driven_learning_intent,
    move_for_plan,
    normalize_confidence_value,
)
from hephaistos.study.state import (
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    RecallRating,
)

_log = get_logger("study.controller")

type TurnResult = tuple[LearningState, str]

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
    "- Do not hard-code an English recall sentence when the learning exchange is in "
    "another language.\n"
)
_NO_ASSESS_USER_RULE = "- Do not assess the user.\n"
_STORED_MATERIAL_CONTEXT_RULE = "- Use only the stored material context for this item.\n"
_CITE_EVIDENCE_STEP_RULE = "- Cite evidence IDs whenever you state a factual step or value.\n"
_CITE_EVIDENCE_CLAIMS_RULE = "- Cite evidence IDs for claims grounded in source material.\n"
_KEEP_ONE_SHORT_SENTENCE_RULE = "- Keep it to one short sentence.\n"
_KEEP_ONE_OR_TWO_SHORT_SENTENCES_RULE = "- Keep it to one or two short sentences.\n"
_FORBIDDEN_RECALL_QUESTION_TYPES_HEADER = (
    "- FORBIDDEN question types (these never test knowledge):\n"
)
_NO_UNSOLICITED_LEARNING_MENU_RULE = (
    "- Do not offer menus, next steps, drills, study plans, readiness prompts, or ask what "
    "the user wants next unless the user asks for that."
)
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
    r"armory|armories|model\s+picker|"
    r"login|privacy|diagnostics|settings"
    r")\b",
    re.IGNORECASE,
)
_HEPH_PRONOUN_SELF_REQUEST_RE = re.compile(
    r"\b(?:"
    r"what\s+is\s+(?:heph|hephaistos|this\s+(?:tool|app|cli))|"
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
_MAX_PRACTICE_TURNS = 24


@dataclass(frozen=True, slots=True)
class LearningTurnPlan:
    action: LearningAction
    phase: LearningPhase
    prompt: str
    retrieval_query: str | None = None
    use_expected_source_refs: bool = False
    allow_tools: bool = True
    buffer_response: bool = False
    stated_confidence: float | None = None
    learning_move: LearningMove | None = None


def _turn_plan(
    action: LearningAction,
    prompt: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
    retrieval_query: str | None = None,
    use_expected_source_refs: bool = False,
    allow_tools: bool = False,
    buffer_response: bool = False,
    stated_confidence: float | None = None,
    learning_move: LearningMove | None = None,
) -> LearningTurnPlan:
    return LearningTurnPlan(
        action=action,
        phase=phase,
        prompt=prompt,
        retrieval_query=retrieval_query,
        use_expected_source_refs=use_expected_source_refs,
        allow_tools=allow_tools,
        buffer_response=buffer_response,
        stated_confidence=stated_confidence,
        learning_move=learning_move,
    )


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def _derive_presentation_query(user_input: str, state: LearningState) -> str:
    cleaned = _normalize(user_input)
    if cleaned and not _SKIP_RE.fullmatch(cleaned.lower()):
        return cleaned
    if state.current_item:
        return f"different material-backed item from {state.current_item}"
    return "next material-backed learning item"


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


def _is_overview_request(text: str) -> bool:
    return bool(OVERVIEW_REQUEST_RE.search(_normalize(text)))


def _is_reveal_request(text: str) -> bool:
    return bool(_REVEAL_RE.search(text) or _SHORT_REVEAL_RE.fullmatch(text))


def _is_recall_clarification_request(text: str) -> bool:
    normalized = _normalize(text)
    return any(_recall_clarification_checks(normalized))


def _recall_clarification_checks(text: str) -> tuple[bool, ...]:
    return (
        is_source_only_policy(text),
        _RECALL_CLARIFICATION_RE.search(text) is not None,
        _RECALL_REPROMPT_RE.search(text) is not None,
        _RECALL_SHORT_REPROMPT_RE.fullmatch(text) is not None,
        _RECALL_LANGUAGE_ONLY_RE.fullmatch(text) is not None,
        _is_recall_question_clarification(text),
    )


def _is_recall_question_clarification(text: str) -> bool:
    return _RECALL_QUESTION_PUNCT_RE.search(text) is not None and not _looks_like_recall_answer(
        text
    )


def _looks_like_recall_answer(text: str) -> bool:
    return bool(
        _RECALL_ANSWER_CLAIM_RE.search(text)
        or _RECALL_TENTATIVE_ANSWER_RE.fullmatch(text)
        or _RECALL_SHORT_ANSWER_RE.fullmatch(text)
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
    state: LearningState,
    user_input: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan | None:
    text = _normalize(user_input)
    if "priorit" in text.lower():
        return _priority_plan(user_input, phase=phase)
    if drill_query := material_drill_query(user_input):
        return material_topic_drill_plan(user_input, retrieval_query=drill_query)
    query = _derive_presentation_query(user_input, state)
    return _material_query_plan(query)


def _material_query_plan(query: str) -> LearningTurnPlan | None:
    if _is_overview_request(query):
        return material_overview_plan(query)
    if is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    if is_new_material_topic_request(query):
        return material_topic_presentation_plan(query, retrieval_query=query)
    return None


def _prompt_frame(execute_line: str, *context_lines: str, rules: tuple[str, ...]) -> str:
    return f"{execute_line}\n{_prompt_lines(context_lines)}Rules:\n{_prompt_lines(rules)}".rstrip()


def _prompt_lines(lines: tuple[str, ...]) -> str:
    return "".join(_prompt_line(line) for line in lines if line)


def _prompt_line(line: str) -> str:
    return line if line.endswith("\n") else f"{line}\n"


def _calibration_prompt(*, user_request: str | None = None) -> str:
    request_line = ""
    if user_request:
        request_line = (
            "User request (language/topic signal; rules below override it): "
            f"{_normalize(user_request)}\n"
        )
    return _prompt_frame(
        "Execute CALIBRATE.",
        request_line,
        rules=(
            "- Use the retrieved material to ask exactly one diagnostic recall question.",
            "- The question must be grounded in at least one retrieved source span, "
            "past-exam pattern, rubric point, or mark-scheme point.",
            "- The question must test understanding of a concept, procedure, or "
            "relationship from the material — not surface-level document metadata.",
            "Question quality contract:",
            _ACTIVE_RECALL_QUESTION_CONTRACT,
            _FORBIDDEN_RECALL_QUESTION_TYPES_HEADER,
            "  * Titles of documents, chapters, sections, or slides.",
            "  * Author names, dates, or institutional affiliations.",
            "  * Page numbers, section numbers, or slide numbers.",
            "  * File names, folder names, or file paths.",
            "  * Headings or subheadings as standalone answers.",
            "- Instead, ask about definitions, cause-effect relationships, key steps "
            "in a procedure, comparisons between concepts, or applications of a principle.",
            "- Prefer an introductory, concrete item a first-time user can attempt.",
            "- If the user asked for an easy question, make it genuinely easy and "
            "prerequisite-level.",
            "- If the user asked for an exam-style or timed question, include one reasonable "
            "time limit and require them to reason their answer from memory.",
            "- Do not present the solution or method.",
            "- Do not include evidence IDs, citations, source labels, or answer-location hints "
            "in the question.",
            "- Internally preserve the source grounding for later assessment; never invent "
            "unsupported questions from general model knowledge.",
            "- End with one short learner-facing instruction in the user's language asking "
            "them to answer from memory, or ask for an easier question or material review.",
            _NO_ENGLISH_CLOSING_RULE,
            "- If no retrieved source material is available, ask which material or topic "
            "to start with.",
        ),
    )


def _priority_prompt(user_request: str = "") -> str:
    request_line = f"User request: {user_request}\n" if user_request else ""
    return _prompt_frame(
        "Execute PRIORITY.",
        request_line,
        rules=(
            _SAME_LANGUAGE_USER_RULE,
            "- Analyze the retrieved materials and past exams only.",
            "- Identify the highest-priority topics by recurrence, exam weighting signals, "
            "and prerequisite value.",
            "- Separate direct evidence from inference. Cite evidence IDs for direct claims.",
            "- Include missing prerequisites the user should review first.",
            "- If the retrieved evidence is too thin to infer priorities, say so and list "
            "what materials are needed.",
        ),
    )


def _priority_plan(user_input: str, *, phase: LearningPhase) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.PRIORITY,
        _priority_prompt(user_input),
        phase=phase,
        retrieval_query=_PRIORITY_RETRIEVAL_QUERY,
    )


def _chat_prompt_plan(prompt: str, *, phase: LearningPhase) -> LearningTurnPlan:
    return _turn_plan(LearningAction.CHAT, prompt, phase=phase)


def _chat_or_product_help_plan(
    user_input: str,
    text: str,
    *,
    phase: LearningPhase,
    allow_light_chat: bool,
    skip_simple_greeting: bool = False,
    normalize_light_prompt: bool = False,
) -> LearningTurnPlan | None:
    if _is_heph_self_request(text):
        return _chat_prompt_plan(_heph_self_prompt(text), phase=phase)
    if not _should_route_light_chat(
        user_input,
        text,
        allow_light_chat=allow_light_chat,
        skip_simple_greeting=skip_simple_greeting,
    ):
        return None
    prompt_text = text if normalize_light_prompt else user_input
    return _chat_prompt_plan(_plain_chat_prompt(prompt_text), phase=phase)


def _should_route_light_chat(
    user_input: str,
    text: str,
    *,
    allow_light_chat: bool,
    skip_simple_greeting: bool,
) -> bool:
    if not allow_light_chat or (skip_simple_greeting and _is_simple_greeting(user_input)):
        return False
    return _is_light_chat_request(user_input) or is_standalone_source_only_policy(text)


def _prompt_recall_plan(item: str) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.PROMPT_RECALL,
        _recall_prompt(item),
        phase=LearningPhase.RECALL,
    )


def _refuse_reveal_plan(item: str, *, phase: LearningPhase) -> LearningTurnPlan:
    return _turn_plan(LearningAction.REFUSE_REVEAL, _refusal_prompt(item), phase=phase)


def _material_review_plan(
    prompt: str,
    retrieval_query: str,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.REVIEW,
        prompt,
        phase=phase,
        retrieval_query=retrieval_query,
        use_expected_source_refs=True,
    )


def _present_query_plan(state: LearningState, user_input: str) -> LearningTurnPlan:
    query = _derive_presentation_query(user_input, state)
    if _is_overview_request(query):
        return material_overview_plan(query)
    return material_topic_presentation_plan(query, retrieval_query=query)


def _present_prompt(item: str, *, user_request: str | None = None) -> str:
    request_line = ""
    if user_request and _normalize(user_request) != _normalize(item):
        request_line = f"User request: {user_request}\n"
    return _prompt_frame(
        "Execute the PRESENT phase.",
        f"Current item: {item}",
        request_line,
        rules=(
            _SAME_LANGUAGE_REQUEST_RULE,
            "- Use only the retrieved material for this item.",
            "- Present the complete solution or method once, concisely.",
            _CITE_EVIDENCE_STEP_RULE,
            _NO_UNSOLICITED_LEARNING_MENU_RULE,
            "- If no retrieved source material is available, say no searchable armory "
            "evidence was found for this item. Do not answer from outside knowledge. "
            "Ask for a more specific material-backed prompt or for the material to be indexed.",
            "- Do not switch into assessment or extra tutoring.",
        ),
    )


def _overview_prompt(query: str) -> str:
    return _prompt_frame(
        "Execute MATERIAL_OVERVIEW.",
        f"User request: {query}",
        rules=(
            _SAME_LANGUAGE_REQUEST_RULE,
            "- Give the big picture first: domain, document types, major topic clusters, "
            "and how the topics relate.",
            "- Use only cited retrieved evidence. Do not infer from filenames, dates, "
            "semester labels, lecturers, institutions, language, or outside knowledge.",
            "- Avoid course administration metadata and do not explain retrieval sampling "
            "mechanics.",
            "- Synthesize in your own words. Do not paste long source excerpts; quote only "
            "short exact wording when useful.",
            "- Use at least two concise cited bullets when evidence supports them, and cite "
            "evidence IDs for every factual claim.",
            "- If evidence is thin, state only the supported subject and document roles; "
            "do not add a generic sampling or completeness disclaimer.",
            "- Do not end with readiness, drill, next-step, evidence-grounding-block, "
            "sample-scope, non-exhaustive list, or completeness caveats.",
        ),
    )


def material_overview_plan(
    user_request: str,
    *,
    retrieval_query: str = "what is the material about",
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.PRESENT,
        _overview_prompt(user_request),
        retrieval_query=retrieval_query,
        buffer_response=True,
    )


def material_topic_presentation_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> LearningTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return _turn_plan(
        LearningAction.PRESENT,
        _present_prompt(query, user_request=user_request),
        retrieval_query=query,
        allow_tools=True,
    )


def material_topic_drill_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> LearningTurnPlan:
    prompt = _calibration_prompt(user_request=user_request)
    if _EXAM_DRILL_RE.search(_normalize(user_request)):
        prompt = (
            f"{prompt}\n"
            "- This is an active-recall exam drill: do not show the result, answer key, "
            "rubric, source explanation, source IDs, or citations until after the user's "
            "attempt has been assessed."
        )
    return _turn_plan(
        LearningAction.CALIBRATE,
        prompt,
        phase=LearningPhase.RECALL,
        retrieval_query=_normalize(retrieval_query) or None,
        buffer_response=True,
    )


def material_source_qa_plan(
    user_request: str,
    *,
    retrieval_query: str,
) -> LearningTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return _turn_plan(
        LearningAction.SOURCE_QA,
        _source_qa_prompt(query, user_request=user_request),
        retrieval_query=query,
        buffer_response=True,
    )


def recall_clarification_plan(
    user_request: str,
    *,
    current_item: str,
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.PROMPT_RECALL,
        _recall_clarification_prompt(current_item, _normalize(user_request)),
        phase=LearningPhase.RECALL,
    )


def plain_chat_plan(
    user_request: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.CHAT,
        _plain_chat_prompt(_normalize(user_request), terminal_context=True),
        phase=phase,
    )


def _source_qa_prompt(query: str, *, user_request: str | None = None) -> str:
    request_line = ""
    if user_request and _normalize(user_request) != _normalize(query):
        request_line = f"User request: {user_request}\n"
    return _prompt_frame(
        "Execute SOURCE_QA.",
        f"User question: {query}",
        request_line,
        rules=(
            _SAME_LANGUAGE_REQUEST_RULE,
            "- Answer the user's question directly using only the retrieved source material.",
            "- If the user asks for an exact phrase, quote only the exact phrase plus citations.",
            _CITE_EVIDENCE_CLAIMS_RULE,
            "- If no retrieved source material answers the question, say that the armory sources "
            "do not contain the answer and ask for more specific material.",
        ),
    )


def _plain_chat_prompt(query: str, *, terminal_context: bool = False) -> str:
    rules = [
        _SAME_LANGUAGE_USER_RULE,
        "- Do not quiz unless the user explicitly asks.\n",
        _NO_UNSOLICITED_LEARNING_MENU_RULE + "\n",
    ]
    if terminal_context:
        rules[1:1] = [
            "- Behave like a plain terminal assistant with access to the current "
            "armory's memory and materials.\n",
            "- Use retrieved armory evidence when it is relevant, and cite evidence IDs for "
            "claims based on the armory.\n",
            "- You may supplement with general knowledge when the user is not asking for a "
            "source-only or armory-only answer; clearly separate general knowledge from "
            "armory-backed claims.\n",
        ]
    else:
        if is_standalone_source_only_policy(query):
            rules.append(
                "- Treat this as a source-only preference: acknowledge briefly, then use "
                "enabled material only and say when sources are insufficient.\n"
            )
        rules.extend(
            (
                "- Reply directly as a plain terminal assistant.\n",
                "- Keep it short. Do not use armory retrieval or citations unless the user "
                "asks about their materials.\n",
                "- For questions about Heph itself, answer from current Heph documentation "
                "context when provided by the system prompt or turn prompt.",
            )
        )
    return _prompt_frame("Execute CHAT.", f"User request: {query}", rules=tuple(rules))


def _heph_self_prompt(query: str) -> str:
    docs_context = heph_product_context()
    context_block = (
        f"Current Heph documentation excerpt:\n{docs_context}\n"
        if docs_context
        else "Current Heph documentation excerpt: unavailable.\n"
    )
    return _prompt_frame(
        "Execute HEPH_HELP.",
        f"User request: {query}",
        context_block,
        rules=(
            _SAME_LANGUAGE_USER_RULE,
            "- Answer from the Heph documentation excerpt above, not from armory material.",
            "- Do not treat the user message as a recall attempt, even during an active drill.",
            "- Do not grade the learner, require confidence, or reveal any active recall answer.",
            "- Do not use armory material, citations, retrieved evidence, or tool output.",
            "- If the excerpt does not answer the request, say what is missing and point to "
            "/help.",
            "- Keep the answer concise and practical.",
        ),
    )


def _practice_calibration_prompt(query: str, state: LearningState) -> str:
    goal = state.session_goal or "material review"
    session_type = state.practice_session_type or "general"
    return _prompt_frame(
        "Execute PRACTICE_CALIBRATION.",
        f"Practice type: {session_type}",
        f"Practice goal: {goal}",
        f"User request: {query}",
        rules=(
            "- Do not print planning labels.",
            "- Start directly with the learner-facing task.",
            "- Use the retrieved source material to ask exactly one diagnostic recall, "
            "prediction, application, or comparison question.",
            "- Ground the question in at least one retrieved source span, past-exam pattern, "
            "rubric point, or mark-scheme point.",
            "- The question must test understanding, not document metadata.",
            "Question quality contract:",
            _ACTIVE_RECALL_QUESTION_CONTRACT,
            _FORBIDDEN_RECALL_QUESTION_TYPES_HEADER,
            "  * Titles of documents, chapters, sections, or slides.",
            "  * Author names, dates, or institutional affiliations.",
            "  * Page numbers, section numbers, or slide numbers.",
            "  * File names, folder names, or file paths.",
            "  * Headings or subheadings as standalone answers.",
            "- Internally preserve source grounding and never invent unsupported questions.",
            "- Do not reveal the answer, method, answer key, source IDs, or citations.",
            "- Require the learner to answer from memory and include confidence from 0-100%.",
            "- If source material is unavailable or too thin, ask the smallest necessary "
            "clarifying question instead of inventing a task.",
            "- End with one short learner-facing instruction in the user's language asking them "
            "to answer from memory and give confidence from 0-100%.",
            _NO_ENGLISH_CLOSING_RULE,
        ),
    )


def _source_followup_prompt(item: str, user_input: str) -> str:
    return _prompt_frame(
        "Execute SOURCE_FOLLOWUP.",
        f"Current material focus: {item}",
        f"User follow-up: {user_input}",
        rules=(
            "- Answer in the same language as the user's follow-up when clear.",
            "- Treat the follow-up as a real question or reaction about the cited material, "
            "not as a readiness signal and not as a recall attempt.",
            "- Use the stored or retrieved material evidence before answering.",
            "- If the follow-up is an acknowledgement such as 'interesting', explain one "
            "specific reason grounded in the material for why it is interesting or important.",
            "- If the follow-up asks why, answer the why-question directly from the evidence.",
            _NO_UNSOLICITED_LEARNING_MENU_RULE,
            _CITE_EVIDENCE_CLAIMS_RULE,
            _NO_ASSESS_USER_RULE,
        ),
    )


def _waiting_prompt() -> str:
    return _prompt_frame(
        "Execute WAITING_FOR_READY.",
        rules=(
            "- Do not reveal any more of the solution.",
            "- Tell the user, in their language when clear, to signal when they are ready "
            "for recall.",
            _NO_ENGLISH_READY_RULE,
            _KEEP_ONE_SHORT_SENTENCE_RULE,
        ),
    )


def _recall_prompt(item: str) -> str:
    return _prompt_frame(
        "Execute RECALL.",
        f"Current item: {item}",
        rules=(
            "- Do not answer the item.",
            "- Tell the user to reproduce the solution from memory now.",
            _SAME_LANGUAGE_ITEM_RULE,
            _NO_ENGLISH_RECALL_RULE,
            _KEEP_ONE_SHORT_SENTENCE_RULE,
        ),
    )


def _recall_clarification_prompt(item: str, request: str) -> str:
    return _prompt_frame(
        "Execute RECALL_CLARIFICATION.",
        f"Current item: {item}",
        f"User request: {request}",
        rules=(
            "- The user is asking what to answer, not attempting the answer.",
            "- If the user asks to repeat, rephrase, translate, or use a language, honor "
            "that request for the prompt only.",
            "- Restate what they should recall from memory without revealing the solution.",
            _NO_ASSESS_USER_RULE,
            "- Do not include answer content, grading, scores, or correctness labels.",
            "- Answer in the same language as the user's clarification request when clear.",
            "- Do not hard-code an English recall sentence when the user asked in another "
            "language.",
            _KEEP_ONE_OR_TWO_SHORT_SENTENCES_RULE,
        ),
    )


def _refusal_prompt(item: str) -> str:
    return _prompt_frame(
        "Execute REFUSE_REVEAL.",
        f"Current item: {item}",
        rules=(
            "- Do not reveal new solution content.",
            "- Briefly refuse and tell the user to attempt recall first.",
            _SAME_LANGUAGE_ITEM_RULE,
            "- Do not hard-code an English refusal when the learning exchange is in another "
            "language.",
            _KEEP_ONE_OR_TWO_SHORT_SENTENCES_RULE,
        ),
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
    return _prompt_frame(
        "Execute HINT.",
        f"Current item: {item}",
        f"Hint level: {bounded_level}",
        rules=(
            _STORED_MATERIAL_CONTEXT_RULE,
            level_instruction,
            leakage_rule,
            "- If no grounded material context is available, say no grounded hint is available.",
            _SAME_LANGUAGE_ITEM_RULE,
            "- Do not hard-code an English hint when the learning exchange is in another "
            "language.",
            _KEEP_ONE_SHORT_SENTENCE_RULE,
        ),
    )


def _practice_scaffold_prompt(item: str) -> str:
    return _prompt_frame(
        "Execute PRACTICE_SCAFFOLD.",
        f"Previous item: {item}",
        rules=(
            "- The learner signaled that they are not ready or not sure.",
            "- Do not grade the learner and do not mark the attempt wrong.",
            _STORED_MATERIAL_CONTEXT_RULE,
            "- Give the smallest useful scaffold: a sentence starter, one partial setup, "
            "or a 1-3 blank fill-the-gaps prompt.",
            "- Keep the full answer hidden; reveal only enough structure for the learner "
            "to make a real next attempt.",
            "- Ground the scaffold in a retrieved source span, past-exam pattern, rubric "
            "point, or mark-scheme point.",
            "- Ask exactly one easier action the learner can complete now.",
            "- End with one short learner-facing instruction in the user's language asking "
            "them to fill the gap or continue the starter, then give confidence from 0-100%.",
            _NO_ENGLISH_CLOSING_RULE,
            "- If no grounded material context is available, say no grounded scaffold is "
            "available and ask which subtopic to review first.",
        ),
    )


def _review_prompt(item: str) -> str:
    return _prompt_frame(
        "Execute REVIEW.",
        f"Current item: {item}",
        rules=(
            "- The user needs to look at the material before attempting recall.",
            _STORED_MATERIAL_CONTEXT_RULE,
            "- Present the minimum cited-material explanation needed to restart.",
            _CITE_EVIDENCE_STEP_RULE,
            _NO_UNSOLICITED_LEARNING_MENU_RULE,
            "- If no grounded material context is available, say no grounded review is available.",
        ),
    )


def _assess_prompt(item: str, attempt_count: int) -> str:
    return _prompt_frame(
        "Execute ASSESS.",
        f"Current item: {item}",
        f"Attempt number: {attempt_count + 1}",
        rules=(
            "- Evaluate the user's attempt against the retrieved material only.",
            "- Treat retrieved material, rubrics, mark schemes, and past-exam patterns as "
            "the source of truth. General model knowledge may only clarify wording; it "
            "must not add expected points or override the material.",
            "- Start the reply with exactly one label: CORRECT:, PARTIAL:, or WRONG:.",
            "- After the label, use this compact structure when evidence is available:",
            "  Score: <earned>/<available or expected points>.",
            "  Got: <material-supported points the user included>.",
            "  Missing: <rubric or material-supported points still needed>.",
            "  Misconception: <incorrect idea and why the source contradicts it, or none>.",
            "  Correction: <minimal cited correction with evidence IDs>.",
            "  Try again: <one next retrieval prompt>.",
            "  Confidence: <whether the user's confidence seems calibrated, if stated>.",
            "- CORRECT: keep the structure brief and do not restate a full solution.",
            "- PARTIAL: identify missing required points without revealing unrelated "
            "extra material.",
            "- WRONG: correct the misconception or first wrong step immediately, then give "
            "one focused retrieval prompt. Do not let the user continue with a false idea.",
            "- Cite evidence IDs for rubric points, missing points, misconceptions, and "
            "corrections whenever IDs are available.",
            "- If the uploaded material does not contain enough evidence to assess "
            "confidently, say so clearly and default to PARTIAL:.",
            "- Be factual and direct. No praise. No generic encouragement.",
            "- If material evidence is missing, default to PARTIAL: and say grounded "
            "assessment is unavailable.",
        ),
    )


def plan_turn(
    state: LearningState,
    user_input: str,
    *,
    due_reviews: tuple[ReviewItem, ...] = (),
    memory_state: MemoryState | None = None,
    allow_direct_chat: bool = True,
) -> LearningTurnPlan:
    effective_memory = memory_state if memory_state is not None else MemoryState()
    bounded_plan = _practice_stop_plan(
        state,
        due_reviews=due_reviews,
        memory_state=effective_memory,
    )
    if bounded_plan is not None:
        return bounded_plan
    plan = _plan_turn_from_intent(state, user_input, allow_direct_chat=allow_direct_chat)
    return _with_learning_policy(
        plan,
        state,
        user_input,
        due_reviews=due_reviews,
        memory_state=effective_memory,
    )


def _with_learning_policy(
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> LearningTurnPlan:
    move = move_for_plan(
        plan.action,
        state,
        user_input,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    skip_policy_prompt = (
        _is_material_overview_plan(plan) or plan.action is LearningAction.SOURCE_QA
    )
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
        learning_move=None if skip_policy_prompt else move,
    )


def _is_material_overview_plan(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.PRESENT and (
        "Execute MATERIAL_OVERVIEW" in plan.prompt
        or (plan.retrieval_query is not None and _is_overview_request(plan.retrieval_query))
    )


def _plan_turn_from_intent(
    state: LearningState,
    user_input: str,
    *,
    allow_direct_chat: bool,
) -> LearningTurnPlan:
    if state.current_item or state.phase is not LearningPhase.PRESENTING:
        return _plan_turn_base(state, user_input, allow_direct_chat=allow_direct_chat)
    if is_driven_learning_intent(user_input) or _practice_session_active(state):
        return _plan_turn_driven_learning(state, user_input, allow_direct_chat=allow_direct_chat)
    return _plan_turn_plain(state, user_input)


def _practice_session_active(state: LearningState) -> bool:
    return bool(state.practice_started_at or state.practice_session_type or state.practice_turns)


def _practice_stop_plan(
    state: LearningState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> LearningTurnPlan | None:
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


def _practice_stop_prompt(reason: str) -> str:
    return _prompt_frame(
        "Practice session boundary.",
        rules=(
            f"- Tell the user the current practice session is complete because: {reason}.",
            "- Be brief and do not offer a menu or next step.",
        ),
    )


def _practice_stop_reason(
    state: LearningState,
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


def _practice_time_stop_reason(state: LearningState, *, now: datetime | None = None) -> str:
    return "time budget reached" if _practice_time_budget_reached(state, now=now) else ""


def _practice_completion_stop_reason(
    state: LearningState,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState,
) -> str:
    return _practice_session_completion_reason(
        state,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )


def _practice_fatigue_stop_reason(state: LearningState) -> str:
    return "learner fatigue or frustration detected" if _practice_fatigue_detected(state) else ""


def _practice_time_budget_reached(state: LearningState, *, now: datetime | None = None) -> bool:
    if state.time_budget_minutes is None or state.practice_started_at is None:
        return False
    current_time = now or datetime.now(UTC)
    started = state.practice_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return current_time - started >= timedelta(minutes=state.time_budget_minutes)


def _practice_session_completion_reason(
    state: LearningState,
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
    state: LearningState,
    due_reviews: tuple[ReviewItem, ...],
) -> bool:
    return session_type == "review" and state.practice_turns > 0 and not due_reviews


def _exam_session_complete(
    session_type: str,
    state: LearningState,
    learner_state_active: bool,
) -> bool:
    return (
        session_type in {"exam", "cram"} and state.practice_turns >= 6 and not learner_state_active
    )


def _mastery_target_reached(
    state: LearningState,
    memory_state: MemoryState,
    learner_state_active: bool,
) -> bool:
    return (
        state.practice_turns >= 4 and not learner_state_active and not memory_state.misconceptions
    )


def _practice_fatigue_detected(state: LearningState) -> bool:
    return (
        state.last_feedback_type in {LearningFeedbackType.WRONG, LearningFeedbackType.PARTIAL}
        and state.hint_level >= 4
    )


def _plan_turn_plain(state: LearningState, user_input: str) -> LearningTurnPlan:
    text = _normalize(user_input)
    if plan := _priority_or_initial_drill_plan(user_input, phase=state.phase):
        return plan
    if chat_plan := _plain_chat_direct_plan(
        user_input,
        text,
        phase=LearningPhase.PRESENTING,
        allow_light_chat=True,
    ):
        return chat_plan

    query = _derive_presentation_query(user_input, state)
    return _without_current_query_plan(query)


def _plan_turn_driven_learning(
    state: LearningState,
    user_input: str,
    *,
    allow_direct_chat: bool,
) -> LearningTurnPlan:
    if state.current_item:
        return _plan_turn_base(state, user_input, allow_direct_chat=allow_direct_chat)

    if direct_plan := _practice_direct_plan(state, user_input, allow_direct_chat):
        return direct_plan

    query = _derive_presentation_query(user_input, state)
    if plan := _driven_material_plan(user_input, query, phase=state.phase):
        return plan
    return _turn_plan(
        LearningAction.CALIBRATE,
        _practice_calibration_prompt(query, state),
        phase=LearningPhase.RECALL,
        retrieval_query=_practice_calibration_retrieval_query(query),
        buffer_response=True,
    )


def _driven_material_plan(
    user_input: str,
    query: str,
    *,
    phase: LearningPhase,
) -> LearningTurnPlan | None:
    if "priorit" in _normalize(user_input).lower():
        return _priority_plan(user_input, phase=phase)
    if _is_overview_request(query):
        return material_overview_plan(query)
    if not _is_practice_bootstrap(query) and is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    return None


def _practice_direct_plan(
    state: LearningState,
    user_input: str,
    allow_direct_chat: bool,
) -> LearningTurnPlan | None:
    text = _normalize(user_input)
    return _chat_or_product_help_plan(
        user_input,
        text,
        phase=state.phase,
        allow_light_chat=True,
        skip_simple_greeting=True,
        normalize_light_prompt=not allow_direct_chat,
    )


def _is_practice_bootstrap(query: str) -> bool:
    normalized_query = _normalize(query).casefold()
    return normalized_query.startswith("start ") and bool(
        re.search(r"\b(?:a|an)?\s*practice session\b", normalized_query)
    )


def _practice_calibration_retrieval_query(query: str) -> str | None:
    if _is_practice_bootstrap(query):
        return None
    if drill_query := material_drill_query(query):
        return drill_query
    if _needs_initial_calibration(query):
        return None
    return query


def _plan_turn_base(
    state: LearningState,
    user_input: str,
    *,
    allow_direct_chat: bool = True,
) -> LearningTurnPlan:
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
    return _plan_turn_with_current_item(state, user_input, text, source_query)


def _plan_turn_with_current_item(
    state: LearningState,
    user_input: str,
    text: str,
    source_query: str,
) -> LearningTurnPlan:
    if state.phase == LearningPhase.WAITING_FOR_READY:
        return _plan_waiting_for_ready_turn(state, user_input, text, source_query)
    if state.phase == LearningPhase.RECALL:
        return _plan_recall_turn(state, user_input, text, source_query)
    return _present_query_plan(state, user_input)


def _plan_turn_without_current_item(
    state: LearningState,
    user_input: str,
    text: str,
    *,
    allow_direct_chat: bool,
) -> LearningTurnPlan:
    if direct_plan := _plain_chat_direct_plan(
        user_input,
        text,
        phase=state.phase,
        allow_light_chat=not allow_direct_chat,
    ):
        return direct_plan
    if plan := _priority_or_initial_drill_plan(user_input, phase=state.phase):
        return plan

    query = _derive_presentation_query(user_input, state)
    return _without_current_query_plan(query)


def _plain_chat_direct_plan(
    user_input: str,
    text: str,
    *,
    phase: LearningPhase,
    allow_light_chat: bool,
) -> LearningTurnPlan | None:
    return _chat_or_product_help_plan(
        user_input,
        text,
        phase=phase,
        allow_light_chat=allow_light_chat,
        normalize_light_prompt=True,
    )


def _priority_or_initial_drill_plan(
    user_input: str,
    *,
    phase: LearningPhase,
) -> LearningTurnPlan | None:
    if "priorit" in _normalize(user_input).lower():
        return _priority_plan(user_input, phase=phase)
    if _needs_initial_calibration(user_input):
        drill_query = material_drill_query(user_input)
        return material_topic_drill_plan(user_input, retrieval_query=drill_query or "")
    return None


def _without_current_query_plan(query: str) -> LearningTurnPlan:
    if _is_overview_request(query):
        return material_overview_plan(query)
    if is_material_source_request(query):
        return material_source_qa_plan(query, retrieval_query=query)
    return material_topic_presentation_plan(query, retrieval_query=query)


def _plan_waiting_for_ready_turn(
    state: LearningState,
    user_input: str,
    text: str,
    source_query: str,
) -> LearningTurnPlan:
    if material_plan := _material_request_plan(state, user_input):
        return material_plan
    if _READY_RE.fullmatch(text):
        return _prompt_recall_plan(state.current_item)
    if _is_reveal_request(text):
        return _refuse_reveal_plan(state.current_item, phase=LearningPhase.WAITING_FOR_READY)
    if not _WAITING_PROCEDURE_RE.fullmatch(text):
        return _material_review_plan(
            prompt=_source_followup_prompt(state.current_item, user_input),
            retrieval_query=source_query,
        )
    return _turn_plan(
        LearningAction.WAIT_READY_REMINDER,
        _waiting_prompt(),
        phase=LearningPhase.WAITING_FOR_READY,
    )


def _plan_recall_turn(
    state: LearningState,
    user_input: str,
    text: str,
    source_query: str,
) -> LearningTurnPlan:
    if control_plan := _recall_control_plan(state, user_input, text):
        return control_plan
    if learning_plan := _recall_learning_plan(state, text, source_query):
        return learning_plan
    return _recall_assessment_plan(state, text, source_query)


def _recall_control_plan(
    state: LearningState,
    user_input: str,
    text: str,
) -> LearningTurnPlan | None:
    if _is_reveal_request(text):
        return _refuse_reveal_plan(state.current_item, phase=LearningPhase.RECALL)
    if _is_heph_self_request(text):
        return _chat_prompt_plan(_heph_self_prompt(text), phase=LearningPhase.RECALL)
    if material_plan := _material_request_plan(state, user_input):
        return material_plan
    return None


def _recall_learning_plan(
    state: LearningState,
    text: str,
    source_query: str,
) -> LearningTurnPlan | None:
    if _is_recall_scaffold_request(text) or _TOO_HARD_RE.search(text):
        return _recall_scaffold_plan(state, source_query)
    if _is_recall_clarification_request(text):
        return recall_clarification_plan(text, current_item=state.current_item)
    return _recall_review_or_hint_plan(state, text, source_query)


def _recall_review_or_hint_plan(
    state: LearningState,
    text: str,
    source_query: str,
) -> LearningTurnPlan | None:
    if _REVIEW_MATERIAL_RE.search(text):
        return _recall_review_plan(state, source_query)
    if _HINT_RE.search(text) and state.attempt_count > 0:
        return _recall_hint_plan(state, source_query)
    return None


def _recall_review_plan(state: LearningState, source_query: str) -> LearningTurnPlan:
    return _material_review_plan(
        prompt=_review_prompt(state.current_item),
        retrieval_query=source_query,
    )


def _recall_scaffold_plan(state: LearningState, source_query: str) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.SIMPLIFY,
        _practice_scaffold_prompt(state.current_item),
        phase=LearningPhase.RECALL,
        retrieval_query=source_query,
        use_expected_source_refs=True,
    )


def _recall_hint_plan(state: LearningState, source_query: str) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.HINT,
        _hint_prompt(state.current_item, state.hint_level + 1),
        phase=LearningPhase.ASSESS,
        retrieval_query=source_query,
        use_expected_source_refs=True,
    )


def _recall_assessment_plan(
    state: LearningState,
    text: str,
    source_query: str,
) -> LearningTurnPlan:
    confidence_match = _CONFIDENCE_RE.search(text)
    return _turn_plan(
        LearningAction.ASSESS,
        _assess_prompt(state.current_item, state.attempt_count),
        phase=LearningPhase.ASSESS,
        retrieval_query=source_query,
        use_expected_source_refs=True,
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


def _fallback_assessment_message(feedback: LearningFeedbackType) -> str:
    if feedback is LearningFeedbackType.CORRECT:
        return "I could not parse the assessment output as CORRECT."
    if feedback is LearningFeedbackType.WRONG:
        return "I could not parse the assessment output as WRONG."
    return "I could not parse the assessment output as PARTIAL."


def _parse_assessment_reply(reply: str) -> tuple[LearningFeedbackType, str]:
    match = _ASSESS_PREFIX_RE.match(reply)
    if not match:
        _log.warning("assessment reply missing prefix; defaulting to PARTIAL")
        cleaned = reply.strip() or _fallback_assessment_message(LearningFeedbackType.PARTIAL)
        return LearningFeedbackType.PARTIAL, _assessment_visible_reply("PARTIAL", cleaned)

    label = match.group(1).upper()
    cleaned = _ASSESS_PREFIX_RE.sub("", reply, count=1).strip()
    feedback = {
        "CORRECT": LearningFeedbackType.CORRECT,
        "PARTIAL": LearningFeedbackType.PARTIAL,
        "WRONG": LearningFeedbackType.WRONG,
    }[label]
    body = cleaned or _fallback_assessment_message(feedback)
    return feedback, _assessment_visible_reply(label, body)


def _assessment_visible_reply(label: str, body: str) -> str:
    cleaned = body.strip()
    if _ASSESS_SECTION_RE.match(cleaned):
        return f"{label}:\n{cleaned}"
    return f"{label}: {cleaned}"


def _derive_recall_rating(
    feedback: LearningFeedbackType,
    elapsed_seconds: int | None,
) -> RecallRating:
    if feedback is LearningFeedbackType.WRONG:
        return RecallRating.HARD
    if feedback is LearningFeedbackType.PARTIAL:
        return _partial_recall_rating(elapsed_seconds)
    if feedback is LearningFeedbackType.CORRECT:
        return _correct_recall_rating(elapsed_seconds)
    return RecallRating.NONE


def _partial_recall_rating(elapsed_seconds: int | None) -> RecallRating:
    return (
        RecallRating.GOOD
        if elapsed_seconds is not None and elapsed_seconds <= 30
        else RecallRating.HARD
    )


def _correct_recall_rating(elapsed_seconds: int | None) -> RecallRating:
    if elapsed_seconds is None:
        return RecallRating.GOOD
    if elapsed_seconds <= 30:
        return RecallRating.EASY
    if elapsed_seconds <= 120:
        return RecallRating.GOOD
    return RecallRating.HARD


def _clear_recall_target(
    state: LearningState,
    *,
    feedback: LearningFeedbackType,
    phase: LearningPhase = LearningPhase.PRESENTING,
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
    state: LearningState,
    *,
    phase: LearningPhase,
    current_item: str,
    retrieval_query: str,
    source_refs: list[str],
    feedback: LearningFeedbackType,
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
    state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    *,
    now: datetime | None = None,
) -> tuple[LearningState, str]:
    current_time = now or datetime.now(UTC)
    next_state = state.clone()
    _increment_practice_turn_count(state, next_state, plan)

    if plan.action is LearningAction.ASSESS:
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
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
) -> None:
    if state.practice_started_at is not None and plan.action is not LearningAction.CHAT:
        next_state.practice_turns = state.practice_turns + 1


def _apply_non_assess_result(
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
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
    next_state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult | None:
    if plan.action is LearningAction.CHAT:
        return _apply_chat_result(next_state, reply)
    if plan.action is LearningAction.PRIORITY:
        return _apply_priority_result(next_state, reply)
    if plan.action is LearningAction.SOURCE_QA:
        return _apply_source_qa_result(next_state, reply)
    if plan.action is LearningAction.CALIBRATE:
        return _apply_calibrate_result(next_state, plan, reply, source_refs, current_time)
    return None


def _apply_chat_result(
    next_state: LearningState,
    reply: str,
) -> TurnResult:
    next_state.last_feedback_type = LearningFeedbackType.NONE
    return next_state, reply


def _apply_priority_result(next_state: LearningState, reply: str) -> TurnResult:
    next_state.phase = LearningPhase.PRESENTING
    next_state.last_feedback_type = LearningFeedbackType.NONE
    return next_state, reply


def _apply_source_qa_result(next_state: LearningState, reply: str) -> TurnResult:
    _clear_recall_target(next_state, feedback=LearningFeedbackType.NONE, reset_hint=False)
    return next_state, reply


_SOURCED_STEP_ACTIONS = frozenset(
    {
        LearningAction.PRESENT,
        LearningAction.SIMPLIFY,
        LearningAction.REVIEW,
    }
)


def _apply_sourced_action_result(
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
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
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> TurnResult:
    next_retrieval_query = plan.retrieval_query or state.retrieval_query
    if plan.action is LearningAction.PRESENT:
        return _apply_present_result(
            state,
            next_state,
            plan,
            reply,
            source_refs,
            next_retrieval_query,
        )
    if plan.action is LearningAction.SIMPLIFY:
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
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[LearningState, str] | None:
    if plan.action is LearningAction.PROMPT_RECALL:
        return _apply_prompt_recall_result(next_state, reply, current_time)
    if plan.action is LearningAction.WAIT_READY_REMINDER:
        return _apply_wait_ready_reminder_result(next_state, reply)
    if plan.action is LearningAction.REFUSE_REVEAL:
        return _apply_refuse_reveal_result(state, next_state, reply)
    if plan.action is LearningAction.HINT:
        return _apply_hint_result(state, next_state, reply, source_refs)
    return None


def _apply_prompt_recall_result(
    next_state: LearningState,
    reply: str,
    current_time: datetime,
) -> TurnResult:
    next_state.phase = LearningPhase.RECALL
    next_state.last_feedback_type = LearningFeedbackType.READY
    next_state.recall_started_at = current_time
    next_state.last_recall_seconds = None
    next_state.last_recall_rating = RecallRating.NONE
    next_state.hint_level = 0
    return next_state, reply


def _apply_wait_ready_reminder_result(next_state: LearningState, reply: str) -> TurnResult:
    next_state.phase = LearningPhase.WAITING_FOR_READY
    next_state.last_feedback_type = LearningFeedbackType.WAITING
    return next_state, reply


def _apply_refuse_reveal_result(
    state: LearningState,
    next_state: LearningState,
    reply: str,
) -> TurnResult:
    next_state.phase = state.phase
    next_state.last_feedback_type = LearningFeedbackType.REFUSED
    return next_state, reply


def _apply_hint_result(
    state: LearningState,
    next_state: LearningState,
    reply: str,
    source_refs: list[str],
) -> TurnResult:
    next_state.phase = LearningPhase.RECALL
    next_state.last_feedback_type = LearningFeedbackType.HINT
    next_state.hint_level = min(5, state.hint_level + 1)
    if source_refs:
        next_state.expected_source_refs = list(source_refs)
    return next_state, reply


def _apply_calibrate_result(
    next_state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[LearningState, str]:
    if source_refs:
        _enter_recall_from_reply(
            next_state,
            reply=reply,
            retrieval_query=plan.retrieval_query,
            source_refs=source_refs,
            feedback=LearningFeedbackType.CALIBRATING,
            current_time=current_time,
            hint_level=0,
        )
    else:
        _mark_insufficient_evidence(next_state)
    return next_state, reply


def _apply_present_result(
    state: LearningState,
    next_state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[LearningState, str]:
    if _is_material_overview_plan(plan):
        _clear_recall_target(
            next_state,
            feedback=LearningFeedbackType.NONE if source_refs else LearningFeedbackType.NO_SOURCE,
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
    next_state: LearningState,
    state: LearningState,
    plan: LearningTurnPlan,
    source_refs: list[str],
    next_retrieval_query: str,
) -> None:
    _enter_sourced_step(
        next_state,
        phase=LearningPhase.WAITING_FOR_READY,
        current_item=plan.retrieval_query or state.current_item,
        retrieval_query=next_retrieval_query,
        source_refs=source_refs,
        feedback=LearningFeedbackType.PRESENTED,
        recall_started_at=None,
        hint_level=0,
    )


def _apply_simplify_result(
    state: LearningState,
    next_state: LearningState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
    current_time: datetime,
) -> tuple[LearningState, str]:
    if source_refs:
        _enter_recall_from_reply(
            next_state,
            reply=reply,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=LearningFeedbackType.EASIER,
            current_time=current_time,
            hint_level=min(5, state.hint_level + 1),
        )
    else:
        _mark_insufficient_evidence(next_state, phase=LearningPhase.RECALL)
    return next_state, reply


def _enter_recall_from_reply(
    state: LearningState,
    *,
    reply: str,
    retrieval_query: str | None,
    source_refs: list[str],
    feedback: LearningFeedbackType,
    current_time: datetime,
    hint_level: int,
) -> None:
    current_item = _normalize(reply)
    _enter_sourced_step(
        state,
        phase=LearningPhase.RECALL,
        current_item=current_item,
        retrieval_query=retrieval_query or current_item,
        source_refs=source_refs,
        feedback=feedback,
        recall_started_at=current_time,
        hint_level=hint_level,
    )


def _apply_review_result(
    state: LearningState,
    next_state: LearningState,
    reply: str,
    source_refs: list[str],
    next_retrieval_query: str,
) -> tuple[LearningState, str]:
    if source_refs:
        _enter_sourced_step(
            next_state,
            phase=LearningPhase.WAITING_FOR_READY,
            current_item=state.current_item,
            retrieval_query=next_retrieval_query,
            source_refs=source_refs,
            feedback=LearningFeedbackType.REVIEWING,
            recall_started_at=None,
        )
    else:
        _mark_insufficient_evidence(next_state, phase=LearningPhase.RECALL)
    return next_state, reply


def _mark_insufficient_evidence(
    state: LearningState,
    *,
    phase: LearningPhase | None = None,
) -> None:
    if phase is None:
        _clear_recall_target(state, feedback=LearningFeedbackType.NO_SOURCE)
    else:
        state.phase = phase
        state.last_feedback_type = LearningFeedbackType.NO_SOURCE
    _set_insufficient_evidence_stop_reason(state)


def _set_insufficient_evidence_stop_reason(state: LearningState) -> None:
    _set_practice_stop_reason(state, "evidence is insufficient")


def _apply_assess_result(
    next_state: LearningState,
    state: LearningState,
    plan: LearningTurnPlan,
    reply: str,
    source_refs: list[str],
    current_time: datetime,
) -> tuple[LearningState, str]:
    feedback, cleaned_reply = _parse_assessment_reply(reply)
    elapsed_seconds = _elapsed_recall_seconds(state.recall_started_at, current_time)
    next_state.attempt_count = state.attempt_count + 1
    if source_refs:
        next_state.expected_source_refs = list(source_refs)
    next_state.last_feedback_type = feedback
    next_state.last_recall_seconds = elapsed_seconds
    next_state.last_recall_rating = _derive_recall_rating(feedback, elapsed_seconds)
    next_state.last_confidence = plan.stated_confidence
    if feedback is LearningFeedbackType.CORRECT:
        _clear_recall_target(next_state, feedback=feedback)
        next_state.attempt_count = state.attempt_count + 1
    else:
        next_state.phase = LearningPhase.RECALL
        next_state.recall_started_at = current_time
        if _practice_assessment_fatigue(state, feedback):
            _set_practice_stop_reason(next_state, "learner fatigue or frustration detected")
    if not source_refs:
        _set_practice_stop_reason(next_state, "evidence is insufficient")
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


def _practice_assessment_fatigue(
    state: LearningState,
    feedback: LearningFeedbackType,
) -> bool:
    return (
        feedback is LearningFeedbackType.WRONG
        and state.hint_level >= 4
        and state.practice_started_at is not None
    )


def _set_practice_stop_reason(state: LearningState, reason: str) -> None:
    if state.practice_started_at is None:
        return
    if state.practice_stop_reason:
        return
    state.practice_stop_reason = reason
