"""Types for chat feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatSessionRef:
    """Minimal chat session identity."""

    chat_id: str
    title: str | None = None

