"""Run deterministic external benchmark suites after materialization.

The runner intentionally does not download or materialize external datasets.
Adapters and public-corpus materializers produce portable local suites first;
this script then executes those local inputs with fixed retrieval parameters and
writes an auditable JSON report.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import cast

from armory import storage
from rag import EvidenceReference, RetrievalMode, TransformStrategy
from rag.hybrid import (
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
)
from rag.query_audit import (
    QUERY_AUDIT_SCHEMA_VERSION,
    QUERY_EXCERPT_LIMIT,
    RetrievalAuditConfig,
)
from rag.query_audit import (
    query_class as audit_query_class,
)
from rag.query_audit import (
    query_classification_payload as audit_query_classification_payload,
)
from rag.query_audit import (
    query_excerpt as audit_query_excerpt,
)
from rag.query_audit import (
    retrieval_strategy_payload as audit_retrieval_strategy_payload,
)

from scripts import benchmark_rag, claim_report_envelope, run_benchmark_suite

SCHEMA_VERSION = "external-runner-report-v1"
RUNNER_ID = "scripts.run_external_benchmarks"

_DEFAULT_TOP_K = 5
_DEFAULT_MIN_SCORE = 0.0
_DEFAULT_RETRIEVAL_MODE = RetrievalMode.BM25
_DEFAULT_CANDIDATE_MULTIPLIER = 2
_DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_DEFAULT_REPAIR_MAX_PASSES = 1
_PUBLIC_ACADEMIC_READINESS_REPORT = "readiness_report.json"
_QUERY_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:-]*")
_REPAIR_QUOTED_FRAGMENT_RE = re.compile(r"['\"`][^'\"`]{1,180}['\"`]")
_REPAIR_NOISE_RE = re.compile(
    r"(?i)\b(?:distractor|decoy|irrelevant|unrelated|noise|red\s+herring|ignore)\b"
)
_QUERY_REPAIR_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "which",
        "who",
        "why",
    }
)

_BENCHMARK_TYPES = (
    "beir",
    "mteb",
    "standard-rag",
    "heph-native",
    "public-academic",
    "enterprise-rag",
)
_SUPPORTED_DATASETS = {
    "beir": frozenset({"beir/nfcorpus", "beir/scidocs", "beir/trec-covid", "beir/fixture"}),
    "mteb": frozenset({"mteb/fixture"}),
    "standard-rag": frozenset({"ms-marco", "natural-questions", "fixture-standard-rag"}),
    "public-academic": frozenset({"public-academic"}),
    "heph-native": frozenset({"academic", "heph-native"}),
    "enterprise-rag": frozenset({"enterprise-rag-bench"}),
}
_ORACLE_KEYS = frozenset(
    {
        "answer_key",
        "expected",
        "expected_answer",
        "expected_answers",
        "expected_citations",
        "expected_doc_ids",
        "expected_mark_totals",
        "expected_ordered_topics",
        "expected_past_exam_sources",
        "expected_role",
        "expected_source_ids",
        "expected_sources",
        "expected_text",
        "expected_topics",
        "forbidden_before_expected",
        "forbidden_text",
        "forbidden_topics",
        "gold_answer",
        "gold_answers",
        "gold_references",
        "leaderboard_rows",
        "must_include",
        "must_not_include",
        "qrels",
        "relevance_grades",
    }
)

_METRIC_FORMULAS = {
    "hit_rate": (
        "fraction of queries with at least one expected reference retrieved within top-k"
    ),
    "mrr": "mean reciprocal rank of the first retrieved expected reference",
    "expected_recall": (
        "average retrieved expected references divided by total expected references per query"
    ),
    "precision_at_k": ("average binary precision@k over retrieved expected references per query"),
    "map_at_k": "mean average precision@k over binary expected-reference relevance",
    "ndcg_at_k": "mean normalized discounted cumulative gain@k with binary relevance",
    "graded_ndcg_at_k": (
        "mean normalized discounted cumulative gain@k using supplied relevance grades, "
        "falling back to binary grades when labels are ungraded"
    ),
    "latency": (
        "retrieval-only wall-clock milliseconds measured per query; aggregate reports the mean"
    ),
}

_RUNTIME_ONLY_FIELDS = (
    "metadata.suite_path",
    "metadata.armory_path",
    "metadata.cases_path",
    "metadata.command_invocation",
    "metadata.readiness_report_path",
    "metadata.report_path",
    "claim_envelope.reproducibility.command_invocation",
    "claim_envelope.determinism.projection_sha256",
    "deterministic_projection.sha256",
    "benchmarks[].metrics.mean_latency_ms",
    "benchmarks[].metrics.latency.mean_ms",
    "benchmarks[].per_query_results[].latency_ms",
    "benchmarks[].per_query_results[].retrieval_trace.latency_ms",
    "benchmarks[].repair_analysis.per_query[].passes[].latency_ms",
    "benchmarks[].rag_report.armory_path",
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
    "metadata.fixed_parameters.repair_max_passes",
    "benchmarks[].metrics.hit_rate",
    "benchmarks[].metrics.mrr",
    "benchmarks[].metrics.expected_recall",
    "benchmarks[].metrics.precision_at_k",
    "benchmarks[].metrics.map_at_k",
    "benchmarks[].metrics.ndcg_at_k",
    "benchmarks[].metrics.graded_ndcg_at_k",
    "benchmarks[].metrics.query_count",
    "aggregate_metrics.query_count",
    "benchmarks[].per_query_results[].case_id",
    "benchmarks[].per_query_results[].retrieved",
    "benchmarks[].per_query_results[].hit",
    "benchmarks[].per_query_results[].rank",
    "benchmarks[].per_query_results[].precision_at_k",
    "benchmarks[].per_query_results[].average_precision_at_k",
    "benchmarks[].per_query_results[].ndcg_at_k",
    "benchmarks[].per_query_results[].graded_ndcg_at_k",
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
    retrieval_mode: RetrievalMode
    candidate_multiplier: int
    embedding_model: str | None
    embedding_query_prefix: str
    embedding_document_prefix: str
    rerank_model: str | None
    hybrid_sparse_weight: float
    hybrid_dense_weight: float
    pseudo_feedback_docs: int
    pseudo_feedback_terms: int
    pseudo_feedback_weight: float
    repair_max_passes: int


@dataclass(frozen=True, slots=True)
class RagRun:
    first_report: benchmark_rag.BenchmarkReport
    effective_report: benchmark_rag.BenchmarkReport
    repair_analysis: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class PromptIdentity:
    path: Path
    sha256: str
    title: str
    version: str


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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json_report(path: Path | None, report: Mapping[str, object]) -> None:
    if path is None:
        return
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _float_value(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _rate_thresholds(args: argparse.Namespace) -> Thresholds:
    return Thresholds(
        hit_rate=cast("float", args.min_hit_rate),
        mrr=cast("float", args.min_mrr),
        expected_recall=cast("float", args.min_expected_recall),
    )


def _parameters(args: argparse.Namespace) -> RunnerParameters:
    retrieval_mode = RetrievalMode(cast("str", args.retrieval_mode))
    rerank_model = _optional_cli_string(cast("str | None", args.rerank_model))
    if rerank_model is None and retrieval_mode == RetrievalMode.HYBRID_RERANK:
        rerank_model = (
            _optional_cli_string(os.environ.get("HEPHAION_RERANK_MODEL")) or _DEFAULT_RERANK_MODEL
        )
    return RunnerParameters(
        top_k=cast("int", args.top_k),
        min_score=cast("float", args.min_score),
        transform_strategy=TransformStrategy(cast("str", args.strategy)),
        retrieval_mode=retrieval_mode,
        candidate_multiplier=cast("int", args.candidate_multiplier),
        embedding_model=_optional_cli_string(cast("str | None", args.embedding_model)),
        embedding_query_prefix=cast("str", args.embedding_query_prefix),
        embedding_document_prefix=cast("str", args.embedding_document_prefix),
        rerank_model=rerank_model,
        hybrid_sparse_weight=cast("float", args.hybrid_sparse_weight),
        hybrid_dense_weight=cast("float", args.hybrid_dense_weight),
        pseudo_feedback_docs=cast("int", args.pseudo_feedback_docs),
        pseudo_feedback_terms=cast("int", args.pseudo_feedback_terms),
        pseudo_feedback_weight=cast("float", args.pseudo_feedback_weight),
        repair_max_passes=cast("int", args.repair_max_passes),
    )


def _optional_cli_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


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
    if parameters.candidate_multiplier <= 0:
        raise RunnerError(
            "invalid_candidate_multiplier",
            f"--candidate-multiplier must be positive; got {parameters.candidate_multiplier}",
            "Pass a positive integer candidate multiplier.",
        )
    if parameters.hybrid_sparse_weight < 0 or parameters.hybrid_dense_weight < 0:
        raise RunnerError(
            "invalid_hybrid_weight",
            "--hybrid-sparse-weight and --hybrid-dense-weight must be non-negative",
            "Pass non-negative fusion weights.",
        )
    if parameters.pseudo_feedback_docs <= 0 or parameters.pseudo_feedback_terms <= 0:
        raise RunnerError(
            "invalid_pseudo_feedback_budget",
            "--pseudo-feedback-docs and --pseudo-feedback-terms must be positive",
            "Use positive pseudo-relevance-feedback budgets.",
        )
    if parameters.pseudo_feedback_weight < 0:
        raise RunnerError(
            "invalid_pseudo_feedback_weight",
            "--pseudo-feedback-weight must be non-negative",
            "Pass a non-negative pseudo-relevance-feedback fusion weight.",
        )
    if not 1 <= parameters.repair_max_passes <= 2:
        raise RunnerError(
            "invalid_repair_max_passes",
            f"--repair-max-passes must be 1 or 2; got {parameters.repair_max_passes}",
            "Use 1 for retrieval-only scoring or 2 to enable one audited repair pass.",
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
    if benchmark_type == "mteb" and dataset.startswith("mteb/") and len(dataset) > len("mteb/"):
        return
    supported = _SUPPORTED_DATASETS[benchmark_type]
    if dataset in supported:
        return
    supported_list = ", ".join(sorted(supported))
    raise RunnerError(
        "unsupported_dataset",
        f"unsupported {benchmark_type} dataset: {dataset}",
        f"Use one of: {supported_list}.",
    )


def _prompt_identity(prompt_path: Path | None) -> PromptIdentity | None:
    if prompt_path is None:
        return None
    path = prompt_path.expanduser().resolve()
    if not path.is_file():
        raise RunnerError(
            "prompt_not_found",
            f"benchmark evaluation prompt does not exist: {path}",
            "Pass --prompt pointing to benchmarks/model-evaluation-prompt.md.",
        )
    try:
        content = path.read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RunnerError(
            "malformed_prompt",
            f"benchmark evaluation prompt could not be read as UTF-8: {path}",
            "Use a readable Markdown prompt file.",
        ) from exc
    title, version = _prompt_title_and_version(text, path)
    return PromptIdentity(
        path=path,
        sha256=hashlib.sha256(content).hexdigest(),
        title=title,
        version=version,
    )


def _prompt_title_and_version(text: str, path: Path) -> tuple[str, str]:
    title = path.stem
    version = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped.removeprefix("# ").strip() or title
        if stripped.startswith("Prompt-Version:"):
            version = stripped.removeprefix("Prompt-Version:").strip()
    return title, version


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
            "Pass a materialized Heph armory path.",
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
    prompt_identity: PromptIdentity | None,
    model_label: str,
) -> tuple[dict[str, object], int]:
    cases = _load_and_validate_cases(
        inputs.cases_path,
        inputs.armory_path,
        default_top_k=parameters.top_k,
    )
    warnings = _input_warnings(inputs.armory_path, parameters.top_k)
    rag_run = _run_rag_once(inputs, cases, parameters)
    candidate_report = _candidate_report_for_rerank(inputs, cases, parameters)
    rerank_analysis = (
        _rerank_analysis(parameters, candidate_report, rag_run.first_report)
        if candidate_report is not None
        else None
    )
    benchmark_payload = _rag_benchmark_payload(
        inputs,
        rag_run.effective_report,
        parameters,
        initial_report=rag_run.first_report
        if rag_run.first_report is not rag_run.effective_report
        else None,
        repair_analysis=rag_run.repair_analysis,
        rerank_analysis=rerank_analysis,
    )
    metrics = _metrics_from_rag_report(rag_run.effective_report)
    threshold_failures = _threshold_failures(metrics, thresholds)
    reproducibility = _skipped_reproducibility()

    if validate_reproducibility:
        second_run = _run_rag_once(inputs, cases, parameters)
        reproducibility = _rag_reproducibility(
            rag_run.effective_report,
            second_run.effective_report,
        )

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
            prompt_identity=prompt_identity,
            model_label=model_label,
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


def _run_rag_once(
    inputs: ResolvedInputs,
    cases: Sequence[benchmark_rag.BenchmarkCase],
    parameters: RunnerParameters,
) -> RagRun:
    first_report = _run_rag_benchmark_with_gc_paused(
        inputs.armory_path,
        cases,
        top_k=parameters.top_k,
        min_score=parameters.min_score,
        transform_strategy=parameters.transform_strategy,
        retrieval_mode=parameters.retrieval_mode,
        candidate_multiplier=parameters.candidate_multiplier,
        embed_model=parameters.embedding_model,
        embed_query_prefix=parameters.embedding_query_prefix,
        embed_document_prefix=parameters.embedding_document_prefix,
        rerank_model=parameters.rerank_model,
        hybrid_sparse_weight=parameters.hybrid_sparse_weight,
        hybrid_dense_weight=parameters.hybrid_dense_weight,
        pseudo_feedback_docs=parameters.pseudo_feedback_docs,
        pseudo_feedback_terms=parameters.pseudo_feedback_terms,
        pseudo_feedback_weight=parameters.pseudo_feedback_weight,
        use_case_top_k=False,
    )
    repair_report, repair_queries = _repair_report_for_cases(
        inputs,
        cases,
        parameters,
        first_report,
    )
    effective_report, repair_analysis = _repair_analysis(
        parameters,
        first_report,
        repair_report,
        repair_queries,
    )
    return RagRun(
        first_report=first_report,
        effective_report=effective_report,
        repair_analysis=repair_analysis,
    )


def _candidate_report_for_rerank(
    inputs: ResolvedInputs,
    cases: Sequence[benchmark_rag.BenchmarkCase],
    parameters: RunnerParameters,
) -> benchmark_rag.BenchmarkReport | None:
    if parameters.retrieval_mode != RetrievalMode.HYBRID_RERANK:
        return None
    candidate_budget = parameters.top_k * max(1, parameters.candidate_multiplier)
    return _run_rag_benchmark_with_gc_paused(
        inputs.armory_path,
        cases,
        top_k=candidate_budget,
        min_score=parameters.min_score,
        transform_strategy=parameters.transform_strategy,
        retrieval_mode=RetrievalMode.HYBRID,
        candidate_multiplier=1,
        embed_model=parameters.embedding_model,
        embed_query_prefix=parameters.embedding_query_prefix,
        embed_document_prefix=parameters.embedding_document_prefix,
        rerank_model=None,
        hybrid_sparse_weight=parameters.hybrid_sparse_weight,
        hybrid_dense_weight=parameters.hybrid_dense_weight,
        pseudo_feedback_docs=parameters.pseudo_feedback_docs,
        pseudo_feedback_terms=parameters.pseudo_feedback_terms,
        pseudo_feedback_weight=parameters.pseudo_feedback_weight,
        use_case_top_k=False,
    )


def _run_rag_benchmark_with_gc_paused(
    armory_path: Path,
    cases: Sequence[benchmark_rag.BenchmarkCase],
    *,
    top_k: int,
    min_score: float,
    transform_strategy: TransformStrategy,
    retrieval_mode: RetrievalMode,
    candidate_multiplier: int,
    embed_model: str | None,
    embed_query_prefix: str,
    embed_document_prefix: str,
    rerank_model: str | None,
    hybrid_sparse_weight: float,
    hybrid_dense_weight: float,
    pseudo_feedback_docs: int,
    pseudo_feedback_terms: int,
    pseudo_feedback_weight: float,
    use_case_top_k: bool,
) -> benchmark_rag.BenchmarkReport:
    gc_was_enabled = gc.isenabled()
    if gc_was_enabled:
        gc.disable()
    try:
        return benchmark_rag.run_benchmark(
            armory_path,
            cases,
            top_k=top_k,
            min_score=min_score,
            transform_strategy=transform_strategy,
            retrieval_mode=retrieval_mode,
            candidate_multiplier=candidate_multiplier,
            embed_model=embed_model,
            embed_query_prefix=embed_query_prefix,
            embed_document_prefix=embed_document_prefix,
            rerank_model=rerank_model,
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
            pseudo_feedback_docs=pseudo_feedback_docs,
            pseudo_feedback_terms=pseudo_feedback_terms,
            pseudo_feedback_weight=pseudo_feedback_weight,
            use_case_top_k=use_case_top_k,
        )
    finally:
        if gc_was_enabled:
            gc.enable()


def _repair_report_for_cases(
    inputs: ResolvedInputs,
    cases: Sequence[benchmark_rag.BenchmarkCase],
    parameters: RunnerParameters,
    first_report: benchmark_rag.BenchmarkReport,
) -> tuple[benchmark_rag.BenchmarkReport | None, dict[str, str]]:
    if parameters.repair_max_passes <= 1:
        return None, {}
    first_by_id = {result.case_id: result for result in first_report.results}
    repair_cases: list[benchmark_rag.BenchmarkCase] = []
    repair_queries: dict[str, str] = {}
    for case in cases:
        result = first_by_id.get(case.case_id)
        if result is None or not _result_needs_repair(result):
            continue
        repair_query = _repair_query_text(case.query)
        if not repair_query or repair_query == case.query:
            continue
        repair_cases.append(replace(case, query=repair_query))
        repair_queries[case.case_id] = repair_query
    if not repair_cases:
        return None, repair_queries
    return (
        _run_rag_benchmark_with_gc_paused(
            inputs.armory_path,
            repair_cases,
            top_k=parameters.top_k,
            min_score=parameters.min_score,
            transform_strategy=parameters.transform_strategy,
            retrieval_mode=parameters.retrieval_mode,
            candidate_multiplier=parameters.candidate_multiplier,
            embed_model=parameters.embedding_model,
            embed_query_prefix=parameters.embedding_query_prefix,
            embed_document_prefix=parameters.embedding_document_prefix,
            rerank_model=parameters.rerank_model,
            hybrid_sparse_weight=parameters.hybrid_sparse_weight,
            hybrid_dense_weight=parameters.hybrid_dense_weight,
            pseudo_feedback_docs=parameters.pseudo_feedback_docs,
            pseudo_feedback_terms=parameters.pseudo_feedback_terms,
            pseudo_feedback_weight=parameters.pseudo_feedback_weight,
            use_case_top_k=False,
        ),
        repair_queries,
    )


def _repair_analysis(
    parameters: RunnerParameters,
    first_report: benchmark_rag.BenchmarkReport,
    repair_report: benchmark_rag.BenchmarkReport | None,
    repair_queries: Mapping[str, str],
) -> tuple[benchmark_rag.BenchmarkReport, dict[str, object] | None]:
    if parameters.repair_max_passes <= 1:
        return first_report, None
    repair_by_id = {
        result.case_id: result
        for result in (repair_report.results if repair_report is not None else ())
    }
    diagnostic_effective_results: list[benchmark_rag.CaseResult] = []
    per_query: list[dict[str, object]] = []
    attempted_count = 0
    success_count = 0
    failed_count = 0
    abstention_count = 0
    improved_count = 0

    for result in first_report.results:
        repaired = repair_by_id.get(result.case_id)
        attempted = result.case_id in repair_queries
        effective = result
        used_repair = False
        if repaired is not None and _repair_result_is_better(result, repaired):
            effective = replace(
                repaired,
                query=result.query,
                elapsed_ms=result.elapsed_ms + repaired.elapsed_ms,
            )
            used_repair = True
            improved_count += 1
        if attempted:
            attempted_count += 1
            if used_repair and _result_sufficient(effective):
                success_count += 1
            else:
                failed_count += 1
        if not _result_sufficient(effective):
            abstention_count += 1
        diagnostic_effective_results.append(effective)
        per_query.append(
            _repair_case_payload(
                result,
                repaired,
                effective,
                parameters,
                attempted=attempted,
                used_repair=used_repair,
                repair_query=repair_queries.get(result.case_id),
            )
        )

    diagnostic_effective_report = _report_with_results(first_report, diagnostic_effective_results)
    analysis = {
        "enabled": True,
        "max_passes": parameters.repair_max_passes,
        "policy": "diagnostic_query_cleanup_on_label_scored_weak_evidence",
        "claim_eligible": False,
        "claim_blocking": True,
        "claim_path": "original_retrieval_only",
        "ineligibility_reasons": [
            "repair routing and effective-result selection are label-scored diagnostics"
        ],
        "measurement": {
            "success_metric": "original-question evidence sufficiency after repaired retrieval",
            "oracle_free_routing": False,
            "uses_case_labels_for_routing": True,
            "claim_eligible": False,
        },
        "attempted_count": attempted_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "improved_count": improved_count,
        "abstain_or_clarify_count": abstention_count,
        "fabricated_evidence_ids": [],
        "initial_metrics": _metrics_from_rag_report(first_report),
        "effective_metrics": _metrics_from_rag_report(first_report),
        "diagnostic_effective_metrics": _metrics_from_rag_report(diagnostic_effective_report),
        "per_query": per_query,
    }
    return first_report, analysis


def _report_with_results(
    base_report: benchmark_rag.BenchmarkReport,
    results: Sequence[benchmark_rag.CaseResult],
) -> benchmark_rag.BenchmarkReport:
    total = len(results)
    if total == 0:
        return base_report
    hit_count = sum(1 for result in results if result.hit)
    reciprocal_rank_sum = sum(1 / result.rank for result in results if result.rank is not None)
    recall_sum = sum(result.recall for result in results)
    precision_sum = sum(result.precision_at_k for result in results)
    average_precision_sum = sum(result.average_precision_at_k for result in results)
    ndcg_sum = sum(result.ndcg_at_k for result in results)
    graded_ndcg_sum = sum(result.graded_ndcg_at_k for result in results)
    forbidden_case_count = sum(1 for result in results if result.forbidden_before_expected)
    forbidden_ok_count = sum(
        1
        for result in results
        if result.forbidden_before_expected and result.forbidden_before_expected_ok
    )
    forbidden_avoidance = (
        forbidden_ok_count / forbidden_case_count if forbidden_case_count else 1.0
    )
    latency_sum = sum(result.elapsed_ms for result in results)
    return replace(
        base_report,
        cases=total,
        hit_rate=hit_count / total,
        mean_reciprocal_rank=reciprocal_rank_sum / total,
        mean_expected_recall=recall_sum / total,
        mean_precision_at_k=precision_sum / total,
        mean_average_precision_at_k=average_precision_sum / total,
        mean_ndcg_at_k=ndcg_sum / total,
        mean_graded_ndcg_at_k=graded_ndcg_sum / total,
        forbidden_before_expected_avoidance=forbidden_avoidance,
        mean_latency_ms=latency_sum / total,
        misses=tuple(result.case_id for result in results if not result.hit),
        forbidden_before_expected_failures=tuple(
            result.case_id
            for result in results
            if result.forbidden_before_expected and not result.forbidden_before_expected_ok
        ),
        results=tuple(results),
    )


def _repair_case_payload(
    first_result: benchmark_rag.CaseResult,
    repaired_result: benchmark_rag.CaseResult | None,
    effective_result: benchmark_rag.CaseResult,
    parameters: RunnerParameters,
    *,
    attempted: bool,
    used_repair: bool,
    repair_query: str | None,
) -> dict[str, object]:
    first_stop = _repair_first_pass_stop_reason(first_result, attempted, repair_query)
    passes = [
        _retrieval_pass_payload(
            first_result,
            parameters,
            pass_number=1,
            query=first_result.query,
            stop_reason=first_stop,
        )
    ]
    if repaired_result is not None:
        passes.append(
            _retrieval_pass_payload(
                repaired_result,
                parameters,
                pass_number=2,
                query=repaired_result.query,
                stop_reason=_repair_second_pass_stop_reason(repaired_result),
            )
        )
    final_refs = list(effective_result.retrieved[: parameters.top_k])
    return {
        "case_id": first_result.case_id,
        "original_query_excerpt": _query_excerpt(first_result.query),
        "query_classification": _query_classification_payload(first_result.query, parameters),
        "attempted": attempted,
        "used_repair": used_repair,
        "pass_count": len(passes),
        "initial_sufficiency": _sufficiency_label(first_result),
        "final_sufficiency": _sufficiency_label(effective_result),
        "successful": attempted and used_repair and _result_sufficient(effective_result),
        "abstain_or_clarify": not _result_sufficient(effective_result),
        "fabricated_evidence_ids": [],
        "final_evidence_refs": final_refs,
        "final_cited_evidence_subset_of_retrieved": True,
        "repair_query_excerpt": _query_excerpt(repair_query) if repair_query else None,
        "passes": passes,
    }


def _repair_first_pass_stop_reason(
    result: benchmark_rag.CaseResult,
    attempted: bool,
    repair_query: str | None,
) -> str:
    if _result_sufficient(result):
        return "sufficient_evidence"
    if attempted:
        return "retry_with_cleaned_query"
    if repair_query is None:
        return "no_repair_query_generated"
    return "repair_not_attempted"


def _repair_second_pass_stop_reason(result: benchmark_rag.CaseResult) -> str:
    if _result_sufficient(result):
        return "sufficient_evidence_after_repair"
    return "abstain_or_clarify"


def _repair_query_text(query: str) -> str:
    normalized = " ".join(query.split())
    cleaned = _REPAIR_QUOTED_FRAGMENT_RE.sub(" ", normalized)
    cleaned = _REPAIR_NOISE_RE.sub(" ", cleaned)
    tokens = _QUERY_TOKEN_RE.findall(cleaned)
    if len(tokens) > 24:
        tokens = [token for token in tokens if token.casefold() not in _QUERY_REPAIR_STOPWORDS]
    repaired = " ".join(tokens).strip()
    return repaired or normalized


def _result_needs_repair(result: benchmark_rag.CaseResult) -> bool:
    return not _result_sufficient(result)


def _repair_result_is_better(
    first_result: benchmark_rag.CaseResult,
    repaired_result: benchmark_rag.CaseResult,
) -> bool:
    if not repaired_result.forbidden_before_expected_ok:
        return False
    if _result_sufficient(repaired_result) and not _result_sufficient(first_result):
        return True
    if repaired_result.recall > first_result.recall:
        return True
    if first_result.rank is None:
        return repaired_result.rank is not None
    return repaired_result.rank is not None and repaired_result.rank < first_result.rank


def _result_sufficient(result: benchmark_rag.CaseResult) -> bool:
    return _sufficiency_label(result) == "sufficient"


def _sufficiency_label(result: benchmark_rag.CaseResult) -> str:
    if not result.forbidden_before_expected_ok:
        return "conflicted"
    if result.recall >= 1.0 and result.hit:
        return "sufficient"
    if result.hit or result.recall > 0:
        return "partial"
    if result.retrieved:
        return "insufficient"
    return "no_evidence"


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
    parameters: RunnerParameters,
    *,
    initial_report: benchmark_rag.BenchmarkReport | None = None,
    repair_analysis: Mapping[str, object] | None = None,
    rerank_analysis: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": f"{inputs.benchmark_type}:{inputs.dataset}",
        "benchmark_type": inputs.benchmark_type,
        "dataset": inputs.dataset,
        "status": "success",
        "metrics": _metrics_from_rag_report(report),
        "query_classification": _query_classification_summary(report.results, parameters),
        "per_query_results": [
            _case_result_payload(result, parameters) for result in report.results
        ],
        "miss_diagnostics": _miss_diagnostics(report),
        "rag_report": _claim_safe_rag_report(report),
    }
    if initial_report is not None:
        payload["initial_metrics"] = _metrics_from_rag_report(initial_report)
    if repair_analysis is not None:
        payload["repair_analysis"] = dict(repair_analysis)
    if rerank_analysis is not None:
        payload["rerank_analysis"] = dict(rerank_analysis)
    return payload


def _miss_diagnostics(report: benchmark_rag.BenchmarkReport) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for result in report.results:
        if result.hit:
            continue
        bucket = "no_retrieved_candidates" if not result.retrieved else "top_k_or_ranking_miss"
        diagnostics.append(
            {
                "case_id": result.case_id,
                "bucket": bucket,
                "query": result.query,
                "expected_count": len(result.expected),
                "retrieved_count": len(result.retrieved),
                "top_retrieved": list(result.retrieved[:3]),
            }
        )
    return diagnostics[:30]


def _rerank_analysis(
    parameters: RunnerParameters,
    candidate_report: benchmark_rag.BenchmarkReport,
    post_report: benchmark_rag.BenchmarkReport,
) -> dict[str, object]:
    top_k = parameters.top_k
    candidate_budget = top_k * max(1, parameters.candidate_multiplier)
    candidate_by_id = {result.case_id: result for result in candidate_report.results}
    per_query = [
        _rerank_case_analysis(candidate_by_id.get(result.case_id), result, top_k=top_k)
        for result in post_report.results
    ]
    outcomes = {
        "win": sum(1 for row in per_query if row.get("rerank_outcome") == "win"),
        "loss": sum(1 for row in per_query if row.get("rerank_outcome") == "loss"),
        "tie": sum(1 for row in per_query if row.get("rerank_outcome") == "tie"),
    }
    harm_cases = [row for row in per_query if row.get("harm_bucket") is not None]
    candidate_metrics = _metrics_from_rag_report(candidate_report)
    pre_metrics = _rerank_pre_metrics(per_query)
    post_metrics = _metrics_from_rag_report(post_report)
    reranker_state = _reranker_state(parameters, post_report)
    return {
        "top_k": top_k,
        "candidate_multiplier": parameters.candidate_multiplier,
        "candidate_budget": candidate_budget,
        "candidate_generation_mode": RetrievalMode.HYBRID.value,
        "final_rerank_mode": RetrievalMode.HYBRID_RERANK.value,
        "candidate_metrics": candidate_metrics,
        "pre_rerank_metrics_at_k": pre_metrics,
        "post_rerank_metrics": post_metrics,
        "recall_at_candidate_budget": candidate_report.mean_expected_recall,
        "recall_at_k": post_report.mean_expected_recall,
        "configuration_selection": _rerank_configuration_selection(
            parameters,
            candidate_report,
            post_report,
            reranker_state,
            pre_metrics,
            post_metrics,
            harm_cases,
        ),
        "win_loss_tie": outcomes,
        "harm": {
            "computed": True,
            "case_count": len(harm_cases),
            "cases": harm_cases[:30],
        },
        "bottleneck_counts": _rerank_bottleneck_counts(per_query),
        "source_family_confusion": _rerank_source_family_confusion(per_query),
        "boost_diagnostics": _rerank_boost_diagnostics(per_query),
        "reranker_state": reranker_state,
        "per_query": per_query,
    }


def _rerank_case_analysis(
    candidate_result: benchmark_rag.CaseResult | None,
    post_result: benchmark_rag.CaseResult,
    *,
    top_k: int,
) -> dict[str, object]:
    candidate_retrieved = list(candidate_result.retrieved) if candidate_result else []
    final_retrieved = list(post_result.retrieved)
    pre_rank_at_k = (
        _first_expected_ref_rank(candidate_result.expected, candidate_retrieved[:top_k])
        if candidate_result
        else None
    )
    candidate_rank = candidate_result.rank if candidate_result else None
    pre_rank = pre_rank_at_k
    post_rank = post_result.rank
    harm_bucket = _rerank_harm_bucket(
        candidate_result,
        post_result,
        pre_rank=pre_rank,
        post_rank=post_rank,
    )
    bottleneck_bucket = _rerank_bottleneck_bucket(candidate_result, post_result)
    expected_families = (
        _source_families_from_refs(candidate_result.expected) if candidate_result else ("unknown",)
    )
    top_candidate_family = (
        _source_family(candidate_retrieved[0]) if candidate_retrieved else "none"
    )
    top_final_family = _source_family(final_retrieved[0]) if final_retrieved else "none"
    score_comparison = _rerank_score_comparison(candidate_result, post_result)
    return {
        "case_id": post_result.case_id,
        "query": post_result.query,
        "top_k": top_k,
        "candidate_budget": len(candidate_retrieved),
        "candidate_count": len(candidate_retrieved),
        "final_count": len(final_retrieved),
        "candidate_rank": candidate_rank,
        "pre_rerank_rank": candidate_rank,
        "pre_rerank_rank_at_k": pre_rank_at_k,
        "post_rerank_rank": post_rank,
        "rank_delta": _rank_delta(pre_rank, post_rank),
        "candidate_recall_at_budget": candidate_result.recall if candidate_result else 0.0,
        "pre_rerank_recall_at_k": _recall_from_refs(candidate_result, candidate_retrieved[:top_k]),
        "post_rerank_recall_at_k": post_result.recall,
        "pre_forbidden_before_expected_ok": (
            candidate_result.forbidden_before_expected_ok if candidate_result else True
        ),
        "post_forbidden_before_expected_ok": post_result.forbidden_before_expected_ok,
        "rerank_outcome": _rerank_outcome(pre_rank, post_rank),
        "harm_bucket": harm_bucket,
        "bottleneck_bucket": bottleneck_bucket,
        "expected_source_families": list(expected_families),
        "top_candidate_source_family": top_candidate_family,
        "top_final_source_family": top_final_family,
        "score_delta_available": score_comparison["available"],
        "score_comparison": score_comparison,
        "candidate_retrieved": candidate_retrieved[:10],
        "final_retrieved": final_retrieved[:10],
    }


def _rerank_score_comparison(
    candidate_result: benchmark_rag.CaseResult | None,
    post_result: benchmark_rag.CaseResult,
) -> dict[str, object]:
    if candidate_result is None:
        return {
            "available": False,
            "shared_ref_count": 0,
            "shared_ref_score_deltas": [],
            "top_candidate_score": None,
            "top_final_score": _top_retrieval_score(post_result),
            "first_relevant_candidate_score": None,
            "first_relevant_final_score": _first_matching_score(
                post_result.expected,
                _chunk_scores_by_ref(post_result),
            ),
            "first_relevant_score_delta": None,
        }
    candidate_scores = _chunk_scores_by_ref(candidate_result)
    final_scores = _chunk_scores_by_ref(post_result)
    shared_refs = sorted(candidate_scores.keys() & final_scores.keys())
    first_relevant_candidate_score = _first_matching_score(
        candidate_result.expected,
        candidate_scores,
    )
    first_relevant_final_score = _first_matching_score(
        candidate_result.expected,
        final_scores,
    )
    return {
        "available": bool(shared_refs),
        "shared_ref_count": len(shared_refs),
        "shared_ref_score_deltas": [
            {
                "ref": ref,
                "candidate_score": _round_score(candidate_scores[ref]),
                "final_score": _round_score(final_scores[ref]),
                "delta": _round_score(final_scores[ref] - candidate_scores[ref]),
            }
            for ref in shared_refs[:10]
        ],
        "top_candidate_score": _top_retrieval_score(candidate_result),
        "top_final_score": _top_retrieval_score(post_result),
        "first_relevant_candidate_score": first_relevant_candidate_score,
        "first_relevant_final_score": first_relevant_final_score,
        "first_relevant_score_delta": _score_delta(
            first_relevant_candidate_score,
            first_relevant_final_score,
        ),
    }


def _chunk_scores_by_ref(result: benchmark_rag.CaseResult) -> dict[str, float]:
    return {chunk.ref: chunk.score for chunk in result.retrieved_chunks}


def _first_matching_score(
    references: Sequence[str],
    scores_by_ref: Mapping[str, float],
) -> float | None:
    for expected_ref in references:
        for retrieved_ref, score in scores_by_ref.items():
            if _ref_matches_expected(expected_ref, retrieved_ref):
                return _round_score(score)
    return None


def _score_delta(first_score: float | None, second_score: float | None) -> float | None:
    if first_score is None or second_score is None:
        return None
    return _round_score(second_score - first_score)


def _round_score(value: float) -> float:
    return round(value, 6)


def _first_expected_ref_rank(expected: Sequence[str], retrieved: Sequence[str]) -> int | None:
    for rank, retrieved_ref in enumerate(retrieved, start=1):
        if any(_ref_matches_expected(expected_ref, retrieved_ref) for expected_ref in expected):
            return rank
    return None


def _ref_matches_expected(expected_ref: str, retrieved_ref: str) -> bool:
    expected = EvidenceReference.parse(expected_ref)
    retrieved = EvidenceReference.parse(retrieved_ref)
    if expected is None:
        return _reference_source(retrieved_ref) == expected_ref
    return (
        retrieved is not None
        and retrieved.source == expected.source
        and retrieved.chunk_index == expected.chunk_index
    )


def _reference_source(reference: str) -> str:
    parsed = EvidenceReference.parse(reference)
    if parsed is not None:
        return parsed.source
    return reference.split("#", 1)[0]


def _recall_from_refs(
    candidate_result: benchmark_rag.CaseResult | None,
    retrieved: Sequence[str],
) -> float:
    if candidate_result is None:
        return 0.0
    found = sum(
        1
        for expected_ref in candidate_result.expected
        if any(_ref_matches_expected(expected_ref, retrieved_ref) for retrieved_ref in retrieved)
    )
    return found / len(candidate_result.expected) if candidate_result.expected else 0.0


def _rank_delta(pre_rank: int | None, post_rank: int | None) -> int | None:
    if pre_rank is None or post_rank is None:
        return None
    return pre_rank - post_rank


def _rerank_outcome(pre_rank: int | None, post_rank: int | None) -> str:
    if pre_rank is None and post_rank is None:
        return "tie"
    if pre_rank is None:
        return "win"
    if post_rank is None:
        return "loss"
    if post_rank < pre_rank:
        return "win"
    if post_rank > pre_rank:
        return "loss"
    return "tie"


def _rerank_harm_bucket(
    candidate_result: benchmark_rag.CaseResult | None,
    post_result: benchmark_rag.CaseResult,
    *,
    pre_rank: int | None,
    post_rank: int | None,
) -> str | None:
    if (
        candidate_result is not None
        and candidate_result.forbidden_before_expected_ok
        and not post_result.forbidden_before_expected_ok
    ):
        return "forbidden_moved_before_expected"
    if pre_rank is not None and post_rank is None:
        return "expected_dropped_from_final_top_k"
    if pre_rank is not None and post_rank is not None and post_rank > pre_rank:
        return "expected_rank_lowered"
    return None


def _rerank_bottleneck_bucket(
    candidate_result: benchmark_rag.CaseResult | None,
    post_result: benchmark_rag.CaseResult,
) -> str | None:
    if candidate_result is None or candidate_result.rank is None:
        return "no_candidate_evidence_found"
    if post_result.rank is None:
        return "candidate_found_but_ranked_outside_final_top_k"
    if not post_result.forbidden_before_expected_ok:
        return "blocked_by_forbidden_before_expected_ordering"
    return None


def _rerank_pre_metrics(per_query: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not per_query:
        return {
            "hit_rate": 0.0,
            "expected_recall": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
            "query_count": 0,
        }
    hit_count = sum(1 for row in per_query if row.get("pre_rerank_rank_at_k") is not None)
    recall_sum = sum(_float_value(row.get("pre_rerank_recall_at_k")) for row in per_query)
    reciprocal_rank_sum = sum(
        0.0
        if row.get("pre_rerank_rank_at_k") is None
        else 1 / _float_value(row.get("pre_rerank_rank_at_k"))
        for row in per_query
    )
    query_count = len(per_query)
    return {
        "hit_rate": hit_count / query_count,
        "expected_recall": recall_sum / query_count,
        "recall_at_k": recall_sum / query_count,
        "mrr": reciprocal_rank_sum / query_count,
        "query_count": query_count,
    }


def _rerank_configuration_selection(
    parameters: RunnerParameters,
    candidate_report: benchmark_rag.BenchmarkReport,
    post_report: benchmark_rag.BenchmarkReport,
    reranker_state: Mapping[str, object],
    pre_metrics: Mapping[str, object],
    post_metrics: Mapping[str, object],
    harm_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    primary_metric = "expected_recall"
    pre_primary = _float_value(pre_metrics.get(primary_metric))
    post_primary = _float_value(post_metrics.get(primary_metric))
    primary_delta = _metric_delta(pre_primary, post_primary)
    pre_mrr = _float_value(pre_metrics.get("mrr"))
    post_mrr = _float_value(post_metrics.get("mrr"))
    pre_hit_rate = _float_value(pre_metrics.get("hit_rate"))
    post_hit_rate = _float_value(post_metrics.get("hit_rate"))
    pre_avoidance = candidate_report.forbidden_before_expected_avoidance
    post_avoidance = post_report.forbidden_before_expected_avoidance
    avoidance_delta = _metric_delta(pre_avoidance, post_avoidance)
    claim_eligible = reranker_state.get("claim_eligible") is True
    harm_count = len(harm_cases)
    safe_improvement = claim_eligible and primary_delta > 0.0 and harm_count == 0
    if not claim_eligible:
        selected_configuration = "no_claim_eligible_rerank"
        rationale = (
            "rerank output is not claim-eligible because the active reranker was not recorded"
        )
    elif harm_count:
        selected_configuration = "pre_rerank_baseline"
        rationale = "rerank introduced harm cases, so the safer baseline is selected"
    elif primary_delta > 0.0:
        selected_configuration = RetrievalMode.HYBRID_RERANK.value
        rationale = "rerank improves the predeclared primary metric without observed harm"
    else:
        selected_configuration = "pre_rerank_baseline"
        rationale = "rerank did not improve the predeclared primary metric"
    return {
        "primary_metric": primary_metric,
        "baseline_configuration": "hybrid_candidates_at_final_top_k",
        "candidate_configuration": {
            "retrieval_mode": RetrievalMode.HYBRID.value,
            "top_k": candidate_report.top_k,
            "candidate_budget": parameters.top_k * max(1, parameters.candidate_multiplier),
            "candidate_multiplier": 1,
        },
        "final_configuration": {
            "retrieval_mode": RetrievalMode.HYBRID_RERANK.value,
            "top_k": post_report.top_k,
            "candidate_multiplier": parameters.candidate_multiplier,
            "rerank_model": reranker_state.get("reported_model"),
        },
        "controlled_comparison": {
            "pre_rerank_at_k": dict(pre_metrics),
            "post_rerank": dict(post_metrics),
        },
        "metric_deltas": {
            "expected_recall": primary_delta,
            "mrr": _metric_delta(pre_mrr, post_mrr),
            "hit_rate": _metric_delta(pre_hit_rate, post_hit_rate),
            "forbidden_before_expected_avoidance": avoidance_delta,
        },
        "latency_tradeoff": {
            "candidate_generation_mean_ms": candidate_report.mean_latency_ms,
            "final_rerank_mean_ms": post_report.mean_latency_ms,
            "delta_ms": _metric_delta(
                candidate_report.mean_latency_ms,
                post_report.mean_latency_ms,
            ),
            "scope": "retrieval_only_per_query",
        },
        "harm_case_count": harm_count,
        "claim_eligible": claim_eligible,
        "safe_improvement": safe_improvement,
        "selected_configuration": selected_configuration,
        "rationale": rationale,
    }


def _metric_delta(first_value: float, second_value: float) -> float:
    return round(second_value - first_value, 6)


def _rerank_bottleneck_counts(per_query: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in per_query:
        bucket = row.get("bottleneck_bucket")
        if isinstance(bucket, str):
            counts[bucket] = counts.get(bucket, 0) + 1
    return dict(sorted(counts.items()))


def _rerank_source_family_confusion(
    per_query: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in per_query:
        expected_families = _string_list(row.get("expected_source_families")) or ["unknown"]
        top_family = row.get("top_final_source_family")
        top_label = top_family if isinstance(top_family, str) else "none"
        for expected_family in expected_families:
            key = f"{expected_family}->{top_label}"
            bucket = counts.setdefault(key, {"case_count": 0, "harm_count": 0})
            bucket["case_count"] += 1
            if row.get("harm_bucket") is not None:
                bucket["harm_count"] += 1
    return dict(sorted(counts.items()))


def _rerank_boost_diagnostics(per_query: Sequence[Mapping[str, object]]) -> dict[str, object]:
    changed_family_count = sum(
        1
        for row in per_query
        if row.get("top_candidate_source_family") != row.get("top_final_source_family")
    )
    shared_score_deltas = _shared_score_deltas(per_query)
    first_relevant_score_deltas = _first_relevant_score_deltas(per_query)
    return {
        "source_family_rank_change_count": changed_family_count,
        "source_family_confusion_available": True,
        "score_delta_available": bool(shared_score_deltas or first_relevant_score_deltas),
        "shared_ref_score_delta_count": len(shared_score_deltas),
        "shared_ref_score_delta_mean": _mean_or_none(shared_score_deltas),
        "first_relevant_score_delta_count": len(first_relevant_score_deltas),
        "first_relevant_score_delta_mean": _mean_or_none(first_relevant_score_deltas),
        "first_relevant_score_improved_count": sum(
            1 for delta in first_relevant_score_deltas if delta > 0.0
        ),
        "first_relevant_score_lowered_count": sum(
            1 for delta in first_relevant_score_deltas if delta < 0.0
        ),
        "notes": [
            "External benchmark reports source-family rank changes and score deltas when "
            "retrieval traces expose comparable candidate and final chunk scores."
        ],
    }


def _shared_score_deltas(per_query: Sequence[Mapping[str, object]]) -> list[float]:
    deltas: list[float] = []
    for row in per_query:
        score_comparison = row.get("score_comparison")
        if not isinstance(score_comparison, Mapping):
            continue
        raw_shared_deltas = score_comparison.get("shared_ref_score_deltas")
        if not isinstance(raw_shared_deltas, list):
            continue
        for raw_delta_row in raw_shared_deltas:
            if not isinstance(raw_delta_row, Mapping):
                continue
            raw_delta = raw_delta_row.get("delta")
            if isinstance(raw_delta, int | float):
                deltas.append(float(raw_delta))
    return deltas


def _first_relevant_score_deltas(per_query: Sequence[Mapping[str, object]]) -> list[float]:
    deltas: list[float] = []
    for row in per_query:
        score_comparison = row.get("score_comparison")
        if not isinstance(score_comparison, Mapping):
            continue
        raw_delta = score_comparison.get("first_relevant_score_delta")
        if isinstance(raw_delta, int | float):
            deltas.append(float(raw_delta))
    return deltas


def _mean_or_none(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _reranker_state(
    parameters: RunnerParameters,
    post_report: benchmark_rag.BenchmarkReport,
) -> dict[str, object]:
    model_name = parameters.rerank_model or _DEFAULT_RERANK_MODEL
    report_model = post_report.rerank_model
    claim_eligible = post_report.retrieval_mode == RetrievalMode.HYBRID_RERANK.value and bool(
        report_model
    )
    reasons = []
    if post_report.retrieval_mode != RetrievalMode.HYBRID_RERANK.value:
        reasons.append(
            f"retrieval mode reported as {post_report.retrieval_mode!r}, not "
            f"{RetrievalMode.HYBRID_RERANK.value!r}"
        )
    if not report_model:
        reasons.append("hybrid-rerank report did not record an active reranker model")
    return {
        "requested": True,
        "requested_model": model_name,
        "reported_model": report_model,
        "dependency_state": "runtime_reported" if claim_eligible else "unavailable_or_fallback",
        "fallback_status": "not_detected" if claim_eligible else "non_reranked_fallback",
        "claim_eligible": claim_eligible,
        "claim_blocking": not claim_eligible,
        "ineligibility_reasons": reasons,
    }


def _source_families_from_refs(references: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({_source_family(reference) for reference in references}))


def _source_family(reference: str) -> str:
    source = _reference_source(reference)
    if source.startswith("materials/"):
        source = source.removeprefix("materials/")
    path = Path(source)
    if len(path.parts) > 1 and path.parts[0]:
        return _neutral_token(path.parts[0])
    stem = path.stem or source
    for separator in ("-", "_", "."):
        if separator in stem:
            stem = stem.split(separator, 1)[0]
            break
    return _neutral_token(stem)


def _neutral_token(value: str) -> str:
    normalized = "".join(
        char.lower() if char.isalnum() else "-"
        for char in value.strip()
        if char.isalnum() or char in {"-", "_"}
    ).strip("-")
    return normalized or "unknown"


def _query_classification_summary(
    results: Sequence[benchmark_rag.CaseResult],
    parameters: RunnerParameters,
) -> dict[str, object]:
    counts: dict[str, int] = {}
    for result in results:
        query_class = _query_class(result.query)
        counts[query_class] = counts.get(query_class, 0) + 1
    return {
        "schema_version": QUERY_AUDIT_SCHEMA_VERSION,
        "decision_basis": "query-shape-and-fixed-retrieval-parameters",
        "query_class_counts": dict(sorted(counts.items())),
        "retrieval_strategy": _retrieval_strategy_payload(parameters),
    }


def _query_classification_payload(
    query: str,
    parameters: RunnerParameters,
) -> dict[str, object]:
    return audit_query_classification_payload(query, _audit_config(parameters))


def _query_class(query: str) -> str:
    return audit_query_class(query)


def _retrieval_strategy_payload(parameters: RunnerParameters) -> dict[str, object]:
    return audit_retrieval_strategy_payload(_audit_config(parameters))


def _audit_config(parameters: RunnerParameters) -> RetrievalAuditConfig:
    return RetrievalAuditConfig(
        retrieval_mode=parameters.retrieval_mode.value,
        transform_strategy=parameters.transform_strategy.value,
        top_k=parameters.top_k,
        candidate_multiplier=parameters.candidate_multiplier,
        repair_max_passes=parameters.repair_max_passes,
        rerank_requested=parameters.retrieval_mode == RetrievalMode.HYBRID_RERANK,
    )


def _retrieval_pass_payload(
    result: benchmark_rag.CaseResult,
    parameters: RunnerParameters,
    *,
    pass_number: int,
    query: str,
    stop_reason: str,
) -> dict[str, object]:
    classification = _query_classification_payload(query, parameters)
    return {
        "pass": pass_number,
        "query_excerpt": _query_excerpt(query),
        "query_class": classification["query_class"],
        "retrieval_strategy": classification["retrieval_strategy"],
        "top_k": parameters.top_k,
        "candidate_budget": parameters.top_k * max(1, parameters.candidate_multiplier),
        "retrieved_count": len(result.retrieved),
        "returned_count": len(result.retrieved),
        "top_score": _top_retrieval_score(result),
        "sufficiency": _sufficiency_label(result),
        "stop_reason": stop_reason,
        "latency_ms": result.elapsed_ms,
        "items": _retrieval_trace_items(result),
    }


def _retrieval_trace_items(result: benchmark_rag.CaseResult) -> list[dict[str, object]]:
    return [
        {
            "ref": chunk.ref,
            "source_id": _reference_source(chunk.ref),
            "score": round(chunk.score, 6),
            "text_excerpt": chunk.text_excerpt,
        }
        for chunk in result.retrieved_chunks[:10]
    ]


def _top_retrieval_score(result: benchmark_rag.CaseResult) -> float | None:
    if not result.retrieved_chunks:
        return None
    return round(result.retrieved_chunks[0].score, 6)


def _query_excerpt(query: str | None) -> str:
    return audit_query_excerpt(query, limit=QUERY_EXCERPT_LIMIT)


def _metrics_from_rag_report(report: benchmark_rag.BenchmarkReport) -> dict[str, object]:
    return {
        "hit_rate": report.hit_rate,
        "mrr": report.mean_reciprocal_rank,
        "expected_recall": report.mean_expected_recall,
        "recall_at_k": report.mean_expected_recall,
        "precision_at_k": report.mean_precision_at_k,
        "map_at_k": report.mean_average_precision_at_k,
        "ndcg_at_k": report.mean_ndcg_at_k,
        "graded_ndcg_at_k": report.mean_graded_ndcg_at_k,
        "query_count": report.cases,
        "sample_size": report.cases,
        "forbidden_before_expected_avoidance": report.forbidden_before_expected_avoidance,
        "mean_latency_ms": report.mean_latency_ms,
        "latency": {
            "mean_ms": report.mean_latency_ms,
            "scope": "retrieval_only_per_query",
            "unit": "milliseconds",
        },
    }


def _case_result_payload(
    result: benchmark_rag.CaseResult,
    parameters: RunnerParameters,
) -> dict[str, object]:
    reciprocal_rank = 0.0 if result.rank is None else 1 / result.rank
    return {
        "case_id": result.case_id,
        "query": result.query,
        "query_classification": _query_classification_payload(result.query, parameters),
        "retrieval_trace": _retrieval_pass_payload(
            result,
            parameters,
            pass_number=1,
            query=result.query,
            stop_reason="sufficient_evidence"
            if _result_sufficient(result)
            else "insufficient_evidence",
        ),
        "retrieved": list(result.retrieved),
        "hit": result.hit,
        "rank": result.rank,
        "reciprocal_rank": reciprocal_rank,
        "expected_recall": result.recall,
        "recall_at_k": result.recall,
        "precision_at_k": result.precision_at_k,
        "average_precision_at_k": result.average_precision_at_k,
        "ndcg_at_k": result.ndcg_at_k,
        "graded_ndcg_at_k": result.graded_ndcg_at_k,
        "first_forbidden_rank": result.first_forbidden_rank,
        "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
        "latency_ms": result.elapsed_ms,
    }


def _claim_safe_rag_report(report: benchmark_rag.BenchmarkReport) -> dict[str, object]:
    payload = cast("dict[str, object]", asdict(report))
    return _remove_oracle_fields(payload)


def _remove_oracle_fields(value: object) -> dict[str, object]:
    redacted = _without_oracle_fields(value)
    if isinstance(redacted, dict):
        return cast("dict[str, object]", redacted)
    return {}


def _without_oracle_fields(value: object) -> object:
    if isinstance(value, dict):
        cleaned: dict[str, object] = {}
        for raw_key, child in value.items():
            if not isinstance(raw_key, str) or raw_key in _ORACLE_KEYS:
                continue
            cleaned[raw_key] = _without_oracle_fields(child)
        return cleaned
    if isinstance(value, list):
        return [_without_oracle_fields(item) for item in value]
    if isinstance(value, tuple):
        return [_without_oracle_fields(item) for item in value]
    return value


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
        "retrieval_mode": report.retrieval_mode,
        "candidate_multiplier": report.candidate_multiplier,
        "pseudo_feedback_docs": report.pseudo_feedback_docs,
        "pseudo_feedback_terms": report.pseudo_feedback_terms,
        "pseudo_feedback_weight": report.pseudo_feedback_weight,
        "retriever_backends": list(report.retriever_backends),
        "transform_strategy": report.transform_strategy,
        "metrics": {
            "hit_rate": report.hit_rate,
            "mrr": report.mean_reciprocal_rank,
            "expected_recall": report.mean_expected_recall,
            "precision_at_k": report.mean_precision_at_k,
            "map_at_k": report.mean_average_precision_at_k,
            "ndcg_at_k": report.mean_ndcg_at_k,
            "graded_ndcg_at_k": report.mean_graded_ndcg_at_k,
            "forbidden_before_expected_avoidance": report.forbidden_before_expected_avoidance,
        },
        "results": [
            {
                "case_id": result.case_id,
                "retrieved": list(result.retrieved),
                "hit": result.hit,
                "rank": result.rank,
                "first_forbidden_rank": result.first_forbidden_rank,
                "forbidden_before_expected_ok": result.forbidden_before_expected_ok,
                "expected_recall": result.recall,
                "precision_at_k": result.precision_at_k,
                "average_precision_at_k": result.average_precision_at_k,
                "ndcg_at_k": result.ndcg_at_k,
                "graded_ndcg_at_k": result.graded_ndcg_at_k,
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
    prompt_identity: PromptIdentity | None,
    model_label: str,
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
            "Pass --suite pointing to an existing Heph benchmark suite.",
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
            prompt_identity=prompt_identity,
            model_label=model_label,
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
        "native_suite_report": _remove_oracle_fields(native_report),
    }


def _metrics_from_native_report(native_report: Mapping[str, object]) -> dict[str, object]:
    rag = native_report.get("rag")
    if not isinstance(rag, dict):
        return {
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "recall_at_k": 0.0,
            "precision_at_k": 0.0,
            "map_at_k": 0.0,
            "ndcg_at_k": 0.0,
            "query_count": 0,
            "sample_size": 0,
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
        "recall_at_k": _number_field(rag, "mean_expected_recall"),
        "precision_at_k": _number_field(rag, "mean_precision_at_k"),
        "map_at_k": _number_field(rag, "mean_average_precision_at_k"),
        "ndcg_at_k": _number_field(rag, "mean_ndcg_at_k"),
        "query_count": _int_field(rag, "cases"),
        "sample_size": _int_field(rag, "cases"),
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


def _int_field(payload: Mapping[object, object], field_name: str) -> int:
    value = payload.get(field_name)
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return 0


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
    return claim_report_envelope.deterministic_report_projection(report)


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
    prompt_identity: PromptIdentity | None,
    model_label: str,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "runner": RUNNER_ID,
        "benchmark_type": benchmark_type,
        "dataset": dataset,
        "suite_path": str(suite_path),
        "fixed_parameters": {
            "top_k": parameters.top_k,
            "min_score": parameters.min_score,
            "retrieval_mode": parameters.retrieval_mode.value,
            "candidate_multiplier": parameters.candidate_multiplier,
            "hybrid_sparse_weight": parameters.hybrid_sparse_weight,
            "hybrid_dense_weight": parameters.hybrid_dense_weight,
            "pseudo_feedback_docs": parameters.pseudo_feedback_docs,
            "pseudo_feedback_terms": parameters.pseudo_feedback_terms,
            "pseudo_feedback_weight": parameters.pseudo_feedback_weight,
            "repair_max_passes": parameters.repair_max_passes,
            "transform_strategy": parameters.transform_strategy.value,
            "query_order": "case-file-order",
            "result_order": "retrieval-rank-order",
            "random_seed": 0,
            "randomness": "not-used",
            "network_access": "disabled-after-materialization",
            "embedding_model": parameters.embedding_model
            or os.environ.get("HEPHAION_EMBED_MODEL", _DEFAULT_EMBEDDING_MODEL),
            "embedding_query_prefix": parameters.embedding_query_prefix,
            "embedding_document_prefix": parameters.embedding_document_prefix,
            "rerank_model": parameters.rerank_model
            or os.environ.get("HEPHAION_RERANK_MODEL", _DEFAULT_RERANK_MODEL),
        },
        "metric_formulas": dict(_METRIC_FORMULAS),
        "latency_scope": claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY,
        "timestamp_policy": "no wall-clock timestamp is included in deterministic reports",
        "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
    }
    if armory_path is not None:
        metadata["armory_path"] = str(armory_path)
        materials_path = armory_path / storage.MATERIALS_DIR
        if materials_path.is_dir():
            metadata["corpus_sha256"] = claim_report_envelope.sha256_directory(materials_path)
    if cases_path is not None:
        metadata["cases_path"] = str(cases_path)
        metadata["cases_sha256"] = _sha256_file(cases_path)
        metadata["qrels_sha256"] = metadata["cases_sha256"]
    conversion_manifest = suite_path / "conversion_manifest.json"
    if conversion_manifest.is_file():
        metadata["conversion_manifest_path"] = str(conversion_manifest)
        metadata["conversion_manifest_sha256"] = _sha256_file(conversion_manifest)
        metadata["manifest_sha256"] = metadata["conversion_manifest_sha256"]
    elif cases_path is not None:
        metadata["manifest_sha256"] = metadata["cases_sha256"]
    elif suite_path.exists():
        metadata["manifest_sha256"] = claim_report_envelope.sha256_directory(suite_path)
        metadata["corpus_sha256"] = metadata["manifest_sha256"]
        metadata["qrels_sha256"] = metadata["manifest_sha256"]
    if readiness_report_path is not None:
        metadata["readiness_report_path"] = str(readiness_report_path.resolve())
    if report_path is not None:
        metadata["report_path"] = str(report_path.expanduser().resolve())
    if prompt_identity is not None:
        metadata["prompt_path"] = str(prompt_identity.path)
        metadata["prompt_hash"] = prompt_identity.sha256
        metadata["prompt_title"] = prompt_identity.title
        metadata["prompt_version"] = prompt_identity.version
    if model_label.strip():
        metadata["model"] = model_label.strip()
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
        "known_limits": _known_limits_for_benchmarks(benchmarks),
        "warnings": warnings,
        "errors": errors,
        "reproducibility": reproducibility,
    }


def _known_limits_for_benchmarks(
    benchmarks: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    if _contains_claim_blocking_repair_diagnostic(benchmarks):
        entries.append(
            {
                "id": "repair-routing-label-scored-diagnostics",
                "version": "repair-routing-label-scored-diagnostics-v1",
                "rationale": (
                    "Repair routing and diagnostic effective-result selection use "
                    "benchmark labels to measure sufficiency; repaired diagnostics are "
                    "retained for audits only."
                ),
                "limitation": (
                    "Reports with repair diagnostics are not claim-eligible until repair "
                    "routing uses observable retrieval/evidence signals only."
                ),
                "recorded_before_claim": True,
                "claim_blocking": True,
            }
        )
    return {
        "schema_version": claim_report_envelope.KNOWN_LIMITS_SCHEMA_VERSION,
        "policy_version": claim_report_envelope.KNOWN_LIMITS_POLICY_VERSION,
        "entries": entries,
    }


def _contains_claim_blocking_repair_diagnostic(
    benchmarks: Sequence[Mapping[str, object]],
) -> bool:
    for benchmark in benchmarks:
        repair_analysis = benchmark.get("repair_analysis")
        if isinstance(repair_analysis, Mapping) and repair_analysis.get("claim_blocking") is True:
            return True
    return False


def _report_id(metadata: Mapping[str, object]) -> str:
    raw_benchmark_type = metadata.get("benchmark_type")
    raw_dataset = metadata.get("dataset")
    benchmark_type = raw_benchmark_type if isinstance(raw_benchmark_type, str) else "unknown"
    dataset = raw_dataset if isinstance(raw_dataset, str) else "unknown"
    fixed_parameters = metadata.get("fixed_parameters")
    if not isinstance(fixed_parameters, dict):
        return f"{benchmark_type}:{dataset}"
    parameters = cast("dict[str, object]", fixed_parameters)
    mode = _report_id_part(parameters.get("retrieval_mode"), default="unknown")
    strategy = _report_id_part(parameters.get("transform_strategy"), default="unknown")
    top_k = _report_id_part(parameters.get("top_k"), default="na")
    min_score = _report_id_part(parameters.get("min_score"), default="na")
    candidate_multiplier = _report_id_part(
        parameters.get("candidate_multiplier"),
        default="na",
    )
    suffix = ""
    embedding_model = parameters.get("embedding_model")
    if isinstance(embedding_model, str) and embedding_model != _DEFAULT_EMBEDDING_MODEL:
        suffix += f":embedding_model={_report_id_part(embedding_model, default='unknown')}"
    embedding_query_prefix = parameters.get("embedding_query_prefix")
    if isinstance(embedding_query_prefix, str) and embedding_query_prefix:
        suffix += (
            f":embedding_query_prefix={_report_id_part(embedding_query_prefix, default='unknown')}"
        )
    embedding_document_prefix = parameters.get("embedding_document_prefix")
    if isinstance(embedding_document_prefix, str) and embedding_document_prefix:
        suffix += (
            ":embedding_document_prefix="
            f"{_report_id_part(embedding_document_prefix, default='unknown')}"
        )
    rerank_model = parameters.get("rerank_model")
    if isinstance(rerank_model, str) and rerank_model != _DEFAULT_RERANK_MODEL:
        suffix += f":rerank_model={_report_id_part(rerank_model, default='unknown')}"
    sparse_weight = parameters.get("hybrid_sparse_weight")
    if isinstance(sparse_weight, int | float) and float(sparse_weight) != 1.0:
        suffix += f":sparse_weight={_report_id_part(sparse_weight, default='unknown')}"
    dense_weight = parameters.get("hybrid_dense_weight")
    if isinstance(dense_weight, int | float) and float(dense_weight) != 1.0:
        suffix += f":dense_weight={_report_id_part(dense_weight, default='unknown')}"
    if parameters.get("retrieval_mode") == RetrievalMode.HYBRID_PRF.value:
        feedback_docs = _report_id_part(
            parameters.get("pseudo_feedback_docs"),
            default="unknown",
        )
        feedback_terms = _report_id_part(
            parameters.get("pseudo_feedback_terms"),
            default="unknown",
        )
        feedback_weight = _report_id_part(
            parameters.get("pseudo_feedback_weight"),
            default="unknown",
        )
        suffix += (
            f":prf_docs={feedback_docs}:prf_terms={feedback_terms}:prf_weight={feedback_weight}"
        )
    repair_max_passes = parameters.get("repair_max_passes")
    if isinstance(repair_max_passes, int) and repair_max_passes != _DEFAULT_REPAIR_MAX_PASSES:
        suffix += f":repair_max_passes={_report_id_part(repair_max_passes, default='unknown')}"
    return (
        f"{benchmark_type}:{dataset}:mode={mode}:strategy={strategy}:"
        f"top_k={top_k}:min_score={min_score}:candidate_multiplier={candidate_multiplier}"
        f"{suffix}"
    )


def _report_id_part(value: object, *, default: str) -> str:
    if isinstance(value, bool):
        return default
    text = str(value) if isinstance(value, int | float | str) else default
    return (
        text.replace(" ", "-").replace("/", "-").replace(":", "-").replace("=", "-").strip()
        or default
    )


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
    prompt_identity: PromptIdentity | None,
    model_label: str,
    error: RunnerError,
) -> dict[str, object]:
    suite_path = Path()
    metadata: dict[str, object] = {
        "runner": RUNNER_ID,
        "benchmark_type": benchmark_type,
        "dataset": dataset,
        "suite_path": str(suite_path),
        "fixed_parameters": {
            "top_k": parameters.top_k,
            "min_score": parameters.min_score,
            "retrieval_mode": parameters.retrieval_mode.value,
            "candidate_multiplier": parameters.candidate_multiplier,
            "hybrid_sparse_weight": parameters.hybrid_sparse_weight,
            "hybrid_dense_weight": parameters.hybrid_dense_weight,
            "pseudo_feedback_docs": parameters.pseudo_feedback_docs,
            "pseudo_feedback_terms": parameters.pseudo_feedback_terms,
            "pseudo_feedback_weight": parameters.pseudo_feedback_weight,
            "repair_max_passes": parameters.repair_max_passes,
            "transform_strategy": parameters.transform_strategy.value,
            "query_order": "case-file-order",
            "result_order": "retrieval-rank-order",
            "random_seed": 0,
            "randomness": "not-used",
            "network_access": "disabled-after-materialization",
            "embedding_model": parameters.embedding_model
            or os.environ.get("HEPHAION_EMBED_MODEL", _DEFAULT_EMBEDDING_MODEL),
            "embedding_query_prefix": parameters.embedding_query_prefix,
            "embedding_document_prefix": parameters.embedding_document_prefix,
            "rerank_model": parameters.rerank_model
            or os.environ.get("HEPHAION_RERANK_MODEL", _DEFAULT_RERANK_MODEL),
        },
        "metric_formulas": dict(_METRIC_FORMULAS),
        "latency_scope": "not_executed",
        "timestamp_policy": "no wall-clock timestamp is included in deterministic reports",
        "runtime_only_fields": list(_RUNTIME_ONLY_FIELDS),
    }
    if report_path is not None:
        metadata["report_path"] = str(report_path.expanduser().resolve())
    if prompt_identity is not None:
        metadata["prompt_path"] = str(prompt_identity.path)
        metadata["prompt_hash"] = prompt_identity.sha256
        metadata["prompt_title"] = prompt_identity.title
        metadata["prompt_version"] = prompt_identity.version
    if model_label.strip():
        metadata["model"] = model_label.strip()
    return _base_report(
        status="error",
        metadata=metadata,
        benchmarks=[],
        aggregate_metrics={
            "hit_rate": 0.0,
            "mrr": 0.0,
            "expected_recall": 0.0,
            "recall_at_k": 0.0,
            "precision_at_k": 0.0,
            "map_at_k": 0.0,
            "ndcg_at_k": 0.0,
            "query_count": 0,
            "sample_size": 0,
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
        help=(
            "Dataset identifier, e.g. beir/nfcorpus, mteb/SciFact, ms-marco, "
            "public-academic, or academic"
        ),
    )
    parser.add_argument(
        "--suite",
        type=Path,
        help="Materialized benchmark suite directory containing armory/ and rag.jsonl",
    )
    parser.add_argument("--armory", type=Path, help="Materialized Heph armory path")
    parser.add_argument("--cases", type=Path, help="Generated rag.jsonl benchmark cases")
    parser.add_argument("--top-k", type=int, default=_DEFAULT_TOP_K)
    parser.add_argument("--min-score", type=float, default=_DEFAULT_MIN_SCORE)
    parser.add_argument(
        "--retrieval-mode",
        choices=[mode.value for mode in RetrievalMode],
        default=_DEFAULT_RETRIEVAL_MODE.value,
        help="Retriever pipeline to run with fixed inputs",
    )
    parser.add_argument(
        "--candidate-multiplier",
        type=int,
        default=_DEFAULT_CANDIDATE_MULTIPLIER,
        help="Hybrid over-retrieval multiplier before final top-k/reranking",
    )
    parser.add_argument(
        "--strategy",
        choices=[strategy.value for strategy in TransformStrategy],
        default=TransformStrategy.IDENTITY.value,
        help="RAG query transformation strategy",
    )
    parser.add_argument(
        "--embedding-model",
        help=(
            "Sentence-transformers embedding model. Defaults to HEPHAION_EMBED_MODEL "
            f"or {_DEFAULT_EMBEDDING_MODEL}."
        ),
    )
    parser.add_argument(
        "--embedding-query-prefix",
        default="",
        help="Prefix applied to embedding queries, for instruction-tuned retrievers",
    )
    parser.add_argument(
        "--embedding-document-prefix",
        default="",
        help="Prefix applied to embedded documents, for asymmetric retrievers",
    )
    parser.add_argument(
        "--rerank-model",
        help=(
            "Cross-encoder reranking model. Defaults to HEPHAION_RERANK_MODEL "
            f"or {_DEFAULT_RERANK_MODEL}."
        ),
    )
    parser.add_argument(
        "--hybrid-sparse-weight",
        type=float,
        default=1.0,
        help="Sparse retriever weight for hybrid reciprocal-rank fusion",
    )
    parser.add_argument(
        "--hybrid-dense-weight",
        type=float,
        default=1.0,
        help="Dense retriever weight for hybrid reciprocal-rank fusion",
    )
    parser.add_argument(
        "--pseudo-feedback-docs",
        type=int,
        default=DEFAULT_PSEUDO_FEEDBACK_DOCS,
        help="Number of top sparse results used for hybrid-prf query feedback",
    )
    parser.add_argument(
        "--pseudo-feedback-terms",
        type=int,
        default=DEFAULT_PSEUDO_FEEDBACK_TERMS,
        help="Number of expansion terms added for hybrid-prf sparse feedback",
    )
    parser.add_argument(
        "--pseudo-feedback-weight",
        type=float,
        default=DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
        help="Sparse feedback RRF weight for hybrid-prf retrieval",
    )
    parser.add_argument(
        "--repair-max-passes",
        type=int,
        default=_DEFAULT_REPAIR_MAX_PASSES,
        help=(
            "Maximum audited retrieval passes per query. Use 2 to retry misses with a "
            "deterministic cleaned query."
        ),
    )
    parser.add_argument(
        "--validate-reproducibility",
        action="store_true",
        help="Run equivalent inputs twice and compare deterministic fields",
    )
    parser.add_argument("--min-hit-rate", type=float, default=0.0)
    parser.add_argument("--min-mrr", type=float, default=0.0)
    parser.add_argument("--min-expected-recall", type=float, default=0.0)
    parser.add_argument(
        "--prompt",
        type=Path,
        help="Benchmark evaluation prompt whose path/hash should be recorded in reports",
    )
    parser.add_argument(
        "--model-label",
        default="",
        help="Optional model or evaluation configuration label to record in reports",
    )
    parser.add_argument("--json-report", type=Path, help="Write a versioned JSON report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    invocation = claim_report_envelope.command_invocation(RUNNER_ID, effective_argv)
    args = parser.parse_args(effective_argv)
    benchmark_type = cast("str", args.benchmark_type)
    dataset = cast("str", args.dataset)
    report_path = cast("Path | None", args.json_report)
    thresholds = _rate_thresholds(args)
    parameters = _parameters(args)
    prompt_identity: PromptIdentity | None = None
    model_label = cast("str", args.model_label)

    try:
        prompt_identity = _prompt_identity(cast("Path | None", args.prompt))
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
                prompt_identity=prompt_identity,
                model_label=model_label,
            )
        else:
            inputs = _resolve_external_inputs(benchmark_type, dataset, args)
            report, status = _run_rag_flow(
                inputs,
                parameters,
                thresholds,
                validate_reproducibility=cast("bool", args.validate_reproducibility),
                prompt_identity=prompt_identity,
                model_label=model_label,
                report_path=report_path,
            )
    except RunnerError as exc:
        report = _error_report(
            benchmark_type,
            dataset,
            thresholds,
            parameters,
            report_path,
            prompt_identity,
            model_label,
            exc,
        )
        report = claim_report_envelope.finalize_claim_report(report, command=invocation)
        _write_json_report(report_path, report)
        _print_status(report, error=True)
        return 2
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        error = RunnerError(
            "execution_failed",
            f"benchmark execution failed: {exc}",
            "Check local materialized inputs and rerun with a small fixture.",
        )
        report = _error_report(
            benchmark_type,
            dataset,
            thresholds,
            parameters,
            report_path,
            prompt_identity,
            model_label,
            error,
        )
        report = claim_report_envelope.finalize_claim_report(report, command=invocation)
        _write_json_report(report_path, report)
        _print_status(report, error=True)
        return 2

    report = claim_report_envelope.finalize_claim_report(report, command=invocation)
    _write_json_report(report_path, report)
    _print_status(report, error=status != 0)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
