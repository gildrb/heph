"""Benchmark source-traceable academic item extraction."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.rag import load_or_build
from hephaistos.study.knowledge import (
    AcademicItem,
    AcademicItemKind,
    build_course_knowledge_graph,
    extract_academic_items,
    generate_grounded_study_questions,
)


class RawAcademicItemCase(TypedDict):
    source_ref: str
    kind: str
    text: str
    concept: NotRequired[str]
    id: NotRequired[str]
    domain: NotRequired[str]


@dataclass(frozen=True, slots=True)
class AcademicItemCase:
    case_id: str
    source_ref: str
    kind: AcademicItemKind
    text: str
    concept: str = ""
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class AcademicItemCaseResult:
    case_id: str
    source_ref: str
    kind: str
    expected_text: str
    matched: bool
    failure: str = ""


@dataclass(frozen=True, slots=True)
class AcademicItemBenchmarkReport:
    cases: int
    domains: tuple[str, ...]
    kinds: tuple[str, ...]
    pass_rate: float
    generated_questions: int
    question_type_count: int
    question_types: tuple[str, ...]
    grounded_question_rate: float
    failures: tuple[str, ...]
    results: tuple[AcademicItemCaseResult, ...]


def _as_raw_cases(payload: object) -> list[RawAcademicItemCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("academic item dataset must be a JSON list or object with cases")
    cases: list[RawAcademicItemCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        source_ref = raw.get("source_ref")
        kind = raw.get("kind")
        text = raw.get("text")
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise ValueError(f"case {idx} must include source_ref")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError(f"case {idx} must include kind")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"case {idx} must include text")
        case: RawAcademicItemCase = {
            "source_ref": source_ref.strip(),
            "kind": kind.strip(),
            "text": text.strip(),
        }
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            case["id"] = raw_id.strip()
        raw_concept = raw.get("concept")
        if isinstance(raw_concept, str) and raw_concept.strip():
            case["concept"] = raw_concept.strip()
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            case["domain"] = raw_domain.strip()
        cases.append(case)
    return cases


def load_cases(path: Path) -> list[AcademicItemCase]:
    """Load academic-item benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read academic item benchmark dataset: {path}") from exc
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
        raise ValueError(f"invalid academic item benchmark JSON: {path}") from exc

    cases: list[AcademicItemCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        try:
            kind = AcademicItemKind(raw["kind"])
        except ValueError as exc:
            raise ValueError(f"case {idx} has unsupported academic item kind") from exc
        cases.append(
            AcademicItemCase(
                case_id=raw.get("id", f"case-{idx}"),
                source_ref=raw["source_ref"],
                kind=kind,
                text=raw["text"],
                concept=raw.get("concept", ""),
                domain=raw.get("domain"),
            )
        )
    return cases


def run_benchmark(
    armory_path: Path,
    cases: Sequence[AcademicItemCase],
) -> AcademicItemBenchmarkReport:
    """Run academic-item extraction benchmark cases against an armory."""
    if not cases:
        raise ValueError("academic item benchmark dataset does not contain any cases")
    items = extract_academic_items(load_or_build(armory_path).all_chunks)
    questions = generate_grounded_study_questions(
        build_course_knowledge_graph(items),
        limit_per_concept=8,
    )
    results = tuple(_evaluate_case(case, items) for case in cases)
    passed = sum(1 for result in results if result.matched)
    failures = tuple(result.case_id for result in results if not result.matched)
    grounded_questions = sum(1 for question in questions if question.grounding_source_refs)
    question_types = tuple(sorted({question.question_type for question in questions}))
    return AcademicItemBenchmarkReport(
        cases=len(cases),
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        kinds=tuple(sorted({case.kind.value for case in cases})),
        pass_rate=passed / len(cases),
        generated_questions=len(questions),
        question_type_count=len(question_types),
        question_types=question_types,
        grounded_question_rate=(grounded_questions / len(questions) if questions else 1.0),
        failures=failures,
        results=results,
    )


def _evaluate_case(
    case: AcademicItemCase,
    items: Sequence[AcademicItem],
) -> AcademicItemCaseResult:
    for item in items:
        if (
            item.source_ref == case.source_ref
            and item.kind is case.kind
            and case.text.casefold() in item.text.casefold()
            and (not case.concept or item.concept.casefold() == case.concept.casefold())
        ):
            return AcademicItemCaseResult(
                case_id=case.case_id,
                source_ref=case.source_ref,
                kind=case.kind.value,
                expected_text=case.text,
                matched=True,
            )
    return AcademicItemCaseResult(
        case_id=case.case_id,
        source_ref=case.source_ref,
        kind=case.kind.value,
        expected_text=case.text,
        matched=False,
        failure="expected academic item not extracted",
    )


def print_text_report(report: AcademicItemBenchmarkReport) -> None:
    """Print a compact human-readable report."""
    print(f"Academic item benchmark: {report.cases} cases")
    if report.domains:
        print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    if report.kinds:
        print(f"kinds={len(report.kinds)} ({', '.join(report.kinds)})")
    print(f"pass_rate={report.pass_rate * 100:.1f}%")
    if report.generated_questions:
        print(
            f"generated_questions={report.generated_questions} "
            f"question_types={report.question_type_count} "
            f"grounded_question_rate={report.grounded_question_rate * 100:.1f}%"
        )
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-pass-rate", type=float, default=0.0)
    parser.add_argument("--min-grounded-question-rate", type=float, default=0.0)
    parser.add_argument("--min-question-types", type=int, default=0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    min_pass_rate = cast("float", args.min_pass_rate)
    min_grounded_question_rate = cast("float", args.min_grounded_question_rate)
    min_question_types = cast("int", args.min_question_types)
    if not 0 <= min_pass_rate <= 1:
        parser.error("--min-pass-rate must be between 0 and 1")
    if not 0 <= min_grounded_question_rate <= 1:
        parser.error("--min-grounded-question-rate must be between 0 and 1")
    if min_question_types < 0:
        parser.error("--min-question-types must be non-negative")
    try:
        report = run_benchmark(
            cast("Path", args.armory).expanduser().resolve(),
            load_cases(cast("Path", args.dataset).expanduser().resolve()),
        )
    except (TypeError, ValueError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2
    if cast("bool", args.json):
        print(json.dumps(asdict(report), indent=2))
    else:
        print_text_report(report)
    if (
        report.pass_rate < min_pass_rate
        or report.grounded_question_rate < min_grounded_question_rate
        or len(report.question_types) < min_question_types
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
