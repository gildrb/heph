"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

import contextlib
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.events import render_turn_event
from hephaistos.chat.orchestrator import TurnOrchestrator
from hephaistos.chat.usage import SessionUsage
from hephaistos.harness.prompt import build_system_prompt
from hephaistos.harness.rag import ArmoryIndex
from hephaistos.logging import TraceWriter, get_logger
from hephaistos.memory import MemoryStore, load_memory
from hephaistos.study import StudyState

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
    trace: TraceWriter = field(default=None, init=False, repr=False)  # type: ignore[assignment]
    steering: object = field(
        default=None, init=False, repr=False
    )  # SteeringQueue, typed as object to avoid circular import
    study_state: StudyState = field(default_factory=StudyState)

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(self, "trace", TraceWriter(self.session_id, self.armory_path))
        if self.steering is None:
            from hephaistos.harness.dispatch import SteeringQueue

            object.__setattr__(self, "steering", SteeringQueue())


class SessionError(Exception):
    """Raised when a session cannot be created or used."""


_SYSTEM_PROMPT_FALLBACK = (
    "Hephaistos. A drill instructor for exam preparation.\n"
    "Ask the student to attach an armory with source documents first.\n"
    "Be concise. Never fabricate information."
)


def validate_armory_path(path_str: str) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path



def _count_source_files(armory_path: Path) -> int:
    """Count source files in armory."""
    count = 0
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                count += 1
    return count



def _list_source_file_names(armory_path: Path) -> list[str]:
    """Return relative paths of source files for the system prompt."""
    names: list[str] = []
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        names.extend(
            str(file_path.relative_to(armory_path))
            for file_path in sorted(folder.rglob("*"))
            if file_path.is_file() and not file_path.name.startswith(".")
        )
    return names



def create_plain_session(config: ChatConfig) -> ChatSession:
    """Create a fresh chat session without an attached armory."""
    conversation = Conversation()
    conversation.add("system", _SYSTEM_PROMPT_FALLBACK)
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
    )
    _log.info(
        "plain session created",
        extra={"fields": {"session_id": session.session_id, "model": config.model}},
    )
    session.trace.record_session_event("created", model=config.model, mode="plain")
    return session



def create_session(config: ChatConfig, armory_path: Path) -> ChatSession:
    """Create a fresh chat session scoped to an armory."""
    if armory_path is None:
        raise SessionError("An armory is required. Create one with: hephaistos armory init <path>")

    source_file_count = _count_source_files(armory_path)
    if source_file_count == 0:
        raise SessionError(
            f"Armory has no source documents. Add past exams to {armory_path}/source/ "
            "or reference material to library/."
        )

    conversation = Conversation()
    source_files = _list_source_file_names(armory_path)
    memory_ctx = ""
    with contextlib.suppress(Exception):
        memory_ctx = load_memory(armory_path).build_system_context()
    conversation.add(
        "system",
        build_system_prompt(
            armory_path=armory_path,
            source_files=source_files,
            memory_context=memory_ctx,
        ),
    )

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=source_file_count,
    )
    session._memory = load_memory(armory_path)
    _log.info(
        "session created",
        extra={
            "fields": {
                "session_id": session.session_id,
                "armory": str(armory_path),
                "source_files": source_file_count,
                "model": config.model,
                "memory_entries": len(session._memory.entries) if session._memory else 0,
            }
        },
    )
    session.trace.record_session_event("created", model=config.model)
    return session



def resume_session(config: ChatConfig, armory_path: Path, session_id: str) -> ChatSession:
    """Load a saved session from an armory."""
    conversation, title = chat_storage.load(armory_path, session_id)
    metadata = chat_storage.load_metadata(armory_path, session_id)
    source_file_count = _count_source_files(armory_path)
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=source_file_count,
        study_state=StudyState.from_dict(metadata.get("study_state")),
    )
    session._memory = load_memory(armory_path)
    _log.info(
        "session resumed",
        extra={
            "fields": {
                "session_id": session_id,
                "armory": str(armory_path),
                "message_count": len(conversation.messages),
                "memory_entries": len(session._memory.entries) if session._memory else 0,
            }
        },
    )
    session.trace.record_session_event("resumed", title=title)
    return session



def session_has_messages(session: ChatSession) -> bool:
    """Return ``True`` when the session contains non-system messages."""
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
    """Run one user turn via the orchestrator and mirror events to stdout."""
    orchestrator = TurnOrchestrator(session)
    for event in orchestrator.iter_events(user_input, abort=abort):
        rendered = render_turn_event(event)
        if not rendered:
            continue
        sys.stdout.write(rendered)
        sys.stdout.flush()

    if orchestrator.last_reply:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return orchestrator.last_reply



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
        metadata={"study_state": session.study_state.to_dict()},
    )
    session.dirty = False
    _log.info(
        "session saved",
        extra={
            "fields": {
                "session_id": session.session_id,
                "path": str(path),
                "message_count": len(session.conversation.messages),
            }
        },
    )
    session.trace.record_session_event("saved", path=str(path))
    return path



def list_armory_sessions(armory_path: Path) -> list[dict[str, str]]:
    """Return saved sessions for the given armory."""
    return chat_storage.list_sessions(armory_path)
