"""Structural validation policy for grounded material overview replies."""

from __future__ import annotations

import difflib
import re
from collections.abc import Sequence
from dataclasses import dataclass

from harness.agent.citation import verify_citations
from harness.chat.citation_patterns import (
    _OVERVIEW_CITATION_BRACKET_RE,
    _OVERVIEW_CITATION_ID_RE,
    _OVERVIEW_CITATION_TOKEN_RE,
)
from harness.chat.overview_cues import _overview_starts_with_sentence_fragment
from harness.chat.overview_topics import _OVERVIEW_LINE_MARKER_RE
from harness.chat.reply_text import (
    _has_uncited_tail_after_last_citation,
)
from harness.chat.turn_contract import TurnContract
from harness.chat.turn_contract_checks import (
    _contract_requests_table,
    _material_overview_turn,
)
from harness.rag.context import TurnEvidence
from harness.rag.scoring import tokenize
from harness.study.prompt_plans import LearningTurnPlan

_MARKDOWN_TABLE_SEPARATOR_LINE_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_INLINE_LIST_MARKER_RE = re.compile(r"(?m)^\s*\S.*:\s*(?:[-*+]|\d+[.)])\s+\S")
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MAX_WORDS = 110
_OVERVIEW_MAX_CHARS = 700
_OVERVIEW_MAX_TABLE_CHARS = 1800
_OVERVIEW_MAX_UNCITED_LEAD_WORDS = 32
_OVERVIEW_MAX_UNCITED_LEAD_CHARS = 260
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MAX_CITATIONS = 8
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES = 5
_OVERVIEW_MAX_LIST_ITEMS = 3
_OVERVIEW_MAX_TABLE_ROWS = 8
_OVERVIEW_EXTRACTIVE_MIN_SPANS = 2
_OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS = 3
_OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO = 0.34


@dataclass(frozen=True, slots=True)
class _OverviewShapeMetrics:
    citation_ids: tuple[str, ...]
    words: tuple[str, ...]
    has_table: bool
    max_chars: int


def _valid_overview_model_reply(
    reply: str,
    evidence: TurnEvidence,
    *,
    allow_table: bool = False,
    allow_list: bool = False,
) -> bool:
    if not reply:
        return False
    if allow_table and not _contains_markdown_table(reply):
        return False
    if allow_list and _list_item_count(reply) == 0:
        return False
    verification = verify_citations(reply, evidence)
    return (
        verification.has_citations
        and verification.all_verified
        and not _overview_answer_has_bad_shape(reply, evidence, allow_table=allow_table)
    )


def _needs_overview_fallback(
    plan: LearningTurnPlan,
    raw_reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if not _material_overview_turn(plan, contract) or evidence is None or not evidence.items:
        return False
    verification = verify_citations(raw_reply, evidence)
    if not verification.has_citations or not verification.all_verified:
        return True
    return _overview_answer_has_bad_shape(
        raw_reply,
        evidence,
        allow_table=_contract_requests_table(contract),
    )


def _overview_answer_has_bad_shape(
    raw_reply: str,
    evidence: TurnEvidence | None = None,
    *,
    allow_table: bool = False,
) -> bool:
    """Reject overview replies that are too thin, too noisy, or under-grounded."""
    metrics = _overview_shape_metrics(raw_reply, allow_table=allow_table)
    if _overview_table_requirement_is_bad(metrics, allow_table=allow_table):
        return True
    if _overview_length_budget_is_bad(raw_reply, metrics):
        return True
    if _overview_layout_limits_are_bad(raw_reply, metrics, evidence):
        return True
    return _overview_grounding_requirements_are_bad(metrics, evidence)


def _overview_shape_metrics(raw_reply: str, *, allow_table: bool) -> _OverviewShapeMetrics:
    has_table = _contains_markdown_table(raw_reply)
    max_chars = _OVERVIEW_MAX_TABLE_CHARS if has_table and allow_table else _OVERVIEW_MAX_CHARS
    return _OverviewShapeMetrics(
        citation_ids=_overview_citation_ids(raw_reply),
        words=tuple(re.findall(r"\b[\w'-]+\b", raw_reply)),
        has_table=has_table,
        max_chars=max_chars,
    )


def _overview_table_requirement_is_bad(
    metrics: _OverviewShapeMetrics,
    *,
    allow_table: bool,
) -> bool:
    return allow_table and not metrics.has_table


def _overview_length_budget_is_bad(raw_reply: str, metrics: _OverviewShapeMetrics) -> bool:
    return len(raw_reply) > metrics.max_chars


def _overview_layout_limits_are_bad(
    raw_reply: str,
    metrics: _OverviewShapeMetrics,
    evidence: TurnEvidence | None,
) -> bool:
    if not metrics.has_table and _plain_overview_shape_is_bad(
        raw_reply,
        metrics.words,
        metrics.citation_ids,
        evidence,
    ):
        return True
    if metrics.has_table and _markdown_table_row_count(raw_reply) > _OVERVIEW_MAX_TABLE_ROWS:
        return True
    return _list_item_count(raw_reply) > _OVERVIEW_MAX_LIST_ITEMS


def _overview_grounding_requirements_are_bad(
    metrics: _OverviewShapeMetrics,
    evidence: TurnEvidence | None,
) -> bool:
    if len(metrics.citation_ids) < _OVERVIEW_MIN_CITATIONS:
        return True
    if not metrics.has_table and len(metrics.words) < _OVERVIEW_MIN_WORDS:
        return True
    return evidence is not None and not _overview_covers_enough_sources(
        metrics.citation_ids,
        evidence,
    )


def _plain_overview_shape_is_bad(
    raw_reply: str,
    words: Sequence[str],
    citation_ids: tuple[str, ...],
    evidence: TurnEvidence | None,
) -> bool:
    return (
        len(words) > _OVERVIEW_MAX_WORDS
        or _has_uncited_tail_after_last_citation(raw_reply)
        or len(citation_ids) > _OVERVIEW_MAX_CITATIONS
        or _overview_starts_with_sentence_fragment(raw_reply)
        or _overview_has_inline_list_marker(raw_reply)
        or _overview_has_long_uncited_lead(raw_reply)
        or (evidence is not None and _overview_is_extractive_inventory(raw_reply, evidence))
    )


def _overview_has_long_uncited_lead(raw_reply: str) -> bool:
    match = _OVERVIEW_CITATION_ID_RE.search(raw_reply)
    if match is None:
        return False
    lead = raw_reply[: match.start()].strip()
    if len(lead) > _OVERVIEW_MAX_UNCITED_LEAD_CHARS:
        return True
    return len(re.findall(r"\b[\w'-]+\b", lead)) > _OVERVIEW_MAX_UNCITED_LEAD_WORDS


def _contains_markdown_table(text: str) -> bool:
    return any(_MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line) for line in text.splitlines())


def _markdown_table_row_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("|"))


def _list_item_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line))


def _overview_has_inline_list_marker(text: str) -> bool:
    return bool(_INLINE_LIST_MARKER_RE.search(text))


def _overview_citation_ids(raw_reply: str) -> tuple[str, ...]:
    ids: list[str] = []
    for bracket in _OVERVIEW_CITATION_BRACKET_RE.finditer(raw_reply):
        ids.extend(
            f"E{match.group('id')}"
            for match in _OVERVIEW_CITATION_TOKEN_RE.finditer(bracket.group("body"))
        )
    return tuple(ids)


def _overview_covers_enough_sources(citation_ids: tuple[str, ...], evidence: TurnEvidence) -> bool:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[citation_id.casefold()]
        for citation_id in citation_ids
        if citation_id.casefold() in source_by_id
    }
    return len(cited_sources) >= _overview_required_distinct_source_count(evidence)


def _overview_is_extractive_inventory(raw_reply: str, evidence: TurnEvidence) -> bool:
    spans = _overview_cited_claim_spans(raw_reply)
    if len(spans) < _OVERVIEW_EXTRACTIVE_MIN_SPANS:
        return False
    copied = sum(1 for span in spans if _overview_span_is_copied(span, evidence))
    return copied >= _OVERVIEW_EXTRACTIVE_MIN_SPANS and (
        copied / len(spans) >= _OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO
    )


def _overview_cited_claim_spans(raw_reply: str) -> tuple[str, ...]:
    spans: list[str] = []
    start = 0
    for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply):
        span = _clean_overview_extract_span(raw_reply[start : match.start()])
        start = match.end()
        if len(tokenize(span)) >= _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
            spans.append(span)
    return tuple(spans)


def _clean_overview_extract_span(span: str) -> str:
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", span.strip())
    return cleaned.strip(" \t\r\n\"'\u201c\u201d\u2018\u2019.,;:")


def _overview_span_is_copied(span: str, evidence: TurnEvidence) -> bool:
    if len(tokenize(span)) < _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
        return False
    normalized_span = _overview_copy_normalized_text(span)
    return any(
        _overview_normalized_span_is_copied(
            normalized_span,
            _overview_copy_normalized_text(item.content),
        )
        for item in evidence.items
    )


def _overview_normalized_span_is_copied(span: str, evidence_text: str) -> bool:
    if not span or not evidence_text:
        return False
    if span in evidence_text:
        return True
    if len(span) < 32:
        return False
    return difflib.SequenceMatcher(a=span, b=evidence_text).ratio() >= 0.82


def _overview_copy_normalized_text(text: str) -> str:
    return " ".join(tokenize(text))


def _overview_required_distinct_source_count(evidence: TurnEvidence) -> int:
    available_source_count = len({item.source for item in evidence.items})
    if available_source_count <= _OVERVIEW_MIN_DISTINCT_SOURCES:
        return available_source_count
    proportional_floor = (available_source_count + 1) // 2
    return min(
        available_source_count,
        _OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES,
        max(_OVERVIEW_MIN_DISTINCT_SOURCES, proportional_floor),
    )
