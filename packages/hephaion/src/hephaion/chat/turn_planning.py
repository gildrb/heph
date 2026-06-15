"""Turn-plan contract reconciliation and retrieval planning."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ai.runtime.conversation import Conversation

from hephaion.chat.citation_patterns import (
    _OVERVIEW_CITATION_ID_RE,
)
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.evidence import evidence_refs as _evidence_refs
from hephaion.chat.followup_retrieval import (
    _contract_has_empty_retrieval_query,
    _contract_has_nonliteral_retrieval_surface,
    _contract_retrieval_query,
    _current_request_query,
    _expanded_prior_followup_query,
    _expanded_prior_should_use_current_request,
    _fresh_current_request_query,
    _stabilized_followup_retrieval,
)
from hephaion.chat.material_state import (
    _EVIDENCE_REQUIRED_ACTIONS,
)
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_PLAIN,
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from hephaion.chat.turn_predicates import (
    _contract_followup_target,
    _overview_turn,
    _trace_excerpt,
)
from hephaion.rag.context import TurnEvidence
from hephaion.study.prompt_plans import LearningTurnPlan
from hephaion.study.state import LearningAction

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession


from hephaion.chat.conversation_context import (
    _last_assistant_message,
    _last_cited_assistant_message,
)
from hephaion.chat.prior_answer import (
    _PRIOR_ANSWER_CONTEXT_LIMIT,
    _evidence_item_ref,
)
from hephaion.chat.reply_repair import _reply_evidence_ids
from hephaion.chat.turn_contract_checks import (
    _contract_has_specific_material_target,
    _plan_requires_citations,
)
from hephaion.chat.turn_query import (
    _best_current_request_query,
    _content_terms,
    _current_request_introduces_fresh_content,
    _lacks_retrievable_content,
    _normalized_query_terms,
    _same_normalized_text,
)

_FRESH_CURRENT_REQUEST_MIN_TERMS = 3
_DEFAULT_MATERIAL_OVERVIEW_REQUEST = "Provide a compact overview of the material contents."
_CURRENT_TOPIC_QUERY_INTENTS = frozenset({"source_qa", "topic_presentation"})
_CURRENT_TOPIC_QUERY_BLOCKED_STRATEGIES = frozenset(
    {
        RETRIEVAL_STRATEGY_NONE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
    }
)
_EMPTY_QUERY_NO_RETRIEVAL_STRATEGIES = frozenset(
    {
        RETRIEVAL_STRATEGY_NONE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    }
)
_CONTINUABLE_MATERIAL_INTENTS = frozenset(
    {
        "material_overview",
        "source_qa",
        "source_only_policy",
        "topic_presentation",
        "topic_drill",
    }
)
_PLAN_CONTRACT_LABEL_BY_ACTION: Mapping[LearningAction, str] = {
    LearningAction.PRIORITY: "material_overview",
    LearningAction.SOURCE_QA: "source_qa",
    LearningAction.PRESENT: "topic_presentation",
    LearningAction.CALIBRATE: "topic_drill",
    LearningAction.REVIEW: "topic_presentation",
    LearningAction.SIMPLIFY: "topic_presentation",
    LearningAction.HINT: "topic_drill",
    LearningAction.PROMPT_RECALL: "ready_for_recall",
    LearningAction.WAIT_READY_REMINDER: "ready_for_recall",
    LearningAction.REFUSE_REVEAL: "recall_clarification",
    LearningAction.ASSESS: "recall_answer_attempt",
    LearningAction.CHAT: "chat",
}


@dataclass(slots=True)
class _PlanContractApplication:
    plan: LearningTurnPlan
    contract: TurnContract
    prior_contract: TurnContract | None
    retrieval_strategy: str
    retrieval_query: str | None


@dataclass(frozen=True, slots=True)
class _RetrievalState:
    strategy: str
    query: str | None


@dataclass(frozen=True, slots=True)
class _ReasoningFollowupApplication:
    contract: TurnContract
    retrieval: _RetrievalState


def _resolved_plan_intent(plan: LearningTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material_overview"
    return _PLAN_CONTRACT_LABEL_BY_ACTION.get(plan.action, plan.action.value)


def _resolved_turn_intent(resolved: ResolvedTurnPlan) -> str:
    if resolved.turn_contract is not None and resolved.turn_contract.resolved_intent:
        return resolved.turn_contract.resolved_intent
    return _resolved_plan_intent(resolved.learning_plan)


def _apply_turn_contract_to_plan(
    plan: LearningTurnPlan,
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> tuple[LearningTurnPlan, TurnContract]:
    contract = _contract_with_default_material_scope(plan, contract)
    if contract.resolved_intent in {"heph_action", "heph_help"}:
        return _heph_command_plan_contract(plan, contract)
    state = _PlanContractApplication(
        plan=plan,
        contract=contract,
        prior_contract=prior_contract,
        retrieval_strategy=contract.retrieval_strategy,
        retrieval_query=_semantic_retrieval_query(plan, contract),
    )
    _apply_stabilized_followup_retrieval(state)
    _apply_prior_answer_followup_state(state)
    _apply_current_request_retrieval_state(state)
    _apply_replayability_state(state)
    _apply_current_topic_retrieval_state(state)
    _apply_direct_evidence_state(state)
    _apply_overview_state(state)
    _apply_priority_retrieval_state(state)
    return _finalized_plan_contract(state)


def _heph_command_plan_contract(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> tuple[LearningTurnPlan, TurnContract]:
    updated_plan = replace(
        plan,
        original_user_input=contract.original_user_input,
        retrieval_query=None,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
        evidence_refs=(),
        requires_direct_evidence=False,
        uses_overview_sampling=False,
    )
    updated_contract = replace(
        contract,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
        retrieval_query="",
        evidence_refs=(),
        citation_required=False,
        direct_evidence_required=False,
    )
    return updated_plan, updated_contract


def _apply_stabilized_followup_retrieval(state: _PlanContractApplication) -> None:
    decision = _stabilized_followup_retrieval(
        state.contract,
        prior_contract=state.prior_contract,
        retrieval_strategy=state.retrieval_strategy,
        retrieval_query=state.retrieval_query,
    )
    state.retrieval_strategy = decision.strategy
    state.retrieval_query = decision.query


def _apply_prior_answer_followup_state(state: _PlanContractApplication) -> None:
    if _prior_followup_should_transform_prior_answer(
        state.contract,
        prior_contract=state.prior_contract,
    ):
        state.contract = replace(
            state.contract,
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
        state.retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
        state.retrieval_query = None
    retrieval = _prior_followup_retrieval_state(
        state.contract,
        prior_contract=state.prior_contract,
        retrieval_strategy=state.retrieval_strategy,
        retrieval_query=state.retrieval_query,
    )
    state.retrieval_strategy = retrieval.strategy
    state.retrieval_query = retrieval.query


def _apply_current_request_retrieval_state(state: _PlanContractApplication) -> None:
    if _source_request_needs_current_retrieval(
        state.contract,
        prior_contract=state.prior_contract,
        retrieval_strategy=state.retrieval_strategy,
        retrieval_query=state.retrieval_query,
    ):
        state.retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        state.retrieval_query = _fresh_current_request_query(state.contract)
    application = _apply_reasoning_followup_contract(
        state.contract,
        prior_contract=state.prior_contract,
        retrieval_strategy=state.retrieval_strategy,
        retrieval_query=state.retrieval_query,
    )
    state.contract = application.contract
    state.retrieval_strategy = application.retrieval.strategy
    state.retrieval_query = application.retrieval.query
    if (
        _expanded_prior_should_use_current_request(
            state.contract,
            prior_contract=state.prior_contract,
            retrieval_strategy=state.retrieval_strategy,
            fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
        )
        and state.prior_contract is not None
    ):
        state.retrieval_query = _expanded_prior_followup_query(
            state.contract,
            state.prior_contract,
            fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
        )
    if (
        state.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and state.contract.resolved_intent != "material_overview"
    ):
        state.retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        state.retrieval_query = (
            state.contract.retrieval_query
            or state.contract.canonical_request
            or state.retrieval_query
        )


def _apply_replayability_state(state: _PlanContractApplication) -> None:
    if _followup_lacks_replayable_prior_surface(
        state.contract,
        prior_contract=state.prior_contract,
    ):
        state.contract = replace(state.contract, prior_answer_reference=True)
        state.retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
        state.retrieval_query = None
    elif (
        state.prior_contract is not None
        and not state.prior_contract.evidence_refs
        and state.contract.is_followup
        and state.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not state.retrieval_query
    ):
        state.contract = replace(state.contract, prior_answer_reference=True)


def _apply_current_topic_retrieval_state(state: _PlanContractApplication) -> None:
    current_topic_query = _stabilized_current_topic_query(
        state.contract,
        state.retrieval_query,
        retrieval_strategy=state.retrieval_strategy,
    )
    if current_topic_query != state.retrieval_query:
        if (
            state.prior_contract is not None
            and state.prior_contract.evidence_refs
            and state.contract.is_followup
            and state.contract.resolved_intent == "source_qa"
        ):
            state.retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            state.retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
    state.retrieval_query = current_topic_query


def _apply_direct_evidence_state(state: _PlanContractApplication) -> None:
    if _prior_followup_has_literal_direct_requirement(
        state.contract,
        prior_contract=state.prior_contract,
    ):
        state.contract = replace(state.contract, direct_evidence_required=False)
    if _prior_followup_should_reason_from_prior(
        state.contract,
        prior_contract=state.prior_contract,
        retrieval_strategy=state.retrieval_strategy,
    ):
        state.contract = replace(
            state.contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
        )


def _apply_overview_state(state: _PlanContractApplication) -> None:
    if _contract_requires_overview_sampling(
        state.contract,
        prior_contract=state.prior_contract,
    ):
        if state.contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
            state.contract = replace(
                state.contract,
                answer_mode=ANSWER_MODE_FROM_EVIDENCE,
                prior_answer_reference=False,
                prior_answer_positions=(),
                prior_answer_position_basis="",
            )
        state.retrieval_strategy = RETRIEVAL_STRATEGY_OVERVIEW
        state.retrieval_query = _overview_retrieval_surface(
            state.plan,
            state.contract,
            state.retrieval_query,
        )
    elif (
        state.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and _contract_has_specific_material_target(state.contract)
    ):
        state.retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        state.retrieval_query = (
            state.contract.retrieval_query
            or state.contract.canonical_request
            or state.retrieval_query
        )


def _apply_priority_retrieval_state(state: _PlanContractApplication) -> None:
    if (
        state.plan.action is LearningAction.PRIORITY
        and state.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not state.contract.prior_answer_reference
    ):
        state.retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        state.retrieval_query = (
            state.plan.retrieval_query or state.contract.canonical_request or state.retrieval_query
        )


def _finalized_plan_contract(
    state: _PlanContractApplication,
) -> tuple[LearningTurnPlan, TurnContract]:
    evidence_refs = _apply_prior_evidence_refs(state)
    requires_direct_evidence = _contract_requires_direct_source_support(
        state.plan,
        state.contract,
        retrieval_strategy=state.retrieval_strategy,
    )
    updated_plan = replace(
        state.plan,
        original_user_input=state.contract.original_user_input,
        retrieval_query=state.retrieval_query,
        retrieval_strategy=state.retrieval_strategy,
        evidence_refs=evidence_refs,
        requires_direct_evidence=requires_direct_evidence,
        uses_overview_sampling=state.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW,
    )
    updated_contract = replace(
        state.contract,
        resolved_intent=state.contract.resolved_intent or _resolved_plan_intent(updated_plan),
        retrieval_strategy=state.retrieval_strategy,
        retrieval_query=state.retrieval_query or "",
        evidence_refs=evidence_refs,
        citation_required=_plan_requires_citations(updated_plan),
        direct_evidence_required=updated_plan.requires_direct_evidence,
    )
    return updated_plan, updated_contract


def _apply_prior_evidence_refs(state: _PlanContractApplication) -> tuple[str, ...]:
    evidence_refs = _prior_evidence_refs_for_strategy(
        state.retrieval_strategy,
        state.prior_contract,
    )
    if _reusing_prior_evidence(state, evidence_refs):
        state.retrieval_query = None
    elif _reuse_prior_without_evidence_has_query(state, evidence_refs):
        state.retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
    if _direct_followup_reuses_prior_evidence(state, evidence_refs):
        state.contract = replace(state.contract, prior_answer_reference=True)
    return evidence_refs


def _reusing_prior_evidence(
    state: _PlanContractApplication,
    evidence_refs: tuple[str, ...],
) -> bool:
    return bool(evidence_refs) and state.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR


def _reuse_prior_without_evidence_has_query(
    state: _PlanContractApplication,
    evidence_refs: tuple[str, ...],
) -> bool:
    return (
        not evidence_refs
        and bool(state.retrieval_query)
        and state.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    )


def _direct_followup_reuses_prior_evidence(
    state: _PlanContractApplication,
    evidence_refs: tuple[str, ...],
) -> bool:
    return (
        _reusing_prior_evidence(state, evidence_refs)
        and state.contract.is_followup
        and state.contract.direct_evidence_required
    )


def _prior_followup_retrieval_state(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _RetrievalState:
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    ):
        retrieval_query = _fresh_current_request_query(contract)
        if _current_request_introduces_fresh_content(
            contract,
            prior_contract,
            fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
        ):
            retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
            retrieval_query = None
    if _reuse_prior_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        retrieval_query = _fresh_current_request_query(contract)
    return _RetrievalState(strategy=retrieval_strategy, query=retrieval_query)


def _apply_reasoning_followup_contract(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _ReasoningFollowupApplication:
    if not _transform_followup_introduces_substantive_request(
        contract,
        prior_contract=prior_contract,
    ):
        return _ReasoningFollowupApplication(
            contract=contract,
            retrieval=_RetrievalState(strategy=retrieval_strategy, query=retrieval_query),
        )
    return _ReasoningFollowupApplication(
        contract=replace(
            contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        ),
        retrieval=_RetrievalState(
            strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            query=_current_request_query(contract),
        ),
    )


def _reuse_prior_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
        and not contract.prior_answer_reference
        and _current_request_introduces_fresh_content(
            contract,
            prior_contract,
            fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
        )
    )


def _prior_followup_should_reason_from_prior(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and not contract.direct_evidence_required
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and retrieval_strategy in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
    )


def _prior_followup_should_transform_prior_answer(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and not contract.direct_evidence_required
        and not _content_terms(contract.original_user_input)
    )


def _transform_followup_introduces_substantive_request(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and _current_request_introduces_fresh_content(
            contract,
            prior_contract,
            fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
        )
    )


def _prior_followup_has_literal_direct_requirement(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.direct_evidence_required
        and not _contract_has_nonliteral_retrieval_surface(contract)
    )


def _source_request_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> bool:
    return (
        (prior_contract is None or not prior_contract.evidence_refs)
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and contract.resolved_intent in _CONTINUABLE_MATERIAL_INTENTS
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
        and not retrieval_query
        and len(_content_terms(contract.original_user_input)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS
    )


def _contract_requires_direct_source_support(
    plan: LearningTurnPlan,
    contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    if contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        return False
    if contract.direct_evidence_required:
        return retrieval_strategy != RETRIEVAL_STRATEGY_REUSE_PRIOR or bool(
            _contract_has_nonliteral_retrieval_surface(contract)
        )
    if retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        return False
    return (
        plan.action is LearningAction.SOURCE_QA
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
    )


def _contract_with_default_material_scope(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> TurnContract:
    if _default_material_scope_not_applicable(plan, contract):
        return contract
    retrieval_query = _overview_retrieval_surface(plan, contract, plan.retrieval_query)
    if _overview_plan_should_replace_request(plan, contract):
        return _default_material_overview_contract(
            contract,
            retrieval_query=retrieval_query,
            canonical_request=_DEFAULT_MATERIAL_OVERVIEW_REQUEST,
            clear_followup_target=True,
        )
    if contract.resolved_intent:
        return contract
    return _default_material_overview_contract(
        contract,
        retrieval_query=retrieval_query,
        canonical_request=contract.canonical_request or _DEFAULT_MATERIAL_OVERVIEW_REQUEST,
    )


def _default_material_scope_not_applicable(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> bool:
    return not _overview_turn(plan) or (
        bool(contract.resolved_intent) and contract.resolved_intent != "material_overview"
    )


def _overview_plan_should_replace_request(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> bool:
    if contract.answer_format != ANSWER_FORMAT_PLAIN or contract.is_followup:
        return False
    return plan.buffer_response or not _contract_has_specific_material_target(contract)


def _default_material_overview_contract(
    contract: TurnContract,
    *,
    retrieval_query: str | None,
    canonical_request: str,
    clear_followup_target: bool = False,
) -> TurnContract:
    updated_contract = replace(
        contract,
        resolved_intent="material_overview",
        canonical_request=canonical_request,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=retrieval_query or "",
    )
    if clear_followup_target:
        return replace(updated_contract, followup_target="")
    return updated_contract


def _overview_retrieval_surface(
    plan: LearningTurnPlan,
    contract: TurnContract,
    fallback: str | None,
) -> str | None:
    for candidate in (
        contract.retrieval_query,
        fallback or "",
        contract.canonical_request,
        contract.original_user_input,
        plan.retrieval_query or "",
        plan.original_user_input,
    ):
        if candidate and not _lacks_retrievable_content(candidate):
            return candidate
    return None


def _followup_lacks_replayable_prior_surface(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and not contract.canonical_request
        and not _contract_followup_target(contract)
    )


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
    return (
        contract.is_followup and prior_contract is not None and bool(prior_contract.evidence_refs)
    )


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
        fresh_request_min_terms=_FRESH_CURRENT_REQUEST_MIN_TERMS,
    )


def _semantic_retrieval_query(plan: LearningTurnPlan, contract: TurnContract) -> str | None:
    if not _plan_uses_material_retrieval(plan):
        return plan.retrieval_query
    if _overview_query_should_follow_plan(contract):
        return plan.retrieval_query
    if _empty_contract_query_disables_retrieval(contract):
        return None
    if _contract_strategy_disables_empty_retrieval(contract):
        return None
    return _semantic_retrieval_surface(plan, contract)


def _overview_query_should_follow_plan(contract: TurnContract) -> bool:
    return (
        contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and not _contract_has_specific_material_target(contract)
    )


def _empty_contract_query_disables_retrieval(contract: TurnContract) -> bool:
    return (
        _contract_has_empty_retrieval_query(contract)
        and contract.retrieval_strategy in _EMPTY_QUERY_NO_RETRIEVAL_STRATEGIES
    )


def _contract_strategy_disables_empty_retrieval(contract: TurnContract) -> bool:
    return (
        contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
        and not _contract_retrieval_query(contract)
    )


def _semantic_retrieval_surface(plan: LearningTurnPlan, contract: TurnContract) -> str | None:
    retrieval_query = _contract_retrieval_query(contract)
    return retrieval_query or contract.canonical_request or plan.retrieval_query


def _plan_uses_material_retrieval(plan: LearningTurnPlan) -> bool:
    return (
        plan.action in _EVIDENCE_REQUIRED_ACTIONS
        or plan.retrieval_query is not None
        or plan.use_expected_source_refs
    )


def _prior_evidence_refs_for_strategy(
    retrieval_strategy: str,
    prior_contract: TurnContract | None,
) -> tuple[str, ...]:
    if retrieval_strategy not in {
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    }:
        return ()
    if prior_contract is None:
        return ()
    if prior_contract.evidence_refs:
        return prior_contract.evidence_refs
    if prior_contract.prior_answer_reference:
        return prior_contract.prior_turn_evidence_refs
    return ()


def _turn_contract_with_evidence(
    contract: TurnContract,
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> TurnContract:
    refs = tuple(_evidence_refs(turn_evidence)) or contract.evidence_refs
    return replace(
        contract,
        retrieval_query=plan.retrieval_query or "",
        retrieval_strategy=plan.retrieval_strategy or contract.retrieval_strategy,
        evidence_refs=refs,
        citation_required=_plan_requires_citations(plan),
        direct_evidence_required=plan.requires_direct_evidence,
    )


def _turn_contract_with_prior_replay_state(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    conversation: Conversation,
    user_input: str,
) -> TurnContract:
    if prior_contract is None or not _contract_needs_prior_replay_state(contract):
        return contract
    prior_answer = (
        _last_cited_assistant_message(conversation, user_input)
        if prior_contract.evidence_refs
        else _last_assistant_message(conversation, user_input)
    )
    return replace(
        contract,
        prior_turn_original_user_input=prior_contract.original_user_input,
        prior_turn_resolved_intent=prior_contract.resolved_intent,
        prior_turn_canonical_request=prior_contract.canonical_request,
        prior_turn_evidence_refs=prior_contract.evidence_refs,
        prior_turn_validation_result=prior_contract.validation_result,
        prior_answer_excerpt=(
            _trace_excerpt(prior_answer.content, limit=_PRIOR_ANSWER_CONTEXT_LIMIT)
            if prior_answer is not None
            else ""
        ),
    )


def _reset_unreplayable_followup_state(
    plan: LearningTurnPlan,
    contract: TurnContract,
) -> tuple[LearningTurnPlan, TurnContract]:
    if not _contract_needs_prior_replay_state(contract):
        return plan, contract
    if _contract_has_replayable_grounding_surface(contract):
        return plan, contract

    retrieval_query = _unreplayable_followup_current_query(contract)
    retrieval_strategy = (
        RETRIEVAL_STRATEGY_RETRIEVE if retrieval_query else RETRIEVAL_STRATEGY_NONE
    )
    reset_contract = replace(
        contract,
        is_followup=False,
        followup_target="",
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
        evidence_refs=(),
        prior_answer_reference=False,
        prior_answer_positions=(),
        prior_answer_position_basis="",
        prior_turn_original_user_input="",
        prior_turn_resolved_intent="",
        prior_turn_canonical_request="",
        prior_turn_evidence_refs=(),
        prior_turn_validation_result="",
        prior_answer_excerpt="",
    )
    requires_direct_evidence = _contract_requires_direct_source_support(
        plan,
        reset_contract,
        retrieval_strategy=retrieval_strategy,
    )
    reset_plan = replace(
        plan,
        retrieval_query=retrieval_query or None,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=(),
        requires_direct_evidence=requires_direct_evidence,
    )
    reset_contract = replace(
        reset_contract,
        citation_required=_plan_requires_citations(reset_plan),
        direct_evidence_required=reset_plan.requires_direct_evidence,
    )
    return reset_plan, reset_contract


def _unreplayable_followup_current_query(contract: TurnContract) -> str:
    if not contract.is_followup or not contract.prior_turn_original_user_input:
        return contract.canonical_request or contract.original_user_input
    if len(_content_terms(contract.original_user_input)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS:
        return contract.canonical_request or contract.original_user_input
    return ""


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


def _turn_contract_with_validation(
    contract: TurnContract | None,
    notice: str,
) -> TurnContract | None:
    if contract is None:
        return None
    return replace(contract, validation_result=notice or "ok")


def _resolved_with_validation_result(
    resolved: ResolvedTurnPlan,
    notice: str,
) -> ResolvedTurnPlan:
    return replace(
        resolved,
        turn_contract=_turn_contract_with_validation(resolved.turn_contract, notice),
    )


def _resolved_with_visible_evidence_refs(
    resolved: ResolvedTurnPlan,
    reply: str,
    visible_evidence: TurnEvidence | None,
) -> ResolvedTurnPlan:
    contract = resolved.turn_contract
    if contract is None:
        return resolved
    return replace(
        resolved,
        turn_contract=replace(
            contract,
            evidence_refs=tuple(_reply_cited_evidence_refs(reply, visible_evidence)),
        ),
    )


def _reply_cited_evidence_refs(
    reply: str,
    evidence: TurnEvidence | None,
) -> list[str]:
    if evidence is None or not evidence.items:
        return []
    ref_by_id = {item.evidence_id.casefold(): _evidence_item_ref(item) for item in evidence.items}
    refs: list[str] = []
    seen: set[str] = set()
    for evidence_id in _reply_evidence_ids(reply):
        ref = ref_by_id.get(evidence_id.casefold())
        if ref is None or ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)
    return refs


def _turn_contract_can_seed_followup(
    contract: TurnContract | None,
    *,
    visible_evidence: TurnEvidence | None,
) -> bool:
    if contract is None:
        return False
    return (
        visible_evidence is not None
        or bool(contract.evidence_refs)
        or (contract.prior_answer_reference and bool(contract.prior_turn_evidence_refs))
        or contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        or contract.resolved_intent in {"heph_action", "heph_help"}
    )


def _prior_contract_for_followup_seed(session: ChatSession) -> TurnContract | None:
    contract = session.last_turn_contract
    if _turn_contract_can_seed_followup(contract, visible_evidence=session.last_turn_evidence):
        return contract
    return None


def _resolved_with_citation_requirement(
    resolved: ResolvedTurnPlan,
    *,
    citation_required: bool | None,
) -> ResolvedTurnPlan:
    if citation_required is None or resolved.turn_contract is None:
        return resolved
    return replace(
        resolved,
        turn_contract=replace(
            resolved.turn_contract,
            citation_required=citation_required,
        ),
    )
