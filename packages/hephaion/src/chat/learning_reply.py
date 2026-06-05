"""Learning-reply selection, fallback, and post-processing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rag.context import TurnEvidence
from runtime.config import ChatConfig
from study.prompt_plans import LearningTurnPlan
from study.state import LearningAction

from chat.evidence import ResolvedTurnPlan
from chat.evidence import evidence_refs as _evidence_refs
from chat.material_state import (
    _missing_indexed_material_reply,
    _no_matching_indexed_evidence_reply,
)
from chat.reply_text import (
    _localize_deterministic_reply,
    _strip_leading_control_json,
    _strip_tool_call_markup,
    _unicode_math_reply,
)
from chat.turn_contract import (
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from chat.turn_predicates import (
    _overview_turn,
)

if TYPE_CHECKING:
    from chat.session import ChatSession


from chat.conversation_context import (
    _recent_current_evidence_citation_ids,
)
from chat.overview_reply import (
    _compact_overview_citation_inventory,
    _contract_requests_list,
    _contract_requests_table,
    _deterministic_overview_fallback_reply,
    _material_overview_turn,
    _needs_overview_fallback,
    _overview_fallback_reply,
    _overview_model_fallback_reply,
    _overview_unavailable_reply,
)
from chat.prior_answer import (
    _prior_answer_list_transform_reply,
    _prior_answer_position_absence_reply,
    _prior_answer_single_citation_reply,
    _prior_answer_source_object_absence_reply,
    _prior_answer_target_phrase_reply,
)
from chat.reply_repair import (
    _evidence_quote_repair_reply,
    _normalize_escaped_evidence_citations,
    _normalize_structural_table_reply,
    _run_bounded_internal_repairs,
)
from chat.turn_outputs import _DeterministicLearningReply, _ProcessedLearningReply


def _postprocess_learning_reply(
    plan: LearningTurnPlan,
    raw_reply: str,
    visible_reply: str,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str,
    config: ChatConfig,
) -> _ProcessedLearningReply:
    shape_reply = _shape_validation_reply(raw_reply)
    original_shape_reply = shape_reply
    if _needs_overview_fallback(
        plan,
        shape_reply,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    ):
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            rejected_reply=shape_reply,
            contract=resolved.turn_contract,
        )
        raw_reply = fallback_reply or _overview_unavailable_reply()
        visible_reply = raw_reply

    visible_reply, pass_count = _run_bounded_internal_repairs(
        plan,
        visible_reply,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
        user_input=user_input,
        config=config,
    )
    visible_reply = _normalize_structural_table_reply(visible_reply)
    visible_reply = _unicode_math_reply(visible_reply)
    if (
        _needs_overview_fallback(
            plan,
            visible_reply,
            resolved.turn_evidence,
            contract=resolved.turn_contract,
        )
        and resolved.turn_evidence is not None
    ):
        repaired_reply = _overview_model_fallback_reply(
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            rejected_reply=visible_reply,
            allow_table=_contract_requests_table(resolved.turn_contract),
            allow_list=_contract_requests_list(resolved.turn_contract),
        )
        if not repaired_reply and resolved.turn_evidence is not None:
            repaired_reply = _compact_overview_citation_inventory(
                original_shape_reply,
                resolved.turn_evidence,
                allow_table=_contract_requests_table(resolved.turn_contract),
                allow_list=_contract_requests_list(resolved.turn_contract),
            )
        if not repaired_reply and resolved.turn_evidence is not None:
            repaired_reply = _overview_fallback_reply(
                plan,
                resolved.turn_evidence,
                user_input=user_input,
                config=config,
                rejected_reply=visible_reply,
                contract=resolved.turn_contract,
            )
        raw_reply = repaired_reply or _overview_unavailable_reply()
        visible_reply = raw_reply
    return _ProcessedLearningReply(
        raw_reply=raw_reply,
        visible_reply=visible_reply,
        pass_count=pass_count,
    )


def _shape_validation_reply(raw_reply: str) -> str:
    cleaned = _strip_tool_call_markup(raw_reply).strip()
    cleaned = _normalize_escaped_evidence_citations(cleaned)
    return _strip_leading_control_json(cleaned)


def _deterministic_learning_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> _DeterministicLearningReply | None:
    if prior_absence_reply := _prior_answer_position_absence_reply(
        session,
        resolved.turn_contract,
    ):
        return prior_absence_reply
    if prior_source_object_absence_reply := _prior_answer_source_object_absence_reply(
        session,
        resolved.turn_contract,
    ):
        return prior_source_object_absence_reply
    if abstain_reply := _source_qa_abstain_reply(plan, resolved):
        return _DeterministicLearningReply(abstain_reply, citation_required=False)
    if prior_list_transform_reply := _prior_answer_list_transform_reply(
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_list_transform_reply
    if prior_target_phrase_reply := _prior_answer_target_phrase_reply(
        session,
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_target_phrase_reply
    if prior_single_citation_reply := _prior_answer_single_citation_reply(
        session,
        resolved.turn_contract,
        resolved.turn_evidence,
    ):
        return prior_single_citation_reply
    if overview_followup_reply := _deterministic_broad_overview_followup_reply(
        session,
        plan,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    ):
        source_refs = _evidence_refs(resolved.turn_evidence) if resolved.turn_evidence else None
        return _DeterministicLearningReply(overview_followup_reply, source_refs=source_refs)
    if resolved.turn_evidence is not None and resolved.turn_evidence.items:
        return None
    if missing_reply := _missing_indexed_material_reply(session, plan.action):
        return _DeterministicLearningReply(missing_reply, updates_learning_state=False)
    if no_match_reply := _no_matching_indexed_evidence_reply(
        session,
        plan,
        resolved.turn_contract,
    ):
        return _DeterministicLearningReply(no_match_reply)
    return None


def _source_qa_abstain_reply(
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
) -> str:
    assessment = resolved.evidence_assessment
    if (
        plan.action is not LearningAction.SOURCE_QA
        or (resolved.turn_evidence is None and bool(plan.retrieval_query))
        or assessment is None
        or assessment.sufficient
        or assessment.recommended_action != "abstain"
    ):
        return ""
    return "The current evidence does not contain a direct source answer for this request."


def _plain_empty_reply(user_input: str, config: ChatConfig) -> str:
    return _localize_deterministic_reply(
        "I could not generate a response.",
        user_input=user_input,
        config=config,
    )


def _empty_learning_reply(
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str,
    config: ChatConfig,
) -> str:
    fallback_reply = _source_qa_evidence_reply(
        plan,
        resolved.turn_evidence,
        contract=resolved.turn_contract,
    )
    if fallback_reply:
        should_localize = True
    else:
        fallback_reply = _overview_fallback_reply(
            plan,
            resolved.turn_evidence,
            user_input=user_input,
            config=config,
            contract=resolved.turn_contract,
        )
        should_localize = not bool(fallback_reply)
    if not fallback_reply:
        fallback_reply = _generic_empty_learning_reply(plan)
    return (
        _localize_deterministic_reply(fallback_reply, user_input=user_input, config=config)
        if should_localize
        else fallback_reply
    )


def _generic_empty_learning_reply(plan: LearningTurnPlan) -> str:
    if _overview_turn(plan):
        return _overview_unavailable_reply()
    if plan.action is LearningAction.ASSESS:
        return "PARTIAL: I could not generate a grounded assessment."
    return "I could not generate a prompt."


def _deterministic_broad_overview_followup_reply(
    session: ChatSession,
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None,
) -> str:
    if (
        evidence is None
        or not evidence.items
        or contract is None
        or not contract.is_followup
        or _contract_requests_table(contract)
        or not _material_overview_turn(plan, contract)
    ):
        return ""
    if contract.retrieval_strategy not in {
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
    }:
        return ""
    excluded_ids = _recent_current_evidence_citation_ids(
        session.conversation,
        contract.original_user_input,
        evidence,
    )
    reply = _deterministic_overview_fallback_reply(
        evidence,
        excluded_evidence_ids=excluded_ids,
    )
    if reply:
        return reply
    return _deterministic_overview_fallback_reply(evidence)


def _source_qa_evidence_reply(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> str:
    if not _can_answer_source_qa_from_evidence(plan, evidence, contract=contract):
        return ""
    assert evidence is not None
    return _evidence_quote_repair_reply("", evidence)


def _can_answer_source_qa_from_evidence(
    plan: LearningTurnPlan,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if evidence is None or not evidence.items:
        return False
    return plan.action is LearningAction.SOURCE_QA and (
        plan.requires_direct_evidence
        or (contract is not None and contract.direct_evidence_required)
    )
