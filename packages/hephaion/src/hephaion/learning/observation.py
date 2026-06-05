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
    reply_chars: int = 0
    latency_ms: float = 0.0
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
            "reply_chars": self.reply_chars,
            "latency_ms": self.latency_ms,
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
            reply_chars=_payload_int(payload, "reply_chars"),
            latency_ms=_payload_float(payload, "latency_ms"),
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
) -> AttemptObservation:
    evidence_stats = _evidence_stats(evidence)
    assessment_stats = _assessment_stats(evidence_assessment)
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
        reply_chars=len(reply),
        latency_ms=max(0.0, latency_ms),
        internal_passes=max(1, internal_passes),
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


def _payload_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    return 0.0
