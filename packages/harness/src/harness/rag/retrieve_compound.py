"""Compound-query splitting and result merging for retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.rag.retrieval_types import ScoredChunk
from harness.rag.scoring import tokenize

_COMPOUND_SPLIT_RE = re.compile(r"\s*(?:;|,\s+and\s+|\band\b)\s*", re.IGNORECASE)
_MIN_COMPOUND_QUERY_TOKENS = 3
_MAX_COMPOUND_QUERY_PARTS = 4


@dataclass(frozen=True, slots=True)
class _CompoundMergeEntry:
    scored_chunk: ScoredChunk
    best_score: float
    first_list_index: int
    best_rank: int


def _compound_query_variants(query: str) -> list[str]:
    normalized = " ".join(query.split())
    if not normalized:
        return [query]
    query_parts = _compound_focus_parts(normalized)
    if len(query_parts) < 2:
        return [normalized]
    return [normalized, *query_parts[:_MAX_COMPOUND_QUERY_PARTS]]


def _compound_focus_parts(raw_focus: str) -> list[str]:
    return [
        part
        for raw_part in _COMPOUND_SPLIT_RE.split(raw_focus)
        if len(tokenize(part := _normalized_compound_part(raw_part))) >= _MIN_COMPOUND_QUERY_TOKENS
    ]


def _normalized_compound_part(raw_part: str) -> str:
    normalized = " ".join(raw_part.strip(" \t\n\r,;:.?!").split())
    if ":" in normalized:
        _prefix, _separator, normalized = normalized.partition(":")
    return normalized.strip(" \t\n\r,;:.?!")


def _merge_compound_query_results(
    ranked_lists: list[list[ScoredChunk]],
    top_k: int,
) -> list[ScoredChunk]:
    entries: dict[tuple[str, int], _CompoundMergeEntry] = {}
    for list_index, ranked in enumerate(ranked_lists):
        _merge_ranked_entries(entries, ranked, list_index)

    promoted_keys = _promoted_compound_keys(ranked_lists)
    promoted_entries = _promoted_compound_entries(entries, promoted_keys)
    remaining_entries = _remaining_compound_entries(entries, promoted_keys)
    merged = [
        *promoted_entries,
        *[_entry_to_scored_chunk(entry) for entry in remaining_entries],
    ]
    return merged[:top_k]


def _merge_ranked_entries(
    entries: dict[tuple[str, int], _CompoundMergeEntry],
    ranked: list[ScoredChunk],
    list_index: int,
) -> None:
    for rank, scored_chunk in enumerate(ranked):
        key = _scored_chunk_key(scored_chunk)
        existing = entries.get(key)
        entries[key] = (
            _new_compound_entry(scored_chunk, list_index, rank)
            if existing is None
            else _updated_compound_entry(existing, scored_chunk, list_index, rank)
        )


def _promoted_compound_keys(ranked_lists: list[list[ScoredChunk]]) -> list[tuple[str, int]]:
    promoted_keys: list[tuple[str, int]] = []
    promoted_seen: set[tuple[str, int]] = set()
    for ranked in ranked_lists[1:]:
        if not ranked:
            continue
        promoted_key = _scored_chunk_key(ranked[0])
        if promoted_key in promoted_seen:
            continue
        promoted_keys.append(promoted_key)
        promoted_seen.add(promoted_key)
    return promoted_keys


def _promoted_compound_entries(
    entries: dict[tuple[str, int], _CompoundMergeEntry],
    promoted_keys: list[tuple[str, int]],
) -> list[ScoredChunk]:
    return [_entry_to_scored_chunk(entries[key]) for key in promoted_keys if key in entries]


def _remaining_compound_entries(
    entries: dict[tuple[str, int], _CompoundMergeEntry],
    promoted_keys: list[tuple[str, int]],
) -> list[_CompoundMergeEntry]:
    promoted_key_set = set(promoted_keys)
    remaining_entries = [entry for key, entry in entries.items() if key not in promoted_key_set]
    remaining_entries.sort(key=_compound_entry_sort_key, reverse=True)
    return remaining_entries


def _compound_entry_sort_key(entry: _CompoundMergeEntry) -> tuple[float, int, int]:
    return entry.best_score, -entry.best_rank, -entry.first_list_index


def _new_compound_entry(
    scored_chunk: ScoredChunk,
    list_index: int,
    rank: int,
) -> _CompoundMergeEntry:
    return _CompoundMergeEntry(
        scored_chunk=scored_chunk,
        best_score=scored_chunk.score,
        first_list_index=list_index,
        best_rank=rank,
    )


def _updated_compound_entry(
    existing: _CompoundMergeEntry,
    scored_chunk: ScoredChunk,
    list_index: int,
    rank: int,
) -> _CompoundMergeEntry:
    return _CompoundMergeEntry(
        scored_chunk=existing.scored_chunk,
        best_score=max(existing.best_score, scored_chunk.score),
        first_list_index=min(existing.first_list_index, list_index),
        best_rank=min(existing.best_rank, rank),
    )


def _scored_chunk_key(scored_chunk: ScoredChunk) -> tuple[str, int]:
    return scored_chunk.chunk.source, scored_chunk.chunk.index


def _entry_to_scored_chunk(entry: _CompoundMergeEntry) -> ScoredChunk:
    return ScoredChunk(chunk=entry.scored_chunk.chunk, score=entry.best_score)
