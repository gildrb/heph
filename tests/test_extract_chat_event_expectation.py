from __future__ import annotations

import json
from pathlib import Path

from scripts import extract_chat_event_expectation


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_extract_expectation_uses_evidence_notice_metadata(tmp_path: Path) -> None:
    events_path = tmp_path / "chat_events.jsonl"
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "material_operation",
                "operation": "sample_overview",
                "message": "Sampling corpus overview.",
                "metadata": {"query": "what is the material about"},
            },
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.pdf#chunk=0",
                            "text_excerpt": "Lecture excerpt with reviewed topic text.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.pdf#chunk=3",
                            "text_excerpt": "Exam excerpt with points and question text.",
                        },
                    ]
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {
                "type": "assistant_delta",
                "delta": "Retrieved overview sample: content [E1][E2].",
            },
            {
                "type": "turn_complete",
                "full_text": "Retrieved overview sample: content [E1][E2].",
            },
        ],
    )

    expectation = extract_chat_event_expectation.extract_expectation(events_path)

    assert expectation[0]["expected_citations"] == ["E1", "E2"]
    assert "must_include" not in expectation[0]
    assert expectation[0]["required_material_operations"] == ["sample_overview"]
    assert expectation[0]["forbidden_material_operations"] == ["search_index"]
    assert expectation[0]["evidence"] == [
        {
            "id": "E1",
            "source": "materials/lecture.pdf",
            "chunk": 0,
            "text": "Lecture excerpt with reviewed topic text.",
        },
        {
            "id": "E2",
            "source": "materials/exam.pdf",
            "chunk": 3,
            "text": "Exam excerpt with points and question text.",
        },
    ]
    assert "known_limits" in expectation[0]


def test_extract_expectation_cli_writes_scaffold(tmp_path: Path) -> None:
    events_path = tmp_path / "chat_events.jsonl"
    output_path = tmp_path / "chat_event_expectation.json"
    _write_jsonl(
        events_path,
        [
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/a.md#chunk=0",
                            "text_excerpt": "Alpha text.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/b.md#chunk=0",
                            "text_excerpt": "Beta text.",
                        },
                    ]
                },
            },
            {
                "type": "turn_complete",
                "full_text": "Retrieved overview sample [E1][E2].",
            },
        ],
    )

    status = extract_chat_event_expectation.main([str(events_path), "--output", str(output_path)])

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert status == 0
    assert payload[0]["evidence"][0]["source"] == "materials/a.md"


def test_extract_expectation_reviewed_omits_known_limits(tmp_path: Path) -> None:
    events_path = tmp_path / "chat_events.jsonl"
    _write_jsonl(
        events_path,
        [
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/a.md#chunk=0",
                            "text_excerpt": "Alpha text.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/b.md#chunk=0",
                            "text_excerpt": "Beta text.",
                        },
                    ]
                },
            },
            {"type": "turn_complete", "full_text": "Grounded answer [E1][E2]."},
        ],
    )

    expectation = extract_chat_event_expectation.extract_expectation(
        events_path,
        reviewed=True,
    )

    assert "known_limits" not in expectation[0]


def test_extract_expectation_rejects_missing_evidence_metadata(tmp_path: Path) -> None:
    events_path = tmp_path / "chat_events.jsonl"
    _write_jsonl(
        events_path,
        [{"type": "notice", "code": "evidence", "message": "Using evidence."}],
    )

    status = extract_chat_event_expectation.main(
        [str(events_path), "--output", str(tmp_path / "out.json")]
    )

    assert status == 2
