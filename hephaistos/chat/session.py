"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation, Message, get_reply
from hephaistos.harness.dispatch import agent_loop
from hephaistos.harness.rag import ArmoryIndex, build_context, load_or_build, retrieve


@dataclass
class ChatSession:
    config: ChatConfig
    conversation: Conversation
    session_id: str
    title: str = ""
    armory_path: Path | None = None
    source_file_count: int = 0
    dirty: bool = False
    autonomy: str = "low"
    _rag_index: ArmoryIndex | None = field(default=None, init=False, repr=False)


def validate_armory_path(path_str: str) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path


def _count_source_files(armory_path: Path) -> int:
    """Count source files in armory (for display only; no stuffing)."""
    count = 0
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file():
                count += 1
    return count


_SYSTEM_PROMPT = (
    "You are a helpful coding assistant with access to tools. "
    "When asked about files or code, use list_files and read_file "
    "to explore the workspace rather than guessing. "
    "Use bash to run commands when needed. "
    "Be concise and accurate."
)

_SYSTEM_PROMPT_RAG = (
    "You are a knowledgeable study assistant. "
    "Relevant excerpts from the armory's source material are provided below "
    "as context for each question. Use this context as your primary reference. "
    "When you draw from a source, cite it by filename. "
    "If the provided context is insufficient, you may use read_file and "
    "list_files to explore the armory workspace for more detail. "
    "Use bash to run commands when needed. "
    "Be concise, accurate, and attribute your answers to sources."
)

_RAG_CONTEXT_PREFIX = (
    "The following excerpts were automatically retrieved from the armory "
    "based on the user's question:\n\n"
)


def create_session(config: ChatConfig, armory_path: Path | None = None) -> ChatSession:
    """Create a fresh chat session, optionally scoped to an armory."""
    conversation = Conversation()
    source_file_count = 0

    if armory_path is not None:
        source_file_count = _count_source_files(armory_path)
        conversation.add("system", _SYSTEM_PROMPT_RAG)
    else:
        conversation.add("system", _SYSTEM_PROMPT)

    return ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=source_file_count,
    )


def resume_session(
    config: ChatConfig,
    armory_path: Path,
    session_id: str,
) -> ChatSession:
    """Load a saved session from an armory."""
    conversation, title = chat_storage.load(armory_path, session_id)
    source_file_count = _count_source_files(armory_path)
    return ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=source_file_count,
    )


def session_has_messages(session: ChatSession) -> bool:
    """Return ``True`` when the session contains user or assistant messages."""
    return any(message.role != "system" for message in session.conversation.messages)


def _derive_title(conversation: Conversation) -> str:
    first_user_content = ""
    for message in conversation.messages:
        if message.role == "user":
            first_user_content = message.content
            break
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


def send_user_message(
    session: ChatSession,
    user_input: str,
    *,
    abort: threading.Event | None = None,
) -> str:
    """Append a user message, run the agent loop, stream output, return reply."""
    length_before = len(session.conversation.messages)
    session.conversation.add("user", user_input)

    # RAG context injection: retrieve and stuff before the user message
    if session.armory_path is not None:
        _inject_rag_context(session, user_input)

    try:
        if session.armory_path is not None:
            # Agent loop with tools — workspace is the armory
            parts: list[str] = []
            for chunk in agent_loop(
                session.config,
                session.conversation,
                session.armory_path,
                abort=abort,
            ):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                parts.append(chunk)
            sys.stdout.write("\n")
            sys.stdout.flush()
            reply = "".join(parts)
        else:
            # Fallback: plain streaming without tools
            reply = get_reply(session.config, session.conversation, abort=abort)
    except Exception:
        del session.conversation.messages[length_before:]
        raise

    # The agent_loop already adds the assistant message to conversation,
    # but for the plain get_reply path we need to add it here.
    if session.conversation.messages and session.conversation.messages[-1].role != "assistant":
        session.conversation.add("assistant", reply)

    if not session.title:
        session.title = _derive_title(session.conversation)
    session.dirty = True
    return reply


def _inject_rag_context(session: ChatSession, user_input: str) -> int:
    """Build/load the RAG index, retrieve relevant chunks, and inject context.

    Inserts a system message with retrieved context just before the last
    user message. Returns the number of messages inserted (0 or 1).
    """
    try:
        if session._rag_index is None:
            session._rag_index = load_or_build(session.armory_path)  # type: ignore[arg-type]

        scored = retrieve(user_input, session._rag_index, top_k=5)
        if not scored:
            return 0

        context_text = build_context(scored, max_tokens=2000)
        if not context_text:
            return 0

        full_context = _RAG_CONTEXT_PREFIX + context_text

        # Insert just before the last message (which is the user message)
        last_idx = len(session.conversation.messages) - 1
        session.conversation.messages.insert(
            last_idx,
            Message(role="system", content=full_context),
        )
        return 1
    except Exception:
        # RAG failure should never block the conversation
        return 0


def save_session(session: ChatSession) -> Path:
    """Persist the session to the active armory."""
    if session.armory_path is None:
        raise chat_storage.ChatStorageError(
            "cannot save chat without an active armory; use /armory first"
        )
    title = session.title or _derive_title(session.conversation)
    path = chat_storage.save(
        session.armory_path,
        session.session_id,
        session.conversation,
        title=title,
    )
    session.dirty = False
    return path


def list_armory_sessions(armory_path: Path) -> list[dict[str, str]]:
    """Return saved sessions for the given armory."""
    return chat_storage.list_sessions(armory_path)
