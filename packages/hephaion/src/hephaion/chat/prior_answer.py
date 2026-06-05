"""Prior-answer context and deterministic prior-answer transforms."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.runtime.conversation import Conversation, Message

from hephaion.chat.citation_patterns import (
    _INLINE_QUOTED_TEXT_RE,
    _OVERVIEW_CITATION_BRACKET_RE,
    _OVERVIEW_CITATION_ID_RE,
    _OVERVIEW_CITATION_TOKEN_RE,
    _TRAILING_EVIDENCE_CITATION_GROUP_RE,
)
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.evidence import build_priority_context as _build_priority_context
from hephaion.chat.evidence import evidence_refs as _evidence_refs
from hephaion.chat.material_state import (
    _should_use_material_answer_conversation_window,
)
from hephaion.chat.turn_contract import (
    ANSWER_FORMAT_LIST,
    ANSWER_MODE_FROM_EVIDENCE,
    ANSWER_MODE_REASON_FROM_PRIOR,
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    TurnContract,
)
from hephaion.chat.turn_predicates import (
    _count_label,
    _trace_excerpt,
)
from hephaion.rag.context import EvidenceChunk, TurnEvidence
from hephaion.study.prompt_plans import LearningTurnPlan
from hephaion.study.state import LearningAction, LearningPhase, LearningState

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession


from hephaion.chat.conversation_context import _recent_assistant_messages
from hephaion.chat.evidence_prompt import _append_evidence_assessment_prompt
from hephaion.chat.reply_repair import _evidence_pointer_excerpt
from hephaion.chat.turn_contract_checks import _intent_contract_refs_text
from hephaion.chat.turn_outputs import _DeterministicLearningReply
from hephaion.chat.turn_query import _normalized_query_text

_PRIOR_ANSWER_CONTEXT_LIMIT = 500


def _isolated_recall_conversation(
    plan: LearningTurnPlan,
    original_learning_state: LearningState,
    user_input: str,
    contract: TurnContract | None,
) -> Conversation | None:
    if _should_use_material_answer_conversation_window(plan, contract):
        return None
    if plan.action in {
        LearningAction.CALIBRATE,
        LearningAction.PROMPT_RECALL,
        LearningAction.REFUSE_REVEAL,
        LearningAction.WAIT_READY_REMINDER,
    }:
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    if (
        original_learning_state.phase is LearningPhase.RECALL
        and plan.action is LearningAction.CHAT
        and plan.retrieval_query is None
    ):
        conversation = Conversation()
        conversation.add("user", user_input)
        return conversation
    return None


def _learning_extra_system_prompt(
    session: ChatSession,
    plan: LearningTurnPlan,
    resolved: ResolvedTurnPlan,
    *,
    user_input: str = "",
) -> str:
    contract_context = _turn_contract_prompt_context(resolved.turn_contract)
    extra_system_prompt = (
        f"{plan.prompt}\n\n{contract_context}" if contract_context else plan.prompt
    )
    prior_answer_context = _prior_answer_prompt_context(
        session.conversation,
        user_input=user_input,
        contract=resolved.turn_contract,
    )
    if prior_answer_context:
        extra_system_prompt = f"{extra_system_prompt}\n\n{prior_answer_context}"
    if plan.action is LearningAction.PRIORITY:
        priority_context = _build_priority_context(session)
        if priority_context:
            extra_system_prompt = f"{extra_system_prompt}\n\n{priority_context}"
    return _append_evidence_assessment_prompt(extra_system_prompt, resolved)


def _turn_contract_prompt_context(contract: TurnContract | None) -> str:
    if contract is None:
        return ""
    ask = _trace_excerpt(contract.canonical_request or contract.original_user_input, limit=140)
    lines = [
        (
            "Turn: "
            f"intent={contract.resolved_intent or 'unknown'}; "
            f"ask={ask}; "
            f"mode={contract.answer_mode}; fmt={contract.answer_format}; "
            f"retrieval={contract.retrieval_strategy}; cite={contract.citation_required}."
        )
    ]
    if contract.prior_turn_original_user_input and _contract_context_needs_prior_turn(contract):
        lines.append(
            "Prior: "
            f"intent={contract.prior_turn_resolved_intent or 'unknown'}; "
            f"refs={_intent_contract_refs_text(contract.prior_turn_evidence_refs)}."
        )
    lines.append(
        "Use current evidence for facts. Conversation text resolves references or requested shape "
        "only. Cite source claims; keep inference brief and clearly separated; keep compact; "
        "no offers or next-step prompts."
    )
    if contract.direct_evidence_required:
        lines.append(
            "Direct-evidence turn: state only claims explicit in current evidence; "
            "otherwise abstain."
        )
    if contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
        lines.append("Pure rewrite: preserve prior claims and citations; add no new source facts.")
    elif contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        lines.append(
            "Referenced-answer reasoning: answer the user's reasoning/application request "
            "directly. Use the prior answer to identify the claim, cite source facts from "
            "evidence, and keep concise inference separate. Prior answer citations are not "
            "current evidence IDs."
        )
    return "\n".join(lines)


def _contract_context_needs_prior_turn(contract: TurnContract) -> bool:
    if (
        contract.answer_mode == ANSWER_MODE_FROM_EVIDENCE
        and contract.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    ):
        return False
    return contract.is_followup or contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }


def _prior_turn_canonical_request_excerpt(contract: TurnContract) -> str:
    return _trace_excerpt(contract.prior_turn_canonical_request, limit=160) or "unspecified"


def _prior_answer_prompt_context(
    conversation: Conversation,
    *,
    user_input: str,
    contract: TurnContract | None,
) -> str:
    if contract is None or not _should_include_prior_answer_context(contract):
        return ""
    recent_assistant = _prior_answer_context_messages(
        conversation,
        user_input,
        contract=contract,
    )
    if not recent_assistant:
        return ""
    context_lines: list[str] = ["Prior assistant reply (reference context only):"]
    for index, message in enumerate(recent_assistant, start=1):
        excerpt = _prior_answer_context_excerpt(message.content)
        if not excerpt:
            continue
        context_lines.extend((f"Answer {index}:", excerpt))
    if len(context_lines) == 1:
        return ""
    last_assistant = recent_assistant[-1]
    structure = (
        _prior_answer_structure_context(last_assistant.content)
        if contract.prior_answer_reference or contract.prior_answer_positions
        else ""
    )
    if structure:
        context_lines.extend(("Prior answer structure:", structure))
    if contract.answer_mode == ANSWER_MODE_REASON_FROM_PRIOR:
        context_lines.append(
            "Use this to identify the referenced claim. Answer the user's reasoning/application "
            "request directly; cite current evidence IDs and keep concise inference separate."
        )
    elif contract.answer_mode == ANSWER_MODE_TRANSFORM_PRIOR:
        context_lines.append(
            "If this is a pure rewrite, preserve claims and citations and add no facts."
        )
    else:
        context_lines.append(
            "Use this only to resolve references. Cite only current evidence IDs."
        )
    return "\n".join(context_lines)


def _prior_answer_context_excerpt(content: str) -> str:
    excerpt = _trace_excerpt(content, limit=_PRIOR_ANSWER_CONTEXT_LIMIT)
    cleaned = _OVERVIEW_CITATION_BRACKET_RE.sub(_prior_context_citation_bracket, excerpt)
    return re.sub(r"\s+([,.;:!?])", r"\1", cleaned).strip()


def _prior_context_citation_bracket(match: re.Match[str]) -> str:
    citations = tuple(_OVERVIEW_CITATION_TOKEN_RE.finditer(match.group("body")))
    if not citations:
        return match.group(0)
    return ""


def _prior_answer_structure_context(content: str) -> str:
    cited_claims = _prior_answer_cited_claims(content)
    list_item_count = _prior_answer_list_item_count(content)
    lines = [
        f"- cited_claims={len(cited_claims)}",
        f"- list_items={list_item_count}",
        "- If the requested prior-answer item is absent, say it is not available.",
    ]
    if cited_claims:
        lines.append("- cited_claims_in_order:")
        lines.extend(
            f"  {index}. {claim}" for index, claim in enumerate(cited_claims[:5], start=1)
        )
    return "\n".join(lines)


def _prior_answer_cited_claims(content: str) -> tuple[str, ...]:
    claims: list[str] = []
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content):
        if not _citation_ends_prior_claim(content, match.end()):
            continue
        fragment = _prior_answer_fragment_before_citation(content, match.start())
        if not fragment:
            continue
        claim = fragment
        if claim not in claims:
            claims.append(claim)
    return tuple(claims)


def _citation_ends_prior_claim(content: str, citation_end: int) -> bool:
    index = citation_end
    while index < len(content) and content[index] in " \t)]}":
        index += 1
    return index >= len(content) or content[index] in ".!?\n" or content[index].isupper()


def _prior_answer_fragment_before_citation(content: str, citation_start: int) -> str:
    group_start = _prior_citation_group_start(content, citation_start)
    prefix = content[:group_start].rstrip()
    if not prefix:
        return ""
    if prefix[-1:] in ".!?":
        prefix = prefix[:-1].rstrip()
    boundary = _prior_answer_sentence_boundary(prefix)
    boundary = max(boundary, _previous_prior_citation_boundary(content, before=group_start))
    fragment = prefix[boundary + 1 :].strip()
    fragment = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", fragment).strip()
    return _trace_excerpt(fragment, limit=180)


def _prior_answer_sentence_boundary(prefix: str) -> int:
    boundary = -1
    for match in re.finditer(r"(?:[.!?;](?=\s)|\n)", prefix):
        boundary = match.start()
    return boundary


def _prior_citation_group_start(content: str, citation_start: int) -> int:
    prefix = content[:citation_start]
    match = _TRAILING_EVIDENCE_CITATION_GROUP_RE.search(prefix)
    return match.start() if match is not None else citation_start


def _previous_prior_citation_boundary(content: str, *, before: int) -> int:
    boundary = -1
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content[:before]):
        if _citation_ends_prior_claim(content, match.end()):
            boundary = max(boundary, match.end() - 1)
    return boundary


def _prior_answer_list_item_count(content: str) -> int:
    return sum(1 for line in content.splitlines() if re.match(r"\s*(?:[-*+]\s+|\d+[.)]\s+)", line))


def _should_include_prior_answer_context(contract: TurnContract | None) -> bool:
    return (
        contract is not None
        and contract.is_followup
        and _contract_needs_prior_answer_context(contract)
    )


def _prior_answer_context_messages(
    conversation: Conversation,
    user_input: str,
    *,
    contract: TurnContract,
) -> tuple[Message, ...]:
    limit = 5 if contract.prior_answer_positions else 1
    recent = _recent_assistant_messages(conversation, user_input, limit=limit)
    if not contract.prior_answer_reference:
        return recent
    selected = _prior_answer_message_for_contract(recent, contract)
    return (selected,) if selected is not None else ()


def _prior_answer_message_for_contract(
    messages: Sequence[Message],
    _contract: TurnContract,
) -> Message | None:
    if not messages:
        return None
    return messages[-1]


def _contract_needs_prior_answer_context(contract: TurnContract) -> bool:
    return contract.prior_answer_reference or contract.answer_mode in {
        ANSWER_MODE_TRANSFORM_PRIOR,
        ANSWER_MODE_REASON_FROM_PRIOR,
    }


def _contract_evidence_refs_text(contract: TurnContract) -> str:
    return ", ".join(contract.evidence_refs) if contract.evidence_refs else "none"


def _contract_prior_positions_text(contract: TurnContract) -> str:
    return (
        ", ".join(str(position) for position in contract.prior_answer_positions)
        if contract.prior_answer_positions
        else "none"
    )


def _prior_answer_position_absence_reply(
    session: ChatSession,
    contract: TurnContract | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.prior_answer_position_basis not in {"cited_claims", "list_items"}
    ):
        return None
    requested_positions = contract.prior_answer_positions or _implicit_prior_answer_positions(
        contract,
    )
    if not requested_positions:
        return None
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    selected_answer = _prior_answer_message_for_contract(recent_assistant, contract)
    if selected_answer is None:
        return None
    available_count = _prior_answer_position_basis_count(
        selected_answer.content,
        basis=contract.prior_answer_position_basis,
    )
    missing_positions = tuple(
        position for position in requested_positions if position > available_count
    )
    if available_count == 0 and contract.prior_answer_position_basis == "list_items":
        cited_claim_count = len(_prior_answer_cited_claims(selected_answer.content))
        cited_claims_cover_positions = all(
            position <= cited_claim_count for position in requested_positions
        )
        if cited_claim_count and cited_claims_cover_positions:
            return None
    if not missing_positions:
        return None
    reply = _prior_missing_position_text(
        available_count=available_count,
        missing_positions=missing_positions,
        basis=contract.prior_answer_position_basis,
    )
    return _DeterministicLearningReply(reply, citation_required=False)


def _prior_answer_source_object_absence_reply(
    session: ChatSession,
    contract: TurnContract | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.prior_answer_positions
        or not contract.citation_required
    ):
        return None
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    selected_answer = _prior_answer_message_for_contract(recent_assistant, contract)
    if selected_answer is None or _prior_answer_has_any_structure(selected_answer.content):
        return None
    return _DeterministicLearningReply(
        "The prior answer does not contain a cited material claim to extend.",
        citation_required=False,
    )


def _prior_answer_list_transform_reply(
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or contract.answer_mode != ANSWER_MODE_TRANSFORM_PRIOR
        or contract.answer_format != ANSWER_FORMAT_LIST
        or evidence is None
        or len(evidence.items) < 2
    ):
        return None
    cited_items = [
        (item, excerpt) for item in evidence.items if (excerpt := _evidence_pointer_excerpt(item))
    ][:2]
    if not cited_items:
        return None
    reply = "\n".join(
        f"{index}. {excerpt} [{item.evidence_id}]"
        for index, (item, excerpt) in enumerate(cited_items, start=1)
    )
    return _DeterministicLearningReply(reply, source_refs=_evidence_refs(evidence))


def _prior_answer_target_phrase_reply(
    session: ChatSession,
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.answer_mode not in {ANSWER_MODE_FROM_EVIDENCE, ANSWER_MODE_REASON_FROM_PRIOR}
        or evidence is None
        or not evidence.items
    ):
        return None
    selected_answer = _selected_prior_answer(session, contract)
    if selected_answer is None:
        return None
    for phrase in _quoted_followup_target_phrases(contract):
        if not _normalized_text_contains(selected_answer.content, phrase):
            continue
        item = _evidence_item_containing_text(evidence, phrase)
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item)
        if not excerpt:
            continue
        return _DeterministicLearningReply(
            f"“{excerpt}” [{item.evidence_id}].",
            source_refs=_evidence_refs(evidence),
        )
    return None


def _prior_answer_single_citation_reply(
    session: ChatSession,
    contract: TurnContract | None,
    evidence: TurnEvidence | None,
) -> _DeterministicLearningReply | None:
    if (
        contract is None
        or not contract.prior_answer_reference
        or contract.answer_mode != ANSWER_MODE_FROM_EVIDENCE
        or contract.prior_answer_positions
        or not contract.citation_required
        or _quoted_followup_target_phrases(contract)
        or evidence is None
        or not evidence.items
    ):
        return None
    selected_answer = _selected_prior_answer(session, contract)
    if selected_answer is None:
        return None
    cited_refs = _prior_answer_citation_refs(
        selected_answer.content,
        session.last_turn_contract,
    )
    if len(cited_refs) != 1:
        return None
    item = _evidence_item_by_ref(evidence, cited_refs[0])
    if item is None:
        return None
    excerpt = _evidence_pointer_excerpt(item)
    if not excerpt:
        return None
    return _DeterministicLearningReply(
        f"“{excerpt}” [{item.evidence_id}].",
        source_refs=_evidence_refs(evidence),
    )


def _selected_prior_answer(session: ChatSession, contract: TurnContract) -> Message | None:
    recent_assistant = _recent_assistant_messages(
        session.conversation,
        contract.original_user_input,
        limit=5,
    )
    return _prior_answer_message_for_contract(recent_assistant, contract)


def _quoted_followup_target_phrases(contract: TurnContract) -> tuple[str, ...]:
    text = " ".join(
        part for part in (contract.followup_target, contract.canonical_request) if part
    )
    phrases: list[str] = []
    seen: set[str] = set()
    for match in _INLINE_QUOTED_TEXT_RE.finditer(text):
        phrase = " ".join(match.group("text").split())
        key = _normalized_query_text(phrase)
        if not key or key in seen or not _quoted_followup_phrase_is_semantic(phrase):
            continue
        phrases.append(phrase)
        seen.add(key)
    return tuple(phrases)


def _quoted_followup_phrase_is_semantic(phrase: str) -> bool:
    without_citations = _OVERVIEW_CITATION_ID_RE.sub(" ", phrase)
    compact = "".join(char for char in without_citations if char.isalnum())
    return len(compact) >= 3


def _normalized_text_contains(text: str, needle: str) -> bool:
    normalized_text = _normalized_query_text(text)
    normalized_needle = _normalized_query_text(needle)
    return bool(normalized_needle and normalized_needle in normalized_text)


def _evidence_item_containing_text(
    evidence: TurnEvidence,
    text: str,
) -> EvidenceChunk | None:
    return next(
        (
            item
            for item in evidence.items
            if _normalized_text_contains(f"{item.chunk.heading}\n{item.content}", text)
        ),
        None,
    )


def _prior_answer_citation_refs(
    content: str,
    prior_contract: TurnContract | None,
) -> tuple[str, ...]:
    if prior_contract is None or not prior_contract.evidence_refs:
        return ()
    cited_refs: list[str] = []
    seen: set[str] = set()
    for match in _OVERVIEW_CITATION_ID_RE.finditer(content):
        ref = _prior_citation_ref(match.group("id"), prior_contract.evidence_refs)
        if not ref or ref in seen:
            continue
        cited_refs.append(ref)
        seen.add(ref)
    return tuple(cited_refs)


def _prior_citation_ref(citation_number: str, refs: Sequence[str]) -> str:
    try:
        index = int(citation_number) - 1
    except ValueError:
        return ""
    if index < 0 or index >= len(refs):
        return ""
    return refs[index]


def _evidence_item_by_ref(evidence: TurnEvidence, ref: str) -> EvidenceChunk | None:
    return next((item for item in evidence.items if _evidence_item_ref(item) == ref), None)


def _evidence_item_ref(item: EvidenceChunk) -> str:
    return f"{item.source}#chunk={item.chunk_index}"


def _prior_answer_position_basis_count(content: str, *, basis: str) -> int:
    if basis == "cited_claims":
        return len(_prior_answer_cited_claims(content))
    if basis == "list_items":
        return _prior_answer_list_item_count(content)
    return 0


def _prior_answer_has_any_structure(content: str) -> bool:
    return (
        bool(_prior_answer_cited_claims(content))
        or _prior_answer_list_item_count(content) > 0
        or _OVERVIEW_CITATION_ID_RE.search(content) is not None
    )


def _implicit_prior_answer_positions(contract: TurnContract) -> tuple[int, ...]:
    if contract.prior_answer_position_basis == "list_items":
        return (2,)
    return ()


def _prior_missing_position_text(
    *,
    available_count: int,
    missing_positions: Sequence[int],
    basis: str,
) -> str:
    missing = _number_list_text(missing_positions)
    label = _prior_position_label(basis)
    return (
        "That prior-answer position is absent: the referenced answer has only "
        f"{_count_label(available_count, label)}, so position {missing} "
        "is not available."
    )


def _prior_position_label(basis: str) -> str:
    if basis == "list_items":
        return "separate list/table point"
    return "cited claim"


def _number_list_text(numbers: Sequence[int]) -> str:
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    return ", ".join(str(number) for number in numbers[:-1]) + f", and {numbers[-1]}"
