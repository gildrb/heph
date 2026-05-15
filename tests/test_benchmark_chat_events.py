from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import benchmark_chat_events


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_overview_expectation(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "overview",
                    "task": "material-overview",
                    "must_include": [
                        "These are the study topics",
                        "Choose a topic",
                    ],
                    "must_not_include": [
                        "the files cover",
                        "next action",
                        "say ready when you want recall",
                        "ask for recall",
                        "answer from memory",
                        "source-backed",
                        "source backed",
                        "Retrieved overview sample",
                        "not an exhaustive summary",
                    ],
                    "min_words": 24,
                    "min_citation_count": 2,
                    "min_distinct_sources": 2,
                    "min_bullet_count": 2,
                    "min_cited_bullet_count": 2,
                    "max_explicit_date_lines": 1,
                    "required_material_operations": ["sample_overview"],
                    "forbidden_material_operations": ["search_index"],
                    "evidence": [
                        {
                            "id": "E1",
                            "source": "materials/lecture.md",
                            "chunk": 0,
                            "text": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "id": "E2",
                            "source": "materials/exam.md",
                            "chunk": 0,
                            "text": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )


def _material_operation_rows() -> list[dict[str, object]]:
    return [
        {
            "type": "material_operation",
            "operation": "index_ready",
            "message": "Material index ready: 2 enabled sources, 2 chunks.",
            "metadata": {"indexed_sources": 2, "indexed_chunks": 2},
        },
        {
            "type": "material_operation",
            "operation": "sample_overview",
            "message": "Sampling corpus overview: 2 excerpts from 2 of 2 indexed sources.",
            "metadata": {
                "query": "what is the material about",
                "evidence_blocks": 2,
                "sampled_sources": 2,
                "total_sources": 2,
            },
        },
        {
            "type": "material_operation",
            "operation": "read_excerpt",
            "message": "Opened materials/lecture.md#chunk=0: Lecture notes.",
            "metadata": {
                "evidence_id": "E1",
                "ref": "materials/lecture.md#chunk=0",
                "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
            },
        },
        {
            "type": "material_operation",
            "operation": "read_excerpt",
            "message": "Opened materials/exam.md#chunk=0: Past exam.",
            "metadata": {
                "evidence_id": "E2",
                "ref": "materials/exam.md#chunk=0",
                "text_excerpt": "Past exam. Question 1 asks for a proof.",
            },
        },
    ]


def test_chat_event_benchmark_passes_structured_overview_stream(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            *_material_operation_rows(),
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.has_consistent_completion
    assert report.has_material_operation
    assert report.has_material_operation_metadata
    assert report.material_operation_count == 4
    assert report.has_evidence_metadata
    assert report.has_tool_runtime_metadata
    assert report.failures == ()


def test_chat_event_benchmark_rejects_overview_study_loop_tail(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1].\n\n"
        "Next action: Review the smallest source-backed piece, then ask for recall."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            *_material_operation_rows(),
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.answer_pass_rate == 0.0
    assert any("forbidden text: next action" in failure for failure in report.failures)
    assert any("source-backed" in failure for failure in report.failures)


def test_chat_event_benchmark_validates_tool_runtime_notice_metadata(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            *_material_operation_rows(),
            {
                "type": "notice",
                "code": "acceptance_criteria",
                "message": "Acceptance criteria: inspect sources with tools.",
                "metadata": {"source": "agent_harness", "requires_tools": True},
            },
            {
                "type": "notice",
                "code": "tool_runtime",
                "message": "Execution note: tool 'read_file' failed.",
                "metadata": {
                    "tool": "read_file",
                    "reason": "failed",
                    "latency_ms": 4.2,
                    "result_length": 21,
                    "error": "file not found",
                },
            },
            {
                "type": "notice",
                "code": "tool_runtime",
                "message": "Execution note: repeated call.",
                "metadata": {
                    "tool": "read_file",
                    "reason": "repeated_call",
                    "repeat_count": 2,
                    "arguments": {"path": "missing.md"},
                },
            },
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.has_tool_runtime
    assert report.has_tool_runtime_metadata
    assert report.has_acceptance_criteria
    assert report.has_acceptance_criteria_metadata
    assert report.failures == ()


def test_chat_event_benchmark_fails_malformed_acceptance_criteria_notice(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "notice",
                "code": "acceptance_criteria",
                "message": "Criteria hidden.",
                "metadata": {"source": "other", "requires_tools": False},
            },
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.has_acceptance_criteria
    assert not report.has_acceptance_criteria_metadata
    assert any("missing criteria message" in failure for failure in report.failures)
    assert any("invalid source" in failure for failure in report.failures)
    assert any("requires_tools" in failure for failure in report.failures)


def test_chat_event_benchmark_fails_malformed_tool_runtime_notice(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "notice",
                "code": "tool_runtime",
                "message": "Execution note: tool failed.",
                "metadata": {"reason": "mystery", "latency_ms": "slow"},
            },
            {
                "type": "notice",
                "code": "tool_runtime",
                "message": "Execution note: repeated call.",
                "metadata": {
                    "tool": "read_file",
                    "reason": "repeated_call",
                    "repeat_count": 1,
                },
            },
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.has_tool_runtime
    assert not report.has_tool_runtime_metadata
    assert any("missing tool" in failure for failure in report.failures)
    assert any("invalid reason" in failure for failure in report.failures)
    assert any("invalid latency_ms" in failure for failure in report.failures)
    assert any("invalid repeat_count" in failure for failure in report.failures)
    assert any("missing repeated arguments" in failure for failure in report.failures)


def test_chat_event_benchmark_fails_malformed_material_operations(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "material_operation",
                "operation": "search_index",
                "message": "Searching indexed materials.",
            },
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {
                "type": "material_operation",
                "operation": "read_excerpt",
                "message": "Opened materials/lecture.md#chunk=0.",
                "metadata": {"ref": "materials/lecture.md#chunk=0"},
            },
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert report.has_material_operation
    assert not report.has_material_operation_metadata
    assert any("appears after assistant answer" in failure for failure in report.failures)
    assert any("missing metadata" in failure for failure in report.failures)
    assert any("missing index_ready" in failure for failure in report.failures)
    assert any("missing required operation" in failure for failure in report.failures)
    assert any("forbidden operation" in failure for failure in report.failures)


def test_chat_event_benchmark_enforces_expected_material_operations(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "These are the study topics I found in the material [E1] [E2].\n"
        "- Definitions, theorems, and examples [E1].\n"
        "- Past exam proof practice [E2].\n"
        "- Choose a topic to study next with the menu [E1]."
    )
    rows = _material_operation_rows()
    rows[1] = {
        "type": "material_operation",
        "operation": "search_index",
        "message": "Searching indexed materials for: what is the material about",
        "metadata": {"query": "what is the material about", "top_k": 12},
    }
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            *rows,
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert any(
        "missing required operation(s): sample_overview" in failure for failure in report.failures
    )
    assert any("forbidden operation(s): search_index" in failure for failure in report.failures)


def test_chat_event_benchmark_fails_missing_stage_and_bad_overview_shape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = "The files cover lectures and exams [E1] [E2]. Say ready when you want recall."
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    status = benchmark_chat_events.main(
        [str(events_path), "--answer-expectation", str(expectation_path)]
    )

    output = capsys.readouterr().out
    assert status == 1
    assert "missing evidence notice" in output
    assert "answer benchmark failed" in output


def test_chat_event_benchmark_fails_unreadable_student_visible_diagnostics(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "Retrieved overview sample: 2 excerpts from 2 indexed sources [E1] [E2].\n"
        "- Document signals: @lecture.md looks like lecture notes [E1].\n"
        "- Evidence roles: @exam.md looks like past exam material [E2].\n"
        "- Scope: this is a grounded sample, not an exhaustive summary of every file.\n\n"
        "_sources: E1: lecture.md (materials/lecture.md; score 0.93; "
        "expand: /evidence E1; open: /evidence E1 open)_"
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert any("raw sources footer" in failure for failure in report.failures)
    assert any("retrieval score diagnostics" in failure for failure in report.failures)
    assert any("open command diagnostics" in failure for failure in report.failures)


def test_chat_event_benchmark_fails_when_delta_and_completion_disagree(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    good_answer = (
        "Retrieved overview sample: 2 excerpts from 2 indexed sources [E1] [E2].\n"
        "- Document signals: @lecture.md looks like lecture notes [E1].\n"
        "- Evidence roles: @exam.md looks like past exam material [E2].\n"
        "- Scope: this is a grounded sample, not an exhaustive summary of every file."
    )
    stale_answer = "The files cover lectures and exams [E1] [E2]. Say ready."
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {"type": "notice", "code": "evidence", "message": "Using evidence."},
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": good_answer},
            {"type": "turn_complete", "full_text": stale_answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    status = benchmark_chat_events.main(
        [str(events_path), "--answer-expectation", str(expectation_path)]
    )

    output = capsys.readouterr().out
    assert status == 1
    assert "assistant delta text does not match turn completion text" in output
    assert "consistent_completion=no" in output


def test_chat_event_benchmark_fails_missing_evidence_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "Retrieved overview sample: 2 excerpts from 2 indexed sources [E1] [E2].\n"
        "- Document signals: @lecture.md looks like lecture notes [E1].\n"
        "- Evidence roles: @exam.md looks like past exam material [E2].\n"
        "- Scope: this is a grounded sample, not an exhaustive summary of every file."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {"type": "notice", "code": "evidence", "message": "Using evidence."},
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    status = benchmark_chat_events.main(
        [str(events_path), "--answer-expectation", str(expectation_path)]
    )

    output = capsys.readouterr().out
    assert status == 1
    assert "evidence notice missing metadata" in output
    assert "evidence_metadata=no" in output


def test_chat_event_benchmark_fails_metadata_without_expected_citation(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "Retrieved overview sample: 2 excerpts from 2 indexed sources [E1] [E2].\n"
        "- Document signals: @lecture.md looks like lecture notes [E1].\n"
        "- Evidence roles: @exam.md looks like past exam material [E2].\n"
        "- Scope: this is a grounded sample, not an exhaustive summary of every file."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 1,
                        "sampled_sources": 1,
                        "total_sources": 1,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes.",
                        }
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)

    report = benchmark_chat_events.run_chat_event_benchmark(
        benchmark_chat_events.load_events(events_path),
        expectation=benchmark_chat_events.load_expectation(expectation_path),
    )

    assert not report.has_evidence_metadata
    assert any("E2" in failure for failure in report.failures)


def test_chat_event_benchmark_rejects_unreviewed_expectation_known_limits(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.jsonl"
    expectation_path = tmp_path / "expectation.json"
    answer = (
        "Retrieved overview sample: 2 excerpts from 2 indexed sources [E1] [E2].\n"
        "- Document signals: @lecture.md looks like lecture notes [E1].\n"
        "- Evidence roles: @exam.md looks like past exam material [E2].\n"
        "- Scope: this is a grounded sample, not an exhaustive summary of every file."
    )
    _write_jsonl(
        events_path,
        [
            {"type": "notice", "code": "reading", "message": "Reading."},
            {
                "type": "notice",
                "code": "evidence",
                "message": "Using evidence.",
                "metadata": {
                    "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                    "coverage": {
                        "evidence_blocks": 2,
                        "sampled_sources": 2,
                        "total_sources": 2,
                    },
                    "items": [
                        {
                            "evidence_id": "E1",
                            "ref": "materials/lecture.md#chunk=0",
                            "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                        },
                        {
                            "evidence_id": "E2",
                            "ref": "materials/exam.md#chunk=0",
                            "text_excerpt": "Past exam. Question 1 asks for a proof.",
                        },
                    ],
                },
            },
            {"type": "notice", "code": "writing", "message": "Writing."},
            {"type": "assistant_delta", "delta": answer},
            {"type": "turn_complete", "full_text": answer, "turn_index": 1},
        ],
    )
    _write_overview_expectation(expectation_path)
    payload = json.loads(expectation_path.read_text(encoding="utf-8"))
    payload[0]["known_limits"] = ["Review scaffold extracted from chat JSONL."]
    expectation_path.write_text(json.dumps(payload), encoding="utf-8")

    status = benchmark_chat_events.main(
        [str(events_path), "--answer-expectation", str(expectation_path)]
    )

    output = capsys.readouterr().out
    assert status == 1
    assert "unresolved known_limits" in output
