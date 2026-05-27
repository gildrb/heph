"""Benchmark material role inference against labelled academic files.

Dataset format:

JSONL:
    {
      "id": "lecture-role",
      "source": "materials/lecture.md",
      "expected_role": "lecture"
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.materials import MaterialRole, infer_material_role_from_text

_MIN_DEFAULT_PASS_RATE = 1.0


class RawRoleCase(TypedDict):
    expected_role: str
    source: str
    domain: NotRequired[str]
    id: NotRequired[str]


@dataclass(frozen=True, slots=True)
class MaterialRoleCase:
    case_id: str
    source: str
    expected_role: MaterialRole
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class MaterialRoleCaseResult:
    case_id: str
    source: str
    expected_role: MaterialRole
    actual_role: MaterialRole
    confidence: float
    reason: str
    passed: bool


@dataclass(frozen=True, slots=True)
class MaterialRoleBenchmarkReport:
    armory_path: str
    cases: int
    pass_rate: float
    domains: tuple[str, ...]
    expected_roles: tuple[MaterialRole, ...]
    failures: tuple[str, ...]
    results: tuple[MaterialRoleCaseResult, ...]


def _as_material_role(value: str, case_number: int) -> MaterialRole:
    roles = {
        "assignment",
        "codebase",
        "lecture",
        "past_exam",
        "reference",
        "slides",
        "textbook",
        "vocabulary",
    }
    if value not in roles:
        raise ValueError(f"case {case_number} expected_role is not a known material role")
    return cast("MaterialRole", value)


def _as_raw_cases(payload: object) -> list[RawRoleCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("material role dataset must be a JSON list or object with a 'cases' list")
    cases: list[RawRoleCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        source = raw.get("source")
        expected_role = raw.get("expected_role")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"case {idx} must include non-empty source")
        if not isinstance(expected_role, str) or not expected_role.strip():
            raise ValueError(f"case {idx} must include non-empty expected_role")
        case: RawRoleCase = {
            "source": source,
            "expected_role": expected_role,
        }
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            case["domain"] = raw_domain.strip()
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            case["id"] = raw_id
        cases.append(case)
    return cases


def load_cases(path: Path) -> list[MaterialRoleCase]:
    """Load material role benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read material role benchmark dataset: {path}") from exc
    try:
        if path.suffix == ".jsonl":
            payload: object = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid material role benchmark JSON: {path}") from exc

    cases: list[MaterialRoleCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        source = raw["source"].strip()
        cases.append(
            MaterialRoleCase(
                case_id=raw.get("id", f"case-{idx}"),
                source=source,
                expected_role=_as_material_role(raw["expected_role"].strip(), idx),
                domain=raw.get("domain"),
            )
        )
    return cases


def run_benchmark(
    armory_path: Path,
    cases: Sequence[MaterialRoleCase],
) -> MaterialRoleBenchmarkReport:
    """Run material role benchmark cases and return aggregate metrics."""
    if not cases:
        raise ValueError("material role benchmark dataset does not contain any cases")

    results: list[MaterialRoleCaseResult] = []
    for case in cases:
        material_path = armory_path / case.source
        try:
            text = material_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"could not read benchmark material: {material_path}") from exc
        actual_role, confidence, reason = infer_material_role_from_text(case.source, text)
        results.append(
            MaterialRoleCaseResult(
                case_id=case.case_id,
                source=case.source,
                expected_role=case.expected_role,
                actual_role=actual_role,
                confidence=confidence,
                reason=reason,
                passed=actual_role == case.expected_role,
            )
        )

    total = len(results)
    return MaterialRoleBenchmarkReport(
        armory_path=str(armory_path),
        cases=total,
        pass_rate=sum(1 for result in results if result.passed) / total,
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        expected_roles=tuple(sorted({case.expected_role for case in cases})),
        failures=tuple(result.case_id for result in results if not result.passed),
        results=tuple(results),
    )


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_text_report(report: MaterialRoleBenchmarkReport) -> None:
    """Print a compact human-readable material role benchmark report."""
    print(f"Material role benchmark: {report.cases} cases against {report.armory_path}")
    print(f"pass_rate={_format_percent(report.pass_rate)}")
    if report.domains:
        print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    print(f"expected_roles={len(report.expected_roles)} ({', '.join(report.expected_roles)})")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL material role cases")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    parser.add_argument("--min-pass-rate", type=float, default=_MIN_DEFAULT_PASS_RATE)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    min_pass_rate = cast("float", args.min_pass_rate)
    if not 0 <= min_pass_rate <= 1:
        parser.error("--min-pass-rate must be between 0 and 1")
    try:
        report = run_benchmark(armory, load_cases(dataset))
    except (OSError, TypeError, ValueError) as exc:
        print(f"material role benchmark error: {exc}", file=sys.stderr)
        return 2
    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0 if report.pass_rate >= min_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
