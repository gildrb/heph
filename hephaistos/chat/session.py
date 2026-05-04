"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

import atexit
import contextlib
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from hephaistos.agent.dispatch import SteeringQueue
from hephaistos.agent.persona import Persona, resolve_persona
from hephaistos.agent.prompt import build_system_prompt
from hephaistos.agent.tools import ToolRegistry, default_registry
from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.events import render_turn_event
from hephaistos.chat.orchestrator import TurnOrchestrator
from hephaistos.chat.titles import derive_title as _derive_title
from hephaistos.chat.usage import SessionUsage
from hephaistos.diagnostics.crashes import set_session_context
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.logging import TraceWriter, get_logger
from hephaistos.materials import iter_material_files
from hephaistos.memory import MemoryStore, load_memory
from hephaistos.rag import ArmoryIndex, TurnEvidence
from hephaistos.runtime import ChatConfig, Conversation, Message
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
    source_files: tuple[str, ...] = ()
    dirty: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resumed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    live_tokens_visible: bool = False
    live_cost_visible: bool = False
    last_turn_evidence: TurnEvidence | None = None
    _rag_index: ArmoryIndex | None = field(default=None, init=False, repr=False)
    _memory: MemoryStore | None = field(default=None, init=False, repr=False)
    _tool_registry: ToolRegistry = field(
        default_factory=default_registry.child,
        init=False,
        repr=False,
    )
    usage: SessionUsage = field(default_factory=SessionUsage)
    trace: TraceWriter = field(init=False, repr=False)
    steering: SteeringQueue = field(default_factory=SteeringQueue, init=False, repr=False)
    study_state: StudyState = field(default_factory=StudyState)
    persona: Persona = field(default_factory=lambda: resolve_persona(None))

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace", TraceWriter(self.session_id, self.armory_path))
        atexit.register(self.trace.close)

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tool_registry

    @property
    def current_run_seconds(self) -> int:
        return max(0, int((datetime.now(UTC) - self.resumed_at).total_seconds()))

    def mark_activity(self) -> None:
        self.last_activity_at = datetime.now(UTC)

    @property
    def memory(self) -> MemoryStore | None:
        return self._memory

    @property
    def rag_index(self) -> ArmoryIndex | None:
        return self._rag_index

    @rag_index.setter
    def rag_index(self, value: ArmoryIndex | None) -> None:
        object.__setattr__(self, "_rag_index", value)

    def configure_armory_context(
        self,
        *,
        memory: MemoryStore | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        if memory is not None:
            object.__setattr__(self, "_memory", memory)
        if tool_registry is not None:
            object.__setattr__(self, "_tool_registry", tool_registry)


class SessionError(Exception):
    """Raised when a session cannot be created or used."""


_SYSTEM_PROMPT_FALLBACK = (
    "Hephaistos. A study drill engine.\n"
    "You need an armory with study materials to study. No armory is attached.\n"
    "Tell the user to create one: run `heph armory init <path>` or type /armory "
    "in the shell. Say nothing else."
)

_PLAIN_CHAT_CONTEXT = (
    "No armory or study materials are attached. Workspace tools are unavailable.\n"
    "Do not answer general-knowledge questions or chat. Do not fabricate evidence.\n"
    "Tell the user to create an armory (`heph armory init <path>` or /armory) and "
    "add study materials to begin studying. Be terse."
)


def _metadata_datetime(metadata: dict[str, object], key: str) -> datetime | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_armory_path(path_str: str) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path


def _scan_source_files(armory_path: Path) -> tuple[int, list[str]]:
    """Count material files and collect relative paths in a single pass."""
    count = 0
    names: list[str] = []
    for file_path in iter_material_files(armory_path):
        count += 1
        names.append(str(file_path.relative_to(armory_path)))
    return count, names


def _load_armory_tools(armory_path: Path) -> ToolRegistry:
    """Create a child registry and load any armory tool plugins."""
    registry = default_registry.child()
    tools_dir = armory_path / ".hephaistos" / "tools"
    loaded = registry.load_plugins(tools_dir)
    if loaded:
        _log.info(
            "armory tools loaded",
            extra={"fields": {"armory": str(armory_path), "plugins": loaded}},
        )
    return registry


def _build_plain_system_prompt(persona: Persona) -> str:
    if persona.slug == "drill":
        return _SYSTEM_PROMPT_FALLBACK
    return f"{persona.role_block}\n\n{_PLAIN_CHAT_CONTEXT}"


def _replace_system_prompt(session: ChatSession) -> None:  # ty: ignore
    """Replace the system prompt in the conversation with the current persona."""
    if session.armory_path is None:
        new_prompt = _build_plain_system_prompt(session.persona)
    else:
        source_files = _scan_source_files(session.armory_path)[1]
        memory_ctx = ""
        with contextlib.suppress(Exception):
            memory_ctx = load_memory(session.armory_path).build_system_context()
        new_prompt = build_system_prompt(
            armory_path=session.armory_path,
            source_files=source_files or None,
            memory_context=memory_ctx,
            persona=session.persona,
        )
    for msg in session.conversation.messages:
        if msg.role == "system" and not msg.content.startswith("[Conversation summary]"):
            msg.content = new_prompt
            return
    # No system message found (shouldn't happen), prepend one
    session.conversation.messages.insert(0, Message(role="system", content=new_prompt))


replace_system_prompt = _replace_system_prompt


def create_plain_session(config: ChatConfig) -> ChatSession:
    """Create a fresh chat session without an attached armory."""
    conversation = Conversation()
    conversation.add("system", _build_plain_system_prompt(resolve_persona(None)))
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
    set_session_context(
        session_id=session.session_id,
        armory="plain",
        provider=config.provider_slug or "unknown",
        model=config.model,
    )
    capture_analytics("session_created", {"mode": "plain", "model": config.model})
    return session


def create_session(config: ChatConfig, armory_path: Path) -> ChatSession:
    """Create a fresh chat session scoped to an armory."""
    if armory_path is None:  # ty: ignore runtime guard for untyped callers
        raise SessionError("An armory is required. Create one with: hephaistos armory init <path>")

    source_file_count, source_files = _scan_source_files(armory_path)
    if source_file_count == 0:
        raise SessionError(
            f"Armory has no study materials. Add your files to {armory_path}/materials/."
        )

    conversation = Conversation()
    memory_ctx = ""
    with contextlib.suppress(Exception):
        memory_ctx = load_memory(armory_path).build_system_context()
    conversation.add(
        "system",
        build_system_prompt(
            armory_path=armory_path,
            source_files=source_files,
            memory_context=memory_ctx,
            persona=None,
        ),
    )

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=source_file_count,
        source_files=tuple(source_files),
    )
    session.configure_armory_context(
        memory=load_memory(armory_path),
        tool_registry=_load_armory_tools(armory_path),
    )
    _log.info(
        "session created",
        extra={
            "fields": {
                "session_id": session.session_id,
                "armory": str(armory_path),
                "source_files": source_file_count,
                "model": config.model,
                "memory_entries": len(session.memory.entries) if session.memory else 0,
                "tools": len(session.tool_registry.schemas),
            }
        },
    )
    session.trace.record_session_event("created", model=config.model)
    set_session_context(
        session_id=session.session_id,
        armory="attached",
        provider=config.provider_slug or "unknown",
        model=config.model,
    )
    capture_analytics(
        "session_created",
        {
            "mode": "armory",
            "source_file_count": source_file_count,
            "model": config.model,
        },
    )
    return session


def resume_session(config: ChatConfig, armory_path: Path, session_id: str) -> ChatSession:
    """Load a saved session from an armory."""
    conversation, title = chat_storage.load(armory_path, session_id)
    metadata = chat_storage.load_metadata(armory_path, session_id)
    source_file_count, source_files = _scan_source_files(armory_path)
    now = datetime.now(UTC)
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=source_file_count,
        source_files=tuple(source_files),
        study_state=StudyState.from_dict(metadata.get("study_state")),
        started_at=_metadata_datetime(metadata, "started_at") or now,
        resumed_at=now,
        last_activity_at=now,
    )
    session.configure_armory_context(
        memory=load_memory(armory_path),
        tool_registry=_load_armory_tools(armory_path),
    )
    _log.info(
        "session resumed",
        extra={
            "fields": {
                "session_id": session_id,
                "armory": str(armory_path),
                "message_count": len(conversation.messages),
                "memory_entries": len(session.memory.entries) if session.memory else 0,
                "tools": len(session.tool_registry.schemas),
            }
        },
    )
    session.trace.record_session_event("resumed", title=title)
    set_session_context(
        session_id=session_id,
        armory="attached",
        provider=config.provider_slug or "unknown",
        model=config.model,
    )
    capture_analytics(
        "session_resumed",
        {
            "message_count": len(conversation.messages),
            "model": config.model,
        },
    )
    return session


def session_has_messages(session: ChatSession) -> bool:
    """Return ``True`` when the session contains non-system messages."""
    return any(message.role != "system" for message in session.conversation.messages)


def send_user_message(
    session: ChatSession,
    user_input: str,
    *,
    abort: threading.Event | None = None,
    reply_prefix: str = "",
    writer: Callable[[str], None] | None = None,
) -> str:
    """Run one user turn via the orchestrator and mirror events to a writer.

    When *writer* is provided, rendered output is forwarded to it instead of
    being written to ``sys.stdout``. This keeps backward compatibility with
    callers that still rely on stdout behaviour.
    """
    session.mark_activity()
    orchestrator = TurnOrchestrator(session)
    printed_prefix = False

    def _write(text: str) -> None:
        if writer is not None:
            writer(text)
        else:
            sys.stdout.write(text)
            sys.stdout.flush()

    for event in orchestrator.iter_events(user_input, abort=abort):
        rendered = render_turn_event(event)
        if not rendered:
            continue
        if reply_prefix and not printed_prefix:
            _write(reply_prefix)
            printed_prefix = True
        _write(rendered)

    if orchestrator.last_reply:
        _write("\n")
    session.mark_activity()
    if session.armory_path is not None and session.dirty and session_has_messages(session):
        with contextlib.suppress(chat_storage.ChatStorageError):
            save_session(session)
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
        metadata={
            "study_state": session.study_state.to_dict(),
            "started_at": session.started_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
        },
    )
    session.dirty = False
    capture_analytics(
        "session_saved",
        {
            "message_count": len(session.conversation.messages),
            "mode": "armory",
            "model": session.config.model,
        },
    )
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


def list_armory_sessions(armory_path: Path) -> list[chat_storage.SessionRecord]:
    """Return saved sessions for the given armory."""
    return chat_storage.list_sessions(armory_path)
