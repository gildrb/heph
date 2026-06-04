"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import difflib
import json
import re
import threading
import unicodedata
from collections.abc import Callable, Generator, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from html import unescape
from typing import TYPE_CHECKING

import unicodeit

from hephaion._types import is_string_mapping, parse_json_object_fragment
from hephaion.agent.citation import VerificationResult, verify_citations, verify_response
from hephaion.agent.dispatch import iter_agent_events
from hephaion.chat.events import (
    AssistantDeltaEvent,
    GuardrailEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaion.chat.evidence import (
    ResolvedTurnPlan,
)
from hephaion.chat.evidence import (
    assess_turn_evidence as _assess_turn_evidence,
)
from hephaion.chat.evidence import (
    build_priority_context as _build_priority_context,
)
from hephaion.chat.evidence import (
    ensure_rag_index as _ensure_rag_index,
)
from hephaion.chat.evidence import (
    evidence_assessment_trace as _evidence_assessment_trace,
)
from hephaion.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from hephaion.chat.evidence import (
    evidence_trace_coverage as _evidence_trace_coverage,
)
from hephaion.chat.evidence import (
    evidence_trace_items as _evidence_trace_items,
)
from hephaion.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from hephaion.chat.evidence import (
    retrieval_audit_metadata as _retrieval_audit_metadata,
)
from hephaion.chat.learning_signals import (
    _exam_importance,
    _learner_assessment_trace,
    _learning_move_kind,
    _learning_practice_context,
    _matching_recall_item,
    _pedagogy_validation_trace,
    _policy_outcome_from_review,
    _positive_hint_level,
    _trace_task,
    _trace_turn_retrieval_query,
)
from hephaion.chat.material_state import (
    _EVIDENCE_REQUIRED_ACTIONS,
    _material_operation_events,
    _missing_indexed_material_reply,
    _no_matching_indexed_evidence_reply,
    _reading_notice,
    _should_use_material_answer_conversation_window,
    _tool_result_refreshes_current_armory,
    _writing_notice,
)
from hephaion.chat.titles import derive_title
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_LIST,
    ANSWER_FORMAT_PLAIN,
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
    TurnIntentResolution,
    intent_resolution_from_payload,
    turn_contract_from_resolution,
)
from hephaion.chat.turn_history import build_turn_snapshot
from hephaion.chat.turn_predicates import (
    _contract_followup_target,
    _count_label,
    _material_label,
    _overview_turn,
    _plural,
    _readable_material_label,
    _stored_turn_evidence,
    _trace_excerpt,
    _visible_turn_evidence,
)
from hephaion.chat.usage import save_usage
from hephaion.diagnostics.crashes import get_meter, get_tracer
from hephaion.logging import Timer, get_logger
from hephaion.memory.workflow import schedule_memory_extraction
from hephaion.product.context import heph_product_routing_context
from hephaion.rag import EvidenceChunk, TurnEvidence
from hephaion.rag.scoring import tokenize
from hephaion.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaion.safety import (
    GUARDRAIL_ACTION_WARN,
    GUARDRAIL_STAGE_OUTPUT,
    GuardrailMessage,
    check_user_input,
)
from hephaion.study import (
    EvidenceAssessment,
    LearningAction,
    LearningPhase,
    LearningState,
    LearningTurnPlan,
    apply_turn_result,
    plan_turn,
)
from hephaion.study.policy import LearningMoveKind
from hephaion.study.schedule import (
    RecallItemState,
    RecallScheduleStore,
    load_recall_schedule,
    save_recall_schedule,
)

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from hephaion.rag import ArmoryIndex

_log = get_logger("chat.orchestrator")
_tracer = get_tracer("chat.orchestrator")
_meter = get_meter("chat.orchestrator")
_rag_duration_hist = _meter.create_histogram(
    "rag.retrieval.duration",
    unit="ms",
    description="Duration of RAG retrieval queries",
)

_BROAD_PRIOR_EVIDENCE_REF_COUNT = 8
_FRESH_CURRENT_REQUEST_MIN_TERMS = 3
_MODEL_NORMALIZED_INTENTS = (
    "material_overview",
    "source_qa",
    "source_only_policy",
    "topic_presentation",
    "topic_drill",
    "ready_for_recall",
    "recall_clarification",
    "recall_answer_attempt",
    "reveal_request",
    "hint_request",
    "skip_request",
    "scaffold_request",
    "material_review",
    "priority_request",
    "driven_learning_calibration",
    "wait",
    "heph_action",
    "heph_help",
    "chat",
)
_MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = 0.75
_EVIDENCE_CITATION_TEXT_RE = re.compile(
    r"\s*(?:\[|【)(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*(?:\]|】)"
)
_ESCAPED_EVIDENCE_CITATION_RE = re.compile(r"\\\[((?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*)\\\]")
_PRIVATE_USE_EVIDENCE_CITATION_RE = re.compile(
    r"\ue200cite(?::|\ue202)((?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*)\ue201"
)
_INLINE_QUOTED_TEXT_RE = re.compile(r"[\"“”'](?P<text>[^\"“”']{2,80})[\"“”']")
_OVERVIEW_CITATION_ID_RE = re.compile(r"\[(?:e|E)(?P<id>\d+)\]")
_OVERVIEW_CITATION_BRACKET_RE = re.compile(
    r"\[(?P<body>\s*(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*\s*)\]"
)
_OVERVIEW_CITATION_TOKEN_RE = re.compile(r"(?:e|E)(?P<id>\d+)")
_OVERVIEW_CITATION_GROUP_RE = re.compile(r"\[(?:e|E)\d+\](?:(?:\s|,\s*)*\[(?:e|E)\d+\])+")
_TRAILING_EVIDENCE_CITATION_GROUP_RE = re.compile(r"(?:\s*\[(?:e|E)\d+\])+\s*$")
_CITATION_ONLY_REPLY_RE = re.compile(r"^\s*(?:\[(?:e|E)\d+\]\s*)+(?:[.,;:])?\s*$")
_THIN_EVIDENCE_POINTER_MAX_WORDS = 8
_MARKDOWN_TABLE_SEPARATOR_LINE_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_LATEX_INLINE_MATH_RE = re.compile(r"\\\((?P<expr>.+?)\\\)")
_LATEX_DISPLAY_MATH_RE = re.compile(r"\\\[(?P<expr>.+?)\\\]", re.DOTALL)
_LATEX_BARE_MATHBB_RE = re.compile(r"\\mathbb\s+(?P<symbol>[A-Za-z])")
_TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call\b[^>]*>.*?</tool_call>", re.IGNORECASE | re.DOTALL)
_TOOL_CALL_OPEN_RE = re.compile(r"<tool_call\b[^>]*>", re.IGNORECASE)
_TOOL_CALL_CLOSE_RE = re.compile(r"</tool_call>", re.IGNORECASE)
_DETERMINISTIC_REPLY_LITERAL_RE = re.compile(r"`[^`]+`|/[\w-]+|\"[^\"]+\"")
_ASSESSMENT_LABEL_RE = re.compile(r"^(?:CORRECT|PARTIAL|WRONG):")
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MAX_WORDS = 110
_OVERVIEW_MAX_CHARS = 700
_OVERVIEW_MAX_TABLE_CHARS = 1800
_OVERVIEW_MAX_UNCITED_LEAD_WORDS = 32
_OVERVIEW_MAX_UNCITED_LEAD_CHARS = 260
_MATERIAL_REPLY_MAX_CHARS = 700
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MAX_CITATIONS = 8
_OVERVIEW_COMPACT_CITATION_GROUP_SIZE = 5
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES = 5
_OVERVIEW_FALLBACK_MAX_ITEMS = 3
_TABLE_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_LIST_ITEMS = 3
_OVERVIEW_MAX_TABLE_ROWS = 8
_OVERVIEW_EXTRACTIVE_MIN_SPANS = 2
_OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS = 3
_OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO = 0.34
_PRIOR_ANSWER_CONTEXT_LIMIT = 500
_MATERIAL_CONTEXT_MESSAGE_LIMIT = 4
_MAX_INTERNAL_PASSES = 2
_CONTINUABLE_MATERIAL_INTENTS = frozenset(
    {
        "material_overview",
        "source_qa",
        "source_only_policy",
        "topic_presentation",
        "topic_drill",
    }
)
_LEADING_CONTROL_JSON_KEYS = frozenset(
    {
        "canonical_english_request",
        "confidence",
        "intent",
        "query",
        "retrieval_query",
        "topic",
    }
)
_MALFORMED_LEADING_CONTROL_JSON_RE = re.compile(
    r"(?is)^\s*\{\s*\"(?:"
    + "|".join(re.escape(key) for key in sorted(_LEADING_CONTROL_JSON_KEYS))
    + r")\"\s*:\s*.*?\}\s*(?=[A-ZÄÖÜ])"
)
_OVERVIEW_CONTACT_OR_URL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+)", re.IGNORECASE)
_OVERVIEW_DATE_LINE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-zÄÖÜäöüß]+\s+\d{4}\b|\b\d{4}\b")
_OVERVIEW_FORMULA_RE = re.compile(r"(?:\\[a-zA-Z]+|[$=∑∫√≤≥→↦∀∃])")
_OVERVIEW_LINE_MARKER_RE = re.compile(r"^[#*\-\d.\s:;()\[\]]+")
_LEARNING_INTENT_NORMALIZATION_SCHEMA = "\n".join(
    (
        "{",
        f'  "intent": "{" | ".join(_MODEL_NORMALIZED_INTENTS)}",',
        '  "canonical_english_request": "concise English request preserving the user\'s intent",',
        '  "is_followup": true,',
        (
            '  "followup_target": "what prior answer, cited claim, bullet, source, '
            'or topic this refers to",'
        ),
        (
            '  "answer_mode": "answer_from_evidence | transform_prior_answer | '
            'reason_from_prior_evidence",'
        ),
        '  "answer_format": "plain | table | list",',
        (
            '  "retrieval_strategy": "retrieve | reuse_prior_evidence | '
            'expand_prior_evidence | overview | none",'
        ),
        (
            '  "retrieval_query": "semantic retrieval query derived from the '
            'conversation, not filler words",'
        ),
        '  "direct_evidence_required": true,',
        '  "prior_answer_reference": true,',
        '  "prior_answer_positions": [1, 3],',
        '  "prior_answer_position_basis": "cited_claims | list_items | none",',
        '  "confidence": 0.0',
        "}",
    )
)
_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = """
Resolve routing hints for the current Heph turn; do not answer the user.

Materials are the default subject. Keep the current user request primary; use prior context only
to resolve references. New source content uses answer_from_evidence. Broad corpus views use
overview. Specific facts, definitions, quotes, named concepts, or named sources use retrieve.
Product/self explanation turns use heph_help with retrieval_strategy=none, not material_overview.
Product operations that create, validate, or import armories/material files use heph_action with
retrieval_strategy=none.
Corpus-level synthesis, comparison, evaluation, ranking, prioritization, or judgment over the
materials uses material_overview with retrieval_strategy=overview, even when the answer should
name one resulting topic or source. Do not turn a corpus-level operation into a literal keyword
lookup unless the user asks about a specific named concept, source, citation, or quoted claim.
Set is_followup=false unless the current request explicitly depends on a prior answer, citation,
source, listed item, table row, or continuing instruction. A fresh question about the materials is
not a follow-up merely because previous turns exist.
Use topic_drill only when the current user request asks Heph to quiz, drill, practice, or ask a
recall question; never carry drill mode from the previous assistant question by inertia.
Pure rewrites of a displayed prior answer use transform_prior_answer and reuse prior evidence.
Requests that change the prior answer's length, language, format, or presentation without asking
for a new source fact are transform_prior_answer turns, not source lookups.
Questions about why a cited prior answer matters use reason_from_prior_evidence.
Interpretation, relevance, implication, application, or cited synthesis follow-ups over a cited
prior answer use reason_from_prior_evidence with direct_evidence_required=false. Set
direct_evidence_required=true only when the requested answer is an exact quoted span, source or
citation location, or whether a source states a specific claim.
When the user points to cited/list/table positions in a prior answer, fill prior_answer_positions
and prior_answer_position_basis.

Return compact JSON only:
""".strip()
_OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT = """
Write a compact user-facing corpus overview from supplied evidence only. Use the user's request
language for prose, even when evidence uses another language; preserve source terms. Prefer
substantive learnable content over metadata. Cite every source claim with current IDs. Use a short
answer with at most 3 cited topic clusters unless a table was requested. Compress useful cited
synthesis from a rejected draft, but do not stitch copied source sentences or unsupported text.
If the user asks for judgment or opinion, answer as a neutral observation from the evidence.
Place citations next to the topic, method, or example they support; omit specifics without a
matching citation.
Do not discuss retrieval, validation, truncation, or sampling, and do not add offers or next steps.
""".strip()
_DETERMINISTIC_FALLBACK_LOCALIZATION_PROMPT = """
Rewrite an internal English fallback message for the user. Use the same language as the user's
request when clear. If the request is English or the language is unclear, return the original
English message. Preserve command literals, slash commands, paths, and quoted phrases exactly.
Preserve any leading CORRECT:, PARTIAL:, or WRONG: assessment label exactly.
Do not add facts, citations, source claims, apologies, or next actions.
Return plain text only.
""".strip()


@dataclass(frozen=True, slots=True)
class _LearningAgentOutput:
    streamed_reply: str
    raw_reply: str
    visible_reply: str
    completion_event: TurnCompleteEvent | None


@dataclass(slots=True)
class _LearningAgentBuffer:
    raw_parts: list[str] = field(default_factory=list)
    visible_parts: list[str] = field(default_factory=list)
    completion_event: TurnCompleteEvent | None = None

    def add_delta(self, delta: str, *, visible: bool) -> None:
        self.raw_parts.append(delta)
        if visible:
            self.visible_parts.append(delta)

    @property
    def streamed_reply(self) -> str:
        return "".join(self.raw_parts)

    @property
    def visible_streamed_reply(self) -> str:
        return "".join(self.visible_parts)


@dataclass(frozen=True, slots=True)
class _LearningAgentRequest:
    conversation: Conversation
    buffer_output: bool


@dataclass(frozen=True, slots=True)
class _ProcessedLearningReply:
    raw_reply: str
    visible_reply: str
    pass_count: int


@dataclass(frozen=True, slots=True)
class _DeterministicLearningReply:
    reply: str
    source_refs: list[str] | None = None
    internal_passes: int | None = None
    citation_required: bool | None = None
    updates_learning_state: bool = True


def _localize_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> str:
    if not _should_localize_deterministic_reply(reply, user_input=user_input, config=config):
        return reply

    localized = _localized_deterministic_reply(reply, user_input=user_input, config=config)
    return localized if _valid_localized_deterministic_reply(localized, original=reply) else reply


def _should_localize_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> bool:
    return (
        bool(reply.strip())
        and bool(user_input.strip())
        and config is not None
        and bool(config.base_url)
        and bool(config.model)
    )


def _localized_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> str:
    if config is None:
        return ""
    conversation = Conversation()
    conversation.add("system", _DETERMINISTIC_FALLBACK_LOCALIZATION_PROMPT)
    conversation.add(
        "user",
        f"User request:\n{user_input.strip()}\n\nFallback message:\n{reply.strip()}",
    )
    parts: list[str] = []
    try:
        parts.extend(
            delta.content
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
                client_factory=build_client,
            )
            if delta.content
        )
    except EngineError:
        return ""
    return _strip_tool_call_markup("".join(parts)).strip()


def _valid_localized_deterministic_reply(localized: str, *, original: str) -> bool:
    return (
        bool(localized)
        and not _localized_reply_too_long(localized, original)
        and not _localized_reply_adds_citations(localized, original)
        and _localized_reply_preserves_assessment_label(localized, original)
        and _localized_reply_preserves_literals(localized, original)
    )


def _localized_reply_too_long(localized: str, original: str) -> bool:
    return len(localized) > max(len(original) * 3, len(original) + 600)


def _localized_reply_adds_citations(localized: str, original: str) -> bool:
    return bool(_OVERVIEW_CITATION_ID_RE.search(localized)) and not bool(
        _OVERVIEW_CITATION_ID_RE.search(original)
    )


def _localized_reply_preserves_assessment_label(localized: str, original: str) -> bool:
    assessment_label = _ASSESSMENT_LABEL_RE.match(original.strip())
    return assessment_label is None or localized.startswith(assessment_label.group(0))


def _localized_reply_preserves_literals(localized: str, original: str) -> bool:
    literals = _DETERMINISTIC_REPLY_LITERAL_RE.findall(original)
    return all(literal in localized for literal in literals)


def _repair_missing_evidence_citations(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if not _can_repair_evidence_citations(reply, evidence):
        return reply
    assert evidence is not None
    cleaned_reply, verification = _remove_unverified_citation_refs(reply, evidence)
    if appended_reply := _append_required_action_citation(
        plan,
        cleaned_reply,
        evidence,
        verification,
    ):
        return appended_reply
    return cleaned_reply


def _append_required_action_citation(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence,
    verification: VerificationResult,
) -> str:
    if not _should_append_required_action_citation(plan, verification):
        return ""
    first_item = evidence.items[0]
    return f"{reply.rstrip()} [{first_item.evidence_id}]"


def _should_append_required_action_citation(
    plan: LearningTurnPlan,
    verification: VerificationResult,
) -> bool:
    if verification.has_citations or not _plan_requires_citations(plan):
        return False
    return plan.action is not LearningAction.PRESENT


def _can_repair_evidence_citations(reply: str, evidence: TurnEvidence | None) -> bool:
    return bool(reply.strip() and evidence is not None and evidence.items)


def _remove_unverified_citation_refs(
    reply: str,
    evidence: TurnEvidence,
) -> tuple[str, VerificationResult]:
    verification = verify_citations(reply, evidence)
    if not verification.unverified:
        return reply, verification
    cleaned_reply = reply
    for evidence_id in verification.unverified:
        cleaned_reply = re.sub(rf"\s*\[\s*{re.escape(evidence_id)}\s*\]", "", cleaned_reply)
    return cleaned_reply, verify_citations(cleaned_reply, evidence)


def _evidence_bullet_lines(evidence: TurnEvidence, *, limit: int = 8) -> tuple[str, ...]:
    return tuple(
        f"- {_readable_material_label(item.source)}: "
        f"{_trace_excerpt(item.content, limit=700)} [{item.evidence_id}]"
        for item in evidence.items[:limit]
    )


def _evidence_notice(resolved: ResolvedTurnPlan) -> str:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return ""
    plan = resolved.learning_plan
    if plan is not None and _overview_turn(plan):
        notice = _overview_evidence_notice(visible_evidence)
    else:
        notice = _retrieved_evidence_notice(visible_evidence)
    return _append_evidence_assessment_notice(notice, resolved)


def _overview_evidence_notice(evidence: TurnEvidence) -> str:
    sources = list(dict.fromkeys(item.source for item in evidence.items))
    sampled_sources = evidence.sampled_source_count or len(sources)
    total_sources = evidence.total_source_count or sampled_sources
    return (
        f"Using {len(evidence.items)} overview evidence {_plural('excerpt', len(evidence.items))} "
        f"from {sampled_sources} of {total_sources} indexed "
        f"{_plural('source', total_sources)}: {_summarized_material_labels(sources)}"
    )


def _retrieved_evidence_notice(evidence: TurnEvidence) -> str:
    refs = _evidence_refs(evidence)
    return (
        f"Using {len(refs)} retrieved evidence {_plural('excerpt', len(refs))}: "
        f"{_summarized_refs(refs)}"
    )


def _summarized_material_labels(sources: Sequence[str], *, limit: int = 4) -> str:
    labels = ", ".join(_material_label(source) for source in sources[:limit])
    remaining = len(sources) - limit
    suffix = f", and {remaining} more" if remaining > 0 else ""
    return f"{labels}{suffix}"


def _summarized_refs(refs: Sequence[str], *, limit: int = 3) -> str:
    shown = ", ".join(refs[:limit])
    remaining = len(refs) - limit
    suffix = f", and {remaining} more" if remaining > 0 else ""
    return f"{shown}{suffix}"


def _append_evidence_assessment_notice(notice: str, resolved: ResolvedTurnPlan) -> str:
    assessment = resolved.evidence_assessment
    if assessment is None or assessment.sufficient:
        return notice
    action = assessment.recommended_action.replace("_", " ")
    return f"{notice}. Evidence sufficiency: {action} ({assessment.confidence:.0%})."


def _evidence_notice_metadata(
    resolved: ResolvedTurnPlan,
    session: ChatSession | None = None,
) -> dict[str, object]:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return {}
    plan = resolved.learning_plan
    task = _trace_task(plan)
    metadata: dict[str, object] = {
        "task": task,
        "refs": _evidence_refs(visible_evidence),
        "coverage": _evidence_trace_coverage(visible_evidence),
        "items": _evidence_trace_items(visible_evidence),
        "assessment": _evidence_assessment_trace(resolved.evidence_assessment),
    }
    if session is not None and plan is not None:
        metadata.update(_retrieval_audit_metadata(session, plan, resolved))
    return metadata


def _user_visible_reply(plan: LearningTurnPlan, reply: str) -> str:
    cleaned = _strip_tool_call_markup(reply).strip()
    cleaned = _normalize_escaped_evidence_citations(cleaned)
    cleaned = _strip_leading_control_json(cleaned)
    cleaned = _normalize_structural_table_reply(cleaned)
    cleaned = _unicode_math_reply(cleaned)
    if plan.action is LearningAction.SOURCE_QA:
        cleaned = _strip_unsolicited_learning_followup(cleaned)
    if plan.action is LearningAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", cleaned).strip()
    return cleaned


def _normalize_escaped_evidence_citations(reply: str) -> str:
    normalized = _ESCAPED_EVIDENCE_CITATION_RE.sub(r"[\1]", reply)
    return _PRIVATE_USE_EVIDENCE_CITATION_RE.sub(r"[\1]", normalized)


def _normalize_structural_table_reply(reply: str) -> str:
    if _contains_markdown_table(reply):
        return reply
    return _overview_pipe_table_as_markdown(reply) or reply


def _unicode_math_reply(reply: str) -> str:
    converted = _LATEX_DISPLAY_MATH_RE.sub(_unicode_math_match, reply)
    converted = _LATEX_INLINE_MATH_RE.sub(_unicode_math_match, converted)
    return _LATEX_BARE_MATHBB_RE.sub(_unicode_bare_mathbb_match, converted)


def _unicode_math_match(match: re.Match[str]) -> str:
    expression = match.group("expr").strip()
    converted = unicodeit.replace(expression)
    if _unicode_math_conversion_is_suspicious(converted):
        return expression
    return converted


def _unicode_bare_mathbb_match(match: re.Match[str]) -> str:
    expression = rf"\mathbb{{{match.group('symbol')}}}"
    converted = unicodeit.replace(expression)
    if _unicode_math_conversion_is_suspicious(converted):
        return match.group(0)
    return converted


def _unicode_math_conversion_is_suspicious(converted: str) -> bool:
    return "ł" in converted or "Ł" in converted


def _strip_leading_control_json(reply: str) -> str:
    if not reply.startswith("{"):
        return reply
    try:
        payload, end = json.JSONDecoder().raw_decode(reply)
    except json.JSONDecodeError:
        return _strip_malformed_leading_control_json(reply)
    tail = reply[end:].lstrip()
    if not tail or not is_string_mapping(payload):
        return reply
    if _LEADING_CONTROL_JSON_KEYS.isdisjoint(payload):
        return reply
    return tail


def _strip_malformed_leading_control_json(reply: str) -> str:
    match = _MALFORMED_LEADING_CONTROL_JSON_RE.match(reply)
    return reply[match.end() :].lstrip() if match else reply


def _should_buffer_learning_output(plan: LearningTurnPlan) -> bool:
    return (
        plan.buffer_response
        or plan.action is LearningAction.CHAT
        or _plan_requires_citations(plan)
    )


def _strip_unsolicited_learning_followup(reply: str) -> str:
    if not reply.strip():
        return reply
    return _strip_uncited_tail_after_last_citation(reply)


def _strip_uncited_tail_after_last_citation(reply: str) -> str:
    citation_end = _last_citation_end(reply)
    if citation_end is None:
        return reply.strip()
    keep_end = _citation_tail_keep_end(reply, citation_end)
    if not reply[keep_end:].strip():
        return reply.strip()
    return reply[:keep_end].rstrip()


def _has_uncited_tail_after_last_citation(reply: str) -> bool:
    citation_end = _last_citation_end(reply)
    if citation_end is None:
        return False
    keep_end = _citation_tail_keep_end(reply, citation_end)
    return bool(reply[keep_end:].strip())


def _last_citation_end(reply: str) -> int | None:
    matches = tuple(_OVERVIEW_CITATION_ID_RE.finditer(reply))
    if not matches:
        return None
    return matches[-1].end()


def _citation_tail_keep_end(reply: str, citation_end: int) -> int:
    keep_end = citation_end
    while keep_end < len(reply) and reply[keep_end] in " \t.,;:)]}":
        keep_end += 1
    return keep_end


def _strip_tool_call_markup(reply: str) -> str:
    cleaned = _TOOL_CALL_BLOCK_RE.sub("", reply)
    cleaned = _TOOL_CALL_OPEN_RE.sub("", cleaned)
    cleaned = _TOOL_CALL_CLOSE_RE.sub("", cleaned)
    kept_lines = [line for line in cleaned.splitlines() if "<tool_call" not in line.casefold()]
    return "\n".join(kept_lines)


def _run_bounded_internal_repairs(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    user_input: str,
    config: ChatConfig,
    contract: TurnContract | None = None,
) -> tuple[str, int]:
    repaired = reply
    passes = 1  # pass 1 = initial model generation
    if _overview_turn(plan) and repaired == _overview_unavailable_reply():
        return repaired, passes
    for _ in range(_MAX_INTERNAL_PASSES - 1):
        previous = repaired
        repaired = _repair_table_source_coverage_output(
            plan,
            repaired,
            evidence,
            contract=contract,
        )
        repaired = _repair_structurally_invalid_evidence_output(
            plan,
            repaired,
            evidence,
            user_input=user_input,
            config=config,
            contract=contract,
        )
        repaired = _repair_unverified_evidence_quotes(repaired, evidence)
        repaired = _repair_missing_evidence_citations(plan, repaired, evidence)
        passes += 1
        if repaired == previous:
            break
    return repaired, passes


def _repair_table_source_coverage_output(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None,
) -> str:
    if not _table_reply_needs_source_coverage_repair(plan, reply, evidence, contract):
        return reply
    assert evidence is not None
    table = _deterministic_evidence_table(evidence)
    return table or reply


def _table_reply_needs_source_coverage_repair(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    contract: TurnContract | None,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.SOURCE_QA}:
        return False
    if not _contract_requests_table(contract) or evidence is None or not evidence.items:
        return False
    if _available_evidence_source_count(evidence) < _TABLE_MIN_DISTINCT_SOURCES:
        return False
    return _cited_evidence_source_count(reply, evidence) < _TABLE_MIN_DISTINCT_SOURCES


def _available_evidence_source_count(evidence: TurnEvidence) -> int:
    return len({item.source for item in evidence.items})


def _cited_evidence_source_count(reply: str, evidence: TurnEvidence) -> int:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[evidence_id.casefold()]
        for evidence_id in _reply_evidence_ids(reply)
        if evidence_id.casefold() in source_by_id
    }
    return len(cited_sources)


def _deterministic_evidence_table(evidence: TurnEvidence) -> str:
    cited_items = _overview_fallback_citation_items(evidence, limit=3)
    if len({item.source for item, _cue in cited_items}) < _TABLE_MIN_DISTINCT_SOURCES:
        return ""
    return _deterministic_overview_table(cited_items)


def _repair_structurally_invalid_evidence_output(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    user_input: str,
    config: ChatConfig,
    contract: TurnContract | None = None,
) -> str:
    if not _evidence_output_needs_model_repair(plan, reply, evidence, contract=contract):
        return reply
    assert evidence is not None
    if _contract_requests_table(contract) and not _contains_markdown_table(reply):
        table = _compact_overview_table_reply(reply, evidence)
        if table:
            return table
    deterministic = _deterministic_evidence_pointer_repair(reply, evidence)
    if deterministic:
        return deterministic
    if len(reply) > _MATERIAL_REPLY_MAX_CHARS:
        compacted = _compact_verified_cited_reply(reply, evidence)
        if compacted:
            return compacted
    if config.base_url is None or not config.model:
        return reply
    conversation = Conversation()
    conversation.add("system", _EVIDENCE_OUTPUT_REPAIR_SYSTEM_PROMPT)
    conversation.add(
        "user",
        _evidence_output_repair_context(reply, evidence, user_input=user_input),
    )
    candidate = _strip_unsolicited_learning_followup(
        _strip_tool_call_markup(_stream_one_shot_model_text(config, conversation)).strip()
    )
    if not _valid_repaired_evidence_output(candidate, evidence):
        return (
            _deterministic_evidence_pointer_repair(reply, evidence, allow_unbalanced=True) or reply
        )
    return candidate


def _evidence_output_needs_model_repair(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.SOURCE_QA}:
        return False
    if evidence is None or not evidence.items:
        return False
    verification = verify_citations(reply, evidence)
    if not verification.has_citations:
        return True
    if _contains_markdown_table(reply) and verification.all_verified:
        return len(reply) > _OVERVIEW_MAX_TABLE_CHARS
    if len(reply) > _MATERIAL_REPLY_MAX_CHARS:
        return True
    if _CITATION_ONLY_REPLY_RE.match(reply):
        return True
    return bool(_OVERVIEW_CITATION_ID_RE.search(reply)) and (
        _thin_evidence_pointer(reply) or _reply_has_unbalanced_inline_markup(reply)
    )


def _thin_evidence_pointer(reply: str) -> bool:
    if not _OVERVIEW_CITATION_ID_RE.search(reply):
        return False
    if reply.strip().endswith((".", "!", "?")):
        return False
    if re.search(r"[.!?]\s*(?:\[(?:e|E)\d+\]\s*)+[.,;:]?\s*$", reply):
        return False
    without_citations = _OVERVIEW_CITATION_ID_RE.sub(" ", reply)
    words = re.findall(r"\w+", without_citations)
    return len(words) <= _THIN_EVIDENCE_POINTER_MAX_WORDS


def _deterministic_evidence_pointer_repair(
    reply: str,
    evidence: TurnEvidence,
    *,
    allow_unbalanced: bool = False,
) -> str:
    if _reply_has_unbalanced_inline_markup(reply) and not allow_unbalanced:
        return ""
    if not (
        _CITATION_ONLY_REPLY_RE.match(reply)
        or _thin_evidence_pointer(reply)
        or (allow_unbalanced and _reply_has_unbalanced_inline_markup(reply))
    ):
        return ""
    evidence_by_id = {item.evidence_id.casefold(): item for item in evidence.items}
    for evidence_id in _reply_evidence_ids(reply):
        item = evidence_by_id.get(evidence_id.casefold())
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item)
        if excerpt:
            return f"Check [{item.evidence_id}]: “{excerpt}” [{item.evidence_id}]."
    return ""


def _reply_evidence_ids(reply: str) -> tuple[str, ...]:
    seen: set[str] = set()
    ids: list[str] = []
    for match in _OVERVIEW_CITATION_ID_RE.finditer(reply):
        evidence_id = f"E{match.group('id')}"
        if evidence_id not in seen:
            ids.append(evidence_id)
            seen.add(evidence_id)
    return tuple(ids)


def _evidence_pointer_excerpt(item: EvidenceChunk) -> str:
    lines = [line.strip() for line in unescape(item.content).splitlines() if line.strip()]
    if lines and lines[0].startswith("#") and len(lines) > 1:
        lines = lines[1:]
    text = " ".join(lines or [unescape(item.content)])
    text = re.sub(r"^#+\s*", "", " ".join(text.split())).strip()
    for candidate in _overview_sentence_candidates(text):
        excerpt = _trim_overview_cue(candidate, limit=220)
        if excerpt and _source_pointer_excerpt_is_useful(excerpt):
            return excerpt
    return ""


def _source_pointer_excerpt_is_useful(excerpt: str) -> bool:
    compact = "".join(char for char in excerpt if char.isalnum())
    if len(compact) < 3:
        return False
    return any(char.isalpha() for char in compact) or len(compact) >= 6


def _valid_repaired_evidence_output(candidate: str, evidence: TurnEvidence) -> bool:
    if not candidate or _CITATION_ONLY_REPLY_RE.match(candidate):
        return False
    if _reply_has_unbalanced_inline_markup(candidate):
        return False
    verification = verify_citations(candidate, evidence)
    return verification.has_citations and verification.all_verified


def _compact_verified_cited_reply(reply: str, evidence: TurnEvidence) -> str:
    selected: list[str] = []
    for unit in _cited_reply_units(reply):
        candidate = "\n".join((*selected, unit)).strip()
        if len(candidate) > _MATERIAL_REPLY_MAX_CHARS and selected:
            break
        verification = verify_citations(unit, evidence)
        if not (verification.has_citations and verification.all_verified):
            continue
        selected.append(unit)
        if len("\n".join(selected)) >= _MATERIAL_REPLY_MAX_CHARS:
            break
    compacted = "\n".join(selected).strip()
    return compacted if compacted and len(compacted) < len(reply.strip()) else ""


def _cited_reply_units(reply: str) -> tuple[str, ...]:
    line_units = tuple(
        line.strip()
        for line in reply.splitlines()
        if line.strip() and _OVERVIEW_CITATION_ID_RE.search(line)
    )
    if len(line_units) > 1:
        return line_units
    return tuple(
        unit.strip()
        for unit in re.split(r"(?<=[.!?])\s+|(?<=\])\s+(?=[A-ZÄÖÜ])", reply)
        if unit.strip() and _OVERVIEW_CITATION_ID_RE.search(unit)
    )


def _repair_unverified_evidence_quotes(reply: str, evidence: TurnEvidence | None) -> str:
    if evidence is None or not evidence.items or not reply:
        return reply
    for quote in _reply_source_quote_fragments(reply):
        if not _quote_fragment_in_evidence(quote, evidence):
            return _evidence_quote_repair_reply(reply, evidence) or reply
    return reply


def _reply_source_quote_fragments(reply: str) -> tuple[str, ...]:
    fragments: list[str] = []
    for match in _INLINE_QUOTED_TEXT_RE.finditer(reply):
        phrase = " ".join(match.group("text").split())
        if len(phrase) >= 24:
            fragments.append(phrase)
    return tuple(fragments)


def _quote_fragment_in_evidence(quote: str, evidence: TurnEvidence) -> bool:
    normalized_quote = _normalized_query_text(quote)
    if not normalized_quote:
        return True
    return any(
        normalized_quote in _normalized_query_text(f"{item.chunk.heading} {item.content}")
        for item in evidence.items
    )


def _evidence_quote_repair_reply(reply: str, evidence: TurnEvidence) -> str:
    evidence_by_id = {item.evidence_id: item for item in evidence.items}
    for evidence_id in (*_reply_evidence_ids(reply), evidence.items[0].evidence_id):
        item = evidence_by_id.get(evidence_id)
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item) or _trace_excerpt(
            " ".join(unescape(item.content).split()),
            limit=220,
        )
        if excerpt:
            return f"“{excerpt}” [{item.evidence_id}]"
    return ""


def _evidence_output_repair_context(
    reply: str,
    evidence: TurnEvidence,
    *,
    user_input: str,
) -> str:
    lines = [
        f"User request: {user_input.strip() or '(none)'}",
        "Draft answer:",
        reply.strip(),
        "",
        "Evidence excerpts:",
    ]
    for item in evidence.items[:8]:
        compact_text = " ".join(unescape(item.content).split())
        if len(compact_text) > 700:
            compact_text = f"{compact_text[:699]}…"
        lines.extend(
            (
                "",
                f"Evidence {item.evidence_id}",
                f"Source: {item.source}",
                f"Text: {compact_text}",
            )
        )
    return "\n".join(lines)


_EVIDENCE_OUTPUT_REPAIR_SYSTEM_PROMPT = (
    "Repair the draft into a concise user-visible answer using only the evidence excerpts. "
    "Return only the final answer. Every material claim must cite evidence IDs from the "
    "provided excerpts. Do not return citation IDs alone; name the claim or phrase the "
    "evidence supports. Do not add optional next steps, offers, menus, or study-plan prompts."
)


def _reply_has_unbalanced_inline_markup(reply: str) -> bool:
    return reply.count("**") % 2 == 1 or reply.count("__") % 2 == 1 or reply.count("`") % 2 == 1


def _isolated_recall_conversation(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    contract: TurnContract | None,
) -> Conversation | None:
    if _should_use_material_answer_conversation_window(plan, contract):
        return None
    if plan.action in {
        LearningAction.CALIBRATE,
        LearningAction.PROMPT_RECALL,
        LearningAction.REFUSE_REVEAL,
        LearningAction.WAIT_READY_REMINDER,
    }:
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    if (
        original_learning_state.phase is LearningPhase.RECALL
        and plan.action is LearningAction.CHAT
        and plan.retrieval_query is None
    ):
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    return None


def _learning_extra_system_prompt(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str = "",
) -> str:
    contract_context = _turn_contract_prompt_context(resolved.turn_contract)
    extra_system_prompt = (
        f"{plan.prompt}\n\n{contract_context}" if contract_context else plan.prompt
    )
    prior_answer_context = _prior_answer_prompt_context(
        session.conversation,
        user_input=user_input,
        contract=resolved.turn_contract,
    )
    if prior_answer_context:
        extra_system_prompt = f"{extra_system_prompt}\n\n{prior_answer_context}"
    if plan.action is LearningAction.PRIORITY:
        priority_context = _build_priority_context(session)
        if priority_context:
            extra_system_prompt = f"{extra_system_prompt}\n\n{priority_context}"
    return _append_evidence_assessment_prompt(extra_system_prompt, resolved)


def _turn_contract_prompt_context(contract: TurnContract | None) -> str:
    if contract is None:
        return ""
    ask = _trace_excerpt(contract.canonical_request or contract.original_user_input, limit=140)
    lines = [
        (
            "Turn: "
            f"intent={contract.resolved_intent or 'unknown'}; "
            f"ask={ask}; "
            f"mode={contract.answer_mode}; fmt={contract.answer_format}; "
            f"retrieval={contract.retrieval_strategy}; cite={contract.citation_required}."
        )
    ]
    if contract.prior_turn_original_user_input and _contract_context_needs_prior_turn(contract):
        lines.append(
            "Prior: "
            f"intent={contract.prior_turn_resolved_intent or 'unknown'}; "
            f"refs={_intent_contract_refs_text(contract.prior_turn_evidence_refs)}."
        )
    lines.append(
        "Use current evidence for facts. Conversation text resolves references or requested shape "
        "only. Cite source claims; keep inference brief and clearly separated; keep compact; "
        "no offers or next-step prompts."
    )
    if contract.direct_evidence_required:
        lines.append(
            "Direct-evidence turn: state only claims explicit in current evidence; "
            "otherwise abstain."
        )
    if contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
        lines.append("Pure rewrite: preserve prior claims and citations; add no new source facts.")
    elif contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        lines.append(
            "Referenced-answer reasoning: answer the user's reasoning/application request "
            "directly. Use the prior answer to identify the claim, cite source facts from "
            "evidence, and keep concise inference separate. Prior answer citations are not "
            "current evidence IDs."
        )
    return "\n".join(lines)


def _contract_context_needs_prior_turn(contract: TurnContract) -> bool:
    if (
        contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    ):
        return False
    return contract.is_followup or contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }


def _prior_turn_canonical_request_excerpt(contract: TurnContract) -> str:
    return _trace_excerpt(contract.prior_turn_canonical_request, limit=160) or "unspecified"


def _prior_answer_prompt_context(
    conversation: Conversation,
    *,
    user_input: str,
    contract: TurnContract | None,
) -> str:
    if contract is None or not _should_include_prior_answer_context(contract):
        return ""
    recent_assistant = _prior_answer_context_messages(
        conversation,
        user_input,
        contract=contract,
    )
    if not recent_assistant:
        return ""
    context_lines: list[str] = ["Prior assistant reply (reference context only):"]
    for index, message in enumerate(recent_assistant, start=1):
        excerpt = _prior_answer_context_excerpt(message.content)
        if not excerpt:
            continue
        context_lines.extend((f"Answer {index}:", excerpt))
    if len(context_lines) == 1:
        return ""
    last_assistant = recent_assistant[-1]
    structure = (
        _prior_answer_structure_context(last_assistant.content)
        if contract.prior_answer_reference or contract.prior_answer_positions
        else ""
    )
    if structure:
        context_lines.extend(("Prior answer structure:", structure))
    if contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        context_lines.append(
            "Use this to identify the referenced claim. Answer the user's reasoning/application "
            "request directly; cite current evidence IDs and keep concise inference separate."
        )
    elif contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
        context_lines.append(
            "If this is a pure rewrite, preserve claims and citations and add no facts."
        )
    else:
        context_lines.append(
            "Use this only to resolve references. Cite only current evidence IDs."
        )
    return "\n".join(context_lines)


def _prior_answer_context_excerpt(content: str) -> str:
    excerpt = _trace_excerpt(content, limit=_PRIOR_ANSWER_CONTEXT_LIMIT)
    cleaned = _OVERVIEW_CITATION_BRACKET_RE.sub(_prior_context_citation_bracket, excerpt)
    return re.sub(r"\s+([,.;:!?])", r"\1", cleaned).strip()


def _prior_context_citation_bracket(match: re.Match[str]) -> str:
    citations = tuple(_OVERVIEW_CITATION_TOKEN_RE.finditer(match.group("body")))
    if not citations:
        return match.group(0)
    return ""


def _prior_answer_structure_context(content: str) -> str:
    cited_claims = _prior_answer_cited_claims(content)
    list_item_count = _prior_answer_list_item_count(content)
    lines = [
        f"- cited_claims={len(cited_claims)}",
        f"- list_items={list_item_count}",
        "- If the requested prior-answer item is absent, say it is not available.",
    ]
    if cited_claims:
        lines.append("- cited_claims_in_order:")
        lines.extend(
            f"  {index}. {claim}" for index, claim in enumerate(cited_claims[:5], start=1)
        )
    return "\n".join(lines)


def _prior_answer_cited_claims(content: str) -> tuple[str, ...]:
    claims: list[str] = []
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content):
        if not _citation_ends_prior_claim(content, match.end()):
            continue
        fragment = _prior_answer_fragment_before_citation(content, match.start())
        if not fragment:
            continue
        claim = fragment
        if claim not in claims:
            claims.append(claim)
    return tuple(claims)


def _citation_ends_prior_claim(content: str, citation_end: int) -> bool:
    index = citation_end
    while index < len(content) and content[index] in " \t)]}":
        index += 1
    return index >= len(content) or content[index] in ".!?\n" or content[index].isupper()


def _prior_answer_fragment_before_citation(content: str, citation_start: int) -> str:
    group_start = _prior_citation_group_start(content, citation_start)
    prefix = content[:group_start].rstrip()
    if not prefix:
        return ""
    if prefix[-1:] in ".!?":
        prefix = prefix[:-1].rstrip()
    boundary = _prior_answer_sentence_boundary(prefix)
    boundary = max(boundary, _previous_prior_citation_boundary(content, before=group_start))
    fragment = prefix[boundary + 1 :].strip()
    fragment = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", fragment).strip()
    return _trace_excerpt(fragment, limit=180)


def _prior_answer_sentence_boundary(prefix: str) -> int:
    boundary = -1
    for match in re.finditer(r"(?:[.!?;](?=\s)|\n)", prefix):
        boundary = match.start()
    return boundary


def _prior_citation_group_start(content: str, citation_start: int) -> int:
    prefix = content[:citation_start]
    match = _TRAILING_EVIDENCE_CITATION_GROUP_RE.search(prefix)
    return match.start() if match is not None else citation_start


def _previous_prior_citation_boundary(content: str, *, before: int) -> int:
    boundary = -1
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content[:before]):
        if _citation_ends_prior_claim(content, match.end()):
            boundary = max(boundary, match.end() - 1)
    return boundary


def _prior_answer_list_item_count(content: str) -> int:
    return sum(1 for line in content.splitlines() if re.match(r"\s*(?:[-*+]\s+|\d+[.)]\s+)", line))


def _should_include_prior_answer_context(contract: TurnContract | None) -> bool:
    return (
        contract is not None
        and contract.is_followup
        and _contract_needs_prior_answer_context(contract)
    )


def _prior_answer_context_messages(
    conversation: Conversation,
    user_input: str,
    *,
    contract: TurnContract,
) -> tuple[Message, ...]:
    limit = 5 if contract.prior_answer_positions else 1
    recent = _recent_assistant_messages(conversation, user_input, limit=limit)
    if not contract.prior_answer_reference:
        return recent
    selected = _prior_answer_message_for_contract(recent, contract)
    return (selected,) if selected is not None else ()


def _prior_answer_message_for_contract(
    messages: Sequence[Message],
    _contract: TurnContract,
) -> Message | None:
    if not messages:
        return None
    return messages[-1]


def _contract_needs_prior_answer_context(contract: TurnContract) -> bool:
    return contract.prior_answer_reference or contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }


def _contract_evidence_refs_text(contract: TurnContract) -> str:
    return ", ".join(contract.evidence_refs) if contract.evidence_refs else "none"


def _contract_prior_positions_text(contract: TurnContract) -> str:
    return (
        ", ".join(str(position) for position in contract.prior_answer_positions)
        if contract.prior_answer_positions
        else "none"
    )


def _postprocess_learning_reply(
    plan: LearningTurnPlan,
    raw_reply: str,
    visible_reply: str,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str,
    config: ChatConfig,
) -> _ProcessedLearningReply:
    shape_reply = _shape_validation_reply(raw_reply)
    original_shape_reply = shape_reply
    if _needs_overview_fallback(
        plan,
        shape_reply,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    ):
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            rejected_reply=shape_reply,
            contract=resolved.turn_contract,
        )
        raw_reply = fallback_reply or _overview_unavailable_reply()
        visible_reply = raw_reply

    visible_reply, pass_count = _run_bounded_internal_repairs(
        plan,
        visible_reply,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
        user_input=user_input,
        config=config,
    )
    visible_reply = _normalize_structural_table_reply(visible_reply)
    visible_reply = _unicode_math_reply(visible_reply)
    if (
        _needs_overview_fallback(
            plan,
            visible_reply,
            resolved.turn_evidence,
            contract=resolved.turn_contract,
        )
        and resolved.turn_evidence is not None
    ):
        repaired_reply = _overview_model_fallback_reply(
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            rejected_reply=visible_reply,
            allow_table=_contract_requests_table(resolved.turn_contract),
            allow_list=_contract_requests_list(resolved.turn_contract),
        )
        if not repaired_reply and resolved.turn_evidence is not None:
            repaired_reply = _compact_overview_citation_inventory(
                original_shape_reply,
                resolved.turn_evidence,
                allow_table=_contract_requests_table(resolved.turn_contract),
                allow_list=_contract_requests_list(resolved.turn_contract),
            )
        if not repaired_reply and resolved.turn_evidence is not None:
            repaired_reply = _overview_fallback_reply(
                plan,
                resolved.turn_evidence,
                user_input=user_input,
                config=config,
                rejected_reply=visible_reply,
                contract=resolved.turn_contract,
            )
        raw_reply = repaired_reply or _overview_unavailable_reply()
        visible_reply = raw_reply
    return _ProcessedLearningReply(
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        pass_count=pass_count,
    )


def _shape_validation_reply(raw_reply: str) -> str:
    cleaned = _strip_tool_call_markup(raw_reply).strip()
    cleaned = _normalize_escaped_evidence_citations(cleaned)
    return _strip_leading_control_json(cleaned)


def _deterministic_learning_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> _DeterministicLearningReply | None:
    if prior_absence_reply := _prior_answer_position_absence_reply(
        session,
        resolved.turn_contract,
    ):
        return prior_absence_reply
    if prior_source_object_absence_reply := _prior_answer_source_object_absence_reply(
        session,
        resolved.turn_contract,
    ):
        return prior_source_object_absence_reply
    if abstain_reply := _source_qa_abstain_reply(plan, resolved):
        return _DeterministicLearningReply(abstain_reply, citation_required=False)
    if prior_list_transform_reply := _prior_answer_list_transform_reply(
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_list_transform_reply
    if prior_target_phrase_reply := _prior_answer_target_phrase_reply(
        session,
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_target_phrase_reply
    if prior_single_citation_reply := _prior_answer_single_citation_reply(
        session,
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_single_citation_reply
    if overview_followup_reply := _deterministic_broad_overview_followup_reply(
        session,
        plan,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    ):
        source_refs = _evidence_refs(resolved.turn_evidence) if resolved.turn_evidence else None
        return _DeterministicLearningReply(overview_followup_reply, source_refs=source_refs)
    if resolved.turn_evidence is not None and resolved.turn_evidence.items:
        return None
    if missing_reply := _missing_indexed_material_reply(session, plan.action):
        return _DeterministicLearningReply(missing_reply, updates_learning_state=False)
    if no_match_reply := _no_matching_indexed_evidence_reply(
        session,
        plan,
        resolved.turn_contract,
    ):
        return _DeterministicLearningReply(no_match_reply)
    return None


def _prior_answer_position_absence_reply(
    session: ChatSession,
    contract: TurnContract | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.prior_answer_position_basis not in {"cited_claims", "list_items"}
    ):
        return None
    requested_positions = contract.prior_answer_positions or _implicit_prior_answer_positions(
        contract,
    )
    if not requested_positions:
        return None
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    selected_answer = _prior_answer_message_for_contract(recent_assistant, contract)
    if selected_answer is None:
        return None
    available_count = _prior_answer_position_basis_count(
        selected_answer.content,
        basis=contract.prior_answer_position_basis,
    )
    missing_positions = tuple(
        position for position in requested_positions if position > available_count
    )
    if available_count == 0 and contract.prior_answer_position_basis == "list_items":
        cited_claim_count = len(_prior_answer_cited_claims(selected_answer.content))
        cited_claims_cover_positions = all(
            position <= cited_claim_count for position in requested_positions
        )
        if cited_claim_count and cited_claims_cover_positions:
            return None
    if not missing_positions:
        return None
    reply = _prior_missing_position_text(
        available_count=available_count,
        missing_positions=missing_positions,
        basis=contract.prior_answer_position_basis,
    )
    return _DeterministicLearningReply(reply, citation_required=False)


def _prior_answer_source_object_absence_reply(
    session: ChatSession,
    contract: TurnContract | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.prior_answer_positions
        or not contract.citation_required
    ):
        return None
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    selected_answer = _prior_answer_message_for_contract(recent_assistant, contract)
    if selected_answer is None or _prior_answer_has_any_structure(selected_answer.content):
        return None
    return _DeterministicLearningReply(
        "The prior answer does not contain a cited material claim to extend.",
        citation_required=False,
    )


def _prior_answer_list_transform_reply(
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or contract.answer_mode != ANSWER_MODE_TRANSFORM_PRIOR
        or contract.answer_format != ANSWER_FORMAT_LIST
        or evidence is None
        or len(evidence.items) < 2
    ):
        return None
    cited_items = [
        (item, excerpt) for item in evidence.items if (excerpt := _evidence_pointer_excerpt(item))
    ][:2]
    if not cited_items:
        return None
    reply = "\n".join(
        f"{index}. {excerpt} [{item.evidence_id}]"
        for index, (item, excerpt) in enumerate(cited_items, start=1)
    )
    return _DeterministicLearningReply(reply, source_refs=_evidence_refs(evidence))


def _prior_answer_target_phrase_reply(
    session: ChatSession,
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.answer_mode not in {ANSWER_MODE_FROM_EVIDENCE, ANSWER_MODE_REASON_FROM_PRIOR}
        or evidence is None
        or not evidence.items
    ):
        return None
    selected_answer = _selected_prior_answer(session, contract)
    if selected_answer is None:
        return None
    for phrase in _quoted_followup_target_phrases(contract):
        if not _normalized_text_contains(selected_answer.content, phrase):
            continue
        item = _evidence_item_containing_text(evidence, phrase)
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item)
        if not excerpt:
            continue
        return _DeterministicLearningReply(
            f"“{excerpt}” [{item.evidence_id}].",
            source_refs=_evidence_refs(evidence),
        )
    return None


def _prior_answer_single_citation_reply(
    session: ChatSession,
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE
        or contract.prior_answer_positions
        or not contract.citation_required
        or _quoted_followup_target_phrases(contract)
        or evidence is None
        or not evidence.items
    ):
        return None
    selected_answer = _selected_prior_answer(session, contract)
    if selected_answer is None:
        return None
    cited_refs = _prior_answer_citation_refs(
        selected_answer.content,
        session.last_turn_contract,
    )
    if len(cited_refs) != 1:
        return None
    item = _evidence_item_by_ref(evidence, cited_refs[0])
    if item is None:
        return None
    excerpt = _evidence_pointer_excerpt(item)
    if not excerpt:
        return None
    return _DeterministicLearningReply(
        f"“{excerpt}” [{item.evidence_id}].",
        source_refs=_evidence_refs(evidence),
    )


def _selected_prior_answer(session: ChatSession, contract: TurnContract) -> Message | None:
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    return _prior_answer_message_for_contract(recent_assistant, contract)


def _quoted_followup_target_phrases(contract: TurnContract) -> tuple[str, ...]:
    text = " ".join(
        part for part in (contract.followup_target, contract.canonical_request) if part
    )
    phrases: list[str] = []
    seen: set[str] = set()
    for match in _INLINE_QUOTED_TEXT_RE.finditer(text):
        phrase = " ".join(match.group("text").split())
        key = _normalized_query_text(phrase)
        if not key or key in seen or not _quoted_followup_phrase_is_semantic(phrase):
            continue
        phrases.append(phrase)
        seen.add(key)
    return tuple(phrases)


def _quoted_followup_phrase_is_semantic(phrase: str) -> bool:
    without_citations = _OVERVIEW_CITATION_ID_RE.sub(" ", phrase)
    compact = "".join(char for char in without_citations if char.isalnum())
    return len(compact) >= 3


def _normalized_text_contains(text: str, needle: str) -> bool:
    normalized_text = _normalized_query_text(text)
    normalized_needle = _normalized_query_text(needle)
    return bool(normalized_needle and normalized_needle in normalized_text)


def _evidence_item_containing_text(
    evidence: TurnEvidence,
    text: str,
) -> EvidenceChunk | None:
    return next(
        (
            item
            for item in evidence.items
            if _normalized_text_contains(f"{item.chunk.heading}\n{item.content}", text)
        ),
        None,
    )


def _prior_answer_citation_refs(
    content: str,
    prior_contract: TurnContract | None,
) -> tuple[str, ...]:
    if prior_contract is None or not prior_contract.evidence_refs:
        return ()
    cited_refs: list[str] = []
    seen: set[str] = set()
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content):
        ref = _prior_citation_ref(match.group("id"), prior_contract.evidence_refs)
        if not ref or ref in seen:
            continue
        cited_refs.append(ref)
        seen.add(ref)
    return tuple(cited_refs)


def _prior_citation_ref(citation_number: str, refs: Sequence[str]) -> str:
    try:
        index = int(citation_number) - 1
    except ValueError:
        return ""
    if index < 0 or index >= len(refs):
        return ""
    return refs[index]


def _evidence_item_by_ref(evidence: TurnEvidence, ref: str) -> EvidenceChunk | None:
    return next((item for item in evidence.items if _evidence_item_ref(item) == ref), None)


def _evidence_item_ref(item: EvidenceChunk) -> str:
    return f"{item.source}#chunk={item.chunk_index}"


def _prior_answer_position_basis_count(content: str, *, basis: str) -> int:
    if basis == "cited_claims":
        return len(_prior_answer_cited_claims(content))
    if basis == "list_items":
        return _prior_answer_list_item_count(content)
    return 0


def _prior_answer_has_any_structure(content: str) -> bool:
    return (
        bool(_prior_answer_cited_claims(content))
        or _prior_answer_list_item_count(content) > 0
        or _OVERVIEW_CITATION_ID_RE.search(content) is not None
    )


def _implicit_prior_answer_positions(contract: TurnContract) -> tuple[int, ...]:
    if contract.prior_answer_position_basis == "list_items":
        return (2,)
    return ()


def _prior_missing_position_text(
    *,
    available_count: int,
    missing_positions: Sequence[int],
    basis: str,
) -> str:
    missing = _number_list_text(missing_positions)
    label = _prior_position_label(basis)
    return (
        "That prior-answer position is absent: the referenced answer has only "
        f"{_count_label(available_count, label)}, so position {missing} "
        "is not available."
    )


def _prior_position_label(basis: str) -> str:
    if basis == "list_items":
        return "separate list/table point"
    return "cited claim"


def _number_list_text(numbers: Sequence[int]) -> str:
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    return ", ".join(str(number) for number in numbers[:-1]) + f", and {numbers[-1]}"


def _source_qa_abstain_reply(
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> str:
    assessment = resolved.evidence_assessment
    if (
        plan.action is not LearningAction.SOURCE_QA
        or (resolved.turn_evidence is None and bool(plan.retrieval_query))
        or assessment is None
        or assessment.sufficient
        or assessment.recommended_action != "abstain"
    ):
        return ""
    return "The current evidence does not contain a direct source answer for this request."


def _plain_empty_reply(user_input: str, config: ChatConfig) -> str:
    return _localize_deterministic_reply(
        "I could not generate a response.",
        user_input=user_input,
        config=config,
    )


def _empty_learning_reply(
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str,
    config: ChatConfig,
) -> str:
    fallback_reply = _source_qa_evidence_reply(
        plan,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    )
    if fallback_reply:
        should_localize = True
    else:
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            contract=resolved.turn_contract,
        )
        should_localize = not bool(fallback_reply)
    if not fallback_reply:
        fallback_reply = _generic_empty_learning_reply(plan)
    return (
        _localize_deterministic_reply(fallback_reply, user_input=user_input, config=config)
        if should_localize
        else fallback_reply
    )


def _generic_empty_learning_reply(plan: LearningTurnPlan) -> str:
    if _overview_turn(plan):
        return _overview_unavailable_reply()
    if plan.action is LearningAction.ASSESS:
        return "PARTIAL: I could not generate a grounded assessment."
    return "I could not generate a prompt."


def _deterministic_broad_overview_followup_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None,
) -> str:
    if (
        evidence is None
        or not evidence.items
        or contract is None
        or not contract.is_followup
        or _contract_requests_table(contract)
        or not _material_overview_turn(plan, contract)
    ):
        return ""
    if contract.retrieval_strategy not in {
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
    }:
        return ""
    excluded_ids = _recent_current_evidence_citation_ids(
        session.conversation,
        contract.original_user_input,
        evidence,
    )
    reply = _deterministic_overview_fallback_reply(
        evidence,
        excluded_evidence_ids=excluded_ids,
    )
    if reply:
        return reply
    return _deterministic_overview_fallback_reply(evidence)


def _source_qa_evidence_reply(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> str:
    if not _can_answer_source_qa_from_evidence(plan, evidence, contract=contract):
        return ""
    assert evidence is not None
    return _evidence_quote_repair_reply("", evidence)


def _can_answer_source_qa_from_evidence(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if evidence is None or not evidence.items:
        return False
    return plan.action is LearningAction.SOURCE_QA and (
        plan.requires_direct_evidence
        or (contract is not None and contract.direct_evidence_required)
    )


def _append_evidence_assessment_prompt(
    prompt: str,
    resolved: ResolvedTurnPlan,
) -> str:
    if not _needs_evidence_assessment_prompt(prompt, resolved):
        return prompt
    assessment = resolved.evidence_assessment
    if assessment is None:
        return prompt
    return f"{prompt}\n\n{_evidence_assessment_prompt_line(assessment)}"


def _needs_evidence_assessment_prompt(prompt: str, resolved: ResolvedTurnPlan) -> bool:
    plan = resolved.learning_plan
    assessment = resolved.evidence_assessment
    if not prompt or plan is None or assessment is None:
        return False
    return plan.action not in {LearningAction.CHAT, LearningAction.CALIBRATE} and not (
        assessment.sufficient
    )


def _evidence_assessment_prompt_line(assessment: EvidenceAssessment) -> str:
    missing = ", ".join(assessment.missing_information) or "missing supporting evidence"
    refs = ", ".join(assessment.supporting_refs) or "none"
    action = assessment.recommended_action.replace("_", " ")
    return (
        "Evidence gate: "
        f"partial/insufficient ({assessment.confidence:.0%}); action={action}; "
        f"refs={refs}; missing={missing}. "
        "Do not fill gaps; scope any answer to cited evidence. If action=abstain, say the "
        "direct cited answer is missing for the resolved request; do not claim whole-corpus "
        "absence unless the current turn exhaustively checked the corpus."
    )


_PLAN_CONTRACT_LABEL_BY_ACTION: Mapping[LearningAction, str] = {
    LearningAction.PRIORITY: "material_overview",
    LearningAction.SOURCE_QA: "source_qa",
    LearningAction.PRESENT: "topic_presentation",
    LearningAction.CALIBRATE: "topic_drill",
    LearningAction.REVIEW: "topic_presentation",
    LearningAction.SIMPLIFY: "topic_presentation",
    LearningAction.HINT: "topic_drill",
    LearningAction.PROMPT_RECALL: "ready_for_recall",
    LearningAction.WAIT_READY_REMINDER: "ready_for_recall",
    LearningAction.REFUSE_REVEAL: "recall_clarification",
    LearningAction.ASSESS: "recall_answer_attempt",
    LearningAction.CHAT: "chat",
}


def _resolved_plan_intent(plan: LearningTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material_overview"
    return _PLAN_CONTRACT_LABEL_BY_ACTION.get(plan.action, plan.action.value)


def _resolved_turn_intent(resolved: ResolvedTurnPlan) -> str:
    if resolved.turn_contract is not None and resolved.turn_contract.resolved_intent:
        return resolved.turn_contract.resolved_intent
    return _resolved_plan_intent(resolved.learning_plan)


def _apply_turn_contract_to_plan(
    plan: LearningTurnPlan,
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> tuple[LearningTurnPlan, TurnContract]:
    contract = _contract_with_default_material_scope(plan, contract)
    if contract.resolved_intent in {"heph_action", "heph_help"}:
        updated_plan = replace(
            plan,
            original_user_input=contract.original_user_input,
            retrieval_query=None,
            retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
            evidence_refs=(),
            requires_direct_evidence=False,
            uses_overview_sampling=False,
        )
        updated_contract = replace(
            contract,
            retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
            retrieval_query="",
            evidence_refs=(),
            citation_required=False,
            direct_evidence_required=False,
        )
        return updated_plan, updated_contract
    retrieval_query = _semantic_retrieval_query(plan, contract)
    retrieval_strategy = contract.retrieval_strategy
    retrieval_strategy, retrieval_query = _stabilized_followup_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    )
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    ):
        retrieval_query = _fresh_current_request_query(contract)
        if _current_request_introduces_fresh_content(contract, prior_contract):
            retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
            retrieval_query = None
    if _reuse_prior_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        retrieval_query = _fresh_current_request_query(contract)
    if _source_request_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = _fresh_current_request_query(contract)
    if _transform_followup_introduces_substantive_request(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(
            contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        retrieval_query = _current_request_query(contract)
    if (
        _expanded_prior_should_use_current_request(
            contract,
            prior_contract=prior_contract,
            retrieval_strategy=retrieval_strategy,
        )
        and prior_contract is not None
    ):
        retrieval_query = _expanded_prior_followup_query(contract, prior_contract)
    if (
        retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and contract.resolved_intent != "material_overview"
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = contract.retrieval_query or contract.canonical_request or retrieval_query
    if _followup_lacks_replayable_prior_surface(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(contract, prior_answer_reference=True)
        retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
        retrieval_query = None
    elif (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not retrieval_query
    ):
        contract = replace(contract, prior_answer_reference=True)
    current_topic_query = _stabilized_current_topic_query(
        contract,
        retrieval_query,
        retrieval_strategy=retrieval_strategy,
    )
    if current_topic_query != retrieval_query:
        if (
            prior_contract is not None
            and prior_contract.evidence_refs
            and contract.is_followup
            and contract.resolved_intent == "source_qa"
        ):
            retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
    retrieval_query = current_topic_query
    if _prior_followup_has_literal_direct_requirement(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(contract, direct_evidence_required=False)
    if _prior_followup_should_reason_from_prior(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        contract = replace(
            contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
        )
    if _contract_requires_overview_sampling(contract, prior_contract=prior_contract):
        if contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
            contract = replace(
                contract,
                answer_mode=ANSWER_MODE_FROM_EVIDENCE,
                prior_answer_reference=False,
                prior_answer_positions=(),
                prior_answer_position_basis="",
            )
        retrieval_strategy = RETRIEVAL_STRATEGY_OVERVIEW
        retrieval_query = _overview_retrieval_surface(plan, contract, retrieval_query)
    elif (
        retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and _contract_has_specific_material_target(contract)
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = contract.retrieval_query or contract.canonical_request or retrieval_query
    if (
        plan.action is LearningAction.PRIORITY
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not contract.prior_answer_reference
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = plan.retrieval_query or contract.canonical_request or retrieval_query
    evidence_refs = _prior_evidence_refs_for_strategy(retrieval_strategy, prior_contract)
    if evidence_refs and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_query = None
    elif retrieval_query and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
    if (
        evidence_refs
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.is_followup
        and contract.direct_evidence_required
    ):
        contract = replace(contract, prior_answer_reference=True)

    requires_direct_evidence = _contract_requires_direct_source_support(
        plan,
        contract,
        retrieval_strategy=retrieval_strategy,
    )

    updated_plan = replace(
        plan,
        original_user_input=contract.original_user_input,
        retrieval_query=retrieval_query,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=evidence_refs,
        requires_direct_evidence=requires_direct_evidence,
        uses_overview_sampling=retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW,
    )
    updated_contract = replace(
        contract,
        resolved_intent=contract.resolved_intent or _resolved_plan_intent(updated_plan),
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query or "",
        evidence_refs=evidence_refs,
        citation_required=_plan_requires_citations(updated_plan),
        direct_evidence_required=updated_plan.requires_direct_evidence,
    )
    return updated_plan, updated_contract


def _reuse_prior_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
        and not contract.prior_answer_reference
        and _current_request_introduces_fresh_content(contract, prior_contract)
    )


def _prior_followup_should_reason_from_prior(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and not contract.direct_evidence_required
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and retrieval_strategy in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
    )


def _expanded_prior_should_use_current_request(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and not contract.prior_answer_reference
        and contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and (
            _current_turn_semantic_query(contract) is not None
            or _current_request_introduces_fresh_content(contract, prior_contract)
        )
    )


def _transform_followup_introduces_substantive_request(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and _current_request_introduces_fresh_content(contract, prior_contract)
    )


def _expanded_prior_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> str:
    current_semantic_query = _current_turn_semantic_query(contract)
    retrieval_query = _contract_retrieval_query(contract)
    followup_target = _contract_followup_target(contract)
    if (
        followup_target
        and retrieval_query
        and not _same_normalized_text(retrieval_query, contract.original_user_input)
        and _query_reuses_surface(retrieval_query, followup_target)
    ):
        return retrieval_query
    if current_semantic_query:
        if (
            retrieval_query
            and not _same_normalized_text(retrieval_query, contract.original_user_input)
            and _query_reuses_surface(
                retrieval_query,
                current_semantic_query,
            )
        ):
            return retrieval_query
        return current_semantic_query
    if _current_request_introduces_fresh_content(contract, prior_contract):
        return _current_request_query(contract)
    return retrieval_query or _current_request_query(contract)


def _query_reuses_surface(query: str, surface: str) -> bool:
    surface_terms = _normalized_query_terms(surface)
    if not surface_terms:
        return False
    return _query_term_overlap(query, surface_terms) >= min(2, len(surface_terms))


def _prior_followup_has_literal_direct_requirement(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.direct_evidence_required
        and not _contract_has_nonliteral_retrieval_surface(contract)
    )


def _contract_has_nonliteral_retrieval_surface(contract: TurnContract) -> bool:
    query = _contract_retrieval_query(contract)
    return bool(query) and not _same_normalized_text(query, contract.original_user_input)


def _fresh_current_request_query(contract: TurnContract) -> str:
    return (
        _contract_retrieval_query(contract)
        or contract.canonical_request.strip()
        or contract.original_user_input.strip()
    )


def _current_request_query(contract: TurnContract) -> str:
    return (
        contract.canonical_request.strip()
        or contract.original_user_input.strip()
        or _contract_retrieval_query(contract)
    )


def _source_request_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> bool:
    return (
        (prior_contract is None or not prior_contract.evidence_refs)
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and contract.resolved_intent in _CONTINUABLE_MATERIAL_INTENTS
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
        and not retrieval_query
        and len(_content_terms(contract.original_user_input)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS
    )


def _current_request_introduces_fresh_content(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> bool:
    current_terms = _content_terms(contract.original_user_input)
    if not current_terms:
        return False
    prior_terms = _content_terms(
        " ".join(
            text
            for text in (
                prior_contract.original_user_input,
                prior_contract.canonical_request,
                prior_contract.retrieval_query,
                " ".join(prior_contract.evidence_refs),
                contract.prior_answer_excerpt,
                contract.prior_turn_original_user_input,
                contract.prior_turn_canonical_request,
                " ".join(contract.prior_turn_evidence_refs),
            )
            if text
        )
    )
    if not prior_terms:
        return len(current_terms) >= _FRESH_CURRENT_REQUEST_MIN_TERMS
    fresh_terms = [
        term
        for term in current_terms
        if not any(_query_terms_match(term, prior_term) for prior_term in prior_terms)
    ]
    return len(fresh_terms) >= _FRESH_CURRENT_REQUEST_MIN_TERMS


def _content_terms(text: str) -> frozenset[str]:
    return frozenset(
        term
        for term in _normalized_query_terms(text)
        if len(term) >= 5 and any(char.isalpha() for char in term)
    )


def _contract_requires_direct_source_support(
    plan: LearningTurnPlan,
    contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    if contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        return False
    if contract.direct_evidence_required:
        return retrieval_strategy != RETRIEVAL_STRATEGY_REUSE_PRIOR or bool(
            _contract_has_nonliteral_retrieval_surface(contract)
        )
    if retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        return False
    return (
        plan.action is LearningAction.SOURCE_QA
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    )


def _contract_with_default_material_scope(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> TurnContract:
    if not _overview_turn(plan):
        return contract
    if contract.resolved_intent and contract.resolved_intent != "material_overview":
        return contract
    retrieval_query = _overview_retrieval_surface(plan, contract, plan.retrieval_query)
    if (
        plan.buffer_response
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and not contract.is_followup
    ):
        return replace(
            contract,
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            followup_target="",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=retrieval_query or "",
        )
    if (
        contract.answer_format == ANSWER_FORMAT_PLAIN
        and not contract.is_followup
        and not _contract_has_specific_material_target(contract)
    ):
        return replace(
            contract,
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            followup_target="",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=retrieval_query or "",
        )
    if contract.resolved_intent:
        return contract
    return replace(
        contract,
        resolved_intent="material_overview",
        canonical_request=contract.canonical_request
        or "Provide a compact overview of the material contents.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=retrieval_query or "",
    )


def _overview_retrieval_surface(
    plan: LearningTurnPlan,
    contract: TurnContract,
    fallback: str | None,
) -> str | None:
    for candidate in (
        contract.retrieval_query,
        fallback or "",
        contract.canonical_request,
        contract.original_user_input,
        plan.retrieval_query or "",
        plan.original_user_input,
    ):
        if candidate and not _lacks_retrievable_content(candidate):
            return candidate
    return None


def _followup_lacks_replayable_prior_surface(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and not contract.canonical_request
        and not _contract_followup_target(contract)
    )


def _contract_has_specific_material_target(contract: TurnContract) -> bool:
    return (
        contract.resolved_intent == "material_overview"
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and bool(_contract_followup_target(contract))
        and bool(contract.canonical_request)
    )


def _contract_requires_overview_sampling(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    if contract.resolved_intent != "material_overview" or (
        contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
    ):
        return False
    if contract.answer_format != ANSWER_FORMAT_PLAIN:
        return True
    if _contract_has_specific_material_target(contract):
        return False
    if not contract.is_followup:
        return True
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW:
        return True
    return not (
        contract.is_followup and prior_contract is not None and bool(prior_contract.evidence_refs)
    )


def _stabilized_followup_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> tuple[str, str | None]:
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.direct_evidence_required
        and _contract_has_nonliteral_retrieval_surface(contract)
    ):
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, _fresh_current_request_query(contract)
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and (target_phrase_query := _followup_target_phrase_query(contract))
    ):
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, target_phrase_query
    if (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and (
            contract.prior_answer_reference
            or (
                retrieval_strategy
                in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
                and not retrieval_query
            )
        )
    ):
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and _contract_is_material_overview(prior_contract)
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
    ):
        if (
            contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
            and contract.resolved_intent == "material_overview"
            and (semantic_query := _first_non_literal_followup_query(contract, prior_contract))
        ):
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
    ):
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and len(prior_contract.evidence_refs) > _BROAD_PRIOR_EVIDENCE_REF_COUNT
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
    if (
        contract.is_followup
        and retrieval_query
        and _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            if prior_contract is not None and prior_contract.evidence_refs:
                return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
            return RETRIEVAL_STRATEGY_RETRIEVE, semantic_query
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
        and retrieval_query
    ):
        if _same_normalized_text(retrieval_query, contract.original_user_input):
            semantic_query = _first_non_literal_followup_query(contract, prior_contract)
            if semantic_query:
                return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, retrieval_query
    if (
        prior_contract is None
        or not prior_contract.evidence_refs
        or not contract.is_followup
        or retrieval_strategy != RETRIEVAL_STRATEGY_RETRIEVE
        or not retrieval_query
        or not _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        return retrieval_strategy, retrieval_query

    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query


def _stabilized_current_topic_query(
    contract: TurnContract,
    retrieval_query: str | None,
    *,
    retrieval_strategy: str,
) -> str | None:
    if (
        contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and retrieval_query
        and not _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        return retrieval_query
    if (
        not contract.is_followup
        or contract.resolved_intent not in {"source_qa", "topic_presentation"}
        or contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE
        or contract.prior_answer_reference
        or retrieval_strategy in {RETRIEVAL_STRATEGY_NONE, RETRIEVAL_STRATEGY_REUSE_PRIOR}
    ):
        return retrieval_query
    current_query = contract.canonical_request
    if not current_query:
        return retrieval_query
    if not retrieval_query:
        return current_query
    request_terms = _normalized_query_terms(contract.original_user_input)
    if not request_terms:
        return retrieval_query
    return _best_current_request_query(
        request_terms,
        original_text=contract.original_user_input,
        candidates=(
            retrieval_query,
            current_query,
            _contract_followup_target(contract),
        ),
    )


def _best_current_request_query(
    request_terms: frozenset[str],
    *,
    original_text: str,
    candidates: Sequence[str | None],
) -> str | None:
    scored = [
        (
            _query_term_overlap(candidate, request_terms),
            _semantic_query_specificity(candidate),
            candidate,
        )
        for candidate in candidates
        if candidate
    ]
    if not scored:
        return None
    best = max(scored)[2]
    if not _same_normalized_text(best, original_text):
        return best
    if len(_content_terms(original_text)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS:
        return best
    semantic_candidates = [
        scored_candidate
        for scored_candidate in scored
        if not _same_normalized_text(scored_candidate[2], original_text)
    ]
    return max(semantic_candidates)[2] if semantic_candidates else best


def _first_non_literal_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> str | None:
    if semantic_current_query := _current_turn_semantic_query(contract):
        return semantic_current_query
    prior_candidates = [
        prior_contract.canonical_request if prior_contract is not None else "",
        prior_contract.retrieval_query if prior_contract is not None else "",
    ]
    semantic_candidates = [
        candidate
        for candidate in prior_candidates
        if candidate and not _same_normalized_text(candidate, contract.original_user_input)
    ]
    if not semantic_candidates:
        return None
    return max(semantic_candidates, key=_semantic_query_specificity)


def _current_turn_semantic_query(contract: TurnContract) -> str | None:
    current_candidates = [
        _contract_followup_target(contract),
        contract.canonical_request,
    ]
    semantic_current_candidates = [
        candidate
        for candidate in current_candidates
        if candidate and not _same_normalized_text(candidate, contract.original_user_input)
    ]
    if not semantic_current_candidates:
        return None
    return max(semantic_current_candidates, key=_semantic_query_specificity)


def _followup_target_phrase_query(contract: TurnContract) -> str:
    phrases = _quoted_followup_target_phrases(contract)
    if not phrases:
        return ""
    return max(phrases, key=_semantic_query_specificity)


def _contract_retrieval_query(contract: TurnContract) -> str:
    if _contract_has_empty_retrieval_query(contract):
        return ""
    return contract.retrieval_query.strip()


def _contract_has_empty_retrieval_query(contract: TurnContract) -> bool:
    return contract.retrieval_query.strip().casefold() == RETRIEVAL_STRATEGY_NONE


def _contract_is_material_overview(contract: TurnContract) -> bool:
    return (
        contract.resolved_intent == "material_overview"
        or contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    )


def _semantic_query_specificity(text: str) -> tuple[int, int]:
    normalized = _normalized_query_text(text)
    return (len(normalized.split()), len(normalized))


def _same_normalized_text(left: str, right: str) -> bool:
    return _normalized_query_text(left) == _normalized_query_text(right)


def _normalized_query_text(text: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"\W+", " ", folded.casefold()).strip()


def _normalized_query_terms(text: str) -> frozenset[str]:
    return frozenset(_normalized_query_text(text).split())


def _query_term_overlap(text: str, request_terms: frozenset[str]) -> int:
    return sum(
        1
        for term in _normalized_query_terms(text)
        if any(_query_terms_match(term, request_term) for request_term in request_terms)
    )


def _query_terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if min(len(left), len(right)) < 5:
        return False
    return difflib.SequenceMatcher(a=left, b=right).ratio() >= 0.84


def _semantic_retrieval_query(plan: LearningTurnPlan, contract: TurnContract) -> str | None:
    if not _plan_uses_material_retrieval(plan):
        return plan.retrieval_query
    if (
        contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and not _contract_has_specific_material_target(contract)
    ):
        return plan.retrieval_query
    if _contract_has_empty_retrieval_query(contract) and contract.retrieval_strategy in {
        RETRIEVAL_STRATEGY_NONE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    }:
        return None
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE and not _contract_retrieval_query(
        contract
    ):
        return None
    retrieval_query = _contract_retrieval_query(contract)
    return retrieval_query or contract.canonical_request or plan.retrieval_query


def _plan_uses_material_retrieval(plan: LearningTurnPlan) -> bool:
    return (
        plan.action in _EVIDENCE_REQUIRED_ACTIONS
        or plan.retrieval_query is not None
        or plan.use_expected_source_refs
    )


def _prior_evidence_refs_for_strategy(
    retrieval_strategy: str,
    prior_contract: TurnContract | None,
) -> tuple[str, ...]:
    if retrieval_strategy not in {
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    }:
        return ()
    if prior_contract is None:
        return ()
    if prior_contract.evidence_refs:
        return prior_contract.evidence_refs
    if prior_contract.prior_answer_reference:
        return prior_contract.prior_turn_evidence_refs
    return ()


def _turn_contract_with_evidence(
    contract: TurnContract,
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> TurnContract:
    refs = tuple(_evidence_refs(turn_evidence)) or contract.evidence_refs
    return replace(
        contract,
        retrieval_query=plan.retrieval_query or "",
        retrieval_strategy=plan.retrieval_strategy or contract.retrieval_strategy,
        evidence_refs=refs,
        citation_required=_plan_requires_citations(plan),
        direct_evidence_required=plan.requires_direct_evidence,
    )


def _turn_contract_with_prior_replay_state(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    conversation: Conversation,
    user_input: str,
) -> TurnContract:
    if prior_contract is None or not _contract_needs_prior_replay_state(contract):
        return contract
    prior_answer = (
        _last_cited_assistant_message(conversation, user_input)
        if prior_contract.evidence_refs
        else _last_assistant_message(conversation, user_input)
    )
    return replace(
        contract,
        prior_turn_original_user_input=prior_contract.original_user_input,
        prior_turn_resolved_intent=prior_contract.resolved_intent,
        prior_turn_canonical_request=prior_contract.canonical_request,
        prior_turn_evidence_refs=prior_contract.evidence_refs,
        prior_answer_excerpt=(
            _trace_excerpt(prior_answer.content, limit=_PRIOR_ANSWER_CONTEXT_LIMIT)
            if prior_answer is not None
            else ""
        ),
    )


def _reset_unreplayable_followup_state(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> tuple[LearningTurnPlan, TurnContract]:
    if not _contract_needs_prior_replay_state(contract):
        return plan, contract
    if _contract_has_replayable_grounding_surface(contract):
        return plan, contract

    retrieval_query = _unreplayable_followup_current_query(contract)
    retrieval_strategy = (
        RETRIEVAL_STRATEGY_RETRIEVE if retrieval_query else RETRIEVAL_STRATEGY_NONE
    )
    reset_contract = replace(
        contract,
        is_followup=False,
        followup_target="",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
        evidence_refs=(),
        prior_answer_reference=False,
        prior_answer_positions=(),
        prior_answer_position_basis="",
        prior_turn_original_user_input="",
        prior_turn_resolved_intent="",
        prior_turn_canonical_request="",
        prior_turn_evidence_refs=(),
        prior_answer_excerpt="",
    )
    requires_direct_evidence = _contract_requires_direct_source_support(
        plan,
        reset_contract,
        retrieval_strategy=retrieval_strategy,
    )
    reset_plan = replace(
        plan,
        retrieval_query=retrieval_query or None,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=(),
        requires_direct_evidence=requires_direct_evidence,
    )
    reset_contract = replace(
        reset_contract,
        citation_required=_plan_requires_citations(reset_plan),
        direct_evidence_required=reset_plan.requires_direct_evidence,
    )
    return reset_plan, reset_contract


def _unreplayable_followup_current_query(contract: TurnContract) -> str:
    if not contract.is_followup or not contract.prior_turn_original_user_input:
        return contract.canonical_request or contract.original_user_input
    if len(_content_terms(contract.original_user_input)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS:
        return contract.canonical_request or contract.original_user_input
    return ""


def _contract_has_replayable_grounding_surface(contract: TurnContract) -> bool:
    return bool(contract.prior_turn_evidence_refs) or (
        _OVERVIEW_CITATION_ID_RE.search(contract.prior_answer_excerpt) is not None
    )


def _contract_needs_prior_replay_state(contract: TurnContract) -> bool:
    return (
        contract.is_followup
        or contract.prior_answer_reference
        or contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
        or contract.retrieval_strategy
        in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
    )


def _turn_contract_with_validation(
    contract: TurnContract | None,
    notice: str,
) -> TurnContract | None:
    if contract is None:
        return None
    return replace(contract, validation_result=notice or "ok")


def _resolved_with_validation_result(
    resolved: ResolvedTurnPlan,
    notice: str,
) -> ResolvedTurnPlan:
    return replace(
        resolved,
        turn_contract=_turn_contract_with_validation(resolved.turn_contract, notice),
    )


def _resolved_with_visible_evidence_refs(
    resolved: ResolvedTurnPlan,
    reply: str,
    visible_evidence: TurnEvidence | None,
) -> ResolvedTurnPlan:
    contract = resolved.turn_contract
    if contract is None:
        return resolved
    return replace(
        resolved,
        turn_contract=replace(
            contract,
            evidence_refs=tuple(_reply_cited_evidence_refs(reply, visible_evidence)),
        ),
    )


def _reply_cited_evidence_refs(
    reply: str,
    evidence: TurnEvidence | None,
) -> list[str]:
    if evidence is None or not evidence.items:
        return []
    ref_by_id = {item.evidence_id.casefold(): _evidence_item_ref(item) for item in evidence.items}
    refs: list[str] = []
    seen: set[str] = set()
    for evidence_id in _reply_evidence_ids(reply):
        ref = ref_by_id.get(evidence_id.casefold())
        if ref is None or ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)
    return refs


def _turn_contract_can_seed_followup(
    contract: TurnContract | None,
    *,
    visible_evidence: TurnEvidence | None,
) -> bool:
    if contract is None:
        return False
    return (
        visible_evidence is not None
        or bool(contract.evidence_refs)
        or (contract.prior_answer_reference and bool(contract.prior_turn_evidence_refs))
        or contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        or contract.resolved_intent in {"heph_action", "heph_help"}
    )


def _prior_contract_for_followup_seed(session: ChatSession) -> TurnContract | None:
    contract = session.last_turn_contract
    if _turn_contract_can_seed_followup(contract, visible_evidence=session.last_turn_evidence):
        return contract
    return None


def _resolved_with_citation_requirement(
    resolved: ResolvedTurnPlan,
    *,
    citation_required: bool | None,
) -> ResolvedTurnPlan:
    if citation_required is None or resolved.turn_contract is None:
        return resolved
    return replace(
        resolved,
        turn_contract=replace(
            resolved.turn_contract,
            citation_required=citation_required,
        ),
    )


def _plan_requires_citations(plan: LearningTurnPlan | None) -> bool:
    if plan is None:
        return False
    return plan.action in {
        LearningAction.PRESENT,
        LearningAction.SOURCE_QA,
        LearningAction.PRIORITY,
        LearningAction.REVIEW,
        LearningAction.CALIBRATE,
        LearningAction.ASSESS,
        LearningAction.HINT,
        LearningAction.SIMPLIFY,
    }


def _overview_fallback_reply(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    user_input: str = "",
    config: ChatConfig | None = None,
    rejected_reply: str = "",
    contract: TurnContract | None = None,
) -> str:
    if not _material_overview_turn(plan, contract) or evidence is None or not evidence.items:
        return ""

    allow_table = _contract_requests_table(contract)
    allow_list = _contract_requests_list(contract)
    compacted_rejected = _compact_overview_citation_inventory(
        rejected_reply,
        evidence,
        allow_table=allow_table,
        allow_list=allow_list,
    )
    if compacted_rejected:
        return compacted_rejected
    model_reply = _overview_model_fallback_reply(
        evidence,
        user_input=user_input,
        config=config,
        rejected_reply=rejected_reply,
        allow_table=allow_table,
        allow_list=allow_list,
    )
    if model_reply:
        return model_reply
    if allow_table or allow_list:
        deterministic_reply = _deterministic_overview_fallback_reply(
            evidence,
            allow_table=allow_table,
            allow_list=allow_list,
        )
        if deterministic_reply:
            return deterministic_reply
    return _overview_model_fallback_reply(
        evidence,
        user_input=user_input,
        config=config,
        rejected_reply=rejected_reply,
        allow_table=allow_table,
        allow_list=allow_list,
    )


def _compact_overview_citation_inventory(
    rejected_reply: str,
    evidence: TurnEvidence,
    *,
    allow_table: bool,
    allow_list: bool,
) -> str:
    reply = _clean_overview_model_reply(rejected_reply)
    if allow_table and not _contains_markdown_table(reply):
        return _compact_overview_table_reply(reply, evidence)
    if len(_overview_citation_ids(reply)) <= _OVERVIEW_MAX_CITATIONS:
        return ""
    if allow_table:
        return _compact_overview_table_reply(reply, evidence)
    for base in _overview_inventory_base_candidates(reply):
        compacted = _compact_overview_citation_groups(base)
        if not compacted:
            continue
        compacted = _strip_unsolicited_learning_followup(compacted)
        compacted = re.sub(r"[ \t]+", " ", compacted).strip()
        for candidate in _overview_compaction_candidates(compacted):
            if _valid_overview_model_reply(
                candidate,
                evidence,
                allow_table=allow_table,
                allow_list=allow_list,
            ):
                return candidate
    return ""


def _compact_overview_table_reply(reply: str, evidence: TurnEvidence) -> str:
    table = _overview_markdown_table_block(reply) or _overview_pipe_table_as_markdown(reply)
    if not table:
        return ""
    compacted = _compact_overview_citation_groups(table) or table
    lines = compacted.splitlines()
    trimmed = "\n".join(lines[:_OVERVIEW_MAX_TABLE_ROWS])
    if _valid_overview_model_reply(trimmed, evidence, allow_table=True):
        return trimmed
    return ""


def _overview_markdown_table_block(reply: str) -> str:
    lines = reply.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if index + 1 >= len(lines) or not _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(
            lines[index + 1]
        ):
            continue
        end = index + 2
        while end < len(lines) and lines[end].strip().startswith("|"):
            end += 1
        return "\n".join(line.rstrip() for line in lines[index:end]).strip()
    return ""


def _overview_pipe_table_as_markdown(reply: str) -> str:
    rows = _overview_pipe_table_rows(reply)
    if len(rows) < 2:
        return ""
    width = max(len(row) for row in rows)
    normalized_rows = [(*row, *("",) * (width - len(row))) for row in rows]
    first_row = normalized_rows[0]
    if any(_OVERVIEW_CITATION_ID_RE.search(cell) for cell in first_row):
        header = tuple(f"Column {index}" for index in range(1, width + 1))
        data_rows = normalized_rows
    else:
        header = first_row
        data_rows = normalized_rows[1:]
    separator = tuple("---" for _ in range(width))
    rendered_rows = (header, separator, *data_rows[: max(1, _OVERVIEW_MAX_TABLE_ROWS - 2)])
    return "\n".join(_render_markdown_table_row(row) for row in rendered_rows)


def _overview_pipe_table_rows(reply: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in reply.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 2:
            continue
        rows.extend(_overview_pipe_table_line_rows(stripped))
    return tuple(rows)


def _overview_pipe_table_line_rows(line: str) -> tuple[tuple[str, ...], ...]:
    if _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line):
        return ()
    cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
    if len(cells) < 2:
        return ()
    if "" not in cells:
        return (cells,)
    rows: list[tuple[str, ...]] = []
    current: list[str] = []
    for cell in cells:
        if cell:
            current.append(cell)
            continue
        if len(current) >= 2:
            rows.append(tuple(current))
        current = []
    if len(current) >= 2:
        rows.append(tuple(current))
    return tuple(row for row in rows if not _markdown_separator_cells(row))


def _markdown_separator_cells(row: Sequence[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)


def _render_markdown_table_row(row: Sequence[str]) -> str:
    return "| " + " | ".join(_escape_markdown_table_cell(cell) for cell in row) + " |"


def _compact_overview_citation_groups(reply: str) -> str:
    compacted_brackets = _compact_overview_bracket_citation_groups(reply)
    group_matches = tuple(_OVERVIEW_CITATION_GROUP_RE.finditer(compacted_brackets))
    if not group_matches:
        return "" if compacted_brackets == reply else compacted_brackets

    compacted = _compact_adjacent_overview_citation_groups(compacted_brackets, group_matches)
    return "" if compacted == reply else compacted


def _compact_overview_bracket_citation_groups(reply: str) -> str:
    def compact_group(match: re.Match[str]) -> str:
        citation_ids = _overview_citation_ids(match.group(0))
        if len(citation_ids) <= 1:
            return match.group(0)
        compacted = _compact_overview_citation_ids(
            citation_ids,
            limit=min(len(citation_ids), _OVERVIEW_COMPACT_CITATION_GROUP_SIZE),
        )
        return "".join(f"[{citation_id}]" for citation_id in compacted)

    return _OVERVIEW_CITATION_BRACKET_RE.sub(compact_group, reply)


def _compact_adjacent_overview_citation_groups(
    reply: str,
    group_matches: Sequence[re.Match[str]],
) -> str:
    if not group_matches:
        return ""

    group_limit = min(
        _OVERVIEW_COMPACT_CITATION_GROUP_SIZE,
        max(1, _OVERVIEW_MAX_CITATIONS // len(group_matches)),
    )

    def compact_group(match: re.Match[str]) -> str:
        citation_ids = _compact_overview_citation_ids(
            _overview_citation_ids(match.group(0)),
            limit=group_limit,
        )
        return "".join(f"[{citation_id}]" for citation_id in citation_ids)

    return _OVERVIEW_CITATION_GROUP_RE.sub(compact_group, reply)


def _overview_inventory_base_candidates(reply: str) -> tuple[str, ...]:
    candidates = (_leading_overview_synthesis_block(reply), reply)
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        deduped.append(candidate)
        seen.add(key)
    return tuple(deduped)


def _leading_overview_synthesis_block(reply: str) -> str:
    inline_prefix = _leading_inline_list_prefix(reply)
    if inline_prefix:
        return inline_prefix
    selected: list[str] = []
    for line in reply.splitlines():
        stripped = line.strip()
        if not stripped:
            if selected:
                break
            continue
        if _overview_line_is_list_item(stripped):
            break
        selected.append(stripped)
    block = " ".join(selected).strip()
    if not block or block == reply.strip() or not _OVERVIEW_CITATION_ID_RE.search(block):
        return ""
    return block


def _leading_inline_list_prefix(reply: str) -> str:
    match = re.search(r"\s+(?:[-*+]|\d+[.)])\s+\S", reply)
    if match is None:
        return ""
    prefix = reply[: match.start()].strip()
    if not prefix or prefix == reply.strip() or not _OVERVIEW_CITATION_ID_RE.search(prefix):
        return ""
    return prefix


def _overview_line_is_list_item(line: str) -> bool:
    return re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line) is not None


def _overview_compaction_candidates(reply: str) -> tuple[str, ...]:
    candidates = (
        reply,
        _leading_overview_synthesis_block(reply),
        _trim_overview_long_uncited_lead(reply),
        _trim_overview_trailing_citation_inventory(reply),
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        deduped.append(candidate)
        seen.add(key)
    return tuple(deduped)


def _trim_overview_long_uncited_lead(reply: str) -> str:
    match = _OVERVIEW_CITATION_ID_RE.search(reply)
    if match is None or not _overview_has_long_uncited_lead(reply):
        return ""
    lead = reply[: match.start()].strip()
    suffix = reply[match.start() :].strip()
    body = _overview_lead_prefix_within_budget(lead)
    body = _trim_overview_dangling_lead_tail(body)
    if not body:
        return ""
    candidate = f"{body.rstrip(' .,;:')} {suffix}"
    return candidate if candidate.rstrip().endswith((".", "!", "?")) else f"{candidate}."


def _overview_lead_prefix_within_budget(lead: str) -> str:
    normalized = re.sub(r"\s+", " ", lead).strip()
    if not normalized:
        return ""
    if not _lead_exceeds_overview_budget(normalized):
        return normalized

    selected = ""
    for sentence in _overview_sentence_candidates(normalized):
        candidate = f"{selected} {sentence}".strip() if selected else sentence
        if _lead_exceeds_overview_budget(candidate):
            break
        selected = candidate
    if _overview_lead_is_substantive(selected):
        return selected

    selected = ""
    for clause in re.split(r"(?<=[,;:])\s+", normalized):
        if selected and not _overview_clause_is_substantive(clause):
            break
        candidate = f"{selected} {clause}".strip() if selected else clause
        if _lead_exceeds_overview_budget(candidate):
            break
        selected = candidate
    if _overview_lead_is_substantive(selected):
        return selected

    words = re.findall(r"\S+", normalized)
    selected_words: list[str] = []
    for word in words:
        candidate = " ".join((*selected_words, word))
        if _lead_exceeds_overview_budget(candidate):
            break
        selected_words.append(word)
    selected = " ".join(selected_words).strip()
    if _overview_lead_is_substantive(selected):
        return selected
    return ""


def _trim_overview_dangling_lead_tail(lead: str) -> str:
    if not lead or lead.rstrip().endswith((".", "!", "?")):
        return lead
    sentence_matches = tuple(re.finditer(r"[.!?]\s+", lead))
    if sentence_matches:
        trimmed_sentence = lead[: sentence_matches[-1].end()].strip()
        if _overview_lead_is_substantive(trimmed_sentence):
            return trimmed_sentence
    match = tuple(re.finditer(r"[,;:]\s+", lead))
    if not match:
        return lead
    tail_start = match[-1].end()
    tail = lead[tail_start:].strip(" ,;:")
    if len(re.findall(r"\b[\w'-]+\b", tail)) > 4:
        return lead
    trimmed = lead[: match[-1].start()].strip(" ,;:")
    return trimmed if _overview_lead_is_substantive(trimmed) else lead


def _overview_clause_is_substantive(clause: str) -> bool:
    return len(re.findall(r"\b[\w'-]+\b", clause.strip(" ,;:"))) >= 2


def _lead_exceeds_overview_budget(lead: str) -> bool:
    return (
        len(lead) > _OVERVIEW_MAX_UNCITED_LEAD_CHARS
        or len(re.findall(r"\b[\w'-]+\b", lead)) > _OVERVIEW_MAX_UNCITED_LEAD_WORDS
    )


def _overview_lead_is_substantive(lead: str) -> bool:
    return len(re.findall(r"\b[\w'-]+\b", lead)) >= _OVERVIEW_MIN_WORDS


def _trim_overview_trailing_citation_inventory(reply: str) -> str:
    match = _last_trailing_overview_citation_group(reply)
    if match is None:
        return ""
    prefix = reply[: match.start()].rstrip(" ,;:.")
    if not prefix or _OVERVIEW_CITATION_ID_RE.search(prefix):
        return ""
    suffix = re.sub(r"\s+", "", match.group(0))
    body = _overview_body_prefix_within_budget(prefix, suffix)
    if not body:
        return ""
    return f"{body.rstrip(' .,;:')} {suffix}."


def _last_trailing_overview_citation_group(reply: str) -> re.Match[str] | None:
    matches = tuple(_OVERVIEW_CITATION_GROUP_RE.finditer(reply))
    if not matches:
        return None
    match = matches[-1]
    keep_end = _citation_tail_keep_end(reply, match.end())
    if reply[keep_end:].strip():
        return None
    return match


def _overview_body_prefix_within_budget(prefix: str, suffix: str) -> str:
    budget = _OVERVIEW_MAX_CHARS - len(suffix) - 2
    if budget <= 0:
        return ""
    if len(prefix) <= budget:
        return prefix
    selected = ""
    for sentence in _overview_sentence_candidates(prefix):
        candidate = f"{selected} {sentence}".strip() if selected else sentence
        if len(candidate) > budget:
            break
        selected = candidate
    if not selected:
        return ""
    words = re.findall(r"\b[\w'-]+\b", selected)
    if len(words) < _OVERVIEW_MIN_WORDS:
        return ""
    return selected


def _compact_overview_citation_ids(
    citation_ids: Sequence[str],
    *,
    limit: int,
) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for citation_id in citation_ids:
        key = citation_id.casefold()
        if key in seen:
            continue
        deduped.append(citation_id)
        seen.add(key)
    if len(deduped) <= limit:
        return tuple(deduped)
    if limit <= 1:
        return (deduped[0],)
    indexes = {round(position * (len(deduped) - 1) / (limit - 1)) for position in range(limit)}
    return tuple(deduped[index] for index in sorted(indexes))


def _overview_unavailable_reply() -> str:
    return "I could not produce a grounded material overview from the current model output."


def _deterministic_overview_fallback_reply(
    evidence: TurnEvidence,
    *,
    allow_table: bool = False,
    allow_list: bool = False,
    excluded_evidence_ids: frozenset[str] | None = None,
) -> str:
    limit = _overview_required_distinct_source_count(evidence)
    cited_items = _overview_fallback_citation_items(
        evidence,
        limit=max(limit, _OVERVIEW_MIN_DISTINCT_SOURCES),
        excluded_evidence_ids=excluded_evidence_ids,
        table_cues=allow_table,
    )
    if not cited_items:
        return ""
    if allow_table:
        return _deterministic_overview_table(cited_items)
    if allow_list:
        return _deterministic_overview_list(cited_items)
    return _deterministic_overview_paragraph(cited_items)


def _deterministic_overview_paragraph(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    clauses = tuple(
        _overview_fallback_sentence(cue, item.evidence_id)
        for item, cue in items[:_OVERVIEW_FALLBACK_MAX_ITEMS]
    )
    return " ".join(clauses)


def _overview_fallback_sentence(cue: str, evidence_id: str) -> str:
    body = cue.rstrip(" .;:")
    return f"{body} [{evidence_id}]."


def _deterministic_overview_table(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        "| Source | Grounded excerpt |",
        "|---|---|",
    ]
    for item, cue_text in items:
        source = _escape_markdown_table_cell(item.source)
        cue = _escape_markdown_table_cell(cue_text)
        lines.append(f"| {source} | {cue} [{item.evidence_id}] |")
    return "\n".join(lines)


def _deterministic_overview_list(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        f"{index}. {cue} [{item.evidence_id}]"
        for index, (item, cue) in enumerate(items[:_OVERVIEW_MAX_LIST_ITEMS], start=1)
    ]
    return "\n".join(lines)


def _escape_markdown_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _overview_fallback_citation_items(
    evidence: TurnEvidence,
    *,
    limit: int = 4,
    excluded_evidence_ids: frozenset[str] | None = None,
    table_cues: bool = False,
) -> list[tuple[EvidenceChunk, str]]:
    cue_for_item = _overview_table_cue_for_item if table_cues else _overview_fallback_cue_for_item
    candidates = _overview_fallback_candidate_items(
        evidence,
        limit=limit,
        excluded_evidence_ids=excluded_evidence_ids or frozenset(),
    )
    selected = _select_overview_fallback_citation_items(
        candidates,
        limit=limit,
        cue_for_item=cue_for_item,
        suppress_repeated_cues=True,
    )
    if selected:
        return selected
    return _select_overview_fallback_citation_items(
        candidates,
        limit=limit,
        cue_for_item=_overview_table_cue_for_item,
        suppress_repeated_cues=False,
    )


def _select_overview_fallback_citation_items(
    candidates: Sequence[EvidenceChunk],
    *,
    limit: int,
    cue_for_item: Callable[[EvidenceChunk], str],
    suppress_repeated_cues: bool,
) -> list[tuple[EvidenceChunk, str]]:
    selected: list[tuple[EvidenceChunk, str]] = []
    seen_keys: set[tuple[str, int]] = set()
    repeated_cues = _overview_repeated_fallback_cues(candidates, cue_for_item=cue_for_item)
    for item in _spread_overview_candidate_items(candidates, limit=limit):
        key = (item.source, item.chunk_index)
        cue = cue_for_item(item)
        repeated = suppress_repeated_cues and _normalize_overview_topic(cue) in repeated_cues
        if key in seen_keys or not cue or repeated:
            continue
        selected.append((item, cue))
        seen_keys.add(key)
        if len(selected) >= limit:
            break
    return selected


def _spread_overview_candidate_items(
    candidates: Sequence[EvidenceChunk],
    *,
    limit: int,
) -> tuple[EvidenceChunk, ...]:
    if limit <= 0 or len(candidates) <= limit * 2:
        return tuple(candidates)
    if limit == 1:
        return (candidates[0],)
    indexes = {round(position * (len(candidates) - 1) / (limit - 1)) for position in range(limit)}
    selected = [candidates[index] for index in sorted(indexes)]
    selected.extend(item for index, item in enumerate(candidates) if index not in indexes)
    return tuple(selected)


def _overview_fallback_candidate_items(
    evidence: TurnEvidence,
    *,
    limit: int,
    excluded_evidence_ids: frozenset[str],
) -> tuple[EvidenceChunk, ...]:
    return tuple(
        item for item in evidence.items if item.evidence_id.casefold() not in excluded_evidence_ids
    )


def _overview_repeated_fallback_cues(
    items: Sequence[EvidenceChunk],
    *,
    cue_for_item: Callable[[EvidenceChunk], str] | None = None,
) -> frozenset[str]:
    if cue_for_item is None:
        cue_for_item = _overview_fallback_cue_for_item
    sources_by_cue: dict[str, set[str]] = {}
    for item in items:
        cue = cue_for_item(item)
        if not cue:
            continue
        sources_by_cue.setdefault(_normalize_overview_topic(cue), set()).add(item.source)
    return frozenset(cue for cue, sources in sources_by_cue.items() if len(sources) > 1)


def _overview_fallback_cue_for_item(item: EvidenceChunk) -> str:
    for candidate in _overview_content_cue_candidates(item):
        cue = _trim_overview_cue(_clean_overview_line(candidate))
        if _overview_fallback_cue_is_substantive(cue):
            return cue
    return ""


def _overview_table_cue_for_item(item: EvidenceChunk) -> str:
    fallback_cue = _overview_fallback_cue_for_item(item)
    if fallback_cue:
        return fallback_cue
    return _overview_cue_for_item(item)


def _overview_fallback_cue_is_substantive(cue: str) -> bool:
    if not _overview_cue_is_useful(cue):
        return False
    if (
        _overview_cue_looks_like_byline(cue)
        or _overview_cue_is_symbolic_fragment(cue)
        or _overview_starts_with_sentence_fragment(cue)
    ):
        return False
    words = re.findall(r"\b[\w'-]+\b", cue)
    if _looks_like_sentence(cue):
        return len(words) >= 3 and _overview_cue_has_content_word(words)
    if "," in cue or ";" in cue or any(_overview_symbolic_char(char) for char in cue):
        return False
    return len(words) >= 6


def _overview_cue_looks_like_byline(cue: str) -> bool:
    words = _letter_words(cue)
    if len(words) < 4:
        return False
    name_like = sum(1 for word in words if _looks_like_name_word(word))
    if len(words) >= 6 and name_like / len(words) >= 0.8:
        return True
    segments = [_letter_words(segment) for segment in re.split(r"[,;/]", cue) if segment.strip()]
    name_segments = sum(1 for segment in segments if _looks_like_person_name_segment(segment))
    return bool(segments) and name_segments >= 2 and name_segments / len(segments) >= 0.6


def _looks_like_person_name_segment(words: Sequence[str]) -> bool:
    return 1 <= len(words) <= 3 and all(_looks_like_name_word(word) for word in words)


def _overview_cue_is_symbolic_fragment(cue: str) -> bool:
    characters = tuple(char for char in cue if not char.isspace())
    if not characters:
        return True
    symbolic = sum(1 for char in characters if _overview_symbolic_char(char))
    if symbolic >= 3 and symbolic / len(characters) >= 0.08:
        return True
    words = _letter_words(cue)
    return bool(words) and symbolic >= len(words)


def _overview_symbolic_char(char: str) -> bool:
    return unicodedata.category(char) == "Sm" or char in "<>=|^_{}[]()"


def _looks_like_sentence(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?"))


def _overview_cue_has_content_word(words: Sequence[str]) -> bool:
    return any(sum(char.isalpha() for char in word) >= 6 for word in words)


def _overview_cue_for_item(item: EvidenceChunk) -> str:
    candidates = (*_overview_content_cue_candidates(item), *_overview_heading_candidates(item))
    for candidate in candidates:
        cue = _trim_overview_cue(_clean_overview_line(candidate))
        if _overview_cue_is_useful(cue):
            return cue
    return ""


def _overview_content_cue_candidates(item: EvidenceChunk) -> tuple[str, ...]:
    candidates: list[str] = []
    for line in _overview_content_lines(item.content):
        cleaned = _clean_overview_line(line)
        if not cleaned:
            continue
        candidates.extend(_overview_sentence_candidates(cleaned))
    return tuple(candidates)


def _overview_sentence_candidates(text: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip())
    return parts or (text,)


def _overview_cue_is_useful(cue: str) -> bool:
    normalized = " ".join(cue.casefold().split())
    if not normalized:
        return False
    words = normalized.split()
    if len(words) < 3 and not _overview_topic_is_useful(cue):
        return False
    if (
        _overview_heading_looks_like_metadata(cue)
        or _overview_topic_is_too_short_or_generic(normalized)
        or _OVERVIEW_FORMULA_RE.search(cue) is not None
    ):
        return False
    return not _overview_cue_looks_like_byline(cue)


def _clean_overview_line(line: str) -> str:
    cleaned = " ".join(unescape(line).strip().split())
    cleaned = cleaned.replace("[... truncated]", "").strip()
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", cleaned).strip()
    return cleaned.strip(" -:;")


def _trim_overview_cue(line: str, *, limit: int = 120) -> str:
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip(" ,;:.") + "…"


def _overview_model_fallback_reply(
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig | None,
    rejected_reply: str = "",
    allow_table: bool = False,
    allow_list: bool = False,
) -> str:
    usable_config = _overview_fallback_config(config)
    if usable_config is None:
        return ""
    conversation = Conversation()
    system_prompt = _OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT
    if allow_table:
        system_prompt = (
            f"{system_prompt}\nThe user requested a table. Produce a compact markdown table "
            "instead of prose, with concise cited cells and no source inventory."
        )
    if allow_list:
        system_prompt = (
            f"{system_prompt}\nThe user requested a list. Produce a compact cited list "
            "instead of prose."
        )
    conversation.add("system", system_prompt)
    conversation.add(
        "user",
        _overview_topic_normalization_context(
            evidence,
            user_input,
            rejected_reply=rejected_reply,
        ),
    )
    reply = _clean_overview_model_reply(_stream_one_shot_model_text(usable_config, conversation))
    for candidate in _overview_model_fallback_candidates(
        reply,
        allow_table=allow_table,
        allow_list=allow_list,
    ):
        if _valid_overview_model_reply(
            candidate,
            evidence,
            allow_table=allow_table,
            allow_list=allow_list,
        ):
            return candidate
    return ""


def _overview_model_fallback_candidates(
    reply: str,
    *,
    allow_table: bool,
    allow_list: bool,
) -> tuple[str, ...]:
    if not reply:
        return ()
    candidates = [reply]
    if allow_table:
        table = _overview_markdown_table_block(reply) or _overview_pipe_table_as_markdown(reply)
        if table:
            candidates.append(_compact_overview_citation_groups(table) or table)
    elif not allow_list:
        leading = _leading_overview_synthesis_block(
            _compact_overview_bracket_citation_groups(reply)
        )
        if leading:
            candidates.extend(_overview_compaction_candidates(leading))
        compacted = _compact_overview_citation_groups(reply)
        if compacted:
            candidates.extend(_overview_compaction_candidates(compacted))
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = _strip_unsolicited_learning_followup(candidate)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        if not cleaned or cleaned in seen:
            continue
        deduped.append(cleaned)
        seen.add(cleaned)
    return tuple(deduped)


def _overview_fallback_config(config: ChatConfig | None) -> ChatConfig | None:
    if config is None or not config.model:
        return None
    if not config.base_url and not config.provider_slug:
        return None
    return config


def _clean_overview_model_reply(model_text: str) -> str:
    if not model_text:
        return ""
    return _strip_tool_call_markup(model_text).strip()


def _valid_overview_model_reply(
    reply: str,
    evidence: TurnEvidence,
    *,
    allow_table: bool = False,
    allow_list: bool = False,
) -> bool:
    if not reply:
        return False
    if allow_table and not _contains_markdown_table(reply):
        return False
    if allow_list and _list_item_count(reply) == 0:
        return False
    verification = verify_citations(reply, evidence)
    return (
        verification.has_citations
        and verification.all_verified
        and not _overview_answer_has_bad_shape(reply, evidence, allow_table=allow_table)
    )


def _stream_one_shot_model_text(
    config: ChatConfig,
    conversation: Conversation,
    *,
    raise_errors: bool = False,
) -> str:
    parts: list[str] = []
    try:
        parts.extend(
            delta.content
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
                client_factory=build_client,
            )
            if delta.content
        )
    except EngineError:
        if raise_errors:
            raise
        return ""
    return "".join(parts)


def _learning_agent_output_from_buffer(
    plan: LearningTurnPlan,
    buffer: _LearningAgentBuffer,
) -> _LearningAgentOutput:
    streamed_reply = buffer.streamed_reply
    raw_reply = streamed_reply
    if not raw_reply and buffer.completion_event is not None:
        raw_reply = buffer.completion_event.full_text
    visible_reply = _user_visible_reply(plan, raw_reply)
    if _overview_turn(plan):
        raw_reply = visible_reply
    return _LearningAgentOutput(
        streamed_reply=streamed_reply,
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        completion_event=buffer.completion_event,
    )


def _learning_agent_request(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    session: ChatSession,
    contract: TurnContract | None,
) -> _LearningAgentRequest:
    conversation = _learning_agent_conversation(
        plan,
        original_learning_state,
        user_input,
        session,
        contract,
    )
    return _LearningAgentRequest(
        conversation=conversation,
        buffer_output=_should_buffer_learning_output(plan),
    )


def _learning_agent_conversation(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    session: ChatSession,
    contract: TurnContract | None,
) -> Conversation:
    isolated = _isolated_recall_conversation(
        plan,
        original_learning_state,
        user_input,
        contract,
    )
    if isolated is not None:
        return isolated
    if _should_use_material_answer_conversation_window(plan, contract):
        return _material_answer_conversation_window(session.conversation, user_input)
    return session.conversation


def _material_answer_conversation_window(
    conversation: Conversation,
    user_input: str,
) -> Conversation:
    window = Conversation()
    for message in _recent_material_context_messages(conversation, user_input):
        content = _material_context_message_content(message)
        if content:
            window.add(message.role, content)
    window.add("user", user_input)
    return window


def _recent_material_context_messages(
    conversation: Conversation,
    user_input: str,
) -> tuple[Message, ...]:
    messages = conversation.messages
    if messages and messages[-1].role == "user" and messages[-1].content == user_input:
        messages = messages[:-1]
    eligible = [
        message
        for message in messages
        if message.role in {"user", "assistant"} and message.content.strip()
    ]
    return tuple(eligible[-_MATERIAL_CONTEXT_MESSAGE_LIMIT:])


def _material_context_message_content(message: Message) -> str:
    content = message.content.strip()
    if message.role != "assistant":
        return content
    return _prior_answer_context_excerpt(content)


def _overview_topic_normalization_context(
    evidence: TurnEvidence,
    user_input: str,
    *,
    rejected_reply: str = "",
) -> str:
    lines = [
        f"User request: {user_input.strip() or '(none)'}",
        "Task rules:",
        "- Treat title pages, logistics, and boilerplate as non-substantive unless requested.",
        "- Infer substantive learning material by semantic context, not hardcoded keywords.",
    ]
    if rejected_reply.strip():
        lines.extend(
            (
                "",
                "Rejected draft to repair:",
                _trace_excerpt(rejected_reply, limit=1400),
            )
        )
    lines.append("Evidence excerpts:")
    for item in evidence.items[:12]:
        heading = item.chunk.heading or "none"
        compact_text = " ".join(unescape(item.content).split())
        if len(compact_text) > 700:
            compact_text = f"{compact_text[:699]}…"
        lines.extend(
            (
                "",
                f"Evidence {item.evidence_id}",
                f"Source: {item.source}",
                f"Heading: {heading}",
                f"Text: {compact_text}",
            )
        )
    return "\n".join(lines)


def _classified_user_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
    conversation: Conversation | None = None,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> str:
    return _resolved_user_intent(
        user_input,
        config=config,
        conversation=conversation,
        prior_intent=prior_intent,
        prior_contract=prior_contract,
    ).intent


def _resolved_user_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
    conversation: Conversation | None = None,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> TurnIntentResolution:
    if not user_input.strip() or config is None or not config.base_url or not config.model:
        return TurnIntentResolution()
    try:
        payload = _model_json_payload(
            config,
            system_prompt=(
                f"{_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT}\n"
                f"{_LEARNING_INTENT_NORMALIZATION_SCHEMA}"
            ),
            user_prompt=_intent_normalization_context(
                user_input,
                conversation,
                prior_intent=prior_intent,
                prior_contract=prior_contract,
            ),
            raise_errors=True,
        )
    except EngineError:
        if prior_intent in _CONTINUABLE_MATERIAL_INTENTS:
            return _low_confidence_prior_followup_resolution(
                user_input=user_input,
                prior_intent=prior_intent,
                prior_contract=prior_contract,
                confidence=0.0,
                expand_from_prior=False,
            )
        return TurnIntentResolution(confidence=0.0)
    intent, confidence = _classifier_intent_from_payload(payload)
    if confidence >= _MODEL_NORMALIZED_CONFIDENCE_THRESHOLD:
        resolution = intent_resolution_from_payload(payload, intent=intent, confidence=confidence)
        return _stabilized_followup_intent_resolution(
            resolution,
            user_input=user_input,
            prior_intent=prior_intent,
        )
    if prior_intent in _CONTINUABLE_MATERIAL_INTENTS:
        return _low_confidence_prior_followup_resolution(
            user_input=user_input,
            prior_intent=prior_intent,
            prior_contract=prior_contract,
            confidence=confidence,
            expand_from_prior=True,
        )
    return TurnIntentResolution(confidence=confidence)


def _low_confidence_prior_followup_resolution(
    *,
    user_input: str,
    prior_intent: str,
    prior_contract: TurnContract | None,
    confidence: float,
    expand_from_prior: bool,
) -> TurnIntentResolution:
    if prior_contract is None or not prior_contract.evidence_refs:
        return TurnIntentResolution(intent=prior_intent, confidence=confidence, is_followup=True)
    prior_request = prior_contract.canonical_request or prior_contract.original_user_input
    retrieval_strategy = (
        RETRIEVAL_STRATEGY_EXPAND_PRIOR if expand_from_prior else RETRIEVAL_STRATEGY_REUSE_PRIOR
    )
    return TurnIntentResolution(
        intent=prior_intent,
        canonical_request=user_input,
        is_followup=True,
        followup_target=prior_request,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        answer_format=prior_contract.answer_format,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=prior_request if expand_from_prior else "",
        prior_answer_reference=True,
        confidence=confidence,
    )


def _prior_contract_retrieval_surface(prior_contract: TurnContract) -> str:
    return (
        prior_contract.retrieval_query.strip()
        or prior_contract.canonical_request.strip()
        or prior_contract.original_user_input.strip()
    )


def _stabilized_intent_for_named_material(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    index: ArmoryIndex | None,
) -> TurnIntentResolution:
    if resolution.intent not in _CONTINUABLE_MATERIAL_INTENTS:
        return resolution
    query = _corpus_named_material_query(user_input, index)
    if not query:
        return resolution
    intent = (
        "topic_presentation" if resolution.intent == "material_overview" else resolution.intent
    )
    return replace(
        resolution,
        intent=intent,
        answer_mode="answer_from_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query=query,
        canonical_request=resolution.canonical_request or user_input,
    )


def _stabilized_intent_for_default_material_plan(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
    index: ArmoryIndex | None,
) -> TurnIntentResolution:
    if (
        prior_contract is None
        and _overview_turn(default_plan)
        and _lacks_retrievable_content(user_input)
        and (not resolution.intent or resolution.intent in _CONTINUABLE_MATERIAL_INTENTS)
    ):
        return TurnIntentResolution(
            intent="material_overview",
            canonical_request=resolution.canonical_request or user_input,
            confidence=resolution.confidence,
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            answer_format=resolution.answer_format,
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query="",
        )
    if (
        prior_contract is not None
        or not _overview_turn(default_plan)
        or resolution.intent != "source_qa"
    ):
        return resolution
    if not resolution.direct_evidence_required:
        return resolution
    if index is not None and _source_lookup_preserves_user_terms(resolution, index):
        return resolution
    return TurnIntentResolution(
        intent="material_overview",
        canonical_request=resolution.canonical_request or user_input,
        confidence=resolution.confidence,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        answer_format=resolution.answer_format,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=_overview_resolution_query(resolution, user_input, default_plan),
    )


def _overview_resolution_query(
    resolution: TurnIntentResolution,
    user_input: str,
    default_plan: LearningTurnPlan,
) -> str:
    for candidate in (
        resolution.retrieval_query,
        default_plan.retrieval_query or "",
        resolution.canonical_request,
        user_input,
        default_plan.original_user_input,
    ):
        if candidate and not _lacks_retrievable_content(candidate):
            return candidate
    return ""


def _lacks_retrievable_content(text: str) -> bool:
    return bool(text.strip()) and not tokenize(text)


def _unresolved_followup_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
) -> TurnIntentResolution:
    if resolution.intent or prior_contract is None or not _overview_turn(default_plan):
        return resolution
    return TurnIntentResolution(
        intent=prior_contract.resolved_intent or "source_qa",
        canonical_request=user_input,
        confidence=resolution.confidence,
        is_followup=True,
        followup_target=prior_contract.canonical_request or prior_contract.original_user_input,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        answer_format=prior_contract.answer_format,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        prior_answer_reference=True,
    )


def _source_lookup_preserves_user_terms(
    resolution: TurnIntentResolution,
    index: ArmoryIndex | None,
) -> bool:
    lookup_query = resolution.retrieval_query or resolution.canonical_request
    if not lookup_query.strip():
        return True
    query_terms = frozenset(tokenize(lookup_query))
    if not query_terms:
        return False
    if index is not None:
        return _query_has_index_anchor(query_terms, index)
    return False


def _query_has_index_anchor(query_terms: frozenset[str], index: ArmoryIndex) -> bool:
    corpus_terms = _index_query_terms(index)
    return not corpus_terms or any(
        _query_has_matching_term(term, corpus_terms) for term in query_terms
    )


def _index_query_terms(index: ArmoryIndex) -> frozenset[str]:
    return frozenset(
        token
        for document in index.documents
        for chunk in document.chunks
        for token in tokenize(chunk.text)
    )


def _query_has_matching_term(term: str, query_terms: frozenset[str]) -> bool:
    return any(_query_terms_match(term, query_term) for query_term in query_terms)


def _corpus_named_material_query(user_input: str, index: ArmoryIndex | None) -> str:
    if index is None:
        return ""
    normalized_user = f" {_normalized_query_text(user_input)} "
    if not normalized_user.strip():
        return ""
    for document in index.documents:
        label = _normalized_source_label(document.source)
        if label and f" {label} " in normalized_user:
            return f"{label} {user_input.strip()}".strip()
    return ""


def _normalized_source_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    stem = name.rsplit(".", maxsplit=1)[0]
    return _normalized_query_text(re.sub(r"[-_]+", " ", stem))


def _stabilized_followup_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str = "",
    prior_intent: str,
) -> TurnIntentResolution:
    if resolution.intent in {"heph_action", "heph_help"}:
        return replace(
            resolution,
            retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
            retrieval_query="",
            direct_evidence_required=False,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    if (
        resolution.direct_evidence_required
        and resolution.intent != "source_qa"
        and resolution.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    ):
        retrieval_query = resolution.retrieval_query or resolution.canonical_request
        retrieval_strategy = (
            RETRIEVAL_STRATEGY_RETRIEVE
            if resolution.retrieval_strategy
            in {RETRIEVAL_STRATEGY_NONE, RETRIEVAL_STRATEGY_OVERVIEW}
            else resolution.retrieval_strategy
        )
        return replace(
            resolution,
            intent="source_qa",
            retrieval_strategy=retrieval_strategy,
            retrieval_query=retrieval_query,
        )
    if (
        resolution.intent == "material_overview"
        and resolution.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and (
            not resolution.is_followup
            or prior_intent not in _CONTINUABLE_MATERIAL_INTENTS
            or resolution.answer_format != ANSWER_FORMAT_PLAIN
        )
    ):
        return replace(
            resolution,
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=(
                resolution.retrieval_query or resolution.canonical_request or user_input
            ),
        )
    if (
        prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    ):
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    if (
        prior_intent in {"material_overview", "topic_presentation"}
        and resolution.is_followup
        and resolution.intent == "source_qa"
        and resolution.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not resolution.direct_evidence_required
        and (resolution.prior_answer_reference or resolution.followup_target.strip())
    ):
        return replace(
            resolution,
            intent=prior_intent,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            retrieval_query="",
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    if prior_intent in _CONTINUABLE_MATERIAL_INTENTS and resolution.intent in {
        "scaffold_request",
        "hint_request",
        "material_review",
    }:
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
            retrieval_strategy=(
                resolution.retrieval_strategy
                if resolution.retrieval_strategy != RETRIEVAL_STRATEGY_NONE
                else RETRIEVAL_STRATEGY_REUSE_PRIOR
            ),
        )
    if (
        prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and resolution.answer_format == ANSWER_FORMAT_PLAIN
    ):
        if not _transform_resolution_points_at_prior_answer(
            resolution,
            user_input=user_input,
        ):
            return replace(resolution, answer_mode=ANSWER_MODE_FROM_EVIDENCE)
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
        )
    if (
        resolution.is_followup
        and prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.intent in {"priority_request", "driven_learning_calibration"}
    ):
        return replace(resolution, intent=prior_intent)
    return resolution


_PRIOR_REFERENCE_SHORT_TOKEN_LIMIT = 4
_PRIOR_REFERENCE_MIN_OVERLAP = 0.5


def _transform_resolution_points_at_prior_answer(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
) -> bool:
    if resolution.prior_answer_positions:
        return True
    if not (resolution.prior_answer_reference or resolution.followup_target.strip()):
        return False
    user_tokens = frozenset(tokenize(user_input))
    resolved_tokens = frozenset(
        token
        for text in (resolution.canonical_request, resolution.followup_target)
        for token in tokenize(text)
    )
    if user_tokens and not any(
        _query_has_matching_term(token, resolved_tokens) for token in user_tokens
    ):
        return False
    request_tokens = frozenset(tokenize(resolution.canonical_request))
    if len(request_tokens) <= _PRIOR_REFERENCE_SHORT_TOKEN_LIMIT:
        return True
    target_tokens = frozenset(tokenize(resolution.followup_target))
    if not target_tokens:
        return False
    overlap = len(request_tokens & target_tokens) / min(len(request_tokens), len(target_tokens))
    return overlap >= _PRIOR_REFERENCE_MIN_OVERLAP


def _intent_normalization_context(
    user_input: str,
    conversation: Conversation | None,
    *,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> str:
    lines: list[str] = []
    if routing_context := heph_product_routing_context():
        lines.extend(
            (
                "Heph self-knowledge routing context:",
                routing_context,
                "",
            )
        )
    if prior_context := _prior_turn_contract_intent_context(prior_contract, prior_intent):
        lines.extend(("Prior turn:", prior_context, ""))
    last_assistant = _last_assistant_message(conversation, user_input)
    if last_assistant is not None:
        lines.extend(
            (
                "Last reply:",
                _trace_excerpt(last_assistant.content, limit=240),
                "",
            )
        )
    lines.extend(("Current user request:", user_input.strip()))
    return "\n".join(lines)


def _prior_turn_contract_intent_context(
    contract: TurnContract | None,
    prior_intent: str,
) -> str:
    if contract is None and not prior_intent:
        return ""
    if contract is None:
        return f"intent={prior_intent}; refs=0."
    return (
        f"intent={contract.resolved_intent or prior_intent or 'unknown'}; "
        f"mode={contract.answer_mode}; retrieval={contract.retrieval_strategy}; "
        f"refs={_intent_contract_refs_text(contract.evidence_refs)}."
    )


def _intent_contract_refs_text(refs: Sequence[str], *, limit: int = 4) -> str:
    if not refs:
        return "none"
    visible = ", ".join(refs[:limit])
    remaining = len(refs) - limit
    if remaining <= 0:
        return visible
    return f"{visible}, +{remaining} more"


def _last_assistant_message(
    conversation: Conversation | None,
    user_input: str,
) -> Message | None:
    recent = _recent_assistant_messages(conversation, user_input, limit=1)
    return recent[-1] if recent else None


def _last_cited_assistant_message(
    conversation: Conversation | None,
    user_input: str,
) -> Message | None:
    for message in reversed(_recent_assistant_messages(conversation, user_input, limit=6)):
        if _OVERVIEW_CITATION_ID_RE.search(message.content):
            return message
    return _last_assistant_message(conversation, user_input)


def _recent_assistant_messages(
    conversation: Conversation | None,
    user_input: str,
    *,
    limit: int,
) -> tuple[Message, ...]:
    if conversation is None:
        return ()
    messages = [
        message
        for message in conversation.messages
        if message.role in {"user", "assistant"} and message.content.strip()
    ]
    if messages and _same_message_text(messages[-1].content, user_input):
        messages = messages[:-1]
    assistant_messages = [message for message in messages if message.role == "assistant"]
    if limit <= 0:
        return ()
    return tuple(assistant_messages[-limit:])


def _recent_current_evidence_citation_ids(
    conversation: Conversation | None,
    user_input: str,
    evidence: TurnEvidence,
    *,
    limit: int = 4,
) -> frozenset[str]:
    current_ids = {item.evidence_id.casefold() for item in evidence.items}
    cited_ids: set[str] = set()
    for message in _recent_assistant_messages(conversation, user_input, limit=limit):
        for match in _OVERVIEW_CITATION_ID_RE.finditer(message.content):
            evidence_id = f"E{match.group('id')}".casefold()
            if evidence_id in current_ids:
                cited_ids.add(evidence_id)
    return frozenset(cited_ids)


def _same_message_text(left: str, right: str) -> bool:
    return " ".join(left.split()) == " ".join(right.split())


def _model_json_payload(
    config: ChatConfig | None,
    *,
    system_prompt: str,
    user_prompt: str,
    raise_errors: bool = False,
) -> dict[str, object] | None:
    if config is None or not config.base_url or not config.model:
        return None
    conversation = Conversation()
    conversation.add("system", system_prompt)
    conversation.add("user", user_prompt)
    return parse_json_object_fragment(
        _stream_one_shot_model_text(config, conversation, raise_errors=raise_errors)
    )


def _classifier_intent_from_payload(
    payload: Mapping[str, object] | None,
) -> tuple[str, float]:
    if payload is None:
        return ("", 0.0)
    raw_intent = payload.get("intent")
    if not isinstance(raw_intent, str):
        return ("", 0.0)
    intent = re.sub(r"[^a-z0-9]+", "_", raw_intent.strip().casefold()).strip("_")
    if intent not in _MODEL_NORMALIZED_INTENTS:
        return ("", 0.0)
    return (intent, _normalized_confidence(payload.get("confidence")))


def _normalized_confidence(value: object) -> float:
    if isinstance(value, (int, float)):
        confidence = float(value)
    elif isinstance(value, str):
        try:
            confidence = float(value.strip().rstrip("%"))
        except ValueError:
            return 0.0
    else:
        return 0.0
    if confidence > 1.0:
        confidence /= 100.0
    return min(1.0, max(0.0, confidence))


def _overview_heading_candidates(item: EvidenceChunk) -> tuple[str, ...]:
    candidates = (item.chunk.heading, *_overview_markdown_headings(item.content))
    return tuple(topic for candidate in candidates if (topic := _clean_overview_line(candidate)))


def _overview_heading_looks_like_metadata(topic: str) -> bool:
    if _OVERVIEW_CONTACT_OR_URL_RE.search(topic) or _OVERVIEW_DATE_LINE_RE.search(topic):
        return True
    if _looks_like_sentence(topic):
        return False
    return _overview_heading_is_sparse_title_block(topic)


def _overview_heading_is_sparse_title_block(topic: str) -> bool:
    words = _letter_words(topic)
    if len(words) < 2:
        return False
    alnum_count = sum(char.isalnum() for char in topic)
    if alnum_count < 4:
        return True
    punctuation_count = sum(1 for char in topic if char in ",;:!?()[]{}")
    separator_count = sum(1 for char in topic if char in "-_/|")
    title_case_count = sum(1 for word in words if word[:1].isupper() and not word.isupper())
    mostly_labels = title_case_count / len(words) >= 0.8
    low_density = punctuation_count + separator_count >= max(2, len(words) // 2)
    return len(words) <= 6 and mostly_labels and low_density


def _overview_markdown_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in unescape(text).splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = _clean_overview_line(stripped)
        if heading:
            headings.append(heading)
    return headings


def _normalize_overview_topic(topic: str) -> str:
    return " ".join(topic.casefold().split())


def _overview_topic_is_useful(topic: str) -> bool:
    normalized = " ".join(topic.casefold().split())
    if _overview_topic_text_is_invalid(topic, normalized):
        return False
    return len(normalized.split()) <= 5


def _overview_topic_text_is_invalid(topic: str, normalized: str) -> bool:
    return any(
        (
            _overview_topic_is_too_short_or_generic(normalized),
            _OVERVIEW_FORMULA_RE.search(topic) is not None,
            _overview_topic_has_sentence_punctuation(topic),
        )
    )


def _overview_topic_is_too_short_or_generic(normalized: str) -> bool:
    words = normalized.split()
    if not words:
        return True
    if len(words) == 1 and sum(char.isalpha() for char in words[0]) < 6:
        return True
    return len(normalized) < 4


def _overview_topic_has_sentence_punctuation(topic: str) -> bool:
    return re.search(r"[.:;!?]|->|:=|=>", topic) is not None


def _overview_content_lines(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip()]


def _letter_words(line: str) -> list[str]:
    words = [word.strip(".,;:()[]{}") for word in line.split()]
    return [word for word in words if any(char.isalpha() for char in word)]


def _looks_like_name_word(word: str) -> bool:
    return word[:1].isupper() and not word.isupper()


def _needs_overview_fallback(
    plan: LearningTurnPlan,
    raw_reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if not _material_overview_turn(plan, contract) or evidence is None or not evidence.items:
        return False
    verification = verify_citations(raw_reply, evidence)
    if not verification.has_citations or not verification.all_verified:
        return True
    return _overview_answer_has_bad_shape(
        raw_reply,
        evidence,
        allow_table=_contract_requests_table(contract),
    )


def _material_overview_turn(
    plan: LearningTurnPlan,
    contract: TurnContract | None = None,
) -> bool:
    if contract is None:
        return _overview_turn(plan)
    if contract is not None and contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }:
        return (
            contract.resolved_intent == "material_overview"
            and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
            and not contract.prior_turn_evidence_refs
        )
    if _overview_turn(plan):
        return True
    return (
        contract.resolved_intent == "material_overview"
        and plan.action is LearningAction.PRESENT
        and not _contract_has_specific_material_target(contract)
        and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    )


def _overview_answer_has_bad_shape(
    raw_reply: str,
    evidence: TurnEvidence | None = None,
    *,
    allow_table: bool = False,
) -> bool:
    """Reject overview replies that are too thin, too noisy, or under-grounded."""
    citation_ids = _overview_citation_ids(raw_reply)
    words = re.findall(r"\b[\w'-]+\b", raw_reply)
    has_table = _contains_markdown_table(raw_reply)
    if allow_table and not has_table:
        return True
    max_chars = _OVERVIEW_MAX_TABLE_CHARS if has_table and allow_table else _OVERVIEW_MAX_CHARS
    if len(raw_reply) > max_chars:
        return True
    if not has_table and len(words) > _OVERVIEW_MAX_WORDS:
        return True
    if not has_table and _has_uncited_tail_after_last_citation(raw_reply):
        return True
    if not has_table and len(citation_ids) > _OVERVIEW_MAX_CITATIONS:
        return True
    if not has_table and _overview_starts_with_sentence_fragment(raw_reply):
        return True
    if not has_table and _overview_has_long_uncited_lead(raw_reply):
        return True
    if (
        not has_table
        and evidence is not None
        and _overview_is_extractive_inventory(raw_reply, evidence)
    ):
        return True
    if has_table and _markdown_table_row_count(raw_reply) > _OVERVIEW_MAX_TABLE_ROWS:
        return True
    if _list_item_count(raw_reply) > _OVERVIEW_MAX_LIST_ITEMS:
        return True
    if len(citation_ids) < _OVERVIEW_MIN_CITATIONS:
        return True
    if not has_table and len(words) < _OVERVIEW_MIN_WORDS:
        return True
    return evidence is not None and not _overview_covers_enough_sources(citation_ids, evidence)


def _overview_has_long_uncited_lead(raw_reply: str) -> bool:
    match = _OVERVIEW_CITATION_ID_RE.search(raw_reply)
    if match is None:
        return False
    lead = raw_reply[: match.start()].strip()
    if len(lead) > _OVERVIEW_MAX_UNCITED_LEAD_CHARS:
        return True
    return len(re.findall(r"\b[\w'-]+\b", lead)) > _OVERVIEW_MAX_UNCITED_LEAD_WORDS


def _contract_requests_table(contract: TurnContract | None) -> bool:
    return contract is not None and contract.answer_format == ANSWER_FORMAT_TABLE


def _contract_requests_list(contract: TurnContract | None) -> bool:
    return contract is not None and contract.answer_format == ANSWER_FORMAT_LIST


def _contains_markdown_table(text: str) -> bool:
    return any(_MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line) for line in text.splitlines())


def _markdown_table_row_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("|"))


def _list_item_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line))


def _overview_starts_with_sentence_fragment(text: str) -> bool:
    first_alpha = next((char for char in text.lstrip() if char.isalpha()), "")
    return bool(first_alpha) and first_alpha.islower()


def _overview_citation_ids(raw_reply: str) -> tuple[str, ...]:
    ids: list[str] = []
    for bracket in _OVERVIEW_CITATION_BRACKET_RE.finditer(raw_reply):
        ids.extend(
            f"E{match.group('id')}"
            for match in _OVERVIEW_CITATION_TOKEN_RE.finditer(bracket.group("body"))
        )
    return tuple(ids)


def _overview_covers_enough_sources(citation_ids: tuple[str, ...], evidence: TurnEvidence) -> bool:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[citation_id.casefold()]
        for citation_id in citation_ids
        if citation_id.casefold() in source_by_id
    }
    return len(cited_sources) >= _overview_required_distinct_source_count(evidence)


def _overview_is_extractive_inventory(raw_reply: str, evidence: TurnEvidence) -> bool:
    spans = _overview_cited_claim_spans(raw_reply)
    if len(spans) < _OVERVIEW_EXTRACTIVE_MIN_SPANS:
        return False
    copied = sum(1 for span in spans if _overview_span_is_copied(span, evidence))
    return copied >= _OVERVIEW_EXTRACTIVE_MIN_SPANS and (
        copied / len(spans) >= _OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO
    )


def _overview_cited_claim_spans(raw_reply: str) -> tuple[str, ...]:
    spans: list[str] = []
    start = 0
    for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply):
        span = _clean_overview_extract_span(raw_reply[start : match.start()])
        start = match.end()
        if len(tokenize(span)) >= _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
            spans.append(span)
    return tuple(spans)


def _clean_overview_extract_span(span: str) -> str:
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", span.strip())
    return cleaned.strip(" \t\r\n\"'\u201c\u201d\u2018\u2019.,;:")


def _overview_span_is_copied(span: str, evidence: TurnEvidence) -> bool:
    if len(tokenize(span)) < _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
        return False
    normalized_span = _overview_copy_normalized_text(span)
    return any(
        _overview_normalized_span_is_copied(
            normalized_span,
            _overview_copy_normalized_text(item.content),
        )
        for item in evidence.items
    )


def _overview_normalized_span_is_copied(span: str, evidence_text: str) -> bool:
    if not span or not evidence_text:
        return False
    if span in evidence_text:
        return True
    if len(span) < 32:
        return False
    return difflib.SequenceMatcher(a=span, b=evidence_text).ratio() >= 0.82


def _overview_copy_normalized_text(text: str) -> str:
    return " ".join(tokenize(text))


def _overview_required_distinct_source_count(evidence: TurnEvidence) -> int:
    available_source_count = len({item.source for item in evidence.items})
    if available_source_count <= _OVERVIEW_MIN_DISTINCT_SOURCES:
        return available_source_count
    proportional_floor = (available_source_count + 1) // 2
    return min(
        available_source_count,
        _OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES,
        max(_OVERVIEW_MIN_DISTINCT_SOURCES, proportional_floor),
    )


@dataclass(slots=True)
class TurnOrchestrator:
    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)
    last_internal_passes: int = field(default=1, init=False)
    _last_reply_citation_required: bool | None = field(default=None, init=False)

    def iter_events(
        self,
        user_input: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        original_messages = list(session.conversation.messages)
        original_learning_state = session.learning_state.clone()
        timer = Timer()
        self.last_reply = ""
        self.last_internal_passes = 1
        self._last_reply_citation_required = None

        input_decision = check_user_input(
            user_input,
            conversation=tuple(
                GuardrailMessage(role=message.role, content=message.content)
                for message in session.conversation.messages
            ),
        )
        if input_decision.blocks:
            yield GuardrailEvent(
                stage=input_decision.stage,
                action=input_decision.action,
                message=input_decision.message,
                metadata=input_decision.metadata,
            )
            self.last_reply = input_decision.message
            yield from _final_reply_events(self.last_reply)
            return
        if input_decision.warns:
            yield GuardrailEvent(
                stage=input_decision.stage,
                action=input_decision.action,
                message=input_decision.message,
                metadata=input_decision.metadata,
            )

        session.conversation.add("user", user_input)
        session.trace.record_user_message(user_input)
        _log.info(
            "user message",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "input_len": len(user_input),
                    "message_count": len(session.conversation.messages),
                    "learning_phase": session.learning_state.phase.value,
                }
            },
        )

        resolved = ResolvedTurnPlan()
        try:
            with timer:
                if session.armory_path is not None:
                    resolved = yield from self._iter_armory_turn_events(
                        original_learning_state,
                        user_input,
                        abort=abort,
                    )
                else:
                    session.last_turn_evidence = None
                    yield from self._iter_plain_events(user_input=user_input, abort=abort)

            notice = self._finalize_successful_turn(user_input, resolved, latency_ms=timer.ms)
            if notice:
                yield GuardrailEvent(
                    stage=GUARDRAIL_STAGE_OUTPUT,
                    action=GUARDRAIL_ACTION_WARN,
                    message=notice,
                    metadata={"code": "verification", "silent": True},
                )
                yield NoticeEvent(notice, code="verification")
        except StreamRecoveryError as rec:
            _log.warning(
                "stream interrupted, rolling back",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "partial_len": len(rec.partial_content),
                        "latency_ms": timer.ms,
                    }
                },
            )
            session.trace.record_session_event(
                "turn_error",
                original_user_input=user_input,
                error=str(rec),
                latency_ms=round(timer.ms, 1),
            )
            self._rollback_turn(original_messages, original_learning_state)
            session.dirty = True
            raise
        except EngineError as exc:
            _log.warning(
                "turn orchestration failed: %s",
                exc,
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "latency_ms": timer.ms,
                    }
                },
            )
            session.trace.record_session_event(
                "turn_error",
                original_user_input=user_input,
                error=str(exc),
                latency_ms=round(timer.ms, 1),
            )
            self._rollback_turn(original_messages, original_learning_state)
            raise
        except Exception:
            _log.error(
                "turn orchestration failed",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "latency_ms": timer.ms,
                    }
                },
                exc_info=True,
            )
            session.trace.record_session_event(
                "turn_error",
                original_user_input=user_input,
                error="unexpected turn orchestration failure",
                latency_ms=round(timer.ms, 1),
            )
            self._rollback_turn(original_messages, original_learning_state)
            raise

    def _iter_armory_turn_events(
        self,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]:
        session = self.session
        due_reviews, memory_state = _learning_practice_context(session)
        prior_contract = _prior_contract_for_followup_seed(session)
        prior_intent = session.last_plan_intent
        intent_index = session.rag_index
        default_plan = plan_turn(
            original_learning_state,
            user_input,
            intent="",
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        intent_resolution = _resolved_user_intent(
            user_input,
            config=session.config,
            conversation=session.conversation,
            prior_intent=prior_intent,
            prior_contract=prior_contract,
        )
        if (
            intent_index is None
            and session.armory_path is not None
            and intent_resolution.intent in _CONTINUABLE_MATERIAL_INTENTS
        ):
            intent_index = _ensure_rag_index(session)
        intent_resolution = _stabilized_intent_for_named_material(
            intent_resolution,
            user_input=user_input,
            index=intent_index,
        )
        intent_resolution = _stabilized_intent_for_default_material_plan(
            intent_resolution,
            user_input=user_input,
            default_plan=default_plan,
            prior_contract=prior_contract,
            index=intent_index,
        )
        intent_resolution = _unresolved_followup_intent_resolution(
            intent_resolution,
            user_input=user_input,
            default_plan=default_plan,
            prior_contract=prior_contract,
        )
        learning_plan = plan_turn(
            original_learning_state,
            user_input,
            intent=intent_resolution.intent,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        turn_contract = turn_contract_from_resolution(user_input, intent_resolution)
        learning_plan, turn_contract = _apply_turn_contract_to_plan(
            learning_plan,
            turn_contract,
            prior_contract=prior_contract,
        )
        turn_contract = _turn_contract_with_prior_replay_state(
            turn_contract,
            prior_contract=prior_contract,
            conversation=session.conversation,
            user_input=user_input,
        )
        learning_plan, turn_contract = _reset_unreplayable_followup_state(
            learning_plan,
            turn_contract,
        )
        if notice := _reading_notice(learning_plan):
            yield NoticeEvent(notice, code="reading")
        resolved = self._resolve_timed_turn_plan(learning_plan)
        resolved = replace(
            resolved,
            turn_contract=_turn_contract_with_evidence(
                turn_contract,
                learning_plan,
                resolved.turn_evidence,
            ),
        )
        yield from self._iter_material_operation_events(learning_plan, resolved)
        if notice := _evidence_notice(resolved):
            yield NoticeEvent(
                notice,
                code="evidence",
                metadata=_evidence_notice_metadata(resolved, session),
            )
        yield from self._iter_learning_events(
            resolved,
            original_learning_state,
            user_input=user_input,
            abort=abort,
        )
        return resolved

    def _iter_plain_events(
        self,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        parts: list[str] = []
        for delta in stream_completion(
            session.config,
            session.conversation,
            abort=abort,
            retry=self.retry,
            client_factory=build_client,
        ):
            if not delta.content:
                continue
            parts.append(delta.content)
            yield AssistantDeltaEvent(delta.content)

        if parts:
            self.last_reply = "".join(parts)
        else:
            self.last_reply = _plain_empty_reply(user_input, session.config)
            yield AssistantDeltaEvent(self.last_reply)

        self._append_assistant_message(self.last_reply)
        self.last_internal_passes = 1
        yield _turn_complete_from_result(None, self.last_reply)

    def _iter_learning_agent_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, _LearningAgentOutput]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.learning_plan
        assert plan is not None
        buffer = _LearningAgentBuffer()
        request = _learning_agent_request(
            plan,
            original_learning_state,
            user_input,
            session,
            resolved.turn_contract,
        )
        for event in iter_agent_events(
            session.config,
            request.conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=_learning_extra_system_prompt(
                session,
                plan,
                resolved,
                user_input=user_input,
            ),
            tool_schemas=None if plan.allow_tools else [],
            allowed_tool_names=plan.allowed_tool_names if plan.allow_tools else (),
            registry=session.tool_registry,
        ):
            yield from self._record_learning_agent_event(
                event,
                buffer,
                buffer_output=request.buffer_output,
            )

        if buffer.visible_parts:
            self.last_reply = buffer.visible_streamed_reply
        return _learning_agent_output_from_buffer(plan, buffer)

    def _record_learning_agent_event(
        self,
        event: TurnEvent,
        buffer: _LearningAgentBuffer,
        *,
        buffer_output: bool,
    ) -> Iterator[TurnEvent]:
        if isinstance(event, AssistantDeltaEvent):
            buffer.add_delta(event.delta, visible=not buffer_output)
            if not buffer_output:
                yield event
            return
        if isinstance(event, TurnCompleteEvent):
            buffer.completion_event = event
            return
        if _tool_result_refreshes_current_armory(event):
            self.session.refresh_armory_sources()
        yield event

    def _iter_empty_learning_reply_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.learning_plan
        assert plan is not None
        fallback_reply = _empty_learning_reply(
            plan,
            resolved,
            user_input=user_input,
            config=session.config,
        )
        final_reply = self._apply_learning_reply(
            original_learning_state,
            plan,
            fallback_reply,
            source_refs=_evidence_refs(resolved.turn_evidence),
        )
        yield from _final_reply_events(final_reply)

    def _iter_final_learning_reply_events(
        self,
        plan: LearningTurnPlan,
        completion_event: TurnCompleteEvent | None,
        *,
        raw_reply: str,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[TurnEvent]:
        self._persist_final_learning_reply(raw_reply, final_reply)
        self.last_reply = final_reply
        yield from self._final_learning_delta_events(plan, streamed_reply, final_reply)
        yield _turn_complete_from_result(completion_event, final_reply)

    def _persist_final_learning_reply(self, raw_reply: str, final_reply: str) -> None:
        if not final_reply:
            return
        if self._should_append_final_learning_reply():
            self._append_assistant_message(final_reply)
            return
        if raw_reply != final_reply:
            self._replace_last_assistant_message(final_reply)

    def _should_append_final_learning_reply(self) -> bool:
        return (
            not self.session.conversation.messages
            or self.session.conversation.messages[-1].role != "assistant"
        )

    def _replace_last_assistant_message(self, final_reply: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = final_reply
                return

    def _final_learning_delta_events(
        self,
        plan: LearningTurnPlan,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[AssistantDeltaEvent]:
        if final_reply and (_should_buffer_learning_output(plan) or not streamed_reply):
            yield AssistantDeltaEvent(final_reply)
            return
        if final_reply == streamed_reply:
            return
        suffix = final_reply.removeprefix(streamed_reply)
        if suffix:
            yield AssistantDeltaEvent(suffix)

    def _iter_learning_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.learning_plan
        assert plan is not None

        if deterministic_reply := _deterministic_learning_reply(session, plan, resolved):
            yield from self._iter_deterministic_learning_reply_events(
                deterministic_reply,
                original_learning_state,
                plan,
                user_input=user_input,
            )
            return

        if notice := _writing_notice(plan):
            yield NoticeEvent(notice, code="writing")

        agent_output = yield from self._iter_learning_agent_events(
            resolved,
            original_learning_state,
            user_input=user_input,
            abort=abort,
        )
        yield from self._iter_agent_learning_reply_events(
            agent_output,
            resolved,
            original_learning_state,
            user_input=user_input,
        )

    def _iter_deterministic_learning_reply_events(
        self,
        deterministic_reply: _DeterministicLearningReply,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        if deterministic_reply.internal_passes is not None:
            self.last_internal_passes = deterministic_reply.internal_passes
        self._last_reply_citation_required = deterministic_reply.citation_required
        final_reply = self._apply_deterministic_reply(
            original_learning_state,
            plan,
            deterministic_reply.reply,
            user_input=user_input,
            source_refs=deterministic_reply.source_refs,
            updates_learning_state=deterministic_reply.updates_learning_state,
        )
        yield from _final_reply_events(final_reply)

    def _iter_agent_learning_reply_events(
        self,
        agent_output: _LearningAgentOutput,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.learning_plan
        assert plan is not None
        streamed_reply = agent_output.streamed_reply
        raw_reply = agent_output.raw_reply
        visible_reply = agent_output.visible_reply
        completion_event = agent_output.completion_event

        if not raw_reply:
            yield from self._iter_empty_learning_reply_events(
                resolved,
                original_learning_state,
                user_input=user_input,
            )
            return

        processed_reply = _postprocess_learning_reply(
            plan,
            raw_reply,
            visible_reply,
            resolved,
            user_input=user_input,
            config=session.config,
        )
        raw_reply = processed_reply.raw_reply
        visible_reply = processed_reply.visible_reply
        self.last_internal_passes = processed_reply.pass_count

        if raw_reply:
            source_refs = _evidence_refs(resolved.turn_evidence)
            final_reply = self._apply_learning_reply(
                original_learning_state,
                plan,
                visible_reply,
                source_refs=source_refs,
            )
            self._record_learning_review_if_needed(
                original_learning_state,
                plan,
                source_refs,
            )
        else:
            session.learning_state = original_learning_state
            final_reply = raw_reply

        yield from self._iter_final_learning_reply_events(
            plan,
            completion_event,
            raw_reply=raw_reply,
            streamed_reply=streamed_reply,
            final_reply=final_reply,
        )

    def _apply_deterministic_reply(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        reply: str,
        *,
        user_input: str,
        source_refs: list[str] | None = None,
        updates_learning_state: bool,
    ) -> str:
        localized_reply = _localize_deterministic_reply(
            reply,
            user_input=user_input,
            config=self.session.config,
        )
        if not updates_learning_state:
            self.last_reply = localized_reply
            self._append_assistant_message(localized_reply)
            return localized_reply
        return self._apply_learning_reply(
            original_learning_state,
            plan,
            localized_reply,
            source_refs=source_refs or [],
        )

    def _apply_learning_reply(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        reply: str,
        *,
        source_refs: list[str],
    ) -> str:
        self.session.learning_state, final_reply = apply_turn_result(
            original_learning_state,
            plan,
            reply,
            source_refs,
        )
        self.last_reply = final_reply
        self._append_assistant_message(final_reply)
        return final_reply

    def _append_assistant_message(self, reply: str) -> None:
        if reply and (
            not self.session.conversation.messages
            or self.session.conversation.messages[-1].role != "assistant"
        ):
            self.session.conversation.add("assistant", reply)

    def _record_learning_review_if_needed(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        source_refs: list[str],
    ) -> None:
        if not self._should_record_learning_review(plan):
            return
        armory_path = self.session.armory_path
        if armory_path is None:
            return
        store = load_recall_schedule(armory_path)
        previous = _matching_recall_item(
            store.item_list,
            item=original_learning_state.current_item,
            retrieval_query=original_learning_state.retrieval_query,
        )
        intervention = _learning_move_kind(plan)
        reviewed_state = self._record_learning_review(
            store,
            original_learning_state.current_item,
            concept=original_learning_state.retrieval_query,
            retrieval_query=original_learning_state.retrieval_query,
            source_refs=source_refs or original_learning_state.expected_source_refs,
            hint_level_needed=_positive_hint_level(original_learning_state),
            intervention=intervention,
            exam_importance=_exam_importance(original_learning_state),
        )
        self._record_learning_policy_outcome(
            store,
            original_learning_state=original_learning_state,
            previous=previous,
            state=reviewed_state,
            intervention=intervention,
        )
        save_recall_schedule(store)

    def _should_record_learning_review(self, plan: LearningTurnPlan) -> bool:
        return (
            self.session.armory_path is not None
            and plan.action is LearningAction.ASSESS
            and self.session.learning_state.last_recall_rating.value != "none"
        )

    def _record_learning_review(
        self,
        store: RecallScheduleStore,
        item: str,
        *,
        concept: str,
        retrieval_query: str,
        source_refs: list[str],
        hint_level_needed: int | None,
        intervention: LearningMoveKind,
        exam_importance: float,
    ) -> RecallItemState:
        state = self.session.learning_state
        return store.record_review(
            item,
            concept=concept,
            retrieval_query=retrieval_query,
            source_refs=source_refs,
            rating=state.last_recall_rating,
            elapsed_seconds=state.last_recall_seconds,
            confidence=state.last_confidence,
            hint_level_needed=hint_level_needed,
            error_type=state.last_feedback_type.value,
            intervention=intervention,
            exam_importance=exam_importance,
        )

    def _record_learning_policy_outcome(
        self,
        store: RecallScheduleStore,
        *,
        original_learning_state: LearningState,
        previous: RecallItemState | None,
        state: RecallItemState,
        intervention: LearningMoveKind,
    ) -> None:
        outcome = _policy_outcome_from_review(
            original_learning_state,
            self.session.learning_state,
            state,
            previous,
            intervention,
        )
        store.record_policy_outcome(
            intervention,
            success=state.last_correct,
            mastery_delta=outcome.mastery_delta,
            confidence_delta=outcome.confidence_delta,
            time_cost_seconds=outcome.time_cost_seconds,
            frustration_signal=outcome.frustration_signal,
        )
        self.session.trace.record_session_event(
            "policy_outcome",
            move_type=outcome.move_type,
            topic=outcome.topic,
            correctness_delta=round(outcome.correctness_delta, 3),
            confidence_delta=round(outcome.confidence_delta, 3),
            mastery_delta=round(outcome.mastery_delta, 3),
            time_cost_seconds=outcome.time_cost_seconds,
            frustration_signal=outcome.frustration_signal,
            score=round(outcome.score, 3),
        )

    def _resolve_timed_turn_plan(self, plan: LearningTurnPlan) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(plan)
        if isinstance(resolved, ResolvedTurnPlan):
            resolved = replace(resolved, retrieval_latency_ms=rag_timer.ms)
        session.last_turn_evidence = _stored_turn_evidence(resolved)
        if resolved.turn_evidence is not None:
            rag_span.set_attribute("rag.retrieved", len(resolved.turn_evidence.items))
        rag_span.end()
        _rag_duration_hist.record(rag_timer.ms, {"armory": str(session.armory_path or "none")})
        return resolved

    def _resolve_turn_plan(self, plan: LearningTurnPlan) -> ResolvedTurnPlan:
        turn_evidence = _resolve_turn_evidence(self.session, plan)
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=turn_evidence,
            evidence_assessment=_assess_turn_evidence(plan, turn_evidence),
        )

    def _iter_material_operation_events(
        self,
        plan: LearningTurnPlan,
        resolved: ResolvedTurnPlan,
    ) -> Iterator[MaterialOperationEvent]:
        yield from self._record_material_operation_events(
            _material_operation_events(self.session, plan, resolved)
        )

    def _record_material_operation_events(
        self,
        events: Iterator[MaterialOperationEvent],
    ) -> Iterator[MaterialOperationEvent]:
        for event in events:
            self.session.trace.record_material_operation(
                operation=event.operation,
                message=event.message,
                metadata=event.metadata,
            )
            yield event

    def _rollback_turn(
        self,
        original_messages: list[Message],
        original_learning_state: LearningState,
    ) -> None:
        self.session.conversation.messages = original_messages
        self.session.learning_state = original_learning_state

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str:
        resolved = _resolved_with_citation_requirement(
            resolved,
            citation_required=self._last_reply_citation_required,
        )
        visible_evidence = _visible_turn_evidence(resolved)
        resolved = _resolved_with_visible_evidence_refs(
            resolved,
            self.last_reply,
            visible_evidence,
        )
        notice = self._verification_notice(resolved, visible_evidence)
        resolved = _resolved_with_validation_result(resolved, notice)
        self._mark_session_dirty()
        self._record_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )
        if _turn_contract_can_seed_followup(
            resolved.turn_contract,
            visible_evidence=visible_evidence,
        ):
            self.session.last_plan_intent = _resolved_turn_intent(resolved)
            self.session.last_turn_contract = resolved.turn_contract
        snapshot = build_turn_snapshot(
            self.session.conversation,
            self.session.turn_history,
            learning_state=self.session.learning_state,
            user_input=user_input,
            assistant_reply=self.last_reply,
            evidence=visible_evidence,
            plan_intent=_resolved_turn_intent(resolved),
            contract=resolved.turn_contract,
        )
        if snapshot is not None:
            self.session.turn_history.append(snapshot)
        self._schedule_memory_extraction(user_input, visible_evidence)
        self._save_usage_if_armory_session()
        return notice

    def _verification_notice(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
    ) -> str:
        if (
            resolved.learning_plan is not None
            and resolved.learning_plan.action is LearningAction.CALIBRATE
        ):
            return ""
        if resolved.turn_contract is not None and not resolved.turn_contract.citation_required:
            return ""
        return verify_response(self.last_reply, visible_evidence)

    def _mark_session_dirty(self) -> None:
        if not self.session.title:
            self.session.title = derive_title(self.session.conversation)
        self.session.dirty = True

    def _record_successful_reply(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
        notice: str,
    ) -> None:
        self._log_successful_reply(visible_evidence, latency_ms=latency_ms)
        self._trace_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )

    def _log_successful_reply(
        self,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
    ) -> None:
        session = self.session
        _log.info(
            "reply complete",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "reply_len": len(self.last_reply),
                    "latency_ms": latency_ms,
                    "learning_phase": session.learning_state.phase.value,
                    "learning_feedback": session.learning_state.last_feedback_type.value,
                    "evidence_blocks": len(visible_evidence.items) if visible_evidence else 0,
                }
            },
        )

    def _trace_successful_reply(
        self,
        resolved: ResolvedTurnPlan,
        visible_evidence: TurnEvidence | None,
        *,
        latency_ms: float,
        notice: str,
    ) -> None:
        session = self.session
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            reply_excerpt=_trace_excerpt(self.last_reply),
            learning_phase=session.learning_state.phase.value,
            learning_action=resolved.learning_plan.action.value if resolved.learning_plan else "",
            material_task=_trace_task(resolved.learning_plan),
            retrieval_query=_trace_turn_retrieval_query(resolved),
            turn_contract=(
                resolved.turn_contract.to_dict() if resolved.turn_contract is not None else {}
            ),
            learning_feedback=session.learning_state.last_feedback_type.value,
            evidence_blocks=len(visible_evidence.items) if visible_evidence else 0,
            evidence_refs=(
                list(resolved.turn_contract.evidence_refs)
                if resolved.turn_contract is not None
                else []
            ),
            evidence_coverage=_evidence_trace_coverage(visible_evidence),
            evidence_items=_evidence_trace_items(visible_evidence),
            evidence_assessment=_evidence_assessment_trace(resolved.evidence_assessment),
            pedagogy_validation=_pedagogy_validation_trace(
                resolved.learning_plan,
                self.last_reply,
            ),
            learner_assessment=_learner_assessment_trace(
                resolved.learning_plan,
                session.learning_state,
            ),
            internal_passes=self.last_internal_passes,
            internal_pass_max=_MAX_INTERNAL_PASSES,
            verification_notice=notice,
        )

    def _schedule_memory_extraction(
        self,
        user_input: str,
        visible_evidence: TurnEvidence | None,
    ) -> None:
        session = self.session
        if session.config.is_feature_enabled("disable_memory_extraction"):
            return
        schedule_memory_extraction(
            config=session.config,
            memory=session.memory,
            user_input=user_input,
            reply=self.last_reply,
            evidence=", ".join(_evidence_refs(visible_evidence)),
        )

    def _save_usage_if_armory_session(self) -> None:
        session = self.session
        if session.armory_path is None:
            return
        with contextlib.suppress(Exception):
            save_usage(session.armory_path, session.session_id, session.usage)


def _turn_complete_from_result(
    event: TurnCompleteEvent | None,
    final_reply: str,
) -> TurnCompleteEvent:
    if event is None:
        return TurnCompleteEvent(
            full_text=final_reply,
            turn_index=0,
            latency_ms=0.0,
            finish_reason="fallback",
            tokens_remaining=0,
        )
    return TurnCompleteEvent(
        full_text=final_reply,
        turn_index=event.turn_index,
        latency_ms=event.latency_ms,
        finish_reason=event.finish_reason,
        tokens_remaining=event.tokens_remaining,
    )


def _final_reply_events(
    final_reply: str,
    completion_event: TurnCompleteEvent | None = None,
) -> Iterator[TurnEvent]:
    if final_reply:
        yield AssistantDeltaEvent(final_reply)
    yield _turn_complete_from_result(completion_event, final_reply)
