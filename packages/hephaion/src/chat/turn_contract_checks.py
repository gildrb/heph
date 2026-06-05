"""Turn-contract structural checks shared across chat services."""

from __future__ import annotations

from collections.abc import Sequence

from study.prompt_plans import LearningTurnPlan
from study.state import LearningAction

from chat.turn_contract import (
    ANSWER_FORMAT_LIST,
    ANSWER_FORMAT_PLAIN,
    ANSWER_FORMAT_TABLE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    TurnContract,
)
from chat.turn_predicates import (
    _contract_followup_target,
    _overview_turn,
)


def _contract_has_specific_material_target(contract: TurnContract) -> bool:
    return (
        contract.resolved_intent == "material_overview"
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and bool(_contract_followup_target(contract))
        and bool(contract.canonical_request)
    )


def _contract_requests_table(contract: TurnContract | None) -> bool:
    return contract is not None and contract.answer_format == ANSWER_FORMAT_TABLE


def _contract_requests_list(contract: TurnContract | None) -> bool:
    return contract is not None and contract.answer_format == ANSWER_FORMAT_LIST


def _material_overview_turn(
    plan: LearningTurnPlan,
    contract: TurnContract | None = None,
) -> bool:
    if contract is None:
        return _overview_turn(plan)
    if contract is not None and contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }:
        return (
            contract.resolved_intent == "material_overview"
            and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
            and not contract.prior_turn_evidence_refs
        )
    if _overview_turn(plan):
        return True
    return (
        contract.resolved_intent == "material_overview"
        and plan.action is LearningAction.PRESENT
        and not _contract_has_specific_material_target(contract)
        and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    )


def _plan_requires_citations(plan: LearningTurnPlan | None) -> bool:
    if plan is None:
        return False
    if plan.action is LearningAction.CHAT:
        return bool(
            plan.retrieval_query
            or plan.evidence_refs
            or plan.use_expected_source_refs
            or plan.requires_direct_evidence
        )
    return plan.action in {
        LearningAction.PRESENT,
        LearningAction.SOURCE_QA,
        LearningAction.PRIORITY,
        LearningAction.REVIEW,
        LearningAction.CALIBRATE,
        LearningAction.ASSESS,
        LearningAction.HINT,
        LearningAction.SIMPLIFY,
    }


def _intent_contract_refs_text(refs: Sequence[str], *, limit: int = 4) -> str:
    if not refs:
        return "none"
    visible = ", ".join(refs[:limit])
    remaining = len(refs) - limit
    if remaining <= 0:
        return visible
    return f"{visible}, +{remaining} more"
