"""Tests for rich transcript rendering with inline evidence badges."""

from __future__ import annotations

from hephaistos.rag.chunker import Chunk
from hephaistos.rag.context import EvidenceChunk, TurnEvidence
from hephaistos.tui.rich_transcript import (
    enrich_reply,
    evidence_summary_text,
    extract_cited_ids,
)


def _make_chunk(source: str, index: int, text: str) -> Chunk:
    return Chunk(
        source=source,
        index=index,
        text=text,
        char_start=0,
        char_end=len(text),
    )


def _make_evidence(*items: tuple[str, str, int, float, str]) -> TurnEvidence:
    chunks: list[EvidenceChunk] = []
    for eid, source, idx, score, content in items:
        chunks.append(
            EvidenceChunk(
                evidence_id=eid,
                chunk=_make_chunk(source, idx, content),
                score=score,
                content=content,
            )
        )
    return TurnEvidence(tuple(chunks))


def test_enrich_reply_with_no_evidence_returns_text_unchanged() -> None:
    result = enrich_reply("Hello world", None)
    assert result.markdown_text == "Hello world"
    assert result.evidence is None


def test_enrich_reply_with_empty_evidence_returns_text_unchanged() -> None:
    result = enrich_reply("Hello world", TurnEvidence())
    assert result.markdown_text == "Hello world"


def test_enrich_reply_appends_evidence_panel() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.85, "Binary search is O(log n)."),
    )
    result = enrich_reply("The answer is O(log n) [E1].", evidence)

    assert "[E1]" in result.markdown_text
    assert "evidence" in result.markdown_text
    assert "algorithms.md" in result.markdown_text
    assert "0.85" in result.markdown_text
    assert "Binary search is O(log n)" in result.markdown_text


def test_enrich_reply_with_multiple_evidence_chunks() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.90, "First chunk."),
        ("E2", "source/datastructures.md", 1, 0.75, "Second chunk."),
    )
    result = enrich_reply("See [E1] and [E2].", evidence)

    assert "E1" in result.markdown_text
    assert "E2" in result.markdown_text
    assert "algorithms.md" in result.markdown_text
    assert "datastructures.md" in result.markdown_text


def test_extract_cited_ids_finds_single_citation() -> None:
    ids = extract_cited_ids("The answer is [E1].")
    assert ids == ["E1"]


def test_extract_cited_ids_finds_multiple_in_one_bracket() -> None:
    ids = extract_cited_ids("See [E1, E2] for details.")
    assert ids == ["E1", "E2"]


def test_extract_cited_ids_deduplicates() -> None:
    ids = extract_cited_ids("[E1] and again [E1]")
    assert ids == ["E1"]


def test_extract_cited_ids_handles_lowercase() -> None:
    ids = extract_cited_ids("See [e3].")
    assert ids == ["E3"]


def test_extract_cited_ids_returns_empty_for_no_citations() -> None:
    ids = extract_cited_ids("No citations here.")
    assert ids == []


def test_evidence_summary_text_with_no_evidence() -> None:
    assert evidence_summary_text(None) == "no evidence"
    assert evidence_summary_text(TurnEvidence()) == "no evidence"


def test_evidence_summary_text_with_single_source() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.9, "chunk1"),
        ("E2", "source/algorithms.md", 1, 0.8, "chunk2"),
    )
    summary = evidence_summary_text(evidence)
    assert "2 chunk(s)" in summary
    assert "algorithms.md" in summary


def test_evidence_summary_text_with_multiple_sources() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.9, "chunk1"),
        ("E2", "source/datastructures.md", 0, 0.8, "chunk2"),
    )
    summary = evidence_summary_text(evidence)
    assert "2 chunk(s)" in summary
    assert "2 source(s)" in summary


def test_evidence_panel_truncates_long_content() -> None:
    long_text = "A" * 500
    evidence = _make_evidence(("E1", "source/long.md", 0, 0.5, long_text))
    result = enrich_reply("See [E1].", evidence)

    assert "..." in result.markdown_text
    assert len(result.markdown_text) < len(long_text) + 500
