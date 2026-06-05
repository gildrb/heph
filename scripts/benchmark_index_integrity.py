"""Benchmark index integrity for extracted/chunked academic material text.

Dataset format:

JSONL:
    {
      "id": "required-topic-text",
      "source": "materials/lecture-notes.md",
      "must_include": ["Administrative header", "Matrix multiplication"],
      "must_not_include": ["Formula-not-decoded"]
    }

This benchmark checks the indexed chunks directly. It catches extraction,
normalization, and chunking regressions before retrieval or model answering can
hide them.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.rag import load_or_build
from hephaion.rag.health import (
    DEFAULT_EXTRACTION_FORBIDDEN_TEXT,
    scan_extraction_health,
)


class RawIndexIntegrityCase(TypedDict):
    source: str
    must_include: list[str]
    domain: NotRequired[str]
    id: NotRequired[str]
    task: NotRequired[str]
    must_not_include: NotRequired[list[str]]


@dataclass(frozen=True, slots=True)
class IndexIntegrityCase:
    case_id: str
    source: str
    must_include: tuple[str, ...]
    must_not_include: tuple[str, ...] = ()
    domain: str | None = None
    task: str | None = None


@dataclass(frozen=True, slots=True)
class IndexIntegrityCaseResult:
    case_id: str
    source: str
    chunk_count: int
    missing_text: tuple[str, ...]
    forbidden_text_present: tuple[str, ...]
    passed: bool


@dataclass(frozen=True, slots=True)
class CorpusForbiddenTextResult:
    source: str
    forbidden_text_present: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IndexIntegrityReport:
    armory_path: str
    cases: int
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    pass_rate: float
    required_text_rate: float
    forbidden_text_rate: float
    corpus_forbidden_text_rate: float
    corpus_forbidden_text: tuple[str, ...]
    corpus_forbidden_text_failures: tuple[CorpusForbiddenTextResult, ...]
    failures: tuple[str, ...]
    results: tuple[IndexIntegrityCaseResult, ...]


def _as_string_tuple(value: object, label: str, case_number: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TypeError(f"case {case_number} {label} must be a list")
    items = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"case {case_number} {label} entries must be non-empty strings")
    return items


def _as_raw_cases(payload: object) -> list[RawIndexIntegrityCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("index integrity dataset must be a JSON list or object with a cases list")

    cases: list[RawIndexIntegrityCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        source = raw.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"case {idx} must include non-empty source")
        must_include = raw.get("must_include")
        if not isinstance(must_include, list) or not must_include:
            raise ValueError(f"case {idx} must include non-empty must_include")
        case: RawIndexIntegrityCase = {"source": source, "must_include": list(must_include)}
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            case["id"] = raw_id
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            case["domain"] = raw_domain.strip()
        raw_task = raw.get("task")
        if isinstance(raw_task, str) and raw_task.strip():
            case["task"] = raw_task.strip()
        raw_forbidden = raw.get("must_not_include")
        if isinstance(raw_forbidden, list):
            case["must_not_include"] = list(raw_forbidden)
        cases.append(case)
    return cases


def load_cases(path: Path) -> list[IndexIntegrityCase]:
    """Load index-integrity benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read index integrity dataset: {path}") from exc
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
        raise ValueError(f"invalid index integrity benchmark JSON: {path}") from exc

    cases: list[IndexIntegrityCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        cases.append(
            IndexIntegrityCase(
                case_id=raw.get("id", f"case-{idx}"),
                source=raw["source"].strip(),
                must_include=_as_string_tuple(raw["must_include"], "must_include", idx),
                must_not_include=_as_string_tuple(
                    raw.get("must_not_include"), "must_not_include", idx
                ),
                domain=raw.get("domain"),
                task=raw.get("task"),
            )
        )
    return cases


def run_benchmark(
    armory_path: Path,
    cases: Sequence[IndexIntegrityCase],
    *,
    corpus_forbidden_text: Sequence[str] = DEFAULT_EXTRACTION_FORBIDDEN_TEXT,
) -> IndexIntegrityReport:
    """Run index-integrity checks against an armory index."""
    index = load_or_build(armory_path)
    by_source = {
        document.source: " ".join(chunk.text for chunk in document.chunks)
        for document in index.documents
    }
    chunk_counts = {document.source: len(document.chunks) for document in index.documents}
    results: list[IndexIntegrityCaseResult] = []
    for case in cases:
        text = by_source.get(case.source, "")
        missing_text = tuple(item for item in case.must_include if item not in text)
        forbidden_text_present = tuple(item for item in case.must_not_include if item in text)
        results.append(
            IndexIntegrityCaseResult(
                case_id=case.case_id,
                source=case.source,
                chunk_count=chunk_counts.get(case.source, 0),
                missing_text=missing_text,
                forbidden_text_present=forbidden_text_present,
                passed=bool(text) and not missing_text and not forbidden_text_present,
            )
        )

    failures = tuple(
        (
            f"{result.case_id}: missing={result.missing_text} "
            f"forbidden={result.forbidden_text_present}"
        )
        for result in results
        if not result.passed
    )
    required_checks = sum(len(case.must_include) for case in cases)
    required_passes = sum(
        len(case.must_include) - len(result.missing_text)
        for case, result in zip(cases, results, strict=True)
    )
    forbidden_checks = sum(len(case.must_not_include) for case in cases)
    forbidden_passes = sum(
        len(case.must_not_include) - len(result.forbidden_text_present)
        for case, result in zip(cases, results, strict=True)
    )
    health_report = scan_extraction_health(
        armory_path,
        forbidden_text=tuple(corpus_forbidden_text),
    )
    corpus_failures = tuple(
        CorpusForbiddenTextResult(
            source=issue.source,
            forbidden_text_present=issue.forbidden_text_present,
        )
        for issue in health_report.issues
    )
    return IndexIntegrityReport(
        armory_path=str(armory_path),
        cases=len(cases),
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        tasks=tuple(sorted({case.task for case in cases if case.task})),
        pass_rate=sum(1 for result in results if result.passed) / len(cases) if cases else 0.0,
        required_text_rate=required_passes / required_checks if required_checks else 1.0,
        forbidden_text_rate=forbidden_passes / forbidden_checks if forbidden_checks else 1.0,
        corpus_forbidden_text_rate=health_report.pass_rate,
        corpus_forbidden_text=health_report.forbidden_text,
        corpus_forbidden_text_failures=corpus_failures,
        failures=failures,
        results=tuple(results),
    )


def print_text_report(report: IndexIntegrityReport) -> None:
    """Print a concise index-integrity benchmark report."""
    print(f"Index integrity benchmark: {report.cases} case(s) against {report.armory_path}")
    print(f"pass_rate={report.pass_rate:.1%}")
    print(f"required_text={report.required_text_rate:.1%}")
    print(f"forbidden_text={report.forbidden_text_rate:.1%}")
    print(f"corpus_forbidden_text={report.corpus_forbidden_text_rate:.1%}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")
    if report.corpus_forbidden_text_failures:
        print("corpus forbidden text failures:")
        for failure in report.corpus_forbidden_text_failures:
            print(f"  - {failure.source}: {failure.forbidden_text_present}")


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path)
    parser.add_argument("dataset", type=Path, nargs="?")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help=(
            "Run only the whole-corpus generic extraction-noise scan. "
            "Use this before labelled cases exist for a new armory."
        ),
    )
    parser.add_argument("--min-pass-rate", type=float, default=1.0)
    parser.add_argument("--min-required-text", type=float, default=1.0)
    parser.add_argument("--min-forbidden-text", type=float, default=1.0)
    parser.add_argument("--min-corpus-forbidden-text", type=float, default=1.0)
    parser.add_argument("--json-report", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    scan_only = cast("bool", args.scan_only)
    dataset = cast("Path | None", args.dataset)
    if dataset is None and not scan_only:
        print(
            "index integrity benchmark error: dataset is required unless --scan-only is set",
            file=sys.stderr,
        )
        return 2
    min_pass_rate = cast("float", args.min_pass_rate)
    min_required_text = cast("float", args.min_required_text)
    min_forbidden_text = cast("float", args.min_forbidden_text)
    min_corpus_forbidden_text = cast("float", args.min_corpus_forbidden_text)
    _validate_rate(min_pass_rate, "--min-pass-rate", parser)
    _validate_rate(min_required_text, "--min-required-text", parser)
    _validate_rate(min_forbidden_text, "--min-forbidden-text", parser)
    _validate_rate(min_corpus_forbidden_text, "--min-corpus-forbidden-text", parser)
    try:
        cases = [] if dataset is None else load_cases(dataset.expanduser().resolve())
        report = run_benchmark(
            cast("Path", args.armory).expanduser().resolve(),
            cases,
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"index integrity benchmark error: {exc}", file=sys.stderr)
        return 2
    print_text_report(report)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote index integrity benchmark report to {json_report}")
    return (
        0
        if (scan_only or report.pass_rate >= min_pass_rate)
        and report.required_text_rate >= min_required_text
        and report.forbidden_text_rate >= min_forbidden_text
        and report.corpus_forbidden_text_rate >= min_corpus_forbidden_text
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
