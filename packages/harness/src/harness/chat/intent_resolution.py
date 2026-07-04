"""Model-backed user intent resolution and default material route stabilization."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation
from ai.runtime.errors import EngineError
from extensions.contracts import heph_product_routing_context

import harness.chat.intent as _chat_intent
from harness.chat.turn_contract import (
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
    TurnIntentResolution,
    intent_resolution_from_payload,
)
from harness.chat.turn_predicates import (
    _overview_turn,
    _trace_excerpt,
)
from harness.documents.prompt_plans import DocumentTurnPlan

if TYPE_CHECKING:
    from harness.rag.index import ArmoryIndex


import harness.chat.model_text as _model_text
from harness.chat.conversation_context import _last_assistant_message
from harness.chat.followup_intent_resolution import (
    _CONTINUABLE_MATERIAL_INTENTS,
    _stabilized_followup_intent_resolution,
)
from harness.chat.turn_contract_checks import (
    _intent_contract_refs_text,
)
from harness.chat.turn_query import (
    _corpus_named_material_query,
    _lacks_retrievable_content,
    _query_reuses_surface,
    _source_lookup_preserves_user_terms,
)

_MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = _chat_intent.MODEL_NORMALIZED_CONFIDENCE_THRESHOLD
_LEARNING_INTENT_NORMALIZATION_SCHEMA = _chat_intent.LEARNING_INTENT_NORMALIZATION_SCHEMA
_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = (
    _chat_intent.LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT
)
_classifier_intent_from_payload = _chat_intent.classifier_intent_from_payload
_normalized_document_intent_from_payload = _chat_intent.normalized_document_intent_from_payload
_normalized_confidence = _chat_intent.normalized_confidence


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
    default_plan: DocumentTurnPlan,
    prior_contract: TurnContract | None,
    index: ArmoryIndex | None,
) -> TurnIntentResolution:
    if _should_default_to_material_overview(
        resolution,
        user_input=user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
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
    if not _should_convert_source_route_to_overview(
        resolution,
        user_input=user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
        index=index,
    ):
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


def _should_default_to_material_overview(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: DocumentTurnPlan,
    prior_contract: TurnContract | None,
) -> bool:
    return (
        prior_contract is None
        and _overview_turn(default_plan)
        and _lacks_retrievable_content(user_input)
        and (not resolution.intent or resolution.intent in _CONTINUABLE_MATERIAL_INTENTS)
    )


def _should_convert_source_route_to_overview(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
    default_plan: DocumentTurnPlan,
    prior_contract: TurnContract | None,
    index: ArmoryIndex | None,
) -> bool:
    if (
        prior_contract is not None
        or not _overview_turn(default_plan)
        or resolution.intent != "source_qa"
    ):
        return False
    if not resolution.direct_evidence_required:
        return False
    if _direct_source_resolution_should_keep_source_route(resolution, user_input=user_input):
        return False
    return index is None or not _source_lookup_preserves_user_terms(resolution, index)


def _direct_source_resolution_should_keep_source_route(
    resolution: TurnIntentResolution,
    *,
    user_input: str,
) -> bool:
    retrieval_query = resolution.retrieval_query.strip()
    if retrieval_query and _query_reuses_surface(retrieval_query, user_input):
        return True
    canonical_request = resolution.canonical_request.strip()
    return (
        not retrieval_query
        and bool(canonical_request)
        and _query_reuses_surface(
            canonical_request,
            user_input,
        )
    )


def _overview_resolution_query(
    resolution: TurnIntentResolution,
    user_input: str,
    default_plan: DocumentTurnPlan,
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
    default_plan: DocumentTurnPlan,
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
        f"refs={_intent_contract_refs_text(contract.evidence_refs)}; "
        f"validation={contract.validation_result or 'unknown'}."
    )
