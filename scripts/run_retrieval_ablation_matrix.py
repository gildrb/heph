"""Run a local Hephaistos retrieval ablation matrix over labelled RAG cases.

The matrix is intentionally benchmark-script-only: it calls Hephaistos retrieval APIs over a
materialized armory, records matched corpus/case/hash metadata for every row, and writes private
artifacts under a caller-provided output directory.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import shutil
import sys
import time
from collections.abc import Mapping, Sequence
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
    fusion_strategy: str = "none"

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
        if self.fusion_strategy == "none":
            return {"strategy": "none", "sparse_weight": 0.0, "dense_weight": 0.0}
        return {
            "strategy": self.fusion_strategy,
            "sparse_weight": self.hybrid_sparse_weight,
            "dense_weight": self.hybrid_dense_weight,
        }


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
    fusion_strategy: str = "none"
    candidate_multiplier: int = _DEFAULT_CANDIDATE_MULTIPLIER
    sparse_weight: float = 1.0
    dense_weight: float = 0.0

    def payload(self) -> dict[str, object]:
        """Return a stable machine-readable config payload."""
        return {
            "retriever": self.retriever,
            "granularity": self.granularity.value,
            "retrieval_mode": self.retrieval_mode.value,
            "candidate_multiplier": self.candidate_multiplier,
            "fusion": self.fusion_payload(),
        }

    def fusion_payload(self) -> dict[str, object]:
        """Return explicit fusion metadata for this matrix config."""
        if self.fusion_strategy == "none":
            return {"strategy": "none", "sparse_weight": 0.0, "dense_weight": 0.0}
        return {
            "strategy": self.fusion_strategy,
            "sparse_weight": self.sparse_weight,
            "dense_weight": self.dense_weight,
        }

    def candidate_budget(self, top_k: int) -> int:
        """Return the requested pre-final candidate budget for this row."""
        if self.granularity == ReferenceGranularity.DOCUMENT and (
            self.retrieval_mode != RetrievalMode.BM25_DOCUMENT
        ):
            return max(top_k, top_k * self.candidate_multiplier)
        if self.fusion_strategy != "none":
            return max(top_k, top_k * self.candidate_multiplier)
        return top_k


@dataclass(frozen=True, slots=True)
class RankedReference:
    """A retrieved reference with the score and excerpt needed for audit artifacts."""

    ref: str
    score: float
    text_excerpt: str


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
class ScoredCaseResult:
    """Scored per-query result after canonical reference handling."""

    case_id: str
    query: str
    expected_count: int
    forbidden_count: int
    retrieved: tuple[str, ...]
    retrieved_chunks: tuple[dict[str, object], ...]
    hit: bool
    rank: int | None
    first_forbidden_rank: int | None
    forbidden_before_expected_ok: bool
    metrics: RankingMetrics
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
    hybrid_sparse_weight: float = 1.0,
    hybrid_dense_weight: float = 1.0,
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
            fusion_strategy="weighted_sparse_dense",
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
        ),
        MatrixCell(
            retriever="hybrid",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy="weighted_sparse_dense",
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
        ),
        MatrixCell(
            retriever="rrf",
            granularity=ReferenceGranularity.CHUNK.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy="reciprocal_rank_fusion",
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
        ),
        MatrixCell(
            retriever="rrf",
            granularity=ReferenceGranularity.DOCUMENT.value,
            retrieval_mode=RetrievalMode.HYBRID,
            candidate_multiplier=candidate_multiplier,
            fusion_strategy="reciprocal_rank_fusion",
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
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
    expected_labels = tuple(
        _canonical_label(reference, corpus, granularity=granularity) for reference in expected
    )
    forbidden_labels = tuple(
        _canonical_label(reference, corpus, granularity=granularity)
        for reference in forbidden_before_expected
    )
    _validate_label_uniqueness(expected_labels, label="expected")
    _validate_label_uniqueness(forbidden_labels, label="forbidden_before_expected")
    return CaseLabels(expected=expected_labels, forbidden_before_expected=forbidden_labels)


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
    labels: CaseLabels,
    retrieved: Sequence[RankedReference],
    corpus: CanonicalCorpus,
    granularity: ReferenceGranularity,
    top_k: int,
    elapsed_ms: float,
) -> ScoredCaseResult:
    """Score a ranked list after canonicalizing and deduplicating retrieved references."""
    canonical_retrieved = _canonicalize_retrieved(retrieved, corpus, granularity=granularity)
    top_retrieved = canonical_retrieved[:top_k]
    rank = _first_label_rank(labels.expected, top_retrieved)
    forbidden_rank = _first_label_rank(labels.forbidden_before_expected, top_retrieved)
    metrics = _rank_metrics(labels.expected, top_retrieved, top_k=top_k)
    forbidden_ok = _forbidden_before_expected_ok(rank, forbidden_rank)
    retrieved_chunk_rows = [_retrieved_chunk_payload(item) for item in top_retrieved]
    return ScoredCaseResult(
        case_id=case_id,
        query=query,
        expected_count=len(labels.expected),
        forbidden_count=len(labels.forbidden_before_expected),
        retrieved=tuple(item.canonical for item in top_retrieved),
        retrieved_chunks=tuple(retrieved_chunk_rows),
        hit=rank is not None,
        rank=rank,
        first_forbidden_rank=forbidden_rank,
        forbidden_before_expected_ok=forbidden_ok,
        metrics=metrics,
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
    configured_rows = _configured_keys(matrix.get("configured_rows"), errors)
    if not configured_rows:
        configured_rows = {
            (cell.retriever, cell.granularity)
            for cell in required_matrix_cells(candidate_multiplier=_DEFAULT_CANDIDATE_MULTIPLIER)
        }
    rows = _row_mappings(matrix.get("rows"), errors)
    seen: set[tuple[str, str, int]] = set()
    report_metadata = _mapping_or_empty(report.get("metadata"))
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
    command_invocation: str,
) -> dict[str, object]:
    """Run all configured matrix rows and return the finalized JSON report."""
    resolved_armory = armory_path.expanduser().resolve()
    resolved_cases = cases_path.expanduser().resolve()
    resolved_output_dir = output_dir.expanduser().resolve()
    working_armory = _prepare_working_armory(resolved_armory, resolved_output_dir, copy_armory)
    cases = benchmark_rag.load_cases(resolved_cases)
    index = load_or_build(working_armory)
    corpus = CanonicalCorpus.from_index(index)
    configs = tuple(
        _with_candidate_multiplier(config, candidate_multiplier)
        for config in default_matrix_configs()
    )
    hashes = _input_hashes(resolved_armory, resolved_cases)
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
    _write_json(diagnostics_path, {"rows": diagnostics})
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
    copy_armory = cast("bool", args.copy_armory)
    top_k_values = _parse_top_k_values(cast("str", args.top_k_values), parser)

    if min_score < 0:
        parser.error("--min-score must be non-negative")
    if candidate_multiplier <= 0:
        parser.error("--candidate-multiplier must be positive")

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
            retrieval_top_k = (
                config.candidate_budget(top_k)
                if config.granularity == ReferenceGranularity.DOCUMENT
                and config.retrieval_mode != RetrievalMode.BM25_DOCUMENT
                else top_k
            )
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
                labels=labels,
                retrieved=ranked,
                corpus=corpus,
                granularity=config.granularity,
                top_k=top_k,
                elapsed_ms=elapsed_ms,
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
        "fusion": config.fusion_payload(),
        "top_k": top_k,
        "candidate_budget": config.candidate_budget(top_k),
        "candidate_multiplier": config.candidate_multiplier,
        "claim_eligible": True,
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
    dataset_id: str,
) -> dict[str, object]:
    selected = _selected_configuration(rows)
    aggregate_metrics = _selected_aggregate_metrics(selected, rows)
    baseline_delta = _baseline_delta(selected, rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_id": f"retrieval-ablation-matrix:{dataset_id}",
        "status": status,
        "metadata": {
            "runner": RUNNER_ID,
            "benchmark_type": "retrieval-ablation-matrix",
            "dataset": dataset_id,
            "armory_path": str(armory_path),
            "working_armory_path": str(working_armory_path),
            "cases_path": str(cases_path),
            "output_dir": str(output_dir),
            "corpus_sha256": hashes["corpus_sha256"],
            "cases_sha256": hashes["cases_sha256"],
            "labels_sha256": hashes["qrels_sha256"],
            "qrels_sha256": hashes["qrels_sha256"],
            "manifest_sha256": hashes["manifest_sha256"],
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
        "thresholds": {
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "primary_metric": _PRIMARY_METRIC,
            "primary_top_k": _PRIMARY_TOP_K,
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
        ("hybrid", "chunk"): 4,
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
    miss_count = sum(1 for result in results if not result.hit)
    hit_count = query_count - miss_count
    reciprocal_rank_sum = sum(result.metrics.reciprocal_rank for result in results)
    recall_sum = sum(result.metrics.recall_at_k for result in results)
    precision_sum = sum(result.metrics.precision_at_k for result in results)
    average_precision_sum = sum(result.metrics.average_precision_at_k for result in results)
    ndcg_sum = sum(result.metrics.ndcg_at_k for result in results)
    latency_values = [result.elapsed_ms for result in results]
    mean_latency = sum(latency_values) / query_count
    return {
        "hit_rate_at_k": hit_count / query_count,
        "recall_at_k": recall_sum / query_count,
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
        "top_k": top_k,
    }


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


def _forbidden_before_expected_ok(
    expected_rank: int | None,
    forbidden_rank: int | None,
) -> bool:
    if forbidden_rank is None:
        return True
    if expected_rank is None:
        return False
    return expected_rank < forbidden_rank


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
    retrieval_top_k = (
        config.candidate_budget(top_k)
        if config.granularity == ReferenceGranularity.DOCUMENT
        and config.retrieval_mode != RetrievalMode.BM25_DOCUMENT
        else top_k
    )
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
) -> tuple[RankedReference, ...]:
    ranked: list[RankedReference] = []
    seen_documents: set[str] = set()
    for scored_chunk in chunks:
        ref = EvidenceReference(scored_chunk.chunk.source, scored_chunk.chunk.index).render()
        if config.granularity == ReferenceGranularity.DOCUMENT:
            if scored_chunk.chunk.source in seen_documents:
                continue
            seen_documents.add(scored_chunk.chunk.source)
        ranked.append(
            RankedReference(
                ref=ref,
                score=scored_chunk.score,
                text_excerpt=_excerpt(scored_chunk.chunk.text),
            )
        )
        if len(ranked) >= top_k:
            break
    return tuple(ranked)


def _per_query_payload(
    config: MatrixConfig,
    top_k: int,
    result: ScoredCaseResult,
) -> dict[str, object]:
    return {
        "row_id": matrix_row_id(config, top_k),
        "case_id": result.case_id,
        "query": result.query,
        "retriever": config.retriever,
        "granularity": config.granularity.value,
        "top_k": top_k,
        "candidate_budget": config.candidate_budget(top_k),
        "expected_count": result.expected_count,
        "forbidden_before_expected_count": result.forbidden_count,
        "retrieved": list(result.retrieved),
        "retrieved_chunks": list(result.retrieved_chunks),
        "hit": result.hit,
        "rank": result.rank,
        "reciprocal_rank": result.metrics.reciprocal_rank,
        "recall_at_k": result.metrics.recall_at_k,
        "precision_at_k": result.metrics.precision_at_k,
        "average_precision_at_k": result.metrics.average_precision_at_k,
        "ndcg_at_k": result.metrics.ndcg_at_k,
        "first_forbidden_rank": result.first_forbidden_rank,
        "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
        "latency_ms": result.elapsed_ms,
    }


def _row_diagnostics(
    row_id: str,
    row: Mapping[str, object],
    per_query_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    misses = [
        {
            "case_id": item.get("case_id"),
            "bucket": "no_expected_evidence_retrieved"
            if item.get("retrieved")
            else "no_retrieved_candidates",
            "retrieved_count": len(_object_list(item.get("retrieved"))),
            "top_retrieved": _object_list(item.get("retrieved"))[:3],
        }
        for item in per_query_rows
        if item.get("hit") is False
    ]
    return {
        "row_id": row_id,
        "status": row.get("status"),
        "miss_count": len(misses),
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
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-query-prefix", default="")
    parser.add_argument("--embedding-document-prefix", default="")
    parser.add_argument("--rerank-model")
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


def _configured_keys(value: object, errors: list[str]) -> set[tuple[str, str]]:
    if value is None:
        return set()
    if not isinstance(value, list):
        errors.append("matrix configured_rows must be a list")
        return set()
    keys: set[tuple[str, str]] = set()
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
        keys.add((retriever, granularity))
    return keys


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
    latency_value = metrics.get("latency")
    if isinstance(latency_value, dict):
        latency = cast("dict[str, object]", latency_value)
        if latency.get("scope") != claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY:
            errors.append(f"row {key} latency scope must be retrieval-only")


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
