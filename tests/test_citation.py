"""Tests for citation verification: extraction, verification, and notice formatting."""

from __future__ import annotations

from hephaistos.chat.engine import Message
from hephaistos.harness.citation import (
    VerificationResult,
    _get_rag_sources,
    extract_citations,
    format_verification_notice,
    verify_citations,
    verify_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rag_message(*sources: str, chunks_per_source: int = 1) -> Message:
    """Build a RAG context system message with the given source paths."""
    parts = ["Source material retrieved for this question:\n"]
    for src in sources:
        for i in range(chunks_per_source):
            parts.append(f"\n--- {src} (chunk {i}, relevance: 0.75) ---")
            parts.append(f"Content of {src}, chunk {i}.\n")
    return Message(role="system", content="".join(parts))


# ---------------------------------------------------------------------------
# _get_rag_sources
# ---------------------------------------------------------------------------


class TestGetRagSources:
    def test_extracts_single_source(self) -> None:
        msg = _rag_message("source/notes.md")
        assert _get_rag_sources([msg]) == {"source/notes.md"}

    def test_extracts_multiple_sources(self) -> None:
        msg = _rag_message("source/a.md", "library/b.txt")
        assert _get_rag_sources([msg]) == {"source/a.md", "library/b.txt"}

    def test_ignores_non_rag_system_messages(self) -> None:
        messages = [
            Message(role="system", content="You are a helpful assistant."),
        ]
        assert _get_rag_sources(messages) == set()

    def test_ignores_user_messages(self) -> None:
        messages = [
            Message(role="user", content="What is TCP?"),
            _rag_message("source/network.md"),
        ]
        assert _get_rag_sources(messages) == {"source/network.md"}

    def test_multiple_rag_messages(self) -> None:
        messages = [
            _rag_message("source/a.md"),
            _rag_message("source/b.md"),
        ]
        assert _get_rag_sources(messages) == {"source/a.md", "source/b.md"}

    def test_empty_messages(self) -> None:
        assert _get_rag_sources([]) == set()


# ---------------------------------------------------------------------------
# extract_citations
# ---------------------------------------------------------------------------


class TestExtractCitations:
    def test_explicit_source_colon(self) -> None:
        text = "TCP uses a 3-way handshake (source: networking.md)."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "networking.md"

    def test_source_dash(self) -> None:
        text = "The answer is 42 — answers.md"
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "answers.md"

    def test_parenthetical_citation(self) -> None:
        text = "See the handshake diagram (networking.md) for details."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "networking.md"

    def test_according_to(self) -> None:
        text = "According to networking.md, TCP uses SYN packets."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "networking.md"

    def test_from_source(self) -> None:
        text = "From source/notes.md we learn that UDP is connectionless."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "source/notes.md"

    def test_in_source(self) -> None:
        text = "In exam_2023.pdf the professor asks about OSI layers."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "exam_2023.pdf"

    def test_see_source(self) -> None:
        text = "See reference.md for more details."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "reference.md"

    def test_multiple_citations(self) -> None:
        text = (
            "According to networking.md, TCP is reliable. "
            "From algorithms.py we see the pseudocode. "
            "(source: exam_2022.pdf)"
        )
        cits = extract_citations(text)
        assert len(cits) == 3
        raws = {c.raw for c in cits}
        assert raws == {"networking.md", "algorithms.py", "exam_2022.pdf"}

    def test_deduplicates_same_source(self) -> None:
        text = "See notes.md. Also (source: notes.md) confirms this."
        cits = extract_citations(text)
        assert len(cits) == 1

    def test_empty_text(self) -> None:
        assert extract_citations("") == []

    def test_no_citations(self) -> None:
        text = "The answer is 42. No sources needed here."
        assert extract_citations(text) == []

    def test_em_dash_attribution(self) -> None:
        text = "TCP handshake: SYN, SYN-ACK, ACK — networking_notes.md"
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "networking_notes.md"

    def test_case_insensitive_source_prefix(self) -> None:
        text = "TCP is reliable (Source: networking.md)."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "networking.md"

    def test_full_path_citation(self) -> None:
        text = "According to source/chapter10/networking.md, the port is 80."
        cits = extract_citations(text)
        assert len(cits) == 1
        assert cits[0].raw == "source/chapter10/networking.md"

    def test_no_false_positive_sentence_end(self) -> None:
        """A period at end of sentence should not create a false match."""
        text = "The answer is found in the textbook."
        cits = extract_citations(text)
        assert len(cits) == 0


# ---------------------------------------------------------------------------
# verify_citations
# ---------------------------------------------------------------------------


class TestVerifyCitations:
    def test_all_verified(self) -> None:
        reply = "According to networking.md, TCP is reliable."
        sources = {"source/networking.md"}
        result = verify_citations(reply, sources)
        assert result.all_verified
        assert result.verified == ["networking.md"]
        assert result.unverified == []
        assert result.citation_count == 1

    def test_unverified_citation(self) -> None:
        reply = "From made_up.md we learn that TCP is unreliable."
        sources = {"source/networking.md"}
        result = verify_citations(reply, sources)
        assert not result.all_verified
        assert result.unverified == ["made_up.md"]
        assert result.verified == []

    def test_mixed_verified_unverified(self) -> None:
        reply = (
            "According to networking.md, TCP is reliable. "
            "From fiction.md, we learn it's not."
        )
        sources = {"source/networking.md"}
        result = verify_citations(reply, sources)
        assert not result.all_verified
        assert result.verified == ["networking.md"]
        assert result.unverified == ["fiction.md"]

    def test_no_citations(self) -> None:
        reply = "The answer is 42."
        sources = {"source/notes.md"}
        result = verify_citations(reply, sources)
        assert result.all_verified
        assert result.citation_count == 0
        assert not result.has_citations

    def test_no_rag_context(self) -> None:
        reply = "According to networking.md, TCP is reliable."
        result = verify_citations(reply, set())
        assert not result.all_verified
        assert not result.rag_context_present
        assert result.unverified == ["networking.md"]

    def test_basename_matching(self) -> None:
        """'notes.md' should match 'source/notes.md'."""
        reply = "See notes.md for details."
        sources = {"source/notes.md"}
        result = verify_citations(reply, sources)
        assert result.all_verified

    def test_empty_reply(self) -> None:
        result = verify_citations("", {"source/a.md"})
        assert result.all_verified
        assert result.citation_count == 0


# ---------------------------------------------------------------------------
# format_verification_notice
# ---------------------------------------------------------------------------


class TestFormatVerificationNotice:
    def test_no_notice_when_all_verified(self) -> None:
        result = VerificationResult(
            verified=["a.md"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            rag_context_present=True,
        )
        assert format_verification_notice(result, 500) == ""

    def test_unverified_citation_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=["fiction.md"],
            citation_count=1,
            has_citations=True,
            all_verified=False,
            rag_context_present=True,
        )
        notice = format_verification_notice(result, 500)
        assert "fiction.md" in notice
        assert "Unverified" in notice

    def test_no_citations_long_answer_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            rag_context_present=True,
        )
        # Long answer (> 200 chars)
        notice = format_verification_notice(result, 500)
        assert "No source citations" in notice

    def test_no_citations_short_answer_no_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            rag_context_present=True,
        )
        # Short answer (≤ 200 chars) — no warning
        notice = format_verification_notice(result, 100)
        assert notice == ""

    def test_multiple_unverified_truncated(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=["a.md", "b.md", "c.md", "d.md", "e.md", "f.md"],
            citation_count=6,
            has_citations=True,
            all_verified=False,
            rag_context_present=True,
        )
        notice = format_verification_notice(result, 500)
        # Should show at most 5
        assert "a.md" in notice
        assert "e.md" in notice


# ---------------------------------------------------------------------------
# verify_response (end-to-end)
# ---------------------------------------------------------------------------


class TestVerifyResponse:
    def test_verified_response_no_notice(self) -> None:
        messages = [
            _rag_message("source/networking.md"),
            Message(role="user", content="What is TCP?"),
        ]
        reply = "According to networking.md, TCP uses a 3-way handshake."
        notice = verify_response(reply, messages)
        assert notice == ""

    def test_hallucinated_citation_notice(self) -> None:
        messages = [
            _rag_message("source/networking.md"),
            Message(role="user", content="What is UDP?"),
        ]
        reply = "From made_up_doc.md, UDP is connectionless."
        notice = verify_response(reply, messages)
        assert "made_up_doc.md" in notice
        assert "Unverified" in notice

    def test_no_citations_long_answer_notice(self) -> None:
        messages = [
            _rag_message("source/networking.md"),
            Message(role="user", content="Explain TCP"),
        ]
        reply = (
            "TCP is a connection-oriented protocol that provides reliable, "
            "ordered, and error-checked delivery of a stream of bytes between "
            "applications. It establishes a connection via a three-way handshake "
            "using SYN, SYN-ACK, and ACK packets. This ensures both parties are "
            "ready to communicate before data transfer begins."
        )
        notice = verify_response(reply, messages)
        assert "No source citations" in notice

    def test_no_rag_context_no_notice(self) -> None:
        messages = [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello"),
        ]
        reply = "Hello! How can I help?"
        notice = verify_response(reply, messages)
        assert notice == ""

    def test_never_raises(self) -> None:
        """verify_response must never throw, even with bad input."""
        notice = verify_response("test", None)  # type: ignore[arg-type]
        assert notice == ""
