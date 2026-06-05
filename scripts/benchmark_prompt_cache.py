"""Verify prompt-cache-aware request construction."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import cast

from ai.runtime._api_types import ApiMessage
from ai.runtime.prompt_cache import PromptCacheRequest, StablePrefixBuilder


@dataclass(frozen=True, slots=True)
class PromptCacheCaseResult:
    case_id: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class PromptCacheBenchmarkReport:
    cases: int
    pass_rate: float
    stable_hash_reuse_rate: float
    prefix_invalidation_rate: float
    dynamic_tail_preservation_rate: float
    request_order_preservation_rate: float
    evidence_stable_prefix_rate: float
    failures: tuple[str, ...]
    results: tuple[PromptCacheCaseResult, ...]


def run_benchmark() -> PromptCacheBenchmarkReport:
    """Run deterministic prompt-cache construction checks."""
    checks = (
        _check_stable_hash_reuse(),
        _check_prefix_invalidation(),
        _check_dynamic_tail_preservation(),
        _check_request_order_preservation(),
        _check_evidence_in_stable_prefix(),
    )
    failures = tuple(result.detail for result in checks if not result.passed)
    passed_cases = sum(1 for result in checks if result.passed)
    return PromptCacheBenchmarkReport(
        cases=len(checks),
        pass_rate=passed_cases / len(checks),
        stable_hash_reuse_rate=_rate(checks, "stable-hash-reuse"),
        prefix_invalidation_rate=_rate(checks, "prefix-invalidation"),
        dynamic_tail_preservation_rate=_rate(checks, "dynamic-tail-preservation"),
        request_order_preservation_rate=_rate(checks, "request-order-preservation"),
        evidence_stable_prefix_rate=_rate(checks, "evidence-stable-prefix"),
        failures=failures,
        results=checks,
    )


def print_text_report(report: PromptCacheBenchmarkReport) -> None:
    """Print a compact prompt-cache report."""
    print(f"Prompt cache benchmark: {report.cases} case(s)")
    print(f"pass_rate={report.pass_rate * 100:.1f}%")
    print(f"stable_hash_reuse={report.stable_hash_reuse_rate * 100:.1f}%")
    print(f"prefix_invalidation={report.prefix_invalidation_rate * 100:.1f}%")
    print(f"dynamic_tail_preservation={report.dynamic_tail_preservation_rate * 100:.1f}%")
    print(f"request_order_preservation={report.request_order_preservation_rate * 100:.1f}%")
    print(f"evidence_stable_prefix={report.evidence_stable_prefix_rate * 100:.1f}%")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _check_stable_hash_reuse() -> PromptCacheCaseResult:
    first = _request(
        [
            {"role": "system", "content": "Stable persona."},
            {"role": "system", "content": "Stable source-grounding rules."},
            {"role": "user", "content": "Explain integration by parts."},
        ]
    )
    second = _request(
        [
            {"role": "system", "content": "Stable persona."},
            {"role": "system", "content": "Stable source-grounding rules."},
            {"role": "user", "content": "Explain Dijkstra."},
            {"role": "assistant", "content": "Dijkstra uses a priority queue [E1]."},
        ]
    )
    passed = (
        first.stable_prefix.fingerprint == second.stable_prefix.fingerprint
        and first.dynamic_tail.fingerprint != second.dynamic_tail.fingerprint
    )
    return PromptCacheCaseResult(
        case_id="stable-hash-reuse",
        passed=passed,
        detail="stable prefix hash changed across dynamic-tail-only edits",
    )


def _check_prefix_invalidation() -> PromptCacheCaseResult:
    first = _request(
        [
            {"role": "system", "content": "Stable persona."},
            {"role": "user", "content": "Explain integration by parts."},
        ]
    )
    second = _request(
        [
            {"role": "system", "content": "Changed persona."},
            {"role": "user", "content": "Explain integration by parts."},
        ]
    )
    passed = first.stable_prefix.fingerprint != second.stable_prefix.fingerprint
    return PromptCacheCaseResult(
        case_id="prefix-invalidation",
        passed=passed,
        detail="stable prefix hash did not change after stable instruction edit",
    )


def _check_dynamic_tail_preservation() -> PromptCacheCaseResult:
    request = _request(
        [
            {"role": "system", "content": "Stable persona."},
            {"role": "user", "content": "First question."},
            {"role": "system", "content": "[Conversation summary] Earlier thread."},
            {"role": "tool", "content": "Observed source text."},
            {"role": "assistant", "content": "Grounded answer [E1]."},
        ]
    )
    dynamic_roles = tuple(message["role"] for message in request.dynamic_tail.messages)
    passed = request.stable_prefix.message_count == 1 and dynamic_roles == (
        "user",
        "system",
        "tool",
        "assistant",
    )
    return PromptCacheCaseResult(
        case_id="dynamic-tail-preservation",
        passed=passed,
        detail="dynamic tail did not preserve user, summary, tool, and assistant messages",
    )


def _check_request_order_preservation() -> PromptCacheCaseResult:
    messages: list[ApiMessage] = [
        {"role": "system", "content": "Stable persona."},
        {"role": "user", "content": "First question."},
        {"role": "assistant", "content": "First answer."},
        {"role": "user", "content": "Second question."},
    ]
    request = _request(messages)
    passed = request.messages == messages
    return PromptCacheCaseResult(
        case_id="request-order-preservation",
        passed=passed,
        detail="prompt-cache split changed model request message order",
    )


def _check_evidence_in_stable_prefix() -> PromptCacheCaseResult:
    request = _request(
        [
            {"role": "system", "content": "Stable persona."},
            {"role": "system", "content": "Stable source-grounding rules."},
            {
                "role": "system",
                "content": "Retrieved evidence for this question:\n\n[E1] notes.md (chunk 0)",
            },
            {"role": "user", "content": "Explain the evidence."},
        ]
    )
    passed = (
        request.stable_prefix.message_count == 3
        and request.dynamic_tail.message_count == 1
        and str(request.stable_prefix.messages[-1]["content"]).startswith(
            "Retrieved evidence for this question:"
        )
    )
    return PromptCacheCaseResult(
        case_id="evidence-stable-prefix",
        passed=passed,
        detail="evidence system message was not included in the stable prefix",
    )


def _request(messages: list[ApiMessage]) -> PromptCacheRequest:
    return StablePrefixBuilder().build_request(messages)


def _rate(results: tuple[PromptCacheCaseResult, ...], case_id: str) -> float:
    matching = [result for result in results if result.case_id == case_id]
    if not matching:
        return 0.0
    return 1.0 if matching[0].passed else 0.0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = run_benchmark()
    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
