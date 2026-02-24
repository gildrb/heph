"""Chat feature use-cases."""

from __future__ import annotations

from hephaistos.chat.session_store import ensure_chat_storage
from hephaistos.chat.types import ChatSessionRef


def create_chat(title: str | None = None) -> str:
    """Placeholder chat create flow."""
    ensure_chat_storage()
    session = ChatSessionRef(chat_id="new", title=title or "(untitled)")
    return f"[todo] chat new title={session.title}"


def resume_chat(chat_id: str) -> str:
    """Placeholder chat resume flow."""
    ensure_chat_storage()
    session = ChatSessionRef(chat_id=chat_id)
    return f"[todo] chat resume id={session.chat_id}"

