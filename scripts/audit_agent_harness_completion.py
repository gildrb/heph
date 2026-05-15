"""Audit whether the academic agent harness objective has enough proof.

This is stricter than the deterministic benchmark suite. It checks that the
native harness artifacts exist, then optionally verifies external real-corpus
and model-backed reports. Without those external reports, the audit should fail
with explicit missing evidence instead of treating synthetic fixtures as final
proof.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from scripts import (
    benchmark_academic_items,
    benchmark_answers,
    benchmark_chat_events,
    benchmark_prompt_cache,
    replay_answer_benchmark,
    run_benchmark_suite,
    run_model_eval_matrix,
    validate_benchmark_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_FRAMEWORKS = ("langchain", "langgraph", "llama-index", "llama_index")
FORBIDDEN_FIXTURE_COURSE_TERMS = re.compile(
    r"\b(?:"
    r"fixture_private_name|fixture_private_course|fixture_private_institution"
    r")\b"
)
DEFAULT_REAL_MIN_DOCUMENTS = 40
DEFAULT_REAL_MIN_DOMAINS = 5
DEFAULT_REAL_MIN_DOCUMENT_TYPES = 8
DEFAULT_REAL_MIN_STRESSORS = 16
DEFAULT_REQUIRED_REAL_STRESSORS = (
    "real-pdf",
    "ocr-noise",
    "table-heavy",
    "multi-column",
    "multilingual",
)
DEFAULT_FORBIDDEN_REAL_KNOWN_LIMITS = (
    "synthetic",
    "no real scanned pdfs",
    "no table-heavy",
    "generated scaffold",
    "provenance requires human review",
    "require human review",
    "no model-backed",
)
DEFAULT_REQUIRED_PREFLIGHT_ROLES = ("assignment", "past_exam", "slides")
DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SOURCE_COVERAGE = 0.4
DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SAMPLE_CAP = 32
DEFAULT_PREFLIGHT_SAMPLE_CAP_MAX_COVERAGE_FLOOR = 0.4
DEFAULT_REQUIRED_REAL_DATASET_KINDS = (
    "chat-events",
    "chat-event-answer-expectation",
    "model-replay-prompts",
)
DEFAULT_REQUIRED_MODEL_GROUPS = ("local", "frontier")
DEFAULT_REQUIRED_MODEL_METRICS = {
    "pass_rate": 1.0,
    "citation_validity_rate": 1.0,
    "citation_presence_rate": 1.0,
    "expected_citation_rate": 1.0,
    "required_text_rate": 1.0,
    "forbidden_text_rate": 1.0,
    "supported_claim_rate": 1.0,
    "answer_shape_rate": 1.0,
    "evidence_coverage_rate": 1.0,
    "required_label_rate": 1.0,
}
DEFAULT_REQUIRED_CHILD_THRESHOLDS = {
    "answer_pass_rate": 1.0,
    "citation_validity": 1.0,
    "citation_presence": 1.0,
    "expected_citations": 1.0,
    "required_text": 1.0,
    "forbidden_text": 1.0,
    "supported_claims": 1.0,
    "answer_shape": 1.0,
    "evidence_coverage": 1.0,
    "required_label": 1.0,
}
DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS = {
    "min_answer_domains": 3,
    "min_answer_tasks": 3,
}
HARNESS_GENERALITY_SCRIPT_EXCLUDES = frozenset(
    {
        "audit_agent_harness_completion.py",
    }
)


@dataclass(frozen=True, slots=True)
class AuditItem:
    requirement: str
    status: str
    evidence: str


@dataclass(frozen=True, slots=True)
class HarnessCompletionAudit:
    status: str
    items: tuple[AuditItem, ...]
    missing: tuple[str, ...]
    next_steps: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.status == "complete"


@dataclass(frozen=True, slots=True)
class ReplayDatasetAudit:
    error: str
    case_count: int
    case_ids: tuple[str, ...]
    domains: tuple[str, ...]
    tasks: tuple[str, ...]


def _repo_file(path: str) -> Path:
    return REPO_ROOT / path


def _file_exists(path: str) -> AuditItem:
    target = _repo_file(path)
    status = "covered" if target.exists() else "missing"
    return AuditItem(path, status, str(target))


def _model_matrix_example_item() -> AuditItem:
    requirement = "Model matrix example declares local/frontier responsibilities"
    path = _repo_file("benchmarks/model-matrix.example.json")
    if not path.is_file():
        return AuditItem(requirement, "missing", f"model matrix example missing: {path}")
    try:
        candidates = run_model_eval_matrix.load_candidates(path)
        report = run_model_eval_matrix.validate_model_eval_matrix(candidates)
    except (OSError, TypeError, ValueError) as exc:
        return AuditItem(requirement, "missing", f"model matrix example invalid: {exc}")
    if report.status != 0:
        return AuditItem(requirement, "missing", "; ".join(report.failures))

    required_groups = set(run_model_eval_matrix.DEFAULT_REQUIRED_GROUPS)
    responsibilities_by_group = {
        group: sum(
            len(candidate.responsibilities) for candidate in candidates if candidate.group == group
        )
        for group in required_groups
    }
    missing_responsibilities = sorted(
        group for group, count in responsibilities_by_group.items() if count == 0
    )
    if missing_responsibilities:
        return AuditItem(
            requirement,
            "missing",
            "missing responsibilities for group(s): " + ", ".join(missing_responsibilities),
        )

    evidence = ", ".join(
        f"{group}_responsibilities={responsibilities_by_group[group]}"
        for group in sorted(required_groups)
    )
    return AuditItem(requirement, "covered", f"{path}; {evidence}")


def _framework_policy_item() -> AuditItem:
    checked = []
    for path in (_repo_file("pyproject.toml"), _repo_file("uv.lock")):
        if path.is_file():
            checked.append(path)
            text = path.read_text(encoding="utf-8").lower()
            if any(framework in text for framework in FORBIDDEN_FRAMEWORKS):
                return AuditItem(
                    "No LangChain/LangGraph/LlamaIndex dependencies",
                    "missing",
                    f"forbidden framework reference found in {path}",
                )
    return AuditItem(
        "No LangChain/LangGraph/LlamaIndex dependencies",
        "covered",
        ", ".join(str(path) for path in checked),
    )


def _runtime_generality_item() -> AuditItem:
    offenders = [
        f"{path.relative_to(REPO_ROOT)} contains {match.group(0)!r}"
        for path in sorted(_repo_file("hephaistos").rglob("*.py"))
        for match in FORBIDDEN_FIXTURE_COURSE_TERMS.finditer(
            path.read_text(encoding="utf-8").casefold()
        )
    ]
    requirement = "No fixture-specific course terms in runtime harness code"
    if offenders:
        return AuditItem(requirement, "missing", "; ".join(offenders[:20]))
    return AuditItem(requirement, "covered", str(_repo_file("hephaistos")))


def _script_generality_item() -> AuditItem:
    scripts_root = _repo_file("scripts")
    offenders = [
        f"{path.relative_to(REPO_ROOT)} contains {match.group(0)!r}"
        for path in sorted(scripts_root.rglob("*.py"))
        if path.name not in HARNESS_GENERALITY_SCRIPT_EXCLUDES
        for match in FORBIDDEN_FIXTURE_COURSE_TERMS.finditer(
            path.read_text(encoding="utf-8").casefold()
        )
    ]
    requirement = "No fixture-specific course terms in non-fixture harness scripts"
    if offenders:
        return AuditItem(requirement, "missing", "; ".join(offenders[:20]))
    return AuditItem(requirement, "covered", str(scripts_root))


def _deterministic_chat_event_suite_item() -> AuditItem:
    requirement = "Deterministic suite verifies public chat JSONL harness events"
    suite = _repo_file("benchmarks/academic")
    manifest_path = suite / "manifest.json"
    events_path = suite / "chat_events.jsonl"
    runtime_events_path = suite / "chat_events_runtime.jsonl"
    expectation_path = suite / "chat_event_expectation.json"
    if not manifest_path.is_file():
        return AuditItem(requirement, "missing", f"manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return AuditItem(requirement, "missing", f"could not read manifest: {exc}")
    if not isinstance(manifest, dict):
        return AuditItem(requirement, "missing", "benchmark manifest must be an object")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        return AuditItem(requirement, "missing", "benchmark manifest datasets missing")
    dataset_kinds = {
        dataset.get("kind"): dataset.get("path")
        for dataset in datasets
        if isinstance(dataset, dict)
        and isinstance(dataset.get("kind"), str)
        and isinstance(dataset.get("path"), str)
    }
    if dataset_kinds.get("chat-events") != "chat_events.jsonl":
        return AuditItem(requirement, "missing", "manifest missing chat-events dataset")
    if dataset_kinds.get("chat-events-runtime") != "chat_events_runtime.jsonl":
        return AuditItem(requirement, "missing", "manifest missing chat-events-runtime dataset")
    if dataset_kinds.get("chat-event-answer-expectation") != "chat_event_expectation.json":
        return AuditItem(
            requirement,
            "missing",
            "manifest missing chat-event-answer-expectation dataset",
        )
    if not events_path.is_file():
        return AuditItem(requirement, "missing", f"chat event fixture missing: {events_path}")
    if not runtime_events_path.is_file():
        return AuditItem(
            requirement,
            "missing",
            f"chat runtime event fixture missing: {runtime_events_path}",
        )
    if not expectation_path.is_file():
        return AuditItem(
            requirement,
            "missing",
            f"chat event expectation missing: {expectation_path}",
        )
    try:
        runtime_events = benchmark_chat_events.load_events(runtime_events_path)
        report = benchmark_chat_events.run_chat_event_benchmark(
            benchmark_chat_events.load_events(events_path),
            expectation=benchmark_chat_events.load_expectation(expectation_path),
        )
        runtime_report = benchmark_chat_events.run_chat_event_benchmark(
            runtime_events,
            expectation=benchmark_chat_events.load_expectation(expectation_path),
        )
    except (OSError, TypeError, ValueError) as exc:
        return AuditItem(requirement, "missing", f"chat event verifier failed: {exc}")
    if report.failures:
        return AuditItem(requirement, "missing", "; ".join(report.failures))
    if runtime_report.failures:
        return AuditItem(requirement, "missing", "; ".join(runtime_report.failures))
    if not runtime_report.has_tool_runtime:
        return AuditItem(requirement, "missing", "runtime chat event fixture lacks tool_runtime")
    runtime_has_repeated_call = any(
        event["type"] == "notice"
        and event.get("code") == "tool_runtime"
        and isinstance(event.get("metadata"), dict)
        and event["metadata"].get("reason") == "repeated_call"
        for event in runtime_events
    )
    answer_pass_rate = report.answer_pass_rate if report.answer_pass_rate is not None else 0.0
    return AuditItem(
        requirement,
        "covered",
        (
            f"{events_path}: reading={report.has_reading}, evidence={report.has_evidence}, "
            f"writing={report.has_writing}, complete={report.has_turn_complete}, "
            f"consistent={report.has_consistent_completion}, "
            f"material_operation={report.has_material_operation}, "
            f"material_operation_metadata_rate={report.material_operation_metadata_rate:.3f}, "
            f"metadata={report.has_evidence_metadata}, "
            f"tool_runtime_metadata_rate={report.tool_runtime_metadata_rate:.3f}, "
            f"runtime_fixture_tool_runtime={runtime_report.has_tool_runtime}, "
            "runtime_fixture_material_operation_metadata_rate="
            f"{runtime_report.material_operation_metadata_rate:.3f}, "
            f"runtime_fixture_metadata_rate={runtime_report.tool_runtime_metadata_rate:.3f}, "
            f"runtime_fixture_repeated_call={runtime_has_repeated_call}, "
            "runtime_fixture_acceptance_criteria_metadata_rate="
            f"{runtime_report.acceptance_criteria_metadata_rate:.3f}, "
            f"answer_pass_rate={answer_pass_rate:.3f}"
        ),
    )


def _deterministic_benchmark_suite_item() -> AuditItem:
    requirement = "Deterministic academic benchmark suite passes"
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = run_benchmark_suite.run_suite()
    except (OSError, TypeError, ValueError) as exc:
        return AuditItem(requirement, "missing", f"benchmark suite failed: {exc}")
    if status != 0:
        return AuditItem(requirement, "missing", f"benchmark suite status is {status}")
    return AuditItem(
        requirement,
        "covered",
        _deterministic_suite_evidence(),
    )


def _deterministic_suite_evidence() -> str:
    suite = run_benchmark_suite.DEFAULT_SUITE
    academic_items_dataset = suite / "academic_items.jsonl"
    if not academic_items_dataset.is_file():
        return str(suite)
    try:
        prompt_cache_report = benchmark_prompt_cache.run_benchmark()
        study_intent_report = run_benchmark_suite.study_intent_contract_report()
        with tempfile.TemporaryDirectory(prefix="heph-audit-academic-items-") as tmp:
            armory = Path(tmp) / "armory"
            shutil.copytree(suite / "armory", armory)
            academic_report = benchmark_academic_items.run_benchmark(
                armory,
                benchmark_academic_items.load_cases(academic_items_dataset),
            )
    except (OSError, TypeError, ValueError) as exc:
        return f"{suite}; academic_item_metrics_unavailable={exc}"
    return (
        f"{suite}: academic_items_pass_rate={academic_report.pass_rate:.3f}, "
        f"academic_question_type_count={academic_report.question_type_count}, "
        f"academic_grounded_question_rate={academic_report.grounded_question_rate:.3f}, "
        "academic_canonical_source_label_rate="
        f"{academic_report.canonical_source_label_rate:.3f}, "
        f"study_intent_contract_passed={study_intent_report.passed}, "
        "study_intent_required_intents="
        f"{','.join(study_intent_report.required_intents)}, "
        "study_intent_parsed_intents="
        f"{','.join(study_intent_report.parsed_intents)}, "
        f"prompt_cache_pass_rate={prompt_cache_report.pass_rate:.3f}, "
        f"prompt_cache_stable_hash_reuse={prompt_cache_report.stable_hash_reuse_rate:.3f}"
    )


def _real_corpus_item(manifest_path: Path | None) -> AuditItem:
    requirement = "Large real/public or permissioned academic corpus"
    if manifest_path is None:
        return AuditItem(
            requirement,
            "missing",
            "provide --real-manifest for a non-synthetic corpus manifest",
        )
    try:
        report = validate_benchmark_manifest.validate_manifest(
            manifest_path,
            min_documents=DEFAULT_REAL_MIN_DOCUMENTS,
            min_domains=DEFAULT_REAL_MIN_DOMAINS,
            min_document_types=DEFAULT_REAL_MIN_DOCUMENT_TYPES,
            min_stressors=DEFAULT_REAL_MIN_STRESSORS,
            required_stressors=DEFAULT_REQUIRED_REAL_STRESSORS,
            forbid_known_limit=DEFAULT_FORBIDDEN_REAL_KNOWN_LIMITS,
            require_document_provenance=True,
        )
    except (OSError, TypeError, ValueError) as exc:
        return AuditItem(requirement, "missing", str(exc))
    if report.corpus_kind == "synthetic-snippets":
        return AuditItem(requirement, "missing", "real corpus manifest is still synthetic")
    dataset_failures = _manifest_required_dataset_failures(
        manifest_path,
        DEFAULT_REQUIRED_REAL_DATASET_KINDS,
    )
    if dataset_failures:
        return AuditItem(requirement, "missing", "; ".join(dataset_failures))
    return AuditItem(
        requirement,
        "covered",
        (
            f"{manifest_path}: documents={report.documents}, domains={len(report.domains)}, "
            f"document_types={len(report.document_types)}, stressors={len(report.stressors)}"
        ),
    )


def _real_chat_event_item(manifest_path: Path | None) -> AuditItem:
    requirement = "Real corpus public chat JSONL harness events pass"
    if manifest_path is None:
        return AuditItem(
            requirement,
            "missing",
            "provide --real-manifest with chat-events and chat-event-answer-expectation datasets",
        )
    event_paths = _manifest_dataset_paths(manifest_path, "chat-events")
    expectation_paths = _manifest_dataset_paths(manifest_path, "chat-event-answer-expectation")
    if not event_paths:
        return AuditItem(requirement, "missing", "real manifest missing chat-events dataset")
    if not expectation_paths:
        return AuditItem(
            requirement,
            "missing",
            "real manifest missing chat-event-answer-expectation dataset",
        )
    events_path = event_paths[0]
    expectation_path = expectation_paths[0]
    if not events_path.is_file():
        return AuditItem(requirement, "missing", f"real chat events file missing: {events_path}")
    if not expectation_path.is_file():
        return AuditItem(
            requirement,
            "missing",
            f"real chat event expectation file missing: {expectation_path}",
        )
    try:
        expectation = benchmark_chat_events.load_expectation(expectation_path)
        evidence_failure = _real_chat_expectation_evidence_failure(expectation)
        if evidence_failure:
            return AuditItem(requirement, "missing", evidence_failure)
        report = benchmark_chat_events.run_chat_event_benchmark(
            benchmark_chat_events.load_events(events_path),
            expectation=expectation,
        )
    except (OSError, TypeError, ValueError) as exc:
        return AuditItem(requirement, "missing", f"real chat event verifier failed: {exc}")
    if report.failures:
        return AuditItem(requirement, "missing", "; ".join(report.failures))
    answer_pass_rate = report.answer_pass_rate if report.answer_pass_rate is not None else 0.0
    return AuditItem(
        requirement,
        "covered",
        (
            f"{events_path}: reading={report.has_reading}, evidence={report.has_evidence}, "
            f"writing={report.has_writing}, complete={report.has_turn_complete}, "
            f"consistent={report.has_consistent_completion}, "
            f"material_operation={report.has_material_operation}, "
            f"material_operation_metadata_rate={report.material_operation_metadata_rate:.3f}, "
            f"metadata={report.has_evidence_metadata}, "
            f"tool_runtime_metadata_rate={report.tool_runtime_metadata_rate:.3f}, "
            "acceptance_criteria_metadata_rate="
            f"{report.acceptance_criteria_metadata_rate:.3f}, "
            f"answer_pass_rate={answer_pass_rate:.3f}"
        ),
    )


def _real_chat_expectation_evidence_failure(expectation: Mapping[str, object]) -> str:
    known_limits = expectation.get("known_limits", [])
    if not isinstance(known_limits, list):
        return "real chat event expectation known_limits must be a list when present"
    if known_limits:
        return "real chat event expectation has unresolved known_limits; review and remove them"
    evidence = expectation.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 2:
        return "real chat event expectation must include at least 2 evidence items"
    evidence_ids: set[str] = set()
    evidence_sources: set[str] = set()
    for index, raw_item in enumerate(evidence, start=1):
        if not isinstance(raw_item, dict):
            return f"real chat event expectation evidence item {index} must be an object"
        evidence_id = raw_item.get("id")
        source = raw_item.get("source")
        text = raw_item.get("text")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            return f"real chat event expectation evidence item {index} missing id"
        if not isinstance(source, str) or not source.strip():
            return f"real chat event expectation evidence item {index} missing source"
        if not isinstance(text, str) or not text.strip():
            return f"real chat event expectation evidence item {index} missing reviewed text"
        evidence_ids.add(evidence_id.strip().upper())
        evidence_sources.add(source.strip())
    expected_citations = expectation.get("expected_citations")
    if not isinstance(expected_citations, list) or len(expected_citations) < 2:
        return "real chat event expectation must include at least 2 expected citations"
    normalized_expected_citations = {
        citation.strip().upper()
        for citation in expected_citations
        if isinstance(citation, str) and citation.strip()
    }
    if len(normalized_expected_citations) != len(expected_citations):
        return "real chat event expectation expected citations must be non-empty strings"
    missing_expected = tuple(sorted(normalized_expected_citations - evidence_ids))
    if missing_expected:
        return (
            "real chat event expectation expected citation(s) missing reviewed evidence: "
            + ", ".join(missing_expected)
        )
    if len(evidence_sources) < 2:
        return "real chat event expectation must cover at least 2 distinct evidence sources"
    return ""


def _real_preflight_item(report_path: Path | None, manifest_path: Path | None) -> AuditItem:
    requirement = "Real corpus preflight passes extraction, indexing, and role smoke checks"
    if report_path is None:
        return AuditItem(
            requirement,
            "missing",
            "provide --real-preflight-report from scripts.run_real_corpus_preflight",
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return AuditItem(requirement, "missing", f"could not read preflight report: {exc}")
    except json.JSONDecodeError as exc:
        return AuditItem(requirement, "missing", f"invalid preflight report JSON: {exc}")
    if not isinstance(payload, dict):
        return AuditItem(requirement, "missing", "preflight report must be an object")
    status = payload.get("status")
    if status != 0:
        return AuditItem(requirement, "missing", f"preflight status is {status!r}")
    failures = payload.get("failures")
    if not isinstance(failures, list) or failures:
        return AuditItem(requirement, "missing", "preflight failures are present or malformed")
    reported_armory = payload.get("armory_path")
    if not isinstance(reported_armory, str) or not reported_armory:
        return AuditItem(requirement, "missing", "preflight report armory_path missing")
    armory_path = Path(reported_armory).expanduser()
    if not armory_path.is_dir():
        return AuditItem(
            requirement,
            "missing",
            f"preflight armory_path is not a directory: {armory_path}",
        )
    reported_manifest = payload.get("manifest_path")
    if not isinstance(reported_manifest, str) or not reported_manifest:
        return AuditItem(requirement, "missing", "preflight report manifest_path missing")
    reported_manifest_path = Path(reported_manifest).expanduser()
    if not reported_manifest_path.is_file():
        return AuditItem(
            requirement,
            "missing",
            f"preflight manifest_path is not a file: {reported_manifest_path}",
        )
    if (
        manifest_path is not None
        and reported_manifest_path.resolve() != manifest_path.expanduser().resolve()
    ):
        return AuditItem(
            requirement,
            "missing",
            "preflight report manifest_path does not match --real-manifest",
        )
    document_understanding = payload.get("document_understanding")
    if not isinstance(document_understanding, dict):
        return AuditItem(
            requirement,
            "missing",
            "preflight report missing document_understanding object",
        )
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        return AuditItem(requirement, "missing", "preflight report missing manifest object")
    manifest_documents = _int_field(manifest, "documents")
    if manifest_documents < DEFAULT_REAL_MIN_DOCUMENTS:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight manifest documents {manifest_documents} below "
                f"{DEFAULT_REAL_MIN_DOCUMENTS}"
            ),
        )
    if document_understanding.get("extraction_health_passed") is not True:
        return AuditItem(requirement, "missing", "preflight extraction health did not pass")
    visible_materials = _int_field(document_understanding, "visible_materials")
    indexed_documents = _int_field(document_understanding, "indexed_documents")
    chunks = _int_field(document_understanding, "chunks")
    if visible_materials != manifest_documents:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight manifest documents {manifest_documents} do not match "
                f"visible materials {visible_materials}"
            ),
        )
    if visible_materials < DEFAULT_REAL_MIN_DOCUMENTS:
        return AuditItem(
            requirement,
            "missing",
            f"preflight visible materials {visible_materials} below {DEFAULT_REAL_MIN_DOCUMENTS}",
        )
    if indexed_documents < visible_materials:
        return AuditItem(
            requirement,
            "missing",
            f"preflight indexed {indexed_documents} of {visible_materials} visible materials",
        )
    if chunks <= 0:
        return AuditItem(requirement, "missing", "preflight indexed no chunks")
    role_counts = document_understanding.get("role_counts")
    if not isinstance(role_counts, dict):
        return AuditItem(requirement, "missing", "preflight role_counts missing or malformed")
    counted_roles = sum(_int_field(role_counts, str(role)) for role in role_counts)
    if counted_roles != visible_materials:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight role counts cover {counted_roles} document(s), "
                f"expected {visible_materials}"
            ),
        )
    indexed_role_counts = document_understanding.get("indexed_role_counts")
    if not isinstance(indexed_role_counts, dict):
        return AuditItem(
            requirement,
            "missing",
            "preflight indexed_role_counts missing or malformed",
        )
    counted_indexed_roles = sum(
        _int_field(indexed_role_counts, str(role)) for role in indexed_role_counts
    )
    if counted_indexed_roles != indexed_documents:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight indexed role counts cover {counted_indexed_roles} "
                f"document(s), expected {indexed_documents}"
            ),
        )
    missing_roles = tuple(
        role
        for role in DEFAULT_REQUIRED_PREFLIGHT_ROLES
        if _int_field(indexed_role_counts, role) <= 0
    )
    if missing_roles:
        return AuditItem(
            requirement,
            "missing",
            "preflight missing required indexed role(s): " + ", ".join(missing_roles),
        )
    extraction_health_pass_rate = _float_field(
        document_understanding, "extraction_health_pass_rate"
    )
    if extraction_health_pass_rate < 1.0:
        return AuditItem(
            requirement,
            "missing",
            f"preflight extraction health pass rate {extraction_health_pass_rate:.3f} below 1.000",
        )
    overview_coverage = _float_field(document_understanding, "overview_source_coverage_rate")
    overview_sampled_sources = _int_field(document_understanding, "overview_sampled_sources")
    overview_total_sources = _int_field(document_understanding, "overview_total_sources")
    if overview_total_sources != indexed_documents:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight overview total sources {overview_total_sources} "
                f"does not match indexed documents {indexed_documents}"
            ),
        )
    if not 0 <= overview_sampled_sources <= overview_total_sources:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight overview sampled sources {overview_sampled_sources} "
                f"outside total {overview_total_sources}"
            ),
        )
    computed_overview_coverage = (
        overview_sampled_sources / overview_total_sources if overview_total_sources else 0.0
    )
    if abs(computed_overview_coverage - overview_coverage) > 0.001:
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight overview source coverage {overview_coverage:.3f} does not "
                f"match sampled/total {computed_overview_coverage:.3f}"
            ),
        )
    overview_sampled_enough = overview_sampled_sources >= min(
        overview_total_sources,
        DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SAMPLE_CAP,
    )
    overview_cap_satisfies_floor = (
        DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SOURCE_COVERAGE
        <= DEFAULT_PREFLIGHT_SAMPLE_CAP_MAX_COVERAGE_FLOOR
        and overview_sampled_enough
    )
    if (
        overview_coverage < DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SOURCE_COVERAGE
        and not overview_cap_satisfies_floor
    ):
        return AuditItem(
            requirement,
            "missing",
            (
                f"preflight overview source coverage {overview_coverage:.3f} below "
                f"{DEFAULT_REQUIRED_PREFLIGHT_OVERVIEW_SOURCE_COVERAGE:.3f}"
            ),
        )
    preflight_failures = document_understanding.get("failures")
    if not isinstance(preflight_failures, list) or preflight_failures:
        return AuditItem(
            requirement,
            "missing",
            "document-understanding failures are present or malformed",
        )
    return AuditItem(
        requirement,
        "covered",
        (
            f"{report_path}: indexed={indexed_documents}, chunks={chunks}, "
            f"health=passed, overview_sampled={overview_sampled_sources}/"
            f"{overview_total_sources}"
        ),
    )


def _int_field(payload: dict[object, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _float_field(payload: dict[object, object], field: str) -> float:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _preflight_armory_path(report_path: Path | None) -> Path | None:
    if report_path is None:
        return None
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    armory_path = payload.get("armory_path")
    if not isinstance(armory_path, str) or not armory_path.strip():
        return None
    return Path(armory_path).expanduser()


def _manifest_dataset_paths(manifest_path: Path | None, kind: str) -> tuple[Path, ...]:
    if manifest_path is None:
        return ()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict):
        return ()
    datasets = payload.get("datasets")
    if not isinstance(datasets, list):
        return ()
    manifest_dir = manifest_path.expanduser().resolve().parent
    paths: list[Path] = []
    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue
        if dataset.get("kind") != kind:
            continue
        path = dataset.get("path")
        if isinstance(path, str) and path.strip():
            paths.append((manifest_dir / path).resolve())
    return tuple(paths)


def _manifest_replay_dataset_paths(manifest_path: Path | None) -> tuple[Path, ...]:
    return _manifest_dataset_paths(manifest_path, "model-replay-prompts")


def _manifest_required_dataset_failures(
    manifest_path: Path,
    required_kinds: tuple[str, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    for kind in required_kinds:
        paths = _manifest_dataset_paths(manifest_path, kind)
        if not paths:
            failures.append(f"real corpus manifest missing dataset kind: {kind}")
    return tuple(failures)


def _model_matrix_item(
    report_path: Path | None,
    *,
    expected_armory_path: Path | None = None,
    expected_replay_dataset_paths: tuple[Path, ...] = (),
) -> AuditItem:
    requirement = "Model-backed replay eval passes local and frontier groups"
    if report_path is None:
        return AuditItem(
            requirement,
            "missing",
            "provide --model-matrix-report from scripts.run_model_eval_matrix",
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return AuditItem(requirement, "missing", f"could not read model report: {exc}")
    except json.JSONDecodeError as exc:
        return AuditItem(requirement, "missing", f"invalid model report JSON: {exc}")
    if not isinstance(payload, dict):
        return AuditItem(requirement, "missing", "model matrix report must be an object")
    status = payload.get("status")
    armory = payload.get("armory")
    replay_dataset = payload.get("replay_dataset")
    output_dir = payload.get("output_dir")
    groups = payload.get("groups")
    required_groups = payload.get("required_groups")
    results = payload.get("results")
    if status != 0:
        return AuditItem(requirement, "missing", f"model matrix status is {status!r}")
    if not isinstance(required_groups, list) or set(DEFAULT_REQUIRED_MODEL_GROUPS) != {
        group for group in required_groups if isinstance(group, str)
    }:
        return AuditItem(
            requirement,
            "missing",
            "model matrix required_groups must be exactly local/frontier",
        )
    if not isinstance(groups, list) or not set(DEFAULT_REQUIRED_MODEL_GROUPS) <= {
        group for group in groups if isinstance(group, str)
    }:
        return AuditItem(requirement, "missing", "model matrix lacks local/frontier groups")
    if not isinstance(results, list) or not results:
        return AuditItem(requirement, "missing", "model matrix report has no candidate results")
    result_objects = [result for result in results if isinstance(result, dict)]
    if len(result_objects) != len(results):
        return AuditItem(requirement, "missing", "model matrix results must be objects")
    passing_groups = {
        result["group"]
        for result in result_objects
        if result.get("status") == 0 and isinstance(result.get("group"), str)
    }
    missing_passing_groups = sorted(set(DEFAULT_REQUIRED_MODEL_GROUPS) - passing_groups)
    if missing_passing_groups:
        return AuditItem(
            requirement,
            "missing",
            "no passing candidate for required group(s): " + ", ".join(missing_passing_groups),
        )
    has_codex_frontier = any(
        result.get("status") == 0
        and result.get("group") == "frontier"
        and result.get("provider_slug") == "openai-codex"
        and result.get("auth_source") == "codex_oauth"
        for result in result_objects
    )
    if not has_codex_frontier:
        return AuditItem(
            requirement,
            "missing",
            "model matrix lacks passing Codex subscription-backed frontier candidate",
        )
    failing = [
        str(result.get("candidate_id", "unknown"))
        for result in result_objects
        if result.get("status") != 0
    ]
    if failing:
        return AuditItem(requirement, "missing", "failing candidates: " + ", ".join(failing))
    metric_failures = _model_metric_failures(result_objects)
    if metric_failures:
        return AuditItem(requirement, "missing", "; ".join(metric_failures[:20]))
    if not isinstance(armory, str) or not armory.strip():
        return AuditItem(requirement, "missing", "model matrix armory missing")
    if not isinstance(replay_dataset, str) or not replay_dataset.strip():
        return AuditItem(requirement, "missing", "model matrix replay_dataset missing")
    if not isinstance(output_dir, str) or not output_dir.strip():
        return AuditItem(requirement, "missing", "model matrix output_dir missing")
    armory_path = Path(armory).expanduser()
    if not armory_path.is_dir():
        return AuditItem(
            requirement,
            "missing",
            f"model matrix armory is not a directory: {armory_path}",
        )
    if (
        expected_armory_path is not None
        and armory_path.resolve() != expected_armory_path.expanduser().resolve()
    ):
        return AuditItem(
            requirement,
            "missing",
            "model matrix armory does not match real-corpus preflight armory",
        )
    output_dir_path = Path(output_dir).expanduser()
    if not output_dir_path.is_dir():
        return AuditItem(
            requirement,
            "missing",
            f"model matrix output_dir is not a directory: {output_dir_path}",
        )
    replay_dataset_path = Path(replay_dataset).expanduser()
    if not replay_dataset_path.is_file():
        return AuditItem(
            requirement,
            "missing",
            f"model matrix replay_dataset is not a file: {replay_dataset_path}",
        )
    if expected_replay_dataset_paths and replay_dataset_path.resolve() not in {
        path.resolve() for path in expected_replay_dataset_paths
    }:
        return AuditItem(
            requirement,
            "missing",
            "model matrix replay_dataset is not declared by the real-corpus manifest",
        )
    replay_audit = _replay_dataset_audit(replay_dataset_path)
    if replay_audit.error:
        return AuditItem(requirement, "missing", replay_audit.error)
    matrix_replay_summary_failures = _model_replay_summary_failures(payload, replay_audit)
    if matrix_replay_summary_failures:
        return AuditItem(
            requirement,
            "missing",
            "; ".join(matrix_replay_summary_failures[:20]),
        )
    case_count_failures = _model_case_count_failures(result_objects, replay_audit.case_count)
    if case_count_failures:
        return AuditItem(requirement, "missing", "; ".join(case_count_failures[:20]))
    breadth_failures = _model_breadth_failures(result_objects, replay_audit)
    if breadth_failures:
        return AuditItem(requirement, "missing", "; ".join(breadth_failures[:20]))
    child_report_failures = _model_child_report_failures(
        result_objects,
        armory=armory,
        replay_dataset=replay_dataset,
        output_dir=output_dir_path,
        replay_audit=replay_audit,
    )
    if child_report_failures:
        return AuditItem(requirement, "missing", "; ".join(child_report_failures[:20]))
    return AuditItem(
        requirement,
        "covered",
        (
            f"{report_path}: groups={', '.join(cast('list[str]', groups))}, "
            f"candidates={len(results)}, codex_oauth=present"
        ),
    )


def _model_metric_failures(results: list[dict[object, object]]) -> tuple[str, ...]:
    failures: list[str] = []
    for result in results:
        candidate_id = str(result.get("candidate_id", "unknown"))
        for metric, threshold in DEFAULT_REQUIRED_MODEL_METRICS.items():
            value = result.get(metric)
            if isinstance(value, bool) or not isinstance(value, int | float):
                failures.append(f"{candidate_id}: metric {metric} missing")
            elif float(value) < threshold:
                failures.append(
                    f"{candidate_id}: metric {metric} {float(value):.3f} below {threshold:.3f}"
                )
    return tuple(failures)


def _model_case_count_failures(
    results: list[dict[object, object]],
    replay_case_count: int,
) -> tuple[str, ...]:
    failures: list[str] = []
    for result in results:
        candidate_id = str(result.get("candidate_id", "unknown"))
        cases = _int_field(result, "cases")
        if cases != replay_case_count:
            failures.append(
                f"{candidate_id}: matrix scored {cases} case(s), "
                f"replay dataset contains {replay_case_count}"
            )
    return tuple(failures)


def _model_replay_summary_failures(
    payload: dict[object, object],
    replay_audit: ReplayDatasetAudit,
) -> tuple[str, ...]:
    failures: list[str] = []
    replay_cases = _int_field(payload, "replay_cases")
    if replay_cases != replay_audit.case_count:
        failures.append(
            f"model matrix replay_cases {replay_cases} does not match replay dataset "
            f"{replay_audit.case_count}"
        )
    for field, expected_values in (
        ("replay_domains", replay_audit.domains),
        ("replay_tasks", replay_audit.tasks),
    ):
        raw_values = payload.get(field)
        if not isinstance(raw_values, list):
            failures.append(f"model matrix {field} missing")
            continue
        actual_values = tuple(sorted({value for value in raw_values if isinstance(value, str)}))
        if actual_values != expected_values:
            failures.append(
                f"model matrix {field} does not match replay dataset "
                f"(actual={', '.join(actual_values)}, expected={', '.join(expected_values)})"
            )
    return tuple(failures)


def _model_breadth_failures(
    results: list[dict[object, object]],
    replay_audit: ReplayDatasetAudit,
) -> tuple[str, ...]:
    failures: list[str] = []
    for result in results:
        candidate_id = str(result.get("candidate_id", "unknown"))
        for field, required in (
            ("domains", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_domains"]),
            ("tasks", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_tasks"]),
        ):
            failure = _sequence_breadth_failure(
                candidate_id,
                result,
                field=field,
                required=required,
                label="matrix",
            )
            if failure:
                failures.append(failure)
                continue
            expected_values = replay_audit.domains if field == "domains" else replay_audit.tasks
            match_failure = _sequence_match_failure(
                candidate_id,
                result,
                field=field,
                expected_values=expected_values,
                label="matrix",
            )
            if match_failure:
                failures.append(match_failure)
    return tuple(failures)


def _replay_dataset_audit(path: Path) -> ReplayDatasetAudit:
    try:
        cases = replay_answer_benchmark.load_cases(path)
    except ValueError as exc:
        return ReplayDatasetAudit(
            error=f"invalid replay dataset: {exc}",
            case_count=0,
            case_ids=(),
            domains=(),
            tasks=(),
        )
    case_ids = tuple(case.case_id for case in cases)
    domains = tuple(sorted({case.domain for case in cases if case.domain}))
    tasks = tuple(sorted({case.task for case in cases if case.task}))
    if len(set(case_ids)) != len(case_ids):
        return ReplayDatasetAudit(
            error="replay dataset case ids must be unique",
            case_count=len(cases),
            case_ids=case_ids,
            domains=domains,
            tasks=tasks,
        )
    min_domains = DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_domains"]
    if len(domains) < min_domains:
        return ReplayDatasetAudit(
            error=(
                f"replay dataset covers {len(domains)} domain(s), expected at least {min_domains}"
            ),
            case_count=len(cases),
            case_ids=case_ids,
            domains=domains,
            tasks=tasks,
        )
    min_tasks = DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_tasks"]
    if len(tasks) < min_tasks:
        return ReplayDatasetAudit(
            error=f"replay dataset covers {len(tasks)} task(s), expected at least {min_tasks}",
            case_count=len(cases),
            case_ids=case_ids,
            domains=domains,
            tasks=tasks,
        )
    if not any(case.task == "material-overview" for case in cases):
        return ReplayDatasetAudit(
            error="replay dataset must include a material-overview case",
            case_count=len(cases),
            case_ids=case_ids,
            domains=domains,
            tasks=tasks,
        )
    if not replay_answer_benchmark.has_shaped_material_overview_case(cases):
        return ReplayDatasetAudit(
            error=(
                "replay material-overview case must include word, citation, source, bullet, "
                "cited-bullet, and explicit-date shape constraints"
            ),
            case_count=len(cases),
            case_ids=case_ids,
            domains=domains,
            tasks=tasks,
        )
    return ReplayDatasetAudit(
        error="",
        case_count=len(cases),
        case_ids=case_ids,
        domains=domains,
        tasks=tasks,
    )


def _model_child_report_failures(
    results: list[dict[object, object]],
    *,
    armory: str,
    replay_dataset: str,
    output_dir: Path,
    replay_audit: ReplayDatasetAudit,
) -> tuple[str, ...]:
    failures: list[str] = []
    for result in results:
        candidate_id = str(result.get("candidate_id", "unknown"))
        raw_report_path = result.get("report_path")
        if not isinstance(raw_report_path, str) or not raw_report_path.strip():
            failures.append(f"{candidate_id}: report_path missing")
            continue
        report_path = Path(raw_report_path).expanduser()
        if not _is_relative_to(report_path.resolve(), output_dir.resolve()):
            failures.append(f"{candidate_id}: report_path outside model matrix output_dir")
            continue
        try:
            child_payload = json.loads(report_path.read_text(encoding="utf-8"))
        except OSError as exc:
            failures.append(f"{candidate_id}: could not read child report: {exc}")
            continue
        except json.JSONDecodeError as exc:
            failures.append(f"{candidate_id}: invalid child report JSON: {exc}")
            continue
        if not isinstance(child_payload, dict):
            failures.append(f"{candidate_id}: child report must be an object")
            continue
        metadata_failure = _child_metadata_failure(
            candidate_id,
            result,
            child_payload,
            armory=armory,
            replay_dataset=replay_dataset,
        )
        if metadata_failure:
            failures.append(metadata_failure)
            continue
        if child_payload.get("status") != 0:
            failures.append(
                f"{candidate_id}: child report status is {child_payload.get('status')!r}"
            )
            continue
        child_report = child_payload.get("report")
        if not isinstance(child_report, dict):
            failures.append(f"{candidate_id}: child report missing report object")
            continue
        report_breadth_failures = _child_report_breadth_failures(
            candidate_id,
            child_report,
            replay_audit,
        )
        if report_breadth_failures:
            failures.extend(report_breadth_failures)
            continue
        child_thresholds = child_payload.get("thresholds")
        if not isinstance(child_thresholds, dict):
            failures.append(f"{candidate_id}: child report missing thresholds object")
            continue
        threshold_failures = _child_threshold_failures(candidate_id, child_thresholds)
        if threshold_failures:
            failures.extend(threshold_failures)
            continue
        raw_output_path = child_payload.get("output")
        if not isinstance(raw_output_path, str) or not raw_output_path.strip():
            failures.append(f"{candidate_id}: child report output path missing")
            continue
        output_path = Path(raw_output_path).expanduser()
        matrix_output_path = result.get("output")
        if not isinstance(matrix_output_path, str) or not matrix_output_path.strip():
            failures.append(f"{candidate_id}: matrix output path missing")
            continue
        matrix_output = Path(matrix_output_path).expanduser()
        if not _is_relative_to(matrix_output.resolve(), output_dir.resolve()):
            failures.append(f"{candidate_id}: matrix output path outside model matrix output_dir")
            continue
        if output_path.resolve() != Path(matrix_output_path).expanduser().resolve():
            failures.append(f"{candidate_id}: child output path does not match matrix output")
            continue
        if not output_path.is_file():
            failures.append(f"{candidate_id}: child answer fixture missing: {output_path}")
            continue
        fixture_error = _answer_fixture_error(
            output_path,
            child_report,
            replay_audit,
        )
        if fixture_error:
            failures.append(f"{candidate_id}: {fixture_error}")
            continue
        rescored_failure = _answer_fixture_rescored_metric_failure(
            candidate_id,
            output_path,
            child_report,
        )
        if rescored_failure:
            failures.append(rescored_failure)
            continue
        failures.extend(_child_metric_mismatches(candidate_id, result, child_report))
    return tuple(failures)


def _child_metadata_failure(
    candidate_id: str,
    result: dict[object, object],
    child_payload: dict[object, object],
    *,
    armory: str,
    replay_dataset: str,
) -> str:
    for field, expected_override in (
        ("model", ""),
        ("base_url", ""),
        ("armory", armory),
        ("replay_dataset", replay_dataset),
    ):
        result_value = result.get(field)
        child_value = child_payload.get(field)
        expected = expected_override or (result_value if isinstance(result_value, str) else "")
        actual = child_value if isinstance(child_value, str) else ""
        if actual != expected:
            return (
                f"{candidate_id}: child report {field} {actual!r} "
                f"does not match matrix {expected!r}"
            )
    return ""


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _child_threshold_failures(
    candidate_id: str,
    thresholds: dict[object, object],
) -> tuple[str, ...]:
    failures: list[str] = []
    for threshold, required in DEFAULT_REQUIRED_CHILD_THRESHOLDS.items():
        value = thresholds.get(threshold)
        if isinstance(value, bool) or not isinstance(value, int | float):
            failures.append(f"{candidate_id}: child threshold {threshold} missing")
        elif float(value) < required:
            failures.append(
                f"{candidate_id}: child threshold {threshold} {float(value):.3f} "
                f"below {required:.3f}"
            )
    for threshold, required in DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS.items():
        value = _int_field(thresholds, threshold)
        if value < required:
            failures.append(
                f"{candidate_id}: child threshold {threshold} {value} below {required}"
            )
    return tuple(failures)


def _child_report_breadth_failures(
    candidate_id: str,
    child_report: dict[object, object],
    replay_audit: ReplayDatasetAudit,
) -> tuple[str, ...]:
    failures: list[str] = []
    for field, required in (
        ("domains", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_domains"]),
        ("tasks", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_tasks"]),
    ):
        failure = _sequence_breadth_failure(
            candidate_id,
            child_report,
            field=field,
            required=required,
            label="child report",
        )
        if failure:
            failures.append(failure)
            continue
        expected_values = replay_audit.domains if field == "domains" else replay_audit.tasks
        match_failure = _sequence_match_failure(
            candidate_id,
            child_report,
            field=field,
            expected_values=expected_values,
            label="child report",
        )
        if match_failure:
            failures.append(match_failure)
    return tuple(failures)


def _answer_fixture_breadth_failure(
    cases: list[benchmark_answers.AnswerCase],
    *,
    field: str,
    required: int,
) -> str:
    values = {
        value
        for value in ((case.domain if field == "domains" else case.task) for case in cases)
        if value
    }
    if len(values) < required:
        return f"child answer fixture {field} covers {len(values)}, expected {required}"
    return ""


def _answer_fixture_match_failure(
    cases: list[benchmark_answers.AnswerCase],
    *,
    field: str,
    expected_values: tuple[str, ...],
) -> str:
    values = tuple(
        sorted(
            {
                value
                for value in ((case.domain if field == "domains" else case.task) for case in cases)
                if value
            }
        )
    )
    if values != expected_values:
        return (
            f"child answer fixture {field} do not match replay dataset "
            f"(actual={', '.join(values)}, expected={', '.join(expected_values)})"
        )
    return ""


def _sequence_breadth_failure(
    candidate_id: str,
    payload: dict[object, object],
    *,
    field: str,
    required: int,
    label: str,
) -> str:
    raw_values = payload.get(field)
    if not isinstance(raw_values, list):
        return f"{candidate_id}: {label} {field} missing"
    values = {value for value in raw_values if isinstance(value, str) and value.strip()}
    if len(values) < required:
        return f"{candidate_id}: {label} {field} covers {len(values)}, expected {required}"
    return ""


def _sequence_match_failure(
    candidate_id: str,
    payload: dict[object, object],
    *,
    field: str,
    expected_values: tuple[str, ...],
    label: str,
) -> str:
    raw_values = payload.get(field)
    if not isinstance(raw_values, list):
        return f"{candidate_id}: {label} {field} missing"
    actual_values = tuple(sorted({value for value in raw_values if isinstance(value, str)}))
    if actual_values != expected_values:
        return (
            f"{candidate_id}: {label} {field} do not match replay dataset "
            f"(actual={', '.join(actual_values)}, expected={', '.join(expected_values)})"
        )
    return ""


def _answer_fixture_error(
    path: Path,
    child_report: dict[object, object],
    replay_audit: ReplayDatasetAudit,
) -> str:
    try:
        cases = benchmark_answers.load_cases(path)
    except ValueError as exc:
        return f"invalid answer fixture: {exc}"
    if not cases:
        return "child answer fixture is empty"
    expected_cases = _int_field(child_report, "cases")
    if expected_cases <= 0:
        return "child report case count missing"
    if expected_cases != replay_audit.case_count:
        return (
            f"child report scored {expected_cases} case(s), "
            f"replay dataset contains {replay_audit.case_count}"
        )
    if len(cases) != expected_cases:
        return f"child answer fixture has {len(cases)} case(s), report scored {expected_cases}"
    answer_case_ids = tuple(case.case_id for case in cases)
    if set(answer_case_ids) != set(replay_audit.case_ids):
        missing_ids = sorted(set(replay_audit.case_ids) - set(answer_case_ids))
        extra_ids = sorted(set(answer_case_ids) - set(replay_audit.case_ids))
        details: list[str] = []
        if missing_ids:
            details.append("missing " + ", ".join(missing_ids[:5]))
        if extra_ids:
            details.append("extra " + ", ".join(extra_ids[:5]))
        return "child answer fixture case ids do not match replay dataset: " + "; ".join(details)
    for field, required in (
        ("domains", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_domains"]),
        ("tasks", DEFAULT_REQUIRED_CHILD_INT_THRESHOLDS["min_answer_tasks"]),
    ):
        breadth_failure = _answer_fixture_breadth_failure(cases, field=field, required=required)
        if breadth_failure:
            return breadth_failure
        expected_values = replay_audit.domains if field == "domains" else replay_audit.tasks
        match_failure = _answer_fixture_match_failure(
            cases,
            field=field,
            expected_values=expected_values,
        )
        if match_failure:
            return match_failure
    return ""


def _answer_fixture_rescored_metric_failure(
    candidate_id: str,
    output_path: Path,
    child_report: dict[object, object],
) -> str:
    report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output_path))
    for metric, required in DEFAULT_REQUIRED_MODEL_METRICS.items():
        rescored_value = _answer_report_metric(report, metric)
        child_value = child_report.get(metric)
        if rescored_value < required:
            return (
                f"{candidate_id}: rescored answer fixture metric {metric} "
                f"{rescored_value:.3f} below {required:.3f}"
            )
        if isinstance(child_value, bool) or not isinstance(child_value, int | float):
            return f"{candidate_id}: child report metric {metric} missing"
        if float(child_value) != rescored_value:
            return (
                f"{candidate_id}: child report metric {metric} {float(child_value):.3f} "
                f"does not match rescored answer fixture {rescored_value:.3f}"
            )
    return ""


def _answer_report_metric(
    report: benchmark_answers.AnswerBenchmarkReport,
    metric: str,
) -> float:
    if metric == "pass_rate":
        return report.pass_rate
    if metric == "citation_validity_rate":
        return report.citation_validity_rate
    if metric == "citation_presence_rate":
        return report.citation_presence_rate
    if metric == "expected_citation_rate":
        return report.expected_citation_rate
    if metric == "required_text_rate":
        return report.required_text_rate
    if metric == "forbidden_text_rate":
        return report.forbidden_text_rate
    if metric == "supported_claim_rate":
        return report.supported_claim_rate
    if metric == "answer_shape_rate":
        return report.answer_shape_rate
    if metric == "evidence_coverage_rate":
        return report.evidence_coverage_rate
    if metric == "required_label_rate":
        return report.required_label_rate
    raise KeyError(metric)


def _child_metric_mismatches(
    candidate_id: str,
    result: dict[object, object],
    child_report: dict[object, object],
) -> tuple[str, ...]:
    failures: list[str] = []
    for metric in DEFAULT_REQUIRED_MODEL_METRICS:
        result_value = result.get(metric)
        child_value = child_report.get(metric)
        if isinstance(child_value, bool) or not isinstance(child_value, int | float):
            failures.append(f"{candidate_id}: child report metric {metric} missing")
        elif not isinstance(result_value, int | float) or (
            float(child_value) != float(result_value)
        ):
            failures.append(
                f"{candidate_id}: child report metric {metric} {float(child_value):.3f} "
                "does not match matrix"
            )
    return tuple(failures)


def audit_completion(
    *,
    real_manifest: Path | None = None,
    real_preflight_report: Path | None = None,
    model_matrix_report: Path | None = None,
) -> HarnessCompletionAudit:
    """Return completion status for the competitive academic harness objective."""
    items = [
        _framework_policy_item(),
        _runtime_generality_item(),
        _script_generality_item(),
        _file_exists("scripts/run_benchmark_suite.py"),
        _file_exists("scripts/benchmark_document_understanding.py"),
        _file_exists("scripts/discover_real_corpus_candidates.py"),
        _file_exists("scripts/build_permissioned_corpus_armory.py"),
        _file_exists("scripts/prepare_real_corpus_evidence.py"),
        _file_exists("scripts/replay_answer_benchmark.py"),
        _file_exists("scripts/benchmark_chat_events.py"),
        _file_exists("scripts/extract_chat_event_expectation.py"),
        _file_exists("scripts/materialize_public_corpus.py"),
        _file_exists("scripts/run_model_eval_matrix.py"),
        _file_exists("benchmarks/academic/manifest.json"),
        _deterministic_benchmark_suite_item(),
        _deterministic_chat_event_suite_item(),
        _model_matrix_example_item(),
        _real_corpus_item(real_manifest),
        _real_chat_event_item(real_manifest),
        _real_preflight_item(real_preflight_report, real_manifest),
        _model_matrix_item(
            model_matrix_report,
            expected_armory_path=_preflight_armory_path(real_preflight_report),
            expected_replay_dataset_paths=_manifest_replay_dataset_paths(real_manifest),
        ),
    ]
    missing = tuple(item.requirement for item in items if item.status != "covered")
    return HarnessCompletionAudit(
        status="complete" if not missing else "incomplete",
        items=tuple(items),
        missing=missing,
        next_steps=_next_steps(missing),
    )


def print_text_report(report: HarnessCompletionAudit) -> None:
    print(f"Agent harness completion audit: {report.status}")
    for item in report.items:
        print(f"- {item.status}: {item.requirement}")
        print(f"  {item.evidence}")
    if report.missing:
        print("Missing evidence:")
        for requirement in report.missing:
            print(f"  - {requirement}")
    if report.next_steps:
        print("Next commands:")
        for command in report.next_steps:
            print(f"  - {command}")


def _next_steps(missing: tuple[str, ...]) -> tuple[str, ...]:
    steps: list[str] = []
    if any("real/public or permissioned academic corpus" in item for item in missing):
        steps.append(
            "uv run python -m scripts.discover_real_corpus_candidates "
            "~/.armories --min-documents 40 --min-roles 3 --require-candidate"
        )
        steps.append(
            "uv run python -m scripts.prepare_real_corpus_evidence "
            "path/to/real-armory .artifacts/real-corpus-evidence"
        )
        steps.append(
            "uv run python -m scripts.build_permissioned_corpus_armory "
            ".artifacts/real-corpus-evidence/armory "
            ".artifacts/real-corpus-evidence/real-corpus-manifest.json "
            "path/to/permissioned-materials "
            "--domain-from-parent --balance-domains --infer-roles-from-index --overwrite"
        )
        steps.append(
            "uv run python -m scripts.materialize_public_corpus "
            "path/to/reviewed-public-manifest.json path/to/real-armory"
        )
    if any("public chat JSONL harness events" in item for item in missing):
        steps.extend(
            (
                'uv run heph chat ask --jsonl path/to/real-armory "what is the material about" '
                "> .artifacts/real-corpus-evidence/chat_events.jsonl",
                "uv run python -m scripts.extract_chat_event_expectation "
                ".artifacts/real-corpus-evidence/chat_events.jsonl "
                "--output .artifacts/real-corpus-evidence/chat_event_expectation.json",
                "uv run python -m scripts.benchmark_chat_events "
                ".artifacts/real-corpus-evidence/chat_events.jsonl "
                "--answer-expectation "
                ".artifacts/real-corpus-evidence/chat_event_expectation.json",
            )
        )
    if any("Model-backed replay eval" in item for item in missing):
        steps.extend(
            (
                "uv run python -m scripts.run_model_eval_matrix "
                "path/to/real-armory path/to/replay.jsonl path/to/model-matrix.json "
                ".artifacts/model-eval --validate-inputs "
                "--json-report .artifacts/model-eval/matrix.inputs.json",
                "uv run python -m scripts.run_model_eval_matrix "
                "path/to/real-armory path/to/replay.jsonl path/to/model-matrix.json "
                ".artifacts/model-eval "
                "--json-report .artifacts/model-eval/matrix.report.json",
            )
        )
    if missing:
        steps.append(
            "uv run python -m scripts.audit_agent_harness_completion "
            "--real-manifest .artifacts/real-corpus-evidence/real-corpus-manifest.json "
            "--real-preflight-report "
            ".artifacts/real-corpus-evidence/real-corpus-preflight.json "
            "--model-matrix-report .artifacts/model-eval/matrix.report.json"
        )
    return tuple(steps)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-manifest", type=Path)
    parser.add_argument("--real-preflight-report", type=Path)
    parser.add_argument("--model-matrix-report", type=Path)
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    real_manifest = cast("Path | None", args.real_manifest)
    real_preflight_report = cast("Path | None", args.real_preflight_report)
    model_matrix_report = cast("Path | None", args.model_matrix_report)
    json_report = cast("Path | None", args.json_report)
    report = audit_completion(
        real_manifest=real_manifest.expanduser().resolve() if real_manifest else None,
        real_preflight_report=(
            real_preflight_report.expanduser().resolve() if real_preflight_report else None
        ),
        model_matrix_report=(
            model_matrix_report.expanduser().resolve() if model_matrix_report else None
        ),
    )
    print_text_report(report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0 if report.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
