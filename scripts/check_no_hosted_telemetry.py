"""Reject hosted telemetry and persistent install fingerprints in source."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_FORBIDDEN = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        "posthog",
        "sentry",
        "telemetry",
        "crash_reports",
        "install_id",
        "harness_analytics",
        "harness_crash",
    )
)
_SCAN_ROOTS = (
    *(
        ROOT / "packages" / package / "src"
        for package in ("ai", "extensions", "heph", "harness", "interfaces")
    ),
    ROOT / "scripts" / "build_release_artifacts.py",
    ROOT / ".github" / "workflows",
)


def _paths() -> list[Path]:
    paths: list[Path] = []
    for root in _SCAN_ROOTS:
        if root.is_file():
            paths.append(root)
        elif root.is_dir():
            paths.extend(
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix in {".py", ".yml", ".yaml"}
            )
    return [path for path in paths if path != Path(__file__)]


def main() -> int:
    violations: list[str] = []
    for path in _paths():
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            if path == ROOT / ".github" / "workflows" / "ci.yml" and (
                "scripts.check_no_hosted_telemetry" in line
            ):
                continue
            if any(pattern.search(line) for pattern in _FORBIDDEN):
                violations.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    if violations:
        print("Hosted telemetry references found:")
        print("\n".join(violations))
        return 1
    print("No hosted telemetry or install fingerprint references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
