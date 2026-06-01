"""RAG evidence resolution for chat turns."""

from __future__ import annotations

import difflib
import re
import unicodedata
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from html import unescape
from typing import TYPE_CHECKING

from hephaion.chat.turn_contract import (
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from hephaion.chat.usage import ContextBudget
from hephaion.logging import Timer, get_logger
from hephaion.rag import (
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
from hephaion.rag.chunker import ChunkedDocument
from hephaion.rag.query_audit import (
    RetrievalAuditConfig,
    query_classification_payload,
    query_excerpt,
    retrieval_strategy_payload,
)
from hephaion.rag.query_transform import PromptFn
from hephaion.rag.retrieval_types import EvidenceReference
from hephaion.rag.scoring import tokenize
from hephaion.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaion.study import EvidenceAssessment, LearningAction, LearningTurnPlan, assess_evidence
from hephaion.study.overview import CANONICAL_OVERVIEW_QUERY
from hephaion.study.priority import PriorityAnalysis, analyze_priority

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

_log = get_logger("chat.evidence")
_RAG_MIN_SCORE = 0.1
_QUERY_RETRIEVAL_TOP_K = 30
_QUERY_NEIGHBOR_RADIUS = 1
_QUERY_NEIGHBOR_LIMIT = 8
_PRIORITY_TOPIC_CHUNK_LIMIT = 10
_SOURCE_ONLY_MIN_TOP_SCORE = 0.18
_DUPLICATE_LOW_CONTENT_MAX_CHARS = 240
_DUPLICATE_LOW_CONTENT_MIN_SOURCES = 2
_OVERVIEW_CHUNK_LIMIT = 10
_OVERVIEW_CHUNKS_PER_DOCUMENT = 1
_OVERVIEW_EXCERPT_CHAR_LIMIT = 260
_OVERVIEW_CONTEXT_TOKEN_BUDGET = 2500
_OVERVIEW_PRIMARY_SOURCE_LIMIT = 10
_OVERVIEW_DOCUMENT_SCAN_LIMIT = 12
_OVERVIEW_SUBSTANTIVE_MIN_SCORE = 16
_CONTACT_OR_URL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+)", re.IGNORECASE)
_QUOTE_CHARS = "'\"\u201c\u201d\u2018\u2019"
_DIRECT_SUPPORT_MIN_TOKEN_LEN = 4
_DIRECT_SUPPORT_MIN_COVERAGE = 0.5
_EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE = 0.3
_DIRECT_SUPPORT_MIN_MATCHES = 2
_DIRECT_SUPPORT_DISTINCTIVE_TOKEN_FLOOR = 0.5
_DIRECT_SUPPORT_DISTINCTIVE_MIN_MISSING = 2
_DIRECT_SUPPORT_QUERY_OVERLAP_FLOOR = 0.6
_DIRECT_SUPPORT_DOMINANT_SCORE_FLOOR = 0.75
_DIRECT_SUPPORT_DOMINANT_SCORE_RATIO = 2.0
_DIRECT_SUPPORT_DOMINANT_MIN_MATCHES = 2
_SOURCE_QUESTION_RE = re.compile(
    r"^User (?:question|request|follow-up):\s*(?P<text>.+)$",
    re.MULTILINE,
)


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
    assessment = _adjust_evidence_assessment(plan, assessment)
    return _direct_support_adjusted_assessment(plan, turn_evidence, assessment)


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


def _direct_support_adjusted_assessment(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
    assessment: EvidenceAssessment,
) -> EvidenceAssessment:
    if plan.action is not LearningAction.SOURCE_QA:
        return assessment
    if _source_answer_reuses_prior_evidence(plan, turn_evidence):
        return replace(
            assessment,
            sufficient=True,
            confidence=max(assessment.confidence, _DIRECT_SUPPORT_MIN_COVERAGE),
            missing_information=(),
            recommended_action="answer",
        )
    query = _source_answer_query(plan)
    if not query:
        return assessment
    strict_source_match = plan.requires_direct_evidence or plan.retrieval_query is None
    expanded_prior = _source_answer_expands_prior_evidence(plan)
    expanded_prior_source_anchor = bool(
        expanded_prior
        and turn_evidence is not None
        and _query_matches_evidence_source(query, turn_evidence)
    )
    support_floor = (
        _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE
        if expanded_prior_source_anchor
        else _DIRECT_SUPPORT_MIN_COVERAGE
        if strict_source_match
        else _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE
        if expanded_prior
        else _DIRECT_SUPPORT_MIN_COVERAGE
    )
    query_terms_missing = bool(
        query
        and turn_evidence is not None
        and _distinctive_query_terms_missing(
            _direct_support_terms(query),
            turn_evidence,
        )
    )
    expanded_prior_direct_query_missing = bool(
        expanded_prior
        and plan.requires_direct_evidence
        and plan.retrieval_query
        and query_terms_missing
        and _query_preserves_user_terms(
            plan.retrieval_query,
            _source_answer_original_request(plan),
        )
    )
    strict_terms_missing = bool(strict_source_match and not expanded_prior and query_terms_missing)
    quoted_phrase_missing = bool(
        plan.retrieval_query
        and turn_evidence is not None
        and _quoted_phrase_terms_missing(plan.retrieval_query, turn_evidence)
    )
    if strict_terms_missing or expanded_prior_direct_query_missing or quoted_phrase_missing:
        support = 0.0
    elif expanded_prior:
        support = _direct_support_coverage_score(query, turn_evidence)
    else:
        support = _direct_support_score(query, turn_evidence)
        support = max(support, _dominant_retrieval_support_score(query, turn_evidence))
    if support >= support_floor:
        if assessment.sufficient:
            return assessment
        return replace(
            assessment,
            sufficient=True,
            confidence=max(assessment.confidence, support),
            missing_information=(),
            recommended_action="answer",
        )
    if (
        not strict_source_match
        and not expanded_prior_direct_query_missing
        and not quoted_phrase_missing
    ):
        return assessment
    return replace(
        assessment,
        sufficient=False,
        confidence=min(assessment.confidence, support),
        missing_information=(f"direct source span for {_excerpt(query, limit=140)}",),
        recommended_action="abstain",
    )


def _source_answer_reuses_prior_evidence(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> bool:
    return bool(
        plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not plan.requires_direct_evidence
        and plan.evidence_refs
        and turn_evidence is not None
        and turn_evidence.items
    )


def _source_answer_expands_prior_evidence(plan: LearningTurnPlan) -> bool:
    return bool(plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR and plan.evidence_refs)


def _source_answer_query(plan: LearningTurnPlan) -> str:
    original_request = _source_answer_original_request(plan)
    if plan.requires_direct_evidence and original_request:
        return original_request
    if plan.retrieval_query:
        return plan.retrieval_query
    return original_request


def _source_answer_original_request(plan: LearningTurnPlan) -> str:
    if match := _SOURCE_QUESTION_RE.search(plan.prompt):
        return match.group("text").strip()
    return ""


def _direct_support_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 1.0
    if _distinctive_query_terms_missing(query_terms, turn_evidence):
        return 0.0
    min_matches = (
        1 if len(query_terms) <= _DIRECT_SUPPORT_MIN_MATCHES else _DIRECT_SUPPORT_MIN_MATCHES
    )
    return max(
        (
            _direct_support_item_score(query_terms, item, min_matches=min_matches)
            for item in turn_evidence.items
        ),
        default=0.0,
    )


def _direct_support_coverage_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 0.0
    min_matches = (
        1 if len(query_terms) <= _DIRECT_SUPPORT_MIN_MATCHES else _DIRECT_SUPPORT_MIN_MATCHES
    )
    return max(
        (
            _direct_support_item_score(query_terms, item, min_matches=min_matches)
            for item in turn_evidence.items
        ),
        default=0.0,
    )


def _dominant_retrieval_support_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None or not turn_evidence.items:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 0.0
    top_item = turn_evidence.items[0]
    if top_item.score < _DIRECT_SUPPORT_DOMINANT_SCORE_FLOOR:
        return 0.0
    next_score = max((item.score for item in turn_evidence.items[1:]), default=0.0)
    if next_score > 0 and top_item.score / next_score < _DIRECT_SUPPORT_DOMINANT_SCORE_RATIO:
        return 0.0
    top_terms = set(_direct_support_terms(f"{top_item.chunk.heading}\n{top_item.content}"))
    matches = sum(1 for term in query_terms if _direct_term_in_terms(term, top_terms))
    if matches < _DIRECT_SUPPORT_DOMINANT_MIN_MATCHES:
        return 0.0
    return max(_DIRECT_SUPPORT_MIN_COVERAGE, matches / len(query_terms))


def _direct_support_item_score(
    query_terms: tuple[str, ...],
    item: EvidenceChunk,
    *,
    min_matches: int,
) -> float:
    item_terms = set(_direct_support_terms(f"{item.chunk.heading}\n{item.content}"))
    matches = sum(1 for term in query_terms if _direct_term_in_terms(term, item_terms))
    if matches < min_matches:
        return 0.0
    return matches / len(query_terms)


def _query_preserves_user_terms(query: str, user_request: str) -> bool:
    query_terms = set(_direct_support_terms(query))
    request_terms = set(_direct_support_terms(user_request))
    if not query_terms or not request_terms:
        return False
    return (
        sum(1 for term in query_terms if _direct_term_in_terms(term, request_terms))
        / len(query_terms)
        >= _DIRECT_SUPPORT_QUERY_OVERLAP_FLOOR
    )


def _direct_support_terms(text: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            term
            for term in tokenize(text)
            if len(term) >= _DIRECT_SUPPORT_MIN_TOKEN_LEN and not term.isdigit()
        )
    )


def _query_matches_evidence_source(query: str, turn_evidence: TurnEvidence) -> bool:
    query_terms = set(_direct_support_terms(query))
    if not query_terms:
        return False
    for item in turn_evidence.items:
        source_terms = set(_direct_support_terms(item.source))
        if source_terms and any(_direct_term_in_terms(term, source_terms) for term in query_terms):
            return True
    return False


def _distinctive_query_terms_missing(
    query_terms: tuple[str, ...],
    turn_evidence: TurnEvidence,
) -> bool:
    if len(query_terms) < _DIRECT_SUPPORT_MIN_MATCHES:
        return False
    evidence_terms = _turn_evidence_terms(turn_evidence)
    missing_terms = [
        term for term in query_terms if not _direct_term_in_terms(term, evidence_terms)
    ]
    if len(missing_terms) < _DIRECT_SUPPORT_DISTINCTIVE_MIN_MISSING:
        return False
    return len(missing_terms) / len(query_terms) >= _DIRECT_SUPPORT_DISTINCTIVE_TOKEN_FLOOR


def _turn_evidence_terms(turn_evidence: TurnEvidence) -> set[str]:
    terms: set[str] = set()
    for item in turn_evidence.items:
        terms.update(_direct_support_terms(f"{item.chunk.heading}\n{item.content}"))
    return terms


def _quoted_phrase_terms_missing(query: str, turn_evidence: TurnEvidence) -> bool:
    evidence_terms = _turn_evidence_terms(turn_evidence)
    for phrase in _quoted_phrases(query):
        phrase_terms = _direct_support_terms(phrase)
        if len(phrase_terms) < _DIRECT_SUPPORT_MIN_MATCHES:
            continue
        if not all(_direct_term_in_terms(term, evidence_terms) for term in phrase_terms):
            return True
    return False


def _direct_term_in_terms(term: str, terms: set[str]) -> bool:
    return any(_direct_terms_match(term, candidate) for candidate in terms)


def _direct_terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if min(len(left), len(right)) < _DIRECT_SUPPORT_MIN_TOKEN_LEN + 1:
        return False
    return difflib.SequenceMatcher(a=left, b=right).ratio() >= 0.84


def _quoted_phrases(text: str) -> tuple[str, ...]:
    phrases: list[str] = []
    opening_index: int | None = None
    for index, character in enumerate(text):
        if not _is_quote_delimiter(text, index, character):
            continue
        if opening_index is None:
            opening_index = index
            continue
        phrase = text[opening_index + 1 : index].strip()
        if len(phrase) >= 3:
            phrases.append(phrase)
        opening_index = None
    return tuple(phrases)


def _is_quote_delimiter(text: str, index: int, character: str) -> bool:
    if character not in _QUOTE_CHARS:
        return False
    if character not in {"'", "\u2019"}:
        return True
    previous_is_word = index > 0 and text[index - 1].isalnum()
    next_is_word = index + 1 < len(text) and text[index + 1].isalnum()
    return not (previous_is_word and next_is_word)


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
    return _query_signature(query) == _query_signature(CANONICAL_OVERVIEW_QUERY)


def _query_signature(query: str) -> str:
    return " ".join(tokenize(query))


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
    content_chunks = [item for item in scored if not _chunk_is_low_content(item.chunk.text)]
    content_chunks = _filter_repeated_short_duplicate_chunks(content_chunks)
    return content_chunks or scored


def _filter_repeated_short_duplicate_chunks(scored: list[ScoredChunk]) -> list[ScoredChunk]:
    duplicate_signatures = _repeated_short_duplicate_signatures(scored)
    if not duplicate_signatures:
        return scored
    return [
        item
        for item in scored
        if _short_duplicate_signature(item.chunk.text) not in duplicate_signatures
    ]


def _repeated_short_duplicate_signatures(scored: Sequence[ScoredChunk]) -> set[str]:
    sources_by_signature: dict[str, set[str]] = {}
    for item in scored:
        signature = _short_duplicate_signature(item.chunk.text)
        if signature:
            sources_by_signature.setdefault(signature, set()).add(item.chunk.source)
    return {
        signature
        for signature, sources in sources_by_signature.items()
        if len(sources) >= _DUPLICATE_LOW_CONTENT_MIN_SOURCES
    }


def _short_duplicate_signature(text: str) -> str:
    normalized = " ".join(unescape(text).casefold().split())
    if not normalized or len(normalized) > _DUPLICATE_LOW_CONTENT_MAX_CHARS:
        return ""
    return normalized


def _chunk_is_low_content(text: str) -> bool:
    normalized = " ".join(unescape(text).split())
    if not normalized:
        return True
    alnum_count = sum(character.isalnum() for character in normalized)
    if alnum_count == 0:
        return True
    if _CONTACT_OR_URL_RE.search(normalized) and _low_content_density(normalized):
        return True
    punctuation_count = sum(character in ".,;:!?()[]{}<>/\\|" for character in normalized)
    alpha_count = sum(character.isalpha() for character in normalized)
    return len(normalized) <= _DUPLICATE_LOW_CONTENT_MAX_CHARS and punctuation_count > alpha_count


def _low_content_density(text: str) -> bool:
    words = tokenize(text)
    if len(words) <= 8:
        return True
    url_chars = sum(len(match.group(0)) for match in _CONTACT_OR_URL_RE.finditer(text))
    return url_chars / max(len(text), 1) >= 0.35


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
    chunks_by_document = [
        _overview_document_chunks(document) for document in _overview_selected_documents(documents)
    ]
    for offset in range(_OVERVIEW_CHUNKS_PER_DOCUMENT):
        if _append_overview_offset(scored, chunks_by_document, offset):
            return scored
    return scored


def _overview_selected_documents(
    documents: Sequence[ChunkedDocument],
) -> tuple[ChunkedDocument, ...]:
    ranked = tuple(sorted(documents, key=_overview_document_sort_key))
    return ranked[: min(_OVERVIEW_PRIMARY_SOURCE_LIMIT, _OVERVIEW_CHUNK_LIMIT)]


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
    chunks = tuple(chunk for chunk in document.chunks if not _chunk_is_low_content(chunk.text))
    return tuple(
        sorted(
            chunks,
            key=lambda chunk: _overview_chunk_sort_key(document.source, chunk),
        )
    )


def _overview_document_sort_key(document: ChunkedDocument) -> tuple[int, str]:
    return len(document.chunks), document.source.casefold()


def _overview_chunk_sort_key(
    source: str,
    chunk: Chunk,
) -> tuple[int, int, int, int]:
    _ = source
    score_text = _overview_chunk_score_text(chunk.text)
    covered = _overview_chunk_looks_like_cover_page(score_text)
    substantive = _overview_chunk_content_score(score_text) >= _OVERVIEW_SUBSTANTIVE_MIN_SCORE
    structural = substantive and _overview_chunk_has_structural_signal(score_text)
    early = chunk.index < _OVERVIEW_DOCUMENT_SCAN_LIMIT
    acceptable = substantive and not covered
    return (
        int(not early),
        int(not structural),
        int(not acceptable),
        chunk.index,
    )


def _overview_chunk_content_score(text: str) -> int:
    token_count = len(set(tokenize(text)))
    punctuation_count = sum(text.count(mark) for mark in ".;:?!")
    section_bonus = 30 if "\f" in text else 0
    return min(token_count, 80) + min(punctuation_count, 12) * 4 + section_bonus


def _overview_chunk_has_structural_signal(text: str) -> bool:
    return any(_overview_character_is_structural_signal(character) for character in text)


def _overview_character_is_structural_signal(character: str) -> bool:
    return unicodedata.category(character) == "Sm" or character in "=<>"


def _overview_chunk_score_text(text: str) -> str:
    sections = [section.strip() for section in text.split("\f") if section.strip()]
    return sections[-1] if len(sections) > 1 else text


def _overview_chunk_looks_like_cover_page(text: str) -> bool:
    normalized = " ".join(unescape(text).split())
    if not normalized:
        return True
    sentence_text = re.sub(r"\b\d{1,2}\.", "", normalized)
    return not any(mark in sentence_text for mark in ".!?;:")


def _fallback_overview_chunks(chunks: Sequence[Chunk]) -> list[ScoredChunk]:
    return [
        _overview_scored_chunk(chunk) for chunk in chunks if not _chunk_is_low_content(chunk.text)
    ][:_OVERVIEW_CHUNK_LIMIT]


def _overview_scored_chunk(chunk: Chunk) -> ScoredChunk:
    return ScoredChunk(chunk=_compact_overview_chunk(chunk), score=1.0)


def _compact_overview_chunk(chunk: Chunk) -> Chunk:
    text = " ".join(_overview_chunk_score_text(chunk.text).split())
    if len(text) <= _OVERVIEW_EXCERPT_CHAR_LIMIT:
        return replace(chunk, text=text)
    return replace(
        chunk,
        text=text[: _OVERVIEW_EXCERPT_CHAR_LIMIT - 17].rstrip() + "\n[... truncated]",
    )


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

        if _material_overview_prompt(plan):
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
    if plan.retrieval_query is None:
        return None
    if plan.action is LearningAction.PRESENT and is_overview_query(plan.retrieval_query):
        return build_turn_evidence_from_overview(session)
    if plan.action is LearningAction.PRESENT and (
        plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    ):
        if _material_overview_prompt(plan):
            return build_turn_evidence_from_overview(session)
        return build_turn_evidence_from_query(session, plan.retrieval_query) or (
            build_turn_evidence_from_overview(session)
        )
    query_evidence = build_turn_evidence_from_query(session, plan.retrieval_query)
    if _material_overview_prompt(plan) and not _query_evidence_supports_request(
        plan.retrieval_query,
        query_evidence,
    ):
        return build_turn_evidence_from_overview(session)
    return query_evidence


def _material_overview_prompt(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.PRESENT and "Execute MATERIAL_OVERVIEW." in plan.prompt


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
    "is_overview_query",
    "parse_source_ref",
    "resolve_transform_strategy",
    "resolve_turn_evidence",
    "retrieval_audit_metadata",
]
