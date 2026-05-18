from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import sample_benchmark_cases


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _report(labels: dict[str, bool]) -> dict[str, object]:
    return {
        "benchmarks": [
            {
                "per_query_results": [
                    {"case_id": case_id, "hit": hit} for case_id, hit in labels.items()
                ]
            }
        ]
    }


def test_sample_cases_mixed_uses_report_hit_labels(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    output_path = tmp_path / "sample.jsonl"
    report_path = tmp_path / "report.json"
    rows: list[dict[str, object]] = [
        {"id": f"case-{index}", "query": f"query {index}", "expected": [f"doc-{index}.md"]}
        for index in range(8)
    ]
    _write_jsonl(cases_path, rows)
    report_path.write_text(
        json.dumps(
            _report(
                {
                    "case-0": True,
                    "case-1": False,
                    "case-2": True,
                    "case-3": False,
                    "case-4": True,
                    "case-5": False,
                    "case-6": True,
                    "case-7": False,
                }
            )
        ),
        encoding="utf-8",
    )

    status = sample_benchmark_cases.main(
        [
            str(cases_path),
            str(output_path),
            "--report",
            str(report_path),
            "--mode",
            "mixed",
            "--count",
            "4",
            "--seed",
            "7",
        ]
    )

    sampled = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    sampled_ids = {row["id"] for row in sampled}
    labels = sample_benchmark_cases.load_report_labels(report_path)
    assert status == 0
    assert len(sampled) == 4
    assert sum(1 for case_id in sampled_ids if labels[case_id]) == 2
    assert sum(1 for case_id in sampled_ids if not labels[case_id]) == 2
    assert [row["id"] for row in sampled] == sorted(sampled_ids)


def test_sample_cases_rejects_hit_mode_without_report(tmp_path: Path, capsys) -> None:
    cases_path = tmp_path / "cases.jsonl"
    _write_jsonl(cases_path, [{"id": "case", "query": "query", "expected": ["doc.md"]}])

    with pytest.raises(SystemExit) as exc_info:
        sample_benchmark_cases.main(
            [str(cases_path), str(tmp_path / "sample.jsonl"), "--mode", "misses"]
        )
    assert exc_info.value.code == 2
    assert "requires --report" in capsys.readouterr().err
