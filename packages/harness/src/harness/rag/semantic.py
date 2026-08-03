"""Reserved seam for a future provider-backed embedding retriever."""

from __future__ import annotations

from harness.rag.retrieval_types import ScoredChunk


class EmbeddingRetriever:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError(
            "Dense retrieval is unavailable in the lean install; use BM25 or TF-IDF."
        )

    def retrieve(self, _query: str, _top_k: int = 5) -> list[ScoredChunk]:
        raise RuntimeError(
            "Dense retrieval is unavailable in the lean install; use BM25 or TF-IDF."
        )


class CrossEncoderReranker:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Reranking is unavailable in the lean install; use lexical retrieval.")
