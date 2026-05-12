from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from hephaistos.runtime import ChatConfig
from scripts import replay_answer_benchmark, run_replay_answer_eval


def _write_replay_dataset(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                (
                    '{"id":"dijkstra","domain":"computer-science",'
                    '"task":"grounded-explanation","prompt":"Explain Dijkstra.",'
                    '"expected_citations":["E1"],"must_include":["priority queue"],'
                    '"supported_claims":[{"text":"priority queue","evidence_id":"E1"}]}'
                ),
                (
                    '{"id":"calculus","domain":"mathematics","task":"single-source-fact",'
                    '"prompt":"What rule?","expected_citations":["E1"],'
                    '"must_include":["product rule"],'
                    '"supported_claims":[{"text":"product rule","evidence_id":"E1"}]}'
                ),
                (
                    '{"id":"unknown","domain":"study-methods","task":"abstention",'
                    '"prompt":"Unknown?","require_citations":false,'
                    '"require_abstention":true,"must_include":["do not contain"]}'
                ),
            )
        ),
        encoding="utf-8",
    )


def _fixtures() -> list[replay_answer_benchmark.AnswerFixture]:
    return [
        {
            "id": "dijkstra",
            "domain": "computer-science",
            "task": "grounded-explanation",
            "query": "Explain Dijkstra.",
            "answer": "Dijkstra uses a priority queue [E1].",
            "evidence": [
                {
                    "id": "E1",
                    "source": "materials/algorithms.md",
                    "chunk": 0,
                    "text": "Dijkstra uses a priority queue.",
                }
            ],
            "expected_citations": ["E1"],
            "must_include": ["priority queue"],
            "supported_claims": [{"text": "priority queue", "evidence_id": "E1"}],
        },
        {
            "id": "calculus",
            "domain": "mathematics",
            "task": "single-source-fact",
            "query": "What rule?",
            "answer": "Integration by parts follows from the product rule [E1].",
            "evidence": [
                {
                    "id": "E1",
                    "source": "materials/calculus.md",
                    "chunk": 0,
                    "text": "Integration by parts follows from the product rule.",
                }
            ],
            "expected_citations": ["E1"],
            "must_include": ["product rule"],
            "supported_claims": [{"text": "product rule", "evidence_id": "E1"}],
        },
        {
            "id": "unknown",
            "domain": "study-methods",
            "task": "abstention",
            "query": "Unknown?",
            "answer": "The enabled armory sources do not contain that answer.",
            "evidence": [],
            "require_citations": False,
            "require_abstention": True,
            "must_include": ["do not contain"],
        },
    ]


def test_replay_answer_eval_writes_and_scores_fixtures(
    tmp_path: Path,
    capsys,
) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_replay_dataset(dataset)

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = _fixtures()
        status = run_replay_answer_eval.main([str(tmp_path / "armory"), str(dataset), str(output)])

    captured = capsys.readouterr()
    assert status == 0
    assert "Wrote 3 answer fixture(s)" in captured.out
    assert "pass_rate=100.0%" in captured.out
    assert output.is_file()
    assert len(output.read_text(encoding="utf-8").splitlines()) == 3


def test_replay_answer_eval_writes_machine_readable_report(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    report_path = tmp_path / "reports" / "eval.json"
    _write_replay_dataset(dataset)

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = _fixtures()
        status = run_replay_answer_eval.run_replay_answer_eval(
            tmp_path / "armory",
            dataset,
            output,
            ChatConfig(model="eval-model", base_url="https://example.invalid"),
            report_path=report_path,
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert report["status"] == 0
    assert report["model"] == "eval-model"
    assert report["base_url"] == "https://example.invalid"
    assert report["output"] == str(output)
    assert report["thresholds"]["answer_pass_rate"] == 1.0
    assert report["thresholds"]["answer_shape"] == 1.0
    assert report["thresholds"]["evidence_coverage"] == 1.0
    assert report["report"]["pass_rate"] == 1.0
    assert report["report"]["answer_shape_rate"] == 1.0
    assert report["report"]["evidence_coverage_rate"] == 1.0
    assert report["report"]["domains"] == ["computer-science", "mathematics", "study-methods"]
    assert report["report_path"] == str(report_path)


def test_replay_answer_eval_can_compare_current_report_to_baseline(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    _write_replay_dataset(dataset)

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = _fixtures()
        assert (
            run_replay_answer_eval.run_replay_answer_eval(
                tmp_path / "armory",
                dataset,
                output,
                ChatConfig(),
                report_path=baseline_path,
            )
            == 0
        )
        replay.return_value = _fixtures()
        status = run_replay_answer_eval.run_replay_answer_eval(
            tmp_path / "armory",
            dataset,
            output,
            ChatConfig(),
            report_path=current_path,
            compare_to=baseline_path,
        )

    assert status == 0


def test_replay_answer_eval_rejects_compare_without_current_report(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    baseline_path = tmp_path / "baseline.json"
    _write_replay_dataset(dataset)
    baseline_path.write_text('{"report":{"pass_rate":1.0}}\n', encoding="utf-8")

    status = run_replay_answer_eval.main(
        [str(tmp_path / "armory"), str(dataset), str(output), "--compare-to", str(baseline_path)]
    )

    assert status == 2


def test_replay_answer_eval_gates_generated_answer_quality(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_replay_dataset(dataset)
    fixtures = _fixtures()
    fixtures[0]["answer"] = "Dijkstra uses a queue."

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = fixtures
        status = run_replay_answer_eval.run_replay_answer_eval(
            tmp_path / "armory",
            dataset,
            output,
            ChatConfig(),
            answer_pass_rate=1.0,
        )

    assert status == 1


def test_replay_answer_eval_rejects_narrow_generated_tasks(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_replay_dataset(dataset)
    fixtures = _fixtures()
    for fixture in fixtures:
        fixture["domain"] = "computer-science"
        fixture["task"] = "grounded-explanation"

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = fixtures
        status = run_replay_answer_eval.main([str(tmp_path / "armory"), str(dataset), str(output)])

    assert status == 2


def test_replay_answer_eval_preserves_json_fixture_shape(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    output = tmp_path / "answers.jsonl"
    _write_replay_dataset(dataset)

    with patch("scripts.run_replay_answer_eval.replay_answer_benchmark.replay_cases") as replay:
        replay.return_value = _fixtures()
        run_replay_answer_eval.run_replay_answer_eval(
            tmp_path / "armory",
            dataset,
            output,
            ChatConfig(),
        )

    first = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert first["domain"] == "computer-science"
    assert first["task"] == "grounded-explanation"
