"""RAG pipeline: index, retrieve, and inject armory content into LLM context."""

from hephaistos.harness.rag.context import build_context, estimate_tokens
from hephaistos.harness.rag.index import ArmoryIndex, build_index, load_or_build
from hephaistos.harness.rag.retrieve import Retriever, ScoredChunk, retrieve

__all__ = [
    "ArmoryIndex",
    "Retriever",
    "ScoredChunk",
    "build_context",
    "build_index",
    "estimate_tokens",
    "load_or_build",
    "retrieve",
]
