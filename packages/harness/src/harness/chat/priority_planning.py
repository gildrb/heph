"""Priority retrieval planning policy."""

from __future__ import annotations

from dataclasses import dataclass

from harness.chat.turn_contract import (
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.documents.state import DocumentAction


@dataclass(frozen=True, slots=True)
class _PriorityRetrievalState:
    strategy: str
    query: str | None


def _priority_retrieval_state(
    plan: DocumentTurnPlan,
    contract: TurnContract,
    *,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _PriorityRetrievalState:
    if not _priority_reuse_should_retrieve_current_request(
        plan,
        contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return _PriorityRetrievalState(retrieval_strategy, retrieval_query)
    return _PriorityRetrievalState(
        RETRIEVAL_STRATEGY_RETRIEVE,
        _priority_current_request_query(plan, contract, retrieval_query),
    )


def _priority_reuse_should_retrieve_current_request(
    plan: DocumentTurnPlan,
    contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    if plan.action is not DocumentAction.PRIORITY:
        return False
    if retrieval_strategy != RETRIEVAL_STRATEGY_REUSE_PRIOR:
        return False
    return not contract.prior_answer_reference


def _priority_current_request_query(
    plan: DocumentTurnPlan,
    contract: TurnContract,
    fallback: str | None,
) -> str | None:
    if plan.retrieval_query:
        return plan.retrieval_query
    if contract.canonical_request:
        return contract.canonical_request
    return fallback
