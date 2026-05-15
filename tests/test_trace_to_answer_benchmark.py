from __future__ import annotations

import json
from pathlib import Path

from scripts import benchmark_answers, trace_to_answer_benchmark


def _write_trace(
    path: Path,
    *,
    answer: str = "Dijkstra uses a priority queue [E1].",
    study_task: str = "",
    evidence_coverage: dict[str, int] | None = None,
) -> None:
    coverage = evidence_coverage or {
        "evidence_blocks": 1,
        "sampled_sources": 1,
        "total_sources": 1,
    }
    events = [
        {"type": "user_message", "ts": "2026-05-11T00:00:00Z", "content": "How?"},
        {
            "type": "rag_retrieve",
            "ts": "2026-05-11T00:00:01Z",
            "query": "How?",
            "top_k": 5,
            "retrieved": 1,
            "scores": [0.9],
            "chunks": [
                {
                    "ref": "materials/graphs.md#chunk=0",
                    "score": 0.9,
                    "text_excerpt": "Dijkstra shortest paths use a priority queue.",
                }
            ],
        },
        {
            "type": "session",
            "ts": "2026-05-11T00:00:02Z",
            "event": "reply",
            "reply_excerpt": answer,
            "study_task": study_task,
            "evidence_refs": ["materials/graphs.md#chunk=0"],
            "evidence_items": [
                {
                    "evidence_id": "E1",
                    "ref": "materials/graphs.md#chunk=0",
                    "score": 0.9,
                    "text_excerpt": "Dijkstra shortest paths use a priority queue.",
                }
            ],
            "evidence_coverage": coverage,
            "verification_notice": "",
        },
    ]
    path.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )


def test_fixtures_from_trace_preserves_answer_and_evidence(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    _write_trace(trace)

    fixtures = trace_to_answer_benchmark.fixtures_from_trace(
        trace,
        expect_all_citations=True,
    )

    assert fixtures == [
        {
            "id": "sess-turn-1",
            "query": "How?",
            "answer": "Dijkstra uses a priority queue [E1].",
            "evidence": [
                {
                    "id": "E1",
                    "source": "materials/graphs.md",
                    "chunk": 0,
                    "text": "Dijkstra shortest paths use a priority queue.",
                    "score": 0.9,
                }
            ],
            "task": "trace-replay",
            "require_citations": True,
            "expected_citations": ["E1"],
            "evidence_coverage": {
                "evidence_blocks": 1,
                "sampled_sources": 1,
                "total_sources": 1,
            },
        }
    ]


def test_fixtures_from_trace_preserves_study_task_label(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    _write_trace(trace, study_task="material-overview")

    fixtures = trace_to_answer_benchmark.fixtures_from_trace(trace)

    assert fixtures[0]["task"] == "material-overview"


def test_material_overview_trace_gets_generic_answer_shape_contract(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    _write_trace(
        trace,
        answer=(
            "The retrieved overview sample mentions Dijkstra [E1]. "
            "It is not an exhaustive summary."
        ),
        study_task="material-overview",
        evidence_coverage={
            "evidence_blocks": 2,
            "sampled_sources": 2,
            "total_sources": 9,
        },
    )

    fixtures = trace_to_answer_benchmark.fixtures_from_trace(trace)

    assert fixtures[0]["task"] == "material-overview"
    assert "must_include" not in fixtures[0]
    assert fixtures[0]["must_not_include"] == [
        "No evidence citations",
        "Say ready when you want recall",
        "the files cover",
    ]
    assert fixtures[0]["min_words"] == 24
    assert fixtures[0]["max_words"] == 120
    assert fixtures[0]["min_citation_count"] == 2
    assert fixtures[0]["min_distinct_sources"] == 2
    assert fixtures[0]["min_sampled_sources"] == 2
    assert fixtures[0]["min_bullet_count"] == 2
    assert fixtures[0]["min_cited_bullet_count"] == 2
    assert fixtures[0]["max_explicit_date_lines"] == 1
    assert fixtures[0]["evidence_coverage"] == {
        "evidence_blocks": 2,
        "sampled_sources": 2,
        "total_sources": 9,
    }


def test_material_overview_trace_contract_catches_vague_bad_answer(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_trace(
        trace,
        answer="The files cover computer science topics [E1]. Say ready when you want recall.",
        study_task="material-overview",
    )

    status = trace_to_answer_benchmark.main([str(trace), str(output), "--score"])

    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output))
    assert status == 1
    assert report.results[0].evidence_coverage == {
        "evidence_blocks": 1,
        "sampled_sources": 1,
        "total_sources": 1,
    }
    assert report.results[0].missing_required_text == ()
    assert report.results[0].forbidden_text_present == (
        "Say ready when you want recall",
        "the files cover",
    )
    assert report.results[0].shape_failures == (
        "words 13 below 24",
        "citations 1 below 2",
        "distinct sources 1 below 2",
        "bullets 0 below 2",
        "cited bullets 0 below 2",
    )
    assert report.results[0].coverage_failures == ("sampled sources 1 below 2",)


def test_trace_fixture_scores_with_answer_benchmark(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_trace(trace)

    status = trace_to_answer_benchmark.main(
        [str(trace), str(output), "--expect-all-citations", "--score"]
    )

    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output))
    assert status == 0
    assert report.pass_rate == 1.0


def test_trace_scoring_fails_uncited_evidence_answer(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_trace(trace, answer="Dijkstra uses a priority queue.")

    status = trace_to_answer_benchmark.main([str(trace), str(output), "--score"])

    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output))
    assert status == 1
    assert report.pass_rate == 0.0
    assert report.results[0].missing_citations is True


def test_trace_expectations_add_answer_contract_checks(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    expectations = tmp_path / "expectations.json"
    output = tmp_path / "answers.jsonl"
    _write_trace(trace, answer="CORRECT: Dijkstra uses a priority queue [E1].")
    expectations.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "turn": 1,
                        "domain": "computer-science",
                        "task": "shortest-paths",
                        "required_label": "CORRECT",
                        "must_include": ["priority queue"],
                        "must_not_include": ["negative weights"],
                        "supported_claims": [{"text": "priority queue", "evidence_id": "E1"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = trace_to_answer_benchmark.main(
        [str(trace), str(output), "--expectations", str(expectations), "--score"]
    )

    fixture = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert status == 0
    assert fixture["domain"] == "computer-science"
    assert fixture["task"] == "shortest-paths"
    assert fixture["required_label"] == "CORRECT"
    assert fixture["must_include"] == ["priority queue"]
    assert fixture["must_not_include"] == ["negative weights"]
    assert fixture["supported_claims"] == [{"text": "priority queue", "evidence_id": "E1"}]


def test_trace_expectations_can_fail_required_text(tmp_path: Path) -> None:
    trace = tmp_path / "sess.jsonl"
    expectations = tmp_path / "expectations.json"
    output = tmp_path / "answers.jsonl"
    _write_trace(trace)
    expectations.write_text(
        json.dumps({"cases": [{"id": "sess-turn-1", "must_include": ["binary heap"]}]}),
        encoding="utf-8",
    )

    status = trace_to_answer_benchmark.main(
        [str(trace), str(output), "--expectations", str(expectations), "--score"]
    )

    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output))
    assert status == 1
    assert report.results[0].missing_required_text == ("binary heap",)


def test_trace_converter_rejects_trace_without_reply(tmp_path: Path) -> None:
    trace = tmp_path / "empty.jsonl"
    output = tmp_path / "answers.jsonl"
    trace.write_text(
        json.dumps({"type": "user_message", "content": "hello"}) + "\n",
        encoding="utf-8",
    )

    status = trace_to_answer_benchmark.main([str(trace), str(output)])

    assert status == 2
    assert not output.exists()
