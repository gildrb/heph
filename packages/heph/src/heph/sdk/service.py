"""Stateful service facade for transport adapters."""

from __future__ import annotations

import threading
from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue

from ai.providers.reasoning import normalize_reasoning_level
from ai.runtime import ChatConfig, normalize_thinking_visibility

from heph.sdk.events import event_to_dict
from heph.sdk.materials import IndexProgressEvent
from heph.sdk.runtime import HephRuntime, HephSdkBusyError, HephSdkError, HephSession
from heph.sdk.state import (
    HephSdkRuntimeState,
    HephSdkServiceState,
    HephSdkSessionState,
    HephSdkState,
)

type ServicePayload = dict[str, object]
type ServiceStream = Iterator[ServicePayload]


@dataclass(frozen=True, slots=True)
class _IndexStreamDone:
    payload: ServicePayload | None = None
    error: BaseException | None = None


type _IndexStreamItem = ServicePayload | _IndexStreamDone


@dataclass(slots=True)
class HephService:
    """JSON-ready state facade for native clients and future RPC adapters."""

    runtime: HephRuntime
    session: HephSession | None = None
    _prompt_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _active_prompt_abort: threading.Event | None = field(default=None, init=False, repr=False)
    _active_operation: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.session is not None:
            self._attach_session_stream_guard(self.session)

    @classmethod
    def plain(cls, *, config: ChatConfig | None = None) -> HephService:
        return cls(runtime=HephRuntime.plain(config=config))

    @classmethod
    def open_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephService:
        return cls(runtime=HephRuntime.open_armory(path, config=config))

    @classmethod
    def create_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephService:
        return cls(runtime=HephRuntime.create_armory(path, config=config))

    def state_snapshot(self) -> HephSdkState:
        with self._prompt_lock:
            return HephSdkState(
                service=self._service_state(),
                runtime=self._runtime_state(),
                session=self._session_state(),
            )

    def state(self) -> dict[str, object]:
        return self.state_snapshot().to_dict()

    def call(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServicePayload:
        parameters = params or {}
        if self._is_busy() and method not in {"state", "abort"}:
            raise HephSdkBusyError()
        if method == "state":
            return self.state()
        if method == "use_plain_runtime":
            return self.use_plain_runtime()
        if method == "open_armory":
            return self.open_runtime_armory(_required_str(parameters, "path"))
        if method == "create_armory":
            return self.create_runtime_armory(_required_str(parameters, "path"))
        if method == "list_armories":
            return self.list_armories()
        if method == "new_session":
            return self.new_session()
        if method == "resume_session":
            return self.resume_session(_required_str(parameters, "session_id"))
        if method == "fork_session":
            return self.fork_session(_required_str(parameters, "turn_id"))
        if method == "list_sessions":
            return self.list_sessions()
        if method == "save_session":
            return self.save_session()
        if method == "messages":
            return self.messages()
        if method == "ask":
            return self.ask(_required_str(parameters, "text"))
        if method == "abort":
            return self.abort()
        if method == "set_source_enabled":
            return self.set_source_enabled(
                _required_str(parameters, "source"),
                _required_bool(parameters, "enabled"),
            )
        if method == "list_materials":
            return self.list_materials()
        if method == "import_materials":
            return self.import_materials(_required_str(parameters, "source"))
        if method == "build_index":
            return self.build_index()
        if method == "scan_extraction_health":
            return self.scan_extraction_health()
        if method == "update_config":
            return self.update_config(parameters)
        raise HephSdkError(f"Unknown SDK service method: {method}")

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServiceStream:
        parameters = params or {}
        if method == "prompt":
            yield from self.prompt(_required_str(parameters, "text"))
            return
        if method == "build_index":
            yield from self.build_index_stream()
            return
        raise HephSdkError(f"Unknown SDK service stream method: {method}")

    def use_plain_runtime(self) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_runtime(HephRuntime.plain(config=self.runtime.config))
        return self.state()

    def open_runtime_armory(self, path: str | Path) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_runtime(HephRuntime.open_armory(path, config=self.runtime.config))
        return self.state()

    def create_runtime_armory(self, path: str | Path) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_runtime(HephRuntime.create_armory(path, config=self.runtime.config))
        return self.state()

    def list_armories(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"armories": [armory.to_dict() for armory in HephRuntime.list_armories()]}

    def new_session(self) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_session(self.runtime.new_session())
        return self._session_payload()

    def resume_session(self, session_id: str) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_session(self.runtime.resume_session(session_id))
        return self._session_payload()

    def fork_session(self, turn_id: str) -> dict[str, object]:
        with self._idle_service_call():
            self._replace_session(self.runtime.fork_session(self._require_session(), turn_id))
        return self._session_payload()

    def list_sessions(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"sessions": [session.to_dict() for session in self.runtime.list_sessions()]}

    def save_session(self) -> dict[str, object]:
        with self._idle_service_call():
            session = self._require_session()
            saved_path = session.save()
            return {"path": str(saved_path), "session": session.to_dict()}

    def messages(self) -> dict[str, object]:
        with self._idle_service_call():
            return {
                "messages": [message.to_dict() for message in self._require_session().messages]
            }

    def prompt(
        self,
        text: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[dict[str, object]]:
        active_abort = abort or threading.Event()
        session = self._begin_prompt(active_abort)
        try:
            for event in session.prompt(text, abort=active_abort):
                yield event_to_dict(event)
        finally:
            self._end_prompt(active_abort)

    def ask(self, text: str) -> dict[str, object]:
        chunks: list[str] = []
        full_text = ""
        for event in self.prompt(text):
            event_type = event.get("type")
            if event_type == "assistant_delta":
                delta = event.get("delta")
                if isinstance(delta, str):
                    chunks.append(delta)
            elif event_type == "turn_complete":
                complete_text = event.get("full_text")
                if isinstance(complete_text, str):
                    full_text = complete_text
        return {"text": full_text or "".join(chunks), "session": self._session_dict()}

    def abort(self) -> dict[str, object]:
        if active_abort := self._active_prompt_abort_event():
            active_abort.set()
            return {"aborted": True, "state": self.state()}
        with self._prompt_lock:
            if self._active_operation is not None:
                return {"aborted": False, "state": self.state()}
            session = self._require_session()
        session.abort()
        return {"aborted": True, "session": session.to_dict()}

    def set_source_enabled(self, source: str, enabled: bool) -> dict[str, object]:
        with self._idle_service_call():
            changed = self._require_session().set_source_enabled(source, enabled)
            return {"changed": changed, "session": self._session_dict()}

    def update_config(self, params: Mapping[str, object]) -> dict[str, object]:
        with self._idle_service_call():
            if value := _optional_str(params, "base_url"):
                self.runtime.config.base_url = value
            if value := _optional_str(params, "model"):
                self.runtime.config.model = value
            if "max_tokens" in params:
                max_tokens = _optional_int(params, "max_tokens")
                if max_tokens is not None:
                    self.runtime.config.max_tokens = max_tokens
            if "rag_context_budget" in params:
                rag_context_budget = _optional_int(params, "rag_context_budget")
                if rag_context_budget is not None:
                    self.runtime.config.rag_context_budget = rag_context_budget
            if "temperature" in params:
                self.runtime.config.temperature = _optional_float(params, "temperature")
            reasoning_level = _optional_str(params, "reasoning_level")
            if reasoning_level is not None:
                self.runtime.config.reasoning_level = normalize_reasoning_level(reasoning_level)
            if value := _optional_str(params, "thinking_visibility"):
                self.runtime.config.thinking_visibility = normalize_thinking_visibility(value)
        return {"runtime": self._runtime_state().to_dict()}

    def list_materials(self) -> dict[str, object]:
        with self._idle_service_call():
            return {
                "materials": [material.to_dict() for material in self.runtime.list_materials()]
            }

    def import_materials(self, source: str | Path) -> dict[str, object]:
        with self._idle_service_call():
            summary = self.runtime.import_materials(source)
            if self.session is not None and summary.imported:
                self.session.refresh_materials()
        return {"import": summary.to_dict()}

    def build_index(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"index": self.runtime.build_index().to_dict()}

    def build_index_stream(self) -> Iterator[dict[str, object]]:
        items: Queue[_IndexStreamItem] = Queue()

        def record_progress(event: IndexProgressEvent) -> None:
            items.put({"type": "index_progress", **event.to_dict()})

        self._begin_operation("build_index")

        def build() -> None:
            try:
                summary = self.runtime.build_index(progress=record_progress)
            except BaseException as exc:
                items.put(_IndexStreamDone(error=exc))
            else:
                items.put(
                    _IndexStreamDone(
                        payload={"type": "index_complete", "index": summary.to_dict()}
                    )
                )

        thread = threading.Thread(target=build, name="heph-sdk-build-index")
        try:
            thread.start()
        except BaseException:
            self._end_operation("build_index")
            raise
        try:
            while True:
                item = items.get()
                if isinstance(item, _IndexStreamDone):
                    if item.error is not None:
                        raise item.error
                    if item.payload is not None:
                        yield item.payload
                    return
                yield item
        finally:
            try:
                thread.join()
            finally:
                self._end_operation("build_index")

    def scan_extraction_health(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"health": self.runtime.scan_extraction_health().to_dict()}

    def prompt_is_active(self) -> bool:
        with self._prompt_lock:
            return self._prompt_is_active_locked()

    def _service_state(self) -> HephSdkServiceState:
        return HephSdkServiceState(
            prompt_active=self._prompt_is_active_locked(),
            active_operation=self._active_operation,
        )

    def _runtime_state(self) -> HephSdkRuntimeState:
        return HephSdkRuntimeState.from_runtime(self.runtime)

    def _session_state(self) -> HephSdkSessionState | None:
        if self.session is None:
            return None
        return HephSdkSessionState.from_session(self.session)

    def _session_payload(self) -> dict[str, object]:
        return {"session": self._session_dict(), "runtime": self._runtime_state().to_dict()}

    def _session_dict(self) -> dict[str, object]:
        return self._require_session().to_dict()

    def _require_session(self) -> HephSession:
        if self.session is None:
            raise HephSdkError("No active SDK session.")
        return self.session

    def _replace_runtime(self, runtime: HephRuntime) -> None:
        old_session = self.session
        self.runtime = runtime
        self.session = None
        if old_session is not None:
            old_session.dispose()

    def _replace_session(self, session: HephSession) -> None:
        old_session = self.session
        self._attach_session_stream_guard(session)
        self.session = session
        if old_session is not None and old_session is not session:
            old_session.dispose()

    def _attach_session_stream_guard(self, session: HephSession) -> None:
        def stream_guard(abort: threading.Event) -> AbstractContextManager[None]:
            return self._direct_stream_guard(session, abort)

        session._set_stream_start_guard(stream_guard)

    def _begin_prompt(self, abort: threading.Event) -> HephSession:
        with self._prompt_lock:
            if self._active_operation is not None:
                raise HephSdkBusyError()
            if self._active_prompt_abort is not None:
                raise HephSdkBusyError()
            session = self._require_session()
            if session.is_streaming:
                raise HephSdkBusyError("Session is already streaming.")
            self._active_prompt_abort = abort
            return session

    def _end_prompt(self, abort: threading.Event) -> None:
        with self._prompt_lock:
            if self._active_prompt_abort is abort:
                self._active_prompt_abort = None

    def _active_prompt_abort_event(self) -> threading.Event | None:
        with self._prompt_lock:
            return self._active_prompt_abort

    def _is_busy(self) -> bool:
        with self._prompt_lock:
            return self._is_busy_locked()

    def _begin_operation(self, name: str) -> None:
        with self._prompt_lock:
            self._ensure_idle_for_service_call()
            self._active_operation = name

    def _end_operation(self, name: str) -> None:
        with self._prompt_lock:
            if self._active_operation == name:
                self._active_operation = None

    @contextmanager
    def _direct_stream_guard(
        self,
        session: HephSession,
        abort: threading.Event,
    ) -> Iterator[None]:
        with self._prompt_lock:
            if self.session is not session:
                raise HephSdkBusyError("SDK session is no longer active.")
            if self._active_operation is not None:
                raise HephSdkBusyError()
            active_abort = self._active_prompt_abort
            if active_abort is not None and active_abort is not abort:
                raise HephSdkBusyError()
            yield

    @contextmanager
    def _idle_service_call(self) -> Iterator[None]:
        with self._prompt_lock:
            self._ensure_idle_for_service_call()
            yield

    def _ensure_idle_for_service_call(self) -> None:
        if self._is_busy_locked():
            raise HephSdkBusyError()

    def _is_busy_locked(self) -> bool:
        return self._active_operation is not None or self._prompt_is_active_locked()

    def _prompt_is_active_locked(self) -> bool:
        if self._active_prompt_abort is not None:
            return True
        return self.session is not None and self.session.is_streaming


def _required_str(params: Mapping[str, object], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HephSdkError(f"SDK service parameter '{key}' must be a non-empty string.")
    return value


def _required_bool(params: Mapping[str, object], key: str) -> bool:
    value = params.get(key)
    if not isinstance(value, bool):
        raise HephSdkError(f"SDK service parameter '{key}' must be a boolean.")
    return value


def _optional_str(params: Mapping[str, object], key: str) -> str | None:
    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HephSdkError(f"SDK service parameter '{key}' must be a string.")
    return value


def _optional_int(params: Mapping[str, object], key: str) -> int | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise HephSdkError(f"SDK service parameter '{key}' must be an integer.")
    return value


def _optional_float(params: Mapping[str, object], key: str) -> float | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return min(2.0, max(0.0, float(value)))
    raise HephSdkError(f"SDK service parameter '{key}' must be a number or null.")


__all__ = [
    "HephSdkRuntimeState",
    "HephSdkServiceState",
    "HephSdkSessionState",
    "HephSdkState",
    "HephService",
    "ServicePayload",
    "ServiceStream",
]
