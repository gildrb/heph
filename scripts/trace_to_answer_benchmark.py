"""Convert Heph session traces into grounded-answer benchmark fixtures.

Trace files live under ``<armory>/.hephaion/traces/<session_id>.jsonl``.
This helper extracts user/reply pairs plus the exact evidence metadata recorded
for each reply and writes JSONL compatible with ``scripts.benchmark_answers``.
It lets a bad live answer become a reproducible benchmark case without calling
the model again.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.rag.retrieval_types import EvidenceReference

from scripts import benchmark_answers, replay_answer_benchmark

_LEGACY_MATERIAL_TASK_KEY = "study_task"


class TraceEvidenceItem(TypedDict):
    evidence_id: str
    ref: str
    score: NotRequired[float]
    text_excerpt: NotRequired[str]


class TraceReply(TypedDict):
    query: str
    answer: str
    evidence_items: list[TraceEvidenceItem]
    case_id: str
    task: NotRequired[str]
    evidence_coverage: NotRequired[dict[str, int]]


class TraceReplyLabels(TypedDict, total=False):
    task: str


class TraceExpectation(TypedDict, total=False):
    id: str
    turn: int
    domain: str
    task: str
    require_citations: bool
    require_abstention: bool
    required_label: str
    expected_citations: list[str]
    must_include: list[str]
    must_not_include: list[str]
    min_words: int
    max_words: int
    min_citation_count: int
    min_distinct_sources: int
    min_sampled_sources: int
    min_bullet_count: int
    min_cited_bullet_count: int
    max_explicit_date_lines: int
    supported_claims: list[dict[str, str]]


def _load_trace_events(path: Path) -> list[Mapping[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"could not read trace file: {path}") from exc

    events: list[Mapping[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid trace JSON at line {line_number}: {path}") from exc
        if not isinstance(payload, dict):
            raise TypeError(f"trace line {line_number} must be a JSON object")
        events.append(cast("Mapping[str, object]", payload))
    if not events:
        raise ValueError("trace file does not contain any events")
    return events


def _as_evidence_items(value: object) -> list[TraceEvidenceItem]:
    if not isinstance(value, list):
        return []
    items: list[TraceEvidenceItem] = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        evidence_id = raw.get("evidence_id")
        ref = raw.get("ref")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            continue
        if not isinstance(ref, str) or EvidenceReference.parse(ref) is None:
            continue
        item: TraceEvidenceItem = {
            "evidence_id": evidence_id.strip().upper(),
            "ref": ref,
        }
        score = raw.get("score")
        if isinstance(score, int | float):
            item["score"] = float(score)
        text_excerpt = raw.get("text_excerpt")
        if isinstance(text_excerpt, str) and text_excerpt.strip():
            item["text_excerpt"] = text_excerpt.strip()
        items.append(item)
    return items


def extract_trace_replies(path: Path) -> list[TraceReply]:
    """Extract user/reply/evidence tuples from a session trace."""
    events = _load_trace_events(path)
    replies: list[TraceReply] = []
    last_user = ""
    reply_index = 0
    for event in events:
        event_type = event.get("type")
        if event_type == "user_message":
            content = event.get("content")
            last_user = content.strip() if isinstance(content, str) else ""
            continue
        if event_type != "session" or event.get("event") != "reply":
            continue
        reply_excerpt = event.get("reply_excerpt")
        if not isinstance(reply_excerpt, str) or not reply_excerpt.strip():
            continue
        reply_index += 1
        reply: TraceReply = {
            "case_id": f"{path.stem}-turn-{reply_index}",
            "query": last_user,
            "answer": reply_excerpt.strip(),
            "evidence_items": _as_evidence_items(event.get("evidence_items")),
            **_trace_reply_labels(event),
        }
        coverage = _as_evidence_coverage(event.get("evidence_coverage"))
        if coverage:
            reply["evidence_coverage"] = coverage
        replies.append(reply)
    if not replies:
        raise ValueError("trace does not contain reply events with reply excerpts")
    return replies


def _trace_reply_labels(event: Mapping[str, object]) -> TraceReplyLabels:
    labels: TraceReplyLabels = {}
    material_task = event.get("material_task")
    if material_task is None:
        material_task = event.get(_LEGACY_MATERIAL_TASK_KEY)
    if isinstance(material_task, str) and material_task.strip():
        labels["task"] = material_task.strip()
    return labels


def _as_evidence_coverage(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    coverage: dict[str, int] = {}
    for field_name in ("evidence_blocks", "sampled_sources", "total_sources"):
        raw_value = value.get(field_name)
        if isinstance(raw_value, bool) or not isinstance(raw_value, int) or raw_value < 0:
            continue
        coverage[field_name] = raw_value
    return coverage


def _as_string_list(value: object, field_name: str, item_label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{item_label} field '{field_name}' must be a list")
    items = [item for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        raise ValueError(f"{item_label} field '{field_name}' must contain strings only")
    return items


def _as_non_negative_int(value: object, field_name: str, item_label: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{item_label} field '{field_name}' must be a non-negative integer")
    return value


def _as_supported_claims(value: object, item_label: str) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{item_label} field 'supported_claims' must be a list")
    claims: list[dict[str, str]] = []
    for claim_idx, raw_claim in enumerate(value, start=1):
        if not isinstance(raw_claim, dict):
            raise TypeError(f"{item_label} supported claim {claim_idx} must be an object")
        text = raw_claim.get("text")
        evidence_id = raw_claim.get("evidence_id")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{item_label} supported claim {claim_idx} must include text")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError(f"{item_label} supported claim {claim_idx} must include evidence_id")
        claims.append({"text": text.strip(), "evidence_id": evidence_id.strip().upper()})
    return claims


def _load_expectations(path: Path | None) -> dict[str, TraceExpectation]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read trace expectation file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid trace expectation JSON: {path}") from exc
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("trace expectations must be a JSON list or an object with a 'cases' list")

    expectations: dict[str, TraceExpectation] = {}
    for idx, raw in enumerate(raw_cases, start=1):
        item_label = f"expectation {idx}"
        if not isinstance(raw, dict):
            raise TypeError(f"{item_label} must be an object")
        expectation: TraceExpectation = {}
        raw_id = raw.get("id")
        raw_turn = raw.get("turn")
        key = ""
        if isinstance(raw_id, str) and raw_id.strip():
            expectation["id"] = raw_id.strip()
            key = expectation["id"]
        elif isinstance(raw_turn, int) and raw_turn > 0:
            expectation["turn"] = raw_turn
            key = f"turn:{raw_turn}"
        else:
            raise ValueError(f"{item_label} must include non-empty id or positive turn")

        domain = raw.get("domain")
        if isinstance(domain, str) and domain.strip():
            expectation["domain"] = domain.strip()
        task = raw.get("task")
        if isinstance(task, str) and task.strip():
            expectation["task"] = task.strip()
        require_citations = raw.get("require_citations")
        if isinstance(require_citations, bool):
            expectation["require_citations"] = require_citations
        require_abstention = raw.get("require_abstention")
        if isinstance(require_abstention, bool):
            expectation["require_abstention"] = require_abstention
        required_label = raw.get("required_label")
        if isinstance(required_label, str) and required_label.strip():
            expectation["required_label"] = required_label.strip()

        expected_citations = _as_string_list(
            raw.get("expected_citations"), "expected_citations", item_label
        )
        if expected_citations:
            expectation["expected_citations"] = expected_citations
        must_include = _as_string_list(raw.get("must_include"), "must_include", item_label)
        if must_include:
            expectation["must_include"] = must_include
        must_not_include = _as_string_list(
            raw.get("must_not_include"), "must_not_include", item_label
        )
        if must_not_include:
            expectation["must_not_include"] = must_not_include
        for field_name in (
            "min_words",
            "max_words",
            "min_citation_count",
            "min_distinct_sources",
            "min_sampled_sources",
            "min_bullet_count",
            "min_cited_bullet_count",
        ):
            value = _as_non_negative_int(raw.get(field_name), field_name, item_label)
            if value:
                expectation[field_name] = value
        claims = _as_supported_claims(raw.get("supported_claims"), item_label)
        if claims:
            expectation["supported_claims"] = claims
        expectations[key] = expectation
    return expectations


def _expectation_for_reply(
    reply: TraceReply,
    expectations: Mapping[str, TraceExpectation],
) -> TraceExpectation:
    raw_turn = reply["case_id"].rsplit("-turn-", maxsplit=1)[-1]
    turn_key = f"turn:{raw_turn}" if raw_turn.isdigit() else ""
    explicit = expectations.get(reply["case_id"]) or expectations.get(turn_key)
    default = _default_expectation_for_reply(reply)
    if explicit is None:
        return default
    return _merge_expectations(default, explicit)


def _default_expectation_for_reply(reply: TraceReply) -> TraceExpectation:
    """Return generic task contracts inferred from trace metadata."""
    if reply.get("task") != "material-overview":
        return {}
    return {
        "task": "material-overview",
        "min_words": 24,
        "max_words": 120,
        "min_citation_count": 2,
        "min_distinct_sources": 2,
        "min_sampled_sources": 2,
        "min_bullet_count": 2,
        "min_cited_bullet_count": 2,
        "max_explicit_date_lines": 1,
        "must_not_include": [
            "No evidence citations",
            "Say ready when you want recall",
            "the files cover",
        ],
    }


def _merge_expectations(
    default: TraceExpectation,
    explicit: TraceExpectation,
) -> TraceExpectation:
    merged: TraceExpectation = {**default, **explicit}
    expected_citations = [
        *default.get("expected_citations", []),
        *explicit.get("expected_citations", []),
    ]
    if expected_citations:
        merged["expected_citations"] = expected_citations
    must_include = [*default.get("must_include", []), *explicit.get("must_include", [])]
    if must_include:
        merged["must_include"] = must_include
    must_not_include = [
        *default.get("must_not_include", []),
        *explicit.get("must_not_include", []),
    ]
    if must_not_include:
        merged["must_not_include"] = must_not_include
    for field_name in (
        "min_words",
        "max_words",
        "min_citation_count",
        "min_distinct_sources",
        "min_sampled_sources",
        "min_bullet_count",
        "min_cited_bullet_count",
        "max_explicit_date_lines",
    ):
        merged_value = max(default.get(field_name, 0), explicit.get(field_name, 0))
        if merged_value:
            merged[field_name] = merged_value
    default_claims = default.get("supported_claims", [])
    explicit_claims = explicit.get("supported_claims", [])
    if default_claims or explicit_claims:
        merged["supported_claims"] = [*default_claims, *explicit_claims]
    return merged


def _fixture_from_trace_reply(
    reply: TraceReply,
    *,
    require_citations: bool,
    expect_all_citations: bool,
    expectation: TraceExpectation | None = None,
) -> replay_answer_benchmark.AnswerFixture:
    resolved_expectation: TraceExpectation = expectation if expectation is not None else {}
    evidence: list[dict[str, object]] = []
    expected_citations: list[str] = []
    for item in reply["evidence_items"]:
        parsed = EvidenceReference.parse(item["ref"])
        if parsed is None:
            continue
        evidence_id = item["evidence_id"]
        evidence.append(
            {
                "id": evidence_id,
                "source": parsed.source,
                "chunk": parsed.chunk_index,
                "text": item.get("text_excerpt", ""),
                "score": item.get("score", 1.0),
            }
        )
        expected_citations.append(evidence_id)

    fixture: replay_answer_benchmark.AnswerFixture = {
        "id": reply["case_id"],
        "query": reply["query"],
        "answer": reply["answer"],
        "evidence": evidence,
        "task": resolved_expectation.get("task", reply.get("task", "trace-replay")),
        "require_citations": resolved_expectation.get(
            "require_citations", require_citations and bool(evidence)
        ),
    }
    coverage = reply.get("evidence_coverage", {})
    if coverage:
        fixture["evidence_coverage"] = coverage
    if "domain" in resolved_expectation:
        fixture["domain"] = resolved_expectation["domain"]
    if resolved_expectation.get("require_abstention"):
        fixture["require_abstention"] = True
    if resolved_expectation.get("required_label"):
        fixture["required_label"] = resolved_expectation["required_label"]
    explicit_expected = resolved_expectation.get("expected_citations", [])
    if explicit_expected:
        fixture["expected_citations"] = explicit_expected
    elif expect_all_citations and expected_citations:
        fixture["expected_citations"] = expected_citations
    if resolved_expectation.get("must_include"):
        fixture["must_include"] = resolved_expectation["must_include"]
    if resolved_expectation.get("must_not_include"):
        fixture["must_not_include"] = resolved_expectation["must_not_include"]
    for field_name in (
        "min_words",
        "max_words",
        "min_citation_count",
        "min_distinct_sources",
        "min_sampled_sources",
        "min_bullet_count",
        "min_cited_bullet_count",
        "max_explicit_date_lines",
    ):
        value = resolved_expectation.get(field_name)
        if isinstance(value, int) and value > 0:
            fixture[field_name] = value
    if resolved_expectation.get("supported_claims"):
        fixture["supported_claims"] = resolved_expectation["supported_claims"]
    return fixture


def fixtures_from_trace(
    path: Path,
    *,
    require_citations: bool = True,
    expect_all_citations: bool = False,
    expectations_path: Path | None = None,
) -> list[replay_answer_benchmark.AnswerFixture]:
    """Convert one trace file into answer benchmark fixtures."""
    expectations = _load_expectations(expectations_path)
    return [
        _fixture_from_trace_reply(
            reply,
            require_citations=require_citations,
            expect_all_citations=expect_all_citations,
            expectation=_expectation_for_reply(reply, expectations),
        )
        for reply in extract_trace_replies(path)
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="Session trace JSONL file")
    parser.add_argument("output", type=Path, help="Output answer fixture JSONL path")
    parser.add_argument(
        "--allow-uncited",
        action="store_true",
        help="Do not require citations when a reply had evidence in the trace.",
    )
    parser.add_argument(
        "--expect-all-citations",
        action="store_true",
        help="Require the reply to cite every evidence ID recorded for the turn.",
    )
    parser.add_argument(
        "--expectations",
        type=Path,
        default=None,
        help=(
            "Optional JSON expectations keyed by trace case id or turn number "
            "(must_include, must_not_include, supported_claims, etc.)."
        ),
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Score the generated fixtures with scripts.benchmark_answers.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    trace = cast("Path", args.trace).expanduser().resolve()
    output = cast("Path", args.output).expanduser().resolve()
    require_citations = not cast("bool", args.allow_uncited)
    expect_all_citations = cast("bool", args.expect_all_citations)
    expectations = cast("Path | None", args.expectations)
    if expectations is not None:
        expectations = expectations.expanduser().resolve()

    try:
        fixtures = fixtures_from_trace(
            trace,
            require_citations=require_citations,
            expect_all_citations=expect_all_citations,
            expectations_path=expectations,
        )
        replay_answer_benchmark.write_jsonl(output, fixtures)
    except (OSError, TypeError, ValueError) as exc:
        print(f"trace replay error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {len(fixtures)} trace answer fixture(s) to {output}")
    if cast("bool", args.score):
        report = benchmark_answers.run_benchmark(benchmark_answers.load_cases(output))
        benchmark_answers.print_text_report(report)
        return 0 if report.pass_rate == 1.0 else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
