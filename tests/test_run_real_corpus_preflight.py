from __future__ import annotations

import json
import time
from pathlib import Path

from hephaion.armory.storage import initialize
from scripts import run_real_corpus_preflight


def _make_real_corpus(tmp_path: Path) -> tuple[Path, Path]:
    suite = tmp_path / "suite"
    armory = suite / "armory"
    initialize(armory)
    materials = armory / "materials"
    domains = ["math", "biology", "chemistry", "physics", "history"]
    roles = ["past_exam", "lecture", "assignment"]
    document_types = [
        "pdf",
        "scanned-pdf",
        "lecture-slides",
        "exercise-sheet",
        "past-exam",
        "solutions",
        "table-heavy-notes",
        "multilingual-notes",
    ]
    stressors = [
        "real-pdf",
        "ocr-noise",
        "table-heavy",
        "multi-column",
        "multilingual",
        "formula-language",
        "unicode",
        "past-exam",
        "exercise-sheet",
        "slides",
        "scan-artifacts",
        "near-miss-concept",
        "multi-source-synthesis",
        "boilerplate",
        "points-format",
        "tables",
    ]
    documents = []
    for idx in range(40):
        role = roles[idx % len(roles)]
        source = f"materials/real-{idx}.md"
        text = {
            "past_exam": "Question 1. Explain enzyme kinetics. [10 marks]\n",
            "lecture": "Table of contents\nLecture goals\nVorlesung overview\nExercise groups\n",
            "assignment": "Exercise Sheet 4\nDue date Friday\nExercise 1.\nExercise 2.\n",
        }[role]
        (materials / f"real-{idx}.md").write_text(text, encoding="utf-8")
        documents.append(
            {
                "source": source,
                "domain": domains[idx % len(domains)],
                "role": role,
                "document_type": document_types[idx % len(document_types)],
                "permission_note": "test fixture permissioned corpus",
                "stressors": [
                    stressors[idx % len(stressors)],
                    stressors[(idx + 5) % len(stressors)],
                ],
            }
        )
    for dataset in (
        "rag.jsonl",
        "material_roles.jsonl",
        "priority.jsonl",
        "answers.jsonl",
        "replay.jsonl",
        "learning_state.jsonl",
    ):
        (suite / dataset).write_text("{}\n", encoding="utf-8")
    manifest = {
        "id": "real-corpus",
        "description": "test real corpus",
        "corpus_kind": "permissioned-pdfs",
        "documents": documents,
        "datasets": [
            {"path": "rag.jsonl", "kind": "retrieval"},
            {"path": "material_roles.jsonl", "kind": "material-roles"},
            {"path": "priority.jsonl", "kind": "priority"},
            {"path": "answers.jsonl", "kind": "grounded-answers"},
            {"path": "replay.jsonl", "kind": "model-replay-prompts"},
            {"path": "learning_state.jsonl", "kind": "study-state"},
        ],
        "known_limits": [],
    }
    manifest_path = suite / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return armory, manifest_path


def test_real_corpus_preflight_passes_broad_manifest_and_documents(tmp_path: Path) -> None:
    armory, manifest = _make_real_corpus(tmp_path)

    report = run_real_corpus_preflight.run_preflight(armory, manifest)

    assert report.status == 0
    assert report.manifest is not None
    assert report.manifest.documents == 40
    assert report.document_understanding is not None
    assert report.document_understanding.indexed_documents == 40
    assert report.document_understanding.overview_source_coverage_rate >= 0.4


def test_real_corpus_preflight_fails_low_overview_source_coverage(
    tmp_path: Path,
) -> None:
    armory, manifest = _make_real_corpus(tmp_path)

    report = run_real_corpus_preflight.run_preflight(
        armory,
        manifest,
        min_overview_source_coverage=1.0,
    )

    assert report.status == 1
    assert any("overview source coverage" in failure for failure in report.failures)


def test_real_corpus_preflight_fails_narrow_manifest(tmp_path: Path) -> None:
    armory, manifest = _make_real_corpus(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for document in payload["documents"]:
        document["stressors"] = ["real-pdf"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = run_real_corpus_preflight.run_preflight(armory, manifest)

    assert report.status == 1
    assert any("manifest" in failure for failure in report.failures)


def test_real_corpus_preflight_rejects_unreviewed_scaffold_limits(tmp_path: Path) -> None:
    armory, manifest = _make_real_corpus(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["known_limits"] = [
        "Generated scaffold: domains, stressors, and roles require human review."
    ]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = run_real_corpus_preflight.run_preflight(armory, manifest)

    assert report.status == 1
    assert any("Generated scaffold" in failure for failure in report.failures)


def test_real_corpus_preflight_rejects_missing_document_provenance(tmp_path: Path) -> None:
    armory, manifest = _make_real_corpus(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    del payload["documents"][0]["permission_note"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = run_real_corpus_preflight.run_preflight(armory, manifest)

    assert report.status == 1
    assert any("missing provenance" in failure for failure in report.failures)


def test_real_corpus_preflight_fails_when_armory_has_unmanifested_material(
    tmp_path: Path,
) -> None:
    armory, manifest = _make_real_corpus(tmp_path)
    (armory / "materials" / "unmanifested.md").write_text(
        "Table of contents\nLecture schedule\n",
        encoding="utf-8",
    )

    report = run_real_corpus_preflight.run_preflight(armory, manifest)

    assert report.status == 1
    assert any("missing from manifest" in failure for failure in report.failures)


def test_real_corpus_preflight_fails_when_manifest_is_for_different_armory(
    tmp_path: Path,
) -> None:
    _armory, manifest = _make_real_corpus(tmp_path)
    other_armory = tmp_path / "other" / "armory"
    initialize(other_armory)

    report = run_real_corpus_preflight.run_preflight(other_armory, manifest)

    assert report.status == 1
    assert any("missing from armory" in failure for failure in report.failures)


def test_real_corpus_preflight_reports_document_timeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    armory, manifest = _make_real_corpus(tmp_path)

    def slow_benchmark(*_args: object, **_kwargs: object) -> object:
        time.sleep(3)
        raise AssertionError("timeout should interrupt this call")

    monkeypatch.setattr(
        run_real_corpus_preflight.benchmark_document_understanding,
        "run_benchmark",
        slow_benchmark,
    )

    report = run_real_corpus_preflight.run_preflight(
        armory,
        manifest,
        document_timeout_seconds=1,
    )

    assert report.status == 1
    assert report.document_understanding is None
    assert any("timed out after 1 second" in failure for failure in report.failures)


def test_real_corpus_preflight_cli_writes_report(tmp_path: Path) -> None:
    armory, manifest = _make_real_corpus(tmp_path)
    report_path = tmp_path / "preflight.json"

    status = run_real_corpus_preflight.main(
        [str(armory), str(manifest), "--json-report", str(report_path)]
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["status"] == 0
    assert payload["manifest"]["documents"] == 40
    assert payload["document_understanding"]["overview_source_coverage_rate"] >= 0.4
