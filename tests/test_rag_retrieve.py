"""Tests for the RAG retriever."""

from __future__ import annotations

from pathlib import Path

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.index import ArmoryIndex
from hephaistos.harness.rag.retrieve import Retriever, ScoredChunk, retrieve


def _make_chunk(text: str, source: str = "test.md", index: int = 0) -> Chunk:
    return Chunk(text=text, source=source, index=index, char_start=0, char_end=len(text))


def _make_index_with_chunks(chunks: list[Chunk]) -> ArmoryIndex:
    """Build a minimal ArmoryIndex with the given chunks."""
    from hephaistos.harness.rag.chunker import ChunkedDocument

    by_source: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)

    index = ArmoryIndex(Path("/fake"))
    for source, source_chunks in by_source.items():
        index.documents.append(ChunkedDocument(
            source=source,
            chunks=source_chunks,
            content_hash="fake",
        ))
    return index


class TestRetriever:
    def test_empty_index_returns_nothing(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = Retriever(index)
        results = retriever.retrieve("python")
        assert results == []

    def test_exact_keyword_match(self) -> None:
        chunks = [
            _make_chunk("Python is a programming language with dynamic typing.", "python.md", 0),
            _make_chunk("Rust is a systems programming language with ownership.", "rust.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("python programming")

        assert len(results) > 0
        assert results[0].chunk.source == "python.md"

    def test_top_k_limit(self) -> None:
        chunks = [
            _make_chunk(f"Document about topic number {i}.", f"doc{i}.md", 0)
            for i in range(10)
        ]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("topic number", top_k=3)
        assert len(results) == 3

    def test_scores_are_positive(self) -> None:
        chunks = [
            _make_chunk("Machine learning uses neural networks.", "ml.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("machine learning")
        for r in results:
            assert r.score > 0

    def test_results_sorted_by_score(self) -> None:
        chunks = [
            _make_chunk("Python Python Python programming language", "a.md", 0),
            _make_chunk("Python is mentioned once here.", "b.md", 0),
            _make_chunk("Completely unrelated content about cooking.", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("python")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_query_returns_nothing(self) -> None:
        chunks = [_make_chunk("Some content", "a.md", 0)]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("")
        assert results == []

    def test_stop_words_only_query(self) -> None:
        chunks = [_make_chunk("Some content about things", "a.md", 0)]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("the is a")
        assert results == []

    def test_no_match_returns_empty(self) -> None:
        chunks = [
            _make_chunk("Cooking recipes and baking tips.", "cooking.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = Retriever(index)
        results = retriever.retrieve("quantum physics astronomy")
        assert results == []


class TestRetrieveConvenience:
    def test_convenience_function(self) -> None:
        chunks = [
            _make_chunk("Binary search runs in O(log n) time.", "algo.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve("binary search algorithm", index)
        assert len(results) > 0
        assert isinstance(results[0], ScoredChunk)
