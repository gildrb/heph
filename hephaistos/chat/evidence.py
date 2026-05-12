"""RAG evidence resolution for chat turns."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from html import unescape
from typing import TYPE_CHECKING

from hephaistos.chat.usage import ContextBudget
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import infer_material_role_from_text
from hephaistos.rag import (
    ArmoryIndex,
    Chunk,
    ScoredChunk,
    TransformStrategy,
    TurnEvidence,
    build_turn_evidence,
    load_or_build,
    retrieve,
)
from hephaistos.rag.query_transform import PromptFn
from hephaistos.rag.retrieval_types import EvidenceReference
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaistos.study import StudyAction, StudyTurnPlan
from hephaistos.study.overview import OVERVIEW_REQUEST_RE
from hephaistos.study.priority import analyze_priority

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_log = get_logger("chat.evidence")
_RAG_MIN_SCORE = 0.1
_QUERY_RETRIEVAL_TOP_K = 30
_QUERY_NEIGHBOR_RADIUS = 1
_QUERY_NEIGHBOR_LIMIT = 8
_SOURCE_ONLY_MIN_TOP_SCORE = 0.18
_SOURCE_ONLY_QUERY_RE = re.compile(
    r"\b(?:using|use|from|based on)\s+(?:only\s+)?(?:the\s+)?"
    r"(?:indexed\s+)?(?:sources?|materials?|documents?)\b|"
    r"\b(?:if|when)\s+(?:the\s+)?(?:sources?|materials?|documents?)\s+do\s+not\s+contain\b|"
    r"\bdo\s+not\s+guess\b",
    re.IGNORECASE,
)
_OVERVIEW_CHUNK_LIMIT = 32
_OVERVIEW_CHUNKS_PER_DOCUMENT = 2
_OVERVIEW_DOCUMENT_LIMIT = 32
_OVERVIEW_EXCERPT_CHAR_LIMIT = 700
_OVERVIEW_CONTEXT_TOKEN_BUDGET = 6000
_FRONT_MATTER_METADATA_RE = re.compile(
    r"\b(?:university|universität|institute|department|faculty|semester|professor|lecturer|"
    r"instructor|dozent|dozentin|author|email)\b",
    re.IGNORECASE,
)
_FRONT_MATTER_DATE_RE = re.compile(r"\b\d{1,2}[. ]\s*[A-Za-zÄÖÜäöüß]+\s+\d{4}\b|\b\d{4}\b")
_FRONT_MATTER_CONTENT_RE = re.compile(
    r"\b(?:table of contents|inhaltsverzeichnis|definition|theorem|satz|lemma|proof|beweis|"
    r"question|aufgabe|exercise|übung)\b",
    re.IGNORECASE,
)
_LOW_CONTENT_CHUNK_RE = re.compile(
    r"^\s*(?:cite as:|for information about citing|downloaded on|terms of use\b|"
    r"copyright\b|http://ocw\.mit\.edu/terms)",
    re.IGNORECASE,
)
_DOCUMENT_SURVEY_QUERY_RE = re.compile(
    r"\b(?:problem styles?|topic areas?|topics?|tests?|constraints?|exam material|"
    r"assessment material)\b",
    re.IGNORECASE,
)
_ASSESSMENT_CHUNK_RE = re.compile(
    r"(?:^|\n)\s*(?:question|aufgabe)?\s*\d+[.)]?\s*(?:\(\d+\s*(?:points?|punkte)\)|"
    r".{0,80}\b(?:points?|punkte)\b)|\b(?:question|aufgabe)\s+\d+\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ResolvedTurnPlan:
    """A controller plan plus any retrieved turn evidence."""

    study_plan: StudyTurnPlan | None = None
    turn_evidence: TurnEvidence | None = None
    priority_context: str = ""


def evidence_refs(turn_evidence: TurnEvidence | None) -> list[str]:
    """Return stable source/chunk references for turn evidence."""
    if not turn_evidence:
        return []
    return [
        EvidenceReference(item.source, item.chunk_index).render() for item in turn_evidence.items
    ]


def _excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(unescape(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def evidence_trace_items(turn_evidence: TurnEvidence | None) -> list[dict[str, object]]:
    """Return compact evidence metadata for local session traces."""
    if not turn_evidence:
        return []
    return [
        {
            "evidence_id": item.evidence_id,
            "ref": EvidenceReference(item.source, item.chunk_index).render(),
            "score": round(item.score, 4),
            "text_excerpt": _excerpt(item.content),
        }
        for item in turn_evidence.items
    ]


def evidence_trace_coverage(turn_evidence: TurnEvidence | None) -> dict[str, int]:
    """Return compact evidence coverage metadata for local session traces."""
    if not turn_evidence:
        return {
            "evidence_blocks": 0,
            "sampled_sources": 0,
            "total_sources": 0,
        }
    fallback_sources = {item.source for item in turn_evidence.items}
    sampled_sources = turn_evidence.sampled_source_count or len(fallback_sources)
    total_sources = turn_evidence.total_source_count or sampled_sources
    return {
        "evidence_blocks": len(turn_evidence.items),
        "sampled_sources": sampled_sources,
        "total_sources": total_sources,
    }


def parse_source_ref(ref: str) -> tuple[str, int] | None:
    """Parse ``path#chunk=N`` evidence references."""
    parsed = EvidenceReference.parse(ref)
    if parsed is None:
        return None
    return parsed.source, parsed.chunk_index


_FLAG_STRATEGY_MAP: dict[str, TransformStrategy] = {
    "rag_expansion": TransformStrategy.EXPANSION,
    "rag_hyde": TransformStrategy.HYDE,
    "rag_multi_query": TransformStrategy.MULTI_QUERY,
}


def resolve_transform_strategy(config: ChatConfig) -> TransformStrategy:
    """Resolve RAG query-transform strategy from feature flags."""
    for flag, strategy in _FLAG_STRATEGY_MAP.items():
        if config.is_feature_enabled(flag):
            return strategy
    return TransformStrategy.EXPANSION


def build_prompt_fn(config: ChatConfig) -> PromptFn:
    """Build a prompt function for LLM-based query transforms."""

    def _prompt(prompt_text: str) -> str:
        conv = Conversation()
        conv.add("user", prompt_text)
        client = build_client(config)
        messages = to_chat_completion_messages(conv.to_api_messages())
        resp = client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=500,
            stream=False,
        )
        content = resp.choices[0].message.content
        return content if isinstance(content, str) else ""

    return _prompt


def ensure_rag_index(session: ChatSession) -> ArmoryIndex | None:
    """Load and cache the armory RAG index on the session."""
    if session.armory_path is None:
        return None
    if session.rag_index is None or session.rag_index.is_stale():
        session.rag_index = load_or_build(session.armory_path)
    return session.rag_index


def _enabled_scored_chunks(
    scored: list[ScoredChunk],
    disabled_sources: set[str],
) -> list[ScoredChunk]:
    if not disabled_sources:
        return scored
    return [
        scored_chunk
        for scored_chunk in scored
        if scored_chunk.chunk.source not in disabled_sources
    ]


def query_demands_source_only_answer(query: str) -> bool:
    return bool(_SOURCE_ONLY_QUERY_RE.search(query))


def _filter_weak_source_only_evidence(
    query: str,
    scored: list[ScoredChunk],
) -> list[ScoredChunk]:
    if not scored or not query_demands_source_only_answer(query):
        return scored
    top_score = max(scored_chunk.score for scored_chunk in scored)
    if top_score < _SOURCE_ONLY_MIN_TOP_SCORE:
        return []
    return scored


def adaptive_rag_budget(session: ChatSession) -> int:
    """Allocate a bounded retrieval context budget for the current session."""
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    api_msgs = session.conversation.to_api_messages()
    remaining = budget.tokens_remaining(api_msgs)  # type: ignore[arg-type]
    return min(session.config.rag_context_budget, max(200, int(remaining * 0.3)))


def _is_overview_query(query: str) -> bool:
    return bool(OVERVIEW_REQUEST_RE.search(query.strip()))


def is_overview_query(query: str) -> bool:
    """Return whether a query asks for broad material/corpus overview."""
    return _is_overview_query(query)


def build_turn_evidence_from_query(session: ChatSession, query: str) -> TurnEvidence | None:
    """Retrieve and build evidence for a free-text query."""
    if session.armory_path is None:
        return None
    try:
        timer = Timer()
        index = ensure_rag_index(session)
        if index is None:
            return None

        strategy = resolve_transform_strategy(session.config)
        prompt_fn: PromptFn | None = None
        if strategy in (TransformStrategy.HYDE, TransformStrategy.MULTI_QUERY):
            prompt_fn = build_prompt_fn(session.config)

        with timer:
            scored = retrieve(
                query,
                index,
                top_k=_QUERY_RETRIEVAL_TOP_K,
                min_score=_RAG_MIN_SCORE,
                transform_strategy=strategy,
                prompt_fn=prompt_fn,
            )
        scored = _enabled_scored_chunks(scored, session.disabled_source_files)
        scored = _filter_weak_source_only_evidence(query, scored)
        scored = _filter_low_content_chunks(scored)
        scored = _expand_with_neighbor_chunks(index, scored)
        scored = _expand_assessment_survey_chunks(query, index, scored)
        if not scored:
            _log.info(
                "rag retrieve: no relevant results",
                extra={
                    "fields": {
                        "query_len": len(query),
                        "latency_ms": timer.ms,
                        "min_score": _RAG_MIN_SCORE,
                    }
                },
            )
            return None

        scores = [sc.score for sc in scored]
        _log.info(
            "rag retrieve",
            extra={
                "fields": {
                    "query_len": len(query),
                    "retrieved": len(scored),
                    "top_score": round(scores[0], 4) if scores else 0,
                    "latency_ms": round(timer.ms, 1),
                }
            },
        )
        session.trace.record_rag_retrieve(
            query=query,
            top_k=_QUERY_RETRIEVAL_TOP_K,
            retrieved=len(scored),
            scores=scores,
            latency_ms=timer.ms,
            chunks=[
                {
                    "ref": EvidenceReference(sc.chunk.source, sc.chunk.index).render(),
                    "score": round(sc.score, 4),
                    "text_excerpt": _excerpt(sc.chunk.text),
                }
                for sc in scored
            ],
        )
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence build failed", exc_info=True)
        return None


def _filter_low_content_chunks(scored: list[ScoredChunk]) -> list[ScoredChunk]:
    content_chunks = [item for item in scored if not _LOW_CONTENT_CHUNK_RE.search(item.chunk.text)]
    return content_chunks or scored


def _expand_with_neighbor_chunks(
    index: ArmoryIndex,
    scored: list[ScoredChunk],
) -> list[ScoredChunk]:
    """Add nearby chunks so heading hits carry their local explanatory context."""
    if not scored:
        return scored
    by_source = {document.source: document for document in index.documents}
    expanded: list[ScoredChunk] = []
    seen: set[tuple[str, int]] = set()
    added_neighbors = 0
    for item in scored:
        key = (item.chunk.source, item.chunk.index)
        if key not in seen:
            expanded.append(item)
            seen.add(key)
        document = by_source.get(item.chunk.source)
        if document is None:
            continue
        for offset in range(1, _QUERY_NEIGHBOR_RADIUS + 1):
            for neighbor_index in (item.chunk.index - offset, item.chunk.index + offset):
                neighbor_key = (item.chunk.source, neighbor_index)
                if neighbor_key in seen or neighbor_index < 0:
                    continue
                if neighbor_index >= len(document.chunks):
                    continue
                neighbor = document.chunks[neighbor_index]
                if _LOW_CONTENT_CHUNK_RE.search(neighbor.text):
                    continue
                expanded.append(
                    ScoredChunk(
                        chunk=neighbor,
                        score=max(item.score * 0.92, _RAG_MIN_SCORE),
                    )
                )
                seen.add(neighbor_key)
                added_neighbors += 1
                if added_neighbors >= _QUERY_NEIGHBOR_LIMIT:
                    return expanded
    return expanded


def _expand_assessment_survey_chunks(
    query: str,
    index: ArmoryIndex,
    scored: list[ScoredChunk],
) -> list[ScoredChunk]:
    if not scored or not _DOCUMENT_SURVEY_QUERY_RE.search(query):
        return scored
    documents = {document.source: document for document in index.documents}
    expanded = list(scored)
    seen = {(item.chunk.source, item.chunk.index) for item in expanded}
    survey_items: list[ScoredChunk] = []
    source_order = list(dict.fromkeys(item.chunk.source for item in scored))
    for source in source_order[:2]:
        document = documents.get(source)
        if document is None:
            continue
        sample = "\n".join(chunk.text for chunk in document.chunks[:4])
        role, confidence, _reason = infer_material_role_from_text(source, sample)
        if role != "past_exam" or confidence < 0.6:
            continue
        additions = 0
        for chunk in document.chunks:
            key = (chunk.source, chunk.index)
            if key in seen or _LOW_CONTENT_CHUNK_RE.search(chunk.text):
                continue
            if not _ASSESSMENT_CHUNK_RE.search(chunk.text):
                continue
            survey_items.append(ScoredChunk(chunk=chunk, score=_RAG_MIN_SCORE))
            seen.add(key)
            additions += 1
            if additions >= 8:
                break
    if not survey_items:
        return expanded
    pivot = min(3, len(expanded))
    return [*expanded[:pivot], *survey_items, *expanded[pivot:]]


def build_turn_evidence_from_overview(session: ChatSession) -> TurnEvidence | None:
    """Build starter evidence from the beginning of available material files."""
    try:
        index = ensure_rag_index(session)
        if index is None:
            return None

        scored: list[ScoredChunk] = []
        enabled_documents = [
            document
            for document in index.documents
            if document.source not in session.disabled_source_files and document.chunks
        ]
        overview_chunks_by_document = [
            _overview_chunks_for_document(document.chunks) for document in enabled_documents
        ]
        for offset in range(_OVERVIEW_CHUNKS_PER_DOCUMENT):
            for document_chunks in overview_chunks_by_document:
                if offset >= len(document_chunks):
                    continue
                scored.append(
                    ScoredChunk(chunk=_compact_overview_chunk(document_chunks[offset]), score=1.0)
                )
                if len(scored) >= _OVERVIEW_CHUNK_LIMIT:
                    break
            if len(scored) >= _OVERVIEW_CHUNK_LIMIT:
                break

        if not scored:
            scored = [
                ScoredChunk(chunk=_compact_overview_chunk(chunk), score=1.0)
                for chunk in index.all_chunks
                if chunk.source not in session.disabled_source_files
            ][:_OVERVIEW_CHUNK_LIMIT]
        if not scored:
            return None
        evidence = build_turn_evidence(
            scored,
            max_tokens=max(adaptive_rag_budget(session), _OVERVIEW_CONTEXT_TOKEN_BUDGET),
        )
        sampled_sources = {item.source for item in evidence.items}
        return TurnEvidence(
            items=evidence.items,
            sampled_source_count=len(sampled_sources),
            total_source_count=len(enabled_documents),
        )
    except Exception:
        _log.warning("turn overview evidence build failed", exc_info=True)
        return None


def _overview_chunks_for_document(chunks: list[Chunk]) -> list[Chunk]:
    if len(chunks) <= 1:
        return chunks
    if _looks_like_front_matter(chunks[0].text):
        return chunks[1:]
    return chunks


def _compact_overview_chunk(chunk: Chunk) -> Chunk:
    text = " ".join(chunk.text.split())
    if len(text) <= _OVERVIEW_EXCERPT_CHAR_LIMIT:
        return chunk
    return replace(
        chunk,
        text=text[: _OVERVIEW_EXCERPT_CHAR_LIMIT - 17].rstrip() + "\n[... truncated]",
    )


def _looks_like_front_matter(text: str) -> bool:
    lines = [line.strip(" #\t") for line in text.splitlines() if line.strip()]
    if not lines:
        return True
    sample = "\n".join(lines[:12])
    if _FRONT_MATTER_CONTENT_RE.search(sample):
        return False
    has_metadata = bool(_FRONT_MATTER_METADATA_RE.search(sample))
    has_date = bool(_FRONT_MATTER_DATE_RE.search(sample))
    return has_metadata and has_date and len(lines) <= 12


def build_overview_context(session: ChatSession) -> str:
    """Return deterministic model-facing corpus context for overview requests."""
    try:
        index = ensure_rag_index(session)
        if index is None:
            return ""
        enabled_documents = [
            document
            for document in index.documents
            if document.source not in session.disabled_source_files and document.chunks
        ]
        if not enabled_documents:
            return ""

        role_counts: dict[str, int] = {}
        document_lines: list[str] = []
        for document in enabled_documents[:_OVERVIEW_DOCUMENT_LIMIT]:
            text = " ".join(chunk.text for chunk in document.chunks)
            role, confidence, reason = infer_material_role_from_text(document.source, text)
            role_counts[role] = role_counts.get(role, 0) + 1
            document_lines.append(
                f"- {document.source}: {role} ({confidence:.2f}; {reason}; "
                f"{len(document.chunks)} chunks)"
            )
        remaining = len(enabled_documents) - len(document_lines)
        if remaining > 0:
            document_lines.append(f"- ... {remaining} more enabled indexed document(s)")

        enabled_chunks = [chunk for document in enabled_documents for chunk in document.chunks]
        analysis = analyze_priority(enabled_chunks, limit=8)
        role_summary = ", ".join(f"{role}={count}" for role, count in sorted(role_counts.items()))
        lines = [
            "Deterministic local corpus overview from enabled indexed material:",
            f"- indexed_documents={len(enabled_documents)}",
            f"- chunks={sum(len(document.chunks) for document in enabled_documents)}",
            f"- inferred_roles={role_summary or 'none'}",
            "Document role sample:",
            *document_lines,
        ]
        if analysis.topics:
            lines.extend(
                [
                    "Topic scan from enabled indexed text:",
                    analysis.render_for_prompt(limit=8),
                ]
            )
        lines.append(
            "Use this overview only as deterministic corpus context. Cite retrieved evidence "
            "for factual claims, distinguish evidence from uncertainty, and do not infer from "
            "filenames, lecturer names, subject names, institutions, or outside knowledge."
        )
        return "\n".join(lines)
    except Exception:
        _log.warning("overview context build failed", exc_info=True)
        return ""


def _priority_scored_chunks(session: ChatSession, index: ArmoryIndex) -> list[ScoredChunk]:
    enabled_chunks = [
        chunk for chunk in index.all_chunks if chunk.source not in session.disabled_source_files
    ]
    analysis = analyze_priority(enabled_chunks, limit=12)
    scored: list[ScoredChunk] = []
    selected: set[tuple[str, int]] = set()
    topic_scores = {topic.topic: topic.score for topic in analysis.topics}

    def add(chunk: Chunk, score: float) -> None:
        key = (chunk.source, chunk.index)
        if key in selected:
            return
        selected.add(key)
        scored.append(ScoredChunk(chunk=chunk, score=score))

    for topic in analysis.topics[:8]:
        for evidence in topic.evidence[:3]:
            for chunk in enabled_chunks:
                if chunk.source != evidence.source:
                    continue
                if topic.topic in chunk.text.lower() or evidence.excerpt[:80] in chunk.text:
                    add(chunk, topic.score)
                    break
    for chunk in enabled_chunks:
        text = chunk.text.lower()
        matching_scores = [score for topic, score in topic_scores.items() if topic in text]
        if matching_scores:
            add(chunk, max(matching_scores))
        if len(scored) >= 10:
            break
    if not scored:
        return [ScoredChunk(chunk=chunk, score=1.0) for chunk in enabled_chunks[:6]]
    return scored[:10]


def build_priority_turn_evidence(session: ChatSession) -> TurnEvidence | None:
    """Build priority evidence from the deterministic whole-corpus priority analyzer."""
    try:
        index = ensure_rag_index(session)
        if index is None:
            return None
        scored = _priority_scored_chunks(session, index)
        if not scored:
            return None
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("priority evidence build failed", exc_info=True)
        return None


def build_priority_context(session: ChatSession, *, limit: int = 8) -> str:
    """Return concise model-facing priority context from all enabled indexed chunks."""
    try:
        index = ensure_rag_index(session)
        if index is None:
            return ""
        enabled_chunks = [
            chunk
            for chunk in index.all_chunks
            if chunk.source not in session.disabled_source_files
        ]
        analysis = analyze_priority(enabled_chunks, limit=12)
        if not analysis.topics:
            return ""
        lines = [
            "Deterministic local priority scan over all enabled indexed material:",
            analysis.render_for_prompt(limit=limit),
            (
                "Use this scan as the primary priority signal. Do not infer priorities from "
                "filenames, lecturer names, subject names, or outside knowledge."
            ),
        ]
        return "\n".join(lines)
    except Exception:
        _log.warning("priority context build failed", exc_info=True)
        return ""


def build_turn_evidence_from_refs(session: ChatSession, refs: list[str]) -> TurnEvidence | None:
    """Rebuild evidence from persisted source/chunk references."""
    try:
        index = ensure_rag_index(session)
        if index is None or not refs:
            return None

        by_key = {(chunk.source, chunk.index): chunk for chunk in index.all_chunks}
        scored: list[ScoredChunk] = []
        total = len(refs)
        for pos, ref in enumerate(refs):
            parsed = parse_source_ref(ref)
            if parsed is None:
                continue
            chunk = by_key.get(parsed)
            if chunk is None or chunk.source in session.disabled_source_files:
                continue
            scored.append(ScoredChunk(chunk=chunk, score=float(total - pos)))
        if not scored:
            return None
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence rebuild from refs failed", exc_info=True)
        return None


def resolve_turn_evidence(session: ChatSession, plan: StudyTurnPlan) -> TurnEvidence | None:
    """Resolve the best evidence for a study turn plan."""
    if plan.action is StudyAction.CALIBRATE:
        return build_turn_evidence_from_overview(session)
    if plan.action is StudyAction.PRIORITY:
        return build_priority_turn_evidence(session)
    if plan.use_expected_source_refs and session.study_state.expected_source_refs:
        turn_evidence = build_turn_evidence_from_refs(
            session,
            session.study_state.expected_source_refs,
        )
        if turn_evidence:
            return turn_evidence
    if plan.retrieval_query:
        if plan.action is StudyAction.PRESENT and _is_overview_query(plan.retrieval_query):
            return build_turn_evidence_from_overview(session)
        return build_turn_evidence_from_query(session, plan.retrieval_query)
    return None


__all__ = [
    "ResolvedTurnPlan",
    "adaptive_rag_budget",
    "build_overview_context",
    "build_priority_context",
    "build_priority_turn_evidence",
    "build_prompt_fn",
    "build_turn_evidence_from_overview",
    "build_turn_evidence_from_query",
    "build_turn_evidence_from_refs",
    "ensure_rag_index",
    "evidence_refs",
    "evidence_trace_coverage",
    "evidence_trace_items",
    "is_overview_query",
    "parse_source_ref",
    "query_demands_source_only_answer",
    "resolve_transform_strategy",
    "resolve_turn_evidence",
]
