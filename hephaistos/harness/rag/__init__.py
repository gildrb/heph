"""RAG pipeline: index, retrieve, and inject armory content into LLM context."""

from hephaistos.harness.rag.chunker import (
    Chunk,
    ChunkStrategy,
    chunk_file,
    chunk_markdown,
    chunk_semantic,
    chunk_text,
)
from hephaistos.harness.rag.context import build_context, estimate_tokens
from hephaistos.harness.rag.index import ArmoryIndex, build_index, load_or_build
from hephaistos.harness.rag.retrieve import (
    CrossEncoderReranker,
    EmbeddingRetriever,
    HybridRetriever,
    RerankerProtocol,
    Retriever,
    RetrieverProtocol,
    ScoredChunk,
    TfidfRetriever,
    retrieve,
)

__all__ = [
    "ArmoryIndex",
    "Chunk",
    "ChunkStrategy",
    "CrossEncoderReranker",
    "EmbeddingRetriever",
    "HybridRetriever",
    "RerankerProtocol",
    "Retriever",
    "RetrieverProtocol",
    "ScoredChunk",
    "TfidfRetriever",
    "build_context",
    "build_index",
    "chunk_file",
    "chunk_markdown",
    "chunk_semantic",
    "chunk_text",
    "estimate_tokens",
    "load_or_build",
    "retrieve",
]
