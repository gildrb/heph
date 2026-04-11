"""Typed turn evidence for retrieval-grounded answers.

Builds a first-class evidence object from retrieved chunks, assigns stable
IDs (``E1``, ``E2``, ...), and renders that evidence into the prompt format
shown to the model. The rendered prompt requires the assistant to cite
those evidence IDs instead of raw filenames.
"""

from __future__ import annotations

from dataclasses import dataclass

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.retrieve import ScoredChunk

_CHARS_PER_TOKEN = 4
_EVIDENCE_ID_PREFIX = "E"
_EVIDENCE_HEADER_TEMPLATE = "[{evidence_id}] {source} (chunk {index}, relevance: {score:.2f})"
_EVIDENCE_PROMPT_PREFIX = (
    "Retrieved evidence for this question:\n\n"
    "Cite evidence IDs in brackets after factual claims, for example [E1] or [E1][E2]. "
    "Do not cite filenames by themselves.\n\n"
)
_TRUNCATION_MARKER = "[... truncated]"


@dataclass(frozen=True, slots=True)
class EvidenceChunk:
    """A retrieved chunk promoted into a stable, citable evidence block."""

    evidence_id: str
    chunk: Chunk
    score: float
    content: str

    @property
    def source(self) -> str:
        return self.chunk.source

    @property
    def chunk_index(self) -> int:
        return self.chunk.index


@dataclass(frozen=True, slots=True)
class TurnEvidence:
    """Evidence assembled for a single user turn."""

    items: tuple[EvidenceChunk, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.items)

    @property
    def ids(self) -> set[str]:
        return {item.evidence_id for item in self.items}

    def get(self, evidence_id: str) -> EvidenceChunk | None:
        normalized = evidence_id.strip().upper()
        for item in self.items:
            if item.evidence_id == normalized:
                return item
        return None

    def render(self) -> str:
        """Render evidence into the prompt format shown to the model."""
        if not self.items:
            return ""

        parts = [_EVIDENCE_PROMPT_PREFIX]
        rendered_items = [
            _render_evidence_item(item)
            for item in self.items
        ]
        parts.append("\n\n".join(rendered_items))
        return "".join(parts)


def _render_evidence_item(item: EvidenceChunk) -> str:
    header = _EVIDENCE_HEADER_TEMPLATE.format(
        evidence_id=item.evidence_id,
        source=item.source,
        index=item.chunk_index,
        score=item.score,
    )
    return f"{header}\n{item.content}"


def build_turn_evidence(
    scored_chunks: list[ScoredChunk],
    max_tokens: int = 2000,
) -> TurnEvidence:
    """Build citable turn evidence from retrieved chunks.

    Chunks are included in relevance order until the budget is exhausted.
    Included chunks are assigned stable IDs (``E1``, ``E2``, ...) in prompt
    order. When the next chunk would exceed the budget, its content is
    truncated if enough room remains to preserve a useful partial block.
    """
    if not scored_chunks:
        return TurnEvidence()

    budget_chars = max_tokens * _CHARS_PER_TOKEN
    used = 0
    items: list[EvidenceChunk] = []

    for idx, sc in enumerate(scored_chunks, start=1):
        evidence_id = f"{_EVIDENCE_ID_PREFIX}{idx}"
        header = _EVIDENCE_HEADER_TEMPLATE.format(
            evidence_id=evidence_id,
            source=sc.chunk.source,
            index=sc.chunk.index,
            score=sc.score,
        )
        entry = f"{header}\n{sc.chunk.text}"
        entry_len = len(entry) + 2  # +2 for newline separators between blocks

        if used + entry_len > budget_chars:
            remaining = budget_chars - used
            minimum = len(header) + len(_TRUNCATION_MARKER) + 12
            if remaining > minimum:
                available = max(0, remaining - len(header) - len(_TRUNCATION_MARKER) - 10)
                truncated = sc.chunk.text[:available].rstrip()
                if truncated:
                    items.append(
                        EvidenceChunk(
                            evidence_id=evidence_id,
                            chunk=sc.chunk,
                            score=sc.score,
                            content=f"{truncated}\n{_TRUNCATION_MARKER}",
                        )
                    )
            break

        items.append(
            EvidenceChunk(
                evidence_id=evidence_id,
                chunk=sc.chunk,
                score=sc.score,
                content=sc.chunk.text,
            )
        )
        used += entry_len

    return TurnEvidence(tuple(items))


def build_context(
    scored_chunks: list[ScoredChunk],
    max_tokens: int = 2000,
) -> str:
    """Backward-compatible wrapper that renders typed turn evidence."""
    return build_turn_evidence(scored_chunks, max_tokens=max_tokens).render()


def estimate_tokens(text: str) -> int:
    """Rough token estimate for budget tracking."""
    return len(text) // _CHARS_PER_TOKEN
