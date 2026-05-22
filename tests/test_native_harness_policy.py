from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts import check_repo_policies, claim_report_envelope


def _minimal_claim_report(*, warnings: list[str] | None = None) -> dict[str, object]:
    hashes = {
        "cases_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "qrels_sha256": "c" * 64,
        "corpus_sha256": "d" * 64,
    }
    return {
        "schema_version": "external-runner-report-v1",
        "report_id": "policy-fixture",
        "status": "success",
        "metadata": {
            "runner": "scripts.run_external_benchmarks",
            "benchmark_type": "beir",
            "dataset": "beir/fixture",
            "fixed_parameters": {
                "top_k": 1,
                "candidate_multiplier": 1,
                "network_access": "disabled-after-materialization",
            },
            "metric_formulas": {
                "hit_rate": "fraction of queries with support in top-k",
                "mrr": "mean reciprocal rank",
                "expected_recall": "mean expected reference recall",
            },
            "model": "retrieval-only:no-generation",
            **hashes,
        },
        "benchmarks": [
            {
                "id": "policy-fixture",
                "benchmark_type": "beir",
                "dataset": "beir/fixture",
                "status": "success",
                "metrics": {
                    "hit_rate": 1.0,
                    "mrr": 1.0,
                    "expected_recall": 1.0,
                    "query_count": 1,
                },
                "per_query_results": [
                    {
                        "case_id": "opaque-1",
                        "hit": True,
                        "rank": 1,
                        "expected_recall": 1.0,
                    }
                ],
            }
        ],
        "aggregate_metrics": {
            "hit_rate": 1.0,
            "mrr": 1.0,
            "expected_recall": 1.0,
            "query_count": 1,
            "latency": {
                "scope": "retrieval_only_per_query",
                "unit": "milliseconds",
                "mean_ms": 1.0,
            },
        },
        "thresholds": {},
        "threshold_failures": [],
        "warnings": warnings or [],
        "errors": [],
        "reproducibility": {
            "enabled": True,
            "status": "passed",
            "deterministic_fields_compared": ["metadata.dataset", "aggregate_metrics.hit_rate"],
            "runtime_only_fields": [],
            "mismatches": [],
        },
    }


def test_claim_policy_rejects_qrels_or_expected_answer_leakage() -> None:
    report = _minimal_claim_report()
    benchmarks = cast("list[dict[str, object]]", report["benchmarks"])
    benchmark = benchmarks[0]
    benchmark["expected_topics"] = ["hidden private topic"]
    benchmark["forbidden_topics"] = ["private distractor"]
    per_query = benchmark["per_query_results"]
    assert isinstance(per_query, list)
    first_result = per_query[0]
    assert isinstance(first_result, dict)
    first_result = cast("dict[str, object]", first_result)
    first_result["expected"] = ["materials/hidden-answer.md"]
    first_result["expected_text"] = "hidden answer text"

    finalized = claim_report_envelope.finalize_claim_report(
        report,
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )

    envelope = cast("dict[str, object]", finalized["claim_envelope"])
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    leakage = cast("dict[str, object]", claim_policy["leakage"])
    findings = cast("list[dict[str, object]]", leakage["findings"])
    reasons = cast("list[str]", envelope["ineligibility_reasons"])
    assert envelope["claim_eligible"] is False
    assert "claim leakage scan failed" in reasons
    assert leakage["status"] == "failed"
    finding_keys = {finding["key"] for finding in findings}
    assert {"expected", "expected_text", "expected_topics", "forbidden_topics"} <= finding_keys


def test_claim_policy_redacts_seeded_secrets_before_report_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAISTOS_TEST_POLICY_TOKEN", "policy-secret-value")

    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(warnings=["diagnostic token policy-secret-value must redact"]),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    serialized = json.dumps(finalized, ensure_ascii=False, sort_keys=True)
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    redaction = cast("dict[str, object]", claim_policy["redaction"])

    assert "policy-secret-value" not in serialized
    assert "[REDACTED]" in serialized
    assert redaction["status"] == "passed"


def test_claim_policy_validator_rejects_failed_redaction_status() -> None:
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    claim_policy = cast("dict[str, object]", finalized["claim_policy"])
    redaction = cast("dict[str, object]", claim_policy["redaction"])
    redaction["status"] = "failed"

    validation = claim_report_envelope.validate_claim_report_envelope(
        finalized,
        require_claim_eligible=False,
    )

    assert "claim redaction policy failed" in validation.errors


def test_claim_policy_rejects_fixture_private_terms() -> None:
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(warnings=["fixture_private_course appeared in runtime output"]),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )

    envelope = cast("dict[str, object]", finalized["claim_envelope"])
    reasons = cast("list[str]", envelope["ineligibility_reasons"])
    assert envelope["claim_eligible"] is False
    assert "claim leakage scan failed" in reasons


def test_native_harness_policy_file_stays_outside_generated_artifacts(tmp_path: Path) -> None:
    report_path = tmp_path / "policy.json"
    finalized = claim_report_envelope.finalize_claim_report(
        _minimal_claim_report(),
        command="uv run python -m scripts.run_external_benchmarks beir beir/fixture",
    )
    report_path.write_text(json.dumps(finalized, sort_keys=True) + "\n", encoding="utf-8")

    assert report_path.is_file()
    assert ".artifacts" not in report_path.parts


def test_repo_policy_rejects_product_runtime_imports_from_benchmark_only_code() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "import scripts.run_external_benchmarks",
                "from benchmarks.academic import fixture",
            )
        ),
        "hephaistos/chat/runtime_boundary_fixture.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "benchmark-only module `scripts.run_external_benchmarks`" in rendered
    assert "benchmark-only module `benchmarks.academic`" in rendered


def test_repo_policy_rejects_allowlisted_runtime_dynamic_benchmark_imports() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "import importlib",
                'importlib.import_module("scripts.run_external_benchmarks")',
                'importlib.import_module("benchmarks.academic.fixture")',
            )
        ),
        "hephaistos/cli/main.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "benchmark-only module `scripts.run_external_benchmarks`" in rendered
    assert "benchmark-only module `benchmarks.academic.fixture`" in rendered


def test_repo_policy_rejects_imported_runtime_dynamic_benchmark_imports() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "from importlib import import_module",
                'import_module("scripts.run_external_benchmarks")',
                'import_module("benchmarks.academic.fixture")',
            )
        ),
        "hephaistos/cli/main.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "benchmark-only module `scripts.run_external_benchmarks`" in rendered
    assert "benchmark-only module `benchmarks.academic.fixture`" in rendered


def test_repo_policy_rejects_aliased_runtime_dynamic_benchmark_imports() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "import importlib as il",
                'il.import_module("scripts.run_external_benchmarks")',
                'il.import_module("benchmarks.academic.fixture")',
            )
        ),
        "hephaistos/cli/main.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "benchmark-only module `scripts.run_external_benchmarks`" in rendered
    assert "benchmark-only module `benchmarks.academic.fixture`" in rendered


def test_repo_policy_allows_allowlisted_runtime_dynamic_product_imports() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "import importlib",
                'importlib.import_module("hephaistos.commands")',
            )
        ),
        "hephaistos/cli/main.py",
    )

    assert violations == []


def test_repo_policy_rejects_literal_reply_assignment_without_reply_function_name() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "def route() -> str:",
                '    direct_reply = "Before I answer from sources, I need one clarification."',
                "    return direct_reply",
            )
        ),
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_rejects_literal_reply_attribute_assignment() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "def route(plan: object) -> None:",
                '    plan.reply = "If you want, I can give you a study plan next."',
            )
        ),
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_rejects_literal_response_subscript_assignment() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "def route(payload: dict[str, str]) -> None:",
                '    payload["response"] = "Tell the user to choose one option from the menu."',
            )
        ),
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_allows_allowlisted_aliased_runtime_dynamic_product_imports() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                "from importlib import import_module as load_module",
                "import importlib as il",
                'load_module("hephaistos.commands")',
                'il.import_module("hephaistos.commands")',
            )
        ),
        "hephaistos/cli/main.py",
    )

    assert violations == []


def test_repo_policy_rejects_product_runtime_references_to_generated_artifacts() -> None:
    violations = check_repo_policies._check_source(
        "\n".join(
            (
                "from __future__ import annotations",
                'REPORT_PATH = ".artifacts/benchmarks/report.json"',
                'FIXTURE_PATH = "benchmarks/academic/rag.jsonl"',
            )
        ),
        "hephaistos/rag/runtime_boundary_fixture.py",
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert rendered.count("generated benchmark artifact paths") == 2


def test_repo_policy_rejects_duplicate_model_facing_prompt_rules() -> None:
    first = check_repo_policies.PromptRuleLiteral(
        text="- answer in the same language as the user's request when clear.",
        path="hephaistos/study/controller.py",
        line=10,
        column=5,
    )
    duplicate = check_repo_policies.PromptRuleLiteral(
        text="- answer in the same language as the user's request when clear.",
        path="hephaistos/chat/orchestrator.py",
        line=20,
        column=9,
    )

    violations = check_repo_policies._duplicate_prompt_rule_violations([first, duplicate])
    rendered = "\n".join(violation.render() for violation in violations)

    assert "duplicate model-facing prompt rule" in rendered
    assert "first seen at hephaistos/study/controller.py:10" in rendered


def test_repo_policy_rejects_hardcoded_chat_answers() -> None:
    violations = check_repo_policies._hardcoded_answer_violations(
        [
            check_repo_policies.HardcodedAnswerLiteral(
                text="Hey. I can help with your documents.",
                path="hephaistos/study/controller.py",
                line=12,
                column=8,
            )
        ]
    )

    rendered = "\n".join(violation.render() for violation in violations)

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_rejects_literal_returns_from_reply_functions() -> None:
    source = """
def _clarifying_question_reply(missing: str) -> str:
    return "Before I answer from sources, I need one clarification."
"""

    violations = check_repo_policies._hardcoded_answer_literals(
        source,
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(
        violation.render()
        for violation in check_repo_policies._hardcoded_answer_violations(violations)
    )

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_rejects_literal_returns_from_answerish_helpers() -> None:
    source = """
def _clarifying_question(missing: str) -> str:
    return "Before I answer from sources, I need one clarification."

def _product_answer() -> str:
    return "Heph can help with local documents."
"""

    violations = check_repo_policies._hardcoded_answer_literals(
        source,
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(
        violation.render()
        for violation in check_repo_policies._hardcoded_answer_violations(violations)
    )

    assert rendered.count("hardcoded assistant answer") == 2


def test_repo_policy_rejects_composed_literal_returns_from_answerish_helpers() -> None:
    source = """
def _product_answer() -> str:
    return "Heph can " + "help with local documents."

def _source_response() -> str:
    return "\\n".join(["I found this in your material.", "Here is the answer."])
"""

    violations = check_repo_policies._hardcoded_answer_literals(
        source,
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(
        violation.render()
        for violation in check_repo_policies._hardcoded_answer_violations(violations)
    )

    assert rendered.count("hardcoded assistant answer") == 2


def test_repo_policy_rejects_harness_like_prefixes_outside_allowlisted_helpers() -> None:
    source = """
def _product_answer() -> str:
    return "I could not generate a response. Please try again."
"""

    violations = check_repo_policies._hardcoded_answer_literals(
        source,
        "hephaistos/chat/orchestrator.py",
    )
    rendered = "\n".join(
        violation.render()
        for violation in check_repo_policies._hardcoded_answer_violations(violations)
    )

    assert "hardcoded assistant answer" in rendered


def test_repo_policy_allows_harness_fallback_answers_in_allowlisted_helpers() -> None:
    source = """
def _plain_empty_reply(user_input: str, config: object) -> str:
    return "I could not generate a response. Please try again."
"""

    violations = check_repo_policies._hardcoded_answer_literals(
        source,
        "hephaistos/chat/orchestrator.py",
    )

    assert violations == []


def test_repo_policy_rejects_tracked_generated_python_caches() -> None:
    violations = check_repo_policies._check_generated_caches(
        ("hephaistos/__pycache__/removed_module.cpython-313.pyc",)
    )
    rendered = "\n".join(violation.render() for violation in violations)

    assert "generated Python cache files" in rendered
    assert "removed_module.cpython-313.pyc" in rendered


def test_current_product_runtime_has_no_benchmark_only_import_or_artifact_coupling() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    product_root = repo_root / "hephaistos"
    violations: list[str] = []
    for path in sorted(product_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        violations.extend(
            violation.render()
            for violation in check_repo_policies._check_file(path)
            if "benchmark" in violation.message
        )

    assert violations == []
