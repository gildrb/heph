"""Structural query normalization helpers for chat turn planning."""

from __future__ import annotations

import difflib
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from harness.chat.turn_contract import (
    TurnContract,
    TurnIntentResolution,
)
from harness.rag.scoring import tokenize

if TYPE_CHECKING:
    from harness.rag.index import ArmoryIndex


@dataclass(frozen=True, order=True, slots=True)
class _CurrentRequestQueryCandidate:
    term_overlap: int
    specificity: tuple[int, int]
    text: str


def _query_reuses_surface(query: str, surface: str) -> bool:
    surface_terms = _normalized_query_terms(surface)
    if not surface_terms:
        return False
    return _query_term_overlap(query, surface_terms) >= min(2, len(surface_terms))


def _content_terms(text: str) -> frozenset[str]:
    return frozenset(
        term
        for term in _normalized_query_terms(text)
        if len(term) >= 5 and any(char.isalpha() for char in term)
    )


def _semantic_query_specificity(text: str) -> tuple[int, int]:
    normalized = _normalized_query_text(text)
    return (len(normalized.split()), len(normalized))


def _same_normalized_text(left: str, right: str) -> bool:
    return _normalized_query_text(left) == _normalized_query_text(right)


def _normalized_query_text(text: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"\W+", " ", folded.casefold()).strip()


def _normalized_query_terms(text: str) -> frozenset[str]:
    return frozenset(_normalized_query_text(text).split())


def _query_term_overlap(text: str, request_terms: frozenset[str]) -> int:
    return sum(
        1
        for term in _normalized_query_terms(text)
        if any(_query_terms_match(term, request_term) for request_term in request_terms)
    )


def _query_terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if min(len(left), len(right)) < 5:
        return False
    return difflib.SequenceMatcher(a=left, b=right).ratio() >= 0.84


def _lacks_retrievable_content(text: str) -> bool:
    return bool(text.strip()) and not tokenize(text)


def _source_lookup_preserves_user_terms(
    resolution: TurnIntentResolution,
    index: ArmoryIndex | None,
) -> bool:
    lookup_query = resolution.retrieval_query or resolution.canonical_request
    if not lookup_query.strip():
        return True
    query_terms = frozenset(tokenize(lookup_query))
    if not query_terms:
        return False
    if index is not None:
        return _query_has_index_anchor(query_terms, index)
    return False


def _query_has_index_anchor(query_terms: frozenset[str], index: ArmoryIndex) -> bool:
    corpus_terms = _index_query_terms(index)
    return not corpus_terms or any(
        _query_has_matching_term(term, corpus_terms) for term in query_terms
    )


def _index_query_terms(index: ArmoryIndex) -> frozenset[str]:
    return frozenset(
        token
        for document in index.documents
        for chunk in document.chunks
        for token in tokenize(chunk.text)
    )


def _query_has_matching_term(term: str, query_terms: frozenset[str]) -> bool:
    return any(_query_terms_match(term, query_term) for query_term in query_terms)


def _best_current_request_query(
    request_terms: frozenset[str],
    *,
    original_text: str,
    candidates: Sequence[str | None],
    fresh_request_min_terms: int,
) -> str | None:
    scored_candidates = _current_request_query_candidates(request_terms, candidates)
    if not scored_candidates:
        return None
    best = max(scored_candidates)
    if not _query_candidate_matches_original(best, original_text):
        return best.text
    if len(_content_terms(original_text)) >= fresh_request_min_terms:
        return best.text
    semantic_candidates = _semantic_current_request_candidates(
        scored_candidates,
        original_text,
    )
    return max(semantic_candidates).text if semantic_candidates else best.text


def _current_request_query_candidates(
    request_terms: frozenset[str],
    candidates: Sequence[str | None],
) -> tuple[_CurrentRequestQueryCandidate, ...]:
    return tuple(
        _CurrentRequestQueryCandidate(
            _query_term_overlap(candidate, request_terms),
            _semantic_query_specificity(candidate),
            candidate,
        )
        for candidate in candidates
        if candidate
    )


def _semantic_current_request_candidates(
    candidates: Sequence[_CurrentRequestQueryCandidate],
    original_text: str,
) -> tuple[_CurrentRequestQueryCandidate, ...]:
    return tuple(
        candidate
        for candidate in candidates
        if not _query_candidate_matches_original(candidate, original_text)
    )


def _query_candidate_matches_original(
    candidate: _CurrentRequestQueryCandidate,
    original_text: str,
) -> bool:
    return _same_normalized_text(candidate.text, original_text)


def _current_request_introduces_fresh_content(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    fresh_request_min_terms: int,
) -> bool:
    current_terms = _content_terms(contract.original_user_input)
    if not current_terms:
        return False
    prior_terms = _prior_request_context_terms(contract, prior_contract)
    if not prior_terms:
        return len(current_terms) >= fresh_request_min_terms
    fresh_terms = _terms_not_reused_by_prior(current_terms, prior_terms)
    return len(fresh_terms) >= fresh_request_min_terms


def _prior_request_context_terms(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> frozenset[str]:
    return _content_terms(" ".join(_prior_request_context_surfaces(contract, prior_contract)))


def _prior_request_context_surfaces(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> tuple[str, ...]:
    return tuple(
        text
        for text in (
            prior_contract.original_user_input,
            prior_contract.canonical_request,
            prior_contract.retrieval_query,
            " ".join(prior_contract.evidence_refs),
            contract.prior_answer_excerpt,
            contract.prior_turn_original_user_input,
            contract.prior_turn_canonical_request,
            " ".join(contract.prior_turn_evidence_refs),
        )
        if text
    )


def _terms_not_reused_by_prior(
    current_terms: frozenset[str],
    prior_terms: frozenset[str],
) -> tuple[str, ...]:
    return tuple(term for term in current_terms if not _term_reused_by_prior(term, prior_terms))


def _term_reused_by_prior(term: str, prior_terms: frozenset[str]) -> bool:
    return any(_query_terms_match(term, prior_term) for prior_term in prior_terms)


def _corpus_named_material_query(user_input: str, index: ArmoryIndex | None) -> str:
    if index is None:
        return ""
    normalized_user = f" {_normalized_query_text(user_input)} "
    if not normalized_user.strip():
        return ""
    for document in index.documents:
        label = _normalized_source_label(document.source)
        if label and f" {label} " in normalized_user:
            return f"{label} {user_input.strip()}".strip()
    return ""


def _normalized_source_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    stem = name.rsplit(".", maxsplit=1)[0]
    return _normalized_query_text(re.sub(r"[-_]+", " ", stem))


def _letter_words(line: str) -> list[str]:
    words = [word.strip(".,;:()[]{}") for word in line.split()]
    return [word for word in words if any(char.isalpha() for char in word)]


def _looks_like_name_word(word: str) -> bool:
    return word[:1].isupper() and not word.isupper()


def _looks_like_sentence(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?"))
