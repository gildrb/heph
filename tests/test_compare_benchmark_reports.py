from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import compare_benchmark_reports


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compare_suite_reports_passes_when_metrics_do_not_regress(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(
        baseline,
        {
            "rag": {"hit_rate": 0.95, "mean_reciprocal_rank": 0.7},
            "document_understanding": {"overview_source_coverage_rate": 1.0},
            "answers": {"pass_rate": 0.9},
        },
    )
    _write_json(
        current,
        {
            "rag": {"hit_rate": 1.0, "mean_reciprocal_rank": 0.72},
            "document_understanding": {"overview_source_coverage_rate": 1.0},
            "answers": {"pass_rate": 0.9},
        },
    )

    report = compare_benchmark_reports.compare_reports(baseline, current)

    assert report.regressions == ()
    assert [comparison.metric for comparison in report.comparisons] == [
        "rag.hit_rate",
        "rag.mean_reciprocal_rank",
        "document_understanding.overview_source_coverage_rate",
        "answers.pass_rate",
    ]


def test_compare_reports_fails_on_overview_source_coverage_regression(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(
        baseline,
        {"document_understanding": {"overview_source_coverage_rate": 1.0}},
    )
    _write_json(
        current,
        {"document_understanding": {"overview_source_coverage_rate": 0.5}},
    )

    report = compare_benchmark_reports.compare_reports(baseline, current)

    assert report.regressions == ("document_understanding.overview_source_coverage_rate",)


def test_compare_reports_fails_on_regression(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(baseline, {"answers": {"pass_rate": 1.0}})
    _write_json(current, {"answers": {"pass_rate": 0.8}})

    status = compare_benchmark_reports.main([str(baseline), str(current)])

    captured = capsys.readouterr()
    assert status == 1
    assert "REGRESSION answers.pass_rate" in captured.out


def test_compare_reports_accepts_tolerance(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(baseline, {"rag": {"mean_reciprocal_rank": 0.9}})
    _write_json(current, {"rag": {"mean_reciprocal_rank": 0.895}})

    report = compare_benchmark_reports.compare_reports(baseline, current, tolerance=0.01)

    assert report.regressions == ()
    assert report.comparisons[0].delta == pytest.approx(-0.005)


def test_compare_replay_answer_eval_reports(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(
        baseline,
        {
            "report": {
                "pass_rate": 0.9,
                "citation_validity_rate": 1.0,
            }
        },
    )
    _write_json(
        current,
        {
            "report": {
                "pass_rate": 0.95,
                "citation_validity_rate": 1.0,
            }
        },
    )

    status = compare_benchmark_reports.main(
        [str(baseline), str(current), "--metric", "report.pass_rate"]
    )

    assert status == 0


def test_compare_reports_rejects_missing_comparable_metrics(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(baseline, {"metadata": {"status": "ok"}})
    _write_json(current, {"metadata": {"status": "ok"}})

    with pytest.raises(ValueError, match="no comparable numeric metrics"):
        compare_benchmark_reports.compare_reports(baseline, current)
