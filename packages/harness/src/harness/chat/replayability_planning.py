"""Replayability policy for prior-turn follow-up state."""

from __future__ import annotations

from harness.chat.citation_patterns import _OVERVIEW_CITATION_ID_RE
from harness.chat.turn_contract import (
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from harness.chat.turn_query import _content_terms

_FRESH_REPLAYABLE_FOLLOWUP_MIN_TERMS = 3


def _unreplayable_followup_current_query(contract: TurnContract) -> str:
    if _contract_can_use_own_request_surface(contract):
        return contract.canonical_request or contract.original_user_input
    return ""


def _contract_can_use_own_request_surface(contract: TurnContract) -> bool:
    if not contract.is_followup:
        return True
    if not contract.prior_turn_original_user_input:
        return True
    return _followup_has_fresh_request_terms(contract)


def _followup_has_fresh_request_terms(contract: TurnContract) -> bool:
    content_terms = _content_terms(contract.original_user_input)
    return len(content_terms) >= _FRESH_REPLAYABLE_FOLLOWUP_MIN_TERMS


def _contract_has_replayable_grounding_surface(contract: TurnContract) -> bool:
    return bool(contract.prior_turn_evidence_refs) or (
        _OVERVIEW_CITATION_ID_RE.search(contract.prior_answer_excerpt) is not None
    )


def _contract_needs_prior_replay_state(contract: TurnContract) -> bool:
    return (
        contract.is_followup
        or contract.prior_answer_reference
        or contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
        or contract.retrieval_strategy
        in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
    )
