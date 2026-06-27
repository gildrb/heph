"""Shared text filters for evidence retrieval and sampling."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from html import unescape

from harness.rag.retrieval_types import ScoredChunk
from harness.rag.scoring import tokenize

_CONTACT_OR_URL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+)", re.IGNORECASE)
_DUPLICATE_LOW_CONTENT_MAX_CHARS = 240
_DUPLICATE_LOW_CONTENT_MIN_SOURCES = 2


def filter_low_content_chunks(scored: list[ScoredChunk]) -> list[ScoredChunk]:
    content_chunks = [item for item in scored if not chunk_is_low_content(item.chunk.text)]
    content_chunks = _filter_repeated_short_duplicate_chunks(content_chunks)
    return content_chunks or scored


def _filter_repeated_short_duplicate_chunks(scored: list[ScoredChunk]) -> list[ScoredChunk]:
    duplicate_signatures = _repeated_short_duplicate_signatures(scored)
    if not duplicate_signatures:
        return scored
    return [
        item
        for item in scored
        if _short_duplicate_signature(item.chunk.text) not in duplicate_signatures
    ]


def _repeated_short_duplicate_signatures(scored: Sequence[ScoredChunk]) -> set[str]:
    sources_by_signature: dict[str, set[str]] = {}
    for item in scored:
        signature = _short_duplicate_signature(item.chunk.text)
        if signature:
            sources_by_signature.setdefault(signature, set()).add(item.chunk.source)
    return {
        signature
        for signature, sources in sources_by_signature.items()
        if len(sources) >= _DUPLICATE_LOW_CONTENT_MIN_SOURCES
    }


def _short_duplicate_signature(text: str) -> str:
    normalized = " ".join(unescape(text).casefold().split())
    if not normalized or len(normalized) > _DUPLICATE_LOW_CONTENT_MAX_CHARS:
        return ""
    return normalized


def chunk_is_low_content(text: str) -> bool:
    normalized = " ".join(unescape(text).split())
    if not normalized:
        return True
    alnum_count = sum(character.isalnum() for character in normalized)
    if alnum_count == 0:
        return True
    if _short_year_dominated_text(normalized):
        return True
    if _CONTACT_OR_URL_RE.search(normalized) and _low_content_density(normalized):
        return True
    punctuation_count = sum(character in ".,;:!?()[]{}<>/\\|" for character in normalized)
    alpha_count = sum(character.isalpha() for character in normalized)
    return len(normalized) <= _DUPLICATE_LOW_CONTENT_MAX_CHARS and punctuation_count > alpha_count


def _short_year_dominated_text(text: str) -> bool:
    tokens = tokenize(text)
    return bool(
        len(tokens) <= 8
        and any(token.isdigit() and len(token) == 4 for token in tokens)
        and not overview_chunk_has_structural_signal(text)
    )


def _low_content_density(text: str) -> bool:
    words = tokenize(text)
    if len(words) <= 8:
        return True
    url_chars = sum(len(match.group(0)) for match in _CONTACT_OR_URL_RE.finditer(text))
    return url_chars / max(len(text), 1) >= 0.35


def overview_chunk_has_structural_signal(text: str) -> bool:
    return any(_overview_character_is_structural_signal(character) for character in text)


def _overview_character_is_structural_signal(character: str) -> bool:
    return unicodedata.category(character) == "Sm" or character in "=<>"


__all__ = [
    "chunk_is_low_content",
    "filter_low_content_chunks",
    "overview_chunk_has_structural_signal",
]
