"""Validation helpers for advertised SDK method contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from heph.sdk.methods import SdkMethodParameter, SdkMethodSpec
from heph.sdk.runtime import HephSdkError

_ARRAY_PREFIX = "array<"
_LITERAL_PREFIX = "literal<"
type _TypeMatcher = Callable[[object], bool]


@dataclass(frozen=True, slots=True)
class _TypeRule:
    message: str
    matches: _TypeMatcher


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
    _validate_unknown_parameters(surface, method, parameters, spec)
    _validate_required_parameters(surface, method, parameters, spec)
    _validate_supplied_parameters(surface, method, parameters, spec)
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


def _validate_unknown_parameters(
    surface: str,
    method: str,
    parameters: Mapping[str, object],
    spec: SdkMethodSpec,
) -> None:
    allowed_keys = frozenset(param.name for param in spec.params)
    unknown_keys = tuple(sorted(key for key in parameters if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} method '{method}' does not accept "
            f"{_parameter_names_message(unknown_keys)}."
        )


def _validate_required_parameters(
    surface: str,
    method: str,
    parameters: Mapping[str, object],
    spec: SdkMethodSpec,
) -> None:
    missing_keys = tuple(
        param.name for param in spec.params if param.required and param.name not in parameters
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} method '{method}' requires {_parameter_names_message(missing_keys)}."
        )


def _validate_supplied_parameters(
    surface: str,
    method: str,
    parameters: Mapping[str, object],
    spec: SdkMethodSpec,
) -> None:
    for param in spec.params:
        if param.name in parameters:
            _validate_supplied_parameter(surface, method, param, parameters[param.name])


def _validate_supplied_parameter(
    surface: str,
    method: str,
    param: SdkMethodParameter,
    value: object,
) -> None:
    _validate_parameter_type(surface, method, param.name, value, param.value_type)
    if param.choices:
        _validate_parameter_choice(surface, method, param.name, value, param.choices)


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
    if rule := _TYPE_RULES.get(value_type):
        return rule.matches(value)
    if item_type := _array_item_type(value_type):
        return _value_is_array_of_type(value, item_type)
    literal_value = _literal_value(value_type)
    if literal_value is not None:
        return value == literal_value
    return True


def _array_item_type(value_type: str) -> str | None:
    if value_type.startswith(_ARRAY_PREFIX) and value_type.endswith(">"):
        return value_type.removeprefix(_ARRAY_PREFIX).removesuffix(">")
    return None


def _literal_value(value_type: str) -> str | None:
    if value_type.startswith(_LITERAL_PREFIX) and value_type.endswith(">"):
        return value_type.removeprefix(_LITERAL_PREFIX).removesuffix(">")
    return None


def _value_is_array_of_type(value: object, item_type: str) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return False
    return all(_value_matches_type(item, item_type) for item in value)


def _is_json_string(value: object) -> bool:
    return isinstance(value, str)


def _is_json_boolean(value: object) -> bool:
    return isinstance(value, bool)


def _is_json_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_json_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_json_number_or_null(value: object) -> bool:
    return value is None or _is_json_number(value)


def _is_json_string_or_integer(value: object) -> bool:
    return isinstance(value, str) or _is_json_integer(value)


def _is_json_object(value: object) -> bool:
    return isinstance(value, Mapping)


def _type_message(value_type: str) -> str:
    if rule := _TYPE_RULES.get(value_type):
        return rule.message
    if _array_item_type(value_type) is not None:
        return "an array"
    literal_value = _literal_value(value_type)
    if literal_value is not None:
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


_TYPE_RULES: Mapping[str, _TypeRule] = {
    "string": _TypeRule("a string", _is_json_string),
    "boolean": _TypeRule("a boolean", _is_json_boolean),
    "integer": _TypeRule("an integer", _is_json_integer),
    "number": _TypeRule("a number", _is_json_number),
    "number_or_null": _TypeRule("a number or null", _is_json_number_or_null),
    "string_or_integer": _TypeRule("a string or integer", _is_json_string_or_integer),
    "object": _TypeRule("an object", _is_json_object),
}


__all__ = ["validate_method_params"]
