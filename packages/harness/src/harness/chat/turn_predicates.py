"""Shared turn predicates and text utilities used across chat submodules."""

from __future__ import annotations

import re

from harness.chat.evidence import ResolvedTurnPlan
from harness.chat.turn_contract import (
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    TurnContract,
)
from harness.rag.context import TurnEvidence
from harness.study.prompt_plans import LearningTurnPlan
from harness.study.state import LearningAction


def _overview_turn(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.PRESENT and (
        plan.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW or plan.uses_overview_sampling
    )


def _trace_excerpt(text: str, *, limit: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _count_label(count: int, singular: str) -> str:
    return f"{count} {singular}{'' if count == 1 else 's'}"


def _plural(word: str, count: int) -> str:
    return f"{word}{'' if count == 1 else 's'}"


def _material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1]
    return f"@{name or source}"


def _readable_material_label(source: str) -> str:
    name = source.rsplit("/", maxsplit=1)[-1] or source
    stem = name.rsplit(".", maxsplit=1)[0]
    readable = re.sub(r"[-_]+", " ", stem).strip()
    return readable or name


def _visible_turn_evidence(resolved: object) -> TurnEvidence | None:
    if not isinstance(resolved, ResolvedTurnPlan):
        return None
    plan = resolved.learning_plan
    if plan is not None and plan.action is LearningAction.CALIBRATE:
        return None
    return resolved.turn_evidence


def _stored_turn_evidence(resolved: object) -> TurnEvidence | None:
    if not isinstance(resolved, ResolvedTurnPlan):
        return None
    if (
        resolved.learning_plan is not None
        and resolved.learning_plan.action is LearningAction.CALIBRATE
    ):
        return resolved.turn_evidence
    return _visible_turn_evidence(resolved)


def _contract_followup_target(contract: TurnContract) -> str:
    target = contract.followup_target.strip()
    if target.casefold() == RETRIEVAL_STRATEGY_NONE:
        return ""
    return target


def _no_match_request_text(contract: TurnContract | None) -> str:
    if contract is None:
        return "this request"
    return (
        contract.canonical_request
        or _contract_followup_target(contract)
        or contract.original_user_input
        or "this request"
    )
