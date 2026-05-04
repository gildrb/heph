"""Adapter helpers for displaying attached study materials in the TUI."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.matching import ranked_matches


def material_listing(session: ChatSession, query: str = "") -> str:
    """Return a compact material listing for the active chat session."""
    files = list(session.source_files)
    if not files:
        return "No material files are attached."
    if query.strip():
        matches = ranked_matches(query, files, key=lambda value: value, limit=12, min_score=35.0)
        files = [match.value for match in matches]
        if not files:
            return f"No materials match: {query}"
    visible = files[:16]
    body = "\n".join(f"@{name}" for name in visible)
    if len(files) > len(visible):
        body += f"\n... {len(files) - len(visible)} more"
    return body
