"""Benchmark deterministic study-loop state transitions and review scheduling.

Dataset format:

JSONL:
    {
      "id": "fast-correct-review",
      "domain": "mathematics",
      "turns": [
        {
          "user": "Explain integration by parts",
          "reply": "Use the product rule rearrangement.",
          "source_refs": ["materials/calculus.md#chunk=0"],
          "expected_action": "present",
          "expected_phase": "waiting_for_ready",
          "expected_feedback": "presented"
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.study import (
    StudyAction,
    StudyState,
    apply_turn_result,
    plan_turn,
)
from hephaistos.study.schedule import StudyScheduleStore


class RawStudyTurn(TypedDict):
    user: str
    reply: str
    expected_action: NotRequired[str]
    expected_phase: NotRequired[str]
    expected_feedback: NotRequired[str]
    expected_rating: NotRequired[str]
    expected_confidence: NotRequired[float]
    source_refs: NotRequired[list[str]]
    advance_seconds: NotRequired[int]
    record_schedule: NotRequired[bool]


class RawStudyStateCase(TypedDict):
    turns: list[RawStudyTurn]
    domain: NotRequired[str]
    id: NotRequired[str]
    expected_final_phase: NotRequired[str]
    expected_scheduled_reviews: NotRequired[int]
    expected_due_reviews: NotRequired[int]
    expected_scheduled_concepts: NotRequired[list[str]]
    expected_schedule_error_types: NotRequired[list[str]]
    expected_schedule_failures: NotRequired[list[int]]


@dataclass(frozen=True, slots=True)
class StudyTurnCase:
    user: str
    reply: str
    source_refs: tuple[str, ...] = ()
    advance_seconds: int = 0
    expected_action: str | None = None
    expected_phase: str | None = None
    expected_feedback: str | None = None
    expected_rating: str | None = None
    expected_confidence: float | None = None
    record_schedule: bool = False


@dataclass(frozen=True, slots=True)
class StudyStateCase:
    case_id: str
    turns: tuple[StudyTurnCase, ...]
    domain: str | None = None
    expected_final_phase: str | None = None
    expected_scheduled_reviews: int | None = None
    expected_due_reviews: int | None = None
    expected_scheduled_concepts: tuple[str, ...] = ()
    expected_schedule_error_types: tuple[str, ...] = ()
    expected_schedule_failures: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class StudyTurnResult:
    turn: int
    user: str
    action: str
    phase: str
    feedback: str
    rating: str
    confidence: float | None
    passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StudyStateCaseResult:
    case_id: str
    domain: str | None
    final_phase: str
    scheduled_reviews: int
    due_reviews: int
    scheduled_concepts: tuple[str, ...]
    schedule_error_types: tuple[str, ...]
    schedule_failures: tuple[int, ...]
    schedule_confidences: tuple[float | None, ...]
    schedule_retrieval_successes: tuple[bool, ...]
    schedule_transfer_successes: tuple[bool, ...]
    passed: bool
    failures: tuple[str, ...]
    turns: tuple[StudyTurnResult, ...]


@dataclass(frozen=True, slots=True)
class StudyStateBenchmarkReport:
    cases: int
    domains: tuple[str, ...]
    pass_rate: float
    transition_pass_rate: float
    scheduling_pass_rate: float
    mastery_metadata_rate: float
    failures: tuple[str, ...]
    results: tuple[StudyStateCaseResult, ...]


def _as_raw_cases(payload: object) -> list[RawStudyStateCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("study state dataset must be a JSON list or object with a 'cases' list")

    cases: list[RawStudyStateCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        raw_turns = raw.get("turns")
        if not isinstance(raw_turns, list) or not raw_turns:
            raise ValueError(f"case {idx} must include non-empty turns")

        turns: list[RawStudyTurn] = []
        for turn_idx, raw_turn in enumerate(raw_turns, start=1):
            if not isinstance(raw_turn, dict):
                raise TypeError(f"case {idx} turn {turn_idx} must be an object")
            user = raw_turn.get("user")
            reply = raw_turn.get("reply")
            if not isinstance(user, str) or not user.strip():
                raise ValueError(f"case {idx} turn {turn_idx} must include user")
            if not isinstance(reply, str):
                raise TypeError(f"case {idx} turn {turn_idx} must include reply")
            turn: RawStudyTurn = {"user": user, "reply": reply}
            raw_refs = raw_turn.get("source_refs")
            if isinstance(raw_refs, list):
                turn["source_refs"] = list(raw_refs)
            for field in (
                "expected_action",
                "expected_phase",
                "expected_feedback",
                "expected_rating",
            ):
                raw_value = raw_turn.get(field)
                if isinstance(raw_value, str) and raw_value.strip():
                    turn[field] = raw_value.strip()
            raw_advance = raw_turn.get("advance_seconds")
            if isinstance(raw_advance, int):
                turn["advance_seconds"] = raw_advance
            raw_record = raw_turn.get("record_schedule")
            if isinstance(raw_record, bool):
                turn["record_schedule"] = raw_record
            raw_confidence = raw_turn.get("expected_confidence")
            if isinstance(raw_confidence, int | float) and not isinstance(raw_confidence, bool):
                turn["expected_confidence"] = float(raw_confidence)
            turns.append(turn)

        case: RawStudyStateCase = {"turns": turns}
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            case["id"] = raw_id.strip()
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            case["domain"] = raw_domain.strip()
        raw_final_phase = raw.get("expected_final_phase")
        if isinstance(raw_final_phase, str) and raw_final_phase.strip():
            case["expected_final_phase"] = raw_final_phase.strip()
        for field in ("expected_scheduled_reviews", "expected_due_reviews"):
            raw_count = raw.get(field)
            if isinstance(raw_count, int):
                case[field] = raw_count
        expected_scheduled_concepts = _as_optional_string_list(
            raw.get("expected_scheduled_concepts"),
            f"case {idx} expected_scheduled_concepts",
        )
        if expected_scheduled_concepts:
            case["expected_scheduled_concepts"] = expected_scheduled_concepts
        expected_schedule_error_types = _as_optional_string_list(
            raw.get("expected_schedule_error_types"),
            f"case {idx} expected_schedule_error_types",
        )
        if expected_schedule_error_types:
            case["expected_schedule_error_types"] = expected_schedule_error_types
        expected_schedule_failures = _as_optional_int_list(
            raw.get("expected_schedule_failures"),
            f"case {idx} expected_schedule_failures",
        )
        if expected_schedule_failures:
            case["expected_schedule_failures"] = expected_schedule_failures
        cases.append(case)
    return cases


def _as_optional_string_list(value: object, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    items = [item for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        raise ValueError(f"{field_name} must contain strings only")
    return items


def _as_optional_int_list(value: object, field_name: str) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    items = [item for item in value if isinstance(item, int) and not isinstance(item, bool)]
    if len(items) != len(value):
        raise ValueError(f"{field_name} must contain integers only")
    return items


def _string_tuple(value: object, field_name: str, case_idx: int, turn_idx: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TypeError(f"case {case_idx} turn {turn_idx} {field_name} must be a list")
    refs = tuple(ref for ref in value if isinstance(ref, str) and ref.strip())
    if len(refs) != len(value):
        raise ValueError(f"case {case_idx} turn {turn_idx} {field_name} must contain strings only")
    return refs


def load_cases(path: Path) -> list[StudyStateCase]:
    """Load study-state benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read study state benchmark dataset: {path}") from exc
    try:
        if path.suffix == ".jsonl":
            payload: object = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid study state benchmark JSON: {path}") from exc

    cases: list[StudyStateCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        turns = tuple(
            StudyTurnCase(
                user=raw_turn["user"],
                reply=raw_turn["reply"],
                source_refs=_string_tuple(
                    raw_turn.get("source_refs"), "source_refs", idx, turn_idx
                ),
                advance_seconds=raw_turn.get("advance_seconds", 0),
                expected_action=raw_turn.get("expected_action"),
                expected_phase=raw_turn.get("expected_phase"),
                expected_feedback=raw_turn.get("expected_feedback"),
                expected_rating=raw_turn.get("expected_rating"),
                expected_confidence=raw_turn.get("expected_confidence"),
                record_schedule=raw_turn.get("record_schedule", False),
            )
            for turn_idx, raw_turn in enumerate(raw["turns"], start=1)
        )
        cases.append(
            StudyStateCase(
                case_id=raw.get("id", f"case-{idx}"),
                domain=raw.get("domain"),
                turns=turns,
                expected_final_phase=raw.get("expected_final_phase"),
                expected_scheduled_reviews=raw.get("expected_scheduled_reviews"),
                expected_due_reviews=raw.get("expected_due_reviews"),
                expected_scheduled_concepts=tuple(raw.get("expected_scheduled_concepts", [])),
                expected_schedule_error_types=tuple(raw.get("expected_schedule_error_types", [])),
                expected_schedule_failures=tuple(raw.get("expected_schedule_failures", [])),
            )
        )
    return cases


def run_benchmark(
    cases: Sequence[StudyStateCase], *, armory_path: Path
) -> StudyStateBenchmarkReport:
    """Run study-state transition and scheduling benchmark cases."""
    domains = tuple(sorted({case.domain for case in cases if case.domain}))
    results = [_run_case(case, armory_path=armory_path) for case in cases]

    case_passes = sum(1 for result in results if result.passed)
    turn_results = [turn for result in results for turn in result.turns]
    transition_passes = sum(1 for turn in turn_results if turn.passed)
    scheduling_cases = [
        result for result in results if result.scheduled_reviews > 0 or result.due_reviews > 0
    ]
    scheduling_passes = sum(
        1
        for result in scheduling_cases
        if not any("scheduled" in failure or "due" in failure for failure in result.failures)
    )
    mastery_metadata_rate = _mastery_metadata_rate(results)
    failures = tuple(
        f"{result.case_id}: {failure}" for result in results for failure in result.failures
    )
    return StudyStateBenchmarkReport(
        cases=len(cases),
        domains=domains,
        pass_rate=case_passes / len(cases) if cases else 0.0,
        transition_pass_rate=transition_passes / len(turn_results) if turn_results else 0.0,
        scheduling_pass_rate=(
            scheduling_passes / len(scheduling_cases) if scheduling_cases else 1.0
        ),
        mastery_metadata_rate=mastery_metadata_rate,
        failures=failures,
        results=tuple(results),
    )


def _mastery_metadata_rate(results: Sequence[StudyStateCaseResult]) -> float:
    scheduled_items = [
        (
            concept,
            error_type,
            failure_count,
            confidence,
            retrieval_success,
        )
        for result in results
        for concept, error_type, failure_count, confidence, retrieval_success in zip(
            result.scheduled_concepts,
            result.schedule_error_types,
            result.schedule_failures,
            result.schedule_confidences,
            result.schedule_retrieval_successes,
            strict=True,
        )
    ]
    if not scheduled_items:
        return 1.0
    complete = sum(
        1
        for concept, error_type, failure_count, confidence, retrieval_success in scheduled_items
        if concept
        and error_type
        and failure_count >= 0
        and confidence is not None
        and retrieval_success
    )
    return complete / len(scheduled_items)


def _run_case(case: StudyStateCase, *, armory_path: Path) -> StudyStateCaseResult:
    state = StudyState()
    store = StudyScheduleStore(armory_path)
    now = datetime(2026, 5, 11, 9, 0, tzinfo=UTC)
    turn_results: list[StudyTurnResult] = []
    failures: list[str] = []

    for idx, turn in enumerate(case.turns, start=1):
        now += timedelta(seconds=turn.advance_seconds)
        plan = plan_turn(state, turn.user)
        next_state, _cleaned = apply_turn_result(
            state,
            plan,
            turn.reply,
            list(turn.source_refs),
            now=now,
        )
        turn_failures = _turn_failures(idx, turn, plan.action, next_state)
        if turn.record_schedule:
            store.record_review(
                state.current_item,
                concept=state.retrieval_query,
                retrieval_query=state.retrieval_query,
                source_refs=list(state.expected_source_refs),
                rating=next_state.last_recall_rating,
                elapsed_seconds=next_state.last_recall_seconds,
                confidence=next_state.last_confidence,
                error_type=next_state.last_feedback_type.value,
                exam_importance=1.0 if state.expected_source_refs else 0.0,
                now=now,
            )
        failures.extend(turn_failures)
        turn_results.append(
            StudyTurnResult(
                turn=idx,
                user=turn.user,
                action=plan.action.value,
                phase=next_state.phase.value,
                feedback=next_state.last_feedback_type.value,
                rating=next_state.last_recall_rating.value,
                confidence=next_state.last_confidence,
                passed=not turn_failures,
                failures=tuple(turn_failures),
            )
        )
        state = next_state

    due_reviews = len(store.due_items(now=now + timedelta(days=2)))
    if case.expected_final_phase is not None and state.phase.value != case.expected_final_phase:
        failures.append(
            f"final phase expected {case.expected_final_phase!r}, got {state.phase.value!r}"
        )
    if (
        case.expected_scheduled_reviews is not None
        and len(store.item_list) != case.expected_scheduled_reviews
    ):
        failures.append(
            "scheduled review count expected "
            f"{case.expected_scheduled_reviews}, got {len(store.item_list)}"
        )
    if case.expected_due_reviews is not None and due_reviews != case.expected_due_reviews:
        failures.append(
            f"due review count expected {case.expected_due_reviews}, got {due_reviews}"
        )
    scheduled_concepts = tuple(item.concept for item in store.item_list)
    schedule_error_types = tuple(item.error_type for item in store.item_list)
    schedule_failures = tuple(item.failures for item in store.item_list)
    schedule_confidences = tuple(item.last_confidence for item in store.item_list)
    schedule_retrieval_successes = tuple(item.last_retrieval_success for item in store.item_list)
    schedule_transfer_successes = tuple(item.last_transfer_success for item in store.item_list)
    if case.expected_scheduled_concepts and scheduled_concepts != case.expected_scheduled_concepts:
        failures.append(
            "scheduled concepts expected "
            f"{case.expected_scheduled_concepts!r}, got {scheduled_concepts!r}"
        )
    if (
        case.expected_schedule_error_types
        and schedule_error_types != case.expected_schedule_error_types
    ):
        failures.append(
            "schedule error types expected "
            f"{case.expected_schedule_error_types!r}, got {schedule_error_types!r}"
        )
    if case.expected_schedule_failures and schedule_failures != case.expected_schedule_failures:
        failures.append(
            "schedule failures expected "
            f"{case.expected_schedule_failures!r}, got {schedule_failures!r}"
        )

    return StudyStateCaseResult(
        case_id=case.case_id,
        domain=case.domain,
        final_phase=state.phase.value,
        scheduled_reviews=len(store.item_list),
        due_reviews=due_reviews,
        scheduled_concepts=scheduled_concepts,
        schedule_error_types=schedule_error_types,
        schedule_failures=schedule_failures,
        schedule_confidences=schedule_confidences,
        schedule_retrieval_successes=schedule_retrieval_successes,
        schedule_transfer_successes=schedule_transfer_successes,
        passed=not failures,
        failures=tuple(failures),
        turns=tuple(turn_results),
    )


def _turn_failures(
    turn_idx: int,
    turn: StudyTurnCase,
    action: StudyAction,
    state: StudyState,
) -> list[str]:
    failures: list[str] = []
    if turn.expected_action is not None and action.value != turn.expected_action:
        failures.append(
            f"turn {turn_idx} action expected {turn.expected_action!r}, got {action.value!r}"
        )
    if turn.expected_phase is not None and state.phase.value != turn.expected_phase:
        failures.append(
            f"turn {turn_idx} phase expected {turn.expected_phase!r}, got {state.phase.value!r}"
        )
    if (
        turn.expected_feedback is not None
        and state.last_feedback_type.value != turn.expected_feedback
    ):
        failures.append(
            "turn "
            f"{turn_idx} feedback expected {turn.expected_feedback!r}, "
            f"got {state.last_feedback_type.value!r}"
        )
    if turn.expected_rating is not None and state.last_recall_rating.value != turn.expected_rating:
        failures.append(
            f"turn {turn_idx} rating expected {turn.expected_rating!r}, "
            f"got {state.last_recall_rating.value!r}"
        )
    if turn.expected_confidence is not None and state.last_confidence != turn.expected_confidence:
        failures.append(
            f"turn {turn_idx} confidence expected {turn.expected_confidence!r}, "
            f"got {state.last_confidence!r}"
        )
    return failures


def print_text_report(report: StudyStateBenchmarkReport) -> None:
    """Print a concise human-readable study-state benchmark report."""
    print(f"Study-state benchmark: {report.cases} case(s)")
    print(f"  pass rate: {report.pass_rate:.2%}")
    print(f"  transition pass rate: {report.transition_pass_rate:.2%}")
    print(f"  scheduling pass rate: {report.scheduling_pass_rate:.2%}")
    print(f"  mastery metadata rate: {report.mastery_metadata_rate:.2%}")
    if report.failures:
        print("  failures:")
        for failure in report.failures:
            print(f"    - {failure}")


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--armory", type=Path, default=Path.cwd())
    parser.add_argument("--min-pass-rate", type=float, default=1.0)
    parser.add_argument("--min-transition-pass-rate", type=float, default=1.0)
    parser.add_argument("--min-scheduling-pass-rate", type=float, default=1.0)
    parser.add_argument("--json-report", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    min_pass_rate = cast("float", args.min_pass_rate)
    min_transition_pass_rate = cast("float", args.min_transition_pass_rate)
    min_scheduling_pass_rate = cast("float", args.min_scheduling_pass_rate)
    _validate_rate(min_pass_rate, "--min-pass-rate", parser)
    _validate_rate(min_transition_pass_rate, "--min-transition-pass-rate", parser)
    _validate_rate(min_scheduling_pass_rate, "--min-scheduling-pass-rate", parser)

    try:
        report = run_benchmark(
            load_cases(cast("Path", args.dataset).expanduser().resolve()),
            armory_path=cast("Path", args.armory).expanduser().resolve(),
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"study state benchmark error: {exc}", file=sys.stderr)
        return 2

    print_text_report(report)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote study-state benchmark report to {json_report}")
    return (
        0
        if report.pass_rate >= min_pass_rate
        and report.transition_pass_rate >= min_transition_pass_rate
        and report.scheduling_pass_rate >= min_scheduling_pass_rate
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
