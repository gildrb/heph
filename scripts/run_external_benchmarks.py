"""Run deterministic external benchmark suites after materialization.

The runner intentionally does not download or materialize external datasets.
Adapters and public-corpus materializers produce portable local suites first;
this script then executes those local inputs with fixed retrieval parameters and
writes an auditable JSON report.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaistos.armory import storage
from hephaistos.rag import TransformStrategy
from scripts import benchmark_rag, run_benchmark_suite

SCHEMA_VERSION = "external-runner-report-v1"
RUNNER_ID = "scripts.run_external_benchmarks"

_DEFAULT_TOP_K = 5
_DEFAULT_MIN_SCORE = 0.1
_PUBLIC_ACADEMIC_READINESS_REPORT = "readiness_report.json"

_BENCHMARK_TYPES = ("beir", "standard-rag", "heph-native", "public-academic")
_SUPPORTED_DATASETS = {
    "beir": frozenset({"beir/nfcorpus", "beir/scidocs", "beir/trec-covid", "beir/fixture"}),
    "standard-rag": frozenset({"ms-marco", "natural-questions", "fixture-standard-rag"}),
    "public-academic": frozenset({"public-academic"}),
    "heph-native": frozenset({"academic", "heph-native"}),
}

_METRIC_FORMULAS = {
    "hit_rate": (
        "fraction of queries with at least one expected reference retrieved within top-k"
    ),
    "mrr": "mean reciprocal rank of the first retrieved expected reference",
    "expected_recall": (
        "average retrieved expected references divided by total expected references per query"
    ),
    "latency": (
        "retrieval-only wall-clock milliseconds measured per query; aggregate reports the mean"
    ),
}

_RUNTIME_ONLY_FIELDS = (
    "metadata.suite_path",
    "metadata.armory_path",
    "metadata.cases_path",
    "metadata.readiness_report_path",
    "metadata.report_path",
    "benchmarks[].metrics.mean_latency_ms",
    "benchmarks[].metrics.latency.mean_ms",
    "benchmarks[].per_query_results[].latency_ms",
    "benchmarks[].rag_report.mean_latency_ms",
    "benchmarks[].rag_report.results[].elapsed_ms",
    "benchmarks[].native_suite_report.suite",
    "benchmarks[].native_suite_report.report_path",
    "aggregate_metrics.mean_latency_ms",
    "aggregate_metrics.latency.mean_ms",
)

_DETERMINISTIC_FIELDS_COMPARED = (
    "metadata.benchmark_type",
    "metadata.dataset",
    "metadata.fixed_parameters",
    "benchmarks[].metrics.hit_rate",
    "benchmarks[].metrics.mrr",
    "benchmarks[].metrics.expected_recall",
    "benchmarks[].per_query_results[].case_id",
    "benchmarks[].per_query_results[].retrieved",
    "benchmarks[].per_query_results[].hit",
    "benchmarks[].per_query_results[].rank",
)


class RunnerError(Exception):
    """Expected runner failure with a stable code and remediation hint."""

    def __init__(self, code: str, message: str, remediation: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.remediation = remediation


@dataclass(frozen=True, slots=True)
class Thresholds:
    hit_rate: float
    mrr: float
    expected_recall: float


@dataclass(frozen=True, slots=True)
class RunnerParameters:
    top_k: int
    min_score: float
    transform_strategy: TransformStrategy


@dataclass(frozen=True, slots=True)
class ResolvedInputs:
    benchmark_type: str
    dataset: str
    suite_path: Path
    armory_path: Path
    cases_path: Path
    readiness_report_path: Path | None = None


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RunnerError(
            "input_not_found",
            f"could not read {label}: {path}",
            "Provide existing materialized benchmark inputs.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(
            "malformed_input",
            f"{label} contains invalid JSON at line {exc.lineno}: {path}",
            "Fix the JSON file and rerun the benchmark.",
        ) from exc
    if not isinstance(raw, dict):
        raise RunnerError(
            "malformed_input",
            f"{label} must be a JSON object: {path}",
            "Regenerate the benchmark artifact with the approved script.",
        )
    return cast("dict[str, object]", raw)


def _write_json_report(path: Path | None, report: Mapping[str, object]) -> None:
    if path is None:
        return
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rate_thresholds(args: argparse.Namespace) -> Thresholds:
    return Thresholds(
        hit_rate=cast("float", args.min_hit_rate),
        mrr=cast("float", args.min_mrr),
        expected_recall=cast("float", args.min_expected_recall),
    )


def _parameters(args: argparse.Namespace) -> RunnerParameters:
    return RunnerParameters(
        top_k=cast("int", args.top_k),
        min_score=cast("float", args.min_score),
        transform_strategy=TransformStrategy(cast("str", args.strategy)),
    )


def _threshold_payload(thresholds: Thresholds) -> dict[str, float]:
    return {
        "hit_rate": thresholds.hit_rate,
        "mrr": thresholds.mrr,
        "expected_recall": thresholds.expected_recall,
    }


def _validate_cli_values(parameters: RunnerParameters, thresholds: Thresholds) -> None:
    if parameters.top_k <= 0:
        raise RunnerError(
            "invalid_top_k",
            f"--top-k must be positive; got {parameters.top_k}",
            "Pass a positive integer top-k value.",
        )
    if parameters.min_score < 0:
        raise RunnerError(
            "invalid_min_score",
            f"--min-score must be non-negative; got {parameters.min_score}",
            "Pass a non-negative retrieval score threshold.",
        )
    invalid_thresholds = [
        (name, value)
        for name, value in _threshold_payload(thresholds).items()
        if not 0 <= value <= 1
    ]
    if invalid_thresholds:
        name, value = invalid_thresholds[0]
        raise RunnerError(
            "invalid_threshold",
            f"--min-{name.replace('_', '-')} must be between 0 and 1; got {value}",
            "Use metric gates in the inclusive range [0, 1].",
        )


def _validate_dataset(benchmark_type: str, dataset: str) -> None:
    supported = _SUPPORTED_DATASETS[benchmark_type]
    if dataset in supported:
        return
    supported_list = ", ".join(sorted(supported))
    raise RunnerError(
        "unsupported_dataset",
        f"unsupported {benchmark_type} dataset: {dataset}",
        f"Use one of: {supported_list}.",
    )


def _resolve_external_inputs(
    benchmark_type: str,
    dataset: str,
    args: argparse.Namespace,
) -> ResolvedInputs:
    suite_arg = cast("Path | None", args.suite)
    armory_arg = cast("Path | None", args.armory)
    cases_arg = cast("Path | None", args.cases)
    readiness_report_path: Path | None = None

    suite_path = suite_arg.expanduser().resolve() if suite_arg is not None else None
    armory_path = armory_arg.expanduser().resolve() if armory_arg is not None else None
    cases_path = cases_arg.expanduser().resolve() if cases_arg is not None else None

    if benchmark_type == "public-academic" and suite_path is not None:
        readiness_report_path = suite_path / _PUBLIC_ACADEMIC_READINESS_REPORT
        if readiness_report_path.is_file():
            readiness = _read_json_object(
                readiness_report_path,
                label="public-academic readiness report",
            )
            if readiness.get("status") != "passed" or readiness.get("benchmark_ready") is not True:
                raise RunnerError(
                    "public_academic_not_ready",
                    "public-academic readiness report is not benchmark-ready: "
                    f"{readiness_report_path}",
                    "Materialize and validate the public academic corpus before running.",
                )
            if armory_path is None:
                armory_path = _path_from_json_field(
                    readiness,
                    "armory_path",
                    readiness_report_path,
                )
            if cases_path is None:
                generated_files = readiness.get("generated_files")
                if isinstance(generated_files, dict):
                    raw_rag = generated_files.get("rag")
                    if isinstance(raw_rag, str) and raw_rag.strip():
                        cases_path = Path(raw_rag).expanduser().resolve()

    if suite_path is not None:
        if armory_path is None:
            candidate_armory = suite_path / "armory"
            if candidate_armory.is_dir():
                armory_path = candidate_armory.resolve()
        if cases_path is None:
            candidate_cases = suite_path / "rag.jsonl"
            if candidate_cases.is_file():
                cases_path = candidate_cases.resolve()

    if armory_path is None or cases_path is None:
        raise RunnerError(
            "missing_materialized_inputs",
            "external benchmark execution requires local armory and rag.jsonl inputs",
            "Pass --suite containing armory/ and rag.jsonl, or pass --armory and --cases.",
        )
    if suite_path is None:
        suite_path = cases_path.parent.resolve()

    _validate_input_paths(armory_path, cases_path)
    return ResolvedInputs(
        benchmark_type=benchmark_type,
        dataset=dataset,
        suite_path=suite_path,
        armory_path=armory_path,
        cases_path=cases_path,
        readiness_report_path=readiness_report_path,
    )


def _path_from_json_field(
    payload: Mapping[str, object],
    field_name: str,
    source_path: Path,
) -> Path:
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RunnerError(
            "malformed_input",
            f"{source_path} is missing string field {field_name!r}",
            "Regenerate the readiness report with the public academic case generator.",
        )
    return Path(raw_value).expanduser().resolve()


def _validate_input_paths(armory_path: Path, cases_path: Path) -> None:
    if not armory_path.is_dir():
        raise RunnerError(
            "input_not_found",
            f"armory path does not exist or is not a directory: {armory_path}",
            "Pass a materialized Hephaistos armory path.",
        )
    materials_dir = armory_path / storage.MATERIALS_DIR
    if not materials_dir.is_dir():
        raise RunnerError(
            "missing_materials",
            f"armory is missing a materials directory: {materials_dir}",
            "Use adapter or corpus materialization output that contains materials/.",
        )
    if not cases_path.is_file():
        raise RunnerError(
            "input_not_found",
            f"benchmark cases file does not exist: {cases_path}",
            "Pass a generated rag.jsonl file.",
        )


def _load_and_validate_cases(
    cases_path: Path,
    armory_path: Path,
    *,
    default_top_k: int,
) -> list[benchmark_rag.BenchmarkCase]:
    _validate_raw_case_fields(cases_path)
    try:
        cases = benchmark_rag.load_cases(cases_path)
    except (OSError, TypeError, ValueError) as exc:
        raise RunnerError(
            "invalid_cases",
            f"could not load benchmark cases: {exc}",
            "Regenerate rag.jsonl with an approved adapter or fix the case schema.",
        ) from exc
    if not cases:
        raise RunnerError(
            "empty_cases",
            "benchmark cases file does not contain any cases",
            "Provide at least one query with positive expected references.",
        )
    for case in cases:
        case_top_k = case.top_k if case.top_k is not None else default_top_k
        if case_top_k <= 0:
            raise RunnerError(
                "invalid_top_k",
                f"case {case.case_id} has malformed top_k: {case_top_k}",
                "Use positive top-k values in case files.",
            )
        if len(set(case.expected)) != len(case.expected):
            raise RunnerError(
                "duplicate_expected_references",
                f"case {case.case_id} contains duplicate expected references",
                "Deduplicate expected references for each query.",
            )
        if not case.expected:
            raise RunnerError(
                "no_positive_references",
                f"case {case.case_id} has no positive expected references",
                "Provide at least one expected material reference for each query.",
            )
        for reference in (*case.expected, *case.forbidden_before_expected):
            _validate_material_reference(case.case_id, reference, armory_path)
    return cases


def _validate_raw_case_fields(cases_path: Path) -> None:
    for index, raw_case in enumerate(_raw_case_objects(cases_path), start=1):
        raw_top_k = raw_case.get("top_k")
        if "top_k" in raw_case and not isinstance(raw_top_k, int):
            raise RunnerError(
                "invalid_top_k",
                f"case {index} has malformed top_k: {raw_top_k!r}",
                "Use positive integer top-k values in case files.",
            )
        raw_expected = raw_case.get("expected")
        if isinstance(raw_expected, list) and not raw_expected:
            raise RunnerError(
                "no_positive_references",
                f"case {index} has no positive expected references",
                "Provide at least one expected material reference for each query.",
            )


def _raw_case_objects(cases_path: Path) -> list[dict[str, object]]:
    try:
        text = cases_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerError(
            "input_not_found",
            f"could not read benchmark cases: {cases_path}",
            "Pass a generated rag.jsonl file.",
        ) from exc
    try:
        if cases_path.suffix == ".jsonl":
            raw_payload: object = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            raw_payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RunnerError(
            "malformed_input",
            f"benchmark cases contain invalid JSON at line {exc.lineno}: {cases_path}",
            "Regenerate rag.jsonl with an approved adapter or fix the JSON syntax.",
        ) from exc
    raw_cases = raw_payload.get("cases") if isinstance(raw_payload, dict) else raw_payload
    if not isinstance(raw_cases, list):
        raise RunnerError(
            "invalid_cases",
            "benchmark cases must be a JSON list or an object with a cases list",
            "Regenerate rag.jsonl with an approved adapter or fix the case schema.",
        )
    cases: list[dict[str, object]] = []
    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise RunnerError(
                "invalid_cases",
                f"case {index} must be a JSON object",
                "Regenerate rag.jsonl with an approved adapter or fix the case schema.",
            )
        cases.append(cast("dict[str, object]", raw_case))
    return cases


def _validate_material_reference(case_id: str, reference: str, armory_path: Path) -> None:
    source = reference.split("#", 1)[0]
    source_path = Path(source)
    if (
        source_path.is_absolute()
        or not source_path.parts
        or source_path.parts[0] != storage.MATERIALS_DIR
        or any(part in ("", ".", "..") for part in source_path.parts)
    ):
        raise RunnerError(
            "invalid_reference",
            f"case {case_id} has unsafe material reference: {reference}",
            "Use stable relative materials/... references generated by adapters.",
        )
    materials_root = (armory_path / storage.MATERIALS_DIR).resolve()
    material_path = (armory_path / source_path).resolve()
    try:
        material_path.relative_to(materials_root)
    except ValueError as exc:
        raise RunnerError(
            "invalid_reference",
            f"case {case_id} reference escapes materials directory: {reference}",
            "Use stable relative materials/... references generated by adapters.",
        ) from exc
    if not material_path.is_file():
        raise RunnerError(
            "missing_material_file",
            f"case {case_id} references missing material: {reference}",
            "Regenerate the benchmark suite or materialize the missing source file.",
        )


def _material_file_count(armory_path: Path) -> int:
    materials_dir = armory_path / storage.MATERIALS_DIR
    return sum(1 for path in materials_dir.rglob("*") if path.is_file())


def _run_rag_flow(
    inputs: ResolvedInputs,
    parameters: RunnerParameters,
    thresholds: Thresholds,
    *,
    validate_reproducibility: bool,
    report_path: Path | None,
) -> tuple[dict[str, object], int]:
    cases = _load_and_validate_cases(
        inputs.cases_path,
        inputs.armory_path,
        default_top_k=parameters.top_k,
    )
    warnings = _input_warnings(inputs.armory_path, parameters.top_k)
    first_report = benchmark_rag.run_benchmark(
        inputs.armory_path,
        cases,
        top_k=parameters.top_k,
        min_score=parameters.min_score,
        transform_strategy=parameters.transform_strategy,
    )
    benchmark_payload = _rag_benchmark_payload(inputs, first_report)
    metrics = _metrics_from_rag_report(first_report)
    threshold_failures = _threshold_failures(metrics, thresholds)
    reproducibility = _skipped_reproducibility()

    if validate_reproducibility:
        second_report = benchmark_rag.run_benchmark(
            inputs.armory_path,
            cases,
            top_k=parameters.top_k,
            min_score=parameters.min_score,
            transform_strategy=parameters.transform_strategy,
        )
        reproducibility = _rag_reproducibility(first_report, second_report)

    status, exit_code = _status_and_exit_code(threshold_failures, reproducibility)
    report = _base_report(
        status=status,
        metadata=_metadata(
            inputs.benchmark_type,
            inputs.dataset,
            parameters,
            suite_path=inputs.suite_path,
            armory_path=inputs.armory_path,
            cases_path=inputs.cases_path,
            readiness_report_path=inputs.readiness_report_path,
            report_path=report_path,
        ),
        benchmarks=[benchmark_payload],
        aggregate_metrics=metrics,
        thresholds=thresholds,
        threshold_failures=threshold_failures,
        warnings=warnings,
        errors=[],
        reproducibility=reproducibility,
    )
    return report, exit_code


def _input_warnings(armory_path: Path, top_k: int) -> list[str]:
    material_count = _material_file_count(armory_path)
    if top_k > material_count:
        return [
            f"top_k={top_k} is larger than material file count={material_count}; "
            "retrieval will return at most the available local chunks"
        ]
    return []


def _rag_benchmark_payload(
    inputs: ResolvedInputs,
    report: benchmark_rag.BenchmarkReport,
) -> dict[str, object]:
    return {
        "id": f"{inputs.benchmark_type}:{inputs.dataset}",
        "benchmark_type": inputs.benchmark_type,
        "dataset": inputs.dataset,
        "status": "success",
        "metrics": _metrics_from_rag_report(report),
        "per_query_results": [_case_result_payload(result) for result in report.results],
        "rag_report": asdict(report),
    }


def _metrics_from_rag_report(report: benchmark_rag.BenchmarkReport) -> dict[str, object]:
    return {
        "hit_rate": report.hit_rate,
        "mrr": report.mean_reciprocal_rank,
        "expected_recall": report.mean_expected_recall,
        "forbidden_before_expected_avoidance": report.forbidden_before_expected_avoidance,
        "mean_latency_ms": report.mean_latency_ms,
        "latency": {
            "mean_ms": report.mean_latency_ms,
            "scope": "retrieval_only_per_query",
            "unit": "milliseconds",
        },
    }


def _case_result_payload(result: benchmark_rag.CaseResult) -> dict[str, object]:
    reciprocal_rank = 0.0 if result.rank is None else 1 / result.rank
    return {
        "case_id": result.case_id,
        "query": result.query,
        "expected": list(result.expected),
        "forbidden_before_expected": list(result.forbidden_before_expected),
        "retrieved": list(result.retrieved),
        "hit": result.hit,
        "rank": result.rank,
        "reciprocal_rank": reciprocal_rank,
        "expected_recall": result.recall,
        "first_forbidden_rank": result.first_forbidden_rank,
        "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
        "latency_ms": result.elapsed_ms,
    }


def _threshold_failures(
    metrics: Mapping[str, object],
    thresholds: Thresholds,
) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    for metric_name, minimum in _threshold_payload(thresholds).items():
        raw_actual = metrics.get(metric_name)
        actual = raw_actual if isinstance(raw_actual, int | float) else 0.0
        if actual < minimum:
            failures.append(
                {
                    "metric": metric_name,
                    "minimum": minimum,
                    "actual": float(actual),
                }
            )
    return failures


def _rag_reproducibility(
    first_report: benchmark_rag.BenchmarkReport,
    second_report: benchmark_rag.BenchmarkReport,
) -> dict[str, object]:
    first_projection = _rag_reproducibility_projection(first_report)
    second_projection = _rag_reproducibility_projection(second_report)
    mismatches = []
    if first_projection != second_projection:
        mismatches.append(
            {
                "field": "rag_deterministic_projection",
                "first": first_projection,
                "second": second_projection,
            }
        )
    return _reproducibility_payload(
        enabled=True,
        status="failed" if mismatches else "passed",
        mismatches=mismatches,
    )


def _rag_reproducibility_projection(
    report: benchmark_rag.BenchmarkReport,
) -> dict[str, object]:
    return {
        "cases": report.cases,
        "domains": list(report.domains),
        "tasks": list(report.tasks),
        "top_k": report.top_k,
        "min_score": report.min_score,
        "transform_strategy": report.transform_strategy,
        "metrics": {
            "hit_rate": report.hit_rate,
            "mrr": report.mean_reciprocal_rank,
            "expected_recall": report.mean_expected_recall,
            "forbidden_before_expected_avoidance": report.forbidden_before_expected_avoidance,
        },
        "results": [
            {
                "case_id": result.case_id,
                "expected": list(result.expected),
                "forbidden_before_expected": list(result.forbidden_before_expected),
                "retrieved": list(result.retrieved),
                "hit": result.hit,
                "rank": result.rank,
                "first_forbidden_rank": result.first_forbidden_rank,
                "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
                "expected_recall": result.recall,
            }
            for result in report.results
        ],
    }


def _run_native_flow(
    dataset: str,
    args: argparse.Namespace,
    thresholds: Thresholds,
    parameters: RunnerParameters,
    *,
    validate_reproducibility: bool,
    report_path: Path | None,
) -> tuple[dict[str, object], int]:
    raw_suite = cast("Path | None", args.suite)
    suite_path = (
        raw_suite.expanduser().resolve()
        if raw_suite is not None
        else run_benchmark_suite.DEFAULT_SUITE.resolve()
    )
    if not suite_path.exists():
        raise RunnerError(
            "input_not_found",
            f"native benchmark suite path does not exist: {suite_path}",
            "Pass --suite pointing to an existing Hephaistos benchmark suite.",
        )

    native_status, native_report = _run_native_suite_once(suite_path, thresholds)
    benchmark_payload = _native_benchmark_payload(dataset, native_status, native_report)
    metrics = _metrics_from_native_report(native_report)
    threshold_failures = _threshold_failures(metrics, thresholds)
    if native_status != 0 and not threshold_failures:
        threshold_failures.append(
            {
                "metric": "heph_native_suite",
                "minimum": 0.0,
                "actual": float(native_status),
                "message": "native suite reported a non-zero status",
            }
        )
    reproducibility = _skipped_reproducibility()
    if validate_reproducibility:
        second_status, second_report = _run_native_suite_once(suite_path, thresholds)
        reproducibility = _native_reproducibility(
            native_status,
            native_report,
            second_status,
            second_report,
        )
    status, exit_code = _status_and_exit_code(threshold_failures, reproducibility)
    report = _base_report(
        status=status,
        metadata=_metadata(
            "heph-native",
            dataset,
            parameters,
            suite_path=suite_path,
            armory_path=None,
            cases_path=None,
            readiness_report_path=None,
            report_path=report_path,
        ),
        benchmarks=[benchmark_payload],
        aggregate_metrics=metrics,
        thresholds=thresholds,
        threshold_failures=threshold_failures,
        warnings=[],
        errors=[],
        reproducibility=reproducibility,
    )
    return report, exit_code


def _run_native_suite_once(
    suite_path: Path,
    thresholds: Thresholds,
) -> tuple[int, dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="heph-native-bench-") as tmp:
        native_report_path = Path(tmp) / "native-suite.json"
        status = run_benchmark_suite.run_suite(
            suite_path,
            rag_hit_rate=thresholds.hit_rate,
            rag_mrr=thresholds.mrr,
            rag_expected_recall=thresholds.expected_recall,
            report_path=native_report_path,
        )
        native_report = _read_json_object(native_report_path, label="native benchmark report")
    return status, native_report


def _native_benchmark_payload(
    dataset: str,
    native_status: int,
    native_report: Mapping[str, object],
) -> dict[str, object]:
    return {
        "id": f"heph-native:{dataset}",
        "benchmark_type": "heph-native",
        "dataset": dataset,
        "status": "success" if native_status == 0 else "threshold_failed",
        "metrics": _metrics_from_native_report(native_report),
        "native_suite_report": native_report,
    }


def _metrics_from_native_report(native_report: Mapping[str, object]) -> dict[str, object]:
    rag = native_report.get("rag")
    if not isinstance(rag, dict):
        return {
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "mean_latency_ms": 0.0,
            "latency": {
                "mean_ms": 0.0,
                "scope": "native_suite_rag_retrieval",
                "unit": "milliseconds",
            },
        }
    return {
        "hit_rate": _number_field(rag, "hit_rate"),
        "mrr": _number_field(rag, "mean_reciprocal_rank"),
        "expected_recall": _number_field(rag, "mean_expected_recall"),
        "mean_latency_ms": _number_field(rag, "mean_latency_ms"),
        "latency": {
            "mean_ms": _number_field(rag, "mean_latency_ms"),
            "scope": "native_suite_rag_retrieval",
            "unit": "milliseconds",
        },
    }


def _number_field(payload: Mapping[object, object], field_name: str) -> float:
    value = payload.get(field_name)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _native_reproducibility(
    first_status: int,
    first_report: Mapping[str, object],
    second_status: int,
    second_report: Mapping[str, object],
) -> dict[str, object]:
    first_projection = {
        "status": first_status,
        "report": _strip_runtime_fields(first_report),
    }
    second_projection = {
        "status": second_status,
        "report": _strip_runtime_fields(second_report),
    }
    mismatches = []
    if first_projection != second_projection:
        mismatches.append(
            {
                "field": "native_suite_deterministic_projection",
                "first": first_projection,
                "second": second_projection,
            }
        )
    return _reproducibility_payload(
        enabled=True,
        status="failed" if mismatches else "passed",
        mismatches=mismatches,
    )


def _strip_runtime_fields(value: object, *, key_name: str = "") -> object:
    if key_name in {
        "armory_path",
        "cases_path",
        "elapsed_ms",
        "latency_ms",
        "mean_latency_ms",
        "mean_ms",
        "readiness_report_path",
        "report_path",
        "suite",
        "suite_path",
    }:
        return None
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for raw_key, raw_child in sorted(value.items(), key=lambda item: str(item[0])):
            if not isinstance(raw_key, str):
                continue
            if raw_key in {
                "armory_path",
                "cases_path",
                "elapsed_ms",
                "latency_ms",
                "mean_latency_ms",
                "mean_ms",
                "readiness_report_path",
                "report_path",
                "suite",
                "suite_path",
            }:
                continue
            normalized[raw_key] = _strip_runtime_fields(raw_child, key_name=raw_key)
        return normalized
    if isinstance(value, list):
        return [_strip_runtime_fields(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_runtime_fields(item) for item in value]
    return value


def deterministic_report_projection(report: Mapping[str, object]) -> object:
    """Return report content with enumerated runtime-only fields removed."""
    return _strip_runtime_fields(report)


def _status_and_exit_code(
    threshold_failures: Sequence[Mapping[str, object]],
    reproducibility: Mapping[str, object],
) -> tuple[str, int]:
    if threshold_failures:
        return "threshold_failed", 1
    if reproducibility.get("status") == "failed":
        return "reproducibility_failed", 1
    return "success", 0


def _metadata(
    benchmark_type: str,
    dataset: str,
    parameters: RunnerParameters,
    *,
    suite_path: Path,
    armory_path: Path | None,
    cases_path: Path | None,
    readiness_report_path: Path | None,
    report_path: Path | None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "runner": RUNNER_ID,
        "benchmark_type": benchmark_type,
        "dataset": dataset,
        "suite_path": str(suite_path),
        "fixed_parameters": {
            "top_k": parameters.top_k,
            "min_score": parameters.min_score,
            "transform_strategy": parameters.transform_strategy.value,
            "query_order": "case-file-order",
            "result_order": "retrieval-rank-order",
            "random_seed": 0,
            "randomness": "not-used",
            "network_access": "disabled-after-materialization",
        },
        "metric_formulas": dict(_METRIC_FORMULAS),
        "latency_scope": _METRIC_FORMULAS["latency"],
        "timestamp_policy": "no wall-clock timestamp is included in deterministic reports",
        "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
    }
    if armory_path is not None:
        metadata["armory_path"] = str(armory_path)
    if cases_path is not None:
        metadata["cases_path"] = str(cases_path)
    if readiness_report_path is not None:
        metadata["readiness_report_path"] = str(readiness_report_path.resolve())
    if report_path is not None:
        metadata["report_path"] = str(report_path.expanduser().resolve())
    return metadata


def _base_report(
    *,
    status: str,
    metadata: dict[str, object],
    benchmarks: list[dict[str, object]],
    aggregate_metrics: dict[str, object],
    thresholds: Thresholds,
    threshold_failures: list[dict[str, object]],
    warnings: list[str],
    errors: list[dict[str, object]],
    reproducibility: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_id": _report_id(metadata),
        "status": status,
        "metadata": metadata,
        "benchmarks": benchmarks,
        "aggregate_metrics": aggregate_metrics,
        "thresholds": _threshold_payload(thresholds),
        "threshold_failures": threshold_failures,
        "warnings": warnings,
        "errors": errors,
        "reproducibility": reproducibility,
    }


def _report_id(metadata: Mapping[str, object]) -> str:
    raw_benchmark_type = metadata.get("benchmark_type")
    raw_dataset = metadata.get("dataset")
    benchmark_type = raw_benchmark_type if isinstance(raw_benchmark_type, str) else "unknown"
    dataset = raw_dataset if isinstance(raw_dataset, str) else "unknown"
    return f"{benchmark_type}:{dataset}"


def _skipped_reproducibility() -> dict[str, object]:
    return _reproducibility_payload(enabled=False, status="skipped", mismatches=[])


def _reproducibility_payload(
    *,
    enabled: bool,
    status: str,
    mismatches: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "enabled": enabled,
        "status": status,
        "deterministic_fields_compared": list(_DETERMINISTIC_FIELDS_COMPARED),
        "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
        "mismatches": mismatches,
    }


def _error_report(
    benchmark_type: str,
    dataset: str,
    thresholds: Thresholds,
    parameters: RunnerParameters,
    report_path: Path | None,
    error: RunnerError,
) -> dict[str, object]:
    suite_path = Path()
    return _base_report(
        status="error",
        metadata={
            "runner": RUNNER_ID,
            "benchmark_type": benchmark_type,
            "dataset": dataset,
            "suite_path": str(suite_path),
            "fixed_parameters": {
                "top_k": parameters.top_k,
                "min_score": parameters.min_score,
                "transform_strategy": parameters.transform_strategy.value,
                "query_order": "case-file-order",
                "result_order": "retrieval-rank-order",
                "random_seed": 0,
                "randomness": "not-used",
                "network_access": "disabled-after-materialization",
            },
            "metric_formulas": dict(_METRIC_FORMULAS),
            "latency_scope": _METRIC_FORMULAS["latency"],
            "timestamp_policy": "no wall-clock timestamp is included in deterministic reports",
            "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
            **(
                {"report_path": str(report_path.expanduser().resolve())}
                if report_path is not None
                else {}
            ),
        },
        benchmarks=[],
        aggregate_metrics={
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "mean_latency_ms": 0.0,
            "latency": {
                "mean_ms": 0.0,
                "scope": "not_executed",
                "unit": "milliseconds",
            },
        },
        thresholds=thresholds,
        threshold_failures=[],
        warnings=[],
        errors=[
            {
                "code": error.code,
                "message": error.message,
                "remediation": error.remediation,
            }
        ],
        reproducibility=_skipped_reproducibility(),
    )


def _print_status(report: Mapping[str, object], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    status = report.get("status")
    metadata = report.get("metadata")
    benchmark_type = ""
    dataset = ""
    if isinstance(metadata, dict):
        raw_benchmark_type = metadata.get("benchmark_type")
        raw_dataset = metadata.get("dataset")
        benchmark_type = raw_benchmark_type if isinstance(raw_benchmark_type, str) else ""
        dataset = raw_dataset if isinstance(raw_dataset, str) else ""
    if status == "error":
        errors = report.get("errors")
        message = "external benchmark failed"
        code = "unknown_error"
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            raw_code = errors[0].get("code")
            raw_message = errors[0].get("message")
            if isinstance(raw_code, str):
                code = raw_code
            if isinstance(raw_message, str):
                message = raw_message
        print(f"external benchmark error [{code}]: {message}", file=stream)
        return
    metrics = report.get("aggregate_metrics")
    hit_rate = mrr = expected_recall = 0.0
    if isinstance(metrics, dict):
        hit_rate = _number_field(metrics, "hit_rate")
        mrr = _number_field(metrics, "mrr")
        expected_recall = _number_field(metrics, "expected_recall")
    print(
        "external benchmark "
        f"{status}: type={benchmark_type} dataset={dataset} "
        f"hit_rate={hit_rate:.3f} mrr={mrr:.3f} expected_recall={expected_recall:.3f}",
        file=stream,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "benchmark_type",
        choices=_BENCHMARK_TYPES,
        help="Benchmark flow to execute against already materialized local inputs",
    )
    parser.add_argument(
        "dataset",
        help=("Dataset identifier, e.g. beir/nfcorpus, ms-marco, public-academic, or academic"),
    )
    parser.add_argument(
        "--suite",
        type=Path,
        help="Materialized benchmark suite directory containing armory/ and rag.jsonl",
    )
    parser.add_argument("--armory", type=Path, help="Materialized Hephaistos armory path")
    parser.add_argument("--cases", type=Path, help="Generated rag.jsonl benchmark cases")
    parser.add_argument("--top-k", type=int, default=_DEFAULT_TOP_K)
    parser.add_argument("--min-score", type=float, default=_DEFAULT_MIN_SCORE)
    parser.add_argument(
        "--strategy",
        choices=[strategy.value for strategy in TransformStrategy],
        default=TransformStrategy.IDENTITY.value,
        help="RAG query transformation strategy",
    )
    parser.add_argument(
        "--validate-reproducibility",
        action="store_true",
        help="Run equivalent inputs twice and compare deterministic fields",
    )
    parser.add_argument("--min-hit-rate", type=float, default=0.0)
    parser.add_argument("--min-mrr", type=float, default=0.0)
    parser.add_argument("--min-expected-recall", type=float, default=0.0)
    parser.add_argument("--json-report", type=Path, help="Write a versioned JSON report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    benchmark_type = cast("str", args.benchmark_type)
    dataset = cast("str", args.dataset)
    report_path = cast("Path | None", args.json_report)
    thresholds = _rate_thresholds(args)
    parameters = _parameters(args)

    try:
        _validate_cli_values(parameters, thresholds)
        _validate_dataset(benchmark_type, dataset)
        if benchmark_type == "heph-native":
            report, status = _run_native_flow(
                dataset,
                args,
                thresholds,
                parameters,
                validate_reproducibility=cast("bool", args.validate_reproducibility),
                report_path=report_path,
            )
        else:
            inputs = _resolve_external_inputs(benchmark_type, dataset, args)
            report, status = _run_rag_flow(
                inputs,
                parameters,
                thresholds,
                validate_reproducibility=cast("bool", args.validate_reproducibility),
                report_path=report_path,
            )
    except RunnerError as exc:
        report = _error_report(benchmark_type, dataset, thresholds, parameters, report_path, exc)
        _write_json_report(report_path, report)
        _print_status(report, error=True)
        return 2
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        error = RunnerError(
            "execution_failed",
            f"benchmark execution failed: {exc}",
            "Check local materialized inputs and rerun with a small fixture.",
        )
        report = _error_report(benchmark_type, dataset, thresholds, parameters, report_path, error)
        _write_json_report(report_path, report)
        _print_status(report, error=True)
        return 2

    _write_json_report(report_path, report)
    _print_status(report, error=status != 0)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
