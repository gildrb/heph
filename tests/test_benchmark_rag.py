from __future__ import annotations

import json
from pathlib import Path

from hephaistos.armory.storage import initialize
from scripts import benchmark_rag


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    (armory / "materials" / "graphs.md").write_text(
        "Dijkstra shortest paths use a priority queue and relax weighted graph edges.\n",
        encoding="utf-8",
    )
    (armory / "materials" / "systems.md").write_text(
        "Cache invalidation is a common systems design concern.\n",
        encoding="utf-8",
    )
    return armory


def test_load_cases_supports_jsonl(tmp_path: Path) -> None:
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "graphs",
                        "domain": "computer-science",
                        "task": "single-source-fact",
                        "query": "priority queue graph relaxation",
                        "expected": ["materials/graphs.md"],
                        "forbidden_before_expected": ["materials/systems.md"],
                    }
                ),
                "# comment",
                json.dumps(
                    {
                        "query": "cache invalidation",
                        "expected": ["materials/systems.md#chunk=0"],
                        "top_k": 3,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = benchmark_rag.load_cases(dataset)

    assert [case.case_id for case in cases] == ["graphs", "case-2"]
    assert cases[0].domain == "computer-science"
    assert cases[0].task == "single-source-fact"
    assert cases[0].forbidden_before_expected == ("materials/systems.md",)
    assert cases[1].top_k == 3
    assert cases[1].expected == ("materials/systems.md#chunk=0",)


def test_run_benchmark_scores_source_and_chunk_matches(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    cases = [
        benchmark_rag.BenchmarkCase(
            case_id="source-match",
            domain="computer-science",
            task="single-source-fact",
            query="Which material discusses graph edge relaxation?",
            expected=("materials/graphs.md",),
        ),
        benchmark_rag.BenchmarkCase(
            case_id="chunk-match",
            domain="systems",
            task="chunk-pinpoint",
            query="What mentions cache invalidation?",
            expected=("materials/systems.md#chunk=0",),
        ),
    ]

    report = benchmark_rag.run_benchmark(armory, cases, top_k=2, min_score=0.0)

    assert report.cases == 2
    assert report.domains == ("computer-science", "systems")
    assert report.tasks == ("chunk-pinpoint", "single-source-fact")
    assert report.hit_rate == 1.0
    assert report.mean_reciprocal_rank == 1.0
    assert report.mean_expected_recall == 1.0
    assert report.forbidden_before_expected_avoidance == 1.0
    assert report.forbidden_before_expected_failures == ()
    assert report.mean_latency_ms >= 0.0
    assert report.misses == ()
    assert report.results[0].retrieved[0] == "materials/graphs.md#chunk=0"
    assert report.results[0].retrieved_chunks[0].ref == "materials/graphs.md#chunk=0"
    assert report.results[0].retrieved_chunks[0].score >= 0.0
    assert "priority queue" in report.results[0].retrieved_chunks[0].text_excerpt
    assert report.results[0].first_forbidden_rank is None
    assert report.results[0].forbidden_before_expected_ok is True
    assert report.results[0].elapsed_ms >= 0.0


def test_main_fails_below_threshold(tmp_path: Path, capsys) -> None:
    armory = _make_armory(tmp_path)
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "miss",
                        "query": "totally unrelated astronomy term",
                        "expected": ["materials/graphs.md"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_rag.main(
        [
            str(armory),
            str(dataset),
            "--min-score",
            "0.5",
            "--min-hit-rate",
            "1.0",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "hit_rate=0.0%" in captured.out
    assert "misses=miss" in captured.out


def test_main_gates_expected_recall(tmp_path: Path, capsys) -> None:
    armory = _make_armory(tmp_path)
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "partial",
                        "query": "priority queue graph relaxation",
                        "expected": ["materials/graphs.md", "materials/missing.md"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_rag.main(
        [
            str(armory),
            str(dataset),
            "--min-score",
            "0.0",
            "--min-hit-rate",
            "1.0",
            "--min-expected-recall",
            "1.0",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "hit_rate=100.0%" in captured.out
    assert "expected_recall=50.0%" in captured.out


def test_main_gates_forbidden_before_expected_avoidance(
    tmp_path: Path,
    capsys,
) -> None:
    armory = _make_armory(tmp_path)
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "wrong-first",
                        "query": "cache invalidation",
                        "expected": ["materials/graphs.md"],
                        "forbidden_before_expected": ["materials/systems.md"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_rag.main(
        [
            str(armory),
            str(dataset),
            "--min-score",
            "0.0",
            "--min-forbidden-before-expected-avoidance",
            "1.0",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "forbidden_before_expected_avoidance=0.0%" in captured.out
    assert "forbidden_before_expected_failures=wrong-first" in captured.out
