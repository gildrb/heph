"""Stateful service facade for transport adapters."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from ai.runtime import ChatConfig, normalize_thinking_visibility

from heph.sdk.capabilities import get_sdk_capabilities
from heph.sdk.config import (
    SdkConfigUpdate,
    SdkConfigUpdateName,
    SdkConfigUpdateValue,
    apply_sdk_config_updates,
)
from heph.sdk.events import event_to_dict
from heph.sdk.materials import IndexProgressEvent
from heph.sdk.method_validation import validate_method_params
from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_METHODS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_METHODS,
)
from heph.sdk.operation_stream import OperationStreamPublish, iter_operation_stream
from heph.sdk.runtime import (
    HephRuntime,
    HephSdkBusyError,
    HephSdkError,
    HephSdkUnavailableError,
    HephSession,
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

type ServicePayload = dict[str, object]
type ServiceStream = Iterator[ServicePayload]
type _ServiceCallArgumentDecoder = Callable[[Mapping[str, object], str], object]
type _ServiceCallHandler = Callable[..., ServicePayload]
type _ServiceStreamHandler = Callable[[dict[str, object]], ServiceStream]
type _ServiceConfigParamDecoder = Callable[
    [Mapping[str, object], str],
    SdkConfigUpdateValue | None,
]


class _ServiceAvailabilityRequirement(Enum):
    ALWAYS = auto()
    ARMORY = auto()
    SESSION = auto()
    ARMORY_SESSION = auto()
    SESSION_SOURCES = auto()


@dataclass(frozen=True, slots=True)
class _ServiceCallArgument:
    name: str
    decoder: _ServiceCallArgumentDecoder

    def value_from(self, params: Mapping[str, object]) -> object:
        return self.decoder(params, self.name)


@dataclass(frozen=True, slots=True)
class _ServiceCallRoute:
    method: str
    handler: _ServiceCallHandler
    arguments: tuple[_ServiceCallArgument, ...] = ()
    keyword_arguments: tuple[_ServiceCallArgument, ...] = ()
    params_as_argument: bool = False
    availability: _ServiceAvailabilityRequirement = _ServiceAvailabilityRequirement.ALWAYS

    def dispatch(self, params: Mapping[str, object]) -> ServicePayload:
        if self.params_as_argument:
            return self.handler(params)
        keywords = {
            argument.name: argument.value_from(params) for argument in self.keyword_arguments
        }
        return self.handler(
            *(argument.value_from(params) for argument in self.arguments),
            **keywords,
        )


@dataclass(frozen=True, slots=True)
class _ServiceStreamRoute:
    method: str
    handler: _ServiceStreamHandler
    availability: _ServiceAvailabilityRequirement

    def dispatch(self, params: dict[str, object]) -> ServiceStream:
        return self.handler(params)


@dataclass(frozen=True, slots=True)
class _ServiceConfigParam:
    name: SdkConfigUpdateName
    decoder: _ServiceConfigParamDecoder
    keep_none: bool = False

    def update_from(self, params: Mapping[str, object]) -> SdkConfigUpdate | None:
        if self.name not in params:
            return None
        value = self.decoder(params, self.name)
        if value is None and not self.keep_none:
            return None
        return SdkConfigUpdate(self.name, value)


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
        return self.state_snapshot().to_dict()

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
            return route.dispatch(parameters)
        raise HephSdkError(f"Unknown SDK service method: {method}")

    def _call_routes(self) -> dict[str, _ServiceCallRoute]:
        routes = (
            _ServiceCallRoute("state", self.state),
            _ServiceCallRoute("capabilities", self.capabilities),
            _ServiceCallRoute("use_plain_runtime", self.use_plain_runtime),
            _ServiceCallRoute(
                "open_armory",
                self.open_runtime_armory,
                (_ServiceCallArgument("path", _required_str),),
            ),
            _ServiceCallRoute(
                "create_armory",
                self.create_runtime_armory,
                (_ServiceCallArgument("path", _required_str),),
            ),
            _ServiceCallRoute("list_armories", self.list_armories),
            _ServiceCallRoute(
                "validate_armory",
                self.validate_armory,
                (_ServiceCallArgument("path", _required_str),),
            ),
            _ServiceCallRoute("new_session", self.new_session),
            _ServiceCallRoute(
                "resume_session",
                self.resume_session,
                (_ServiceCallArgument("session_id", _required_str),),
                availability=_ServiceAvailabilityRequirement.ARMORY,
            ),
            _ServiceCallRoute(
                "fork_session",
                self.fork_session,
                (_ServiceCallArgument("turn_id", _required_str),),
                availability=_ServiceAvailabilityRequirement.SESSION,
            ),
            _ServiceCallRoute("list_sessions", self.list_sessions),
            _ServiceCallRoute(
                "save_session",
                self.save_session,
                availability=_ServiceAvailabilityRequirement.ARMORY_SESSION,
            ),
            _ServiceCallRoute(
                "messages",
                self.messages,
                availability=_ServiceAvailabilityRequirement.SESSION,
            ),
            _ServiceCallRoute(
                "ask",
                self.ask,
                (_ServiceCallArgument("text", _required_str),),
                availability=_ServiceAvailabilityRequirement.SESSION,
            ),
            _ServiceCallRoute(
                "abort",
                self.abort,
                availability=_ServiceAvailabilityRequirement.SESSION,
            ),
            _ServiceCallRoute("settings", self.settings),
            _ServiceCallRoute("list_providers", self.list_providers),
            _ServiceCallRoute(
                "list_model_choices",
                self.list_model_choices,
                keyword_arguments=(
                    _ServiceCallArgument("refresh_live", _optional_bool_default_false),
                ),
            ),
            _ServiceCallRoute(
                "switch_model",
                self.switch_model,
                (
                    _ServiceCallArgument("provider_slug", _required_str),
                    _ServiceCallArgument("model", _required_str),
                ),
            ),
            _ServiceCallRoute(
                "set_source_enabled",
                self.set_source_enabled,
                (
                    _ServiceCallArgument("source", _required_str),
                    _ServiceCallArgument("enabled", _required_bool),
                ),
                availability=_ServiceAvailabilityRequirement.SESSION_SOURCES,
            ),
            _ServiceCallRoute(
                "list_materials",
                self.list_materials,
                availability=_ServiceAvailabilityRequirement.ARMORY,
            ),
            _ServiceCallRoute(
                "import_materials",
                self.import_materials,
                (_ServiceCallArgument("source", _required_str),),
                availability=_ServiceAvailabilityRequirement.ARMORY,
            ),
            _ServiceCallRoute(
                "build_index",
                self.build_index,
                availability=_ServiceAvailabilityRequirement.ARMORY,
            ),
            _ServiceCallRoute(
                "scan_extraction_health",
                self.scan_extraction_health,
                availability=_ServiceAvailabilityRequirement.ARMORY,
            ),
            _ServiceCallRoute("update_config", self.update_config, params_as_argument=True),
            _ServiceCallRoute("update_settings", self.update_settings, params_as_argument=True),
        )
        return {route.method: route for route in routes}

    def capabilities(self) -> ServicePayload:
        return {"capabilities": get_sdk_capabilities().to_dict()}

    def settings(self) -> ServicePayload:
        return {"settings": load_sdk_app_settings().to_dict()}

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServiceStream:
        parameters = self.validate_stream_params(method, params)
        if route := self._stream_routes().get(method):
            self._ensure_stream_route_available(route)
            yield from route.dispatch(parameters)
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
            is_busy = self._is_busy_locked()
            if is_busy:
                if route.method not in BUSY_ALLOWED_CALL_METHODS:
                    raise HephSdkBusyError()
                return
            is_available = _route_is_available(route, self.runtime, self.session)
        if not is_available:
            raise HephSdkUnavailableError(route.method, kind="SDK service call")

    def _ensure_stream_route_available(self, route: _ServiceStreamRoute) -> None:
        with self._prompt_lock:
            if self._is_busy_locked():
                raise HephSdkBusyError()
            is_available = _route_is_available(route, self.runtime, self.session)
        if not is_available:
            raise HephSdkUnavailableError(route.method, kind="SDK service stream")

    def _stream_routes(self) -> dict[str, _ServiceStreamRoute]:
        routes = (
            _ServiceStreamRoute(
                "prompt",
                self._prompt_stream,
                _ServiceAvailabilityRequirement.SESSION,
            ),
            _ServiceStreamRoute(
                "build_index",
                self._build_index_stream,
                _ServiceAvailabilityRequirement.ARMORY,
            ),
        )
        return {route.method: route for route in routes}

    def _prompt_stream(self, params: dict[str, object]) -> ServiceStream:
        return self.prompt(_required_str(params, "text"))

    def _build_index_stream(self, params: dict[str, object]) -> ServiceStream:
        _ = params
        return self.build_index_stream()

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
                yield event_to_dict(event)
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
            yield from iter_operation_stream(thread_name="heph-sdk-build-index", worker=build)
        finally:
            self._end_operation("build_index")

    def scan_extraction_health(self) -> dict[str, object]:
        with self._idle_service_call():
            return {"health": self.runtime.scan_extraction_health().to_dict()}

    def prompt_is_active(self) -> bool:
        with self._prompt_lock:
            return self._prompt_is_active_locked()

    def _service_state(self) -> HephSdkServiceState:
        prompt_active = self._prompt_is_active_locked()
        is_busy = self._active_operation is not None or prompt_active
        return HephSdkServiceState(
            prompt_active=prompt_active,
            active_operation=self._active_operation,
            is_busy=is_busy,
            available_call_methods=_available_call_methods(
                self._call_routes(),
                self.runtime,
                self.session,
                is_busy=is_busy,
            ),
            available_stream_methods=_available_stream_methods(
                self._stream_routes(),
                self.runtime,
                self.session,
                is_busy=is_busy,
            ),
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


type _AvailableRoute = _ServiceCallRoute | _ServiceStreamRoute


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
        and _route_is_available(route, runtime, session)
    )


def _available_stream_methods(
    routes: Mapping[str, _ServiceStreamRoute],
    runtime: HephRuntime,
    session: HephSession | None,
    *,
    is_busy: bool,
) -> tuple[str, ...]:
    if is_busy:
        return ()

    return tuple(
        method
        for method in SERVICE_STREAM_METHODS
        if (route := routes.get(method)) is not None
        and _route_is_available(route, runtime, session)
    )


def _route_is_available(
    route: _AvailableRoute,
    runtime: HephRuntime,
    session: HephSession | None,
) -> bool:
    match route.availability:
        case _ServiceAvailabilityRequirement.ALWAYS:
            return True
        case _ServiceAvailabilityRequirement.ARMORY:
            return runtime.armory_path is not None
        case _ServiceAvailabilityRequirement.SESSION:
            return session is not None
        case _ServiceAvailabilityRequirement.ARMORY_SESSION:
            return session is not None and session.armory_path is not None
        case _ServiceAvailabilityRequirement.SESSION_SOURCES:
            return session is not None and bool(session.source_files)


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
    _ServiceConfigParam("base_url", _optional_str),
    _ServiceConfigParam("model", _optional_str),
    _ServiceConfigParam("max_tokens", _optional_int),
    _ServiceConfigParam("rag_context_budget", _optional_int),
    _ServiceConfigParam("temperature", _optional_float, keep_none=True),
    _ServiceConfigParam("reasoning_level", _optional_str),
    _ServiceConfigParam("thinking_visibility", _optional_str),
)


__all__ = [
    "HephSdkRuntimeState",
    "HephSdkServiceState",
    "HephSdkSessionState",
    "HephSdkState",
    "HephService",
    "ServicePayload",
    "ServiceStream",
]
