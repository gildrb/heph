"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import re
import threading
import urllib.error
from collections.abc import Iterator
from dataclasses import dataclass, field
from html import unescape
from typing import TYPE_CHECKING

from hephaistos.agent.citation import verify_citations, verify_response
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
from hephaistos.chat.titles import derive_title
from hephaistos.chat.usage import save_usage
from hephaistos.diagnostics.crashes import get_meter, get_tracer
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import infer_material_role_from_text
from hephaistos.memory.workflow import schedule_memory_extraction
from hephaistos.rag import TurnEvidence
from hephaistos.runtime import (
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaistos.study import (
    MemoryState,
    PolicyOutcome,
    ReviewItem,
    StudyAction,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyState,
    StudyTurnPlan,
    apply_turn_result,
    learner_assessment_from_state,
    plan_turn,
    validate_pedagogy,
)
from hephaistos.study.priority import PriorityWebSearcher, analyze_priority, duckduckgo_search
from hephaistos.study.schedule import StudyItemState, load_study_schedule, save_study_schedule

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

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
        StudyAction.PRIORITY,
        StudyAction.SOURCE_QA,
        StudyAction.PRESENT,
        StudyAction.HINT,
        StudyAction.SIMPLIFY,
        StudyAction.REVIEW,
        StudyAction.ASSESS,
    }
)
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
_OVERVIEW_MIN_BULLETS = 3
_OVERVIEW_MIN_CITED_BULLETS = 2
_OVERVIEW_TOPIC_LIMIT = 7
_OVERVIEW_WEB_TOPIC_SEARCH_LIMIT = 10
_OVERVIEW_TOPIC_SECTION_HEADING = "These are the study topics I found in the material:"
_OVERVIEW_RECOMMENDATIONS_HEADING = "Recommended options:"
_OVERVIEW_TOPIC_MENU_PROMPT = (
    "Choose a topic to study next. In the shell, use ↑/↓ and press Enter."
)
_OVERVIEW_REPLY_TOPIC_LINE_RE = re.compile(r"^- (?P<label>.+?)(?:\s+\[(?:e|E)\d+\])?\.?$")
_GUIDED_RECOMMENDATION_LABEL_RE = re.compile(
    r"^\s*Recommendation\s*:", re.IGNORECASE | re.MULTILINE
)
_MAX_INTERNAL_PASSES = 3
_OVERVIEW_REQUIRED_SHAPE: tuple[str, ...] = ()
_OVERVIEW_FORBIDDEN_SHAPE = (
    "corpus-level claim",
    "document signal",
    "indexed source",
    "no evidence citations",
    "not an exhaustive summary",
    "retrieved overview sample",
    "say ready when you want recall",
    "sampled mix",
    "sampled orientation",
    "the files cover",
    "visible topics",
)
_OVERVIEW_METADATA_LINE_RE = re.compile(
    r"\b(?:university|universität|institute|department|faculty|semester|professor|lecturer|"
    r"instructor|dozent|dozentin|author|email|opencourseware)\b",
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
        "mathematik",
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
        "informatiker",
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
    r"(?:mathematik|math(?:ematics)?|informatik|computer\s+science|biochemistry|biology|"
    r"chemistry|physics|calculus|analysis|algebra)\s+"
    r"(?:für|fuer|for|[ivx]{1,4}|\d)|"
    r"(?:module|modul|course|vorlesung)\s*[:#]?\s*\d*"
    r")\b",
    re.IGNORECASE,
)
_OVERVIEW_CONTENT_CUE_RE = re.compile(
    r"\b(?:"
    r"abstract|aims?|aufgabe|beispiel|chapter|definition|example|exercise|goals?|"
    r"inhaltsverzeichnis|introduction|lemma|learning\s+outcomes?|method|objectives?|"
    r"problem|proof|question|satz|summary|theorem|topics?|überblick|uebung|übung"
    r")\b",
    re.IGNORECASE,
)
_OVERVIEW_FORMULA_RE = re.compile(r"(?:\\[a-zA-Z]+|[$=∑∫√≤≥→↦∀∃])")
_OVERVIEW_LINE_MARKER_RE = re.compile(r"^[#*\-\d.\s:;()\[\]]+")
_OVERVIEW_TOPIC_FRAGMENT_RE = re.compile(
    r"\b(?:"
    r"achtung|defined|definiert|bezeichnet|bezeichnen|setting|setzen|question|questions|"
    r"assessment|prompts?|exam-style|structured|readiness|recall|study\s+topic"
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
_OVERVIEW_CANONICAL_LABELS = {
    "ableitungen": "Ableitungen",
    "derivatives": "Derivatives",
    "differenzierbarkeit": "Differenzierbarkeit",
    "folgen": "Folgen",
    "sequences": "Sequences",
    "grenzwerte": "Grenzwerte",
    "limits": "Limits",
    "konvergenz": "Konvergenz",
    "partialsummen": "Partialsummen",
    "reihen": "Reihen",
    "series": "Series",
    "stetigkeit": "Stetigkeit",
    "continuity": "Continuity",
    "integrale": "Integrale",
    "taylorreihen": "Taylorreihen",
    "kurvendiskussion": "Kurvendiskussion",
}


def _material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    return f"@{name or source}"


def _readable_material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1] or source
    stem = name.rsplit(".", maxsplit=1)[0]
    readable = re.sub(r"[-_]+", " ", stem).strip()
    return readable or name


def _format_material_labels(sources: list[str]) -> str:
    labels = [_material_label(source) for source in sources[:3]]
    rendered = ", ".join(labels)
    remaining = len(sources) - len(labels)
    if remaining > 0:
        rendered = f"{rendered}, and {remaining} more"
    return rendered


def _missing_indexed_material_reply(session: ChatSession, action: StudyAction) -> str:
    if action not in _EVIDENCE_REQUIRED_ACTIONS:
        return ""
    index = session.rag_index
    if session.source_file_count <= 0:
        return ""
    if index is None:
        return (
            "The armory has visible materials, but Hephaistos could not prepare the "
            "searchable materials index for this turn. I cannot answer from outside "
            "knowledge. Check the material files or run `heph index <armory>` to see "
            "the indexing error directly."
        )
    if index.chunk_count > 0:
        indexed_enabled = any(
            document.source not in session.disabled_source_files and document.chunks
            for document in index.documents
        )
        if indexed_enabled:
            return ""
        return (
            "The armory has searchable materials, but all indexed material is currently "
            "disabled. Enable at least one material with /materials before asking."
        )

    unindexable_sources = [
        source
        for source in sorted(index.unindexable_files)
        if source not in session.disabled_source_files
    ]
    if unindexable_sources:
        materials = _format_material_labels(unindexable_sources)
        reasons = {index.unindexable_files[source] for source in unindexable_sources}
        if all("conversion backend unavailable" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but PDF/document conversion is unavailable in this "
                "installation. I cannot answer from outside knowledge. Update or reinstall "
                "Hephaistos, then ask again or run `heph index <armory>` to verify indexing."
            )
        if all("docling conversion failed" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but document conversion did not extract searchable "
                "text from it. I cannot answer from outside knowledge. Re-export, replace, "
                "or convert the document to text/Markdown, then ask again."
            )
        if all("timed out" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but document conversion timed out before searchable "
                "text was indexed. I cannot answer from outside knowledge. Re-export or "
                "convert the material to text/Markdown, then ask again."
            )
        if all("docling" in reason.lower() for reason in reasons):
            return (
                f"I can see {materials}, but it is not searchable armory evidence yet. "
                "I cannot answer from outside knowledge. Update Hephaistos, then ask again "
                "or run `heph index <armory>` to verify indexing."
            )
        return (
            f"I can see {materials}, but no searchable text was indexed from it. "
            "I cannot answer from outside knowledge. Convert the material to text or "
            "Markdown, then ask again."
        )

    return (
        "The armory has visible materials, but no searchable evidence is indexed yet. "
        "I cannot answer from outside knowledge. Hephaistos prepares the index "
        "automatically when possible; run `heph index <armory>` to inspect the failure."
    )


def _needs_source_only_no_evidence_fallback(
    plan: StudyTurnPlan,
    resolved: ResolvedTurnPlan,
) -> bool:
    assessment = resolved.evidence_assessment
    if assessment is not None and assessment.recommended_action == "abstain":
        return True
    if resolved.turn_evidence is not None:
        return False
    if _overview_turn(plan):
        return False
    if plan.action is StudyAction.SOURCE_QA:
        return True
    query = plan.retrieval_query or ""
    return bool(query and _query_demands_source_only_answer(query))


def _repair_missing_evidence_citations(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if not reply.strip() or evidence is None or not evidence.items:
        return reply
    if plan.action not in {StudyAction.PRESENT, StudyAction.SOURCE_QA}:
        return reply
    verification = verify_citations(reply, evidence)
    if verification.unverified:
        reply = _remove_unverified_citations(reply, verification.unverified)
        verification = verify_citations(reply, evidence)
    if verification.has_citations:
        return reply
    bullets = [
        f"- {_readable_material_label(item.source)}: "
        f"{_trace_excerpt(item.content, limit=700)} [{item.evidence_id}]"
        for item in evidence.items[:8]
    ]
    return f"{reply.rstrip()}\n\nEvidence checked:\n" + "\n".join(bullets)


def _remove_unverified_citations(reply: str, unverified_ids: list[str]) -> str:
    cleaned = reply
    for evidence_id in unverified_ids:
        cleaned = re.sub(rf"\s*\[\s*{re.escape(evidence_id)}\s*\]", "", cleaned)
    return cleaned


def _append_key_evidence_for_source_qa(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if plan.action is not StudyAction.SOURCE_QA:
        return reply
    if not reply.strip() or evidence is None or not evidence.items:
        return reply
    if "Key evidence:" in reply or "Evidence checked:" in reply:
        return reply
    bullets = [
        f"- {_readable_material_label(item.source)}: "
        f"{_trace_excerpt(item.content, limit=700)} [{item.evidence_id}]"
        for item in evidence.items[:8]
    ]
    return f"{reply.rstrip()}\n\nKey evidence:\n" + "\n".join(bullets)


def _visible_turn_evidence(resolved: ResolvedTurnPlan) -> TurnEvidence | None:
    plan = resolved.study_plan
    if plan is not None and plan.action is StudyAction.CALIBRATE:
        return None
    return resolved.turn_evidence


def _evidence_notice(resolved: ResolvedTurnPlan) -> str:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return ""
    plan = resolved.study_plan
    if plan is not None and _overview_turn(plan):
        sources = list(dict.fromkeys(item.source for item in visible_evidence.items))
        labels = ", ".join(_material_label(source) for source in sources[:4])
        remaining = len(sources) - 4
        suffix = f", and {remaining} more" if remaining > 0 else ""
        sampled_sources = visible_evidence.sampled_source_count or len(sources)
        total_sources = visible_evidence.total_source_count or sampled_sources
        source_plural = "s" if total_sources != 1 else ""
        excerpt_plural = "s" if len(visible_evidence.items) != 1 else ""
        notice = (
            f"Using {len(visible_evidence.items)} overview evidence excerpt{excerpt_plural} "
            f"from {sampled_sources} of {total_sources} indexed source{source_plural}: "
            f"{labels}{suffix}"
        )
        return _append_evidence_assessment_notice(notice, resolved)
    refs = _evidence_refs(visible_evidence)
    shown = ", ".join(refs[:3])
    remaining = len(refs) - 3
    suffix = f", and {remaining} more" if remaining > 0 else ""
    plural = "s" if len(refs) != 1 else ""
    notice = f"Using {len(refs)} retrieved evidence excerpt{plural}: {shown}{suffix}"
    return _append_evidence_assessment_notice(notice, resolved)


def _append_evidence_assessment_notice(notice: str, resolved: ResolvedTurnPlan) -> str:
    assessment = resolved.evidence_assessment
    if assessment is None or assessment.sufficient:
        return notice
    action = assessment.recommended_action.replace("_", " ")
    return f"{notice}. Evidence sufficiency: {action} ({assessment.confidence:.0%})."


def _evidence_notice_metadata(resolved: ResolvedTurnPlan) -> dict[str, object]:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return {}
    plan = resolved.study_plan
    task = _trace_task(plan)
    return {
        "task": task,
        "refs": _evidence_refs(visible_evidence),
        "coverage": _evidence_trace_coverage(visible_evidence),
        "items": _evidence_trace_items(visible_evidence),
        "assessment": _evidence_assessment_trace(resolved.evidence_assessment),
    }


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


def _index_counts(session: ChatSession) -> tuple[int, int]:
    index = session.rag_index
    if index is None:
        return 0, 0
    enabled_documents = [
        document
        for document in index.documents
        if document.source not in session.disabled_source_files and document.chunks
    ]
    return len(enabled_documents), sum(len(document.chunks) for document in enabled_documents)


def _read_all_files_requested(query: str | None) -> bool:
    return bool(query and _READ_ALL_FILES_RE.search(query))


def _material_operation_events(
    session: ChatSession,
    plan: StudyTurnPlan,
    resolved: ResolvedTurnPlan,
) -> list[MaterialOperationEvent]:
    if plan.direct_reply is not None or plan.action is StudyAction.CALIBRATE:
        return []
    if not (plan.retrieval_query or plan.use_expected_source_refs or resolved.turn_evidence):
        return []

    events: list[MaterialOperationEvent] = []
    indexed_sources, indexed_chunks = _index_counts(session)
    if indexed_sources or indexed_chunks:
        events.append(
            _material_operation_event(
                "index_ready",
                (
                    f"Material index ready: {indexed_sources} enabled source"
                    f"{'' if indexed_sources == 1 else 's'}, {indexed_chunks} chunk"
                    f"{'' if indexed_chunks == 1 else 's'}."
                ),
                indexed_sources=indexed_sources,
                indexed_chunks=indexed_chunks,
            )
        )

    evidence = _visible_turn_evidence(resolved)
    if _overview_turn(plan):
        sampled_sources = evidence.sampled_source_count if evidence else 0
        total_sources = evidence.total_source_count if evidence else indexed_sources
        evidence_blocks = len(evidence.items) if evidence else 0
        events.append(
            _material_operation_event(
                "sample_overview",
                (
                    f"Sampling corpus overview: {evidence_blocks} excerpt"
                    f"{'' if evidence_blocks == 1 else 's'} from {sampled_sources} of "
                    f"{total_sources} indexed source{'' if total_sources == 1 else 's'}."
                ),
                query=plan.retrieval_query,
                evidence_blocks=evidence_blocks,
                sampled_sources=sampled_sources,
                total_sources=total_sources,
                read_all_requested=_read_all_files_requested(plan.retrieval_query),
            )
        )
    elif plan.use_expected_source_refs and session.study_state.expected_source_refs:
        events.append(
            _material_operation_event(
                "open_stored_evidence",
                (
                    "Opening stored material evidence from the current recall item: "
                    + ", ".join(session.study_state.expected_source_refs[:3])
                ),
                refs=list(session.study_state.expected_source_refs),
            )
        )
    elif plan.retrieval_query:
        events.append(
            _material_operation_event(
                "search_index",
                f"Searching indexed materials for: {plan.retrieval_query}",
                query=plan.retrieval_query,
                indexed_sources=indexed_sources,
                indexed_chunks=indexed_chunks,
            )
        )

    if evidence is not None and evidence.items:
        for item in evidence.items[:3]:
            ref = f"{item.source}#chunk={item.chunk_index}"
            events.append(
                _material_operation_event(
                    "read_excerpt",
                    (f"Opened {ref}: {_trace_excerpt(item.content, limit=180)}"),
                    evidence_id=item.evidence_id,
                    ref=ref,
                    source=item.source,
                    chunk=item.chunk_index,
                    score=round(item.score, 4),
                    text_excerpt=_trace_excerpt(item.content, limit=240),
                )
            )
    elif plan.retrieval_query:
        events.append(
            _material_operation_event(
                "search_result",
                "Material search returned no matching indexed evidence.",
                query=plan.retrieval_query,
                indexed_sources=indexed_sources,
                indexed_chunks=indexed_chunks,
            )
        )

    if _read_all_files_requested(plan.retrieval_query):
        sampled_sources = evidence.sampled_source_count if evidence else 0
        total_sources = evidence.total_source_count if evidence else indexed_sources
        events.append(
            _material_operation_event(
                "read_all_scope",
                (
                    "Read-all scope: this turn samples indexed evidence; it did not read every "
                    "file end to end. Run `heph index <armory>` for a full index rebuild, then "
                    "ask a narrower source-backed question."
                ),
                query=plan.retrieval_query,
                sampled_sources=sampled_sources,
                total_sources=total_sources,
                command="heph index <armory>",
            )
        )
    return events


def _reading_notice(plan: StudyTurnPlan) -> str:
    if plan.direct_reply is not None or plan.action is StudyAction.CALIBRATE:
        return ""
    if _overview_turn(plan):
        return "Preparing the material index and reading enabled evidence for a corpus overview."
    if plan.retrieval_query or plan.use_expected_source_refs:
        return "Preparing the material index and reading relevant evidence."
    return ""


def _writing_notice(plan: StudyTurnPlan) -> str:
    if plan.direct_reply is not None:
        return ""
    if plan.action is StudyAction.CALIBRATE:
        return ""
    if _overview_turn(plan):
        return "Writing a grounded corpus overview."
    return "Writing a grounded response."


def _student_visible_reply(plan: StudyTurnPlan, reply: str) -> str:
    cleaned = _strip_tool_call_markup(reply).strip()
    if plan.action is StudyAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", cleaned).strip()
    return cleaned


def _strip_tool_call_markup(reply: str) -> str:
    cleaned = _TOOL_CALL_BLOCK_RE.sub("", reply)
    cleaned = _TOOL_CALL_OPEN_RE.sub("", cleaned)
    cleaned = _TOOL_CALL_CLOSE_RE.sub("", cleaned)
    kept_lines = [line for line in cleaned.splitlines() if "<tool_call" not in line.casefold()]
    return "\n".join(kept_lines)


def _append_read_all_scope_disclosure(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if not reply.strip() or not _read_all_files_requested(plan.retrieval_query):
        return reply
    normalized = reply.casefold()
    if "did not read every file" in normalized or "heph index <armory>" in normalized:
        return reply
    sampled_sources = evidence.sampled_source_count if evidence else 0
    total_sources = evidence.total_source_count if evidence else sampled_sources
    if total_sources > sampled_sources:
        sample_text = f"{sampled_sources} of {total_sources} indexed sources"
    elif sampled_sources:
        sample_text = f"{sampled_sources} indexed source{'' if sampled_sources == 1 else 's'}"
    else:
        sample_text = "the available indexed evidence"
    return (
        f"{reply.rstrip()}\n\n"
        f"Read-all scope: I sampled {sample_text}; I did not read every file end to end in "
        "this turn. Run `heph index <armory>` to rebuild the full materials index, then ask "
        "a narrower source-backed question."
    )


def _insufficient_evidence_reply(
    plan: StudyTurnPlan,
    resolved: ResolvedTurnPlan,
) -> str:
    assessment = resolved.evidence_assessment
    if assessment is None or assessment.sufficient:
        return ""
    if plan.action is StudyAction.CALIBRATE:
        return ""
    missing = ", ".join(assessment.missing_information) or "supporting source evidence"
    action = assessment.recommended_action
    if action == "abstain":
        return _source_qa_fallback_reply(plan, resolved.turn_evidence) or (
            "I do not have enough source evidence to answer that reliably. "
            f"Missing: {missing}. Please narrow the source-backed target."
        )
    if (
        action == "retrieve_more"
        and resolved.turn_evidence is None
        and plan.action is StudyAction.SOURCE_QA
    ):
        return (
            "I do not have enough indexed evidence for a reliable answer yet. "
            f"Missing: {missing}. "
            "Please narrow the question to one concept, theorem, or exercise so I can retrieve "
            "a tighter evidence set."
        )
    if action == "ask_clarifying_question":
        return (
            "Before I answer from sources, I need one clarification: "
            f"which exact concept or item should I target? Missing: {missing}."
        )
    if action == "quiz_first":
        return (
            "Evidence is thin for a direct answer, so I will test your current understanding "
            "first: answer one focused recall question from memory and include confidence 0-100%."
        )
    return ""


def _apply_grounding_repairs(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    repaired = _repair_missing_evidence_citations(plan, reply, evidence)
    repaired = _append_key_evidence_for_source_qa(plan, repaired, evidence)
    return _append_read_all_scope_disclosure(plan, repaired, evidence)


def _run_bounded_internal_repairs(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> tuple[str, int]:
    """Run a bounded generate->grounding->pedagogy repair loop."""
    repaired = reply
    passes = 1  # pass 1 = initial model generation
    for _ in range(_MAX_INTERNAL_PASSES - 1):
        previous = repaired
        repaired = _apply_grounding_repairs(plan, repaired, evidence)
        repaired = _repair_pedagogy_shape(plan, repaired)
        passes += 1
        if repaired == previous:
            break
    return repaired, passes


def _isolated_recall_conversation(
    plan: StudyTurnPlan,
    original_study_state: StudyState,
    user_input: str,
) -> Conversation | None:
    """Return a minimal context for recall control turns that must not see answers."""
    if plan.action in {
        StudyAction.PROMPT_RECALL,
        StudyAction.REFUSE_REVEAL,
        StudyAction.WAIT_READY_REMINDER,
    }:
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    if (
        original_study_state.phase is StudyPhase.RECALL
        and plan.action is StudyAction.CHAT
        and plan.retrieval_query is None
    ):
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    return None


def _repair_pedagogy_shape(plan: StudyTurnPlan, reply: str) -> str:
    move = plan.study_move
    if (
        not reply.strip()
        or move is None
        or plan.action in {StudyAction.CALIBRATE, StudyAction.CHAT}
    ):
        return reply
    validation = validate_pedagogy(reply, move, plan.autonomy_mode)
    if validation.valid:
        return reply
    additions: list[str] = []
    issues = set(validation.issues)
    if "possible answer leakage during recall" in issues:
        additions.append(
            "Pause before using the solution: answer the active-recall task from memory first."
        )
    if "missing confidence request" in issues:
        additions.append("Include your confidence from 0-100%.")
    if "missing explicit next action" in issues:
        next_action = validation.suggested_next_action or move.expected_output_shape
        if next_action:
            additions.append(f"Next action: {next_action}")
    if "missing recommendation rationale" in issues:
        additions.append(f"Why this helps: {move.reason}.")
    if not additions:
        return reply
    return f"{reply.rstrip()}\n\n" + "\n".join(dict.fromkeys(additions))


def _learner_assessment_trace(plan: StudyTurnPlan | None, state: StudyState) -> dict[str, object]:
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


def _pedagogy_validation_trace(plan: StudyTurnPlan | None, reply: str) -> dict[str, object]:
    if plan is None or plan.study_move is None:
        return {}
    validation = validate_pedagogy(reply, plan.study_move, plan.autonomy_mode)
    return {
        "valid": validation.valid,
        "issues": list(validation.issues),
        "rewrite_instruction": validation.rewrite_instruction or "",
        "suggested_next_action": validation.suggested_next_action or "",
        "move": plan.study_move.kind,
    }


def _trace_excerpt(text: str, *, limit: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _trace_task(plan: StudyTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material-overview"
    if plan.action is StudyAction.PRIORITY:
        return "priority"
    if plan.action is StudyAction.SOURCE_QA:
        return "source-qa"
    if plan.action is StudyAction.CALIBRATE:
        return "calibration"
    if plan.action is StudyAction.ASSESS:
        return "active-recall-assessment"
    if plan.action is StudyAction.HINT:
        return "hint"
    return plan.action.value


def _study_autopilot_context(session: ChatSession) -> tuple[tuple[ReviewItem, ...], MemoryState]:
    if session.armory_path is None:
        return (), MemoryState()
    store = load_study_schedule(session.armory_path)
    due_reviews = tuple(
        ReviewItem(
            item=item.item,
            concept=item.concept,
            failures=item.failures,
            last_confidence=item.last_confidence,
        )
        for item in store.due_items(limit=5)
    )
    weak_items = sorted(
        (
            item
            for item in store.item_list
            if item.failures > 0
            or item.mastery < 0.55
            or item.next_best_action
            in {"contrastive_question", "give_hint", "prerequisite_repair"}
        ),
        key=lambda item: (-item.failures, item.mastery, -item.exam_importance),
    )
    weak_topics = tuple(
        dict.fromkeys(item.concept or item.retrieval_query or item.item for item in weak_items)
    )
    misconception_items = [
        item
        for item in weak_items
        if item.next_best_action == "contrastive_question" or item.common_errors
    ]
    misconceptions = tuple(
        dict.fromkeys(
            item.concept or item.retrieval_query or item.item for item in misconception_items
        )
    )
    successful_interventions: list[str] = []
    failed_interventions: list[str] = []
    for item in store.item_list:
        successful_interventions.extend(item.successful_interventions or [])
        failed_interventions.extend(item.failed_interventions or [])
    for move_type, stats in store.policy_stats.items():
        if stats.success_rate >= 0.6 and stats.uses >= 2:
            successful_interventions.append(move_type)
        elif stats.uses >= 2:
            failed_interventions.append(move_type)
    return due_reviews, MemoryState(
        weak_topics=weak_topics[:5],
        misconceptions=misconceptions[:5],
        successful_interventions=tuple(dict.fromkeys(successful_interventions)),
        failed_interventions=tuple(dict.fromkeys(failed_interventions)),
    )


def _matching_study_item(
    items: list[StudyItemState],
    *,
    item: str,
    retrieval_query: str,
) -> StudyItemState | None:
    for candidate in items:
        if candidate.item == item and candidate.retrieval_query == retrieval_query:
            return candidate
    return None


def _source_qa_fallback_reply(plan: StudyTurnPlan, evidence: TurnEvidence | None) -> str:
    """Return a local source-grounded fallback when source QA streaming is empty."""
    source_only_query = bool(
        plan.retrieval_query and _query_demands_source_only_answer(plan.retrieval_query)
    )
    if plan.action is not StudyAction.SOURCE_QA and not source_only_query:
        return ""
    if evidence is None or not evidence.items:
        return (
            "The enabled armory sources do not contain an answer to that question. "
            "Enable the relevant material with /materials or add a more specific source."
        )

    query = plan.retrieval_query or ""
    wants_exact_phrase = bool(
        re.search(r"\bexact phrase\b|\bexact wording\b", query, re.IGNORECASE)
    )
    if wants_exact_phrase:
        for item in evidence.items:
            for pattern in (_QUOTED_PHRASE_RE, _EXACT_PHRASE_AFTER_LABEL_RE):
                match = pattern.search(item.content)
                if match is not None:
                    phrase = " ".join(match.group("phrase").strip().split())
                    if phrase:
                        return f'"{phrase}" [{item.evidence_id}]'

    bullets: list[str] = []
    for item in evidence.items[:4]:
        source = _readable_material_label(item.source)
        excerpt = _trace_excerpt(item.content, limit=700)
        bullets.append(f"- {source}: {excerpt} [{item.evidence_id}]")
    return "The indexed sources provide this directly:\n" + "\n".join(bullets)


def _append_evidence_assessment_prompt(
    prompt: str,
    resolved: ResolvedTurnPlan,
) -> str:
    """Inject weak-evidence routing instructions into the model turn prompt."""
    plan = resolved.study_plan
    assessment = resolved.evidence_assessment
    if not prompt or plan is None or assessment is None:
        return prompt
    if plan.action is StudyAction.CHAT:
        return prompt
    if plan.action is StudyAction.CALIBRATE or assessment.sufficient:
        return prompt
    missing = ", ".join(assessment.missing_information) or "missing supporting evidence"
    refs = ", ".join(assessment.supporting_refs) or "none"
    action = assessment.recommended_action.replace("_", " ")
    return (
        f"{prompt}\n\n"
        "Evidence sufficiency gate:\n"
        f"- Verdict: insufficient or partial evidence; confidence {assessment.confidence:.0%}.\n"
        f"- Recommended action: {action}.\n"
        f"- Supporting refs: {refs}.\n"
        f"- Missing information: {missing}.\n"
        "- Do not fill gaps from outside knowledge. If you answer, scope the answer to "
        "the cited evidence and state what remains unsupported."
    )


def _overview_turn(plan: StudyTurnPlan) -> bool:
    return (
        plan.action is StudyAction.PRESENT
        and plan.retrieval_query is not None
        and _is_overview_query(plan.retrieval_query)
    )


def _overview_fallback_reply(
    plan: StudyTurnPlan,
    evidence: TurnEvidence | None,
    *,
    web_searcher: PriorityWebSearcher | None = None,
) -> str:
    """Return a conservative local overview when model grounding is unusable."""
    if not _overview_turn(plan) or evidence is None or not evidence.items:
        return ""

    topic_items = _overview_topic_items(evidence, web_searcher=web_searcher)
    if not topic_items:
        lines = ["I could not identify precise study topics from the sampled material yet."]
        content_clues = _overview_content_clues(evidence, limit=3)
        if content_clues:
            lines.append("")
            lines.append("What the sample does show:")
            lines.extend(f"- {clue}" for clue in content_clues)
        return _append_read_all_scope_disclosure(plan, "\n".join(lines), evidence)

    recommendations = _overview_recommendation_items(evidence, topic_items)

    lines = [_OVERVIEW_TOPIC_SECTION_HEADING]
    lines.extend(f"- {topic}" for topic in topic_items[:_OVERVIEW_TOPIC_LIMIT])
    lines.append("")
    lines.append(_OVERVIEW_TOPIC_MENU_PROMPT)
    if recommendations:
        lines.append("")
        lines.append(_OVERVIEW_RECOMMENDATIONS_HEADING)
        lines.extend(f"- {recommendation}" for recommendation in recommendations)
    return _append_read_all_scope_disclosure(plan, "\n".join(lines), evidence)


def _append_guided_choice_menu(
    plan: StudyTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    """Append selectable study options while preserving a good model-written summary."""
    if (
        plan.autonomy_mode is not StudyAutonomyMode.GUIDED
        or plan.action is not StudyAction.PRESENT
        or evidence is None
        or not evidence.items
        or not reply.strip()
        or _reply_has_selectable_study_menu(reply)
    ):
        return reply
    if not _overview_turn(plan) and _GUIDED_RECOMMENDATION_LABEL_RE.search(reply) is None:
        return reply

    topic_items = _overview_topic_items(evidence, web_searcher=None)
    if not topic_items:
        return reply

    recommendations = _overview_recommendation_items(evidence, topic_items)
    lines = ["", _OVERVIEW_TOPIC_SECTION_HEADING]
    lines.extend(f"- {topic}" for topic in topic_items[:_OVERVIEW_TOPIC_LIMIT])
    lines.append("")
    lines.append(_OVERVIEW_TOPIC_MENU_PROMPT)
    if recommendations:
        lines.append("")
        lines.append(_OVERVIEW_RECOMMENDATIONS_HEADING)
        lines.extend(f"- {recommendation}" for recommendation in recommendations)
    return f"{reply.rstrip()}\n" + "\n".join(lines)


def _reply_has_selectable_study_menu(reply: str) -> bool:
    normalized = reply.casefold()
    topic_heading = _OVERVIEW_TOPIC_SECTION_HEADING.removesuffix(":").casefold()
    if _OVERVIEW_TOPIC_MENU_PROMPT in reply:
        return True
    return topic_heading in normalized and (
        _OVERVIEW_RECOMMENDATIONS_HEADING.casefold() in normalized or "menu" in normalized
    )


def _overview_source_role_sentence(evidence: TurnEvidence) -> str:
    content_by_source: dict[str, list[str]] = {}
    evidence_id_by_source: dict[str, str] = {}
    for item in evidence.items:
        content_by_source.setdefault(item.source, []).append(item.content)
        evidence_id_by_source.setdefault(item.source, item.evidence_id)

    candidates: list[tuple[str, str, str]] = []
    for source, snippets in content_by_source.items():
        role, confidence, _reason = infer_material_role_from_text(source, " ".join(snippets))
        if confidence < 0.6:
            continue
        evidence_id = evidence_id_by_source[source]
        candidates.append((role, _material_label(source), evidence_id))
    signals = [
        f"{label}: {_overview_role_label(role)} [{evidence_id}]"
        for role, label, evidence_id in _select_role_diverse_items(candidates, limit=5)
    ]
    return "; ".join(signals)


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
        f"{_overview_role_label(role)} ({len(sources)} source{'' if len(sources) == 1 else 's'}, "
        f"e.g. [{role_examples[role]}])"
        for role, sources in sorted(sources_by_role.items())
    ]
    return "; ".join(parts) + "."


def _overview_role_label(role: str) -> str:
    return _OVERVIEW_ROLE_LABELS.get(role, role.replace("_", " "))


def _overview_content_clues(evidence: TurnEvidence, *, limit: int = 8) -> list[str]:
    """Return readable, cited content cues without depending on a subject or language."""
    candidates: list[tuple[str, str, str]] = []
    seen_sources: set[str] = set()
    for item in evidence.items:
        if item.source in seen_sources:
            continue
        cue = _overview_content_cue(item.content)
        if not cue:
            continue
        seen_sources.add(item.source)
        role, _confidence, _reason = infer_material_role_from_text(item.source, item.content)
        if role == "past_exam":
            cue = "exam-style questions or structured assessment prompts"
        elif role == "assignment":
            cue = "exercise or assignment prompts"
        candidates.append((role, f"{_material_label(item.source)}: {cue}", item.evidence_id))
    return [
        f"{label} [{evidence_id}]"
        for _role, label, evidence_id in _select_role_diverse_items(candidates, limit=limit)
    ]


def _select_role_diverse_items(
    candidates: list[tuple[str, str, str]],
    *,
    limit: int,
) -> list[tuple[str, str, str]]:
    selected: list[tuple[str, str, str]] = []
    seen_roles: set[str] = set()
    for candidate in candidates:
        role, _label, _evidence_id = candidate
        if role in seen_roles:
            continue
        seen_roles.add(role)
        selected.append(candidate)
        if len(selected) >= limit:
            return selected
    for candidate in candidates:
        if candidate in selected:
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            return selected
    return selected


def _overview_content_cue(text: str) -> str:
    lines = [_clean_overview_line(line) for line in unescape(text).splitlines()]
    candidates = [line for line in lines if _overview_line_is_content_cue(line)]
    if not candidates:
        sentences = re.split(r"(?<=[.!?])\s+", " ".join(unescape(text).split()))
        candidates = [
            _clean_overview_line(sentence)
            for sentence in sentences
            if _overview_line_is_content_cue(_clean_overview_line(sentence))
        ]
    if not candidates:
        candidates = [
            _clean_overview_line(line)
            for line in lines
            if 18 <= len(line) <= 140 and not _overview_line_looks_like_metadata(line)
        ]
    if not candidates:
        return ""
    return _trim_overview_cue(candidates[0])


def _clean_overview_line(line: str) -> str:
    cleaned = " ".join(unescape(line).strip().split())
    cleaned = cleaned.replace("[... truncated]", "").strip()
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", cleaned).strip()
    return cleaned.strip(" -:;")


def _overview_line_is_content_cue(line: str) -> bool:
    if not 8 <= len(line) <= 180:
        return False
    if _overview_line_looks_like_metadata(line):
        return False
    normalized = line.casefold()
    if normalized in _OVERVIEW_TOPIC_STOPWORDS:
        return False
    if normalized.startswith(("http://", "https://")):
        return False
    if "ocw.mit.edu" in normalized:
        return False
    if re.fullmatch(r"(?:question|aufgabe|problem|exercise)\s+\d+[a-z]?", normalized):
        return False
    return bool(_OVERVIEW_CONTENT_CUE_RE.search(line) or _OVERVIEW_FORMULA_RE.search(line))


def _overview_line_looks_like_metadata(line: str) -> bool:
    if _OVERVIEW_METADATA_LINE_RE.search(line):
        return True
    if _looks_like_name_line(line):
        return True
    return bool(_OVERVIEW_DATE_LINE_RE.search(line) and _looks_like_name_line(line))


def _trim_overview_cue(line: str, *, limit: int = 120) -> str:
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip(" ,;:.") + "…"


def _overview_topic_items(
    evidence: TurnEvidence,
    *,
    web_searcher: PriorityWebSearcher | None = None,
) -> list[str]:
    topic_clues = _overview_heading_topics(evidence)
    seen = {_normalize_overview_topic(topic.rsplit(" [", maxsplit=1)[0]) for topic in topic_clues}

    analysis = analyze_priority((item.chunk for item in evidence.items), limit=16)
    evidence_id_by_source = {item.source: item.evidence_id for item in evidence.items}
    subject_hint = _overview_subject_hint(evidence)
    web_checked = 0
    for topic in analysis.topics:
        evidence_id = ""
        for source in topic.sources:
            evidence_id = evidence_id_by_source.get(source, "")
            if evidence_id:
                break
        label = _overview_display_topic(topic.topic)
        normalized_topic = _normalize_overview_topic(label)
        if not evidence_id or normalized_topic in seen:
            continue
        if _overview_topic_source_role(topic.sources, evidence) in {"assignment", "past_exam"}:
            continue
        if _overview_topic_looks_like_metadata(topic.topic, evidence):
            continue
        if not _overview_topic_is_useful(label):
            continue
        if web_searcher is not None and web_checked < _OVERVIEW_WEB_TOPIC_SEARCH_LIMIT:
            web_checked += 1
            if not _overview_topic_web_supported(label, subject_hint, web_searcher):
                continue
        seen.add(normalized_topic)
        topic_clues.append(f"{label} [{evidence_id}]")
        if len(topic_clues) >= _OVERVIEW_TOPIC_LIMIT:
            break
    return topic_clues


def _overview_topic_sentence(evidence: TurnEvidence) -> str:
    topic_clues = _overview_topic_items(evidence)
    if not topic_clues:
        return ""
    return ", ".join(topic_clues)


def _overview_default_web_searcher(evidence: TurnEvidence | None) -> PriorityWebSearcher | None:
    if evidence is None or not evidence.items:
        return None
    return duckduckgo_search


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


def _overview_display_topic(topic: str) -> str:
    normalized = _normalize_overview_topic(topic)
    return _OVERVIEW_CANONICAL_LABELS.get(normalized, topic)


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

    topic_words = [
        word for word in re.findall(r"[\wÄÖÜäöüß+-]+", topic.casefold()) if len(word) > 2
    ]
    if not topic_words:
        return False
    for result in results[:3]:
        haystack = f"{result.title} {result.snippet}".casefold()
        if not all(word in haystack for word in topic_words):
            continue
        if _OVERVIEW_WEB_EDUCATION_RE.search(haystack):
            return True
    return False


def _overview_recommendation_items(
    evidence: TurnEvidence,
    topic_items: list[str],
) -> list[str]:
    clean_topics = [_split_overview_citation(topic)[0] for topic in topic_items]
    cited_topics = topic_items[:3]
    recommendations: list[str] = []
    if cited_topics:
        recommendations.append(f"Start with a guided explanation of {cited_topics[0]}.")
    if _overview_has_role(evidence, {"past_exam", "assignment"}):
        practice_source = _overview_first_role_citation(evidence, {"past_exam", "assignment"})
        target = ""
        if len(cited_topics) > 1:
            target = cited_topics[1]
        elif cited_topics:
            target = cited_topics[0]
        if target:
            source_text = f" using {practice_source}" if practice_source else ""
            recommendations.append(
                f"Practice one exam-style or exercise question on {target}{source_text}."
            )
        else:
            source_text = f" {practice_source}" if practice_source else ""
            recommendations.append(
                f"Practice one exam-style or exercise question from the material{source_text}."
            )
    if len(cited_topics) >= 2:
        topic_pair = " and ".join(clean_topics[:2])
        citation = _overview_first_citation(cited_topics[1])
        recommendations.append(f"Compare {topic_pair} so you can separate the ideas {citation}.")
    if len(clean_topics) >= 3:
        citation = _overview_first_citation(cited_topics[2])
        recommendations.append(
            f"Make a short study order for {', '.join(clean_topics[:3])} {citation}."
        )
    recommendations.append("Turn the selected topic into a quick recall drill.")
    return _dedupe_overview_recommendations(recommendations)[:3]


def _overview_has_role(evidence: TurnEvidence, roles: set[str]) -> bool:
    for item in evidence.items:
        role, confidence, _reason = infer_material_role_from_text(item.source, item.content)
        if confidence >= 0.6 and role in roles:
            return True
    return False


def _overview_first_role_citation(evidence: TurnEvidence, roles: set[str]) -> str:
    for item in evidence.items:
        role, confidence, _reason = infer_material_role_from_text(item.source, item.content)
        if confidence >= 0.6 and role in roles:
            return f"[{item.evidence_id}]"
    return ""


def _dedupe_overview_recommendations(recommendations: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for recommendation in recommendations:
        normalized = _normalize_overview_topic(recommendation)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(recommendation)
    return deduped


def _split_overview_citation(text: str) -> tuple[str, str]:
    match = _OVERVIEW_CITATION_ID_RE.search(text)
    if match is None:
        return text.strip(), ""
    citation = match.group(0)
    label = text[: match.start()].strip()
    return label, citation


def _overview_first_citation(text: str) -> str:
    _label, citation = _split_overview_citation(text)
    return citation


def _overview_heading_topics(evidence: TurnEvidence, *, limit: int = 8) -> list[str]:
    topic_clues: list[str] = []
    seen: set[str] = set()
    for item in evidence.items:
        candidates = [item.chunk.heading, *_overview_markdown_headings(item.content)]
        for candidate in candidates:
            topic = _clean_overview_line(candidate)
            normalized_topic = _normalize_overview_topic(topic)
            if not normalized_topic or normalized_topic in seen:
                continue
            if not _overview_topic_is_useful(topic):
                continue
            if _overview_heading_looks_like_metadata(topic):
                continue
            seen.add(normalized_topic)
            topic_clues.append(f"{topic} [{item.evidence_id}]")
            break
        if len(topic_clues) >= min(limit, _OVERVIEW_TOPIC_LIMIT):
            break
    return topic_clues


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


def _overview_heading_looks_like_metadata(heading: str) -> bool:
    if _OVERVIEW_METADATA_LINE_RE.search(heading):
        return True
    return bool(_OVERVIEW_DATE_LINE_RE.search(heading))


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
    if len(normalized) < 4:
        return False
    if normalized == "table" or normalized in _OVERVIEW_GENERIC_TOPIC_LABELS:
        return False
    if _OVERVIEW_COURSE_TITLE_RE.search(topic):
        return False
    if _OVERVIEW_TOPIC_FRAGMENT_RE.search(topic):
        return False
    if _OVERVIEW_FORMULA_RE.search(topic):
        return False
    if re.search(r"[.:;!?]|->|:=|=>", topic):
        return False
    words = normalized.split()
    if any(word in _OVERVIEW_TOPIC_STOPWORDS for word in words):
        return False
    return len(words) <= 5


def _overview_topic_looks_like_metadata(topic: str, evidence: TurnEvidence) -> bool:
    normalized_topic = " ".join(topic.casefold().split())
    if not normalized_topic:
        return True
    for item in evidence.items:
        lines = [line.strip() for line in item.content.splitlines() if line.strip()]
        for line_index, line in enumerate(lines[:10]):
            normalized_line = " ".join(line.casefold().split()).strip("# ")
            if normalized_line != normalized_topic:
                continue
            neighboring = " ".join(lines[max(0, line_index - 2) : line_index + 3])
            if _OVERVIEW_METADATA_LINE_RE.search(neighboring):
                return True
            if _OVERVIEW_DATE_LINE_RE.search(neighboring) and _looks_like_name_line(line):
                return True
    return False


def _looks_like_name_line(line: str) -> bool:
    words = [word.strip(".,;:()[]{}") for word in line.split()]
    letter_words = [word for word in words if any(char.isalpha() for char in word)]
    if not 2 <= len(letter_words) <= 4:
        return False
    return all(word[:1].isupper() and not word.isupper() for word in letter_words)


def _needs_overview_fallback(
    plan: StudyTurnPlan,
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
    normalized = raw_reply.casefold()
    if _OVERVIEW_CITATION_RANGE_RE.search(raw_reply):
        return True
    if any(phrase not in normalized for phrase in _OVERVIEW_REQUIRED_SHAPE):
        return True
    if any(phrase in normalized for phrase in _OVERVIEW_FORBIDDEN_SHAPE):
        return True
    words = re.findall(r"\b[\w'-]+\b", raw_reply)
    if len(words) < _OVERVIEW_MIN_WORDS:
        return True
    citation_ids = tuple(
        f"E{match.group('id')}" for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply)
    )
    if len(citation_ids) < _OVERVIEW_MIN_CITATIONS:
        return True
    if evidence is not None:
        source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
        cited_sources = {
            source_by_id[citation_id.casefold()]
            for citation_id in citation_ids
            if citation_id.casefold() in source_by_id
        }
        if len(cited_sources) < min(_OVERVIEW_MIN_DISTINCT_SOURCES, len(source_by_id)):
            return True
    bullet_lines = [
        line.strip() for line in raw_reply.splitlines() if line.lstrip().startswith(("- ", "* "))
    ]
    if len(bullet_lines) < _OVERVIEW_MIN_BULLETS:
        return True
    cited_bullets = [line for line in bullet_lines if _OVERVIEW_CITATION_ID_RE.search(line)]
    if len(cited_bullets) < _OVERVIEW_MIN_CITED_BULLETS:
        return True
    topic_labels = _overview_reply_topic_labels(raw_reply)
    if len(topic_labels) > _OVERVIEW_TOPIC_LIMIT:
        return True
    return any(not _overview_topic_is_useful(label) for label in topic_labels)


def _overview_reply_topic_labels(raw_reply: str) -> tuple[str, ...]:
    labels: list[str] = []
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
        match = _OVERVIEW_REPLY_TOPIC_LINE_RE.match(stripped)
        if match is None:
            if labels:
                break
            continue
        labels.append(match.group("label").strip())
    return tuple(labels)


@dataclass(slots=True)
class TurnOrchestrator:
    """Own one user turn end-to-end."""

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
        original_study_state = session.study_state.clone()
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
                    "study_phase": session.study_state.phase.value,
                }
            },
        )

        resolved = ResolvedTurnPlan()
        try:
            with timer:
                if session.armory_path is not None:
                    due_reviews, memory_state = _study_autopilot_context(session)
                    study_plan = plan_turn(
                        original_study_state,
                        user_input,
                        due_reviews=due_reviews,
                        memory_state=memory_state,
                        allow_direct_chat=False,
                    )
                    if notice := _reading_notice(study_plan):
                        yield NoticeEvent(notice, code="reading")
                    resolved = self._resolve_timed_turn_plan(study_plan)
                    yield from self._iter_material_operation_events(study_plan, resolved)
                    if notice := _evidence_notice(resolved):
                        yield NoticeEvent(
                            notice,
                            code="evidence",
                            metadata=_evidence_notice_metadata(resolved),
                        )
                    for event in self._iter_study_events(
                        resolved,
                        original_study_state,
                        user_input=user_input,
                        abort=abort,
                    ):
                        yield event
                else:
                    session.last_turn_evidence = None
                    plain_plan = plan_turn(original_study_state, user_input)
                    if plain_plan.direct_reply is not None:
                        session.study_state, final_reply = apply_turn_result(
                            original_study_state,
                            plain_plan,
                            plain_plan.direct_reply,
                            [],
                        )
                        self.last_reply = final_reply
                        if final_reply and (
                            not session.conversation.messages
                            or session.conversation.messages[-1].role != "assistant"
                        ):
                            session.conversation.add("assistant", final_reply)
                        if final_reply:
                            yield AssistantDeltaEvent(final_reply)
                        return
                    for event in self._iter_plain_events(abort=abort):
                        yield event

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
            self._rollback_turn(original_messages, original_study_state)
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
            self._rollback_turn(original_messages, original_study_state)
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
            self._rollback_turn(original_messages, original_study_state)
            raise

    def _iter_plain_events(self, *, abort: threading.Event | None) -> Iterator[TurnEvent]:
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

        if self.last_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", self.last_reply)
        self.last_internal_passes = 1

    def _iter_study_events(
        self,
        resolved: ResolvedTurnPlan,
        original_study_state: StudyState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.study_plan
        assert plan is not None

        if missing_reply := _missing_indexed_material_reply(session, plan.action):
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                missing_reply,
                [],
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if plan.direct_reply is not None:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                plan.direct_reply,
                [],
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if _needs_source_only_no_evidence_fallback(plan, resolved):
            fallback_reply = _source_qa_fallback_reply(plan, None)
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                fallback_reply,
                [],
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if evidence_reply := _insufficient_evidence_reply(plan, resolved):
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                evidence_reply,
                _evidence_refs(resolved.turn_evidence),
            )
            self.last_reply = final_reply
            self.last_internal_passes = 1
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        if notice := _writing_notice(plan):
            yield NoticeEvent(notice, code="writing")

        extra_system_prompt = plan.prompt
        if plan.action is StudyAction.PRIORITY:
            priority_context = _build_priority_context(session)
            if priority_context:
                extra_system_prompt = f"{plan.prompt}\n\n{priority_context}"
        elif plan.retrieval_query is not None and _is_overview_query(plan.retrieval_query):
            overview_context = _build_overview_context(session)
            if overview_context:
                extra_system_prompt = f"{plan.prompt}\n\n{overview_context}"
        extra_system_prompt = _append_evidence_assessment_prompt(extra_system_prompt, resolved)

        raw_parts: list[str] = []
        last_reply_parts: list[str] = []
        completion_event: TurnCompleteEvent | None = None
        agent_conversation = (
            _isolated_recall_conversation(plan, original_study_state, user_input)
            or session.conversation
        )
        for event in iter_agent_events(
            session.config,
            agent_conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=extra_system_prompt,
            tool_schemas=None if plan.allow_tools else [],
            registry=session.tool_registry,
        ):
            if isinstance(event, AssistantDeltaEvent):
                raw_parts.append(event.delta)
                if not plan.buffer_response:
                    last_reply_parts.append(event.delta)
                    yield event
            elif isinstance(event, TurnCompleteEvent):
                completion_event = event
            else:
                yield event

        raw_reply = "".join(raw_parts)
        streamed_reply = raw_reply
        visible_reply = _student_visible_reply(plan, raw_reply)
        if last_reply_parts:
            self.last_reply = "".join(last_reply_parts)

        if not raw_reply:
            fallback_reply = _source_qa_fallback_reply(plan, resolved.turn_evidence)
            if not fallback_reply:
                fallback_reply = _overview_fallback_reply(
                    plan,
                    resolved.turn_evidence,
                    web_searcher=_overview_default_web_searcher(resolved.turn_evidence),
                )
            if not fallback_reply:
                fallback_reply = (
                    "I could not generate a grounded assessment. Please try again."
                    if plan.buffer_response
                    else "I could not generate a study prompt. Please try again."
                )
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                fallback_reply,
                _evidence_refs(resolved.turn_evidence),
            )
            self.last_reply = final_reply
            if final_reply and (
                not session.conversation.messages
                or session.conversation.messages[-1].role != "assistant"
            ):
                session.conversation.add("assistant", final_reply)
            if final_reply:
                yield AssistantDeltaEvent(final_reply)
            return

        used_overview_fallback = False
        if _needs_overview_fallback(plan, raw_reply, resolved.turn_evidence):
            fallback_reply = _overview_fallback_reply(
                plan,
                resolved.turn_evidence,
                web_searcher=_overview_default_web_searcher(resolved.turn_evidence),
            )
            if fallback_reply:
                raw_reply = fallback_reply
                visible_reply = fallback_reply
                used_overview_fallback = True

        if not used_overview_fallback:
            guided_menu_reply = _append_guided_choice_menu(
                plan, visible_reply, resolved.turn_evidence
            )
            if guided_menu_reply != visible_reply:
                visible_reply = guided_menu_reply
                raw_reply = guided_menu_reply

        visible_reply, pass_count = _run_bounded_internal_repairs(
            plan,
            visible_reply,
            resolved.turn_evidence,
        )
        self.last_internal_passes = pass_count

        if raw_reply:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                visible_reply,
                _evidence_refs(resolved.turn_evidence),
            )
            self._record_study_review_if_needed(
                original_study_state,
                plan,
                _evidence_refs(resolved.turn_evidence),
            )
        else:
            session.study_state = original_study_state
            final_reply = raw_reply

        if final_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", final_reply)
        elif final_reply and raw_reply != final_reply:
            self._replace_last_assistant_message(final_reply)

        self.last_reply = final_reply
        if plan.buffer_response and final_reply:
            yield AssistantDeltaEvent(final_reply)
        elif final_reply and streamed_reply and final_reply != streamed_reply:
            suffix = final_reply.removeprefix(streamed_reply)
            if suffix:
                yield AssistantDeltaEvent(suffix)
        yield _turn_complete_from_result(completion_event, final_reply)

    def _record_study_review_if_needed(
        self,
        original_study_state: StudyState,
        plan: StudyTurnPlan,
        source_refs: list[str],
    ) -> None:
        session = self.session
        if session.armory_path is None or plan.action is not StudyAction.ASSESS:
            return
        if session.study_state.last_recall_rating.value == "none":
            return
        store = load_study_schedule(session.armory_path)
        previous = _matching_study_item(
            store.item_list,
            item=original_study_state.current_item,
            retrieval_query=original_study_state.retrieval_query,
        )
        previous_mastery = previous.mastery if previous is not None else 0.0
        previous_confidence = previous.last_confidence if previous is not None else None
        previous_correctness = 1.0 if previous is not None and previous.last_correct else 0.0
        intervention = plan.study_move.kind if plan.study_move is not None else plan.action.value
        state = store.record_review(
            original_study_state.current_item,
            concept=original_study_state.retrieval_query,
            retrieval_query=original_study_state.retrieval_query,
            source_refs=source_refs or original_study_state.expected_source_refs,
            rating=session.study_state.last_recall_rating,
            elapsed_seconds=session.study_state.last_recall_seconds,
            confidence=session.study_state.last_confidence,
            hint_level_needed=(
                original_study_state.hint_level if original_study_state.hint_level > 0 else None
            ),
            error_type=session.study_state.last_feedback_type.value,
            intervention=intervention,
            exam_importance=1.0 if original_study_state.expected_source_refs else 0.0,
        )
        confidence_delta = 0.0
        if state.last_confidence is not None and previous_confidence is not None:
            confidence_delta = state.last_confidence - previous_confidence
        current_correctness = 1.0 if state.last_correct else 0.0
        correctness_delta = current_correctness - previous_correctness
        if previous is None and not state.last_correct:
            correctness_delta = -1.0
        outcome = PolicyOutcome(
            move_type=intervention,
            topic=original_study_state.retrieval_query or original_study_state.current_item,
            correctness_delta=correctness_delta,
            confidence_delta=confidence_delta,
            mastery_delta=state.mastery - previous_mastery,
            time_cost_seconds=state.last_recall_seconds or 0,
            frustration_signal=(
                session.study_state.last_feedback_type is StudyFeedbackType.WRONG
                and original_study_state.hint_level >= 3
            ),
        )
        store.record_policy_outcome(
            intervention,
            success=state.last_correct,
            mastery_delta=outcome.mastery_delta,
            confidence_delta=outcome.confidence_delta,
            time_cost_seconds=outcome.time_cost_seconds,
            frustration_signal=outcome.frustration_signal,
        )
        session.trace.record_session_event(
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
        save_study_schedule(store)

    def _resolve_timed_turn_plan(self, plan: StudyTurnPlan) -> ResolvedTurnPlan:
        session = self.session
        rag_span = _tracer.start_span("rag.retrieval")
        rag_timer = Timer()
        with rag_timer:
            resolved = self._resolve_turn_plan(plan)
        visible_evidence = _visible_turn_evidence(resolved)
        session.last_turn_evidence = visible_evidence
        if resolved.turn_evidence is not None:
            rag_span.set_attribute("rag.retrieved", len(resolved.turn_evidence.items))
        rag_span.end()
        _rag_duration_hist.record(rag_timer.ms, {"armory": str(session.armory_path or "none")})
        return resolved

    def _resolve_turn_plan(self, plan: StudyTurnPlan) -> ResolvedTurnPlan:
        turn_evidence = _resolve_turn_evidence(self.session, plan)
        return ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=turn_evidence,
            evidence_assessment=_assess_turn_evidence(plan, turn_evidence),
        )

    def _iter_material_operation_events(
        self,
        plan: StudyTurnPlan,
        resolved: ResolvedTurnPlan,
    ) -> Iterator[MaterialOperationEvent]:
        for event in _material_operation_events(self.session, plan, resolved):
            self.session.trace.record_material_operation(
                operation=event.operation,
                message=event.message,
                metadata=event.metadata,
            )
            yield event

    def _rollback_turn(
        self,
        original_messages: list[Message],
        original_study_state: StudyState,
    ) -> None:
        self.session.conversation.messages = original_messages
        self.session.study_state = original_study_state

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str:
        session = self.session
        visible_evidence = _visible_turn_evidence(resolved)
        if resolved.study_plan is not None and resolved.study_plan.action is StudyAction.CALIBRATE:
            notice = ""
        else:
            notice = verify_response(self.last_reply, visible_evidence)

        if not session.title:
            session.title = derive_title(session.conversation)
        session.dirty = True

        _log.info(
            "reply complete",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "reply_len": len(self.last_reply),
                    "latency_ms": latency_ms,
                    "study_phase": session.study_state.phase.value,
                    "study_feedback": session.study_state.last_feedback_type.value,
                    "evidence_blocks": len(visible_evidence.items) if visible_evidence else 0,
                }
            },
        )
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            reply_excerpt=_trace_excerpt(self.last_reply),
            study_phase=session.study_state.phase.value,
            study_action=resolved.study_plan.action.value if resolved.study_plan else "",
            study_task=_trace_task(resolved.study_plan),
            retrieval_query=resolved.study_plan.retrieval_query if resolved.study_plan else "",
            study_feedback=session.study_state.last_feedback_type.value,
            evidence_blocks=len(visible_evidence.items) if visible_evidence else 0,
            evidence_refs=_evidence_refs(visible_evidence),
            evidence_coverage=_evidence_trace_coverage(visible_evidence),
            evidence_items=_evidence_trace_items(visible_evidence),
            evidence_assessment=_evidence_assessment_trace(resolved.evidence_assessment),
            pedagogy_validation=_pedagogy_validation_trace(resolved.study_plan, self.last_reply),
            learner_assessment=_learner_assessment_trace(resolved.study_plan, session.study_state),
            internal_passes=self.last_internal_passes,
            internal_pass_max=_MAX_INTERNAL_PASSES,
            verification_notice=notice,
        )

        if not session.config.is_feature_enabled("disable_memory_extraction"):
            schedule_memory_extraction(
                config=session.config,
                memory=session.memory,
                user_input=user_input,
                reply=self.last_reply,
                evidence=", ".join(_evidence_refs(visible_evidence)),
            )

        if session.armory_path is not None:
            with contextlib.suppress(Exception):
                save_usage(session.armory_path, session.session_id, session.usage)

        return notice

    def _replace_last_assistant_message(self, content: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = content
                return


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
