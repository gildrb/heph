"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import re
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from html import unescape
from typing import TYPE_CHECKING

from hephaistos.agent.citation import verify_citations, verify_response
from hephaistos.agent.dispatch import iter_agent_events
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, TurnCompleteEvent, TurnEvent
from hephaistos.chat.evidence import (
    ResolvedTurnPlan,
)
from hephaistos.chat.evidence import (
    build_overview_context as _build_overview_context,
)
from hephaistos.chat.evidence import (
    build_priority_context as _build_priority_context,
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
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    stream_completion,
)
from hephaistos.study import StudyAction, StudyState, StudyTurnPlan, apply_turn_result, plan_turn
from hephaistos.study.priority import analyze_priority
from hephaistos.study.schedule import load_study_schedule, save_study_schedule

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
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MIN_BULLETS = 3
_OVERVIEW_MIN_CITED_BULLETS = 2
_OVERVIEW_REQUIRED_SHAPE: tuple[str, ...] = ()
_OVERVIEW_FORBIDDEN_SHAPE = (
    "no evidence citations",
    "not an exhaustive summary",
    "retrieved overview sample",
    "say ready when you want recall",
    "the files cover",
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
        "aufgabe",
        "beispiel",
        "beispiele",
        "course",
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
        return (
            f"Using {len(visible_evidence.items)} overview evidence excerpt{excerpt_plural} "
            f"from {sampled_sources} of {total_sources} indexed source{source_plural}: "
            f"{labels}{suffix}"
        )
    refs = _evidence_refs(visible_evidence)
    shown = ", ".join(refs[:3])
    remaining = len(refs) - 3
    suffix = f", and {remaining} more" if remaining > 0 else ""
    plural = "s" if len(refs) != 1 else ""
    return f"Using {len(refs)} retrieved evidence excerpt{plural}: {shown}{suffix}"


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
    }


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
    if plan.action is StudyAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", reply).strip()
    return reply


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


def _overview_turn(plan: StudyTurnPlan) -> bool:
    return (
        plan.action is StudyAction.PRESENT
        and plan.retrieval_query is not None
        and _is_overview_query(plan.retrieval_query)
    )


def _overview_fallback_reply(plan: StudyTurnPlan, evidence: TurnEvidence | None) -> str:
    """Return a conservative local overview when model grounding is unusable."""
    if not _overview_turn(plan) or evidence is None or not evidence.items:
        return ""

    sources: dict[str, str] = {}
    for item in evidence.items:
        sources.setdefault(item.source, item.evidence_id)
    cited_sources = list(sources.items())
    source_citations = " ".join(f"[{evidence_id}]" for _source, evidence_id in cited_sources[:4])
    sampled_sources = evidence.sampled_source_count or len(cited_sources)
    total_sources = evidence.total_source_count or sampled_sources
    if total_sources > sampled_sources:
        source_summary = f"{sampled_sources} of {total_sources} indexed sources were sampled"
    else:
        source_summary = "1 indexed source was sampled"
        if sampled_sources != 1:
            source_summary = f"{sampled_sources} indexed sources were sampled"

    role_sentence = _overview_role_sentence(evidence)
    source_role_sentence = _overview_source_role_sentence(evidence)
    topic_sentence = _overview_topic_sentence(evidence)
    content_clues = _overview_content_clues(evidence)
    lines = [
        (
            f"Sampled orientation: {source_summary}; this is not a complete corpus-level "
            f"claim {source_citations}."
        )
    ]
    if source_role_sentence:
        first_signal = next(
            (signal for signal in source_role_sentence.split("; ") if signal),
            "",
        )
        if first_signal:
            lines.append(f"- Document signal: {first_signal}")
    if role_sentence:
        lines.append(f"- Sampled mix: {role_sentence}")
    if content_clues:
        lines.append(f"- Example evidence: {content_clues[0]}")
    if topic_sentence:
        lines.append(f"- Visible topics: {topic_sentence}")
    lines.append(
        "- Best next use: ask for a specific concept, exercise, exam problem, or lecture title."
    )
    return "\n".join(lines)


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


def _overview_topic_sentence(evidence: TurnEvidence) -> str:
    topic_clues = _overview_heading_topics(evidence)
    seen = {_normalize_overview_topic(topic.rsplit(" [", maxsplit=1)[0]) for topic in topic_clues}

    analysis = analyze_priority((item.chunk for item in evidence.items), limit=10)
    evidence_id_by_source = {item.source: item.evidence_id for item in evidence.items}
    for topic in analysis.topics:
        evidence_id = ""
        for source in topic.sources:
            evidence_id = evidence_id_by_source.get(source, "")
            if evidence_id:
                break
        normalized_topic = _normalize_overview_topic(topic.topic)
        if not evidence_id or normalized_topic in seen:
            continue
        if _overview_topic_source_role(topic.sources, evidence) in {"assignment", "past_exam"}:
            continue
        if _overview_topic_looks_like_metadata(topic.topic, evidence):
            continue
        if not _overview_topic_is_useful(topic.topic):
            continue
        seen.add(normalized_topic)
        topic_clues.append(f"{topic.topic} [{evidence_id}]")
        if len(topic_clues) >= 8:
            break
    if not topic_clues:
        return ""
    return ", ".join(topic_clues)


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
        if len(topic_clues) >= limit:
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
    words = normalized.split()
    if any(word in _OVERVIEW_TOPIC_STOPWORDS for word in words):
        return False
    return not (len(words) == 1 and len(words[0]) < 8)


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
    return len(cited_bullets) < _OVERVIEW_MIN_CITED_BULLETS


@dataclass(slots=True)
class TurnOrchestrator:
    """Own one user turn end-to-end."""

    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)

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
                    study_plan = plan_turn(original_study_state, user_input)
                    if notice := _reading_notice(study_plan):
                        yield NoticeEvent(notice, code="reading")
                    resolved = self._resolve_timed_turn_plan(study_plan)
                    if notice := _evidence_notice(resolved):
                        yield NoticeEvent(
                            notice,
                            code="evidence",
                            metadata=_evidence_notice_metadata(resolved),
                        )
                    for event in self._iter_study_events(
                        resolved,
                        original_study_state,
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

    def _iter_study_events(
        self,
        resolved: ResolvedTurnPlan,
        original_study_state: StudyState,
        *,
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

        if notice := _writing_notice(plan):
            yield NoticeEvent(notice, code="writing")

        if _overview_turn(plan):
            fallback_reply = _overview_fallback_reply(plan, resolved.turn_evidence)
            if fallback_reply:
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
                    yield TurnCompleteEvent(
                        full_text=final_reply,
                        turn_index=len(session.conversation.messages) - 1,
                        latency_ms=0.0,
                        finish_reason="fallback",
                        tokens_remaining=0,
                    )
                return

        extra_system_prompt = plan.prompt
        if plan.action is StudyAction.PRIORITY:
            priority_context = _build_priority_context(session)
            if priority_context:
                extra_system_prompt = f"{plan.prompt}\n\n{priority_context}"
        elif (
            plan.action is StudyAction.PRESENT
            and plan.retrieval_query is not None
            and _is_overview_query(plan.retrieval_query)
        ):
            overview_context = _build_overview_context(session)
            if overview_context:
                extra_system_prompt = f"{plan.prompt}\n\n{overview_context}"

        raw_parts: list[str] = []
        last_reply_parts: list[str] = []
        completion_event: TurnCompleteEvent | None = None
        for event in iter_agent_events(
            session.config,
            session.conversation,
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
                fallback_reply = _overview_fallback_reply(plan, resolved.turn_evidence)
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

        if _needs_overview_fallback(plan, raw_reply, resolved.turn_evidence):
            fallback_reply = _overview_fallback_reply(plan, resolved.turn_evidence)
            if fallback_reply:
                raw_reply = fallback_reply
                visible_reply = fallback_reply

        visible_reply = _repair_missing_evidence_citations(
            plan,
            visible_reply,
            resolved.turn_evidence,
        )
        visible_reply = _append_key_evidence_for_source_qa(
            plan,
            visible_reply,
            resolved.turn_evidence,
        )

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
        store.record_review(
            original_study_state.current_item,
            retrieval_query=original_study_state.retrieval_query,
            source_refs=source_refs or original_study_state.expected_source_refs,
            rating=session.study_state.last_recall_rating,
            elapsed_seconds=session.study_state.last_recall_seconds,
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
        return ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=_resolve_turn_evidence(self.session, plan),
        )

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
