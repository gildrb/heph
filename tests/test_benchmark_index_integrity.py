from __future__ import annotations

from pathlib import Path

from scripts import benchmark_index_integrity


def _write_material(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_cases_supports_jsonl() -> None:
    dataset = Path("benchmarks/academic/index_integrity.jsonl")

    cases = benchmark_index_integrity.load_cases(dataset)

    assert cases[0].case_id == "matrix-topic-preserved"
    assert "Administrative header" in cases[0].must_include
    assert cases[0].task == "topic-extraction"


def test_index_integrity_benchmark_scores_required_and_forbidden_text(
    tmp_path: Path,
) -> None:
    armory = tmp_path / "armory"
    _write_material(
        armory / "materials" / "lecture.md",
        "# Lecture\n\nAdministrative header explains matrix multiplication.\n",
    )
    cases = [
        benchmark_index_integrity.IndexIntegrityCase(
            case_id="topic",
            source="materials/lecture.md",
            must_include=("Administrative header", "matrix multiplication"),
            must_not_include=("Formula-not-decoded",),
            domain="mathematics",
            task="topic-extraction",
        )
    ]

    report = benchmark_index_integrity.run_benchmark(armory, cases)

    assert report.pass_rate == 1.0
    assert report.required_text_rate == 1.0
    assert report.forbidden_text_rate == 1.0
    assert report.corpus_forbidden_text_rate == 1.0
    assert report.tasks == ("topic-extraction",)


def test_index_integrity_benchmark_reports_missing_and_forbidden_text(
    tmp_path: Path,
) -> None:
    armory = tmp_path / "armory"
    _write_material(
        armory / "materials" / "lecture.md",
        "# Lecture\n\nIntegration by parts. ExtractionNoise.\n",
    )
    cases = [
        benchmark_index_integrity.IndexIntegrityCase(
            case_id="broken",
            source="materials/lecture.md",
            must_include=("product rule",),
            must_not_include=("ExtractionNoise",),
        )
    ]

    report = benchmark_index_integrity.run_benchmark(armory, cases)

    assert report.pass_rate == 0.0
    assert report.required_text_rate == 0.0
    assert report.forbidden_text_rate == 0.0
    assert report.results[0].missing_text == ("product rule",)
    assert report.results[0].forbidden_text_present == ("ExtractionNoise",)


def test_index_integrity_benchmark_scans_whole_corpus_for_extraction_noise(
    tmp_path: Path,
) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "checked.md", "# Checked\n\nClean source text.\n")
    _write_material(
        armory / "materials" / "unchecked.md",
        "# Unchecked\n\nThis unrelated file still contains ExtractionNoise.\n",
    )
    cases = [
        benchmark_index_integrity.IndexIntegrityCase(
            case_id="checked",
            source="materials/checked.md",
            must_include=("Clean source text",),
        )
    ]

    report = benchmark_index_integrity.run_benchmark(
        armory,
        cases,
        corpus_forbidden_text=("ExtractionNoise",),
    )

    assert report.pass_rate == 1.0
    assert report.corpus_forbidden_text_rate < 1.0
    assert report.corpus_forbidden_text_failures[0].source == "materials/unchecked.md"
    assert report.corpus_forbidden_text_failures[0].forbidden_text_present == ("ExtractionNoise",)


def test_index_integrity_scan_only_cli_does_not_require_labelled_cases(
    tmp_path: Path,
) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "lecture.md", "# Lecture\n\nClean source text.\n")

    status = benchmark_index_integrity.main(["--scan-only", str(armory)])

    assert status == 0


def test_index_integrity_cli_requires_dataset_without_scan_only(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "lecture.md", "# Lecture\n\nClean source text.\n")

    status = benchmark_index_integrity.main([str(armory)])

    assert status == 2
