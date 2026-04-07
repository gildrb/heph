"""Citation verification: detect and validate source citations in LLM responses.

Post-generation verification loop that checks every source citation in the
LLM's response against the documents that were *actually retrieved* in the
RAG context.  Catches fabricated source attributions before the user accepts
them as fact.

Pipeline:

1. **Resolve** retrieved sources from the RAG context messages injected by
   :func:`~hephaistos.chat.session._inject_rag_context`.
2. **Extract** citations from the response text using regex patterns that
   match common citation formats (``source: file.md``, parenthetical
   references, ``according to`` constructions, em-dash attributions).
3. **Verify** each citation against the resolved source set (fuzzy basename
   matching so ``file.md`` matches ``source/file.md``).
4. **Flag** unverified citations and substantive answers with zero citations.

The verification runs after the agent loop completes.  It is display-only —
a notice is written to stdout but the conversation history is not modified.
Failures are caught and logged so they never block a response.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from hephaistos.chat.engine import Message
from hephaistos.logging import get_logger

_log = get_logger("harness.citation")

# ---------------------------------------------------------------------------
# RAG context parsing
# ---------------------------------------------------------------------------

_RAG_PREFIX = "Source material retrieved for this question:"

# Matches the attribution headers produced by context.build_context():
#   --- source/file.md (chunk 0, relevance: 0.85) ---
_ATTRIB_RE = re.compile(r"^---\s+(\S+)\s+\(chunk\s+\d+")


def _get_rag_sources(messages: list[Message]) -> set[str]:
    """Extract source paths from RAG context system messages.

    Returns the set of unique source paths (e.g.
    ``{"source/notes.md", "library/glossary.txt"}``).
    """
    sources: set[str] = set()
    for msg in messages:
        if msg.role != "system":
            continue
        if not msg.content.startswith(_RAG_PREFIX):
            continue
        for line in msg.content.splitlines():
            m = _ATTRIB_RE.match(line.strip())
            if m:
                sources.add(m.group(1))
    return sources


# ---------------------------------------------------------------------------
# Source matching helpers
# ---------------------------------------------------------------------------

_DOC_EXTENSIONS = frozenset({
    ".md", ".txt", ".py", ".pdf", ".rst", ".json", ".yaml", ".yml",
    ".toml", ".csv", ".html", ".tex", ".adoc", ".org",
    ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp",
})


def _normalize(source: str) -> str:
    """Lowercase, strip whitespace for comparison."""
    return source.strip().lower()


def _build_source_lookup(sources: set[str]) -> dict[str, str]:
    """Map normalized keys (full path + basename) → original source path."""
    lookup: dict[str, str] = {}
    for src in sources:
        lookup[_normalize(src)] = src
        basename = PurePosixPath(src).name.lower()
        if basename not in lookup:
            lookup[basename] = src
    return lookup


def _looks_like_source(text: str) -> bool:
    """Quick heuristic: does *text* look like a document path?"""
    lower = text.lower()
    return any(lower.endswith(ext) for ext in _DOC_EXTENSIONS) or "/" in text


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------

# Multiple regex patterns to catch common citation formats.
_CITATION_PATTERNS: list[re.Pattern[str]] = [
    # Explicit "source: file.md" / "Source — file.md"
    re.compile(
        r"(?:source|Source|SOURCE)\s*[:\-—]\s*"
        r"([^\s,\)\]\}]+(?:\.[a-zA-Z0-9]+)?)",
    ),
    # Parenthetical: (file.md) or (source/file.md)
    re.compile(
        r"\(\s*([a-zA-Z][^\s\)]*?"
        r"(?:\.(?:md|txt|py|pdf|rst|json|yaml|yml|toml|csv|html|tex))"
        r")\s*\)",
    ),
    # "according to file.md" / "from file.md" / "in file.md" / "see file.md"
    re.compile(
        r"(?:according\s+to|from|in|see|ref(?:erence)?|document|file)\s+"
        r"([a-zA-Z][^\s,.;:!?\)\]]*?"
        r"(?:\.(?:md|txt|py|pdf|rst|json|yaml|yml|toml|csv|html|tex))"
        r")",
        re.IGNORECASE,
    ),
    # Em-dash attribution: "— file.md" or "– file.md"
    re.compile(
        r"[—–]\s*([a-zA-Z][^\s,.;:!?]*?"
        r"(?:\.(?:md|txt|py|pdf|rst|json|yaml|yml|toml|csv|html|tex))"
        r")",
    ),
]


@dataclass(frozen=True, slots=True)
class ExtractedCitation:
    """A source citation found in LLM response text."""

    raw: str       # matched filename / path
    position: int  # character offset in the response


def extract_citations(text: str) -> list[ExtractedCitation]:
    """Extract source citations from LLM response text.

    Deduplicates by normalised form; returns citations in order of first
    appearance.
    """
    if not text:
        return []

    seen: set[str] = set()
    citations: list[ExtractedCitation] = []

    for pattern in _CITATION_PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            if not _looks_like_source(raw):
                continue
            key = _normalize(raw)
            if key in seen:
                continue
            seen.add(key)
            citations.append(ExtractedCitation(
                raw=raw,
                position=m.start(1),
            ))

    return citations


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

# Responses shorter than this are considered conversational (hints,
# assessments) and won't trigger the "no citations" warning.
_NO_CITATION_CHAR_THRESHOLD = 200


@dataclass
class VerificationResult:
    """Outcome of citation verification."""

    verified: list[str]       # citations matching retrieved sources
    unverified: list[str]     # citations NOT in retrieved sources
    citation_count: int
    has_citations: bool
    all_verified: bool
    rag_context_present: bool  # was RAG context injected at all?

    @property
    def has_unverified(self) -> bool:
        return len(self.unverified) > 0


def verify_citations(
    reply: str,
    retrieved_sources: set[str],
) -> VerificationResult:
    """Verify citations in *reply* against *retrieved_sources*.

    If no RAG context was provided (empty set), citations cannot be
    verified and are all marked unverified.
    """
    citations = extract_citations(reply)
    has_rag = len(retrieved_sources) > 0

    if not citations:
        return VerificationResult(
            verified=[],
            unverified=[],
            citation_count=0,
            has_citations=False,
            all_verified=True,
            rag_context_present=has_rag,
        )

    if not has_rag:
        # No RAG context — every citation is suspect
        return VerificationResult(
            verified=[],
            unverified=[c.raw for c in citations],
            citation_count=len(citations),
            has_citations=True,
            all_verified=False,
            rag_context_present=False,
        )

    lookup = _build_source_lookup(retrieved_sources)
    verified: list[str] = []
    unverified: list[str] = []

    for cit in citations:
        if _normalize(cit.raw) in lookup:
            verified.append(cit.raw)
        else:
            unverified.append(cit.raw)

    return VerificationResult(
        verified=verified,
        unverified=unverified,
        citation_count=len(citations),
        has_citations=True,
        all_verified=len(unverified) == 0,
        rag_context_present=True,
    )


def format_verification_notice(result: VerificationResult, reply_len: int) -> str:
    """Build a human-readable notice string.  Returns ``""`` when all is well."""
    if result.all_verified and result.has_citations:
        return ""

    parts: list[str] = []

    if result.unverified:
        listed = ", ".join(result.unverified[:5])
        parts.append(
            f"\n⚠ Unverified citation(s): {listed}. "
            "These sources were not found in the retrieved context."
        )

    # Substantive answer with RAG context but zero citations
    if (
        not result.has_citations
        and result.rag_context_present
        and reply_len > _NO_CITATION_CHAR_THRESHOLD
    ):
        parts.append(
            "\n⚠ No source citations found in this answer "
            "— verify claims against your materials."
        )

    return "".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def verify_response(reply: str, messages: list[Message]) -> str:
    """Full verification pipeline.  Returns a notice string or ``""``.

    This is the main entry point called from the session layer.  It never
    raises — failures are logged and silently ignored so the user always
    gets their response.
    """
    try:
        sources = _get_rag_sources(messages)
        result = verify_citations(reply, sources)
        notice = format_verification_notice(result, len(reply))

        if notice:
            _log.info("citation verification", extra={"fields": {
                "sources_retrieved": len(sources),
                "citations_found": result.citation_count,
                "verified": len(result.verified),
                "unverified": result.unverified,
            }})

        return notice

    except Exception:
        _log.warning("citation verification failed", exc_info=True)
        return ""
