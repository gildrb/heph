"""Follow-up retrieval decisions for turn planning."""

from __future__ import annotations

from dataclasses import dataclass

from hephaion.chat.prior_answer import _quoted_followup_target_phrases
from hephaion.chat.turn_contract import (
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
from hephaion.chat.turn_predicates import _contract_followup_target
from hephaion.chat.turn_query import (
    _current_request_introduces_fresh_content,
    _query_reuses_surface,
    _same_normalized_text,
    _semantic_query_specificity,
)

_BROAD_PRIOR_EVIDENCE_REF_COUNT = 8


@dataclass(frozen=True, slots=True)
class _FollowupRetrievalDecision:
    strategy: str
    query: str | None


def _stabilized_followup_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _FollowupRetrievalDecision:
    if decision := _prior_answer_direct_followup_retrieval(contract, prior_contract):
        return decision
    if decision := _missing_prior_evidence_followup_retrieval(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    ):
        return decision
    if decision := _overview_reuse_followup_retrieval(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return decision
    if decision := _prior_answer_reference_followup_retrieval(contract, prior_contract):
        return decision
    if decision := _prior_answer_mode_followup_retrieval(contract, prior_contract):
        return decision
    if decision := _broad_prior_followup_retrieval(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return decision
    if decision := _literal_followup_query_retrieval(
        contract,
        prior_contract,
        retrieval_query=retrieval_query,
    ):
        return decision
    if decision := _prior_retrieve_followup_retrieval(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    ):
        return decision
    return _FollowupRetrievalDecision(retrieval_strategy, retrieval_query)


def _prior_answer_direct_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or not prior_contract.evidence_refs or not contract.is_followup:
        return None
    if not contract.prior_answer_reference:
        return None
    if contract.direct_evidence_required and _contract_has_nonliteral_retrieval_surface(contract):
        return _FollowupRetrievalDecision(
            RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            _fresh_current_request_query(contract),
        )
    if contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE:
        target_phrase_query = _followup_target_phrase_query(contract)
        if target_phrase_query:
            return _FollowupRetrievalDecision(
                RETRIEVAL_STRATEGY_EXPAND_PRIOR,
                target_phrase_query,
            )
    return None


def _prior_answer_reference_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or not prior_contract.evidence_refs or not contract.is_followup:
        return None
    if not contract.prior_answer_reference:
        return None
    if (
        contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
        and contract.resolved_intent == "material_overview"
    ):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)


def _missing_prior_evidence_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or prior_contract.evidence_refs or not contract.is_followup:
        return None
    if contract.prior_answer_reference:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)
    if (
        retrieval_strategy in {RETRIEVAL_STRATEGY_REUSE_PRIOR, RETRIEVAL_STRATEGY_EXPAND_PRIOR}
        and not retrieval_query
    ):
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)
    return None


def _overview_reuse_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_strategy: str,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or not prior_contract.evidence_refs or not contract.is_followup:
        return None
    if not (
        _contract_is_material_overview(prior_contract)
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
    ):
        return None
    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    if semantic_query:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return None


def _prior_answer_mode_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or not prior_contract.evidence_refs or not contract.is_followup:
        return None
    if contract.answer_mode in {ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)
    return None


def _broad_prior_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_strategy: str,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None or not contract.is_followup:
        return None
    if not (
        retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and len(prior_contract.evidence_refs) > _BROAD_PRIOR_EVIDENCE_REF_COUNT
    ):
        return None
    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    if semantic_query:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return None


def _literal_followup_query_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_query: str | None,
) -> _FollowupRetrievalDecision | None:
    if not (
        contract.is_followup
        and retrieval_query
        and _same_normalized_text(retrieval_query, contract.original_user_input)
    ):
        return None
    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    if not semantic_query:
        return None
    if prior_contract is not None and prior_contract.evidence_refs:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_RETRIEVE, semantic_query)


def _prior_retrieve_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
    *,
    retrieval_strategy: str,
    retrieval_query: str | None,
) -> _FollowupRetrievalDecision | None:
    if (
        prior_contract is None
        or not prior_contract.evidence_refs
        or not contract.is_followup
        or retrieval_strategy != RETRIEVAL_STRATEGY_RETRIEVE
        or not retrieval_query
    ):
        return None
    if _same_normalized_text(retrieval_query, contract.original_user_input):
        semantic_query = _first_non_literal_followup_query(contract, prior_contract)
        if semantic_query:
            return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, retrieval_query)


def _prior_followup_retrieval_state(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
    fresh_request_min_terms: int,
) -> _FollowupRetrievalDecision:
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
            fresh_request_min_terms=fresh_request_min_terms,
        ):
            retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        else:
            retrieval_strategy = RETRIEVAL_STRATEGY_REUSE_PRIOR
            retrieval_query = None
    if _reuse_prior_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        retrieval_strategy = RETRIEVAL_STRATEGY_EXPAND_PRIOR
        retrieval_query = _fresh_current_request_query(contract)
    return _FollowupRetrievalDecision(strategy=retrieval_strategy, query=retrieval_query)


def _reuse_prior_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    fresh_request_min_terms: int,
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
            fresh_request_min_terms=fresh_request_min_terms,
        )
    )


def _expanded_prior_should_use_current_request(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    fresh_request_min_terms: int,
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
            or _current_request_introduces_fresh_content(
                contract,
                prior_contract,
                fresh_request_min_terms=fresh_request_min_terms,
            )
        )
    )


def _expanded_prior_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    fresh_request_min_terms: int,
) -> str:
    current_semantic_query = _current_turn_semantic_query(contract)
    retrieval_query = _contract_retrieval_query(contract)
    followup_target = _contract_followup_target(contract)
    target_query = _reusable_nonliteral_query_for_surface(
        contract,
        retrieval_query,
        followup_target,
    )
    if target_query:
        return target_query
    if current_semantic_query:
        semantic_query = _reusable_nonliteral_query_for_surface(
            contract,
            retrieval_query,
            current_semantic_query,
        )
        return semantic_query or current_semantic_query
    if _current_request_introduces_fresh_content(
        contract,
        prior_contract,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        return _current_request_query(contract)
    return retrieval_query or _current_request_query(contract)


def _reusable_nonliteral_query_for_surface(
    contract: TurnContract,
    retrieval_query: str | None,
    surface: str | None,
) -> str | None:
    if not retrieval_query or not surface:
        return None
    if _same_normalized_text(retrieval_query, contract.original_user_input):
        return None
    if not _query_reuses_surface(retrieval_query, surface):
        return None
    return retrieval_query


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
