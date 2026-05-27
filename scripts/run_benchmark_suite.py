"""Run a deterministic local benchmark suite.

The suite copies a private, ignored benchmark armory into a temporary directory
before running retrieval benchmarks, so generated indexes never dirty source
fixtures or the working tree.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.chat import orchestrator as chat_orchestrator
from scripts import (
    benchmark_academic_items,
    benchmark_answers,
    benchmark_chat_events,
    benchmark_document_understanding,
    benchmark_index_integrity,
    benchmark_material_roles,
    benchmark_priority,
    benchmark_prompt_cache,
    benchmark_rag,
    compare_benchmark_reports,
    replay_answer_benchmark,
    validate_benchmark_manifest,
)
from scripts import (
    benchmark_study_state as learning_state_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SUITE = REPO_ROOT / "benchmarks" / "academic"
DEFAULT_RAG_HIT_RATE = 1.0
DEFAULT_RAG_MRR = 0.7
DEFAULT_RAG_EXPECTED_RECALL = 1.0
DEFAULT_RAG_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE = 1.0
DEFAULT_MIN_RAG_DOMAINS = 3
DEFAULT_MIN_RAG_TASKS = 3
DEFAULT_MIN_RAG_MULTI_SOURCE_CASES = 1
DEFAULT_ANSWER_PASS_RATE = 1.0
DEFAULT_MIN_ANSWER_DOMAINS = 3
DEFAULT_MIN_SPECIALIZED_ANSWER_DOMAINS = 1
DEFAULT_MIN_ANSWER_TASKS = 3
DEFAULT_MIN_ANSWER_MULTI_EVIDENCE_CASES = 1
DEFAULT_FOUNDATIONAL_ANSWER_DOMAINS = frozenset(
    {"computer-science", "cross-domain", "general", "mathematics", "study-methods"}
)
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
DEFAULT_MATERIAL_ROLE_PASS_RATE = 1.0
DEFAULT_MIN_MATERIAL_ROLE_DOMAINS = 4
DEFAULT_MIN_MATERIAL_ROLE_TYPES = 3
DEFAULT_INDEX_INTEGRITY_PASS_RATE = 1.0
DEFAULT_INDEX_INTEGRITY_REQUIRED_TEXT = 1.0
DEFAULT_INDEX_INTEGRITY_FORBIDDEN_TEXT = 1.0
DEFAULT_INDEX_INTEGRITY_CORPUS_FORBIDDEN_TEXT = 1.0
DEFAULT_MIN_INDEX_INTEGRITY_DOMAINS = 4
DEFAULT_MIN_INDEX_INTEGRITY_TASKS = 3
DEFAULT_PRIORITY_PASS_RATE = 1.0
DEFAULT_MIN_PRIORITY_DOMAINS = 4
DEFAULT_PRIORITY_TOPIC_RECALL = 1.0
DEFAULT_PRIORITY_FORBIDDEN_AVOIDANCE = 1.0
DEFAULT_PRIORITY_PAST_EXAM_RECALL = 1.0
DEFAULT_MIN_REPLAY_TASKS = 3
DEFAULT_MIN_ACTIVE_RECALL_ASSESSMENT_CASES = 1
DEFAULT_MIN_HINT_CASES = 1
DEFAULT_LEARNING_STATE_PASS_RATE = 1.0
DEFAULT_LEARNING_STATE_TRANSITION_PASS_RATE = 1.0
DEFAULT_LEARNING_STATE_SCHEDULING_PASS_RATE = 1.0
DEFAULT_MIN_LEARNING_STATE_DOMAINS = 2
DEFAULT_MIN_LEARNING_STATE_SCHEDULE_CASES = 1
DEFAULT_MIN_LEARNING_STATE_PROMPT_CONTRACT_TURNS = 1
DEFAULT_MIN_ACADEMIC_QUESTION_TYPES = 6
DEFAULT_ACADEMIC_QUESTION_QUALITY_RATE = 1.0
DEFAULT_REQUIRED_LEARNING_INTENT_LABELS = (
    "material_overview",
    "source_qa",
    "source_only_policy",
    "topic_presentation",
    "topic_drill",
    "ready_for_recall",
    "recall_clarification",
    "recall_answer_attempt",
    "chat",
)
DEFAULT_REQUIRED_LEARNING_INTENT_PROMPT_PHRASES = (
    "Classify the user's intent",
    "Heph",
    "any language",
    "Return JSON only",
)
DEFAULT_FORBIDDEN_LEARNING_INTENT_LANGUAGE_EXAMPLES = (
    "deutsch",
    "español",
    "espanol",
    "français",
    "francais",
    "german",
    "spanish",
    "french",
    "por favor",
    "frag mich",
)
_LEGACY_LEARNING_STATE_DATASET = "study_state.jsonl"


def _learning_state_dataset_path(suite_path: Path) -> Path:
    current_path = suite_path / "learning_state.jsonl"
    if current_path.is_file():
        return current_path
    return suite_path / _LEGACY_LEARNING_STATE_DATASET


DEFAULT_LANGUAGE_GENERIC_PROMPT_PATHS = (
    "hephaion/chat/orchestrator.py",
    "hephaion/study/controller.py",
    "hephaion/tui/inline_flows.py",
)
DEFAULT_DOCUMENT_UNDERSTANDING_MIN_DOCUMENTS = 10
DEFAULT_DOCUMENT_UNDERSTANDING_REQUIRED_ROLES = ("assignment", "lecture", "past_exam")
DEFAULT_DOCUMENT_UNDERSTANDING_OVERVIEW_COVERAGE = 1.0
DEFAULT_OVERVIEW_FORBIDDEN_PHRASES = (
    "Document signals",
    "Retrieved overview sample",
    "Sampled orientation",
    "Visible topics",
    "non-exhaustive list",
    "not an exhaustive summary",
    "only a sample",
    "partial inventory",
)
GENERATED_ARMORY_INDEX_ARTIFACTS = frozenset(("rag_index.json",))
GENERATED_ARMORY_INDEX_ARTIFACT_PREFIXES = frozenset(("embeddings_", "retriever_"))


class BenchmarkSuiteSummary(TypedDict):
    suite: str
    status: int
    thresholds: dict[str, object]
    rag: dict[str, object]
    material_roles: dict[str, object]
    document_understanding: dict[str, object]
    index_integrity: dict[str, object]
    priority: dict[str, object]
    prompt_cache: dict[str, object]
    learning_intent: dict[str, object]
    replay: dict[str, object]
    chat_events: dict[str, object]
    chat_runtime_events: dict[str, object]
    answers: dict[str, object]
    learning_state: dict[str, object]
    academic_items: dict[str, object]
    manifest: dict[str, object]
    report_path: NotRequired[str]


@dataclass(frozen=True, slots=True)
class LearningIntentContractReport:
    passed: bool
    required_intents: tuple[str, ...]
    parsed_intents: tuple[str, ...]
    required_prompt_phrases: tuple[str, ...]
    forbidden_language_examples: tuple[str, ...]
    language_generic_prompt_paths: tuple[str, ...]
    failures: tuple[str, ...]


def _is_generated_armory_index_artifact(name: str) -> bool:
    return name in GENERATED_ARMORY_INDEX_ARTIFACTS or (
        name.endswith(".json")
        and any(name.startswith(prefix) for prefix in GENERATED_ARMORY_INDEX_ARTIFACT_PREFIXES)
    )


def _ignore_generated_armory_index_artifacts(directory: str, names: list[str]) -> set[str]:
    if Path(directory).name != ".hephaion":
        return set()
    return {name for name in names if _is_generated_armory_index_artifact(name)}


def _copy_suite_armory(suite_path: Path, destination: Path) -> Path:
    source = suite_path / "armory"
    if not source.is_dir():
        raise ValueError(f"benchmark suite is missing armory fixture: {source}")
    target = destination / "armory"
    shutil.copytree(source, target, ignore=_ignore_generated_armory_index_artifacts)
    return target


def _validate_material_role_suite_integrity(
    report: benchmark_material_roles.MaterialRoleBenchmarkReport,
    *,
    min_domains: int = DEFAULT_MIN_MATERIAL_ROLE_DOMAINS,
    min_role_types: int = DEFAULT_MIN_MATERIAL_ROLE_TYPES,
) -> None:
    """Reject narrow suites that cannot catch subject-specific role logic."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "material role benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    if len(report.expected_roles) < min_role_types:
        raise ValueError(
            "material role benchmark must cover at least "
            f"{min_role_types} material role types; found {len(report.expected_roles)}"
        )


def _validate_index_integrity_suite_integrity(
    report: benchmark_index_integrity.IndexIntegrityReport,
    *,
    min_domains: int = DEFAULT_MIN_INDEX_INTEGRITY_DOMAINS,
    min_tasks: int = DEFAULT_MIN_INDEX_INTEGRITY_TASKS,
) -> None:
    """Reject extraction checks that only prove one indexing behavior."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "index integrity benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    if len(report.tasks) < min_tasks:
        raise ValueError(
            "index integrity benchmark must cover at least "
            f"{min_tasks} labelled extraction/indexing tasks; found {len(report.tasks)}"
        )


def _validate_rag_suite_integrity(
    report: benchmark_rag.BenchmarkReport,
    *,
    min_domains: int = DEFAULT_MIN_RAG_DOMAINS,
    min_tasks: int = DEFAULT_MIN_RAG_TASKS,
    min_multi_source_cases: int = DEFAULT_MIN_RAG_MULTI_SOURCE_CASES,
) -> None:
    """Reject retrieval suites that are too narrow to catch RAG regressions."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "RAG benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    if len(report.tasks) < min_tasks:
        raise ValueError(
            "RAG benchmark must cover at least "
            f"{min_tasks} labelled retrieval tasks; found {len(report.tasks)}"
        )
    multi_source_cases = [
        result
        for result in report.results
        if len({ref.partition("#")[0] for ref in result.expected}) > 1
    ]
    if len(multi_source_cases) < min_multi_source_cases:
        raise ValueError(
            "RAG benchmark must cover at least "
            f"{min_multi_source_cases} multi-source synthesis case(s); "
            f"found {len(multi_source_cases)}"
        )


def _validate_priority_suite_integrity(
    report: benchmark_priority.PriorityBenchmarkReport,
    *,
    min_domains: int = DEFAULT_MIN_PRIORITY_DOMAINS,
) -> None:
    """Reject priority suites that only prove one academic domain."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "priority benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )


def _validate_replay_suite_integrity(
    cases: Sequence[replay_answer_benchmark.ReplayCase],
    *,
    min_tasks: int = DEFAULT_MIN_REPLAY_TASKS,
) -> None:
    """Reject replay prompt sets that only cover one answer behavior."""
    tasks = {case.task for case in cases if case.task}
    if len(tasks) < min_tasks:
        raise ValueError(
            "replay benchmark must cover at least "
            f"{min_tasks} labelled answer tasks; found {len(tasks)}"
        )
    if not any(case.task == "material-overview" for case in cases):
        raise ValueError("replay benchmark must include a material-overview case")
    if not replay_answer_benchmark.has_shaped_material_overview_case(cases):
        raise ValueError(
            "replay material-overview case must include word, citation, source, bullet, "
            "cited-bullet, and explicit-date shape constraints"
        )


def _validate_overview_forbidden_phrase_contract(
    cases: Sequence[benchmark_answers.AnswerCase | Mapping[str, object]],
    *,
    required_phrases: tuple[str, ...] = DEFAULT_OVERVIEW_FORBIDDEN_PHRASES,
    label: str = "answer",
) -> None:
    overview_cases = [
        case for case in cases if _overview_contract_task(case) == "material-overview"
    ]
    if not overview_cases:
        raise ValueError(f"{label} benchmark must include a material-overview case")
    covered = {
        phrase
        for case in overview_cases
        for phrase in required_phrases
        if phrase in _overview_contract_must_not_include(case)
    }
    missing = tuple(phrase for phrase in required_phrases if phrase not in covered)
    if missing:
        raise ValueError(
            f"{label} material-overview case must forbid boilerplate topic phrase(s): "
            + ", ".join(missing)
        )


def _overview_contract_task(contract: benchmark_answers.AnswerCase | Mapping[str, object]) -> str:
    if isinstance(contract, benchmark_answers.AnswerCase):
        return contract.task or ""
    task = contract.get("task")
    return task if isinstance(task, str) else ""


def _overview_contract_must_not_include(
    contract: benchmark_answers.AnswerCase | Mapping[str, object],
) -> tuple[str, ...]:
    if isinstance(contract, benchmark_answers.AnswerCase):
        return contract.must_not_include
    phrases = contract.get("must_not_include")
    if not isinstance(phrases, list):
        return ()
    return tuple(phrase for phrase in phrases if isinstance(phrase, str))


def _validate_answer_suite_integrity(
    report: benchmark_answers.AnswerBenchmarkReport,
    cases: Sequence[benchmark_answers.AnswerCase],
    *,
    min_domains: int = DEFAULT_MIN_ANSWER_DOMAINS,
    min_specialized_domains: int = DEFAULT_MIN_SPECIALIZED_ANSWER_DOMAINS,
    min_tasks: int = DEFAULT_MIN_ANSWER_TASKS,
    min_multi_evidence_cases: int = DEFAULT_MIN_ANSWER_MULTI_EVIDENCE_CASES,
    min_active_recall_assessment_cases: int = DEFAULT_MIN_ACTIVE_RECALL_ASSESSMENT_CASES,
    min_hint_cases: int = DEFAULT_MIN_HINT_CASES,
) -> None:
    """Reject saved answer fixtures that do not prove varied answer behaviors."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    specialized_domains = [
        domain for domain in report.domains if domain not in DEFAULT_FOUNDATIONAL_ANSWER_DOMAINS
    ]
    if len(specialized_domains) < min_specialized_domains:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_specialized_domains} specialized non-math/non-CS domain(s); "
            f"found {len(specialized_domains)}"
        )
    if len(report.tasks) < min_tasks:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_tasks} labelled answer tasks; found {len(report.tasks)}"
        )
    multi_evidence_case_ids = {
        case.case_id
        for case in cases
        if case.task == "multi-source-synthesis"
        and case.evidence is not None
        and len(case.evidence.items) > 1
    }
    multi_evidence_cases = [
        result for result in report.results if result.case_id in multi_evidence_case_ids
    ]
    if len(multi_evidence_cases) < min_multi_evidence_cases:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_multi_evidence_cases} multi-evidence synthesis case(s); "
            f"found {len(multi_evidence_cases)}"
        )
    active_recall_cases = [
        result for result in report.results if "active-recall" in result.case_id
    ]
    if len(active_recall_cases) < min_active_recall_assessment_cases:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_active_recall_assessment_cases} active-recall assessment case(s); "
            f"found {len(active_recall_cases)}"
        )
    hint_cases = [result for result in report.results if "hint" in result.case_id]
    if len(hint_cases) < min_hint_cases:
        raise ValueError(
            "answer benchmark must cover at least "
            f"{min_hint_cases} hint case(s); found {len(hint_cases)}"
        )
    _validate_overview_forbidden_phrase_contract(cases)


def _validate_learning_state_suite_integrity(
    report: learning_state_benchmark.LearningStateBenchmarkReport,
    *,
    min_domains: int = DEFAULT_MIN_LEARNING_STATE_DOMAINS,
    min_schedule_cases: int = DEFAULT_MIN_LEARNING_STATE_SCHEDULE_CASES,
    min_prompt_contract_turns: int = DEFAULT_MIN_LEARNING_STATE_PROMPT_CONTRACT_TURNS,
) -> None:
    """Reject learning-state suites that do not prove scheduling, prompts, and domains."""
    if len(report.domains) < min_domains:
        raise ValueError(
            "learning-state benchmark must cover at least "
            f"{min_domains} labelled domains; found {len(report.domains)}"
        )
    schedule_cases = [result for result in report.results if result.scheduled_reviews > 0]
    if len(schedule_cases) < min_schedule_cases:
        raise ValueError(
            "learning-state benchmark must cover at least "
            f"{min_schedule_cases} scheduling case(s); found {len(schedule_cases)}"
        )
    prompt_contract_turns = [
        turn for result in report.results for turn in result.turns if turn.prompt_contract_checked
    ]
    if len(prompt_contract_turns) < min_prompt_contract_turns:
        raise ValueError(
            "learning-state benchmark must cover at least "
            f"{min_prompt_contract_turns} prompt contract turn(s); "
            f"found {len(prompt_contract_turns)}"
        )


def learning_intent_contract_report(
    *,
    schema: str | None = None,
    prompt: str | None = None,
    language_generic_prompt_paths: Sequence[str | Path] = DEFAULT_LANGUAGE_GENERIC_PROMPT_PATHS,
) -> LearningIntentContractReport:
    """Verify the learning intent classifier stays English-first and language-generic."""
    if schema is None or prompt is None:
        schema = chat_orchestrator._LEARNING_INTENT_NORMALIZATION_SCHEMA
        prompt = chat_orchestrator._LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT

    combined = f"{prompt}\n{schema}"
    combined_normalized = _normalized_contract_text(combined)
    prompt_normalized = _normalized_contract_text(prompt)
    failures: list[str] = [
        f"schema missing intent label: {intent}"
        for intent in DEFAULT_REQUIRED_LEARNING_INTENT_LABELS
        if intent not in schema
    ]
    failures.extend(
        f"prompt missing phrase: {phrase}"
        for phrase in DEFAULT_REQUIRED_LEARNING_INTENT_PROMPT_PHRASES
        if _normalized_contract_text(phrase) not in prompt_normalized
    )
    failures.extend(
        f"prompt/schema contains language-specific example: {example}"
        for example in DEFAULT_FORBIDDEN_LEARNING_INTENT_LANGUAGE_EXAMPLES
        if _normalized_contract_text(example) in combined_normalized
    )
    checked_prompt_paths = tuple(str(path) for path in language_generic_prompt_paths)
    failures.extend(_language_generic_prompt_failures(language_generic_prompt_paths))
    parsed_intents: list[str] = []
    for intent in DEFAULT_REQUIRED_LEARNING_INTENT_LABELS:
        parsed = chat_orchestrator._normalized_learning_intent_from_payload(
            {
                "intent": intent.replace("_", " "),
                "canonical_english_request": "source-grounded material request",
                "confidence": 1.0,
            }
        )
        if parsed is None:
            failures.append(f"parser rejected intent label: {intent}")
            continue
        parsed_intents.append(parsed.intent)
        if parsed.intent != intent:
            failures.append(f"parser normalized intent label {intent} as {parsed.intent}")
    return LearningIntentContractReport(
        passed=not failures,
        required_intents=DEFAULT_REQUIRED_LEARNING_INTENT_LABELS,
        parsed_intents=tuple(parsed_intents),
        required_prompt_phrases=DEFAULT_REQUIRED_LEARNING_INTENT_PROMPT_PHRASES,
        forbidden_language_examples=DEFAULT_FORBIDDEN_LEARNING_INTENT_LANGUAGE_EXAMPLES,
        language_generic_prompt_paths=checked_prompt_paths,
        failures=tuple(failures),
    )


def _normalized_contract_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _language_generic_prompt_failures(paths: Sequence[str | Path]) -> tuple[str, ...]:
    failures: list[str] = []
    for path_like in paths:
        path = Path(path_like)
        display = str(path)
        full_path = path if path.is_absolute() else REPO_ROOT / path
        try:
            normalized = _normalized_contract_text(full_path.read_text(encoding="utf-8"))
        except OSError as exc:
            failures.append(f"language-generic prompt path unreadable: {display}: {exc}")
            continue
        failures.extend(
            f"{display} contains language-specific prompt example: {example}"
            for example in DEFAULT_FORBIDDEN_LEARNING_INTENT_LANGUAGE_EXAMPLES
            if _normalized_contract_text(example) in normalized
        )
    return tuple(failures)


def print_learning_intent_contract_report(report: LearningIntentContractReport) -> None:
    """Print a concise learning intent prompt contract report."""
    print("Learning intent contract:")
    print(f"  pass: {'yes' if report.passed else 'no'}")
    print(f"  required intents: {', '.join(report.required_intents)}")
    if report.failures:
        print(f"  failures: {'; '.join(report.failures)}")


def run_suite(
    suite_path: Path = DEFAULT_SUITE,
    *,
    rag_hit_rate: float = DEFAULT_RAG_HIT_RATE,
    rag_mrr: float = DEFAULT_RAG_MRR,
    rag_expected_recall: float = DEFAULT_RAG_EXPECTED_RECALL,
    rag_forbidden_before_expected_avoidance: float = (
        DEFAULT_RAG_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE
    ),
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
    material_role_pass_rate: float = DEFAULT_MATERIAL_ROLE_PASS_RATE,
    document_understanding_min_documents: int = DEFAULT_DOCUMENT_UNDERSTANDING_MIN_DOCUMENTS,
    document_understanding_required_roles: tuple[str, ...] = (
        DEFAULT_DOCUMENT_UNDERSTANDING_REQUIRED_ROLES
    ),
    document_understanding_overview_coverage: float = (
        DEFAULT_DOCUMENT_UNDERSTANDING_OVERVIEW_COVERAGE
    ),
    index_integrity_pass_rate: float = DEFAULT_INDEX_INTEGRITY_PASS_RATE,
    index_integrity_required_text: float = DEFAULT_INDEX_INTEGRITY_REQUIRED_TEXT,
    index_integrity_forbidden_text: float = DEFAULT_INDEX_INTEGRITY_FORBIDDEN_TEXT,
    index_integrity_corpus_forbidden_text: float = (DEFAULT_INDEX_INTEGRITY_CORPUS_FORBIDDEN_TEXT),
    priority_pass_rate: float = DEFAULT_PRIORITY_PASS_RATE,
    priority_topic_recall: float = DEFAULT_PRIORITY_TOPIC_RECALL,
    priority_forbidden_avoidance: float = DEFAULT_PRIORITY_FORBIDDEN_AVOIDANCE,
    priority_past_exam_recall: float = DEFAULT_PRIORITY_PAST_EXAM_RECALL,
    learning_state_pass_rate: float = DEFAULT_LEARNING_STATE_PASS_RATE,
    learning_state_transition_pass_rate: float = DEFAULT_LEARNING_STATE_TRANSITION_PASS_RATE,
    learning_state_scheduling_pass_rate: float = DEFAULT_LEARNING_STATE_SCHEDULING_PASS_RATE,
    report_path: Path | None = None,
    compare_to: Path | None = None,
    compare_tolerance: float = 0.0,
) -> int:
    """Run deterministic retrieval and answer benchmarks."""
    if compare_to is not None and report_path is None:
        raise ValueError("--compare-to requires --json-report so the current run can be compared")
    rag_dataset = suite_path / "rag.jsonl"
    answer_dataset = suite_path / "answers.jsonl"
    material_role_dataset = suite_path / "material_roles.jsonl"
    index_integrity_dataset = suite_path / "index_integrity.jsonl"
    priority_dataset = suite_path / "priority.jsonl"
    replay_dataset = suite_path / "replay.jsonl"
    chat_events_dataset = suite_path / "chat_events.jsonl"
    chat_runtime_events_dataset = suite_path / "chat_events_runtime.jsonl"
    chat_event_expectation = suite_path / "chat_event_expectation.json"
    learning_state_dataset = _learning_state_dataset_path(suite_path)
    academic_items_dataset = suite_path / "academic_items.jsonl"
    manifest_path = suite_path / "manifest.json"
    if not rag_dataset.is_file():
        raise ValueError(f"benchmark suite is missing retrieval dataset: {rag_dataset}")
    if not answer_dataset.is_file():
        raise ValueError(f"benchmark suite is missing answer dataset: {answer_dataset}")
    if not material_role_dataset.is_file():
        raise ValueError(
            f"benchmark suite is missing material role dataset: {material_role_dataset}"
        )
    if not index_integrity_dataset.is_file():
        raise ValueError(
            f"benchmark suite is missing index integrity dataset: {index_integrity_dataset}"
        )
    if not priority_dataset.is_file():
        raise ValueError(f"benchmark suite is missing priority dataset: {priority_dataset}")
    if not replay_dataset.is_file():
        raise ValueError(f"benchmark suite is missing replay dataset: {replay_dataset}")
    if not chat_events_dataset.is_file():
        raise ValueError(f"benchmark suite is missing chat event dataset: {chat_events_dataset}")
    if not chat_runtime_events_dataset.is_file():
        raise ValueError(
            f"benchmark suite is missing chat runtime event dataset: {chat_runtime_events_dataset}"
        )
    if not chat_event_expectation.is_file():
        raise ValueError(
            f"benchmark suite is missing chat event expectation: {chat_event_expectation}"
        )
    if not learning_state_dataset.is_file():
        raise ValueError(
            f"benchmark suite is missing learning-state dataset: {learning_state_dataset}"
        )
    if not academic_items_dataset.is_file():
        raise ValueError(
            f"benchmark suite is missing academic-item dataset: {academic_items_dataset}"
        )
    if not manifest_path.is_file():
        raise ValueError(f"benchmark suite is missing manifest: {manifest_path}")

    manifest_report = validate_benchmark_manifest.validate_manifest(manifest_path)
    validate_benchmark_manifest.print_text_report(manifest_report)
    print()
    with tempfile.TemporaryDirectory(prefix="heph-bench-") as tmp:
        armory = _copy_suite_armory(suite_path, Path(tmp))
        rag_report = benchmark_rag.run_benchmark(
            armory,
            benchmark_rag.load_cases(rag_dataset),
            top_k=3,
            min_score=0.0,
        )
        _validate_rag_suite_integrity(rag_report)
        benchmark_rag.print_text_report(rag_report)
        print()
        material_role_report = benchmark_material_roles.run_benchmark(
            armory,
            benchmark_material_roles.load_cases(material_role_dataset),
        )
        _validate_material_role_suite_integrity(material_role_report)
        benchmark_material_roles.print_text_report(material_role_report)
        print()
        document_understanding_report = benchmark_document_understanding.run_benchmark(
            armory,
            min_documents=document_understanding_min_documents,
            require_roles=tuple(
                benchmark_document_understanding._as_material_role(role)
                for role in document_understanding_required_roles
            ),
            min_overview_source_coverage=document_understanding_overview_coverage,
        )
        benchmark_document_understanding.print_text_report(document_understanding_report)
        print()
        index_integrity_report = benchmark_index_integrity.run_benchmark(
            armory,
            benchmark_index_integrity.load_cases(index_integrity_dataset),
        )
        _validate_index_integrity_suite_integrity(index_integrity_report)
        benchmark_index_integrity.print_text_report(index_integrity_report)
        print()
        priority_report = benchmark_priority.run_benchmark(
            armory,
            benchmark_priority.load_cases(priority_dataset),
        )
        _validate_priority_suite_integrity(priority_report)
        benchmark_priority.print_text_report(priority_report)
        print()
        prompt_cache_report = benchmark_prompt_cache.run_benchmark()
        benchmark_prompt_cache.print_text_report(prompt_cache_report)
        print()
        learning_intent_report = learning_intent_contract_report()
        print_learning_intent_contract_report(learning_intent_report)
        print()
        if not learning_intent_report.passed:
            raise ValueError(
                "learning intent normalizer contract failed: "
                + "; ".join(learning_intent_report.failures)
            )
        replay_cases = replay_answer_benchmark.load_cases(replay_dataset)
        _validate_replay_suite_integrity(replay_cases)
        print(f"Replay dataset: {len(replay_cases)} case(s) valid")
        print()
        chat_event_expectation_case = benchmark_chat_events.load_expectation(
            chat_event_expectation
        )
        _validate_overview_forbidden_phrase_contract(
            (chat_event_expectation_case,),
            label="chat-event expectation",
        )
        chat_events_report = benchmark_chat_events.run_chat_event_benchmark(
            benchmark_chat_events.load_events(chat_events_dataset),
            expectation=chat_event_expectation_case,
        )
        benchmark_chat_events.print_text_report(chat_events_report)
        print()
        chat_runtime_events_report = benchmark_chat_events.run_chat_event_benchmark(
            benchmark_chat_events.load_events(chat_runtime_events_dataset),
            expectation=chat_event_expectation_case,
        )
        benchmark_chat_events.print_text_report(chat_runtime_events_report)
        print()
        learning_state_report = learning_state_benchmark.run_benchmark(
            learning_state_benchmark.load_cases(learning_state_dataset),
            armory_path=armory,
        )
        _validate_learning_state_suite_integrity(learning_state_report)
        learning_state_benchmark.print_text_report(learning_state_report)
        print()
        academic_items_report = benchmark_academic_items.run_benchmark(
            armory,
            benchmark_academic_items.load_cases(academic_items_dataset),
        )
        benchmark_academic_items.print_text_report(academic_items_report)
        print()

    answer_cases = benchmark_answers.load_cases(answer_dataset)
    answer_report = benchmark_answers.run_benchmark(answer_cases)
    _validate_answer_suite_integrity(answer_report, answer_cases)
    benchmark_answers.print_text_report(answer_report)

    failed_threshold = (
        rag_report.hit_rate < rag_hit_rate
        or rag_report.mean_reciprocal_rank < rag_mrr
        or rag_report.mean_expected_recall < rag_expected_recall
        or rag_report.forbidden_before_expected_avoidance < rag_forbidden_before_expected_avoidance
        or answer_report.pass_rate < answer_pass_rate
        or answer_report.citation_validity_rate < citation_validity
        or answer_report.citation_presence_rate < citation_presence
        or answer_report.expected_citation_rate < expected_citations
        or answer_report.citation_source_rate < citation_sources
        or answer_report.required_text_rate < required_text
        or answer_report.forbidden_text_rate < forbidden_text
        or answer_report.supported_claim_rate < supported_claims
        or answer_report.contradiction_rate < contradiction_rate
        or answer_report.answer_shape_rate < answer_shape
        or answer_report.evidence_coverage_rate < evidence_coverage
        or answer_report.required_label_rate < required_label
        or material_role_report.pass_rate < material_role_pass_rate
        or not document_understanding_report.passed
        or index_integrity_report.pass_rate < index_integrity_pass_rate
        or index_integrity_report.required_text_rate < index_integrity_required_text
        or index_integrity_report.forbidden_text_rate < index_integrity_forbidden_text
        or (
            index_integrity_report.corpus_forbidden_text_rate
            < index_integrity_corpus_forbidden_text
        )
        or priority_report.pass_rate < priority_pass_rate
        or priority_report.topic_recall < priority_topic_recall
        or priority_report.forbidden_topic_avoidance < priority_forbidden_avoidance
        or priority_report.past_exam_source_recall < priority_past_exam_recall
        or bool(prompt_cache_report.failures)
        or bool(chat_events_report.failures)
        or bool(chat_runtime_events_report.failures)
        or not chat_runtime_events_report.has_tool_runtime
        or learning_state_report.pass_rate < learning_state_pass_rate
        or learning_state_report.transition_pass_rate < learning_state_transition_pass_rate
        or learning_state_report.scheduling_pass_rate < learning_state_scheduling_pass_rate
        or learning_state_report.mastery_metadata_rate < 1.0
        or academic_items_report.pass_rate < 1.0
        or academic_items_report.grounded_question_rate < 1.0
        or academic_items_report.canonical_source_label_rate < 1.0
        or academic_items_report.question_quality_rate < DEFAULT_ACADEMIC_QUESTION_QUALITY_RATE
        or len(academic_items_report.question_types) < DEFAULT_MIN_ACADEMIC_QUESTION_TYPES
    )
    status = 1 if failed_threshold else 0
    if report_path is not None:
        _write_json_report(
            report_path,
            _summary(
                suite_path=suite_path,
                status=status,
                rag_hit_rate=rag_hit_rate,
                rag_mrr=rag_mrr,
                rag_expected_recall=rag_expected_recall,
                rag_forbidden_before_expected_avoidance=(rag_forbidden_before_expected_avoidance),
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
                material_role_pass_rate=material_role_pass_rate,
                document_understanding_min_documents=document_understanding_min_documents,
                document_understanding_required_roles=document_understanding_required_roles,
                document_understanding_overview_coverage=(
                    document_understanding_overview_coverage
                ),
                index_integrity_pass_rate=index_integrity_pass_rate,
                index_integrity_required_text=index_integrity_required_text,
                index_integrity_forbidden_text=index_integrity_forbidden_text,
                index_integrity_corpus_forbidden_text=(index_integrity_corpus_forbidden_text),
                priority_pass_rate=priority_pass_rate,
                priority_topic_recall=priority_topic_recall,
                priority_forbidden_avoidance=priority_forbidden_avoidance,
                priority_past_exam_recall=priority_past_exam_recall,
                learning_state_pass_rate=learning_state_pass_rate,
                learning_state_transition_pass_rate=learning_state_transition_pass_rate,
                learning_state_scheduling_pass_rate=learning_state_scheduling_pass_rate,
                rag_report=rag_report,
                material_role_report=material_role_report,
                document_understanding_report=document_understanding_report,
                index_integrity_report=index_integrity_report,
                priority_report=priority_report,
                prompt_cache_report=prompt_cache_report,
                learning_intent_report=learning_intent_report,
                replay_case_count=len(replay_cases),
                replay_tasks=tuple(sorted({case.task for case in replay_cases if case.task})),
                chat_events_report=chat_events_report,
                chat_runtime_events_report=chat_runtime_events_report,
                answer_report=answer_report,
                learning_state_report=learning_state_report,
                academic_items_report=academic_items_report,
                manifest_report=manifest_report,
                report_path=report_path,
            ),
        )
        print(f"Wrote benchmark suite report to {report_path}")
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
    suite_path: Path,
    status: int,
    rag_hit_rate: float,
    rag_mrr: float,
    rag_expected_recall: float,
    rag_forbidden_before_expected_avoidance: float,
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
    material_role_pass_rate: float,
    document_understanding_min_documents: int,
    document_understanding_required_roles: tuple[str, ...],
    document_understanding_overview_coverage: float,
    index_integrity_pass_rate: float,
    index_integrity_required_text: float,
    index_integrity_forbidden_text: float,
    index_integrity_corpus_forbidden_text: float,
    priority_pass_rate: float,
    priority_topic_recall: float,
    priority_forbidden_avoidance: float,
    priority_past_exam_recall: float,
    learning_state_pass_rate: float,
    learning_state_transition_pass_rate: float,
    learning_state_scheduling_pass_rate: float,
    rag_report: benchmark_rag.BenchmarkReport,
    material_role_report: benchmark_material_roles.MaterialRoleBenchmarkReport,
    document_understanding_report: (benchmark_document_understanding.DocumentUnderstandingReport),
    index_integrity_report: benchmark_index_integrity.IndexIntegrityReport,
    priority_report: benchmark_priority.PriorityBenchmarkReport,
    prompt_cache_report: benchmark_prompt_cache.PromptCacheBenchmarkReport,
    learning_intent_report: LearningIntentContractReport,
    replay_case_count: int,
    replay_tasks: tuple[str, ...],
    chat_events_report: benchmark_chat_events.ChatEventBenchmarkReport,
    chat_runtime_events_report: benchmark_chat_events.ChatEventBenchmarkReport,
    answer_report: benchmark_answers.AnswerBenchmarkReport,
    learning_state_report: learning_state_benchmark.LearningStateBenchmarkReport,
    academic_items_report: benchmark_academic_items.AcademicItemBenchmarkReport,
    manifest_report: validate_benchmark_manifest.ManifestReport,
    report_path: Path | None = None,
) -> BenchmarkSuiteSummary:
    summary: BenchmarkSuiteSummary = {
        "suite": str(suite_path),
        "status": status,
        "thresholds": {
            "rag_hit_rate": rag_hit_rate,
            "rag_mrr": rag_mrr,
            "rag_expected_recall": rag_expected_recall,
            "rag_forbidden_before_expected_avoidance": (rag_forbidden_before_expected_avoidance),
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
            "material_role_pass_rate": material_role_pass_rate,
            "document_understanding_min_documents": document_understanding_min_documents,
            "document_understanding_required_roles": list(document_understanding_required_roles),
            "document_understanding_overview_coverage": (document_understanding_overview_coverage),
            "index_integrity_pass_rate": index_integrity_pass_rate,
            "index_integrity_required_text": index_integrity_required_text,
            "index_integrity_forbidden_text": index_integrity_forbidden_text,
            "index_integrity_corpus_forbidden_text": (index_integrity_corpus_forbidden_text),
            "priority_pass_rate": priority_pass_rate,
            "priority_topic_recall": priority_topic_recall,
            "priority_forbidden_avoidance": priority_forbidden_avoidance,
            "priority_past_exam_recall": priority_past_exam_recall,
            "learning_state_pass_rate": learning_state_pass_rate,
            "learning_state_transition_pass_rate": learning_state_transition_pass_rate,
            "learning_state_scheduling_pass_rate": learning_state_scheduling_pass_rate,
        },
        "rag": cast("dict[str, object]", asdict(rag_report)),
        "material_roles": cast("dict[str, object]", asdict(material_role_report)),
        "document_understanding": cast("dict[str, object]", asdict(document_understanding_report)),
        "index_integrity": cast("dict[str, object]", asdict(index_integrity_report)),
        "priority": cast("dict[str, object]", asdict(priority_report)),
        "prompt_cache": cast("dict[str, object]", asdict(prompt_cache_report)),
        "learning_intent": cast("dict[str, object]", asdict(learning_intent_report)),
        "replay": {
            "cases": replay_case_count,
            "tasks": list(replay_tasks),
        },
        "chat_events": cast("dict[str, object]", asdict(chat_events_report)),
        "chat_runtime_events": cast("dict[str, object]", asdict(chat_runtime_events_report)),
        "answers": cast("dict[str, object]", asdict(answer_report)),
        "learning_state": cast("dict[str, object]", asdict(learning_state_report)),
        "academic_items": cast("dict[str, object]", asdict(academic_items_report)),
        "manifest": cast("dict[str, object]", asdict(manifest_report)),
    }
    if report_path is not None:
        summary["report_path"] = str(report_path)
    return summary


def _write_json_report(path: Path, summary: BenchmarkSuiteSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--min-rag-hit-rate", type=float, default=DEFAULT_RAG_HIT_RATE)
    parser.add_argument("--min-rag-mrr", type=float, default=DEFAULT_RAG_MRR)
    parser.add_argument(
        "--min-rag-expected-recall",
        type=float,
        default=DEFAULT_RAG_EXPECTED_RECALL,
    )
    parser.add_argument(
        "--min-rag-forbidden-before-expected-avoidance",
        type=float,
        default=DEFAULT_RAG_FORBIDDEN_BEFORE_EXPECTED_AVOIDANCE,
    )
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
    parser.add_argument(
        "--min-material-role-pass-rate",
        type=float,
        default=DEFAULT_MATERIAL_ROLE_PASS_RATE,
    )
    parser.add_argument(
        "--min-document-understanding-overview-coverage",
        type=float,
        default=DEFAULT_DOCUMENT_UNDERSTANDING_OVERVIEW_COVERAGE,
    )
    parser.add_argument(
        "--min-index-integrity-pass-rate",
        type=float,
        default=DEFAULT_INDEX_INTEGRITY_PASS_RATE,
    )
    parser.add_argument(
        "--min-index-integrity-required-text",
        type=float,
        default=DEFAULT_INDEX_INTEGRITY_REQUIRED_TEXT,
    )
    parser.add_argument(
        "--min-index-integrity-forbidden-text",
        type=float,
        default=DEFAULT_INDEX_INTEGRITY_FORBIDDEN_TEXT,
    )
    parser.add_argument(
        "--min-index-integrity-corpus-forbidden-text",
        type=float,
        default=DEFAULT_INDEX_INTEGRITY_CORPUS_FORBIDDEN_TEXT,
    )
    parser.add_argument("--min-priority-pass-rate", type=float, default=DEFAULT_PRIORITY_PASS_RATE)
    parser.add_argument(
        "--min-priority-topic-recall",
        type=float,
        default=DEFAULT_PRIORITY_TOPIC_RECALL,
    )
    parser.add_argument(
        "--min-priority-forbidden-avoidance",
        type=float,
        default=DEFAULT_PRIORITY_FORBIDDEN_AVOIDANCE,
    )
    parser.add_argument(
        "--min-priority-past-exam-recall",
        type=float,
        default=DEFAULT_PRIORITY_PAST_EXAM_RECALL,
    )
    parser.add_argument(
        "--min-learning-state-pass-rate",
        type=float,
        default=DEFAULT_LEARNING_STATE_PASS_RATE,
    )
    parser.add_argument(
        "--min-learning-state-transition-pass-rate",
        type=float,
        default=DEFAULT_LEARNING_STATE_TRANSITION_PASS_RATE,
    )
    parser.add_argument(
        "--min-learning-state-scheduling-pass-rate",
        type=float,
        default=DEFAULT_LEARNING_STATE_SCHEDULING_PASS_RATE,
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help="Optional machine-readable benchmark suite report path",
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
    suite = cast("Path", args.suite).expanduser().resolve()
    rag_hit_rate = cast("float", args.min_rag_hit_rate)
    rag_mrr = cast("float", args.min_rag_mrr)
    rag_expected_recall = cast("float", args.min_rag_expected_recall)
    rag_forbidden_before_expected_avoidance = cast(
        "float",
        args.min_rag_forbidden_before_expected_avoidance,
    )
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
    material_role_pass_rate = cast("float", args.min_material_role_pass_rate)
    document_understanding_overview_coverage = cast(
        "float",
        args.min_document_understanding_overview_coverage,
    )
    index_integrity_pass_rate = cast("float", args.min_index_integrity_pass_rate)
    index_integrity_required_text = cast("float", args.min_index_integrity_required_text)
    index_integrity_forbidden_text = cast("float", args.min_index_integrity_forbidden_text)
    index_integrity_corpus_forbidden_text = cast(
        "float",
        args.min_index_integrity_corpus_forbidden_text,
    )
    priority_pass_rate = cast("float", args.min_priority_pass_rate)
    priority_topic_recall = cast("float", args.min_priority_topic_recall)
    priority_forbidden_avoidance = cast("float", args.min_priority_forbidden_avoidance)
    priority_past_exam_recall = cast("float", args.min_priority_past_exam_recall)
    learning_state_pass_rate = cast("float", args.min_learning_state_pass_rate)
    learning_state_transition_pass_rate = cast(
        "float", args.min_learning_state_transition_pass_rate
    )
    learning_state_scheduling_pass_rate = cast(
        "float", args.min_learning_state_scheduling_pass_rate
    )
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
    compare_to = cast("Path | None", args.compare_to)
    if compare_to is not None:
        compare_to = compare_to.expanduser().resolve()
    compare_tolerance = cast("float", args.compare_tolerance)

    _validate_rate(rag_hit_rate, "--min-rag-hit-rate", parser)
    _validate_rate(rag_mrr, "--min-rag-mrr", parser)
    _validate_rate(rag_expected_recall, "--min-rag-expected-recall", parser)
    _validate_rate(
        rag_forbidden_before_expected_avoidance,
        "--min-rag-forbidden-before-expected-avoidance",
        parser,
    )
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
    _validate_rate(material_role_pass_rate, "--min-material-role-pass-rate", parser)
    _validate_rate(
        document_understanding_overview_coverage,
        "--min-document-understanding-overview-coverage",
        parser,
    )
    _validate_rate(index_integrity_pass_rate, "--min-index-integrity-pass-rate", parser)
    _validate_rate(index_integrity_required_text, "--min-index-integrity-required-text", parser)
    _validate_rate(
        index_integrity_forbidden_text,
        "--min-index-integrity-forbidden-text",
        parser,
    )
    _validate_rate(
        index_integrity_corpus_forbidden_text,
        "--min-index-integrity-corpus-forbidden-text",
        parser,
    )
    _validate_rate(priority_pass_rate, "--min-priority-pass-rate", parser)
    _validate_rate(priority_topic_recall, "--min-priority-topic-recall", parser)
    _validate_rate(priority_forbidden_avoidance, "--min-priority-forbidden-avoidance", parser)
    _validate_rate(priority_past_exam_recall, "--min-priority-past-exam-recall", parser)
    _validate_rate(learning_state_pass_rate, "--min-learning-state-pass-rate", parser)
    _validate_rate(
        learning_state_transition_pass_rate,
        "--min-learning-state-transition-pass-rate",
        parser,
    )
    _validate_rate(
        learning_state_scheduling_pass_rate,
        "--min-learning-state-scheduling-pass-rate",
        parser,
    )
    if compare_tolerance < 0:
        parser.error("--compare-tolerance must be non-negative")

    try:
        return run_suite(
            suite,
            rag_hit_rate=rag_hit_rate,
            rag_mrr=rag_mrr,
            rag_expected_recall=rag_expected_recall,
            rag_forbidden_before_expected_avoidance=(rag_forbidden_before_expected_avoidance),
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
            material_role_pass_rate=material_role_pass_rate,
            document_understanding_overview_coverage=(document_understanding_overview_coverage),
            index_integrity_pass_rate=index_integrity_pass_rate,
            index_integrity_required_text=index_integrity_required_text,
            index_integrity_forbidden_text=index_integrity_forbidden_text,
            index_integrity_corpus_forbidden_text=index_integrity_corpus_forbidden_text,
            priority_pass_rate=priority_pass_rate,
            priority_topic_recall=priority_topic_recall,
            priority_forbidden_avoidance=priority_forbidden_avoidance,
            priority_past_exam_recall=priority_past_exam_recall,
            learning_state_pass_rate=learning_state_pass_rate,
            learning_state_transition_pass_rate=learning_state_transition_pass_rate,
            learning_state_scheduling_pass_rate=learning_state_scheduling_pass_rate,
            report_path=json_report,
            compare_to=compare_to,
            compare_tolerance=compare_tolerance,
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"benchmark suite error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
