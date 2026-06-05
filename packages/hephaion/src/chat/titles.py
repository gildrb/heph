"""Title derivation helpers for chat sessions."""

from __future__ import annotations

import re

from ai.runtime import Conversation

_TITLE_MAX_CHARS = 60
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0e-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_title_text(text: str, *, max_chars: int = _TITLE_MAX_CHARS) -> str:
    if max_chars <= 0:
        return ""
    without_ansi = _ANSI_ESCAPE_RE.sub("", text)
    without_controls = _CONTROL_RE.sub("", without_ansi)
    visible_tokens = _WHITESPACE_RE.sub(" ", without_controls).strip()
    return visible_tokens[:max_chars].rstrip()


def derive_title(conversation: Conversation) -> str:
    first_user_title = sanitize_title_text(_first_user_content(conversation))
    if not first_user_title:
        return ""
    prefix = first_user_title[:_TITLE_MAX_CHARS]
    count = _matching_user_message_count(conversation, first_user_title[:20])
    if count > 1:
        suffix = f" ({count})"
        counted_prefix = prefix[: _TITLE_MAX_CHARS - len(suffix)].rstrip()
        return f"{counted_prefix}{suffix}"
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
        if message.role == "user" and sanitize_title_text(message.content).startswith(prefix)
    )
