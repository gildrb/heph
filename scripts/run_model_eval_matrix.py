"""Run model-backed replay evals for a matrix of configured models.

The matrix file is JSON:

    {
      "candidates": [
        {
          "id": "local-small",
          "group": "local",
          "model": "llama-3.1-8b",
          "base_url": "http://localhost:11434/v1",
          "api_key_env": "OPENAI_API_KEY"
        }
      ]
    }

Each candidate runs ``scripts.run_replay_answer_eval`` and produces one answer
fixture file plus one scored report. The combined matrix report records only
model metadata and scores, never API keys.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.providers.oauth import load_credentials
from hephaistos.runtime import ChatConfig
from hephaistos.runtime.engine import EngineError
from scripts import replay_answer_benchmark, run_replay_answer_eval

DEFAULT_REQUIRED_GROUPS = ("local", "frontier")
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_METRIC_LABELS = {
    "pass_rate": "answer pass rate",
    "citation_validity_rate": "citation validity",
    "citation_presence_rate": "citation presence",
    "expected_citation_rate": "expected citations",
    "required_text_rate": "required text",
    "forbidden_text_rate": "forbidden text",
    "supported_claim_rate": "supported claims",
    "answer_shape_rate": "answer shape",
    "evidence_coverage_rate": "evidence coverage",
    "required_label_rate": "required labels",
}


class RawModelCandidate(TypedDict):
    id: str
    model: str
    group: NotRequired[str]
    base_url: NotRequired[str]
    api_key: NotRequired[str]
    api_key_env: NotRequired[str]
    provider_slug: NotRequired[str]
    provider_env: NotRequired[str]
    max_tokens: NotRequired[int]
    rag_context_budget: NotRequired[int]
    timeout_seconds: NotRequired[int]


@dataclass(frozen=True, slots=True)
class ModelCandidate:
    candidate_id: str
    model: str
    group: str
    base_url: str = ""
    api_key: str = ""
    provider_slug: str = ""
    provider_env: str = ""
    max_tokens: int = 4096
    rag_context_budget: int = 2000
    timeout_seconds: int = 0


@dataclass(frozen=True, slots=True)
class ModelEvalResult:
    candidate_id: str
    group: str
    model: str
    base_url: str
    status: int
    output: str
    report_path: str
    cases: int | None
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    pass_rate: float | None
    citation_validity_rate: float | None
    citation_presence_rate: float | None
    expected_citation_rate: float | None
    required_text_rate: float | None
    forbidden_text_rate: float | None
    supported_claim_rate: float | None
    answer_shape_rate: float | None
    evidence_coverage_rate: float | None
    required_label_rate: float | None
    error: str = ""


@dataclass(frozen=True, slots=True)
class ModelEvalMatrixReport:
    armory: str
    replay_dataset: str
    output_dir: str
    required_groups: tuple[str, ...]
    status: int
    candidates: int
    groups: tuple[str, ...]
    failures: tuple[str, ...]
    results: tuple[ModelEvalResult, ...]
    replay_cases: int = 0
    replay_domains: tuple[str, ...] = ()
    replay_tasks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CandidateReportMetrics:
    cases: int | None
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    pass_rate: float | None
    citation_validity_rate: float | None
    citation_presence_rate: float | None
    expected_citation_rate: float | None
    required_text_rate: float | None
    forbidden_text_rate: float | None
    supported_claim_rate: float | None
    answer_shape_rate: float | None
    evidence_coverage_rate: float | None
    required_label_rate: float | None


@dataclass(frozen=True, slots=True)
class ReplayCoverage:
    case_count: int
    domains: tuple[str, ...]
    tasks: tuple[str, ...]


class _CandidateTimeoutError(TimeoutError):
    """Raised when one model candidate exceeds its wall-clock budget."""


def _safe_id(value: str) -> str:
    safe = _SAFE_ID_RE.sub("-", value.strip()).strip("-._")
    return safe or "model"


def _string_field(raw: dict[str, object], field: str, candidate_number: int) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"candidate {candidate_number} must include non-empty {field!r}")
    return value.strip()


def _optional_string_field(raw: dict[str, object], field: str) -> str:
    value = raw.get(field)
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _positive_int_field(raw: dict[str, object], field: str, default: int) -> int:
    value = raw.get(field, default)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"candidate field {field!r} must be a positive integer")
    return value


def _non_negative_int_field(raw: dict[str, object], field: str, default: int) -> int:
    value = raw.get(field, default)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"candidate field {field!r} must be a non-negative integer")
    return value


def _raw_candidates(payload: object) -> list[dict[str, object]]:
    raw_candidates: object
    if isinstance(payload, dict):
        raw_candidates = cast("dict[str, object]", payload).get("candidates")
    else:
        raw_candidates = payload
    if not isinstance(raw_candidates, list):
        raise TypeError("model matrix must be a JSON list or object with a 'candidates' list")
    candidates: list[dict[str, object]] = []
    for idx, raw in enumerate(raw_candidates, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"candidate {idx} must be an object")
        candidates.append(cast("dict[str, object]", raw))
    return candidates


def load_candidates(path: Path) -> list[ModelCandidate]:
    """Load model candidates from a JSON matrix file."""
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read model matrix: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid model matrix JSON: {path}") from exc

    candidates: list[ModelCandidate] = []
    seen: set[str] = set()
    for idx, raw in enumerate(_raw_candidates(payload), start=1):
        candidate_id = _safe_id(_string_field(raw, "id", idx))
        if candidate_id in seen:
            raise ValueError(f"duplicate model candidate id: {candidate_id}")
        seen.add(candidate_id)
        api_key = _optional_string_field(raw, "api_key")
        api_key_env = _optional_string_field(raw, "api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env, api_key)
        candidates.append(
            ModelCandidate(
                candidate_id=candidate_id,
                model=_string_field(raw, "model", idx),
                group=_optional_string_field(raw, "group") or "ungrouped",
                base_url=_optional_string_field(raw, "base_url"),
                api_key=api_key,
                provider_slug=_optional_string_field(raw, "provider_slug"),
                provider_env=_optional_string_field(raw, "provider_env"),
                max_tokens=_positive_int_field(raw, "max_tokens", 4096),
                rag_context_budget=_positive_int_field(raw, "rag_context_budget", 2000),
                timeout_seconds=_non_negative_int_field(raw, "timeout_seconds", 0),
            )
        )
    if not candidates:
        raise ValueError("model matrix must include at least one candidate")
    return candidates


def run_model_eval_matrix(
    armory_path: Path,
    replay_dataset: Path,
    output_dir: Path,
    candidates: Sequence[ModelCandidate],
    *,
    required_groups: Sequence[str] = DEFAULT_REQUIRED_GROUPS,
    answer_pass_rate: float = run_replay_answer_eval.DEFAULT_ANSWER_PASS_RATE,
    citation_validity: float = run_replay_answer_eval.DEFAULT_CITATION_VALIDITY,
    citation_presence: float = run_replay_answer_eval.DEFAULT_CITATION_PRESENCE,
    expected_citations: float = run_replay_answer_eval.DEFAULT_EXPECTED_CITATIONS,
    required_text: float = run_replay_answer_eval.DEFAULT_REQUIRED_TEXT,
    forbidden_text: float = run_replay_answer_eval.DEFAULT_FORBIDDEN_TEXT,
    supported_claims: float = run_replay_answer_eval.DEFAULT_SUPPORTED_CLAIMS,
    answer_shape: float = run_replay_answer_eval.DEFAULT_ANSWER_SHAPE,
    evidence_coverage: float = run_replay_answer_eval.DEFAULT_EVIDENCE_COVERAGE,
    required_label: float = run_replay_answer_eval.DEFAULT_REQUIRED_LABEL,
    min_answer_domains: int = run_replay_answer_eval.DEFAULT_MIN_ANSWER_DOMAINS,
    min_answer_tasks: int = run_replay_answer_eval.DEFAULT_MIN_ANSWER_TASKS,
    report_path: Path | None = None,
) -> int:
    """Run replay eval for each candidate and write a combined matrix report."""
    missing_groups = sorted(set(required_groups) - {candidate.group for candidate in candidates})
    if missing_groups:
        raise ValueError(f"model matrix missing required group(s): {', '.join(missing_groups)}")

    replay_coverage = _replay_coverage(
        replay_dataset,
        min_answer_domains=min_answer_domains,
        min_answer_tasks=min_answer_tasks,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[ModelEvalResult] = []
    failures: list[str] = []
    for candidate in candidates:
        result = _run_candidate(
            armory_path,
            replay_dataset,
            output_dir,
            candidate,
            answer_pass_rate=answer_pass_rate,
            citation_validity=citation_validity,
            citation_presence=citation_presence,
            expected_citations=expected_citations,
            required_text=required_text,
            forbidden_text=forbidden_text,
            supported_claims=supported_claims,
            answer_shape=answer_shape,
            evidence_coverage=evidence_coverage,
            required_label=required_label,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            replay_coverage=replay_coverage,
        )
        results.append(result)
        if result.status != 0:
            failures.append(result.candidate_id)

    status = 1 if failures else 0
    report = ModelEvalMatrixReport(
        armory=str(armory_path),
        replay_dataset=str(replay_dataset),
        output_dir=str(output_dir),
        required_groups=tuple(required_groups),
        status=status,
        candidates=len(candidates),
        groups=tuple(sorted({candidate.group for candidate in candidates})),
        failures=tuple(failures),
        results=tuple(results),
        replay_cases=replay_coverage.case_count,
        replay_domains=replay_coverage.domains,
        replay_tasks=replay_coverage.tasks,
    )
    if report_path is not None:
        _write_json_report(report_path, report)
    print_text_report(report)
    return status


def validate_model_eval_matrix(
    candidates: Sequence[ModelCandidate],
    *,
    required_groups: Sequence[str] = DEFAULT_REQUIRED_GROUPS,
) -> ModelEvalMatrixReport:
    """Validate candidate matrix structure without running model calls."""
    missing_groups = sorted(set(required_groups) - {candidate.group for candidate in candidates})
    failures = tuple(f"missing required group: {group}" for group in missing_groups)
    return ModelEvalMatrixReport(
        armory="",
        replay_dataset="",
        output_dir="",
        required_groups=tuple(required_groups),
        status=1 if failures else 0,
        candidates=len(candidates),
        groups=tuple(sorted({candidate.group for candidate in candidates})),
        failures=failures,
        results=(),
    )


def validate_model_eval_inputs(
    armory_path: Path,
    replay_dataset: Path,
    output_dir: Path,
    candidates: Sequence[ModelCandidate],
    *,
    required_groups: Sequence[str] = DEFAULT_REQUIRED_GROUPS,
    min_answer_domains: int = run_replay_answer_eval.DEFAULT_MIN_ANSWER_DOMAINS,
    min_answer_tasks: int = run_replay_answer_eval.DEFAULT_MIN_ANSWER_TASKS,
) -> ModelEvalMatrixReport:
    """Validate candidate groups and replay dataset coverage without model calls."""
    group_report = validate_model_eval_matrix(candidates, required_groups=required_groups)
    failures = list(group_report.failures)
    replay_coverage = ReplayCoverage(case_count=0, domains=(), tasks=())
    try:
        replay_coverage = _replay_coverage(
            replay_dataset,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
        )
    except ValueError as exc:
        failures.append(f"replay dataset: {exc}")
    if not armory_path.is_dir():
        failures.append(f"armory path is not a directory: {armory_path}")
    credential_failures = _candidate_credential_failures(candidates)
    failures.extend(credential_failures)
    return ModelEvalMatrixReport(
        armory=str(armory_path),
        replay_dataset=str(replay_dataset),
        output_dir=str(output_dir),
        required_groups=tuple(required_groups),
        status=1 if failures else 0,
        candidates=len(candidates),
        groups=group_report.groups,
        failures=tuple(failures),
        results=(),
        replay_cases=replay_coverage.case_count,
        replay_domains=replay_coverage.domains,
        replay_tasks=replay_coverage.tasks,
    )


def _run_candidate(
    armory_path: Path,
    replay_dataset: Path,
    output_dir: Path,
    candidate: ModelCandidate,
    *,
    answer_pass_rate: float,
    citation_validity: float,
    citation_presence: float,
    expected_citations: float,
    required_text: float,
    forbidden_text: float,
    supported_claims: float,
    answer_shape: float,
    evidence_coverage: float,
    required_label: float,
    min_answer_domains: int,
    min_answer_tasks: int,
    replay_coverage: ReplayCoverage,
) -> ModelEvalResult:
    output_path = output_dir / f"{candidate.candidate_id}.answers.jsonl"
    report_path = output_dir / f"{candidate.candidate_id}.report.json"
    if credential_failure := _candidate_credential_failure(candidate):
        return ModelEvalResult(
            candidate_id=candidate.candidate_id,
            group=candidate.group,
            model=candidate.model,
            base_url=candidate.base_url,
            status=2,
            output=str(output_path),
            report_path=str(report_path),
            cases=None,
            domains=(),
            tasks=(),
            pass_rate=None,
            citation_validity_rate=None,
            citation_presence_rate=None,
            expected_citation_rate=None,
            required_text_rate=None,
            forbidden_text_rate=None,
            supported_claim_rate=None,
            answer_shape_rate=None,
            evidence_coverage_rate=None,
            required_label_rate=None,
            error=credential_failure,
        )
    config = ChatConfig(
        api_key=candidate.api_key,
        base_url=candidate.base_url,
        model=candidate.model,
        max_tokens=candidate.max_tokens,
        rag_context_budget=candidate.rag_context_budget,
        feature_flags=frozenset({"disable_memory_extraction"}),
    )
    if candidate.provider_slug:
        config.apply_provider_reference(candidate.provider_slug, candidate.provider_env)
    try:
        status = _run_replay_eval_with_timeout(
            armory_path,
            replay_dataset,
            output_path,
            config,
            timeout_seconds=candidate.timeout_seconds,
            answer_pass_rate=answer_pass_rate,
            citation_validity=citation_validity,
            citation_presence=citation_presence,
            expected_citations=expected_citations,
            required_text=required_text,
            forbidden_text=forbidden_text,
            supported_claims=supported_claims,
            answer_shape=answer_shape,
            evidence_coverage=evidence_coverage,
            required_label=required_label,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            report_path=report_path,
        )
        metrics = _report_metrics(report_path)
        metric_failures = _coverage_failures(
            metrics,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            replay_coverage=replay_coverage,
        ) + _metric_failures(
            metrics,
            {
                "pass_rate": answer_pass_rate,
                "citation_validity_rate": citation_validity,
                "citation_presence_rate": citation_presence,
                "expected_citation_rate": expected_citations,
                "required_text_rate": required_text,
                "forbidden_text_rate": forbidden_text,
                "supported_claim_rate": supported_claims,
                "answer_shape_rate": answer_shape,
                "evidence_coverage_rate": evidence_coverage,
                "required_label_rate": required_label,
            },
        )
        error = "; ".join(metric_failures)
        if metric_failures:
            status = 1
        return ModelEvalResult(
            candidate_id=candidate.candidate_id,
            group=candidate.group,
            model=candidate.model,
            base_url=candidate.base_url,
            status=status,
            output=str(output_path),
            report_path=str(report_path),
            cases=metrics.cases,
            domains=metrics.domains,
            tasks=metrics.tasks,
            pass_rate=metrics.pass_rate,
            citation_validity_rate=metrics.citation_validity_rate,
            citation_presence_rate=metrics.citation_presence_rate,
            expected_citation_rate=metrics.expected_citation_rate,
            required_text_rate=metrics.required_text_rate,
            forbidden_text_rate=metrics.forbidden_text_rate,
            supported_claim_rate=metrics.supported_claim_rate,
            answer_shape_rate=metrics.answer_shape_rate,
            evidence_coverage_rate=metrics.evidence_coverage_rate,
            required_label_rate=metrics.required_label_rate,
            error=error,
        )
    except (_CandidateTimeoutError, EngineError, OSError, TypeError, ValueError) as exc:
        return ModelEvalResult(
            candidate_id=candidate.candidate_id,
            group=candidate.group,
            model=candidate.model,
            base_url=candidate.base_url,
            status=2,
            output=str(output_path),
            report_path=str(report_path),
            cases=None,
            domains=(),
            tasks=(),
            pass_rate=None,
            citation_validity_rate=None,
            citation_presence_rate=None,
            expected_citation_rate=None,
            required_text_rate=None,
            forbidden_text_rate=None,
            supported_claim_rate=None,
            answer_shape_rate=None,
            evidence_coverage_rate=None,
            required_label_rate=None,
            error=str(exc),
        )


def _candidate_credential_failures(candidates: Sequence[ModelCandidate]) -> tuple[str, ...]:
    return tuple(
        failure
        for candidate in candidates
        if (failure := _candidate_credential_failure(candidate))
    )


def _run_replay_eval_with_timeout(
    armory_path: Path,
    replay_dataset: Path,
    output_path: Path,
    config: ChatConfig,
    *,
    timeout_seconds: int,
    answer_pass_rate: float,
    citation_validity: float,
    citation_presence: float,
    expected_citations: float,
    required_text: float,
    forbidden_text: float,
    supported_claims: float,
    answer_shape: float,
    evidence_coverage: float,
    required_label: float,
    min_answer_domains: int,
    min_answer_tasks: int,
    report_path: Path,
) -> int:
    if timeout_seconds <= 0:
        return _run_replay_eval(
            armory_path,
            replay_dataset,
            output_path,
            config,
            answer_pass_rate=answer_pass_rate,
            citation_validity=citation_validity,
            citation_presence=citation_presence,
            expected_citations=expected_citations,
            required_text=required_text,
            forbidden_text=forbidden_text,
            supported_claims=supported_claims,
            answer_shape=answer_shape,
            evidence_coverage=evidence_coverage,
            required_label=required_label,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            report_path=report_path,
        )

    start_method = "fork" if "fork" in multiprocessing.get_all_start_methods() else "spawn"
    context = multiprocessing.get_context(start_method)
    queue = context.Queue()
    process_factory = cast("type[multiprocessing.Process]", getattr(context, "Process"))  # noqa: B009
    process = process_factory(
        target=_run_replay_eval_worker,
        args=(
            queue,
            armory_path,
            replay_dataset,
            output_path,
            config,
            answer_pass_rate,
            citation_validity,
            citation_presence,
            expected_citations,
            required_text,
            forbidden_text,
            supported_claims,
            answer_shape,
            evidence_coverage,
            required_label,
            min_answer_domains,
            min_answer_tasks,
            report_path,
        ),
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5)
        raise _CandidateTimeoutError(f"candidate timed out after {timeout_seconds} second(s)")
    if queue.empty():
        raise ValueError("candidate worker exited without a report")
    status, payload = cast("tuple[str, object]", queue.get())
    if status == "ok":
        return cast("int", payload)
    raise ValueError(str(payload))


def _run_replay_eval_worker(
    queue: object,
    armory_path: Path,
    replay_dataset: Path,
    output_path: Path,
    config: ChatConfig,
    answer_pass_rate: float,
    citation_validity: float,
    citation_presence: float,
    expected_citations: float,
    required_text: float,
    forbidden_text: float,
    supported_claims: float,
    answer_shape: float,
    evidence_coverage: float,
    required_label: float,
    min_answer_domains: int,
    min_answer_tasks: int,
    report_path: Path,
) -> None:
    result_queue = cast("multiprocessing.queues.Queue", queue)
    try:
        result_queue.put(
            (
                "ok",
                _run_replay_eval(
                    armory_path,
                    replay_dataset,
                    output_path,
                    config,
                    answer_pass_rate=answer_pass_rate,
                    citation_validity=citation_validity,
                    citation_presence=citation_presence,
                    expected_citations=expected_citations,
                    required_text=required_text,
                    forbidden_text=forbidden_text,
                    supported_claims=supported_claims,
                    answer_shape=answer_shape,
                    evidence_coverage=evidence_coverage,
                    required_label=required_label,
                    min_answer_domains=min_answer_domains,
                    min_answer_tasks=min_answer_tasks,
                    report_path=report_path,
                ),
            )
        )
    except Exception as exc:
        result_queue.put(("error", f"{type(exc).__name__}: {exc}"))


def _run_replay_eval(
    armory_path: Path,
    replay_dataset: Path,
    output_path: Path,
    config: ChatConfig,
    *,
    answer_pass_rate: float,
    citation_validity: float,
    citation_presence: float,
    expected_citations: float,
    required_text: float,
    forbidden_text: float,
    supported_claims: float,
    answer_shape: float,
    evidence_coverage: float,
    required_label: float,
    min_answer_domains: int,
    min_answer_tasks: int,
    report_path: Path,
) -> int:
    return run_replay_answer_eval.run_replay_answer_eval(
        armory_path,
        replay_dataset,
        output_path,
        config,
        answer_pass_rate=answer_pass_rate,
        citation_validity=citation_validity,
        citation_presence=citation_presence,
        expected_citations=expected_citations,
        required_text=required_text,
        forbidden_text=forbidden_text,
        supported_claims=supported_claims,
        answer_shape=answer_shape,
        evidence_coverage=evidence_coverage,
        required_label=required_label,
        min_answer_domains=min_answer_domains,
        min_answer_tasks=min_answer_tasks,
        report_path=report_path,
    )


def _candidate_credential_failure(candidate: ModelCandidate) -> str:
    if candidate.provider_slug == "openai-codex" and load_credentials("openai-codex") is not None:
        return ""
    if candidate.provider_slug and candidate.provider_env:
        return ""
    if candidate.api_key:
        return ""
    if candidate.base_url:
        return ""
    return (
        f"candidate {candidate.candidate_id} has no api_key and no base_url; "
        "set api_key/api_key_env or an OpenAI-compatible local base_url"
    )


def _report_metrics(path: Path) -> CandidateReportMetrics:
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = payload.get("report") if isinstance(payload, dict) else None
    if not isinstance(report, dict):
        raise TypeError(f"candidate report missing report object: {path}")
    return CandidateReportMetrics(
        cases=_int_metric(report.get("cases")),
        domains=_string_tuple_metric(report.get("domains")),
        tasks=_string_tuple_metric(report.get("tasks")),
        pass_rate=_float_metric(report.get("pass_rate")),
        citation_validity_rate=_float_metric(report.get("citation_validity_rate")),
        citation_presence_rate=_float_metric(report.get("citation_presence_rate")),
        expected_citation_rate=_float_metric(report.get("expected_citation_rate")),
        required_text_rate=_float_metric(report.get("required_text_rate")),
        forbidden_text_rate=_float_metric(report.get("forbidden_text_rate")),
        supported_claim_rate=_float_metric(report.get("supported_claim_rate")),
        answer_shape_rate=_float_metric(report.get("answer_shape_rate")),
        evidence_coverage_rate=_float_metric(report.get("evidence_coverage_rate")),
        required_label_rate=_float_metric(report.get("required_label_rate")),
    )


def _replay_coverage(
    path: Path,
    *,
    min_answer_domains: int,
    min_answer_tasks: int,
) -> ReplayCoverage:
    cases = replay_answer_benchmark.load_cases(path)
    case_ids = tuple(case.case_id for case in cases)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("replay dataset case ids must be unique")
    domains = tuple(sorted({case.domain for case in cases if case.domain}))
    if len(domains) < min_answer_domains:
        raise ValueError(
            "replay dataset must cover at least "
            f"{min_answer_domains} labelled domains; found {len(domains)}"
        )
    tasks = tuple(sorted({case.task for case in cases if case.task}))
    if len(tasks) < min_answer_tasks:
        raise ValueError(
            "replay dataset must cover at least "
            f"{min_answer_tasks} labelled answer tasks; found {len(tasks)}"
        )
    if not any(case.task == "material-overview" for case in cases):
        raise ValueError("replay dataset must include a material-overview case")
    if not replay_answer_benchmark.has_shaped_material_overview_case(cases):
        raise ValueError(
            "replay material-overview case must include word, citation, source, bullet, "
            "and cited-bullet shape constraints"
        )
    return ReplayCoverage(
        case_count=len(cases),
        domains=domains,
        tasks=tasks,
    )


def _int_metric(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None


def _string_tuple_metric(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _float_metric(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    return float(value) if isinstance(value, int | float) else None


def _metric_failures(
    metrics: CandidateReportMetrics,
    thresholds: dict[str, float],
) -> tuple[str, ...]:
    failures: list[str] = []
    for metric, threshold in thresholds.items():
        value = _candidate_rate_metric(metrics, metric)
        label = _METRIC_LABELS[metric]
        if value is None:
            failures.append(f"{label} metric missing")
        elif value < threshold:
            failures.append(f"{label} {value:.3f} below {threshold:.3f}")
    return tuple(failures)


def _coverage_failures(
    metrics: CandidateReportMetrics,
    *,
    min_answer_domains: int,
    min_answer_tasks: int,
    replay_coverage: ReplayCoverage,
) -> tuple[str, ...]:
    failures: list[str] = []
    if metrics.cases is None or metrics.cases <= 0:
        failures.append("case count missing")
    elif metrics.cases != replay_coverage.case_count:
        failures.append(
            f"case count {metrics.cases} does not match replay dataset "
            f"{replay_coverage.case_count}"
        )
    if len(metrics.domains) < min_answer_domains:
        failures.append(f"domain coverage {len(metrics.domains)} below {min_answer_domains}")
    elif metrics.domains != replay_coverage.domains:
        failures.append(
            "domain coverage does not match replay dataset "
            f"(actual={', '.join(metrics.domains)}, "
            f"expected={', '.join(replay_coverage.domains)})"
        )
    if len(metrics.tasks) < min_answer_tasks:
        failures.append(f"task coverage {len(metrics.tasks)} below {min_answer_tasks}")
    elif metrics.tasks != replay_coverage.tasks:
        failures.append(
            "task coverage does not match replay dataset "
            f"(actual={', '.join(metrics.tasks)}, expected={', '.join(replay_coverage.tasks)})"
        )
    return tuple(failures)


def _candidate_rate_metric(metrics: CandidateReportMetrics, metric: str) -> float | None:
    if metric == "pass_rate":
        return metrics.pass_rate
    if metric == "citation_validity_rate":
        return metrics.citation_validity_rate
    if metric == "citation_presence_rate":
        return metrics.citation_presence_rate
    if metric == "expected_citation_rate":
        return metrics.expected_citation_rate
    if metric == "required_text_rate":
        return metrics.required_text_rate
    if metric == "forbidden_text_rate":
        return metrics.forbidden_text_rate
    if metric == "supported_claim_rate":
        return metrics.supported_claim_rate
    if metric == "answer_shape_rate":
        return metrics.answer_shape_rate
    if metric == "evidence_coverage_rate":
        return metrics.evidence_coverage_rate
    if metric == "required_label_rate":
        return metrics.required_label_rate
    raise KeyError(metric)


def _write_json_report(path: Path, report: ModelEvalMatrixReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def print_text_report(report: ModelEvalMatrixReport) -> None:
    """Print a concise model-eval matrix report."""
    print(f"Model eval matrix: {report.candidates} candidate(s)")
    print(f"groups={', '.join(report.groups)}")
    if report.replay_cases:
        print(f"replay_cases={report.replay_cases}")
        print(f"replay_domains={', '.join(report.replay_domains)}")
        print(f"replay_tasks={', '.join(report.replay_tasks)}")
    for result in report.results:
        status = "PASS" if result.status == 0 else "FAIL"
        pass_rate = "n/a" if result.pass_rate is None else f"{result.pass_rate:.3f}"
        print(
            f"{status} {result.candidate_id} "
            f"[{result.group}] model={result.model} pass_rate={pass_rate}"
        )
        if result.error:
            print(f"  error: {result.error}")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def _validate_positive(value: int, label: str, parser: argparse.ArgumentParser) -> None:
    if value <= 0:
        parser.error(f"{label} must be positive")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL replay prompts")
    parser.add_argument("matrix", type=Path, help="JSON model matrix")
    parser.add_argument("output_dir", type=Path, help="Directory for fixtures and reports")
    parser.add_argument(
        "--required-group",
        action="append",
        dest="required_groups",
        help="Required candidate group. Defaults to local and frontier; repeat as needed.",
    )
    parser.add_argument("--min-answer-pass-rate", type=float, default=1.0)
    parser.add_argument("--min-citation-validity", type=float, default=1.0)
    parser.add_argument("--min-citation-presence", type=float, default=1.0)
    parser.add_argument("--min-expected-citations", type=float, default=1.0)
    parser.add_argument("--min-required-text", type=float, default=1.0)
    parser.add_argument("--min-forbidden-text", type=float, default=1.0)
    parser.add_argument("--min-supported-claims", type=float, default=1.0)
    parser.add_argument("--min-answer-shape", type=float, default=1.0)
    parser.add_argument("--min-evidence-coverage", type=float, default=1.0)
    parser.add_argument("--min-required-label", type=float, default=1.0)
    parser.add_argument("--min-answer-domains", type=int, default=3)
    parser.add_argument("--min-answer-tasks", type=int, default=3)
    parser.add_argument("--json-report", type=Path, default=None)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate candidate groups and write an optional report without calling models.",
    )
    parser.add_argument(
        "--validate-inputs",
        action="store_true",
        help=(
            "Validate candidate groups, armory path, and replay dataset breadth without "
            "calling models."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    matrix = cast("Path", args.matrix).expanduser().resolve()
    output_dir = cast("Path", args.output_dir).expanduser().resolve()
    required_groups = tuple(
        cast("list[str] | None", args.required_groups) or DEFAULT_REQUIRED_GROUPS
    )
    answer_pass_rate = cast("float", args.min_answer_pass_rate)
    citation_validity = cast("float", args.min_citation_validity)
    citation_presence = cast("float", args.min_citation_presence)
    expected_citations = cast("float", args.min_expected_citations)
    required_text = cast("float", args.min_required_text)
    forbidden_text = cast("float", args.min_forbidden_text)
    supported_claims = cast("float", args.min_supported_claims)
    answer_shape = cast("float", args.min_answer_shape)
    evidence_coverage = cast("float", args.min_evidence_coverage)
    required_label = cast("float", args.min_required_label)
    min_answer_domains = cast("int", args.min_answer_domains)
    min_answer_tasks = cast("int", args.min_answer_tasks)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
    validate_only = bool(args.validate_only)
    validate_inputs = bool(args.validate_inputs)

    for value, label in (
        (answer_pass_rate, "--min-answer-pass-rate"),
        (citation_validity, "--min-citation-validity"),
        (citation_presence, "--min-citation-presence"),
        (expected_citations, "--min-expected-citations"),
        (required_text, "--min-required-text"),
        (forbidden_text, "--min-forbidden-text"),
        (supported_claims, "--min-supported-claims"),
        (answer_shape, "--min-answer-shape"),
        (evidence_coverage, "--min-evidence-coverage"),
        (required_label, "--min-required-label"),
    ):
        _validate_rate(value, label, parser)
    _validate_positive(min_answer_domains, "--min-answer-domains", parser)
    _validate_positive(min_answer_tasks, "--min-answer-tasks", parser)

    try:
        candidates = load_candidates(matrix)
        if validate_inputs:
            report = validate_model_eval_inputs(
                armory,
                dataset,
                output_dir,
                candidates,
                required_groups=required_groups,
                min_answer_domains=min_answer_domains,
                min_answer_tasks=min_answer_tasks,
            )
            if json_report is not None:
                _write_json_report(json_report, report)
            print_text_report(report)
            return report.status
        if validate_only:
            report = validate_model_eval_matrix(
                candidates,
                required_groups=required_groups,
            )
            if json_report is not None:
                _write_json_report(json_report, report)
            print_text_report(report)
            return report.status
        return run_model_eval_matrix(
            armory,
            dataset,
            output_dir,
            candidates,
            required_groups=required_groups,
            answer_pass_rate=answer_pass_rate,
            citation_validity=citation_validity,
            citation_presence=citation_presence,
            expected_citations=expected_citations,
            required_text=required_text,
            forbidden_text=forbidden_text,
            supported_claims=supported_claims,
            answer_shape=answer_shape,
            evidence_coverage=evidence_coverage,
            required_label=required_label,
            min_answer_domains=min_answer_domains,
            min_answer_tasks=min_answer_tasks,
            report_path=json_report,
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"model eval matrix error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
