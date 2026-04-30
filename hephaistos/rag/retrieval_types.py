"""Public retrieval result and backend protocol types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hephaistos.rag.chunker import Chunk


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Stable reference to a source chunk used as turn evidence."""

    source: str
    chunk_index: int

    def render(self) -> str:
        """Render as the persisted ``path#chunk=N`` form."""
        return f"{self.source}#chunk={self.chunk_index}"

    @classmethod
    def parse(cls, value: str) -> EvidenceReference | None:
        """Parse the persisted ``path#chunk=N`` form."""
        source, sep, suffix = value.partition("#chunk=")
        if not sep:
            return None
        try:
            return cls(source=source, chunk_index=int(suffix))
        except ValueError:
            return None


@runtime_checkable
class RetrieverProtocol(Protocol):
    """Minimal interface every retriever must implement."""

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]: ...


@runtime_checkable
class RerankerProtocol(Protocol):
    """Interface for post-retrieval re-rankers."""

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]: ...
