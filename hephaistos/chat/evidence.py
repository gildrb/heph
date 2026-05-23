"""RAG evidence resolution for chat turns."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from html import unescape
from typing import TYPE_CHECKING

from hephaistos.chat.usage import ContextBudget
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import infer_material_role_from_text
from hephaistos.rag import (
    ArmoryIndex,
    Chunk,
    RetrievalMode,
    ScoredChunk,
    TransformStrategy,
    TurnEvidence,
    build_turn_evidence,
    load_or_build,
    retrieve,
)
from hephaistos.rag.chunker import ChunkedDocument
from hephaistos.rag.query_audit import (
    RetrievalAuditConfig,
    query_classification_payload,
    query_excerpt,
    retrieval_strategy_payload,
)
from hephaistos.rag.query_transform import PromptFn
from hephaistos.rag.retrieval_types import EvidenceReference
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaistos.study import EvidenceAssessment, LearningAction, LearningTurnPlan, assess_evidence
from hephaistos.study.overview import CANONICAL_OVERVIEW_QUERY
from hephaistos.study.priority import PriorityAnalysis, analyze_priority

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_log = get_logger("chat.evidence")
_RAG_MIN_SCORE = 0.1
_QUERY_RETRIEVAL_TOP_K = 30
_QUERY_NEIGHBOR_RADIUS = 1
_QUERY_NEIGHBOR_LIMIT = 8
_PRIORITY_TOPIC_CHUNK_LIMIT = 10
_SOURCE_ONLY_MIN_TOP_SCORE = 0.18
_OVERVIEW_CHUNK_LIMIT = 48
_OVERVIEW_CHUNKS_PER_DOCUMENT = 5
_OVERVIEW_DOCUMENT_LIMIT = 48
_OVERVIEW_EXCERPT_CHAR_LIMIT = 700
_OVERVIEW_CONTEXT_TOKEN_BUDGET = 9000
_LOW_CONTENT_CHUNK_RE = re.compile(
    r"^\s*(?:cite as:|for information about citing|downloaded on|terms of use\b|"
    r"copyright\b|http://ocw\.mit\.edu/terms)",
    re.IGNORECASE,
)
_OVERVIEW_CONTEXT_POLICY = (
    "Use this overview only as deterministic corpus context. Cite retrieved evidence "
    "for factual claims, distinguish evidence from uncertainty, and do not infer from "
    "filenames, lecturer names, subject names, institutions, or outside knowledge."
)


@dataclass(frozen=True, slots=True)
class ResolvedTurnPlan:
    learning_plan: LearningTurnPlan | None = None
    turn_evidence: TurnEvidence | None = None
    evidence_assessment: EvidenceAssessment | None = None
    priority_context: str = ""
    retrieval_latency_ms: float | None = None


@dataclass(frozen=True, slots=True)
class _EnabledCorpus:
    documents: list[ChunkedDocument]
    chunks: list[Chunk]


@dataclass(frozen=True, slots=True)
class _QueryRetrievalResult:
    scored: list[ScoredChunk]


def evidence_refs(turn_evidence: TurnEvidence | None) -> list[str]:
    if not turn_evidence:
        return []
    return [
        EvidenceReference(item.source, item.chunk_index).render() for item in turn_evidence.items
    ]


def _enabled_corpus(index: ArmoryIndex, disabled_sources: set[str]) -> _EnabledCorpus:
    documents = _enabled_documents(index, disabled_sources)
    if not documents:
        return _EnabledCorpus(
            documents=[],
            chunks=_enabled_chunks(index.all_chunks, disabled_sources),
        )
    return _EnabledCorpus(documents=documents, chunks=_document_chunks(documents))


def _enabled_documents(index: ArmoryIndex, disabled_sources: set[str]) -> list[ChunkedDocument]:
    return [
        document
        for document in index.documents
        if document.source not in disabled_sources and document.chunks
    ]


def _enabled_chunks(chunks: Sequence[Chunk], disabled_sources: set[str]) -> list[Chunk]:
    return [chunk for chunk in chunks if chunk.source not in disabled_sources]


def _document_chunks(documents: Sequence[ChunkedDocument]) -> list[Chunk]:
    return [chunk for document in documents for chunk in document.chunks]


def _excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(unescape(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def evidence_trace_items(turn_evidence: TurnEvidence | None) -> list[dict[str, object]]:
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


def assess_turn_evidence(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> EvidenceAssessment:
    source_only = _plan_needs_source_only_answer(plan)
    assessment = assess_evidence(
        tuple(evidence_refs(turn_evidence)),
        source_only=source_only,
        missing_hint=_missing_evidence_hint(plan, source_only=source_only),
    )
    return _adjust_evidence_assessment(plan, assessment)


def _plan_needs_source_only_answer(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.SOURCE_QA


def _missing_evidence_hint(plan: LearningTurnPlan, *, source_only: bool) -> str:
    if plan.action is LearningAction.PRIORITY:
        return "recurring topics, exam weighting, or prerequisite evidence"
    if source_only:
        return "source span that directly answers the source-only question"
    if plan.action is LearningAction.ASSESS:
        return "rubric, mark scheme, or source span for grounded assessment"
    return "source span that supports the requested response"


def _adjust_evidence_assessment(
    plan: LearningTurnPlan,
    assessment: EvidenceAssessment,
) -> EvidenceAssessment:
    if assessment.sufficient or assessment.recommended_action != "retrieve_more":
        return assessment
    if _should_ask_clarifying_query(plan, assessment):
        return replace(assessment, recommended_action="ask_clarifying_question")
    return assessment


def _should_ask_clarifying_query(
    plan: LearningTurnPlan,
    assessment: EvidenceAssessment,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.PRIORITY}:
        return False
    if not _needs_clarifying_query(plan.retrieval_query or ""):
        return False
    return plan.action is not LearningAction.PRESENT or bool(assessment.supporting_refs)


def evidence_assessment_trace(
    assessment: EvidenceAssessment | None,
) -> dict[str, object]:
    if assessment is None:
        return {}
    return {
        "sufficient": assessment.sufficient,
        "confidence": round(assessment.confidence, 3),
        "supporting_refs": list(assessment.supporting_refs),
        "missing_information": list(assessment.missing_information),
        "conflicts": list(assessment.conflicts),
        "source_diversity_score": round(assessment.source_diversity_score, 3),
        "recommended_action": assessment.recommended_action,
    }


def retrieval_audit_metadata(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> dict[str, object]:
    """Return the JSONL-compatible retrieval audit contract for a chat turn."""
    query = plan.retrieval_query or ""
    if not query or plan.action is LearningAction.CALIBRATE:
        return {}
    config = _retrieval_audit_config(session)
    assessment = evidence_assessment_trace(resolved.evidence_assessment)
    return {
        "query_classification": query_classification_payload(query, config),
        "retrieval_trace": _retrieval_trace(query, config, resolved, assessment),
    }


def _retrieval_trace(
    query: str,
    config: RetrievalAuditConfig,
    resolved: ResolvedTurnPlan,
    assessment: Mapping[str, object],
) -> dict[str, object]:
    coverage = evidence_trace_coverage(resolved.turn_evidence)
    trace = {
        "pass": 1,
        "query_excerpt": query_excerpt(query),
        "query_class": query_classification_payload(query, config)["query_class"],
        "retrieval_strategy": retrieval_strategy_payload(config),
        "top_k": config.top_k,
        "candidate_budget": config.candidate_budget,
        "retrieved_count": coverage["evidence_blocks"],
        "returned_count": coverage["evidence_blocks"],
        "top_score": _top_evidence_score(resolved.turn_evidence),
        "sufficiency": _audit_status(assessment, "sufficient"),
        "stop_reason": _audit_status(assessment, "sufficient_evidence"),
        "items": evidence_trace_items(resolved.turn_evidence),
    }
    if resolved.retrieval_latency_ms is not None:
        trace["latency_ms"] = round(resolved.retrieval_latency_ms, 1)
    return trace


def _top_evidence_score(turn_evidence: TurnEvidence | None) -> float | None:
    if turn_evidence is None or not turn_evidence.items:
        return None
    return round(turn_evidence.items[0].score, 4)


def _retrieval_audit_config(session: ChatSession) -> RetrievalAuditConfig:
    strategy = resolve_transform_strategy(session.config)
    return RetrievalAuditConfig(
        retrieval_mode=RetrievalMode.AUTO.value,
        transform_strategy=strategy.value,
        top_k=_QUERY_RETRIEVAL_TOP_K,
        candidate_multiplier=1,
        repair_max_passes=1,
        rerank_requested=True,
    )


def _audit_status(assessment: Mapping[str, object], sufficient: str) -> str:
    if assessment.get("sufficient") is True:
        return sufficient
    recommended = assessment.get("recommended_action")
    return recommended if isinstance(recommended, str) and recommended else "no_evidence"


def parse_source_ref(ref: str) -> tuple[str, int] | None:
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
    for flag, strategy in _FLAG_STRATEGY_MAP.items():
        if config.is_feature_enabled(flag):
            return strategy
    return TransformStrategy.EXPANSION


def build_prompt_fn(config: ChatConfig) -> PromptFn:
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


def _needs_clarifying_query(query: str) -> bool:
    normalized = " ".join(query.split())
    return bool(normalized) and len(normalized) <= 18


def _prepare_query_scored_chunks(
    query: str,
    index: ArmoryIndex,
    scored: list[ScoredChunk],
    disabled_sources: set[str],
) -> list[ScoredChunk]:
    scored = _enabled_scored_chunks(scored, disabled_sources)
    scored = _filter_low_content_chunks(scored)
    return _expand_with_neighbor_chunks(index, scored)


def adaptive_rag_budget(session: ChatSession) -> int:
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    api_msgs = session.conversation.to_api_messages()
    remaining = budget.tokens_remaining(api_msgs)
    return min(session.config.rag_context_budget, max(200, int(remaining * 0.3)))


def is_overview_query(query: str) -> bool:
    return query.strip().casefold() == CANONICAL_OVERVIEW_QUERY


def build_turn_evidence_from_query(session: ChatSession, query: str) -> TurnEvidence | None:
    if session.armory_path is None:
        return None
    try:
        timer = Timer()
        index = ensure_rag_index(session)
        if index is None:
            return None

        with timer:
            result = _retrieve_query_scored_chunks(session, query, index)
        if not result.scored:
            _log_empty_query_retrieval(query, timer.ms)
            return None

        _record_query_retrieval(session, query, result, latency_ms=timer.ms)
        return build_turn_evidence(result.scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence build failed", exc_info=True)
        return None


def _retrieve_query_scored_chunks(
    session: ChatSession,
    query: str,
    index: ArmoryIndex,
) -> _QueryRetrievalResult:
    strategy = resolve_transform_strategy(session.config)
    prompt_fn = _query_transform_prompt_fn(session, strategy)
    scored = retrieve(
        query,
        index,
        top_k=_QUERY_RETRIEVAL_TOP_K,
        min_score=_RAG_MIN_SCORE,
        transform_strategy=strategy,
        prompt_fn=prompt_fn,
    )
    scored = _prepare_query_scored_chunks(
        query,
        index,
        scored,
        session.disabled_source_files,
    )
    return _QueryRetrievalResult(scored=scored)


def _query_transform_prompt_fn(
    session: ChatSession,
    strategy: TransformStrategy,
) -> PromptFn | None:
    if strategy in (TransformStrategy.HYDE, TransformStrategy.MULTI_QUERY):
        return build_prompt_fn(session.config)
    return None


def _log_empty_query_retrieval(query: str, latency_ms: float) -> None:
    _log.info(
        "rag retrieve: no relevant results",
        extra={
            "fields": {
                "query_len": len(query),
                "latency_ms": latency_ms,
                "min_score": _RAG_MIN_SCORE,
            }
        },
    )


def _record_query_retrieval(
    session: ChatSession,
    query: str,
    result: _QueryRetrievalResult,
    *,
    latency_ms: float,
) -> None:
    scores = [item.score for item in result.scored]
    _log_query_retrieval(query, result.scored, scores, latency_ms=latency_ms)
    session.trace.record_rag_retrieve(
        query=query,
        top_k=_QUERY_RETRIEVAL_TOP_K,
        retrieved=len(result.scored),
        scores=scores,
        latency_ms=latency_ms,
        chunks=_trace_query_chunks(result.scored),
    )


def _log_query_retrieval(
    query: str,
    scored: Sequence[ScoredChunk],
    scores: Sequence[float],
    *,
    latency_ms: float,
) -> None:
    _log.info(
        "rag retrieve",
        extra={
            "fields": {
                "query_len": len(query),
                "retrieved": len(scored),
                "top_score": round(scores[0], 4) if scores else 0,
                "latency_ms": round(latency_ms, 1),
            }
        },
    )


def _trace_query_chunks(scored: Sequence[ScoredChunk]) -> list[Mapping[str, object]]:
    return [
        {
            "ref": EvidenceReference(item.chunk.source, item.chunk.index).render(),
            "score": round(item.score, 4),
            "text_excerpt": _excerpt(item.chunk.text),
        }
        for item in scored
    ]


def _filter_low_content_chunks(scored: list[ScoredChunk]) -> list[ScoredChunk]:
    content_chunks = [item for item in scored if not _LOW_CONTENT_CHUNK_RE.search(item.chunk.text)]
    return content_chunks or scored


def _expand_with_neighbor_chunks(
    index: ArmoryIndex,
    scored: list[ScoredChunk],
) -> list[ScoredChunk]:
    if not scored:
        return scored
    documents = {document.source: document for document in index.documents}
    expanded: list[ScoredChunk] = []
    seen: set[tuple[str, int]] = set()
    added_neighbors = 0
    for item in scored:
        _append_scored_item(expanded, seen, item)
        added_neighbors += _append_neighbor_items(
            expanded,
            seen,
            documents.get(item.chunk.source),
            item,
            remaining=_QUERY_NEIGHBOR_LIMIT - added_neighbors,
        )
        if added_neighbors >= _QUERY_NEIGHBOR_LIMIT:
            return expanded
    return expanded


def _append_scored_item(
    scored: list[ScoredChunk],
    seen: set[tuple[str, int]],
    item: ScoredChunk,
) -> bool:
    key = (item.chunk.source, item.chunk.index)
    if key in seen:
        return False
    scored.append(item)
    seen.add(key)
    return True


def _append_neighbor_items(
    scored: list[ScoredChunk],
    seen: set[tuple[str, int]],
    document: ChunkedDocument | None,
    item: ScoredChunk,
    *,
    remaining: int,
) -> int:
    if document is None or remaining <= 0:
        return 0
    added = 0
    for neighbor in _neighbor_chunks(document, item.chunk.index):
        added += _append_neighbor_item(scored, seen, neighbor, item.score)
        if added >= remaining:
            return added
    return added


def _append_neighbor_item(
    scored: list[ScoredChunk],
    seen: set[tuple[str, int]],
    neighbor: Chunk,
    score: float,
) -> int:
    return int(_append_scored_item(scored, seen, _neighbor_scored_chunk(neighbor, score)))


def _neighbor_chunks(document: ChunkedDocument, chunk_index: int) -> list[Chunk]:
    return [
        neighbor
        for neighbor_index in _neighbor_indexes(document, chunk_index)
        if not _LOW_CONTENT_CHUNK_RE.search((neighbor := document.chunks[neighbor_index]).text)
    ]


def _neighbor_indexes(document: ChunkedDocument, chunk_index: int) -> tuple[int, ...]:
    indexes: list[int] = []
    for offset in range(1, _QUERY_NEIGHBOR_RADIUS + 1):
        indexes.extend((chunk_index - offset, chunk_index + offset))
    return tuple(index for index in indexes if 0 <= index < len(document.chunks))


def _neighbor_scored_chunk(chunk: Chunk, base_score: float) -> ScoredChunk:
    return ScoredChunk(chunk=chunk, score=max(base_score * 0.92, _RAG_MIN_SCORE))


def build_turn_evidence_from_overview(session: ChatSession) -> TurnEvidence | None:
    try:
        index = ensure_rag_index(session)
        if index is None:
            return None

        corpus = _enabled_corpus(index, session.disabled_source_files)
        scored = _overview_scored_chunks(corpus)
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
            total_source_count=len(corpus.documents),
        )
    except Exception:
        _log.warning("turn overview evidence build failed", exc_info=True)
        return None


def _overview_scored_chunks(corpus: _EnabledCorpus) -> list[ScoredChunk]:
    scored = _round_robin_overview_chunks(corpus.documents)
    if scored:
        return scored
    return _fallback_overview_chunks(corpus.chunks)


def _round_robin_overview_chunks(documents: Sequence[ChunkedDocument]) -> list[ScoredChunk]:
    scored: list[ScoredChunk] = []
    chunks_by_document = [_overview_document_chunks(document) for document in documents]
    for offset in range(_OVERVIEW_CHUNKS_PER_DOCUMENT):
        if _append_overview_offset(scored, chunks_by_document, offset):
            return scored
    return scored


def _append_overview_offset(
    scored: list[ScoredChunk],
    chunks_by_document: Sequence[Sequence[Chunk]],
    offset: int,
) -> bool:
    for document_chunks in chunks_by_document:
        if offset < len(document_chunks):
            scored.append(_overview_scored_chunk(document_chunks[offset]))
        if len(scored) >= _OVERVIEW_CHUNK_LIMIT:
            return True
    return False


def _overview_document_chunks(document: ChunkedDocument) -> tuple[Chunk, ...]:
    return tuple(document.chunks)


def _fallback_overview_chunks(chunks: Sequence[Chunk]) -> list[ScoredChunk]:
    return [_overview_scored_chunk(chunk) for chunk in chunks[:_OVERVIEW_CHUNK_LIMIT]]


def _overview_scored_chunk(chunk: Chunk) -> ScoredChunk:
    return ScoredChunk(chunk=_compact_overview_chunk(chunk), score=1.0)


def _compact_overview_chunk(chunk: Chunk) -> Chunk:
    text = " ".join(chunk.text.split())
    if len(text) <= _OVERVIEW_EXCERPT_CHAR_LIMIT:
        return chunk
    return replace(
        chunk,
        text=text[: _OVERVIEW_EXCERPT_CHAR_LIMIT - 17].rstrip() + "\n[... truncated]",
    )


def build_overview_context(session: ChatSession) -> str:
    try:
        index = ensure_rag_index(session)
        if index is None:
            return ""
        corpus = _enabled_corpus(index, session.disabled_source_files)
        if not corpus.documents:
            return ""

        role_counts, document_lines = _overview_document_lines(corpus.documents)
        analysis = analyze_priority(corpus.chunks, limit=8)
        return _render_overview_context(corpus, role_counts, document_lines, analysis)
    except Exception:
        _log.warning("overview context build failed", exc_info=True)
        return ""


def _overview_document_lines(
    documents: Sequence[ChunkedDocument],
) -> tuple[dict[str, int], list[str]]:
    role_counts: dict[str, int] = {}
    document_lines = [
        _overview_document_line(document, role_counts)
        for document in documents[:_OVERVIEW_DOCUMENT_LIMIT]
    ]
    remaining = len(documents) - len(document_lines)
    if remaining > 0:
        document_lines.append(f"- ... {remaining} more enabled indexed document(s)")
    return role_counts, document_lines


def _overview_document_line(
    document: ChunkedDocument,
    role_counts: dict[str, int],
) -> str:
    text = " ".join(chunk.text for chunk in document.chunks)
    role, confidence, reason = infer_material_role_from_text(document.source, text)
    role_counts[role] = role_counts.get(role, 0) + 1
    return (
        f"- {document.source}: {role} ({confidence:.2f}; {reason}; {len(document.chunks)} chunks)"
    )


def _render_overview_context(
    corpus: _EnabledCorpus,
    role_counts: Mapping[str, int],
    document_lines: Sequence[str],
    analysis: PriorityAnalysis,
) -> str:
    lines = _overview_header_lines(corpus, role_counts, document_lines)
    if analysis.topics:
        lines.extend(
            (
                "Topic scan from enabled indexed text:",
                analysis.render_for_prompt(limit=8),
            )
        )
    lines.append(_OVERVIEW_CONTEXT_POLICY)
    return "\n".join(lines)


def _overview_header_lines(
    corpus: _EnabledCorpus,
    role_counts: Mapping[str, int],
    document_lines: Sequence[str],
) -> list[str]:
    return [
        "Deterministic local corpus overview from enabled indexed material:",
        f"- indexed_documents={len(corpus.documents)}",
        f"- chunks={len(corpus.chunks)}",
        f"- inferred_roles={_overview_role_summary(role_counts)}",
        "Document role sample:",
        *document_lines,
    ]


def _overview_role_summary(role_counts: Mapping[str, int]) -> str:
    if not role_counts:
        return "none"
    return ", ".join(f"{role}={count}" for role, count in sorted(role_counts.items()))


def _priority_scored_chunks(session: ChatSession, index: ArmoryIndex) -> list[ScoredChunk]:
    corpus = _enabled_corpus(index, session.disabled_source_files)
    analysis = analyze_priority(corpus.chunks, limit=12)
    scored = _priority_evidence_chunks(corpus.chunks, analysis)
    scored = _fill_priority_topic_chunks(corpus.chunks, analysis, scored)
    return scored[:10] or [ScoredChunk(chunk=chunk, score=1.0) for chunk in corpus.chunks[:6]]


def _priority_evidence_chunks(
    chunks: Sequence[Chunk],
    analysis: PriorityAnalysis,
) -> list[ScoredChunk]:
    selected: set[tuple[str, int]] = set()
    scored: list[ScoredChunk] = []
    for topic in analysis.topics[:8]:
        for evidence in topic.evidence[:3]:
            chunk = _priority_evidence_chunk(
                chunks,
                topic.topic,
                evidence.source,
                evidence.excerpt,
            )
            if chunk is not None:
                _append_unique_scored_chunk(scored, selected, chunk, topic.score)
    return scored


def _priority_evidence_chunk(
    chunks: Sequence[Chunk],
    topic: str,
    source: str,
    excerpt: str,
) -> Chunk | None:
    for chunk in chunks:
        if chunk.source != source:
            continue
        if topic in chunk.text.lower() or excerpt[:80] in chunk.text:
            return chunk
    return None


def _fill_priority_topic_chunks(
    chunks: Sequence[Chunk],
    analysis: PriorityAnalysis,
    scored: list[ScoredChunk],
) -> list[ScoredChunk]:
    selected = {(item.chunk.source, item.chunk.index) for item in scored}
    topic_scores = {topic.topic: topic.score for topic in analysis.topics}
    for chunk, score in _priority_topic_chunk_scores(chunks, topic_scores):
        _append_unique_scored_chunk(scored, selected, chunk, score)
        if _priority_topic_chunk_limit_reached(scored):
            break
    return scored


def _priority_topic_chunk_scores(
    chunks: Sequence[Chunk],
    topic_scores: Mapping[str, float],
) -> Iterator[tuple[Chunk, float]]:
    for chunk in chunks:
        if score := _priority_topic_score(chunk, topic_scores):
            yield chunk, score


def _priority_topic_chunk_limit_reached(scored: Sequence[ScoredChunk]) -> bool:
    return len(scored) >= _PRIORITY_TOPIC_CHUNK_LIMIT


def _priority_topic_score(chunk: Chunk, topic_scores: Mapping[str, float]) -> float | None:
    text = chunk.text.lower()
    scores = [score for topic, score in topic_scores.items() if topic in text]
    if not scores:
        return None
    return max(scores)


def _append_unique_scored_chunk(
    scored: list[ScoredChunk],
    selected: set[tuple[str, int]],
    chunk: Chunk,
    score: float,
) -> None:
    key = (chunk.source, chunk.index)
    if key in selected:
        return
    selected.add(key)
    scored.append(ScoredChunk(chunk=chunk, score=score))


def build_priority_turn_evidence(session: ChatSession) -> TurnEvidence | None:
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
    try:
        index = ensure_rag_index(session)
        if index is None:
            return ""
        corpus = _enabled_corpus(index, session.disabled_source_files)
        analysis = analyze_priority(corpus.chunks, limit=12)
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
    try:
        index = ensure_rag_index(session)
        if index is None or not refs:
            return None

        scored = _scored_chunks_from_refs(
            index,
            refs,
            disabled_sources=session.disabled_source_files,
        )
        if not scored:
            return None
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence rebuild from refs failed", exc_info=True)
        return None


def _scored_chunks_from_refs(
    index: ArmoryIndex,
    refs: Sequence[str],
    *,
    disabled_sources: set[str],
) -> list[ScoredChunk]:
    by_key = {(chunk.source, chunk.index): chunk for chunk in index.all_chunks}
    total = len(refs)
    return [
        ScoredChunk(chunk=chunk, score=float(total - pos))
        for pos, ref in enumerate(refs)
        if (chunk := _chunk_from_ref(by_key, ref, disabled_sources=disabled_sources)) is not None
    ]


def _chunk_from_ref(
    chunks_by_key: Mapping[tuple[str, int], Chunk],
    ref: str,
    *,
    disabled_sources: set[str],
) -> Chunk | None:
    parsed = parse_source_ref(ref)
    if parsed is None:
        return None
    chunk = chunks_by_key.get(parsed)
    if chunk is None or chunk.source in disabled_sources:
        return None
    return chunk


def resolve_turn_evidence(session: ChatSession, plan: LearningTurnPlan) -> TurnEvidence | None:
    if plan.action is LearningAction.CALIBRATE:
        return _calibration_turn_evidence(session, plan)
    if plan.action is LearningAction.PRIORITY:
        return build_priority_turn_evidence(session)
    if turn_evidence := _expected_source_ref_evidence(session, plan):
        return turn_evidence
    if plan.retrieval_query:
        return _retrieval_query_evidence(session, plan)
    return None


def _calibration_turn_evidence(
    session: ChatSession,
    plan: LearningTurnPlan,
) -> TurnEvidence | None:
    if plan.retrieval_query:
        return build_turn_evidence_from_query(session, plan.retrieval_query) or (
            build_turn_evidence_from_overview(session)
        )
    return build_turn_evidence_from_overview(session)


def _expected_source_ref_evidence(
    session: ChatSession,
    plan: LearningTurnPlan,
) -> TurnEvidence | None:
    if not plan.use_expected_source_refs or not session.learning_state.expected_source_refs:
        return None
    return build_turn_evidence_from_refs(session, session.learning_state.expected_source_refs)


def _retrieval_query_evidence(session: ChatSession, plan: LearningTurnPlan) -> TurnEvidence | None:
    if plan.retrieval_query is None:
        return None
    if plan.action is LearningAction.PRESENT and is_overview_query(plan.retrieval_query):
        return build_turn_evidence_from_overview(session)
    return build_turn_evidence_from_query(session, plan.retrieval_query)


__all__ = [
    "ResolvedTurnPlan",
    "adaptive_rag_budget",
    "assess_turn_evidence",
    "build_overview_context",
    "build_priority_context",
    "build_priority_turn_evidence",
    "build_prompt_fn",
    "build_turn_evidence_from_overview",
    "build_turn_evidence_from_query",
    "build_turn_evidence_from_refs",
    "ensure_rag_index",
    "evidence_assessment_trace",
    "evidence_refs",
    "evidence_trace_coverage",
    "evidence_trace_items",
    "is_overview_query",
    "parse_source_ref",
    "resolve_transform_strategy",
    "resolve_turn_evidence",
    "retrieval_audit_metadata",
]
