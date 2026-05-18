from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts import validate_mission_boundary_gates as gates


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _base_evidence(repo: Path) -> dict[str, object]:
    artifacts = repo / ".artifacts" / "safety-run"
    artifacts.mkdir(parents=True)
    report_path = artifacts / "external-report.json"
    _write_json(
        report_path,
        {
            "metadata": {
                "network_state": "disabled-after-materialization",
                "fixed_parameters": {"network_access": "disabled-after-materialization"},
            }
        },
    )
    temp_armory = repo.parent / "copied-armory"
    temp_armory.mkdir()
    return {
        "artifact_roots": [str(artifacts)],
        "temporary_armory_roots": [str(temp_armory)],
        "generated_artifacts": [
            str(artifacts / "summary.json"),
            str(temp_armory / ".hephaistos" / "rag_index.json"),
        ],
        "changed_paths": ["scripts/validate_mission_boundary_gates.py"],
        "egress": {"mode": "disabled-after-materialization", "requests": []},
        "reports": [str(report_path)],
        "validators": [
            {"name": "ruff", "command": "uv run ruff check .", "exit_code": 0},
            {
                "name": "format-check",
                "command": "uv run ruff format --check .",
                "exit_code": 0,
            },
            {
                "name": "repo-policies",
                "command": "uv run python -m scripts.check_repo_policies",
                "exit_code": 0,
            },
            {"name": "typecheck", "command": "uv run ty check", "exit_code": 0},
            {"name": "import-boundaries", "command": "uv run lint-imports", "exit_code": 0},
            {
                "name": "focused-tests",
                "command": (
                    "uv run pytest -n 2 --cov-fail-under=0 "
                    "tests/test_validate_mission_boundary_gates.py"
                ),
                "exit_code": 0,
                "concurrency": 2,
                "weight": "lightweight",
            },
            {
                "name": "full-tests",
                "command": "uv run pytest -n 2",
                "exit_code": 0,
                "concurrency": 2,
                "weight": "lightweight",
            },
        ],
        "commands": [
            {"command": "git status --porcelain", "exit_code": 0},
            {
                "command": (
                    "uv run pytest -n 2 --cov-fail-under=0 "
                    "tests/test_validate_mission_boundary_gates.py"
                ),
                "exit_code": 0,
                "concurrency": 2,
                "weight": "lightweight",
            },
        ],
        "resources": {
            "before_listeners": ["tcp4 127.0.0.1:5000 LISTEN"],
            "after_listeners": ["tcp4 127.0.0.1:5000 LISTEN"],
            "services_started": [],
            "ports_claimed": [],
        },
    }


def _failure_codes(report: gates.BoundaryGateReport) -> set[str]:
    return {failure.code for failure in report.failures}


def _failure_by_code(
    report: gates.BoundaryGateReport,
    code: str,
) -> gates.BoundaryFailure:
    matches = [failure for failure in report.failures if failure.code == code]
    assert matches
    return matches[0]


def test_boundary_gate_accepts_valid_mission_closure_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    report_path = repo / ".artifacts" / "safety-run" / "gate-report.json"

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)
    status = gates.main(
        [
            "--evidence",
            "-",
            "--repo-root",
            str(repo),
            "--json-report",
            str(report_path),
        ],
        stdin_text=json.dumps(evidence),
    )

    payload = _as_dict(json.loads(report_path.read_text(encoding="utf-8")))
    assert report.status == "passed"
    assert report.failures == ()
    assert status == 0
    assert payload["status"] == "passed"
    assert payload["failures"] == []
    assert "artifact-containment" in _as_list(payload["checks"])


def test_boundary_gate_rejects_missing_declared_report_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    missing_report = repo / ".artifacts" / "safety-run" / "missing-report.json"
    evidence["reports"] = [str(missing_report)]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    failure = _failure_by_code(report, "report_load_failed")
    assert report.status == "failed"
    assert str(missing_report) in failure.evidence


def test_boundary_gate_rejects_unreadable_declared_report_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    unreadable_report = repo / ".artifacts" / "safety-run"
    evidence["reports"] = [str(unreadable_report)]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    failure = _failure_by_code(report, "report_load_failed")
    assert report.status == "failed"
    assert str(unreadable_report) in failure.evidence


def test_boundary_gate_rejects_malformed_declared_report_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    report_path = repo / ".artifacts" / "safety-run" / "malformed-report.json"
    report_path.write_text("{not-json", encoding="utf-8")
    evidence["reports"] = [str(report_path)]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    failure = _failure_by_code(report, "report_json_invalid")
    assert report.status == "failed"
    assert str(report_path) in failure.evidence


def test_boundary_gate_rejects_non_object_declared_report_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    report_path = repo / ".artifacts" / "safety-run" / "list-report.json"
    report_path.write_text("[]\n", encoding="utf-8")
    evidence["reports"] = [str(report_path)]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    failure = _failure_by_code(report, "report_payload_invalid")
    assert report.status == "failed"
    assert str(report_path) in failure.evidence


def test_boundary_gate_rejects_repo_artifacts_and_docs_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    evidence["generated_artifacts"] = [str(repo / "docs" / "benchmark-summary.md")]
    evidence["changed_paths"] = ["README.md", "docs/index.md", "AGENTS.md"]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert report.status == "failed"
    assert {
        "artifact_outside_allowed_roots",
        "docs_changed",
    } <= _failure_codes(report)


def test_boundary_gate_rejects_symlinked_artifact_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    outside = tmp_path / "outside-artifacts"
    outside.mkdir()
    artifact_link = repo / ".artifacts" / "linked-artifacts"
    try:
        artifact_link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")
    evidence["artifact_roots"] = [str(artifact_link)]
    evidence["generated_artifacts"] = [str(artifact_link / "summary.json")]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert {
        "artifact_root_symlink",
        "artifact_path_symlink",
    } <= _failure_codes(report)


def test_boundary_gate_rejects_unapproved_network_egress(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    evidence["egress"] = {
        "mode": "public-only",
        "requests": [
            {
                "method": "POST",
                "url": "http://127.0.0.1:8787/private",
                "headers": {"Authorization": "Bearer secret", "Cookie": "sid=secret"},
            }
        ],
    }

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert {
        "egress_method_not_get",
        "egress_url_not_https",
        "egress_private_host",
        "egress_forbidden_header",
    } <= _failure_codes(report)


def test_boundary_gate_rejects_competing_harnesses_and_port_commands(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    commands = _as_list(evidence["commands"])
    commands.append(
        {
            "command": "codex run terminal-bench --port 8787 &",
            "exit_code": 0,
            "concurrency": 1,
            "weight": "heavy",
        }
    )

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert {
        "prohibited_harness_command",
        "persistent_command",
        "port_binding_command",
    } <= _failure_codes(report)


def test_boundary_gate_rejects_missing_failed_and_over_concurrent_validators(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    validators = [
        _as_dict(validator)
        for validator in _as_list(evidence["validators"])
        if _as_dict(validator)["name"] != "typecheck"
    ]
    validators[0]["exit_code"] = 1
    validators[-1]["concurrency"] = 3
    evidence["validators"] = validators

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert {
        "validator_failed",
        "validator_missing",
        "concurrency_cap_exceeded",
    } <= _failure_codes(report)


def test_boundary_gate_rejects_listener_drift(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = _base_evidence(repo)
    resources = _as_dict(evidence["resources"])
    resources["after_listeners"] = [
        "tcp4 127.0.0.1:5000 LISTEN",
        "tcp4 127.0.0.1:9000 LISTEN",
    ]
    resources["ports_claimed"] = [9000]
    resources["services_started"] = ["python -m http.server 9000"]

    report = gates.validate_boundary_evidence(evidence, repo_root=repo)

    assert {
        "listener_drift",
        "port_claimed",
        "persistent_service_started",
    } <= _failure_codes(report)
