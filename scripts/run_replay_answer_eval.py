"""Run replay prompts through the real chat harness and score the answers.

This is the model-backed companion to the deterministic benchmark suite. It
turns replay prompts into answer fixtures, writes them to disk for inspection,
then applies the same grounded-answer gates used by ``benchmark_answers``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.runtime import ChatConfig
from scripts import benchmark_answers, compare_benchmark_reports, replay_answer_benchmark

DEFAULT_ANSWER_PASS_RATE = 1.0
DEFAULT_CITATION_VALIDITY = 1.0
DEFAULT_CITATION_PRESENCE = 1.0
DEFAULT_EXPECTED_CITATIONS = 1.0
DEFAULT_CITATION_SOURCES = 1.0
DEFAULT_REQUIRED_TEXT = 1.0
DEFAULT_FORBIDDEN_TEXT = 1.0
DEFAULT_SUPPORTED_CLAIMS = 1.0
DEFAULT_CONTRADICTION_RATE = 1.0
DEFAULT_ANSWER_SHAPE = 1.0
DEFAULT_EVIDENCE_COVERAGE = 1.0
DEFAULT_REQUIRED_LABEL = 1.0
DEFAULT_MIN_ANSWER_DOMAINS = 3
DEFAULT_MIN_ANSWER_TASKS = 3


class ReplayAnswerEvalSummary(TypedDict):
    armory: str
    replay_dataset: str
    output: str
    model: str
    base_url: str
    max_tokens: int
    rag_context_budget: int
    status: int
    thresholds: dict[str, float | int]
    report: dict[str, object]
    report_path: NotRequired[str]


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def _validate_positive(value: int, label: str, parser: argparse.ArgumentParser) -> None:
    if value <= 0:
        parser.error(f"{label} must be positive")


def _validate_answer_suite_integrity(
    report: benchmark_answers.AnswerBenchmarkReport,
    *,
    min_domains: int = DEFAULT_MIN_ANSWER_DOMAINS,
    min_tasks: int = DEFAULT_MIN_ANSWER_TASKS,
) -> None:
    """Reject model replay runs that only prove one response shape."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "replay answer benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    if len(report.tasks) < min_tasks:
        raise ValueError(
            "replay answer benchmark must cover at least "
            f"{min_tasks} labelled answer tasks; found {len(report.tasks)}"
        )


def run_replay_answer_eval(
    armory_path: Path,
    replay_dataset: Path,
    output_path: Path,
    config: ChatConfig,
    *,
    answer_pass_rate: float = DEFAULT_ANSWER_PASS_RATE,
    citation_validity: float = DEFAULT_CITATION_VALIDITY,
    citation_presence: float = DEFAULT_CITATION_PRESENCE,
    expected_citations: float = DEFAULT_EXPECTED_CITATIONS,
    citation_sources: float = DEFAULT_CITATION_SOURCES,
    required_text: float = DEFAULT_REQUIRED_TEXT,
    forbidden_text: float = DEFAULT_FORBIDDEN_TEXT,
    supported_claims: float = DEFAULT_SUPPORTED_CLAIMS,
    contradiction_rate: float = DEFAULT_CONTRADICTION_RATE,
    answer_shape: float = DEFAULT_ANSWER_SHAPE,
    evidence_coverage: float = DEFAULT_EVIDENCE_COVERAGE,
    required_label: float = DEFAULT_REQUIRED_LABEL,
    min_answer_domains: int = DEFAULT_MIN_ANSWER_DOMAINS,
    min_answer_tasks: int = DEFAULT_MIN_ANSWER_TASKS,
    report_path: Path | None = None,
    compare_to: Path | None = None,
    compare_tolerance: float = 0.0,
) -> int:
    """Replay prompts, write answer fixtures, score them, and return a status code."""
    if compare_to is not None and report_path is None:
        raise ValueError("--compare-to requires --json-report so the current run can be compared")
    replay_cases = replay_answer_benchmark.load_cases(replay_dataset)
    fixtures = replay_answer_benchmark.replay_cases(armory_path, replay_cases, config)
    replay_answer_benchmark.write_jsonl(output_path, fixtures)

    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output_path))
    _validate_answer_suite_integrity(
        report,
        min_domains=min_answer_domains,
        min_tasks=min_answer_tasks,
    )
    failed_threshold = (
        report.pass_rate < answer_pass_rate
        or report.citation_validity_rate < citation_validity
        or report.citation_presence_rate < citation_presence
        or report.expected_citation_rate < expected_citations
        or report.citation_source_rate < citation_sources
        or report.required_text_rate < required_text
        or report.forbidden_text_rate < forbidden_text
        or report.supported_claim_rate < supported_claims
        or report.contradiction_rate < contradiction_rate
        or report.answer_shape_rate < answer_shape
        or report.evidence_coverage_rate < evidence_coverage
        or report.required_label_rate < required_label
    )
    status = 1 if failed_threshold else 0
    if report_path is not None:
        _write_json_report(
            report_path,
            _summary(
                armory_path=armory_path,
                replay_dataset=replay_dataset,
                output_path=output_path,
                config=config,
                status=status,
                answer_pass_rate=answer_pass_rate,
                citation_validity=citation_validity,
                citation_presence=citation_presence,
                expected_citations=expected_citations,
                citation_sources=citation_sources,
                required_text=required_text,
                forbidden_text=forbidden_text,
                supported_claims=supported_claims,
                contradiction_rate=contradiction_rate,
                answer_shape=answer_shape,
                evidence_coverage=evidence_coverage,
                required_label=required_label,
                min_answer_domains=min_answer_domains,
                min_answer_tasks=min_answer_tasks,
                report=report,
                report_path=report_path,
            ),
        )
    print(f"Wrote {len(fixtures)} answer fixture(s) to {output_path}")
    if report_path is not None:
        print(f"Wrote replay answer eval report to {report_path}")
    benchmark_answers.print_text_report(report)
    if compare_to is not None:
        if report_path is None:
            raise ValueError(
                "--compare-to requires --json-report so the current run can be compared"
            )
        comparison = compare_benchmark_reports.compare_reports(
            compare_to,
            report_path,
            tolerance=compare_tolerance,
        )
        compare_benchmark_reports.print_text_report(comparison)
        if comparison.regressions:
            status = 1
    return status


def _summary(
    *,
    armory_path: Path,
    replay_dataset: Path,
    output_path: Path,
    config: ChatConfig,
    status: int,
    answer_pass_rate: float,
    citation_validity: float,
    citation_presence: float,
    expected_citations: float,
    citation_sources: float,
    required_text: float,
    forbidden_text: float,
    supported_claims: float,
    contradiction_rate: float,
    answer_shape: float,
    evidence_coverage: float,
    required_label: float,
    min_answer_domains: int,
    min_answer_tasks: int,
    report: benchmark_answers.AnswerBenchmarkReport,
    report_path: Path | None = None,
) -> ReplayAnswerEvalSummary:
    summary: ReplayAnswerEvalSummary = {
        "armory": str(armory_path),
        "replay_dataset": str(replay_dataset),
        "output": str(output_path),
        "model": config.model,
        "base_url": config.base_url,
        "max_tokens": config.max_tokens,
        "rag_context_budget": config.rag_context_budget,
        "status": status,
        "thresholds": {
            "answer_pass_rate": answer_pass_rate,
            "citation_validity": citation_validity,
            "citation_presence": citation_presence,
            "expected_citations": expected_citations,
            "citation_sources": citation_sources,
            "required_text": required_text,
            "forbidden_text": forbidden_text,
            "supported_claims": supported_claims,
            "contradiction_rate": contradiction_rate,
            "answer_shape": answer_shape,
            "evidence_coverage": evidence_coverage,
            "required_label": required_label,
            "min_answer_domains": min_answer_domains,
            "min_answer_tasks": min_answer_tasks,
        },
        "report": cast("dict[str, object]", asdict(report)),
    }
    if report_path is not None:
        summary["report_path"] = str(report_path)
    return summary


def _write_json_report(path: Path, summary: ReplayAnswerEvalSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL replay prompts")
    parser.add_argument("output", type=Path, help="Output JSONL answer fixture path")
    parser.add_argument("--model", default="", help="Model name for ChatConfig")
    parser.add_argument("--base-url", default="", help="Optional OpenAI-compatible base URL")
    parser.add_argument("--api-key", default="", help="Optional API key")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--rag-context-budget", type=int, default=2000)
    parser.add_argument("--min-answer-pass-rate", type=float, default=DEFAULT_ANSWER_PASS_RATE)
    parser.add_argument("--min-citation-validity", type=float, default=DEFAULT_CITATION_VALIDITY)
    parser.add_argument("--min-citation-presence", type=float, default=DEFAULT_CITATION_PRESENCE)
    parser.add_argument("--min-expected-citations", type=float, default=DEFAULT_EXPECTED_CITATIONS)
    parser.add_argument("--min-citation-sources", type=float, default=DEFAULT_CITATION_SOURCES)
    parser.add_argument("--min-required-text", type=float, default=DEFAULT_REQUIRED_TEXT)
    parser.add_argument("--min-forbidden-text", type=float, default=DEFAULT_FORBIDDEN_TEXT)
    parser.add_argument("--min-supported-claims", type=float, default=DEFAULT_SUPPORTED_CLAIMS)
    parser.add_argument(
        "--min-contradiction-rate",
        type=float,
        default=DEFAULT_CONTRADICTION_RATE,
    )
    parser.add_argument("--min-answer-shape", type=float, default=DEFAULT_ANSWER_SHAPE)
    parser.add_argument("--min-evidence-coverage", type=float, default=DEFAULT_EVIDENCE_COVERAGE)
    parser.add_argument("--min-required-label", type=float, default=DEFAULT_REQUIRED_LABEL)
    parser.add_argument("--min-answer-domains", type=int, default=DEFAULT_MIN_ANSWER_DOMAINS)
    parser.add_argument("--min-answer-tasks", type=int, default=DEFAULT_MIN_ANSWER_TASKS)
    parser.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help="Optional machine-readable eval report path",
    )
    parser.add_argument(
        "--compare-to",
        type=Path,
        default=None,
        help="Optional baseline JSON report. Requires --json-report.",
    )
    parser.add_argument(
        "--compare-tolerance",
        type=float,
        default=0.0,
        help="Allowed negative metric delta when comparing to --compare-to.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    output = cast("Path", args.output).expanduser().resolve()
    max_tokens = cast("int", args.max_tokens)
    rag_context_budget = cast("int", args.rag_context_budget)
    answer_pass_rate = cast("float", args.min_answer_pass_rate)
    citation_validity = cast("float", args.min_citation_validity)
    citation_presence = cast("float", args.min_citation_presence)
    expected_citations = cast("float", args.min_expected_citations)
    citation_sources = cast("float", args.min_citation_sources)
    required_text = cast("float", args.min_required_text)
    forbidden_text = cast("float", args.min_forbidden_text)
    supported_claims = cast("float", args.min_supported_claims)
    contradiction_rate = cast("float", args.min_contradiction_rate)
    answer_shape = cast("float", args.min_answer_shape)
    evidence_coverage = cast("float", args.min_evidence_coverage)
    required_label = cast("float", args.min_required_label)
    min_answer_domains = cast("int", args.min_answer_domains)
    min_answer_tasks = cast("int", args.min_answer_tasks)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
    compare_to = cast("Path | None", args.compare_to)
    if compare_to is not None:
        compare_to = compare_to.expanduser().resolve()
    compare_tolerance = cast("float", args.compare_tolerance)

    _validate_positive(max_tokens, "--max-tokens", parser)
    _validate_positive(rag_context_budget, "--rag-context-budget", parser)
    _validate_positive(min_answer_domains, "--min-answer-domains", parser)
    _validate_positive(min_answer_tasks, "--min-answer-tasks", parser)
    _validate_rate(answer_pass_rate, "--min-answer-pass-rate", parser)
    _validate_rate(citation_validity, "--min-citation-validity", parser)
    _validate_rate(citation_presence, "--min-citation-presence", parser)
    _validate_rate(expected_citations, "--min-expected-citations", parser)
    _validate_rate(citation_sources, "--min-citation-sources", parser)
    _validate_rate(required_text, "--min-required-text", parser)
    _validate_rate(forbidden_text, "--min-forbidden-text", parser)
    _validate_rate(supported_claims, "--min-supported-claims", parser)
    _validate_rate(contradiction_rate, "--min-contradiction-rate", parser)
    _validate_rate(answer_shape, "--min-answer-shape", parser)
    _validate_rate(evidence_coverage, "--min-evidence-coverage", parser)
    _validate_rate(required_label, "--min-required-label", parser)
    if compare_tolerance < 0:
        parser.error("--compare-tolerance must be non-negative")

    config = ChatConfig(
        api_key=cast("str", args.api_key),
        base_url=cast("str", args.base_url),
        model=cast("str", args.model),
        max_tokens=max_tokens,
        rag_context_budget=rag_context_budget,
    )

    try:
        return run_replay_answer_eval(
            armory,
            dataset,
            output,
            config,
            answer_pass_rate=answer_pass_rate,
            citation_validity=citation_validity,
            citation_presence=citation_presence,
            expected_citations=expected_citations,
            citation_sources=citation_sources,
            required_text=required_text,
            forbidden_text=forbidden_text,
            supported_claims=supported_claims,
            contradiction_rate=contradiction_rate,
            answer_shape=answer_shape,
            evidence_coverage=evidence_coverage,
            required_label=required_label,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            report_path=json_report,
            compare_to=compare_to,
            compare_tolerance=compare_tolerance,
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"replay answer eval error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
