"""Overview fallback, compaction, and structural validation helpers."""

from __future__ import annotations

import difflib
import re
import unicodedata
from collections.abc import Callable, Sequence

from agent.citation import verify_citations
from rag.context import EvidenceChunk, TurnEvidence
from rag.scoring import tokenize
from runtime.config import ChatConfig
from runtime.conversation import Conversation
from study.prompt_plans import LearningTurnPlan

import chat.model_text as _model_text
from chat.citation_patterns import (
    _OVERVIEW_CITATION_BRACKET_RE,
    _OVERVIEW_CITATION_GROUP_RE,
    _OVERVIEW_CITATION_ID_RE,
    _OVERVIEW_CITATION_TOKEN_RE,
)
from chat.overview_topics import (
    _OVERVIEW_FORMULA_RE,
    _OVERVIEW_LINE_MARKER_RE,
    _clean_overview_line,
    _normalize_overview_topic,
    _overview_content_lines,
    _overview_heading_candidates,
    _overview_heading_looks_like_metadata,
    _overview_topic_is_too_short_or_generic,
    _overview_topic_is_useful,
    _overview_topic_normalization_context,
    _trim_overview_cue,
)
from chat.reply_text import (
    _citation_tail_keep_end,
    _has_uncited_tail_after_last_citation,
    _strip_tool_call_markup,
    _strip_unsolicited_learning_followup,
)
from chat.turn_contract import (
    TurnContract,
)
from chat.turn_contract_checks import (
    _contract_requests_list,
    _contract_requests_table,
    _material_overview_turn,
)
from chat.turn_query import (
    _letter_words,
    _looks_like_name_word,
    _looks_like_sentence,
)

_MARKDOWN_TABLE_SEPARATOR_LINE_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_OVERVIEW_MIN_WORDS = 24
_OVERVIEW_MAX_WORDS = 110
_OVERVIEW_MAX_CHARS = 700
_OVERVIEW_MAX_TABLE_CHARS = 1800
_OVERVIEW_MAX_UNCITED_LEAD_WORDS = 32
_OVERVIEW_MAX_UNCITED_LEAD_CHARS = 260
_OVERVIEW_MIN_CITATIONS = 2
_OVERVIEW_MAX_CITATIONS = 8
_OVERVIEW_COMPACT_CITATION_GROUP_SIZE = 5
_OVERVIEW_MIN_DISTINCT_SOURCES = 2
_OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES = 5
_OVERVIEW_FALLBACK_MAX_ITEMS = 3
_OVERVIEW_MAX_LIST_ITEMS = 3
_OVERVIEW_MAX_TABLE_ROWS = 8
_OVERVIEW_EXTRACTIVE_MIN_SPANS = 2
_OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS = 3
_OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO = 0.34
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
    plan: LearningTurnPlan,
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
        compacted = _strip_unsolicited_learning_followup(compacted)
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


def _overview_markdown_table_block(reply: str) -> str:
    lines = reply.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if index + 1 >= len(lines) or not _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(
            lines[index + 1]
        ):
            continue
        end = index + 2
        while end < len(lines) and lines[end].strip().startswith("|"):
            end += 1
        return "\n".join(line.rstrip() for line in lines[index:end]).strip()
    return ""


def _overview_pipe_table_as_markdown(reply: str) -> str:
    rows = _overview_pipe_table_rows(reply)
    if len(rows) < 2:
        return ""
    width = max(len(row) for row in rows)
    normalized_rows = [(*row, *("",) * (width - len(row))) for row in rows]
    first_row = normalized_rows[0]
    if any(_OVERVIEW_CITATION_ID_RE.search(cell) for cell in first_row):
        header = tuple(f"Column {index}" for index in range(1, width + 1))
        data_rows = normalized_rows
    else:
        header = first_row
        data_rows = normalized_rows[1:]
    separator = tuple("---" for _ in range(width))
    rendered_rows = (header, separator, *data_rows[: max(1, _OVERVIEW_MAX_TABLE_ROWS - 2)])
    return "\n".join(_render_markdown_table_row(row) for row in rendered_rows)


def _overview_pipe_table_rows(reply: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in reply.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 2:
            continue
        rows.extend(_overview_pipe_table_line_rows(stripped))
    return tuple(rows)


def _overview_pipe_table_line_rows(line: str) -> tuple[tuple[str, ...], ...]:
    if _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line):
        return ()
    cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
    if len(cells) < 2:
        return ()
    if "" not in cells:
        return (cells,)
    rows: list[tuple[str, ...]] = []
    current: list[str] = []
    for cell in cells:
        if cell:
            current.append(cell)
            continue
        if len(current) >= 2:
            rows.append(tuple(current))
        current = []
    if len(current) >= 2:
        rows.append(tuple(current))
    return tuple(row for row in rows if not _markdown_separator_cells(row))


def _markdown_separator_cells(row: Sequence[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)


def _render_markdown_table_row(row: Sequence[str]) -> str:
    return "| " + " | ".join(_escape_markdown_table_cell(cell) for cell in row) + " |"


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

    selected = ""
    for sentence in _overview_sentence_candidates(normalized):
        candidate = f"{selected} {sentence}".strip() if selected else sentence
        if _lead_exceeds_overview_budget(candidate):
            break
        selected = candidate
    if _overview_lead_is_substantive(selected):
        return selected

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

    words = re.findall(r"\S+", normalized)
    selected_words: list[str] = []
    for word in words:
        candidate = " ".join((*selected_words, word))
        if _lead_exceeds_overview_budget(candidate):
            break
        selected_words.append(word)
    selected = " ".join(selected_words).strip()
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


def _deterministic_overview_table(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        "| Source | Grounded excerpt |",
        "|---|---|",
    ]
    for item, cue_text in items:
        source = _escape_markdown_table_cell(item.source)
        cue = _escape_markdown_table_cell(cue_text)
        lines.append(f"| {source} | {cue} [{item.evidence_id}] |")
    return "\n".join(lines)


def _deterministic_overview_list(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        f"{index}. {cue} [{item.evidence_id}]"
        for index, (item, cue) in enumerate(items[:_OVERVIEW_MAX_LIST_ITEMS], start=1)
    ]
    return "\n".join(lines)


def _escape_markdown_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


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
        limit=limit,
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
    limit: int,
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


def _overview_fallback_cue_is_substantive(cue: str) -> bool:
    if not _overview_cue_is_useful(cue):
        return False
    if (
        _overview_cue_looks_like_byline(cue)
        or _overview_cue_is_symbolic_fragment(cue)
        or _overview_starts_with_sentence_fragment(cue)
    ):
        return False
    words = re.findall(r"\b[\w'-]+\b", cue)
    if _looks_like_sentence(cue):
        return len(words) >= 3 and _overview_cue_has_content_word(words)
    if "," in cue or ";" in cue or any(_overview_symbolic_char(char) for char in cue):
        return False
    return len(words) >= 6


def _overview_cue_looks_like_byline(cue: str) -> bool:
    words = _letter_words(cue)
    if len(words) < 4:
        return False
    name_like = sum(1 for word in words if _looks_like_name_word(word))
    if len(words) >= 6 and name_like / len(words) >= 0.8:
        return True
    segments = [_letter_words(segment) for segment in re.split(r"[,;/]", cue) if segment.strip()]
    name_segments = sum(1 for segment in segments if _looks_like_person_name_segment(segment))
    return bool(segments) and name_segments >= 2 and name_segments / len(segments) >= 0.6


def _looks_like_person_name_segment(words: Sequence[str]) -> bool:
    return 1 <= len(words) <= 3 and all(_looks_like_name_word(word) for word in words)


def _overview_cue_is_symbolic_fragment(cue: str) -> bool:
    characters = tuple(char for char in cue if not char.isspace())
    if not characters:
        return True
    symbolic = sum(1 for char in characters if _overview_symbolic_char(char))
    if symbolic >= 3 and symbolic / len(characters) >= 0.08:
        return True
    words = _letter_words(cue)
    return bool(words) and symbolic >= len(words)


def _overview_symbolic_char(char: str) -> bool:
    return unicodedata.category(char) == "Sm" or char in "<>=|^_{}[]()"


def _overview_cue_has_content_word(words: Sequence[str]) -> bool:
    return any(sum(char.isalpha() for char in word) >= 6 for word in words)


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


def _overview_cue_is_useful(cue: str) -> bool:
    normalized = " ".join(cue.casefold().split())
    if not normalized:
        return False
    words = normalized.split()
    if len(words) < 3 and not _overview_topic_is_useful(cue):
        return False
    if (
        _overview_heading_looks_like_metadata(cue)
        or _overview_topic_is_too_short_or_generic(normalized)
        or _OVERVIEW_FORMULA_RE.search(cue) is not None
    ):
        return False
    return not _overview_cue_looks_like_byline(cue)


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
    candidates = [reply]
    if allow_table:
        table = _overview_markdown_table_block(reply) or _overview_pipe_table_as_markdown(reply)
        if table:
            candidates.append(_compact_overview_citation_groups(table) or table)
    elif not allow_list:
        leading = _leading_overview_synthesis_block(
            _compact_overview_bracket_citation_groups(reply)
        )
        if leading:
            candidates.extend(_overview_compaction_candidates(leading))
        compacted = _compact_overview_citation_groups(reply)
        if compacted:
            candidates.extend(_overview_compaction_candidates(compacted))
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = _strip_unsolicited_learning_followup(candidate)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        if not cleaned or cleaned in seen:
            continue
        deduped.append(cleaned)
        seen.add(cleaned)
    return tuple(deduped)


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


def _valid_overview_model_reply(
    reply: str,
    evidence: TurnEvidence,
    *,
    allow_table: bool = False,
    allow_list: bool = False,
) -> bool:
    if not reply:
        return False
    if allow_table and not _contains_markdown_table(reply):
        return False
    if allow_list and _list_item_count(reply) == 0:
        return False
    verification = verify_citations(reply, evidence)
    return (
        verification.has_citations
        and verification.all_verified
        and not _overview_answer_has_bad_shape(reply, evidence, allow_table=allow_table)
    )


def _needs_overview_fallback(
    plan: LearningTurnPlan,
    raw_reply: str,
    evidence: TurnEvidence | None,
    *,
    contract: TurnContract | None = None,
) -> bool:
    if not _material_overview_turn(plan, contract) or evidence is None or not evidence.items:
        return False
    verification = verify_citations(raw_reply, evidence)
    if not verification.has_citations or not verification.all_verified:
        return True
    return _overview_answer_has_bad_shape(
        raw_reply,
        evidence,
        allow_table=_contract_requests_table(contract),
    )


def _overview_answer_has_bad_shape(
    raw_reply: str,
    evidence: TurnEvidence | None = None,
    *,
    allow_table: bool = False,
) -> bool:
    """Reject overview replies that are too thin, too noisy, or under-grounded."""
    citation_ids = _overview_citation_ids(raw_reply)
    words = re.findall(r"\b[\w'-]+\b", raw_reply)
    has_table = _contains_markdown_table(raw_reply)
    if allow_table and not has_table:
        return True
    max_chars = _OVERVIEW_MAX_TABLE_CHARS if has_table and allow_table else _OVERVIEW_MAX_CHARS
    if len(raw_reply) > max_chars:
        return True
    if not has_table and len(words) > _OVERVIEW_MAX_WORDS:
        return True
    if not has_table and _has_uncited_tail_after_last_citation(raw_reply):
        return True
    if not has_table and len(citation_ids) > _OVERVIEW_MAX_CITATIONS:
        return True
    if not has_table and _overview_starts_with_sentence_fragment(raw_reply):
        return True
    if not has_table and _overview_has_long_uncited_lead(raw_reply):
        return True
    if (
        not has_table
        and evidence is not None
        and _overview_is_extractive_inventory(raw_reply, evidence)
    ):
        return True
    if has_table and _markdown_table_row_count(raw_reply) > _OVERVIEW_MAX_TABLE_ROWS:
        return True
    if _list_item_count(raw_reply) > _OVERVIEW_MAX_LIST_ITEMS:
        return True
    if len(citation_ids) < _OVERVIEW_MIN_CITATIONS:
        return True
    if not has_table and len(words) < _OVERVIEW_MIN_WORDS:
        return True
    return evidence is not None and not _overview_covers_enough_sources(citation_ids, evidence)


def _overview_has_long_uncited_lead(raw_reply: str) -> bool:
    match = _OVERVIEW_CITATION_ID_RE.search(raw_reply)
    if match is None:
        return False
    lead = raw_reply[: match.start()].strip()
    if len(lead) > _OVERVIEW_MAX_UNCITED_LEAD_CHARS:
        return True
    return len(re.findall(r"\b[\w'-]+\b", lead)) > _OVERVIEW_MAX_UNCITED_LEAD_WORDS


def _contains_markdown_table(text: str) -> bool:
    return any(_MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line) for line in text.splitlines())


def _markdown_table_row_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("|"))


def _list_item_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line))


def _overview_starts_with_sentence_fragment(text: str) -> bool:
    first_alpha = next((char for char in text.lstrip() if char.isalpha()), "")
    return bool(first_alpha) and first_alpha.islower()


def _overview_citation_ids(raw_reply: str) -> tuple[str, ...]:
    ids: list[str] = []
    for bracket in _OVERVIEW_CITATION_BRACKET_RE.finditer(raw_reply):
        ids.extend(
            f"E{match.group('id')}"
            for match in _OVERVIEW_CITATION_TOKEN_RE.finditer(bracket.group("body"))
        )
    return tuple(ids)


def _overview_covers_enough_sources(citation_ids: tuple[str, ...], evidence: TurnEvidence) -> bool:
    source_by_id = {item.evidence_id.casefold(): item.source for item in evidence.items}
    cited_sources = {
        source_by_id[citation_id.casefold()]
        for citation_id in citation_ids
        if citation_id.casefold() in source_by_id
    }
    return len(cited_sources) >= _overview_required_distinct_source_count(evidence)


def _overview_is_extractive_inventory(raw_reply: str, evidence: TurnEvidence) -> bool:
    spans = _overview_cited_claim_spans(raw_reply)
    if len(spans) < _OVERVIEW_EXTRACTIVE_MIN_SPANS:
        return False
    copied = sum(1 for span in spans if _overview_span_is_copied(span, evidence))
    return copied >= _OVERVIEW_EXTRACTIVE_MIN_SPANS and (
        copied / len(spans) >= _OVERVIEW_EXTRACTIVE_MAX_SPAN_RATIO
    )


def _overview_cited_claim_spans(raw_reply: str) -> tuple[str, ...]:
    spans: list[str] = []
    start = 0
    for match in _OVERVIEW_CITATION_ID_RE.finditer(raw_reply):
        span = _clean_overview_extract_span(raw_reply[start : match.start()])
        start = match.end()
        if len(tokenize(span)) >= _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
            spans.append(span)
    return tuple(spans)


def _clean_overview_extract_span(span: str) -> str:
    cleaned = _OVERVIEW_LINE_MARKER_RE.sub("", span.strip())
    return cleaned.strip(" \t\r\n\"'\u201c\u201d\u2018\u2019.,;:")


def _overview_span_is_copied(span: str, evidence: TurnEvidence) -> bool:
    if len(tokenize(span)) < _OVERVIEW_EXTRACTIVE_MIN_SPAN_WORDS:
        return False
    normalized_span = _overview_copy_normalized_text(span)
    return any(
        _overview_normalized_span_is_copied(
            normalized_span,
            _overview_copy_normalized_text(item.content),
        )
        for item in evidence.items
    )


def _overview_normalized_span_is_copied(span: str, evidence_text: str) -> bool:
    if not span or not evidence_text:
        return False
    if span in evidence_text:
        return True
    if len(span) < 32:
        return False
    return difflib.SequenceMatcher(a=span, b=evidence_text).ratio() >= 0.82


def _overview_copy_normalized_text(text: str) -> str:
    return " ".join(tokenize(text))


def _overview_required_distinct_source_count(evidence: TurnEvidence) -> int:
    available_source_count = len({item.source for item in evidence.items})
    if available_source_count <= _OVERVIEW_MIN_DISTINCT_SOURCES:
        return available_source_count
    proportional_floor = (available_source_count + 1) // 2
    return min(
        available_source_count,
        _OVERVIEW_MAX_REQUIRED_DISTINCT_SOURCES,
        max(_OVERVIEW_MIN_DISTINCT_SOURCES, proportional_floor),
    )
