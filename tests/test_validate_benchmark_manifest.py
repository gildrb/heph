from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts import run_benchmark_suite, validate_benchmark_manifest


def test_default_manifest_passes() -> None:
    report = validate_benchmark_manifest.validate_manifest(
        run_benchmark_suite.DEFAULT_SUITE / "manifest.json"
    )

    assert report.corpus_kind == "synthetic-snippets"
    assert "mathematics" in report.domains
    assert "past_exam" in report.roles
    assert "german-text" in report.stressors
    assert "near-miss-negative" in report.stressors
    assert "misleading-overlap" in report.stressors
    assert report.documents == 14
    assert report.datasets == 9


def test_manifest_rejects_missing_document(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["documents"][0]["source"] = "materials/missing.md"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = validate_benchmark_manifest.main([str(manifest_path)])

    assert status == 2


def test_manifest_rejects_narrow_stressors(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for document in manifest["documents"]:
        document["stressors"] = ["same"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = validate_benchmark_manifest.main([str(manifest_path), "--min-stressors", "2"])

    assert status == 2


def test_manifest_allows_zero_optional_breadth_threshold_for_diagnostics(
    tmp_path: Path,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"

    report = validate_benchmark_manifest.validate_manifest(
        manifest_path,
        min_domains=0,
        min_roles=0,
        min_document_types=0,
        min_stressors=0,
    )

    assert report.documents == 14


def test_manifest_rejects_zero_document_threshold(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"

    status = validate_benchmark_manifest.main([str(manifest_path), "--min-documents", "0"])

    assert status == 2


def test_manifest_can_gate_external_real_corpus_requirements(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["corpus_kind"] = "public-pdfs"
    manifest["known_limits"] = ["No model-backed run result is committed."]
    for document in manifest["documents"]:
        document["permission_note"] = "test fixture permissioned source"
    (suite / "armory" / "materials" / "table-heavy.pdf").write_text(
        "fake pdf fixture placeholder",
        encoding="utf-8",
    )
    manifest["documents"].append(
        {
            "source": "materials/table-heavy.pdf",
            "domain": "statistics",
            "role": "lecture",
            "document_type": "pdf",
            "source_url": "https://example.edu/table-heavy.pdf",
            "stressors": ["real-pdf", "table-heavy", "multi-column"],
        }
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_benchmark_manifest.validate_manifest(
        manifest_path,
        min_documents=15,
        require_corpus_kind="public-pdfs",
        required_document_types=("pdf",),
        required_stressors=("real-pdf", "table-heavy", "multi-column"),
        forbid_known_limit=("No real scanned PDFs",),
        require_document_provenance=True,
    )

    assert report.documents == 15
    assert "pdf" in report.document_types
    assert "table-heavy" in report.stressors


def test_manifest_rejects_missing_required_document_provenance(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"

    status = validate_benchmark_manifest.main(
        [
            str(manifest_path),
            "--require-document-provenance",
        ]
    )

    assert status == 2


def test_manifest_rejects_missing_required_stressor(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"

    status = validate_benchmark_manifest.main(
        [
            str(manifest_path),
            "--require-stressor",
            "real-pdf",
        ]
    )

    assert status == 2


def test_manifest_rejects_forbidden_known_limit(tmp_path: Path) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    manifest_path = suite / "manifest.json"

    status = validate_benchmark_manifest.main(
        [
            str(manifest_path),
            "--forbid-known-limit",
            "synthetic snippets",
        ]
    )

    assert status == 2


def test_suite_report_includes_manifest(tmp_path: Path) -> None:
    report_path = tmp_path / "suite.json"

    status = run_benchmark_suite.run_suite(report_path=report_path)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert report["manifest"]["corpus_kind"] == "synthetic-snippets"
    assert "exercise-sheet" in report["manifest"]["stressors"]
