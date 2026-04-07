"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

import contextlib
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    Message,
    StreamRecoveryError, get_reply,
)
from hephaistos.chat.usage import SessionUsage, save_usage
from hephaistos.harness.dispatch import agent_loop
from hephaistos.harness.prompt import build_system_prompt
from hephaistos.harness.rag import ArmoryIndex, build_context, load_or_build, retrieve
from hephaistos.logging import Timer, TraceWriter, get_logger
from hephaistos.memory import MemoryStore, load_memory

_log = get_logger("chat.session")


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
    _memory: MemoryStore | None = field(default=None, init=False, repr=False)
    usage: SessionUsage = field(default_factory=SessionUsage)
    trace: TraceWriter = field(default=None, init=False, repr=False)
    steering: object = field(default=None, init=False, repr=False)  # SteeringQueue, typed as object to avoid circular import

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(
                self, "trace", TraceWriter(self.session_id, self.armory_path)
            )
        if self.steering is None:
            from hephaistos.harness.dispatch import SteeringQueue
            object.__setattr__(self, "steering", SteeringQueue())


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


def _list_source_file_names(armory_path: Path) -> list[str]:
    """Return relative paths of source files for the system prompt."""
    names: list[str] = []
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file():
                rel = file_path.relative_to(armory_path)
                names.append(str(rel))
    return names


_RAG_CONTEXT_PREFIX = (
    "Source material retrieved for this question:\n\n"
)


_SYSTEM_PROMPT_FALLBACK = (
    "Hephaistos. A drill instructor for exam preparation.\n"
    "Ask the student to attach an armory with source documents first.\n"
    "Be concise. Cite sources for every answer. Never fabricate information."
)


class SessionError(Exception):
    """Raised when a session cannot be created or used."""


def create_plain_session(config: ChatConfig) -> ChatSession:
    """Create a fresh chat session without an attached armory."""
    conversation = Conversation()
    conversation.add("system", _SYSTEM_PROMPT_FALLBACK)

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
    )
    _log.info("plain session created", extra={"fields": {
        "session_id": session.session_id,
        "model": config.model,
    }})
    session.trace.record_session_event("created", model=config.model, mode="plain")
    return session


def create_session(config: ChatConfig, armory_path: Path) -> ChatSession:
    """Create a fresh chat session scoped to an armory.

    Raises SessionError if armory_path is None or has no source documents.
    """
    if armory_path is None:
        raise SessionError(
            "An armory is required. Create one with: hephaistos armory init <path>"
        )

    source_file_count = _count_source_files(armory_path)
    if source_file_count == 0:
        raise SessionError(
            f"Armory has no source documents. Add past exams to {armory_path}/source/ "
            "or reference material to library/."
        )

    conversation = Conversation()

    # List source files for the prompt builder
    source_files = _list_source_file_names(armory_path)

    # Build memory context
    memory_ctx = ""
    try:
        mem = load_memory(armory_path)
        memory_ctx = mem.build_system_context()
    except Exception:
        pass

    # Build the rich system prompt with tool docs, anti-hallucination directives,
    # source file list, date, and memory context
    system_prompt = build_system_prompt(
        armory_path=armory_path,
        source_files=source_files,
        memory_context=memory_ctx,
    )

    conversation.add("system", system_prompt)

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=source_file_count,
    )
    # Load memory for this session
    session._memory = load_memory(armory_path)
    _log.info("session created", extra={"fields": {
        "session_id": session.session_id,
        "armory": str(armory_path),
        "source_files": source_file_count,
        "model": config.model,
        "memory_entries": len(session._memory.entries) if session._memory else 0,
    }})
    session.trace.record_session_event("created", model=config.model)
    return session


def resume_session(
    config: ChatConfig,
    armory_path: Path,
    session_id: str,
) -> ChatSession:
    """Load a saved session from an armory."""
    conversation, title = chat_storage.load(armory_path, session_id)
    source_file_count = _count_source_files(armory_path)
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=source_file_count,
    )
    session._memory = load_memory(armory_path)
    _log.info("session resumed", extra={"fields": {
        "session_id": session_id,
        "armory": str(armory_path),
        "message_count": len(conversation.messages),
        "memory_entries": len(session._memory.entries) if session._memory else 0,
    }})
    session.trace.record_session_event("resumed", title=title)
    return session


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
    # Snapshot original messages so rollback is always correct,
    # even if auto_compact rebuilt the message list mid-loop.
    original_messages = list(session.conversation.messages)
    session.conversation.add("user", user_input)
    session.trace.record_user_message(user_input)

    _log.info("user message", extra={"fields": {
        "session_id": session.session_id,
        "input_len": len(user_input),
        "message_count": len(session.conversation.messages),
    }})

    timer = Timer()
    reply = ""
    try:
        if session.armory_path is not None:
            _inject_rag_context(session, user_input)

            # Agent loop with tools — workspace is the armory
            parts: list[str] = []
            for chunk in agent_loop(
                session.config,
                session.conversation,
                session.armory_path,
                abort=abort,
                usage=session.usage,
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
    except StreamRecoveryError as rec:
        # Partial content was streamed before the connection dropped.
        # Roll back the conversation to keep it consistent, but preserve
        # the partial reply in the exception for the caller to inspect.
        _log.warning("stream interrupted, rolling back", extra={"fields": {
            "session_id": session.session_id,
            "partial_len": len(rec.partial_content),
            "latency_ms": timer.ms,
        }})
        session.conversation.messages = original_messages
        session.dirty = True
        raise
    except Exception:
        _log.error("send_user_message failed", extra={"fields": {
            "session_id": session.session_id,
            "latency_ms": timer.ms,
        }}, exc_info=True)
        session.conversation.messages = original_messages
        raise

    # Citation verification: flag fabricated source references
    if session.armory_path is not None and reply:
        try:
            from hephaistos.harness.citation import verify_response
            notice = verify_response(reply, session.conversation.messages)
            if notice:
                sys.stdout.write(notice)
                sys.stdout.flush()
        except Exception:
            _log.warning("citation verification failed", exc_info=True)

    # Add assistant reply to conversation if the agent loop didn't already.
    if session.conversation.messages and session.conversation.messages[-1].role != "assistant":
        session.conversation.add("assistant", reply)

    if not session.title:
        session.title = _derive_title(session.conversation)
    session.dirty = True

    _log.info("reply complete", extra={"fields": {
        "session_id": session.session_id,
        "reply_len": len(reply),
        "latency_ms": timer.ms,
    }})
    session.trace.record_session_event(
        "reply", latency_ms=round(timer.ms, 1), reply_len=len(reply)
    )

    # Extract and store memory from this exchange
    if session._memory is not None and len(reply) >= 100:
        try:
            from hephaistos.memory.extract import extract_and_store
            sources_used = ""
            # Find RAG context that was injected to identify sources
            for msg in session.conversation.messages:
                if msg.role == "system" and msg.content.startswith(_RAG_CONTEXT_PREFIX):
                    sources_used = msg.content[:200]
                    break
            added = extract_and_store(
                session.config,
                session._memory,
                user_input,
                reply,
                sources=sources_used,
            )
            if added:
                _log.info("memory updated", extra={"fields": {
                    "new_entries": added,
                }})
        except Exception:
            _log.warning("memory extraction failed", exc_info=True)

    # Persist usage
    if session.armory_path is not None:
        with contextlib.suppress(Exception):
            save_usage(session.armory_path, session.session_id, session.usage)

    return reply


def _inject_rag_context(session: ChatSession, user_input: str) -> int:
    """Build/load the RAG index, retrieve relevant chunks, and inject context.

    Inserts a system message with retrieved context just before the last
    user message. Returns the number of messages inserted (0 or 1).
    """
    if session.armory_path is None:
        return 0
    try:
        timer = Timer()
        if session._rag_index is None:
            session._rag_index = load_or_build(session.armory_path)

        with timer:
            scored = retrieve(user_input, session._rag_index, top_k=5)
        if not scored:
            _log.info("rag retrieve: no results", extra={"fields": {
                "query_len": len(user_input),
                "latency_ms": timer.ms,
            }})
            return 0

        scores = [sc.score for sc in scored]
        _log.info("rag retrieve", extra={"fields": {
            "query_len": len(user_input),
            "retrieved": len(scored),
            "top_score": round(scores[0], 4) if scores else 0,
            "latency_ms": round(timer.ms, 1),
        }})
        session.trace.record_rag_retrieve(
            query=user_input,
            top_k=5,
            retrieved=len(scored),
            scores=scores,
            latency_ms=timer.ms,
        )

        context_text = build_context(
            scored, max_tokens=session.config.rag_context_budget
        )
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
        _log.warning("rag context injection failed", exc_info=True)
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
    _log.info("session saved", extra={"fields": {
        "session_id": session.session_id,
        "path": str(path),
        "message_count": len(session.conversation.messages),
    }})
    session.trace.record_session_event("saved", path=str(path))
    return path


def list_armory_sessions(armory_path: Path) -> list[dict[str, str]]:
    """Return saved sessions for the given armory."""
    return chat_storage.list_sessions(armory_path)
