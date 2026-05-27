from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import audit_agent_harness_completion, run_benchmark_suite

PRIVATE_DEFAULT_SUITE = run_benchmark_suite.DEFAULT_SUITE
PRIVATE_DEFAULT_SUITE_AVAILABLE = (PRIVATE_DEFAULT_SUITE / "manifest.json").is_file()
requires_private_default_suite = pytest.mark.skipif(
    not PRIVATE_DEFAULT_SUITE_AVAILABLE,
    reason="private benchmark suite is local-only",
)
PRIVATE_MODEL_MATRIX_EXAMPLE = (
    audit_agent_harness_completion.REPO_ROOT / "benchmarks" / "model-matrix.example.json"
)
PRIVATE_MODEL_MATRIX_EXAMPLE_AVAILABLE = PRIVATE_MODEL_MATRIX_EXAMPLE.is_file()
requires_private_model_matrix_example = pytest.mark.skipif(
    not PRIVATE_MODEL_MATRIX_EXAMPLE_AVAILABLE,
    reason="private model matrix example is local-only",
)

_PASSING_MODEL_METRICS = {
    "cases": 4,
    "domains": ["biology", "cross-domain", "history", "mathematics"],
    "tasks": ["abstention", "citation-check", "grounded-explanation", "material-overview"],
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
_PASSING_CHILD_THRESHOLDS = {
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
    "min_answer_domains": 3,
    "min_answer_tasks": 3,
}


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _chat_fixture_answer() -> str:
    return (
        "The enabled materials include lecture notes and past exam practice [E1] [E2].\n"
        "- Content areas visible in the cited excerpts include definitions, theorems, "
        "examples, and proof practice [E1][E2].\n"
        "- @lecture.md: Definitions, theorems, and examples [E1].\n"
        "- @exam.md: Past exam proof practice [E2]."
    )


def _chat_fixture_evidence() -> list[dict[str, object]]:
    return [
        {
            "id": "E1",
            "source": "materials/lecture.md",
            "chunk": 0,
            "text": "Lecture notes. Definitions, theorems, and examples.",
        },
        {
            "id": "E2",
            "source": "materials/exam.md",
            "chunk": 0,
            "text": "Past exam. Question 1 asks for a proof.",
        },
    ]


def _chat_fixture_expectation() -> list[dict[str, object]]:
    return [
        {
            "id": "overview",
            "task": "material-overview",
            "must_include": ["The enabled materials include", "Content areas"],
            "must_not_include": ["the files cover", "next action"],
            "expected_citations": ["E1", "E2"],
            "min_words": 24,
            "min_citation_count": 2,
            "min_distinct_sources": 2,
            "min_bullet_count": 2,
            "min_cited_bullet_count": 2,
            "max_explicit_date_lines": 1,
            "required_material_operations": ["sample_overview"],
            "evidence": _chat_fixture_evidence(),
        }
    ]


def _chat_fixture_material_operations() -> list[dict[str, object]]:
    return [
        {
            "type": "material_operation",
            "operation": "index_ready",
            "message": "Material index ready: 2 enabled sources, 2 chunks.",
            "metadata": {"indexed_sources": 2, "indexed_chunks": 2},
        },
        {
            "type": "material_operation",
            "operation": "sample_overview",
            "message": "Sampling corpus overview: 2 excerpts from 2 of 2 indexed sources.",
            "metadata": {
                "query": "what is the material about",
                "evidence_blocks": 2,
                "sampled_sources": 2,
                "total_sources": 2,
            },
        },
        {
            "type": "material_operation",
            "operation": "read_excerpt",
            "message": "Opened materials/lecture.md#chunk=0: Lecture notes.",
            "metadata": {
                "evidence_id": "E1",
                "ref": "materials/lecture.md#chunk=0",
                "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
            },
        },
        {
            "type": "material_operation",
            "operation": "read_excerpt",
            "message": "Opened materials/exam.md#chunk=0: Past exam.",
            "metadata": {
                "evidence_id": "E2",
                "ref": "materials/exam.md#chunk=0",
                "text_excerpt": "Past exam. Question 1 asks for a proof.",
            },
        },
    ]


def _chat_fixture_events(*, include_tool_runtime: bool = False) -> list[dict[str, object]]:
    answer = _chat_fixture_answer()
    tool_runtime_events: list[dict[str, object]] = []
    if include_tool_runtime:
        tool_runtime_events = [
            {
                "type": "notice",
                "code": "acceptance_criteria",
                "message": "Acceptance criteria: inspect sources with tools.",
                "metadata": {"source": "agent_harness", "requires_tools": True},
            },
            {
                "type": "notice",
                "code": "tool_runtime",
                "message": "Execution note: repeated call.",
                "metadata": {
                    "tool": "read_file",
                    "reason": "repeated_call",
                    "repeat_count": 2,
                    "arguments": {"path": "materials/lecture.md"},
                },
            },
        ]
    return [
        {"type": "notice", "code": "reading", "message": "Reading."},
        *_chat_fixture_material_operations(),
        *tool_runtime_events,
        {
            "type": "notice",
            "code": "evidence",
            "message": "Using evidence.",
            "metadata": {
                "refs": ["materials/lecture.md#chunk=0", "materials/exam.md#chunk=0"],
                "coverage": {
                    "evidence_blocks": 2,
                    "sampled_sources": 2,
                    "total_sources": 2,
                },
                "items": [
                    {
                        "evidence_id": "E1",
                        "ref": "materials/lecture.md#chunk=0",
                        "text_excerpt": "Lecture notes. Definitions, theorems, and examples.",
                    },
                    {
                        "evidence_id": "E2",
                        "ref": "materials/exam.md#chunk=0",
                        "text_excerpt": "Past exam. Question 1 asks for a proof.",
                    },
                ],
            },
        },
        {"type": "notice", "code": "writing", "message": "Writing."},
        {"type": "assistant_delta", "delta": answer},
        {"type": "turn_complete", "full_text": answer, "turn_index": 1},
    ]


def _write_chat_event_suite(suite: Path) -> Path:
    suite.mkdir(parents=True)
    _write_jsonl(suite / "chat_events.jsonl", _chat_fixture_events())
    _write_jsonl(
        suite / "chat_events_runtime.jsonl",
        _chat_fixture_events(include_tool_runtime=True),
    )
    (suite / "chat_event_expectation.json").write_text(
        json.dumps(_chat_fixture_expectation()),
        encoding="utf-8",
    )
    (suite / "manifest.json").write_text(
        json.dumps(
            {
                "corpus_kind": "chat-event-fixture",
                "documents": [
                    {
                        "source": "materials/lecture.md",
                        "domain": "mathematics",
                        "role": "lecture",
                        "document_type": "notes",
                        "stressors": ["overview"],
                        "permission_note": "temporary test fixture",
                    }
                ],
                "datasets": [
                    {"path": "chat_events.jsonl", "kind": "chat-events"},
                    {"path": "chat_events_runtime.jsonl", "kind": "chat-events-runtime"},
                    {
                        "path": "chat_event_expectation.json",
                        "kind": "chat-event-answer-expectation",
                    },
                ],
                "known_limits": [],
            }
        ),
        encoding="utf-8",
    )
    return suite


def _write_candidate_replay_report(path: Path, *, status: int = 0) -> None:
    artifact_root = path.parent.parent if path.parent.name == "model-output" else path.parent
    output = path.with_suffix(".answers.jsonl")
    fixture_cases = (
        {
            "id": "case-1",
            "domain": "mathematics",
            "task": "grounded-explanation",
            "answer": "The answer is grounded in the source [E1].",
            "expected_citations": ["E1"],
            "must_include": ["grounded"],
            "must_not_include": ["unsupported"],
        },
        {
            "id": "case-2",
            "domain": "biology",
            "task": "citation-check",
            "answer": "The answer is grounded in the source [E1].",
            "expected_citations": ["E1"],
            "must_include": ["grounded"],
            "must_not_include": ["unsupported"],
        },
        {
            "id": "case-3",
            "domain": "history",
            "task": "abstention",
            "answer": "The answer is grounded in the source [E1].",
            "expected_citations": ["E1"],
            "must_include": ["grounded"],
            "must_not_include": ["unsupported"],
        },
        {
            "id": "case-4",
            "domain": "cross-domain",
            "task": "material-overview",
            "answer": (
                "The retrieved overview sample is not an exhaustive summary, "
                "but it is grounded in indexed sources [E1].\n"
                "- Source signal: the first document supports the main claim [E1].\n"
                "- Cross-check: another indexed source confirms supporting context [E2]."
            ),
            "expected_citations": ["E1", "E2"],
            "must_include": ["retrieved overview sample", "not an exhaustive summary"],
            "min_words": 16,
            "max_words": 120,
            "min_citation_count": 2,
            "min_distinct_sources": 2,
            "min_bullet_count": 2,
            "min_cited_bullet_count": 2,
            "max_explicit_date_lines": 1,
        },
    )
    output.write_text(
        "\n".join(
            json.dumps(
                {
                    **case,
                    "evidence": [
                        {
                            "id": "E1",
                            "source": "materials/source.md",
                            "chunk": 0,
                            "text": "The answer is grounded in the source.",
                            "score": 1.0,
                        },
                        {
                            "id": "E2",
                            "source": "materials/other-source.md",
                            "chunk": 0,
                            "text": "Another indexed source is available.",
                            "score": 1.0,
                        },
                    ],
                }
            )
            for case in fixture_cases
        )
        + "\n",
        encoding="utf-8",
    )
    path.write_text(
        json.dumps(
            {
                "status": status,
                "armory": str(artifact_root / "armory"),
                "replay_dataset": str(artifact_root / "replay.jsonl"),
                "model": path.stem.removesuffix(".report"),
                "base_url": "",
                "output": str(output),
                "thresholds": _PASSING_CHILD_THRESHOLDS,
                "report": _PASSING_MODEL_METRICS,
            }
        ),
        encoding="utf-8",
    )


def _write_valid_replay_dataset(path: Path) -> None:
    path.write_text(
        "\n".join(
            json.dumps(case)
            for case in (
                {
                    "id": "case-1",
                    "domain": "mathematics",
                    "task": "grounded-explanation",
                    "prompt": "Answer with grounded evidence.",
                    "must_include": ["grounded"],
                },
                {
                    "id": "case-2",
                    "domain": "biology",
                    "task": "citation-check",
                    "prompt": "Answer with citation evidence.",
                    "expected_citations": ["E1"],
                },
                {
                    "id": "case-3",
                    "domain": "history",
                    "task": "abstention",
                    "prompt": "Answer only if the source contains it.",
                    "require_abstention": True,
                },
                {
                    "id": "case-4",
                    "domain": "cross-domain",
                    "task": "material-overview",
                    "prompt": "Give a grounded overview of the enabled material.",
                    "must_include": ["retrieved overview sample"],
                    "min_words": 16,
                    "max_words": 120,
                    "min_citation_count": 2,
                    "min_distinct_sources": 2,
                    "min_bullet_count": 2,
                    "min_cited_bullet_count": 2,
                    "max_explicit_date_lines": 1,
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_model_matrix_report(path: Path) -> None:
    (path.parent / "armory").mkdir()
    (path.parent / "model-output").mkdir()
    _write_valid_replay_dataset(path.parent / "replay.jsonl")
    local_report = path.parent / "model-output" / "local-small.report.json"
    frontier_report = path.parent / "model-output" / "frontier-hosted.report.json"
    _write_candidate_replay_report(local_report)
    _write_candidate_replay_report(frontier_report)
    local_output = local_report.with_suffix(".answers.jsonl")
    frontier_output = frontier_report.with_suffix(".answers.jsonl")
    path.write_text(
        json.dumps(
            {
                "status": 0,
                "armory": str(path.parent / "armory"),
                "replay_dataset": str(path.parent / "replay.jsonl"),
                "output_dir": str(path.parent / "model-output"),
                "required_groups": ["frontier", "local"],
                "groups": ["frontier", "local"],
                "replay_cases": 4,
                "replay_domains": ["biology", "cross-domain", "history", "mathematics"],
                "replay_tasks": [
                    "abstention",
                    "citation-check",
                    "grounded-explanation",
                    "material-overview",
                ],
                "results": [
                    {
                        "candidate_id": "local-small",
                        "group": "local",
                        "model": "local-small",
                        "base_url": "",
                        "provider_slug": "",
                        "auth_source": "base_url",
                        "status": 0,
                        "output": str(local_output),
                        "report_path": str(local_report),
                        **_PASSING_MODEL_METRICS,
                    },
                    {
                        "candidate_id": "frontier-hosted",
                        "group": "frontier",
                        "model": "frontier-hosted",
                        "base_url": "",
                        "provider_slug": "openai-codex",
                        "auth_source": "codex_oauth",
                        "status": 0,
                        "output": str(frontier_output),
                        "report_path": str(frontier_report),
                        **_PASSING_MODEL_METRICS,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _retarget_model_matrix_armory(model_report: Path, armory: Path) -> None:
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["armory"] = str(armory)
    for result in payload["results"]:
        child_report = Path(result["report_path"])
        child_payload = json.loads(child_report.read_text(encoding="utf-8"))
        child_payload["armory"] = str(armory)
        child_report.write_text(json.dumps(child_payload), encoding="utf-8")
    model_report.write_text(json.dumps(payload), encoding="utf-8")


def _retarget_model_matrix_replay_dataset(model_report: Path, replay_dataset: Path) -> None:
    _write_valid_replay_dataset(replay_dataset)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["replay_dataset"] = str(replay_dataset)
    for result in payload["results"]:
        child_report = Path(result["report_path"])
        child_payload = json.loads(child_report.read_text(encoding="utf-8"))
        child_payload["replay_dataset"] = str(replay_dataset)
        child_report.write_text(json.dumps(child_payload), encoding="utf-8")
    model_report.write_text(json.dumps(payload), encoding="utf-8")


def _write_real_manifest(tmp_path: Path) -> Path:
    suite = tmp_path / "real-suite"
    suite.mkdir()
    armory = suite / "armory"
    materials = armory / "materials"
    materials.mkdir(parents=True)
    _write_jsonl(suite / "chat_events.jsonl", _chat_fixture_events())
    _write_jsonl(
        suite / "chat_events_runtime.jsonl", _chat_fixture_events(include_tool_runtime=True)
    )
    (suite / "chat_event_expectation.json").write_text(
        json.dumps(_chat_fixture_expectation()),
        encoding="utf-8",
    )
    _write_valid_replay_dataset(suite / "replay.jsonl")
    manifest_path = suite / "manifest.json"
    domains = ["math", "biology", "chemistry", "physics", "history"]
    document_types = [
        "pdf",
        "scanned-pdf",
        "lecture-slides",
        "exercise-sheet",
        "past-exam",
        "solutions",
        "table-heavy-notes",
        "multilingual-notes",
    ]
    stressors = [
        "real-pdf",
        "ocr-noise",
        "table-heavy",
        "multi-column",
        "multilingual",
        "formula-language",
        "unicode",
        "past-exam",
        "exercise-sheet",
        "slides",
        "scan-artifacts",
        "near-miss-concept",
        "multi-source-synthesis",
        "boilerplate",
        "points-format",
        "tables",
    ]
    documents = []
    for idx in range(40):
        source = f"materials/real-{idx}.md"
        (materials / f"real-{idx}.md").write_text("real corpus placeholder\n", encoding="utf-8")
        documents.append(
            {
                "id": f"real-corpus-{idx}",
                "title": f"Real corpus fixture {idx}",
                "source": source,
                "domain": domains[idx % len(domains)],
                "role": ("past_exam", "lecture", "assignment")[idx % 3],
                "document_type": document_types[idx % len(document_types)],
                "permission_note": "test fixture permissioned corpus",
                "stressors": [
                    stressors[idx % len(stressors)],
                    stressors[(idx + 5) % len(stressors)],
                ],
            }
        )
    manifest_path.write_text(
        json.dumps(
            {
                "id": "permissioned-real-test",
                "description": "Permissioned real-corpus fixture manifest.",
                "corpus_kind": "permissioned-pdfs",
                "documents": documents,
                "datasets": [
                    {"path": "chat_events.jsonl", "kind": "chat-events"},
                    {
                        "path": "chat_event_expectation.json",
                        "kind": "chat-event-answer-expectation",
                    },
                    {"path": "replay.jsonl", "kind": "model-replay-prompts"},
                ],
                "known_limits": [],
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_real_preflight_report(path: Path, manifest_path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": 0,
                "armory_path": str(manifest_path.parent / "armory"),
                "manifest_path": str(manifest_path),
                "failures": [],
                "manifest": {"documents": 40},
                "document_understanding": {
                    "visible_materials": 40,
                    "indexed_documents": 40,
                    "chunks": 80,
                    "role_counts": {
                        "assignment": 13,
                        "past_exam": 14,
                        "slides": 13,
                    },
                    "indexed_role_counts": {
                        "assignment": 13,
                        "past_exam": 14,
                        "slides": 13,
                    },
                    "extraction_health_passed": True,
                    "extraction_health_pass_rate": 1.0,
                    "overview_sampled_sources": 16,
                    "overview_total_sources": 40,
                    "overview_source_coverage_rate": 0.4,
                    "failures": [],
                },
            }
        ),
        encoding="utf-8",
    )


def _write_public_academic_real_manifest(tmp_path: Path) -> Path:
    suite = tmp_path / "public-suite"
    suite.mkdir()
    for dataset in ("chat_events.jsonl", "chat_event_expectation.json", "replay.jsonl"):
        (suite / dataset).write_text("{}\n", encoding="utf-8")
    domains = (
        "artificial-intelligence",
        "software-engineering",
        "computer-vision",
        "security",
        "reinforcement-learning",
    )
    roles = ("textbook", "lecture-notes", "reference")
    document_types = (
        "html-textbook-section",
        "html-course-notes",
        "html-chapter-summary",
        "html-lecture-notes",
        "html-search-textbook-section",
        "html-probability-textbook-section",
        "html-game-theory-textbook-section",
        "html-reinforcement-learning-section",
    )
    stressors = (
        "public-html",
        "course-notes",
        "textbook-section",
        "search",
        "security",
        "software-engineering",
        "computer-vision",
        "deep-learning",
        "reinforcement-learning",
        "rl",
        "artificial-intelligence",
        "probabilistic-modeling",
        "bayes-nets",
        "constraint-satisfaction",
        "decision-processes",
        "games",
    )
    documents = [
        {
            "id": f"public-academic-{idx}",
            "title": f"Public academic document {idx}",
            "source": f"materials/public-academic/doc-{idx}.html",
            "source_url": f"https://example.edu/course/doc-{idx}.html",
            "bytes": 100 + idx,
            "sha256": f"{idx:064x}"[-64:],
            "source_organization": "Example University",
            "license": "Public academic fixture attribution.",
            "license_url": "https://example.edu/license",
            "attribution": "Example University public course fixture.",
            "domain": domains[idx % len(domains)],
            "role": roles[idx % len(roles)],
            "document_type": document_types[idx % len(document_types)],
            "stressors": [
                stressors[idx % len(stressors)],
                stressors[(idx + 5) % len(stressors)],
            ],
        }
        for idx in range(40)
    ]
    manifest_path = suite / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "id": "public-academic-real-test",
                "description": "Public academic fixture manifest.",
                "corpus_kind": "public-academic",
                "documents": documents,
                "datasets": [
                    {"path": "chat_events.jsonl", "kind": "chat-events"},
                    {
                        "path": "chat_event_expectation.json",
                        "kind": "chat-event-answer-expectation",
                    },
                    {"path": "replay.jsonl", "kind": "model-replay-prompts"},
                ],
                "known_limits": [],
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_public_academic_preflight_report(path: Path, manifest_path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": 0,
                "armory_path": str(manifest_path.parent),
                "manifest_path": str(manifest_path),
                "failures": [],
                "manifest": {"corpus_kind": "public-academic", "documents": 40},
                "document_understanding": {
                    "visible_materials": 40,
                    "indexed_documents": 40,
                    "chunks": 80,
                    "role_counts": {"lecture": 12, "textbook": 16, "reference": 12},
                    "indexed_role_counts": {"lecture": 12, "textbook": 16, "reference": 12},
                    "extraction_health_passed": True,
                    "extraction_health_pass_rate": 1.0,
                    "overview_sampled_sources": 16,
                    "overview_total_sources": 40,
                    "overview_source_coverage_rate": 0.4,
                    "failures": [],
                },
            }
        ),
        encoding="utf-8",
    )


def test_completion_audit_is_incomplete_without_external_proof() -> None:
    report = audit_agent_harness_completion.audit_completion()
    items_by_requirement = {item.requirement: item for item in report.items}

    assert report.status == "incomplete"
    assert "No fixture-specific course terms in runtime harness code" not in report.missing
    assert "Large real/public or permissioned academic corpus" in report.missing
    assert (
        "Real corpus preflight passes extraction, indexing, and role smoke checks"
        in report.missing
    )
    assert "Real corpus public chat JSONL harness events pass" in report.missing
    assert "Model-backed replay eval passes local and frontier groups" in report.missing
    assert all(
        item.status == "covered"
        for item in report.items
        if item.requirement == "scripts/prepare_real_corpus_evidence.py"
    )
    assert all(
        item.status == "covered"
        for item in report.items
        if item.requirement == "scripts/discover_real_corpus_candidates.py"
    )
    assert all(
        item.status == "covered"
        for item in report.items
        if item.requirement == "scripts/build_permissioned_corpus_armory.py"
    )
    assert all(
        item.status == "covered"
        for item in report.items
        if item.requirement == "scripts/materialize_public_corpus.py"
    )
    if PRIVATE_DEFAULT_SUITE_AVAILABLE:
        assert (
            items_by_requirement[
                "Deterministic suite verifies public chat JSONL harness events"
            ].status
            == "covered"
        )
        assert (
            items_by_requirement["Deterministic academic benchmark suite passes"].status
            == "covered"
        )
    else:
        assert items_by_requirement["Private deterministic benchmark suite manifest"].status == (
            "missing"
        )
        assert (
            items_by_requirement[
                "Deterministic suite verifies public chat JSONL harness events"
            ].status
            == "missing"
        )
        assert (
            items_by_requirement["Deterministic academic benchmark suite passes"].status
            == "missing"
        )
    assert any("--min-roles 3" in command for command in report.next_steps)
    assert any("build_permissioned_corpus_armory" in command for command in report.next_steps)
    assert any("--domain-from-parent" in command for command in report.next_steps)
    assert any("--balance-domains" in command for command in report.next_steps)
    assert any("--infer-roles-from-index" in command for command in report.next_steps)
    assert any("benchmark_chat_events" in command for command in report.next_steps)


def test_completion_audit_reports_missing_private_suite_without_skipping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    (repo / "hephaion").mkdir(parents=True)
    scripts = repo / "scripts"
    scripts.mkdir()
    for script_name in (
        "run_benchmark_suite.py",
        "benchmark_document_understanding.py",
        "discover_real_corpus_candidates.py",
        "build_permissioned_corpus_armory.py",
        "prepare_real_corpus_evidence.py",
        "replay_answer_benchmark.py",
        "benchmark_chat_events.py",
        "extract_chat_event_expectation.py",
        "materialize_public_corpus.py",
        "run_model_eval_matrix.py",
    ):
        (scripts / script_name).write_text(
            "from __future__ import annotations\n", encoding="utf-8"
        )
    monkeypatch.setattr(audit_agent_harness_completion, "REPO_ROOT", repo)

    report = audit_agent_harness_completion.audit_completion()

    items_by_requirement = {item.requirement: item for item in report.items}
    assert report.status == "incomplete"
    assert items_by_requirement[
        "No fixture-specific course terms in runtime harness code"
    ].status == ("covered")
    assert items_by_requirement[
        "No fixture-specific course terms in non-fixture harness scripts"
    ].status == ("covered")
    assert items_by_requirement["Private deterministic benchmark suite manifest"].status == (
        "missing"
    )
    assert items_by_requirement["Deterministic academic benchmark suite passes"].status == (
        "missing"
    )
    assert (
        items_by_requirement[
            "Deterministic suite verifies public chat JSONL harness events"
        ].status
        == "missing"
    )
    assert "Large real/public or permissioned academic corpus" in report.missing


@requires_private_default_suite
def test_completion_audit_runs_default_deterministic_suite() -> None:
    item = audit_agent_harness_completion._deterministic_benchmark_suite_item()

    assert item.status == "covered"
    assert str(run_benchmark_suite.DEFAULT_SUITE) in item.evidence
    assert "academic_items_pass_rate=1.000" in item.evidence
    assert "academic_question_type_count=6" in item.evidence
    assert "academic_grounded_question_rate=1.000" in item.evidence
    assert "academic_canonical_source_label_rate=1.000" in item.evidence
    assert "learning_intent_contract_passed=True" in item.evidence
    assert "recall_clarification" in item.evidence


def test_completion_audit_rejects_failing_deterministic_suite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit_agent_harness_completion.run_benchmark_suite, "run_suite", lambda: 1)

    item = audit_agent_harness_completion._deterministic_benchmark_suite_item()

    assert item.status == "missing"
    assert "status is 1" in item.evidence


def test_completion_audit_verifies_chat_event_suite(tmp_path: Path) -> None:
    suite = _write_chat_event_suite(tmp_path / "benchmarks" / "academic")

    item = audit_agent_harness_completion._deterministic_chat_event_suite_item(suite)

    assert item.status == "covered"
    assert str(suite / "chat_events.jsonl") in item.evidence
    assert "consistent=True" in item.evidence
    assert "metadata=True" in item.evidence
    assert "tool_runtime_metadata_rate=1.000" in item.evidence
    assert "runtime_fixture_tool_runtime=True" in item.evidence
    assert "runtime_fixture_metadata_rate=1.000" in item.evidence
    assert "runtime_fixture_repeated_call=True" in item.evidence
    assert "runtime_fixture_acceptance_criteria_metadata_rate=1.000" in item.evidence
    assert "answer_pass_rate=1.000" in item.evidence


def test_completion_audit_rejects_inconsistent_chat_event_completion(
    tmp_path: Path,
) -> None:
    suite = _write_chat_event_suite(tmp_path / "benchmarks" / "academic")
    lines = []
    for line in (suite / "chat_events.jsonl").read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("type") == "turn_complete":
            payload["full_text"] = "The files cover vague material [E1] [E2]. Say ready."
        lines.append(json.dumps(payload))
    (suite / "chat_events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._deterministic_chat_event_suite_item(suite)

    assert item.status == "missing"
    assert "assistant delta text does not match turn completion text" in item.evidence


def test_completion_audit_rejects_manifest_without_chat_event_dataset(
    tmp_path: Path,
) -> None:
    suite = _write_chat_event_suite(tmp_path / "benchmarks" / "academic")
    manifest_path = suite / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["datasets"] = [
        dataset
        for dataset in manifest["datasets"]
        if dataset["kind"] not in {"chat-events", "chat-events-runtime"}
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    item = audit_agent_harness_completion._deterministic_chat_event_suite_item(suite)

    assert item.status == "missing"
    assert "chat-events dataset" in item.evidence


def test_completion_audit_rejects_fixture_terms_in_runtime_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = tmp_path / "hephaion"
    runtime.mkdir()
    (runtime / "bad.py").write_text('EXAMPLE = "fixture_private_course"\n', encoding="utf-8")
    monkeypatch.setattr(audit_agent_harness_completion, "REPO_ROOT", tmp_path)

    item = audit_agent_harness_completion._runtime_generality_item()

    assert item.status == "missing"
    assert "fixture_private_course" in item.evidence


def test_completion_audit_rejects_fixture_terms_in_harness_scripts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "bad_harness.py").write_text(
        'COURSE = "fixture_private_name"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(audit_agent_harness_completion, "REPO_ROOT", tmp_path)

    item = audit_agent_harness_completion._script_generality_item()

    assert item.status == "missing"
    assert "fixture_private_name" in item.evidence


@requires_private_model_matrix_example
def test_completion_audit_verifies_model_matrix_example_responsibilities() -> None:
    item = audit_agent_harness_completion._model_matrix_example_item()

    assert item.status == "covered"
    assert "local_responsibilities=" in item.evidence
    assert "frontier_responsibilities=" in item.evidence


def test_completion_audit_rejects_model_matrix_example_without_responsibilities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark_dir = tmp_path / "benchmarks"
    benchmark_dir.mkdir()
    (benchmark_dir / "model-matrix.example.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "local-small",
                        "group": "local",
                        "model": "local-small",
                    },
                    {
                        "id": "frontier-hosted",
                        "group": "frontier",
                        "model": "frontier-hosted",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(audit_agent_harness_completion, "REPO_ROOT", tmp_path)

    item = audit_agent_harness_completion._model_matrix_example_item()

    assert item.status == "missing"
    assert "missing responsibilities" in item.evidence


def test_completion_audit_allows_fixture_terms_inside_audit_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "audit_agent_harness_completion.py").write_text(
        'FORBIDDEN = "fixture_private_name"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(audit_agent_harness_completion, "REPO_ROOT", tmp_path)

    item = audit_agent_harness_completion._script_generality_item()

    assert item.status == "covered"


def test_completion_audit_can_pass_with_real_manifest_and_model_report(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    _retarget_model_matrix_armory(model_report, manifest.parent / "armory")
    _retarget_model_matrix_replay_dataset(model_report, manifest.parent / "replay.jsonl")

    report = audit_agent_harness_completion.audit_completion(
        real_manifest=manifest,
        real_preflight_report=preflight_report,
        model_matrix_report=model_report,
    )

    if PRIVATE_DEFAULT_SUITE_AVAILABLE and PRIVATE_MODEL_MATRIX_EXAMPLE_AVAILABLE:
        assert report.status == "complete"
        assert report.missing == ()
    else:
        assert report.status == "incomplete"
        assert "Large real/public or permissioned academic corpus" not in report.missing
        assert (
            "Real corpus preflight passes extraction, indexing, and role smoke checks"
            not in report.missing
        )
        assert "Real corpus public chat JSONL harness events pass" not in report.missing
        assert "Model-backed replay eval passes local and frontier groups" not in report.missing
    real_chat_item = next(
        item
        for item in report.items
        if item.requirement == "Real corpus public chat JSONL harness events pass"
    )
    assert "tool_runtime_metadata_rate=1.000" in real_chat_item.evidence
    assert "acceptance_criteria_metadata_rate=1.000" in real_chat_item.evidence


def test_completion_audit_rejects_inconsistent_real_chat_event_completion(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    _retarget_model_matrix_armory(model_report, manifest.parent / "armory")
    _retarget_model_matrix_replay_dataset(model_report, manifest.parent / "replay.jsonl")
    chat_events = manifest.parent / "chat_events.jsonl"
    lines = []
    for line in chat_events.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("type") == "turn_complete":
            payload["full_text"] = "The files cover vague material [E1] [E2]. Say ready."
        lines.append(json.dumps(payload))
    chat_events.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = audit_agent_harness_completion.audit_completion(
        real_manifest=manifest,
        real_preflight_report=preflight_report,
        model_matrix_report=model_report,
    )

    item = next(
        item
        for item in report.items
        if item.requirement == "Real corpus public chat JSONL harness events pass"
    )
    assert report.status == "incomplete"
    assert item.status == "missing"
    assert "assistant delta text does not match turn completion text" in item.evidence


def test_completion_audit_rejects_unreviewed_real_chat_expectation(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads((manifest.parent / "chat_event_expectation.json").read_text())
    payload[0]["evidence"] = []
    (manifest.parent / "chat_event_expectation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._real_chat_event_item(manifest)

    assert item.status == "missing"
    assert "at least 2 evidence items" in item.evidence


def test_completion_audit_rejects_real_chat_expectation_without_reviewed_text(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads((manifest.parent / "chat_event_expectation.json").read_text())
    del payload[0]["evidence"][0]["text"]
    (manifest.parent / "chat_event_expectation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._real_chat_event_item(manifest)

    assert item.status == "missing"
    assert "missing reviewed text" in item.evidence


def test_completion_audit_rejects_real_chat_expected_citation_without_evidence(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads((manifest.parent / "chat_event_expectation.json").read_text())
    payload[0]["expected_citations"] = ["E1", "E404"]
    (manifest.parent / "chat_event_expectation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._real_chat_event_item(manifest)

    assert item.status == "missing"
    assert "E404" in item.evidence


def test_completion_audit_rejects_real_chat_expectation_single_source(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads((manifest.parent / "chat_event_expectation.json").read_text())
    payload[0]["evidence"][1]["source"] = payload[0]["evidence"][0]["source"]
    (manifest.parent / "chat_event_expectation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._real_chat_event_item(manifest)

    assert item.status == "missing"
    assert "2 distinct evidence sources" in item.evidence


def test_completion_audit_rejects_real_chat_expectation_known_limits(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads((manifest.parent / "chat_event_expectation.json").read_text())
    payload[0]["known_limits"] = ["Review scaffold extracted from chat JSONL."]
    (manifest.parent / "chat_event_expectation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._real_chat_event_item(manifest)

    assert item.status == "missing"
    assert "unresolved known_limits" in item.evidence


def test_completion_audit_rejects_model_matrix_for_different_real_armory(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    other_armory = tmp_path / "other-armory"
    other_armory.mkdir()
    _retarget_model_matrix_armory(model_report, other_armory)

    report = audit_agent_harness_completion.audit_completion(
        real_manifest=manifest,
        real_preflight_report=preflight_report,
        model_matrix_report=model_report,
    )

    assert report.status == "incomplete"
    item = next(
        item
        for item in report.items
        if item.requirement == "Model-backed replay eval passes local and frontier groups"
    )
    assert item.status == "missing"
    assert "does not match real-corpus preflight armory" in item.evidence


def test_completion_audit_rejects_model_matrix_with_undeclared_replay_dataset(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    _retarget_model_matrix_armory(model_report, manifest.parent / "armory")

    report = audit_agent_harness_completion.audit_completion(
        real_manifest=manifest,
        real_preflight_report=preflight_report,
        model_matrix_report=model_report,
    )

    assert report.status == "incomplete"
    item = next(
        item
        for item in report.items
        if item.requirement == "Model-backed replay eval passes local and frontier groups"
    )
    assert item.status == "missing"
    assert "not declared by the real-corpus manifest" in item.evidence


def test_completion_audit_rejects_unreviewed_real_manifest_scaffold(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["known_limits"] = [
        "Generated scaffold: domains, stressors, and roles require human review."
    ]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_corpus_item(manifest)

    assert item.status == "missing"
    assert "Generated scaffold" in item.evidence


def test_completion_audit_rejects_real_manifest_without_document_provenance(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    del payload["documents"][0]["permission_note"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_corpus_item(manifest)

    assert item.status == "missing"
    assert "missing provenance" in item.evidence


def test_completion_audit_rejects_real_manifest_without_chat_event_dataset(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["datasets"] = [
        dataset for dataset in payload["datasets"] if dataset["kind"] != "chat-events"
    ]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_corpus_item(manifest)

    assert item.status == "missing"
    assert "chat-events" in item.evidence


def test_completion_audit_rejects_real_manifest_without_chat_expectation_dataset(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["datasets"] = [
        dataset
        for dataset in payload["datasets"]
        if dataset["kind"] != "chat-event-answer-expectation"
    ]
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_corpus_item(manifest)

    assert item.status == "missing"
    assert "chat-event-answer-expectation" in item.evidence


def test_completion_audit_rejects_missing_real_preflight_report(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)

    item = audit_agent_harness_completion._real_preflight_item(None, manifest)

    assert item.status == "missing"
    assert "--real-preflight-report" in item.evidence


def test_completion_audit_accepts_public_academic_corpus_requirements(tmp_path: Path) -> None:
    manifest = _write_public_academic_real_manifest(tmp_path)

    item = audit_agent_harness_completion._real_corpus_item(manifest)

    assert item.status == "covered"
    assert "documents=40" in item.evidence


def test_completion_audit_accepts_public_academic_preflight_roles(tmp_path: Path) -> None:
    manifest = _write_public_academic_real_manifest(tmp_path)
    preflight_report = tmp_path / "public-preflight-report.json"
    _write_public_academic_preflight_report(preflight_report, manifest)

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "covered"
    assert "indexed=40" in item.evidence


def test_completion_audit_rejects_public_academic_preflight_without_textbook(
    tmp_path: Path,
) -> None:
    manifest = _write_public_academic_real_manifest(tmp_path)
    preflight_report = tmp_path / "public-preflight-report.json"
    _write_public_academic_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["indexed_role_counts"] = {
        "lecture": 20,
        "reference": 20,
    }
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "textbook" in item.evidence


def test_completion_audit_rejects_failed_real_preflight_report(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["indexed_documents"] = 39
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "indexed 39 of 40" in item.evidence


def test_completion_audit_rejects_preflight_manifest_count_mismatch(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["manifest"]["documents"] = 45
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "do not match" in item.evidence


def test_completion_audit_rejects_preflight_without_required_roles(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["indexed_role_counts"] = {
        "assignment": 20,
        "past_exam": 20,
    }
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "slides" in item.evidence
    assert "indexed role" in item.evidence


def test_completion_audit_rejects_preflight_role_count_total_mismatch(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["role_counts"] = {
        "assignment": 1,
        "past_exam": 1,
        "slides": 1,
    }
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "cover 3 document" in item.evidence


def test_completion_audit_rejects_preflight_with_partial_extraction_health(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["extraction_health_pass_rate"] = 0.95
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "0.950" in item.evidence


def test_completion_audit_rejects_preflight_with_low_overview_source_coverage(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["overview_source_coverage_rate"] = 0.2
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "overview source coverage" in item.evidence


def test_completion_audit_accepts_preflight_overview_sample_cap_for_large_corpus(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["manifest"]["documents"] = 382
    payload["document_understanding"]["indexed_documents"] = 382
    payload["document_understanding"]["visible_materials"] = 382
    payload["document_understanding"]["overview_sampled_sources"] = 32
    payload["document_understanding"]["overview_total_sources"] = 382
    payload["document_understanding"]["overview_source_coverage_rate"] = 32 / 382
    payload["document_understanding"]["role_counts"] = {
        "assignment": 17,
        "past_exam": 62,
        "slides": 27,
        "reference": 276,
    }
    payload["document_understanding"]["indexed_role_counts"] = {
        "assignment": 17,
        "past_exam": 62,
        "slides": 27,
        "reference": 276,
    }
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "covered"
    assert "overview_sampled=32/382" in item.evidence


def test_completion_audit_rejects_preflight_with_mismatched_overview_total(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["overview_total_sources"] = 39
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "does not match indexed documents" in item.evidence


def test_completion_audit_rejects_preflight_with_inconsistent_overview_rate(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["document_understanding"]["overview_source_coverage_rate"] = 1.0
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "does not match sampled/total" in item.evidence


def test_completion_audit_rejects_preflight_for_different_manifest(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    other_manifest = tmp_path / "other" / "manifest.json"
    other_manifest.parent.mkdir()
    other_manifest.write_text("{}", encoding="utf-8")
    payload["manifest_path"] = str(other_manifest)
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "does not match" in item.evidence


def test_completion_audit_rejects_preflight_without_manifest_path(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    del payload["manifest_path"]
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "manifest_path" in item.evidence


def test_completion_audit_rejects_preflight_with_missing_manifest_path(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["manifest_path"] = str(tmp_path / "missing-manifest.json")
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "not a file" in item.evidence


def test_completion_audit_rejects_preflight_without_armory_path(tmp_path: Path) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    del payload["armory_path"]
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "armory_path" in item.evidence


def test_completion_audit_rejects_preflight_with_missing_armory_path(
    tmp_path: Path,
) -> None:
    manifest = _write_real_manifest(tmp_path)
    preflight_report = tmp_path / "preflight-report.json"
    _write_real_preflight_report(preflight_report, manifest)
    payload = json.loads(preflight_report.read_text(encoding="utf-8"))
    payload["armory_path"] = str(tmp_path / "missing-armory")
    preflight_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._real_preflight_item(preflight_report, manifest)

    assert item.status == "missing"
    assert "not a directory" in item.evidence


def test_completion_audit_rejects_model_report_without_metrics(tmp_path: Path) -> None:
    model_report = tmp_path / "model-report.json"
    model_report.write_text(
        json.dumps(
            {
                "status": 0,
                "armory": str(tmp_path / "armory"),
                "replay_dataset": str(tmp_path / "replay.jsonl"),
                "required_groups": ["frontier", "local"],
                "groups": ["frontier", "local"],
                "results": [
                    {"candidate_id": "local-small", "group": "local", "status": 0},
                    {
                        "candidate_id": "frontier-hosted",
                        "group": "frontier",
                        "provider_slug": "openai-codex",
                        "auth_source": "codex_oauth",
                        "status": 0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "metric pass_rate missing" in item.evidence


def test_completion_audit_rejects_model_report_without_candidate_report_path(
    tmp_path: Path,
) -> None:
    (tmp_path / "armory").mkdir()
    (tmp_path / "out").mkdir()
    _write_valid_replay_dataset(tmp_path / "replay.jsonl")
    model_report = tmp_path / "model-report.json"
    model_report.write_text(
        json.dumps(
            {
                "status": 0,
                "armory": str(tmp_path / "armory"),
                "replay_dataset": str(tmp_path / "replay.jsonl"),
                "output_dir": str(tmp_path / "out"),
                "required_groups": ["frontier", "local"],
                "groups": ["frontier", "local"],
                "replay_cases": 4,
                "replay_domains": ["biology", "cross-domain", "history", "mathematics"],
                "replay_tasks": [
                    "abstention",
                    "citation-check",
                    "grounded-explanation",
                    "material-overview",
                ],
                "results": [
                    {
                        "candidate_id": "local-small",
                        "group": "local",
                        "status": 0,
                        **_PASSING_MODEL_METRICS,
                    },
                    {
                        "candidate_id": "frontier-hosted",
                        "group": "frontier",
                        "model": "frontier-hosted",
                        "base_url": "",
                        "provider_slug": "openai-codex",
                        "auth_source": "codex_oauth",
                        "status": 0,
                        **_PASSING_MODEL_METRICS,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "report_path missing" in item.evidence


def test_completion_audit_requires_codex_oauth_frontier_candidate(tmp_path: Path) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    for result in payload["results"]:
        if result["group"] == "frontier":
            result["provider_slug"] = ""
            result["auth_source"] = "api_key"
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "Codex subscription-backed frontier" in item.evidence


def test_completion_audit_rejects_model_report_without_output_dir(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    del payload["output_dir"]
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "output_dir missing" in item.evidence


def test_completion_audit_rejects_model_report_with_missing_output_dir(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    shutil.rmtree(Path(payload["output_dir"]))

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "output_dir is not a directory" in item.evidence


def test_completion_audit_rejects_model_child_report_outside_output_dir(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    external_child = tmp_path / "external.report.json"
    external_child.write_text(local_child.read_text(encoding="utf-8"), encoding="utf-8")
    payload["results"][0]["report_path"] = str(external_child)
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "report_path outside" in item.evidence


def test_completion_audit_rejects_model_output_outside_output_dir(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["results"][0]["output"] = str(tmp_path / "external.answers.jsonl")
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "output path outside" in item.evidence


def test_completion_audit_rejects_model_child_report_metric_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["report"]["pass_rate"] = 0.5
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child report metric pass_rate 0.500" in item.evidence
    assert "does not match rescored answer fixture" in item.evidence


def test_completion_audit_rejects_model_child_report_when_rescored_fixture_fails(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    output = Path(child_payload["output"])
    lines = output.read_text(encoding="utf-8").splitlines()
    first_case = json.loads(lines[0])
    first_case["answer"] = "The answer is grounded in the source."
    lines[0] = json.dumps(first_case)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "rescored answer fixture metric" in item.evidence


def test_completion_audit_rejects_model_child_report_metadata_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["model"] = "different-model"
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "does not match matrix" in item.evidence


def test_completion_audit_rejects_model_child_report_dataset_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["replay_dataset"] = str(tmp_path / "other-replay.jsonl")
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "replay_dataset" in item.evidence
    assert "does not match matrix" in item.evidence


def test_completion_audit_rejects_model_report_with_missing_armory_path(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    shutil.rmtree(Path(payload["armory"]))

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "armory is not a directory" in item.evidence


def test_completion_audit_rejects_model_report_with_missing_replay_dataset(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    Path(payload["replay_dataset"]).unlink()

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "replay_dataset is not a file" in item.evidence


def test_completion_audit_rejects_model_report_with_empty_replay_dataset(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    Path(payload["replay_dataset"]).write_text("", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "invalid replay dataset" in item.evidence


def test_completion_audit_rejects_model_report_with_contractless_replay_dataset(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    Path(payload["replay_dataset"]).write_text(
        json.dumps({"id": "weak", "prompt": "Answer this."}) + "\n",
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "answer-contract" in item.evidence


def test_completion_audit_rejects_model_report_with_narrow_replay_domains(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    Path(payload["replay_dataset"]).write_text(
        "\n".join(
            json.dumps(
                {
                    "id": f"case-{idx}",
                    "domain": "mathematics",
                    "task": task,
                    "prompt": f"Prompt {idx}.",
                    "must_include": ["answer"],
                }
            )
            for idx, task in enumerate(("explain", "cite", "abstain"), start=1)
        )
        + "\n",
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "domain" in item.evidence


def test_completion_audit_rejects_model_report_with_narrow_replay_tasks(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    Path(payload["replay_dataset"]).write_text(
        "\n".join(
            json.dumps(
                {
                    "id": f"case-{idx}",
                    "domain": domain,
                    "task": "grounded-explanation",
                    "prompt": f"Prompt {idx}.",
                    "must_include": ["answer"],
                }
            )
            for idx, domain in enumerate(("mathematics", "biology", "history"), start=1)
        )
        + "\n",
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "task" in item.evidence


def test_completion_audit_rejects_model_report_without_material_overview_replay(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    replay_path = Path(payload["replay_dataset"])
    lines = [
        line
        for line in replay_path.read_text(encoding="utf-8").splitlines()
        if "material-overview" not in line
    ]
    replay_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "material-overview" in item.evidence


def test_completion_audit_rejects_model_child_output_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["results"][0]["output"] = str(Path(payload["output_dir"]) / "other.answers.jsonl")
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child output path does not match matrix output" in item.evidence


def test_completion_audit_rejects_model_child_report_without_answer_fixture(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    Path(child_payload["output"]).unlink()

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "answer fixture missing" in item.evidence


def test_completion_audit_rejects_model_child_report_with_empty_answer_fixture(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    Path(child_payload["output"]).write_text("", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "answer fixture is empty" in item.evidence


def test_completion_audit_rejects_model_child_report_with_invalid_answer_jsonl(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    Path(child_payload["output"]).write_text("not json\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "invalid answer benchmark dataset JSON" in item.evidence


def test_completion_audit_rejects_model_child_report_with_weakened_thresholds(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["thresholds"]["answer_pass_rate"] = 0.5
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child threshold answer_pass_rate 0.500" in item.evidence


def test_completion_audit_rejects_model_child_report_without_domain_breadth(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["report"]["domains"] = ["mathematics"]
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child report domains covers 1" in item.evidence


def test_completion_audit_rejects_model_child_report_case_count_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["report"]["cases"] = 2
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "report scored 2" in item.evidence


def test_completion_audit_rejects_model_matrix_case_count_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["results"][0]["cases"] = 2
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "matrix scored 2" in item.evidence


def test_completion_audit_rejects_model_matrix_replay_summary_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["replay_cases"] = 2
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "replay_cases 2" in item.evidence


def test_completion_audit_rejects_model_matrix_without_domain_breadth(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["results"][0]["domains"] = ["mathematics"]
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "matrix domains covers 1" in item.evidence


def test_completion_audit_rejects_model_matrix_domain_set_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["results"][0]["domains"] = ["astronomy", "biology", "mathematics"]
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "matrix domains do not match" in item.evidence


def test_completion_audit_rejects_model_child_fixture_case_count_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    output = Path(child_payload["output"])
    first_case = output.read_text(encoding="utf-8").splitlines()[0]
    output.write_text(first_case + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "answer fixture has 1 case" in item.evidence


def test_completion_audit_rejects_model_child_fixture_case_id_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    output = Path(child_payload["output"])
    lines = output.read_text(encoding="utf-8").splitlines()
    last_case = json.loads(lines[-1])
    last_case["id"] = "unrelated-case"
    lines[-1] = json.dumps(last_case)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "case ids do not match" in item.evidence
    assert "case-4" in item.evidence


def test_completion_audit_rejects_model_child_fixture_without_task_breadth(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    output = Path(child_payload["output"])
    lines = []
    for line in output.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        case["task"] = "grounded-explanation"
        lines.append(json.dumps(case))
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child answer fixture tasks covers 1" in item.evidence


def test_completion_audit_rejects_model_child_report_task_set_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    child_payload["report"]["tasks"] = ["abstention", "citation-check", "summarization"]
    local_child.write_text(json.dumps(child_payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child report tasks do not match" in item.evidence


def test_completion_audit_rejects_model_child_fixture_domain_set_mismatch(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    local_child = Path(payload["results"][0]["report_path"])
    child_payload = json.loads(local_child.read_text(encoding="utf-8"))
    output = Path(child_payload["output"])
    lines = []
    for line in output.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        if case["id"] == "case-3":
            case["domain"] = "astronomy"
        lines.append(json.dumps(case))
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "child answer fixture domains do not match" in item.evidence


def test_completion_audit_rejects_model_report_with_weakened_required_groups(
    tmp_path: Path,
) -> None:
    model_report = tmp_path / "model-report.json"
    _write_model_matrix_report(model_report)
    payload = json.loads(model_report.read_text(encoding="utf-8"))
    payload["required_groups"] = ["frontier"]
    model_report.write_text(json.dumps(payload), encoding="utf-8")

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "required_groups" in item.evidence


def test_completion_audit_requires_passing_candidate_per_model_group(tmp_path: Path) -> None:
    model_report = tmp_path / "model-report.json"
    child_report = tmp_path / "frontier-hosted.report.json"
    _write_candidate_replay_report(child_report)
    model_report.write_text(
        json.dumps(
            {
                "status": 0,
                "armory": str(tmp_path / "armory"),
                "replay_dataset": str(tmp_path / "replay.jsonl"),
                "required_groups": ["frontier", "local"],
                "groups": ["frontier", "local"],
                "results": [
                    {
                        "candidate_id": "frontier-hosted",
                        "group": "frontier",
                        "status": 0,
                        "report_path": str(child_report),
                        **_PASSING_MODEL_METRICS,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    item = audit_agent_harness_completion._model_matrix_item(model_report)

    assert item.status == "missing"
    assert "local" in item.evidence


def test_completion_audit_cli_writes_json_report(tmp_path: Path) -> None:
    report_path = tmp_path / "audit.json"

    status = audit_agent_harness_completion.main(["--json-report", str(report_path)])

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 1
    assert payload["status"] == "incomplete"
    assert any("discover_real_corpus_candidates" in step for step in payload["next_steps"])
    assert any("prepare_real_corpus_evidence" in step for step in payload["next_steps"])
    assert any("benchmark_chat_events" in step for step in payload["next_steps"])
    assert any("run_model_eval_matrix" in step for step in payload["next_steps"])
    assert "discover_real_corpus_candidates" in payload["next_steps"][0]
    assert "audit_agent_harness_completion" in payload["next_steps"][-1]


@requires_private_default_suite
def test_completion_audit_cli_uses_explicit_private_suite(
    tmp_path: Path,
) -> None:
    suite = tmp_path / "private-suite"
    report_path = tmp_path / "audit.json"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)

    status = audit_agent_harness_completion.main(
        ["--suite", str(suite), "--json-report", str(report_path)]
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    manifest_item = next(
        item
        for item in payload["items"]
        if item["requirement"] == "Private deterministic benchmark suite manifest"
    )
    benchmark_item = next(
        item
        for item in payload["items"]
        if item["requirement"] == "Deterministic academic benchmark suite passes"
    )
    chat_item = next(
        item
        for item in payload["items"]
        if item["requirement"] == "Deterministic suite verifies public chat JSONL harness events"
    )
    assert status == 1
    assert manifest_item["status"] == "covered"
    assert manifest_item["evidence"] == str(suite / "manifest.json")
    assert benchmark_item["status"] == "covered"
    assert str(suite) in benchmark_item["evidence"]
    assert chat_item["status"] == "covered"
    assert str(suite / "chat_events.jsonl") in chat_item["evidence"]
