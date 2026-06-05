"""Structural topic and heading helpers for overview replies."""

from __future__ import annotations

import re
from collections.abc import Sequence
from html import unescape

from rag.context import EvidenceChunk, TurnEvidence

from chat.turn_predicates import _trace_excerpt
from chat.turn_query import _letter_words, _looks_like_sentence

_OVERVIEW_CONTACT_OR_URL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+)", re.IGNORECASE)
_OVERVIEW_DATE_LINE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-zÄÖÜäöüß]+\s+\d{4}\b|\b\d{4}\b")
_OVERVIEW_FORMULA_RE = re.compile(r"(?:\\[a-zA-Z]+|[$=∑∫√≤≥→↦∀∃])")
_OVERVIEW_LINE_MARKER_RE = re.compile(r"^[#*\-\d.\s:;()\[\]]+")


def _overview_topic_normalization_context(
    evidence: TurnEvidence,
    user_input: str,
    *,
    rejected_reply: str = "",
) -> str:
    lines = [
        f"User request: {user_input.strip() or '(none)'}",
        "Task rules:",
        "- Treat title pages, logistics, and boilerplate as non-substantive unless requested.",
        "- Infer substantive learning material by semantic context, not hardcoded keywords.",
    ]
    if rejected_reply.strip():
        lines.extend(
            (
                "",
                "Rejected draft to repair:",
                _trace_excerpt(rejected_reply, limit=1400),
            )
        )
    lines.append("Evidence excerpts:")
    for item in evidence.items[:12]:
        heading = item.chunk.heading or "none"
        compact_text = " ".join(unescape(item.content).split())
        if len(compact_text) > 700:
            compact_text = f"{compact_text[:699]}…"
        lines.extend(
            (
                "",
                f"Evidence {item.evidence_id}",
                f"Source: {item.source}",
                f"Heading: {heading}",
                f"Text: {compact_text}",
            )
        )
    return "\n".join(lines)


def _overview_heading_candidates(item: EvidenceChunk) -> tuple[str, ...]:
    candidates = (item.chunk.heading, *_overview_markdown_headings(item.content))
    return tuple(topic for candidate in candidates if (topic := _clean_overview_line(candidate)))


def _overview_heading_looks_like_metadata(topic: str) -> bool:
    if _OVERVIEW_CONTACT_OR_URL_RE.search(topic) or _OVERVIEW_DATE_LINE_RE.search(topic):
        return True
    if _looks_like_sentence(topic):
        return False
    return _overview_heading_is_sparse_title_block(topic)


def _overview_heading_is_sparse_title_block(topic: str) -> bool:
    words = _letter_words(topic)
    if len(words) < 2:
        return False
    if _overview_heading_has_sparse_characters(topic):
        return True
    return _overview_heading_has_sparse_label_shape(topic, words)


def _overview_heading_has_sparse_characters(topic: str) -> bool:
    return sum(char.isalnum() for char in topic) < 4


def _overview_heading_has_sparse_label_shape(topic: str, words: Sequence[str]) -> bool:
    return (
        len(words) <= 6
        and _overview_heading_mostly_title_labels(words)
        and _overview_heading_has_low_text_density(topic, words)
    )


def _overview_heading_mostly_title_labels(words: Sequence[str]) -> bool:
    title_case_count = sum(1 for word in words if word[:1].isupper() and not word.isupper())
    return title_case_count / len(words) >= 0.8


def _overview_heading_has_low_text_density(topic: str, words: Sequence[str]) -> bool:
    punctuation_count = sum(1 for char in topic if char in ",;:!?()[]{}")
    separator_count = sum(1 for char in topic if char in "-_/|")
    return punctuation_count + separator_count >= max(2, len(words) // 2)


def _overview_markdown_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in unescape(text).splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = _clean_overview_line(stripped)
        if heading:
            headings.append(heading)
    return headings


def _normalize_overview_topic(topic: str) -> str:
    return " ".join(topic.casefold().split())


def _overview_topic_is_useful(topic: str) -> bool:
    normalized = " ".join(topic.casefold().split())
    if _overview_topic_text_is_invalid(topic, normalized):
        return False
    return len(normalized.split()) <= 5


def _overview_topic_text_is_invalid(topic: str, normalized: str) -> bool:
    return any(
        (
            _overview_topic_is_too_short_or_generic(normalized),
            _OVERVIEW_FORMULA_RE.search(topic) is not None,
            _overview_topic_has_sentence_punctuation(topic),
        )
    )


def _overview_topic_is_too_short_or_generic(normalized: str) -> bool:
    words = normalized.split()
    if not words:
        return True
    if len(words) == 1 and sum(char.isalpha() for char in words[0]) < 6:
        return True
    return len(normalized) < 4


def _overview_topic_has_sentence_punctuation(topic: str) -> bool:
    return re.search(r"[.:;!?]|->|:=|=>", topic) is not None


def _overview_content_lines(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip()]


def _clean_overview_line(line: str) -> str:
    cleaned = " ".join(unescape(line).strip().split())
    cleaned = cleaned.replace("[... truncated]", "").strip()
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", cleaned).strip()
    return cleaned.strip(" -:;")


def _trim_overview_cue(line: str, *, limit: int = 120) -> str:
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip(" ,;:.") + "…"
