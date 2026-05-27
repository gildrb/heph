"""Title derivation helpers for chat sessions."""

from __future__ import annotations

from hephaion.runtime import Conversation


def derive_title(conversation: Conversation) -> str:
    first_user_content = _first_user_content(conversation)
    if not first_user_content:
        return ""
    prefix = first_user_content[:60]
    count = _matching_user_message_count(conversation, first_user_content[:20])
    if count > 1:
        return f"{prefix} ({count})"
    return prefix


def _first_user_content(conversation: Conversation) -> str:
    for message in conversation.messages:
        if message.role == "user":
            return message.content
    return ""


def _matching_user_message_count(conversation: Conversation, prefix: str) -> int:
    return sum(
        1
        for message in conversation.messages
        if message.role == "user" and message.content.startswith(prefix)
    )
