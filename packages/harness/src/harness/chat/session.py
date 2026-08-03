"""Reusable chat session helpers shared by the CLI and TUI."""

from __future__ import annotations

import atexit
import contextlib
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from ai.logging import get_logger
from ai.runtime import ChatConfig, Conversation, Message

from harness.agent.prompt import build_system_prompt
from harness.agent.shell_tools import ARMORY_SHELL_TRUST_ENV
from harness.agent.steering import Steering
from harness.agent.tools import ToolRegistry, default_registry, register_shell_tool
from harness.armory.trust import armory_path_trusted
from harness.chat import storage as chat_storage
from harness.chat.message_delivery import send_user_message as _deliver_user_message
from harness.chat.session_persistence import save_session, session_has_messages
from harness.chat.titles import derive_title as _derive_title
from harness.chat.turn_contract import TurnContract
from harness.chat.turn_history import (
    TurnSnapshot,
    build_turn_snapshot,
    turn_history_from_payload,
    turn_history_through,
    turn_snapshot_by_id,
)
from harness.chat.turn_orchestrator import TurnOrchestrator
from harness.chat.usage import SessionUsage
from harness.diagnostics.crashes import set_session_context
from harness.diagnostics.events import capture as capture_analytics
from harness.diagnostics.traces import TraceWriter
from harness.documents import RecallState
from harness.materials import iter_material_files
from harness.memory import MemoryStore, load_memory
from harness.rag import ArmoryIndex, TurnEvidence, scan_unindexable_files
from harness.rag.health import ExtractionHealthIssue, scan_extraction_health

_log = get_logger("harness.chat.session")
_LEGACY_RECALL_STATE_KEYS = ("learning_state", "study_state")


@dataclass(frozen=True, slots=True)
class _SessionArmoryContext:
    source_file_count: int
    source_files: list[str]
    disabled_source_files: set[str]


@dataclass
class ChatSession:
    config: ChatConfig
    conversation: Conversation
    session_id: str
    title: str = ""
    armory_path: Path | None = None
    source_file_count: int = 0
    source_files: tuple[str, ...] = ()
    disabled_source_files: set[str] = field(default_factory=set)
    dirty: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resumed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    live_tokens_visible: bool = False
    live_cost_visible: bool = False
    last_turn_evidence: TurnEvidence | None = None
    last_plan_intent: str = ""
    last_turn_contract: TurnContract | None = None
    retrieval_notice: str = ""
    turn_history: list[TurnSnapshot] = field(default_factory=list)
    _rag_index: ArmoryIndex | None = field(default=None, init=False, repr=False)
    _memory: MemoryStore | None = field(default=None, init=False, repr=False)
    _tool_registry: ToolRegistry = field(
        default_factory=default_registry.child,
        init=False,
        repr=False,
    )
    usage: SessionUsage = field(default_factory=SessionUsage)
    trace: TraceWriter = field(init=False, repr=False)
    steering: Steering = field(default_factory=Steering, init=False, repr=False)
    recall_state: RecallState = field(default_factory=RecallState)
    _last_document_cost_usd: float = field(default=0.0, init=False, repr=False)

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

    def refresh_armory_sources(self) -> None:
        refresh_armory_sources(self)


class SessionError(Exception):
    pass


ARMORY_PLUGINS_TRUST_ENV = "HARNESS_TRUST_ARMORY_PLUGINS"
ARMORY_MEMORY_TRUST_ENV = "HARNESS_TRUST_ARMORY_MEMORY"


def _scan_source_files(armory_path: Path) -> tuple[int, list[str]]:
    names = [
        str(file_path.relative_to(armory_path)) for file_path in iter_material_files(armory_path)
    ]
    return len(names), names


def _armory_context(
    armory_path: Path,
    metadata: Mapping[str, object] | None = None,
) -> _SessionArmoryContext:
    source_file_count, source_files = _scan_source_files(armory_path)
    return _SessionArmoryContext(
        source_file_count=source_file_count,
        source_files=source_files,
        disabled_source_files=_active_disabled_sources(
            metadata.get("disabled_source_files") if metadata else None,
            source_files,
        ),
    )


def _active_disabled_sources(raw_disabled: object, source_files: list[str]) -> set[str]:
    if not isinstance(raw_disabled, list):
        return set()
    return {item for item in raw_disabled if isinstance(item, str)} & set(source_files)


def refresh_armory_sources(session: ChatSession) -> None:
    if session.armory_path is None:
        return
    context = _armory_context(session.armory_path)
    session.source_file_count = context.source_file_count
    session.source_files = tuple(context.source_files)
    session.disabled_source_files &= set(context.source_files)
    session.rag_index = None
    _replace_system_prompt(session)


def _load_armory_tools(armory_path: Path) -> ToolRegistry:
    registry = default_registry.child()
    if _armory_shell_trusted(armory_path):
        register_shell_tool(registry)
        _log.warning(
            "shell tool enabled; agent can run commands on this machine",
            extra={"fields": {"armory": str(armory_path), "env": ARMORY_SHELL_TRUST_ENV}},
        )
    tools_dir = armory_path / ".harness" / "tools"
    if not _armory_plugins_trusted(armory_path):
        _warn_untrusted_armory_plugins(armory_path, tools_dir)
        return registry

    loaded = registry.load_plugins(tools_dir)
    if loaded:
        _log.info(
            "armory tools loaded",
            extra={"fields": {"armory": str(armory_path), "plugins": loaded}},
        )
    return registry


def _armory_plugins_trusted(armory_path: Path) -> bool:
    return armory_path_trusted(armory_path, ARMORY_PLUGINS_TRUST_ENV)


def _armory_shell_trusted(armory_path: Path) -> bool:
    return armory_path_trusted(armory_path, ARMORY_SHELL_TRUST_ENV)


def _warn_untrusted_armory_plugins(armory_path: Path, tools_dir: Path) -> None:
    has_plugins = any(_is_visible_plugin_file(path) for path in tools_dir.glob("*.py"))
    if not tools_dir.is_dir() or not has_plugins:
        return
    _log.warning(
        "armory tools skipped; explicit trust not enabled",
        extra={
            "fields": {
                "armory": str(armory_path),
                "env": ARMORY_PLUGINS_TRUST_ENV,
            }
        },
    )


def _is_visible_plugin_file(path: Path) -> bool:
    return path.is_file() and not path.name.startswith("_")


def _build_plain_system_prompt() -> str:
    return build_system_prompt()


def _scan_extraction_health_issues(armory_path: Path) -> tuple[ExtractionHealthIssue, ...]:
    try:
        return scan_extraction_health(armory_path).issues
    except Exception:
        _log.warning(
            "extraction health scan failed",
            extra={"fields": {"armory": str(armory_path)}},
            exc_info=True,
        )
        return ()


def _replace_system_prompt(session: ChatSession) -> None:
    new_prompt = _system_prompt_for_session(session)
    for msg in session.conversation.messages:
        if msg.role == "system" and not msg.content.startswith("[Conversation summary]"):
            msg.content = new_prompt
            return
    # No system message found (shouldn't happen), prepend one
    session.conversation.messages.insert(0, Message(role="system", content=new_prompt))


replace_system_prompt = _replace_system_prompt


def _system_prompt_for_session(session: ChatSession) -> str:
    if session.armory_path is None:
        return _build_plain_system_prompt()
    return _armory_system_prompt(session.armory_path, registry=session.tool_registry)


def _armory_system_prompt(
    armory_path: Path,
    source_files: list[str] | None = None,
    *,
    registry: ToolRegistry | None = None,
) -> str:
    material_files = (
        source_files if source_files is not None else _scan_source_files(armory_path)[1]
    )
    unindexable = scan_unindexable_files(armory_path)
    return build_system_prompt(
        armory_path=armory_path,
        source_files=material_files or None,
        unindexable_files=unindexable or None,
        extraction_health_issues=_scan_extraction_health_issues(armory_path),
        memory_context=_memory_system_context(armory_path),
        registry=registry,
    )


def _memory_system_context(armory_path: Path) -> str:
    if not armory_path_trusted(armory_path, ARMORY_MEMORY_TRUST_ENV):
        _warn_untrusted_armory_memory(armory_path)
        return ""
    with contextlib.suppress(Exception):
        return load_memory(armory_path).build_system_context()
    return ""


def _warn_untrusted_armory_memory(armory_path: Path) -> None:
    memory_file = armory_path / ".harness" / "memory.json"
    if not memory_file.is_file():
        return
    _log.warning(
        "armory memory skipped for system context; explicit trust not enabled",
        extra={
            "fields": {
                "armory": str(armory_path),
                "env": ARMORY_MEMORY_TRUST_ENV,
            }
        },
    )


def create_plain_session(config: ChatConfig) -> ChatSession:
    conversation = Conversation()
    conversation.add("system", _build_plain_system_prompt())
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
    if armory_path is None:
        raise SessionError("An armory is required. Create one with: heph armory init <name>")

    context = _armory_context(armory_path)

    conversation = Conversation()
    conversation.add("system", _armory_system_prompt(armory_path, context.source_files))

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=context.source_file_count,
        source_files=tuple(context.source_files),
    )
    _configure_session_armory_context(session, armory_path)
    _log.info(
        "session created",
        extra={
            "fields": {
                "session_id": session.session_id,
                "armory": str(armory_path),
                "source_files": context.source_file_count,
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
            "source_file_count": context.source_file_count,
            "model": config.model,
        },
    )
    return session


def resume_session(config: ChatConfig, armory_path: Path, session_id: str) -> ChatSession:
    conversation, title = chat_storage.load(armory_path, session_id)
    metadata = chat_storage.load_metadata(armory_path, session_id)
    context = _armory_context(armory_path, metadata)
    now = datetime.now(UTC)
    started_at = _metadata_datetime(metadata, "started_at") or now
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=context.source_file_count,
        source_files=tuple(context.source_files),
        recall_state=RecallState.from_dict(_session_recall_state_payload(metadata)),
        disabled_source_files=context.disabled_source_files,
        last_plan_intent=_metadata_string(metadata, "last_plan_intent"),
        last_turn_contract=TurnContract.from_dict(metadata.get("last_turn_contract")),
        last_turn_evidence=TurnEvidence.from_dict(metadata.get("last_turn_evidence")),
        turn_history=turn_history_from_payload(metadata.get("turn_history")),
        started_at=started_at,
        resumed_at=now,
        last_activity_at=now,
    )
    _configure_session_armory_context(session, armory_path)
    replace_system_prompt(session)
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


def _configure_session_armory_context(session: ChatSession, armory_path: Path) -> None:
    session.configure_armory_context(
        memory=load_memory(armory_path),
        tool_registry=_load_armory_tools(armory_path),
    )
    _replace_system_prompt(session)


def _metadata_datetime(metadata: Mapping[str, object], key: str) -> datetime | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    with contextlib.suppress(ValueError):
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    return None


def _metadata_string(metadata: Mapping[str, object], key: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) else ""


def _session_recall_state_payload(metadata: Mapping[str, object]) -> object:
    current_payload = metadata.get("recall_state")
    if current_payload is not None:
        return current_payload
    for key in _LEGACY_RECALL_STATE_KEYS:
        legacy_payload = metadata.get(key)
        if legacy_payload is not None:
            return legacy_payload
    return None


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
    return _deliver_user_message(
        session,
        user_input,
        runner_factory=TurnOrchestrator,
        abort=abort,
        reply_prefix=reply_prefix,
        writer=writer,
    )


def record_turn_snapshot(
    session: ChatSession,
    *,
    user_input: str,
    assistant_reply: str,
    evidence: TurnEvidence | None,
    plan_intent: str,
    contract: TurnContract | None,
) -> None:
    snapshot = build_turn_snapshot(
        session.conversation,
        session.turn_history,
        recall_state=session.recall_state,
        user_input=user_input,
        assistant_reply=assistant_reply,
        evidence=evidence,
        plan_intent=plan_intent,
        contract=contract,
    )
    if snapshot is None:
        return
    session.turn_history.append(snapshot)


def fork_session_at_turn(session: ChatSession, turn_id: str) -> ChatSession:
    snapshot = turn_snapshot_by_id(session.turn_history, turn_id)
    if snapshot is None:
        raise SessionError(f"turn not found: {turn_id}")
    if session.armory_path is not None and session.dirty and session_has_messages(session):
        with contextlib.suppress(chat_storage.ChatStorageError):
            save_session(session)

    messages = [
        Message(message.role, message.content)
        for message in session.conversation.messages[: snapshot.message_count]
    ]
    branched = ChatSession(
        config=replace(session.config),
        conversation=Conversation(messages=messages),
        session_id=chat_storage.new_session_id(),
        title=_branched_title(session.title or _derive_title(Conversation(messages=messages))),
        armory_path=session.armory_path,
        source_file_count=session.source_file_count,
        source_files=tuple(session.source_files),
        disabled_source_files=set(session.disabled_source_files),
        dirty=True,
        last_turn_evidence=snapshot.evidence,
        last_plan_intent=snapshot.plan_intent,
        last_turn_contract=snapshot.contract,
        turn_history=turn_history_through(session.turn_history, snapshot),
        recall_state=snapshot.recall_state.clone(),
    )
    if session.armory_path is not None:
        _configure_session_armory_context(branched, session.armory_path)
        replace_system_prompt(branched)
    return branched


def _branched_title(title: str) -> str:
    cleaned = title.strip() or "Chat"
    suffix = " branch"
    if cleaned.endswith(suffix):
        return cleaned
    return f"{cleaned}{suffix}"


def list_armory_sessions(armory_path: Path) -> list[chat_storage.SessionRecord]:
    return chat_storage.list_sessions(armory_path)
