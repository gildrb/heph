from __future__ import annotations

from html import unescape

from harness.rag.context import TurnEvidence
from harness.rag.retrieval_types import EvidenceReference


def excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(unescape(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def evidence_refs(turn_evidence: TurnEvidence | None) -> list[str]:
    if not turn_evidence:
        return []
    return [
        EvidenceReference(item.source, item.chunk_index).render() for item in turn_evidence.items
    ]
