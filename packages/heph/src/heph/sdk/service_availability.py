"""Availability policy for SDK service routes."""

from __future__ import annotations

from collections.abc import Callable, Mapping

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
    SERVICE_CALL_METHODS,
    SERVICE_STREAM_METHOD_AVAILABILITY_SPECS,
    SERVICE_STREAM_METHODS,
    SdkMethodAvailabilitySpec,
)
from heph.sdk.runtime import (
    HephRuntime,
    HephSdkBusyError,
    HephSdkUnavailableError,
    HephSession,
)
from heph.sdk.service_routes import (
    _RouteAvailability,
    _ServiceCallRoute,
    _ServiceStreamRoute,
)
from heph.sdk.state import HephSdkMethodAvailability

type _MethodAvailabilitySpecsByMethod = Mapping[str, SdkMethodAvailabilitySpec]
type _AvailabilityCheck = Callable[[HephRuntime, HephSession | None], bool]


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


def _availability_specs_by_method(
    specs: tuple[SdkMethodAvailabilitySpec, ...],
) -> dict[str, SdkMethodAvailabilitySpec]:
    return {spec.method: spec for spec in specs}


_AVAILABILITY_CHECKS_BY_REQUIREMENT: dict[str, _AvailabilityCheck] = {
    SDK_METHOD_REQUIREMENT_ALWAYS: _runtime_is_always_available,
    SDK_METHOD_REQUIREMENT_ARMORY: _runtime_has_armory,
    SDK_METHOD_REQUIREMENT_SESSION: _session_is_active,
    SDK_METHOD_REQUIREMENT_ARMORY_SESSION: _session_has_armory,
    SDK_METHOD_REQUIREMENT_SESSION_SOURCES: _session_has_sources,
}
_SERVICE_CALL_AVAILABILITY_SPECS_BY_METHOD: _MethodAvailabilitySpecsByMethod = (
    _availability_specs_by_method(SERVICE_CALL_METHOD_AVAILABILITY_SPECS)
)
_SERVICE_STREAM_AVAILABILITY_SPECS_BY_METHOD: _MethodAvailabilitySpecsByMethod = (
    _availability_specs_by_method(SERVICE_STREAM_METHOD_AVAILABILITY_SPECS)
)
