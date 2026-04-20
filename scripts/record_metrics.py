#!/usr/bin/env python3
"""Record build and test performance metrics from CI runs.

Queries the GitHub API for recent CI run durations and parses
pytest junit XML for test timing data. Outputs a timing
comparison to GITHUB_STEP_SUMMARY.

Usage:
    python scripts/record_metrics.py
    python scripts/record_metrics.py --junit-xml .artifacts/pytest-junit.xml
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
JUNIT_DEFAULT = REPO_ROOT / ".artifacts" / "pytest-junit.xml"
SUMMARY_FILE = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null")
REGRESSION_THRESHOLD = 0.20  # 20% slower triggers alert


class RunInfo(TypedDict):
    run_id: str
    duration_ms: float
    created_at: str


class TestTiming(TypedDict):
    name: str
    time_s: float


class JunitResult(TypedDict):
    total_time_s: float
    test_count: int
    slowest: list[TestTiming]


def _gh(*args: str) -> str:
    """Run a gh CLI command and return stdout."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _get_recent_run_durations(limit: int = 10) -> list[RunInfo]:
    """Fetch recent CI run durations from GitHub API."""
    output = _gh(
        "run",
        "list",
        "--workflow",
        "ci.yml",
        "--limit",
        str(limit),
        "--json",
        "conclusion,createdAt,databaseId,headBranch",
    )
    if not output:
        return []

    try:
        runs = json.loads(output)
    except json.JSONDecodeError:
        return []

    durations: list[RunInfo] = []
    for run in runs:
        if run.get("conclusion") != "success" or run.get("headBranch") != "main":
            continue
        run_id = run.get("databaseId")
        if not run_id:
            continue
        try:
            timing_output = _gh("run", "view", str(run_id), "--json", "jobs")
            if not timing_output:
                continue
            jobs = json.loads(timing_output)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            continue

        total_ms = 0.0
        for job in jobs:
            started = job.get("startedAt", "")
            completed = job.get("completedAt", "")
            if started and completed:
                start_dt = _parse_iso(started)
                end_dt = _parse_iso(completed)
                if start_dt and end_dt:
                    total_ms += (end_dt - start_dt).total_seconds() * 1000

        if total_ms > 0:
            durations.append(
                {
                    "run_id": str(run_id),
                    "duration_ms": total_ms,
                    "created_at": run.get("createdAt", ""),
                }
            )

    return durations


def _parse_iso(s: str) -> datetime | None:
    """Parse ISO 8601 datetime string."""
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _parse_junit_timing(path: Path) -> JunitResult | None:
    """Parse junit XML for per-test timing data."""
    if not path.exists():
        return None

    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    tests: list[TestTiming] = []
    total_time = 0.0

    for testsuite in root.iter("testsuite"):
        for testcase in testsuite.iter("testcase"):
            name = testcase.get("name", "unknown")
            classname = testcase.get("classname", "")
            time_s = float(testcase.get("time", 0))
            total_time += time_s
            tests.append(
                {
                    "name": f"{classname}::{name}" if classname else name,
                    "time_s": time_s,
                }
            )

    tests.sort(key=lambda t: t["time_s"], reverse=True)

    return {
        "total_time_s": total_time,
        "test_count": len(tests),
        "slowest": tests[:10],
    }


def _write_summary(content: str) -> None:
    """Append content to GITHUB_STEP_SUMMARY."""
    with Path(SUMMARY_FILE).open("a") as f:
        f.write(content)


def _format_duration(ms: float) -> str:
    """Format milliseconds into human-readable duration."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"


def main() -> int:
    junit_path = (
        Path(sys.argv[sys.argv.index("--junit-xml") + 1])
        if "--junit-xml" in sys.argv
        else JUNIT_DEFAULT
    )

    # --- Build Performance ---
    _write_summary("## Build Performance Tracking\n\n")

    durations = _get_recent_run_durations(limit=10)
    if durations:
        avg_ms = sum(d["duration_ms"] for d in durations) / len(durations)

        _write_summary("| Run | Duration | vs Average |\n")
        _write_summary("|-----|----------|------------|\n")
        for d in durations[:5]:
            diff_pct = ((d["duration_ms"] - avg_ms) / avg_ms * 100) if avg_ms > 0 else 0
            flag = ""
            if diff_pct > REGRESSION_THRESHOLD * 100:
                flag = " :warning: slow"
            elif diff_pct < -(REGRESSION_THRESHOLD * 100):
                flag = " :fast_forward: fast"
            _write_summary(
                f"| #{d['run_id']} | {_format_duration(d['duration_ms'])} "
                f"| {diff_pct:+.1f}%{flag} |\n"
            )

        _write_summary(f"\n**Average duration**: {_format_duration(avg_ms)}\n")
    else:
        _write_summary("*No recent successful CI runs found for comparison.*\n")

    # --- Test Performance ---
    _write_summary("\n## Test Performance Tracking\n\n")

    junit_data = _parse_junit_timing(junit_path)
    if junit_data:
        _write_summary(
            f"**Total test time**: {junit_data['total_time_s']:.2f}s "
            f"({junit_data['test_count']} tests)\n\n"
        )
        _write_summary("### Top 10 Slowest Tests\n\n")
        _write_summary("| Test | Duration |\n")
        _write_summary("|------|----------|\n")
        for t in junit_data["slowest"]:
            _write_summary(f"| `{t['name']}` | {t['time_s']:.3f}s |\n")
    else:
        _write_summary("*No junit XML data available for test timing analysis.*\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
