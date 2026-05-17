from __future__ import annotations

import json
import socket
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from hephaistos.armory.storage import initialize
from scripts import run_external_benchmarks


def _write_jsonl(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_report(path: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _as_str(value: object) -> str:
    assert isinstance(value, str)
    return value


def _make_armory(root: Path) -> Path:
    armory = root / "armory"
    initialize(armory)
    (armory / "materials" / "alpha.md").write_text(
        "Alpha receptor signaling material explains ligand binding and clinical retrieval.\n",
        encoding="utf-8",
    )
    (armory / "materials" / "beta.md").write_text(
        "Beta cache invalidation material is a plausible systems distractor.\n",
        encoding="utf-8",
    )
    return armory


def _make_external_suite(root: Path, cases: Sequence[dict[str, object]]) -> Path:
    suite = root / "suite"
    _make_armory(suite)
    _write_jsonl(suite / "rag.jsonl", cases)
    return suite


def _passing_cases() -> list[dict[str, object]]:
    return [
        {
            "id": "alpha",
            "domain": "fixture",
            "task": "single-source-retrieval",
            "query": "alpha receptor signaling ligand binding",
            "expected": ["materials/alpha.md"],
            "forbidden_before_expected": ["materials/beta.md"],
            "top_k": 9,
        }
    ]


def test_runner_executes_materialized_beir_suite_with_required_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "reports" / "external.json"
    monkeypatch.setenv("HEPHAISTOS_TEST_SECRET", "sentinel-secret-value")

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--top-k",
            "9",
            "--min-score",
            "0.0",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])
    metrics = _as_dict(report["aggregate_metrics"])
    formulas = _as_dict(metadata["metric_formulas"])
    parameters = _as_dict(metadata["fixed_parameters"])
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    warnings = _as_list(report["warnings"])

    assert status == 0
    assert report["schema_version"] == "external-runner-report-v1"
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "beir"
    assert metadata["dataset"] == "beir/fixture"
    assert parameters["top_k"] == 9
    assert parameters["query_order"] == "case-file-order"
    assert _as_str(formulas["hit_rate"]).startswith("fraction of queries")
    assert _as_str(formulas["mrr"]).startswith("mean reciprocal rank")
    assert _as_str(formulas["expected_recall"]).startswith("average retrieved expected references")
    assert metrics["hit_rate"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["expected_recall"] == 1.0
    assert isinstance(metrics["mean_latency_ms"], float)
    assert benchmark["status"] == "success"
    assert any("top_k=9" in str(warning) for warning in warnings)
    assert "sentinel-secret-value" not in json.dumps(report)


def test_runner_validates_reproducibility_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "repro.json"

    def fail_network(*_args: object, **_kwargs: object) -> socket.socket:
        raise AssertionError("runner must not open network sockets after materialization")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    status = run_external_benchmarks.main(
        [
            "standard-rag",
            "ms-marco",
            "--suite",
            str(suite),
            "--validate-reproducibility",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    reproducibility = _as_dict(report["reproducibility"])
    runtime_only_fields = _as_list(reproducibility["runtime_only_fields"])

    assert status == 0
    assert report["status"] == "success"
    assert reproducibility["enabled"] is True
    assert reproducibility["status"] == "passed"
    assert "benchmarks[].metrics.mean_latency_ms" in runtime_only_fields
    assert reproducibility["mismatches"] == []


def test_runner_fails_threshold_gates_with_metric_details(tmp_path: Path) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "miss",
                "query": "unrelated astronomy vocabulary with no shared retrieval tokens",
                "expected": ["materials/alpha.md"],
            }
        ],
    )
    report_path = tmp_path / "threshold.json"

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--min-score",
            "0.75",
            "--min-hit-rate",
            "1.0",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    failures = _as_list(report["threshold_failures"])
    first_failure = _as_dict(failures[0])

    assert status == 1
    assert report["status"] == "threshold_failed"
    assert first_failure["metric"] == "hit_rate"
    assert first_failure["minimum"] == 1.0
    assert first_failure["actual"] == 0.0


def test_runner_reports_structured_error_for_invalid_dataset(tmp_path: Path) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "invalid.json"

    status = run_external_benchmarks.main(
        [
            "beir",
            "unsupported",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == "unsupported_dataset"
    assert "beir/nfcorpus" in str(error["remediation"])


def test_runner_rejects_degenerate_duplicate_expected_references(tmp_path: Path) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "duplicate",
                "query": "alpha receptor signaling",
                "expected": ["materials/alpha.md", "materials/alpha.md"],
            }
        ],
    )
    report_path = tmp_path / "duplicate.json"

    status = run_external_benchmarks.main(
        [
            "standard-rag",
            "ms-marco",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == "duplicate_expected_references"


@pytest.mark.parametrize(
    ("case_payload", "expected_code"),
    [
        (
            {
                "id": "bad-top-k",
                "query": "alpha receptor signaling",
                "expected": ["materials/alpha.md"],
                "top_k": "many",
            },
            "invalid_top_k",
        ),
        (
            {
                "id": "missing-material",
                "query": "alpha receptor signaling",
                "expected": ["materials/missing.md"],
            },
            "missing_material_file",
        ),
        (
            {
                "id": "no-positive",
                "query": "alpha receptor signaling",
                "expected": [],
            },
            "no_positive_references",
        ),
    ],
)
def test_runner_rejects_other_degenerate_cases(
    tmp_path: Path,
    case_payload: dict[str, object],
    expected_code: str,
) -> None:
    suite = _make_external_suite(tmp_path, [case_payload])
    report_path = tmp_path / "degenerate.json"

    status = run_external_benchmarks.main(
        [
            "standard-rag",
            "ms-marco",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == expected_code


def test_runner_resolves_public_academic_readiness_report(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path / "materialized")
    cases_dir = tmp_path / "public-cases"
    _write_jsonl(cases_dir / "rag.jsonl", _passing_cases())
    (cases_dir / "readiness_report.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "benchmark_ready": True,
                "armory_path": str(armory),
                "generated_files": {"rag": str(cases_dir / "rag.jsonl")},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "public-academic.json"

    status = run_external_benchmarks.main(
        [
            "public-academic",
            "public-academic",
            "--suite",
            str(cases_dir),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])

    assert status == 0
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "public-academic"
    assert metadata["dataset"] == "public-academic"
    assert metadata["readiness_report_path"] == str(
        (cases_dir / "readiness_report.json").resolve()
    )


def test_heph_native_runner_wraps_existing_suite_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = tmp_path / "native-suite"
    suite.mkdir()
    report_path = tmp_path / "native-wrapper.json"
    observed: dict[str, object] = {}

    def fake_run_suite(
        suite_path: Path,
        *,
        rag_hit_rate: float,
        rag_mrr: float,
        rag_expected_recall: float,
        report_path: Path | None,
    ) -> int:
        observed["suite_path"] = str(suite_path)
        observed["rag_hit_rate"] = rag_hit_rate
        observed["rag_mrr"] = rag_mrr
        observed["rag_expected_recall"] = rag_expected_recall
        assert report_path is not None
        report_path.write_text(
            json.dumps(
                {
                    "suite": str(suite_path),
                    "status": 0,
                    "thresholds": {
                        "rag_hit_rate": rag_hit_rate,
                        "rag_mrr": rag_mrr,
                        "rag_expected_recall": rag_expected_recall,
                    },
                    "rag": {
                        "hit_rate": 1.0,
                        "mean_reciprocal_rank": 0.9,
                        "mean_expected_recall": 1.0,
                        "mean_latency_ms": 3.0,
                    },
                    "material_roles": {"pass_rate": 1.0},
                    "document_understanding": {"passed": True},
                    "answers": {"pass_rate": 1.0},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(run_external_benchmarks.run_benchmark_suite, "run_suite", fake_run_suite)

    status = run_external_benchmarks.main(
        [
            "heph-native",
            "academic",
            "--suite",
            str(suite),
            "--min-hit-rate",
            "0.8",
            "--min-mrr",
            "0.7",
            "--min-expected-recall",
            "0.9",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    native_report = _as_dict(benchmark["native_suite_report"])

    assert status == 0
    assert observed == {
        "suite_path": str(suite.resolve()),
        "rag_hit_rate": 0.8,
        "rag_mrr": 0.7,
        "rag_expected_recall": 0.9,
    }
    assert benchmark["benchmark_type"] == "heph-native"
    assert _as_dict(native_report["rag"])["hit_rate"] == 1.0
    assert "material_roles" in native_report
