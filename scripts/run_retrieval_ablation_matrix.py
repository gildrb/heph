"""Run a local Hephaistos retrieval ablation matrix over labelled RAG cases.

The matrix is intentionally benchmark-script-only: it calls Hephaistos retrieval APIs over a
materialized armory, records matched corpus/case/hash metadata for every row, and writes private
artifacts under a caller-provided output directory.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import shutil
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from hephaistos.armory import storage
from hephaistos.rag import (
    ArmoryIndex,
    EvidenceReference,
    RetrievalMode,
    ScoredChunk,
    TransformStrategy,
    load_or_build,
    optional_backends,
    retrieve,
)
from hephaistos.rag.hybrid import (
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
)
from scripts import benchmark_rag, claim_report_envelope

SCHEMA_VERSION = "retrieval-ablation-matrix-report-v1"
MANIFEST_SCHEMA_VERSION = "retrieval-ablation-artifact-manifest-v1"
RUNNER_ID = "scripts.run_retrieval_ablation_matrix"
SCORING_PROTOCOL_VERSION = claim_report_envelope.SCORING_PROTOCOL_VERSION
REQUIRED_TOP_K_VALUES = (1, 3, 5, 10, 25, 50, 100)
_DEFAULT_MIN_SCORE = 0.0
_DEFAULT_CANDIDATE_MULTIPLIER = 2
_DEFAULT_WEIGHTED_HYBRID_SPARSE_WEIGHT = 1.25
_DEFAULT_WEIGHTED_HYBRID_DENSE_WEIGHT = 1.0
_UNWEIGHTED_RRF_WEIGHT = 1.0
_DEFAULT_MIN_PERMISSION_RETRIEVAL_SAFETY_RATE = 1.0
_DEFAULT_MIN_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE = 0.0
_DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_PRIMARY_METRIC = "recall_at_k"
_PRIMARY_TOP_K = 50
_METRIC_KEYS = (
    "hit_rate_at_k",
    "recall_at_k",
    "mrr_at_k",
    "map_at_k",
    "ndcg_at_k",
    "precision_at_k",
)
_COUNT_KEYS = ("query_count", "miss_count")
_EVIDENCE_FULL = "full_evidence"
_EVIDENCE_PARTIAL = "partial_evidence"
_EVIDENCE_NONE = "no_evidence"
_EVIDENCE_CATEGORIES = (_EVIDENCE_FULL, _EVIDENCE_PARTIAL, _EVIDENCE_NONE)
_MISS_PARTIAL = "partial_expected_evidence_only"
_MISS_NO_EXPECTED = "no_expected_evidence_retrieved"
_MISS_NO_CANDIDATES = "no_retrieved_candidates"
_MISS_OUTSIDE_TOP_K = "expected_evidence_outside_requested_top_k"
_MISS_FORBIDDEN_ORDERING = "forbidden_before_expected_ordering"
_MISS_PERMISSION_SCOPE = "permission_scope_exclusion"
_FUSION_NONE = "none"
_FUSION_WEIGHTED_HYBRID = "weighted_sparse_dense"
_FUSION_RRF = "reciprocal_rank_fusion"
_ARTIFACT_FILENAMES = {
    "matrix_report": "matrix-report.json",
    "per_query_results": "per-query-results.jsonl",
    "diagnostics": "diagnostics.json",
    "run_metadata": "run-metadata.json",
    "summary": "summary.md",
}
_RUNTIME_ONLY_FIELDS = (
    "metadata.armory_path",
    "metadata.working_armory_path",
    "metadata.cases_path",
    "metadata.output_dir",
    "metadata.command_invocation",
    "metadata.report_path",
    "artifact_manifest.path",
    "artifact_manifest.sha256",
    "matrix.rows[].metrics.mean_latency_ms",
    "matrix.rows[].metrics.latency.mean_ms",
    "per_query_results[].latency_ms",
    "aggregate_metrics.mean_latency_ms",
    "aggregate_metrics.latency.mean_ms",
)


class MatrixValidationError(ValueError):
    """A retrieval matrix report violates the public matrix contract."""


class ReferenceResolutionError(ValueError):
    """A labelled or retrieved reference cannot be resolved to the current corpus."""


class ReferenceGranularity(StrEnum):
    """Scoring granularity for canonical retrieval references."""

    CHUNK = "chunk"
    DOCUMENT = "document"


@dataclass(frozen=True, slots=True)
class MatrixContractResult:
    """Validation result for matrix reports and artifact manifests."""

    status: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MatrixCell:
    """Public matrix cell descriptor used by tests and command fixtures."""

    retriever: str
    granularity: str
    retrieval_mode: RetrievalMode
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER
    hybrid_sparse_weight: float = 1.0
    hybrid_dense_weight: float = 1.0
    fusion_strategy: str = _FUSION_NONE

    def candidate_budget(self, top_k: int) -> int:
        """Return the pre-final candidate budget for this cell."""
        if self.granularity == ReferenceGranularity.DOCUMENT.value or self.retriever in {
            "hybrid",
            "rrf",
        }:
            return max(top_k, top_k * self.candidate_multiplier)
        return top_k

    def fusion_payload(self) -> dict[str, object]:
        """Return explicit fusion metadata for this cell."""
        return _fusion_payload(
            self.fusion_strategy,
            sparse_weight=self.hybrid_sparse_weight,
            dense_weight=self.hybrid_dense_weight,
        )

    def retrieval_signature(self) -> str:
        """Return the canonical mode/fusion identity exercised by this cell."""
        return _retrieval_signature(self.retrieval_mode.value, self.fusion_payload())


@dataclass(frozen=True, slots=True)
class MatrixParameters:
    """Runtime parameters shared by every matrix cell."""

    top_k_values: tuple[int, ...] = REQUIRED_TOP_K_VALUES
    min_score: float = _DEFAULT_MIN_SCORE
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER
    embedding_model: str | None = None
    embedding_query_prefix: str = ""
    embedding_document_prefix: str = ""
    rerank_model: str | None = None
    hybrid_sparse_weight: float = 1.0
    hybrid_dense_weight: float = 1.0


@dataclass(frozen=True, slots=True)
class MatrixConfig:
    """One retrieval-mode/granularity combination in the ablation matrix."""

    retriever: str
    granularity: ReferenceGranularity
    retrieval_mode: RetrievalMode
    fusion_strategy: str = _FUSION_NONE
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER
    sparse_weight: float = 1.0
    dense_weight: float = 0.0

    def payload(self) -> dict[str, object]:
        """Return a stable machine-readable config payload."""
        return {
            "retriever": self.retriever,
            "granularity": self.granularity.value,
            "retrieval_mode": self.retrieval_mode.value,
            "retrieval_signature": self.retrieval_signature(),
            "candidate_multiplier": self.candidate_multiplier,
            "fusion": self.fusion_payload(),
            "claim_eligible": self.claim_eligible(),
        }

    def fusion_payload(self) -> dict[str, object]:
        """Return explicit fusion metadata for this matrix config."""
        return _fusion_payload(
            self.fusion_strategy,
            sparse_weight=self.sparse_weight,
            dense_weight=self.dense_weight,
        )

    def retrieval_signature(self) -> str:
        """Return the canonical mode/fusion identity exercised by this config."""
        return _retrieval_signature(self.retrieval_mode.value, self.fusion_payload())

    def candidate_budget(self, top_k: int) -> int:
        """Return the requested pre-final candidate budget for this row."""
        if self.granularity == ReferenceGranularity.DOCUMENT and (
            self.retrieval_mode != RetrievalMode.BM25_DOCUMENT
        ):
            return max(top_k, top_k * self.candidate_multiplier)
        if self.fusion_strategy != _FUSION_NONE:
            return max(top_k, top_k * self.candidate_multiplier)
        return top_k

    def claim_eligible(self) -> bool:
        """Return whether this row can support comparative retrieval claims."""
        if self.fusion_strategy == _FUSION_WEIGHTED_HYBRID:
            return not _weights_match(
                self.sparse_weight,
                self.dense_weight,
                sparse_weight=_UNWEIGHTED_RRF_WEIGHT,
                dense_weight=_UNWEIGHTED_RRF_WEIGHT,
            )
        return True


@dataclass(frozen=True, slots=True)
class RankedReference:
    """A retrieved reference with the score and excerpt needed for audit artifacts."""

    ref: str
    score: float
    text_excerpt: str


@dataclass(frozen=True, slots=True)
class RankedReferenceSet:
    """Raw and deduplicated retrieval candidates used for top-k reconciliation."""

    ranked: tuple[RankedReference, ...]
    raw_candidate_count: int
    candidate_retrieved_count: int
    duplicate_document_drop_count: int


@dataclass(frozen=True, slots=True)
class CanonicalLabel:
    """A resolved expected or forbidden label at a scoring granularity."""

    canonical: str
    source: str
    chunk_index: int | None
    source_scope: bool


@dataclass(frozen=True, slots=True)
class CanonicalRetrievedReference:
    """A retrieved reference resolved to canonical document or chunk identity."""

    canonical: str
    source: str
    chunk_ref: str
    score: float
    text_excerpt: str


@dataclass(frozen=True, slots=True)
class CaseLabels:
    """Canonical labels for one benchmark case."""

    expected: tuple[CanonicalLabel, ...]
    forbidden_before_expected: tuple[CanonicalLabel, ...]


@dataclass(frozen=True, slots=True)
class RankingMetrics:
    """Per-query retrieval ranking metrics."""

    relevant_found: int
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    average_precision_at_k: float
    ndcg_at_k: float


@dataclass(frozen=True, slots=True)
class GroupEvidence:
    """Evidence coverage for one expected source family or document type."""

    label: str
    expected_count: int
    matched_count: int
    evidence_category: str


@dataclass(frozen=True, slots=True)
class ScoredCaseResult:
    """Scored per-query result after canonical reference handling."""

    case_id: str
    query: str
    query_type: str
    expected_count: int
    forbidden_count: int
    retrieved: tuple[str, ...]
    retrieved_chunks: tuple[dict[str, object], ...]
    hit: bool
    rank: int | None
    candidate_rank: int | None
    first_forbidden_rank: int | None
    forbidden_before_expected_ok: bool
    metrics: RankingMetrics
    candidate_metrics: RankingMetrics
    evidence_category: str
    miss_bucket: str | None
    retrieval_top_k_requested: int
    raw_candidate_count: int
    candidate_retrieved_count: int
    final_retrieved_count: int
    top_k_satisfied: bool
    top_k_shortfall_count: int
    duplicate_document_drop_count: int
    permission_violation_count: int
    permission_violation_sources: tuple[str, ...]
    expected_source_families: tuple[str, ...]
    expected_document_types: tuple[str, ...]
    source_family_evidence: tuple[GroupEvidence, ...]
    document_type_evidence: tuple[GroupEvidence, ...]
    top_retrieved_source_family: str | None
    top_retrieved_document_type: str | None
    elapsed_ms: float


@dataclass(frozen=True, slots=True)
class CanonicalCorpus:
    """Current-corpus reference resolver for matrix scoring."""

    source_to_chunks: dict[str, tuple[int, ...]]

    @classmethod
    def from_index(cls, index: ArmoryIndex) -> CanonicalCorpus:
        """Build a canonical corpus resolver from a loaded armory index."""
        source_to_chunks: dict[str, list[int]] = {}
        for chunk in index.all_chunks:
            source_to_chunks.setdefault(chunk.source, []).append(chunk.index)
        return cls(
            {
                source: tuple(sorted(set(chunk_indices)))
                for source, chunk_indices in source_to_chunks.items()
            }
        )

    @classmethod
    def from_reference_map(cls, source_to_chunks: Mapping[str, Sequence[int]]) -> CanonicalCorpus:
        """Build a resolver from test fixtures or external corpus metadata."""
        return cls(
            {
                source: tuple(sorted(set(chunk_indices)))
                for source, chunk_indices in source_to_chunks.items()
            }
        )

    def has_source(self, source: str) -> bool:
        """Return whether *source* exists in the current corpus."""
        return source in self.source_to_chunks

    def has_chunk(self, source: str, chunk_index: int) -> bool:
        """Return whether *source#chunk=chunk_index* exists in the current corpus."""
        return chunk_index in self.source_to_chunks.get(source, ())


def default_matrix_configs() -> tuple[MatrixConfig, ...]:
    """Return the required core retrieval ablation configs."""
    return tuple(_config_from_cell(cell) for cell in required_matrix_cells())


def required_matrix_cells(
    *,
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER,
    hybrid_sparse_weight: float = _DEFAULT_WEIGHTED_HYBRID_SPARSE_WEIGHT,
    hybrid_dense_weight: float = _DEFAULT_WEIGHTED_HYBRID_DENSE_WEIGHT,
) -> tuple[MatrixCell, ...]:
    """Return the required core matrix cells as public contract descriptors."""
    return (
        MatrixCell(
            retriever="bm25",
            granularity=ReferenceGranularity.CHUNK.value,
            retrieval_mode=RetrievalMode.BM25,
            candidate_multiplier=candidate_multiplier,
            hybrid_sparse_weight=1.0,
            hybrid_dense_weight=0.0,
        ),
        MatrixCell(
            retriever="bm25",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.BM25_DOCUMENT,
            candidate_multiplier=candidate_multiplier,
            hybrid_sparse_weight=1.0,
            hybrid_dense_weight=0.0,
        ),
        MatrixCell(
            retriever="dense",
            granularity=ReferenceGranularity.CHUNK.value,
            retrieval_mode=RetrievalMode.DENSE,
            candidate_multiplier=candidate_multiplier,
            hybrid_sparse_weight=0.0,
            hybrid_dense_weight=1.0,
        ),
        MatrixCell(
            retriever="dense",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.DENSE,
            candidate_multiplier=candidate_multiplier,
            hybrid_sparse_weight=0.0,
            hybrid_dense_weight=1.0,
        ),
        MatrixCell(
            retriever="hybrid",
            granularity=ReferenceGranularity.CHUNK.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy=_FUSION_WEIGHTED_HYBRID,
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
        ),
        MatrixCell(
            retriever="hybrid",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy=_FUSION_WEIGHTED_HYBRID,
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
        ),
        MatrixCell(
            retriever="rrf",
            granularity=ReferenceGranularity.CHUNK.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy=_FUSION_RRF,
            hybrid_sparse_weight=_UNWEIGHTED_RRF_WEIGHT,
            hybrid_dense_weight=_UNWEIGHTED_RRF_WEIGHT,
        ),
        MatrixCell(
            retriever="rrf",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy=_FUSION_RRF,
            hybrid_sparse_weight=_UNWEIGHTED_RRF_WEIGHT,
            hybrid_dense_weight=_UNWEIGHTED_RRF_WEIGHT,
        ),
    )


def _config_from_cell(cell: MatrixCell) -> MatrixConfig:
    return MatrixConfig(
        retriever=cell.retriever,
        granularity=ReferenceGranularity(cell.granularity),
        retrieval_mode=cell.retrieval_mode,
        fusion_strategy=cell.fusion_strategy,
        candidate_multiplier=cell.candidate_multiplier,
        sparse_weight=cell.hybrid_sparse_weight,
        dense_weight=cell.hybrid_dense_weight,
    )


def _cell_from_config(config: MatrixConfig) -> MatrixCell:
    return MatrixCell(
        retriever=config.retriever,
        granularity=config.granularity.value,
        retrieval_mode=config.retrieval_mode,
        candidate_multiplier=config.candidate_multiplier,
        hybrid_sparse_weight=config.sparse_weight,
        hybrid_dense_weight=config.dense_weight,
        fusion_strategy=config.fusion_strategy,
    )


def _fusion_payload(
    fusion_strategy: str,
    *,
    sparse_weight: float,
    dense_weight: float,
) -> dict[str, object]:
    if fusion_strategy == _FUSION_NONE:
        return {
            "strategy": _FUSION_NONE,
            "algorithm": _FUSION_NONE,
            "sparse_weight": 0.0,
            "dense_weight": 0.0,
            "canonical_id": _FUSION_NONE,
        }
    return {
        "strategy": fusion_strategy,
        "algorithm": _fusion_algorithm(fusion_strategy),
        "sparse_weight": sparse_weight,
        "dense_weight": dense_weight,
        "canonical_id": _fusion_canonical_id(fusion_strategy, sparse_weight, dense_weight),
    }


def _fusion_algorithm(fusion_strategy: str) -> str:
    if fusion_strategy == _FUSION_WEIGHTED_HYBRID:
        return "weighted_reciprocal_rank_fusion"
    if fusion_strategy == _FUSION_RRF:
        return _FUSION_RRF
    return fusion_strategy


def _fusion_canonical_id(
    fusion_strategy: str,
    sparse_weight: float,
    dense_weight: float,
) -> str:
    if fusion_strategy == _FUSION_NONE:
        return _FUSION_NONE
    return (
        f"{fusion_strategy}:"
        f"sparse={_weight_label(sparse_weight)}:"
        f"dense={_weight_label(dense_weight)}"
    )


def _retrieval_signature(retrieval_mode: str, fusion: Mapping[str, object]) -> str:
    canonical_fusion = fusion.get("canonical_id")
    if not isinstance(canonical_fusion, str):
        canonical_fusion = _fusion_canonical_id(
            _string_value(fusion.get("strategy"), fallback=_FUSION_NONE),
            _float_value(fusion.get("sparse_weight")),
            _float_value(fusion.get("dense_weight")),
        )
    return f"{retrieval_mode}|fusion={canonical_fusion}"


def _weight_label(value: float) -> str:
    return f"{value:.6g}"


def _weights_match(
    actual_sparse_weight: float,
    actual_dense_weight: float,
    *,
    sparse_weight: float,
    dense_weight: float,
) -> bool:
    return math.isclose(
        actual_sparse_weight,
        sparse_weight,
        rel_tol=0.0,
        abs_tol=1e-12,
    ) and math.isclose(
        actual_dense_weight,
        dense_weight,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def matrix_row_id(config: MatrixConfig, top_k: int) -> str:
    """Build a stable row id from a matrix config and top-k value."""
    return f"{config.retriever}:{config.granularity.value}:k={top_k}"


def canonicalize_case_labels(
    expected: Sequence[str],
    forbidden_before_expected: Sequence[str],
    corpus: CanonicalCorpus,
    *,
    granularity: ReferenceGranularity,
) -> CaseLabels:
    """Resolve expected and forbidden labels, rejecting duplicates and aliases."""
    expected_labels = _collapse_document_labels(
        tuple(
            _canonical_label(reference, corpus, granularity=granularity) for reference in expected
        ),
        granularity=granularity,
    )
    forbidden_labels = _collapse_document_labels(
        tuple(
            _canonical_label(reference, corpus, granularity=granularity)
            for reference in forbidden_before_expected
        ),
        granularity=granularity,
    )
    _validate_label_uniqueness(expected_labels, label="expected")
    _validate_label_uniqueness(forbidden_labels, label="forbidden_before_expected")
    return CaseLabels(expected=expected_labels, forbidden_before_expected=forbidden_labels)


def _collapse_document_labels(
    labels: Sequence[CanonicalLabel],
    *,
    granularity: ReferenceGranularity,
) -> tuple[CanonicalLabel, ...]:
    if granularity != ReferenceGranularity.DOCUMENT:
        return tuple(labels)
    collapsed: list[CanonicalLabel] = []
    seen: set[str] = set()
    for label in labels:
        if label.canonical in seen:
            continue
        collapsed.append(label)
        seen.add(label.canonical)
    return tuple(collapsed)


def canonical_relevant_references(
    references: Sequence[str],
    relevance_grades: Mapping[str, float],
    *,
    granularity: str,
) -> tuple[tuple[str, ...], dict[str, float]]:
    """Canonicalize labelled relevant references without needing a corpus index.

    Chunk granularity preserves exact chunk ids while allowing source-level labels. Document
    granularity collapses chunk aliases to their source path and keeps the strongest grade for
    duplicate document aliases.
    """
    if granularity not in {ReferenceGranularity.CHUNK.value, ReferenceGranularity.DOCUMENT.value}:
        raise ReferenceResolutionError(f"unsupported granularity: {granularity}")
    canonical_refs: list[str] = []
    canonical_grades: dict[str, float] = {}
    seen: set[str] = set()
    for reference in references:
        canonical = _reference_source(reference) if granularity == "document" else reference
        if canonical not in seen:
            canonical_refs.append(canonical)
            seen.add(canonical)
        grade_candidates = [
            grade
            for raw_ref, grade in relevance_grades.items()
            if (
                raw_ref == reference
                or (
                    granularity == ReferenceGranularity.DOCUMENT.value
                    and _reference_source(raw_ref) == canonical
                )
            )
        ]
        if grade_candidates:
            canonical_grades[canonical] = max(
                (canonical_grades.get(canonical, 0.0), *grade_candidates),
            )
    return tuple(canonical_refs), canonical_grades


def score_ranked_references(
    *,
    case_id: str,
    query: str,
    query_type: str,
    labels: CaseLabels,
    retrieved: Sequence[RankedReference],
    corpus: CanonicalCorpus,
    granularity: ReferenceGranularity,
    top_k: int,
    retrieval_top_k_requested: int,
    raw_candidate_count: int,
    candidate_retrieved_count: int,
    duplicate_document_drop_count: int,
    elapsed_ms: float,
    allowed_sources: frozenset[str] | None = None,
) -> ScoredCaseResult:
    """Score a ranked list after canonicalizing and deduplicating retrieved references."""
    canonical_retrieved = _canonicalize_retrieved(retrieved, corpus, granularity=granularity)
    top_retrieved = canonical_retrieved[:top_k]
    rank = _first_label_rank(labels.expected, top_retrieved)
    candidate_rank = _first_label_rank(labels.expected, canonical_retrieved)
    forbidden_rank = _first_label_rank(labels.forbidden_before_expected, top_retrieved)
    metrics = _rank_metrics(labels.expected, top_retrieved, top_k=top_k)
    candidate_metrics = _rank_metrics(
        labels.expected,
        canonical_retrieved,
        top_k=max(retrieval_top_k_requested, top_k),
    )
    forbidden_ok = _forbidden_before_expected_ok(rank, forbidden_rank)
    retrieved_chunk_rows = [_retrieved_chunk_payload(item) for item in top_retrieved]
    final_retrieved_count = len(top_retrieved)
    top_k_shortfall_count = max(0, top_k - final_retrieved_count)
    evidence_category = _evidence_category(metrics.relevant_found, len(labels.expected))
    permission_violation_sources = _permission_violation_sources(top_retrieved, allowed_sources)
    permission_violation_count = 1 if permission_violation_sources else 0
    miss_bucket = _miss_bucket(
        evidence_category=evidence_category,
        forbidden_before_expected_ok=forbidden_ok,
        permission_violation_count=permission_violation_count,
        final_retrieved_count=final_retrieved_count,
        candidate_rank=candidate_rank,
        top_k=top_k,
    )
    return ScoredCaseResult(
        case_id=case_id,
        query=query,
        query_type=query_type,
        expected_count=len(labels.expected),
        forbidden_count=len(labels.forbidden_before_expected),
        retrieved=tuple(item.canonical for item in top_retrieved),
        retrieved_chunks=tuple(retrieved_chunk_rows),
        hit=rank is not None,
        rank=rank,
        candidate_rank=candidate_rank,
        first_forbidden_rank=forbidden_rank,
        forbidden_before_expected_ok=forbidden_ok,
        metrics=metrics,
        candidate_metrics=candidate_metrics,
        evidence_category=evidence_category,
        miss_bucket=miss_bucket,
        retrieval_top_k_requested=retrieval_top_k_requested,
        raw_candidate_count=raw_candidate_count,
        candidate_retrieved_count=candidate_retrieved_count,
        final_retrieved_count=final_retrieved_count,
        top_k_satisfied=top_k_shortfall_count == 0,
        top_k_shortfall_count=top_k_shortfall_count,
        duplicate_document_drop_count=duplicate_document_drop_count,
        permission_violation_count=permission_violation_count,
        permission_violation_sources=permission_violation_sources,
        expected_source_families=_families_from_labels(labels.expected),
        expected_document_types=_document_types_from_labels(labels.expected),
        source_family_evidence=_group_evidence(
            labels.expected,
            top_retrieved,
            label_fn=_source_family,
        ),
        document_type_evidence=_group_evidence(
            labels.expected,
            top_retrieved,
            label_fn=_document_type,
        ),
        top_retrieved_source_family=_source_family(top_retrieved[0].source)
        if top_retrieved
        else None,
        top_retrieved_document_type=_document_type(top_retrieved[0].source)
        if top_retrieved
        else None,
        elapsed_ms=elapsed_ms,
    )


def _retrieved_chunk_payload(item: CanonicalRetrievedReference) -> dict[str, object]:
    return {
        "ref": item.canonical,
        "chunk_ref": item.chunk_ref,
        "source": item.source,
        "score": item.score,
        "text_excerpt": item.text_excerpt,
    }


def validate_matrix_report(report: Mapping[str, object]) -> MatrixContractResult:
    """Validate a generated matrix report and return stable diagnostics."""
    errors: list[str] = []
    matrix = _required_mapping(report, "matrix", "report", errors)
    required_top_k = _int_tuple(matrix.get("required_top_k")) or REQUIRED_TOP_K_VALUES
    if required_top_k != REQUIRED_TOP_K_VALUES:
        errors.append(
            f"required_top_k must be {list(REQUIRED_TOP_K_VALUES)}, got {list(required_top_k)}"
        )
    configured_rows = _configured_rows(matrix.get("configured_rows"), errors)
    if not configured_rows:
        configured_rows = {
            (cell.retriever, cell.granularity): _config_from_cell(cell).payload()
            for cell in required_matrix_cells(candidate_multiplier=_DEFAULT_CANDIDATE_MULTIPLIER)
        }
    rows = _row_mappings(matrix.get("rows"), errors)
    seen: set[tuple[str, str, int]] = set()
    claimable_signatures: dict[tuple[str, str, int], str] = {}
    report_metadata = _mapping_or_empty(report.get("metadata"))
    _validate_index_cache(report_metadata, errors)
    _validate_diagnostic_summary(report, errors)
    for row in rows:
        key = _row_key(row, errors)
        if key in seen:
            errors.append(
                f"duplicate row for retriever={key[0]} granularity={key[1]} top_k={key[2]}"
            )
        seen.add(key)
        status = row.get("status")
        if status not in {"success", "failed"}:
            errors.append(f"matrix row {key} has unsupported status {status!r}")
        if status == "success":
            _validate_row_hashes(row, report_metadata, key, errors)
        if status == "success":
            _validate_row_metrics(row, key, errors)
        configured = configured_rows.get((key[0], key[1]))
        _validate_row_retrieval_identity(row, configured, key, errors)
        _validate_claimable_signature(row, key, claimable_signatures, errors)
    _validate_per_query_reconciliation(report, rows, errors)
    _validate_thresholds(report, rows, errors)
    for retriever, granularity in configured_rows:
        errors.extend(
            f"missing row for retriever={retriever} granularity={granularity} top_k={top_k}"
            for top_k in REQUIRED_TOP_K_VALUES
            if (retriever, granularity, top_k) not in seen
        )
    unsupported = seen - {
        (retriever, granularity, top_k)
        for retriever, granularity in configured_rows
        for top_k in REQUIRED_TOP_K_VALUES
    }
    for retriever, granularity, top_k in sorted(unsupported):
        errors.append(
            f"unsupported row for retriever={retriever} granularity={granularity} top_k={top_k}"
        )
    return _contract_result(errors)


def validate_artifact_manifest(manifest: Mapping[str, object] | Path) -> MatrixContractResult:
    """Validate artifact manifest paths, sizes, and SHA-256 values."""
    errors: list[str] = []
    if isinstance(manifest, Path):
        try:
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        except OSError as exc:
            return MatrixContractResult(
                status="failed",
                errors=(f"could not read manifest: {exc}",),
            )
        if not isinstance(manifest_payload, dict):
            return MatrixContractResult(
                status="failed",
                errors=("artifact manifest must be an object",),
            )
        manifest = cast("dict[str, object]", manifest_payload)
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append("artifact manifest schema_version is unsupported")
    artifacts = manifest.get("artifacts")
    artifact_items: list[dict[str, object]] = []
    if isinstance(artifacts, dict):
        for role, raw_artifact in artifacts.items():
            if not isinstance(role, str) or not isinstance(raw_artifact, dict):
                errors.append("artifact manifest mapping entries must be objects")
                continue
            artifact = cast("dict[str, object]", raw_artifact)
            artifact.setdefault("role", role)
            artifact_items.append(artifact)
    elif isinstance(artifacts, list):
        artifact_items = [
            cast("dict[str, object]", item) for item in artifacts if isinstance(item, dict)
        ]
    else:
        errors.append("artifact manifest must contain artifacts")
        return _contract_result(errors)
    seen_roles: set[str] = set()
    for artifact in artifact_items:
        role = artifact.get("role")
        path_value = artifact.get("path")
        expected_sha = artifact.get("sha256")
        expected_size = artifact.get("size_bytes")
        if not isinstance(role, str):
            errors.append("artifact role must be a string")
            continue
        seen_roles.add(role)
        if not isinstance(path_value, str):
            errors.append(f"artifact {role} path must be a string")
            continue
        path = Path(path_value)
        if not path.is_file():
            errors.append(f"artifact {role} path does not exist: {path}")
            continue
        actual_sha = claim_report_envelope.sha256_file(path)
        if expected_sha != actual_sha:
            errors.append(f"artifact {role} sha256 mismatch")
        if expected_size != path.stat().st_size:
            errors.append(f"artifact {role} size_bytes mismatch")
    missing_roles = set(_ARTIFACT_FILENAMES) - seen_roles
    errors.extend(f"artifact manifest missing role {role}" for role in sorted(missing_roles))
    return _contract_result(errors)


def run_matrix(
    armory_path: Path,
    cases_path: Path,
    *,
    output_dir: Path,
    top_k_values: Sequence[int] = REQUIRED_TOP_K_VALUES,
    min_score: float = _DEFAULT_MIN_SCORE,
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER,
    embed_model: str | None = None,
    embed_query_prefix: str = "",
    embed_document_prefix: str = "",
    rerank_model: str | None = None,
    copy_armory: bool = False,
    dataset_id: str | None = None,
    permission_allowlist_path: Path | None = None,
    min_permission_retrieval_safety_rate: float = _DEFAULT_MIN_PERMISSION_RETRIEVAL_SAFETY_RATE,
    min_forbidden_before_expected_avoidance: float = (
        _DEFAULT_MIN_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE
    ),
    command_invocation: str,
) -> dict[str, object]:
    """Run all configured matrix rows and return the finalized JSON report."""
    resolved_armory = armory_path.expanduser().resolve()
    resolved_cases = cases_path.expanduser().resolve()
    resolved_output_dir = output_dir.expanduser().resolve()
    working_armory = _prepare_working_armory(resolved_armory, resolved_output_dir, copy_armory)
    cases = benchmark_rag.load_cases(resolved_cases)
    hashes = _input_hashes(resolved_armory, resolved_cases)
    loaded_existing_index, stale_before_run = _probe_index_cache(working_armory)
    index = load_or_build(working_armory)
    corpus = CanonicalCorpus.from_index(index)
    allowed_sources = _load_allowed_sources(permission_allowlist_path)
    index_cache = _index_cache_state(
        index,
        working_armory=working_armory,
        corpus_sha256=hashes["corpus_sha256"],
        loaded_existing_index=loaded_existing_index,
        stale_before_run=stale_before_run,
    )
    permission_scope = _permission_scope(
        corpus,
        corpus_sha256=hashes["corpus_sha256"],
        allowed_sources=allowed_sources,
        allowlist_path=permission_allowlist_path,
    )
    configs = tuple(
        _with_candidate_multiplier(config, candidate_multiplier)
        for config in default_matrix_configs()
    )
    observed = claim_report_envelope.observe_current_state()
    resolved_dataset_id = dataset_id or resolved_cases.stem
    matched_metadata = _matched_metadata(
        dataset_id=resolved_dataset_id,
        hashes=hashes,
        observed=observed,
    )
    rows: list[dict[str, object]] = []
    per_query_results: list[dict[str, object]] = []
    row_diagnostics: list[dict[str, object]] = []

    for config in configs:
        for top_k in top_k_values:
            row_id = matrix_row_id(config, top_k)
            try:
                row, row_results = _run_matrix_cell(
                    index,
                    corpus,
                    cases,
                    config=config,
                    top_k=top_k,
                    min_score=min_score,
                    embed_model=embed_model,
                    embed_query_prefix=embed_query_prefix,
                    embed_document_prefix=embed_document_prefix,
                    rerank_model=rerank_model,
                    allowed_sources=allowed_sources,
                    matched_metadata=matched_metadata,
                )
            except Exception as exc:
                row = _failed_row(config, top_k, str(exc), matched_metadata)
                row_results = []
            rows.append(row)
            per_query_results.extend(row_results)
            row_diagnostics.append(_row_diagnostics(row_id, row, row_results))

    report = _base_report(
        status="success" if all(row.get("status") == "success" for row in rows) else "partial",
        armory_path=resolved_armory,
        working_armory_path=working_armory,
        cases_path=resolved_cases,
        output_dir=resolved_output_dir,
        configs=configs,
        top_k_values=tuple(top_k_values),
        min_score=min_score,
        candidate_multiplier=candidate_multiplier,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        hashes=hashes,
        rows=rows,
        per_query_results=per_query_results,
        diagnostics=row_diagnostics,
        index_cache=index_cache,
        permission_scope=permission_scope,
        min_permission_retrieval_safety_rate=min_permission_retrieval_safety_rate,
        min_forbidden_before_expected_avoidance=min_forbidden_before_expected_avoidance,
        dataset_id=resolved_dataset_id,
    )
    finalized = claim_report_envelope.finalize_claim_report(
        report,
        command=command_invocation,
    )
    _raise_if_failed(validate_matrix_report(finalized))
    return finalized


def write_matrix_artifacts(
    report: Mapping[str, object],
    output_dir: Path,
    *,
    command_invocation: str,
    report_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, object]:
    """Write matrix report, per-query rows, diagnostics, metadata, summary, and manifest."""
    resolved_output_dir = output_dir.expanduser().resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    _raise_if_failed(validate_matrix_report(report))

    per_query_results = _list_of_mappings(report.get("per_query_results"))
    diagnostics = _list_of_mappings(report.get("diagnostics"))
    metadata = _mapping_or_empty(report.get("metadata"))
    report_path = (
        report_path.expanduser().resolve()
        if report_path is not None
        else resolved_output_dir / _ARTIFACT_FILENAMES["matrix_report"]
    )
    manifest_path = (
        manifest_path.expanduser().resolve()
        if manifest_path is not None
        else resolved_output_dir / "artifact-manifest.json"
    )
    per_query_path = resolved_output_dir / _ARTIFACT_FILENAMES["per_query_results"]
    diagnostics_path = resolved_output_dir / _ARTIFACT_FILENAMES["diagnostics"]
    metadata_path = resolved_output_dir / _ARTIFACT_FILENAMES["run_metadata"]
    summary_path = resolved_output_dir / _ARTIFACT_FILENAMES["summary"]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(report_path, report)
    per_query_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in per_query_results
        ),
        encoding="utf-8",
    )
    _write_json(
        diagnostics_path,
        {
            "rows": diagnostics,
            "summary": _mapping_or_empty(report.get("diagnostic_summary")),
        },
    )
    _write_json(metadata_path, metadata)
    summary_path.write_text(_summary_markdown(report), encoding="utf-8")

    artifact_paths = {
        "matrix_report": report_path,
        "per_query_results": per_query_path,
        "diagnostics": diagnostics_path,
        "run_metadata": metadata_path,
        "summary": summary_path,
    }
    artifacts = {role: _artifact_entry(role, path) for role, path in artifact_paths.items()}
    manifest: dict[str, object] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "command_invocation": command_invocation,
        "artifacts": artifacts,
    }
    _write_json(manifest_path, manifest)
    _raise_if_failed(validate_artifact_manifest(manifest))
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for the retrieval ablation matrix."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory)
    cases = cast("Path", args.cases)
    json_report = cast("Path | None", args.json_report)
    artifact_manifest = cast("Path | None", args.artifact_manifest)
    output_dir = _resolved_output_dir(
        cast("Path", args.output_dir),
        json_report,
        artifact_manifest,
    )
    dataset_id = _optional_cli_string(cast("str | None", args.dataset_id))
    min_score = cast("float", args.min_score)
    candidate_multiplier = cast("int", args.candidate_multiplier)
    embed_model = _optional_cli_string(cast("str | None", args.embedding_model))
    embed_query_prefix = cast("str", args.embedding_query_prefix)
    embed_document_prefix = cast("str", args.embedding_document_prefix)
    rerank_model = _optional_cli_string(cast("str | None", args.rerank_model))
    permission_allowlist = cast("Path | None", args.permission_allowlist)
    copy_armory = cast("bool", args.copy_armory)
    min_permission_safety = cast("float", args.min_permission_retrieval_safety_rate)
    min_forbidden_avoidance = cast("float", args.min_forbidden_before_expected_avoidance)
    top_k_values = _parse_top_k_values(cast("str", args.top_k_values), parser)

    if min_score < 0:
        parser.error("--min-score must be non-negative")
    if candidate_multiplier <= 0:
        parser.error("--candidate-multiplier must be positive")
    if not 0 <= min_permission_safety <= 1:
        parser.error("--min-permission-retrieval-safety-rate must be in [0, 1]")
    if not 0 <= min_forbidden_avoidance <= 1:
        parser.error("--min-forbidden-before-expected-avoidance must be in [0, 1]")

    command = claim_report_envelope.command_invocation(RUNNER_ID, list(argv or sys.argv[1:]))
    try:
        report = run_matrix(
            armory,
            cases,
            output_dir=output_dir,
            top_k_values=top_k_values,
            min_score=min_score,
            candidate_multiplier=candidate_multiplier,
            embed_model=embed_model,
            embed_query_prefix=embed_query_prefix,
            embed_document_prefix=embed_document_prefix,
            rerank_model=rerank_model,
            copy_armory=copy_armory,
            dataset_id=dataset_id,
            permission_allowlist_path=permission_allowlist,
            min_permission_retrieval_safety_rate=min_permission_safety,
            min_forbidden_before_expected_avoidance=min_forbidden_avoidance,
            command_invocation=command,
        )
        manifest = write_matrix_artifacts(
            report,
            output_dir,
            command_invocation=command,
            report_path=json_report,
            manifest_path=artifact_manifest,
        )
    except (MatrixValidationError, ReferenceResolutionError, TypeError, ValueError) as exc:
        print(f"retrieval matrix error: {exc}", file=sys.stderr)
        return 2
    manifest_path = (
        artifact_manifest.expanduser().resolve()
        if artifact_manifest is not None
        else output_dir.expanduser().resolve() / "artifact-manifest.json"
    )
    selected = _mapping_or_empty(report.get("selected_configuration"))
    matrix_payload = _mapping_or_empty(report.get("matrix"))
    rows = _list_of_mappings(matrix_payload.get("rows"))
    failed_count = sum(1 for row in rows if row.get("status") != "success")
    print(
        "retrieval_ablation_matrix "
        f"status={report.get('status')} rows={len(rows)} failed_rows={failed_count} "
        f"selected_row={selected.get('row_id')} "
        f"primary_delta_vs_baseline={selected.get('primary_metric_delta_vs_baseline')} "
        f"manifest={manifest_path}"
    )
    if manifest.get("artifacts"):
        print(f"artifact_manifest_sha256={claim_report_envelope.sha256_file(manifest_path)}")
    return 0 if failed_count == 0 else 1


def _run_matrix_cell(
    index: ArmoryIndex,
    corpus: CanonicalCorpus,
    cases: Sequence[benchmark_rag.BenchmarkCase],
    *,
    config: MatrixConfig,
    top_k: int,
    min_score: float,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
    allowed_sources: frozenset[str] | None,
    matched_metadata: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    scored_results: list[ScoredCaseResult] = []
    per_query_rows: list[dict[str, object]] = []
    cell = _cell_from_config(config)
    parameters = MatrixParameters(
        top_k_values=REQUIRED_TOP_K_VALUES,
        min_score=min_score,
        candidate_multiplier=config.candidate_multiplier,
        embedding_model=embed_model,
        embedding_query_prefix=embed_query_prefix,
        embedding_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        hybrid_sparse_weight=config.sparse_weight,
        hybrid_dense_weight=config.dense_weight,
    )
    gc_was_enabled = gc.isenabled()
    if gc_was_enabled:
        gc.disable()
    try:
        for case in cases:
            labels = canonicalize_case_labels(
                case.expected,
                case.forbidden_before_expected,
                corpus,
                granularity=config.granularity,
            )
            started = time.perf_counter()
            retrieval_top_k = _retrieval_top_k_for_config(config, top_k)
            chunks = _retrieve_ranked_chunks(
                index,
                case,
                cell,
                retrieval_top_k,
                parameters,
            )
            ranked = _ranked_references_from_chunks(chunks, config=config, top_k=top_k)
            elapsed_ms = (time.perf_counter() - started) * 1000
            scored = score_ranked_references(
                case_id=case.case_id,
                query=case.query,
                query_type=case.task or "unlabeled",
                labels=labels,
                retrieved=ranked.ranked,
                corpus=corpus,
                granularity=config.granularity,
                top_k=top_k,
                retrieval_top_k_requested=retrieval_top_k,
                raw_candidate_count=ranked.raw_candidate_count,
                candidate_retrieved_count=ranked.candidate_retrieved_count,
                duplicate_document_drop_count=ranked.duplicate_document_drop_count,
                elapsed_ms=elapsed_ms,
                allowed_sources=allowed_sources,
            )
            scored_results.append(scored)
            per_query_rows.append(_per_query_payload(config, top_k, scored))
    finally:
        if gc_was_enabled:
            gc.enable()
    row_metrics = _aggregate_metrics(scored_results, top_k=top_k)
    row: dict[str, object] = {
        "row_id": matrix_row_id(config, top_k),
        "status": "success",
        "retriever": config.retriever,
        "granularity": config.granularity.value,
        "retrieval_mode": config.retrieval_mode.value,
        "retrieval_signature": config.retrieval_signature(),
        "fusion": config.fusion_payload(),
        "top_k": top_k,
        "candidate_budget": config.candidate_budget(top_k),
        "candidate_multiplier": config.candidate_multiplier,
        "claim_eligible": config.claim_eligible(),
        "metrics": row_metrics,
        "matched_metadata": dict(matched_metadata),
        "retriever_backends": list(index.retriever_backend_names),
    }
    row.update(_row_metadata_aliases(matched_metadata))
    return row, per_query_rows


def _base_report(
    *,
    status: str,
    armory_path: Path,
    working_armory_path: Path,
    cases_path: Path,
    output_dir: Path,
    configs: Sequence[MatrixConfig],
    top_k_values: Sequence[int],
    min_score: float,
    candidate_multiplier: int,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
    hashes: Mapping[str, str],
    rows: list[dict[str, object]],
    per_query_results: list[dict[str, object]],
    diagnostics: list[dict[str, object]],
    index_cache: Mapping[str, object],
    permission_scope: Mapping[str, object],
    min_permission_retrieval_safety_rate: float,
    min_forbidden_before_expected_avoidance: float,
    dataset_id: str,
) -> dict[str, object]:
    selected = _selected_configuration(rows)
    aggregate_metrics = _selected_aggregate_metrics(selected, rows)
    baseline_delta = _baseline_delta(selected, rows)
    diagnostic_summary = _diagnostic_summary(
        rows=rows,
        per_query_results=per_query_results,
        diagnostics=diagnostics,
        index_cache=index_cache,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_id": f"retrieval-ablation-matrix:{dataset_id}",
        "status": status,
        "metadata": {
            "runner": RUNNER_ID,
            "benchmark_type": "retrieval-ablation-matrix",
            "dataset": dataset_id,
            "dataset_id": dataset_id,
            "armory_path": str(armory_path),
            "working_armory_path": str(working_armory_path),
            "cases_path": str(cases_path),
            "output_dir": str(output_dir),
            "corpus_sha256": hashes["corpus_sha256"],
            "cases_sha256": hashes["cases_sha256"],
            "labels_sha256": hashes["qrels_sha256"],
            "qrels_sha256": hashes["qrels_sha256"],
            "manifest_sha256": hashes["manifest_sha256"],
            "index_cache": dict(index_cache),
            "permission_scope": dict(permission_scope),
            "configured_top_k_values": list(top_k_values),
            "latency_scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
            "scoring_protocol_version": SCORING_PROTOCOL_VERSION,
            "timestamp_policy": "no wall-clock timestamp is included in deterministic reports",
            "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
            "metric_formulas": _metric_formulas(),
            "evaluation_plan": _evaluation_plan(),
            "fixed_parameters": {
                "top_k": _PRIMARY_TOP_K,
                "top_k_values": list(top_k_values),
                "min_score": min_score,
                "retrieval_modes": [config.payload() for config in configs],
                "candidate_multiplier": candidate_multiplier,
                "transform_strategy": TransformStrategy.IDENTITY.value,
                "query_order": "case-file-order",
                "result_order": "retrieval-rank-order",
                "selection_policy": _selection_policy(),
                "random_seed": 0,
                "randomness": "not-used",
                "network_access": "disabled-after-materialization",
                "embedding_model": _embedding_model_label(embed_model),
                "embedding_query_prefix": embed_query_prefix,
                "embedding_document_prefix": embed_document_prefix,
                "rerank_model": _rerank_model_label(rerank_model),
            },
        },
        "matrix": {
            "required_top_k": list(top_k_values),
            "configured_rows": [config.payload() for config in configs],
            "rows": rows,
        },
        "aggregate_metrics": aggregate_metrics,
        "selected_configuration": selected,
        "baseline_delta": baseline_delta,
        "per_query_results": per_query_results,
        "diagnostics": diagnostics,
        "diagnostic_summary": diagnostic_summary,
        "thresholds": {
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "primary_metric": _PRIMARY_METRIC,
            "primary_top_k": _PRIMARY_TOP_K,
            "permission_retrieval_safety_rate": min_permission_retrieval_safety_rate,
            "forbidden_before_expected_avoidance": min_forbidden_before_expected_avoidance,
        },
        "threshold_failures": [],
        "warnings": [],
        "errors": [],
    }


def _selected_configuration(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    baseline_row = _find_row(rows, "bm25", ReferenceGranularity.DOCUMENT.value, _PRIMARY_TOP_K)
    candidates = [
        row
        for row in rows
        if row.get("status") == "success"
        and row.get("top_k") == _PRIMARY_TOP_K
        and row.get("claim_eligible") is True
    ]
    if not candidates:
        return {
            "row_id": None,
            "baseline_row_id": baseline_row.get("row_id") if baseline_row else None,
            "selection_policy": _selection_policy(),
            "primary_metric": _PRIMARY_METRIC,
            "primary_top_k": _PRIMARY_TOP_K,
            "selection_top_k": _PRIMARY_TOP_K,
            "primary_metric_delta_vs_baseline": None,
            "guardrail_metric_deltas": {},
            "limitations": ["no successful claim-eligible rows at the primary top-k"],
        }
    selected = max(candidates, key=_selection_key)
    selected_metrics = _mapping_or_empty(selected.get("metrics"))
    baseline_metrics = _mapping_or_empty(baseline_row.get("metrics") if baseline_row else None)
    guardrails = {
        metric_name: _metric_delta(selected_metrics, baseline_metrics, metric_name)
        for metric_name in ("hit_rate_at_k", "mrr_at_k", "precision_at_k", "ndcg_at_k")
    }
    return {
        "row_id": selected.get("row_id"),
        "baseline_row_id": baseline_row.get("row_id") if baseline_row else None,
        "selection_policy": _selection_policy(),
        "primary_metric": _PRIMARY_METRIC,
        "primary_top_k": _PRIMARY_TOP_K,
        "selection_top_k": _PRIMARY_TOP_K,
        "primary_metric_value": selected_metrics.get(_PRIMARY_METRIC),
        "primary_metric_delta_vs_baseline": _metric_delta(
            selected_metrics,
            baseline_metrics,
            _PRIMARY_METRIC,
        ),
        "guardrail_metric_deltas": guardrails,
        "retriever": selected.get("retriever"),
        "granularity": selected.get("granularity"),
        "fusion": selected.get("fusion"),
        "top_k": selected.get("top_k"),
    }


def _baseline_delta(
    selected: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    selected_metrics = _metrics_for_row(rows, selected.get("row_id"))
    baseline_row = _find_row(rows, "bm25", ReferenceGranularity.DOCUMENT.value, 1)
    baseline_metrics = _mapping_or_empty(baseline_row.get("metrics") if baseline_row else None)
    return {
        "baseline_retriever": "bm25",
        "baseline_granularity": ReferenceGranularity.DOCUMENT.value,
        "baseline_top_k": 1,
        "comparison_top_k": _PRIMARY_TOP_K,
        "primary_metric": _PRIMARY_METRIC,
        "primary_metric_delta": _metric_delta(selected_metrics, baseline_metrics, _PRIMARY_METRIC),
        "guardrail_metric_deltas": {
            metric_name: _metric_delta(selected_metrics, baseline_metrics, metric_name)
            for metric_name in ("hit_rate_at_k", "mrr_at_k", "precision_at_k", "ndcg_at_k")
        },
    }


def _metrics_for_row(
    rows: Sequence[Mapping[str, object]],
    row_id: object,
) -> dict[str, object]:
    selected_row = next((row for row in rows if row.get("row_id") == row_id), None)
    return _mapping_or_empty(selected_row.get("metrics") if selected_row else None)


def _selected_aggregate_metrics(
    selected: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    row_id = selected.get("row_id")
    selected_row = next((row for row in rows if row.get("row_id") == row_id), None)
    metrics = _mapping_or_empty(selected_row.get("metrics") if selected_row else None)
    return {
        "hit_rate": metrics.get("hit_rate_at_k", 0.0),
        "mrr": metrics.get("mrr_at_k", 0.0),
        "expected_recall": metrics.get("recall_at_k", 0.0),
        "recall_at_k": metrics.get("recall_at_k", 0.0),
        "precision_at_k": metrics.get("precision_at_k", 0.0),
        "map_at_k": metrics.get("map_at_k", 0.0),
        "ndcg_at_k": metrics.get("ndcg_at_k", 0.0),
        "query_count": metrics.get("query_count", 0),
        "miss_count": metrics.get("miss_count", 0),
        "full_evidence_count": metrics.get("full_evidence_count", 0),
        "partial_evidence_count": metrics.get("partial_evidence_count", 0),
        "no_evidence_count": metrics.get("no_evidence_count", 0),
        "evidence_categories": metrics.get("evidence_categories", {}),
        "candidate_recall_at_budget": metrics.get("candidate_recall_at_budget", 0.0),
        "forbidden_before_expected_avoidance": metrics.get(
            "forbidden_before_expected_avoidance",
            1.0,
        ),
        "permission_retrieval_safety_rate": metrics.get(
            "permission_retrieval_safety_rate",
            1.0,
        ),
        "mean_latency_ms": metrics.get("mean_latency_ms", 0.0),
        "latency": metrics.get(
            "latency",
            {
                "mean_ms": metrics.get("mean_latency_ms", 0.0),
                "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
                "unit": "milliseconds",
            },
        ),
    }


def _diagnostic_summary(
    *,
    rows: Sequence[Mapping[str, object]],
    per_query_results: Sequence[Mapping[str, object]],
    diagnostics: Sequence[Mapping[str, object]],
    index_cache: Mapping[str, object],
) -> dict[str, object]:
    successful_rows = [row for row in rows if row.get("status") == "success"]
    return {
        "recall_at_50_100": _recall_at_50_100_summary(successful_rows),
        "source_family": _global_breakdown(
            per_query_results,
            evidence_field="source_family_evidence",
            expected_field="expected_source_families",
        ),
        "document_type": _global_breakdown(
            per_query_results,
            evidence_field="document_type_evidence",
            expected_field="expected_document_types",
        ),
        "query_type": _global_query_type_breakdown(per_query_results),
        "latency": {
            "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
            "unit": "milliseconds",
            "rows": len(successful_rows),
            "slowest_rows": _slowest_rows(successful_rows),
        },
        "evidence_categories": _global_evidence_categories(successful_rows),
        "miss_buckets": _global_miss_buckets(successful_rows),
        "top_k_reconciliation": {
            "rows_checked": len(successful_rows),
            "per_query_rows_checked": len(per_query_results),
            "non_monotonic_metric_failures": _non_monotonic_metric_failures(successful_rows),
        },
        "index_cache": dict(index_cache),
        "permission_safety": _permission_safety_summary(successful_rows),
        "optimization_targets": _optimization_targets(successful_rows, diagnostics),
    }


def _recall_at_50_100_summary(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[int, Mapping[str, object]]] = {}
    for row in rows:
        retriever = row.get("retriever")
        granularity = row.get("granularity")
        top_k = row.get("top_k")
        if not isinstance(retriever, str) or not isinstance(granularity, str):
            continue
        if not isinstance(top_k, int) or top_k not in {50, 100}:
            continue
        grouped.setdefault((retriever, granularity), {})[top_k] = row
    summary: list[dict[str, object]] = []
    for retriever, granularity in sorted(grouped):
        at_50 = grouped[(retriever, granularity)].get(50)
        at_100 = grouped[(retriever, granularity)].get(100)
        metrics_50 = _mapping_or_empty(at_50.get("metrics") if at_50 else None)
        metrics_100 = _mapping_or_empty(at_100.get("metrics") if at_100 else None)
        summary.append(
            {
                "retriever": retriever,
                "granularity": granularity,
                "row_id_at_50": at_50.get("row_id") if at_50 else None,
                "row_id_at_100": at_100.get("row_id") if at_100 else None,
                "recall_at_50": metrics_50.get("recall_at_k"),
                "recall_at_100": metrics_100.get("recall_at_k"),
                "candidate_recall_at_50": metrics_50.get("candidate_recall_at_budget"),
                "candidate_recall_at_100": metrics_100.get("candidate_recall_at_budget"),
                "query_count_at_50": metrics_50.get("query_count"),
                "miss_count_at_50": metrics_50.get("miss_count"),
                "query_count_at_100": metrics_100.get("query_count"),
                "miss_count_at_100": metrics_100.get("miss_count"),
                "candidate_recall_scope": "pre_final_candidate_list",
            }
        )
    return summary


def _global_breakdown(
    per_query_rows: Sequence[Mapping[str, object]],
    *,
    evidence_field: str,
    expected_field: str,
) -> dict[str, dict[str, float | int]]:
    return _breakdown_payload(
        per_query_rows,
        evidence_field=evidence_field,
        expected_field=expected_field,
    )


def _global_query_type_breakdown(
    per_query_rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, float | int]]:
    return _query_type_breakdown(per_query_rows)


def _slowest_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    slowest: list[dict[str, object]] = []
    for row in rows:
        metrics = _mapping_or_empty(row.get("metrics"))
        latency = _mapping_or_empty(metrics.get("latency"))
        mean_ms = latency.get("mean_ms")
        if not isinstance(mean_ms, int | float):
            continue
        slowest.append({"row_id": row.get("row_id"), "mean_ms": float(mean_ms)})
    return sorted(slowest, key=lambda item: float(item["mean_ms"]), reverse=True)[:limit]


def _global_evidence_categories(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, float | int]]:
    counts = dict.fromkeys(_EVIDENCE_CATEGORIES, 0)
    total = 0
    for row in rows:
        metrics = _mapping_or_empty(row.get("metrics"))
        query_count = metrics.get("query_count")
        if isinstance(query_count, int):
            total += query_count
        categories = _mapping_or_empty(metrics.get("evidence_categories"))
        for category in _EVIDENCE_CATEGORIES:
            payload = _mapping_or_empty(categories.get(category))
            count = payload.get("count")
            if isinstance(count, int):
                counts[category] += count
    return _evidence_category_payload(counts, total)


def _global_miss_buckets(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        metrics = _mapping_or_empty(row.get("metrics"))
        for bucket, raw_count in _mapping_or_empty(metrics.get("miss_bucket_counts")).items():
            if isinstance(bucket, str) and isinstance(raw_count, int):
                counts[bucket] = counts.get(bucket, 0) + raw_count
    return dict(sorted(counts.items()))


def _permission_safety_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    checked = 0
    violations = 0
    forbidden_cases = 0
    forbidden_failures = 0
    for row in rows:
        metrics = _mapping_or_empty(row.get("metrics"))
        checked += _int_metric(metrics, "permission_scope_checked_count")
        violations += _int_metric(metrics, "permission_violation_count")
        forbidden_cases += _int_metric(metrics, "forbidden_before_expected_case_count")
        forbidden_failures += _int_metric(metrics, "forbidden_before_expected_failure_count")
    return {
        "permission_scope_checked_count": checked,
        "permission_violation_count": violations,
        "permission_retrieval_safety_rate": (checked - violations) / checked if checked else 1.0,
        "forbidden_before_expected_case_count": forbidden_cases,
        "forbidden_before_expected_failure_count": forbidden_failures,
        "forbidden_before_expected_avoidance": (
            (forbidden_cases - forbidden_failures) / forbidden_cases if forbidden_cases else 1.0
        ),
    }


def _optimization_targets(
    rows: Sequence[Mapping[str, object]],
    diagnostics: Sequence[Mapping[str, object]],
    *,
    limit: int = 8,
) -> list[dict[str, object]]:
    row_by_id = {row.get("row_id"): row for row in rows if isinstance(row.get("row_id"), str)}
    targets: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        row_id = diagnostic.get("row_id")
        row = row_by_id.get(row_id)
        metrics = _mapping_or_empty(row.get("metrics") if row else None)
        miss_count = _int_metric(metrics, "miss_count")
        if miss_count <= 0:
            continue
        miss_buckets = _mapping_or_empty(diagnostic.get("miss_bucket_counts"))
        if miss_buckets:
            bucket, count = max(
                (
                    (bucket_name, raw_count)
                    for bucket_name, raw_count in miss_buckets.items()
                    if isinstance(bucket_name, str) and isinstance(raw_count, int)
                ),
                key=lambda item: item[1],
                default=("unknown", 0),
            )
        else:
            bucket, count = ("unknown", miss_count)
        targets.append(
            {
                "row_id": row_id,
                "miss_count": miss_count,
                "dominant_bucket": bucket,
                "dominant_bucket_count": count,
                "candidate_recall_at_budget": metrics.get("candidate_recall_at_budget"),
                "recall_at_k": metrics.get("recall_at_k"),
            }
        )
    return sorted(targets, key=lambda item: int(item["miss_count"]), reverse=True)[:limit]


def _non_monotonic_metric_failures(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    for row in rows:
        retriever = row.get("retriever")
        granularity = row.get("granularity")
        if not isinstance(retriever, str) or not isinstance(granularity, str):
            continue
        grouped.setdefault((retriever, granularity), []).append(row)
    failures: list[dict[str, object]] = []
    for (retriever, granularity), group_rows in grouped.items():
        previous: dict[str, tuple[int, float]] = {}
        for row in sorted(group_rows, key=lambda item: int(item.get("top_k", 0))):
            top_k = row.get("top_k")
            if not isinstance(top_k, int):
                continue
            metrics = _mapping_or_empty(row.get("metrics"))
            for metric_name in ("hit_rate_at_k", "recall_at_k", "candidate_recall_at_budget"):
                value = metrics.get(metric_name)
                if not isinstance(value, int | float):
                    continue
                previous_top_k, previous_value = previous.get(metric_name, (top_k, float(value)))
                if float(value) + 1e-12 < previous_value:
                    failures.append(
                        {
                            "retriever": retriever,
                            "granularity": granularity,
                            "metric": metric_name,
                            "previous_top_k": previous_top_k,
                            "previous_value": previous_value,
                            "top_k": top_k,
                            "value": float(value),
                        }
                    )
                previous[metric_name] = (top_k, max(previous_value, float(value)))
    return failures


def _selection_key(row: Mapping[str, object]) -> tuple[float, float, float, float, float, int]:
    metrics = _mapping_or_empty(row.get("metrics"))
    return (
        _float_metric(metrics, _PRIMARY_METRIC),
        _float_metric(metrics, "mrr_at_k"),
        _float_metric(metrics, "ndcg_at_k"),
        _float_metric(metrics, "precision_at_k"),
        -_float_metric(metrics, "mean_latency_ms"),
        -_mode_order(row),
    )


def _mode_order(row: Mapping[str, object]) -> int:
    retriever = row.get("retriever")
    granularity = row.get("granularity")
    if not isinstance(retriever, str) or not isinstance(granularity, str):
        return -1
    order = {
        ("bm25", "document"): 0,
        ("bm25", "chunk"): 1,
        ("dense", "document"): 2,
        ("dense", "chunk"): 3,
        ("hybrid", "document"): 4,
        ("hybrid", "chunk"): 5,
        ("rrf", "document"): 6,
        ("rrf", "chunk"): 7,
    }
    return order.get((retriever, granularity), -1)


def _find_row(
    rows: Sequence[Mapping[str, object]],
    retriever: str,
    granularity: str,
    top_k: int,
) -> Mapping[str, object] | None:
    return next(
        (
            row
            for row in rows
            if row.get("retriever") == retriever
            and row.get("granularity") == granularity
            and row.get("top_k") == top_k
            and row.get("status") == "success"
        ),
        None,
    )


def _metric_delta(
    selected_metrics: Mapping[str, object],
    baseline_metrics: Mapping[str, object],
    metric_name: str,
) -> float | None:
    if not selected_metrics or not baseline_metrics:
        return None
    selected = selected_metrics.get(metric_name)
    baseline = baseline_metrics.get(metric_name)
    if not isinstance(selected, int | float) or not isinstance(baseline, int | float):
        return None
    return float(selected) - float(baseline)


def _aggregate_metrics(
    results: Sequence[ScoredCaseResult],
    *,
    top_k: int,
) -> dict[str, object]:
    query_count = len(results)
    if not results:
        return _empty_metrics(top_k)
    category_counts = _evidence_category_counts(results)
    miss_count = query_count - category_counts[_EVIDENCE_FULL]
    reciprocal_rank_sum = sum(result.metrics.reciprocal_rank for result in results)
    recall_sum = sum(result.metrics.recall_at_k for result in results)
    candidate_recall_sum = sum(result.candidate_metrics.recall_at_k for result in results)
    precision_sum = sum(result.metrics.precision_at_k for result in results)
    average_precision_sum = sum(result.metrics.average_precision_at_k for result in results)
    ndcg_sum = sum(result.metrics.ndcg_at_k for result in results)
    latency_values = [result.elapsed_ms for result in results]
    mean_latency = sum(latency_values) / query_count
    forbidden_case_count = sum(1 for result in results if result.forbidden_count > 0)
    forbidden_failure_count = sum(
        1
        for result in results
        if result.forbidden_count > 0 and not result.forbidden_before_expected_ok
    )
    forbidden_avoidance = (
        (forbidden_case_count - forbidden_failure_count) / forbidden_case_count
        if forbidden_case_count
        else 1.0
    )
    permission_violation_count = sum(result.permission_violation_count for result in results)
    permission_safety_rate = (
        (query_count - permission_violation_count) / query_count if query_count else 1.0
    )
    category_payload = _evidence_category_payload(category_counts, query_count)
    miss_bucket_counts = _miss_bucket_counts(results)
    top_k_payload = {
        "per_query_count": query_count,
        "raw_candidate_count": sum(result.raw_candidate_count for result in results),
        "candidate_retrieved_count": sum(result.candidate_retrieved_count for result in results),
        "final_retrieved_count": sum(result.final_retrieved_count for result in results),
        "duplicate_document_drop_count": sum(
            result.duplicate_document_drop_count for result in results
        ),
        "top_k_shortfall_count": sum(result.top_k_shortfall_count for result in results),
    }
    return {
        "hit_rate_at_k": sum(1 for result in results if result.hit) / query_count,
        "recall_at_k": recall_sum / query_count,
        "candidate_recall_at_budget": candidate_recall_sum / query_count,
        "mrr_at_k": reciprocal_rank_sum / query_count,
        "map_at_k": average_precision_sum / query_count,
        "ndcg_at_k": ndcg_sum / query_count,
        "precision_at_k": precision_sum / query_count,
        "query_count": query_count,
        "miss_count": miss_count,
        "mean_latency_ms": mean_latency,
        "latency": {
            "mean_ms": mean_latency,
            "p50_ms": _percentile(latency_values, 0.50),
            "p75_ms": _percentile(latency_values, 0.75),
            "p90_ms": _percentile(latency_values, 0.90),
            "p95_ms": _percentile(latency_values, 0.95),
            "p99_ms": _percentile(latency_values, 0.99),
            "sample_count": query_count,
            "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
            "unit": "milliseconds",
        },
        "evidence_categories": category_payload,
        "full_evidence_count": category_counts[_EVIDENCE_FULL],
        "partial_evidence_count": category_counts[_EVIDENCE_PARTIAL],
        "no_evidence_count": category_counts[_EVIDENCE_NONE],
        "miss_bucket_counts": miss_bucket_counts,
        "top_k_reconciliation": top_k_payload,
        "forbidden_before_expected_case_count": forbidden_case_count,
        "forbidden_before_expected_failure_count": forbidden_failure_count,
        "forbidden_before_expected_avoidance": forbidden_avoidance,
        "permission_scope_checked_count": query_count,
        "permission_violation_count": permission_violation_count,
        "permission_retrieval_safety_rate": permission_safety_rate,
        "top_k": top_k,
    }


def _evidence_category_counts(results: Sequence[ScoredCaseResult]) -> dict[str, int]:
    counts = dict.fromkeys(_EVIDENCE_CATEGORIES, 0)
    for result in results:
        counts[result.evidence_category] = counts.get(result.evidence_category, 0) + 1
    return counts


def _evidence_category_payload(
    counts: Mapping[str, int],
    query_count: int,
) -> dict[str, dict[str, float | int]]:
    return {
        category: {
            "count": counts.get(category, 0),
            "rate": counts.get(category, 0) / query_count if query_count else 0.0,
        }
        for category in _EVIDENCE_CATEGORIES
    }


def _miss_bucket_counts(results: Sequence[ScoredCaseResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        if result.miss_bucket is None:
            continue
        counts[result.miss_bucket] = counts.get(result.miss_bucket, 0) + 1
    return counts


def _empty_metrics(top_k: int) -> dict[str, object]:
    metrics: dict[str, object] = dict.fromkeys(_METRIC_KEYS, 0.0)
    metrics.update(
        {
            "query_count": 0,
            "miss_count": 0,
            "mean_latency_ms": 0.0,
            "latency": {
                "mean_ms": 0.0,
                "p50_ms": 0.0,
                "p75_ms": 0.0,
                "p90_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "sample_count": 0,
                "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
                "unit": "milliseconds",
            },
            "candidate_recall_at_budget": 0.0,
            "evidence_categories": _evidence_category_payload(
                dict.fromkeys(_EVIDENCE_CATEGORIES, 0),
                0,
            ),
            "full_evidence_count": 0,
            "partial_evidence_count": 0,
            "no_evidence_count": 0,
            "miss_bucket_counts": {},
            "top_k_reconciliation": {
                "per_query_count": 0,
                "raw_candidate_count": 0,
                "candidate_retrieved_count": 0,
                "final_retrieved_count": 0,
                "duplicate_document_drop_count": 0,
                "top_k_shortfall_count": 0,
            },
            "forbidden_before_expected_case_count": 0,
            "forbidden_before_expected_failure_count": 0,
            "forbidden_before_expected_avoidance": 1.0,
            "permission_scope_checked_count": 0,
            "permission_violation_count": 0,
            "permission_retrieval_safety_rate": 1.0,
            "top_k": top_k,
        }
    )
    return metrics


def _rank_metrics(
    expected: Sequence[CanonicalLabel],
    retrieved: Sequence[CanonicalRetrievedReference],
    *,
    top_k: int,
) -> RankingMetrics:
    matched_expected_indices: set[int] = set()
    relevant_by_rank: list[int] = []
    for item in retrieved[:top_k]:
        match_index = next(
            (
                index
                for index, expected_ref in enumerate(expected)
                if index not in matched_expected_indices and _labels_match(expected_ref, item)
            ),
            None,
        )
        if match_index is None:
            relevant_by_rank.append(0)
            continue
        matched_expected_indices.add(match_index)
        relevant_by_rank.append(1)
    relevant_found = sum(relevant_by_rank)
    expected_count = len(expected)
    ideal_relevant_at_k = min(expected_count, top_k)
    precision_at_k = relevant_found / top_k
    recall_at_k = relevant_found / expected_count if expected_count else 0.0
    reciprocal_rank = 0.0
    precision_sum = 0.0
    cumulative_relevant = 0
    for rank, is_relevant in enumerate(relevant_by_rank, start=1):
        if not is_relevant:
            continue
        if reciprocal_rank == 0.0:
            reciprocal_rank = 1 / rank
        cumulative_relevant += 1
        precision_sum += cumulative_relevant / rank
    average_precision_at_k = precision_sum / ideal_relevant_at_k if ideal_relevant_at_k else 0.0
    dcg = sum(
        is_relevant / math.log2(rank + 1)
        for rank, is_relevant in enumerate(relevant_by_rank, start=1)
        if is_relevant
    )
    idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_relevant_at_k + 1))
    ndcg_at_k = dcg / idcg if idcg else 0.0
    return RankingMetrics(
        relevant_found=relevant_found,
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        reciprocal_rank=reciprocal_rank,
        average_precision_at_k=average_precision_at_k,
        ndcg_at_k=ndcg_at_k,
    )


def _first_label_rank(
    labels: Sequence[CanonicalLabel],
    retrieved: Sequence[CanonicalRetrievedReference],
) -> int | None:
    if not labels:
        return None
    for rank, item in enumerate(retrieved, start=1):
        if any(_labels_match(label, item) for label in labels):
            return rank
    return None


def _labels_match(label: CanonicalLabel, retrieved: CanonicalRetrievedReference) -> bool:
    if label.source_scope:
        return label.source == retrieved.source
    return label.canonical == retrieved.canonical


def _permission_violation_sources(
    retrieved: Sequence[CanonicalRetrievedReference],
    allowed_sources: frozenset[str] | None,
) -> tuple[str, ...]:
    if allowed_sources is None:
        return ()
    return tuple(sorted({item.source for item in retrieved if item.source not in allowed_sources}))


def _group_evidence(
    expected: Sequence[CanonicalLabel],
    retrieved: Sequence[CanonicalRetrievedReference],
    *,
    label_fn: Callable[[str], str],
) -> tuple[GroupEvidence, ...]:
    labels_by_group: dict[str, list[CanonicalLabel]] = {}
    for label in expected:
        labels_by_group.setdefault(label_fn(label.source), []).append(label)
    outcomes: list[GroupEvidence] = []
    for group_label, group_expected in sorted(labels_by_group.items()):
        matched_count = sum(
            1
            for expected_label in group_expected
            if any(_labels_match(expected_label, item) for item in retrieved)
        )
        outcomes.append(
            GroupEvidence(
                label=group_label,
                expected_count=len(group_expected),
                matched_count=matched_count,
                evidence_category=_evidence_category(matched_count, len(group_expected)),
            )
        )
    return tuple(outcomes)


def _forbidden_before_expected_ok(
    expected_rank: int | None,
    forbidden_rank: int | None,
) -> bool:
    if forbidden_rank is None:
        return True
    if expected_rank is None:
        return False
    return expected_rank < forbidden_rank


def _evidence_category(relevant_found: int, expected_count: int) -> str:
    if expected_count > 0 and relevant_found >= expected_count:
        return _EVIDENCE_FULL
    if relevant_found > 0:
        return _EVIDENCE_PARTIAL
    return _EVIDENCE_NONE


def _miss_bucket(
    *,
    evidence_category: str,
    forbidden_before_expected_ok: bool,
    permission_violation_count: int,
    final_retrieved_count: int,
    candidate_rank: int | None,
    top_k: int,
) -> str | None:
    if evidence_category == _EVIDENCE_FULL:
        return None
    if permission_violation_count > 0:
        return _MISS_PERMISSION_SCOPE
    if not forbidden_before_expected_ok:
        return _MISS_FORBIDDEN_ORDERING
    if evidence_category == _EVIDENCE_PARTIAL:
        return _MISS_PARTIAL
    if final_retrieved_count == 0:
        return _MISS_NO_CANDIDATES
    if candidate_rank is not None and candidate_rank > top_k:
        return _MISS_OUTSIDE_TOP_K
    return _MISS_NO_EXPECTED


def _families_from_labels(labels: Sequence[CanonicalLabel]) -> tuple[str, ...]:
    return tuple(sorted({_source_family(label.source) for label in labels}))


def _document_types_from_labels(labels: Sequence[CanonicalLabel]) -> tuple[str, ...]:
    return tuple(sorted({_document_type(label.source) for label in labels}))


def _source_family(source: str) -> str:
    source_path = _reference_source(source)
    if source_path.startswith("materials/"):
        source_path = source_path.removeprefix("materials/")
    path = Path(source_path)
    parts = path.parts
    if len(parts) > 1 and parts[0]:
        return _neutral_token(parts[0])
    stem = path.stem or source_path
    for separator in ("-", "_", "."):
        if separator in stem:
            stem = stem.split(separator, 1)[0]
            break
    return _neutral_token(stem)


def _neutral_token(value: str) -> str:
    normalized = "".join(
        char.lower() if char.isalnum() else "-"
        for char in value.strip()
        if char.isalnum() or char in {"-", "_"}
    ).strip("-")
    return normalized or "unknown"


def _document_type(source: str) -> str:
    suffix = Path(_reference_source(source)).suffix.lower().lstrip(".")
    return {
        "md": "markdown",
        "markdown": "markdown",
        "txt": "text",
        "text": "text",
        "jsonl": "jsonl",
        "json": "json",
        "csv": "csv",
        "tsv": "tsv",
        "html": "html",
        "htm": "html",
        "pdf": "pdf",
        "docx": "docx",
        "pptx": "pptx",
        "xlsx": "xlsx",
    }.get(suffix, suffix or "unknown")


def _canonical_label(
    reference: str,
    corpus: CanonicalCorpus,
    *,
    granularity: ReferenceGranularity,
) -> CanonicalLabel:
    normalized = reference.strip()
    parsed = EvidenceReference.parse(normalized)
    if parsed is not None:
        if not corpus.has_chunk(parsed.source, parsed.chunk_index):
            raise ReferenceResolutionError(f"unresolved chunk reference: {normalized}")
        if granularity == ReferenceGranularity.DOCUMENT:
            return CanonicalLabel(
                canonical=parsed.source,
                source=parsed.source,
                chunk_index=None,
                source_scope=True,
            )
        return CanonicalLabel(
            canonical=parsed.render(),
            source=parsed.source,
            chunk_index=parsed.chunk_index,
            source_scope=False,
        )
    if "#" in normalized:
        raise ReferenceResolutionError(f"unresolved malformed reference: {normalized}")
    if not corpus.has_source(normalized):
        raise ReferenceResolutionError(f"unresolved source reference: {normalized}")
    return CanonicalLabel(
        canonical=normalized,
        source=normalized,
        chunk_index=None,
        source_scope=True,
    )


def _reference_source(reference: str) -> str:
    parsed = EvidenceReference.parse(reference)
    if parsed is not None:
        return parsed.source
    return reference.split("#", 1)[0]


def _validate_label_uniqueness(labels: Sequence[CanonicalLabel], *, label: str) -> None:
    seen: set[str] = set()
    for item in labels:
        if item.canonical in seen:
            raise ReferenceResolutionError(f"{label} contains duplicate canonical reference")
        seen.add(item.canonical)
    source_scope_sources = {item.source for item in labels if item.source_scope}
    for item in labels:
        if not item.source_scope and item.source in source_scope_sources:
            raise ReferenceResolutionError(
                f"{label} contains alias-equivalent document and chunk references"
            )


def _canonicalize_retrieved(
    retrieved: Sequence[RankedReference],
    corpus: CanonicalCorpus,
    *,
    granularity: ReferenceGranularity,
) -> tuple[CanonicalRetrievedReference, ...]:
    results: list[CanonicalRetrievedReference] = []
    seen: set[str] = set()
    for item in retrieved:
        parsed = EvidenceReference.parse(item.ref)
        if parsed is None:
            if "#" in item.ref or not corpus.has_source(item.ref):
                raise ReferenceResolutionError(f"unresolved retrieved reference: {item.ref}")
            source = item.ref
            chunk_ref = item.ref
            canonical = item.ref
        else:
            if not corpus.has_chunk(parsed.source, parsed.chunk_index):
                raise ReferenceResolutionError(f"unresolved retrieved reference: {item.ref}")
            source = parsed.source
            chunk_ref = parsed.render()
            canonical = (
                parsed.source if granularity == ReferenceGranularity.DOCUMENT else chunk_ref
            )
        if canonical in seen:
            continue
        seen.add(canonical)
        results.append(
            CanonicalRetrievedReference(
                canonical=canonical,
                source=source,
                chunk_ref=chunk_ref,
                score=item.score,
                text_excerpt=item.text_excerpt,
            )
        )
    return tuple(results)


def _retrieve_for_config(
    query: str,
    index: ArmoryIndex,
    *,
    config: MatrixConfig,
    top_k: int,
    min_score: float,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
) -> list[ScoredChunk]:
    retrieval_top_k = _retrieval_top_k_for_config(config, top_k)
    return retrieve(
        query,
        index,
        top_k=retrieval_top_k,
        min_score=min_score,
        retrieval_mode=config.retrieval_mode,
        candidate_multiplier=config.candidate_multiplier,
        diversify_sources=False,
        embed_model=embed_model,
        embed_query_prefix=embed_query_prefix,
        embed_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        hybrid_sparse_weight=config.sparse_weight,
        hybrid_dense_weight=config.dense_weight,
        pseudo_feedback_docs=DEFAULT_PSEUDO_FEEDBACK_DOCS,
        pseudo_feedback_terms=DEFAULT_PSEUDO_FEEDBACK_TERMS,
        pseudo_feedback_weight=DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
    )


def _retrieval_top_k_for_config(config: MatrixConfig, top_k: int) -> int:
    if (
        config.granularity == ReferenceGranularity.DOCUMENT
        and config.retrieval_mode != RetrievalMode.BM25_DOCUMENT
    ) or config.fusion_strategy != _FUSION_NONE:
        return config.candidate_budget(top_k)
    return top_k


def _retrieve_ranked_chunks(
    index: ArmoryIndex,
    case: benchmark_rag.BenchmarkCase,
    cell: MatrixCell,
    retrieval_top_k: int,
    parameters: MatrixParameters,
) -> list[ScoredChunk]:
    """Retrieve ranked chunks for a matrix cell.

    This indirection keeps command-level tests black-box friendly: they can monkeypatch this
    function to provide deterministic ranked lists without loading optional embedding models.
    """
    _ensure_cell_backend_available(cell)
    return retrieve(
        case.query,
        index,
        top_k=retrieval_top_k,
        min_score=parameters.min_score,
        retrieval_mode=cell.retrieval_mode,
        candidate_multiplier=cell.candidate_multiplier,
        diversify_sources=False,
        embed_model=parameters.embedding_model,
        embed_query_prefix=parameters.embedding_query_prefix,
        embed_document_prefix=parameters.embedding_document_prefix,
        rerank_model=parameters.rerank_model,
        hybrid_sparse_weight=cell.hybrid_sparse_weight,
        hybrid_dense_weight=cell.hybrid_dense_weight,
        pseudo_feedback_docs=DEFAULT_PSEUDO_FEEDBACK_DOCS,
        pseudo_feedback_terms=DEFAULT_PSEUDO_FEEDBACK_TERMS,
        pseudo_feedback_weight=DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
    )


def _ranked_references_from_chunks(
    chunks: Sequence[ScoredChunk],
    *,
    config: MatrixConfig,
    top_k: int,
) -> RankedReferenceSet:
    ranked: list[RankedReference] = []
    seen_documents: set[str] = set()
    duplicate_document_drop_count = 0
    for scored_chunk in chunks:
        ref = EvidenceReference(scored_chunk.chunk.source, scored_chunk.chunk.index).render()
        if config.granularity == ReferenceGranularity.DOCUMENT:
            if scored_chunk.chunk.source in seen_documents:
                duplicate_document_drop_count += 1
                continue
            seen_documents.add(scored_chunk.chunk.source)
        ranked.append(
            RankedReference(
                ref=ref,
                score=scored_chunk.score,
                text_excerpt=_excerpt(scored_chunk.chunk.text),
            )
        )
        if len(ranked) >= max(top_k, config.candidate_budget(top_k)):
            break
    return RankedReferenceSet(
        ranked=tuple(ranked),
        raw_candidate_count=len(chunks),
        candidate_retrieved_count=len(ranked),
        duplicate_document_drop_count=duplicate_document_drop_count,
    )


def _per_query_payload(
    config: MatrixConfig,
    top_k: int,
    result: ScoredCaseResult,
) -> dict[str, object]:
    return {
        "row_id": matrix_row_id(config, top_k),
        "case_id": result.case_id,
        "query": result.query,
        "query_type": result.query_type,
        "retriever": config.retriever,
        "granularity": config.granularity.value,
        "top_k": top_k,
        "candidate_budget": config.candidate_budget(top_k),
        "retrieval_top_k_requested": result.retrieval_top_k_requested,
        "expected_count": result.expected_count,
        "forbidden_before_expected_count": result.forbidden_count,
        "retrieved": list(result.retrieved),
        "retrieved_chunks": list(result.retrieved_chunks),
        "hit": result.hit,
        "rank": result.rank,
        "candidate_rank": result.candidate_rank,
        "relevant_found": result.metrics.relevant_found,
        "candidate_relevant_found": result.candidate_metrics.relevant_found,
        "reciprocal_rank": result.metrics.reciprocal_rank,
        "recall_at_k": result.metrics.recall_at_k,
        "candidate_recall_at_budget": result.candidate_metrics.recall_at_k,
        "precision_at_k": result.metrics.precision_at_k,
        "average_precision_at_k": result.metrics.average_precision_at_k,
        "ndcg_at_k": result.metrics.ndcg_at_k,
        "evidence_category": result.evidence_category,
        "miss_bucket": result.miss_bucket,
        "raw_candidate_count": result.raw_candidate_count,
        "candidate_retrieved_count": result.candidate_retrieved_count,
        "final_retrieved_count": result.final_retrieved_count,
        "top_k_satisfied": result.top_k_satisfied,
        "top_k_shortfall_count": result.top_k_shortfall_count,
        "duplicate_document_drop_count": result.duplicate_document_drop_count,
        "first_forbidden_rank": result.first_forbidden_rank,
        "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
        "permission_violation_count": result.permission_violation_count,
        "permission_violation_sources": list(result.permission_violation_sources),
        "expected_source_families": list(result.expected_source_families),
        "source_family_evidence": _group_evidence_payload(result.source_family_evidence),
        "top_retrieved_source_family": result.top_retrieved_source_family,
        "expected_document_types": list(result.expected_document_types),
        "document_type_evidence": _group_evidence_payload(result.document_type_evidence),
        "top_retrieved_document_type": result.top_retrieved_document_type,
        "latency_ms": result.elapsed_ms,
    }


def _group_evidence_payload(outcomes: Sequence[GroupEvidence]) -> list[dict[str, object]]:
    return [
        {
            "label": outcome.label,
            "expected_count": outcome.expected_count,
            "matched_count": outcome.matched_count,
            "evidence_category": outcome.evidence_category,
        }
        for outcome in outcomes
    ]


def _breakdown_payload(
    per_query_rows: Sequence[Mapping[str, object]],
    *,
    evidence_field: str,
    expected_field: str,
) -> dict[str, dict[str, float | int]]:
    totals: dict[str, dict[str, int]] = {}
    for item in per_query_rows:
        evidence_rows = _list_of_mappings(item.get(evidence_field))
        if evidence_rows:
            _accumulate_group_evidence(totals, evidence_rows)
            continue
        _accumulate_legacy_breakdown(totals, item, expected_field=expected_field)
    return _evidence_rate_breakdown(totals)


def _accumulate_group_evidence(
    totals: dict[str, dict[str, int]],
    evidence_rows: Sequence[Mapping[str, object]],
) -> None:
    for evidence in evidence_rows:
        label = _string_value(evidence.get("label"), fallback="unknown")
        category = _string_value(evidence.get("evidence_category"), fallback=_EVIDENCE_NONE)
        expected_count = _positive_int_value(evidence.get("expected_count"))
        matched_count = _positive_int_value(evidence.get("matched_count"))
        bucket = totals.setdefault(label, _empty_group_totals())
        bucket["case_count"] += 1
        bucket["expected_count"] += expected_count
        bucket["matched_count"] += matched_count
        if matched_count > 0:
            bucket["hit_count"] += 1
        if category == _EVIDENCE_FULL:
            bucket["full_evidence_count"] += 1
        elif category == _EVIDENCE_PARTIAL:
            bucket["partial_evidence_count"] += 1
        else:
            bucket["no_evidence_count"] += 1
            bucket["miss_count"] += 1


def _accumulate_legacy_breakdown(
    totals: dict[str, dict[str, int]],
    item: Mapping[str, object],
    *,
    expected_field: str,
) -> None:
    labels = _string_list(item.get(expected_field)) or ["unknown"]
    for label in labels:
        bucket = totals.setdefault(label, _empty_group_totals())
        bucket["case_count"] += 1
        bucket["expected_count"] += 1
        if item.get("hit") is True:
            bucket["hit_count"] += 1
            bucket["matched_count"] += 1
            bucket["full_evidence_count"] += 1
        else:
            bucket["miss_count"] += 1
            bucket["no_evidence_count"] += 1


def _empty_group_totals() -> dict[str, int]:
    return {
        "case_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "expected_count": 0,
        "matched_count": 0,
        "full_evidence_count": 0,
        "partial_evidence_count": 0,
        "no_evidence_count": 0,
    }


def _query_type_breakdown(
    per_query_rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, float | int]]:
    totals: dict[str, dict[str, int]] = {}
    for item in per_query_rows:
        raw_query_type = item.get("query_type")
        query_type = raw_query_type if isinstance(raw_query_type, str) else "unlabeled"
        bucket = totals.setdefault(query_type, {"case_count": 0, "hit_count": 0, "miss_count": 0})
        bucket["case_count"] += 1
        if item.get("hit") is True:
            bucket["hit_count"] += 1
        else:
            bucket["miss_count"] += 1
    return _rate_breakdown(totals)


def _source_family_confusion(
    per_query_rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    for item in per_query_rows:
        evidence_rows = _list_of_mappings(item.get("source_family_evidence"))
        expected_families = _string_list(item.get("expected_source_families")) or ["unknown"]
        top_family = item.get("top_retrieved_source_family")
        top_label = top_family if isinstance(top_family, str) else "none"
        families = (
            tuple(_string_value(row.get("label"), fallback="unknown") for row in evidence_rows)
            if evidence_rows
            else tuple(expected_families)
        )
        matched = {
            _string_value(row.get("label"), fallback="unknown")
            for row in evidence_rows
            if _positive_int_value(row.get("matched_count")) > 0
        }
        for expected_family in families:
            key = f"{expected_family}->{top_label}"
            bucket = totals.setdefault(key, {"case_count": 0, "hit_count": 0})
            bucket["case_count"] += 1
            if expected_family in matched or (not evidence_rows and item.get("hit") is True):
                bucket["hit_count"] += 1
    return dict(sorted(totals.items()))


def _rate_breakdown(
    totals: Mapping[str, Mapping[str, int]],
) -> dict[str, dict[str, float | int]]:
    payload: dict[str, dict[str, float | int]] = {}
    for label, counts in sorted(totals.items()):
        case_count = counts.get("case_count", 0)
        hit_count = counts.get("hit_count", 0)
        miss_count = counts.get("miss_count", 0)
        payload[label] = {
            "case_count": case_count,
            "hit_count": hit_count,
            "miss_count": miss_count,
            "hit_rate": hit_count / case_count if case_count else 0.0,
            "miss_rate": miss_count / case_count if case_count else 0.0,
        }
    return payload


def _evidence_rate_breakdown(
    totals: Mapping[str, Mapping[str, int]],
) -> dict[str, dict[str, float | int]]:
    payload: dict[str, dict[str, float | int]] = {}
    for label, counts in sorted(totals.items()):
        case_count = counts.get("case_count", 0)
        expected_count = counts.get("expected_count", 0)
        matched_count = counts.get("matched_count", 0)
        full_count = counts.get("full_evidence_count", 0)
        partial_count = counts.get("partial_evidence_count", 0)
        no_count = counts.get("no_evidence_count", 0)
        payload[label] = {
            "case_count": case_count,
            "hit_count": counts.get("hit_count", 0),
            "miss_count": counts.get("miss_count", 0),
            "expected_count": expected_count,
            "matched_count": matched_count,
            "hit_rate": counts.get("hit_count", 0) / case_count if case_count else 0.0,
            "miss_rate": counts.get("miss_count", 0) / case_count if case_count else 0.0,
            "expected_recall": matched_count / expected_count if expected_count else 0.0,
            "full_evidence_count": full_count,
            "partial_evidence_count": partial_count,
            "no_evidence_count": no_count,
            "full_evidence_rate": full_count / case_count if case_count else 0.0,
            "partial_evidence_rate": partial_count / case_count if case_count else 0.0,
            "no_evidence_rate": no_count / case_count if case_count else 0.0,
        }
    return payload


def _candidate_recall_scope(row: Mapping[str, object]) -> str:
    top_k = row.get("top_k")
    candidate_budget = row.get("candidate_budget")
    if isinstance(top_k, int) and isinstance(candidate_budget, int) and candidate_budget > top_k:
        return "pre_final_candidate_list"
    return "final_ranked_list"


def _row_diagnostics(
    row_id: str,
    row: Mapping[str, object],
    per_query_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    metrics = _mapping_or_empty(row.get("metrics"))
    misses = [
        {
            "case_id": item.get("case_id"),
            "bucket": item.get("miss_bucket") or _MISS_NO_EXPECTED,
            "retrieved_count": len(_object_list(item.get("retrieved"))),
            "candidate_rank": item.get("candidate_rank"),
            "top_k": item.get("top_k"),
            "top_retrieved": _object_list(item.get("retrieved"))[:3],
        }
        for item in per_query_rows
        if item.get("evidence_category") != _EVIDENCE_FULL
    ]
    return {
        "row_id": row_id,
        "status": row.get("status"),
        "query_count": metrics.get("query_count", len(per_query_rows)),
        "miss_count": len(misses),
        "miss_bucket_counts": _mapping_or_empty(metrics.get("miss_bucket_counts")),
        "evidence_categories": _mapping_or_empty(metrics.get("evidence_categories")),
        "source_family_breakdown": _breakdown_payload(
            per_query_rows,
            evidence_field="source_family_evidence",
            expected_field="expected_source_families",
        ),
        "document_type_breakdown": _breakdown_payload(
            per_query_rows,
            evidence_field="document_type_evidence",
            expected_field="expected_document_types",
        ),
        "query_type_breakdown": _query_type_breakdown(per_query_rows),
        "source_family_confusion": _source_family_confusion(per_query_rows),
        "latency": metrics.get("latency"),
        "top_k_reconciliation": metrics.get("top_k_reconciliation"),
        "permission_safety": {
            "permission_violation_count": metrics.get("permission_violation_count", 0),
            "permission_retrieval_safety_rate": metrics.get(
                "permission_retrieval_safety_rate",
                1.0,
            ),
            "forbidden_before_expected_case_count": metrics.get(
                "forbidden_before_expected_case_count",
                0,
            ),
            "forbidden_before_expected_failure_count": metrics.get(
                "forbidden_before_expected_failure_count",
                0,
            ),
            "forbidden_before_expected_avoidance": metrics.get(
                "forbidden_before_expected_avoidance",
                1.0,
            ),
        },
        "recall_diagnostics": {
            "top_k": row.get("top_k"),
            "recall_at_k": metrics.get("recall_at_k"),
            "candidate_recall_at_budget": metrics.get("candidate_recall_at_budget"),
            "candidate_recall_scope": _candidate_recall_scope(row),
        },
        "misses": misses,
        "failure": row.get("failure"),
    }


def _failed_row(
    config: MatrixConfig,
    top_k: int,
    message: str,
    matched_metadata: Mapping[str, object],
) -> dict[str, object]:
    return {
        "row_id": matrix_row_id(config, top_k),
        "status": "failed",
        "retriever": config.retriever,
        "granularity": config.granularity.value,
        "retrieval_mode": config.retrieval_mode.value,
        "retrieval_signature": config.retrieval_signature(),
        "fusion": config.fusion_payload(),
        "top_k": top_k,
        "candidate_budget": config.candidate_budget(top_k),
        "candidate_multiplier": config.candidate_multiplier,
        "claim_eligible": False,
        "metrics": _empty_metrics(top_k),
        "matched_metadata": dict(matched_metadata),
        "failure": {"message": message},
        **_row_metadata_aliases(matched_metadata),
    }


def _ensure_backend_available(config: MatrixConfig) -> None:
    if (
        config.retriever
        in {
            "dense",
            "hybrid",
            "rrf",
        }
        and not optional_backends.sentence_transformers_available()
    ):
        raise RuntimeError("sentence-transformers backend unavailable for dense retrieval")


def _ensure_cell_backend_available(cell: MatrixCell) -> None:
    if (
        cell.retriever
        in {
            "dense",
            "hybrid",
            "rrf",
        }
        and not optional_backends.sentence_transformers_available()
    ):
        raise RuntimeError("sentence-transformers backend unavailable for dense retrieval")


def _prepare_working_armory(armory_path: Path, output_dir: Path, copy_armory: bool) -> Path:
    if not copy_armory:
        return armory_path
    destination = output_dir / "working-armory"
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(armory_path, destination)
    return destination.resolve()


def _input_hashes(armory_path: Path, cases_path: Path) -> dict[str, str]:
    materials_path = armory_path / storage.MATERIALS_DIR
    cases_sha = claim_report_envelope.sha256_file(cases_path)
    return {
        "corpus_sha256": claim_report_envelope.sha256_directory(materials_path),
        "cases_sha256": cases_sha,
        "qrels_sha256": cases_sha,
        "manifest_sha256": cases_sha,
    }


def _probe_index_cache(working_armory: Path) -> tuple[bool, bool]:
    probe = ArmoryIndex(working_armory)
    loaded = probe.load(allow_stale=True)
    return loaded, not loaded or probe.is_stale()


def _index_cache_state(
    index: ArmoryIndex,
    *,
    working_armory: Path,
    corpus_sha256: str,
    loaded_existing_index: bool,
    stale_before_run: bool,
) -> dict[str, object]:
    index_path = working_armory / ".hephaistos" / "rag_index.json"
    fresh_for_scored_corpus = not index.is_stale()
    cache_artifacts: list[dict[str, object]] = []
    if index_path.is_file():
        cache_artifacts.append(
            {
                "role": "rag_index",
                "path": str(index_path),
                "sha256": claim_report_envelope.sha256_file(index_path),
                "size_bytes": index_path.stat().st_size,
            }
        )
    return {
        "index_path": str(index_path),
        "index_identity": index.content_hash,
        "index_build_or_refresh_command": f"uv run heph index {working_armory}",
        "scored_corpus_sha256": corpus_sha256,
        "indexed_corpus_sha256": corpus_sha256,
        "fresh_for_scored_corpus": fresh_for_scored_corpus,
        "cache_state": "rebuilt_fresh" if stale_before_run else "warm_reused",
        "loaded_existing_index": loaded_existing_index,
        "stale_before_run": stale_before_run,
        "rebuilt_during_run": stale_before_run,
        "document_count": len(index.documents),
        "chunk_count": index.chunk_count,
        "cache_artifacts": cache_artifacts,
    }


def _load_allowed_sources(path: Path | None) -> frozenset[str] | None:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    raw_text = resolved.read_text(encoding="utf-8")
    stripped = raw_text.strip()
    if not stripped:
        return frozenset()
    if stripped[0] in {"[", "{"}:
        payload = json.loads(stripped)
        return frozenset(_source_entries_from_json(payload))
    sources: set[str] = set()
    for line in raw_text.splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if entry.startswith("{"):
            sources.update(_source_entries_from_json(json.loads(entry)))
        else:
            sources.add(_reference_source(entry))
    return frozenset(sorted(sources))


def _source_entries_from_json(payload: object) -> tuple[str, ...]:
    if isinstance(payload, list):
        return tuple(
            entry
            for item in payload
            if item is not None
            if (entry := _source_entry_from_json_item(item))
        )
    if isinstance(payload, dict):
        for field_name in ("allowed_sources", "sources"):
            sources = payload.get(field_name)
            if isinstance(sources, list):
                return tuple(
                    entry
                    for item in sources
                    if item is not None
                    if (entry := _source_entry_from_json_item(item))
                )
        source = payload.get("source")
        if isinstance(source, str):
            normalized = _reference_source(source.strip())
            return (normalized,) if normalized else ()
    return ()


def _source_entry_from_json_item(item: object) -> str:
    if isinstance(item, str):
        return _reference_source(item.strip())
    if isinstance(item, dict):
        source = item.get("source")
        if isinstance(source, str):
            return _reference_source(source.strip())
    return ""


def _permission_scope(
    corpus: CanonicalCorpus,
    *,
    corpus_sha256: str,
    allowed_sources: frozenset[str] | None,
    allowlist_path: Path | None,
) -> dict[str, object]:
    sources = sorted(corpus.source_to_chunks)
    effective_allowed_sources = sorted(allowed_sources) if allowed_sources is not None else sources
    scope_hash = hashlib.sha256(
        json.dumps(effective_allowed_sources, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    out_of_scope = sorted(set(sources) - set(effective_allowed_sources))
    return {
        "scope": "explicit_allowlist" if allowed_sources is not None else "indexed_materials",
        "scope_hash": scope_hash,
        "corpus_sha256": corpus_sha256,
        "allowlist_path": str(allowlist_path.expanduser().resolve())
        if allowlist_path is not None
        else None,
        "explicit": allowed_sources is not None,
        "allowed_source_count": len(effective_allowed_sources),
        "indexed_source_count": len(sources),
        "out_of_scope_indexed_source_count": len(out_of_scope),
        "policy": (
            "retrieved source paths must be in the explicit allowlist"
            if allowed_sources is not None
            else "hidden, ignored, symlinked, and outside-material paths are excluded"
        ),
    }


def _matched_metadata(
    *,
    dataset_id: str,
    hashes: Mapping[str, str],
    observed: Mapping[str, object],
) -> dict[str, object]:
    git = _mapping_or_empty(observed.get("git"))
    return {
        "dataset_id": dataset_id,
        "corpus_sha256": hashes["corpus_sha256"],
        "cases_sha256": hashes["cases_sha256"],
        "case_hash": hashes["cases_sha256"],
        "qrels_sha256": hashes["qrels_sha256"],
        "label_hash": hashes["qrels_sha256"],
        "manifest_sha256": hashes["manifest_sha256"],
        "scoring_protocol_version": SCORING_PROTOCOL_VERSION,
        "git_commit": git.get("commit"),
        "dependency_lock_sha256": observed.get("uv_lock_sha256"),
    }


def _row_metadata_aliases(matched_metadata: Mapping[str, object]) -> dict[str, object]:
    return {
        "dataset_id": matched_metadata.get("dataset_id"),
        "corpus_sha256": matched_metadata.get("corpus_sha256"),
        "cases_sha256": matched_metadata.get("cases_sha256"),
        "labels_sha256": matched_metadata.get("label_hash"),
        "manifest_sha256": matched_metadata.get("manifest_sha256"),
        "scoring_protocol_version": matched_metadata.get("scoring_protocol_version"),
        "git_commit": matched_metadata.get("git_commit"),
        "dependency_lock_sha256": matched_metadata.get("dependency_lock_sha256"),
    }


def _matched_metadata_fields() -> tuple[str, ...]:
    return (
        "dataset_id",
        "corpus_sha256",
        "cases_sha256",
        "case_hash",
        "qrels_sha256",
        "label_hash",
        "manifest_sha256",
        "scoring_protocol_version",
        "git_commit",
        "dependency_lock_sha256",
    )


def _with_candidate_multiplier(config: MatrixConfig, candidate_multiplier: int) -> MatrixConfig:
    return MatrixConfig(
        retriever=config.retriever,
        granularity=config.granularity,
        retrieval_mode=config.retrieval_mode,
        fusion_strategy=config.fusion_strategy,
        candidate_multiplier=candidate_multiplier,
        sparse_weight=config.sparse_weight,
        dense_weight=config.dense_weight,
    )


def _metric_formulas() -> dict[str, str]:
    return {
        "hit_rate_at_k": "fraction of queries with any canonical expected reference retrieved",
        "recall_at_k": "mean canonical expected references found divided by expected count",
        "mrr_at_k": "mean reciprocal rank of first canonical expected reference",
        "map_at_k": "mean average precision over canonical expected references",
        "ndcg_at_k": "mean binary nDCG over canonical expected references",
        "precision_at_k": "mean canonical precision@k with top-k as denominator",
        "latency": "retrieval-only wall-clock milliseconds per query",
    }


def _evaluation_plan() -> dict[str, object]:
    return {
        "primary_target": "enterprise-rag-bench retrieval matrix",
        "primary_metric": _PRIMARY_METRIC,
        "primary_top_k": _PRIMARY_TOP_K,
        "secondary_metrics": ["mrr_at_k", "ndcg_at_k", "precision_at_k", "hit_rate_at_k"],
        "top_k_values": list(REQUIRED_TOP_K_VALUES),
        "mode_selection_policy": _selection_policy(),
        "failure_handling": "every configured row is represented with success or failed status",
    }


def _selection_policy() -> dict[str, object]:
    return {
        "eligible_rows": "successful rows at k=50 with matched corpus/case/label hashes",
        "maximize": _PRIMARY_METRIC,
        "tie_breakers": ["mrr_at_k", "ndcg_at_k", "precision_at_k", "lower_mean_latency_ms"],
        "baseline_row": "bm25:document:k=50",
        "cherry_picking_guard": "selection uses this policy before inspecting row outcomes",
    }


def _summary_markdown(report: Mapping[str, object]) -> str:
    selected = _mapping_or_empty(report.get("selected_configuration"))
    matrix_payload = _mapping_or_empty(report.get("matrix"))
    rows = _list_of_mappings(matrix_payload.get("rows"))
    failed = [row for row in rows if row.get("status") != "success"]
    return "\n".join(
        [
            "# Retrieval Ablation Matrix",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Rows: `{len(rows)}`",
            f"- Failed rows: `{len(failed)}`",
            f"- Selected row by primary metric policy: `{selected.get('row_id')}`",
            f"- Baseline row: `{selected.get('baseline_row_id')}`",
            (
                "- Primary metric delta vs baseline: "
                f"`{selected.get('primary_metric_delta_vs_baseline')}`"
            ),
            "",
            "This is an internal Hephaistos-only retrieval matrix, not a head-to-head claim.",
            "",
        ]
    )


def _artifact_entry(role: str, path: Path) -> dict[str, object]:
    return {
        "role": role,
        "path": str(path),
        "sha256": claim_report_envelope.sha256_file(path),
        "size_bytes": path.stat().st_size,
        "schema_version": SCHEMA_VERSION if role == "matrix_report" else None,
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("cases", type=Path, help="JSON or JSONL labelled retrieval cases")
    parser.add_argument("--dataset-id", help="Stable dataset id to record in matrix metadata")
    parser.add_argument("--json-report", type=Path, help="Path for the matrix JSON report")
    parser.add_argument(
        "--artifact-manifest",
        type=Path,
        help="Path for the artifact manifest JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".artifacts/benchmarks/retrieval-ablation-matrix"),
        help="Directory for generated private matrix artifacts",
    )
    parser.add_argument("--top-k-values", default=",".join(str(k) for k in REQUIRED_TOP_K_VALUES))
    parser.add_argument("--min-score", type=float, default=_DEFAULT_MIN_SCORE)
    parser.add_argument("--candidate-multiplier", type=int, default=_DEFAULT_CANDIDATE_MULTIPLIER)
    parser.add_argument(
        "--min-permission-retrieval-safety-rate",
        type=float,
        default=_DEFAULT_MIN_PERMISSION_RETRIEVAL_SAFETY_RATE,
    )
    parser.add_argument(
        "--min-forbidden-before-expected-avoidance",
        type=float,
        default=_DEFAULT_MIN_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE,
    )
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-query-prefix", default="")
    parser.add_argument("--embedding-document-prefix", default="")
    parser.add_argument("--rerank-model")
    parser.add_argument(
        "--permission-allowlist",
        type=Path,
        help="JSON, JSONL, or text file listing source paths allowed in retrieved results",
    )
    parser.add_argument(
        "--copy-armory",
        action="store_true",
        help="Run against a copy under output-dir to keep source fixtures free of new caches",
    )
    return parser


def _parse_top_k_values(raw: str, parser: argparse.ArgumentParser) -> tuple[int, ...]:
    try:
        values = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    except ValueError:
        parser.error("--top-k-values must be comma-separated integers")
    if values != REQUIRED_TOP_K_VALUES:
        required = ",".join(str(k) for k in REQUIRED_TOP_K_VALUES)
        parser.error(f"--top-k-values must be exactly {required}")
    return values


def _configured_rows(value: object, errors: list[str]) -> dict[tuple[str, str], dict[str, object]]:
    if value is None:
        return {}
    if not isinstance(value, list):
        errors.append("matrix configured_rows must be a list")
        return {}
    rows: dict[tuple[str, str], dict[str, object]] = {}
    for item in value:
        if not isinstance(item, dict):
            errors.append("matrix configured_rows entries must be objects")
            continue
        row = cast("dict[str, object]", item)
        retriever = row.get("retriever")
        granularity = row.get("granularity")
        if not isinstance(retriever, str) or not isinstance(granularity, str):
            errors.append("configured row missing retriever or granularity")
            continue
        key = (retriever, granularity)
        if key in rows:
            errors.append(
                f"duplicate configured row for retriever={retriever} granularity={granularity}"
            )
        rows[key] = row
    return rows


def _row_mappings(value: object, errors: list[str]) -> list[dict[str, object]]:
    if not isinstance(value, list):
        errors.append("matrix rows must be a list")
        return []
    rows: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            errors.append("matrix row entries must be objects")
            continue
        rows.append(cast("dict[str, object]", item))
    return rows


def _row_key(row: Mapping[str, object], errors: list[str]) -> tuple[str, str, int]:
    retriever = row.get("retriever")
    granularity = row.get("granularity")
    top_k = row.get("top_k")
    if not isinstance(retriever, str):
        errors.append("row missing retriever")
        retriever = ""
    if not isinstance(granularity, str):
        errors.append("row missing granularity")
        granularity = ""
    if not isinstance(top_k, int):
        errors.append("row missing integer top_k")
        top_k = -1
    return retriever, granularity, top_k


def _validate_row_retrieval_identity(
    row: Mapping[str, object],
    configured: Mapping[str, object] | None,
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    expected_mode, expected_strategy = _expected_retrieval_identity(key[0], key[1])
    row_mode = row.get("retrieval_mode")
    if row_mode != expected_mode:
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} retrieval_mode must be {expected_mode!r}")
    row_fusion = _mapping_or_empty(row.get("fusion"))
    if not row_fusion:
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} missing fusion metadata")
    row_strategy = row_fusion.get("strategy")
    if row_strategy != expected_strategy:
        errors.append(
            f"row {key[0]}:{key[1]}:k={key[2]} fusion strategy must be {expected_strategy!r}"
        )
    _validate_expected_fusion_weights(row_fusion, key, errors)
    _validate_claim_eligibility_payload(
        row.get("claim_eligible"),
        row_fusion,
        label=f"row {key[0]}:{key[1]}:k={key[2]}",
        errors=errors,
    )
    _validate_configured_retrieval_identity(row, configured, key, errors)


def _expected_retrieval_identity(retriever: str, granularity: str) -> tuple[str, str]:
    if retriever == "bm25" and granularity == ReferenceGranularity.DOCUMENT.value:
        return RetrievalMode.BM25_DOCUMENT.value, _FUSION_NONE
    if retriever == "bm25":
        return RetrievalMode.BM25.value, _FUSION_NONE
    if retriever == "dense":
        return RetrievalMode.DENSE.value, _FUSION_NONE
    if retriever == "hybrid":
        return RetrievalMode.HYBRID.value, _FUSION_WEIGHTED_HYBRID
    if retriever == "rrf":
        return RetrievalMode.HYBRID.value, _FUSION_RRF
    return "", _FUSION_NONE


def _validate_expected_fusion_weights(
    fusion: Mapping[str, object],
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    if not fusion:
        return
    retriever = key[0]
    if retriever == "rrf" and not _fusion_weights_match(
        fusion,
        sparse_weight=_UNWEIGHTED_RRF_WEIGHT,
        dense_weight=_UNWEIGHTED_RRF_WEIGHT,
    ):
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} rrf fusion must be unweighted")


def _validate_configured_retrieval_identity(
    row: Mapping[str, object],
    configured: Mapping[str, object] | None,
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    if configured is None:
        return
    configured_mode = configured.get("retrieval_mode")
    row_mode = row.get("retrieval_mode")
    if row_mode != configured_mode:
        errors.append(
            f"row {key[0]}:{key[1]}:k={key[2]} retrieval_mode does not match configured row"
        )
    configured_fusion = _mapping_or_empty(configured.get("fusion"))
    row_fusion = _mapping_or_empty(row.get("fusion"))
    _validate_configured_fusion(configured_fusion, row_fusion, key, errors)
    configured_signature = _configured_retrieval_signature(configured)
    row_signature = row.get("retrieval_signature")
    if row_signature != configured_signature:
        errors.append(
            f"row {key[0]}:{key[1]}:k={key[2]} retrieval_signature does not match configured row"
        )
    configured_claim_eligible = configured.get("claim_eligible")
    row_claim_eligible = row.get("claim_eligible")
    if (
        isinstance(configured_claim_eligible, bool)
        and row_claim_eligible != configured_claim_eligible
    ):
        errors.append(
            f"row {key[0]}:{key[1]}:k={key[2]} claim_eligible does not match configured row"
        )
    _validate_claim_eligibility_payload(
        configured_claim_eligible,
        configured_fusion,
        label=f"configured row {key[0]}:{key[1]}",
        errors=errors,
    )


def _validate_configured_fusion(
    configured_fusion: Mapping[str, object],
    row_fusion: Mapping[str, object],
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    if not configured_fusion or not row_fusion:
        return
    errors.extend(
        f"row {key[0]}:{key[1]}:k={key[2]} fusion {field_name} does not match configured row"
        for field_name in ("strategy", "algorithm", "canonical_id")
        if row_fusion.get(field_name) != configured_fusion.get(field_name)
    )
    for field_name in ("sparse_weight", "dense_weight"):
        row_value = row_fusion.get(field_name)
        configured_value = configured_fusion.get(field_name)
        if not isinstance(row_value, int | float) or not isinstance(
            configured_value,
            int | float,
        ):
            errors.append(f"row {key[0]}:{key[1]}:k={key[2]} fusion {field_name} must be numeric")
            continue
        if not math.isclose(float(row_value), float(configured_value), rel_tol=0.0, abs_tol=1e-12):
            errors.append(
                f"row {key[0]}:{key[1]}:k={key[2]} fusion {field_name} "
                "does not match configured row"
            )


def _configured_retrieval_signature(configured: Mapping[str, object]) -> str:
    configured_signature = configured.get("retrieval_signature")
    if isinstance(configured_signature, str):
        return configured_signature
    mode = _string_value(configured.get("retrieval_mode"), fallback="")
    return _retrieval_signature(mode, _mapping_or_empty(configured.get("fusion")))


def _fusion_weights_match(
    fusion: Mapping[str, object],
    *,
    sparse_weight: float,
    dense_weight: float,
) -> bool:
    actual_sparse = fusion.get("sparse_weight")
    actual_dense = fusion.get("dense_weight")
    if not isinstance(actual_sparse, int | float) or not isinstance(actual_dense, int | float):
        return False
    return _weights_match(
        float(actual_sparse),
        float(actual_dense),
        sparse_weight=sparse_weight,
        dense_weight=dense_weight,
    )


def _validate_claim_eligibility_payload(
    claim_eligible: object,
    fusion: Mapping[str, object],
    *,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(claim_eligible, bool):
        errors.append(f"{label} claim_eligible must be a boolean")
        return
    if claim_eligible and _is_unweighted_weighted_hybrid(fusion):
        errors.append(f"{label} unweighted weighted-hybrid row must not be claim_eligible")


def _is_unweighted_weighted_hybrid(fusion: Mapping[str, object]) -> bool:
    return fusion.get("strategy") == _FUSION_WEIGHTED_HYBRID and _fusion_weights_match(
        fusion,
        sparse_weight=_UNWEIGHTED_RRF_WEIGHT,
        dense_weight=_UNWEIGHTED_RRF_WEIGHT,
    )


def _validate_claimable_signature(
    row: Mapping[str, object],
    key: tuple[str, str, int],
    claimable_signatures: dict[tuple[str, str, int], str],
    errors: list[str],
) -> None:
    if row.get("status") != "success" or row.get("claim_eligible") is not True:
        return
    row_signature = row.get("retrieval_signature")
    if not isinstance(row_signature, str):
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} missing retrieval_signature")
        return
    signature_key = (key[1], row_signature, key[2])
    row_id = _string_value(row.get("row_id"), fallback=f"{key[0]}:{key[1]}:k={key[2]}")
    existing = claimable_signatures.get(signature_key)
    if existing is not None and existing != row_id:
        errors.append(
            f"claim-eligible rows {existing} and {row_id} share retrieval_signature "
            f"{row_signature}"
        )
        return
    claimable_signatures[signature_key] = row_id


def _validate_index_cache(report_metadata: Mapping[str, object], errors: list[str]) -> None:
    index_cache = _required_mapping(report_metadata, "index_cache", "metadata", errors)
    if not index_cache:
        return
    if index_cache.get("fresh_for_scored_corpus") is not True:
        errors.append("index cache is not fresh for scored corpus")
    corpus_sha = report_metadata.get("corpus_sha256")
    scored_sha = index_cache.get("scored_corpus_sha256")
    indexed_sha = index_cache.get("indexed_corpus_sha256")
    if corpus_sha is not None and scored_sha != corpus_sha:
        errors.append("index cache scored_corpus_sha256 does not match metadata corpus_sha256")
    if scored_sha is not None and indexed_sha != scored_sha:
        errors.append("index cache indexed corpus does not match scored corpus")


def _validate_diagnostic_summary(report: Mapping[str, object], errors: list[str]) -> None:
    summary = _required_mapping(report, "diagnostic_summary", "report", errors)
    if not summary:
        return
    required_fields = (
        "recall_at_50_100",
        "source_family",
        "document_type",
        "query_type",
        "latency",
        "evidence_categories",
        "top_k_reconciliation",
        "index_cache",
        "permission_safety",
        "optimization_targets",
    )
    errors.extend(
        f"diagnostic_summary missing {field_name}"
        for field_name in required_fields
        if field_name not in summary
    )
    recall_rows = summary.get("recall_at_50_100")
    if isinstance(recall_rows, list) and len(recall_rows) < len(required_matrix_cells()):
        errors.append("diagnostic_summary recall_at_50_100 missing matrix combinations")


def _validate_row_metrics(
    row: Mapping[str, object],
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    metrics = _required_mapping(row, "metrics", "row", errors)
    query_count = metrics.get("query_count")
    miss_count = metrics.get("miss_count")
    if not isinstance(query_count, int) or query_count < 0:
        errors.append(f"row {key} metric query_count must be a non-negative integer")
    if not isinstance(miss_count, int) or miss_count < 0:
        errors.append(f"row {key} metric miss_count must be a non-negative integer")
    if isinstance(query_count, int) and isinstance(miss_count, int) and miss_count > query_count:
        errors.append(f"row {key} miss_count exceeds query_count")
    for metric_name in (*_METRIC_KEYS, "hit_rate", "recall", "mrr", "map", "ndcg", "precision"):
        value = metrics.get(metric_name)
        if value is None:
            if metric_name in _METRIC_KEYS:
                errors.append(f"row {key} metric {metric_name} missing")
            continue
        if not isinstance(value, int | float) or not 0 <= float(value) <= 1:
            errors.append(f"metric {metric_name} outside [0, 1]")
    _validate_latency(metrics.get("latency"), key, errors)
    if isinstance(query_count, int):
        _validate_evidence_categories(metrics, key, query_count, errors)
        _validate_miss_buckets(metrics, key, errors)
    permission_violations = metrics.get("permission_violation_count")
    if isinstance(permission_violations, int) and permission_violations > 0:
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} permission violation count is nonzero")


def _validate_latency(
    value: object,
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"row {key} metric latency missing")
        return
    latency = cast("dict[str, object]", value)
    if latency.get("scope") != claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY:
        errors.append(f"row {key} latency scope must be retrieval-only")
    if latency.get("unit") != "milliseconds":
        errors.append(f"row {key} latency unit must be milliseconds")
    for field_name in ("mean_ms", "p50_ms", "p75_ms", "p90_ms", "p95_ms", "p99_ms"):
        raw_value = latency.get(field_name)
        if not isinstance(raw_value, int | float) or float(raw_value) < 0:
            errors.append(f"row {key} latency {field_name} must be a non-negative number")
    sample_count = latency.get("sample_count")
    if not isinstance(sample_count, int) or sample_count < 0:
        errors.append(f"row {key} latency sample_count must be a non-negative integer")


def _validate_evidence_categories(
    metrics: Mapping[str, object],
    key: tuple[str, str, int],
    query_count: int,
    errors: list[str],
) -> None:
    categories = _required_mapping(metrics, "evidence_categories", "metrics", errors)
    if not categories:
        return
    count_total = 0
    rate_total = 0.0
    for category in _EVIDENCE_CATEGORIES:
        payload = _mapping_or_empty(categories.get(category))
        count = payload.get("count")
        rate = payload.get("rate")
        if not isinstance(count, int) or count < 0:
            errors.append(f"row {key} evidence_categories {category} count invalid")
            continue
        if not isinstance(rate, int | float) or not 0 <= float(rate) <= 1:
            errors.append(f"row {key} evidence_categories {category} rate invalid")
            continue
        count_total += count
        rate_total += float(rate)
    if count_total != query_count:
        errors.append(f"row {key} evidence_categories counts do not sum to query_count")
    if query_count and not math.isclose(rate_total, 1.0, rel_tol=0.0, abs_tol=1e-6):
        errors.append(f"row {key} evidence_categories rates do not sum to 1.0")
    full_count = _category_count(categories, _EVIDENCE_FULL)
    partial_count = _category_count(categories, _EVIDENCE_PARTIAL)
    no_count = _category_count(categories, _EVIDENCE_NONE)
    if metrics.get("full_evidence_count") != full_count:
        errors.append(f"row {key} full_evidence_count does not match evidence_categories")
    if metrics.get("partial_evidence_count") != partial_count:
        errors.append(f"row {key} partial_evidence_count does not match evidence_categories")
    if metrics.get("no_evidence_count") != no_count:
        errors.append(f"row {key} no_evidence_count does not match evidence_categories")
    miss_count = metrics.get("miss_count")
    if isinstance(miss_count, int) and partial_count + no_count != miss_count:
        errors.append(f"row {key} evidence miss counts do not match miss_count")


def _category_count(categories: Mapping[str, object], category: str) -> int:
    payload = _mapping_or_empty(categories.get(category))
    count = payload.get("count")
    return count if isinstance(count, int) else 0


def _validate_miss_buckets(
    metrics: Mapping[str, object],
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    miss_buckets = _mapping_or_empty(metrics.get("miss_bucket_counts"))
    bucket_total = sum(value for value in miss_buckets.values() if isinstance(value, int))
    miss_count = metrics.get("miss_count")
    if isinstance(miss_count, int) and bucket_total != miss_count:
        errors.append(f"row {key} miss_bucket_counts do not sum to miss_count")


def _validate_per_query_reconciliation(
    report: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    raw_per_query = report.get("per_query_results")
    if not isinstance(raw_per_query, list):
        errors.append("per_query_results must be a list")
        return
    per_query_rows = [
        cast("dict[str, object]", item) for item in raw_per_query if isinstance(item, dict)
    ]
    by_row_id: dict[str, list[dict[str, object]]] = {}
    for item in per_query_rows:
        row_id = item.get("row_id")
        if isinstance(row_id, str):
            by_row_id.setdefault(row_id, []).append(item)
    for row in rows:
        if row.get("status") != "success":
            continue
        row_id = row.get("row_id")
        if not isinstance(row_id, str):
            continue
        metrics = _mapping_or_empty(row.get("metrics"))
        query_rows = by_row_id.get(row_id, [])
        query_count = metrics.get("query_count")
        if isinstance(query_count, int) and len(query_rows) != query_count:
            errors.append(f"row {row_id} per_query_results count does not match query_count")
        _validate_metric_average(
            row_id,
            metrics,
            query_rows,
            metric_name="recall_at_k",
            per_query_field="recall_at_k",
            errors=errors,
        )
        _validate_metric_average(
            row_id,
            metrics,
            query_rows,
            metric_name="candidate_recall_at_budget",
            per_query_field="candidate_recall_at_budget",
            errors=errors,
        )
        _validate_metric_average(
            row_id,
            metrics,
            query_rows,
            metric_name="precision_at_k",
            per_query_field="precision_at_k",
            errors=errors,
        )
        _validate_per_query_evidence(row_id, metrics, query_rows, errors)
    _validate_top_k_monotonicity(rows, errors)


def _validate_metric_average(
    row_id: str,
    metrics: Mapping[str, object],
    query_rows: Sequence[Mapping[str, object]],
    *,
    metric_name: str,
    per_query_field: str,
    errors: list[str],
) -> None:
    if not query_rows:
        return
    metric_value = metrics.get(metric_name)
    if not isinstance(metric_value, int | float):
        return
    values = [item.get(per_query_field) for item in query_rows]
    if not all(isinstance(value, int | float) for value in values):
        errors.append(f"row {row_id} {per_query_field} per-query values are incomplete")
        return
    average = sum(float(value) for value in values) / len(values)
    if not math.isclose(float(metric_value), average, rel_tol=0.0, abs_tol=1e-6):
        errors.append(f"row {row_id} {metric_name} does not reconcile with per-query results")


def _validate_per_query_evidence(
    row_id: str,
    metrics: Mapping[str, object],
    query_rows: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    counts = dict.fromkeys(_EVIDENCE_CATEGORIES, 0)
    miss_buckets: dict[str, int] = {}
    for item in query_rows:
        category = item.get("evidence_category")
        if isinstance(category, str):
            counts[category] = counts.get(category, 0) + 1
        miss_bucket = item.get("miss_bucket")
        if isinstance(miss_bucket, str):
            miss_buckets[miss_bucket] = miss_buckets.get(miss_bucket, 0) + 1
    categories = _mapping_or_empty(metrics.get("evidence_categories"))
    for category in _EVIDENCE_CATEGORIES:
        if _category_count(categories, category) != counts.get(category, 0):
            errors.append(f"row {row_id} evidence_categories do not reconcile")
            break
    metric_miss_buckets = _mapping_or_empty(metrics.get("miss_bucket_counts"))
    normalized_metric_buckets = {
        key: value
        for key, value in sorted(metric_miss_buckets.items())
        if isinstance(key, str) and isinstance(value, int)
    }
    if dict(sorted(miss_buckets.items())) != normalized_metric_buckets:
        errors.append(f"row {row_id} miss_bucket_counts do not reconcile")


def _validate_top_k_monotonicity(
    rows: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    for row in rows:
        if row.get("status") != "success":
            continue
        retriever = row.get("retriever")
        granularity = row.get("granularity")
        if isinstance(retriever, str) and isinstance(granularity, str):
            grouped.setdefault((retriever, granularity), []).append(row)
    for key, group_rows in grouped.items():
        previous: dict[str, float] = {}
        for row in sorted(group_rows, key=lambda item: int(item.get("top_k", 0))):
            top_k = row.get("top_k")
            metrics = _mapping_or_empty(row.get("metrics"))
            for metric_name in ("hit_rate_at_k", "recall_at_k", "candidate_recall_at_budget"):
                value = metrics.get(metric_name)
                if not isinstance(value, int | float):
                    continue
                prior = previous.get(metric_name)
                if prior is not None and float(value) + 1e-9 < prior:
                    errors.append(
                        f"row group {key[0]}:{key[1]} {metric_name} is not monotonic at k={top_k}"
                    )
                previous[metric_name] = float(value)


def _validate_thresholds(
    report: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    thresholds = _mapping_or_empty(report.get("thresholds"))
    for row in rows:
        if row.get("status") != "success":
            continue
        row_id = row.get("row_id")
        metrics = _mapping_or_empty(row.get("metrics"))
        for metric_name in (
            "permission_retrieval_safety_rate",
            "forbidden_before_expected_avoidance",
        ):
            threshold = thresholds.get(metric_name)
            metric_value = metrics.get(metric_name)
            if not isinstance(threshold, int | float) or not isinstance(metric_value, int | float):
                continue
            if float(metric_value) + 1e-9 < float(threshold):
                errors.append(
                    f"row {row_id} {metric_name} is below threshold {float(threshold):.3f}"
                )


def _validate_row_hashes(
    row: Mapping[str, object],
    report_metadata: Mapping[str, object],
    key: tuple[str, str, int],
    errors: list[str],
) -> None:
    nested_metadata = _mapping_or_empty(row.get("matched_metadata"))
    for field_name in (
        "corpus_sha256",
        "cases_sha256",
        "manifest_sha256",
        "scoring_protocol_version",
        "git_commit",
        "dependency_lock_sha256",
    ):
        row_value = row.get(field_name, nested_metadata.get(field_name))
        metadata_value = report_metadata.get(field_name)
        if metadata_value is not None and row_value != metadata_value:
            errors.append(f"row {key[0]}:{key[1]}:k={key[2]} {field_name} does not match metadata")
    label_value = row.get("labels_sha256", nested_metadata.get("label_hash"))
    metadata_label = report_metadata.get("labels_sha256", report_metadata.get("qrels_sha256"))
    if metadata_label is not None and label_value not in {metadata_label, None}:
        errors.append(f"row {key[0]}:{key[1]}:k={key[2]} labels_sha256 does not match metadata")


def _contract_result(errors: Sequence[str]) -> MatrixContractResult:
    if errors:
        return MatrixContractResult(status="failed", errors=tuple(errors))
    return MatrixContractResult(status="passed", errors=())


def _raise_if_failed(result: MatrixContractResult) -> None:
    if result.status != "passed":
        raise MatrixValidationError("; ".join(result.errors))


def _required_mapping(
    payload: Mapping[str, object],
    field_name: str,
    label: str,
    errors: list[str],
) -> dict[str, object]:
    value = payload.get(field_name)
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    errors.append(f"{label} missing object field {field_name!r}")
    return {}


def _mapping_or_empty(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return {}


def _list_of_mappings(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast("dict[str, object]", item) for item in value if isinstance(item, dict)]


def _object_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return list(cast("list[object]", value))


def _int_tuple(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, int))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _float_value(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _string_value(value: object, *, fallback: str) -> str:
    if isinstance(value, str):
        return value
    return fallback


def _int_metric(metrics: Mapping[str, object], metric_name: str) -> int:
    value = metrics.get(metric_name)
    if isinstance(value, int):
        return value
    return 0


def _positive_int_value(value: object) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 0


def _float_metric(metrics: Mapping[str, object], metric_name: str) -> float:
    value = metrics.get(metric_name)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = percentile * (len(ordered) - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _embedding_model_label(value: str | None) -> str:
    return value or os.environ.get("HEPHAISTOS_EMBED_MODEL", _DEFAULT_EMBEDDING_MODEL)


def _rerank_model_label(value: str | None) -> str:
    return value or os.environ.get("HEPHAISTOS_RERANK_MODEL", _DEFAULT_RERANK_MODEL)


def _optional_cli_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _resolved_output_dir(
    output_dir: Path,
    json_report: Path | None,
    artifact_manifest: Path | None,
) -> Path:
    if json_report is not None:
        return json_report.expanduser().resolve().parent
    if artifact_manifest is not None:
        return artifact_manifest.expanduser().resolve().parent
    return output_dir.expanduser().resolve()


if __name__ == "__main__":
    raise SystemExit(main())
