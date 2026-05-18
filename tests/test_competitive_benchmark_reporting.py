from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from scripts import generate_benchmark_summary

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "benchmarks" / "model-evaluation-prompt.md"


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _retrieval_report(
    *,
    report_id: str,
    mode: str,
    hit_rate: float,
    mrr: float,
    expected_recall: float,
    ndcg_at_k: float = 0.4,
    graded_ndcg_at_k: float | None = None,
    dense_weight: float = 1.5,
    document_prefix: str | None = None,
) -> dict[str, object]:
    fixed_parameters: dict[str, object] = {
        "candidate_multiplier": 2,
        "embedding_model": "BAAI/bge-large-en-v1.5",
        "embedding_query_prefix": "Represent this sentence for searching relevant passages: ",
        "hybrid_dense_weight": dense_weight,
        "hybrid_sparse_weight": 1.0,
        "min_score": 0.0,
        "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "retrieval_mode": mode,
        "top_k": 5,
        "transform_strategy": "identity",
    }
    if document_prefix is not None:
        fixed_parameters["embedding_document_prefix"] = document_prefix
    if mode == "hybrid-prf":
        fixed_parameters.update(
            {
                "pseudo_feedback_docs": 3,
                "pseudo_feedback_terms": 6,
                "pseudo_feedback_weight": 0.1,
            }
        )
    metrics: dict[str, object] = {
        "expected_recall": expected_recall,
        "hit_rate": hit_rate,
        "mean_latency_ms": 3.0,
        "mrr": mrr,
        "ndcg_at_k": ndcg_at_k,
        "query_count": 10,
    }
    if graded_ndcg_at_k is not None:
        metrics["graded_ndcg_at_k"] = graded_ndcg_at_k
    return {
        "schema_version": "external-runner-report-v1",
        "report_id": report_id,
        "status": "success",
        "metadata": {
            "runner": "scripts.run_external_benchmarks",
            "benchmark_type": "beir",
            "dataset": "beir/nfcorpus",
            "cases_sha256": "abc123456789",
            "fixed_parameters": fixed_parameters,
            "metric_formulas": {
                "hit_rate": "fraction of queries with an expected reference in top-k",
                "mrr": "mean reciprocal rank of the first expected reference",
                "expected_recall": "average retrieved expected references per query",
                "ndcg_at_k": "binary normalized discounted cumulative gain at k",
            },
            "runtime_only_fields": ["aggregate_metrics.mean_latency_ms"],
        },
        "benchmarks": [
            {
                "id": "beir:beir/nfcorpus",
                "benchmark_type": "beir",
                "dataset": "beir/nfcorpus",
                "status": "success",
                "metrics": metrics,
                "per_query_results": [
                    {"case_id": "alpha", "hit": True, "rank": 1, "expected_recall": 1.0}
                ],
            }
        ],
        "aggregate_metrics": metrics,
        "thresholds": {},
        "threshold_failures": [],
        "warnings": [],
        "errors": [],
        "reproducibility": {
            "enabled": False,
            "status": "skipped",
            "deterministic_fields_compared": [],
            "runtime_only_fields": ["aggregate_metrics.mean_latency_ms"],
            "mismatches": [],
        },
    }


def _single_heph_report() -> dict[str, object]:
    return {
        "schema_version": "external-runner-report-v1",
        "report_id": "heph-native:academic",
        "status": "success",
        "metadata": {
            "runner": "scripts.run_external_benchmarks",
            "benchmark_type": "heph-native",
            "dataset": "academic",
            "fixed_parameters": {
                "top_k": 5,
                "min_score": 0.1,
                "query_order": "case-file-order",
            },
            "metric_formulas": {
                "hit_rate": "fraction of queries with an expected reference in top-k",
                "mrr": "mean reciprocal rank of the first expected reference",
                "expected_recall": "average retrieved expected references per query",
            },
            "runtime_only_fields": ["aggregate_metrics.mean_latency_ms"],
            "prompt_path": "benchmarks/model-evaluation-prompt.md",
            "prompt_hash": "prompt-hash",
            "model": "fixture-model",
        },
        "benchmarks": [
            {
                "id": "heph-native:academic",
                "benchmark_type": "heph-native",
                "dataset": "academic",
                "status": "success",
                "metrics": {
                    "hit_rate": 1.0,
                    "mrr": 0.9,
                    "expected_recall": 1.0,
                    "mean_latency_ms": 3.0,
                },
                "per_query_results": [
                    {"case_id": "alpha", "hit": True, "rank": 1, "expected_recall": 1.0}
                ],
            }
        ],
        "aggregate_metrics": {
            "hit_rate": 1.0,
            "mrr": 0.9,
            "expected_recall": 1.0,
            "mean_latency_ms": 3.0,
        },
        "thresholds": {"hit_rate": 0.8, "mrr": 0.7, "expected_recall": 0.9},
        "threshold_failures": [],
        "warnings": [],
        "errors": [],
        "reproducibility": {
            "enabled": False,
            "status": "skipped",
            "deterministic_fields_compared": [],
            "runtime_only_fields": ["aggregate_metrics.mean_latency_ms"],
            "mismatches": [],
        },
    }


def test_prompt_forbids_competitive_claims_without_matched_baselines() -> None:
    text = PROMPT_PATH.read_text(encoding="utf-8").lower()

    for required_text in (
        "do not claim",
        "superior",
        "wins",
        "standard-rag",
        "matched baseline",
        "dataset hashes",
        "case ids",
        "prompt/model metadata",
        "top-k",
        "command/version",
    ):
        assert required_text in text


def test_summary_conclusions_disclaim_superiority_without_matched_baselines(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "heph.json"
    output = tmp_path / "summary.md"
    _write_report(report_path, _single_heph_report())

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    summary = output.read_text(encoding="utf-8").lower()
    assert status == 0
    assert "not a superiority or head-to-head claim" in summary
    assert "matched baseline reports" in summary
    assert "shared dataset hashes" in summary
    assert "beats" not in summary
    assert "wins over" not in summary
    assert "outperforms" not in summary
    assert "standard-rag win" not in summary


def test_summary_compares_primitive_baselines_to_enhanced_modes(tmp_path: Path) -> None:
    dense = tmp_path / "dense.json"
    bm25 = tmp_path / "bm25.json"
    prf = tmp_path / "prf.json"
    output = tmp_path / "summary.md"
    _write_report(
        dense,
        _retrieval_report(
            report_id="dense-report",
            mode="dense",
            hit_rate=0.69,
            mrr=0.56,
            expected_recall=0.14,
            document_prefix=None,
        ),
    )
    _write_report(
        bm25,
        _retrieval_report(
            report_id="bm25-report",
            mode="bm25",
            hit_rate=0.64,
            mrr=0.50,
            expected_recall=0.12,
            document_prefix=None,
        ),
    )
    _write_report(
        prf,
        _retrieval_report(
            report_id="prf-report",
            mode="hybrid-prf",
            hit_rate=0.72,
            mrr=0.58,
            expected_recall=0.15,
            graded_ndcg_at_k=0.41,
            document_prefix="",
        ),
    )

    status = generate_benchmark_summary.main(
        [str(dense), str(bm25), str(prf), "--output", str(output)]
    )

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "## Matched Local Baseline Comparisons" in summary
    assert "`dense` (0.690 hit, 0.560 MRR) | `hybrid-prf`" in summary
    assert "`bm25` (0.640 hit, 0.500 MRR) | `hybrid-prf`" in summary
    assert "`dense` (0.690 hit, 0.560 MRR) | `bm25`" not in summary
    assert "Graded nDCG@k Delta" in summary


def test_summary_includes_same_case_frontier_across_tuning_knobs(tmp_path: Path) -> None:
    dense = tmp_path / "dense.json"
    prf = tmp_path / "prf.json"
    output = tmp_path / "summary.md"
    _write_report(
        dense,
        _retrieval_report(
            report_id="dense-frontier",
            mode="dense",
            hit_rate=0.69,
            mrr=0.56,
            expected_recall=0.14,
            dense_weight=1.5,
        ),
    )
    _write_report(
        prf,
        _retrieval_report(
            report_id="prf-frontier",
            mode="hybrid-prf",
            hit_rate=0.77,
            mrr=0.59,
            expected_recall=0.19,
            ndcg_at_k=0.45,
            dense_weight=1.25,
            document_prefix="",
        ),
    )

    status = generate_benchmark_summary.main([str(dense), str(prf), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "## Same-Case Frontier Comparisons" in summary
    assert "Best Primitive Baseline" in summary
    assert "`hybrid-prf` cm=2 dense=1.25 prf=0.1 hit=0.770 MRR=0.590" in summary
    assert "| +0.080 | +0.030 | +0.050 | +0.050 | n/a | 10 |" in summary
    assert "not a Codex or Factory Droid head-to-head result" in summary


def test_summary_compares_enterprise_rag_recall_to_official_snapshot(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "enterprise-rag.json"
    leaderboard_path = tmp_path / "leaderboard.csv"
    output = tmp_path / "summary.md"
    report = _retrieval_report(
        report_id="enterprise-rag-doc-bm25",
        mode="bm25-document",
        hit_rate=0.7404255319,
        mrr=0.584377744,
        expected_recall=0.6876418439,
        document_prefix="",
    )
    metadata = cast("dict[str, object]", report["metadata"])
    metadata["benchmark_type"] = "enterprise-rag"
    metadata["dataset"] = "enterprise-rag-bench"
    metadata["cases_sha256"] = "enterprise-cases-sha"
    benchmarks = cast("list[dict[str, object]]", report["benchmarks"])
    benchmark = benchmarks[0]
    benchmark["benchmark_type"] = "enterprise-rag"
    benchmark["dataset"] = "enterprise-rag-bench"
    aggregate_metrics = cast("dict[str, object]", report["aggregate_metrics"])
    aggregate_metrics["query_count"] = 470
    benchmark_metrics = cast("dict[str, object]", benchmark["metrics"])
    benchmark_metrics["query_count"] = 470
    _write_report(report_path, report)
    leaderboard_path.write_text(
        "\n".join(
            [
                "model,overall_score,correctness,completeness,recall,invalid_extra_docs,tags",
                "OpenClaw,68.22,81.6,72.86,79.02,0.47,",
                "BM25 + GPT-5.4,50.6,68.8,55.95,68.41,9.01,one_shot",
                "Vector text-embedding-3-large + GPT-5.4,30,40,40,46.03,8,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status = generate_benchmark_summary.main(
        [
            str(report_path),
            "--enterprise-rag-leaderboard-csv",
            str(leaderboard_path),
            "--output",
            str(output),
        ]
    )

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "## Official EnterpriseRAG Recall Comparison" in summary
    assert "`bm25-document`" in summary
    assert "68.76%" in summary
    assert "+0.35 pp" in summary
    assert "2/4" in summary
    assert "not a Codex or Factory Droid head-to-head" in summary


def test_summary_mentions_enterprise_rag_leaderboard_csv_when_missing(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "enterprise-rag.json"
    output = tmp_path / "summary.md"
    report = _retrieval_report(
        report_id="enterprise-rag-doc-bm25",
        mode="bm25-document",
        hit_rate=0.74,
        mrr=0.58,
        expected_recall=0.6876,
    )
    metadata = cast("dict[str, object]", report["metadata"])
    metadata["benchmark_type"] = "enterprise-rag"
    metadata["dataset"] = "enterprise-rag-bench"
    benchmarks = cast("list[dict[str, object]]", report["benchmarks"])
    benchmark = benchmarks[0]
    benchmark["benchmark_type"] = "enterprise-rag"
    benchmark["dataset"] = "enterprise-rag-bench"
    _write_report(report_path, report)

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "Pass `--enterprise-rag-leaderboard-csv`" in summary
