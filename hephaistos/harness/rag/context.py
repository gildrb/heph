"""Context assembly: build a system-context string from retrieved chunks.

Respects a token budget and produces source-attributed output suitable
for injection into the LLM conversation.
"""

from __future__ import annotations

from hephaistos.harness.rag.retrieve import ScoredChunk

_CHARS_PER_TOKEN = 4
_DEFAULT_MAX_TOKENS = 2000
_ATTRIBUTION_TEMPLATE = "--- {source} (chunk {index}, relevance: {score:.2f}) ---"


def build_context(
    scored_chunks: list[ScoredChunk],
    max_tokens: int = _DEFAULT_MAX_TOKENS,
) -> str:
    """Assemble scored chunks into a single context string with attribution.

    Chunks are included in relevance order until the budget is exhausted.
    Each chunk is prefixed with a source attribution header.
    """
    if not scored_chunks:
        return ""

    budget_chars = max_tokens * _CHARS_PER_TOKEN
    parts: list[str] = []
    used = 0

    for sc in scored_chunks:
        header = _ATTRIBUTION_TEMPLATE.format(
            source=sc.chunk.source,
            index=sc.chunk.index,
            score=sc.score,
        )
        entry = f"{header}\n{sc.chunk.text}"
        entry_len = len(entry) + 2  # +2 for newline separators

        if used + entry_len > budget_chars:
            remaining = budget_chars - used
            if remaining > len(header) + 20:
                truncated = sc.chunk.text[: remaining - len(header) - 10]
                entry = f"{header}\n{truncated}\n[... truncated]"
                parts.append(entry)
            break

        parts.append(entry)
        used += entry_len

    return "\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    """Rough token estimate for budget tracking."""
    return len(text) // _CHARS_PER_TOKEN
