"""Conversation compaction workflows."""

from __future__ import annotations

import sys

from hephaistos.chat.session import ChatSession
from hephaistos.runtime import Conversation, Message, stream_reply


def compact_session(session: ChatSession) -> None:
    non_system = [m for m in session.conversation.messages if m.role != "system"]
    summary_prompt = (
        "Summarize the following conversation in a concise paragraph. "
        "Preserve key facts, decisions, and context needed to continue.\n\n"
        + "".join(f"{msg.role}: {msg.content}\n" for msg in non_system)
    )

    temp = Conversation()
    temp.add("system", "You are a helpful assistant that summarizes conversations.")
    temp.add("user", summary_prompt)

    parts: list[str] = []
    for chunk in stream_reply(session.config, temp):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        parts.append(chunk)
    summary = "".join(parts)
    sys.stdout.write("\n")
    sys.stdout.flush()

    system_msgs = [m for m in session.conversation.messages if m.role == "system"]
    session.conversation.messages = [
        *system_msgs,
        Message(
            role="system",
            content="[Conversation summary] " + summary,
        ),
    ]
    session.dirty = True


__all__ = ["compact_session"]
