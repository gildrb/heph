from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import run_benchmark_suite, validate_benchmark_manifest

PUBLIC_ACADEMIC_MANIFEST = Path("benchmarks/public-academic/manifest.json")


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
    assert report.datasets == 11


def test_public_academic_manifest_passes_strict_schema() -> None:
    report = validate_benchmark_manifest.validate_manifest(PUBLIC_ACADEMIC_MANIFEST)

    assert report.corpus_kind == "public-academic"
    assert report.documents >= 50
    assert report.datasets == 0
    assert "artificial-intelligence" in report.domains
    assert "textbook" in report.roles
    assert "public-html" in report.stressors


def test_public_academic_manifest_requires_canonical_materializer_fields(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    document = _public_academic_document("doc-1", "materials/doc-1.html")
    del document["sha256"]
    _write_public_academic_manifest(manifest_path, [document])

    with pytest.raises(ValueError, match="sha256"):
        validate_benchmark_manifest.validate_manifest(
            manifest_path,
            min_domains=0,
            min_roles=0,
            min_document_types=0,
            min_stressors=0,
        )


def test_public_academic_manifest_rejects_duplicate_ids(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_public_academic_manifest(
        manifest_path,
        [
            _public_academic_document("doc-1", "materials/doc-1.html"),
            _public_academic_document("doc-1", "materials/doc-2.html"),
        ],
    )

    with pytest.raises(ValueError, match="duplicate document id"):
        validate_benchmark_manifest.validate_manifest(
            manifest_path,
            min_domains=0,
            min_roles=0,
            min_document_types=0,
            min_stressors=0,
        )


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


def _public_academic_document(document_id: str, source: str) -> dict[str, object]:
    return {
        "id": document_id,
        "title": f"Public academic fixture {document_id}",
        "source": source,
        "source_url": f"https://example.edu/{document_id}.html",
        "bytes": 12,
        "sha256": "a" * 64,
        "source_organization": "Example University",
        "license": "Public academic fixture attribution.",
        "license_url": "https://example.edu/license",
        "attribution": "Example University public course fixture.",
        "domain": "artificial-intelligence",
        "role": "textbook",
        "document_type": "html-textbook-section",
        "stressors": ["public-html"],
    }


def _write_public_academic_manifest(
    manifest_path: Path,
    documents: list[dict[str, object]],
) -> None:
    manifest_path.write_text(
        json.dumps(
            {
                "id": "public-academic-test",
                "description": "Public academic fixture manifest.",
                "corpus_kind": "public-academic",
                "documents": documents,
                "datasets": [],
                "known_limits": [],
            }
        ),
        encoding="utf-8",
    )
