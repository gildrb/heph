"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import json
import re
import threading
import urllib.error
from collections.abc import Callable, Generator, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from html import unescape
from typing import TYPE_CHECKING

from hephaistos._types import is_string_mapping, parse_json_object_fragment
from hephaistos.agent.citation import VerificationResult, verify_citations, verify_response
from hephaistos.agent.dispatch import iter_agent_events
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
)
from hephaistos.chat.evidence import (
    assess_turn_evidence as _assess_turn_evidence,
)
from hephaistos.chat.evidence import (
    build_overview_context as _build_overview_context,
)
from hephaistos.chat.evidence import (
    build_priority_context as _build_priority_context,
)
from hephaistos.chat.evidence import (
    evidence_assessment_trace as _evidence_assessment_trace,
)
from hephaistos.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from hephaistos.chat.evidence import (
    evidence_trace_coverage as _evidence_trace_coverage,
)
from hephaistos.chat.evidence import (
    evidence_trace_items as _evidence_trace_items,
)
from hephaistos.chat.evidence import (
    is_overview_query as _is_overview_query,
)
from hephaistos.chat.evidence import (
    query_demands_source_only_answer as _query_demands_source_only_answer,
)
from hephaistos.chat.evidence import (
    resolve_turn_evidence as _resolve_turn_evidence,
)
from hephaistos.chat.evidence import (
    retrieval_audit_metadata as _retrieval_audit_metadata,
)
from hephaistos.chat.titles import derive_title
from hephaistos.chat.usage import save_usage
from hephaistos.diagnostics.crashes import get_meter, get_tracer
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import infer_material_role_from_text
from hephaistos.memory.workflow import schedule_memory_extraction
from hephaistos.rag import EvidenceChunk, TurnEvidence
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaistos.study import (
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
    material_overview_plan,
    material_source_qa_plan,
    material_topic_drill_plan,
    material_topic_presentation_plan,
    plain_chat_plan,
    plan_turn,
    recall_clarification_plan,
    validate_pedagogy,
)
from hephaistos.study.policy import LearningMoveKind
from hephaistos.study.priority import (
    PriorityTopic,
    PriorityWebSearcher,
    PriorityWebSearchResult,
    analyze_priority,
)
from hephaistos.study.schedule import (
    RecallItemState,
    RecallScheduleStore,
    load_recall_schedule,
    save_recall_schedule,
)

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession
    from hephaistos.rag import ArmoryIndex

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
_TRACE_TASK_BY_ACTION = {
    LearningAction.PRIORITY: "priority",
    LearningAction.SOURCE_QA: "source-qa",
    LearningAction.CALIBRATE: "calibration",
    LearningAction.ASSESS: "active-recall-assessment",
    LearningAction.HINT: "hint",
}
type _IntentPlanBuilder = Callable[[str, str, LearningPhase], LearningTurnPlan]
_MODEL_NORMALIZED_INTENTS = (
    "material_overview",
    "source_qa",
    "source_only_policy",
    "topic_presentation",
    "topic_drill",
    "ready_for_recall",
    "recall_clarification",
    "recall_answer_attempt",
    "chat",
)
_MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = 0.75
_MODEL_NORMALIZED_PLAN_BUILDERS: dict[str, _IntentPlanBuilder] = {
    "chat": lambda user_input, _query, phase: plain_chat_plan(user_input, phase=phase),
    "source_qa": lambda user_input, query, _phase: material_source_qa_plan(
        user_input, retrieval_query=query
    ),
    "topic_presentation": lambda user_input, query, _phase: material_topic_presentation_plan(
        user_input, retrieval_query=query
    ),
    "topic_drill": lambda user_input, query, _phase: material_topic_drill_plan(
        user_input, retrieval_query=query
    ),
}
_EVIDENCE_CITATION_TEXT_RE = re.compile(
    r"\s*(?:\[|【)(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*(?:\]|】)"
)
_EXACT_PHRASE_AFTER_LABEL_RE = re.compile(
    r"\b(?:exact\s+)?phrase\s+(?:is\s*:?\s*)?(?P<phrase>[^\n.;:]+?)(?:\s+when\b|[.]\s*|$)",
    re.IGNORECASE,
)
_QUOTED_PHRASE_RE = re.compile(r"[\"“”'](?P<phrase>[^\"“”']{2,80})[\"“”']")
_OVERVIEW_CITATION_RANGE_RE = re.compile(
    r"\[(?:e|E)\d+\]\s*(?:-|\u2013)\s*(?:\[(?:e|E)\d+\]|(?:e|E)?\d+)"
)
_OVERVIEW_CITATION_ID_RE = re.compile(r"\[(?:e|E)(?P<id>\d+)\]")
_TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call\b[^>]*>.*?</tool_call>", re.IGNORECASE | re.DOTALL)
_TOOL_CALL_OPEN_RE = re.compile(r"<tool_call\b[^>]*>", re.IGNORECASE)
_TOOL_CALL_CLOSE_RE = re.compile(r"</tool_call>", re.IGNORECASE)
_DETERMINISTIC_REPLY_LITERAL_RE = re.compile(r"`[^`]+`|/[\w-]+|\"[^\"]+\"")
_ASSESSMENT_LABEL_RE = re.compile(r"^(?:CORRECT|PARTIAL|WRONG):")
_READ_ALL_FILES_RE = re.compile(
    r"\b(?:"
    r"(?:read|scan|look|go|walk)\s+(?:through|over)?\s*(?:all|every)\s+"
    r"(?:the\s+)?(?:files|documents|pdfs|materials)|"
    r"(?:read|scan)\s+(?:the\s+)?(?:whole|entire|complete)\s+"
    r"(?:corpus|set|folder|armory)"
    r")\b",
    re.IGNORECASE,
)
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MIN_BULLETS = 2
_OVERVIEW_MIN_CITED_BULLETS = 2
_OVERVIEW_TOPIC_LIMIT = 7
_OVERVIEW_WEB_TOPIC_SEARCH_LIMIT = 10
_OVERVIEW_TOPIC_SECTION_HEADING = "These are the topics I found in the material:"
_OVERVIEW_RECOMMENDATIONS_HEADING = "Recommended options:"
_ENGLISH_TOPIC_MENU_CUE_WORDS = frozenset(
    {
        "can",
        "could",
        "create",
        "give",
        "go",
        "help",
        "how",
        "look",
        "overview",
        "please",
        "provide",
        "read",
        "scan",
        "study",
        "summarise",
        "summarize",
        "through",
        "topics",
        "walk",
        "what",
        "which",
        "why",
        "write",
    }
)
_OVERVIEW_REPLY_TOPIC_LINE_RE = re.compile(r"^- (?P<label>.+?)(?:\s+\[(?:e|E)\d+\])?\.?$")
_OVERVIEW_EXPLICIT_DATE_RE = re.compile(
    r"\b(?:"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|"
    r"\d{1,2}\.\s*[A-ZÀ-ÖØ-Þa-zà-öø-ÿ]{3,}\s+\d{4}|"
    r"(?:1[3-9]|2\d|3[01])\.\s*[A-ZÀ-ÖØ-Þa-zà-öø-ÿ]{3,}"
    r")\b"
)
_OVERVIEW_CHRONOLOGICAL_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s*|\d+[.)]\s*)?"
    r"(?:"
    r"(?:first|second|third|next|then|afterwards?|later|finally|subsequently)\b|"
    r"in\s+(?:the\s+)?(?:first|second|third|next|following|later)\b"
    r")",
    re.IGNORECASE,
)
_ENGLISH_TOPIC_PRESENTATION_START_RE = re.compile(
    r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
    r"(?:explain|teach|review|study|go\s+over|walk\s+me\s+through|tell\s+me\s+about|"
    r"help\s+me\s+(?:study|understand))\b",
    re.IGNORECASE,
)
_MAX_INTERNAL_PASSES = 3
_OVERVIEW_REQUIRED_SHAPE: tuple[str, ...] = ()
_OVERVIEW_FORBIDDEN_SHAPE = (
    "corpus-level claim",
    "document signal",
    "indexed source",
    "next action",
    "no evidence citations",
    "non-exhaustive list",
    "not an exhaustive summary",
    "only a sample",
    "partial inventory",
    "ask for recall",
    "answer from memory",
    "retrieved overview sample",
    "source-backed",
    "source backed",
    "say ready when you want recall",
    "sampled mix",
    "sampled orientation",
    "the files cover",
    "visible topics",
)
_UNSOLICITED_LEARNING_FOLLOWUP_LINE_RE = re.compile(
    r"\b(?:next\s+action|say\s+ready|source[-\s]?backed|ask\s+for\s+recall|"
    r"want\s+recall|answer\s+from\s+memory|from\s+memory|recall\s+drill)\b|"
    r"^\s*(?:then\s+)?recall[.!]?\s*$",
    re.IGNORECASE,
)
_INLINE_LEARNING_FOLLOWUP_SUFFIX_RE = re.compile(
    r"(?is)^(?P<body>.+?)\s+(?:"
    r"say\s+ready(?:\s+when\s+you\s+want\s+recall)?|"
    r"next\s+action\s*:\s*.+|"
    r"(?:then\s+)?ask\s+for\s+recall|"
    r"answer\s+from\s+memory|"
    r"include\s+your\s+confidence\s+from\s+0\s*-\s*100%\.?"
    r")[.!?]?\s*$"
)
_PROMPT_USER_REQUEST_RE = re.compile(r"^User request:\s*(?P<request>.+)$", re.MULTILINE)
_PROMPT_USER_FOLLOWUP_RE = re.compile(r"^User follow-up:\s*(?P<request>.+)$", re.MULTILINE)
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
_UNSOLICITED_MENU_RE = re.compile(
    r"(?ims)\n?\s*(?:"
    r"(?:yes|sure|okay|ok)\.?\s+)?"
    r"(?:if\s+you\s+want|i\s+can\s+(?:give|make|turn|show|help)|"
    r"would\s+you\s+like|do\s+you\s+want|next\s+steps?)"
    r"\b.*(?:\n\s*(?:[-*]|\d+[.)]?)\s+\S.+){1,}\s*$"
)
_UNSOLICITED_FOLLOWUP_SENTENCE_RE = re.compile(
    r"(?ims)\n?\s*(?:"
    r"(?:if\s+you\s+want|i\s+can\s+(?:be\s+more\s+specific|give|make|turn|show|help)|"
    r"would\s+you\s+like|do\s+you\s+want|next\s+steps?)"
    r"\b[^\n]*[.!?]?\s*)$"
)
_UNSOLICITED_MENU_INTENT_RE = re.compile(
    r"\b(?:menu|options?|choose|next\s+steps?|what\s+next|study\s+plan|drill|quiz|practice)\b",
    re.IGNORECASE,
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
_OVERVIEW_TOPIC_FRAGMENT_RE = re.compile(
    r"\b(?:"
    r"achtung|defined|definiert|bezeichnet|bezeichnen|setting|setzen|question|questions|"
    r"assessment|prompts?|exam-style|structured|readiness|recall|learning\s+topic"
    r")\b",
    re.IGNORECASE,
)
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
exercises, or proofs.
Every topic must cite exactly one supplied evidence_id and include an exact evidence_quote copied
from that excerpt. Return JSON only, matching this schema:
""".strip()
_LEARNING_INTENT_NORMALIZATION_SCHEMA = "\n".join(
    (
        "{",
        f'  "intent": "{" | ".join(_MODEL_NORMALIZED_INTENTS)}",',
        '  "canonical_english_request": "concise English request preserving the user\'s intent",',
        '  "confidence": 0.0',
        "}",
    )
)
_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = """
Classify a user's learning intent for a local source-grounded assistant. Interpret the request
in whatever language the user wrote, but return an English-first control signal. Do not answer the
request. Use material_overview only when the user asks for the broad picture of the enabled,
uploaded, indexed, or provided materials as a corpus. Use source_qa for a specific fact or quote
from the materials, source_only_policy when the user only instructs Heph not to guess,
hallucinate, invent, or use outside knowledge, topic_presentation for explaining a named concept,
topic_drill for quiz or practice requests, ready_for_recall when the user says they are ready to
answer from memory or continue the active recall step, recall_clarification when active recall is
underway and the user asks to repeat, rephrase, translate, clarify what to answer, or change prompt
language without answering, recall_answer_attempt when the user appears to be answering an
active-recall prompt from memory, and chat when the intent is unclear or not material-specific.
Return JSON only, matching this schema:
""".strip()
_OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT = """
Write a user-facing corpus overview from cited material excerpts. Use only the supplied
evidence. Answer in the same language as the user's request. Give the big picture first and avoid
organizing primarily by dates, filenames, authors, institutions, semester labels, course logistics,
or individual chunks unless the user asks for that metadata. Do not mention calendar dates,
semester labels, lecturer names, or course administration metadata unless the user asks for that
metadata. Include at least two concise bullet lines with evidence IDs such as [E1].
Do not mention internal evidence-grounding blocks, and do not include an English topic menu unless
the user wrote in English. Do not end with a caveat about sampling, orientation, partial inventory,
or non-exhaustive coverage.
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
class _NormalizedLearningIntent:
    intent: str
    canonical_english_request: str
    confidence: float


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
        and not _should_append_english_topic_menu(user_input)
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
    if indexed_reply := _indexed_material_availability_reply(session, index):
        return indexed_reply
    if sources := _enabled_unindexable_sources(session, index):
        materials = _material_list_label(sources)
        reasons = [index.unindexable_files[source] for source in sources]
        return _unindexable_material_reply(materials, reasons)
    return _empty_material_index_reply()


def _indexed_material_availability_reply(session: ChatSession, index: ArmoryIndex) -> str:
    if index.chunk_count <= 0:
        return ""
    if _has_enabled_indexed_material(session, index):
        return ""
    return _all_material_disabled_reply()


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
    if not _should_append_missing_evidence_bullets(plan, cleaned_reply, evidence, verification):
        return cleaned_reply
    return _append_evidence_bullets(cleaned_reply, evidence)


def _can_repair_evidence_citations(reply: str, evidence: TurnEvidence | None) -> bool:
    return bool(reply.strip() and evidence is not None and evidence.items)


def _should_append_missing_evidence_bullets(
    plan: LearningTurnPlan,
    cleaned_reply: str,
    evidence: TurnEvidence,
    verification: VerificationResult,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.SOURCE_QA}:
        return False
    if plan.action is LearningAction.SOURCE_QA:
        return not _reply_contains_evidence_bullet(cleaned_reply, evidence)
    return not verification.has_citations


def _reply_contains_evidence_bullet(reply: str, evidence: TurnEvidence) -> bool:
    return any(line in reply for line in _evidence_bullet_lines(evidence))


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


def _append_evidence_bullets(reply: str, evidence: TurnEvidence) -> str:
    bullets = _evidence_bullet_lines(evidence)
    if not bullets:
        return reply
    return f"{reply.rstrip()}\n\n" + "\n".join(bullets)


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


def _read_all_files_requested(query: str | None) -> bool:
    return bool(query and _READ_ALL_FILES_RE.search(query))


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
    yield from _read_all_scope_events(plan, evidence, index_counts[0])


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
        read_all_requested=_read_all_files_requested(plan.retrieval_query),
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


def _read_all_scope_events(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    indexed_sources: int,
) -> Iterator[MaterialOperationEvent]:
    if not _read_all_files_requested(plan.retrieval_query):
        return
    sampled_sources = evidence.sampled_source_count if evidence else 0
    total_sources = evidence.total_source_count if evidence else indexed_sources
    yield _material_operation_event(
        "read_all_scope",
        (
            "Read-all scope: this turn samples indexed evidence; it did not read every "
            "file end to end. Run `heph index <armory>` for a full index rebuild, then "
            "ask a narrower source-grounded question."
        ),
        query=plan.retrieval_query,
        sampled_sources=sampled_sources,
        total_sources=total_sources,
        command="heph index <armory>",
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
    cleaned = _strip_leading_control_json(cleaned)
    if _overview_turn(plan) or plan.action is LearningAction.SOURCE_QA:
        cleaned = _strip_unsolicited_learning_followup(cleaned)
    cleaned = _strip_unsolicited_chat_menu(plan, cleaned)
    if plan.action is LearningAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", cleaned).strip()
    return cleaned


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


def _strip_unsolicited_chat_menu(plan: LearningTurnPlan, reply: str) -> str:
    if not reply.strip() or _UNSOLICITED_MENU_INTENT_RE.search(_prompt_user_text(plan.prompt)):
        return reply
    cleaned = _UNSOLICITED_MENU_RE.sub("", reply).rstrip()
    cleaned = _UNSOLICITED_FOLLOWUP_SENTENCE_RE.sub("", cleaned).rstrip()
    return cleaned or reply


def _should_buffer_learning_output(plan: LearningTurnPlan) -> bool:
    return plan.buffer_response or plan.action is LearningAction.CHAT


def _prompt_user_text(prompt: str) -> str:
    for pattern in (_PROMPT_USER_REQUEST_RE, _PROMPT_USER_FOLLOWUP_RE):
        if match := pattern.search(prompt):
            return match.group("request")
    return ""


def _strip_unsolicited_learning_followup(reply: str) -> str:
    if not reply.strip():
        return reply
    truncated = _strip_learning_followup_lines(reply.splitlines())
    if truncated is not None:
        return truncated
    return _strip_inline_learning_followup_suffix(reply)


def _strip_learning_followup_lines(lines: list[str]) -> str | None:
    seen_content = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if seen_content and _line_looks_like_unsolicited_learning_followup(stripped):
            return "\n".join(lines[:index]).rstrip()
        if _line_has_substantive_answer_content(stripped):
            seen_content = True
    return None


def _line_has_substantive_answer_content(line: str) -> bool:
    return bool(_OVERVIEW_CITATION_ID_RE.search(line)) or len(re.findall(r"\b\w+\b", line)) >= 4


def _strip_inline_learning_followup_suffix(reply: str) -> str:
    cleaned_lines: list[str] = []
    changed = False
    for line in reply.splitlines():
        match = _INLINE_LEARNING_FOLLOWUP_SUFFIX_RE.match(line.rstrip())
        if match is None:
            cleaned_lines.append(line)
            continue
        body = match.group("body").rstrip()
        if not body:
            cleaned_lines.append(line)
            continue
        cleaned_lines.append(body)
        changed = True
    if not changed:
        return reply.strip()
    return "\n".join(cleaned_lines).strip()


def _line_looks_like_unsolicited_learning_followup(line: str) -> bool:
    if _OVERVIEW_CITATION_ID_RE.search(line):
        return False
    if _UNSOLICITED_LEARNING_FOLLOWUP_LINE_RE.search(line):
        return True
    words = re.findall(r"\b[\w'-]+\b", line)
    return len(words) <= 10 and bool(re.search(r"\brecall\b[.!]?$", line, re.IGNORECASE))


def _strip_tool_call_markup(reply: str) -> str:
    cleaned = _TOOL_CALL_BLOCK_RE.sub("", reply)
    cleaned = _TOOL_CALL_OPEN_RE.sub("", cleaned)
    cleaned = _TOOL_CALL_CLOSE_RE.sub("", cleaned)
    kept_lines = [line for line in cleaned.splitlines() if "<tool_call" not in line.casefold()]
    return "\n".join(kept_lines)


def _append_read_all_scope_disclosure(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if not _should_append_read_all_scope_disclosure(plan, reply):
        return reply
    return (
        f"{reply.rstrip()}\n\n"
        "Read-all scope: I sampled "
        f"{_read_all_scope_sample_text(evidence)}; I did not read every file end to end "
        "in this turn. Run `heph index <armory>` to rebuild the full materials index, "
        "then ask a narrower source-grounded question."
    )


def _should_append_read_all_scope_disclosure(plan: LearningTurnPlan, reply: str) -> bool:
    if not reply.strip() or not _read_all_files_requested(plan.retrieval_query):
        return False
    request_match = _PROMPT_USER_REQUEST_RE.search(plan.prompt)
    if request_match is not None and not _should_append_english_topic_menu(
        request_match.group("request")
    ):
        return False
    normalized = reply.casefold()
    return "did not read every file" not in normalized and "heph index <armory>" not in normalized


def _read_all_scope_sample_text(evidence: TurnEvidence | None) -> str:
    sampled_sources = evidence.sampled_source_count if evidence else 0
    total_sources = evidence.total_source_count if evidence else sampled_sources
    if total_sources > sampled_sources:
        return f"{sampled_sources} of {total_sources} indexed sources"
    if sampled_sources:
        return _count_label(sampled_sources, "indexed source")
    return "the available indexed evidence"


def _run_bounded_internal_repairs(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> tuple[str, int]:
    repaired = reply
    passes = 1  # pass 1 = initial model generation
    if _overview_turn(plan) and repaired == _overview_unavailable_reply():
        return repaired, passes
    for _ in range(_MAX_INTERNAL_PASSES - 1):
        previous = repaired
        repaired = _repair_missing_evidence_citations(plan, repaired, evidence)
        repaired = _append_read_all_scope_disclosure(plan, repaired, evidence)
        passes += 1
        if repaired == previous:
            break
    return repaired, passes


def _isolated_recall_conversation(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
) -> Conversation | None:
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
) -> str:
    extra_system_prompt = plan.prompt
    if plan.action is LearningAction.PRIORITY:
        priority_context = _build_priority_context(session)
        if priority_context:
            extra_system_prompt = f"{plan.prompt}\n\n{priority_context}"
    elif plan.retrieval_query is not None and _is_overview_query(plan.retrieval_query):
        overview_context = _build_overview_context(session)
        if overview_context:
            extra_system_prompt = f"{plan.prompt}\n\n{overview_context}"
    return _append_evidence_assessment_prompt(extra_system_prompt, resolved)


def _postprocess_learning_reply(
    plan: LearningTurnPlan,
    raw_reply: str,
    visible_reply: str,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str,
    config: ChatConfig,
) -> _ProcessedLearningReply:
    if _needs_overview_fallback(plan, raw_reply, resolved.turn_evidence):
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
        )
        raw_reply = fallback_reply or _overview_unavailable_reply()
        visible_reply = raw_reply

    visible_reply, pass_count = _run_bounded_internal_repairs(
        plan,
        visible_reply,
        resolved.turn_evidence,
    )
    return _ProcessedLearningReply(
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        pass_count=pass_count,
    )


def _deterministic_learning_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
) -> _DeterministicLearningReply | None:
    if missing_reply := _missing_indexed_material_reply(session, plan.action):
        return _DeterministicLearningReply(missing_reply)
    return None


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
    query = plan.retrieval_query or ""
    assert evidence is not None
    if exact_phrase := _source_qa_exact_phrase(query, evidence):
        return exact_phrase
    return "\n".join(_evidence_bullet_lines(evidence, limit=4))


def _can_answer_source_qa_from_evidence(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
) -> bool:
    if evidence is None or not evidence.items:
        return False
    query = plan.retrieval_query or ""
    return plan.action is LearningAction.SOURCE_QA or _query_demands_source_only_answer(query)


def _source_qa_exact_phrase(query: str, evidence: TurnEvidence) -> str:
    if not re.search(r"\bexact phrase\b|\bexact wording\b", query, re.IGNORECASE):
        return ""
    for item in evidence.items:
        if phrase := _first_exact_phrase(item.content):
            return f'"{phrase}" [{item.evidence_id}]'
    return ""


def _first_exact_phrase(text: str) -> str:
    for pattern in (_QUOTED_PHRASE_RE, _EXACT_PHRASE_AFTER_LABEL_RE):
        match = pattern.search(text)
        if match is None:
            continue
        phrase = " ".join(match.group("phrase").strip().split())
        if phrase:
            return phrase
    return ""


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
        "Do not fill gaps; scope any answer to cited evidence."
    )


def _overview_turn(plan: LearningTurnPlan) -> bool:
    return (
        plan.action is LearningAction.PRESENT
        and plan.retrieval_query is not None
        and _is_overview_query(plan.retrieval_query)
    )


def _overview_fallback_reply(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    user_input: str = "",
    config: ChatConfig | None = None,
) -> str:
    if not _overview_turn(plan) or evidence is None or not evidence.items:
        return ""

    model_reply = _overview_model_fallback_reply(
        plan,
        evidence,
        user_input=user_input,
        config=config,
    )
    return model_reply or ""


def _overview_unavailable_reply() -> str:
    return (
        "I could not produce a grounded material overview from the current model output. "
        "Please try again or narrow the request to one file or concept."
    )


def _should_append_english_topic_menu(user_input: str) -> bool:
    if not user_input.strip():
        return True
    words = re.findall(r"[a-z]+", user_input.casefold())
    if not words:
        return False
    return any(word in _ENGLISH_TOPIC_MENU_CUE_WORDS for word in words)


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
    plan: LearningTurnPlan,
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> str:
    usable_config = _overview_fallback_config(config)
    if usable_config is None:
        return ""
    conversation = Conversation()
    conversation.add("system", _OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT)
    conversation.add("user", _overview_topic_normalization_context(evidence, user_input))
    reply = _clean_overview_model_reply(_stream_one_shot_model_text(usable_config, conversation))
    if not _valid_overview_model_reply(reply, evidence):
        return ""
    return _append_read_all_scope_disclosure(plan, reply, evidence)


def _overview_fallback_config(config: ChatConfig | None) -> ChatConfig | None:
    if config is None or not config.base_url or not config.model:
        return None
    return config


def _clean_overview_model_reply(model_text: str) -> str:
    if not model_text:
        return ""
    reply = _strip_tool_call_markup(model_text).strip()
    return _strip_unsolicited_learning_followup(reply)


def _valid_overview_model_reply(reply: str, evidence: TurnEvidence) -> bool:
    if not reply:
        return False
    verification = verify_citations(reply, evidence)
    return (
        verification.has_citations
        and verification.all_verified
        and not _overview_answer_has_bad_shape(reply, evidence)
    )


def _stream_one_shot_model_text(config: ChatConfig, conversation: Conversation) -> str:
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
) -> _LearningAgentRequest:
    conversation = (
        _isolated_recall_conversation(plan, original_learning_state, user_input)
        or session.conversation
    )
    return _LearningAgentRequest(
        conversation=conversation,
        buffer_output=_should_buffer_learning_output(plan),
    )


def _overview_topic_normalization_context(evidence: TurnEvidence, user_input: str) -> str:
    lines = [
        f"User request: {user_input.strip() or '(none)'}",
        "Evidence excerpts:",
    ]
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


def _should_model_normalize_learning_intent(
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
    config: ChatConfig | None,
) -> bool:
    if not _can_model_normalize_intent(config, plan, user_input):
        return False
    if _overview_turn(plan) or _ENGLISH_TOPIC_PRESENTATION_START_RE.search(user_input):
        return False
    if state.current_item:
        return _should_normalize_active_recall_intent(plan, state)
    return plan.action is LearningAction.PRESENT and plan.allow_tools


def _can_model_normalize_intent(
    config: ChatConfig | None,
    plan: LearningTurnPlan,
    user_input: str,
) -> bool:
    return bool(config is not None and config.base_url and config.model and user_input.strip())


def _should_normalize_active_recall_intent(
    plan: LearningTurnPlan,
    state: LearningState,
) -> bool:
    if state.phase is LearningPhase.WAITING_FOR_READY:
        return plan.action is LearningAction.REVIEW
    return state.phase is LearningPhase.RECALL and plan.action is LearningAction.ASSESS


def _model_normalized_learning_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
) -> _NormalizedLearningIntent | None:
    payload = _model_json_payload(
        config,
        system_prompt=(
            f"{_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT}\n{_LEARNING_INTENT_NORMALIZATION_SCHEMA}"
        ),
        user_prompt=f"User request:\n{user_input.strip()}",
    )
    return _normalized_learning_intent_from_payload(payload) if payload is not None else None


def _model_json_payload(
    config: ChatConfig | None,
    *,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, object] | None:
    if config is None or not config.base_url or not config.model:
        return None
    conversation = Conversation()
    conversation.add("system", system_prompt)
    conversation.add("user", user_prompt)
    return parse_json_object_fragment(_stream_one_shot_model_text(config, conversation))


def _normalized_learning_intent_from_payload(
    payload: Mapping[str, object],
) -> _NormalizedLearningIntent | None:
    raw_intent = payload.get("intent")
    if not isinstance(raw_intent, str):
        return None
    intent = re.sub(r"[^a-z0-9]+", "_", raw_intent.strip().casefold()).strip("_")
    if intent not in _MODEL_NORMALIZED_INTENTS:
        return None
    raw_request = payload.get("canonical_english_request")
    canonical_request = raw_request.strip() if isinstance(raw_request, str) else ""
    confidence = _normalized_confidence(payload.get("confidence"))
    return _NormalizedLearningIntent(
        intent=intent,
        canonical_english_request=canonical_request,
        confidence=confidence,
    )


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


def _model_normalized_learning_plan(
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
    config: ChatConfig | None,
) -> LearningTurnPlan:
    normalized = _accepted_normalized_learning_intent(plan, state, user_input, config)
    if normalized is None:
        return plan
    canonical_query = normalized.canonical_english_request or user_input
    return _learning_plan_from_normalized_intent(
        normalized.intent,
        plan,
        state,
        user_input,
        canonical_query,
    )


def _accepted_normalized_learning_intent(
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
    config: ChatConfig | None,
) -> _NormalizedLearningIntent | None:
    if not _should_model_normalize_learning_intent(plan, state, user_input, config):
        return None
    normalized = _model_normalized_learning_intent(user_input, config=config)
    if normalized is None or normalized.confidence < _MODEL_NORMALIZED_CONFIDENCE_THRESHOLD:
        return None
    return normalized


def _learning_plan_from_normalized_intent(
    intent: str,
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
    canonical_query: str,
) -> LearningTurnPlan:
    recall_plan = _model_normalized_recall_plan(intent, plan, state, user_input)
    if recall_plan is not None:
        return recall_plan
    if intent == "source_only_policy":
        return _source_only_policy_plan(user_input, state.phase)
    if builder := _MODEL_NORMALIZED_PLAN_BUILDERS.get(intent):
        return builder(user_input, canonical_query, state.phase)
    return _model_normalized_overview_plan(intent, plan, user_input, canonical_query)


def _model_normalized_recall_plan(
    intent: str,
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
) -> LearningTurnPlan | None:
    if intent == "ready_for_recall":
        return _normalized_ready_for_recall_plan(plan, state)
    if intent == "recall_clarification":
        return _normalized_recall_clarification_plan(plan, state, user_input)
    return None


def _normalized_ready_for_recall_plan(
    plan: LearningTurnPlan,
    state: LearningState,
) -> LearningTurnPlan:
    if state.phase is LearningPhase.WAITING_FOR_READY and state.current_item:
        return plan_turn(state, "ready")
    return plan


def _normalized_recall_clarification_plan(
    plan: LearningTurnPlan,
    state: LearningState,
    user_input: str,
) -> LearningTurnPlan:
    if state.phase is LearningPhase.RECALL and state.current_item:
        return recall_clarification_plan(user_input, current_item=state.current_item)
    return plan


def _source_only_policy_plan(user_input: str, phase: LearningPhase) -> LearningTurnPlan:
    return LearningTurnPlan(
        action=LearningAction.CHAT,
        phase=phase,
        prompt=plain_chat_plan(user_input, phase=phase).prompt,
        allow_tools=False,
    )


def _model_normalized_overview_plan(
    intent: str,
    plan: LearningTurnPlan,
    user_input: str,
    canonical_query: str,
) -> LearningTurnPlan:
    if intent != "material_overview":
        return plan
    retrieval_query = canonical_query or "what is the material about"
    if not _is_overview_query(retrieval_query):
        retrieval_query = "what is the material about"
    return material_overview_plan(user_input, retrieval_query=retrieval_query)


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
            _OVERVIEW_TOPIC_FRAGMENT_RE.search(topic) is not None,
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
) -> bool:
    if not _overview_turn(plan) or evidence is None or not evidence.items:
        return False
    verification = verify_citations(raw_reply, evidence)
    if not verification.has_citations or not verification.all_verified:
        return True
    return _overview_answer_has_bad_shape(raw_reply, evidence)


def _overview_answer_has_bad_shape(
    raw_reply: str,
    evidence: TurnEvidence | None = None,
) -> bool:
    if _overview_answer_has_invalid_structure(raw_reply):
        return True
    citation_ids = _overview_citation_ids(raw_reply)
    if _overview_answer_has_weak_evidence_shape(raw_reply, citation_ids, evidence):
        return True
    topic_labels = _overview_reply_topic_labels(raw_reply)
    return _overview_answer_has_bad_topic_labels(topic_labels)


def _overview_answer_has_invalid_structure(raw_reply: str) -> bool:
    return (
        _OVERVIEW_CITATION_RANGE_RE.search(raw_reply) is not None
        or _overview_answer_has_bad_required_language(raw_reply)
        or _overview_answer_is_date_or_document_organized(raw_reply)
    )


def _overview_answer_has_weak_evidence_shape(
    raw_reply: str,
    citation_ids: tuple[str, ...],
    evidence: TurnEvidence | None,
) -> bool:
    return (
        _overview_answer_is_too_thin(raw_reply, citation_ids)
        or (evidence is not None and not _overview_covers_enough_sources(citation_ids, evidence))
        or not _overview_has_enough_cited_bullets(raw_reply)
    )


def _overview_answer_has_bad_topic_labels(topic_labels: Sequence[str]) -> bool:
    return len(topic_labels) > _OVERVIEW_TOPIC_LIMIT or any(
        not _overview_topic_is_useful(label) for label in topic_labels
    )


def _overview_answer_has_bad_required_language(raw_reply: str) -> bool:
    normalized = raw_reply.casefold()
    return any(phrase not in normalized for phrase in _OVERVIEW_REQUIRED_SHAPE) or any(
        phrase in normalized for phrase in _OVERVIEW_FORBIDDEN_SHAPE
    )


def _overview_citation_ids(raw_reply: str) -> tuple[str, ...]:
    return tuple(f"E{match.group('id')}" for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply))


def _overview_answer_is_too_thin(raw_reply: str, citation_ids: tuple[str, ...]) -> bool:
    words = re.findall(r"\b[\w'-]+\b", raw_reply)
    return len(words) < _OVERVIEW_MIN_WORDS or len(citation_ids) < _OVERVIEW_MIN_CITATIONS


def _overview_covers_enough_sources(citation_ids: tuple[str, ...], evidence: TurnEvidence) -> bool:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[citation_id.casefold()]
        for citation_id in citation_ids
        if citation_id.casefold() in source_by_id
    }
    available_source_count = len(set(source_by_id.values()))
    return len(cited_sources) >= min(_OVERVIEW_MIN_DISTINCT_SOURCES, available_source_count)


def _overview_has_enough_cited_bullets(raw_reply: str) -> bool:
    bullet_lines = [
        line.strip() for line in raw_reply.splitlines() if line.lstrip().startswith(("- ", "* "))
    ]
    cited_bullets = [line for line in bullet_lines if _OVERVIEW_CITATION_ID_RE.search(line)]
    return (
        len(bullet_lines) >= _OVERVIEW_MIN_BULLETS
        and len(cited_bullets) >= _OVERVIEW_MIN_CITED_BULLETS
    )


def _overview_answer_is_date_or_document_organized(raw_reply: str) -> bool:
    date_lines = [
        line for line in raw_reply.splitlines() if _OVERVIEW_EXPLICIT_DATE_RE.search(line)
    ]
    chronology_lines = [
        line for line in raw_reply.splitlines() if _OVERVIEW_CHRONOLOGICAL_LINE_RE.search(line)
    ]
    return len(date_lines) >= 2 or len(chronology_lines) >= 2


def _overview_reply_topic_labels(raw_reply: str) -> tuple[str, ...]:
    labels: list[str] = []
    for stripped in _overview_topic_section_lines(raw_reply):
        match = _OVERVIEW_REPLY_TOPIC_LINE_RE.match(stripped)
        if match is None:
            if labels:
                break
            continue
        labels.append(match.group("label").strip())
    return tuple(labels)


def _overview_topic_section_lines(raw_reply: str) -> Iterator[str]:
    in_topics = False
    for line in raw_reply.splitlines():
        stripped = line.strip()
        if stripped.startswith(_OVERVIEW_TOPIC_SECTION_HEADING.removesuffix(":")):
            in_topics = True
            continue
        if not in_topics:
            continue
        if not stripped or stripped == _OVERVIEW_RECOMMENDATIONS_HEADING:
            break
        yield stripped


@dataclass(slots=True)
class TurnOrchestrator:
    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)
    last_internal_passes: int = field(default=1, init=False)

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
        learning_plan = plan_turn(
            original_learning_state,
            user_input,
            due_reviews=due_reviews,
            memory_state=memory_state,
            allow_direct_chat=False,
        )
        learning_plan = _model_normalized_learning_plan(
            learning_plan,
            original_learning_state,
            user_input,
            session.config,
        )
        if notice := _reading_notice(learning_plan):
            yield NoticeEvent(notice, code="reading")
        resolved = self._resolve_timed_turn_plan(learning_plan)
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
        request = _learning_agent_request(plan, original_learning_state, user_input, session)
        for event in iter_agent_events(
            session.config,
            request.conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=_learning_extra_system_prompt(session, plan, resolved),
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

        if deterministic_reply := _deterministic_learning_reply(session, plan):
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
        visible_evidence = _visible_turn_evidence(resolved)
        session.last_turn_evidence = visible_evidence
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
        visible_evidence = _visible_turn_evidence(resolved)
        notice = self._verification_notice(resolved, visible_evidence)
        self._mark_session_dirty()
        self._record_successful_reply(
            resolved,
            visible_evidence,
            latency_ms=latency_ms,
            notice=notice,
        )
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
