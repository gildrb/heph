"""Overview retrieval planning policy."""

from __future__ import annotations

from harness.chat.turn_contract import (
    ANSWER_FORMAT_PLAIN,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    TurnContract,
)
from harness.chat.turn_contract_checks import _contract_has_specific_material_target
from harness.chat.turn_query import _lacks_retrievable_content
from harness.study.prompt_plans import LearningTurnPlan


def _contract_requires_overview_sampling(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    if contract.resolved_intent != "material_overview":
        return False
    if _contract_is_plain_prior_transform(contract):
        return False
    if contract.answer_format != ANSWER_FORMAT_PLAIN:
        return True
    if _contract_has_specific_material_target(contract):
        return False
    return _plain_overview_scope_requires_sampling(contract, prior_contract)


def _plain_overview_scope_requires_sampling(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> bool:
    if not contract.is_followup:
        return True
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW:
        return True
    return not _overview_followup_can_reuse_prior_evidence(contract, prior_contract)


def _contract_is_plain_prior_transform(contract: TurnContract) -> bool:
    return (
        contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
    )


def _overview_followup_can_reuse_prior_evidence(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> bool:
    if not contract.is_followup:
        return False
    if prior_contract is None:
        return False
    return bool(prior_contract.evidence_refs)


def _overview_retrieval_surface(
    plan: LearningTurnPlan,
    contract: TurnContract,
    fallback: str | None,
) -> str | None:
    candidates = _overview_retrieval_candidates(plan, contract, fallback)
    return _first_retrievable_overview_surface(candidates)


def _overview_retrieval_candidates(
    plan: LearningTurnPlan,
    contract: TurnContract,
    fallback: str | None,
) -> tuple[str | None, ...]:
    return (
        contract.retrieval_query,
        fallback or "",
        contract.canonical_request,
        contract.original_user_input,
        plan.retrieval_query or "",
        plan.original_user_input,
    )


def _first_retrievable_overview_surface(candidates: tuple[str | None, ...]) -> str | None:
    for candidate in candidates:
        if candidate and not _lacks_retrievable_content(candidate):
            return candidate
    return None
