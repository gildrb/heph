"""Tests for the typed RAG evidence builder."""

from __future__ import annotations

from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.context import build_context, build_turn_evidence, estimate_tokens
from hephaistos.harness.rag.retrieve import ScoredChunk


def _make_scored(text: str, source: str = "test.md", score: float = 1.0) -> ScoredChunk:
    chunk = Chunk(text=text, source=source, index=0, char_start=0, char_end=len(text))
    return ScoredChunk(chunk=chunk, score=score)


class TestBuildTurnEvidence:
    def test_empty_input(self) -> None:
        evidence = build_turn_evidence([])
        assert not evidence
        assert evidence.items == ()
        assert evidence.render() == ""

    def test_assigns_stable_ids(self) -> None:
        evidence = build_turn_evidence(
            [
                _make_scored("Content A.", "a.md", 0.9),
                _make_scored("Content B.", "b.md", 0.8),
            ]
        )
        assert [item.evidence_id for item in evidence.items] == ["E1", "E2"]

    def test_render_includes_instruction_and_content(self) -> None:
        evidence = build_turn_evidence([_make_scored("Python is great.", "python.md", 0.95)])
        rendered = evidence.render()
        assert "Retrieved evidence for this question" in rendered
        assert "[E1]" in rendered
        assert "python.md" in rendered
        assert "Python is great." in rendered
        assert "0.95" in rendered

    def test_respects_token_budget(self) -> None:
        evidence = build_turn_evidence(
            [_make_scored("A" * 2000, f"doc{i}.md", 1.0 - i * 0.1) for i in range(10)],
            max_tokens=100,
        )
        rendered = evidence.render()
        assert len(rendered) < 1200
        assert len(evidence.items) >= 1

    def test_truncation_marker(self) -> None:
        evidence = build_turn_evidence([_make_scored("A" * 3000, "big.md", 1.0)], max_tokens=50)
        rendered = evidence.render()
        assert "[... truncated]" in rendered

    def test_ordered_by_relevance(self) -> None:
        evidence = build_turn_evidence(
            [
                _make_scored("High relevance content.", "aaa_high.md", 0.9),
                _make_scored("Low relevance content.", "zzz_low.md", 0.3),
            ]
        )
        rendered = evidence.render()
        assert rendered.index("[E1]") < rendered.index("[E2]")
        assert rendered.index("High relevance content") < rendered.index("Low relevance content")


class TestBuildContext:
    def test_wrapper_renders_prompt_text(self) -> None:
        rendered = build_context([_make_scored("Some text.", "notes.md", 0.75)])
        assert "Retrieved evidence for this question" in rendered
        assert "[E1]" in rendered
        assert "notes.md" in rendered


class TestEstimateTokens:
    def test_empty(self) -> None:
        assert estimate_tokens("") == 0

    def test_estimation(self) -> None:
        text = "A" * 100
        assert estimate_tokens(text) == 25

    def test_rounds_down(self) -> None:
        assert estimate_tokens("abc") == 0
