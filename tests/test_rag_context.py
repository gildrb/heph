"""Tests for the RAG context builder."""

from __future__ import annotations

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.context import build_context, estimate_tokens
from hephaistos.harness.rag.retrieve import ScoredChunk


def _make_scored(text: str, source: str = "test.md", score: float = 1.0) -> ScoredChunk:
    chunk = Chunk(text=text, source=source, index=0, char_start=0, char_end=len(text))
    return ScoredChunk(chunk=chunk, score=score)


class TestBuildContext:
    def test_empty_input(self) -> None:
        assert build_context([]) == ""

    def test_single_chunk(self) -> None:
        sc = _make_scored("Python is great.", "python.md", 0.95)
        result = build_context([sc])
        assert "python.md" in result
        assert "Python is great." in result
        assert "0.95" in result

    def test_multiple_chunks(self) -> None:
        chunks = [
            _make_scored("Content A.", "a.md", 0.9),
            _make_scored("Content B.", "b.md", 0.8),
        ]
        result = build_context(chunks)
        assert "a.md" in result
        assert "b.md" in result
        assert "Content A." in result
        assert "Content B." in result

    def test_source_attribution_format(self) -> None:
        sc = _make_scored("Some text.", "notes.md", 0.75)
        result = build_context([sc])
        assert "--- notes.md" in result
        assert "relevance: 0.75" in result

    def test_respects_token_budget(self) -> None:
        long_chunks = [
            _make_scored("A" * 2000, f"doc{i}.md", 1.0 - i * 0.1)
            for i in range(10)
        ]
        result = build_context(long_chunks, max_tokens=100)
        # 100 tokens * 4 chars = 400 chars budget
        assert len(result) < 1000  # well within reason

    def test_truncation_marker(self) -> None:
        chunks = [
            _make_scored("A" * 3000, "big.md", 1.0),
        ]
        result = build_context(chunks, max_tokens=50)
        # Should include truncation indicator
        assert "[... truncated]" in result

    def test_ordered_by_relevance(self) -> None:
        # build_context preserves input order; retrieve() returns highest-first
        chunks = [
            _make_scored("High relevance content.", "aaa_high.md", 0.9),
            _make_scored("Low relevance content.", "zzz_low.md", 0.3),
        ]
        result = build_context(chunks)
        high_pos = result.index("High relevance content")
        low_pos = result.index("Low relevance content")
        assert high_pos < low_pos


class TestEstimateTokens:
    def test_empty(self) -> None:
        assert estimate_tokens("") == 0

    def test_estimation(self) -> None:
        text = "A" * 100
        assert estimate_tokens(text) == 25

    def test_rounds_down(self) -> None:
        assert estimate_tokens("abc") == 0
