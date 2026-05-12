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
    has_assistant_delta: bool
    has_turn_complete: bool
    has_consistent_completion: bool
    has_evidence_metadata: bool
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
    has_assistant_delta = any(event["type"] == "assistant_delta" for event in events)
    has_turn_complete = any(event["type"] == "turn_complete" for event in events)
    metadata_failures = _evidence_metadata_failures(events, expectation)
    has_evidence_metadata = not metadata_failures
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
    if not has_assistant_delta:
        failures.append("missing assistant delta")
    if not has_turn_complete:
        failures.append("missing turn completion")
    if not has_consistent_completion:
        failures.append("assistant delta text does not match turn completion text")
    failures.extend(metadata_failures)
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
        has_assistant_delta=has_assistant_delta,
        has_turn_complete=has_turn_complete,
        has_consistent_completion=has_consistent_completion,
        has_evidence_metadata=has_evidence_metadata,
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
    print(f"assistant_delta={'yes' if report.has_assistant_delta else 'no'}")
    print(f"turn_complete={'yes' if report.has_turn_complete else 'no'}")
    print(f"consistent_completion={'yes' if report.has_consistent_completion else 'no'}")
    print(f"evidence_metadata={'yes' if report.has_evidence_metadata else 'no'}")
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
