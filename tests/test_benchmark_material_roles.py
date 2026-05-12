from __future__ import annotations

from pathlib import Path

from scripts import benchmark_material_roles


def _write_material(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_cases_supports_jsonl(tmp_path: Path) -> None:
    dataset = tmp_path / "roles.jsonl"
    dataset.write_text(
        (
            '{"id":"lecture","domain":"history","source":"materials/lecture.md",'
            '"expected_role":"lecture"}\n'
        ),
        encoding="utf-8",
    )

    cases = benchmark_material_roles.load_cases(dataset)

    assert cases == [
        benchmark_material_roles.MaterialRoleCase(
            case_id="lecture",
            source="materials/lecture.md",
            expected_role="lecture",
            domain="history",
        )
    ]


def test_material_role_benchmark_scores_expected_roles(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(
        armory / "materials" / "lecture.md",
        "# Lecture 1\n\nTable of contents\n\nIntroduction to the course.\n",
    )
    _write_material(
        armory / "materials" / "sheet.md",
        "# Exercise Sheet 1\n\nDue date: Friday.\n\nExercise 1. Prove the claim.\n",
    )
    _write_material(
        armory / "materials" / "exam.md",
        "# Exam\n\nQuestion 1 [10 marks]: Explain the concept.\n",
    )
    cases = [
        benchmark_material_roles.MaterialRoleCase(
            case_id="lecture",
            source="materials/lecture.md",
            expected_role="lecture",
            domain="mathematics",
        ),
        benchmark_material_roles.MaterialRoleCase(
            case_id="sheet",
            source="materials/sheet.md",
            expected_role="assignment",
            domain="physics",
        ),
        benchmark_material_roles.MaterialRoleCase(
            case_id="exam",
            source="materials/exam.md",
            expected_role="past_exam",
            domain="history",
        ),
    ]

    report = benchmark_material_roles.run_benchmark(armory, cases)

    assert report.pass_rate == 1.0
    assert report.domains == ("history", "mathematics", "physics")
    assert report.expected_roles == ("assignment", "lecture", "past_exam")
    assert report.failures == ()


def test_material_role_benchmark_reports_failures(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "notes.md", "# Notes\n")
    case = benchmark_material_roles.MaterialRoleCase(
        case_id="wrong",
        source="materials/notes.md",
        expected_role="past_exam",
    )

    report = benchmark_material_roles.run_benchmark(armory, [case])

    assert report.pass_rate == 0.0
    assert report.failures == ("wrong",)
    assert report.results[0].actual_role == "reference"
