"""Replay benchmark prompts through the chat harness and write answer fixtures.

Input dataset format:

JSONL:
    {"id": "q1", "prompt": "Using the sources, explain Dijkstra.", "must_include": [...]}

JSON:
    {"cases": [{"id": "q1", "prompt": "..."}]}

The output is JSONL compatible with ``scripts.benchmark_answers``. Each output
case includes the model answer and the exact turn evidence visible to the
assistant for that prompt.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from chat.automation import iter_chat_events
from chat.events import AssistantDeltaEvent
from chat.session import create_session
from heph_ai.runtime import ChatConfig
from rag import TurnEvidence


class RawReplayCase(TypedDict):
    prompt: str
    domain: NotRequired[str]
    task: NotRequired[str]
    id: NotRequired[str]
    require_citations: NotRequired[bool]
    require_abstention: NotRequired[bool]
    required_label: NotRequired[str]
    expected_citations: NotRequired[list[str]]
    must_include: NotRequired[list[str]]
    must_not_include: NotRequired[list[str]]
    min_words: NotRequired[int]
    max_words: NotRequired[int]
    min_citation_count: NotRequired[int]
    min_distinct_sources: NotRequired[int]
    min_sampled_sources: NotRequired[int]
    min_bullet_count: NotRequired[int]
    min_cited_bullet_count: NotRequired[int]
    max_explicit_date_lines: NotRequired[int]
    supported_claims: NotRequired[list[dict[str, str]]]


class AnswerFixture(TypedDict):
    id: str
    query: str
    answer: str
    evidence: list[dict[str, object]]
    domain: NotRequired[str]
    task: NotRequired[str]
    require_citations: NotRequired[bool]
    require_abstention: NotRequired[bool]
    required_label: NotRequired[str]
    expected_citations: NotRequired[list[str]]
    must_include: NotRequired[list[str]]
    must_not_include: NotRequired[list[str]]
    min_words: NotRequired[int]
    max_words: NotRequired[int]
    min_citation_count: NotRequired[int]
    min_distinct_sources: NotRequired[int]
    min_sampled_sources: NotRequired[int]
    min_bullet_count: NotRequired[int]
    min_cited_bullet_count: NotRequired[int]
    max_explicit_date_lines: NotRequired[int]
    evidence_coverage: NotRequired[dict[str, int]]
    supported_claims: NotRequired[list[dict[str, str]]]


@dataclass(frozen=True, slots=True)
class ReplayCase:
    case_id: str
    prompt: str
    domain: str | None = None
    task: str | None = None
    require_citations: bool | None = None
    require_abstention: bool = False
    required_label: str | None = None
    expected_citations: tuple[str, ...] = ()
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()
    min_words: int = 0
    max_words: int = 0
    min_citation_count: int = 0
    min_distinct_sources: int = 0
    min_bullet_count: int = 0
    min_cited_bullet_count: int = 0
    max_explicit_date_lines: int = 0
    supported_claims: tuple[dict[str, str], ...] = ()


def _as_string_list(value: object, field_name: str, case_idx: int) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"case {case_idx} field '{field_name}' must be a list")
    items = [item for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        raise ValueError(f"case {case_idx} field '{field_name}' must contain strings only")
    return items


def _as_non_negative_int(value: object, field_name: str, case_idx: int) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"case {case_idx} field '{field_name}' must be a non-negative integer")
    return value


def _as_raw_cases(payload: object) -> list[RawReplayCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("replay dataset must be a JSON list or an object with a 'cases' list")

    cases: list[RawReplayCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        prompt = raw.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"case {idx} must include a non-empty string 'prompt'")
        raw_case: RawReplayCase = {"prompt": prompt}

        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            raw_case["id"] = raw_id
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            raw_case["domain"] = raw_domain.strip()
        raw_task = raw.get("task")
        if isinstance(raw_task, str) and raw_task.strip():
            raw_case["task"] = raw_task.strip()
        raw_require_citations = raw.get("require_citations")
        if isinstance(raw_require_citations, bool):
            raw_case["require_citations"] = raw_require_citations
        raw_require_abstention = raw.get("require_abstention")
        if isinstance(raw_require_abstention, bool):
            raw_case["require_abstention"] = raw_require_abstention
        raw_required_label = raw.get("required_label")
        if isinstance(raw_required_label, str) and raw_required_label.strip():
            raw_case["required_label"] = raw_required_label.strip()

        expected_citations = _as_string_list(
            raw.get("expected_citations"),
            "expected_citations",
            idx,
        )
        if expected_citations:
            raw_case["expected_citations"] = expected_citations
        must_include = _as_string_list(raw.get("must_include"), "must_include", idx)
        if must_include:
            raw_case["must_include"] = must_include
        must_not_include = _as_string_list(raw.get("must_not_include"), "must_not_include", idx)
        if must_not_include:
            raw_case["must_not_include"] = must_not_include
        min_words = _as_non_negative_int(raw.get("min_words"), "min_words", idx)
        if min_words:
            raw_case["min_words"] = min_words
        max_words = _as_non_negative_int(raw.get("max_words"), "max_words", idx)
        if max_words:
            raw_case["max_words"] = max_words
        min_citation_count = _as_non_negative_int(
            raw.get("min_citation_count"),
            "min_citation_count",
            idx,
        )
        if min_citation_count:
            raw_case["min_citation_count"] = min_citation_count
        min_distinct_sources = _as_non_negative_int(
            raw.get("min_distinct_sources"),
            "min_distinct_sources",
            idx,
        )
        if min_distinct_sources:
            raw_case["min_distinct_sources"] = min_distinct_sources
        min_bullet_count = _as_non_negative_int(
            raw.get("min_bullet_count"),
            "min_bullet_count",
            idx,
        )
        if min_bullet_count:
            raw_case["min_bullet_count"] = min_bullet_count
        min_cited_bullet_count = _as_non_negative_int(
            raw.get("min_cited_bullet_count"),
            "min_cited_bullet_count",
            idx,
        )
        if min_cited_bullet_count:
            raw_case["min_cited_bullet_count"] = min_cited_bullet_count
        max_explicit_date_lines = _as_non_negative_int(
            raw.get("max_explicit_date_lines"),
            "max_explicit_date_lines",
            idx,
        )
        if max_explicit_date_lines:
            raw_case["max_explicit_date_lines"] = max_explicit_date_lines
        raw_supported_claims = raw.get("supported_claims")
        if isinstance(raw_supported_claims, list):
            supported_claims: list[dict[str, str]] = []
            for claim_idx, raw_claim in enumerate(raw_supported_claims, start=1):
                if not isinstance(raw_claim, dict):
                    raise TypeError(f"case {idx} supported claim {claim_idx} must be an object")
                text = raw_claim.get("text")
                evidence_id = raw_claim.get("evidence_id")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"case {idx} supported claim {claim_idx} must include text")
                if not isinstance(evidence_id, str) or not evidence_id.strip():
                    raise ValueError(
                        f"case {idx} supported claim {claim_idx} must include evidence_id"
                    )
                supported_claims.append(
                    {"text": text.strip(), "evidence_id": evidence_id.strip().upper()}
                )
            raw_case["supported_claims"] = supported_claims

        cases.append(raw_case)
    return cases


def load_cases(path: Path) -> list[ReplayCase]:
    """Load replay cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read replay dataset: {path}") from exc

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
        raise ValueError(f"invalid replay dataset JSON: {path}") from exc

    cases: list[ReplayCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        case = ReplayCase(
            case_id=raw.get("id", f"case-{idx}"),
            prompt=raw["prompt"].strip(),
            domain=raw.get("domain"),
            task=raw.get("task"),
            require_citations=raw.get("require_citations"),
            require_abstention=raw.get("require_abstention", False),
            required_label=raw.get("required_label"),
            expected_citations=tuple(raw.get("expected_citations", [])),
            must_include=tuple(raw.get("must_include", [])),
            must_not_include=tuple(raw.get("must_not_include", [])),
            min_words=raw.get("min_words", 0),
            max_words=raw.get("max_words", 0),
            min_citation_count=raw.get("min_citation_count", 0),
            min_distinct_sources=raw.get("min_distinct_sources", 0),
            min_bullet_count=raw.get("min_bullet_count", 0),
            min_cited_bullet_count=raw.get("min_cited_bullet_count", 0),
            max_explicit_date_lines=raw.get("max_explicit_date_lines", 0),
            supported_claims=tuple(raw.get("supported_claims", [])),
        )
        if not _has_answer_contract(case):
            raise ValueError(f"case {idx} must include at least one answer-contract check")
        cases.append(case)
    if not cases:
        raise ValueError("replay dataset does not contain any cases")
    return cases


def _has_answer_contract(case: ReplayCase) -> bool:
    return bool(
        case.require_citations is not None
        or case.require_abstention
        or case.required_label
        or case.expected_citations
        or case.must_include
        or case.must_not_include
        or case.min_words
        or case.max_words
        or case.min_citation_count
        or case.min_distinct_sources
        or case.min_bullet_count
        or case.min_cited_bullet_count
        or case.max_explicit_date_lines
        or case.supported_claims
    )


def has_shaped_material_overview_case(cases: Sequence[ReplayCase]) -> bool:
    """Return whether replay cases prove material overview answer shape."""
    return any(
        case.task == "material-overview"
        and case.min_words > 0
        and case.max_words > 0
        and case.min_citation_count > 1
        and case.min_distinct_sources > 1
        and case.min_bullet_count > 1
        and case.min_cited_bullet_count > 1
        and case.max_explicit_date_lines > 0
        for case in cases
    )


def _serialize_evidence(turn_evidence: TurnEvidence | None) -> list[dict[str, object]]:
    if not turn_evidence:
        return []
    return [
        {
            "id": item.evidence_id,
            "source": item.source,
            "chunk": item.chunk_index,
            "text": item.content,
            "score": item.score,
        }
        for item in turn_evidence.items
    ]


def _fixture_from_result(
    case: ReplayCase,
    *,
    answer: str,
    turn_evidence: TurnEvidence | None,
) -> AnswerFixture:
    fixture: AnswerFixture = {
        "id": case.case_id,
        "query": case.prompt,
        "answer": answer,
        "evidence": _serialize_evidence(turn_evidence),
    }
    if case.domain:
        fixture["domain"] = case.domain
    if case.task:
        fixture["task"] = case.task
    if case.require_citations is not None:
        fixture["require_citations"] = case.require_citations
    if case.require_abstention:
        fixture["require_abstention"] = case.require_abstention
    if case.required_label:
        fixture["required_label"] = case.required_label
    if case.expected_citations:
        fixture["expected_citations"] = list(case.expected_citations)
    if case.must_include:
        fixture["must_include"] = list(case.must_include)
    if case.must_not_include:
        fixture["must_not_include"] = list(case.must_not_include)
    if case.min_words:
        fixture["min_words"] = case.min_words
    if case.max_words:
        fixture["max_words"] = case.max_words
    if case.min_citation_count:
        fixture["min_citation_count"] = case.min_citation_count
    if case.min_distinct_sources:
        fixture["min_distinct_sources"] = case.min_distinct_sources
    if case.min_bullet_count:
        fixture["min_bullet_count"] = case.min_bullet_count
    if case.min_cited_bullet_count:
        fixture["min_cited_bullet_count"] = case.min_cited_bullet_count
    if case.max_explicit_date_lines:
        fixture["max_explicit_date_lines"] = case.max_explicit_date_lines
    if case.supported_claims:
        fixture["supported_claims"] = list(case.supported_claims)
    return fixture


def replay_cases(
    armory_path: Path,
    cases: Sequence[ReplayCase],
    config: ChatConfig,
) -> list[AnswerFixture]:
    """Run each replay case in a fresh session and return answer fixtures."""
    if not cases:
        raise ValueError("replay dataset does not contain any cases")

    fixtures: list[AnswerFixture] = []
    for case in cases:
        session = create_session(config, armory_path)
        answer = "".join(
            event.delta
            for event in iter_chat_events(session, case.prompt)
            if isinstance(event, AssistantDeltaEvent)
        )
        fixtures.append(
            _fixture_from_result(
                case,
                answer=answer.strip(),
                turn_evidence=session.last_turn_evidence,
            )
        )
    return fixtures


def write_jsonl(path: Path, fixtures: Sequence[AnswerFixture]) -> None:
    """Write answer fixtures as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for fixture in fixtures:
            handle.write(json.dumps(fixture, ensure_ascii=False))
            handle.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL replay prompts")
    parser.add_argument("output", type=Path, help="Output JSONL answer fixture path")
    parser.add_argument("--model", default="", help="Model name for ChatConfig")
    parser.add_argument("--base-url", default="", help="Optional OpenAI-compatible base URL")
    parser.add_argument("--api-key", default="", help="Optional API key")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--rag-context-budget", type=int, default=2000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    output = cast("Path", args.output).expanduser().resolve()
    max_tokens = cast("int", args.max_tokens)
    rag_context_budget = cast("int", args.rag_context_budget)

    if max_tokens <= 0:
        parser.error("--max-tokens must be positive")
    if rag_context_budget <= 0:
        parser.error("--rag-context-budget must be positive")

    config = ChatConfig(
        api_key=cast("str", args.api_key),
        base_url=cast("str", args.base_url),
        model=cast("str", args.model),
        max_tokens=max_tokens,
        rag_context_budget=rag_context_budget,
    )

    try:
        fixtures = replay_cases(armory, load_cases(dataset), config)
        write_jsonl(output, fixtures)
    except (TypeError, ValueError) as exc:
        print(f"replay error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {len(fixtures)} answer fixture(s) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
