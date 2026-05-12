from __future__ import annotations

import json
from pathlib import Path

from hephaistos.armory.storage import initialize
from scripts import create_benchmark_manifest


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    return armory


def test_create_manifest_scaffolds_visible_materials(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "lecture-01.pdf").write_text("pdf", encoding="utf-8")
    (armory / "materials" / "past-exam-ss23.pdf").write_text("pdf", encoding="utf-8")
    (armory / "materials" / "Übungsblatt-1.md").write_text("sheet", encoding="utf-8")
    (armory / "materials" / "tables.xlsx").write_text("table", encoding="utf-8")

    manifest = create_benchmark_manifest.create_manifest(
        armory,
        corpus_id="public-math",
        corpus_kind="public-pdfs",
        domain="mathematics",
    )

    assert manifest["id"] == "public-math"
    assert manifest["corpus_kind"] == "public-pdfs"
    assert len(manifest["documents"]) == 4
    by_source = {document["source"]: document for document in manifest["documents"]}
    assert by_source["materials/past-exam-ss23.pdf"]["role"] == "past_exam"
    assert by_source["materials/past-exam-ss23.pdf"]["document_type"] == "past-exam"
    assert "real-pdf" in by_source["materials/lecture-01.pdf"]["stressors"]
    assert by_source["materials/lecture-01.pdf"]["source_url"] == ""
    assert by_source["materials/lecture-01.pdf"]["permission_note"] == ""
    assert "multilingual" in by_source["materials/Übungsblatt-1.md"]["stressors"]
    assert "table-heavy" in by_source["materials/tables.xlsx"]["stressors"]
    assert manifest["datasets"][0]["path"] == "rag.jsonl"
    dataset_kinds = {dataset["kind"] for dataset in manifest["datasets"]}
    assert "chat-events" in dataset_kinds
    assert "chat-event-answer-expectation" in dataset_kinds
    assert "model-replay-prompts" in dataset_kinds
    assert any("provenance" in limit.lower() for limit in manifest["known_limits"])


def test_create_manifest_can_omit_default_datasets(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "notes.md").write_text("notes", encoding="utf-8")

    manifest = create_benchmark_manifest.create_manifest(
        armory,
        include_default_datasets=False,
    )

    assert manifest["datasets"] == []


def test_create_manifest_reviewed_omits_scaffold_known_limits(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "notes.md").write_text("notes", encoding="utf-8")

    manifest = create_benchmark_manifest.create_manifest(
        armory,
        reviewed=True,
    )

    assert manifest["known_limits"] == []


def test_create_manifest_can_infer_roles_from_indexed_content(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "document-a.md").write_text(
        "Klausur. Bearbeitungszeit 90 Minuten. Aufgabe 1: 10 Punkte.",
        encoding="utf-8",
    )
    (armory / "materials" / "document-b.md").write_text(
        "Vorlesung overview. Inhaltsverzeichnis. Folien zur Übungsgruppe.",
        encoding="utf-8",
    )

    manifest = create_benchmark_manifest.create_manifest(
        armory,
        infer_roles_from_index=True,
    )

    by_source = {document["source"]: document for document in manifest["documents"]}
    assert by_source["materials/document-a.md"]["role"] == "past_exam"
    assert by_source["materials/document-a.md"]["document_type"] == "past-exam"
    assert "exam-format" in by_source["materials/document-a.md"]["stressors"]
    assert by_source["materials/document-b.md"]["role"] == "slides"
    assert by_source["materials/document-b.md"]["document_type"] == "lecture-slides"


def test_create_manifest_rejects_empty_armory(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    status = create_benchmark_manifest.main([str(armory), str(tmp_path / "manifest.json")])

    assert status == 2


def test_create_manifest_cli_writes_json(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    output = tmp_path / "manifest.json"
    (armory / "materials" / "notes.md").write_text("notes", encoding="utf-8")

    status = create_benchmark_manifest.main([str(armory), str(output), "--domain", "history"])

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["documents"][0]["domain"] == "history"


def test_create_manifest_cli_can_infer_roles_from_index(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    output = tmp_path / "manifest.json"
    (armory / "materials" / "unknown.md").write_text(
        "Question 1. Exercise 2. Problem 3. Due date Friday.",
        encoding="utf-8",
    )

    status = create_benchmark_manifest.main([str(armory), str(output), "--infer-roles-from-index"])

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["documents"][0]["role"] == "assignment"
