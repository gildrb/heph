"""Typed turn evidence for retrieval-grounded answers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

try:
    import tiktoken
except Exception:
    _encoder = None
else:
    try:
        _encoder = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _encoder = None

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.rag.chunker import Chunk
from hephaistos.rag.retrieve import ScoredChunk

_CHARS_PER_TOKEN = 4
_EVIDENCE_ID_PREFIX = "E"
_EVIDENCE_HEADER_TEMPLATE = "[{evidence_id}] {source} (chunk {index}, relevance: {score:.2f})"
_EVIDENCE_PROMPT_PREFIX = "Retrieved evidence for this question:\n\n"
_DISTINCT_SOURCE_HEAD_LIMIT = 4
_TRUNCATION_MARKER = "[... truncated]"


@dataclass(frozen=True, slots=True)
class EvidenceChunk:
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
    items: tuple[EvidenceChunk, ...] = ()
    sampled_source_count: int = 0
    total_source_count: int = 0

    def __bool__(self) -> bool:
        return bool(self.items)

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

        rendered_items: list[str] = []
        for item in self.items:
            header = _EVIDENCE_HEADER_TEMPLATE.format(
                evidence_id=item.evidence_id,
                source=item.source,
                index=item.chunk_index,
                score=item.score,
            )
            rendered_items.append(f"{header}\n{item.content}")
        return _EVIDENCE_PROMPT_PREFIX + "\n\n".join(rendered_items)

    def to_dict(self) -> dict[str, object]:
        return {
            "items": [_evidence_chunk_to_dict(item) for item in self.items],
            "sampled_source_count": self.sampled_source_count,
            "total_source_count": self.total_source_count,
        }

    @classmethod
    def from_dict(cls, payload: object) -> TurnEvidence | None:
        if not is_string_mapping(payload):
            return None
        items = tuple(
            item
            for raw_item in _payload_object_list(payload, "items")
            if (item := _evidence_chunk_from_dict(raw_item)) is not None
        )
        return cls(
            items=items,
            sampled_source_count=_payload_int(payload, "sampled_source_count"),
            total_source_count=_payload_int(payload, "total_source_count"),
        )


def build_turn_evidence(
    scored_chunks: list[ScoredChunk],
    max_tokens: int = 2000,
) -> TurnEvidence:
    """Build citable turn evidence from retrieved chunks.

    The prompt head prefers the first few distinct sources before spending
    budget on duplicate-source neighbors. This keeps multi-source synthesis
    possible under tight budgets while preserving original relevance order
    within the promoted source-diverse head and the remaining tail. Included
    chunks are assigned stable IDs (``E1``, ``E2``, ...) in prompt order. When
    the next chunk would exceed the budget, its content is truncated if enough
    room remains to preserve a useful partial block.
    """
    if not scored_chunks:
        return TurnEvidence()

    budget_chars = max_tokens * _CHARS_PER_TOKEN
    used = 0
    items: list[EvidenceChunk] = []

    for idx, sc in enumerate(_prioritize_distinct_sources(scored_chunks), start=1):
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


def _prioritize_distinct_sources(scored_chunks: list[ScoredChunk]) -> list[ScoredChunk]:
    source_head: list[ScoredChunk] = []
    tail: list[ScoredChunk] = []
    seen_sources: set[str] = set()

    for scored_chunk in scored_chunks:
        source = scored_chunk.chunk.source
        if source not in seen_sources and len(source_head) < _DISTINCT_SOURCE_HEAD_LIMIT:
            source_head.append(scored_chunk)
            seen_sources.add(source)
        else:
            tail.append(scored_chunk)

    return [*source_head, *tail]


def _evidence_chunk_to_dict(item: EvidenceChunk) -> dict[str, object]:
    chunk = item.chunk
    return {
        "evidence_id": item.evidence_id,
        "score": item.score,
        "content": item.content,
        "chunk": {
            "text": chunk.text,
            "source": chunk.source,
            "index": chunk.index,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "heading": chunk.heading,
            "heading_level": chunk.heading_level,
        },
    }


def _evidence_chunk_from_dict(payload: object) -> EvidenceChunk | None:
    if not is_string_mapping(payload):
        return None
    raw_chunk = payload.get("chunk")
    if not is_string_mapping(raw_chunk):
        return None
    evidence_id = _payload_string(payload, "evidence_id").upper()
    content = _payload_string(payload, "content")
    source = _payload_string(raw_chunk, "source")
    if not evidence_id or not content or not source:
        return None
    chunk = Chunk(
        text=_payload_string(raw_chunk, "text"),
        source=source,
        index=_payload_int(raw_chunk, "index"),
        char_start=_payload_int(raw_chunk, "char_start"),
        char_end=_payload_int(raw_chunk, "char_end"),
        heading=_payload_string(raw_chunk, "heading"),
        heading_level=_payload_int(raw_chunk, "heading_level"),
    )
    return EvidenceChunk(
        evidence_id=evidence_id,
        chunk=chunk,
        score=_payload_float(payload, "score"),
        content=content,
    )


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _payload_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    return 0


def _payload_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _payload_object_list(payload: Mapping[str, object], key: str) -> list[object]:
    value = payload.get(key)
    return value if is_object_list(value) else []


def build_context(
    scored_chunks: list[ScoredChunk],
    max_tokens: int = 2000,
) -> str:
    return build_turn_evidence(scored_chunks, max_tokens=max_tokens).render()


def estimate_tokens(text: str) -> int:
    if _encoder is not None:
        return len(_encoder.encode(text))
    return len(text) // _CHARS_PER_TOKEN
