"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import json
import re
import threading
import urllib.error
from collections.abc import Generator, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from html import unescape
from typing import TYPE_CHECKING

from hephaion._types import is_string_mapping, parse_json_object_fragment
from hephaion.agent.citation import VerificationResult, verify_citations, verify_response
from hephaion.agent.dispatch import iter_agent_events
from hephaion.chat.events import (
    AssistantDeltaEvent,
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
    build_overview_context as _build_overview_context,
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
    is_overview_query as _is_overview_query,
)
from hephaion.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from hephaion.chat.evidence import (
    retrieval_audit_metadata as _retrieval_audit_metadata,
)
from hephaion.chat.titles import derive_title
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_LIST,
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
    TurnIntentResolution,
    intent_resolution_from_payload,
    turn_contract_from_resolution,
)
from hephaion.chat.usage import save_usage
from hephaion.diagnostics.crashes import get_meter, get_tracer
from hephaion.logging import Timer, get_logger
from hephaion.materials import infer_material_role_from_text
from hephaion.memory.workflow import schedule_memory_extraction
from hephaion.rag import EvidenceChunk, TurnEvidence
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
from hephaion.study import (
    EvidenceAssessment,
    LearningAction,
    LearningFeedbackType,
    LearningPhase,
    LearningState,
    LearningTurnPlan,
    MemoryState,
    PolicyOutcome,
    ReviewItem,
    apply_turn_result,
    learner_assessment_from_state,
    plan_turn,
    validate_pedagogy,
)
from hephaion.study.policy import LearningMoveKind
from hephaion.study.priority import (
    PriorityTopic,
    PriorityWebSearcher,
    PriorityWebSearchResult,
    analyze_priority,
)
from hephaion.study.schedule import (
    RecallItemState,
    RecallScheduleStore,
    load_recall_schedule,
    save_recall_schedule,
)

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from hephaion.rag import ArmoryIndex
    from hephaion.rag.chunker import ChunkedDocument

_log = get_logger("chat.orchestrator")
_tracer = get_tracer("chat.orchestrator")
_meter = get_meter("chat.orchestrator")
_rag_duration_hist = _meter.create_histogram(
    "rag.retrieval.duration",
    unit="ms",
    description="Duration of RAG retrieval queries",
)

_EVIDENCE_REQUIRED_ACTIONS = frozenset(
    {
        LearningAction.PRIORITY,
        LearningAction.SOURCE_QA,
        LearningAction.PRESENT,
        LearningAction.HINT,
        LearningAction.SIMPLIFY,
        LearningAction.REVIEW,
        LearningAction.ASSESS,
    }
)
_MATERIAL_ANSWER_CONVERSATION_ACTIONS = frozenset(
    {
        LearningAction.PRIORITY,
        LearningAction.SOURCE_QA,
        LearningAction.PRESENT,
        LearningAction.CALIBRATE,
        LearningAction.SIMPLIFY,
        LearningAction.REVIEW,
    }
)
_BROAD_PRIOR_EVIDENCE_REF_COUNT = 8
_TRACE_TASK_BY_ACTION = {
    LearningAction.PRIORITY: "priority",
    LearningAction.SOURCE_QA: "source-qa",
    LearningAction.CALIBRATE: "calibration",
    LearningAction.ASSESS: "active-recall-assessment",
    LearningAction.HINT: "hint",
}
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
_TRAILING_EVIDENCE_CITATION_GROUP_RE = re.compile(r"(?:\s*\[(?:e|E)\d+\])+\s*$")
_CITATION_ONLY_REPLY_RE = re.compile(r"^\s*(?:\[(?:e|E)\d+\]\s*)+(?:[.,;:])?\s*$")
_THIN_EVIDENCE_POINTER_MAX_WORDS = 8
_MARKDOWN_TABLE_SEPARATOR_LINE_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call\b[^>]*>.*?</tool_call>", re.IGNORECASE | re.DOTALL)
_TOOL_CALL_OPEN_RE = re.compile(r"<tool_call\b[^>]*>", re.IGNORECASE)
_TOOL_CALL_CLOSE_RE = re.compile(r"</tool_call>", re.IGNORECASE)
_DETERMINISTIC_REPLY_LITERAL_RE = re.compile(r"`[^`]+`|/[\w-]+|\"[^\"]+\"")
_ASSESSMENT_LABEL_RE = re.compile(r"^(?:CORRECT|PARTIAL|WRONG):")
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MAX_WORDS = 110
_OVERVIEW_MAX_CHARS = 700
_MATERIAL_REPLY_MAX_CHARS = 700
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES = 6
_OVERVIEW_FALLBACK_MAX_ITEMS = 6
_TABLE_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_LIST_ITEMS = 3
_OVERVIEW_MAX_TABLE_ROWS = 8
_OVERVIEW_TOPIC_LIMIT = 7
_OVERVIEW_WEB_TOPIC_SEARCH_LIMIT = 10
_INTENT_SOURCE_CATALOG_LIMIT = 12
_PRIOR_ANSWER_CONTEXT_LIMIT = 500
_MAX_INTERNAL_PASSES = 3
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
_OVERVIEW_METADATA_LINE_RE = re.compile(
    r"\b(?:university|universität|institute|department|faculty|semester|professor|lecturer|"
    r"instructor|dozent|dozentin|author|email|opencourseware|administrative)\b",
    re.IGNORECASE,
)
_OVERVIEW_DATE_LINE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-zÄÖÜäöüß]+\s+\d{4}\b|\b\d{4}\b")
_OVERVIEW_TOPIC_STOPWORDS = frozenset(
    {
        "about",
        "achtung",
        "assessment",
        "aufgabe",
        "beispiel",
        "beispiele",
        "bezeichnet",
        "bezeichnen",
        "course",
        "definiert",
        "definition",
        "example",
        "examples",
        "exercise",
        "folie",
        "folien",
        "haben",
        "heute",
        "introduction",
        "last",
        "letzte",
        "letzten",
        "letztes",
        "lecture",
        "mal",
        "material",
        "materials",
        "module",
        "modul",
        "contents",
        "das",
        "dem",
        "den",
        "der",
        "des",
        "die",
        "eine",
        "einem",
        "einen",
        "einer",
        "für",
        "fur",
        "mit",
        "of",
        "overview",
        "previous",
        "prompt",
        "prompts",
        "question",
        "slide",
        "slides",
        "speaking",
        "sprechen",
        "today",
        "vorlesung",
        "welcome",
        "willkommen",
    }
)
_OVERVIEW_GENERIC_TOPIC_LABELS = frozenset(
    {
        "chapter",
        "chapters",
        "concept",
        "concepts",
        "definition",
        "definitions",
        "example",
        "examples",
        "exercise",
        "exercises",
        "problem",
        "problems",
        "proof",
        "proofs",
        "satz",
        "sätze",
        "saetze",
        "theorem",
        "theorems",
        "topic",
        "topics",
    }
)
_OVERVIEW_COURSE_TITLE_RE = re.compile(
    r"\b(?:"
    r"(?:module|modul|course|cours|curso|vorlesung|lecture)\s*[:#]?\s*[\w.-]*|"
    r"(?:[\w+-]+\s+){1,5}(?:[ivx]{1,4}|\d{1,4})"
    r")\b",
    re.IGNORECASE,
)
_OVERVIEW_FORMULA_RE = re.compile(r"(?:\\[a-zA-Z]+|[$=∑∫√≤≥→↦∀∃])")
_OVERVIEW_LINE_MARKER_RE = re.compile(r"^[#*\-\d.\s:;()\[\]]+")
_OVERVIEW_WEB_EDUCATION_RE = re.compile(
    r"\b(?:"
    r"course|curriculum|definition|example|guide|intro(?:duction)?|lecture|learn|lesson|"
    r"module|notes|overview|prerequisite|syllabus|theorem|topic|tutorial|"
    r"beispiel|definition|lernen|skript|thema|themen|vorlesung|übungen|uebungen"
    r")\b",
    re.IGNORECASE,
)
_OVERVIEW_TOPIC_NORMALIZATION_SCHEMA = """
{
  "topics": [
    {
      "canonical_english": "concise English concept",
      "display_label": "label to show the user, matching the user's language when clear",
      "evidence_id": "E1",
      "evidence_quote": "exact phrase copied from that evidence excerpt"
    }
  ]
}
""".strip()
_OVERVIEW_TOPIC_NORMALIZATION_SYSTEM_PROMPT = """
You normalize topic menus from cited material excerpts. Use only the supplied evidence.
First infer canonical topic names in English. Then choose a concise display label in the language
of the user's request; if the request language is unclear, use the canonical English topic. Return
actual concepts a user can learn or review, not filenames, document roles, metadata,
table-of-contents labels, administrative text, or generic labels such as definitions, examples,
exercises, or proofs. Judge this from meaning and context rather than fixed keyword lists.
Every topic must cite exactly one supplied evidence_id and include an exact evidence_quote copied
from that excerpt. Return JSON only, matching this schema:
""".strip()
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
Classify the user's intent for Hephaion, the harness that runs the Heph agent and answers
from the user's own materials.
The user's materials are the default subject; ambiguous messages refer to them.

Intents:
- material_overview: broad view of the materials as a corpus, listing topics, themes, contents,
  or what is inside the files. Use whenever no single named concept is the focus.
- source_qa: a specific fact, quote, or definition from the materials.
- source_only_policy: user only asks Heph to stay strictly grounded in sources.
- topic_presentation: explain ONE specific concept the user names directly.
- topic_drill: quiz or practice on the materials.
- driven_learning_calibration: user asks to study, prepare, cram, run a study plan, or have
  Heph drive a structured practice session.
- priority_request: user asks what topics to prioritize, what to study first, or what is
  most important.
- ready_for_recall: user signals they are ready to answer the active recall prompt.
- wait: user wants to delay or pause the recall step without skipping or asking for help.
- recall_clarification: user wants the active recall prompt repeated, translated, or clarified
  without attempting an answer.
- recall_answer_attempt: user is attempting an answer to the active recall prompt.
- reveal_request: user asks for the answer, solution, or to be shown how to solve it.
- hint_request: user asks for a hint or partial nudge.
- scaffold_request: user signals the task is too hard or asks how to start without giving up.
- skip_request: user wants to skip, pass, or move on to a different item.
- material_review: user asks to review the cited material before attempting recall.
- heph_help: user asks about Hephaion or Heph: what the harness or agent does, how to
  use it, or its commands.
- chat: clearly unrelated to the user's materials and not about Hephaion or Heph.

When a prior assistant intent is given, continue that intent unless the user clearly switches
to a different one. Short, vague, or anaphoric follow-ups in any language continue the prior
intent; do not classify them as literal keyword searches.
ready_for_recall requires the user to signal they are ready to answer; asking Heph to ask, quiz,
make, create, rewrite, summarize, or format something is not readiness.
recall_answer_attempt requires the user message itself to answer the active prompt; commands to
make a checklist, ask a question, restate, or change format are not answer attempts.
When the user names a new topic, source, section, or source family and asks to move to it, treat
that as a new source request rather than expanding broad prior evidence. Topic/source switches
override follow-up state; include the named topic/source in the retrieval query and do not use
reuse_prior_evidence or the corpus overview query for that turn.
When the user asks for one cited/source-backed point, detail, or example from a material area,
classify it as source_qa even if the prior turn was a broad material overview. A request for one
specific cited item is not a corpus overview.

For retrieval_query, write the semantic source query Heph should use. Preserve the user's raw
message separately by not copying vague continuation text unless the user explicitly asks for those
words as source text. If the best next answer should reuse or expand the previous evidence, choose
that retrieval_strategy and identify the prior target.
Set direct_evidence_required true only when the answer must come from a directly matching source
span rather than a relevant synthesized source span. Leave it false when the requested answer can
be synthesized from expanded evidence around the prior context.
If the user asks to translate, rephrase, shorten, restyle, reformat, or otherwise present the same
prior answer differently without asking for new material facts, set answer_mode to
transform_prior_answer, reuse prior evidence, and leave retrieval_query empty. Do not search for
the prior answer, previous overview, or conversation wording as if it were source text.
If the user asks about a word, term, phrase, table row, bullet, or structure from the prior
assistant reply, treat the prior reply as conversation context. Reuse prior evidence or transform
the prior answer unless the user explicitly asks whether the materials define or support it.
Set prior_answer_reference true when the user points to an object in a prior assistant answer
instead of naming an independent source fact. Resolve the object from conversation context first,
then cite current evidence IDs for source facts.
If the user refers to ordinal prior-answer objects, cited ideas, list rows, bullets, or citations,
put every requested 1-based position in prior_answer_positions. Leave it empty when no positions
are requested.
Set prior_answer_position_basis to cited_claims for citation/cited-idea positions, list_items for
bullet/numbered/table row positions, and none for informal points that are not tied to the prior
answer's citation or list structure. Do not use list_items for prose sentences that merely contain
multiple clauses; those are informal points unless the prior answer displayed them as rows or
bullets.
Do not set answer_mode to transform_prior_answer when the user asks a new source question, asks to
choose one source, explain a definition or example, verify a citation, or compare evidence.
If the user asks why a prior material answer matters, why it is useful, what it is relevant for,
or how to use it, set answer_mode to reason_from_prior_evidence when prior cited evidence exists.
Reuse the prior evidence when the requested explanation depends on the source-backed topics rather
than on a new source fact. The answer may explain practical relevance as reasoning from cited
premises, while making clear that the relevance explanation is an implication rather than a source
quote unless the evidence explicitly states it.
If the user asks for an assumption, implication, or rationale behind a prior cited claim, also use
reason_from_prior_evidence unless they explicitly ask whether the source states that assumption.
If the user asks to clarify a prior answer about usefulness, practical benefit, consequence, or
why something matters, keep reason_from_prior_evidence; do not turn it into a source lookup or a
pure transform.
Set answer_format to table, list, or plain according to the user's requested presentation format.
When a user asks to create, make, or show a table about the materials, keep material_overview
unless they named one specific concept, and set answer_format to table.
For source lookups of named items, search the stable name and source concept, not user-provided
assumptions or unsupported descriptors around that name.
When the user says previous, prior, before it, or similar relational language, interpret it as
conversation order by default. Do not turn it into source, file, or material ordering unless the
user explicitly asks about ordering inside the materials.

Return JSON only, matching this schema:
""".strip()
_OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT = """
Write a user-facing corpus overview from cited material excerpts. Use only the supplied evidence;
ignore any rejected draft as a source. If the rejected draft contains useful cited synthesis,
compress and repair that synthesis instead of replacing it with a failure notice.
Answer in the same language as the user's request. Keep it compact: one short paragraph plus at
most 3 bullets. Cover substantive learnable content first: concepts, definitions, methods, problem
types, examples, or tasks visible in the excerpts. Treat title pages, logistics, and boilerplate as
context, not as the answer, unless the user asks for them. Cite evidence IDs like [E1] for every
claim. Do not use markdown tables or exhaustive source/topic inventories unless the user explicitly
asked for a table. Do not infer from filenames, lecturers, or institutions, and do not lecture the
user about retrieval, truncation, validation, or sampling. Avoid claiming that a theme is central,
recurring, or the overall pattern unless the evidence explicitly establishes that across sources;
say what is visible in the retrieved evidence instead. For broad corpus overviews with many
distinct evidence sources, cover a representative slice of the sources by grouping related visible
claims into compact clauses instead of listing only the first few excerpts.
""".strip()
_DETERMINISTIC_FALLBACK_LOCALIZATION_PROMPT = """
Rewrite an internal English fallback message for the user. Use the same language as the user's
request when clear. If the request is English or the language is unclear, return the original
English message. Preserve command literals, slash commands, paths, and quoted phrases exactly.
Preserve any leading CORRECT:, PARTIAL:, or WRONG: assessment label exactly.
Do not add facts, citations, source claims, apologies, or next actions.
Return plain text only.
""".strip()
_OVERVIEW_ROLE_LABELS = {
    "assignment": "assignment or exercise sheet",
    "codebase": "source code",
    "lecture": "lecture or slide material",
    "past_exam": "past exam or exam-style material",
    "reference": "reference or concept notes",
    "slides": "lecture slides",
    "textbook": "textbook or chapter material",
    "vocabulary": "vocabulary practice material",
}


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


def _material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    return f"@{name or source}"


def _readable_material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1] or source
    stem = name.rsplit(".", maxsplit=1)[0]
    readable = re.sub(r"[-_]+", " ", stem).strip()
    return readable or name


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


def _missing_indexed_material_reply(session: ChatSession, action: LearningAction) -> str:
    if not _requires_indexed_material(session, action):
        return ""
    index = session.rag_index
    if index is None:
        return _index_unavailable_reply()
    return _indexed_material_state_reply(session, index)


def _requires_indexed_material(session: ChatSession, action: LearningAction) -> bool:
    return action in _EVIDENCE_REQUIRED_ACTIONS and session.source_file_count > 0


def _indexed_material_state_reply(session: ChatSession, index: ArmoryIndex) -> str:
    if index.chunk_count > 0:
        if _has_enabled_indexed_material(session, index):
            return ""
        return _all_material_disabled_reply()
    if sources := _enabled_unindexable_sources(session, index):
        materials = _material_list_label(sources)
        reasons = [index.unindexable_files[source] for source in sources]
        return _unindexable_material_reply(materials, reasons)
    return _empty_material_index_reply()


def _has_enabled_indexed_material(session: ChatSession, index: ArmoryIndex) -> bool:
    return any(
        document.source not in session.disabled_source_files and document.chunks
        for document in index.documents
    )


def _enabled_unindexable_sources(session: ChatSession, index: ArmoryIndex) -> list[str]:
    return [
        source
        for source in sorted(index.unindexable_files)
        if source not in session.disabled_source_files
    ]


def _material_list_label(sources: list[str]) -> str:
    labels = [_material_label(source) for source in sources[:3]]
    materials = ", ".join(labels)
    if remaining := len(sources) - len(labels):
        return f"{materials}, and {remaining} more"
    return materials


def _index_unavailable_reply() -> str:
    return (
        "The armory has visible materials, but Heph could not prepare the "
        "searchable materials index for this turn. I cannot answer from outside "
        "knowledge. Check the material files or run `heph index <armory>` to see "
        "the indexing error directly."
    )


def _all_material_disabled_reply() -> str:
    return (
        "The armory has searchable materials, but all indexed material is currently "
        "disabled. Enable at least one material with /materials before asking."
    )


def _empty_material_index_reply() -> str:
    return (
        "The armory has visible materials, but no searchable evidence is indexed yet. "
        "I cannot answer from outside knowledge. Heph prepares the index "
        "automatically when possible; run `heph index <armory>` to inspect the failure."
    )


def _no_matching_indexed_evidence_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
    contract: TurnContract | None = None,
) -> str:
    index = session.rag_index
    if (
        not _requires_indexed_material(session, plan.action)
        or index is None
        or not plan.retrieval_query
        or not _has_enabled_indexed_material(session, index)
    ):
        return ""
    request_text = _no_match_request_text(contract)
    return (
        "The enabled materials are indexed, but this turn did not retrieve matching evidence "
        f"for the resolved request `{request_text}` using retrieval query "
        f"`{plan.retrieval_query}`."
    )


def _no_match_request_text(contract: TurnContract | None) -> str:
    if contract is None:
        return "this request"
    return (
        contract.canonical_request
        or contract.followup_target
        or contract.original_user_input
        or "this request"
    )


def _unindexable_material_reply(materials: str, reasons: list[str]) -> str:
    reason_text = [reason.lower() for reason in reasons]
    if _all_reasons_contain(reason_text, "conversion backend unavailable"):
        return (
            f"I can see {materials}, but PDF/document conversion is unavailable in this "
            "installation. I cannot answer from outside knowledge. Update or reinstall "
            "Heph, then ask again or run `heph index <armory>` to verify indexing."
        )
    if _all_reasons_contain(reason_text, "docling conversion failed"):
        return (
            f"I can see {materials}, but document conversion did not extract searchable "
            "text from it. I cannot answer from outside knowledge. Re-export, replace, "
            "or convert the document to text/Markdown, then ask again."
        )
    if _all_reasons_contain(reason_text, "timed out"):
        return (
            f"I can see {materials}, but document conversion timed out before searchable "
            "text was indexed. I cannot answer from outside knowledge. Re-export or "
            "convert the material to text/Markdown, then ask again."
        )
    if _all_reasons_contain(reason_text, "docling"):
        return (
            f"I can see {materials}, but it is not searchable armory evidence yet. "
            "I cannot answer from outside knowledge. Update Heph, then ask again "
            "or run `heph index <armory>` to verify indexing."
        )
    return (
        f"I can see {materials}, but no searchable text was indexed from it. "
        "I cannot answer from outside knowledge. Convert the material to text or "
        "Markdown, then ask again."
    )


def _all_reasons_contain(reasons: list[str], needle: str) -> bool:
    return bool(reasons) and all(needle in reason for reason in reasons)


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
    return plan.action not in {LearningAction.PRESENT, LearningAction.SOURCE_QA}


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


def _visible_turn_evidence(resolved: object) -> TurnEvidence | None:
    if not isinstance(resolved, ResolvedTurnPlan):
        return None
    plan = resolved.learning_plan
    if plan is not None and plan.action is LearningAction.CALIBRATE:
        return None
    return resolved.turn_evidence


def _stored_turn_evidence(resolved: object) -> TurnEvidence | None:
    if not isinstance(resolved, ResolvedTurnPlan):
        return None
    if (
        resolved.learning_plan is not None
        and resolved.learning_plan.action is LearningAction.CALIBRATE
    ):
        return resolved.turn_evidence
    return _visible_turn_evidence(resolved)


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


def _plural(word: str, count: int) -> str:
    return f"{word}{'' if count == 1 else 's'}"


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


def _material_operation_event(
    operation: str,
    message: str,
    **metadata: object,
) -> MaterialOperationEvent:
    return MaterialOperationEvent(
        operation=operation,
        message=message,
        metadata={key: value for key, value in metadata.items() if value not in ("", None)},
    )


def _count_label(count: int, singular: str) -> str:
    return f"{count} {singular}{'' if count == 1 else 's'}"


def _material_operation_events(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> Iterator[MaterialOperationEvent]:
    if plan.action is LearningAction.CALIBRATE:
        return
    if not (plan.retrieval_query or plan.use_expected_source_refs or resolved.turn_evidence):
        return

    evidence = _visible_turn_evidence(resolved)
    index_counts = _enabled_index_counts(session)
    yield from _index_ready_events(*index_counts)
    yield from _material_operation_start_events(session, plan, evidence, index_counts)
    yield from _material_evidence_events(plan, evidence, index_counts)


def _enabled_index_counts(session: ChatSession) -> tuple[int, int]:
    if session.rag_index is None:
        return 0, 0
    enabled_documents = [
        document
        for document in session.rag_index.documents
        if document.source not in session.disabled_source_files and document.chunks
    ]
    return len(enabled_documents), sum(len(document.chunks) for document in enabled_documents)


def _index_ready_events(
    indexed_sources: int,
    indexed_chunks: int,
) -> Iterator[MaterialOperationEvent]:
    if not (indexed_sources or indexed_chunks):
        return
    yield _material_operation_event(
        "index_ready",
        (
            "Material index ready: "
            f"{_count_label(indexed_sources, 'enabled source')}, "
            f"{_count_label(indexed_chunks, 'chunk')}."
        ),
        indexed_sources=indexed_sources,
        indexed_chunks=indexed_chunks,
    )


def _material_operation_start_events(
    session: ChatSession,
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    index_counts: tuple[int, int],
) -> Iterator[MaterialOperationEvent]:
    indexed_sources, indexed_chunks = index_counts
    if _overview_turn(plan):
        yield _overview_sampling_event(plan, evidence, indexed_sources)
        return
    if plan.use_expected_source_refs and session.learning_state.expected_source_refs:
        yield _material_operation_event(
            "open_stored_evidence",
            (
                "Opening stored material evidence from the current recall item: "
                + ", ".join(session.learning_state.expected_source_refs[:3])
            ),
            refs=list(session.learning_state.expected_source_refs),
        )
        return
    if plan.retrieval_query:
        yield _material_operation_event(
            "search_index",
            f"Searching indexed materials for: {plan.retrieval_query}",
            query=plan.retrieval_query,
            indexed_sources=indexed_sources,
            indexed_chunks=indexed_chunks,
        )


def _overview_sampling_event(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    indexed_sources: int,
) -> MaterialOperationEvent:
    sampled_sources = evidence.sampled_source_count if evidence else 0
    total_sources = evidence.total_source_count if evidence else indexed_sources
    evidence_blocks = len(evidence.items) if evidence else 0
    return _material_operation_event(
        "sample_overview",
        (
            f"Sampling corpus overview: {_count_label(evidence_blocks, 'excerpt')} "
            f"from {sampled_sources} of {_count_label(total_sources, 'indexed source')}."
        ),
        query=plan.retrieval_query,
        evidence_blocks=evidence_blocks,
        sampled_sources=sampled_sources,
        total_sources=total_sources,
    )


def _material_evidence_events(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    index_counts: tuple[int, int],
) -> Iterator[MaterialOperationEvent]:
    indexed_sources, indexed_chunks = index_counts
    if evidence is not None and evidence.items:
        for item in evidence.items[:3]:
            yield _material_operation_event(
                "read_excerpt",
                (
                    f"Opened {item.source}#chunk={item.chunk_index}: "
                    f"{_trace_excerpt(item.content, limit=180)}"
                ),
                evidence_id=item.evidence_id,
                ref=f"{item.source}#chunk={item.chunk_index}",
                source=item.source,
                chunk=item.chunk_index,
                score=round(item.score, 4),
                text_excerpt=_trace_excerpt(item.content, limit=240),
            )
        return
    if plan.retrieval_query:
        yield _material_operation_event(
            "search_result",
            "Material search returned no matching indexed evidence.",
            query=plan.retrieval_query,
            indexed_sources=indexed_sources,
            indexed_chunks=indexed_chunks,
        )


def _reading_notice(plan: LearningTurnPlan) -> str:
    if plan.action is LearningAction.CALIBRATE:
        return ""
    if _overview_turn(plan):
        return "Preparing the material index and reading enabled evidence for a corpus overview."
    if plan.retrieval_query or plan.use_expected_source_refs:
        return "Preparing the material index and reading relevant evidence."
    return ""


def _writing_notice(plan: LearningTurnPlan) -> str:
    if plan.action is LearningAction.CALIBRATE:
        return ""
    if _overview_turn(plan):
        return "Writing a grounded corpus overview."
    if plan.action is LearningAction.CHAT and not (
        plan.retrieval_query or plan.use_expected_source_refs
    ):
        return "Writing a response."
    return "Writing a grounded response."


def _user_visible_reply(plan: LearningTurnPlan, reply: str) -> str:
    cleaned = _strip_tool_call_markup(reply).strip()
    cleaned = _normalize_escaped_evidence_citations(cleaned)
    cleaned = _strip_leading_control_json(cleaned)
    if plan.action is LearningAction.SOURCE_QA:
        cleaned = _strip_unsolicited_learning_followup(cleaned)
    if plan.action is LearningAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", cleaned).strip()
    return cleaned


def _normalize_escaped_evidence_citations(reply: str) -> str:
    normalized = _ESCAPED_EVIDENCE_CITATION_RE.sub(r"[\1]", reply)
    return _PRIVATE_USE_EVIDENCE_CITATION_RE.sub(r"[\1]", normalized)


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
    return plan.buffer_response or plan.action is LearningAction.CHAT


def _strip_unsolicited_learning_followup(reply: str) -> str:
    if not reply.strip():
        return reply
    return _strip_uncited_tail_after_last_citation(reply)


def _strip_uncited_tail_after_last_citation(reply: str) -> str:
    matches = tuple(_OVERVIEW_CITATION_ID_RE.finditer(reply))
    if not matches:
        return reply.strip()
    keep_end = _citation_tail_keep_end(reply, matches[-1].end())
    if not reply[keep_end:].strip():
        return reply.strip()
    return reply[:keep_end].rstrip()


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
    if len(reply) > _MATERIAL_REPLY_MAX_CHARS:
        return True
    if (
        _contract_requests_table(contract)
        and _contains_markdown_table(reply)
        and verification.all_verified
    ):
        return False
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
        if excerpt:
            return excerpt
    return ""


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
    if _should_isolate_material_answer_conversation(plan, contract):
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    if plan.action in {
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


def _should_isolate_material_answer_conversation(
    plan: LearningTurnPlan,
    _contract: TurnContract | None,
) -> bool:
    return plan.action in _MATERIAL_ANSWER_CONVERSATION_ACTIONS


def _learner_assessment_trace(
    plan: LearningTurnPlan | None,
    state: LearningState,
) -> dict[str, object]:
    if plan is None:
        return {}
    assessment = learner_assessment_from_state(
        state,
        topic=state.retrieval_query or state.current_item,
        hint_level_used=state.hint_level if state.hint_level > 0 else None,
    )
    confidence = round(assessment.confidence, 3) if assessment.confidence is not None else None
    calibration_gap = (
        round(assessment.calibration_gap, 3) if assessment.calibration_gap is not None else None
    )
    return {
        "topic": assessment.topic,
        "correctness": round(assessment.correctness, 3),
        "reasoning_quality": round(assessment.reasoning_quality, 3),
        "confidence": confidence,
        "calibration_gap": calibration_gap,
        "misconception_tags": list(assessment.misconception_tags),
        "hint_level_used": assessment.hint_level_used,
        "next_action": assessment.next_action,
    }


def _learning_move_kind(plan: LearningTurnPlan) -> LearningMoveKind:
    return plan.learning_move.kind if plan.learning_move is not None else "assess"


def _positive_hint_level(state: LearningState) -> int | None:
    return state.hint_level if state.hint_level > 0 else None


def _exam_importance(state: LearningState) -> float:
    return 1.0 if state.expected_source_refs else 0.0


def _pedagogy_validation_trace(plan: LearningTurnPlan | None, reply: str) -> dict[str, object]:
    if plan is None or plan.learning_move is None:
        return {}
    validation = validate_pedagogy(reply, plan.learning_move)
    return {
        "valid": validation.valid,
        "issues": list(validation.issues),
        "rewrite_instruction": validation.rewrite_instruction or "",
        "suggested_next_action": validation.suggested_next_action or "",
        "move": plan.learning_move.kind,
    }


def _trace_excerpt(text: str, *, limit: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _trace_task(plan: LearningTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material-overview"
    return _TRACE_TASK_BY_ACTION.get(plan.action, plan.action.value)


def _learning_practice_context(session: ChatSession) -> tuple[tuple[ReviewItem, ...], MemoryState]:
    if session.armory_path is None:
        return (), MemoryState()
    store = load_recall_schedule(session.armory_path)
    due_reviews = _due_review_items(store.due_items(limit=5))
    weak_items = _weak_recall_items(store.item_list)
    weak_topics = _recall_item_topics(weak_items)
    misconceptions = _recall_item_topics(_misconception_items(weak_items))
    successful_interventions, failed_interventions = _learning_policy_interventions(store)
    return due_reviews, MemoryState(
        weak_topics=weak_topics[:5],
        misconceptions=misconceptions[:5],
        successful_interventions=successful_interventions,
        failed_interventions=failed_interventions,
    )


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
    elif plan.retrieval_query is not None and _is_overview_query(plan.retrieval_query):
        overview_context = _build_overview_context(session)
        if overview_context:
            extra_system_prompt = f"{extra_system_prompt}\n\n{overview_context}"
    return _append_evidence_assessment_prompt(extra_system_prompt, resolved)


def _turn_contract_prompt_context(contract: TurnContract | None) -> str:
    if contract is None:
        return ""
    lines = [
        "Turn:",
        f"- user={contract.original_user_input}",
        f"- intent={contract.resolved_intent or 'unknown'}",
        f"- ask={contract.canonical_request or 'unspecified'}",
        (
            f"- followup={'yes' if contract.is_followup else 'no'} "
            f"target={contract.followup_target or 'none'}"
        ),
        f"- mode={contract.answer_mode} format={contract.answer_format}",
        f"- prior_answer_reference={'yes' if contract.prior_answer_reference else 'no'}",
        f"- prior_answer_positions={_contract_prior_positions_text(contract)}",
        f"- prior_answer_position_basis={contract.prior_answer_position_basis or 'none'}",
        f"- retrieval={contract.retrieval_strategy} query={contract.retrieval_query or 'none'}",
        (
            f"- refs={_contract_evidence_refs_text(contract)} "
            f"cite={'yes' if contract.citation_required else 'no'}"
        ),
        "Rules:",
        "- Answer user; use ask/retrieval only to choose evidence.",
        "- Source claim = supported by current evidence and cited with its current ID.",
        "- Sentence citations must cover every claim in that sentence; repeat IDs when "
        "mixing sources.",
        "- Prefer one source claim per sentence. If a checklist step and an example come from "
        "different evidence blocks, split them into separate bullets or sentences.",
        "- For corpus overviews and broad follow-ups, prefer source-by-source visible claims "
        "over umbrella labels. A corpus-wide purpose, emphasis, design goal, or shared theme "
        "needs one evidence block that states it, or each cited source must directly support "
        "that same claim.",
        "- Bare titles, headings, index entries, and section labels are not an overview. "
        "Use them only to orient a substantive claim copied or paraphrased from evidence.",
        "- User-supplied lenses such as practical, important, useful, or comparable are not "
        "source facts. Apply the lens as your reasoning from cited premises; do not say the "
        "source describes itself with that lens unless it does.",
        "- Importance/relevance answers must stay at the same scope as the cited premise. Do "
        "not add broad benefits, qualities, or product-level interpretations unless they "
        "follow directly from the cited premise.",
        "- User wording, filenames, headings, labels, prior replies, memory, and examples "
        "are not source facts.",
        "- Use evidence wording over resolved-query or followup-target wording. If a query "
        "adds a label, bound, absence, order, or category that the evidence does not state, "
        "drop that added wording.",
        "- Prior-answer structure is conversation state; cite only source facts beneath it.",
        "- Informal prior-answer points may be clauses inside a cited sentence. Do not declare "
        "a prior point absent merely because it was prose instead of a bullet or table row.",
        "- In transform_prior_answer, preserve prior supported content; do not add new "
        "reasons, benefits, implications, or use cases.",
        "- Preserve source scope: no stronger quantities, order, purpose, level, ranking, "
        "or comparison unless stated.",
        "- Review/revisit/priority answers must not rank or prescribe order unless evidence "
        "does; otherwise give one non-ranked cited review candidate.",
        "- Counterexample/limitation requests need evidence that states the counterexample, "
        "limit, condition, exception, or contrast. If evidence only gives an adjacent "
        "condition, state that condition without upgrading it into a stronger category.",
        "- Quotes only for exact copied wording; otherwise paraphrase plainly.",
        "- Do not invent example values, dates, names, states, or calculations in "
        "source-grounded turns; examples must come from cited evidence.",
        "- Definitions need current evidence that defines/explains; mere usage is not a "
        "definition.",
        "- Inferences/use cases are allowed only in reason_from_prior_evidence; label them "
        "and cite only premises.",
        "- Source checks should state the supported text directly; omit bare yes/no lead-ins.",
        "- For direct-vs-inferred requests, list only cited direct evidence unless a separate "
        "inference follows from cited premises.",
        "- For assumptions, implications, or rationales behind a prior claim, answer as an "
        "inference from cited premises; do not cite or deny the conversation label itself.",
        "- Source/citation picks may be judgement from visible specificity; do not claim "
        "sources rank themselves. Phrase source choices as your selection from visible "
        "support, not as an objective ranking stated by the materials.",
        "- Do not answer with citation IDs alone; name the claim or phrase the block supports.",
        "- If the requested prior-answer object is absent, say so; do not substitute a nearby "
        "cited claim as if it were the requested object.",
        "- If an ordinal prior-answer reference is ambiguous, say it is ambiguous; do not "
        "substitute an unrelated source claim.",
        "- For prior citation/list references, use the prior answer structure; if the requested "
        "position is not present there, say it is absent and do not manufacture it from evidence.",
        "- When prior answer structure shows fewer cited claims or list items than requested, "
        "state that absence; do not answer only the available position.",
        "- When prior_answer_reference=yes, answer the resolved prior-answer object. Do not "
        "substitute an older, adjacent, or more source-salient object.",
        "- If the user names a source or material visible in the current evidence, answer from "
        "that source rather than the prior topic.",
        "- For evidence/citation reveal turns, show only the source phrase or claim that supports "
        "the prior claim; do not explain retrieval, validation, or procedure unless that is the "
        "claim being checked.",
        "- Do not synthesize an across-source pattern from unrelated examples unless current "
        "evidence states that pattern or each cited source directly supports the same pattern.",
        "- Avoid broad comparative wrap-ups about topics, levels, or presentation style unless "
        "the current evidence or prior answer structure directly supports that comparison.",
        "- Do not cite absence of examples, details, or coverage unless the evidence itself "
        "states that absence. Otherwise say only that the current answer has no sourced "
        "example.",
        "- If evidence is thin or missing, say exactly what current retrieval does not support.",
        "- Do not claim excerpts, chunks, or sources are truncated; answer from the current "
        "evidence text or say which requested fact is unsupported.",
        "- For examples, give a visible example from evidence. Do not turn a used phrase into a "
        "definition unless evidence defines or explains that phrase.",
        "- Do not paste evidence blocks, source excerpts, file contents, or source labels into "
        "the answer. Synthesize cited claims; quote only one short phrase when exact wording is "
        "requested.",
        "- Output compactly: 1-2 sentences, or <=3 bullets/list rows; no offers, menus, "
        "or next-step prompts.",
        "- Tables: compact markdown, short cells, cite relevant cells.",
    ]
    return "\n".join(lines)


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
    context_lines: list[str] = [
        "Recent assistant answers (conversation context only; not source evidence):"
    ]
    for index, message in enumerate(recent_assistant, start=1):
        excerpt = _trace_excerpt(message.content, limit=_PRIOR_ANSWER_CONTEXT_LIMIT)
        if not excerpt:
            continue
        context_lines.extend((f"Answer {index}:", excerpt))
    if len(context_lines) == 1:
        return ""
    last_assistant = recent_assistant[-1]
    structure = _prior_answer_structure_context(last_assistant.content)
    if structure:
        context_lines.extend(("Selected prior answer structure:", structure))
    context_lines.extend(
        (
            "Use this only to resolve references. Prior citation IDs may be stale; cite only "
            "current evidence IDs. Resolve ordinal references against recent answer structure "
            "before declaring them absent. When this turn references a prior answer object, use "
            "the selected prior answer structure. If cited_claims or list_items is lower than "
            "the requested position, say that position is absent instead of substituting another "
            "object.",
        )
    )
    return "\n".join(context_lines)


def _prior_answer_structure_context(content: str) -> str:
    cited_claims = _prior_answer_cited_claims(content)
    list_item_count = _prior_answer_list_item_count(content)
    lines = [
        f"- cited_claims={len(cited_claims)}",
        f"- list_items={list_item_count}",
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
        claim = f"{fragment} [prior E{match.group('id')}]"
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
    limit = 5 if contract.prior_answer_reference else 3
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
    return (
        contract.prior_answer_reference
        or contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
        or contract.retrieval_strategy
        in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
    )


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
    if _needs_overview_fallback(
        plan,
        raw_reply,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    ):
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            rejected_reply=raw_reply,
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
    return _ProcessedLearningReply(
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        pass_count=pass_count,
    )


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
    if abstain_reply := _source_qa_abstain_reply(plan, resolved):
        return _DeterministicLearningReply(abstain_reply, citation_required=False)
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
        return _DeterministicLearningReply(missing_reply)
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


def _prior_answer_target_phrase_reply(
    session: ChatSession,
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
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
            (
                f'The prior answer uses "{phrase}" from this source instruction: '
                f"“{excerpt}” [{item.evidence_id}]."
            ),
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
    cited_ids = _prior_answer_current_citation_ids(selected_answer.content, evidence)
    if len(cited_ids) != 1:
        return None
    item = _evidence_item_by_id(evidence, cited_ids[0])
    if item is None:
        return None
    excerpt = _evidence_pointer_excerpt(item)
    if not excerpt:
        return None
    return _DeterministicLearningReply(
        f"The referenced prior answer is backed by [{item.evidence_id}]: “{excerpt}” "
        f"[{item.evidence_id}].",
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
        if not key or key in seen:
            continue
        phrases.append(phrase)
        seen.add(key)
    return tuple(phrases)


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


def _prior_answer_current_citation_ids(
    content: str,
    evidence: TurnEvidence,
) -> tuple[str, ...]:
    current_ids = {item.evidence_id.casefold() for item in evidence.items}
    cited_ids: list[str] = []
    seen: set[str] = set()
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content):
        evidence_id = f"E{match.group('id')}"
        key = evidence_id.casefold()
        if key not in current_ids or key in seen:
            continue
        cited_ids.append(evidence_id)
        seen.add(key)
    return tuple(cited_ids)


def _evidence_item_by_id(evidence: TurnEvidence, evidence_id: str) -> EvidenceChunk | None:
    key = evidence_id.casefold()
    return next((item for item in evidence.items if item.evidence_id.casefold() == key), None)


def _prior_answer_position_basis_count(content: str, *, basis: str) -> int:
    if basis == "cited_claims":
        return len(_prior_answer_cited_claims(content))
    if basis == "list_items":
        return _prior_answer_list_item_count(content)
    return 0


def _prior_answer_has_any_structure(content: str) -> bool:
    return bool(_prior_answer_cited_claims(content)) or _prior_answer_list_item_count(content) > 0


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
        or resolved.turn_evidence is None
        or not resolved.turn_evidence.items
        or assessment is None
        or assessment.sufficient
        or assessment.recommended_action != "abstain"
    ):
        return ""
    return "The current evidence does not contain a direct source answer for this request."


def _plain_empty_reply(user_input: str, config: ChatConfig) -> str:
    return _localize_deterministic_reply(
        "I could not generate a response. Please try again.",
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
    fallback_reply = _source_qa_evidence_reply(plan, resolved.turn_evidence)
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
        return "PARTIAL: I could not generate a grounded assessment. Please try again."
    return "I could not generate a prompt. Please try again."


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


def _previous_review_metrics(
    previous: RecallItemState | None,
) -> tuple[float, float | None, float]:
    if previous is None:
        return 0.0, None, 0.0
    return previous.mastery, previous.last_confidence, 1.0 if previous.last_correct else 0.0


def _review_confidence_delta(
    state: RecallItemState,
    previous_confidence: float | None,
) -> float:
    if state.last_confidence is None or previous_confidence is None:
        return 0.0
    return state.last_confidence - previous_confidence


def _review_correctness_delta(
    state: RecallItemState,
    previous: RecallItemState | None,
    previous_correctness: float,
) -> float:
    if previous is None and not state.last_correct:
        return -1.0
    current_correctness = 1.0 if state.last_correct else 0.0
    return current_correctness - previous_correctness


def _policy_outcome_from_review(
    original_learning_state: LearningState,
    session_learning_state: LearningState,
    state: RecallItemState,
    previous: RecallItemState | None,
    intervention: LearningMoveKind,
) -> PolicyOutcome:
    previous_mastery, previous_confidence, previous_correctness = _previous_review_metrics(
        previous
    )
    return PolicyOutcome(
        move_type=intervention,
        topic=original_learning_state.retrieval_query or original_learning_state.current_item,
        correctness_delta=_review_correctness_delta(state, previous, previous_correctness),
        confidence_delta=_review_confidence_delta(state, previous_confidence),
        mastery_delta=state.mastery - previous_mastery,
        time_cost_seconds=state.last_recall_seconds or 0,
        frustration_signal=(
            session_learning_state.last_feedback_type is LearningFeedbackType.WRONG
            and original_learning_state.hint_level >= 3
        ),
    )


def _due_review_items(items: list[RecallItemState]) -> tuple[ReviewItem, ...]:
    return tuple(
        ReviewItem(
            item=item.item,
            concept=item.concept,
            failures=item.failures,
            last_confidence=item.last_confidence,
        )
        for item in items
    )


def _weak_recall_items(items: list[RecallItemState]) -> list[RecallItemState]:
    return sorted(
        (item for item in items if _recall_item_is_weak(item)),
        key=lambda item: (-item.failures, item.mastery, -item.exam_importance),
    )


def _recall_item_is_weak(item: RecallItemState) -> bool:
    repair_actions = {"contrastive_question", "give_hint", "prerequisite_repair"}
    return item.failures > 0 or item.mastery < 0.55 or item.next_best_action in repair_actions


def _misconception_items(items: list[RecallItemState]) -> list[RecallItemState]:
    return [
        item
        for item in items
        if item.next_best_action == "contrastive_question" or item.common_errors
    ]


def _recall_item_topics(items: list[RecallItemState]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.concept or item.retrieval_query or item.item for item in items)
    )


def _learning_policy_interventions(
    store: RecallScheduleStore,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    successful_interventions, failed_interventions = _stored_learning_interventions(store)
    _extend_policy_stat_interventions(
        store,
        successful_interventions=successful_interventions,
        failed_interventions=failed_interventions,
    )
    return (
        tuple(dict.fromkeys(successful_interventions)),
        tuple(dict.fromkeys(failed_interventions)),
    )


def _stored_learning_interventions(store: RecallScheduleStore) -> tuple[list[str], list[str]]:
    successful_interventions: list[str] = []
    failed_interventions: list[str] = []
    for item in store.item_list:
        successful_interventions.extend(item.successful_interventions or [])
        failed_interventions.extend(item.failed_interventions or [])
    return successful_interventions, failed_interventions


def _extend_policy_stat_interventions(
    store: RecallScheduleStore,
    *,
    successful_interventions: list[str],
    failed_interventions: list[str],
) -> None:
    for move_type, stats in store.policy_stats.items():
        if stats.success_rate >= 0.6 and stats.uses >= 2:
            successful_interventions.append(move_type)
        elif stats.uses >= 2:
            failed_interventions.append(move_type)


def _matching_recall_item(
    items: list[RecallItemState],
    *,
    item: str,
    retrieval_query: str,
) -> RecallItemState | None:
    for candidate in items:
        if candidate.item == item and candidate.retrieval_query == retrieval_query:
            return candidate
    return None


def _source_qa_evidence_reply(plan: LearningTurnPlan, evidence: TurnEvidence | None) -> str:
    if not _can_answer_source_qa_from_evidence(plan, evidence):
        return ""
    assert evidence is not None
    return _evidence_quote_repair_reply("", evidence)


def _can_answer_source_qa_from_evidence(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
) -> bool:
    if evidence is None or not evidence.items:
        return False
    return plan.action is LearningAction.SOURCE_QA


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


def _overview_turn(plan: LearningTurnPlan) -> bool:
    return (
        plan.action is LearningAction.PRESENT
        and plan.retrieval_query is not None
        and _is_overview_query(plan.retrieval_query)
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


def _apply_turn_contract_to_plan(
    plan: LearningTurnPlan,
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> tuple[LearningTurnPlan, TurnContract]:
    retrieval_query = _semantic_retrieval_query(plan, contract)
    retrieval_strategy = contract.retrieval_strategy
    retrieval_strategy, retrieval_query = _stabilized_followup_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    )
    if (
        plan.action is LearningAction.PRIORITY
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = plan.retrieval_query or contract.canonical_request or retrieval_query
    evidence_refs = _prior_evidence_refs_for_strategy(retrieval_strategy, prior_contract)
    if evidence_refs and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_query = None
    elif retrieval_query and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR

    updated_plan = replace(
        plan,
        retrieval_query=retrieval_query,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=evidence_refs,
        requires_direct_evidence=contract.direct_evidence_required,
    )
    updated_contract = replace(
        contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query or "",
        evidence_refs=evidence_refs,
        citation_required=_plan_requires_citations(updated_plan),
        direct_evidence_required=updated_plan.requires_direct_evidence,
    )
    return updated_plan, updated_contract


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
    ):
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


def _first_non_literal_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> str | None:
    candidates = [
        contract.followup_target,
        contract.canonical_request,
        prior_contract.canonical_request if prior_contract is not None else "",
        prior_contract.retrieval_query if prior_contract is not None else "",
    ]
    semantic_candidates = [
        candidate
        for candidate in candidates
        if candidate and not _same_normalized_text(candidate, contract.original_user_input)
    ]
    if not semantic_candidates:
        return None
    return max(semantic_candidates, key=_semantic_query_specificity)


def _semantic_query_specificity(text: str) -> tuple[int, int]:
    normalized = _normalized_query_text(text)
    return (len(normalized.split()), len(normalized))


def _same_normalized_text(left: str, right: str) -> bool:
    return _normalized_query_text(left) == _normalized_query_text(right)


def _normalized_query_text(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def _semantic_retrieval_query(plan: LearningTurnPlan, contract: TurnContract) -> str | None:
    if not _plan_uses_material_retrieval(plan):
        return plan.retrieval_query
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW:
        return plan.retrieval_query
    return contract.retrieval_query or contract.canonical_request or plan.retrieval_query


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
    return prior_contract.evidence_refs


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
    model_reply = _overview_model_fallback_reply(
        evidence,
        user_input=user_input,
        config=config,
        rejected_reply=rejected_reply,
        allow_table=allow_table,
        allow_list=allow_list,
    )
    return model_reply or _deterministic_overview_fallback_reply(
        evidence,
        allow_table=allow_table,
        allow_list=allow_list,
    )


def _overview_unavailable_reply() -> str:
    return (
        "I could not produce a grounded material overview from the current model output. "
        "Please try again or narrow the request to one file or concept."
    )


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
        f"{cue} [{item.evidence_id}]" for item, cue in items[:_OVERVIEW_FALLBACK_MAX_ITEMS]
    )
    return "Visible material: " + "; ".join(clauses)


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
) -> list[tuple[EvidenceChunk, str]]:
    selected: list[tuple[EvidenceChunk, str]] = []
    seen_keys: set[tuple[str, int]] = set()
    excluded_ids = excluded_evidence_ids or frozenset()
    repeated_cues = _overview_repeated_fallback_cues(evidence)
    for item in evidence.items:
        if item.evidence_id.casefold() in excluded_ids:
            continue
        key = (item.source, item.chunk_index)
        cue = _overview_fallback_cue_for_item(item)
        if key in seen_keys or not cue or _normalize_overview_topic(cue) in repeated_cues:
            continue
        selected.append((item, cue))
        seen_keys.add(key)
        if len(selected) >= limit:
            break
    return selected


def _overview_repeated_fallback_cues(evidence: TurnEvidence) -> frozenset[str]:
    sources_by_cue: dict[str, set[str]] = {}
    for item in evidence.items:
        cue = _overview_fallback_cue_for_item(item)
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


def _overview_fallback_cue_is_substantive(cue: str) -> bool:
    if not _overview_cue_is_useful(cue):
        return False
    words = re.findall(r"\b[\w'-]+\b", cue)
    if _looks_like_sentence(cue):
        return len(words) >= 3 and _overview_cue_has_content_word(words)
    return len(words) >= 6


def _looks_like_sentence(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?"))


def _overview_cue_has_content_word(words: Sequence[str]) -> bool:
    return any(
        (normalized := word.casefold()) not in _OVERVIEW_TOPIC_STOPWORDS
        and normalized not in _OVERVIEW_GENERIC_TOPIC_LABELS
        and normalized != "table"
        for word in words
    )


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
        or _OVERVIEW_COURSE_TITLE_RE.search(cue) is not None
        or _OVERVIEW_FORMULA_RE.search(cue) is not None
    ):
        return False
    return not _looks_like_name_line(cue)


def _overview_role_sentence(evidence: TurnEvidence) -> str:
    role_examples: dict[str, str] = {}
    sources_by_role: dict[str, set[str]] = {}
    for item in evidence.items:
        role, confidence, _reason = infer_material_role_from_text(item.source, item.content)
        if confidence < 0.6:
            continue
        sources_by_role.setdefault(role, set()).add(item.source)
        role_examples.setdefault(role, item.evidence_id)
    if not role_examples:
        return (
            "The excerpts are searchable material, but the sample is not enough to classify "
            "document roles confidently."
        )
    parts = [
        f"{_OVERVIEW_ROLE_LABELS.get(role, role.replace('_', ' '))} "
        f"({len(sources)} source{'' if len(sources) == 1 else 's'}, "
        f"e.g. [{role_examples[role]}])"
        for role, sources in sorted(sources_by_role.items())
    ]
    return "; ".join(parts) + "."


def _clean_overview_line(line: str) -> str:
    cleaned = " ".join(unescape(line).strip().split())
    cleaned = cleaned.replace("[... truncated]", "").strip()
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", cleaned).strip()
    return cleaned.strip(" -:;")


def _trim_overview_cue(line: str, *, limit: int = 120) -> str:
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip(" ,;:.") + "…"


def _overview_model_topic_items(
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> list[str]:
    payload = _model_json_payload(
        config,
        system_prompt=(
            f"{_OVERVIEW_TOPIC_NORMALIZATION_SYSTEM_PROMPT}\n"
            f"{_OVERVIEW_TOPIC_NORMALIZATION_SCHEMA}"
        ),
        user_prompt=_overview_topic_normalization_context(evidence, user_input),
    )
    if payload is None:
        return []
    return _overview_topic_items_from_model_payload(payload, evidence)


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
    if not _valid_overview_model_reply(
        reply,
        evidence,
        allow_table=allow_table,
        allow_list=allow_list,
    ):
        return ""
    return reply


def _overview_fallback_config(config: ChatConfig | None) -> ChatConfig | None:
    if config is None or not config.base_url or not config.model:
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
    conversation = (
        _isolated_recall_conversation(plan, original_learning_state, user_input, contract)
        or session.conversation
    )
    return _LearningAgentRequest(
        conversation=conversation,
        buffer_output=_should_buffer_learning_output(plan),
    )


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
        role, _confidence, _reason = infer_material_role_from_text(item.source, item.content)
        heading = item.chunk.heading or "none"
        compact_text = " ".join(unescape(item.content).split())
        if len(compact_text) > 700:
            compact_text = f"{compact_text[:699]}…"
        lines.extend(
            (
                "",
                f"Evidence {item.evidence_id}",
                f"Source: {item.source}",
                f"Role: {role}",
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
    source_catalog: str = "",
) -> str:
    return _resolved_user_intent(
        user_input,
        config=config,
        conversation=conversation,
        prior_intent=prior_intent,
        source_catalog=source_catalog,
    ).intent


def _resolved_user_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
    conversation: Conversation | None = None,
    prior_intent: str = "",
    source_catalog: str = "",
) -> TurnIntentResolution:
    if not user_input.strip() or config is None or not config.base_url or not config.model:
        return TurnIntentResolution()
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
            source_catalog=source_catalog,
        ),
        raise_errors=True,
    )
    intent, confidence = _classifier_intent_from_payload(payload)
    if confidence >= _MODEL_NORMALIZED_CONFIDENCE_THRESHOLD:
        resolution = intent_resolution_from_payload(payload, intent=intent, confidence=confidence)
        return _stabilized_followup_intent_resolution(
            resolution,
            prior_intent=prior_intent,
        )
    if prior_intent in _CONTINUABLE_MATERIAL_INTENTS:
        return TurnIntentResolution(intent=prior_intent, confidence=confidence, is_followup=True)
    return TurnIntentResolution(confidence=confidence)


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
    prior_intent: str,
) -> TurnIntentResolution:
    if (
        resolution.is_followup
        and prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.intent in {"priority_request", "driven_learning_calibration"}
    ):
        return replace(resolution, intent=prior_intent)
    return resolution


def _intent_normalization_context(
    user_input: str,
    conversation: Conversation | None,
    *,
    prior_intent: str = "",
    source_catalog: str = "",
) -> str:
    lines: list[str] = []
    if prior_intent:
        lines.extend((f"Prior assistant intent: {prior_intent}", ""))
    if source_catalog:
        lines.extend(("Available source map:", source_catalog, ""))
    last_assistant = _last_assistant_message(conversation, user_input)
    if last_assistant is not None:
        lines.extend(
            (
                "Last assistant reply (excerpt):",
                _trace_excerpt(last_assistant.content, limit=400),
                "",
            )
        )
    lines.extend(("Current user request:", user_input.strip()))
    return "\n".join(lines)


def _intent_source_catalog(index: ArmoryIndex | None) -> str:
    if index is None:
        return ""
    entries: list[str] = []
    for document in index.documents[:_INTENT_SOURCE_CATALOG_LIMIT]:
        label = _normalized_source_label(document.source) or _material_label(document.source)
        text = _document_catalog_text(document)
        role, confidence, _reason = infer_material_role_from_text(document.source, text)
        role_text = f", role={role}" if confidence >= 0.5 else ""
        entries.append(f"- label={label}; path={document.source}{role_text}")
    remaining = len(index.documents) - len(entries)
    if remaining > 0:
        entries.append(f"- +{remaining} more indexed sources")
    return "\n".join(entries)


def _document_catalog_text(document: ChunkedDocument) -> str:
    return " ".join(chunk.text for chunk in document.chunks[:2])


def _last_assistant_message(
    conversation: Conversation | None,
    user_input: str,
) -> Message | None:
    recent = _recent_assistant_messages(conversation, user_input, limit=1)
    return recent[-1] if recent else None


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


def _overview_topic_items_from_model_payload(
    payload: dict[str, object],
    evidence: TurnEvidence,
) -> list[str]:
    raw_topics = payload.get("topics")
    if not isinstance(raw_topics, list):
        return []
    evidence_by_id = {item.evidence_id: item for item in evidence.items}
    topic_items: list[str] = []
    seen: set[str] = set()
    for raw_topic in raw_topics:
        topic_item = _overview_topic_item_from_payload(raw_topic, evidence, evidence_by_id, seen)
        if topic_item is None:
            continue
        topic_items.append(topic_item)
        if len(topic_items) >= _OVERVIEW_TOPIC_LIMIT:
            break
    return topic_items


def _overview_topic_item_from_payload(
    raw_topic: object,
    evidence: TurnEvidence,
    evidence_by_id: Mapping[str, EvidenceChunk],
    seen: set[str],
) -> str | None:
    if not is_string_mapping(raw_topic):
        return None
    evidence_id = _overview_payload_string(raw_topic, "evidence_id").upper()
    evidence_item = evidence_by_id.get(evidence_id)
    if evidence_item is None or not _overview_payload_quote_is_grounded(raw_topic, evidence_item):
        return None

    canonical = _clean_overview_model_label(
        _overview_payload_string(raw_topic, "canonical_english")
    )
    label = _clean_overview_model_label(_overview_payload_string(raw_topic, "display_label"))
    if not label:
        label = canonical
    if not _valid_overview_model_topic(canonical, label, evidence, seen):
        return None

    seen.add(_normalize_overview_topic(label))
    return f"{label} [{evidence_id}]"


def _overview_payload_quote_is_grounded(
    raw_topic: Mapping[str, object],
    evidence_item: EvidenceChunk,
) -> bool:
    evidence_quote = _overview_payload_string(raw_topic, "evidence_quote")
    normalized_quote = _normalize_overview_quote(evidence_quote)
    haystack = _normalize_overview_quote(f"{evidence_item.chunk.heading}\n{evidence_item.content}")
    return len(normalized_quote) >= 4 and normalized_quote in haystack


def _valid_overview_model_topic(
    canonical: str,
    label: str,
    evidence: TurnEvidence,
    seen: set[str],
) -> bool:
    normalized_topic = _normalize_overview_topic(label)
    return (
        bool(canonical)
        and bool(normalized_topic)
        and normalized_topic not in seen
        and _overview_topic_is_useful(canonical)
        and _overview_topic_is_useful(label)
        and not _overview_topic_looks_like_metadata(label, evidence)
    )


def _normalize_overview_quote(text: str) -> str:
    return " ".join(unescape(text).casefold().split())


def _overview_payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _clean_overview_model_label(label: str) -> str:
    return _clean_overview_line(label).strip(".")


def _overview_topic_items(
    evidence: TurnEvidence,
    *,
    web_searcher: PriorityWebSearcher | None = None,
) -> list[str]:
    topic_clues = _overview_heading_topics(evidence)
    seen = {_normalize_overview_topic(topic.rsplit(" [", maxsplit=1)[0]) for topic in topic_clues}
    analysis = analyze_priority((item.chunk for item in evidence.items), limit=16)
    topic_clues.extend(
        _overview_analysis_topic_items(
            analysis.topics,
            evidence,
            seen,
            web_searcher=web_searcher,
        )
    )
    return topic_clues[:_OVERVIEW_TOPIC_LIMIT]


def _overview_analysis_topic_items(
    topics: Sequence[PriorityTopic],
    evidence: TurnEvidence,
    seen: set[str],
    *,
    web_searcher: PriorityWebSearcher | None,
) -> list[str]:
    selector = _OverviewAnalysisTopicSelector(
        evidence=evidence,
        seen=seen,
        web_searcher=web_searcher,
    )
    return list(selector.items(topics, limit=_OVERVIEW_TOPIC_LIMIT))


@dataclass(slots=True)
class _OverviewAnalysisTopicSelector:
    evidence: TurnEvidence
    seen: set[str]
    web_searcher: PriorityWebSearcher | None
    web_checked: int = 0
    subject_hint: str = field(init=False)
    evidence_id_by_source: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        self.subject_hint = _overview_subject_hint(self.evidence)
        self.evidence_id_by_source = {
            item.source: item.evidence_id for item in self.evidence.items
        }

    def items(self, topics: Sequence[PriorityTopic], *, limit: int) -> Iterator[str]:
        selected = 0
        for topic in topics:
            item = self.item(topic)
            if item is None:
                continue
            yield item
            selected += 1
            if selected >= limit:
                return

    def item(self, topic: PriorityTopic) -> str | None:
        candidate = _overview_analysis_topic_candidate(
            topic,
            self.evidence,
            self.evidence_id_by_source,
            self.seen,
        )
        if candidate is None:
            return None
        label, evidence_id, normalized_topic = candidate
        if not self._web_supported(label):
            return None
        self.seen.add(normalized_topic)
        return f"{label} [{evidence_id}]"

    def _web_supported(self, label: str) -> bool:
        if self.web_searcher is None or self.web_checked >= _OVERVIEW_WEB_TOPIC_SEARCH_LIMIT:
            return True
        self.web_checked += 1
        return _overview_topic_web_supported(label, self.subject_hint, self.web_searcher)


def _overview_analysis_topic_candidate(
    topic: PriorityTopic,
    evidence: TurnEvidence,
    evidence_id_by_source: Mapping[str, str],
    seen: set[str],
) -> tuple[str, str, str] | None:
    evidence_id = _first_topic_evidence_id(topic, evidence_id_by_source)
    label = _overview_priority_topic_label(topic)
    normalized_topic = _normalize_overview_topic(label)
    if not _include_overview_priority_topic(
        topic,
        label,
        evidence,
        evidence_id=evidence_id,
        normalized_topic=normalized_topic,
        seen=seen,
    ):
        return None
    return label, evidence_id, normalized_topic


def _first_topic_evidence_id(
    topic: PriorityTopic,
    evidence_id_by_source: Mapping[str, str],
) -> str:
    return next(
        (
            evidence_id_by_source[source]
            for source in topic.sources
            if source in evidence_id_by_source
        ),
        "",
    )


def _overview_priority_topic_label(topic: PriorityTopic) -> str:
    label = " ".join(topic.topic.split())
    if label and not any(char.isupper() for char in label):
        return f"{label[0].upper()}{label[1:]}"
    return label


def _include_overview_priority_topic(
    topic: PriorityTopic,
    label: str,
    evidence: TurnEvidence,
    *,
    evidence_id: str,
    normalized_topic: str,
    seen: set[str],
) -> bool:
    return (
        bool(evidence_id)
        and normalized_topic not in seen
        and _overview_topic_source_role(topic.sources, evidence) not in {"assignment", "past_exam"}
        and not _overview_topic_looks_like_metadata(topic.topic, evidence)
        and _overview_topic_is_useful(label)
    )


def _overview_subject_hint(evidence: TurnEvidence) -> str:
    for item in evidence.items:
        for line in unescape(item.content).splitlines()[:8]:
            candidate = _clean_overview_line(line)
            if not candidate:
                continue
            if _OVERVIEW_COURSE_TITLE_RE.search(candidate):
                return _trim_overview_cue(candidate, limit=80)
    role_sentence = _overview_role_sentence(evidence)
    topic_text = " ".join(
        _split_overview_citation(topic)[0] for topic in _overview_heading_topics(evidence, limit=3)
    )
    return _trim_overview_cue(f"{topic_text} {role_sentence}".strip(), limit=80)


def _overview_topic_web_supported(
    topic: str,
    subject_hint: str,
    web_searcher: PriorityWebSearcher,
) -> bool:
    query = f"{subject_hint} {topic} topic".strip()
    try:
        results = tuple(web_searcher(query))
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        return True
    if not results:
        return True

    topic_words = _overview_topic_words(topic)
    if not topic_words:
        return False
    return any(_overview_web_result_supports_topic(result, topic_words) for result in results[:3])


def _overview_topic_words(topic: str) -> tuple[str, ...]:
    return tuple(word for word in re.findall(r"[\w+-]+", topic.casefold()) if len(word) > 2)


def _overview_web_result_supports_topic(
    result: PriorityWebSearchResult,
    topic_words: Sequence[str],
) -> bool:
    haystack = f"{result.title} {result.snippet}".casefold()
    return all(word in haystack for word in topic_words) and bool(
        _OVERVIEW_WEB_EDUCATION_RE.search(haystack)
    )


def _split_overview_citation(text: str) -> tuple[str, str]:
    match = _OVERVIEW_CITATION_ID_RE.search(text)
    if match is None:
        return text.strip(), ""
    citation = match.group(0)
    label = text[: match.start()].strip()
    return label, citation


def _overview_heading_topics(evidence: TurnEvidence, *, limit: int = 8) -> list[str]:
    topic_clues: list[str] = []
    seen: set[str] = set()
    for item in evidence.items:
        for topic in _overview_heading_candidates(item):
            if not _valid_heading_overview_topic(topic, seen):
                continue
            seen.add(_normalize_overview_topic(topic))
            topic_clues.append(f"{topic} [{item.evidence_id}]")
            break
        if len(topic_clues) >= min(limit, _OVERVIEW_TOPIC_LIMIT):
            break
    return topic_clues


def _overview_heading_candidates(item: EvidenceChunk) -> tuple[str, ...]:
    candidates = (item.chunk.heading, *_overview_markdown_headings(item.content))
    return tuple(topic for candidate in candidates if (topic := _clean_overview_line(candidate)))


def _valid_heading_overview_topic(topic: str, seen: set[str]) -> bool:
    normalized_topic = _normalize_overview_topic(topic)
    return (
        bool(normalized_topic)
        and normalized_topic not in seen
        and _overview_topic_is_useful(topic)
        and not _overview_heading_looks_like_metadata(topic)
    )


def _overview_heading_looks_like_metadata(topic: str) -> bool:
    return bool(_OVERVIEW_METADATA_LINE_RE.search(topic) or _OVERVIEW_DATE_LINE_RE.search(topic))


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


def _overview_topic_source_role(sources: tuple[str, ...], evidence: TurnEvidence) -> str:
    for source in sources:
        text = " ".join(item.content for item in evidence.items if item.source == source)
        if not text:
            continue
        role, confidence, _reason = infer_material_role_from_text(source, text)
        if confidence >= 0.6:
            return role
    return ""


def _overview_topic_is_useful(topic: str) -> bool:
    normalized = " ".join(topic.casefold().split())
    if _overview_topic_text_is_invalid(topic, normalized):
        return False
    words = normalized.split()
    if any(word in _OVERVIEW_TOPIC_STOPWORDS for word in words):
        return False
    return len(words) <= 5


def _overview_topic_text_is_invalid(topic: str, normalized: str) -> bool:
    return any(
        (
            _overview_topic_is_too_short_or_generic(normalized),
            _OVERVIEW_COURSE_TITLE_RE.search(topic) is not None,
            _OVERVIEW_FORMULA_RE.search(topic) is not None,
            _overview_topic_has_sentence_punctuation(topic),
        )
    )


def _overview_topic_is_too_short_or_generic(normalized: str) -> bool:
    return (
        len(normalized) < 4
        or normalized == "table"
        or normalized in _OVERVIEW_GENERIC_TOPIC_LABELS
    )


def _overview_topic_has_sentence_punctuation(topic: str) -> bool:
    return re.search(r"[.:;!?]|->|:=|=>", topic) is not None


def _overview_topic_looks_like_metadata(topic: str, evidence: TurnEvidence) -> bool:
    normalized_topic = " ".join(topic.casefold().split())
    if not normalized_topic:
        return True
    for item in evidence.items:
        lines = _overview_content_lines(item.content)
        for line_index, line in _overview_metadata_window_lines(lines):
            if _line_matches_overview_topic(line, normalized_topic) and _metadata_window_matches(
                lines,
                line_index,
                line,
            ):
                return True
    return False


def _overview_content_lines(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip()]


def _overview_metadata_window_lines(lines: Sequence[str]) -> tuple[tuple[int, str], ...]:
    return tuple(enumerate(lines[:10]))


def _line_matches_overview_topic(line: str, normalized_topic: str) -> bool:
    return " ".join(line.casefold().split()).strip("# ") == normalized_topic


def _metadata_window_matches(lines: Sequence[str], line_index: int, line: str) -> bool:
    neighboring = " ".join(lines[max(0, line_index - 2) : line_index + 3])
    if _OVERVIEW_METADATA_LINE_RE.search(neighboring):
        return True
    return bool(_OVERVIEW_DATE_LINE_RE.search(neighboring) and _looks_like_name_line(line))


def _looks_like_name_line(line: str) -> bool:
    letter_words = _letter_words(line)
    if not 2 <= len(letter_words) <= 4:
        return False
    return all(_looks_like_name_word(word) for word in letter_words)


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
    if contract is not None and contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
        return False
    return _overview_turn(plan) or (
        contract is not None
        and contract.resolved_intent == "material_overview"
        and plan.action is LearningAction.PRESENT
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
    if len(raw_reply) > _OVERVIEW_MAX_CHARS:
        return True
    if len(words) > _OVERVIEW_MAX_WORDS:
        return True
    if (
        has_table
        and not allow_table
        and _markdown_table_row_count(raw_reply) > _OVERVIEW_MAX_TABLE_ROWS
    ):
        return True
    if _list_item_count(raw_reply) > _OVERVIEW_MAX_LIST_ITEMS:
        return True
    if len(citation_ids) < _OVERVIEW_MIN_CITATIONS:
        return True
    if not has_table and len(words) < _OVERVIEW_MIN_WORDS:
        return True
    return evidence is not None and not _overview_covers_enough_sources(citation_ids, evidence)


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


def _overview_citation_ids(raw_reply: str) -> tuple[str, ...]:
    return tuple(f"E{match.group('id')}" for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply))


def _overview_covers_enough_sources(citation_ids: tuple[str, ...], evidence: TurnEvidence) -> bool:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[citation_id.casefold()]
        for citation_id in citation_ids
        if citation_id.casefold() in source_by_id
    }
    return len(cited_sources) >= _overview_required_distinct_source_count(evidence)


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
        intent_index = session.rag_index
        if (
            intent_index is None
            and session.armory_path is not None
            and session.config.base_url
            and session.config.model
        ):
            intent_index = _ensure_rag_index(session)
        intent_resolution = _resolved_user_intent(
            user_input,
            config=session.config,
            conversation=session.conversation,
            prior_intent=session.last_plan_intent,
            source_catalog=_intent_source_catalog(intent_index),
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
            prior_contract=session.last_turn_contract,
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
    ) -> str:
        localized_reply = _localize_deterministic_reply(
            reply,
            user_input=user_input,
            config=self.session.config,
        )
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
        notice = self._verification_notice(resolved, visible_evidence)
        resolved = _resolved_with_validation_result(resolved, notice)
        self._mark_session_dirty()
        self._record_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )
        self.session.last_plan_intent = _resolved_plan_intent(resolved.learning_plan)
        self.session.last_turn_contract = resolved.turn_contract
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
            retrieval_query=(
                resolved.learning_plan.retrieval_query if resolved.learning_plan else ""
            ),
            turn_contract=(
                resolved.turn_contract.to_dict() if resolved.turn_contract is not None else {}
            ),
            learning_feedback=session.learning_state.last_feedback_type.value,
            evidence_blocks=len(visible_evidence.items) if visible_evidence else 0,
            evidence_refs=_evidence_refs(visible_evidence),
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
