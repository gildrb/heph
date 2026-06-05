"""Turn-plan contract reconciliation and retrieval planning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING

from ai.runtime.conversation import Conversation
from rag.context import TurnEvidence
from study.prompt_plans import LearningTurnPlan
from study.state import LearningAction

from chat.citation_patterns import (
    _OVERVIEW_CITATION_ID_RE,
)
from chat.evidence import ResolvedTurnPlan
from chat.evidence import evidence_refs as _evidence_refs
from chat.material_state import (
    _EVIDENCE_REQUIRED_ACTIONS,
)
from chat.turn_contract import (
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
from chat.turn_predicates import (
    _contract_followup_target,
    _overview_turn,
    _trace_excerpt,
)

if TYPE_CHECKING:
    from chat.session import ChatSession


from chat.conversation_context import (
    _last_assistant_message,
    _last_cited_assistant_message,
)
from chat.prior_answer import (
    _PRIOR_ANSWER_CONTEXT_LIMIT,
    _evidence_item_ref,
    _quoted_followup_target_phrases,
)
from chat.reply_repair import _reply_evidence_ids
from chat.turn_contract_checks import (
    _contract_has_specific_material_target,
    _plan_requires_citations,
)
from chat.turn_query import (
    _content_terms,
    _lacks_retrievable_content,
    _normalized_query_terms,
    _query_reuses_surface,
    _query_term_overlap,
    _query_terms_match,
    _same_normalized_text,
    _semantic_query_specificity,
)

_BROAD_PRIOR_EVIDENCE_REF_COUNT = 8
_FRESH_CURRENT_REQUEST_MIN_TERMS = 3
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
    retrieval_query = _semantic_retrieval_query(plan, contract)
    retrieval_strategy = contract.retrieval_strategy
    retrieval_strategy, retrieval_query = _stabilized_followup_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    )
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    ):
        retrieval_query = _fresh_current_request_query(contract)
        if _current_request_introduces_fresh_content(contract, prior_contract):
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
    if _source_request_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = _fresh_current_request_query(contract)
    if _transform_followup_introduces_substantive_request(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(
            contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        retrieval_query = _current_request_query(contract)
    if (
        _expanded_prior_should_use_current_request(
            contract,
            prior_contract=prior_contract,
            retrieval_strategy=retrieval_strategy,
        )
        and prior_contract is not None
    ):
        retrieval_query = _expanded_prior_followup_query(contract, prior_contract)
    if (
        retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and contract.resolved_intent != "material_overview"
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = contract.retrieval_query or contract.canonical_request or retrieval_query
    if _followup_lacks_replayable_prior_surface(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(contract, prior_answer_reference=True)
        retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
        retrieval_query = None
    elif (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not retrieval_query
    ):
        contract = replace(contract, prior_answer_reference=True)
    current_topic_query = _stabilized_current_topic_query(
        contract,
        retrieval_query,
        retrieval_strategy=retrieval_strategy,
    )
    if current_topic_query != retrieval_query:
        if (
            prior_contract is not None
            and prior_contract.evidence_refs
            and contract.is_followup
            and contract.resolved_intent == "source_qa"
        ):
            retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
    retrieval_query = current_topic_query
    if _prior_followup_has_literal_direct_requirement(
        contract,
        prior_contract=prior_contract,
    ):
        contract = replace(contract, direct_evidence_required=False)
    if _prior_followup_should_reason_from_prior(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        contract = replace(
            contract,
            answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
            prior_answer_reference=True,
        )
    if _contract_requires_overview_sampling(contract, prior_contract=prior_contract):
        if contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
            contract = replace(
                contract,
                answer_mode=ANSWER_MODE_FROM_EVIDENCE,
                prior_answer_reference=False,
                prior_answer_positions=(),
                prior_answer_position_basis="",
            )
        retrieval_strategy = RETRIEVAL_STRATEGY_OVERVIEW
        retrieval_query = _overview_retrieval_surface(plan, contract, retrieval_query)
    elif (
        retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and _contract_has_specific_material_target(contract)
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = contract.retrieval_query or contract.canonical_request or retrieval_query
    if (
        plan.action is LearningAction.PRIORITY
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not contract.prior_answer_reference
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_RETRIEVE
        retrieval_query = plan.retrieval_query or contract.canonical_request or retrieval_query
    evidence_refs = _prior_evidence_refs_for_strategy(retrieval_strategy, prior_contract)
    if evidence_refs and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_query = None
    elif retrieval_query and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR:
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
    if (
        evidence_refs
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.is_followup
        and contract.direct_evidence_required
    ):
        contract = replace(contract, prior_answer_reference=True)

    requires_direct_evidence = _contract_requires_direct_source_support(
        plan,
        contract,
        retrieval_strategy=retrieval_strategy,
    )

    updated_plan = replace(
        plan,
        original_user_input=contract.original_user_input,
        retrieval_query=retrieval_query,
        retrieval_strategy=retrieval_strategy,
        evidence_refs=evidence_refs,
        requires_direct_evidence=requires_direct_evidence,
        uses_overview_sampling=retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW,
    )
    updated_contract = replace(
        contract,
        resolved_intent=contract.resolved_intent or _resolved_plan_intent(updated_plan),
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query or "",
        evidence_refs=evidence_refs,
        citation_required=_plan_requires_citations(updated_plan),
        direct_evidence_required=updated_plan.requires_direct_evidence,
    )
    return updated_plan, updated_contract


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
        and _current_request_introduces_fresh_content(contract, prior_contract)
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


def _expanded_prior_should_use_current_request(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
) -> bool:
    return (
        prior_contract is not None
        and bool(prior_contract.evidence_refs)
        and contract.is_followup
        and not contract.prior_answer_reference
        and contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and (
            _current_turn_semantic_query(contract) is not None
            or _current_request_introduces_fresh_content(contract, prior_contract)
        )
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
        and _current_request_introduces_fresh_content(contract, prior_contract)
    )


def _expanded_prior_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> str:
    current_semantic_query = _current_turn_semantic_query(contract)
    retrieval_query = _contract_retrieval_query(contract)
    followup_target = _contract_followup_target(contract)
    if (
        followup_target
        and retrieval_query
        and not _same_normalized_text(retrieval_query, contract.original_user_input)
        and _query_reuses_surface(retrieval_query, followup_target)
    ):
        return retrieval_query
    if current_semantic_query:
        if (
            retrieval_query
            and not _same_normalized_text(retrieval_query, contract.original_user_input)
            and _query_reuses_surface(
                retrieval_query,
                current_semantic_query,
            )
        ):
            return retrieval_query
        return current_semantic_query
    if _current_request_introduces_fresh_content(contract, prior_contract):
        return _current_request_query(contract)
    return retrieval_query or _current_request_query(contract)


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


def _contract_has_nonliteral_retrieval_surface(contract: TurnContract) -> bool:
    query = _contract_retrieval_query(contract)
    return bool(query) and not _same_normalized_text(query, contract.original_user_input)


def _fresh_current_request_query(contract: TurnContract) -> str:
    return (
        _contract_retrieval_query(contract)
        or contract.canonical_request.strip()
        or contract.original_user_input.strip()
    )


def _current_request_query(contract: TurnContract) -> str:
    return (
        contract.canonical_request.strip()
        or contract.original_user_input.strip()
        or _contract_retrieval_query(contract)
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


def _current_request_introduces_fresh_content(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> bool:
    current_terms = _content_terms(contract.original_user_input)
    if not current_terms:
        return False
    prior_terms = _content_terms(
        " ".join(
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
    )
    if not prior_terms:
        return len(current_terms) >= _FRESH_CURRENT_REQUEST_MIN_TERMS
    fresh_terms = [
        term
        for term in current_terms
        if not any(_query_terms_match(term, prior_term) for prior_term in prior_terms)
    ]
    return len(fresh_terms) >= _FRESH_CURRENT_REQUEST_MIN_TERMS


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
    if not _overview_turn(plan):
        return contract
    if contract.resolved_intent and contract.resolved_intent != "material_overview":
        return contract
    retrieval_query = _overview_retrieval_surface(plan, contract, plan.retrieval_query)
    if (
        plan.buffer_response
        and contract.answer_format == ANSWER_FORMAT_PLAIN
        and not contract.is_followup
    ):
        return replace(
            contract,
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            followup_target="",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=retrieval_query or "",
        )
    if (
        contract.answer_format == ANSWER_FORMAT_PLAIN
        and not contract.is_followup
        and not _contract_has_specific_material_target(contract)
    ):
        return replace(
            contract,
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            followup_target="",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=retrieval_query or "",
        )
    if contract.resolved_intent:
        return contract
    return replace(
        contract,
        resolved_intent="material_overview",
        canonical_request=contract.canonical_request
        or "Provide a compact overview of the material contents.",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=retrieval_query or "",
    )


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
    if contract.resolved_intent != "material_overview" or (
        contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and contract.answer_format == ANSWER_FORMAT_PLAIN
    ):
        return False
    if contract.answer_format != ANSWER_FORMAT_PLAIN:
        return True
    if _contract_has_specific_material_target(contract):
        return False
    if not contract.is_followup:
        return True
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW:
        return True
    return not (
        contract.is_followup and prior_contract is not None and bool(prior_contract.evidence_refs)
    )


def _stabilized_followup_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> tuple[str, str | None]:
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.direct_evidence_required
        and _contract_has_nonliteral_retrieval_surface(contract)
    ):
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, _fresh_current_request_query(contract)
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and (target_phrase_query := _followup_target_phrase_query(contract))
    ):
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, target_phrase_query
    if (
        prior_contract is not None
        and not prior_contract.evidence_refs
        and contract.is_followup
        and (
            contract.prior_answer_reference
            or (
                retrieval_strategy
                in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
                and not retrieval_query
            )
        )
    ):
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and _contract_is_material_overview(prior_contract)
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.prior_answer_reference
    ):
        if (
            contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
            and contract.resolved_intent == "material_overview"
            and (semantic_query := _first_non_literal_followup_query(contract, prior_contract))
        ):
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
    ):
        return RETRIEVAL_STRATEGY_REUSE_PRIOR, None
    if (
        prior_contract is not None
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and len(prior_contract.evidence_refs) > _BROAD_PRIOR_EVIDENCE_REF_COUNT
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
    if (
        contract.is_followup
        and retrieval_query
        and _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            if prior_contract is not None and prior_contract.evidence_refs:
                return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
            return RETRIEVAL_STRATEGY_RETRIEVE, semantic_query
    if (
        prior_contract is not None
        and prior_contract.evidence_refs
        and contract.is_followup
        and retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE
        and retrieval_query
    ):
        if _same_normalized_text(retrieval_query, contract.original_user_input):
            semantic_query = _first_non_literal_followup_query(contract, prior_contract)
            if semantic_query:
                return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query
        return RETRIEVAL_STRATEGY_EXPAND_PRIOR, retrieval_query
    if (
        prior_contract is None
        or not prior_contract.evidence_refs
        or not contract.is_followup
        or retrieval_strategy != RETRIEVAL_STRATEGY_RETRIEVE
        or not retrieval_query
        or not _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        return retrieval_strategy, retrieval_query

    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    return RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query


def _stabilized_current_topic_query(
    contract: TurnContract,
    retrieval_query: str | None,
    *,
    retrieval_strategy: str,
) -> str | None:
    if (
        contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and retrieval_query
        and not _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        return retrieval_query
    if (
        not contract.is_followup
        or contract.resolved_intent not in {"source_qa", "topic_presentation"}
        or contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE
        or contract.prior_answer_reference
        or retrieval_strategy in {RETRIEVAL_STRATEGY_NONE, RETRIEVAL_STRATEGY_REUSE_PRIOR}
    ):
        return retrieval_query
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
    )


def _best_current_request_query(
    request_terms: frozenset[str],
    *,
    original_text: str,
    candidates: Sequence[str | None],
) -> str | None:
    scored = [
        (
            _query_term_overlap(candidate, request_terms),
            _semantic_query_specificity(candidate),
            candidate,
        )
        for candidate in candidates
        if candidate
    ]
    if not scored:
        return None
    best = max(scored)[2]
    if not _same_normalized_text(best, original_text):
        return best
    if len(_content_terms(original_text)) >= _FRESH_CURRENT_REQUEST_MIN_TERMS:
        return best
    semantic_candidates = [
        scored_candidate
        for scored_candidate in scored
        if not _same_normalized_text(scored_candidate[2], original_text)
    ]
    return max(semantic_candidates)[2] if semantic_candidates else best


def _first_non_literal_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> str | None:
    if semantic_current_query := _current_turn_semantic_query(contract):
        return semantic_current_query
    prior_candidates = [
        prior_contract.canonical_request if prior_contract is not None else "",
        prior_contract.retrieval_query if prior_contract is not None else "",
    ]
    semantic_candidates = [
        candidate
        for candidate in prior_candidates
        if candidate and not _same_normalized_text(candidate, contract.original_user_input)
    ]
    if not semantic_candidates:
        return None
    return max(semantic_candidates, key=_semantic_query_specificity)


def _current_turn_semantic_query(contract: TurnContract) -> str | None:
    current_candidates = [
        _contract_followup_target(contract),
        contract.canonical_request,
    ]
    semantic_current_candidates = [
        candidate
        for candidate in current_candidates
        if candidate and not _same_normalized_text(candidate, contract.original_user_input)
    ]
    if not semantic_current_candidates:
        return None
    return max(semantic_current_candidates, key=_semantic_query_specificity)


def _followup_target_phrase_query(contract: TurnContract) -> str:
    phrases = _quoted_followup_target_phrases(contract)
    if not phrases:
        return ""
    return max(phrases, key=_semantic_query_specificity)


def _contract_retrieval_query(contract: TurnContract) -> str:
    if _contract_has_empty_retrieval_query(contract):
        return ""
    return contract.retrieval_query.strip()


def _contract_has_empty_retrieval_query(contract: TurnContract) -> bool:
    return contract.retrieval_query.strip().casefold() == RETRIEVAL_STRATEGY_NONE


def _contract_is_material_overview(contract: TurnContract) -> bool:
    return (
        contract.resolved_intent == "material_overview"
        or contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    )


def _semantic_retrieval_query(plan: LearningTurnPlan, contract: TurnContract) -> str | None:
    if not _plan_uses_material_retrieval(plan):
        return plan.retrieval_query
    if (
        contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
        and not _contract_has_specific_material_target(contract)
    ):
        return plan.retrieval_query
    if _contract_has_empty_retrieval_query(contract) and contract.retrieval_strategy in {
        RETRIEVAL_STRATEGY_NONE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    }:
        return None
    if contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE and not _contract_retrieval_query(
        contract
    ):
        return None
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
