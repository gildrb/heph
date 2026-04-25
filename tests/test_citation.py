"""Tests for evidence-citation verification."""

from __future__ import annotations

from hephaistos.harness.citation import (
    VerificationResult,
    extract_citations,
    format_verification_notice,
    verify_citations,
    verify_response,
)
from hephaistos.harness.rag.chunker import Chunk
from hephaistos.harness.rag.context import TurnEvidence, build_turn_evidence
from hephaistos.harness.rag.retrieve import ScoredChunk

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_turn_evidence(*sources: str) -> TurnEvidence:
    scored: list[ScoredChunk] = []
    for index, source in enumerate(sources):
        chunk = Chunk(
            text=f"Content of {source}.",
            source=source,
            index=index,
            char_start=0,
            char_end=len(source) + 12,
        )
        scored.append(ScoredChunk(chunk=chunk, score=1.0 - index * 0.1))
    return build_turn_evidence(scored)


# ---------------------------------------------------------------------------
# extract_citations
# ---------------------------------------------------------------------------


class TestExtractCitations:
    def test_single_evidence_id(self) -> None:
        cits = extract_citations("TCP uses a 3-way handshake [E1].")
        assert [c.evidence_id for c in cits] == ["E1"]

    def test_multiple_evidence_ids_in_one_group(self) -> None:
        cits = extract_citations("Handshake [E1, E2] is described in both chunks.")
        assert [c.evidence_id for c in cits] == ["E1", "E2"]

    def test_multiple_groups(self) -> None:
        cits = extract_citations("Claim one [E1]. Claim two [E2].")
        assert [c.evidence_id for c in cits] == ["E1", "E2"]

    def test_semicolon_separator(self) -> None:
        cits = extract_citations("Claim [E1; E2].")
        assert [c.evidence_id for c in cits] == ["E1", "E2"]

    def test_case_insensitive_ids(self) -> None:
        cits = extract_citations("Claim [e1, e2].")
        assert [c.evidence_id for c in cits] == ["E1", "E2"]

    def test_deduplicates_ids(self) -> None:
        cits = extract_citations("Claim [E1]. Another claim [E1].")
        assert [c.evidence_id for c in cits] == ["E1"]

    def test_ignores_raw_filenames(self) -> None:
        cits = extract_citations("According to networking.md, TCP is reliable.")
        assert cits == []

    def test_empty_text(self) -> None:
        assert extract_citations("") == []


# ---------------------------------------------------------------------------
# verify_citations
# ---------------------------------------------------------------------------


class TestVerifyCitations:
    def test_all_verified(self) -> None:
        evidence = _make_turn_evidence("source/networking.md")
        result = verify_citations("TCP is reliable [E1].", evidence)
        assert result.all_verified
        assert result.verified == ["E1"]
        assert result.unverified == []
        assert result.citation_count == 1

    def test_unverified_citation(self) -> None:
        evidence = _make_turn_evidence("source/networking.md")
        result = verify_citations("TCP is reliable [E9].", evidence)
        assert not result.all_verified
        assert result.verified == []
        assert result.unverified == ["E9"]

    def test_mixed_verified_unverified(self) -> None:
        evidence = _make_turn_evidence("source/networking.md", "source/transport.md")
        result = verify_citations("TCP is reliable [E1] but unsupported here [E9].", evidence)
        assert not result.all_verified
        assert result.verified == ["E1"]
        assert result.unverified == ["E9"]

    def test_no_citations(self) -> None:
        evidence = _make_turn_evidence("source/notes.md")
        result = verify_citations("The answer is 42.", evidence)
        assert result.all_verified
        assert result.citation_count == 0
        assert not result.has_citations
        assert result.evidence_present

    def test_no_turn_evidence(self) -> None:
        result = verify_citations("TCP is reliable [E1].", None)
        assert not result.all_verified
        assert not result.evidence_present
        assert result.unverified == ["E1"]

    def test_empty_reply(self) -> None:
        evidence = _make_turn_evidence("source/a.md")
        result = verify_citations("", evidence)
        assert result.all_verified
        assert result.citation_count == 0


# ---------------------------------------------------------------------------
# format_verification_notice
# ---------------------------------------------------------------------------


class TestFormatVerificationNotice:
    def test_no_notice_when_all_verified(self) -> None:
        result = VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        )
        assert format_verification_notice(result, 500) == ""

    def test_unverified_citation_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=["E9"],
            citation_count=1,
            has_citations=True,
            all_verified=False,
            evidence_present=True,
        )
        notice = format_verification_notice(result, 500)
        assert "E9" in notice
        assert "Unverified evidence citation" in notice

    def test_no_citations_long_answer_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            evidence_present=True,
        )
        notice = format_verification_notice(result, 500)
        assert "No evidence citations" in notice

    def test_no_citations_short_answer_no_notice(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            evidence_present=True,
        )
        assert format_verification_notice(result, 100) == ""

    def test_multiple_unverified_truncated(self) -> None:
        result = VerificationResult(
            verified=[],
            unverified=["E1", "E2", "E3", "E4", "E5", "E6"],
            citation_count=6,
            has_citations=True,
            all_verified=False,
            evidence_present=True,
        )
        notice = format_verification_notice(result, 500)
        assert "E1" in notice
        assert "E5" in notice


# ---------------------------------------------------------------------------


class TestVerifyResponse:
    def test_verified_response_no_notice(self) -> None:
        evidence = _make_turn_evidence("source/networking.md")
        notice = verify_response("TCP uses a 3-way handshake [E1].", evidence)
        assert notice == ""

    def test_hallucinated_citation_notice(self) -> None:
        evidence = _make_turn_evidence("source/networking.md")
        notice = verify_response("UDP is connectionless [E9].", evidence)
        assert "E9" in notice
        assert "Unverified" in notice

    def test_no_citations_long_answer_notice(self) -> None:
        evidence = _make_turn_evidence("source/networking.md")
        reply = (
            "TCP is a connection-oriented protocol that provides reliable, ordered, "
            "and error-checked delivery of a stream of bytes between applications. "
            "It establishes a connection via a three-way handshake using SYN, SYN-ACK, "
            "and ACK packets. This ensures both parties are ready to communicate before "
            "data transfer begins."
        )
        notice = verify_response(reply, evidence)
        assert "No evidence citations" in notice

    def test_no_turn_evidence_no_notice(self) -> None:
        notice = verify_response("Hello! How can I help?", None)
        assert notice == ""

    def test_never_raises(self) -> None:
        notice = verify_response("test", None)
        assert notice == ""
