"""Cue filtering policy for compact overview fallback replies."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from hephaion.chat.overview_topics import (
    _OVERVIEW_FORMULA_RE,
    _overview_heading_looks_like_metadata,
    _overview_topic_is_too_short_or_generic,
    _overview_topic_is_useful,
)
from hephaion.chat.turn_query import (
    _letter_words,
    _looks_like_name_word,
    _looks_like_sentence,
)


def _overview_fallback_cue_is_substantive(cue: str) -> bool:
    if _overview_fallback_cue_is_rejected(cue):
        return False
    words = tuple(re.findall(r"\b[\w'-]+\b", cue))
    if _looks_like_sentence(cue):
        return _overview_sentence_cue_is_substantive(words)
    return _overview_fragment_cue_is_substantive(cue, words)


def _overview_fallback_cue_is_rejected(cue: str) -> bool:
    if not _overview_cue_is_useful(cue):
        return True
    return (
        _overview_cue_looks_like_byline(cue)
        or _overview_cue_is_symbolic_fragment(cue)
        or _overview_starts_with_sentence_fragment(cue)
    )


def _overview_sentence_cue_is_substantive(words: Sequence[str]) -> bool:
    return len(words) >= 3 and _overview_cue_has_content_word(words)


def _overview_fragment_cue_is_substantive(cue: str, words: Sequence[str]) -> bool:
    if _overview_fragment_cue_has_separator_or_symbol(cue):
        return False
    return len(words) >= 6


def _overview_fragment_cue_has_separator_or_symbol(cue: str) -> bool:
    return "," in cue or ";" in cue or any(_overview_symbolic_char(char) for char in cue)


def _overview_cue_looks_like_byline(cue: str) -> bool:
    words = _letter_words(cue)
    if len(words) < 4:
        return False
    return _overview_cue_is_name_dense(words) or _overview_cue_has_multiple_name_segments(cue)


def _overview_cue_is_name_dense(words: Sequence[str]) -> bool:
    if len(words) < 6:
        return False
    name_like = sum(1 for word in words if _looks_like_name_word(word))
    return name_like / len(words) >= 0.8


def _overview_cue_has_multiple_name_segments(cue: str) -> bool:
    segments = _overview_name_segments(cue)
    name_segments = sum(1 for segment in segments if _looks_like_person_name_segment(segment))
    return bool(segments) and name_segments >= 2 and name_segments / len(segments) >= 0.6


def _overview_name_segments(cue: str) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(_letter_words(segment)) for segment in re.split(r"[,;/]", cue) if segment.strip()
    )


def _looks_like_person_name_segment(words: Sequence[str]) -> bool:
    return 1 <= len(words) <= 3 and all(_looks_like_name_word(word) for word in words)


def _overview_cue_is_symbolic_fragment(cue: str) -> bool:
    characters = tuple(char for char in cue if not char.isspace())
    if not characters:
        return True
    symbolic = sum(1 for char in characters if _overview_symbolic_char(char))
    if symbolic >= 3 and symbolic / len(characters) >= 0.08:
        return True
    words = _letter_words(cue)
    return bool(words) and symbolic >= len(words)


def _overview_symbolic_char(char: str) -> bool:
    return unicodedata.category(char) == "Sm" or char in "<>=|^_{}[]()"


def _overview_cue_has_content_word(words: Sequence[str]) -> bool:
    return any(sum(char.isalpha() for char in word) >= 6 for word in words)


def _overview_cue_is_useful(cue: str) -> bool:
    normalized = " ".join(cue.casefold().split())
    if not normalized:
        return False
    words = normalized.split()
    if len(words) < 3 and not _overview_topic_is_useful(cue):
        return False
    if (
        _overview_heading_looks_like_metadata(cue)
        or _overview_topic_is_too_short_or_generic(normalized)
        or _OVERVIEW_FORMULA_RE.search(cue) is not None
    ):
        return False
    return not _overview_cue_looks_like_byline(cue)


def _overview_starts_with_sentence_fragment(text: str) -> bool:
    first_alpha = next((char for char in text.lstrip() if char.isalpha()), "")
    return bool(first_alpha) and first_alpha.islower()
