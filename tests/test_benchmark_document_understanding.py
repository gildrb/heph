from __future__ import annotations

import json
from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.rag.health import ExtractionHealthReport
from hephaistos.rag.index import ArmoryIndex
from scripts import benchmark_document_understanding


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    return armory


def test_document_understanding_smoke_detects_generic_roles(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "document-a.md").write_text(
        """
        Table of contents
        Lecture goals
        Vorlesung overview
        Exercise groups and reading plan
        """,
        encoding="utf-8",
    )
    (armory / "materials" / "document-b.md").write_text(
        """
        Final assessment
        Question 1. Explain enzyme kinetics. [10 marks]
        Question 2. Compare protein folding pathways. [8 marks]
        Allowed materials: none.
        """,
        encoding="utf-8",
    )
    (armory / "materials" / "document-c.md").write_text(
        """
        Exercise Sheet 4
        Due date: Friday
        Exercise 1. Prove the recurrence.
        Exercise 2. Compute the example.
        """,
        encoding="utf-8",
    )

    report = benchmark_document_understanding.run_benchmark(
        armory,
        min_documents=3,
        require_roles=("slides", "past_exam", "assignment"),
        min_role_confidence=0.75,
    )

    assert report.passed
    assert report.role_counts["slides"] == 1
    assert report.role_counts["past_exam"] == 1
    assert report.role_counts["assignment"] == 1
    assert report.indexed_role_counts["slides"] == 1
    assert report.indexed_role_counts["past_exam"] == 1
    assert report.indexed_role_counts["assignment"] == 1
    assert report.extraction_health_passed
    assert report.overview_sampled_sources == 3
    assert report.overview_total_sources == 3
    assert report.overview_source_coverage_rate == 1.0


def test_document_understanding_smoke_fails_missing_required_role(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "notes.md").write_text("# Notes\n\nA plain note.\n", encoding="utf-8")

    report = benchmark_document_understanding.run_benchmark(
        armory,
        min_documents=1,
        require_roles=("past_exam",),
    )

    assert not report.passed
    assert report.failures == ("required indexed role not found: past_exam",)


def test_document_understanding_smoke_fails_low_overview_source_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "one.md").write_text("# One\n\nLecture notes.\n", encoding="utf-8")
    monkeypatch.setattr(
        benchmark_document_understanding,
        "_overview_source_coverage",
        lambda _armory, _index, _visible: (1, 2),
    )

    report = benchmark_document_understanding.run_benchmark(
        armory,
        min_documents=1,
        min_overview_source_coverage=1.0,
    )

    assert not report.passed
    assert report.overview_source_coverage_rate == 0.5
    assert "overview source coverage" in report.failures[0]


def test_document_understanding_required_roles_must_be_indexed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "past-exam.pdf").write_bytes(b"%PDF-1.4\n")

    empty_index = ArmoryIndex(armory)
    monkeypatch.setattr(
        benchmark_document_understanding, "load_or_build", lambda _path: empty_index
    )
    monkeypatch.setattr(
        benchmark_document_understanding,
        "scan_extraction_health",
        lambda _path: ExtractionHealthReport(
            armory_path=str(armory),
            documents=0,
            checks=0,
            pass_rate=1.0,
            forbidden_text=(),
            issues=(),
        ),
    )

    report = benchmark_document_understanding.run_benchmark(
        armory,
        min_documents=0,
        require_roles=("past_exam",),
    )

    assert not report.passed
    assert report.role_counts["past_exam"] == 1
    assert report.indexed_role_counts == {}
    assert report.failures == ("required indexed role not found: past_exam",)


def test_document_understanding_cli_writes_json_report(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    armory = _make_armory(tmp_path)
    (armory / "materials" / "exam.md").write_text(
        "Question 1. Explain Hamiltonian mechanics. [12 marks]\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    code = benchmark_document_understanding.main(
        [
            str(armory),
            "--require-role",
            "past_exam",
            "--json-report",
            str(report_path),
        ]
    )

    out = capsys.readouterr().out
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert code == 0
    assert "Document understanding smoke" in out
    assert payload["role_counts"]["past_exam"] == 1
    assert payload["indexed_role_counts"]["past_exam"] == 1
    assert payload["overview_source_coverage_rate"] == 1.0
