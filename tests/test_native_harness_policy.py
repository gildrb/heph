from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts import claim_report_envelope


def _minimal_claim_report(*, warnings: list[str] | None = None) -> dict[str, object]:
    hashes = {
        "cases_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "qrels_sha256": "c" * 64,
        "corpus_sha256": "d" * 64,
    }
    return {
        "schema_version": "external-runner-report-v1",
        "report_id": "policy-fixture",
        "status": "success",
        "metadata": {
            "runner": "scripts.run_external_benchmarks",
            "benchmark_type": "beir",
            "dataset": "beir/fixture",
            "fixed_parameters": {
                "top_k": 1,
                "candidate_multiplier": 1,
                "network_access": "disabled-after-materialization",
            },
            "metric_formulas": {
                "hit_rate": "fraction of queries with support in top-k",
                "mrr": "mean reciprocal rank",
                "expected_recall": "mean expected reference recall",
            },
            "model": "retrieval-only:no-generation",
            **hashes,
        },
        "benchmarks": [
            {
                "id": "policy-fixture",
                "benchmark_type": "beir",
                "dataset": "beir/fixture",
                "status": "success",
                "metrics": {
                    "hit_rate": 1.0,
                    "mrr": 1.0,
                    "expected_recall": 1.0,
                    "query_count": 1,
                },
                "per_query_results": [
                    {
                        "case_id": "opaque-1",
                        "hit": True,
                        "rank": 1,
                        "expected_recall": 1.0,
                    }
                ],
            }
        ],
        "aggregate_metrics": {
            "hit_rate": 1.0,
            "mrr": 1.0,
            "expected_recall": 1.0,
            "query_count": 1,
            "latency": {
                "scope": "retrieval_only_per_query",
                "unit": "milliseconds",
                "mean_ms": 1.0,
            },
        },
        "thresholds": {},
        "threshold_failures": [],
        "warnings": warnings or [],
        "errors": [],
        "reproducibility": {
            "enabled": True,
            "status": "passed",
            "deterministic_fields_compared": ["metadata.dataset", "aggregate_metrics.hit_rate"],
            "runtime_only_fields": [],
            "mismatches": [],
        },
    }


def test_claim_policy_rejects_qrels_or_expected_answer_leakage() -> None:
    report = _minimal_claim_report()
    benchmarks = cast("list[dict[str, object]]", report["benchmarks"])
    benchmark = benchmarks[0]
    benchmark["expected_topics"] = ["hidden private topic"]
    benchmark["forbidden_topics"] = ["private distractor"]
    per_query = benchmark["per_query_results"]
    assert isinstance(per_query, list)
    first_result = per_query[0]
    assert isinstance(first_result, dict)
    first_result = cast("dict[str, object]", first_result)
    first_result["expected"] = ["materials/hidden-answer.md"]
    first_result["expected_text"] = "hidden answer text"

    finalized = claim_report_envelope.finalize_claim_report(
        report,
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )

    envelope = cast("dict[str, object]", finalized["claim_envelope"])
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    leakage = cast("dict[str, object]", claim_policy["leakage"])
    findings = cast("list[dict[str, object]]", leakage["findings"])
    reasons = cast("list[str]", envelope["ineligibility_reasons"])
    assert envelope["claim_eligible"] is False
    assert "claim leakage scan failed" in reasons
    assert leakage["status"] == "failed"
    finding_keys = {finding["key"] for finding in findings}
    assert {"expected", "expected_text", "expected_topics", "forbidden_topics"} <= finding_keys


def test_claim_policy_redacts_seeded_secrets_before_report_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAISTOS_TEST_POLICY_TOKEN", "policy-secret-value")

    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(warnings=["diagnostic token policy-secret-value must redact"]),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    serialized = json.dumps(finalized, ensure_ascii=False, sort_keys=True)
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    redaction = cast("dict[str, object]", claim_policy["redaction"])

    assert "policy-secret-value" not in serialized
    assert "[REDACTED]" in serialized
    assert redaction["status"] == "passed"


def test_claim_policy_validator_rejects_failed_redaction_status() -> None:
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    redaction = cast("dict[str, object]", claim_policy["redaction"])
    redaction["status"] = "failed"

    validation = claim_report_envelope.validate_claim_report_envelope(
        finalized,
        require_claim_eligible=False,
    )

    assert "claim redaction policy failed" in validation.errors


def test_claim_policy_rejects_fixture_private_terms() -> None:
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(warnings=["fixture_private_course appeared in runtime output"]),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )

    envelope = cast("dict[str, object]", finalized["claim_envelope"])
    reasons = cast("list[str]", envelope["ineligibility_reasons"])
    assert envelope["claim_eligible"] is False
    assert "claim leakage scan failed" in reasons


def test_native_harness_policy_file_stays_outside_generated_artifacts(tmp_path: Path) -> None:
    report_path = tmp_path / "policy.json"
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    report_path.write_text(json.dumps(finalized, sort_keys=True) + "\n", encoding="utf-8")

    assert report_path.is_file()
    assert ".artifacts" not in report_path.parts
