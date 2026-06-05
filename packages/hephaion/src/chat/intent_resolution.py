"""Model-backed user intent resolution and follow-up stabilization."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation
from ai.runtime.errors import EngineError
from extension_contracts import heph_product_routing_context
from rag.scoring import tokenize
from study.prompt_plans import LearningTurnPlan

import chat.intent as _chat_intent
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
    TurnIntentResolution,
    intent_resolution_from_payload,
)
from chat.turn_predicates import (
    _overview_turn,
    _trace_excerpt,
)

if TYPE_CHECKING:
    from rag.index import ArmoryIndex


import chat.model_text as _model_text
from chat.conversation_context import _last_assistant_message
from chat.turn_contract_checks import (
    _intent_contract_refs_text,
)
from chat.turn_query import (
    _corpus_named_material_query,
    _lacks_retrievable_content,
    _query_has_matching_term,
    _source_lookup_preserves_user_terms,
)

_MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = _chat_intent.MODEL_NORMALIZED_CONFIDENCE_THRESHOLD
_LEARNING_INTENT_NORMALIZATION_SCHEMA = _chat_intent.LEARNING_INTENT_NORMALIZATION_SCHEMA
_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = (
    _chat_intent.LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT
)
_classifier_intent_from_payload = _chat_intent.classifier_intent_from_payload
_normalized_learning_intent_from_payload = _chat_intent.normalized_learning_intent_from_payload
_normalized_confidence = _chat_intent.normalized_confidence
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


def _classified_user_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
    conversation: Conversation | None = None,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> str:
    return _resolved_user_intent(
        user_input,
        config=config,
        conversation=conversation,
        prior_intent=prior_intent,
        prior_contract=prior_contract,
    ).intent


def _resolved_user_intent(
    user_input: str,
    *,
    config: ChatConfig | None,
    conversation: Conversation | None = None,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> TurnIntentResolution:
    if not user_input.strip() or config is None or not config.base_url or not config.model:
        return TurnIntentResolution()
    try:
        payload = _model_text._model_json_payload(
            config,
            system_prompt=(
                f"{_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT}\n"
                f"{_LEARNING_INTENT_NORMALIZATION_SCHEMA}"
            ),
            user_prompt=_intent_normalization_context(
                user_input,
                conversation,
                prior_intent=prior_intent,
                prior_contract=prior_contract,
            ),
            raise_errors=True,
        )
    except EngineError:
        if prior_intent in _CONTINUABLE_MATERIAL_INTENTS:
            return _low_confidence_prior_followup_resolution(
                user_input=user_input,
                prior_intent=prior_intent,
                prior_contract=prior_contract,
                confidence=0.0,
                expand_from_prior=False,
            )
        return TurnIntentResolution(confidence=0.0)
    intent, confidence = _classifier_intent_from_payload(payload)
    if confidence >= _MODEL_NORMALIZED_CONFIDENCE_THRESHOLD:
        resolution = intent_resolution_from_payload(payload, intent=intent, confidence=confidence)
        return _stabilized_followup_intent_resolution(
            resolution,
            user_input=user_input,
            prior_intent=prior_intent,
        )
    if prior_intent in _CONTINUABLE_MATERIAL_INTENTS:
        return _low_confidence_prior_followup_resolution(
            user_input=user_input,
            prior_intent=prior_intent,
            prior_contract=prior_contract,
            confidence=confidence,
            expand_from_prior=True,
        )
    return TurnIntentResolution(confidence=confidence)


def _low_confidence_prior_followup_resolution(
    *,
    user_input: str,
    prior_intent: str,
    prior_contract: TurnContract | None,
    confidence: float,
    expand_from_prior: bool,
) -> TurnIntentResolution:
    if prior_contract is None or not prior_contract.evidence_refs:
        return TurnIntentResolution(intent=prior_intent, confidence=confidence, is_followup=True)
    prior_request = prior_contract.canonical_request or prior_contract.original_user_input
    retrieval_strategy = (
        RETRIEVAL_STRATEGY_EXPAND_PRIOR if expand_from_prior else RETRIEVAL_STRATEGY_REUSE_PRIOR
    )
    return TurnIntentResolution(
        intent=prior_intent,
        canonical_request=user_input,
        is_followup=True,
        followup_target=prior_request,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        answer_format=prior_contract.answer_format,
        retrieval_strategy=retrieval_strategy,
        retrieval_query=prior_request if expand_from_prior else "",
        prior_answer_reference=True,
        confidence=confidence,
    )


def _prior_contract_retrieval_surface(prior_contract: TurnContract) -> str:
    return (
        prior_contract.retrieval_query.strip()
        or prior_contract.canonical_request.strip()
        or prior_contract.original_user_input.strip()
    )


def _stabilized_intent_for_named_material(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    index: ArmoryIndex | None,
) -> TurnIntentResolution:
    if resolution.intent not in _CONTINUABLE_MATERIAL_INTENTS:
        return resolution
    query = _corpus_named_material_query(user_input, index)
    if not query:
        return resolution
    intent = (
        "topic_presentation" if resolution.intent == "material_overview" else resolution.intent
    )
    return replace(
        resolution,
        intent=intent,
        answer_mode="answer_from_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query=query,
        canonical_request=resolution.canonical_request or user_input,
    )


def _stabilized_intent_for_default_material_plan(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
    index: ArmoryIndex | None,
) -> TurnIntentResolution:
    if (
        prior_contract is None
        and _overview_turn(default_plan)
        and _lacks_retrievable_content(user_input)
        and (not resolution.intent or resolution.intent in _CONTINUABLE_MATERIAL_INTENTS)
    ):
        return TurnIntentResolution(
            intent="material_overview",
            canonical_request=resolution.canonical_request or user_input,
            confidence=resolution.confidence,
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            answer_format=resolution.answer_format,
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query="",
        )
    if (
        prior_contract is not None
        or not _overview_turn(default_plan)
        or resolution.intent != "source_qa"
    ):
        return resolution
    if not resolution.direct_evidence_required:
        return resolution
    if index is not None and _source_lookup_preserves_user_terms(resolution, index):
        return resolution
    return TurnIntentResolution(
        intent="material_overview",
        canonical_request=resolution.canonical_request or user_input,
        confidence=resolution.confidence,
        answer_mode=ANSWER_MODE_FROM_EVIDENCE,
        answer_format=resolution.answer_format,
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        retrieval_query=_overview_resolution_query(resolution, user_input, default_plan),
    )


def _overview_resolution_query(
    resolution: TurnIntentResolution,
    user_input: str,
    default_plan: LearningTurnPlan,
) -> str:
    for candidate in (
        resolution.retrieval_query,
        default_plan.retrieval_query or "",
        resolution.canonical_request,
        user_input,
        default_plan.original_user_input,
    ):
        if candidate and not _lacks_retrievable_content(candidate):
            return candidate
    return ""


def _unresolved_followup_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
) -> TurnIntentResolution:
    if resolution.intent or prior_contract is None or not _overview_turn(default_plan):
        return resolution
    return TurnIntentResolution(
        intent=prior_contract.resolved_intent or "source_qa",
        canonical_request=user_input,
        confidence=resolution.confidence,
        is_followup=True,
        followup_target=prior_contract.canonical_request or prior_contract.original_user_input,
        answer_mode=ANSWER_MODE_REASON_FROM_PRIOR,
        answer_format=prior_contract.answer_format,
        retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
        retrieval_query="",
        prior_answer_reference=True,
    )


def _stabilized_followup_intent_resolution(
    resolution: TurnIntentResolution,
    *,
    user_input: str = "",
    prior_intent: str,
) -> TurnIntentResolution:
    if resolution.intent in {"heph_action", "heph_help"}:
        return replace(
            resolution,
            retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
            retrieval_query="",
            direct_evidence_required=False,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    if (
        resolution.direct_evidence_required
        and resolution.intent != "source_qa"
        and resolution.answer_mode == ANSWER_MODE_FROM_EVIDENCE
    ):
        retrieval_query = resolution.retrieval_query or resolution.canonical_request
        retrieval_strategy = (
            RETRIEVAL_STRATEGY_RETRIEVE
            if resolution.retrieval_strategy
            in {RETRIEVAL_STRATEGY_NONE, RETRIEVAL_STRATEGY_OVERVIEW}
            else resolution.retrieval_strategy
        )
        return replace(
            resolution,
            intent="source_qa",
            retrieval_strategy=retrieval_strategy,
            retrieval_query=retrieval_query,
        )
    if (
        resolution.intent == "material_overview"
        and resolution.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and (
            not resolution.is_followup
            or prior_intent not in _CONTINUABLE_MATERIAL_INTENTS
            or resolution.answer_format != ANSWER_FORMAT_PLAIN
        )
    ):
        return replace(
            resolution,
            answer_mode=ANSWER_MODE_FROM_EVIDENCE,
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query=(
                resolution.retrieval_query or resolution.canonical_request or user_input
            ),
        )
    if (
        prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR
    ):
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
            prior_answer_positions=(),
            prior_answer_position_basis="",
        )
    if (
        prior_intent in {"material_overview", "topic_presentation"}
        and resolution.is_followup
        and resolution.intent == "source_qa"
        and resolution.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and not resolution.direct_evidence_required
        and (resolution.prior_answer_reference or resolution.followup_target.strip())
    ):
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
    if prior_intent in _CONTINUABLE_MATERIAL_INTENTS and resolution.intent in {
        "scaffold_request",
        "hint_request",
        "material_review",
    }:
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
            retrieval_strategy=(
                resolution.retrieval_strategy
                if resolution.retrieval_strategy != RETRIEVAL_STRATEGY_NONE
                else RETRIEVAL_STRATEGY_REUSE_PRIOR
            ),
        )
    if (
        prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR
        and resolution.answer_format == ANSWER_FORMAT_PLAIN
    ):
        if not _transform_resolution_points_at_prior_answer(
            resolution,
            user_input=user_input,
        ):
            return replace(resolution, answer_mode=ANSWER_MODE_FROM_EVIDENCE)
        return replace(
            resolution,
            intent=prior_intent,
            is_followup=True,
            prior_answer_reference=True,
        )
    if (
        resolution.is_followup
        and prior_intent in _CONTINUABLE_MATERIAL_INTENTS
        and resolution.intent in {"priority_request", "driven_learning_calibration"}
    ):
        return replace(resolution, intent=prior_intent)
    return resolution


def _transform_resolution_points_at_prior_answer(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
) -> bool:
    if resolution.prior_answer_positions:
        return True
    if not (resolution.prior_answer_reference or resolution.followup_target.strip()):
        return False
    user_tokens = frozenset(tokenize(user_input))
    resolved_tokens = frozenset(
        token
        for text in (resolution.canonical_request, resolution.followup_target)
        for token in tokenize(text)
    )
    if user_tokens and not any(
        _query_has_matching_term(token, resolved_tokens) for token in user_tokens
    ):
        return False
    request_tokens = frozenset(tokenize(resolution.canonical_request))
    if len(request_tokens) <= _PRIOR_REFERENCE_SHORT_TOKEN_LIMIT:
        return True
    target_tokens = frozenset(tokenize(resolution.followup_target))
    if not target_tokens:
        return False
    overlap = len(request_tokens & target_tokens) / min(len(request_tokens), len(target_tokens))
    return overlap >= _PRIOR_REFERENCE_MIN_OVERLAP


def _intent_normalization_context(
    user_input: str,
    conversation: Conversation | None,
    *,
    prior_intent: str = "",
    prior_contract: TurnContract | None = None,
) -> str:
    lines: list[str] = []
    if routing_context := heph_product_routing_context():
        lines.extend(
            (
                "Heph self-knowledge routing context:",
                routing_context,
                "",
            )
        )
    if prior_context := _prior_turn_contract_intent_context(prior_contract, prior_intent):
        lines.extend(("Prior turn:", prior_context, ""))
    last_assistant = _last_assistant_message(conversation, user_input)
    if last_assistant is not None:
        lines.extend(
            (
                "Last reply:",
                _trace_excerpt(last_assistant.content, limit=240),
                "",
            )
        )
    lines.extend(("Current user request:", user_input.strip()))
    return "\n".join(lines)


def _prior_turn_contract_intent_context(
    contract: TurnContract | None,
    prior_intent: str,
) -> str:
    if contract is None and not prior_intent:
        return ""
    if contract is None:
        return f"intent={prior_intent}; refs=0."
    return (
        f"intent={contract.resolved_intent or prior_intent or 'unknown'}; "
        f"mode={contract.answer_mode}; retrieval={contract.retrieval_strategy}; "
        f"refs={_intent_contract_refs_text(contract.evidence_refs)}."
    )
