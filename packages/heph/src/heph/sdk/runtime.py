"""Programmatic Heph runtime for UI and automation clients."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ai.logging import get_logger
from ai.runtime import ChatConfig, EngineError, EngineErrorCode
from hephaion.armory.search import (
    load_available_armory_entries,
    remember_armory,
    set_last_armory,
)
from hephaion.armory.storage import ArmoryError, initialize, normalize_path, validate_armory_path
from hephaion.chat.orchestrator import iter_chat_events
from hephaion.chat.session import (
    ChatSession,
    create_plain_session,
    create_session,
    fork_session_at_turn,
    list_armory_sessions,
    resume_session,
    save_session,
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
from heph.sdk.methods import SDK_ENGINE_ERROR_CODE
from heph.sdk.models import (
    ModelChoiceSummary,
)
from heph.sdk.models import (
    list_model_choices as list_config_model_choices,
)
from heph.sdk.models import (
    switch_model as switch_config_model,
)
from heph.sdk.providers import (
    ProviderSummary,
)
from heph.sdk.providers import (
    list_providers as list_config_providers,
)
from heph.sdk.state import HephMessage, HephSdkSessionState
from hephaion.materials import MATERIALS_DIR, material_manifest

type HephEventListener = Callable[[HephEvent], None]
type HephSessionStreamGuard = Callable[[threading.Event], AbstractContextManager[None]]

_log = get_logger("heph.sdk.runtime")


class _DisplaySettingsSource(Protocol):
    @property
    def thinking_visibility(self) -> str: ...

    @property
    def live_tokens_visible(self) -> bool: ...

    @property
    def live_cost_visible(self) -> bool: ...


def sdk_error_code_for_engine_error(error: EngineError) -> str:
    if error.code is None:
        return SDK_ENGINE_ERROR_CODE
    return error.code.value


class HephSdkError(Exception):
    """Raised when an SDK operation is invalid for the active runtime."""

    def __init__(self, message: str, *, code: str = "sdk_error") -> None:
        super().__init__(message)
        self.code = code


class HephSdkModelError(HephSdkError):
    """Raised when the model runtime rejects an SDK prompt."""

    def __init__(self, error: EngineError) -> None:
        super().__init__(str(error), code=sdk_error_code_for_engine_error(error))
        self.engine_code: EngineErrorCode | None = error.code


class HephSdkBusyError(HephSdkError):
    """Raised when the SDK service is busy with an active stream."""

    def __init__(
        self,
        message: str = (
            "An SDK stream is active; only state, abort, capabilities, and settings are available."
        ),
    ) -> None:
        super().__init__(message, code="busy")


class HephSdkOperationCancelledError(HephSdkError):
    """Raised when an SDK operation stream is cancelled."""

    def __init__(self, message: str = "SDK operation was cancelled.") -> None:
        super().__init__(message, code="cancelled")


class HephSdkUnavailableError(HephSdkError):
    """Raised when an SDK method is valid but unavailable for current state."""

    def __init__(
        self,
        method: str,
        *,
        kind: str = "SDK method",
        unavailable_reason: str | None = None,
    ) -> None:
        super().__init__(
            f"{kind} '{method}' is not available for the current runtime/session state.",
            code="unavailable",
        )
        self.unavailable_reason = unavailable_reason


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
class ArmoryValidationSummary:
    path: Path
    exists: bool
    is_dir: bool
    valid: bool
    error: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists,
            "is_dir": self.is_dir,
            "valid": self.valid,
            "error": self.error,
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
    _listeners_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _stream_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _active_abort: threading.Event | None = field(default=None, init=False, repr=False)
    _stream_start_guard: HephSessionStreamGuard | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _streaming: bool = field(default=False, init=False, repr=False)
    _disposed: bool = field(default=False, init=False, repr=False)

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
    def thinking_visibility(self) -> str:
        return self._session.config.thinking_visibility

    @property
    def provider_slug(self) -> str:
        return self._session.config.provider_slug

    @property
    def live_tokens_visible(self) -> bool:
        return self._session.live_tokens_visible

    @property
    def live_cost_visible(self) -> bool:
        return self._session.live_cost_visible

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

    @property
    def is_disposed(self) -> bool:
        with self._stream_lock:
            return self._disposed

    def subscribe(self, listener: HephEventListener) -> Callable[[], None]:
        """Subscribe to prompt events. Returns an unsubscribe callback."""
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            with self._listeners_lock:
                self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._listeners_lock:
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
            try:
                for event in iter_chat_events(self._session, text, abort=active_abort):
                    sdk_event = from_turn_event(event)
                    self._emit(sdk_event)
                    yield sdk_event
            except EngineError as exc:
                raise HephSdkModelError(exc) from exc
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

    def list_model_choices(self, *, refresh_live: bool = False) -> tuple[ModelChoiceSummary, ...]:
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            config = self._session.config
        return list_config_model_choices(config, refresh_live=refresh_live)

    def list_providers(self) -> tuple[ProviderSummary, ...]:
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            config = self._session.config
        return list_config_providers(config)

    def switch_model(self, provider_slug: str, model: str) -> bool:
        with self._idle_mutation():
            return switch_config_model(self._session.config, provider_slug, model)

    def apply_display_settings(self, settings: _DisplaySettingsSource) -> None:
        with self._idle_mutation():
            self._session.config.thinking_visibility = settings.thinking_visibility
            self._session.live_tokens_visible = settings.live_tokens_visible
            self._session.live_cost_visible = settings.live_cost_visible

    def refresh_materials(self) -> None:
        with self._idle_mutation():
            self._session.refresh_armory_sources()

    def set_source_enabled(self, source: str, enabled: bool) -> bool:
        with self._idle_mutation():
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
        with self._idle_mutation():
            return save_session(self._session)

    def dispose(self) -> None:
        with self._stream_lock:
            if self._disposed:
                return
            self._disposed = True
            active_abort = self._active_abort
        with self._listeners_lock:
            self._listeners.clear()
        if active_abort is not None:
            active_abort.set()
        self._session.trace.close()

    def to_dict(self) -> dict[str, object]:
        return HephSdkSessionState.from_session(self).to_dict()

    def _emit(self, event: HephEvent) -> None:
        with self._listeners_lock:
            listeners = tuple(self._listeners)
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                _log.warning(
                    "SDK event listener failed",
                    extra={"fields": {"event": event.kind}},
                    exc_info=True,
                )

    def _set_stream_start_guard(self, guard: HephSessionStreamGuard) -> None:
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            self._stream_start_guard = guard

    def _stream_guard(self, abort: threading.Event) -> AbstractContextManager[None]:
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            guard = self._stream_start_guard
        if guard is None:
            return nullcontext()
        return guard(abort)

    @contextmanager
    def _idle_mutation(self) -> Iterator[None]:
        with self._stream_lock:
            self._ensure_idle_locked()
            yield

    @contextmanager
    def _idle_raw_session(self) -> Iterator[ChatSession]:
        with self._stream_lock:
            self._ensure_idle_locked()
            yield self._session

    def _begin_stream(self, abort: threading.Event) -> None:
        with self._stream_lock:
            self._ensure_not_disposed_locked()
            if self._streaming:
                raise HephSdkBusyError("Session is already streaming.")
            self._active_abort = abort
            self._streaming = True

    def _end_stream(self, abort: threading.Event) -> None:
        with self._stream_lock:
            if self._active_abort is abort:
                self._streaming = False
                self._active_abort = None

    def _ensure_not_disposed_locked(self) -> None:
        if self._disposed:
            raise HephSdkError("SDK session is disposed.")

    def _ensure_idle_locked(self) -> None:
        self._ensure_not_disposed_locked()
        if self._streaming:
            raise HephSdkBusyError("Session is already streaming.")


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
        armory_path = _require_sdk_path(path, "armory path")
        try:
            armory_path = validate_armory_path(armory_path)
        except (ArmoryError, OSError, RuntimeError, ValueError) as exc:
            raise HephSdkError(f"SDK armory path is invalid: {exc}") from exc
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
        armory_path = _require_sdk_path(path, "armory path")
        try:
            initialize(armory_path)
        except (OSError, RuntimeError, ValueError) as exc:
            raise HephSdkError(f"SDK armory path is invalid: {exc}") from exc
        remember_armory(armory_path)
        set_last_armory(armory_path)
        return cls(config=_config_or_default(config, armory_path), armory_path=armory_path)

    @staticmethod
    def list_armories() -> tuple[ArmorySummary, ...]:
        return tuple(
            ArmorySummary(path=entry.path, exists=entry.exists, valid=entry.valid)
            for entry in load_available_armory_entries()
        )

    @staticmethod
    def validate_armory(path: str | Path) -> ArmoryValidationSummary:
        path_issue = _sdk_path_issue(path, "armory path")
        if path_issue is not None:
            return ArmoryValidationSummary(
                path=_invalid_validation_summary_path(path),
                exists=False,
                is_dir=False,
                valid=False,
                error=path_issue,
            )
        armory_path = _resolved_validation_path(path)
        exists = armory_path.exists()
        is_dir = armory_path.is_dir() if exists else False
        try:
            valid_path = validate_armory_path(armory_path)
        except (ArmoryError, OSError, RuntimeError, ValueError) as exc:
            return ArmoryValidationSummary(
                path=armory_path,
                exists=exists,
                is_dir=is_dir,
                valid=False,
                error=str(exc),
            )
        return ArmoryValidationSummary(path=valid_path, exists=True, is_dir=True, valid=True)

    def new_session(self) -> HephSession:
        if self.armory_path is None:
            return HephSession(create_plain_session(self.config))
        return HephSession(create_session(self.config, self.armory_path))

    def resume_session(self, session_id: str) -> HephSession:
        if self.armory_path is None:
            raise HephSdkError("Cannot resume a saved session without an armory.")
        return HephSession(resume_session(self.config, self.armory_path, session_id))

    def fork_session(self, session: HephSession, turn_id: str) -> HephSession:
        with session._idle_raw_session() as raw_session:
            self._ensure_raw_session_belongs_to_runtime(raw_session)
            return HephSession(fork_session_at_turn(raw_session, turn_id))

    def _ensure_session_belongs_to_runtime(self, session: HephSession) -> None:
        with session._idle_raw_session() as raw_session:
            self._ensure_raw_session_belongs_to_runtime(raw_session)

    def _ensure_raw_session_belongs_to_runtime(self, session: ChatSession) -> None:
        if _same_armory_path(session.armory_path, self.armory_path):
            return
        raise HephSdkError("SDK session belongs to a different runtime armory.")

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

    def list_model_choices(self, *, refresh_live: bool = False) -> tuple[ModelChoiceSummary, ...]:
        return list_config_model_choices(self.config, refresh_live=refresh_live)

    def list_providers(self) -> tuple[ProviderSummary, ...]:
        return list_config_providers(self.config)

    def switch_model(self, provider_slug: str, model: str) -> bool:
        return switch_config_model(self.config, provider_slug, model)

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
        source_path = _require_sdk_path(source, "material source path")
        result = import_material_files(
            resolve_import_source(str(source_path)),
            armory_path / MATERIALS_DIR,
        )
        return ImportMaterialsSummary(
            imported=result.imported,
            considered=result.considered,
            skipped_duplicates=result.skipped_duplicates,
            skipped_unsupported=result.skipped_unsupported,
        )

    def build_index(
        self,
        *,
        progress: Callable[[IndexProgressEvent], None] | None = None,
        abort: threading.Event | None = None,
    ) -> IndexSummary:
        armory_path = self._require_armory_path("build an index")
        progress_events: list[IndexProgressEvent] = []
        _raise_if_operation_cancelled(abort)

        def record_progress(action: str, detail: str) -> None:
            _raise_if_operation_cancelled(abort)
            event = IndexProgressEvent(action=action, detail=detail)
            progress_events.append(event)
            if progress is not None:
                progress(event)
            _raise_if_operation_cancelled(abort)

        index = build_rag_index(armory_path, progress=record_progress)
        _raise_if_operation_cancelled(abort)
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


def _require_sdk_path(path: str | Path, label: str) -> Path:
    path_issue = _sdk_path_issue(path, label)
    if path_issue is not None:
        raise HephSdkError(path_issue)
    try:
        return normalize_path(path)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise HephSdkError(f"SDK {label} is invalid: {exc}") from exc


def _sdk_path_issue(path: object, label: str) -> str | None:
    if not isinstance(path, str | Path):
        return f"SDK {label} must be a path string or Path."
    path_text = str(path)
    if not path_text.strip():
        return f"SDK {label} must be a non-empty path."
    if "\0" in path_text:
        return f"SDK {label} must not contain null bytes."
    return None


def _invalid_validation_summary_path(path: object) -> Path:
    path_text = str(path).replace("\0", "")
    return Path(path_text or ".")


def _resolved_validation_path(path: str | Path) -> Path:
    try:
        return normalize_path(path)
    except (OSError, RuntimeError, TypeError, ValueError):
        return Path(path)


def _same_armory_path(left: Path | None, right: Path | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return left == right


def _raise_if_operation_cancelled(abort: threading.Event | None) -> None:
    if abort is not None and abort.is_set():
        raise HephSdkOperationCancelledError()


__all__ = [
    "SDK_ENGINE_ERROR_CODE",
    "ArmorySummary",
    "ArmoryValidationSummary",
    "ExtractionHealthIssueSummary",
    "ExtractionHealthSummary",
    "HephEventListener",
    "HephMessage",
    "HephRuntime",
    "HephSdkBusyError",
    "HephSdkError",
    "HephSdkModelError",
    "HephSdkOperationCancelledError",
    "HephSdkSessionState",
    "HephSdkUnavailableError",
    "HephSession",
    "ImportMaterialsSummary",
    "IndexProgressEvent",
    "IndexSummary",
    "MaterialSummary",
    "ModelChoiceSummary",
    "ProviderSummary",
    "SessionSummary",
    "sdk_error_code_for_engine_error",
]
