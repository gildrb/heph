"""Compare benchmark JSON reports and fail on metric regressions.

Both ``scripts.run_benchmark_suite`` and ``scripts.run_replay_answer_eval`` can
write machine-readable JSON reports. This helper compares a current report to a
baseline report so CI or local model bake-offs can detect regressions without
scraping terminal output.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

DEFAULT_METRICS: tuple[str, ...] = (
    "rag.hit_rate",
    "rag.mean_reciprocal_rank",
    "rag.mean_expected_recall",
    "rag.forbidden_before_expected_avoidance",
    "material_roles.pass_rate",
    "document_understanding.indexed_documents",
    "document_understanding.chunks",
    "document_understanding.extraction_health_pass_rate",
    "document_understanding.overview_source_coverage_rate",
    "index_integrity.pass_rate",
    "index_integrity.required_text_rate",
    "index_integrity.forbidden_text_rate",
    "index_integrity.corpus_forbidden_text_rate",
    "priority.pass_rate",
    "priority.topic_recall",
    "priority.forbidden_topic_avoidance",
    "priority.past_exam_source_recall",
    "prompt_cache.pass_rate",
    "prompt_cache.stable_hash_reuse_rate",
    "prompt_cache.prefix_invalidation_rate",
    "prompt_cache.dynamic_tail_preservation_rate",
    "prompt_cache.request_order_preservation_rate",
    "chat_events.material_operation_metadata_rate",
    "chat_events.evidence_metadata_rate",
    "chat_events.tool_runtime_metadata_rate",
    "chat_events.acceptance_criteria_metadata_rate",
    "chat_events.answer_pass_rate",
    "chat_events.answer_shape_rate",
    "chat_runtime_events.tool_runtime_metadata_rate",
    "chat_runtime_events.material_operation_metadata_rate",
    "chat_runtime_events.acceptance_criteria_metadata_rate",
    "chat_runtime_events.answer_pass_rate",
    "chat_runtime_events.answer_shape_rate",
    "answers.pass_rate",
    "answers.citation_validity_rate",
    "answers.citation_presence_rate",
    "answers.expected_citation_rate",
    "answers.citation_source_rate",
    "answers.required_text_rate",
    "answers.forbidden_text_rate",
    "answers.supported_claim_rate",
    "answers.contradiction_rate",
    "answers.answer_shape_rate",
    "answers.evidence_coverage_rate",
    "answers.required_label_rate",
    "academic_items.pass_rate",
    "academic_items.question_type_count",
    "academic_items.grounded_question_rate",
    "academic_items.canonical_source_label_rate",
    "learning_state.pass_rate",
    "learning_state.transition_pass_rate",
    "learning_state.scheduling_pass_rate",
    "learning_state.mastery_metadata_rate",
    "learning_state.prompt_contract_rate",
    "report.pass_rate",
    "report.citation_validity_rate",
    "report.citation_presence_rate",
    "report.expected_citation_rate",
    "report.citation_source_rate",
    "report.required_text_rate",
    "report.forbidden_text_rate",
    "report.supported_claim_rate",
    "report.contradiction_rate",
    "report.answer_shape_rate",
    "report.evidence_coverage_rate",
    "report.required_label_rate",
)


@dataclass(frozen=True, slots=True)
class MetricComparison:
    metric: str
    baseline: float
    current: float
    delta: float
    tolerance: float
    passed: bool


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    baseline_report: str
    current_report: str
    tolerance: float
    comparisons: tuple[MetricComparison, ...]
    regressions: tuple[str, ...]


def _load_report(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read benchmark report: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid benchmark report JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise TypeError(f"benchmark report must be a JSON object: {path}")
    return cast("Mapping[str, object]", payload)


def _metric_value(report: Mapping[str, object], metric: str) -> float | None:
    value: object = report
    for part in metric.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def compare_reports(
    baseline_path: Path,
    current_path: Path,
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    tolerance: float = 0.0,
) -> ComparisonReport:
    """Compare numeric metrics present in both reports."""
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    baseline = _load_report(baseline_path)
    current = _load_report(current_path)

    comparisons: list[MetricComparison] = []
    for metric in metrics:
        baseline_value = _metric_value(baseline, metric)
        current_value = _metric_value(current, metric)
        if baseline_value is None or current_value is None:
            continue
        delta = current_value - baseline_value
        comparisons.append(
            MetricComparison(
                metric=metric,
                baseline=baseline_value,
                current=current_value,
                delta=delta,
                tolerance=tolerance,
                passed=delta + tolerance >= 0,
            )
        )

    if not comparisons:
        raise ValueError("no comparable numeric metrics found")
    regressions = tuple(comparison.metric for comparison in comparisons if not comparison.passed)
    return ComparisonReport(
        baseline_report=str(baseline_path),
        current_report=str(current_path),
        tolerance=tolerance,
        comparisons=tuple(comparisons),
        regressions=regressions,
    )


def _print_text_report(report: ComparisonReport) -> None:
    print(f"Benchmark report comparison: {len(report.comparisons)} metric(s)")
    print(f"baseline={report.baseline_report}")
    print(f"current={report.current_report}")
    print(f"tolerance={report.tolerance:.6f}")
    for comparison in report.comparisons:
        status = "PASS" if comparison.passed else "REGRESSION"
        print(
            f"{status} {comparison.metric}: "
            f"baseline={comparison.baseline:.6f} "
            f"current={comparison.current:.6f} "
            f"delta={comparison.delta:.6f}"
        )


def print_text_report(report: ComparisonReport) -> None:
    """Print a stable human-readable comparison report."""
    _print_text_report(report)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Baseline JSON report")
    parser.add_argument("current", type=Path, help="Current JSON report")
    parser.add_argument(
        "--metric",
        action="append",
        dest="metrics",
        help="Metric path to compare; may be repeated. Defaults to known benchmark metrics.",
    )
    parser.add_argument("--tolerance", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", help="Print comparison as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    baseline = cast("Path", args.baseline).expanduser().resolve()
    current = cast("Path", args.current).expanduser().resolve()
    tolerance = cast("float", args.tolerance)
    metrics = tuple(cast("list[str] | None", args.metrics) or DEFAULT_METRICS)

    try:
        report = compare_reports(
            baseline,
            current,
            metrics=metrics,
            tolerance=tolerance,
        )
    except (TypeError, ValueError) as exc:
        print(f"benchmark report comparison error: {exc}", file=sys.stderr)
        return 2

    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        _print_text_report(report)
    return 0 if not report.regressions else 1


if __name__ == "__main__":
    raise SystemExit(main())
