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
from hephaistos.harness.rag.query_transform import (
    CompositeTransformer,
    HyDETransformer,
    IdentityTransformer,
    MultiQueryTransformer,
    PromptFn,
    QueryExpander,
    QueryTransformerProtocol,
    TransformStrategy,
    create_transformer,
    transform_query,
)
from hephaistos.harness.rag.retrieve import (
    CrossEncoderReranker,
    EmbeddingRetriever,
    HybridRetriever,
    RerankerProtocol,
    RetrieverProtocol,
    ScoredChunk,
    TfidfRetriever,
    retrieve,
)

__all__ = [
    "ArmoryIndex",
    "Chunk",
    "ChunkStrategy",
    "CompositeTransformer",
    "CrossEncoderReranker",
    "EmbeddingRetriever",
    "HyDETransformer",
    "HybridRetriever",
    "IdentityTransformer",
    "MultiQueryTransformer",
    "PromptFn",
    "QueryExpander",
    "QueryTransformerProtocol",
    "RerankerProtocol",
    "RetrieverProtocol",
    "ScoredChunk",
    "TfidfRetriever",
    "TransformStrategy",
    "build_context",
    "build_index",
    "chunk_file",
    "chunk_markdown",
    "chunk_semantic",
    "chunk_text",
    "create_transformer",
    "estimate_tokens",
    "load_or_build",
    "retrieve",
    "transform_query",
]
