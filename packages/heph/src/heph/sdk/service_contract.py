"""Contract validation for the SDK service implementation."""

from __future__ import annotations

from typing import Protocol

from heph.sdk.methods import (
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_METHODS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_METHODS,
    SdkMethodParameter,
    SdkMethodSpec,
)
from heph.sdk.service_routes import _ServiceCallRoute, _ServiceStreamRoute


class _ServiceContractRoutes(Protocol):
    def _call_route_sequence(self) -> tuple[_ServiceCallRoute, ...]: ...

    def _stream_route_sequence(self) -> tuple[_ServiceStreamRoute, ...]: ...


def validate_sdk_service_contract(service: _ServiceContractRoutes) -> tuple[str, ...]:
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
