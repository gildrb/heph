"""Follow-up stabilization policy for model-resolved intents."""

from __future__ import annotations

from dataclasses import replace

from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_PLAIN,
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnIntentResolution,
)
from hephaion.chat.turn_query import _query_has_matching_term
from hephaion.rag.scoring import tokenize

_CONTINUABLE_MATERIAL_INTENTS = frozenset(
    {
        "material_overview",
        "source_qa",
        "source_only_policy",
        "topic_presentation",
        "topic_drill",
    }
)
_PRIOR_REFERENCE_SHORT_TOKEN_LIMIT = 4
_PRIOR_REFERENCE_MIN_OVERLAP = 0.5


def _stabilized_followup_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str = "",
    prior_intent: str,
) -> TurnIntentResolution:
    stabilized = _non_material_heph_intent_resolution(resolution)
    if stabilized is not None:
        return stabilized
    stabilized = _direct_evidence_source_resolution(resolution)
    if stabilized is not None:
        return stabilized
    stabilized = _overview_transform_evidence_resolution(
        resolution,
        user_input=user_input,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    stabilized = _reason_from_prior_intent_resolution(
        resolution,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    stabilized = _source_followup_prior_answer_resolution(
        resolution,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    stabilized = _continuable_learning_request_resolution(
        resolution,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    stabilized = _transform_prior_followup_resolution(
        resolution,
        user_input=user_input,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    stabilized = _continuable_priority_followup_resolution(
        resolution,
        prior_intent=prior_intent,
    )
    if stabilized is not None:
        return stabilized
    return resolution


def _non_material_heph_intent_resolution(
    resolution: TurnIntentResolution,
) -> TurnIntentResolution | None:
    if resolution.intent not in {"heph_action", "heph_help"}:
        return None
    return replace(
        resolution,
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
        retrieval_query="",
        direct_evidence_required=False,
        prior_answer_positions=(),
        prior_answer_position_basis="",
    )


def _direct_evidence_source_resolution(
    resolution: TurnIntentResolution,
) -> TurnIntentResolution | None:
    if (
        not resolution.direct_evidence_required
        or resolution.intent == "source_qa"
        or resolution.answer_mode != ANSWER_MODE_FROM_EVIDENCE
    ):
        return None
    retrieval_query = resolution.retrieval_query or resolution.canonical_request
    retrieval_strategy = (
        RETRIEVAL_STRATEGY_RETRIEVE
        if resolution.retrieval_strategy in {RETRIEVAL_STRATEGY_NONE, RETRIEVAL_STRATEGY_OVERVIEW}
        else resolution.retrieval_strategy
    )
    return replace(
        resolution,
        intent="source_qa",
        retrieval_strategy=retrieval_strategy,
        retrieval_query=retrieval_query,
    )


def _overview_transform_evidence_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if (
        resolution.intent != "material_overview"
        or resolution.answer_mode != ANSWER_MODE_TRANSFORM_PRIOR
    ):
        return None
    if (
        resolution.is_followup
        and prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.answer_format == ANSWER_FORMAT_PLAIN
    ):
        return None
    return replace(
        resolution,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=(resolution.retrieval_query or resolution.canonical_request or user_input),
    )


def _reason_from_prior_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if (
        prior_intent not in _CONTINUABLE_MATERIAL_INTENTS
        or resolution.answer_mode != ANSWER_MODE_REASON_FROM_PRIOR
    ):
        return None
    return replace(
        resolution,
        intent=prior_intent,
        is_followup=True,
        prior_answer_reference=True,
        prior_answer_positions=(),
        prior_answer_position_basis="",
    )


def _source_followup_prior_answer_resolution(
    resolution: TurnIntentResolution,
    *,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if (
        prior_intent not in {"material_overview", "topic_presentation"}
        or not resolution.is_followup
        or resolution.intent != "source_qa"
        or resolution.answer_mode != ANSWER_MODE_FROM_EVIDENCE
        or resolution.direct_evidence_required
        or not (resolution.prior_answer_reference or resolution.followup_target.strip())
    ):
        return None
    return replace(
        resolution,
        intent=prior_intent,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        prior_answer_reference=True,
        prior_answer_positions=(),
        prior_answer_position_basis="",
    )


def _continuable_learning_request_resolution(
    resolution: TurnIntentResolution,
    *,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if prior_intent not in _CONTINUABLE_MATERIAL_INTENTS:
        return None
    if resolution.intent not in {"scaffold_request", "hint_request", "material_review"}:
        return None
    retrieval_strategy = (
        resolution.retrieval_strategy
        if resolution.retrieval_strategy != RETRIEVAL_STRATEGY_NONE
        else RETRIEVAL_STRATEGY_REUSE_PRIOR
    )
    return replace(
        resolution,
        intent=prior_intent,
        is_followup=True,
        prior_answer_reference=True,
        retrieval_strategy=retrieval_strategy,
    )


def _transform_prior_followup_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if (
        prior_intent not in _CONTINUABLE_MATERIAL_INTENTS
        or resolution.answer_mode != ANSWER_MODE_TRANSFORM_PRIOR
        or resolution.answer_format != ANSWER_FORMAT_PLAIN
    ):
        return None
    if not _transform_resolution_points_at_prior_answer(
        resolution,
        user_input=user_input,
        prior_intent=prior_intent,
    ):
        return replace(
            resolution,
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            prior_answer_reference=False,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    return replace(
        resolution,
        intent=prior_intent,
        is_followup=True,
        prior_answer_reference=True,
    )


def _continuable_priority_followup_resolution(
    resolution: TurnIntentResolution,
    *,
    prior_intent: str,
) -> TurnIntentResolution | None:
    if (
        not resolution.is_followup
        or prior_intent not in _CONTINUABLE_MATERIAL_INTENTS
        or resolution.intent not in {"priority_request", "driven_learning_calibration"}
    ):
        return None
    return replace(resolution, intent=prior_intent)


def _transform_resolution_points_at_prior_answer(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    prior_intent: str,
) -> bool:
    if resolution.prior_answer_positions:
        return True
    if resolution.prior_answer_reference:
        return _transform_resolution_has_explicit_prior_reference(
            resolution,
            prior_intent=prior_intent,
        )
    if not resolution.followup_target.strip():
        return False
    if not _transform_resolution_matches_user_input(
        resolution,
        user_input=user_input,
    ):
        return False
    return _transform_resolution_target_overlap_is_sufficient(resolution)


def _transform_resolution_has_explicit_prior_reference(
    resolution: TurnIntentResolution,
    *,
    prior_intent: str,
) -> bool:
    source_intent_switch = resolution.intent == "source_qa" and prior_intent != "source_qa"
    return (
        resolution.prior_answer_reference
        and not resolution.direct_evidence_required
        and not source_intent_switch
    )


def _transform_resolution_matches_user_input(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
) -> bool:
    user_tokens = frozenset(tokenize(user_input))
    if not user_tokens:
        return True
    resolved_tokens = _transform_resolution_resolved_tokens(resolution)
    return any(_query_has_matching_term(token, resolved_tokens) for token in user_tokens)


def _transform_resolution_resolved_tokens(
    resolution: TurnIntentResolution,
) -> frozenset[str]:
    resolved_tokens: set[str] = set()
    for text in (resolution.canonical_request, resolution.followup_target):
        resolved_tokens.update(tokenize(text))
    return frozenset(resolved_tokens)


def _transform_resolution_target_overlap_is_sufficient(
    resolution: TurnIntentResolution,
) -> bool:
    request_tokens = frozenset(tokenize(resolution.canonical_request))
    if len(request_tokens) <= _PRIOR_REFERENCE_SHORT_TOKEN_LIMIT:
        return True
    target_tokens = frozenset(tokenize(resolution.followup_target))
    if not target_tokens:
        return False
    overlap = len(request_tokens & target_tokens) / min(len(request_tokens), len(target_tokens))
    return overlap >= _PRIOR_REFERENCE_MIN_OVERLAP
