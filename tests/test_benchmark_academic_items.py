from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import benchmark_academic_items


def test_load_academic_item_cases(tmp_path: Path) -> None:
    dataset = tmp_path / "academic_items.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "definition",
                "domain": "physics",
                "source_ref": "materials/physics.md#chunk=1",
                "kind": "definition",
                "concept": "Hamiltonian mechanics",
                "text": "generalized coordinates",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    cases = benchmark_academic_items.load_cases(dataset)

    assert len(cases) == 1
    assert cases[0].case_id == "definition"
    assert cases[0].kind.value == "definition"
    assert cases[0].concept == "Hamiltonian mechanics"


def test_academic_item_benchmark_passes_fixture_cases(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    shutil.copytree(Path("benchmarks/academic/armory"), armory)
    cases = benchmark_academic_items.load_cases(Path("benchmarks/academic/academic_items.jsonl"))

    report = benchmark_academic_items.run_benchmark(armory, cases)

    assert report.pass_rate == 1.0
    assert report.domains == ("biochemistry", "mathematics", "physics")
    assert report.kinds == (
        "answer",
        "definition",
        "exam_question",
        "exam_skill",
        "figure",
        "formula",
        "rubric_point",
        "table",
    )
    assert report.generated_questions > 0
    assert report.grounded_question_rate == 1.0
    assert "free_recall" in report.question_types
    assert report.question_type_count == len(report.question_types)
    assert len(report.question_types) >= 3


def test_academic_item_benchmark_reports_missing_items(tmp_path: Path) -> None:
    dataset = tmp_path / "academic_items.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "missing",
                "source_ref": "materials/calculus.md#chunk=0",
                "kind": "definition",
                "concept": "Not in source",
                "text": "not in source",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    armory = tmp_path / "armory"
    shutil.copytree(Path("benchmarks/academic/armory"), armory)

    report = benchmark_academic_items.run_benchmark(
        armory,
        benchmark_academic_items.load_cases(dataset),
    )

    assert report.pass_rate == 0.0
    assert report.failures == ("missing",)
    assert report.results[0].failure == "expected academic item not extracted"


def test_academic_item_cli_gates_question_type_breadth(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "armory"
    shutil.copytree(Path("benchmarks/academic/armory"), armory)

    status = benchmark_academic_items.main(
        [
            str(armory),
            "benchmarks/academic/academic_items.jsonl",
            "--min-question-types",
            "99",
        ]
    )

    assert status == 1
    assert "question_types=" in capsys.readouterr().out
