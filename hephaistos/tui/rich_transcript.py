"""Rich transcript rendering with inline evidence badges and source panels."""

from __future__ import annotations

import re
from dataclasses import dataclass

from hephaistos.rag.context import TurnEvidence

_CITATION_RE = re.compile(r"(?:\[|【)([Ee]\d+(?:\s*[,;]\s*[Ee]\d+)*)(?:\]|】)")
_SINGLE_ID_RE = re.compile(r"[Ee](\d+)")
_SCORE_BAR_FULL = "\u2588"
_SCORE_BAR_EMPTY = "\u2591"
_SCORE_BAR_WIDTH = 5
_LATEX_INLINE_RE = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
_LATEX_BLOCK_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)


@dataclass(frozen=True, slots=True)
class EnrichedReply:
    """An assistant reply enriched with citation metadata."""

    markdown_text: str
    evidence: TurnEvidence | None


def _normalize_latex_delimiters(text: str) -> str:
    """Use Markdown-friendly math delimiters for model output."""
    text = _LATEX_BLOCK_RE.sub(lambda match: f"$$\n{match.group(1).strip()}\n$$", text)
    return _LATEX_INLINE_RE.sub(lambda match: f"${match.group(1).strip()}$", text)


def _render_score_bar(score: float) -> str:
    filled = max(0, min(_SCORE_BAR_WIDTH, round(score * _SCORE_BAR_WIDTH)))
    return _SCORE_BAR_FULL * filled + _SCORE_BAR_EMPTY * (_SCORE_BAR_WIDTH - filled)


def _render_evidence_panel(evidence: TurnEvidence) -> str:
    if not evidence.items:
        return ""
    lines: list[str] = ["---", "", "**evidence**"]
    for chunk in evidence.items:
        source_name = chunk.source.rsplit("/", 1)[-1]
        bar = _render_score_bar(min(1.0, chunk.score))
        lines.extend(
            [
                "",
                f"- **{chunk.evidence_id}** `{source_name}` "
                f"chunk {chunk.chunk_index}, score {chunk.score:.2f} {bar}",
            ]
        )
        preview = _normalize_latex_delimiters(chunk.content.strip())
        if len(preview) > 200:
            preview = preview[:197] + "..."
        lines.extend(f"  > {line}" for line in preview.split("\n") if line.strip())
    return "\n".join(lines)


def enrich_reply(text: str, evidence: TurnEvidence | None) -> EnrichedReply:
    """Enrich a raw assistant reply with citation badge markup.

    Replaces plain [E1] citations with styled badge markup and appends
    an evidence panel below the reply.
    """
    if not evidence or not evidence.items:
        return EnrichedReply(markdown_text=text, evidence=evidence)

    enriched = _normalize_latex_delimiters(text)
    enriched_panel = _render_evidence_panel(evidence)

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
        return f"{len(evidence.items)} chunk(s) from {src}"
    return f"{len(evidence.items)} chunk(s) from {len(sources)} source(s)"
