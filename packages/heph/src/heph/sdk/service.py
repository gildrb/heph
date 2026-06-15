"""Stateful service facade for transport adapters."""

from __future__ import annotations

import threading
from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from ai.runtime import ChatConfig, normalize_thinking_visibility

from heph.sdk.capabilities import get_sdk_capabilities, validate_sdk_capabilities
from heph.sdk.config import apply_sdk_config_updates
from heph.sdk.events import event_to_dict
from heph.sdk.materials import IndexProgressEvent
from heph.sdk.method_validation import (
    validate_method_params,
    validate_result_payload,
    validate_stream_event_payload,
)
from heph.sdk.methods import (
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_RESULT_SPECS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_SPECS,
)
from heph.sdk.operation_stream import OperationStreamPublish, iter_operation_stream
from heph.sdk.runtime import (
    HephRuntime,
    HephSdkBusyError,
    HephSdkError,
    HephSession,
)
from heph.sdk.service_availability import (
    _available_call_methods,
    _available_stream_methods,
    _call_method_availability,
    _call_route_availability,
    _ensure_route_available,
    _stream_method_availability,
    _stream_route_availability,
)
from heph.sdk.service_contract import validate_sdk_service_contract
from heph.sdk.service_routes import (
    ServicePayload,
    ServiceStream,
    _call_routes_by_method,
    _config_updates_from_params,
    _service_call_route_sequence,
    _service_stream_route_sequence,
    _ServiceCallRoute,
    _ServiceStreamRoute,
    _stream_routes_by_method,
)
from heph.sdk.settings import (
    SdkAppSettings,
    SdkSettingsError,
    load_sdk_app_settings,
    update_sdk_app_settings,
)
from heph.sdk.state import (
    HephSdkRuntimeState,
    HephSdkServiceState,
    HephSdkSessionState,
    HephSdkState,
)


@dataclass(slots=True)
class _PromptTextCollector:
    chunks: list[str] = field(default_factory=list)
    full_text: str = ""

    @property
    def text(self) -> str:
        return self.full_text or "".join(self.chunks)

    def record(self, event: Mapping[str, object]) -> None:
        event_type = event.get("type")
        if event_type == "assistant_delta":
            self._record_delta(event)
        elif event_type == "turn_complete":
            self._record_completion(event)

    def _record_delta(self, event: Mapping[str, object]) -> None:
        delta = event.get("delta")
        if isinstance(delta, str):
            self.chunks.append(delta)

    def _record_completion(self, event: Mapping[str, object]) -> None:
        complete_text = event.get("full_text")
        if isinstance(complete_text, str):
            self.full_text = complete_text


@dataclass(slots=True)
class HephService:
    """JSON-ready state facade for native clients and future RPC adapters."""

    runtime: HephRuntime
    session: HephSession | None = None
    _prompt_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _active_prompt_abort: threading.Event | None = field(default=None, init=False, repr=False)
    _active_operation: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        capability_issues = validate_sdk_capabilities()
        if capability_issues:
            message = "SDK capability contract drift: " + "; ".join(capability_issues)
            raise HephSdkError(message)
        issues = validate_sdk_service_contract(self)
        if issues:
            message = "SDK service contract drift: " + "; ".join(issues)
            raise HephSdkError(message)
        if self.session is not None:
            self._attach_session_stream_guard(self.session)
            self._apply_current_app_settings()

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
        return validate_result_payload(
            "state",
            self.state_snapshot().to_dict(),
            SERVICE_CALL_RESULT_SPECS,
        )

    def validate_call_params(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        return validate_method_params(method, params, SERVICE_CALL_METHOD_SPECS)

    def validate_stream_params(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        return validate_method_params(method, params, SERVICE_STREAM_METHOD_SPECS)

    def call(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServicePayload:
        parameters = self.validate_call_params(method, params)
        if route := self._call_routes().get(method):
            self._ensure_call_route_available(route)
            return validate_result_payload(
                method,
                route.dispatch(parameters),
                SERVICE_CALL_RESULT_SPECS,
            )
        raise HephSdkError(f"Unknown SDK service method: {method}")

    def _call_routes(self) -> dict[str, _ServiceCallRoute]:
        return _call_routes_by_method(self._call_route_sequence())

    def _call_route_sequence(self) -> tuple[_ServiceCallRoute, ...]:
        return _service_call_route_sequence(self)

    def capabilities(self) -> ServicePayload:
        return validate_result_payload(
            "capabilities",
            {"capabilities": get_sdk_capabilities().to_dict()},
            SERVICE_CALL_RESULT_SPECS,
        )

    def settings(self) -> ServicePayload:
        return validate_result_payload(
            "settings",
            {"settings": load_sdk_app_settings().to_dict()},
            SERVICE_CALL_RESULT_SPECS,
        )

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServiceStream:
        parameters = self.validate_stream_params(method, params)
        if route := self._stream_routes().get(method):
            self._ensure_stream_route_available(route)
            yield from self._validated_stream(method, route.dispatch(parameters))
            return
        raise HephSdkError(f"Unknown SDK service stream method: {method}")

    def ensure_call_available(self, method: str) -> None:
        if route := self._call_routes().get(method):
            self._ensure_call_route_available(route)
            return
        raise HephSdkError(f"Unknown SDK service method: {method}")

    def ensure_stream_available(self, method: str) -> None:
        if route := self._stream_routes().get(method):
            self._ensure_stream_route_available(route)
            return
        raise HephSdkError(f"Unknown SDK service stream method: {method}")

    def _ensure_call_route_available(self, route: _ServiceCallRoute) -> None:
        with self._prompt_lock:
            availability = _call_route_availability(
                route,
                self.runtime,
                self.session,
                is_busy=self._is_busy_locked(),
            )
        _ensure_route_available(
            route.method,
            availability,
            kind="SDK service call",
        )

    def _ensure_stream_route_available(self, route: _ServiceStreamRoute) -> None:
        with self._prompt_lock:
            availability = _stream_route_availability(
                route,
                self.runtime,
                self.session,
                is_busy=self._is_busy_locked(),
            )
        _ensure_route_available(
            route.method,
            availability,
            kind="SDK service stream",
        )

    def _stream_routes(self) -> dict[str, _ServiceStreamRoute]:
        return _stream_routes_by_method(self._stream_route_sequence())

    def _stream_route_sequence(self) -> tuple[_ServiceStreamRoute, ...]:
        return _service_stream_route_sequence(self)

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

    def validate_armory(self, path: str | Path) -> dict[str, object]:
        with self._idle_service_call():
            return {"armory": HephRuntime.validate_armory(path).to_dict()}

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
                yield self._validated_stream_event("prompt", event_to_dict(event))
        finally:
            self._end_prompt(active_abort)

    def ask(self, text: str) -> dict[str, object]:
        reply = _PromptTextCollector()
        for event in self.prompt(text):
            reply.record(event)
        return {"text": reply.text, "session": self._session_dict()}

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

    def list_providers(self) -> dict[str, object]:
        with self._idle_service_call():
            if self.session is None:
                providers = self.runtime.list_providers()
            else:
                providers = self.session.list_providers()
        return {"providers": [provider.to_dict() for provider in providers]}

    def list_model_choices(self, *, refresh_live: bool = False) -> dict[str, object]:
        with self._idle_service_call():
            if self.session is None:
                models = self.runtime.list_model_choices(refresh_live=refresh_live)
            else:
                models = self.session.list_model_choices(refresh_live=refresh_live)
        return {"models": [model.to_dict() for model in models]}

    def switch_model(self, provider_slug: str, model: str) -> dict[str, object]:
        with self._idle_service_call():
            if self.session is None:
                changed = self.runtime.switch_model(provider_slug, model)
            else:
                changed = self.session.switch_model(provider_slug, model)
                if changed:
                    self.runtime.config = self.session._session.config
            session = self.session.to_dict() if self.session is not None else None
            runtime = self._runtime_state().to_dict()
        return {"changed": changed, "runtime": runtime, "session": session}

    def set_source_enabled(self, source: str, enabled: bool) -> dict[str, object]:
        with self._idle_service_call():
            changed = self._require_session().set_source_enabled(source, enabled)
            return {"changed": changed, "session": self._session_dict()}

    def update_config(self, params: Mapping[str, object]) -> dict[str, object]:
        with self._idle_service_call():
            apply_sdk_config_updates(self.runtime.config, _config_updates_from_params(params))
        return {"runtime": self._runtime_state().to_dict()}

    def update_settings(self, params: Mapping[str, object]) -> dict[str, object]:
        with self._idle_service_call():
            try:
                settings = update_sdk_app_settings(params)
            except SdkSettingsError as exc:
                raise HephSdkError(str(exc)) from exc
            self._apply_app_settings(settings)
            session = self.session.to_dict() if self.session is not None else None
            runtime = self._runtime_state().to_dict()
        return {"settings": settings.to_dict(), "runtime": runtime, "session": session}

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
        def build(publish: OperationStreamPublish) -> ServicePayload:
            def record_progress(event: IndexProgressEvent) -> None:
                publish({"type": "index_progress", **event.to_dict()})

            summary = self.runtime.build_index(progress=record_progress)
            return {"type": "index_complete", "index": summary.to_dict()}

        self.ensure_stream_available("build_index")
        self._begin_operation("build_index")
        try:
            yield from self._validated_stream(
                "build_index",
                iter_operation_stream(thread_name="heph-sdk-build-index", worker=build),
            )
        finally:
            self._end_operation("build_index")

    def _validated_stream(
        self,
        method: str,
        events: Iterator[dict[str, object]],
    ) -> Iterator[dict[str, object]]:
        for event in events:
            yield self._validated_stream_event(method, event)

    def _validated_stream_event(
        self,
        method: str,
        event: dict[str, object],
    ) -> dict[str, object]:
        return validate_stream_event_payload(
            method,
            event,
            SERVICE_STREAM_SPECS,
            surface="SDK service",
        )

    def scan_extraction_health(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"health": self.runtime.scan_extraction_health().to_dict()}

    def prompt_is_active(self) -> bool:
        with self._prompt_lock:
            return self._prompt_is_active_locked()

    def _service_state(self) -> HephSdkServiceState:
        prompt_active = self._prompt_is_active_locked()
        is_busy = self._active_operation is not None or prompt_active
        call_routes = self._call_routes()
        stream_routes = self._stream_routes()
        return HephSdkServiceState(
            prompt_active=prompt_active,
            active_operation=self._active_operation,
            is_busy=is_busy,
            available_call_methods=_available_call_methods(
                call_routes,
                self.runtime,
                self.session,
                is_busy=is_busy,
            ),
            available_stream_methods=_available_stream_methods(
                stream_routes,
                self.runtime,
                self.session,
                is_busy=is_busy,
            ),
            call_method_availability=_call_method_availability(
                call_routes,
                self.runtime,
                self.session,
                is_busy=is_busy,
            )
            if not is_busy
            else None,
            stream_method_availability=_stream_method_availability(
                stream_routes,
                self.runtime,
                self.session,
                is_busy=is_busy,
            )
            if not is_busy
            else None,
        )

    def _runtime_state(self) -> HephSdkRuntimeState:
        return HephSdkRuntimeState.from_runtime(self.runtime)

    def _session_state(self) -> HephSdkSessionState | None:
        if self.session is None:
            return None
        return HephSdkSessionState.from_session(self.session)

    def _apply_app_settings(self, settings: SdkAppSettings) -> None:
        self.runtime.config.thinking_visibility = normalize_thinking_visibility(
            settings.thinking_visibility
        )
        if self.session is not None:
            self.session.apply_display_settings(settings)

    def _apply_current_app_settings(self) -> None:
        self._apply_app_settings(load_sdk_app_settings())

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
        self._apply_current_app_settings()
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


__all__ = [
    "HephSdkRuntimeState",
    "HephSdkServiceState",
    "HephSdkSessionState",
    "HephSdkState",
    "HephService",
    "ServicePayload",
    "ServiceStream",
    "validate_sdk_service_contract",
]
