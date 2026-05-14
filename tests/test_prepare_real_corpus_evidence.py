from __future__ import annotations

import json
from pathlib import Path

from hephaistos.armory.storage import initialize
from scripts import prepare_real_corpus_evidence


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    materials = armory / "materials"
    (materials / "exam.md").write_text(
        "Question 1. Explain enzyme kinetics. [10 marks]\n",
        encoding="utf-8",
    )
    (materials / "lecture.md").write_text(
        "Table of contents\nLecture goals\nVorlesung overview\nExercise groups\n",
        encoding="utf-8",
    )
    return armory


def test_prepare_evidence_writes_manifest_and_keeps_scaffold_unreviewed(
    tmp_path: Path,
) -> None:
    armory = _make_armory(tmp_path)
    output_dir = tmp_path / "evidence"

    report = prepare_real_corpus_evidence.prepare_evidence(
        armory,
        output_dir,
        corpus_id="permissioned-test-corpus",
        domain="biology",
        min_documents=2,
        min_domains=1,
        min_roles=1,
        min_document_types=1,
        min_stressors=1,
        required_stressors=(),
        required_roles=("past_exam", "lecture"),
    )

    manifest = json.loads(Path(report.manifest_path).read_text(encoding="utf-8"))
    preflight = json.loads(Path(report.preflight_report_path).read_text(encoding="utf-8"))
    assert report.status == 1
    assert manifest["id"] == "permissioned-test-corpus"
    assert len(manifest["documents"]) == 2
    assert preflight["status"] == 1
    assert preflight["manifest_path"] == report.manifest_path
    assert (output_dir / "chat_events.jsonl").is_file()
    assert (output_dir / "chat_events.jsonl").read_text(encoding="utf-8") == ""
    chat_expectation = json.loads(
        (output_dir / "chat_event_expectation.json").read_text(encoding="utf-8")
    )
    assert chat_expectation[0]["task"] == "material-overview"
    assert chat_expectation[0]["expected_citations"] == ["E1", "E2"]
    assert chat_expectation[0]["evidence"] == []
    assert "Document signals" in chat_expectation[0]["must_not_include"]
    assert "Sampled orientation" in chat_expectation[0]["must_not_include"]
    assert any(
        "Generated scaffold" in failure or "missing provenance" in failure
        for failure in report.failures
    )
    assert "heph chat ask --jsonl" in report.next_chat_capture_command
    assert "chat_events.jsonl" in report.next_chat_capture_command
    assert "extract_chat_event_expectation" in report.next_chat_extract_command
    assert "chat_event_expectation.json" in report.next_chat_extract_command
    assert "benchmark_chat_events" in report.next_chat_verify_command
    assert "chat_event_expectation.json" in report.next_chat_verify_command
    assert "--real-manifest" in report.next_audit_command
    assert "--real-preflight-report" in report.next_audit_command


def test_prepare_evidence_keeps_strict_failures_visible(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    report = prepare_real_corpus_evidence.prepare_evidence(
        armory,
        tmp_path / "evidence",
        min_documents=40,
    )

    preflight = json.loads(Path(report.preflight_report_path).read_text(encoding="utf-8"))
    assert report.status == 1
    assert report.failures
    assert preflight["status"] == 1


def test_prepare_evidence_can_emit_reviewed_manifest(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    report = prepare_real_corpus_evidence.prepare_evidence(
        armory,
        tmp_path / "evidence",
        min_documents=2,
        min_domains=1,
        min_roles=1,
        min_document_types=1,
        min_stressors=1,
        required_stressors=(),
        required_roles=("past_exam", "lecture"),
        reviewed_manifest=True,
    )

    manifest = json.loads(Path(report.manifest_path).read_text(encoding="utf-8"))
    assert manifest["known_limits"] == []


def test_prepare_evidence_cli_writes_summary_report(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    output_dir = tmp_path / "evidence"
    json_report = tmp_path / "summary.json"

    status = prepare_real_corpus_evidence.main(
        [
            str(armory),
            str(output_dir),
            "--min-documents",
            "2",
            "--min-domains",
            "1",
            "--min-roles",
            "1",
            "--min-document-types",
            "1",
            "--min-stressors",
            "1",
            "--require-role",
            "past_exam",
            "--require-role",
            "slides",
            "--json-report",
            str(json_report),
        ]
    )

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert status == 1
    assert payload["status"] == 1
    assert Path(payload["manifest_path"]).is_file()
    assert Path(payload["preflight_report_path"]).is_file()
    assert "heph chat ask --jsonl" in payload["next_chat_capture_command"]
    assert "extract_chat_event_expectation" in payload["next_chat_extract_command"]
    assert "benchmark_chat_events" in payload["next_chat_verify_command"]
