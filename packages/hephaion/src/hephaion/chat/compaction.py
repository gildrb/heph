"""Conversation compaction workflows."""

from __future__ import annotations

import sys

from heph_ai.runtime import Conversation, Message, stream_reply

from hephaion.chat.session import ChatSession


def compact_session(session: ChatSession) -> None:
    summary = _stream_summary(session)
    session.conversation.messages = [*_system_messages(session), _summary_message(summary)]
    session.dirty = True


def _stream_summary(session: ChatSession) -> str:
    parts: list[str] = []
    for chunk in stream_reply(session.config, _summary_conversation(session.conversation)):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        parts.append(chunk)
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(parts)


def _summary_conversation(conversation: Conversation) -> Conversation:
    temp = Conversation()
    temp.add("system", "You are a helpful assistant that summarizes conversations.")
    temp.add("user", _summary_prompt(conversation))
    return temp


def _summary_prompt(conversation: Conversation) -> str:
    return (
        "Summarize the following conversation in a concise paragraph. "
        "Preserve key facts, decisions, and context needed to continue.\n\n"
        + "".join(
            f"{message.role}: {message.content}\n"
            for message in conversation.messages
            if message.role != "system"
        )
    )


def _system_messages(session: ChatSession) -> list[Message]:
    return [message for message in session.conversation.messages if message.role == "system"]


def _summary_message(summary: str) -> Message:
    return Message(role="system", content="[Conversation summary] " + summary)


__all__ = ["compact_session"]
