"""Conversation context helpers for chat turn services."""

from __future__ import annotations

from ai.runtime.conversation import Conversation, Message

from hephaion.chat.citation_patterns import (
    _OVERVIEW_CITATION_ID_RE,
)
from hephaion.rag.context import TurnEvidence


def _last_assistant_message(
    conversation: Conversation | None,
    user_input: str,
) -> Message | None:
    recent = _recent_assistant_messages(conversation, user_input, limit=1)
    return recent[-1] if recent else None


def _last_cited_assistant_message(
    conversation: Conversation | None,
    user_input: str,
) -> Message | None:
    for message in reversed(_recent_assistant_messages(conversation, user_input, limit=6)):
        if _OVERVIEW_CITATION_ID_RE.search(message.content):
            return message
    return _last_assistant_message(conversation, user_input)


def _recent_assistant_messages(
    conversation: Conversation | None,
    user_input: str,
    *,
    limit: int,
) -> tuple[Message, ...]:
    if conversation is None:
        return ()
    messages = [
        message
        for message in conversation.messages
        if message.role in {"user", "assistant"} and message.content.strip()
    ]
    if messages and _same_message_text(messages[-1].content, user_input):
        messages = messages[:-1]
    assistant_messages = [message for message in messages if message.role == "assistant"]
    if limit <= 0:
        return ()
    return tuple(assistant_messages[-limit:])


def _recent_current_evidence_citation_ids(
    conversation: Conversation | None,
    user_input: str,
    evidence: TurnEvidence,
    *,
    limit: int = 4,
) -> frozenset[str]:
    current_ids = {item.evidence_id.casefold() for item in evidence.items}
    cited_ids: set[str] = set()
    for message in _recent_assistant_messages(conversation, user_input, limit=limit):
        for match in _OVERVIEW_CITATION_ID_RE.finditer(message.content):
            evidence_id = f"E{match.group('id')}".casefold()
            if evidence_id in current_ids:
                cited_ids.add(evidence_id)
    return frozenset(cited_ids)


def _same_message_text(left: str, right: str) -> bool:
    return " ".join(left.split()) == " ".join(right.split())
