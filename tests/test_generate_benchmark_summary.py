from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts import generate_benchmark_summary


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _external_report(
    report_id: str,
    *,
    benchmark_type: str = "beir",
    dataset: str = "beir/fixture",
    status: str = "success",
    hit_rate: float = 1.0,
    mrr: float = 1.0,
    expected_recall: float = 1.0,
    precision_at_k: float | None = None,
    map_at_k: float | None = None,
    ndcg_at_k: float | None = None,
    graded_ndcg_at_k: float | None = None,
    latency_ms: float | None = 2.5,
    warnings: list[str] | None = None,
    errors: list[dict[str, object]] | None = None,
    threshold_failures: list[dict[str, object]] | None = None,
    schema_version: str = "external-runner-report-v1",
    cases_sha256: str | None = None,
    retrieval_mode: str | None = None,
) -> dict[str, object]:
    aggregate_metrics: dict[str, object] = {
        "hit_rate": hit_rate,
        "mrr": mrr,
        "expected_recall": expected_recall,
    }
    benchmark_metrics = dict(aggregate_metrics)
    optional_metrics = {
        "precision_at_k": precision_at_k,
        "map_at_k": map_at_k,
        "ndcg_at_k": ndcg_at_k,
        "graded_ndcg_at_k": graded_ndcg_at_k,
    }
    for name, value in optional_metrics.items():
        if value is not None:
            aggregate_metrics[name] = value
            benchmark_metrics[name] = value
    if latency_ms is not None:
        aggregate_metrics["mean_latency_ms"] = latency_ms
        aggregate_metrics["latency"] = {
            "mean_ms": latency_ms,
            "scope": "retrieval_only_per_query",
            "unit": "milliseconds",
        }
        benchmark_metrics["mean_latency_ms"] = latency_ms
        benchmark_metrics["latency"] = {
            "mean_ms": latency_ms,
            "scope": "retrieval_only_per_query",
            "unit": "milliseconds",
        }
    fixed_parameters: dict[str, object] = {
        "top_k": 5,
        "min_score": 0.1,
        "query_order": "case-file-order",
        "network_access": "disabled-after-materialization",
    }
    if retrieval_mode is not None:
        fixed_parameters["retrieval_mode"] = retrieval_mode
    metadata: dict[str, object] = {
        "runner": "scripts.run_external_benchmarks",
        "benchmark_type": benchmark_type,
        "dataset": dataset,
        "suite_path": "/tmp/fixture-suite",
        "fixed_parameters": fixed_parameters,
        "metric_formulas": {
            "hit_rate": "fraction of queries with an expected reference in top-k",
            "mrr": "mean reciprocal rank of the first expected reference",
            "expected_recall": "average retrieved expected references per query",
            "precision_at_k": "average binary precision@k",
            "map_at_k": "mean average precision@k",
            "ndcg_at_k": "mean normalized discounted cumulative gain@k",
            "graded_ndcg_at_k": "mean graded normalized discounted cumulative gain@k",
            "latency": "retrieval-only wall-clock milliseconds per query",
        },
        "runtime_only_fields": ["metadata.report_path", "aggregate_metrics.mean_latency_ms"],
        "prompt_path": "benchmarks/model-evaluation-prompt.md",
        "prompt_hash": "abc123",
        "model": "fixture-model",
    }
    if cases_sha256 is not None:
        metadata["cases_sha256"] = cases_sha256
    return {
        "schema_version": schema_version,
        "report_id": report_id,
        "status": status,
        "metadata": metadata,
        "benchmarks": [
            {
                "id": f"{benchmark_type}:{dataset}:rag",
                "benchmark_type": benchmark_type,
                "dataset": dataset,
                "status": status,
                "metrics": benchmark_metrics,
                "per_query_results": [
                    {
                        "case_id": "alpha",
                        "hit": hit_rate > 0,
                        "rank": 1 if hit_rate > 0 else None,
                        "expected_recall": expected_recall,
                    }
                ],
            }
        ],
        "aggregate_metrics": aggregate_metrics,
        "thresholds": {"hit_rate": 0.8, "mrr": 0.7, "expected_recall": 0.9},
        "threshold_failures": threshold_failures or [],
        "warnings": warnings or [],
        "errors": errors or [],
        "reproducibility": {
            "enabled": True,
            "status": "passed",
            "runtime_only_fields": ["metadata.report_path", "aggregate_metrics.mean_latency_ms"],
            "deterministic_fields_compared": ["metadata.dataset", "aggregate_metrics.hit_rate"],
            "mismatches": [],
        },
    }


def test_summary_aggregates_reports_without_mutating_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAISTOS_TEST_SECRET_SUMMARY", "summary-secret-token")
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    output = tmp_path / "summary.md"
    repeated_output = tmp_path / "summary-repeated.md"
    _write_report(
        first,
        _external_report(
            "beir:beir/fixture",
            warnings=["diagnostic token summary-secret-token must not leak"],
        ),
    )
    _write_report(
        second,
        _external_report(
            "standard-rag:ms-marco",
            benchmark_type="standard-rag",
            dataset="ms-marco",
            status="threshold_failed",
            hit_rate=0.5,
            mrr=0.25,
            expected_recall=0.75,
            latency_ms=10.0,
            threshold_failures=[{"metric": "hit_rate", "minimum": 0.8, "actual": 0.5}],
        ),
    )
    before = {_checksum(first), _checksum(second)}

    status = generate_benchmark_summary.main([str(first), str(second), "--output", str(output)])
    repeated_status = generate_benchmark_summary.main(
        [str(first), str(second), "--output", str(repeated_output)]
    )

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert repeated_status == 0
    assert summary == repeated_output.read_text(encoding="utf-8")
    assert before == {_checksum(first), _checksum(second)}
    assert "## Executive Summary" in summary
    assert "## Methodology" in summary
    assert "## Result Tables" in summary
    assert "## Per-Benchmark Analysis" in summary
    assert "## Statistical Analysis" in summary
    assert "## Run Disclosure" in summary
    assert "## Interpretation" in summary
    assert "## Recommendations" in summary
    assert (
        "| 1 | `beir:beir/fixture` | success | beir | beir/fixture | "
        "1.000 | 1.000 | 1.000 | n/a | n/a | n/a | n/a | 2.500 | passed |"
    ) in summary
    assert (
        "| 2 | `standard-rag:ms-marco` | threshold_failed | standard-rag | ms-marco | "
        "0.500 | 0.250 | 0.750 | n/a | n/a | n/a | n/a | 10.000 | passed |"
    ) in summary
    assert "Prompt/model metadata: `benchmarks/model-evaluation-prompt.md`" in summary
    assert "- Run count: 2" in summary
    assert "- Failed or gated run count: 1" in summary
    assert "Variance" in summary
    assert "summary-secret-token" not in summary
    assert "[REDACTED]" in summary


def test_summary_includes_matched_local_baseline_comparisons(tmp_path: Path) -> None:
    dense = tmp_path / "dense.json"
    hybrid = tmp_path / "hybrid.json"
    output = tmp_path / "summary.md"
    cases_sha256 = "a" * 64
    _write_report(
        dense,
        _external_report(
            "public-academic:dense",
            benchmark_type="public-academic",
            dataset="public-academic",
            hit_rate=0.8,
            mrr=0.7,
            expected_recall=0.8,
            ndcg_at_k=0.6,
            cases_sha256=cases_sha256,
            retrieval_mode="dense",
        ),
    )
    _write_report(
        hybrid,
        _external_report(
            "public-academic:hybrid",
            benchmark_type="public-academic",
            dataset="public-academic",
            hit_rate=1.0,
            mrr=0.95,
            expected_recall=1.0,
            ndcg_at_k=0.9,
            cases_sha256=cases_sha256,
            retrieval_mode="hybrid",
        ),
    )

    status = generate_benchmark_summary.main([str(dense), str(hybrid), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "## Matched Local Baseline Comparisons" in summary
    assert "local retrieval-mode comparisons only" in summary
    assert "| public-academic | `aaaaaaaaaaaa` | `dense` (0.800 hit, 0.700 MRR) |" in summary
    assert (
        "| `hybrid` (1.000 hit, 0.950 MRR) | +0.200 | +0.250 | +0.200 | +0.300 | n/a |"
    ) in summary


def test_summary_includes_valid_failed_report_errors(tmp_path: Path) -> None:
    report_path = tmp_path / "failed.json"
    output = tmp_path / "summary.md"
    _write_report(
        report_path,
        _external_report(
            "beir:beir/fixture",
            status="error",
            hit_rate=0.0,
            mrr=0.0,
            expected_recall=0.0,
            latency_ms=0.0,
            errors=[
                {
                    "code": "input_not_found",
                    "message": "benchmark cases file does not exist",
                    "remediation": "materialize inputs first",
                }
            ],
        ),
    )

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "Status: `error`" in summary
    assert "input_not_found" in summary
    assert "benchmark cases file does not exist" in summary
    assert "- Failed or gated run count: 1" in summary


def test_summary_rejects_unsupported_competitive_language(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report_path = tmp_path / "unsupported-language.json"
    output = tmp_path / "summary.md"
    _write_report(
        report_path,
        _external_report(
            "beir:beir/fixture",
            warnings=["Heph beats Codex and is objectively superior."],
        ),
    )

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    captured = capsys.readouterr()
    assert status == 2
    assert "unsupported_claim_language" in captured.err
    assert "beats" in captured.err
    assert not output.exists()


def test_summary_excludes_zero_query_reports_from_aggregate_means(
    tmp_path: Path,
) -> None:
    measured_report = tmp_path / "measured.json"
    zero_query_report = tmp_path / "zero-query.json"
    output = tmp_path / "summary.md"
    _write_report(
        measured_report,
        _external_report(
            "beir:measured",
            hit_rate=0.8,
            mrr=0.6,
            expected_recall=0.7,
            latency_ms=5.0,
        ),
    )
    zero_payload = _external_report(
        "standard-rag:zero-query",
        benchmark_type="standard-rag",
        dataset="ms-marco",
        hit_rate=1.0,
        mrr=1.0,
        expected_recall=1.0,
        latency_ms=0.0,
    )
    zero_payload["benchmarks"] = [
        {
            "id": "standard-rag:zero-query:rag",
            "benchmark_type": "standard-rag",
            "dataset": "ms-marco",
            "status": "success",
            "metrics": {
                "hit_rate": 1.0,
                "mrr": 1.0,
                "expected_recall": 1.0,
                "mean_latency_ms": 0.0,
            },
            "per_query_results": [],
        }
    ]
    _write_report(zero_query_report, zero_payload)

    status = generate_benchmark_summary.main(
        [str(measured_report), str(zero_query_report), "--output", str(output)]
    )

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert (
        "- Mean hit rate across aggregate-eligible reports (denominator 1/2): 0.800"
    ) in summary
    assert (
        "- Aggregate statistics denominator: 1 eligible report(s) out of 2 supplied report(s)."
    ) in summary
    assert (
        "| 2 | `standard-rag:zero-query` | success | standard-rag | ms-marco | "
        "n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | passed | 0 | "
        "excluded: zero measured queries |"
    ) in summary
    assert ("| `standard-rag:zero-query` | success | 0 | zero measured queries |") in summary
    assert "| Hit Rate | 1 | 0.800 | 0.800 | 0.800 | 0.800 |" in summary


def test_summary_infers_native_query_count_from_wrapped_rag_report(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "native.json"
    output = tmp_path / "summary.md"
    native_payload = _external_report(
        "heph-native:academic",
        benchmark_type="heph-native",
        dataset="academic",
        hit_rate=0.75,
        mrr=0.5,
        expected_recall=0.875,
        latency_ms=3.0,
    )
    native_payload["benchmarks"] = [
        {
            "id": "heph-native:academic",
            "benchmark_type": "heph-native",
            "dataset": "academic",
            "status": "success",
            "metrics": {
                "hit_rate": 0.75,
                "mrr": 0.5,
                "expected_recall": 0.875,
                "mean_latency_ms": 3.0,
            },
            "native_suite_report": {
                "rag": {
                    "cases": 4,
                    "hit_rate": 0.75,
                    "mean_reciprocal_rank": 0.5,
                    "mean_expected_recall": 0.875,
                    "mean_latency_ms": 3.0,
                }
            },
        }
    ]
    _write_report(report_path, native_payload)

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert (
        "- Mean hit rate across aggregate-eligible reports (denominator 1/1): 0.750"
    ) in summary
    assert (
        "| 1 | `heph-native:academic` | success | heph-native | academic | "
        "0.750 | 0.500 | 0.875 | n/a | n/a | n/a | n/a | 3.000 | passed | 4 | eligible |"
    ) in summary


def test_summary_warns_for_missing_optional_latency(tmp_path: Path) -> None:
    report_path = tmp_path / "partial.json"
    output = tmp_path / "summary.md"
    _write_report(report_path, _external_report("beir:beir/fixture", latency_ms=None))

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert (
        "| 1 | `beir:beir/fixture` | success | beir | beir/fixture | "
        "1.000 | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | passed |"
    ) in summary
    assert "missing optional latency metric" in summary


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ("{not json", "malformed_json"),
        (_external_report("bad:schema", schema_version="unknown-v1"), "unsupported_schema"),
        (
            {
                "schema_version": "external-runner-report-v1",
                "report_id": "missing:metrics",
                "status": "success",
                "metadata": {"benchmark_type": "beir", "dataset": "beir/fixture"},
                "benchmarks": [],
                "aggregate_metrics": {"hit_rate": 1.0},
                "warnings": [],
                "errors": [],
                "reproducibility": {"status": "skipped"},
            },
            "missing_required_metric",
        ),
    ],
)
def test_summary_rejects_malformed_or_partial_reports(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: str | dict[str, object],
    expected_code: str,
) -> None:
    report_path = tmp_path / "report.json"
    output = tmp_path / "summary.md"
    if isinstance(payload, str):
        report_path.write_text(payload, encoding="utf-8")
    else:
        _write_report(report_path, payload)

    status = generate_benchmark_summary.main([str(report_path), "--output", str(output)])

    captured = capsys.readouterr()
    assert status == 2
    assert expected_code in captured.err
    assert not output.exists()


def test_summary_rejects_duplicate_report_ids(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_report(first, _external_report("beir:beir/fixture"))
    _write_report(second, _external_report("beir:beir/fixture"))

    status = generate_benchmark_summary.main([str(first), str(second)])

    captured = capsys.readouterr()
    assert status == 2
    assert "duplicate_report_id" in captured.err


def test_visualization_request_degrades_without_extra(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_path = tmp_path / "report.json"
    output = tmp_path / "summary.md"
    _write_report(report_path, _external_report("beir:beir/fixture"))
    original_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, package: str | None = None) -> object | None:
        if name == "matplotlib":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    status = generate_benchmark_summary.main(
        [str(report_path), "--output", str(output), "--visualize"]
    )

    summary = output.read_text(encoding="utf-8")
    assert status == 0
    assert "Visualization extras were requested but are not installed" in summary
