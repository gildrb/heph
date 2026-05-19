from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.rag.chunker import Chunk
from hephaistos.rag.retrieval_types import ScoredChunk
from scripts import run_retrieval_ablation_matrix


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


def _complete_contract_report() -> dict[str, object]:
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
    }
    cells = run_retrieval_ablation_matrix.required_matrix_cells(
        candidate_multiplier=2,
        hybrid_sparse_weight=1.25,
        hybrid_dense_weight=1.0,
    )
    rows = [
        {
            "row_id": f"{cell.retriever}:{cell.granularity}:k={top_k}",
            "status": "success",
            "retriever": cell.retriever,
            "granularity": cell.granularity,
            "retrieval_mode": cell.retrieval_mode.value,
            "top_k": top_k,
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
            "metrics": {
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
                "query_count": 2,
                "miss_count": 0,
            },
        }
        for cell in cells
        for top_k in run_retrieval_ablation_matrix.REQUIRED_TOP_K_VALUES
    ]
    return {
        "schema_version": run_retrieval_ablation_matrix.SCHEMA_VERSION,
        "metadata": metadata,
        "matrix": {"rows": rows},
    }


def test_matrix_report_contract_accepts_complete_matrix() -> None:
    result = run_retrieval_ablation_matrix.validate_matrix_report(_complete_contract_report())

    assert result.status == "passed"
    assert result.errors == ()


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

    def fake_retrieve(
        _index: object,
        case: run_retrieval_ablation_matrix.benchmark_rag.BenchmarkCase,
        cell: run_retrieval_ablation_matrix.MatrixCell,
        _retrieval_top_k: int,
        _parameters: run_retrieval_ablation_matrix.MatrixParameters,
    ) -> list[ScoredChunk]:
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
