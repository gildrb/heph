"""Evidence-citation verification for retrieval-grounded answers.

Post-generation verification checks whether the assistant cited retrieved
turn evidence using stable IDs like ``[E1]``. This makes grounding auditable:
verification operates on the exact evidence objects passed through the turn,
not on filenames scraped back out of an injected prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_logging import get_logger
from rag.context import TurnEvidence

_log = get_logger("agent.citation")

_EVIDENCE_CITATION_RE = re.compile(
    r"(?:\[|【)\s*((?:e|E)\s*\d+(?:\s*[,;]\s*(?:e|E)\s*\d+)*)\s*(?:\]|】)"
)
_EVIDENCE_ID_RE = re.compile(r"(?:e|E)\s*\d+")

# Responses shorter than this are considered conversational.
_NO_CITATION_CHAR_THRESHOLD = 200


@dataclass(frozen=True, slots=True)
class ExtractedCitation:
    evidence_id: str


@dataclass
class VerificationResult:
    verified: list[str]
    unverified: list[str]
    citation_count: int
    has_citations: bool
    all_verified: bool
    evidence_present: bool


def extract_citations(text: str) -> list[ExtractedCitation]:
    """Extract bracketed evidence citations from response text.

    Accepted format is strict by design: ``[E1]``, ``[E1, E2]``, or
    ``[E1; E2]``. Raw filenames are intentionally not treated as valid.
    """
    if not text:
        return []

    seen: set[str] = set()
    citations: list[ExtractedCitation] = []

    for match in _EVIDENCE_CITATION_RE.finditer(text):
        for evidence_match in _EVIDENCE_ID_RE.finditer(match.group(1)):
            evidence_id = "".join(evidence_match.group(0).split()).upper()
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            citations.append(ExtractedCitation(evidence_id=evidence_id))

    return citations


def verify_citations(
    reply: str,
    turn_evidence: TurnEvidence | None,
) -> VerificationResult:
    """Verify bracketed evidence citations against turn evidence."""
    citations = extract_citations(reply)
    has_evidence = bool(turn_evidence)

    if not citations:
        return VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            evidence_present=has_evidence,
        )

    if not has_evidence:
        return VerificationResult(
            verified=[],
            unverified=[c.evidence_id for c in citations],
            citation_count=len(citations),
            has_citations=True,
            all_verified=False,
            evidence_present=False,
        )

    assert turn_evidence is not None
    verified: list[str] = []
    unverified: list[str] = []

    for citation in citations:
        if turn_evidence.get(citation.evidence_id) is not None:
            verified.append(citation.evidence_id)
        else:
            unverified.append(citation.evidence_id)

    return VerificationResult(
        verified=verified,
        unverified=unverified,
        citation_count=len(citations),
        has_citations=True,
        all_verified=len(unverified) == 0,
        evidence_present=True,
    )


def format_verification_notice(result: VerificationResult, reply_len: int) -> str:
    """Build a human-readable notice string. Returns ``""`` when all is well."""
    if result.all_verified and result.has_citations:
        return ""

    parts: list[str] = []

    if result.unverified:
        listed = ", ".join(result.unverified[:5])
        parts.append(
            f"\nWarning: Unverified evidence citation(s): {listed}. "
            "These IDs were not found in the retrieved evidence."
        )
    if (
        not result.has_citations
        and result.evidence_present
        and reply_len > _NO_CITATION_CHAR_THRESHOLD
    ):
        parts.append(
            "\n⚠ No evidence citations found in this answer"
            " - verify claims against your materials."
        )

    return "".join(parts)


def verify_response(reply: str, turn_evidence: TurnEvidence | None) -> str:
    """Full verification pipeline. Returns a notice string or ``""``."""
    try:
        result = verify_citations(reply, turn_evidence)
        notice = format_verification_notice(result, len(reply))

        if notice:
            _log.info(
                "citation verification",
                extra={
                    "fields": {
                        "evidence_blocks": len(turn_evidence.items) if turn_evidence else 0,
                        "citations_found": result.citation_count,
                        "verified": len(result.verified),
                        "unverified": result.unverified,
                    }
                },
            )

        return notice

    except Exception:
        _log.warning("citation verification failed", exc_info=True)
        return ""
