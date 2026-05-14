"""Verify non-interactive chat JSONL event streams.

This script is intended for output produced by:

    heph chat ask --jsonl <armory> "what is the material about"

It checks that the live CLI stream exposes the harness stages students and
benchmarks need to audit: reading, evidence, writing, assistant output, and
turn completion. It can also score the completed answer by merging the final
``turn_complete.full_text`` into a normal ``scripts.benchmark_answers`` case.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from scripts import benchmark_answers


class RawEvent(TypedDict):
    type: str
    code: NotRequired[str]
    operation: NotRequired[str]
    message: NotRequired[str]
    delta: NotRequired[str]
    full_text: NotRequired[str]
    metadata: NotRequired[dict[str, object]]


@dataclass(frozen=True, slots=True)
class ChatEventBenchmarkReport:
    event_count: int
    notice_codes: tuple[str, ...]
    has_reading: bool
    has_evidence: bool
    has_writing: bool
    has_material_operation: bool
    has_material_operation_metadata: bool
    has_tool_runtime: bool
    has_tool_runtime_metadata: bool
    has_acceptance_criteria: bool
    has_acceptance_criteria_metadata: bool
    has_assistant_delta: bool
    has_turn_complete: bool
    has_consistent_completion: bool
    has_evidence_metadata: bool
    material_operation_count: int
    evidence_metadata_rate: float
    material_operation_metadata_rate: float
    tool_runtime_metadata_rate: float
    acceptance_criteria_metadata_rate: float
    answer_excerpt: str
    answer_pass_rate: float | None
    answer_shape_rate: float | None
    failures: tuple[str, ...]


def load_events(path: Path) -> list[RawEvent]:
    """Load JSONL chat events from ``heph chat ask --jsonl`` output."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"could not read chat event JSONL: {path}") from exc

    events: list[RawEvent] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            payload: object = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid event JSON at line {line_number}: {path}") from exc
        if not isinstance(payload, dict):
            raise TypeError(f"event line {line_number} must be a JSON object")
        event_type = payload.get("type")
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError(f"event line {line_number} must include string 'type'")
        event: RawEvent = {"type": event_type.strip()}
        code = payload.get("code")
        if isinstance(code, str) and code.strip():
            event["code"] = code.strip()
        operation = payload.get("operation")
        if isinstance(operation, str) and operation.strip():
            event["operation"] = operation.strip()
        message = payload.get("message")
        if isinstance(message, str):
            event["message"] = message
        delta = payload.get("delta")
        if isinstance(delta, str):
            event["delta"] = delta
        full_text = payload.get("full_text")
        if isinstance(full_text, str):
            event["full_text"] = full_text
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            event["metadata"] = cast("dict[str, object]", metadata)
        events.append(event)
    if not events:
        raise ValueError("chat event JSONL does not contain any events")
    return events


def load_expectation(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    try:
        payload: object
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".jsonl":
            payload = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not reload answer expectation: {path}") from exc
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list) or len(raw_cases) != 1:
        raise ValueError("chat event answer expectation must contain exactly one case")
    if not isinstance(raw_cases[0], dict):
        raise TypeError("chat event answer expectation must contain one case object")
    return cast("Mapping[str, object]", raw_cases[0])


def _final_answer(events: Sequence[RawEvent]) -> str:
    completed = [
        event.get("full_text", "")
        for event in events
        if event["type"] == "turn_complete" and event.get("full_text")
    ]
    if completed:
        return completed[-1]
    return "".join(
        event.get("delta", "") for event in events if event["type"] == "assistant_delta"
    )


def _answer_case_from_events(
    events: Sequence[RawEvent],
    expectation: Mapping[str, object],
) -> benchmark_answers.AnswerCase | None:
    answer = _final_answer(events).strip()
    if not answer:
        return None
    raw_case = dict(expectation)
    raw_case["answer"] = answer
    raw_case.setdefault("id", "chat-event-answer")
    raw_case.setdefault("query", "chat ask --jsonl")
    raw_case.setdefault("task", "chat-event")
    raw_case.setdefault("require_citations", "evidence" in raw_case)
    return benchmark_answers.load_cases_from_payload([raw_case])[0]


def _notice_codes(events: Sequence[RawEvent]) -> tuple[str, ...]:
    return tuple(
        event["code"]
        for event in events
        if event["type"] == "notice" and isinstance(event.get("code"), str)
    )


def run_chat_event_benchmark(
    events: Sequence[RawEvent],
    *,
    expectation: Mapping[str, object] | None = None,
) -> ChatEventBenchmarkReport:
    """Verify stage events and optionally score the completed answer."""
    expectation = expectation or {}
    notice_codes = _notice_codes(events)
    failures: list[str] = []
    has_reading = "reading" in notice_codes
    has_evidence = "evidence" in notice_codes
    has_writing = "writing" in notice_codes
    material_operation_failures = list(_material_operation_failures(events))
    material_operation_failures.extend(_expected_material_operation_failures(events, expectation))
    material_operations = [event for event in events if event["type"] == "material_operation"]
    has_material_operation = bool(material_operations)
    has_material_operation_metadata = bool(material_operations) and not material_operation_failures
    has_tool_runtime = "tool_runtime" in notice_codes
    has_acceptance_criteria = "acceptance_criteria" in notice_codes
    has_assistant_delta = any(event["type"] == "assistant_delta" for event in events)
    has_turn_complete = any(event["type"] == "turn_complete" for event in events)
    metadata_failures = _evidence_metadata_failures(events, expectation)
    has_evidence_metadata = not metadata_failures
    tool_runtime_failures = _tool_runtime_metadata_failures(events)
    has_tool_runtime_metadata = not tool_runtime_failures
    acceptance_criteria_failures = _acceptance_criteria_metadata_failures(events)
    has_acceptance_criteria_metadata = not acceptance_criteria_failures
    evidence_metadata_rate = 1.0 if has_evidence_metadata else 0.0
    tool_runtime_metadata_rate = 1.0 if has_tool_runtime_metadata else 0.0
    acceptance_criteria_metadata_rate = 1.0 if has_acceptance_criteria_metadata else 0.0
    material_operation_metadata_rate = 1.0 if has_material_operation_metadata else 0.0
    assistant_text = _assistant_text(events).strip()
    final_answer = _final_answer(events).strip()
    has_consistent_completion = not (assistant_text and final_answer) or (
        assistant_text == final_answer
    )
    readability_failures = _student_readability_failures(final_answer)
    if not has_reading:
        failures.append("missing reading notice")
    if not has_evidence:
        failures.append("missing evidence notice")
    if not has_writing:
        failures.append("missing writing notice")
    if not has_material_operation:
        failures.append("missing material operation event")
    if not has_assistant_delta:
        failures.append("missing assistant delta")
    if not has_turn_complete:
        failures.append("missing turn completion")
    if not has_consistent_completion:
        failures.append("assistant delta text does not match turn completion text")
    failures.extend(metadata_failures)
    failures.extend(material_operation_failures)
    failures.extend(tool_runtime_failures)
    failures.extend(acceptance_criteria_failures)
    failures.extend(readability_failures)

    known_limit_failures = _expectation_known_limit_failures(expectation)
    failures.extend(known_limit_failures)

    answer_case = _answer_case_from_events(events, expectation)
    answer_pass_rate: float | None = None
    answer_shape_rate: float | None = None
    if answer_case is None:
        failures.append("missing completed answer text")
        answer_excerpt = ""
    else:
        answer_excerpt = _excerpt(answer_case.answer)
        answer_report = benchmark_answers.run_benchmark([answer_case])
        answer_pass_rate = answer_report.pass_rate
        answer_shape_rate = answer_report.answer_shape_rate
        failures.extend(
            f"answer benchmark failed: {failure}" for failure in answer_report.failures
        )

    return ChatEventBenchmarkReport(
        event_count=len(events),
        notice_codes=notice_codes,
        has_reading=has_reading,
        has_evidence=has_evidence,
        has_writing=has_writing,
        has_material_operation=has_material_operation,
        has_material_operation_metadata=has_material_operation_metadata,
        has_tool_runtime=has_tool_runtime,
        has_tool_runtime_metadata=has_tool_runtime_metadata,
        has_acceptance_criteria=has_acceptance_criteria,
        has_acceptance_criteria_metadata=has_acceptance_criteria_metadata,
        has_assistant_delta=has_assistant_delta,
        has_turn_complete=has_turn_complete,
        has_consistent_completion=has_consistent_completion,
        has_evidence_metadata=has_evidence_metadata,
        material_operation_count=len(material_operations),
        evidence_metadata_rate=evidence_metadata_rate,
        material_operation_metadata_rate=material_operation_metadata_rate,
        tool_runtime_metadata_rate=tool_runtime_metadata_rate,
        acceptance_criteria_metadata_rate=acceptance_criteria_metadata_rate,
        answer_excerpt=answer_excerpt,
        answer_pass_rate=answer_pass_rate,
        answer_shape_rate=answer_shape_rate,
        failures=tuple(failures),
    )


def _excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _assistant_text(events: Sequence[RawEvent]) -> str:
    return "".join(
        event.get("delta", "") for event in events if event["type"] == "assistant_delta"
    )


def _student_readability_failures(answer: str) -> tuple[str, ...]:
    normalized = answer.casefold()
    forbidden_fragments = (
        ("visible reply includes raw sources footer", "_sources:"),
        ("visible reply includes retrieval score diagnostics", "score "),
        ("visible reply includes source open command diagnostics", "open: /evidence"),
        ("visible reply includes per-source expand command diagnostics", "expand: /evidence e"),
        (
            "visible reply includes no-citation warning despite completed answer",
            "no evidence citations",
        ),
        (
            "visible reply uses benchmark wording instead of student-facing prose",
            "retrieved overview sample",
        ),
        ("visible reply uses benchmark scope disclaimer", "not an exhaustive summary"),
    )
    failures = [message for message, fragment in forbidden_fragments if fragment in normalized]
    long_lines = [
        line
        for line in answer.splitlines()
        if len(line) > 240 and not line.strip().startswith("{")
    ]
    if long_lines:
        failures.append("visible reply contains overly long unreadable line(s)")
    return tuple(failures)


def _evidence_metadata_failures(
    events: Sequence[RawEvent],
    expectation: Mapping[str, object],
) -> tuple[str, ...]:
    evidence_notices = [
        event for event in events if event["type"] == "notice" and event.get("code") == "evidence"
    ]
    if not evidence_notices:
        return ()
    metadata = evidence_notices[-1].get("metadata")
    if not isinstance(metadata, dict):
        return ("evidence notice missing metadata",)
    items = metadata.get("items")
    refs = metadata.get("refs")
    coverage = metadata.get("coverage")
    failures: list[str] = []
    if not isinstance(items, list) or not items:
        failures.append("evidence metadata missing items")
    if not isinstance(refs, list) or not refs:
        failures.append("evidence metadata missing refs")
    if not isinstance(coverage, dict):
        failures.append("evidence metadata missing coverage")
        coverage = {}
    if failures:
        return tuple(failures)
    assert isinstance(items, list)
    assert isinstance(refs, list)
    assert isinstance(coverage, dict)
    metadata_ids: set[str] = set()
    metadata_refs: set[str] = set()
    for index, raw_item in enumerate(items, start=1):
        if not isinstance(raw_item, dict):
            failures.append(f"evidence metadata item {index} must be an object")
            continue
        evidence_id = raw_item.get("evidence_id")
        ref = raw_item.get("ref")
        text_excerpt = raw_item.get("text_excerpt")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            failures.append(f"evidence metadata item {index} missing evidence_id")
        else:
            metadata_ids.add(evidence_id.strip().upper())
        if not isinstance(ref, str) or not ref.strip():
            failures.append(f"evidence metadata item {index} missing ref")
        else:
            metadata_refs.add(ref.strip())
        if not isinstance(text_excerpt, str) or not text_excerpt.strip():
            failures.append(f"evidence metadata item {index} missing text_excerpt")
    string_refs = {ref.strip() for ref in refs if isinstance(ref, str) and ref.strip()}
    if len(string_refs) != len(refs):
        failures.append("evidence metadata refs must be non-empty strings")
    missing_item_refs = tuple(sorted(metadata_refs - string_refs))
    if missing_item_refs:
        failures.append("evidence metadata refs omit item ref(s): " + ", ".join(missing_item_refs))
    evidence_blocks = coverage.get("evidence_blocks")
    if evidence_blocks != len(items):
        failures.append(
            f"evidence metadata coverage has {evidence_blocks!r} block(s), expected {len(items)}"
        )
    sampled_sources = coverage.get("sampled_sources")
    total_sources = coverage.get("total_sources")
    if not isinstance(sampled_sources, int) or sampled_sources <= 0:
        failures.append("evidence metadata coverage missing sampled_sources")
    if not isinstance(total_sources, int) or total_sources < sampled_sources:
        failures.append("evidence metadata coverage missing valid total_sources")
    expected_ids = _expected_metadata_ids(expectation)
    missing_expected_ids = tuple(sorted(expected_ids - metadata_ids))
    if missing_expected_ids:
        failures.append(
            "evidence metadata missing expected citation id(s): " + ", ".join(missing_expected_ids)
        )
    return tuple(failures)


def _material_operation_failures(events: Sequence[RawEvent]) -> tuple[str, ...]:
    material_events = [event for event in events if event["type"] == "material_operation"]
    if not material_events:
        return ()
    failures: list[str] = []
    first_answer_index = next(
        (
            index
            for index, event in enumerate(events)
            if event["type"] in {"assistant_delta", "turn_complete"}
        ),
        None,
    )
    if first_answer_index is not None:
        late_material = any(
            index > first_answer_index
            for index, event in enumerate(events)
            if event["type"] == "material_operation"
        )
        if late_material:
            failures.append("material operation appears after assistant answer")

    operations: set[str] = set()
    for index, event in enumerate(material_events, start=1):
        operation = event.get("operation")
        if not isinstance(operation, str) or not operation.strip():
            failures.append(f"material operation {index} missing operation")
        else:
            operations.add(operation.strip())
        message = event.get("message")
        if not isinstance(message, str) or not message.strip():
            failures.append(f"material operation {index} missing message")
        metadata = event.get("metadata")
        if not isinstance(metadata, dict) or not metadata:
            failures.append(f"material operation {index} missing metadata")

    if "index_ready" not in operations:
        failures.append("material operations missing index_ready")
    if not operations.intersection({"search_index", "sample_overview", "open_stored_evidence"}):
        failures.append("material operations missing search or overview operation")
    if not operations.intersection({"read_excerpt", "search_result"}):
        failures.append("material operations missing excerpt or search result operation")
    return tuple(failures)


def _expected_material_operation_failures(
    events: Sequence[RawEvent],
    expectation: Mapping[str, object],
) -> list[str]:
    operations = {
        operation.strip()
        for event in events
        if event["type"] == "material_operation"
        for operation in (event.get("operation"),)
        if isinstance(operation, str) and operation.strip()
    }
    failures: list[str] = []
    required = _string_set(expectation.get("required_material_operations"))
    forbidden = _string_set(expectation.get("forbidden_material_operations"))
    missing = sorted(required - operations)
    present = sorted(forbidden & operations)
    if missing:
        failures.append("material operations missing required operation(s): " + ", ".join(missing))
    if present:
        failures.append(
            "material operations included forbidden operation(s): " + ", ".join(present)
        )
    return failures


def _string_set(raw: object) -> set[str]:
    if not isinstance(raw, list):
        return set()
    return {item.strip() for item in raw if isinstance(item, str) and item.strip()}


def _tool_runtime_metadata_failures(events: Sequence[RawEvent]) -> tuple[str, ...]:
    runtime_notices = [
        event
        for event in events
        if event["type"] == "notice" and event.get("code") == "tool_runtime"
    ]
    failures: list[str] = []
    valid_reasons = {"failed", "slow", "large_result", "repeated_call"}
    for index, event in enumerate(runtime_notices, start=1):
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            failures.append(f"tool_runtime notice {index} missing metadata")
            continue
        tool = metadata.get("tool")
        reason = metadata.get("reason")
        latency_ms = metadata.get("latency_ms")
        result_length = metadata.get("result_length")
        if not isinstance(tool, str) or not tool.strip():
            failures.append(f"tool_runtime notice {index} missing tool")
        if reason not in valid_reasons:
            failures.append(f"tool_runtime notice {index} has invalid reason")
        if latency_ms is not None and not isinstance(latency_ms, int | float):
            failures.append(f"tool_runtime notice {index} has invalid latency_ms")
        if result_length is not None and not isinstance(result_length, int):
            failures.append(f"tool_runtime notice {index} has invalid result_length")
        if reason == "failed" and not isinstance(metadata.get("error"), str):
            failures.append(f"tool_runtime notice {index} missing failure error")
        if reason == "repeated_call":
            repeat_count = metadata.get("repeat_count")
            arguments = metadata.get("arguments")
            if not isinstance(repeat_count, int) or repeat_count < 2:
                failures.append(f"tool_runtime notice {index} has invalid repeat_count")
            if not isinstance(arguments, dict):
                failures.append(f"tool_runtime notice {index} missing repeated arguments")
    return tuple(failures)


def _acceptance_criteria_metadata_failures(events: Sequence[RawEvent]) -> tuple[str, ...]:
    criteria_notices = [
        event
        for event in events
        if event["type"] == "notice" and event.get("code") == "acceptance_criteria"
    ]
    failures: list[str] = []
    for index, event in enumerate(criteria_notices, start=1):
        message = event.get("message")
        if not isinstance(message, str) or "Acceptance criteria:" not in message:
            failures.append(f"acceptance_criteria notice {index} missing criteria message")
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            failures.append(f"acceptance_criteria notice {index} missing metadata")
            continue
        if metadata.get("source") != "agent_harness":
            failures.append(f"acceptance_criteria notice {index} has invalid source")
        if metadata.get("requires_tools") is not True:
            failures.append(f"acceptance_criteria notice {index} missing requires_tools=true")
    return tuple(failures)


def _expected_metadata_ids(expectation: Mapping[str, object]) -> set[str]:
    expected_citations = expectation.get("expected_citations")
    if isinstance(expected_citations, list):
        return {
            citation.strip().upper()
            for citation in expected_citations
            if isinstance(citation, str) and citation.strip()
        }
    evidence = expectation.get("evidence")
    if not isinstance(evidence, list):
        return set()
    return {
        evidence_id.strip().upper()
        for item in evidence
        if isinstance(item, dict)
        for evidence_id in (item.get("id"),)
        if isinstance(evidence_id, str) and evidence_id.strip()
    }


def _expectation_known_limit_failures(expectation: Mapping[str, object]) -> tuple[str, ...]:
    known_limits = expectation.get("known_limits", [])
    if not known_limits:
        return ()
    if not isinstance(known_limits, list):
        return ("chat event expectation known_limits must be a list",)
    return ("chat event expectation has unresolved known_limits; review and remove them",)


def print_text_report(report: ChatEventBenchmarkReport) -> None:
    """Print a compact event-stream report."""
    print(f"Chat event benchmark: {report.event_count} event(s)")
    print(f"notice_codes={', '.join(report.notice_codes) if report.notice_codes else 'none'}")
    print(f"reading={'yes' if report.has_reading else 'no'}")
    print(f"evidence={'yes' if report.has_evidence else 'no'}")
    print(f"writing={'yes' if report.has_writing else 'no'}")
    print(f"material_operation={'yes' if report.has_material_operation else 'no'}")
    print(f"material_operation_count={report.material_operation_count}")
    print(
        f"material_operation_metadata={'yes' if report.has_material_operation_metadata else 'no'}"
    )
    print(f"tool_runtime={'yes' if report.has_tool_runtime else 'no'}")
    print(f"tool_runtime_metadata={'yes' if report.has_tool_runtime_metadata else 'no'}")
    print(f"acceptance_criteria={'yes' if report.has_acceptance_criteria else 'no'}")
    print(
        "acceptance_criteria_metadata="
        f"{'yes' if report.has_acceptance_criteria_metadata else 'no'}"
    )
    print(f"assistant_delta={'yes' if report.has_assistant_delta else 'no'}")
    print(f"turn_complete={'yes' if report.has_turn_complete else 'no'}")
    print(f"consistent_completion={'yes' if report.has_consistent_completion else 'no'}")
    print(f"evidence_metadata={'yes' if report.has_evidence_metadata else 'no'}")
    print(f"evidence_metadata_rate={report.evidence_metadata_rate * 100:.1f}%")
    print(f"material_operation_metadata_rate={report.material_operation_metadata_rate * 100:.1f}%")
    print(f"tool_runtime_metadata_rate={report.tool_runtime_metadata_rate * 100:.1f}%")
    print(
        f"acceptance_criteria_metadata_rate={report.acceptance_criteria_metadata_rate * 100:.1f}%"
    )
    if report.answer_pass_rate is not None:
        print(f"answer_pass_rate={report.answer_pass_rate * 100:.1f}%")
        print(f"answer_shape={report.answer_shape_rate * 100:.1f}%")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSONL output from heph chat ask --jsonl")
    parser.add_argument(
        "--answer-expectation",
        type=Path,
        default=None,
        help="Single-case benchmark_answers JSON/JSONL expectation to apply to final answer.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    events_path = cast("Path", args.events).expanduser().resolve()
    expectation_path = cast("Path | None", args.answer_expectation)
    if expectation_path is not None:
        expectation_path = expectation_path.expanduser().resolve()
    try:
        report = run_chat_event_benchmark(
            load_events(events_path),
            expectation=load_expectation(expectation_path),
        )
    except (TypeError, ValueError) as exc:
        print(f"chat event benchmark error: {exc}", file=sys.stderr)
        return 2
    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
