"""Extract a reviewable answer expectation scaffold from chat JSONL events."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from hephaion.agent.citation import extract_citations

_REF_RE = re.compile(r"^(?P<source>.+)#chunk=(?P<chunk>\d+)$")


def extract_expectation(events_path: Path, *, reviewed: bool = False) -> list[dict[str, object]]:
    """Build a single-case expectation scaffold from a captured chat turn."""
    events = _load_events(events_path)
    final_answer = _final_answer(events)
    evidence_items = _evidence_items(events)
    citations = tuple(citation.evidence_id for citation in extract_citations(final_answer))
    expected_citations = _expected_citations(citations, evidence_items)
    if len(expected_citations) < 2:
        expected_citations = sorted(_evidence_ids(evidence_items))[:2]
    expectation: dict[str, object] = {
        "id": "real-corpus-material-overview",
        "domain": "review-required",
        "task": "material-overview",
        "must_not_include": [
            "the files cover",
            "next action",
            "say ready when you want recall",
            "ask for recall",
            "answer from memory",
            "source-backed",
            "source backed",
            "no evidence citations",
            "Document signals",
            "Retrieved overview sample",
            "Sampled orientation",
            "Visible topics",
            "non-exhaustive list",
            "not an exhaustive summary",
            "only a sample",
            "partial inventory",
        ],
        "expected_citations": expected_citations,
        "min_words": 24,
        "min_citation_count": 2,
        "min_distinct_sources": 2,
        "min_bullet_count": 2,
        "min_cited_bullet_count": 2,
        "max_explicit_date_lines": 1,
        "evidence": evidence_items,
    }
    if _has_material_operation(events, "sample_overview"):
        expectation["required_material_operations"] = ["sample_overview"]
        expectation["forbidden_material_operations"] = ["search_index"]
    if not reviewed:
        expectation["known_limits"] = [
            "Review scaffold extracted from chat JSONL; verify evidence text and "
            "citations before using as completion proof."
        ]
    return [expectation]


def _expected_citations(
    citations: Sequence[str],
    evidence_items: Sequence[Mapping[str, object]],
) -> list[str]:
    evidence_ids = _evidence_ids(evidence_items)
    expected_citations = [citation for citation in citations if citation in evidence_ids]
    if len(expected_citations) < 2:
        return sorted(evidence_ids)[:2]
    return expected_citations


def _load_events(path: Path) -> list[Mapping[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"could not read chat events: {path}") from exc
    events: list[Mapping[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {path}") from exc
        if not isinstance(payload, dict):
            raise TypeError(f"event line {line_number} must be an object")
        events.append(cast("Mapping[str, object]", payload))
    if not events:
        raise ValueError("chat event file is empty")
    return events


def _final_answer(events: Sequence[Mapping[str, object]]) -> str:
    completed = [
        event.get("full_text")
        for event in events
        if event.get("type") == "turn_complete" and isinstance(event.get("full_text"), str)
    ]
    if completed:
        return cast("str", completed[-1])
    return "".join(
        cast("str", event.get("delta"))
        for event in events
        if event.get("type") == "assistant_delta" and isinstance(event.get("delta"), str)
    )


def _evidence_items(events: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    notices = [
        event
        for event in events
        if event.get("type") == "notice" and event.get("code") == "evidence"
    ]
    if not notices:
        raise ValueError("chat events do not include an evidence notice")
    metadata = notices[-1].get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError("evidence notice does not include metadata")
    raw_items = metadata.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("evidence notice metadata does not include evidence items")

    items: list[dict[str, object]] = []
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise TypeError(f"evidence metadata item {index} must be an object")
        evidence_id = _string_field(raw_item, "evidence_id", index)
        ref = _string_field(raw_item, "ref", index)
        text = _string_field(raw_item, "text_excerpt", index)
        source, chunk = _parse_ref(ref)
        items.append(
            {
                "id": evidence_id,
                "source": source,
                "chunk": chunk,
                "text": text,
            }
        )
    return items


def _has_material_operation(events: Sequence[Mapping[str, object]], operation: str) -> bool:
    return any(
        event.get("type") == "material_operation" and event.get("operation") == operation
        for event in events
    )


def _string_field(raw_item: Mapping[object, object], field: str, index: int) -> str:
    value = raw_item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"evidence metadata item {index} missing {field}")
    return value.strip()


def _parse_ref(ref: str) -> tuple[str, int]:
    match = _REF_RE.match(ref)
    if match is None:
        return ref, 0
    return match.group("source"), int(match.group("chunk"))


def _evidence_ids(items: Sequence[Mapping[str, object]]) -> set[str]:
    return {str(item["id"]).upper() for item in items if isinstance(item.get("id"), str)}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSONL output from heph chat ask --jsonl")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the chat_event_expectation.json scaffold.",
    )
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Omit scaffold known_limits after the extracted evidence has been reviewed.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    events_path = cast("Path", args.events).expanduser().resolve()
    output_path = cast("Path", args.output).expanduser().resolve()
    try:
        expectation = extract_expectation(events_path, reviewed=cast("bool", args.reviewed))
    except (TypeError, ValueError) as exc:
        print(f"chat expectation extraction error: {exc}", file=sys.stderr)
        return 2
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(expectation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
