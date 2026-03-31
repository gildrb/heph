"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation, EngineError, get_reply, stream_reply


@dataclass
class ChatSession:
    config: ChatConfig
    conversation: Conversation
    session_id: str
    title: str = ""
    armory_path: Path | None = None
    source_file_count: int = 0
    dirty: bool = False


def validate_armory_path(path_str: str) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path


def _read_source_context(armory_path: Path) -> tuple[str, int]:
    context_parts: list[str] = []
    file_count = 0

    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file():
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = file_path.relative_to(armory_path)
            context_parts.append(f"--- {rel} ---\n{text}")
            file_count += 1

    return "\n\n".join(context_parts), file_count


def _build_system_prompt(source_context: str) -> str:
    base = "You are a helpful assistant."
    if not source_context:
        return base
    return (
        f"{base}\n\n"
        "The user has provided the following reference files. "
        "Use them to inform your responses:\n\n"
        f"{source_context}"
    )


def create_session(config: ChatConfig, armory_path: Path | None = None) -> ChatSession:
    """Create a fresh chat session, optionally scoped to an armory."""
    conversation = Conversation()
    source_context = ""
    source_file_count = 0

    if armory_path is not None:
        source_context, source_file_count = _read_source_context(armory_path)

    conversation.add("system", _build_system_prompt(source_context))
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
    _, source_file_count = _read_source_context(armory_path)
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
    # Use first 60 chars; if the user sends near-identical starts,
    # append a counter suffix so titles stay distinct
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
    stream: bool = False,
) -> str:
    """Append a user message, stream the reply, and store the assistant output.

    When stream=True, each reply chunk is passed to on_chunk(chunk) callback
    instead of being accumulated silently.
    """
    session.conversation.add("user", user_input)

    try:
        if stream:
            reply = _stream_and_print(session)
        else:
            reply = get_reply(session.config, session.conversation)
    except EngineError:
        session.conversation.messages.pop()
        raise

    session.conversation.add("assistant", reply)
    if not session.title:
        session.title = _derive_title(session.conversation)
    session.dirty = True
    return reply


def _stream_and_print(session: ChatSession) -> str:
    """Stream the LLM reply and print each chunk to stdout."""
    parts: list[str] = []
    for chunk in stream_reply(session.config, session.conversation):
        print(chunk, end="", flush=True)
        parts.append(chunk)
    print()
    return "".join(parts)


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
