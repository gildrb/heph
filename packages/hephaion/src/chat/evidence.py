"""RAG evidence resolution for chat turns."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.logging import Timer, get_logger
from ai.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from rag import (
    ArmoryIndex,
    Chunk,
    EvidenceChunk,
    RetrievalMode,
    ScoredChunk,
    TransformStrategy,
    TurnEvidence,
    build_turn_evidence,
    load_or_build,
    retrieve,
)
from rag.chunker import ChunkedDocument
from rag.query_audit import (
    RetrievalAuditConfig,
    query_classification_payload,
    query_excerpt,
    retrieval_strategy_payload,
)
from rag.query_transform import PromptFn
from rag.retrieval_types import EvidenceReference
from study import EvidenceAssessment, LearningAction, LearningTurnPlan
from study.priority import PriorityAnalysis, analyze_priority

from chat.evidence_assessment import (
    _DIRECT_SUPPORT_MIN_MATCHES,
    _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE,
    _direct_support_coverage_score,
    _direct_support_item_score,
    _direct_support_terms,
    _source_answer_query,
    assess_turn_evidence,
    evidence_assessment_trace,
)
from chat.evidence_format import evidence_refs
from chat.evidence_format import excerpt as _excerpt
from chat.evidence_overview import (
    OVERVIEW_CITABLE_CHUNK_LIMIT as _OVERVIEW_CITABLE_CHUNK_LIMIT,
)
from chat.evidence_overview import (
    OVERVIEW_CONTEXT_TOKEN_BUDGET as _OVERVIEW_CONTEXT_TOKEN_BUDGET,
)
from chat.evidence_overview import (
    overview_scored_chunks as _overview_scored_chunks,
)
from chat.evidence_text import (
    chunk_is_low_content as _chunk_is_low_content,
)
from chat.evidence_text import (
    filter_low_content_chunks as _filter_low_content_chunks,
)
from chat.turn_contract import (
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from chat.usage import ContextBudget

if TYPE_CHECKING:
    from chat.session import ChatSession

_log = get_logger("chat.evidence")
_RAG_MIN_SCORE = 0.1
_QUERY_RETRIEVAL_TOP_K = 30
_QUERY_NEIGHBOR_RADIUS = 1
_QUERY_NEIGHBOR_LIMIT = 8
_PRIORITY_TOPIC_CHUNK_LIMIT = 10
_SOURCE_ONLY_MIN_TOP_SCORE = 0.18


@dataclass(frozen=True, slots=True)
class ResolvedTurnPlan:
    learning_plan: LearningTurnPlan | None = None
    turn_evidence: TurnEvidence | None = None
    evidence_assessment: EvidenceAssessment | None = None
    turn_contract: TurnContract | None = None
    priority_context: str = ""
    retrieval_latency_ms: float | None = None


@dataclass(frozen=True, slots=True)
class _EnabledCorpus:
    documents: list[ChunkedDocument]
    chunks: list[Chunk]


@dataclass(frozen=True, slots=True)
class _QueryRetrievalResult:
    scored: list[ScoredChunk]


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
        if not _chunk_is_low_content((neighbor := document.chunks[neighbor_index]).text)
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
        scored = _overview_scored_chunks(corpus.documents, corpus.chunks)
        if not scored:
            return None
        evidence = build_turn_evidence(
            scored[:_OVERVIEW_CITABLE_CHUNK_LIMIT],
            max_tokens=max(adaptive_rag_budget(session), _OVERVIEW_CONTEXT_TOKEN_BUDGET),
        )
        sampled_sources = {item.chunk.source for item in scored}
        return TurnEvidence(
            items=evidence.items,
            sampled_source_count=len(sampled_sources),
            total_source_count=len(corpus.documents),
        )
    except Exception:
        _log.warning("turn overview evidence build failed", exc_info=True)
        return None


def _priority_scored_chunks(session: ChatSession, index: ArmoryIndex) -> list[ScoredChunk]:
    corpus = _enabled_corpus(index, session.disabled_source_files)
    analysis = analyze_priority(corpus.chunks, limit=12)
    scored = _priority_evidence_chunks(corpus.chunks, analysis)
    scored = _fill_priority_topic_chunks(corpus.chunks, analysis, scored)
    scored = _filter_low_content_chunks(scored)
    fallback = _filter_low_content_chunks(
        [ScoredChunk(chunk=chunk, score=1.0) for chunk in corpus.chunks[:6]]
    )
    return scored[:10] or fallback


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
                "source labels, cover-page metadata, or outside knowledge."
            ),
        ]
        return "\n".join(lines)
    except Exception:
        _log.warning("priority context build failed", exc_info=True)
        return ""


def build_turn_evidence_from_refs(
    session: ChatSession,
    refs: list[str],
    *,
    max_tokens: int | None = None,
) -> TurnEvidence | None:
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
        return build_turn_evidence(scored, max_tokens=max_tokens or adaptive_rag_budget(session))
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
    scored = [
        ScoredChunk(chunk=chunk, score=float(total - pos))
        for pos, ref in enumerate(refs)
        if (chunk := _chunk_from_ref(by_key, ref, disabled_sources=disabled_sources)) is not None
    ]
    return _filter_low_content_chunks(scored)


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
    if expanded_evidence := _expanded_prior_query_evidence(session, plan):
        return expanded_evidence
    if turn_evidence := _expected_source_ref_evidence(session, plan):
        return turn_evidence
    if _material_overview_plan(plan):
        return _retrieval_query_evidence(session, plan)
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
    if plan.evidence_refs and plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        return build_turn_evidence_from_refs(session, list(plan.evidence_refs))
    if not plan.use_expected_source_refs or not session.learning_state.expected_source_refs:
        return None
    return build_turn_evidence_from_refs(session, session.learning_state.expected_source_refs)


def _expanded_prior_query_evidence(
    session: ChatSession,
    plan: LearningTurnPlan,
) -> TurnEvidence | None:
    if (
        plan.retrieval_strategy != RETRIEVAL_STRATEGY_EXPAND_PRIOR
        or not plan.evidence_refs
        or not plan.retrieval_query
    ):
        return None
    try:
        timer = Timer()
        index = ensure_rag_index(session)
        if index is None:
            return None

        if _material_overview_plan(plan):
            return build_turn_evidence_from_refs(
                session,
                list(plan.evidence_refs),
                max_tokens=max(adaptive_rag_budget(session), _OVERVIEW_CONTEXT_TOKEN_BUDGET),
            ) or build_turn_evidence_from_overview(session)

        prior_scored = _scored_chunks_from_refs(
            index,
            plan.evidence_refs,
            disabled_sources=session.disabled_source_files,
        )
        with timer:
            query_result = _retrieve_query_scored_chunks(session, plan.retrieval_query, index)
        if query_result.scored:
            _record_query_retrieval(
                session,
                plan.retrieval_query,
                query_result,
                latency_ms=timer.ms,
            )
        elif not prior_scored:
            _log_empty_query_retrieval(plan.retrieval_query, timer.ms)
            return None
        query_scored = _source_qa_relevant_query_scored(plan, query_result.scored)
        scored = _merge_prior_and_query_scored_chunks(prior_scored, query_scored)
        if not scored:
            return None
        return _build_expanded_turn_evidence(
            scored,
            prior_refs=plan.evidence_refs,
            max_tokens=adaptive_rag_budget(session),
        )
    except Exception:
        _log.warning("expanded prior evidence build failed", exc_info=True)
        return None


def _source_qa_relevant_query_scored(
    plan: LearningTurnPlan,
    scored: Sequence[ScoredChunk],
) -> Sequence[ScoredChunk]:
    if plan.action is not LearningAction.SOURCE_QA or not plan.retrieval_query:
        return scored
    query_terms = _direct_support_terms(_source_answer_query(plan))
    if len(query_terms) < _DIRECT_SUPPORT_MIN_MATCHES:
        return scored
    min_matches = (
        1 if len(query_terms) <= _DIRECT_SUPPORT_MIN_MATCHES else _DIRECT_SUPPORT_MIN_MATCHES
    )
    relevant = [
        item
        for item in scored
        if _scored_chunk_direct_support_score(query_terms, item, min_matches=min_matches)
        >= _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE
    ]
    return tuple(relevant)


def _scored_chunk_direct_support_score(
    query_terms: tuple[str, ...],
    item: ScoredChunk,
    *,
    min_matches: int,
) -> float:
    evidence_item = EvidenceChunk(
        evidence_id="E0",
        chunk=item.chunk,
        score=item.score,
        content=item.chunk.text,
    )
    return _direct_support_item_score(query_terms, evidence_item, min_matches=min_matches)


def _build_expanded_turn_evidence(
    scored: Sequence[ScoredChunk],
    *,
    prior_refs: Sequence[str],
    max_tokens: int,
) -> TurnEvidence:
    evidence = build_turn_evidence(list(scored), max_tokens=max_tokens)
    prior_id_by_ref = {
        ref: f"E{index}"
        for index, ref in enumerate(prior_refs, start=1)
        if parse_source_ref(ref) is not None
    }
    if not prior_id_by_ref:
        return evidence
    return _remap_prior_evidence_ids(evidence, prior_id_by_ref)


def _remap_prior_evidence_ids(
    evidence: TurnEvidence,
    prior_id_by_ref: Mapping[str, str],
) -> TurnEvidence:
    used_ids = set(prior_id_by_ref.values())
    next_id = _next_evidence_id(used_ids)
    remapped_items: list[EvidenceChunk] = []
    for item in evidence.items:
        ref = EvidenceReference(item.source, item.chunk_index).render()
        evidence_id = prior_id_by_ref.get(ref)
        if evidence_id is None:
            evidence_id = f"E{next_id}"
            next_id += 1
            while evidence_id in used_ids:
                evidence_id = f"E{next_id}"
                next_id += 1
        used_ids.add(evidence_id)
        remapped_items.append(
            EvidenceChunk(
                evidence_id=evidence_id,
                chunk=item.chunk,
                score=item.score,
                content=item.content,
            )
        )
    return TurnEvidence(
        items=tuple(remapped_items),
        sampled_source_count=evidence.sampled_source_count,
        total_source_count=evidence.total_source_count,
    )


def _next_evidence_id(used_ids: set[str]) -> int:
    numeric_ids = [
        int(evidence_id[1:])
        for evidence_id in used_ids
        if evidence_id.startswith("E") and evidence_id[1:].isdigit()
    ]
    return max(numeric_ids, default=0) + 1


def _merge_prior_and_query_scored_chunks(
    prior_scored: Sequence[ScoredChunk],
    query_scored: Sequence[ScoredChunk],
) -> list[ScoredChunk]:
    merged: list[ScoredChunk] = []
    seen: set[tuple[str, int]] = set()
    for item in (*query_scored, *prior_scored):
        _append_scored_item(merged, seen, item)
    return merged


def _retrieval_query_evidence(session: ChatSession, plan: LearningTurnPlan) -> TurnEvidence | None:
    if _material_overview_plan(plan):
        if plan.evidence_refs:
            return build_turn_evidence_from_refs(
                session,
                list(plan.evidence_refs),
                max_tokens=max(adaptive_rag_budget(session), _OVERVIEW_CONTEXT_TOKEN_BUDGET),
            ) or build_turn_evidence_from_overview(session)
        return build_turn_evidence_from_overview(session)
    if plan.retrieval_query is None:
        return None
    if plan.action is LearningAction.PRESENT and (
        plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    ):
        return build_turn_evidence_from_query(session, plan.retrieval_query) or (
            build_turn_evidence_from_overview(session)
        )
    query_evidence = build_turn_evidence_from_query(session, plan.retrieval_query)
    if _material_overview_plan(plan) and not _query_evidence_supports_request(
        plan.retrieval_query,
        query_evidence,
    ):
        return build_turn_evidence_from_overview(session)
    return query_evidence


def _material_overview_plan(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.PRESENT and plan.uses_overview_sampling


def _query_evidence_supports_request(
    query: str,
    evidence: TurnEvidence | None,
) -> bool:
    if evidence is None or not evidence.items:
        return False
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return False
    return _direct_support_coverage_score(query, evidence) >= _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE


__all__ = [
    "ResolvedTurnPlan",
    "adaptive_rag_budget",
    "assess_turn_evidence",
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
    "parse_source_ref",
    "resolve_transform_strategy",
    "resolve_turn_evidence",
    "retrieval_audit_metadata",
]
