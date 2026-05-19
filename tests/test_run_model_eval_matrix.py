from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import run_model_eval_matrix

PRIVATE_MODEL_MATRIX_EXAMPLE = Path("benchmarks/model-matrix.example.json")


def _write_replay_dataset(path: Path) -> None:
    path.write_text(
        "\n".join(
            json.dumps(case)
            for case in (
                {
                    "id": "case-1",
                    "domain": "computer-science",
                    "task": "grounded-explanation",
                    "prompt": "Explain with evidence.",
                    "must_include": ["evidence"],
                },
                {
                    "id": "case-2",
                    "domain": "mathematics",
                    "task": "single-source-fact",
                    "prompt": "State the rule.",
                    "expected_citations": ["E1"],
                },
                {
                    "id": "case-3",
                    "domain": "study-methods",
                    "task": "abstention",
                    "prompt": "Answer only if known.",
                    "require_abstention": True,
                },
                {
                    "id": "case-4",
                    "domain": "cross-domain",
                    "task": "material-overview",
                    "prompt": "Give a grounded overview of the enabled material.",
                    "must_include": ["retrieved overview sample"],
                    "min_words": 24,
                    "max_words": 120,
                    "min_citation_count": 2,
                    "min_distinct_sources": 2,
                    "min_bullet_count": 2,
                    "min_cited_bullet_count": 2,
                    "max_explicit_date_lines": 1,
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_matrix(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "local-small",
                        "group": "local",
                        "model": "local-model",
                        "base_url": "http://localhost:11434/v1",
                        "responsibilities": ["chunk labeling", "question formatting"],
                    },
                    {
                        "id": "frontier-hosted",
                        "group": "frontier",
                        "model": "frontier-model",
                        "responsibilities": ["essay feedback", "misconception correction"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_candidate_report(
    path: Path,
    *,
    pass_rate: float = 1.0,
    include_required_text: bool = True,
    include_coverage: bool = True,
    domains: list[str] | None = None,
) -> None:
    report: dict[str, object] = {
        "pass_rate": pass_rate,
        "citation_validity_rate": 1.0,
        "citation_presence_rate": 1.0,
        "expected_citation_rate": 1.0,
        "forbidden_text_rate": 1.0,
        "supported_claim_rate": 1.0,
        "answer_shape_rate": 1.0,
        "evidence_coverage_rate": 1.0,
        "required_label_rate": 1.0,
    }
    if include_coverage:
        report["cases"] = 4
        report["domains"] = domains or [
            "computer-science",
            "cross-domain",
            "mathematics",
            "study-methods",
        ]
        report["tasks"] = [
            "abstention",
            "grounded-explanation",
            "material-overview",
            "single-source-fact",
        ]
    if include_required_text:
        report["required_text_rate"] = 1.0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"report": report}),
        encoding="utf-8",
    )


def test_example_model_matrix_loads_and_covers_required_groups() -> None:
    if not PRIVATE_MODEL_MATRIX_EXAMPLE.is_file():
        pytest.skip("private model matrix example is local-only")
    candidates = run_model_eval_matrix.load_candidates(PRIVATE_MODEL_MATRIX_EXAMPLE)

    report = run_model_eval_matrix.validate_model_eval_matrix(candidates)

    assert report.status == 0
    assert report.groups == ("frontier", "local")
    assert "answer point matching" in candidates[0].responsibilities
    assert "misconception correction" in candidates[1].responsibilities
    assert "api_key" not in json.dumps(asdict_like(report))


def asdict_like(report: run_model_eval_matrix.ModelEvalMatrixReport) -> dict[str, object]:
    return {
        "status": report.status,
        "groups": list(report.groups),
        "candidates": report.candidates,
    }


def test_load_candidates_uses_env_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HEPH_EVAL_KEY", "secret")
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps(
            [
                {
                    "id": "local/small",
                    "group": "local",
                    "model": "local",
                    "api_key_env": "HEPH_EVAL_KEY",
                }
            ]
        ),
        encoding="utf-8",
    )

    candidates = run_model_eval_matrix.load_candidates(matrix)

    assert candidates[0].candidate_id == "local-small"
    assert candidates[0].api_key == "secret"


def test_load_candidates_deduplicates_responsibilities(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps(
            [
                {
                    "id": "local",
                    "group": "local",
                    "model": "local",
                    "base_url": "http://localhost:11434/v1",
                    "responsibilities": ["question formatting", "Question Formatting"],
                }
            ]
        ),
        encoding="utf-8",
    )

    candidates = run_model_eval_matrix.load_candidates(matrix)

    assert candidates[0].responsibilities == ("question formatting",)


def test_load_candidates_reads_candidate_timeout(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps(
            [
                {
                    "id": "local",
                    "group": "local",
                    "model": "local",
                    "base_url": "http://localhost:11434/v1",
                    "timeout_seconds": 7,
                }
            ]
        ),
        encoding="utf-8",
    )

    candidates = run_model_eval_matrix.load_candidates(matrix)

    assert candidates[0].timeout_seconds == 7


def test_model_eval_matrix_runs_candidates_and_writes_combined_report(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_matrix(matrix)
    payload = json.loads(matrix.read_text(encoding="utf-8"))
    payload["candidates"][1]["api_key"] = "frontier-key"
    matrix.write_text(json.dumps(payload), encoding="utf-8")
    _write_replay_dataset(replay_dataset)

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        _write_candidate_report(report)
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(tmp_path / "armory"),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--json-report",
                str(report_path),
            ]
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert replay.call_count == 2
    assert replay.call_args.kwargs["evidence_coverage"] == 1.0
    assert report["status"] == 0
    assert report["groups"] == ["frontier", "local"]
    assert Path(report["output_dir"]) == tmp_path / "out"
    assert report["replay_cases"] == 4
    assert report["replay_domains"] == [
        "computer-science",
        "cross-domain",
        "mathematics",
        "study-methods",
    ]
    assert report["replay_tasks"] == [
        "abstention",
        "grounded-explanation",
        "material-overview",
        "single-source-fact",
    ]
    assert report["results"][0]["candidate_id"] == "local-small"
    assert report["results"][0]["auth_source"] == "base_url"
    assert report["results"][0]["provider_slug"] == ""
    assert report["results"][0]["cases"] == 4
    assert report["results"][0]["responsibilities"] == [
        "chunk labeling",
        "question formatting",
    ]
    assert report["results"][1]["responsibilities"] == [
        "essay feedback",
        "misconception correction",
    ]
    assert report["results"][1]["auth_source"] == "api_key"
    assert report["results"][0]["domains"] == [
        "computer-science",
        "cross-domain",
        "mathematics",
        "study-methods",
    ]
    for result in report["results"]:
        assert Path(result["report_path"]).parent == Path(report["output_dir"])
        assert Path(result["output"]).parent == Path(report["output_dir"])
    assert report["results"][0]["pass_rate"] == 1.0
    assert report["results"][0]["evidence_coverage_rate"] == 1.0
    assert "frontier-key" not in json.dumps(report)


def test_model_eval_matrix_records_codex_subscription_auth_source(tmp_path: Path) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
            base_url="http://localhost:11434/v1",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-codex",
            group="frontier",
            model="gpt-5.4-mini",
            provider_slug="openai-codex",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        _write_candidate_report(kwargs["report_path"])
        return 0

    with (
        patch("scripts.run_model_eval_matrix.load_credentials", return_value=object()),
        patch(
            "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
            side_effect=fake_eval,
        ),
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
            report_path=report_path,
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    frontier = report["results"][1]
    assert frontier["provider_slug"] == "openai-codex"
    assert frontier["auth_source"] == "codex_oauth"


def test_model_eval_matrix_requires_codex_oauth_for_codex_candidate(tmp_path: Path) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
            base_url="http://localhost:11434/v1",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-codex",
            group="frontier",
            model="gpt-5.4-mini",
            provider_slug="openai-codex",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        _write_candidate_report(kwargs["report_path"])
        return 0

    with (
        patch("scripts.run_model_eval_matrix.load_credentials", return_value=None),
        patch(
            "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
            side_effect=fake_eval,
        ),
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
            report_path=report_path,
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    frontier = report["results"][1]
    assert frontier["status"] == 2
    assert frontier["auth_source"] == "missing"
    assert "Codex subscription OAuth" in frontier["error"]


def test_model_eval_matrix_requires_local_and_frontier_groups(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps(
            {
                "candidates": [
                    {"id": "local", "group": "local", "model": "local-model"},
                ]
            }
        ),
        encoding="utf-8",
    )

    status = run_model_eval_matrix.main(
        [
            str(tmp_path / "armory"),
            str(tmp_path / "replay.jsonl"),
            str(matrix),
            str(tmp_path / "out"),
        ]
    )

    assert status == 2


def test_model_eval_matrix_validate_only_does_not_run_candidates(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    report_path = tmp_path / "matrix-report.json"
    _write_matrix(matrix)

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(tmp_path / "armory"),
                str(tmp_path / "replay.jsonl"),
                str(matrix),
                str(tmp_path / "out"),
                "--validate-only",
                "--json-report",
                str(report_path),
            ]
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    replay.assert_not_called()
    assert report["candidates"] == 2
    assert report["groups"] == ["frontier", "local"]
    assert report["results"] == []


def test_model_eval_matrix_validate_only_reports_missing_required_group(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps({"candidates": [{"id": "local", "group": "local", "model": "local"}]}),
        encoding="utf-8",
    )

    status = run_model_eval_matrix.main(
        [
            str(tmp_path / "armory"),
            str(tmp_path / "replay.jsonl"),
            str(matrix),
            str(tmp_path / "out"),
            "--validate-only",
        ]
    )

    assert status == 1


def test_model_eval_matrix_validate_inputs_checks_replay_coverage_and_armory(
    tmp_path: Path,
) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_matrix(matrix)
    _write_replay_dataset(replay_dataset)
    lines = []
    for line in replay_dataset.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        case["domain"] = "computer-science"
        lines.append(json.dumps(case))
    replay_dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(tmp_path / "missing-armory"),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--validate-inputs",
                "--json-report",
                str(report_path),
            ]
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    replay.assert_not_called()
    assert any("replay dataset" in failure for failure in report["failures"])
    assert any("armory path is not a directory" in failure for failure in report["failures"])
    assert any("frontier-hosted" in failure for failure in report["failures"])


def test_model_eval_matrix_validate_inputs_requires_shaped_material_overview(
    tmp_path: Path,
) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    armory = tmp_path / "armory"
    armory.mkdir()
    _write_matrix(matrix)
    _write_replay_dataset(replay_dataset)
    lines = [
        line
        for line in replay_dataset.read_text(encoding="utf-8").splitlines()
        if "material-overview" not in line
    ]
    replay_dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(armory),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--validate-inputs",
                "--json-report",
                str(report_path),
            ]
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    replay.assert_not_called()
    assert any("material-overview" in failure for failure in report["failures"])


def test_model_eval_matrix_validate_inputs_passes_broad_replay_without_model_calls(
    tmp_path: Path,
) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    armory = tmp_path / "armory"
    armory.mkdir()
    _write_matrix(matrix)
    payload = json.loads(matrix.read_text(encoding="utf-8"))
    payload["candidates"][1]["api_key"] = "frontier-key"
    matrix.write_text(json.dumps(payload), encoding="utf-8")
    _write_replay_dataset(replay_dataset)

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(armory),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--validate-inputs",
                "--json-report",
                str(report_path),
            ]
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    replay.assert_not_called()
    assert report["armory"] == str(armory.resolve())
    assert report["replay_dataset"] == str(replay_dataset.resolve())
    assert report["replay_cases"] == 4
    assert report["replay_domains"] == [
        "computer-science",
        "cross-domain",
        "mathematics",
        "study-methods",
    ]
    assert report["replay_tasks"] == [
        "abstention",
        "grounded-explanation",
        "material-overview",
        "single-source-fact",
    ]
    assert report["results"] == []


def test_model_eval_matrix_validate_inputs_reports_missing_candidate_credentials(
    tmp_path: Path,
) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    armory = tmp_path / "armory"
    armory.mkdir()
    _write_matrix(matrix)
    _write_replay_dataset(replay_dataset)

    status = run_model_eval_matrix.main(
        [
            str(armory),
            str(replay_dataset),
            str(matrix),
            str(tmp_path / "out"),
            "--validate-inputs",
            "--json-report",
            str(report_path),
        ]
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    assert any("frontier-hosted" in failure for failure in report["failures"])


def test_model_eval_matrix_rejects_duplicate_replay_case_ids(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_matrix(matrix)
    _write_replay_dataset(replay_dataset)
    lines = replay_dataset.read_text(encoding="utf-8").splitlines()
    duplicate = json.loads(lines[-1])
    duplicate["id"] = "case-1"
    lines[-1] = json.dumps(duplicate)
    replay_dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(tmp_path / "armory"),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--json-report",
                str(report_path),
            ]
        )

    assert status == 2
    assert not report_path.exists()
    replay.assert_not_called()


def test_model_eval_matrix_rejects_narrow_replay_dataset_before_model_calls(
    tmp_path: Path,
) -> None:
    matrix = tmp_path / "matrix.json"
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_matrix(matrix)
    _write_replay_dataset(replay_dataset)
    lines = []
    for line in replay_dataset.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        case["domain"] = "computer-science"
        lines.append(json.dumps(case))
    replay_dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
    ) as replay:
        status = run_model_eval_matrix.main(
            [
                str(tmp_path / "armory"),
                str(replay_dataset),
                str(matrix),
                str(tmp_path / "out"),
                "--json-report",
                str(report_path),
            ]
        )

    assert status == 2
    assert not report_path.exists()
    replay.assert_not_called()


def test_model_eval_matrix_fails_when_candidate_fails(tmp_path: Path) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-hosted",
            group="frontier",
            model="frontier-model",
            api_key="frontier-key",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        pass_rate = 0.5 if "local-small" in str(report) else 1.0
        _write_candidate_report(report, pass_rate=pass_rate)
        return 1 if pass_rate < 1.0 else 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
        )

    assert status == 1


def test_model_eval_matrix_records_candidate_timeout(tmp_path: Path) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    report_path = tmp_path / "matrix-report.json"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
            api_key="local-key",
            timeout_seconds=1,
        )
    ]

    def slow_eval(*_args, **_kwargs) -> int:
        time.sleep(2)
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=slow_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
            required_groups=("local",),
            report_path=report_path,
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    assert report["results"][0]["status"] == 2
    assert "timed out" in report["results"][0]["error"]


def test_model_eval_matrix_fails_when_candidate_report_is_missing_metrics(
    tmp_path: Path,
) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-hosted",
            group="frontier",
            model="frontier-model",
            api_key="frontier-key",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        _write_candidate_report(report, include_required_text=False)
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
        )

    assert status == 1


def test_model_eval_matrix_fails_when_candidate_report_is_missing_coverage(
    tmp_path: Path,
) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-hosted",
            group="frontier",
            model="frontier-model",
            api_key="frontier-key",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        _write_candidate_report(report, include_coverage=False)
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
        )

    assert status == 1


def test_model_eval_matrix_fails_when_candidate_report_has_narrow_coverage(
    tmp_path: Path,
) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-hosted",
            group="frontier",
            model="frontier-model",
            api_key="frontier-key",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        _write_candidate_report(report, domains=["mathematics"])
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
        )

    assert status == 1


def test_model_eval_matrix_fails_when_candidate_report_coverage_differs_from_replay(
    tmp_path: Path,
) -> None:
    replay_dataset = tmp_path / "replay.jsonl"
    _write_replay_dataset(replay_dataset)
    candidates = [
        run_model_eval_matrix.ModelCandidate(
            candidate_id="local-small",
            group="local",
            model="local-model",
        ),
        run_model_eval_matrix.ModelCandidate(
            candidate_id="frontier-hosted",
            group="frontier",
            model="frontier-model",
            api_key="frontier-key",
        ),
    ]

    def fake_eval(*_args, **kwargs) -> int:
        report = kwargs["report_path"]
        _write_candidate_report(
            report,
            domains=["biology", "cross-domain", "mathematics", "study-methods"],
        )
        return 0

    with patch(
        "scripts.run_model_eval_matrix.run_replay_answer_eval.run_replay_answer_eval",
        side_effect=fake_eval,
    ):
        status = run_model_eval_matrix.run_model_eval_matrix(
            tmp_path / "armory",
            replay_dataset,
            tmp_path / "out",
            candidates,
        )

    assert status == 1
