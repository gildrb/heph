"""Public retrieval result and backend protocol types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hephaistos.rag.chunker import Chunk

type RetrieverCacheKey = tuple[
    str,
    int | None,
    str,
    int,
    str | None,
    str | None,
    str,
    str,
    float,
    float,
    int,
    int,
    float,
]


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    source: str
    chunk_index: int

    def render(self) -> str:
        """Render as the persisted ``path#chunk=N`` form."""
        return f"{self.source}#chunk={self.chunk_index}"

    @classmethod
    def parse(cls, value: str) -> EvidenceReference | None:
        """Parse the persisted ``path#chunk=N`` form."""
        source, sep, suffix = value.partition("#chunk=")
        if not sep or not source:
            return None
        try:
            chunk_index = int(suffix)
        except ValueError:
            return None
        if chunk_index < 0:
            return None
        return cls(source=source, chunk_index=chunk_index)


@runtime_checkable
class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]: ...


@runtime_checkable
class RerankerProtocol(Protocol):
    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]: ...
