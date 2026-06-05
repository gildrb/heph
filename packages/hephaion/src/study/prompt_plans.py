"""Prompt and turn-plan construction for learning sessions."""

from __future__ import annotations

from dataclasses import dataclass

from self_knowledge import heph_product_context

from study.assessment import CONFIDENCE_RE
from study.policy import LearningMove, normalize_confidence_value
from study.state import LearningAction, LearningPhase, LearningState

_SAME_LANGUAGE_USER_RULE = "- Answer in the same language as the user's request when clear.\n"
_SAME_LANGUAGE_REQUEST_RULE = (
    "- Answer in the same language as the user's request when clear, even when sources use "
    "another language; preserve source terms.\n"
)
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
    "- No unsolicited menus, plans, drills, readiness prompts, or next-step questions."
)
_PRIORITY_RETRIEVAL_QUERY = "exam priority topics prerequisites past exams materials overview"
_MATERIAL_OVERVIEW_ANSWER_RULES = (
    "- Write 1-2 short cited sentences in the user's language, or the requested table/list.",
    "- Honor requested shape exactly; tables need meaningful headers and a markdown separator.",
    "- State only topics, methods, examples, tasks, or problem types visible in the excerpts.",
    "- No unsolicited quality judgments, rankings, difficulty claims, source-wide scope, "
    "or importance claims.",
    "- Cite factual claims next to their support; omit unsupported specifics.",
    "- Do not copy source lines, use filenames/metadata as facts, append inventories, "
    "or add offers.",
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


@dataclass(frozen=True, slots=True)
class LearningTurnPlan:
    action: LearningAction
    phase: LearningPhase
    prompt: str
    original_user_input: str = ""
    retrieval_query: str | None = None
    retrieval_strategy: str = ""
    evidence_refs: tuple[str, ...] = ()
    requires_direct_evidence: bool = False
    use_expected_source_refs: bool = False
    uses_overview_sampling: bool = False
    allow_tools: bool = True
    allowed_tool_names: tuple[str, ...] | None = None
    buffer_response: bool = False
    stated_confidence: float | None = None
    learning_move: LearningMove | None = None


def _turn_plan(
    action: LearningAction,
    prompt: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
    original_user_input: str = "",
    retrieval_query: str | None = None,
    retrieval_strategy: str = "",
    evidence_refs: tuple[str, ...] = (),
    requires_direct_evidence: bool = False,
    use_expected_source_refs: bool = False,
    uses_overview_sampling: bool = False,
    allow_tools: bool = False,
    allowed_tool_names: tuple[str, ...] | None = None,
    buffer_response: bool = False,
    stated_confidence: float | None = None,
    learning_move: LearningMove | None = None,
) -> LearningTurnPlan:
    return LearningTurnPlan(
        action=action,
        phase=phase,
        prompt=prompt,
        original_user_input=original_user_input,
        retrieval_query=retrieval_query,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=evidence_refs,
        requires_direct_evidence=requires_direct_evidence,
        use_expected_source_refs=use_expected_source_refs,
        uses_overview_sampling=uses_overview_sampling,
        allow_tools=allow_tools,
        allowed_tool_names=allowed_tool_names,
        buffer_response=buffer_response,
        stated_confidence=stated_confidence,
        learning_move=learning_move,
    )


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


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
            "- If the user asked for an exam-style question, use only constraints visible in "
            "the retrieved evidence; do not invent time limits, point values, labels, or "
            "answer instructions.",
            "- Do not present the solution or method.",
            "- End the question with the smallest relevant evidence citation, such as [E1]. "
            "Do not include source labels, answer-location hints, or quoted answer text.",
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
            "- Give up to 3 cited review candidates; rank them only when the evidence states "
            "priority, weighting, order, or prerequisites.",
            "- If requested ordering is not source-stated, do not use ranked/order labels; "
            "give a non-ranked cited review candidate.",
            "- Do not use source availability, filenames, or manifest entries as evidence for "
            "what to review first.",
            "- Do not create umbrella category names; name the cited concept or source wording "
            "directly.",
            "- If order is inferred from available evidence, label it as your cited review "
            "candidate, not source-established priority.",
            "- Separate direct evidence from inference. Cite evidence IDs for direct claims.",
            "- Mention prerequisites only when retrieved evidence names them.",
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
            "- Do not infer ranking, importance, or source-wide scope unless evidence states it.",
            _CITE_EVIDENCE_STEP_RULE,
            _NO_UNSOLICITED_LEARNING_MENU_RULE,
            "- If no retrieved source material is available, say no searchable armory "
            "evidence was found for this item. Do not answer from outside knowledge.",
            "- Do not switch into assessment or extra tutoring.",
        ),
    )


def _overview_prompt(query: str) -> str:
    return _prompt_frame(
        "Execute MATERIAL_OVERVIEW.",
        f"User request: {query}",
        rules=(
            _SAME_LANGUAGE_REQUEST_RULE,
            *_MATERIAL_OVERVIEW_ANSWER_RULES,
        ),
    )


def material_overview_plan(
    user_request: str,
    *,
    retrieval_query: str | None = None,
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.PRESENT,
        _overview_prompt(user_request),
        original_user_input=user_request,
        retrieval_query=retrieval_query,
        retrieval_strategy="overview",
        uses_overview_sampling=True,
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
        original_user_input=user_request,
        retrieval_query=query,
        allow_tools=True,
    )


def material_topic_drill_plan(
    user_request: str,
    *,
    retrieval_query: str,
    exam_style: bool = False,
) -> LearningTurnPlan:
    prompt = _calibration_prompt(user_request=user_request)
    if exam_style:
        prompt = (
            f"{prompt}\n"
            "- This is an active-recall exam drill: do not show the result, answer key, "
            "rubric, or source explanation until after the user's attempt has been assessed."
        )
    return _turn_plan(
        LearningAction.CALIBRATE,
        prompt,
        phase=LearningPhase.RECALL,
        original_user_input=user_request,
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
        original_user_input=user_request,
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
        original_user_input=user_request,
    )


def plain_chat_plan(
    user_request: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan:
    return _turn_plan(
        LearningAction.CHAT,
        _plain_chat_prompt(_normalize(user_request)),
        phase=phase,
        original_user_input=user_request,
    )


_HEPH_ACTION_TOOL_NAMES = (
    "create_named_armory",
    "import_materials",
    "validate_armory",
    "list_files",
)


def heph_help_plan(
    user_request: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan:
    """Plan a chat turn answering product questions, grounded in product docs."""
    return _turn_plan(
        LearningAction.CHAT,
        _heph_self_prompt(_normalize(user_request)),
        phase=phase,
        original_user_input=user_request,
    )


def heph_action_plan(
    user_request: str,
    *,
    phase: LearningPhase = LearningPhase.PRESENTING,
) -> LearningTurnPlan:
    """Plan a product operation turn using exact, non-destructive setup tools."""
    return _turn_plan(
        LearningAction.CHAT,
        _heph_action_prompt(_normalize(user_request)),
        phase=phase,
        original_user_input=user_request,
        allow_tools=True,
        allowed_tool_names=_HEPH_ACTION_TOOL_NAMES,
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
            "- Use retrieved material for source facts; for follow-ups, use prior cited claims "
            "as premises and keep any inference concise.",
            "- Prefer one short paragraph; use at most three bullets if bullets help.",
            "- If the user asks for an exact phrase, quote only the exact phrase plus citations.",
            _CITE_EVIDENCE_CLAIMS_RULE,
            "- If direct evidence is required and retrieved material does not directly answer, "
            "say what direct cited answer is missing for the resolved request. Do not claim the "
            "whole armory or all sources lack it unless this turn exhaustively checked every "
            "source.",
        ),
    )


def _heph_action_prompt(query: str) -> str:
    docs_context = heph_product_context()
    context_block = (
        f"Current Hephaion documentation excerpt:\n{docs_context}\n"
        if docs_context
        else "Current Hephaion documentation excerpt: unavailable.\n"
    )
    return _prompt_frame(
        "Execute HEPH_ACTION.",
        f"User request: {query}",
        context_block,
        rules=(
            _SAME_LANGUAGE_USER_RULE,
            "- Use only the provided Heph setup/import tools for filesystem changes.",
            "- Treat armory names as exact. Never fuzzy-match, autocorrect, or substitute a "
            "similar-looking armory name.",
            "- Copy imports into materials/ only. Never move, delete, or overwrite different "
            "original files.",
            "- Set create_if_missing only when the user explicitly asks to create the target "
            "armory.",
            "- If a source path or target armory is missing or ambiguous, report the exact "
            "missing value and stop instead of guessing.",
            "- After tool results, answer with the exact action taken and target path.",
            "- Do not use armory material retrieval or evidence citations for product actions.",
        ),
    )


def _plain_chat_prompt(query: str) -> str:
    rules = (
        _SAME_LANGUAGE_USER_RULE,
        "- Behave like a plain terminal assistant with access to the current "
        "armory's memory and materials.\n",
        "- Use retrieved armory evidence when it is relevant, and cite evidence IDs for "
        "claims based on the armory.\n",
        "- You may supplement with general knowledge when the user is not asking for a "
        "source-only or armory-only answer; clearly separate general knowledge from "
        "armory-backed claims.\n",
        "- Do not quiz unless the user explicitly asks.\n",
        _NO_UNSOLICITED_LEARNING_MENU_RULE + "\n",
    )
    return _prompt_frame("Execute CHAT.", f"User request: {query}", rules=rules)


def _heph_self_prompt(query: str) -> str:
    docs_context = heph_product_context()
    context_block = (
        f"Current Hephaion documentation excerpt:\n{docs_context}\n"
        if docs_context
        else "Current Hephaion documentation excerpt: unavailable.\n"
    )
    return _prompt_frame(
        "Execute HEPH_HELP.",
        f"User request: {query}",
        context_block,
        rules=(
            _SAME_LANGUAGE_USER_RULE,
            "- Answer from the Hephaion documentation excerpt above, not from armory material.",
            "- Be operational: explain concrete Hephaion/Heph actions, commands, paths, or "
            "settings when they help.",
            "- For follow-ups, advance the answer with new specifics instead of repeating "
            "the prior summary.",
            "- When asked about configuring or using Heph, use the docs map to orient the "
            "user through the relevant commands.",
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
            "- Do not reveal the answer, method, or answer key.",
            "- End the question with the smallest relevant evidence citation, such as [E1].",
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
            "- Do not include a confidence value; only the learner may report confidence.",
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
            _CITE_EVIDENCE_CLAIMS_RULE,
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
            "- If cited evidence is available, give a concise review point from it; do not say "
            "no grounded review is available.",
            "- If no grounded material context is available, say no grounded review is available.",
        ),
    )


def _assess_prompt(item: str, attempt_count: int, *, exam_bank_session: bool = False) -> str:
    exam_bank_rule = (
        "- This item came from the structured exam bank. After grading, include the retrieved "
        "source-backed evaluation material for this prompt. Do not add evaluation content that "
        "is not present in the retrieved evidence."
        if exam_bank_session
        else "- Do not reveal unrelated evaluation material beyond what the assessment needs."
    )
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
            "  Confidence: <whether the user's confidence seems calibrated, if stated>.",
            "- CORRECT: keep the structure brief and do not restate a full solution.",
            "- PARTIAL: identify missing required points without revealing unrelated "
            "extra material.",
            "- WRONG: correct the misconception or first wrong step immediately using "
            "retrieved evidence. Do not let the user continue with a false idea.",
            "- Do not define or explain a term merely because the material uses it. If the "
            "retrieved material does not define the term, assess only the source-stated "
            "claim or say that the definition is still missing.",
            "- Cite evidence IDs for rubric points, missing points, misconceptions, and "
            "corrections whenever IDs are available.",
            exam_bank_rule,
            "- If the uploaded material does not contain enough evidence to assess "
            "confidently, say so clearly and default to PARTIAL:.",
            "- Be factual and direct. No praise. No generic encouragement.",
            "- If material evidence is missing, default to PARTIAL: and say grounded "
            "assessment is unavailable.",
        ),
    )


def _open_material_plan_for_intent(user_input: str, intent: str) -> LearningTurnPlan:
    query = _normalize(user_input)
    if intent == "material_overview":
        return material_overview_plan(user_input, retrieval_query=query or None)
    if intent == "source_qa":
        return material_source_qa_plan(user_input, retrieval_query=query)
    if intent == "topic_drill":
        return material_topic_drill_plan(user_input, retrieval_query=query)
    return material_topic_presentation_plan(user_input, retrieval_query=query)


def _practice_calibration_plan(state: LearningState, user_input: str) -> LearningTurnPlan:
    query = _normalize(user_input) or "next material-backed learning item"
    return _turn_plan(
        LearningAction.CALIBRATE,
        _practice_calibration_prompt(query, state),
        phase=LearningPhase.RECALL,
        retrieval_query=query if user_input else None,
        buffer_response=True,
    )


def _practice_stop_prompt(reason: str) -> str:
    return _prompt_frame(
        "Practice session boundary.",
        rules=(
            f"- Tell the user the current practice session is complete because: {reason}.",
            "- Be brief and do not offer a menu or next step.",
        ),
    )


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
    confidence_match = CONFIDENCE_RE.search(text)
    return _turn_plan(
        LearningAction.ASSESS,
        _assess_prompt(
            state.current_item,
            state.attempt_count,
            exam_bank_session=state.practice_session_type == "exam",
        ),
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
