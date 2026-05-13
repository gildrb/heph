from __future__ import annotations

from pathlib import Path

from scripts import benchmark_priority


def _write_material(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_cases_supports_jsonl(tmp_path: Path) -> None:
    dataset = tmp_path / "priority.jsonl"
    dataset.write_text(
        '{"id":"mfi","expected_topics":["geometrische reihe"],'
        '"domain":"mathematics",'
        '"forbidden_topics":["jesse ratzkin"],'
        '"expected_past_exam_sources":["materials/exam.md"],'
        '"expected_ordered_topics":["geometrische reihe","konvergenz"],'
        '"expected_mark_totals":{"geometrische reihe":8},'
        '"expected_tiers":{"geometrische reihe":"High-yield"},'
        '"limit":4}\n',
        encoding="utf-8",
    )

    cases = benchmark_priority.load_cases(dataset)

    assert cases == [
        benchmark_priority.PriorityBenchmarkCase(
            case_id="mfi",
            expected_topics=("geometrische reihe",),
            domain="mathematics",
            forbidden_topics=("jesse ratzkin",),
            expected_past_exam_sources=("materials/exam.md",),
            expected_ordered_topics=("geometrische reihe", "konvergenz"),
            expected_mark_totals={"geometrische reihe": 8},
            expected_tiers={"geometrische reihe": "High-yield"},
            limit=4,
        )
    ]


def test_priority_benchmark_scores_expected_topics_and_forbidden_noise(
    tmp_path: Path,
) -> None:
    armory = tmp_path / "armory"
    _write_material(
        armory / "materials" / "lecture.md",
        "# Mathematik für Informatiker 2\n\n"
        "Jesse Ratzkin. Universität Würzburg. Sommersemester 2026.\n\n"
        "Geometrische Reihe und Konvergenz von Partialsummen.\n",
    )
    _write_material(
        armory / "materials" / "exam.md",
        "# Klausur\n\n"
        "Aufgabe 1 [8 Punkte]: Untersuchen Sie eine geometrische Reihe auf Konvergenz.\n",
    )
    case = benchmark_priority.PriorityBenchmarkCase(
        case_id="mfi",
        expected_topics=("geometrische reihe",),
        domain="mathematics",
        forbidden_topics=("jesse ratzkin", "universität würzburg"),
        expected_past_exam_sources=("materials/exam.md",),
        limit=5,
    )

    report = benchmark_priority.run_benchmark(armory, [case])

    assert report.pass_rate == 1.0
    assert report.domains == ("mathematics",)
    assert report.topic_recall == 1.0
    assert report.forbidden_topic_avoidance == 1.0
    assert report.past_exam_source_recall == 1.0
    assert report.ordered_topic_accuracy == 1.0
    assert report.mark_total_accuracy == 1.0
    assert report.tier_accuracy == 1.0
    assert report.failures == ()


def test_priority_benchmark_validates_marks_tiers_and_order(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(
        armory / "materials" / "exam.md",
        "Question 1 [12 marks]: Explain enzyme kinetics.\n"
        "Question 2 [4 marks]: Explain protein folding.\n",
    )
    case = benchmark_priority.PriorityBenchmarkCase(
        case_id="weighted",
        expected_topics=("enzyme kinetics", "protein folding"),
        expected_ordered_topics=("enzyme kinetics", "protein folding"),
        expected_mark_totals={"enzyme kinetics": 12, "protein folding": 4},
        expected_tiers={"enzyme kinetics": "Exam core", "protein folding": "Foundation"},
        limit=5,
    )

    report = benchmark_priority.run_benchmark(armory, [case])

    assert report.pass_rate == 1.0
    assert report.ordered_topic_accuracy == 1.0
    assert report.mark_total_accuracy == 1.0
    assert report.tier_accuracy == 1.0


def test_priority_benchmark_reports_failures(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "notes.md", "# Notes\n\nHash tables.\n")
    case = benchmark_priority.PriorityBenchmarkCase(
        case_id="missing",
        expected_topics=("geometrische reihe",),
        forbidden_topics=(),
        expected_past_exam_sources=("materials/exam.md",),
        limit=3,
    )

    report = benchmark_priority.run_benchmark(armory, [case])

    assert report.pass_rate == 0.0
    assert report.failures == ("missing",)
    assert report.results[0].missing_topics == ("geometrische reihe",)
    assert report.results[0].missing_past_exam_sources == ("materials/exam.md",)
