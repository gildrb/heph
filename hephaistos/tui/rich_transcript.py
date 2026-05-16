"""Rich transcript rendering with inline evidence badges and source panels."""

from __future__ import annotations

import re
from dataclasses import dataclass

import unicodeit

from hephaistos.rag.context import TurnEvidence
from hephaistos.rag.source_mapping import evidence_location_label

_CITATION_RE = re.compile(r"(?:\[|【)([Ee]\d+(?:\s*[,;]\s*[Ee]\d+)*)(?:\]|】)")
_SINGLE_ID_RE = re.compile(r"[Ee](\d+)")
_LATEX_INLINE_RE = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
_LATEX_BLOCK_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
_MATH_SPAN_RE = re.compile(r"\$(?!\$)(.+?)(?<!\$)\$", re.DOTALL)
_LATEX_FRACTION_RE = re.compile(r"\\(?:dfrac|tfrac|frac)\{([^{}]+)\}\{([^{}]+)\}")
_LATEX_BRACED_SCRIPT_RE = re.compile(r"([_^])\{([^{}]+)\}")
_LATEX_SUPERSCRIPT_SPACING_RE = re.compile(r"(?<=[A-Za-z\u0370-\u03FF])\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾])")
_LATEX_COMMAND_REPLACEMENTS = {
    r"\displaystyle": "",
    r"\left.": "",
    r"\left": "",
    r"\right": "",
    r"\qquad": " ",
    r"\quad": " ",
    r"\dots": "…",
    r"\,": " ",
    r"\;": " ",
    r"\:": " ",
    r"\!": "",
}
_MAX_VISIBLE_SOURCE_ITEMS = 3


@dataclass(frozen=True, slots=True)
class EnrichedReply:
    """An assistant reply enriched with citation metadata."""

    markdown_text: str
    evidence: TurnEvidence | None


def _replace_latex_commands(text: str) -> str:
    formatted = text
    for latex, replacement in _LATEX_COMMAND_REPLACEMENTS.items():
        formatted = formatted.replace(latex, replacement)
    formatted = unicodeit.replace(formatted)
    formatted = _LATEX_BRACED_SCRIPT_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}",
        formatted,
    )
    formatted = _LATEX_FRACTION_RE.sub(
        lambda match: f"{match.group(1)}/{match.group(2)}",
        formatted,
    )
    formatted = _LATEX_SUPERSCRIPT_SPACING_RE.sub(lambda match: match.group(1), formatted)
    return re.sub(r"[ \t]{2,}", " ", formatted)


def _format_math_expression(expression: str) -> str:
    """Render LaTeX math fragments as terminal-friendly Unicode text."""
    return _replace_latex_commands(expression.strip())


def _normalize_latex_delimiters(text: str) -> str:
    """Use terminal-friendly math rendering for model output."""
    text = _LATEX_BLOCK_RE.sub(
        lambda match: f"\n{_format_math_expression(match.group(1))}\n",
        text,
    )
    text = _LATEX_INLINE_RE.sub(lambda match: f"${match.group(1).strip()}$", text)
    return _MATH_SPAN_RE.sub(lambda match: _format_math_expression(match.group(1)), text)


def normalize_math_output(text: str) -> str:
    return _replace_latex_commands(_normalize_latex_delimiters(text))


def _render_evidence_panel(evidence: TurnEvidence, cited_ids: list[str]) -> str:
    if not evidence.items:
        return ""
    cited = set(cited_ids)
    if not cited:
        return f"_sources: {_evidence_scope_text(evidence)}. Details: /evidence_"
    items = [item for item in evidence.items if item.evidence_id in cited]
    parts: list[str] = []
    for item in items[:_MAX_VISIBLE_SOURCE_ITEMS]:
        source_name = item.source.rsplit("/", 1)[-1]
        location = evidence_location_label(item.source, item.chunk, None)
        location_parts = [location]
        if item.chunk.heading:
            location_parts.insert(1, f"under {item.chunk.heading}")
        parts.append(f"{item.evidence_id}: {source_name} ({'; '.join(location_parts)})")
    remaining = len(items) - _MAX_VISIBLE_SOURCE_ITEMS
    if remaining > 0:
        parts.append(f"+{remaining} more cited source{'' if remaining == 1 else 's'}")
    return f"_sources: {'; '.join(parts)}. Details: /evidence_"


def evidence_citation_spans(text: str) -> list[tuple[int, int]]:
    """Return text spans for visible evidence citation markers."""
    return [(match.start(), match.end()) for match in _CITATION_RE.finditer(text)]


def is_evidence_sources_line(text: str) -> bool:
    """Return whether rendered text starts the appended evidence sources footer."""
    return text.lstrip().startswith("sources:")


def _evidence_scope_text(evidence: TurnEvidence) -> str:
    item_count = len(evidence.items)
    excerpt = "evidence excerpt" if item_count == 1 else "evidence excerpts"
    sampled_sources = evidence.sampled_source_count or len(
        {item.source for item in evidence.items}
    )
    total_sources = evidence.total_source_count or sampled_sources
    if total_sources > sampled_sources:
        source_text = f"{sampled_sources} of {total_sources} indexed sources"
    else:
        source_text = f"{sampled_sources} source{'' if sampled_sources == 1 else 's'}"
    return f"{item_count} {excerpt} from {source_text}"


def enrich_reply(text: str, evidence: TurnEvidence | None) -> EnrichedReply:
    """Enrich a raw assistant reply with citation badge markup.

    Replaces plain [E1] citations with styled badge markup and appends
    an evidence panel below the reply.
    """
    enriched = normalize_math_output(text)
    if not evidence or not evidence.items:
        return EnrichedReply(markdown_text=enriched, evidence=evidence)

    enriched_panel = _render_evidence_panel(evidence, extract_cited_ids(text))

    result = f"{enriched}\n\n{enriched_panel}"
    return EnrichedReply(markdown_text=result, evidence=evidence)


def extract_cited_ids(text: str) -> list[str]:
    """Extract unique evidence IDs cited in the text, in order of appearance."""
    seen: set[str] = set()
    ids: list[str] = []
    for match in _CITATION_RE.finditer(text):
        for id_match in _SINGLE_ID_RE.finditer(match.group(1)):
            eid = f"E{id_match.group(1)}"
            if eid not in seen:
                seen.add(eid)
                ids.append(eid)
    return ids


def evidence_summary_text(evidence: TurnEvidence | None) -> str:
    """Return a one-line summary of evidence for the info panel."""
    if not evidence or not evidence.items:
        return "no evidence"
    sources = {chunk.source for chunk in evidence.items}
    if len(sources) == 1:
        src = next(iter(sources))
        return f"{len(evidence.items)} evidence item(s) from {src}"
    return f"{len(evidence.items)} evidence item(s) from {len(sources)} source(s)"
