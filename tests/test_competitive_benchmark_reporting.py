from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from scripts import benchmark_public_targets, claim_report_envelope, generate_benchmark_summary

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "benchmarks" / "model-evaluation-prompt.md"


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _refresh_projection_hash(report: dict[str, object]) -> None:
    projection_sha256 = claim_report_envelope.deterministic_projection_sha256(report)
    envelope = cast("dict[str, object]", report["claim_envelope"])
    determinism = cast("dict[str, object]", envelope["determinism"])
    deterministic_projection = cast("dict[str, object]", report["deterministic_projection"])
    determinism["projection_sha256"] = projection_sha256
    deterministic_projection["sha256"] = projection_sha256


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
    assert "Selected Primitive Baseline" in summary
    assert "`hybrid-prf` cm=2 dense=1.25 prf=0.1 hit=0.770 MRR=0.590" in summary
    assert "| +0.080 | +0.030 | +0.050 | +0.050 | n/a | 10 |" in summary
    assert "not a Codex or Factory Droid head-to-head result" in summary
    assert "Best " not in summary


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


def _enterprise_rag_report(
    *,
    report_id: str,
    mode: str,
    hit_rate: float,
    mrr: float,
    expected_recall: float,
) -> dict[str, object]:
    report = _retrieval_report(
        report_id=report_id,
        mode=mode,
        hit_rate=hit_rate,
        mrr=mrr,
        expected_recall=expected_recall,
        document_prefix="",
    )
    metadata = cast("dict[str, object]", report["metadata"])
    metadata.update(
        {
            "benchmark_type": "enterprise-rag",
            "dataset": "enterprise-rag-bench",
            "cases_sha256": "a" * 64,
            "manifest_sha256": "b" * 64,
            "qrels_sha256": "c" * 64,
            "corpus_sha256": "d" * 64,
            "scoring_protocol_version": "enterprise-rag-document-recall-v1",
            "dependency_lock_sha256": "e" * 64,
            "latency_scope": "retrieval_only_per_query",
            "command_invocation": (
                "uv run python -m scripts.run_external_benchmarks enterprise-rag "
                "enterprise-rag-bench --retrieval-mode " + mode
            ),
            "model": "fixture-retrieval-only",
            "network_state": "disabled-after-materialization",
            "cache_state": "warm-local-cache",
            "prompt_hash": "retrieval-only-no-prompt",
            "permission_scope": "public-benchmark-materials",
        }
    )
    fixed_parameters = cast("dict[str, object]", metadata["fixed_parameters"])
    fixed_parameters["top_k"] = 10
    fixed_parameters["retrieval_mode"] = mode
    aggregate_metrics = cast("dict[str, object]", report["aggregate_metrics"])
    aggregate_metrics["query_count"] = 2
    benchmark = cast("list[dict[str, object]]", report["benchmarks"])[0]
    benchmark["benchmark_type"] = "enterprise-rag"
    benchmark["dataset"] = "enterprise-rag-bench"
    benchmark["per_query_results"] = [
        {
            "case_id": "alpha",
            "hit": True,
            "rank": 1,
            "reciprocal_rank": 1.0,
            "expected_recall": 1.0,
        },
        {
            "case_id": "beta",
            "hit": True,
            "rank": 1,
            "reciprocal_rank": 1.0,
            "expected_recall": 1.0,
        },
    ]
    benchmark_metrics = cast("dict[str, object]", benchmark["metrics"])
    benchmark_metrics["query_count"] = 2
    report["thresholds"] = {"hit_rate": 0.0, "mrr": 0.0, "expected_recall": 0.0}
    report["reproducibility"] = {
        "enabled": True,
        "status": "passed",
        "runtime_only_fields": [
            "metadata.report_path",
            "metadata.command_invocation",
            "aggregate_metrics.mean_latency_ms",
        ],
        "deterministic_fields_compared": [
            "metadata.dataset",
            "metadata.fixed_parameters",
            "aggregate_metrics.expected_recall",
        ],
        "mismatches": [],
    }
    return claim_report_envelope.finalize_claim_report(
        report,
        command=str(metadata["command_invocation"]),
    )


def _write_public_target_inputs(
    tmp_path: Path,
    *,
    current_expected_recall: float = 0.695,
) -> dict[str, Path]:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    raw_snapshot = tmp_path / "enterprise-rag-leaderboard.csv"
    snapshot = tmp_path / "snapshot.json"
    baseline_ledger = tmp_path / "baseline-ledger.json"
    dataset_ledger = tmp_path / "dataset-ledger.json"
    evaluation_plan = tmp_path / "evaluation-plan.json"
    output = tmp_path / "claim-gate.json"

    baseline_report = _enterprise_rag_report(
        report_id="enterprise-rag-bm25-document-baseline",
        mode="bm25-document",
        hit_rate=0.74,
        mrr=0.58,
        expected_recall=0.684,
    )
    current_report = _enterprise_rag_report(
        report_id="enterprise-rag-hybrid-document-current",
        mode="hybrid-document",
        hit_rate=0.75,
        mrr=0.59,
        expected_recall=current_expected_recall,
    )
    _write_report(baseline, baseline_report)
    _write_report(current, current_report)
    raw_snapshot.write_text(
        "\n".join(
            [
                "model,recall,overall_score,dataset,split,scope",
                "OpenClaw,79.02,68.22,enterprise-rag-bench,test,document-retrieval",
                "BM25 + GPT-5.4,68.41,50.6,enterprise-rag-bench,test,document-retrieval",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_report(
        snapshot,
        {
            "schema_version": "enterprise-rag-public-snapshot-v1",
            "snapshot_id": "enterprise-rag-bench-leaderboard-2026-05-18",
            "target_role": "primary",
            "benchmark_type": "enterprise-rag",
            "dataset": "enterprise-rag-bench",
            "split": "test",
            "scope": "document-retrieval",
            "source_url": "https://example.org/enterprise-rag/leaderboard.csv",
            "request_command": (
                "curl -fL https://example.org/enterprise-rag/leaderboard.csv "
                "-o enterprise-rag-leaderboard.csv"
            ),
            "retrieved_at": "2026-05-18T00:00:00Z",
            "http_status": 200,
            "raw_path": raw_snapshot.name,
            "raw_sha256": _sha256(raw_snapshot),
            "byte_count": raw_snapshot.stat().st_size,
            "row_count": 2,
            "source_schema_version": "enterprise-rag-leaderboard-csv-v1",
            "rank_metric": "recall",
            "rank_order": "descending",
            "metric_units": {"recall": "percent"},
            "column_mapping": {
                "system_label": "model",
                "rank_metric": "recall",
                "dataset": "dataset",
                "split": "split",
                "scope": "scope",
            },
            "required_columns": [
                "model",
                "recall",
                "dataset",
                "split",
                "scope",
            ],
        },
    )
    baseline_metadata = cast("dict[str, object]", baseline_report["metadata"])
    baseline_parameters = cast("dict[str, object]", baseline_metadata["fixed_parameters"])
    matched_metadata = {
        "benchmark_type": baseline_metadata["benchmark_type"],
        "dataset": baseline_metadata["dataset"],
        "cases_sha256": baseline_metadata["cases_sha256"],
        "manifest_sha256": baseline_metadata["manifest_sha256"],
        "qrels_sha256": baseline_metadata["qrels_sha256"],
        "corpus_sha256": baseline_metadata["corpus_sha256"],
        "scoring_protocol_version": baseline_metadata["scoring_protocol_version"],
        "top_k": baseline_parameters["top_k"],
        "candidate_multiplier": baseline_parameters["candidate_multiplier"],
        "candidate_depth": (
            cast("int", baseline_parameters["top_k"])
            * cast("int", baseline_parameters["candidate_multiplier"])
        ),
        "latency_scope": baseline_metadata["latency_scope"],
        "dependency_lock_sha256": baseline_metadata["dependency_lock_sha256"],
        "model": baseline_metadata["model"],
        "prompt_hash": baseline_metadata["prompt_hash"],
        "metric_formulas_sha256": benchmark_public_targets.metric_formulas_sha256(baseline_report),
        "cache_state": baseline_metadata["cache_state"],
        "network_state": baseline_metadata["network_state"],
        "permission_scope": baseline_metadata["permission_scope"],
    }
    _write_report(
        baseline_ledger,
        {
            "schema_version": "baseline-ledger-v1",
            "baseline_id": "enterprise-rag-bm25-document",
            "baseline_version": "enterprise-rag-bm25-document-v1",
            "target_role": "primary",
            "artifact_path": baseline.name,
            "artifact_sha256": _sha256(baseline),
            "frozen": True,
            "benchmark_type": "enterprise-rag",
            "dataset": "enterprise-rag-bench",
            "retrieval_mode": "bm25-document",
            "selected_metrics": [
                "aggregate_metrics.expected_recall",
                "aggregate_metrics.hit_rate",
                "aggregate_metrics.mrr",
            ],
            "matched_metadata": matched_metadata,
        },
    )
    _write_report(
        dataset_ledger,
        {
            "schema_version": "dataset-version-ledger-v1",
            "dataset_id": "enterprise-rag-bench",
            "current_version": "enterprise-rag-bench-v2026-05-18",
            "entries": [
                {
                    "version": "enterprise-rag-bench-v2026-05-18",
                    "role": "final_evaluation",
                    "manifest_sha256": "b" * 64,
                    "cases_sha256": "a" * 64,
                    "qrels_sha256": "c" * 64,
                    "corpus_sha256": "d" * 64,
                    "diff_summary": "Initial frozen public target fixture.",
                    "edit_rationale": "Establish the primary public target before claims.",
                    "recorded_before_claim": True,
                }
            ],
        },
    )
    _write_report(
        evaluation_plan,
        {
            "schema_version": "evaluation-plan-v1",
            "plan_id": "enterprise-rag-top10-plan-v1",
            "primary_target": "enterprise-rag-bench",
            "target_role": "primary",
            "declared_before_results": True,
            "primary_metrics": ["aggregate_metrics.expected_recall"],
            "secondary_metrics": ["aggregate_metrics.hit_rate", "aggregate_metrics.mrr"],
            "top_k_values": [10],
            "candidate_depth_values": [20],
            "statistical_method": "paired bootstrap over per-query rows when available",
            "run_policy": "single deterministic run over frozen inputs",
            "seed_policy": [0],
            "mode_selection_policy": "mode must be selected before final claim generation",
            "failure_handling": "regressions beyond tolerance block claim generation",
            "public_rank_target": {
                "metric": "aggregate_metrics.expected_recall",
                "rank_metric": "recall",
                "max_rank_in_snapshot": 10,
            },
            "known_public_target": {
                "optimized_against_public_target": True,
                "limitation": (
                    "EnterpriseRAG-Bench is a known public target; this is not evidence "
                    "of broad retrieval generalization without secondary gates."
                ),
            },
            "baseline_improvement": {
                "baseline_id": "enterprise-rag-bm25-document",
                "primary_metric": "aggregate_metrics.expected_recall",
                "minimum_delta": 0.001,
                "tolerance": 0.0,
                "guardrail_metrics": [
                    {"metric": "aggregate_metrics.hit_rate", "tolerance": 0.0},
                    {"metric": "aggregate_metrics.mrr", "tolerance": 0.0},
                ],
            },
        },
    )
    return {
        "baseline": baseline,
        "current": current,
        "raw_snapshot": raw_snapshot,
        "snapshot": snapshot,
        "baseline_ledger": baseline_ledger,
        "dataset_ledger": dataset_ledger,
        "evaluation_plan": evaluation_plan,
        "output": output,
    }


def test_public_target_claim_gate_records_baseline_snapshot_and_plan_evidence(
    tmp_path: Path,
) -> None:
    paths = _write_public_target_inputs(tmp_path)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
            "--output",
            str(paths["output"]),
        ]
    )

    payload = json.loads(paths["output"].read_text(encoding="utf-8"))
    baseline_sha = _sha256(paths["baseline"])
    snapshot_sha = _sha256(paths["raw_snapshot"])
    assert status == 0
    assert payload["schema_version"] == "public-target-claim-gate-v1"
    assert payload["status"] == "passed"
    assert payload["baseline"]["pre_sha256"] == baseline_sha
    assert payload["baseline"]["post_sha256"] == baseline_sha
    assert payload["baseline"]["immutable"] is True
    assert payload["public_snapshot"]["raw_sha256"] == snapshot_sha
    assert payload["public_snapshot"]["target_role"] == "primary"
    assert payload["public_snapshot"]["source_schema_version"] == (
        "enterprise-rag-leaderboard-csv-v1"
    )
    assert payload["public_snapshot"]["rank_metric"] == "recall"
    assert payload["dataset_version"]["version"] == "enterprise-rag-bench-v2026-05-18"
    assert payload["evaluation_plan"]["predeclared"] is True
    assert payload["evaluation_plan"]["public_rank_target"]["max_rank_in_snapshot"] == 10
    assert payload["baseline_improvement"]["primary_metric_delta"] > 0
    assert payload["statistical_evidence"]["status"] == "passed"
    assert payload["statistical_evidence"]["pairing"] == "paired"
    assert payload["statistical_evidence"]["sample_size"] == 2
    assert (
        payload["statistical_evidence"]["methods"]["aggregate_metrics.expected_recall"]["method"]
        == "paired_empirical_ci"
    )
    assert payload["run_disclosure"]["run_count"] == 2
    assert payload["run_disclosure"]["failed_count"] == 0
    assert payload["claim_language"]["status"] == "passed"
    assert payload["known_public_target"]["optimized_against_public_target"] is True
    assert (
        "not evidence of broad retrieval generalization"
        in payload["known_public_target"]["limitation"]
    )
    public_summary = cast("dict[str, object]", payload["public_comparison_summary"])
    current_rank = public_summary["current_rank_in_snapshot"]
    assert isinstance(current_rank, int)
    assert current_rank <= 10
    assert public_summary["rank_passed"] is True
    assert public_summary["rank_target"] == {
        "metric": "aggregate_metrics.expected_recall",
        "rank_metric": "recall",
        "max_rank_in_snapshot": 10,
    }


def test_public_target_claim_gate_rejects_rank_outside_top10_target(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    paths["raw_snapshot"].write_text(
        "\n".join(
            [
                "model,recall,overall_score,dataset,split,scope",
                "Rank 1,90.00,90.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 2,88.00,88.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 3,86.00,86.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 4,84.00,84.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 5,82.00,82.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 6,80.00,80.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 7,78.00,78.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 8,76.00,76.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 9,74.00,74.00,enterprise-rag-bench,test,document-retrieval",
                "Rank 10,70.00,70.00,enterprise-rag-bench,test,document-retrieval",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    snapshot = json.loads(paths["snapshot"].read_text(encoding="utf-8"))
    snapshot["raw_sha256"] = _sha256(paths["raw_snapshot"])
    snapshot["byte_count"] = paths["raw_snapshot"].stat().st_size
    snapshot["row_count"] = 10
    _write_report(paths["snapshot"], snapshot)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
            "--output",
            str(paths["output"]),
        ]
    )

    payload = json.loads(paths["output"].read_text(encoding="utf-8"))
    captured = capsys.readouterr()
    public_summary = cast("dict[str, object]", payload["public_comparison_summary"])
    assert status == 1
    assert payload["status"] == "failed"
    assert public_summary["current_rank_in_snapshot"] == 11
    assert public_summary["rank_passed"] is False
    assert public_summary["rank_target"] == {
        "metric": "aggregate_metrics.expected_recall",
        "rank_metric": "recall",
        "max_rank_in_snapshot": 10,
    }
    assert "current rank 11 exceeds the predeclared public rank target of top 10" in captured.err


def test_public_target_claim_gate_rejects_unsupported_superiority_claim_text(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
            "--claim-text",
            "Hephaistos beats Codex and is the best system.",
            "--output",
            str(paths["output"]),
        ]
    )

    payload = json.loads(paths["output"].read_text(encoding="utf-8"))
    captured = capsys.readouterr()
    assert status == 1
    assert payload["claim_language"]["status"] == "failed"
    assert payload["claim_language"]["findings"][0]["term"] == "beats"
    assert "unsupported competitive language" in captured.err


def test_public_target_claim_gate_rejects_unpaired_per_query_rows(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    benchmark = cast("list[dict[str, object]]", current_report["benchmarks"])[0]
    per_query = cast("list[dict[str, object]]", benchmark["per_query_results"])
    per_query[1]["case_id"] = "renamed-beta"
    metadata = cast("dict[str, object]", current_report["metadata"])
    current_report = claim_report_envelope.finalize_claim_report(
        current_report,
        command=str(metadata["command_invocation"]),
    )
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "statistical evidence missing paired per-query rows" in captured.err


def test_public_target_claim_gate_rejects_incompatible_statistical_method(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    plan = json.loads(paths["evaluation_plan"].read_text(encoding="utf-8"))
    plan["statistical_method"] = "compare aggregate percentages only"
    _write_report(paths["evaluation_plan"], plan)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "statistical_method" in captured.err
    assert "paired" in captured.err


def test_public_target_claim_gate_rejects_missing_matched_prompt_metadata(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    ledger = json.loads(paths["baseline_ledger"].read_text(encoding="utf-8"))
    matched_metadata = cast("dict[str, object]", ledger["matched_metadata"])
    del matched_metadata["prompt_hash"]
    _write_report(paths["baseline_ledger"], ledger)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "matched_metadata is missing 'prompt_hash'" in captured.err


def test_public_target_verify_report_command_checks_envelope_independently(
    tmp_path: Path,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    metadata = cast("dict[str, object]", current_report["metadata"])
    output = tmp_path / "verify-report.json"

    status = benchmark_public_targets.main(
        [
            "verify-report",
            "--report",
            str(paths["current"]),
            "--command-invocation",
            str(metadata["command_invocation"]),
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["schema_version"] == "claim-report-envelope-verification-v1"
    assert payload["status"] == "passed"
    assert payload["claim_eligible"] is True
    assert payload["errors"] == []


def test_public_target_verify_report_rejects_stale_dirty_state_fingerprint(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    metadata = cast("dict[str, object]", current_report["metadata"])
    envelope = cast("dict[str, object]", current_report["claim_envelope"])
    reproducibility = cast("dict[str, object]", envelope["reproducibility"])
    git = cast("dict[str, object]", reproducibility["git"])
    git["dirty_state_sha256"] = "0" * 64
    _refresh_projection_hash(current_report)
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "verify-report",
            "--report",
            str(paths["current"]),
            "--command-invocation",
            str(metadata["command_invocation"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "dirty state fingerprint does not match checkout" in captured.err


def test_public_target_claim_gate_rejects_changed_frozen_baseline(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    paths["baseline"].write_text(
        paths["baseline"].read_text(encoding="utf-8").replace("0.684", "0.650"),
        encoding="utf-8",
    )

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "baseline_hash_mismatch" in captured.err


def test_public_target_claim_gate_rejects_snapshot_without_rank_mapping(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    snapshot = json.loads(paths["snapshot"].read_text(encoding="utf-8"))
    column_mapping = cast("dict[str, object]", snapshot["column_mapping"])
    del column_mapping["rank_metric"]
    _write_report(paths["snapshot"], snapshot)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "snapshot_schema_invalid" in captured.err


def test_public_target_claim_gate_rejects_missing_baseline_improvement(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path, current_expected_recall=0.684)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "primary improvement did not meet the predeclared minimum delta" in captured.err


def test_public_target_claim_gate_rejects_dataset_ledger_hash_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    dataset_ledger = json.loads(paths["dataset_ledger"].read_text(encoding="utf-8"))
    entry = cast("dict[str, object]", cast("list[object]", dataset_ledger["entries"])[0])
    entry["cases_sha256"] = "f" * 64
    _write_report(paths["dataset_ledger"], dataset_ledger)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "matched metadata did not match baseline/dataset ledger" in captured.err


def test_public_target_claim_gate_rejects_snapshot_row_scope_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    paths["raw_snapshot"].write_text(
        "\n".join(
            [
                "model,recall,overall_score,dataset,split,scope",
                "OpenClaw,79.02,68.22,enterprise-rag-bench,test,answer-generation",
                "BM25 + GPT-5.4,68.41,50.6,enterprise-rag-bench,test,answer-generation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    snapshot = json.loads(paths["snapshot"].read_text(encoding="utf-8"))
    snapshot["raw_sha256"] = _sha256(paths["raw_snapshot"])
    snapshot["byte_count"] = paths["raw_snapshot"].stat().st_size
    _write_report(paths["snapshot"], snapshot)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "snapshot_row_mismatch" in captured.err


def test_public_target_claim_gate_rejects_failed_current_report(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    current_report["status"] = "error"
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "claim_report_not_success" in captured.err


def test_public_target_claim_gate_rejects_stale_current_report_envelope(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    aggregate_metrics = cast("dict[str, object]", current_report["aggregate_metrics"])
    aggregate_metrics["mrr"] = 0.99
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "claim_report_envelope_invalid" in captured.err
    assert "deterministic projection SHA-256 is stale" in captured.err


def test_public_target_claim_gate_rejects_lowered_threshold_without_new_version(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    thresholds = cast("dict[str, object]", current_report["thresholds"])
    thresholds["hit_rate"] = 0.1
    profile = cast("dict[str, object]", current_report["threshold_profile"])
    profile["thresholds"] = dict(thresholds)
    profile["previous_profile"] = {
        "version": profile["version"],
        "thresholds": {"hit_rate": 0.9, "mrr": 0.0, "expected_recall": 0.0},
    }
    metadata = cast("dict[str, object]", current_report["metadata"])
    current_report = claim_report_envelope.finalize_claim_report(
        current_report,
        command=str(metadata["command_invocation"]),
    )
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "claim_report_envelope_invalid" in captured.err
    assert "weakened thresholds require a new threshold_profile version" in captured.err


def test_public_target_claim_gate_rejects_unversioned_known_limit(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    current_report["known_limits"] = {
        "schema_version": claim_report_envelope.KNOWN_LIMITS_SCHEMA_VERSION,
        "policy_version": claim_report_envelope.KNOWN_LIMITS_POLICY_VERSION,
        "entries": [{"id": "fixture-gap"}],
    }
    metadata = cast("dict[str, object]", current_report["metadata"])
    current_report = claim_report_envelope.finalize_claim_report(
        current_report,
        command=str(metadata["command_invocation"]),
    )
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "claim_report_envelope_invalid" in captured.err
    assert "known_limits entry 0 missing meaningful string field 'version'" in captured.err


def test_public_target_claim_gate_rejects_non_boolean_known_limit_claim_blocking(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    current_report["known_limits"] = {
        "schema_version": claim_report_envelope.KNOWN_LIMITS_SCHEMA_VERSION,
        "policy_version": claim_report_envelope.KNOWN_LIMITS_POLICY_VERSION,
        "entries": [
            {
                "id": "fixture-gap",
                "version": "fixture-gap-v1",
                "rationale": "Exercise known-limit type validation.",
                "limitation": "This known limit is a negative fixture.",
                "recorded_before_claim": True,
                "claim_blocking": "false",
            }
        ],
    }
    metadata = cast("dict[str, object]", current_report["metadata"])
    current_report = claim_report_envelope.finalize_claim_report(
        current_report,
        command=str(metadata["command_invocation"]),
    )
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "claim_report_envelope_invalid" in captured.err
    assert "known_limits entry 0 claim_blocking must be boolean" in captured.err


def test_public_target_claim_gate_rejects_unplanned_candidate_depth(
    tmp_path: Path,
    capsys,
) -> None:
    paths = _write_public_target_inputs(tmp_path)
    current_report = json.loads(paths["current"].read_text(encoding="utf-8"))
    metadata = cast("dict[str, object]", current_report["metadata"])
    fixed_parameters = cast("dict[str, object]", metadata["fixed_parameters"])
    fixed_parameters["candidate_multiplier"] = 3
    current_report = claim_report_envelope.finalize_claim_report(
        current_report,
        command=str(metadata["command_invocation"]),
    )
    _write_report(paths["current"], current_report)

    status = benchmark_public_targets.main(
        [
            "claim-gate",
            "--baseline-ledger",
            str(paths["baseline_ledger"]),
            "--current-report",
            str(paths["current"]),
            "--public-snapshot",
            str(paths["snapshot"]),
            "--dataset-ledger",
            str(paths["dataset_ledger"]),
            "--evaluation-plan",
            str(paths["evaluation_plan"]),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "current run used an unplanned top-k or candidate-depth value" in captured.err
