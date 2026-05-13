"""Benchmark deterministic priority analysis against labelled academic cases.

Dataset format:

JSONL:
    {
      "id": "exam-priority",
      "expected_topics": ["geometrische reihe"],
      "forbidden_topics": ["course logistics"],
      "expected_past_exam_sources": ["materials/past-exam.md"]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.rag import load_or_build
from hephaistos.study.priority import analyze_priority, priority_tier

_DEFAULT_LIMIT = 8


class RawPriorityCase(TypedDict):
    expected_topics: list[str]
    domain: NotRequired[str]
    forbidden_topics: NotRequired[list[str]]
    expected_past_exam_sources: NotRequired[list[str]]
    expected_ordered_topics: NotRequired[list[str]]
    expected_mark_totals: NotRequired[dict[str, int]]
    expected_tiers: NotRequired[dict[str, str]]
    id: NotRequired[str]
    limit: NotRequired[int]


@dataclass(frozen=True, slots=True)
class PriorityBenchmarkCase:
    case_id: str
    expected_topics: tuple[str, ...]
    domain: str | None = None
    forbidden_topics: tuple[str, ...] = ()
    expected_past_exam_sources: tuple[str, ...] = ()
    expected_ordered_topics: tuple[str, ...] = ()
    expected_mark_totals: dict[str, int] | None = None
    expected_tiers: dict[str, str] | None = None
    limit: int | None = None


@dataclass(frozen=True, slots=True)
class PriorityCaseResult:
    case_id: str
    expected_topics: tuple[str, ...]
    forbidden_topics: tuple[str, ...]
    expected_past_exam_sources: tuple[str, ...]
    actual_topics: tuple[str, ...]
    actual_past_exam_sources: tuple[str, ...]
    actual_mark_totals: dict[str, int]
    actual_tiers: dict[str, str]
    missing_topics: tuple[str, ...]
    forbidden_hits: tuple[str, ...]
    missing_past_exam_sources: tuple[str, ...]
    order_mismatches: tuple[str, ...]
    mark_total_mismatches: tuple[str, ...]
    tier_mismatches: tuple[str, ...]
    passed: bool


@dataclass(frozen=True, slots=True)
class PriorityBenchmarkReport:
    armory_path: str
    cases: int
    domains: tuple[str, ...]
    pass_rate: float
    topic_recall: float
    forbidden_topic_avoidance: float
    past_exam_source_recall: float
    ordered_topic_accuracy: float
    mark_total_accuracy: float
    tier_accuracy: float
    failures: tuple[str, ...]
    results: tuple[PriorityCaseResult, ...]


def _as_string_tuple(value: object, label: str, case_number: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TypeError(f"case {case_number} {label} must be a list")
    items = tuple(item.strip().lower() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"case {case_number} {label} entries must be non-empty strings")
    return items


def _as_raw_cases(payload: object) -> list[RawPriorityCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("priority dataset must be a JSON list or an object with a 'cases' list")

    cases: list[RawPriorityCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        expected_topics = raw.get("expected_topics")
        if not isinstance(expected_topics, list) or not expected_topics:
            raise ValueError(f"case {idx} must include non-empty expected_topics")
        case: RawPriorityCase = {"expected_topics": list(expected_topics)}
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            case["id"] = raw_id
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            case["domain"] = raw_domain.strip()
        raw_forbidden = raw.get("forbidden_topics")
        if isinstance(raw_forbidden, list):
            case["forbidden_topics"] = list(raw_forbidden)
        raw_sources = raw.get("expected_past_exam_sources")
        if isinstance(raw_sources, list):
            case["expected_past_exam_sources"] = list(raw_sources)
        raw_ordered = raw.get("expected_ordered_topics")
        if isinstance(raw_ordered, list):
            case["expected_ordered_topics"] = list(raw_ordered)
        raw_marks = raw.get("expected_mark_totals")
        if isinstance(raw_marks, dict) and all(
            isinstance(key, str) and isinstance(value, int) for key, value in raw_marks.items()
        ):
            case["expected_mark_totals"] = dict(raw_marks)
        raw_tiers = raw.get("expected_tiers")
        if isinstance(raw_tiers, dict) and all(
            isinstance(key, str) and isinstance(value, str) for key, value in raw_tiers.items()
        ):
            case["expected_tiers"] = dict(raw_tiers)
        raw_limit = raw.get("limit")
        if isinstance(raw_limit, int):
            case["limit"] = raw_limit
        cases.append(case)
    return cases


def _as_string_int_dict(
    value: object,
    label: str,
    case_number: int,
) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"case {case_number} {label} must be an object")
    result: dict[str, int] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(item, int):
            raise ValueError(f"case {case_number} {label} entries must map strings to integers")
        result[key.strip().lower()] = item
    return result


def _as_string_string_dict(
    value: object,
    label: str,
    case_number: int,
) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"case {case_number} {label} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(item, str) or not item:
            raise ValueError(f"case {case_number} {label} entries must map strings to strings")
        result[key.strip().lower()] = item.strip()
    return result


def load_cases(path: Path) -> list[PriorityBenchmarkCase]:
    """Load priority benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read priority benchmark dataset: {path}") from exc
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
        raise ValueError(f"invalid priority benchmark JSON: {path}") from exc

    cases: list[PriorityBenchmarkCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        expected_topics = _as_string_tuple(raw["expected_topics"], "expected_topics", idx)
        if not expected_topics:
            raise ValueError(f"case {idx} expected_topics must not be empty")
        cases.append(
            PriorityBenchmarkCase(
                case_id=raw.get("id", f"case-{idx}"),
                expected_topics=expected_topics,
                domain=raw.get("domain"),
                forbidden_topics=_as_string_tuple(
                    raw.get("forbidden_topics"), "forbidden_topics", idx
                ),
                expected_past_exam_sources=_as_string_tuple(
                    raw.get("expected_past_exam_sources"),
                    "expected_past_exam_sources",
                    idx,
                ),
                expected_ordered_topics=_as_string_tuple(
                    raw.get("expected_ordered_topics"), "expected_ordered_topics", idx
                ),
                expected_mark_totals=_as_string_int_dict(
                    raw.get("expected_mark_totals"), "expected_mark_totals", idx
                ),
                expected_tiers=_as_string_string_dict(
                    raw.get("expected_tiers"), "expected_tiers", idx
                ),
                limit=raw.get("limit"),
            )
        )
    return cases


def run_benchmark(
    armory_path: Path,
    cases: Sequence[PriorityBenchmarkCase],
    *,
    limit: int = _DEFAULT_LIMIT,
) -> PriorityBenchmarkReport:
    """Run priority benchmark cases and return aggregate metrics."""
    if not cases:
        raise ValueError("priority benchmark dataset does not contain any cases")
    index = load_or_build(armory_path)
    results: list[PriorityCaseResult] = []

    for case in cases:
        case_limit = case.limit or limit
        analysis = analyze_priority(index.all_chunks, limit=case_limit)
        actual_topics = tuple(topic.topic.lower() for topic in analysis.topics)
        actual_sources = tuple(source.lower() for source in analysis.past_exam_sources)
        actual_mark_totals = {topic.topic.lower(): topic.exam_marks for topic in analysis.topics}
        actual_tiers = {topic.topic.lower(): priority_tier(topic) for topic in analysis.topics}
        missing_topics = tuple(
            topic for topic in case.expected_topics if topic not in actual_topics
        )
        forbidden_hits = tuple(topic for topic in case.forbidden_topics if topic in actual_topics)
        missing_sources = tuple(
            source for source in case.expected_past_exam_sources if source not in actual_sources
        )
        order_mismatches = _ordered_topic_mismatches(case.expected_ordered_topics, actual_topics)
        mark_total_mismatches = _mark_total_mismatches(
            case.expected_mark_totals,
            actual_mark_totals,
        )
        tier_mismatches = _tier_mismatches(case.expected_tiers, actual_tiers)
        passed = not (
            missing_topics
            or forbidden_hits
            or missing_sources
            or order_mismatches
            or mark_total_mismatches
            or tier_mismatches
        )
        results.append(
            PriorityCaseResult(
                case_id=case.case_id,
                expected_topics=case.expected_topics,
                forbidden_topics=case.forbidden_topics,
                expected_past_exam_sources=case.expected_past_exam_sources,
                actual_topics=actual_topics,
                actual_past_exam_sources=actual_sources,
                actual_mark_totals=actual_mark_totals,
                actual_tiers=actual_tiers,
                missing_topics=missing_topics,
                forbidden_hits=forbidden_hits,
                missing_past_exam_sources=missing_sources,
                order_mismatches=order_mismatches,
                mark_total_mismatches=mark_total_mismatches,
                tier_mismatches=tier_mismatches,
                passed=passed,
            )
        )

    total = len(results)
    expected_topic_count = sum(len(result.expected_topics) for result in results)
    missed_topic_count = sum(len(result.missing_topics) for result in results)
    forbidden_count = sum(len(result.forbidden_topics) for result in results)
    forbidden_hit_count = sum(len(result.forbidden_hits) for result in results)
    expected_source_count = sum(len(result.expected_past_exam_sources) for result in results)
    missed_source_count = sum(len(result.missing_past_exam_sources) for result in results)
    order_check_count = sum(len(case.expected_ordered_topics) > 1 for case in cases)
    order_failure_count = sum(1 for result in results if result.order_mismatches)
    mark_check_count = sum(len(case.expected_mark_totals or {}) for case in cases)
    mark_failure_count = sum(len(result.mark_total_mismatches) for result in results)
    tier_check_count = sum(len(case.expected_tiers or {}) for case in cases)
    tier_failure_count = sum(len(result.tier_mismatches) for result in results)
    return PriorityBenchmarkReport(
        armory_path=str(armory_path),
        cases=total,
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        pass_rate=sum(1 for result in results if result.passed) / total,
        topic_recall=(expected_topic_count - missed_topic_count) / expected_topic_count,
        forbidden_topic_avoidance=(
            1.0
            if forbidden_count == 0
            else (forbidden_count - forbidden_hit_count) / forbidden_count
        ),
        past_exam_source_recall=(
            1.0
            if expected_source_count == 0
            else (expected_source_count - missed_source_count) / expected_source_count
        ),
        ordered_topic_accuracy=(
            1.0
            if order_check_count == 0
            else (order_check_count - order_failure_count) / order_check_count
        ),
        mark_total_accuracy=(
            1.0
            if mark_check_count == 0
            else (mark_check_count - mark_failure_count) / mark_check_count
        ),
        tier_accuracy=(
            1.0
            if tier_check_count == 0
            else (tier_check_count - tier_failure_count) / tier_check_count
        ),
        failures=tuple(result.case_id for result in results if not result.passed),
        results=tuple(results),
    )


def _ordered_topic_mismatches(
    expected_ordered_topics: tuple[str, ...],
    actual_topics: tuple[str, ...],
) -> tuple[str, ...]:
    if len(expected_ordered_topics) < 2:
        return ()
    positions = {topic: index for index, topic in enumerate(actual_topics)}
    mismatches: list[str] = []
    for earlier, later in pairwise(expected_ordered_topics):
        if earlier not in positions or later not in positions:
            continue
        if positions[earlier] > positions[later]:
            mismatches.append(f"{earlier} should rank before {later}")
    return tuple(mismatches)


def _mark_total_mismatches(
    expected_mark_totals: dict[str, int] | None,
    actual_mark_totals: dict[str, int],
) -> tuple[str, ...]:
    if not expected_mark_totals:
        return ()
    mismatches = []
    for topic, expected_marks in expected_mark_totals.items():
        actual_marks = actual_mark_totals.get(topic)
        if actual_marks != expected_marks:
            mismatches.append(f"{topic}: expected {expected_marks}, got {actual_marks}")
    return tuple(mismatches)


def _tier_mismatches(
    expected_tiers: dict[str, str] | None,
    actual_tiers: dict[str, str],
) -> tuple[str, ...]:
    if not expected_tiers:
        return ()
    mismatches = []
    for topic, expected_tier in expected_tiers.items():
        actual_tier = actual_tiers.get(topic)
        if actual_tier != expected_tier:
            mismatches.append(f"{topic}: expected {expected_tier}, got {actual_tier}")
    return tuple(mismatches)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_text_report(report: PriorityBenchmarkReport) -> None:
    """Print a compact human-readable priority benchmark report."""
    print(f"Priority benchmark: {report.cases} cases against {report.armory_path}")
    if report.domains:
        print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    print(f"pass_rate={_format_percent(report.pass_rate)}")
    print(f"topic_recall={_format_percent(report.topic_recall)}")
    print(f"forbidden_topic_avoidance={_format_percent(report.forbidden_topic_avoidance)}")
    print(f"past_exam_source_recall={_format_percent(report.past_exam_source_recall)}")
    print(f"ordered_topic_accuracy={_format_percent(report.ordered_topic_accuracy)}")
    print(f"mark_total_accuracy={_format_percent(report.mark_total_accuracy)}")
    print(f"tier_accuracy={_format_percent(report.tier_accuracy)}")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL priority benchmark cases")
    parser.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    parser.add_argument("--min-pass-rate", type=float, default=0.0)
    parser.add_argument("--min-topic-recall", type=float, default=0.0)
    parser.add_argument("--min-forbidden-avoidance", type=float, default=0.0)
    parser.add_argument("--min-past-exam-source-recall", type=float, default=0.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    report = run_benchmark(armory, load_cases(dataset), limit=cast("int", args.limit))
    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    if (
        report.pass_rate < cast("float", args.min_pass_rate)
        or report.topic_recall < cast("float", args.min_topic_recall)
        or report.forbidden_topic_avoidance < cast("float", args.min_forbidden_avoidance)
        or report.past_exam_source_recall < cast("float", args.min_past_exam_source_recall)
    ):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TypeError, ValueError) as exc:
        print(f"priority benchmark error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
