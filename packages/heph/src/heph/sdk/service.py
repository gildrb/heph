"""Stateful service facade for transport adapters."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from ai.providers.reasoning import REASONING_LEVELS
from ai.runtime import ChatConfig, normalize_thinking_visibility
from ai.runtime.thinking import THINKING_VISIBILITY_MODES

from heph.sdk.capabilities import get_sdk_capabilities, validate_sdk_capabilities
from heph.sdk.config import SdkConfigUpdate, apply_sdk_config_updates
from heph.sdk.events import event_to_dict
from heph.sdk.materials import IndexProgressEvent
from heph.sdk.method_validation import (
    validate_method_params,
    validate_result_payload,
    validate_stream_event_payload,
)
from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    SDK_METHOD_REQUIREMENT_ALWAYS,
    SDK_METHOD_REQUIREMENT_ARMORY,
    SDK_METHOD_REQUIREMENT_ARMORY_SESSION,
    SDK_METHOD_REQUIREMENT_SESSION,
    SDK_METHOD_REQUIREMENT_SESSION_SOURCES,
    SDK_METHOD_UNAVAILABLE_BUSY,
    SDK_METHOD_UNAVAILABLE_GENERIC,
    SERVICE_CALL_METHOD_AVAILABILITY_SPECS,
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_METHODS,
    SERVICE_CALL_RESULT_SPECS,
    SERVICE_STREAM_METHOD_AVAILABILITY_SPECS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_METHODS,
    SERVICE_STREAM_SPECS,
    SdkMethodAvailabilitySpec,
    SdkMethodParameter,
    SdkMethodSpec,
)
from heph.sdk.operation_stream import OperationStreamPublish, iter_operation_stream
from heph.sdk.runtime import (
    HephRuntime,
    HephSdkBusyError,
    HephSdkError,
    HephSdkUnavailableError,
    HephSession,
)
from heph.sdk.service_routes import (
    ServicePayload,
    ServiceStream,
    _RouteAvailability,
    _ServiceCallArgument,
    _ServiceCallRoute,
    _ServiceConfigParam,
    _ServiceStreamRoute,
)
from heph.sdk.settings import (
    SDK_APP_SETTING_CONTRACTS,
    SdkAppSettings,
    SdkSettingsError,
    load_sdk_app_settings,
    update_sdk_app_settings,
)
from heph.sdk.state import (
    HephSdkMethodAvailability,
    HephSdkRuntimeState,
    HephSdkServiceState,
    HephSdkSessionState,
    HephSdkState,
)

type _MethodAvailabilitySpecsByMethod = Mapping[str, SdkMethodAvailabilitySpec]
type _AvailabilityCheck = Callable[[HephRuntime, HephSession | None], bool]


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
        return (
            _ServiceCallRoute("state", self.state),
            _ServiceCallRoute("capabilities", self.capabilities),
            _ServiceCallRoute("use_plain_runtime", self.use_plain_runtime),
            _ServiceCallRoute(
                "open_armory",
                self.open_runtime_armory,
                (_ServiceCallArgument("path", _required_str, "string"),),
            ),
            _ServiceCallRoute(
                "create_armory",
                self.create_runtime_armory,
                (_ServiceCallArgument("path", _required_str, "string"),),
            ),
            _ServiceCallRoute("list_armories", self.list_armories),
            _ServiceCallRoute(
                "validate_armory",
                self.validate_armory,
                (_ServiceCallArgument("path", _required_str, "string"),),
            ),
            _ServiceCallRoute("new_session", self.new_session),
            _ServiceCallRoute(
                "resume_session",
                self.resume_session,
                (_ServiceCallArgument("session_id", _required_str, "string"),),
            ),
            _ServiceCallRoute(
                "fork_session",
                self.fork_session,
                (_ServiceCallArgument("turn_id", _required_str, "string"),),
            ),
            _ServiceCallRoute("list_sessions", self.list_sessions),
            _ServiceCallRoute(
                "save_session",
                self.save_session,
            ),
            _ServiceCallRoute(
                "messages",
                self.messages,
            ),
            _ServiceCallRoute(
                "ask",
                self.ask,
                (_ServiceCallArgument("text", _required_str, "string"),),
            ),
            _ServiceCallRoute(
                "abort",
                self.abort,
            ),
            _ServiceCallRoute("settings", self.settings),
            _ServiceCallRoute("list_providers", self.list_providers),
            _ServiceCallRoute(
                "list_model_choices",
                self.list_model_choices,
                keyword_arguments=(
                    _ServiceCallArgument(
                        "refresh_live",
                        _optional_bool_default_false,
                        "boolean",
                        required=False,
                    ),
                ),
            ),
            _ServiceCallRoute(
                "switch_model",
                self.switch_model,
                (
                    _ServiceCallArgument("provider_slug", _required_str, "string"),
                    _ServiceCallArgument("model", _required_str, "string"),
                ),
            ),
            _ServiceCallRoute(
                "set_source_enabled",
                self.set_source_enabled,
                (
                    _ServiceCallArgument("source", _required_str, "string"),
                    _ServiceCallArgument("enabled", _required_bool, "boolean"),
                ),
            ),
            _ServiceCallRoute(
                "list_materials",
                self.list_materials,
            ),
            _ServiceCallRoute(
                "import_materials",
                self.import_materials,
                (_ServiceCallArgument("source", _required_str, "string"),),
            ),
            _ServiceCallRoute(
                "build_index",
                self.build_index,
            ),
            _ServiceCallRoute(
                "scan_extraction_health",
                self.scan_extraction_health,
            ),
            _ServiceCallRoute(
                "update_config",
                self.update_config,
                params_as_argument=True,
                parameter_contracts=_config_param_contracts(),
            ),
            _ServiceCallRoute(
                "update_settings",
                self.update_settings,
                params_as_argument=True,
                parameter_contracts=_app_setting_param_contracts(),
            ),
        )

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
        return (
            _ServiceStreamRoute(
                "prompt",
                self.prompt,
                (_ServiceCallArgument("text", _required_str, "string"),),
            ),
            _ServiceStreamRoute(
                "build_index",
                self.build_index_stream,
            ),
        )

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


def validate_sdk_service_contract(service: HephService) -> tuple[str, ...]:
    """Return implementation drift between service routes and advertised SDK specs."""
    call_routes = service._call_route_sequence()
    stream_routes = service._stream_route_sequence()
    issues: list[str] = []
    _append_route_name_issues(
        issues,
        "service.call_routes",
        SERVICE_CALL_METHODS,
        tuple(route.method for route in call_routes),
    )
    _append_route_name_issues(
        issues,
        "service.stream_routes",
        SERVICE_STREAM_METHODS,
        tuple(route.method for route in stream_routes),
    )
    _append_call_route_parameter_issues(issues, call_routes)
    _append_stream_route_parameter_issues(issues, stream_routes)
    return tuple(issues)


def _call_routes_by_method(
    routes: tuple[_ServiceCallRoute, ...],
) -> dict[str, _ServiceCallRoute]:
    return {route.method: route for route in routes}


def _stream_routes_by_method(
    routes: tuple[_ServiceStreamRoute, ...],
) -> dict[str, _ServiceStreamRoute]:
    return {route.method: route for route in routes}


def _append_route_name_issues(
    issues: list[str],
    label: str,
    advertised: tuple[str, ...],
    implemented: tuple[str, ...],
) -> None:
    duplicates = _duplicate_names(implemented)
    if duplicates:
        issues.append(f"{label} contains duplicate routes: {', '.join(duplicates)}")
    if implemented != advertised:
        issues.append(f"{label} does not match advertised SDK methods.")


def _append_call_route_parameter_issues(
    issues: list[str],
    routes: tuple[_ServiceCallRoute, ...],
) -> None:
    specs = _method_specs_by_method(SERVICE_CALL_METHOD_SPECS)
    for route in routes:
        spec = specs.get(route.method)
        if spec is None:
            continue
        _append_route_parameter_issue(
            issues,
            f"service.call_routes.{route.method}",
            _method_spec_param_contracts(spec),
            _call_route_param_contracts(route),
            "advertised SDK method params",
        )


def _append_stream_route_parameter_issues(
    issues: list[str],
    routes: tuple[_ServiceStreamRoute, ...],
) -> None:
    specs = _method_specs_by_method(SERVICE_STREAM_METHOD_SPECS)
    for route in routes:
        spec = specs.get(route.method)
        if spec is None:
            continue
        _append_route_parameter_issue(
            issues,
            f"service.stream_routes.{route.method}",
            _method_spec_param_contracts(spec),
            _stream_route_param_contracts(route),
            "advertised SDK stream params",
        )


def _append_route_parameter_issue(
    issues: list[str],
    label: str,
    expected: tuple[SdkMethodParameter, ...],
    implemented: tuple[SdkMethodParameter, ...],
    advertised_label: str,
) -> None:
    if implemented != expected:
        issues.append(f"{label} params do not match {advertised_label}.")


def _method_specs_by_method(specs: tuple[SdkMethodSpec, ...]) -> dict[str, SdkMethodSpec]:
    return {spec.method: spec for spec in specs}


def _method_spec_param_contracts(spec: SdkMethodSpec) -> tuple[SdkMethodParameter, ...]:
    return spec.params


def _call_route_param_contracts(route: _ServiceCallRoute) -> tuple[SdkMethodParameter, ...]:
    if route.params_as_argument:
        return route.parameter_contracts
    return tuple(
        SdkMethodParameter(
            argument.name,
            argument.value_type,
            argument.required,
            argument.choices,
        )
        for argument in (*route.arguments, *route.keyword_arguments)
    )


def _stream_route_param_contracts(
    route: _ServiceStreamRoute,
) -> tuple[SdkMethodParameter, ...]:
    return tuple(
        SdkMethodParameter(
            argument.name,
            argument.value_type,
            argument.required,
            argument.choices,
        )
        for argument in route.arguments
    )


def _duplicate_names(names: tuple[str, ...]) -> tuple[str, ...]:
    counts_by_name: dict[str, int] = {}
    duplicates: list[str] = []
    for name in names:
        count = counts_by_name.get(name, 0) + 1
        counts_by_name[name] = count
        if count == 2:
            duplicates.append(name)
    return tuple(duplicates)


def _available_call_methods(
    routes: Mapping[str, _ServiceCallRoute],
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> tuple[str, ...]:
    if is_busy:
        return BUSY_ALLOWED_CALL_METHODS

    return tuple(
        method
        for method in SERVICE_CALL_METHODS
        if (route := routes.get(method)) is not None
        and _call_route_availability(route, runtime, session, is_busy=is_busy).available
    )


def _available_stream_methods(
    routes: Mapping[str, _ServiceStreamRoute],
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> tuple[str, ...]:
    return tuple(
        method
        for method in SERVICE_STREAM_METHODS
        if (route := routes.get(method)) is not None
        and _stream_route_availability(route, runtime, session, is_busy=is_busy).available
    )


def _call_method_availability(
    routes: Mapping[str, _ServiceCallRoute],
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> tuple[HephSdkMethodAvailability, ...]:
    return tuple(
        _call_route_availability(route, runtime, session, is_busy=is_busy).to_sdk(method)
        for method in SERVICE_CALL_METHODS
        if (route := routes.get(method)) is not None
    )


def _stream_method_availability(
    routes: Mapping[str, _ServiceStreamRoute],
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> tuple[HephSdkMethodAvailability, ...]:
    return tuple(
        _stream_route_availability(route, runtime, session, is_busy=is_busy).to_sdk(method)
        for method in SERVICE_STREAM_METHODS
        if (route := routes.get(method)) is not None
    )


def _call_route_availability(
    route: _ServiceCallRoute,
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> _RouteAvailability:
    if is_busy and route.method not in BUSY_ALLOWED_CALL_METHODS:
        return _unavailable_route(SDK_METHOD_UNAVAILABLE_BUSY)
    if is_busy:
        return _available_route()
    return _route_availability(
        _SERVICE_CALL_AVAILABILITY_SPECS_BY_METHOD[route.method],
        runtime,
        session,
    )


def _stream_route_availability(
    route: _ServiceStreamRoute,
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> _RouteAvailability:
    if is_busy:
        return _unavailable_route(SDK_METHOD_UNAVAILABLE_BUSY)
    return _route_availability(
        _SERVICE_STREAM_AVAILABILITY_SPECS_BY_METHOD[route.method],
        runtime,
        session,
    )


def _route_availability(
    spec: SdkMethodAvailabilitySpec,
    runtime: HephRuntime,
    session: HephSession | None,
) -> _RouteAvailability:
    check = _AVAILABILITY_CHECKS_BY_REQUIREMENT.get(spec.requirement)
    if check is None:
        return _unavailable_route(SDK_METHOD_UNAVAILABLE_GENERIC)
    return _available_when(check(runtime, session), spec)


def _ensure_route_available(
    method: str,
    availability: _RouteAvailability,
    *,
    kind: str,
) -> None:
    if availability.available:
        return
    if availability.unavailable_reason == SDK_METHOD_UNAVAILABLE_BUSY:
        raise HephSdkBusyError()
    raise HephSdkUnavailableError(
        method,
        kind=kind,
        unavailable_reason=availability.unavailable_reason,
    )


def _available_route() -> _RouteAvailability:
    return _RouteAvailability(True)


def _unavailable_route(reason: str) -> _RouteAvailability:
    return _RouteAvailability(False, reason)


def _available_when(
    available: bool,
    spec: SdkMethodAvailabilitySpec,
) -> _RouteAvailability:
    if available:
        return _available_route()
    return _unavailable_route(spec.unavailable_reason or SDK_METHOD_UNAVAILABLE_GENERIC)


def _runtime_is_always_available(
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    _ = runtime, session
    return True


def _runtime_has_armory(
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    _ = session
    return runtime.armory_path is not None


def _session_is_active(
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    _ = runtime
    return session is not None


def _session_has_armory(
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    _ = runtime
    return session is not None and session.armory_path is not None


def _session_has_sources(
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    _ = runtime
    return session is not None and bool(session.source_files)


_AVAILABILITY_CHECKS_BY_REQUIREMENT: dict[str, _AvailabilityCheck] = {
    SDK_METHOD_REQUIREMENT_ALWAYS: _runtime_is_always_available,
    SDK_METHOD_REQUIREMENT_ARMORY: _runtime_has_armory,
    SDK_METHOD_REQUIREMENT_SESSION: _session_is_active,
    SDK_METHOD_REQUIREMENT_ARMORY_SESSION: _session_has_armory,
    SDK_METHOD_REQUIREMENT_SESSION_SOURCES: _session_has_sources,
}


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


def _config_updates_from_params(params: Mapping[str, object]) -> tuple[SdkConfigUpdate, ...]:
    updates: list[SdkConfigUpdate] = []
    for config_param in _CONFIG_PARAMS:
        update = config_param.update_from(params)
        if update is not None:
            updates.append(update)
    return tuple(updates)


def _optional_str(params: Mapping[str, object], key: str) -> str | None:
    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HephSdkError(f"SDK service parameter '{key}' must be a string.")
    return value


def _optional_bool(params: Mapping[str, object], key: str) -> bool | None:
    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise HephSdkError(f"SDK service parameter '{key}' must be a boolean.")
    return value


def _optional_bool_default_false(params: Mapping[str, object], key: str) -> bool:
    value = _optional_bool(params, key)
    return value if value is not None else False


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
        return float(value)
    raise HephSdkError(f"SDK service parameter '{key}' must be a number or null.")


_CONFIG_PARAMS = (
    _ServiceConfigParam("base_url", _optional_str, "string"),
    _ServiceConfigParam("model", _optional_str, "string"),
    _ServiceConfigParam("max_tokens", _optional_int, "integer"),
    _ServiceConfigParam("rag_context_budget", _optional_int, "integer"),
    _ServiceConfigParam("temperature", _optional_float, "number_or_null", keep_none=True),
    _ServiceConfigParam("reasoning_level", _optional_str, "string", choices=REASONING_LEVELS),
    _ServiceConfigParam(
        "thinking_visibility",
        _optional_str,
        "string",
        choices=THINKING_VISIBILITY_MODES,
    ),
)


def _config_param_contracts() -> tuple[SdkMethodParameter, ...]:
    return tuple(
        SdkMethodParameter(
            param.name,
            param.value_type,
            required=False,
            choices=param.choices,
        )
        for param in _CONFIG_PARAMS
    )


def _app_setting_param_contracts() -> tuple[SdkMethodParameter, ...]:
    return tuple(
        SdkMethodParameter(
            contract.name,
            contract.value_type,
            required=False,
            choices=contract.choices,
        )
        for contract in SDK_APP_SETTING_CONTRACTS
    )


def _availability_specs_by_method(
    specs: tuple[SdkMethodAvailabilitySpec, ...],
) -> dict[str, SdkMethodAvailabilitySpec]:
    return {spec.method: spec for spec in specs}


_SERVICE_CALL_AVAILABILITY_SPECS_BY_METHOD: _MethodAvailabilitySpecsByMethod = (
    _availability_specs_by_method(SERVICE_CALL_METHOD_AVAILABILITY_SPECS)
)
_SERVICE_STREAM_AVAILABILITY_SPECS_BY_METHOD: _MethodAvailabilitySpecsByMethod = (
    _availability_specs_by_method(SERVICE_STREAM_METHOD_AVAILABILITY_SPECS)
)


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
