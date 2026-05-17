from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "comprehensive_benchmark_run.sh"


def _write_fake_uv(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def option_value(args: list[str], name: str) -> str:
    try:
        return args[args.index(name) + 1]
    except (ValueError, IndexError):
        return ""


def write_json(path: str, payload: dict[str, object]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")


args = sys.argv[1:]
log_path = Path(os.environ["FAKE_UV_LOG"])
log_path.parent.mkdir(parents=True, exist_ok=True)
with log_path.open("a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\\n")

module = args[args.index("-m") + 1] if "-m" in args else ""
if os.environ.get("FAKE_UV_FAIL_MODULE") == module:
    secret = os.environ.get("HEPHAISTOS_TEST_SECRET_COMPREHENSIVE", "")
    print(f"simulated failure token={secret}", file=sys.stderr)
    raise SystemExit(7)

if module in {
    "scripts.external_benchmarks.beir_adapter",
    "scripts.external_benchmarks.standard_rag_adapter",
}:
    output = Path(option_value(args, "--output"))
    (output / "armory" / "materials").mkdir(parents=True, exist_ok=True)
    (output / "armory" / "materials" / "alpha.md").write_text("alpha\\n", encoding="utf-8")
    (output / "rag.jsonl").write_text(
        '{"id":"alpha","query":"alpha","expected":["materials/alpha.md"]}\\n',
        encoding="utf-8",
    )
    write_json(
        option_value(args, "--json-report"),
        {"schema_version": "external-adapter-report-v1", "status": "success"},
    )
    print(f"adapter ok {module}")
    raise SystemExit(0)

if module == "scripts.run_external_benchmarks":
    module_index = args.index("-m")
    benchmark_type = args[module_index + 2]
    dataset = args[module_index + 3]
    prompt_path = option_value(args, "--prompt")
    write_json(
        option_value(args, "--json-report"),
        {
            "schema_version": "external-runner-report-v1",
            "report_id": f"{benchmark_type}:{dataset}",
            "status": "success",
            "metadata": {
                "runner": "scripts.run_external_benchmarks",
                "benchmark_type": benchmark_type,
                "dataset": dataset,
                "suite_path": option_value(args, "--suite"),
                "fixed_parameters": {
                    "top_k": 5,
                    "network_access": "disabled-after-materialization",
                },
                "metric_formulas": {
                    "hit_rate": "fraction of queries with an expected reference in top-k",
                    "mrr": "mean reciprocal rank",
                    "expected_recall": "expected references retrieved",
                    "latency": "runtime only",
                },
                "runtime_only_fields": ["aggregate_metrics.mean_latency_ms"],
                "prompt_path": prompt_path,
                "prompt_hash": "fake-prompt-hash",
            },
            "benchmarks": [],
            "aggregate_metrics": {
                "hit_rate": 1.0,
                "mrr": 1.0,
                "expected_recall": 1.0,
                "mean_latency_ms": 1.0,
            },
            "thresholds": {"hit_rate": 0.0, "mrr": 0.0, "expected_recall": 0.0},
            "threshold_failures": [],
            "warnings": [],
            "errors": [],
            "reproducibility": {
                "enabled": False,
                "status": "skipped",
                "runtime_only_fields": [],
                "deterministic_fields_compared": [],
                "mismatches": [],
            },
        },
    )
    print(f"runner ok {benchmark_type}:{dataset}")
    raise SystemExit(0)

if module == "scripts.generate_benchmark_summary":
    output = Path(option_value(args, "--output"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("# fake summary\\n", encoding="utf-8")
    print(f"summary ok {output}")
    raise SystemExit(0)

print(f"unexpected module {module}", file=sys.stderr)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _base_env(tmp_path: Path, fake_uv: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HEPH_BENCHMARK_UV"] = str(fake_uv)
    env["FAKE_UV_LOG"] = str(tmp_path / "fake-uv.log")
    env["HEPH_BENCHMARK_SKIP_GIT_CHECK"] = "1"
    return env


def _run_script(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_comprehensive_script_help_documents_required_interface() -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    for option in (
        "--output-dir",
        "--prompt",
        "--fixture-mode",
        "--offline",
        "--validate-reproducibility",
        "--visualize",
        "--require-beir-extra",
    ):
        assert option in result.stdout


def test_comprehensive_script_runs_ordered_fixture_phases_with_quoted_paths(
    tmp_path: Path,
) -> None:
    fake_uv = tmp_path / "fake uv"
    _write_fake_uv(fake_uv)
    env = _base_env(tmp_path, fake_uv)

    with tempfile.TemporaryDirectory(prefix="heph-comprehensive-", dir="/tmp") as temp_root:
        output_dir = Path(temp_root) / "artifact dir"
        result = _run_script(
            [
                "--output-dir",
                str(output_dir),
                "--fixture-mode",
                "--skip-dependency-checks",
                "--native-suite",
                str(ROOT / "benchmarks" / "academic"),
            ],
            env=env,
        )

        output = result.stdout + result.stderr
        assert result.returncode == 0, output
        phase_names = (
            "phase=materialization",
            "phase=external-adapters",
            "phase=native",
            "phase=public-academic",
            "phase=summary",
        )
        phase_positions = [output.index(phase_name) for phase_name in phase_names]
        assert phase_positions == sorted(phase_positions)
        assert (output_dir / "summary" / "benchmark-summary.md").is_file()
        assert (output_dir / "reports" / "beir-runner.json").is_file()
        assert (output_dir / "reports" / "standard-rag-runner.json").is_file()
        assert (output_dir / "reports" / "heph-native-runner.json").is_file()
        assert (output_dir / "reports" / "public-academic-runner.json").is_file()
        assert "status=success" in (output_dir / "run-status.txt").read_text(encoding="utf-8")


def test_comprehensive_script_rejects_symlinked_output_before_writes(
    tmp_path: Path,
) -> None:
    fake_uv = tmp_path / "fake-uv"
    _write_fake_uv(fake_uv)
    env = _base_env(tmp_path, fake_uv)

    with tempfile.TemporaryDirectory(prefix="heph-comprehensive-", dir="/tmp") as temp_root:
        root = Path(temp_root)
        target = root / "target"
        target.mkdir()
        symlink = root / "output-link"
        symlink.symlink_to(target, target_is_directory=True)
        result = _run_script(
            ["--output-dir", str(symlink), "--fixture-mode", "--skip-dependency-checks"],
            env=env,
        )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "symlinked output directory" in output
    assert not (tmp_path / "fake-uv.log").exists()


def test_comprehensive_script_redacts_child_output_and_marks_failed_phase(
    tmp_path: Path,
) -> None:
    fake_uv = tmp_path / "fake-uv"
    _write_fake_uv(fake_uv)
    env = _base_env(tmp_path, fake_uv)
    env["FAKE_UV_FAIL_MODULE"] = "scripts.external_benchmarks.beir_adapter"
    env["HEPHAISTOS_TEST_SECRET_COMPREHENSIVE"] = "super-secret-token"

    with tempfile.TemporaryDirectory(prefix="heph-comprehensive-", dir="/tmp") as temp_root:
        output_dir = Path(temp_root) / "artifacts"
        result = _run_script(
            ["--output-dir", str(output_dir), "--fixture-mode", "--skip-dependency-checks"],
            env=env,
        )

        output = result.stdout + result.stderr
        status = (output_dir / "run-status.txt").read_text(encoding="utf-8")
        assert result.returncode != 0
        assert "super-secret-token" not in output
        assert "[REDACTED]" in output
        assert "status=failed" in status
        assert "phase=external-adapters" in status
        assert not (output_dir / "summary" / "benchmark-summary.md").exists()


def test_comprehensive_script_missing_beir_extra_fails_with_install_guidance(
    tmp_path: Path,
) -> None:
    fake_python = tmp_path / "missing-python"
    fake_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_python.chmod(0o755)
    env = os.environ.copy()
    env["HEPH_BENCHMARK_PYTHON"] = str(fake_python)
    env["HEPH_BENCHMARK_SKIP_GIT_CHECK"] = "1"

    with tempfile.TemporaryDirectory(prefix="heph-comprehensive-", dir="/tmp") as temp_root:
        result = _run_script(
            [
                "--output-dir",
                str(Path(temp_root) / "artifacts"),
                "--require-beir-extra",
                "--dependency-check-only",
            ],
            env=env,
        )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "uv sync --extra beir" in output
    assert "optional dependency" in output
