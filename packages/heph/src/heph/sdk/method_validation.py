"""Validation helpers for advertised SDK method contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from heph.sdk.methods import SdkMethodSpec
from heph.sdk.runtime import HephSdkError

_ARRAY_PREFIX = "array<"
_LITERAL_PREFIX = "literal<"


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
    for param in spec.params:
        if param.name in parameters:
            value = parameters[param.name]
            _validate_parameter_type(
                surface,
                method,
                param.name,
                value,
                param.value_type,
            )
            if param.choices:
                _validate_parameter_choice(
                    surface,
                    method,
                    param.name,
                    value,
                    param.choices,
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


def _validate_parameter_type(
    surface: str,
    method: str,
    name: str,
    value: object,
    value_type: str,
) -> None:
    if _value_matches_type(value, value_type):
        return
    raise HephSdkError(
        f"{surface} method '{method}' parameter '{name}' must be {_type_message(value_type)}."
    )


def _value_matches_type(value: object, value_type: str) -> bool:
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "number":
        return _is_json_number(value)
    if value_type == "number_or_null":
        return value is None or _is_json_number(value)
    if value_type == "string_or_integer":
        return isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool))
    if value_type == "object":
        return isinstance(value, Mapping)
    if value_type.startswith(_ARRAY_PREFIX) and value_type.endswith(">"):
        if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
            return False
        inner_type = value_type.removeprefix(_ARRAY_PREFIX).removesuffix(">")
        return all(_value_matches_type(item, inner_type) for item in value)
    if value_type.startswith(_LITERAL_PREFIX) and value_type.endswith(">"):
        literal_value = value_type.removeprefix(_LITERAL_PREFIX).removesuffix(">")
        return value == literal_value
    return True


def _is_json_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _type_message(value_type: str) -> str:
    if value_type == "string":
        return "a string"
    if value_type == "boolean":
        return "a boolean"
    if value_type == "integer":
        return "an integer"
    if value_type == "number":
        return "a number"
    if value_type == "number_or_null":
        return "a number or null"
    if value_type == "string_or_integer":
        return "a string or integer"
    if value_type == "object":
        return "an object"
    if value_type.startswith(_ARRAY_PREFIX) and value_type.endswith(">"):
        return "an array"
    if value_type.startswith(_LITERAL_PREFIX) and value_type.endswith(">"):
        literal_value = value_type.removeprefix(_LITERAL_PREFIX).removesuffix(">")
        return f"literal value '{literal_value}'"
    return f"SDK type '{value_type}'"


def _validate_parameter_choice(
    surface: str,
    method: str,
    name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    if isinstance(value, str) and value in choices:
        return
    raise HephSdkError(
        f"{surface} method '{method}' parameter '{name}' must be one of: {', '.join(choices)}."
    )


__all__ = ["validate_method_params"]
