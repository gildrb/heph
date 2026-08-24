"""Overview fallback, compaction, and repair helpers."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation

import harness.chat.model_text as _model_text
import harness.chat.overview_validation as _overview_validation
from harness.chat.citation_patterns import (
    _OVERVIEW_CITATION_BRACKET_RE,
    _OVERVIEW_CITATION_GROUP_RE,
    _OVERVIEW_CITATION_ID_RE,
)
from harness.chat.overview_cues import (
    _overview_cue_is_useful,
    _overview_fallback_cue_is_substantive,
)
from harness.chat.overview_tables import (
    _deterministic_overview_table,
    _overview_markdown_table_block,
    _overview_pipe_table_as_markdown,
)
from harness.chat.overview_topics import (
    _clean_overview_line,
    _normalize_overview_topic,
    _overview_content_lines,
    _overview_heading_candidates,
    _overview_topic_normalization_context,
    _trim_overview_cue,
)
from harness.chat.overview_validation import (
    _OVERVIEW_MAX_CHARS,
    _OVERVIEW_MAX_CITATIONS,
    _OVERVIEW_MAX_LIST_ITEMS,
    _OVERVIEW_MAX_TABLE_ROWS,
    _OVERVIEW_MAX_UNCITED_LEAD_CHARS,
    _OVERVIEW_MAX_UNCITED_LEAD_WORDS,
    _OVERVIEW_MIN_DISTINCT_SOURCES,
    _OVERVIEW_MIN_WORDS,
    _contains_markdown_table,
    _overview_citation_ids,
    _overview_has_long_uncited_lead,
    _overview_required_distinct_source_count,
    _valid_overview_model_reply,
)
from harness.chat.reply_text import (
    _citation_tail_keep_end,
    _strip_tool_call_markup,
    _strip_uncited_tail_after_last_citation,
)
from harness.chat.turn_contract import (
    TurnContract,
)
from harness.chat.turn_contract_checks import (
    _contract_requests_list,
    _contract_requests_table,
    _material_overview_turn,
)
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.rag.context import EvidenceChunk, TurnEvidence

_needs_overview_fallback = _overview_validation._needs_overview_fallback
_overview_answer_has_bad_shape = _overview_validation._overview_answer_has_bad_shape
_OVERVIEW_COMPACT_CITATION_GROUP_SIZE = 5
_OVERVIEW_FALLBACK_MAX_ITEMS = 3
_OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT = """
Write a compact user-facing corpus overview from supplied evidence only. Use the user's request
language for prose, even when evidence uses another language; preserve source terms. Prefer
substantive learnable content over metadata. Cite every source claim with current IDs. Use a short
answer with at most 3 cited topic clusters unless a table was requested. Compress useful cited
synthesis from a rejected draft, but do not stitch copied source sentences or unsupported text.
If the user asks for judgment or opinion, answer as a neutral observation from the evidence.
Place citations next to the topic, method, or example they support; omit specifics without a
matching citation.
Do not discuss retrieval, validation, truncation, or sampling, and do not add offers or next steps.
""".strip()


def _overview_fallback_reply(
    plan: DocumentTurnPlan,
    evidence: TurnEvidence | None,
    *,
    user_input: str = "",
    config: ChatConfig | None = None,
    rejected_reply: str = "",
    contract: TurnContract | None = None,
) -> str:
    if not _material_overview_turn(plan, contract) or evidence is None or not evidence.items:
        return ""

    allow_table = _contract_requests_table(contract)
    allow_list = _contract_requests_list(contract)
    compacted_rejected = _compact_overview_citation_inventory(
        rejected_reply,
        evidence,
        allow_table=allow_table,
        allow_list=allow_list,
    )
    if compacted_rejected:
        return compacted_rejected
    model_reply = _overview_model_fallback_reply(
        evidence,
        user_input=user_input,
        config=config,
        rejected_reply=rejected_reply,
        allow_table=allow_table,
        allow_list=allow_list,
    )
    if model_reply:
        return model_reply
    if allow_table or allow_list:
        deterministic_reply = _deterministic_overview_fallback_reply(
            evidence,
            allow_table=allow_table,
            allow_list=allow_list,
        )
        if deterministic_reply:
            return deterministic_reply
    return _overview_model_fallback_reply(
        evidence,
        user_input=user_input,
        config=config,
        rejected_reply=rejected_reply,
        allow_table=allow_table,
        allow_list=allow_list,
    )


def _compact_overview_citation_inventory(
    rejected_reply: str,
    evidence: TurnEvidence,
    *,
    allow_table: bool,
    allow_list: bool,
) -> str:
    reply = _clean_overview_model_reply(rejected_reply)
    if allow_table and not _contains_markdown_table(reply):
        return _compact_overview_table_reply(reply, evidence)
    if len(_overview_citation_ids(reply)) <= _OVERVIEW_MAX_CITATIONS:
        return ""
    if allow_table:
        return _compact_overview_table_reply(reply, evidence)
    for base in _overview_inventory_base_candidates(reply):
        compacted = _compact_overview_citation_groups(base)
        if not compacted:
            continue
        compacted = _strip_uncited_tail_after_last_citation(compacted)
        compacted = re.sub(r"[ \t]+", " ", compacted).strip()
        for candidate in _overview_compaction_candidates(compacted):
            if _valid_overview_model_reply(
                candidate,
                evidence,
                allow_table=allow_table,
                allow_list=allow_list,
            ):
                return candidate
    return ""


def _compact_overview_table_reply(reply: str, evidence: TurnEvidence) -> str:
    table = _overview_markdown_table_block(reply) or _overview_pipe_table_as_markdown(reply)
    if not table:
        return ""
    compacted = _compact_overview_citation_groups(table) or table
    lines = compacted.splitlines()
    trimmed = "\n".join(lines[:_OVERVIEW_MAX_TABLE_ROWS])
    if _valid_overview_model_reply(trimmed, evidence, allow_table=True):
        return trimmed
    return ""


def _compact_overview_citation_groups(reply: str) -> str:
    compacted_brackets = _compact_overview_bracket_citation_groups(reply)
    group_matches = tuple(_OVERVIEW_CITATION_GROUP_RE.finditer(compacted_brackets))
    if not group_matches:
        return "" if compacted_brackets == reply else compacted_brackets

    compacted = _compact_adjacent_overview_citation_groups(compacted_brackets, group_matches)
    return "" if compacted == reply else compacted


def _compact_overview_bracket_citation_groups(reply: str) -> str:
    def compact_group(match: re.Match[str]) -> str:
        citation_ids = _overview_citation_ids(match.group(0))
        if len(citation_ids) <= 1:
            return match.group(0)
        compacted = _compact_overview_citation_ids(
            citation_ids,
            limit=min(len(citation_ids), _OVERVIEW_COMPACT_CITATION_GROUP_SIZE),
        )
        return "".join(f"[{citation_id}]" for citation_id in compacted)

    return _OVERVIEW_CITATION_BRACKET_RE.sub(compact_group, reply)


def _compact_adjacent_overview_citation_groups(
    reply: str,
    group_matches: Sequence[re.Match[str]],
) -> str:
    if not group_matches:
        return ""

    group_limit = min(
        _OVERVIEW_COMPACT_CITATION_GROUP_SIZE,
        max(1, _OVERVIEW_MAX_CITATIONS // len(group_matches)),
    )

    def compact_group(match: re.Match[str]) -> str:
        citation_ids = _compact_overview_citation_ids(
            _overview_citation_ids(match.group(0)),
            limit=group_limit,
        )
        return "".join(f"[{citation_id}]" for citation_id in citation_ids)

    return _OVERVIEW_CITATION_GROUP_RE.sub(compact_group, reply)


def _overview_inventory_base_candidates(reply: str) -> tuple[str, ...]:
    candidates = (_leading_overview_synthesis_block(reply), reply)
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        deduped.append(candidate)
        seen.add(key)
    return tuple(deduped)


def _leading_overview_synthesis_block(reply: str) -> str:
    inline_prefix = _leading_inline_list_prefix(reply)
    if inline_prefix:
        return inline_prefix
    selected: list[str] = []
    for line in reply.splitlines():
        stripped = line.strip()
        if not stripped:
            if selected:
                break
            continue
        if _overview_line_is_list_item(stripped):
            break
        selected.append(stripped)
    block = " ".join(selected).strip()
    if not block or block == reply.strip() or not _OVERVIEW_CITATION_ID_RE.search(block):
        return ""
    return block


def _leading_inline_list_prefix(reply: str) -> str:
    match = re.search(r"\s+(?:[-*+]|\d+[.)])\s+\S", reply)
    if match is None:
        return ""
    prefix = reply[: match.start()].strip()
    if not prefix or prefix == reply.strip() or not _OVERVIEW_CITATION_ID_RE.search(prefix):
        return ""
    return prefix


def _overview_line_is_list_item(line: str) -> bool:
    return re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line) is not None


def _overview_compaction_candidates(reply: str) -> tuple[str, ...]:
    candidates = (
        reply,
        _leading_overview_synthesis_block(reply),
        _trim_overview_long_uncited_lead(reply),
        _trim_overview_trailing_citation_inventory(reply),
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        deduped.append(candidate)
        seen.add(key)
    return tuple(deduped)


def _trim_overview_long_uncited_lead(reply: str) -> str:
    match = _OVERVIEW_CITATION_ID_RE.search(reply)
    if match is None or not _overview_has_long_uncited_lead(reply):
        return ""
    lead = reply[: match.start()].strip()
    suffix = reply[match.start() :].strip()
    body = _overview_lead_prefix_within_budget(lead)
    body = _trim_overview_dangling_lead_tail(body)
    if not body:
        return ""
    candidate = f"{body.rstrip(' .,;:')} {suffix}"
    return candidate if candidate.rstrip().endswith((".", "!", "?")) else f"{candidate}."


def _overview_lead_prefix_within_budget(lead: str) -> str:
    normalized = re.sub(r"\s+", " ", lead).strip()
    if not normalized:
        return ""
    if not _lead_exceeds_overview_budget(normalized):
        return normalized
    return (
        _overview_sentence_lead_prefix(normalized)
        or _overview_clause_lead_prefix(normalized)
        or _overview_word_lead_prefix(normalized)
    )


def _overview_sentence_lead_prefix(normalized: str) -> str:
    return _overview_substantive_lead_prefix(_overview_sentence_candidates(normalized))


def _overview_clause_lead_prefix(normalized: str) -> str:
    selected = ""
    for clause in re.split(r"(?<=[,;:])\s+", normalized):
        if selected and not _overview_clause_is_substantive(clause):
            break
        candidate = f"{selected} {clause}".strip() if selected else clause
        if _lead_exceeds_overview_budget(candidate):
            break
        selected = candidate
    if _overview_lead_is_substantive(selected):
        return selected
    return ""


def _overview_word_lead_prefix(normalized: str) -> str:
    words = re.findall(r"\S+", normalized)
    return _overview_substantive_lead_prefix(words)


def _overview_substantive_lead_prefix(segments: Sequence[str]) -> str:
    selected = ""
    for segment in segments:
        candidate = f"{selected} {segment}".strip() if selected else segment
        if _lead_exceeds_overview_budget(candidate):
            break
        selected = candidate
    if _overview_lead_is_substantive(selected):
        return selected
    return ""


def _trim_overview_dangling_lead_tail(lead: str) -> str:
    if not lead or lead.rstrip().endswith((".", "!", "?")):
        return lead
    sentence_matches = tuple(re.finditer(r"[.!?]\s+", lead))
    if sentence_matches:
        trimmed_sentence = lead[: sentence_matches[-1].end()].strip()
        if _overview_lead_is_substantive(trimmed_sentence):
            return trimmed_sentence
    match = tuple(re.finditer(r"[,;:]\s+", lead))
    if not match:
        return lead
    tail_start = match[-1].end()
    tail = lead[tail_start:].strip(" ,;:")
    if len(re.findall(r"\b[\w'-]+\b", tail)) > 4:
        return lead
    trimmed = lead[: match[-1].start()].strip(" ,;:")
    return trimmed if _overview_lead_is_substantive(trimmed) else lead


def _overview_clause_is_substantive(clause: str) -> bool:
    return len(re.findall(r"\b[\w'-]+\b", clause.strip(" ,;:"))) >= 2


def _lead_exceeds_overview_budget(lead: str) -> bool:
    return (
        len(lead) > _OVERVIEW_MAX_UNCITED_LEAD_CHARS
        or len(re.findall(r"\b[\w'-]+\b", lead)) > _OVERVIEW_MAX_UNCITED_LEAD_WORDS
    )


def _overview_lead_is_substantive(lead: str) -> bool:
    return len(re.findall(r"\b[\w'-]+\b", lead)) >= _OVERVIEW_MIN_WORDS


def _trim_overview_trailing_citation_inventory(reply: str) -> str:
    match = _last_trailing_overview_citation_group(reply)
    if match is None:
        return ""
    prefix = reply[: match.start()].rstrip(" ,;:.")
    if not prefix or _OVERVIEW_CITATION_ID_RE.search(prefix):
        return ""
    suffix = re.sub(r"\s+", "", match.group(0))
    body = _overview_body_prefix_within_budget(prefix, suffix)
    if not body:
        return ""
    return f"{body.rstrip(' .,;:')} {suffix}."


def _last_trailing_overview_citation_group(reply: str) -> re.Match[str] | None:
    matches = tuple(_OVERVIEW_CITATION_GROUP_RE.finditer(reply))
    if not matches:
        return None
    match = matches[-1]
    keep_end = _citation_tail_keep_end(reply, match.end())
    if reply[keep_end:].strip():
        return None
    return match


def _overview_body_prefix_within_budget(prefix: str, suffix: str) -> str:
    budget = _OVERVIEW_MAX_CHARS - len(suffix) - 2
    if budget <= 0:
        return ""
    if len(prefix) <= budget:
        return prefix
    selected = ""
    for sentence in _overview_sentence_candidates(prefix):
        candidate = f"{selected} {sentence}".strip() if selected else sentence
        if len(candidate) > budget:
            break
        selected = candidate
    if not selected:
        return ""
    words = re.findall(r"\b[\w'-]+\b", selected)
    if len(words) < _OVERVIEW_MIN_WORDS:
        return ""
    return selected


def _compact_overview_citation_ids(
    citation_ids: Sequence[str],
    *,
    limit: int,
) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for citation_id in citation_ids:
        key = citation_id.casefold()
        if key in seen:
            continue
        deduped.append(citation_id)
        seen.add(key)
    if len(deduped) <= limit:
        return tuple(deduped)
    if limit <= 1:
        return (deduped[0],)
    indexes = {round(position * (len(deduped) - 1) / (limit - 1)) for position in range(limit)}
    return tuple(deduped[index] for index in sorted(indexes))


def _overview_unavailable_reply() -> str:
    return "I could not produce a grounded material overview from the current model output."


def _deterministic_overview_fallback_reply(
    evidence: TurnEvidence,
    *,
    allow_table: bool = False,
    allow_list: bool = False,
    excluded_evidence_ids: frozenset[str] | None = None,
) -> str:
    limit = _overview_required_distinct_source_count(evidence)
    cited_items = _overview_fallback_citation_items(
        evidence,
        limit=max(limit, _OVERVIEW_MIN_DISTINCT_SOURCES),
        excluded_evidence_ids=excluded_evidence_ids,
        table_cues=allow_table,
    )
    if not cited_items:
        return ""
    if allow_table:
        return _deterministic_overview_table(cited_items)
    if allow_list:
        return _deterministic_overview_list(cited_items)
    return _deterministic_overview_paragraph(cited_items)


def _deterministic_overview_paragraph(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    clauses = tuple(
        _overview_fallback_sentence(cue, item.evidence_id)
        for item, cue in items[:_OVERVIEW_FALLBACK_MAX_ITEMS]
    )
    return " ".join(clauses)


def _overview_fallback_sentence(cue: str, evidence_id: str) -> str:
    body = cue.rstrip(" .;:")
    return f"{body} [{evidence_id}]."


def _deterministic_overview_list(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        f"{index}. {cue} [{item.evidence_id}]"
        for index, (item, cue) in enumerate(items[:_OVERVIEW_MAX_LIST_ITEMS], start=1)
    ]
    return "\n".join(lines)


def _overview_fallback_citation_items(
    evidence: TurnEvidence,
    *,
    limit: int = 4,
    excluded_evidence_ids: frozenset[str] | None = None,
    table_cues: bool = False,
) -> list[tuple[EvidenceChunk, str]]:
    cue_for_item = _overview_table_cue_for_item if table_cues else _overview_fallback_cue_for_item
    candidates = _overview_fallback_candidate_items(
        evidence,
        excluded_evidence_ids=excluded_evidence_ids or frozenset(),
    )
    selected = _select_overview_fallback_citation_items(
        candidates,
        limit=limit,
        cue_for_item=cue_for_item,
        suppress_repeated_cues=True,
    )
    if selected:
        return selected
    return _select_overview_fallback_citation_items(
        candidates,
        limit=limit,
        cue_for_item=_overview_table_cue_for_item,
        suppress_repeated_cues=False,
    )


def _select_overview_fallback_citation_items(
    candidates: Sequence[EvidenceChunk],
    *,
    limit: int,
    cue_for_item: Callable[[EvidenceChunk], str],
    suppress_repeated_cues: bool,
) -> list[tuple[EvidenceChunk, str]]:
    selected: list[tuple[EvidenceChunk, str]] = []
    seen_keys: set[tuple[str, int]] = set()
    repeated_cues = _overview_repeated_fallback_cues(candidates, cue_for_item=cue_for_item)
    for item in _spread_overview_candidate_items(candidates, limit=limit):
        key = (item.source, item.chunk_index)
        cue = cue_for_item(item)
        repeated = suppress_repeated_cues and _normalize_overview_topic(cue) in repeated_cues
        if key in seen_keys or not cue or repeated:
            continue
        selected.append((item, cue))
        seen_keys.add(key)
        if len(selected) >= limit:
            break
    return selected


def _spread_overview_candidate_items(
    candidates: Sequence[EvidenceChunk],
    *,
    limit: int,
) -> tuple[EvidenceChunk, ...]:
    if limit <= 0 or len(candidates) <= limit * 2:
        return tuple(candidates)
    if limit == 1:
        return (candidates[0],)
    indexes = {round(position * (len(candidates) - 1) / (limit - 1)) for position in range(limit)}
    selected = [candidates[index] for index in sorted(indexes)]
    selected.extend(item for index, item in enumerate(candidates) if index not in indexes)
    return tuple(selected)


def _overview_fallback_candidate_items(
    evidence: TurnEvidence,
    *,
    excluded_evidence_ids: frozenset[str],
) -> tuple[EvidenceChunk, ...]:
    return tuple(
        item for item in evidence.items if item.evidence_id.casefold() not in excluded_evidence_ids
    )


def _overview_repeated_fallback_cues(
    items: Sequence[EvidenceChunk],
    *,
    cue_for_item: Callable[[EvidenceChunk], str] | None = None,
) -> frozenset[str]:
    if cue_for_item is None:
        cue_for_item = _overview_fallback_cue_for_item
    sources_by_cue: dict[str, set[str]] = {}
    for item in items:
        cue = cue_for_item(item)
        if not cue:
            continue
        sources_by_cue.setdefault(_normalize_overview_topic(cue), set()).add(item.source)
    return frozenset(cue for cue, sources in sources_by_cue.items() if len(sources) > 1)


def _overview_fallback_cue_for_item(item: EvidenceChunk) -> str:
    for candidate in _overview_content_cue_candidates(item):
        cue = _trim_overview_cue(_clean_overview_line(candidate))
        if _overview_fallback_cue_is_substantive(cue):
            return cue
    return ""


def _overview_table_cue_for_item(item: EvidenceChunk) -> str:
    fallback_cue = _overview_fallback_cue_for_item(item)
    if fallback_cue:
        return fallback_cue
    return _overview_cue_for_item(item)


def _overview_cue_for_item(item: EvidenceChunk) -> str:
    candidates = (*_overview_content_cue_candidates(item), *_overview_heading_candidates(item))
    for candidate in candidates:
        cue = _trim_overview_cue(_clean_overview_line(candidate))
        if _overview_cue_is_useful(cue):
            return cue
    return ""


def _overview_content_cue_candidates(item: EvidenceChunk) -> tuple[str, ...]:
    candidates: list[str] = []
    for line in _overview_content_lines(item.content):
        cleaned = _clean_overview_line(line)
        if not cleaned:
            continue
        candidates.extend(_overview_sentence_candidates(cleaned))
    return tuple(candidates)


def _overview_sentence_candidates(text: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip())
    return parts or (text,)


def _overview_model_fallback_reply(
    evidence: TurnEvidence,
    *,
    user_input: str,
    config: ChatConfig | None,
    rejected_reply: str = "",
    allow_table: bool = False,
    allow_list: bool = False,
) -> str:
    usable_config = _overview_fallback_config(config)
    if usable_config is None:
        return ""
    conversation = Conversation()
    system_prompt = _OVERVIEW_LOCALIZED_FALLBACK_SYSTEM_PROMPT
    if allow_table:
        system_prompt = (
            f"{system_prompt}\nThe user requested a table. Produce a compact markdown table "
            "instead of prose, with concise cited cells and no source inventory."
        )
    if allow_list:
        system_prompt = (
            f"{system_prompt}\nThe user requested a list. Produce a compact cited list "
            "instead of prose."
        )
    conversation.add("system", system_prompt)
    conversation.add(
        "user",
        _overview_topic_normalization_context(
            evidence,
            user_input,
            rejected_reply=rejected_reply,
        ),
    )
    reply = _clean_overview_model_reply(
        _model_text._stream_one_shot_model_text(usable_config, conversation)
    )
    for candidate in _overview_model_fallback_candidates(
        reply,
        allow_table=allow_table,
        allow_list=allow_list,
    ):
        if _valid_overview_model_reply(
            candidate,
            evidence,
            allow_table=allow_table,
            allow_list=allow_list,
        ):
            return candidate
    return ""


def _overview_model_fallback_candidates(
    reply: str,
    *,
    allow_table: bool,
    allow_list: bool,
) -> tuple[str, ...]:
    if not reply:
        return ()
    candidates = (
        reply,
        *_overview_model_fallback_extra_candidates(
            reply,
            allow_table=allow_table,
            allow_list=allow_list,
        ),
    )
    return _deduped_overview_model_fallback_candidates(candidates)


def _overview_model_fallback_extra_candidates(
    reply: str,
    *,
    allow_table: bool,
    allow_list: bool,
) -> tuple[str, ...]:
    if allow_table:
        return _overview_table_model_fallback_candidates(reply)
    if allow_list:
        return ()
    return _overview_prose_model_fallback_candidates(reply)


def _overview_table_model_fallback_candidates(reply: str) -> tuple[str, ...]:
    table = _overview_markdown_table_block(reply) or _overview_pipe_table_as_markdown(reply)
    if not table:
        return ()
    return (_compact_overview_citation_groups(table) or table,)


def _overview_prose_model_fallback_candidates(reply: str) -> tuple[str, ...]:
    candidates: list[str] = []
    leading = _leading_overview_synthesis_block(_compact_overview_bracket_citation_groups(reply))
    if leading:
        candidates.extend(_overview_compaction_candidates(leading))
    compacted = _compact_overview_citation_groups(reply)
    if compacted:
        candidates.extend(_overview_compaction_candidates(compacted))
    return tuple(candidates)


def _deduped_overview_model_fallback_candidates(candidates: Sequence[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = _clean_overview_model_fallback_candidate(candidate)
        if not cleaned or cleaned in seen:
            continue
        deduped.append(cleaned)
        seen.add(cleaned)
    return tuple(deduped)


def _clean_overview_model_fallback_candidate(candidate: str) -> str:
    cleaned = _strip_uncited_tail_after_last_citation(candidate)
    return re.sub(r"[ \t]+", " ", cleaned).strip()


def _overview_fallback_config(config: ChatConfig | None) -> ChatConfig | None:
    if config is None or not config.model:
        return None
    if not config.base_url and not config.provider_slug:
        return None
    return config


def _clean_overview_model_reply(model_text: str) -> str:
    if not model_text:
        return ""
    return _strip_tool_call_markup(model_text).strip()
