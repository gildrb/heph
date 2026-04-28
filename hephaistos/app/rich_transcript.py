# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportPrivateUsage=false
# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false
"""Rich transcript rendering with inline evidence badges and source panels."""

from __future__ import annotations

import re
from dataclasses import dataclass

from hephaistos.harness.rag.context import TurnEvidence

_CITATION_RE = re.compile(r"\[([Ee]\d+(?:\s*[,;]\s*[Ee]\d+)*)\]")
_SINGLE_ID_RE = re.compile(r"[Ee](\d+)")
_EVIDENCE_BADGE_COLOR = "#9B4A2E"
_EVIDENCE_DIM_COLOR = "#555555"
_SOURCE_BADGE_COLOR = "#7F9A6A"
_SCORE_BAR_FULL = "\u2588"
_SCORE_BAR_EMPTY = "\u2591"
_SCORE_BAR_WIDTH = 5


@dataclass(frozen=True, slots=True)
class EnrichedReply:
    """An assistant reply enriched with citation metadata."""

    markdown_text: str
    evidence: TurnEvidence | None


def _render_evidence_badge(evidence_id: str) -> str:
    return f"[bold {_EVIDENCE_BADGE_COLOR}]\u25b6[/bold {_EVIDENCE_BADGE_COLOR}] [{evidence_id}]"


def _render_source_badge(source: str) -> str:
    parts = source.rsplit("/", 1)
    name = parts[-1] if len(parts) > 1 else source
    prefix = parts[0] + "/" if len(parts) > 1 else ""
    dim_close = f"[/dim {_EVIDENCE_DIM_COLOR}]"
    dim_open = f"[dim {_EVIDENCE_DIM_COLOR}]"
    src_open = f"[{_SOURCE_BADGE_COLOR}]"
    src_close = f"[/{_SOURCE_BADGE_COLOR}]"
    if prefix:
        return f"{dim_open}{prefix}{dim_close}{src_open}{name}{src_close}"
    return f"{src_open}{name}{src_close}"


def _render_score_bar(score: float) -> str:
    filled = max(0, min(_SCORE_BAR_WIDTH, round(score * _SCORE_BAR_WIDTH)))
    bar = _SCORE_BAR_FULL * filled + _SCORE_BAR_EMPTY * (_SCORE_BAR_WIDTH - filled)
    return f"[dim {_EVIDENCE_DIM_COLOR}]{bar}[/dim {_EVIDENCE_DIM_COLOR}]"


def _render_evidence_panel(evidence: TurnEvidence) -> str:
    if not evidence.items:
        return ""
    lines: list[str] = []
    header_line = "\u2500" * 3 + " evidence " + "\u2500" * 27
    lines.append(f"[dim {_EVIDENCE_DIM_COLOR}]{header_line}[/dim {_EVIDENCE_DIM_COLOR}]")
    for chunk in evidence.items:
        badge = _render_evidence_badge(chunk.evidence_id)
        source = _render_source_badge(chunk.source)
        bar = _render_score_bar(min(1.0, chunk.score))
        lines.append(f"  {badge}  {source}  {bar}  score={chunk.score:.2f}")
        preview = chunk.content.strip()
        if len(preview) > 200:
            preview = preview[:197] + "..."
        lines.extend(
            f"  [dim {_EVIDENCE_DIM_COLOR}]    {line}[/dim {_EVIDENCE_DIM_COLOR}]"
            for line in preview.split("\n")
        )
    return "\n".join(lines)


def enrich_reply(text: str, evidence: TurnEvidence | None) -> EnrichedReply:
    """Enrich a raw assistant reply with citation badge markup.

    Replaces plain [E1] citations with styled badge markup and appends
    an evidence panel below the reply.
    """
    if not evidence or not evidence.items:
        return EnrichedReply(markdown_text=text, evidence=evidence)

    enriched = text
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
