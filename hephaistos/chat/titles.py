"""Title derivation helpers for chat sessions."""

from __future__ import annotations

from hephaistos.runtime import Conversation


def derive_title(conversation: Conversation) -> str:
    first_user_content = next(
        (message.content for message in conversation.messages if message.role == "user"),
        "",
    )
    if not first_user_content:
        return ""
    prefix = first_user_content[:60]
    count = sum(
        1
        for msg in conversation.messages
        if msg.role == "user" and msg.content.startswith(first_user_content[:20])
    )
    if count > 1:
        return f"{prefix} ({count})"
    return prefix
