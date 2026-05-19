from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.rag.chunker import Chunk
from hephaistos.rag.retrieval_types import ScoredChunk
from scripts import claim_report_envelope, run_retrieval_ablation_matrix


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _has_exact_key(value: object, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(
            _has_exact_key(child, key_name) for child in value.values()
        )
    if isinstance(value, list):
        return any(_has_exact_key(item, key_name) for item in value)
    return False


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "materials" / "alpha.md").write_text(
        "Alpha receptor signaling explains ligand binding in enterprise retrieval.\n",
        encoding="utf-8",
    )
    (armory / "materials" / "beta.md").write_text(
        "Beta cache invalidation describes a systems operations runbook.\n",
        encoding="utf-8",
    )
    return armory


def _fixture_per_query_row(
    *,
    row_id: str,
    cell: run_retrieval_ablation_matrix.MatrixCell,
    top_k: int,
    case_id: str,
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "case_id": case_id,
        "query": f"fixture query {case_id}",
        "query_type": "fixture-query",
        "retriever": cell.retriever,
        "granularity": cell.granularity,
        "top_k": top_k,
        "candidate_budget": cell.candidate_budget(top_k),
        "retrieval_top_k_requested": cell.candidate_budget(top_k),
        "expected_count": 1,
        "forbidden_before_expected_count": 0,
        "retrieved": ["materials/fixture.md"],
        "retrieved_chunks": [
            {
                "ref": "materials/fixture.md",
                "chunk_ref": "materials/fixture.md#chunk=0",
                "source": "materials/fixture.md",
                "score": 1.0,
                "text_excerpt": "Fixture evidence",
            }
        ],
        "hit": True,
        "rank": 1,
        "candidate_rank": 1,
        "relevant_found": 1,
        "candidate_relevant_found": 1,
        "reciprocal_rank": 1.0,
        "recall_at_k": 1.0,
        "candidate_recall_at_budget": 1.0,
        "precision_at_k": 1.0 / top_k,
        "average_precision_at_k": 1.0,
        "ndcg_at_k": 1.0,
        "evidence_category": "full_evidence",
        "miss_bucket": None,
        "raw_candidate_count": 1,
        "candidate_retrieved_count": 1,
        "final_retrieved_count": 1,
        "top_k_satisfied": top_k == 1,
        "top_k_shortfall_count": max(0, top_k - 1),
        "duplicate_document_drop_count": 0,
        "first_forbidden_rank": None,
        "forbidden_before_expected_ok": True,
        "permission_violation_count": 0,
        "expected_source_families": ["fixture"],
        "top_retrieved_source_family": "fixture",
        "expected_document_types": ["markdown"],
        "top_retrieved_document_type": "markdown",
        "latency_ms": 1.0 if case_id == "case-1" else 2.0,
    }


def _complete_contract_report() -> dict[str, object]:
    index_cache = {
        "index_path": "/tmp/fixture-armory/.hephaistos/rag_index.json",
        "index_identity": "1" * 16,
        "index_build_or_refresh_command": "uv run heph index /tmp/fixture-armory",
        "scored_corpus_sha256": "a" * 64,
        "indexed_corpus_sha256": "a" * 64,
        "fresh_for_scored_corpus": True,
        "cache_state": "warm_reused",
        "loaded_existing_index": True,
        "stale_before_run": False,
        "rebuilt_during_run": False,
        "document_count": 1,
        "chunk_count": 2,
        "cache_artifacts": [],
    }
    permission_scope = {
        "scope": "indexed_materials",
        "scope_hash": "9" * 64,
        "allowed_source_count": 1,
        "indexed_source_count": 1,
        "policy": "hidden, ignored, symlinked, and outside-material paths are excluded",
    }
    metadata = {
        "dataset_id": "fixture-matrix",
        "corpus_sha256": "a" * 64,
        "cases_sha256": "b" * 64,
        "labels_sha256": "c" * 64,
        "manifest_sha256": "d" * 64,
        "scoring_protocol_version": "retrieval-ablation-scoring-v1",
        "git_commit": "e" * 40,
        "dependency_lock_sha256": "f" * 64,
        "configured_top_k_values": [1, 3, 5, 10, 25, 50, 100],
        "latency_scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
        "index_cache": index_cache,
        "permission_scope": permission_scope,
    }
    cells = run_retrieval_ablation_matrix.required_matrix_cells(
        candidate_multiplier=2,
        hybrid_sparse_weight=1.25,
        hybrid_dense_weight=1.0,
    )
    configs = [run_retrieval_ablation_matrix._config_from_cell(cell) for cell in cells]
    rows: list[dict[str, object]] = []
    per_query_results: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    for cell, config in zip(cells, configs, strict=True):
        for top_k in run_retrieval_ablation_matrix.REQUIRED_TOP_K_VALUES:
            row_id = f"{cell.retriever}:{cell.granularity}:k={top_k}"
            shortfall = max(0, top_k - 1) * 2
            metrics: dict[str, object] = {
                "hit_rate": 1.0,
                "recall": 1.0,
                "mrr": 1.0,
                "map": 1.0,
                "ndcg": 1.0,
                "precision": 1.0 / top_k,
                "hit_rate_at_k": 1.0,
                "recall_at_k": 1.0,
                "mrr_at_k": 1.0,
                "map_at_k": 1.0,
                "ndcg_at_k": 1.0,
                "precision_at_k": 1.0 / top_k,
                "candidate_recall_at_budget": 1.0,
                "query_count": 2,
                "miss_count": 0,
                "mean_latency_ms": 1.5,
                "latency": {
                    "mean_ms": 1.5,
                    "p50_ms": 1.5,
                    "p75_ms": 1.75,
                    "p90_ms": 1.9,
                    "p95_ms": 1.95,
                    "p99_ms": 1.99,
                    "sample_count": 2,
                    "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
                    "unit": "milliseconds",
                },
                "evidence_categories": {
                    "full_evidence": {"count": 2, "rate": 1.0},
                    "partial_evidence": {"count": 0, "rate": 0.0},
                    "no_evidence": {"count": 0, "rate": 0.0},
                },
                "full_evidence_count": 2,
                "partial_evidence_count": 0,
                "no_evidence_count": 0,
                "miss_bucket_counts": {},
                "top_k_reconciliation": {
                    "per_query_count": 2,
                    "raw_candidate_count": 2,
                    "candidate_retrieved_count": 2,
                    "final_retrieved_count": 2,
                    "duplicate_document_drop_count": 0,
                    "top_k_shortfall_count": shortfall,
                },
                "forbidden_before_expected_case_count": 0,
                "forbidden_before_expected_failure_count": 0,
                "forbidden_before_expected_avoidance": 1.0,
                "permission_scope_checked_count": 2,
                "permission_violation_count": 0,
                "permission_retrieval_safety_rate": 1.0,
            }
            row: dict[str, object] = {
                "row_id": row_id,
                "status": "success",
                "retriever": cell.retriever,
                "granularity": cell.granularity,
                "retrieval_mode": cell.retrieval_mode.value,
                "retrieval_signature": cell.retrieval_signature(),
                "fusion": cell.fusion_payload(),
                "top_k": top_k,
                "candidate_budget": cell.candidate_budget(top_k),
                "candidate_multiplier": cell.candidate_multiplier,
                "claim_eligible": config.claim_eligible(),
                "dataset_id": metadata["dataset_id"],
                "corpus_sha256": metadata["corpus_sha256"],
                "cases_sha256": metadata["cases_sha256"],
                "labels_sha256": metadata["labels_sha256"],
                "manifest_sha256": metadata["manifest_sha256"],
                "scoring_protocol_version": metadata["scoring_protocol_version"],
                "git_commit": metadata["git_commit"],
                "dependency_lock_sha256": metadata["dependency_lock_sha256"],
                "query_count": 2,
                "miss_count": 0,
                "metrics": metrics,
            }
            rows.append(row)
            per_query_results.extend(
                _fixture_per_query_row(
                    row_id=row_id,
                    cell=cell,
                    top_k=top_k,
                    case_id=case_id,
                )
                for case_id in ("case-1", "case-2")
            )
            diagnostics.append(
                {
                    "row_id": row_id,
                    "status": "success",
                    "query_count": 2,
                    "miss_count": 0,
                    "miss_bucket_counts": {},
                    "evidence_categories": metrics["evidence_categories"],
                    "source_family_breakdown": {
                        "fixture": {"case_count": 2, "hit_count": 2, "miss_count": 0}
                    },
                    "document_type_breakdown": {
                        "markdown": {"case_count": 2, "hit_count": 2, "miss_count": 0}
                    },
                    "query_type_breakdown": {
                        "fixture-query": {"case_count": 2, "hit_count": 2, "miss_count": 0}
                    },
                    "source_family_confusion": {
                        "fixture->fixture": {"case_count": 2, "hit_count": 2}
                    },
                    "latency": metrics["latency"],
                    "top_k_reconciliation": metrics["top_k_reconciliation"],
                    "permission_safety": {
                        "permission_violation_count": 0,
                        "permission_retrieval_safety_rate": 1.0,
                    },
                    "recall_diagnostics": {
                        "top_k": top_k,
                        "recall_at_k": 1.0,
                        "candidate_recall_at_budget": 1.0,
                    },
                    "misses": [],
                    "failure": None,
                }
            )
    return {
        "schema_version": run_retrieval_ablation_matrix.SCHEMA_VERSION,
        "metadata": metadata,
        "matrix": {
            "required_top_k": list(run_retrieval_ablation_matrix.REQUIRED_TOP_K_VALUES),
            "configured_rows": [config.payload() for config in configs],
            "rows": rows,
        },
        "per_query_results": per_query_results,
        "diagnostics": diagnostics,
        "diagnostic_summary": {
            "recall_at_50_100": [
                {
                    "retriever": cell.retriever,
                    "granularity": cell.granularity,
                    "recall_at_50": 1.0,
                    "recall_at_100": 1.0,
                    "candidate_recall_at_50": 1.0,
                    "candidate_recall_at_100": 1.0,
                    "candidate_recall_scope": "pre_final_candidate_list",
                }
                for cell in cells
            ],
            "source_family": {"fixture": {"case_count": 112, "miss_count": 0}},
            "document_type": {"markdown": {"case_count": 112, "miss_count": 0}},
            "query_type": {"fixture-query": {"case_count": 112, "miss_count": 0}},
            "latency": {
                "scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
                "unit": "milliseconds",
                "rows": 56,
            },
            "evidence_categories": {
                "full_evidence": {"count": 112, "rate": 1.0},
                "partial_evidence": {"count": 0, "rate": 0.0},
                "no_evidence": {"count": 0, "rate": 0.0},
            },
            "top_k_reconciliation": {
                "rows_checked": 56,
                "per_query_rows_checked": 112,
                "non_monotonic_metric_failures": [],
            },
            "index_cache": index_cache,
            "permission_safety": {
                "permission_retrieval_safety_rate": 1.0,
                "permission_violation_count": 0,
            },
            "optimization_targets": [],
        },
        "thresholds": {"permission_retrieval_safety_rate": 1.0},
        "threshold_failures": [],
    }


def test_matrix_report_contract_accepts_complete_matrix() -> None:
    result = run_retrieval_ablation_matrix.validate_matrix_report(_complete_contract_report())

    assert result.status == "passed"
    assert result.errors == ()


def test_required_matrix_cells_distinguish_weighted_hybrid_and_rrf() -> None:
    cells = run_retrieval_ablation_matrix.required_matrix_cells()
    hybrid = next(
        cell for cell in cells if cell.retriever == "hybrid" and cell.granularity == "chunk"
    )
    rrf = next(cell for cell in cells if cell.retriever == "rrf" and cell.granularity == "chunk")

    assert hybrid.fusion_strategy == "weighted_sparse_dense"
    assert hybrid.hybrid_sparse_weight == 1.25
    assert hybrid.hybrid_dense_weight == 1.0
    assert rrf.fusion_strategy == "reciprocal_rank_fusion"
    assert rrf.hybrid_sparse_weight == 1.0
    assert rrf.hybrid_dense_weight == 1.0
    assert hybrid.retrieval_signature() != rrf.retrieval_signature()


def test_unweighted_hybrid_alias_is_not_claim_eligible() -> None:
    config = run_retrieval_ablation_matrix.MatrixConfig(
        retriever="hybrid",
        granularity=run_retrieval_ablation_matrix.ReferenceGranularity.CHUNK,
        retrieval_mode=run_retrieval_ablation_matrix.RetrievalMode.HYBRID,
        fusion_strategy="weighted_sparse_dense",
        sparse_weight=1.0,
        dense_weight=1.0,
    )

    assert config.claim_eligible() is False


def test_document_labels_collapse_same_document_chunk_aliases() -> None:
    corpus = run_retrieval_ablation_matrix.CanonicalCorpus.from_reference_map(
        {"materials/alpha.md": (0, 1), "materials/beta.md": (0,)}
    )

    labels = run_retrieval_ablation_matrix.canonicalize_case_labels(
        ["materials/alpha.md#chunk=0", "materials/alpha.md#chunk=1"],
        [],
        corpus,
        granularity=run_retrieval_ablation_matrix.ReferenceGranularity.DOCUMENT,
    )

    assert [label.canonical for label in labels.expected] == ["materials/alpha.md"]


@pytest.mark.parametrize(
    ("mutator", "expected_fragment"),
    [
        (
            lambda rows: rows.pop(),
            "missing row for retriever=rrf granularity=document top_k=100",
        ),
        (
            lambda rows: rows.append(dict(rows[0])),
            "duplicate row for retriever=bm25 granularity=chunk top_k=1",
        ),
        (
            lambda rows: _as_dict(rows[0]["metrics"]).__setitem__("ndcg", 1.5),
            "metric ndcg outside [0, 1]",
        ),
        (
            lambda rows: rows[0].__setitem__("corpus_sha256", "0" * 64),
            "row bm25:chunk:k=1 corpus_sha256 does not match metadata",
        ),
        (
            lambda rows: _as_dict(rows[-1]).__setitem__(
                "fusion",
                {
                    "strategy": "weighted_sparse_dense",
                    "algorithm": "weighted_reciprocal_rank_fusion",
                    "sparse_weight": 1.25,
                    "dense_weight": 1.0,
                    "canonical_id": "weighted_sparse_dense:sparse=1.25:dense=1",
                },
            ),
            "fusion strategy must be 'reciprocal_rank_fusion'",
        ),
    ],
)
def test_matrix_report_contract_rejects_negative_fixtures(
    mutator,
    expected_fragment: str,
) -> None:
    report = _complete_contract_report()
    rows = cast("list[dict[str, object]]", _as_dict(report["matrix"])["rows"])

    mutator(rows)

    result = run_retrieval_ablation_matrix.validate_matrix_report(report)
    assert result.status == "failed"
    assert any(expected_fragment in error for error in result.errors)


@pytest.mark.parametrize(
    ("mutator", "expected_fragment"),
    [
        (
            lambda report: _as_dict(
                _as_dict(_as_list(_as_dict(report["matrix"])["rows"])[0])["metrics"]
            ).pop("evidence_categories"),
            "evidence_categories",
        ),
        (
            lambda report: _as_dict(_as_list(report["per_query_results"])[0]).__setitem__(
                "recall_at_k",
                0.5,
            ),
            "recall_at_k does not reconcile",
        ),
        (
            lambda report: _as_dict(_as_dict(report["metadata"])["index_cache"]).__setitem__(
                "fresh_for_scored_corpus",
                False,
            ),
            "index cache is not fresh",
        ),
        (
            lambda report: _as_dict(
                _as_dict(_as_list(_as_dict(report["matrix"])["rows"])[0])["metrics"]
            ).__setitem__("permission_violation_count", 1),
            "permission violation",
        ),
    ],
)
def test_matrix_report_contract_rejects_diagnostics_negative_controls(
    mutator,
    expected_fragment: str,
) -> None:
    report = _complete_contract_report()

    mutator(report)

    result = run_retrieval_ablation_matrix.validate_matrix_report(report)
    assert result.status == "failed"
    assert any(expected_fragment in error for error in result.errors)


def test_canonical_reference_handling_preserves_chunk_and_collapses_document() -> None:
    chunk_refs, chunk_grades = run_retrieval_ablation_matrix.canonical_relevant_references(
        ("materials/alpha.md#chunk=2", "materials/beta.md"),
        {"materials/alpha.md#chunk=2": 3.0, "materials/beta.md": 1.0},
        granularity="chunk",
    )
    document_refs, document_grades = run_retrieval_ablation_matrix.canonical_relevant_references(
        ("materials/alpha.md#chunk=2", "materials/alpha.md#chunk=3", "materials/beta.md"),
        {"materials/alpha.md#chunk=2": 2.0, "materials/alpha.md#chunk=3": 4.0},
        granularity="document",
    )

    assert chunk_refs == ("materials/alpha.md#chunk=2", "materials/beta.md")
    assert chunk_grades == {"materials/alpha.md#chunk=2": 3.0, "materials/beta.md": 1.0}
    assert document_refs == ("materials/alpha.md", "materials/beta.md")
    assert document_grades == {"materials/alpha.md": 4.0}


def test_matrix_command_writes_manifest_and_selects_strongest_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    dataset = tmp_path / "cases.jsonl"
    _write_jsonl(
        dataset,
        [
            {
                "id": "alpha",
                "query": "alpha receptor signaling ligand binding",
                "expected": ["materials/alpha.md"],
            },
            {
                "id": "beta",
                "query": "beta cache invalidation runbook",
                "expected": ["materials/beta.md#chunk=0"],
            },
        ],
    )
    report_path = tmp_path / "artifacts" / "matrix.json"
    manifest_path = tmp_path / "artifacts" / "artifact-manifest.json"
    requested_top_k: list[tuple[str, str, str, float, float, int]] = []

    def fake_retrieve(
        _index: object,
        case: run_retrieval_ablation_matrix.benchmark_rag.BenchmarkCase,
        cell: run_retrieval_ablation_matrix.MatrixCell,
        retrieval_top_k: int,
        _parameters: run_retrieval_ablation_matrix.MatrixParameters,
    ) -> list[ScoredChunk]:
        requested_top_k.append(
            (
                cell.retriever,
                cell.granularity,
                cell.fusion_strategy,
                cell.hybrid_sparse_weight,
                cell.hybrid_dense_weight,
                retrieval_top_k,
            )
        )
        alpha = ScoredChunk(Chunk("alpha", "materials/alpha.md", 0, 0, 5), score=1.0)
        beta = ScoredChunk(Chunk("beta", "materials/beta.md", 0, 0, 4), score=0.9)
        if cell.retriever == "bm25" and cell.granularity == "document":
            return [beta, alpha] if case.case_id == "alpha" else [alpha, beta]
        return [alpha, beta] if case.case_id == "alpha" else [beta, alpha]

    monkeypatch.setattr(run_retrieval_ablation_matrix, "_retrieve_ranked_chunks", fake_retrieve)

    status = run_retrieval_ablation_matrix.main(
        [
            str(armory),
            str(dataset),
            "--dataset-id",
            "enterprise-rag-bench",
            "--json-report",
            str(report_path),
            "--artifact-manifest",
            str(manifest_path),
        ]
    )

    report = _as_dict(json.loads(report_path.read_text(encoding="utf-8")))
    manifest = _as_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    matrix = _as_dict(report["matrix"])
    selected = _as_dict(report["selected_configuration"])
    baseline = _as_dict(report["baseline_delta"])
    artifact_result = run_retrieval_ablation_matrix.validate_artifact_manifest(manifest_path)
    contract_result = run_retrieval_ablation_matrix.validate_matrix_report(report)

    assert status == 0
    assert report["schema_version"] == run_retrieval_ablation_matrix.SCHEMA_VERSION
    assert len(_as_list(matrix["rows"])) == 56
    assert selected["primary_metric"] == "recall_at_k"
    assert selected["selection_top_k"] == 50
    assert selected["retriever"] != "bm25" or selected["granularity"] != "document"
    assert baseline["baseline_retriever"] == "bm25"
    assert baseline["baseline_granularity"] == "document"
    assert baseline["primary_metric_delta"] == 1.0
    assert artifact_result.status == "passed"
    assert contract_result.status == "passed"
    assert "matrix_report" in _as_dict(manifest["artifacts"])
    assert "per_query_results" in _as_dict(manifest["artifacts"])
    assert "summary" in _as_dict(manifest["artifacts"])
    assert not _has_exact_key(report, "expected")
    assert not _has_exact_key(report, "qrels")
    diagnostic_summary = _as_dict(report["diagnostic_summary"])
    assert len(_as_list(diagnostic_summary["recall_at_50_100"])) == 8
    assert "source_family" in diagnostic_summary
    assert "document_type" in diagnostic_summary
    assert "query_type" in diagnostic_summary
    assert "optimization_targets" in diagnostic_summary
    index_cache = _as_dict(_as_dict(report["metadata"])["index_cache"])
    assert index_cache["fresh_for_scored_corpus"] is True
    assert index_cache["scored_corpus_sha256"] == _as_dict(report["metadata"])["corpus_sha256"]
    first_row = _as_dict(_as_list(matrix["rows"])[0])
    first_metrics = _as_dict(first_row["metrics"])
    assert _as_dict(first_metrics["evidence_categories"])["full_evidence"] == {
        "count": 2,
        "rate": 1.0,
    }
    assert "latency" in first_metrics
    assert first_metrics["permission_retrieval_safety_rate"] == 1.0
    assert ("hybrid", "chunk", "weighted_sparse_dense", 1.25, 1.0, 2) in requested_top_k
    assert ("rrf", "chunk", "reciprocal_rank_fusion", 1.0, 1.0, 2) in requested_top_k


def test_matrix_command_excludes_ignored_permissioned_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    (armory / ".hephaistosignore").write_text("materials/private.md\n", encoding="utf-8")
    (armory / "materials" / "private.md").write_text(
        "PRIVATE-TENANT-SENTINEL must never be retrieved.\n",
        encoding="utf-8",
    )
    dataset = tmp_path / "cases.jsonl"
    _write_jsonl(
        dataset,
        [
            {
                "id": "alpha",
                "query": "alpha receptor signaling ligand binding",
                "expected": ["materials/alpha.md"],
            },
        ],
    )
    report_path = tmp_path / "artifacts" / "matrix.json"

    def indexed_chunks_only(
        index: object,
        _case: run_retrieval_ablation_matrix.benchmark_rag.BenchmarkCase,
        _cell: run_retrieval_ablation_matrix.MatrixCell,
        _retrieval_top_k: int,
        _parameters: run_retrieval_ablation_matrix.MatrixParameters,
    ) -> list[ScoredChunk]:
        assert isinstance(index, run_retrieval_ablation_matrix.ArmoryIndex)
        return [ScoredChunk(chunk, score=1.0) for chunk in index.all_chunks]

    monkeypatch.setattr(
        run_retrieval_ablation_matrix,
        "_retrieve_ranked_chunks",
        indexed_chunks_only,
    )

    status = run_retrieval_ablation_matrix.main(
        [
            str(armory),
            str(dataset),
            "--dataset-id",
            "permissioned-test-corpus",
            "--json-report",
            str(report_path),
        ]
    )

    report_text = report_path.read_text(encoding="utf-8")
    report = _as_dict(json.loads(report_text))
    metadata = _as_dict(report["metadata"])
    permission_scope = _as_dict(metadata["permission_scope"])
    first_query = _as_dict(_as_list(report["per_query_results"])[0])

    assert status == 0
    assert "PRIVATE-TENANT-SENTINEL" not in report_text
    assert "materials/private.md" not in report_text
    assert permission_scope["allowed_source_count"] == 2
    assert first_query["permission_violation_count"] == 0
