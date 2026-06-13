"""Validation helpers for advertised SDK method contracts."""

from __future__ import annotations

from collections.abc import Mapping

from heph.sdk.methods import SdkMethodSpec
from heph.sdk.runtime import HephSdkError


def validate_method_params(
    method: str,
    params: Mapping[str, object] | None,
    specs: tuple[SdkMethodSpec, ...],
    *,
    surface: str = "SDK service",
) -> dict[str, object]:
    """Validate request parameters against an advertised method spec."""
    parameters = _normalized_method_params(params)
    spec = _method_spec(method, specs)
    if spec is None:
        return parameters
    allowed_keys = frozenset(param.name for param in spec.params)
    unknown_keys = tuple(sorted(key for key in parameters if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} method '{method}' does not accept "
            f"{_parameter_names_message(unknown_keys)}."
        )
    missing_keys = tuple(
        param.name for param in spec.params if param.required and param.name not in parameters
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} method '{method}' requires {_parameter_names_message(missing_keys)}."
        )
    return parameters


def _normalized_method_params(params: Mapping[str, object] | None) -> dict[str, object]:
    if params is None:
        return {}
    parameters: dict[str, object] = {}
    for key, value in params.items():
        if not isinstance(key, str):
            raise HephSdkError("SDK method parameter names must be strings.")
        parameters[key] = value
    return parameters


def _method_spec(method: str, specs: tuple[SdkMethodSpec, ...]) -> SdkMethodSpec | None:
    return next((spec for spec in specs if spec.method == method), None)


def _parameter_names_message(names: tuple[str, ...]) -> str:
    joined = ", ".join(names)
    return f"parameter: {joined}" if len(names) == 1 else f"parameters: {joined}"


__all__ = ["validate_method_params"]
