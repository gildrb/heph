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
    if prior_contract is None:
        return None
    if not _contract_has_prior_evidence_followup(contract, prior_contract):
        return None
    if not contract.prior_answer_reference:
        return None
    retrieval_query = _prior_answer_direct_followup_query(contract)
    if retrieval_query:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, retrieval_query)
    return None


def _prior_answer_direct_followup_query(contract: TurnContract) -> str:
    if _direct_followup_needs_nonliteral_source(contract):
        return _fresh_current_request_query(contract)
    if contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE:
        return ""
    return _followup_target_phrase_query(contract)


def _direct_followup_needs_nonliteral_source(contract: TurnContract) -> bool:
    return contract.direct_evidence_required and _contract_has_nonliteral_retrieval_surface(
        contract
    )


def _prior_answer_reference_followup_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None:
        return None
    if not _prior_answer_reference_can_reuse_prior(contract, prior_contract):
        return None
    if overview_retrieval := _prior_answer_reference_overview_retrieval(
        contract,
        prior_contract,
    ):
        return overview_retrieval
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)


def _prior_answer_reference_can_reuse_prior(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> bool:
    if not _contract_has_prior_evidence_followup(contract, prior_contract):
        return False
    return contract.prior_answer_reference


def _prior_answer_reference_overview_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> _FollowupRetrievalDecision | None:
    if not _prior_answer_reference_needs_overview_search(contract):
        return None
    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    if not semantic_query:
        return None
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)


def _prior_answer_reference_needs_overview_search(contract: TurnContract) -> bool:
    return (
        contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
        and contract.resolved_intent == "material_overview"
    )


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
    if prior_contract is None:
        return None
    if not _overview_reuse_can_expand_followup(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return None
    semantic_query = _first_non_literal_followup_query(contract, prior_contract)
    if semantic_query:
        return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_EXPAND_PRIOR, semantic_query)
    return None


def _overview_reuse_can_expand_followup(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    return (
        _contract_has_prior_evidence_followup(contract, prior_contract)
        and _contract_is_material_overview(prior_contract)
        and retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
    )


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
    if prior_contract is None or not retrieval_query:
        return None
    if not _prior_retrieve_followup_can_expand(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return None
    return _FollowupRetrievalDecision(
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        _prior_retrieve_followup_query(contract, prior_contract, retrieval_query),
    )


def _prior_retrieve_followup_can_expand(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    if not _contract_has_prior_evidence_followup(contract, prior_contract):
        return False
    return retrieval_strategy == RETRIEVAL_STRATEGY_RETRIEVE


def _prior_retrieve_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract,
    retrieval_query: str,
) -> str:
    if not _same_normalized_text(retrieval_query, contract.original_user_input):
        return retrieval_query
    return _first_non_literal_followup_query(contract, prior_contract) or retrieval_query


def _prior_followup_retrieval_state(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    retrieval_query: str | None,
    fresh_request_min_terms: int,
) -> _FollowupRetrievalDecision:
    retrieval = _FollowupRetrievalDecision(
        strategy=retrieval_strategy,
        query=retrieval_query,
    )
    if prior_retrieval := _seeded_prior_followup_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        retrieval = prior_retrieval
    if current_retrieval := _reuse_prior_current_request_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval.strategy,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        return current_retrieval
    return retrieval


def _seeded_prior_followup_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    fresh_request_min_terms: int,
) -> _FollowupRetrievalDecision | None:
    if prior_contract is None:
        return None
    if not _prior_followup_can_seed_retrieval(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return None
    if _current_request_introduces_fresh_content(
        contract,
        prior_contract,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        return _FollowupRetrievalDecision(
            RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            _fresh_current_request_query(contract),
        )
    return _FollowupRetrievalDecision(RETRIEVAL_STRATEGY_REUSE_PRIOR, None)


def _prior_followup_can_seed_retrieval(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    return (
        _contract_has_prior_evidence_followup(contract, prior_contract)
        and retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    )


def _reuse_prior_current_request_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    fresh_request_min_terms: int,
) -> _FollowupRetrievalDecision | None:
    if not _reuse_prior_needs_current_retrieval(
        contract,
        prior_contract=prior_contract,
        retrieval_strategy=retrieval_strategy,
        fresh_request_min_terms=fresh_request_min_terms,
    ):
        return None
    return _FollowupRetrievalDecision(
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        _fresh_current_request_query(contract),
    )


def _reuse_prior_needs_current_retrieval(
    contract: TurnContract,
    *,
    prior_contract: TurnContract | None,
    retrieval_strategy: str,
    fresh_request_min_terms: int,
) -> bool:
    if prior_contract is None:
        return False
    if not _contract_has_prior_evidence_followup(contract, prior_contract):
        return False
    return (
        retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and _source_answer_can_fetch_current_request(contract)
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
    if prior_contract is None:
        return False
    if not _expanded_prior_can_use_current_request(
        contract,
        prior_contract,
        retrieval_strategy=retrieval_strategy,
    ):
        return False
    return _expanded_prior_has_current_request_signal(
        contract,
        prior_contract,
        fresh_request_min_terms=fresh_request_min_terms,
    )


def _expanded_prior_can_use_current_request(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    retrieval_strategy: str,
) -> bool:
    return (
        _contract_has_prior_evidence_followup(contract, prior_contract)
        and not contract.prior_answer_reference
        and contract.resolved_intent == "source_qa"
        and retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR
        and contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    )


def _expanded_prior_has_current_request_signal(
    contract: TurnContract,
    prior_contract: TurnContract,
    *,
    fresh_request_min_terms: int,
) -> bool:
    return _current_turn_semantic_query(
        contract
    ) is not None or _current_request_introduces_fresh_content(
        contract,
        prior_contract,
        fresh_request_min_terms=fresh_request_min_terms,
    )


def _contract_has_prior_evidence_followup(
    contract: TurnContract,
    prior_contract: TurnContract,
) -> bool:
    return bool(prior_contract.evidence_refs) and contract.is_followup


def _source_answer_can_fetch_current_request(contract: TurnContract) -> bool:
    return (
        contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not contract.direct_evidence_required
        and not contract.prior_answer_reference
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
    return _prior_non_literal_followup_query(contract, prior_contract)


def _prior_non_literal_followup_query(
    contract: TurnContract,
    prior_contract: TurnContract | None,
) -> str | None:
    return _best_non_literal_followup_query(
        contract,
        _prior_followup_query_candidates(prior_contract),
    )


def _prior_followup_query_candidates(prior_contract: TurnContract | None) -> tuple[str, ...]:
    if prior_contract is None:
        return ()
    return (prior_contract.canonical_request, prior_contract.retrieval_query)


def _best_non_literal_followup_query(
    contract: TurnContract,
    candidates: tuple[str, ...],
) -> str | None:
    semantic_candidates = [
        candidate
        for candidate in candidates
        if _is_non_literal_followup_query(contract, candidate)
    ]
    if not semantic_candidates:
        return None
    return max(semantic_candidates, key=_semantic_query_specificity)


def _is_non_literal_followup_query(contract: TurnContract, candidate: str) -> bool:
    return bool(candidate) and not _same_normalized_text(candidate, contract.original_user_input)
