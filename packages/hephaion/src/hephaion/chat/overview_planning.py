"""Overview retrieval planning policy."""

from __future__ import annotations

from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_PLAIN,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    TurnContract,
)
from hephaion.chat.turn_contract_checks import _contract_has_specific_material_target


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
