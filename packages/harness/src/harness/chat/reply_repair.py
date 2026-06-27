"""Bounded reply repair and citation-shape normalization."""

from __future__ import annotations

import re
from html import unescape

from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation

import harness.chat.model_text as _model_text
from harness.agent.citation import VerificationResult, verify_citations
from harness.chat.citation_patterns import (
    _CITATION_ONLY_REPLY_RE,
    _ESCAPED_EVIDENCE_CITATION_RE,
    _EVIDENCE_CITATION_TEXT_RE,
    _INLINE_QUOTED_TEXT_RE,
    _OVERVIEW_CITATION_ID_RE,
    _PRIVATE_USE_EVIDENCE_CITATION_RE,
)
from harness.chat.overview_reply import (
    _compact_overview_table_reply,
    _contains_markdown_table,
    _deterministic_overview_table,
    _overview_fallback_citation_items,
    _overview_pipe_table_as_markdown,
    _overview_sentence_candidates,
    _overview_unavailable_reply,
    _trim_overview_cue,
)
from harness.chat.reply_text import (
    _strip_leading_control_json,
    _strip_tool_call_markup,
    _strip_unsolicited_learning_followup,
    _unicode_math_reply,
)
from harness.chat.turn_contract import (
    TurnContract,
)
from harness.chat.turn_contract_checks import _contract_requests_table, _plan_requires_citations
from harness.chat.turn_predicates import (
    _overview_turn,
    _trace_excerpt,
)
from harness.chat.turn_query import _normalized_query_text
from harness.rag.context import EvidenceChunk, TurnEvidence
from harness.study.prompt_plans import LearningTurnPlan
from harness.study.state import LearningAction

_THIN_EVIDENCE_POINTER_MAX_WORDS = 8
_MATERIAL_REPLY_MAX_CHARS = 700
_OVERVIEW_MAX_TABLE_CHARS = 1800
_TABLE_MIN_DISTINCT_SOURCES = 2
_MAX_INTERNAL_PASSES = 2


def _repair_missing_evidence_citations(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
) -> str:
    if not _can_repair_evidence_citations(reply, evidence):
        return reply
    assert evidence is not None
    cleaned_reply, verification = _remove_unverified_citation_refs(reply, evidence)
    if appended_reply := _append_required_action_citation(
        plan,
        cleaned_reply,
        evidence,
        verification,
    ):
        return appended_reply
    return cleaned_reply


def _append_required_action_citation(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence,
    verification: VerificationResult,
) -> str:
    if not _should_append_required_action_citation(plan, verification):
        return ""
    first_item = evidence.items[0]
    return f"{reply.rstrip()} [{first_item.evidence_id}]"


def _should_append_required_action_citation(
    plan: LearningTurnPlan,
    verification: VerificationResult,
) -> bool:
    if verification.has_citations or not _plan_requires_citations(plan):
        return False
    return plan.action is not LearningAction.PRESENT


def _can_repair_evidence_citations(reply: str, evidence: TurnEvidence | None) -> bool:
    return bool(reply.strip() and evidence is not None and evidence.items)


def _remove_unverified_citation_refs(
    reply: str,
    evidence: TurnEvidence,
) -> tuple[str, VerificationResult]:
    verification = verify_citations(reply, evidence)
    if not verification.unverified:
        return reply, verification
    cleaned_reply = reply
    for evidence_id in verification.unverified:
        cleaned_reply = re.sub(rf"\s*\[\s*{re.escape(evidence_id)}\s*\]", "", cleaned_reply)
    return cleaned_reply, verify_citations(cleaned_reply, evidence)


def _user_visible_reply(plan: LearningTurnPlan, reply: str) -> str:
    cleaned = _strip_tool_call_markup(reply).strip()
    cleaned = _normalize_escaped_evidence_citations(cleaned)
    cleaned = _strip_leading_control_json(cleaned)
    cleaned = _normalize_structural_table_reply(cleaned)
    cleaned = _unicode_math_reply(cleaned)
    if plan.action is LearningAction.SOURCE_QA:
        cleaned = _strip_unsolicited_learning_followup(cleaned)
    if plan.action is LearningAction.CALIBRATE:
        return _EVIDENCE_CITATION_TEXT_RE.sub("", cleaned).strip()
    return cleaned


def _normalize_escaped_evidence_citations(reply: str) -> str:
    normalized = _ESCAPED_EVIDENCE_CITATION_RE.sub(r"[\1]", reply)
    return _PRIVATE_USE_EVIDENCE_CITATION_RE.sub(r"[\1]", normalized)


def _normalize_structural_table_reply(reply: str) -> str:
    if _contains_markdown_table(reply):
        return reply
    return _overview_pipe_table_as_markdown(reply) or reply


def _should_buffer_learning_output(plan: LearningTurnPlan) -> bool:
    return (
        plan.buffer_response
        or plan.action is LearningAction.CHAT
        or _plan_requires_citations(plan)
    )


def _run_bounded_internal_repairs(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    user_input: str,
    config: ChatConfig,
    contract: TurnContract | None = None,
) -> tuple[str, int]:
    repaired = reply
    passes = 1  # pass 1 = initial model generation
    if _overview_turn(plan) and repaired == _overview_unavailable_reply():
        return repaired, passes
    for _ in range(_MAX_INTERNAL_PASSES - 1):
        previous = repaired
        repaired = _repair_table_source_coverage_output(
            plan,
            repaired,
            evidence,
            contract=contract,
        )
        repaired = _repair_structurally_invalid_evidence_output(
            plan,
            repaired,
            evidence,
            user_input=user_input,
            config=config,
            contract=contract,
        )
        repaired = _repair_unverified_evidence_quotes(repaired, evidence)
        repaired = _repair_missing_evidence_citations(plan, repaired, evidence)
        passes += 1
        if repaired == previous:
            break
    return repaired, passes


def _repair_table_source_coverage_output(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None,
) -> str:
    if not _table_reply_needs_source_coverage_repair(plan, reply, evidence, contract):
        return reply
    assert evidence is not None
    table = _deterministic_evidence_table(evidence)
    return table or reply


def _table_reply_needs_source_coverage_repair(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    contract: TurnContract | None,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.SOURCE_QA}:
        return False
    if not _contract_requests_table(contract) or evidence is None or not evidence.items:
        return False
    if _available_evidence_source_count(evidence) < _TABLE_MIN_DISTINCT_SOURCES:
        return False
    return _cited_evidence_source_count(reply, evidence) < _TABLE_MIN_DISTINCT_SOURCES


def _available_evidence_source_count(evidence: TurnEvidence) -> int:
    return len({item.source for item in evidence.items})


def _cited_evidence_source_count(reply: str, evidence: TurnEvidence) -> int:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[evidence_id.casefold()]
        for evidence_id in _reply_evidence_ids(reply)
        if evidence_id.casefold() in source_by_id
    }
    return len(cited_sources)


def _deterministic_evidence_table(evidence: TurnEvidence) -> str:
    cited_items = _overview_fallback_citation_items(evidence, limit=3)
    if len({item.source for item, _cue in cited_items}) < _TABLE_MIN_DISTINCT_SOURCES:
        return ""
    return _deterministic_overview_table(cited_items)


def _repair_structurally_invalid_evidence_output(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    user_input: str,
    config: ChatConfig,
    contract: TurnContract | None = None,
) -> str:
    if not _evidence_output_needs_model_repair(plan, reply, evidence, contract=contract):
        return reply
    assert evidence is not None
    deterministic = _deterministic_structural_evidence_repair(reply, evidence, contract)
    if deterministic:
        return deterministic
    return _model_structural_evidence_repair(
        reply,
        evidence,
        user_input=user_input,
        config=config,
    )


def _deterministic_structural_evidence_repair(
    reply: str,
    evidence: TurnEvidence,
    contract: TurnContract | None,
) -> str:
    if _contract_requests_table(contract) and not _contains_markdown_table(reply):
        table = _compact_overview_table_reply(reply, evidence)
        if table:
            return table
    if pointer_reply := _deterministic_evidence_pointer_repair(reply, evidence):
        return pointer_reply
    if len(reply) > _MATERIAL_REPLY_MAX_CHARS:
        compacted = _compact_verified_cited_reply(reply, evidence)
        if compacted:
            return compacted
    return ""


def _model_structural_evidence_repair(
    reply: str,
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig,
) -> str:
    if config.base_url is None or not config.model:
        return reply
    candidate = _model_repaired_evidence_output(
        reply,
        evidence,
        user_input=user_input,
        config=config,
    )
    if not _valid_repaired_evidence_output(candidate, evidence):
        return _invalid_model_evidence_output_fallback(reply, evidence)
    return candidate


def _model_repaired_evidence_output(
    reply: str,
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig,
) -> str:
    conversation = Conversation()
    conversation.add("system", _EVIDENCE_OUTPUT_REPAIR_SYSTEM_PROMPT)
    conversation.add(
        "user",
        _evidence_output_repair_context(reply, evidence, user_input=user_input),
    )
    repaired = _model_text._stream_one_shot_model_text(config, conversation)
    return _strip_unsolicited_learning_followup(_strip_tool_call_markup(repaired).strip())


def _invalid_model_evidence_output_fallback(reply: str, evidence: TurnEvidence) -> str:
    return _deterministic_evidence_pointer_repair(reply, evidence, allow_unbalanced=True) or reply


def _evidence_output_needs_model_repair(
    plan: LearningTurnPlan,
    reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    _ = contract
    if not _plan_output_can_use_evidence_repair(plan):
        return False
    if evidence is None or not evidence.items:
        return False
    verification = verify_citations(reply, evidence)
    return _reply_requires_structural_evidence_repair(reply, verification)


def _plan_output_can_use_evidence_repair(plan: LearningTurnPlan) -> bool:
    if plan.action in {LearningAction.PRESENT, LearningAction.SOURCE_QA}:
        return True
    return plan.action is LearningAction.CHAT and _plan_requires_citations(plan)


def _reply_requires_structural_evidence_repair(
    reply: str,
    verification: VerificationResult,
) -> bool:
    if not verification.has_citations:
        return True
    if _contains_markdown_table(reply) and verification.all_verified:
        return len(reply) > _OVERVIEW_MAX_TABLE_CHARS
    if len(reply) > _MATERIAL_REPLY_MAX_CHARS:
        return True
    if _CITATION_ONLY_REPLY_RE.match(reply):
        return True
    return bool(_OVERVIEW_CITATION_ID_RE.search(reply)) and (
        _thin_evidence_pointer(reply) or _reply_has_unbalanced_inline_markup(reply)
    )


def _thin_evidence_pointer(reply: str) -> bool:
    if not _OVERVIEW_CITATION_ID_RE.search(reply):
        return False
    if reply.strip().endswith((".", "!", "?")):
        return False
    if re.search(r"[.!?]\s*(?:\[(?:e|E)\d+\]\s*)+[.,;:]?\s*$", reply):
        return False
    without_citations = _OVERVIEW_CITATION_ID_RE.sub(" ", reply)
    words = re.findall(r"\w+", without_citations)
    return len(words) <= _THIN_EVIDENCE_POINTER_MAX_WORDS


def _deterministic_evidence_pointer_repair(
    reply: str,
    evidence: TurnEvidence,
    *,
    allow_unbalanced: bool = False,
) -> str:
    if not _can_use_evidence_pointer_repair(reply, allow_unbalanced=allow_unbalanced):
        return ""
    return _evidence_pointer_repair_for_ids(_reply_evidence_ids(reply), evidence)


def _can_use_evidence_pointer_repair(reply: str, *, allow_unbalanced: bool) -> bool:
    if _reply_has_unbalanced_inline_markup(reply):
        return allow_unbalanced
    return bool(_CITATION_ONLY_REPLY_RE.match(reply) or _thin_evidence_pointer(reply))


def _evidence_pointer_repair_for_ids(
    evidence_ids: tuple[str, ...],
    evidence: TurnEvidence,
) -> str:
    evidence_by_id = {item.evidence_id.casefold(): item for item in evidence.items}
    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id.casefold())
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item)
        if excerpt:
            return f"Check [{item.evidence_id}]: “{excerpt}” [{item.evidence_id}]."
    return ""


def _reply_evidence_ids(reply: str) -> tuple[str, ...]:
    seen: set[str] = set()
    ids: list[str] = []
    for match in _OVERVIEW_CITATION_ID_RE.finditer(reply):
        evidence_id = f"E{match.group('id')}"
        if evidence_id not in seen:
            ids.append(evidence_id)
            seen.add(evidence_id)
    return tuple(ids)


def _evidence_pointer_excerpt(item: EvidenceChunk) -> str:
    lines = [line.strip() for line in unescape(item.content).splitlines() if line.strip()]
    if lines and lines[0].startswith("#") and len(lines) > 1:
        lines = lines[1:]
    text = " ".join(lines or [unescape(item.content)])
    text = re.sub(r"^#+\s*", "", " ".join(text.split())).strip()
    for candidate in _overview_sentence_candidates(text):
        excerpt = _trim_overview_cue(candidate, limit=220)
        if excerpt and _source_pointer_excerpt_is_useful(excerpt):
            return excerpt
    return ""


def _source_pointer_excerpt_is_useful(excerpt: str) -> bool:
    compact = "".join(char for char in excerpt if char.isalnum())
    if len(compact) < 3:
        return False
    return any(char.isalpha() for char in compact) or len(compact) >= 6


def _valid_repaired_evidence_output(candidate: str, evidence: TurnEvidence) -> bool:
    if not candidate or _CITATION_ONLY_REPLY_RE.match(candidate):
        return False
    if _reply_has_unbalanced_inline_markup(candidate):
        return False
    verification = verify_citations(candidate, evidence)
    return verification.has_citations and verification.all_verified


def _compact_verified_cited_reply(reply: str, evidence: TurnEvidence) -> str:
    selected: list[str] = []
    for unit in _cited_reply_units(reply):
        candidate = "\n".join((*selected, unit)).strip()
        if len(candidate) > _MATERIAL_REPLY_MAX_CHARS and selected:
            break
        verification = verify_citations(unit, evidence)
        if not (verification.has_citations and verification.all_verified):
            continue
        selected.append(unit)
        if len("\n".join(selected)) >= _MATERIAL_REPLY_MAX_CHARS:
            break
    compacted = "\n".join(selected).strip()
    return compacted if compacted and len(compacted) < len(reply.strip()) else ""


def _cited_reply_units(reply: str) -> tuple[str, ...]:
    line_units = tuple(
        line.strip()
        for line in reply.splitlines()
        if line.strip() and _OVERVIEW_CITATION_ID_RE.search(line)
    )
    if len(line_units) > 1:
        return line_units
    return tuple(
        unit.strip()
        for unit in re.split(r"(?<=[.!?])\s+|(?<=\])\s+(?=[A-ZÄÖÜ])", reply)
        if unit.strip() and _OVERVIEW_CITATION_ID_RE.search(unit)
    )


def _repair_unverified_evidence_quotes(reply: str, evidence: TurnEvidence | None) -> str:
    if evidence is None or not evidence.items or not reply:
        return reply
    for quote in _reply_source_quote_fragments(reply):
        if not _quote_fragment_in_evidence(quote, evidence):
            return _evidence_quote_repair_reply(reply, evidence) or reply
    return reply


def _reply_source_quote_fragments(reply: str) -> tuple[str, ...]:
    fragments: list[str] = []
    for match in _INLINE_QUOTED_TEXT_RE.finditer(reply):
        phrase = " ".join(match.group("text").split())
        if len(phrase) >= 24:
            fragments.append(phrase)
    return tuple(fragments)


def _quote_fragment_in_evidence(quote: str, evidence: TurnEvidence) -> bool:
    normalized_quote = _normalized_query_text(quote)
    if not normalized_quote:
        return True
    return any(
        normalized_quote in _normalized_query_text(f"{item.chunk.heading} {item.content}")
        for item in evidence.items
    )


def _evidence_quote_repair_reply(reply: str, evidence: TurnEvidence) -> str:
    evidence_by_id = {item.evidence_id: item for item in evidence.items}
    for evidence_id in (*_reply_evidence_ids(reply), evidence.items[0].evidence_id):
        item = evidence_by_id.get(evidence_id)
        if item is None:
            continue
        excerpt = _evidence_pointer_excerpt(item) or _trace_excerpt(
            " ".join(unescape(item.content).split()),
            limit=220,
        )
        if excerpt:
            return f"“{excerpt}” [{item.evidence_id}]"
    return ""


def _evidence_output_repair_context(
    reply: str,
    evidence: TurnEvidence,
    *,
    user_input: str,
) -> str:
    lines = [
        f"User request: {user_input.strip() or '(none)'}",
        "Draft answer:",
        reply.strip(),
        "",
        "Evidence excerpts:",
    ]
    for item in evidence.items[:8]:
        compact_text = " ".join(unescape(item.content).split())
        if len(compact_text) > 700:
            compact_text = f"{compact_text[:699]}…"
        lines.extend(
            (
                "",
                f"Evidence {item.evidence_id}",
                f"Source: {item.source}",
                f"Text: {compact_text}",
            )
        )
    return "\n".join(lines)


def _reply_has_unbalanced_inline_markup(reply: str) -> bool:
    return reply.count("**") % 2 == 1 or reply.count("__") % 2 == 1 or reply.count("`") % 2 == 1


_EVIDENCE_OUTPUT_REPAIR_SYSTEM_PROMPT = (
    "Repair the draft into a concise user-visible answer using only the evidence excerpts. "
    "Return only the final answer. Every material claim must cite evidence IDs from the "
    "provided excerpts. Do not return citation IDs alone; name the claim or phrase the "
    "evidence supports. Do not add optional next steps, offers, menus, or study-plan prompts."
)
