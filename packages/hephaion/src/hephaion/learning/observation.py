"""Compact observations for local harness-attempt policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from hephaion._types import is_string_mapping
from hephaion.agent.citation import VerificationResult
from hephaion.rag.context import TurnEvidence
from hephaion.study.policy import EvidenceAssessment

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class _EvidenceObservationStats:
    evidence_count: int = 0
    distinct_source_count: int = 0
    sampled_source_count: int = 0
    total_source_count: int = 0
    top_score: float = 0.0


@dataclass(frozen=True, slots=True)
class _EvidenceAssessmentStats:
    sufficient: bool = False
    confidence: float = 0.0
    recommended_action: str = ""


@dataclass(frozen=True, slots=True)
class _AnswerRelevanceStats:
    score: float = 1.0
    required: bool = False
    off_topic: bool = False


@dataclass(frozen=True, slots=True)
class AttemptObservation:
    attempt_index: int = 1
    intent: str = ""
    answer_mode: str = ""
    retrieval_strategy: str = ""
    citation_required: bool = False
    evidence_count: int = 0
    distinct_source_count: int = 0
    sampled_source_count: int = 0
    total_source_count: int = 0
    top_score: float = 0.0
    evidence_sufficient: bool = False
    evidence_confidence: float = 0.0
    evidence_recommended_action: str = ""
    has_citations: bool = False
    citation_count: int = 0
    all_citations_verified: bool = True
    unverified_citation_count: int = 0
    unsupported_claim_count: int = 0
    answer_relevance_score: float = 1.0
    answer_relevance_required: bool = False
    off_topic_answer: bool = False
    missing_required_citation_count: int = 0
    confident_thin_evidence: bool = False
    reply_chars: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    internal_passes: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "attempt_index": self.attempt_index,
            "intent": self.intent,
            "answer_mode": self.answer_mode,
            "retrieval_strategy": self.retrieval_strategy,
            "citation_required": self.citation_required,
            "evidence_count": self.evidence_count,
            "distinct_source_count": self.distinct_source_count,
            "sampled_source_count": self.sampled_source_count,
            "total_source_count": self.total_source_count,
            "top_score": self.top_score,
            "evidence_sufficient": self.evidence_sufficient,
            "evidence_confidence": self.evidence_confidence,
            "evidence_recommended_action": self.evidence_recommended_action,
            "has_citations": self.has_citations,
            "citation_count": self.citation_count,
            "all_citations_verified": self.all_citations_verified,
            "unverified_citation_count": self.unverified_citation_count,
            "unsupported_claim_count": self.unsupported_claim_count,
            "answer_relevance_score": self.answer_relevance_score,
            "answer_relevance_required": self.answer_relevance_required,
            "off_topic_answer": self.off_topic_answer,
            "missing_required_citation_count": self.missing_required_citation_count,
            "confident_thin_evidence": self.confident_thin_evidence,
            "reply_chars": self.reply_chars,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "internal_passes": self.internal_passes,
        }

    @classmethod
    def from_dict(cls, payload: object) -> AttemptObservation:
        if not is_string_mapping(payload):
            return cls()
        return cls(
            attempt_index=_payload_int(payload, "attempt_index", default=1),
            intent=_payload_string(payload, "intent"),
            answer_mode=_payload_string(payload, "answer_mode"),
            retrieval_strategy=_payload_string(payload, "retrieval_strategy"),
            citation_required=_payload_bool(payload, "citation_required"),
            evidence_count=_payload_int(payload, "evidence_count"),
            distinct_source_count=_payload_int(payload, "distinct_source_count"),
            sampled_source_count=_payload_int(payload, "sampled_source_count"),
            total_source_count=_payload_int(payload, "total_source_count"),
            top_score=_payload_float(payload, "top_score"),
            evidence_sufficient=_payload_bool(payload, "evidence_sufficient"),
            evidence_confidence=_payload_float(payload, "evidence_confidence"),
            evidence_recommended_action=_payload_string(payload, "evidence_recommended_action"),
            has_citations=_payload_bool(payload, "has_citations"),
            citation_count=_payload_int(payload, "citation_count"),
            all_citations_verified=_payload_bool(payload, "all_citations_verified", default=True),
            unverified_citation_count=_payload_int(payload, "unverified_citation_count"),
            unsupported_claim_count=_payload_int(payload, "unsupported_claim_count"),
            answer_relevance_score=_payload_float(
                payload,
                "answer_relevance_score",
                default=1.0,
            ),
            answer_relevance_required=_payload_bool(payload, "answer_relevance_required"),
            off_topic_answer=_payload_bool(payload, "off_topic_answer"),
            missing_required_citation_count=_payload_int(
                payload,
                "missing_required_citation_count",
            ),
            confident_thin_evidence=_payload_bool(payload, "confident_thin_evidence"),
            reply_chars=_payload_int(payload, "reply_chars"),
            latency_ms=_payload_float(payload, "latency_ms"),
            cost_usd=_payload_float(payload, "cost_usd"),
            internal_passes=_payload_int(payload, "internal_passes", default=1),
        )


def build_attempt_observation(
    *,
    attempt_index: int,
    intent: str,
    answer_mode: str,
    retrieval_strategy: str,
    citation_required: bool,
    evidence: TurnEvidence | None,
    evidence_assessment: EvidenceAssessment | None,
    citation_result: VerificationResult,
    reply: str,
    latency_ms: float,
    internal_passes: int,
    cost_usd: float = 0.0,
    request_text: str = "",
    answer_relevance_required: bool = False,
) -> AttemptObservation:
    evidence_stats = _evidence_stats(evidence)
    assessment_stats = _assessment_stats(evidence_assessment)
    relevance_stats = _answer_relevance_stats(
        request_text=request_text,
        reply=reply,
        evidence=evidence,
        evidence_assessment=evidence_assessment,
        citation_result=citation_result,
        required=answer_relevance_required,
    )
    return AttemptObservation(
        attempt_index=max(1, attempt_index),
        intent=intent,
        answer_mode=answer_mode,
        retrieval_strategy=retrieval_strategy,
        citation_required=citation_required,
        evidence_count=evidence_stats.evidence_count,
        distinct_source_count=evidence_stats.distinct_source_count,
        sampled_source_count=evidence_stats.sampled_source_count,
        total_source_count=evidence_stats.total_source_count,
        top_score=evidence_stats.top_score,
        evidence_sufficient=assessment_stats.sufficient,
        evidence_confidence=assessment_stats.confidence,
        evidence_recommended_action=assessment_stats.recommended_action,
        has_citations=citation_result.has_citations,
        citation_count=citation_result.citation_count,
        all_citations_verified=citation_result.all_verified,
        unverified_citation_count=len(citation_result.unverified),
        unsupported_claim_count=1 if relevance_stats.off_topic else 0,
        answer_relevance_score=relevance_stats.score,
        answer_relevance_required=relevance_stats.required,
        off_topic_answer=relevance_stats.off_topic,
        missing_required_citation_count=(
            1 if citation_required and reply and not citation_result.has_citations else 0
        ),
        confident_thin_evidence=_confident_thin_evidence(assessment_stats),
        reply_chars=len(reply),
        latency_ms=max(0.0, latency_ms),
        cost_usd=max(0.0, cost_usd),
        internal_passes=max(1, internal_passes),
    )


def _answer_relevance_stats(
    *,
    request_text: str,
    reply: str,
    evidence: TurnEvidence | None,
    evidence_assessment: EvidenceAssessment | None,
    citation_result: VerificationResult,
    required: bool,
) -> _AnswerRelevanceStats:
    if not required:
        return _AnswerRelevanceStats(required=False)
    request_terms = _content_terms(request_text)
    if len(request_terms) < 2 or not reply.strip():
        return _AnswerRelevanceStats(required=True)
    reply_terms = _content_terms(reply)
    cited_evidence_terms = _cited_evidence_terms(
        evidence,
        evidence_assessment=evidence_assessment,
        citation_result=citation_result,
    )
    reply_score = _coverage(request_terms, reply_terms)
    evidence_score = _coverage(request_terms, cited_evidence_terms)
    cited_support_score = _coverage(reply_terms, cited_evidence_terms)
    source_backed_score = min(evidence_score, cited_support_score)
    score = max(reply_score, source_backed_score)
    return _AnswerRelevanceStats(
        score=score,
        required=True,
        off_topic=reply_score < 0.12 and source_backed_score < 0.12,
    )


def _content_terms(text: str) -> frozenset[str]:
    return frozenset(
        token
        for token in _iter_normalized_tokens(text)
        if len(token) >= 4 and not token.isdecimal()
    )


def _cited_evidence_terms(
    evidence: TurnEvidence | None,
    *,
    evidence_assessment: EvidenceAssessment | None,
    citation_result: VerificationResult,
) -> frozenset[str]:
    if evidence is None:
        return frozenset()
    cited_refs = tuple(citation_result.verified)
    if not cited_refs and evidence_assessment is not None:
        cited_refs = tuple(evidence_assessment.supporting_refs)
    chunks = tuple(
        chunk
        for evidence_id in cited_refs
        if (chunk := evidence.get(evidence_id)) is not None
    )
    if not chunks:
        return frozenset()
    return frozenset(
        term
        for chunk in chunks
        for term in _content_terms(f"{chunk.source}\n{chunk.content}")
    )


def _iter_normalized_tokens(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in text.casefold():
        if character.isalnum():
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current.clear()
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _coverage(required_terms: frozenset[str], candidate_terms: frozenset[str]) -> float:
    if not required_terms:
        return 1.0
    return round(len(required_terms & candidate_terms) / len(required_terms), 4)


def _confident_thin_evidence(assessment_stats: _EvidenceAssessmentStats) -> bool:
    return bool(
        not assessment_stats.sufficient
        and assessment_stats.confidence >= 0.65
        and assessment_stats.recommended_action != "abstain"
    )


def _evidence_stats(evidence: TurnEvidence | None) -> _EvidenceObservationStats:
    if evidence is None:
        return _EvidenceObservationStats()
    sources = {item.source for item in evidence.items}
    return _EvidenceObservationStats(
        evidence_count=len(evidence.items),
        distinct_source_count=len(sources),
        sampled_source_count=evidence.sampled_source_count,
        total_source_count=evidence.total_source_count,
        top_score=evidence.items[0].score if evidence.items else 0.0,
    )


def _assessment_stats(
    evidence_assessment: EvidenceAssessment | None,
) -> _EvidenceAssessmentStats:
    if evidence_assessment is None:
        return _EvidenceAssessmentStats()
    return _EvidenceAssessmentStats(
        sufficient=evidence_assessment.sufficient,
        confidence=evidence_assessment.confidence,
        recommended_action=evidence_assessment.recommended_action,
    )


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _payload_bool(
    payload: Mapping[str, object],
    key: str,
    *,
    default: bool = False,
) -> bool:
    value = payload.get(key)
    return value if isinstance(value, bool) else default


def _payload_int(
    payload: Mapping[str, object],
    key: str,
    *,
    default: int = 0,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _payload_float(
    payload: Mapping[str, object],
    key: str,
    *,
    default: float = 0.0,
) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    return default
