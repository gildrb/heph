"""Programmatic Heph runtime for UI and automation clients."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path

from ai.runtime import ChatConfig
from hephaion.armory.search import (
    load_available_armory_entries,
    remember_armory,
    set_last_armory,
)
from hephaion.armory.storage import initialize, normalize_path
from hephaion.chat.orchestrator import iter_chat_events
from hephaion.chat.session import (
    ChatSession,
    create_plain_session,
    create_session,
    fork_session_at_turn,
    list_armory_sessions,
    resume_session,
    save_session,
    validate_armory_path,
)
from hephaion.chat.session_persistence import save_dirty_session_if_needed
from hephaion.materials.importing import import_material_files, resolve_import_source
from hephaion.parameters.cli import load_config
from hephaion.rag.health import scan_extraction_health as scan_extraction_health_report
from hephaion.rag.index import build_index as build_rag_index

from heph.sdk.events import AssistantDelta, HephEvent, TurnComplete, from_turn_event
from heph.sdk.materials import (
    ExtractionHealthIssueSummary,
    ExtractionHealthSummary,
    ImportMaterialsSummary,
    IndexProgressEvent,
    IndexSummary,
    MaterialSummary,
)
from hephaion.materials import MATERIALS_DIR, material_manifest

type HephEventListener = Callable[[HephEvent], None]
type HephSessionStreamGuard = Callable[[threading.Event], AbstractContextManager[None]]


class HephSdkError(Exception):
    """Raised when an SDK operation is invalid for the active runtime."""


class HephSdkBusyError(HephSdkError):
    """Raised when the SDK service is busy with an active prompt stream."""

    def __init__(
        self,
        message: str = "An SDK prompt stream is active; only state and abort are available.",
    ) -> None:
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class HephMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, object]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class ArmorySummary:
    path: Path
    exists: bool
    valid: bool

    @property
    def name(self) -> str:
        return self.path.name

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists,
            "valid": self.valid,
        }


@dataclass(frozen=True, slots=True)
class SessionSummary:
    session_id: str
    title: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class HephSession:
    """Stable SDK wrapper around a single Heph chat session."""

    _session: ChatSession
    _listeners: list[HephEventListener] = field(default_factory=list, init=False, repr=False)
    _stream_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _active_abort: threading.Event | None = field(default=None, init=False, repr=False)
    _stream_start_guard: HephSessionStreamGuard | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _streaming: bool = field(default=False, init=False, repr=False)

    @property
    def session_id(self) -> str:
        return self._session.session_id

    @property
    def title(self) -> str:
        return self._session.title

    @property
    def armory_path(self) -> Path | None:
        return self._session.armory_path

    @property
    def model(self) -> str:
        return self._session.config.model

    @property
    def source_file_count(self) -> int:
        return self._session.source_file_count

    @property
    def source_files(self) -> tuple[str, ...]:
        return self._session.source_files

    @property
    def disabled_source_files(self) -> frozenset[str]:
        return frozenset(self._session.disabled_source_files)

    @property
    def enabled_source_files(self) -> tuple[str, ...]:
        disabled = self.disabled_source_files
        return tuple(source for source in self.source_files if source not in disabled)

    @property
    def has_unsaved_changes(self) -> bool:
        return self._session.dirty

    @property
    def messages(self) -> tuple[HephMessage, ...]:
        return tuple(
            HephMessage(role=message.role, content=message.content)
            for message in self._session.conversation.messages
            if message.role != "system"
        )

    @property
    def is_streaming(self) -> bool:
        with self._stream_lock:
            return self._streaming

    def subscribe(self, listener: HephEventListener) -> Callable[[], None]:
        """Subscribe to prompt events. Returns an unsubscribe callback."""
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def abort(self) -> None:
        with self._stream_lock:
            active_abort = self._active_abort
        if active_abort is not None:
            active_abort.set()

    def prompt(
        self,
        text: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[HephEvent]:
        """Run a user turn and stream stable SDK events."""
        active_abort = abort or threading.Event()
        with self._stream_guard(active_abort):
            self._begin_stream(active_abort)
        try:
            for event in iter_chat_events(self._session, text, abort=active_abort):
                sdk_event = from_turn_event(event)
                self._emit(sdk_event)
                yield sdk_event
        finally:
            try:
                save_dirty_session_if_needed(self._session)
            finally:
                self._end_stream(active_abort)

    def ask(self, text: str, *, abort: threading.Event | None = None) -> str:
        """Run a user turn and return the final assistant text."""
        chunks: list[str] = []
        full_text = ""
        for event in self.prompt(text, abort=abort):
            if isinstance(event, AssistantDelta):
                chunks.append(event.delta)
            elif isinstance(event, TurnComplete):
                full_text = event.full_text
        return full_text or "".join(chunks)

    def refresh_materials(self) -> None:
        self._session.refresh_armory_sources()

    def set_source_enabled(self, source: str, enabled: bool) -> bool:
        if source not in self.source_files:
            raise HephSdkError(f"SDK session source file is not attached: {source}")
        disabled_sources = self._session.disabled_source_files
        if enabled:
            if source not in disabled_sources:
                return False
            disabled_sources.remove(source)
        else:
            if source in disabled_sources:
                return False
            disabled_sources.add(source)
        self._session.dirty = True
        return True

    def save(self) -> Path:
        return save_session(self._session)

    def dispose(self) -> None:
        self._listeners.clear()
        self.abort()
        self._session.trace.close()

    def to_dict(self) -> dict[str, object]:
        return HephSdkSessionState.from_session(self).to_dict()

    def _emit(self, event: HephEvent) -> None:
        for listener in tuple(self._listeners):
            listener(event)

    def _set_stream_start_guard(self, guard: HephSessionStreamGuard) -> None:
        with self._stream_lock:
            self._stream_start_guard = guard

    def _stream_guard(self, abort: threading.Event) -> AbstractContextManager[None]:
        with self._stream_lock:
            guard = self._stream_start_guard
        if guard is None:
            return nullcontext()
        return guard(abort)

    def _begin_stream(self, abort: threading.Event) -> None:
        with self._stream_lock:
            if self._streaming:
                raise HephSdkBusyError("Session is already streaming.")
            self._active_abort = abort
            self._streaming = True

    def _end_stream(self, abort: threading.Event) -> None:
        with self._stream_lock:
            if self._active_abort is abort:
                self._streaming = False
                self._active_abort = None


@dataclass(frozen=True, slots=True)
class HephSdkSessionState:
    session_id: str
    title: str
    armory_path: Path | None
    model: str
    is_streaming: bool
    messages: tuple[HephMessage, ...]
    source_file_count: int = 0
    source_files: tuple[str, ...] = ()
    disabled_source_files: frozenset[str] = frozenset()
    enabled_source_files: tuple[str, ...] = ()
    has_unsaved_changes: bool = False

    @classmethod
    def from_session(cls, session: HephSession) -> HephSdkSessionState:
        return cls(
            session_id=session.session_id,
            title=session.title,
            armory_path=session.armory_path,
            model=session.model,
            is_streaming=session.is_streaming,
            messages=session.messages,
            source_file_count=session.source_file_count,
            source_files=session.source_files,
            disabled_source_files=session.disabled_source_files,
            enabled_source_files=session.enabled_source_files,
            has_unsaved_changes=session.has_unsaved_changes,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
            "model": self.model,
            "is_streaming": self.is_streaming,
            "source_file_count": self.source_file_count,
            "source_files": list(self.source_files),
            "disabled_source_files": sorted(self.disabled_source_files),
            "enabled_source_files": list(self.enabled_source_files),
            "has_unsaved_changes": self.has_unsaved_changes,
            "messages": [message.to_dict() for message in self.messages],
        }


@dataclass(slots=True)
class HephRuntime:
    """Runtime facade for creating and replacing Heph sessions."""

    config: ChatConfig
    armory_path: Path | None = None

    @classmethod
    def plain(cls, *, config: ChatConfig | None = None) -> HephRuntime:
        return cls(config=_config_or_default(config, None), armory_path=None)

    @classmethod
    def open_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephRuntime:
        armory_path = validate_armory_path(str(path))
        remember_armory(armory_path)
        set_last_armory(armory_path)
        return cls(config=_config_or_default(config, armory_path), armory_path=armory_path)

    @classmethod
    def create_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephRuntime:
        armory_path = normalize_path(path)
        initialize(armory_path)
        remember_armory(armory_path)
        set_last_armory(armory_path)
        return cls(config=_config_or_default(config, armory_path), armory_path=armory_path)

    @staticmethod
    def list_armories() -> tuple[ArmorySummary, ...]:
        return tuple(
            ArmorySummary(path=entry.path, exists=entry.exists, valid=entry.valid)
            for entry in load_available_armory_entries()
        )

    def new_session(self) -> HephSession:
        if self.armory_path is None:
            return HephSession(create_plain_session(self.config))
        return HephSession(create_session(self.config, self.armory_path))

    def resume_session(self, session_id: str) -> HephSession:
        if self.armory_path is None:
            raise HephSdkError("Cannot resume a saved session without an armory.")
        return HephSession(resume_session(self.config, self.armory_path, session_id))

    def fork_session(self, session: HephSession, turn_id: str) -> HephSession:
        return HephSession(fork_session_at_turn(session._session, turn_id))

    def list_sessions(self) -> tuple[SessionSummary, ...]:
        if self.armory_path is None:
            return ()
        return tuple(
            SessionSummary(
                session_id=record["session_id"],
                title=record["title"],
                created_at=record["created_at"],
                updated_at=record["updated_at"],
            )
            for record in list_armory_sessions(self.armory_path)
        )

    def list_materials(self) -> tuple[MaterialSummary, ...]:
        armory_path = self._require_armory_path("list materials")
        return tuple(
            MaterialSummary(
                path=material.path,
                rel_path=material.rel_path,
                kind=material.kind,
                role=material.role,
                confidence=material.confidence,
                reason=material.reason,
            )
            for material in material_manifest(armory_path)
        )

    def import_materials(self, source: str | Path) -> ImportMaterialsSummary:
        armory_path = self._require_armory_path("import materials")
        result = import_material_files(
            resolve_import_source(str(source)),
            armory_path / MATERIALS_DIR,
        )
        return ImportMaterialsSummary(
            imported=result.imported,
            considered=result.considered,
            skipped_duplicates=result.skipped_duplicates,
            skipped_unsupported=result.skipped_unsupported,
        )

    def build_index(self) -> IndexSummary:
        armory_path = self._require_armory_path("build an index")
        progress_events: list[IndexProgressEvent] = []

        def record_progress(action: str, detail: str) -> None:
            progress_events.append(IndexProgressEvent(action=action, detail=detail))

        index = build_rag_index(armory_path, progress=record_progress)
        return IndexSummary(
            documents=len(index.documents),
            chunks=index.chunk_count,
            progress=tuple(progress_events),
        )

    def scan_extraction_health(self) -> ExtractionHealthSummary:
        armory_path = self._require_armory_path("scan extraction health")
        report = scan_extraction_health_report(armory_path)
        return ExtractionHealthSummary(
            armory_path=Path(report.armory_path),
            documents=report.documents,
            checks=report.checks,
            pass_rate=report.pass_rate,
            forbidden_text=report.forbidden_text,
            issues=tuple(
                ExtractionHealthIssueSummary(
                    source=issue.source,
                    forbidden_text_present=issue.forbidden_text_present,
                )
                for issue in report.issues
            ),
        )

    def _require_armory_path(self, action: str) -> Path:
        if self.armory_path is None:
            raise HephSdkError(f"Cannot {action} without an armory.")
        return self.armory_path


def _config_or_default(config: ChatConfig | None, armory_path: Path | None) -> ChatConfig:
    if config is not None:
        return config
    return load_config(armory_path)


__all__ = [
    "ArmorySummary",
    "ExtractionHealthIssueSummary",
    "ExtractionHealthSummary",
    "HephEventListener",
    "HephMessage",
    "HephRuntime",
    "HephSdkBusyError",
    "HephSdkError",
    "HephSdkSessionState",
    "HephSession",
    "ImportMaterialsSummary",
    "IndexProgressEvent",
    "IndexSummary",
    "MaterialSummary",
    "SessionSummary",
]
