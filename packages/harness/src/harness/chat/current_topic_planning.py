"""Current-topic retrieval planning policy."""

from __future__ import annotations

from dataclasses import dataclass

from harness.chat.turn_contract import (
    ANSWER_MODE_FROM_EVIDENCE,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from harness.chat.turn_predicates import _contract_followup_target
from harness.chat.turn_query import (
    _best_current_request_query,
    _normalized_query_terms,
    _same_normalized_text,
)

_FRESH_CURRENT_TOPIC_REQUEST_MIN_TERMS = 3
_CURRENT_TOPIC_QUERY_INTENTS = frozenset({"source_qa", "topic_presentation"})
_CURRENT_TOPIC_QUERY_BLOCKED_STRATEGIES = frozenset(
    {
        RETRIEVAL_STRATEGY_NONE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
    }
)


@dataclass(frozen=True, slots=True)
class _CurrentTopicRetrievalState:
    strategy: str
    query: str | None


def _current_topic_retrieval_state(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _CurrentTopicRetrievalState:
    current_topic_query = _stabilized_current_topic_query(
        contract,
        retrieval_query,
        retrieval_strategy=retrieval_strategy,
    )
    if current_topic_query == retrieval_query:
        return _CurrentTopicRetrievalState(retrieval_strategy, retrieval_query)
    return _CurrentTopicRetrievalState(
        _current_topic_retrieval_strategy(contract, prior_contract),
        current_topic_query,
    )


def _current_topic_retrieval_strategy(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> str:
    if _source_followup_has_prior_evidence(contract, prior_contract):
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR
    return RETRIEVAL_STRATEGY_RETRIEVE


def _source_followup_has_prior_evidence(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> bool:
    if prior_contract is None:
        return False
    if not prior_contract.evidence_refs:
        return False
    if not contract.is_followup:
        return False
    return contract.resolved_intent == "source_qa"


def _stabilized_current_topic_query(
    contract: TurnContract,
    retrieval_query: str | None,
    *,
    retrieval_strategy: str,
) -> str | None:
    if _expanded_prior_source_query_should_stay(
        contract,
        retrieval_query,
        retrieval_strategy=retrieval_strategy,
    ):
        return retrieval_query
    if not _contract_can_choose_current_topic_query(
        contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return retrieval_query
    return _current_topic_query_for_contract(contract, retrieval_query)


def _expanded_prior_source_query_should_stay(
    contract: TurnContract,
    retrieval_query: str | None,
    *,
    retrieval_strategy: str,
) -> bool:
    return (
        contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and bool(retrieval_query)
        and not _same_normalized_text(retrieval_query, contract.original_user_input)
    )


def _contract_can_choose_current_topic_query(
    contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    if not contract.is_followup:
        return False
    if contract.resolved_intent not in _CURRENT_TOPIC_QUERY_INTENTS:
        return False
    if contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE:
        return False
    if contract.prior_answer_reference:
        return False
    return retrieval_strategy not in _CURRENT_TOPIC_QUERY_BLOCKED_STRATEGIES


def _current_topic_query_for_contract(
    contract: TurnContract,
    retrieval_query: str | None,
) -> str | None:
    current_query = contract.canonical_request
    if not current_query:
        return retrieval_query
    if not retrieval_query:
        return current_query
    request_terms = _normalized_query_terms(contract.original_user_input)
    if not request_terms:
        return retrieval_query
    return _best_current_request_query(
        request_terms,
        original_text=contract.original_user_input,
        candidates=(
            retrieval_query,
            current_query,
            _contract_followup_target(contract),
        ),
        fresh_request_min_terms=_FRESH_CURRENT_TOPIC_REQUEST_MIN_TERMS,
    )
