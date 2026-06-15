"""Route primitives for the SDK service facade."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Protocol

from ai.providers.reasoning import REASONING_LEVELS
from ai.runtime.thinking import THINKING_VISIBILITY_MODES

from heph.sdk.config import (
    SdkConfigUpdate,
    SdkConfigUpdateName,
    SdkConfigUpdateValue,
)
from heph.sdk.methods import SdkMethodParameter
from heph.sdk.runtime import HephSdkError
from heph.sdk.settings import SDK_APP_SETTING_CONTRACTS
from heph.sdk.state import HephSdkMethodAvailability

type ServicePayload = dict[str, object]
type ServiceStream = Iterator[ServicePayload]
type _ServiceCallArgumentDecoder = Callable[[Mapping[str, object], str], object]
type _ServiceCallHandler = Callable[..., ServicePayload]
type _ServiceStreamHandler = Callable[..., ServiceStream]
type _ServiceConfigParamDecoder = Callable[
    [Mapping[str, object], str],
    SdkConfigUpdateValue | None,
]


class _ServiceRouteTarget(Protocol):
    def state(self) -> ServicePayload: ...

    def capabilities(self) -> ServicePayload: ...

    def use_plain_runtime(self) -> ServicePayload: ...

    def open_runtime_armory(self, path: str) -> ServicePayload: ...

    def create_runtime_armory(self, path: str) -> ServicePayload: ...

    def list_armories(self) -> ServicePayload: ...

    def validate_armory(self, path: str) -> ServicePayload: ...

    def new_session(self) -> ServicePayload: ...

    def resume_session(self, session_id: str) -> ServicePayload: ...

    def fork_session(self, turn_id: str) -> ServicePayload: ...

    def list_sessions(self) -> ServicePayload: ...

    def save_session(self) -> ServicePayload: ...

    def messages(self) -> ServicePayload: ...

    def ask(self, text: str) -> ServicePayload: ...

    def abort(self) -> ServicePayload: ...

    def settings(self) -> ServicePayload: ...

    def list_providers(self) -> ServicePayload: ...

    def list_model_choices(self, *, refresh_live: bool = False) -> ServicePayload: ...

    def switch_model(self, provider_slug: str, model: str) -> ServicePayload: ...

    def set_source_enabled(self, source: str, enabled: bool) -> ServicePayload: ...

    def list_materials(self) -> ServicePayload: ...

    def import_materials(self, source: str) -> ServicePayload: ...

    def build_index(self) -> ServicePayload: ...

    def scan_extraction_health(self) -> ServicePayload: ...

    def update_config(self, params: Mapping[str, object]) -> ServicePayload: ...

    def update_settings(self, params: Mapping[str, object]) -> ServicePayload: ...

    def prompt(self, text: str) -> ServiceStream: ...

    def build_index_stream(self) -> ServiceStream: ...


@dataclass(frozen=True, slots=True)
class _ServiceCallArgument:
    name: str
    decoder: _ServiceCallArgumentDecoder
    value_type: str
    required: bool = True
    choices: tuple[str, ...] = ()

    def value_from(self, params: Mapping[str, object]) -> object:
        return self.decoder(params, self.name)


@dataclass(frozen=True, slots=True)
class _ServiceCallRoute:
    method: str
    handler: _ServiceCallHandler
    arguments: tuple[_ServiceCallArgument, ...] = ()
    keyword_arguments: tuple[_ServiceCallArgument, ...] = ()
    params_as_argument: bool = False
    parameter_contracts: tuple[SdkMethodParameter, ...] = ()

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
    arguments: tuple[_ServiceCallArgument, ...] = ()

    def dispatch(self, params: dict[str, object]) -> ServiceStream:
        return self.handler(*(argument.value_from(params) for argument in self.arguments))


@dataclass(frozen=True, slots=True)
class _ServiceConfigParam:
    name: SdkConfigUpdateName
    decoder: _ServiceConfigParamDecoder
    value_type: str
    choices: tuple[str, ...] = ()
    keep_none: bool = False

    def update_from(self, params: Mapping[str, object]) -> SdkConfigUpdate | None:
        if self.name not in params:
            return None
        value = self.decoder(params, self.name)
        if value is None and not self.keep_none:
            return None
        return SdkConfigUpdate(self.name, value)


@dataclass(frozen=True, slots=True)
class _RouteAvailability:
    available: bool
    unavailable_reason: str | None = None

    def to_sdk(self, method: str) -> HephSdkMethodAvailability:
        return HephSdkMethodAvailability(
            method=method,
            available=self.available,
            unavailable_reason=self.unavailable_reason,
        )


def _service_call_route_sequence(
    service: _ServiceRouteTarget,
) -> tuple[_ServiceCallRoute, ...]:
    return (
        _ServiceCallRoute("state", service.state),
        _ServiceCallRoute("capabilities", service.capabilities),
        _ServiceCallRoute("use_plain_runtime", service.use_plain_runtime),
        _ServiceCallRoute(
            "open_armory",
            service.open_runtime_armory,
            (_ServiceCallArgument("path", _required_str, "string"),),
        ),
        _ServiceCallRoute(
            "create_armory",
            service.create_runtime_armory,
            (_ServiceCallArgument("path", _required_str, "string"),),
        ),
        _ServiceCallRoute("list_armories", service.list_armories),
        _ServiceCallRoute(
            "validate_armory",
            service.validate_armory,
            (_ServiceCallArgument("path", _required_str, "string"),),
        ),
        _ServiceCallRoute("new_session", service.new_session),
        _ServiceCallRoute(
            "resume_session",
            service.resume_session,
            (_ServiceCallArgument("session_id", _required_str, "string"),),
        ),
        _ServiceCallRoute(
            "fork_session",
            service.fork_session,
            (_ServiceCallArgument("turn_id", _required_str, "string"),),
        ),
        _ServiceCallRoute("list_sessions", service.list_sessions),
        _ServiceCallRoute(
            "save_session",
            service.save_session,
        ),
        _ServiceCallRoute(
            "messages",
            service.messages,
        ),
        _ServiceCallRoute(
            "ask",
            service.ask,
            (_ServiceCallArgument("text", _required_str, "string"),),
        ),
        _ServiceCallRoute(
            "abort",
            service.abort,
        ),
        _ServiceCallRoute("settings", service.settings),
        _ServiceCallRoute("list_providers", service.list_providers),
        _ServiceCallRoute(
            "list_model_choices",
            service.list_model_choices,
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
            service.switch_model,
            (
                _ServiceCallArgument("provider_slug", _required_str, "string"),
                _ServiceCallArgument("model", _required_str, "string"),
            ),
        ),
        _ServiceCallRoute(
            "set_source_enabled",
            service.set_source_enabled,
            (
                _ServiceCallArgument("source", _required_str, "string"),
                _ServiceCallArgument("enabled", _required_bool, "boolean"),
            ),
        ),
        _ServiceCallRoute(
            "list_materials",
            service.list_materials,
        ),
        _ServiceCallRoute(
            "import_materials",
            service.import_materials,
            (_ServiceCallArgument("source", _required_str, "string"),),
        ),
        _ServiceCallRoute(
            "build_index",
            service.build_index,
        ),
        _ServiceCallRoute(
            "scan_extraction_health",
            service.scan_extraction_health,
        ),
        _ServiceCallRoute(
            "update_config",
            service.update_config,
            params_as_argument=True,
            parameter_contracts=_config_param_contracts(),
        ),
        _ServiceCallRoute(
            "update_settings",
            service.update_settings,
            params_as_argument=True,
            parameter_contracts=_app_setting_param_contracts(),
        ),
    )


def _service_stream_route_sequence(
    service: _ServiceRouteTarget,
) -> tuple[_ServiceStreamRoute, ...]:
    return (
        _ServiceStreamRoute(
            "prompt",
            service.prompt,
            (_ServiceCallArgument("text", _required_str, "string"),),
        ),
        _ServiceStreamRoute(
            "build_index",
            service.build_index_stream,
        ),
    )


def _call_routes_by_method(
    routes: tuple[_ServiceCallRoute, ...],
) -> dict[str, _ServiceCallRoute]:
    return {route.method: route for route in routes}


def _stream_routes_by_method(
    routes: tuple[_ServiceStreamRoute, ...],
) -> dict[str, _ServiceStreamRoute]:
    return {route.method: route for route in routes}


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
