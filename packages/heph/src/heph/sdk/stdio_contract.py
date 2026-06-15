"""JSONL transport contract validation for the SDK stdio server."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from heph.sdk.methods import (
    JSONL_CALL_METHODS,
    JSONL_STREAM_METHODS,
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_STREAM_METHOD_SPECS,
    SdkMethodParameter,
    SdkMethodSpec,
    service_stream_method_for_jsonl,
)
from heph.sdk.service_routes import _ServiceCallRoute, _ServiceStreamRoute


class _JsonlTransportService(Protocol):
    def _call_route_sequence(self) -> tuple[_ServiceCallRoute, ...]: ...

    def _stream_route_sequence(self) -> tuple[_ServiceStreamRoute, ...]: ...


@dataclass(frozen=True, slots=True)
class _JsonlRouteCoverage:
    label: str
    advertised_methods: tuple[str, ...]
    explicit_route_methods: tuple[str, ...]
    implemented_methods: tuple[str, ...]
    missing_methods_label: str


def validate_sdk_jsonl_transport_contract(
    service: _JsonlTransportService,
    *,
    jsonl_call_routes: Mapping[str, object],
    jsonl_operation_stream_methods: Mapping[str, str],
    jsonl_call_method_specs: tuple[SdkMethodSpec, ...],
    jsonl_stream_method_specs: tuple[SdkMethodSpec, ...],
) -> tuple[str, ...]:
    """Return implementation drift between JSONL routes and advertised SDK specs."""
    issues: list[str] = []
    service_call_methods = tuple(route.method for route in service._call_route_sequence())
    service_stream_methods = tuple(route.method for route in service._stream_route_sequence())
    _append_jsonl_call_route_issues(issues, service_call_methods, jsonl_call_routes)
    _append_jsonl_stream_route_issues(
        issues,
        service_stream_methods,
        jsonl_operation_stream_methods,
    )
    _append_jsonl_call_parameter_issues(issues, jsonl_call_method_specs)
    _append_jsonl_stream_parameter_issues(issues, jsonl_stream_method_specs)
    return tuple(issues)


def _append_jsonl_call_route_issues(
    issues: list[str],
    service_call_methods: tuple[str, ...],
    jsonl_call_routes: Mapping[str, object],
) -> None:
    _append_jsonl_route_coverage_issues(
        issues,
        _JsonlRouteCoverage(
            label="jsonl.call_routes",
            advertised_methods=JSONL_CALL_METHODS,
            explicit_route_methods=tuple(jsonl_call_routes),
            implemented_methods=_implemented_jsonl_call_methods(
                service_call_methods,
                tuple(jsonl_call_routes),
            ),
            missing_methods_label="advertised JSONL calls",
        ),
    )


def _append_jsonl_stream_route_issues(
    issues: list[str],
    service_stream_methods: tuple[str, ...],
    jsonl_operation_stream_methods: Mapping[str, str],
) -> None:
    _append_jsonl_route_coverage_issues(
        issues,
        _JsonlRouteCoverage(
            label="jsonl.stream_routes",
            advertised_methods=JSONL_STREAM_METHODS,
            explicit_route_methods=tuple(jsonl_operation_stream_methods),
            implemented_methods=_implemented_jsonl_stream_methods(service_stream_methods),
            missing_methods_label="advertised JSONL streams",
        ),
    )


def _append_jsonl_route_coverage_issues(
    issues: list[str],
    coverage: _JsonlRouteCoverage,
) -> None:
    _append_unadvertised_jsonl_route_issues(issues, coverage)
    _append_missing_jsonl_route_issues(issues, coverage)


def _append_unadvertised_jsonl_route_issues(
    issues: list[str],
    coverage: _JsonlRouteCoverage,
) -> None:
    advertised_methods = frozenset(coverage.advertised_methods)
    unadvertised_routes = tuple(
        sorted(
            method
            for method in coverage.explicit_route_methods
            if method not in advertised_methods
        )
    )
    if unadvertised_routes:
        issues.append(
            f"{coverage.label} contains unadvertised routes: {', '.join(unadvertised_routes)}"
        )


def _append_missing_jsonl_route_issues(
    issues: list[str],
    coverage: _JsonlRouteCoverage,
) -> None:
    implemented_methods = frozenset(coverage.implemented_methods)
    missing_methods = tuple(
        method for method in coverage.advertised_methods if method not in implemented_methods
    )
    if missing_methods:
        issues.append(
            f"{coverage.label} does not implement {coverage.missing_methods_label}: "
            f"{', '.join(missing_methods)}"
        )


def _implemented_jsonl_call_methods(
    service_call_methods: tuple[str, ...],
    jsonl_call_route_methods: tuple[str, ...],
) -> tuple[str, ...]:
    service_methods = frozenset(service_call_methods)
    explicit_routes = frozenset(jsonl_call_route_methods)
    return tuple(
        method
        for method in JSONL_CALL_METHODS
        if method in service_methods or method in explicit_routes
    )


def _implemented_jsonl_stream_methods(
    service_stream_methods: tuple[str, ...],
) -> tuple[str, ...]:
    service_methods = frozenset(service_stream_methods)
    return tuple(
        method
        for method in JSONL_STREAM_METHODS
        if (service_method := _jsonl_service_stream_method(method)) is not None
        and service_method in service_methods
    )


def _append_jsonl_call_parameter_issues(
    issues: list[str],
    jsonl_call_method_specs: tuple[SdkMethodSpec, ...],
) -> None:
    service_specs = _method_specs_by_method(SERVICE_CALL_METHOD_SPECS)
    for spec in jsonl_call_method_specs:
        service_spec = service_specs.get(spec.method)
        if service_spec is None:
            continue
        if _method_param_contracts(spec) != _method_param_contracts(service_spec):
            issues.append(
                f"jsonl.call_specs.{spec.method} params do not match service call params."
            )


def _append_jsonl_stream_parameter_issues(
    issues: list[str],
    jsonl_stream_method_specs: tuple[SdkMethodSpec, ...],
) -> None:
    service_specs = _method_specs_by_method(SERVICE_STREAM_METHOD_SPECS)
    for spec in jsonl_stream_method_specs:
        service_method = _jsonl_service_stream_method(spec.method)
        if service_method is None:
            continue
        service_spec = service_specs.get(service_method)
        if service_spec is None:
            continue
        if _method_param_contracts(spec) != _method_param_contracts(service_spec):
            issues.append(
                f"jsonl.stream_specs.{spec.method} params do not match service stream params."
            )


def _jsonl_service_stream_method(method: str) -> str | None:
    if method == "prompt":
        return "prompt"
    return service_stream_method_for_jsonl(method)


def _method_specs_by_method(specs: tuple[SdkMethodSpec, ...]) -> dict[str, SdkMethodSpec]:
    return {spec.method: spec for spec in specs}


def _method_param_contracts(spec: SdkMethodSpec) -> tuple[SdkMethodParameter, ...]:
    return spec.params
