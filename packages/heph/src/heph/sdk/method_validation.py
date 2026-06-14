"""Validation helpers for advertised SDK method contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from heph.sdk.methods import (
    JSONL_MESSAGE_SPECS,
    JSONL_REQUEST_SPEC,
    SDK_EVENT_SPECS,
    SDK_TYPE_SPECS,
    SdkEventSpec,
    SdkJsonlMessageSpec,
    SdkJsonlRequestSpec,
    SdkMethodParameter,
    SdkMethodSpec,
    SdkObjectFieldSpec,
    SdkResultSpec,
    SdkStreamSpec,
    SdkTypeSpec,
)
from heph.sdk.runtime import HephSdkError

_ARRAY_PREFIX = "array<"
_LITERAL_PREFIX = "literal<"
_MAP_PREFIX = "map<"
_SDK_EVENT_TYPE = "sdk_event"
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


def validate_result_payload(
    method: str,
    result: Mapping[str, object],
    specs: tuple[SdkResultSpec, ...],
    *,
    surface: str = "SDK service",
    type_specs: tuple[SdkTypeSpec, ...] = SDK_TYPE_SPECS,
) -> dict[str, object]:
    """Validate a service result against an advertised result spec."""
    payload = dict(result)
    spec = _result_spec(method, specs)
    if spec is None:
        return payload
    type_map = _type_specs_by_name(type_specs)
    _validate_result_type(surface, method, payload, spec.value_type, type_map)
    _validate_unknown_result_fields(surface, method, payload, spec)
    _validate_required_result_fields(surface, method, payload, spec)
    _validate_supplied_result_fields(surface, method, payload, spec, type_map)
    return payload


def validate_stream_event_payload(
    method: str,
    event: Mapping[str, object],
    stream_specs: tuple[SdkStreamSpec, ...],
    *,
    event_specs: tuple[SdkEventSpec, ...] = SDK_EVENT_SPECS,
    surface: str = "SDK service",
    type_specs: tuple[SdkTypeSpec, ...] = SDK_TYPE_SPECS,
) -> dict[str, object]:
    """Validate a stream event against advertised stream and event specs."""
    payload = _string_keyed_result_object(f"{surface} stream", method, "event", event)
    stream_spec = _stream_spec(method, stream_specs)
    if stream_spec is None:
        return payload
    event_type = _stream_event_type(surface, method, payload)
    _validate_stream_event_allowed(surface, method, event_type, stream_spec)
    event_spec = _event_spec(event_type, event_specs)
    if event_spec is None:
        raise HephSdkError(
            f"{surface} stream '{method}' event type '{event_type}' has no SDK event spec."
        )
    _validate_event_fields(surface, method, event_type, payload, event_spec, type_specs)
    return payload


def validate_jsonl_message_payload(
    message: Mapping[str, object],
    *,
    specs: tuple[SdkJsonlMessageSpec, ...] = JSONL_MESSAGE_SPECS,
    surface: str = "SDK JSONL",
    type_specs: tuple[SdkTypeSpec, ...] = SDK_TYPE_SPECS,
) -> dict[str, object]:
    """Validate an outgoing JSONL transport envelope against advertised specs."""
    payload = _string_keyed_result_object(surface, "message", "payload", message)
    message_type = _jsonl_message_type(surface, payload)
    spec = _jsonl_message_spec(message_type, specs)
    if spec is None:
        raise HephSdkError(f"{surface} message type '{message_type}' is not advertised.")
    _validate_jsonl_message_fields(surface, message_type, payload, spec, type_specs)
    return payload


def validate_jsonl_request_payload(
    request: Mapping[str, object],
    *,
    spec: SdkJsonlRequestSpec = JSONL_REQUEST_SPEC,
    surface: str = "SDK JSONL",
    type_specs: tuple[SdkTypeSpec, ...] = SDK_TYPE_SPECS,
) -> dict[str, object]:
    """Validate an incoming JSONL request envelope against the advertised spec."""
    payload = _string_keyed_json_object(surface, "request", request)
    _validate_jsonl_request_fields(surface, payload, spec, type_specs)
    return payload


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


def _result_spec(method: str, specs: tuple[SdkResultSpec, ...]) -> SdkResultSpec | None:
    return next((spec for spec in specs if spec.method == method), None)


def _stream_spec(method: str, specs: tuple[SdkStreamSpec, ...]) -> SdkStreamSpec | None:
    return next((spec for spec in specs if spec.method == method), None)


def _event_spec(event_type: str, specs: tuple[SdkEventSpec, ...]) -> SdkEventSpec | None:
    return next((spec for spec in specs if spec.event_type == event_type), None)


def _jsonl_message_spec(
    message_type: str,
    specs: tuple[SdkJsonlMessageSpec, ...],
) -> SdkJsonlMessageSpec | None:
    return next((spec for spec in specs if spec.message_type == message_type), None)


def _parameter_names_message(names: tuple[str, ...]) -> str:
    joined = ", ".join(names)
    return f"parameter: {joined}" if len(names) == 1 else f"parameters: {joined}"


def _field_names_message(names: tuple[str, ...]) -> str:
    joined = ", ".join(names)
    return f"field: {joined}" if len(names) == 1 else f"fields: {joined}"


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


def _validate_result_type(
    surface: str,
    method: str,
    payload: Mapping[str, object],
    value_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    _validate_result_value_type(
        surface,
        method,
        "result",
        payload,
        value_type,
        type_map,
    )


def _validate_unknown_result_fields(
    surface: str,
    method: str,
    payload: Mapping[str, object],
    spec: SdkResultSpec,
) -> None:
    if not spec.fields:
        return
    allowed_keys = frozenset(field.name for field in spec.fields)
    unknown_keys = tuple(sorted(key for key in payload if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} method '{method}' result does not accept "
            f"{_field_names_message(unknown_keys)}."
        )


def _validate_required_result_fields(
    surface: str,
    method: str,
    payload: Mapping[str, object],
    spec: SdkResultSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in spec.fields if field.required and field.name not in payload
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} method '{method}' result requires {_field_names_message(missing_keys)}."
        )


def _validate_supplied_result_fields(
    surface: str,
    method: str,
    payload: Mapping[str, object],
    spec: SdkResultSpec,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    for field in spec.fields:
        if field.name in payload:
            _validate_supplied_result_field(
                surface,
                method,
                field,
                payload[field.name],
                type_map,
            )


def _validate_supplied_result_field(
    surface: str,
    method: str,
    field: SdkObjectFieldSpec,
    value: object,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    if value is None and field.nullable:
        return
    _validate_result_value_type(
        surface,
        method,
        _result_field_location(field.name),
        value,
        field.value_type,
        type_map,
    )


def _stream_event_type(
    surface: str,
    method: str,
    payload: Mapping[str, object],
) -> str:
    event_type = payload.get("type")
    if isinstance(event_type, str) and event_type:
        return event_type
    raise HephSdkError(f"{surface} stream '{method}' event type must be a non-empty string.")


def _validate_stream_event_allowed(
    surface: str,
    method: str,
    event_type: str,
    spec: SdkStreamSpec,
) -> None:
    if event_type in spec.event_types:
        return
    raise HephSdkError(f"{surface} stream '{method}' does not advertise event type: {event_type}.")


def _validate_event_fields(
    surface: str,
    method: str,
    event_type: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
    type_specs: tuple[SdkTypeSpec, ...],
) -> None:
    type_map = _type_specs_by_name(type_specs)
    _validate_unknown_event_fields(surface, method, event_type, payload, spec)
    _validate_required_event_fields(surface, method, event_type, payload, spec)
    for field in spec.fields:
        if field.name not in payload:
            continue
        value = payload[field.name]
        if value is None and field.nullable:
            continue
        _validate_result_value_type(
            f"{surface} stream",
            method,
            _event_field_location(event_type, field.name),
            value,
            field.value_type,
            type_map,
        )


def _validate_unknown_event_fields(
    surface: str,
    method: str,
    event_type: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in spec.fields)
    unknown_keys = tuple(sorted(key for key in payload if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} stream '{method}' event '{event_type}' does not accept "
            f"{_field_names_message(unknown_keys)}."
        )


def _validate_required_event_fields(
    surface: str,
    method: str,
    event_type: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in spec.fields if field.required and field.name not in payload
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} stream '{method}' event '{event_type}' requires "
            f"{_field_names_message(missing_keys)}."
        )


def _event_field_location(event_type: str, field_name: str) -> str:
    return f"event '{event_type}' field '{field_name}'"


def _jsonl_message_type(surface: str, payload: Mapping[str, object]) -> str:
    message_type = payload.get("type")
    if isinstance(message_type, str) and message_type:
        return message_type
    raise HephSdkError(f"{surface} message type must be a non-empty string.")


def _validate_jsonl_message_fields(
    surface: str,
    message_type: str,
    payload: Mapping[str, object],
    spec: SdkJsonlMessageSpec,
    type_specs: tuple[SdkTypeSpec, ...],
) -> None:
    type_map = _type_specs_by_name(type_specs)
    _validate_unknown_jsonl_message_fields(surface, message_type, payload, spec)
    _validate_required_jsonl_message_fields(surface, message_type, payload, spec)
    for field in spec.fields:
        if field.name not in payload:
            continue
        value = payload[field.name]
        if value is None and field.nullable:
            continue
        _validate_result_value_type(
            f"{surface} message",
            message_type,
            _jsonl_message_field_location(message_type, field.name),
            value,
            field.value_type,
            type_map,
        )


def _validate_unknown_jsonl_message_fields(
    surface: str,
    message_type: str,
    payload: Mapping[str, object],
    spec: SdkJsonlMessageSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in spec.fields)
    unknown_keys = tuple(sorted(key for key in payload if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} message '{message_type}' does not accept "
            f"{_field_names_message(unknown_keys)}."
        )


def _validate_required_jsonl_message_fields(
    surface: str,
    message_type: str,
    payload: Mapping[str, object],
    spec: SdkJsonlMessageSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in spec.fields if field.required and field.name not in payload
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} message '{message_type}' requires {_field_names_message(missing_keys)}."
        )


def _jsonl_message_field_location(message_type: str, field_name: str) -> str:
    return f"message '{message_type}' field '{field_name}'"


def _validate_jsonl_request_fields(
    surface: str,
    payload: Mapping[str, object],
    spec: SdkJsonlRequestSpec,
    type_specs: tuple[SdkTypeSpec, ...],
) -> None:
    type_map = _type_specs_by_name(type_specs)
    _validate_unknown_jsonl_request_fields(surface, payload, spec)
    _validate_required_jsonl_request_fields(surface, payload, spec)
    for field in spec.fields:
        if field.name not in payload:
            continue
        value = payload[field.name]
        if value is None and field.nullable:
            continue
        _validate_jsonl_request_value_type(
            surface,
            f"request field '{field.name}'",
            value,
            field.value_type,
            type_map,
        )


def _validate_unknown_jsonl_request_fields(
    surface: str,
    payload: Mapping[str, object],
    spec: SdkJsonlRequestSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in spec.fields)
    unknown_keys = tuple(sorted(key for key in payload if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} request does not accept {_field_names_message(unknown_keys)}."
        )


def _validate_required_jsonl_request_fields(
    surface: str,
    payload: Mapping[str, object],
    spec: SdkJsonlRequestSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in spec.fields if field.required and field.name not in payload
    )
    if missing_keys:
        raise HephSdkError(f"{surface} request requires {_field_names_message(missing_keys)}.")


def _validate_jsonl_request_value_type(
    surface: str,
    location: str,
    value: object,
    value_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    custom_type = type_map.get(value_type)
    if custom_type is not None:
        _validate_custom_jsonl_request_type(surface, location, value, custom_type, type_map)
        return
    if item_type := _array_item_type(value_type):
        _validate_jsonl_request_array(surface, location, value, item_type, type_map)
        return
    if item_type := _map_item_type(value_type):
        _validate_jsonl_request_map(surface, location, value, item_type, type_map)
        return
    if _value_matches_type(value, value_type):
        return
    raise HephSdkError(f"{surface} {location} must be {_type_message(value_type)}.")


def _validate_jsonl_request_array(
    surface: str,
    location: str,
    value: object,
    item_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise HephSdkError(f"{surface} {location} must be an array.")
    for index, item in enumerate(value):
        _validate_jsonl_request_value_type(
            surface,
            f"{location}[{index}]",
            item,
            item_type,
            type_map,
        )


def _validate_jsonl_request_map(
    surface: str,
    location: str,
    value: object,
    item_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    fields = _string_keyed_json_object(surface, location, value)
    for key, item in fields.items():
        _validate_jsonl_request_value_type(
            surface,
            f"{location}.{key}",
            item,
            item_type,
            type_map,
        )


def _validate_custom_jsonl_request_type(
    surface: str,
    location: str,
    value: object,
    type_spec: SdkTypeSpec,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    fields = _string_keyed_json_object(surface, location, value)
    _validate_unknown_jsonl_request_type_fields(surface, location, fields, type_spec)
    _validate_required_jsonl_request_type_fields(surface, location, fields, type_spec)
    for field in type_spec.fields:
        if field.name not in fields:
            continue
        value = fields[field.name]
        if value is None and field.nullable:
            continue
        _validate_jsonl_request_value_type(
            surface,
            f"{location}.{field.name}",
            value,
            field.value_type,
            type_map,
        )


def _validate_unknown_jsonl_request_type_fields(
    surface: str,
    location: str,
    value: Mapping[str, object],
    type_spec: SdkTypeSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in type_spec.fields)
    unknown_keys = tuple(sorted(key for key in value if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} {location} does not accept {_field_names_message(unknown_keys)}."
        )


def _validate_required_jsonl_request_type_fields(
    surface: str,
    location: str,
    value: Mapping[str, object],
    type_spec: SdkTypeSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in type_spec.fields if field.required and field.name not in value
    )
    if missing_keys:
        raise HephSdkError(f"{surface} {location} requires {_field_names_message(missing_keys)}.")


def _type_specs_by_name(type_specs: tuple[SdkTypeSpec, ...]) -> dict[str, SdkTypeSpec]:
    return {spec.type_name: spec for spec in type_specs}


def _string_keyed_json_object(
    surface: str,
    location: str,
    value: object,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise HephSdkError(f"{surface} {location} must be an object.")
    fields: dict[str, object] = {}
    for key, field_value in value.items():
        if not isinstance(key, str):
            raise HephSdkError(f"{surface} {location} must use string keys.")
        fields[key] = field_value
    return fields


def _result_field_location(path: str) -> str:
    return f"result field '{path}'"


def _nested_result_field_location(parent: str, field_name: str) -> str:
    if parent.startswith(("event '", "message '")):
        return f"{parent}.{field_name}"
    return _result_field_location(_nested_result_path(parent, field_name))


def _array_item_location(location: str, index: int) -> str:
    if location.startswith("result field '") and location.endswith("'"):
        return _result_field_location(f"{_result_path(location)}[{index}]")
    return f"{location}[{index}]"


def _map_item_location(location: str, key: str) -> str:
    if location.startswith("result field '") and location.endswith("'"):
        return _result_field_location(f"{_result_path(location)}.{key}")
    return f"{location}.{key}"


def _nested_result_path(parent: str, field_name: str) -> str:
    if parent == "result":
        return field_name
    return f"{_result_path(parent)}.{field_name}"


def _result_path(location: str) -> str:
    if location.startswith("result field '") and location.endswith("'"):
        return location.removeprefix("result field '").removesuffix("'")
    return location


def _validate_result_value_type(
    surface: str,
    method: str,
    location: str,
    value: object,
    value_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    if value_type == _SDK_EVENT_TYPE:
        _validate_sdk_event_discriminator(surface, method, location, value, type_map)
        return
    custom_type = type_map.get(value_type)
    if custom_type is not None:
        _validate_custom_result_type(surface, method, location, value, custom_type, type_map)
        return
    if item_type := _array_item_type(value_type):
        _validate_result_array(surface, method, location, value, item_type, type_map)
        return
    if item_type := _map_item_type(value_type):
        _validate_result_map(surface, method, location, value, item_type, type_map)
        return
    if _value_matches_type(value, value_type):
        return
    raise HephSdkError(
        f"{surface} method '{method}' {location} must be {_type_message(value_type)}."
    )


def _validate_sdk_event_discriminator(
    surface: str,
    method: str,
    location: str,
    value: object,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    payload = _string_keyed_result_object(surface, method, location, value)
    event_type = payload.get("type")
    if not isinstance(event_type, str) or not event_type:
        raise HephSdkError(f"{surface} method '{method}' {location}.type must be a string.")
    event_spec = _event_spec(event_type, SDK_EVENT_SPECS)
    if event_spec is None:
        raise HephSdkError(
            f"{surface} method '{method}' {location} event type '{event_type}' "
            "has no SDK event spec."
        )
    _validate_unknown_sdk_event_fields(surface, method, location, event_type, payload, event_spec)
    _validate_required_sdk_event_fields(surface, method, location, event_type, payload, event_spec)
    _validate_supplied_sdk_event_fields(
        surface,
        method,
        location,
        payload,
        event_spec,
        type_map,
    )


def _validate_unknown_sdk_event_fields(
    surface: str,
    method: str,
    location: str,
    event_type: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in spec.fields)
    unknown_keys = tuple(sorted(key for key in payload if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} method '{method}' {location} event '{event_type}' does not accept "
            f"{_field_names_message(unknown_keys)}."
        )


def _validate_required_sdk_event_fields(
    surface: str,
    method: str,
    location: str,
    event_type: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in spec.fields if field.required and field.name not in payload
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} method '{method}' {location} event '{event_type}' requires "
            f"{_field_names_message(missing_keys)}."
        )


def _validate_supplied_sdk_event_fields(
    surface: str,
    method: str,
    location: str,
    payload: Mapping[str, object],
    spec: SdkEventSpec,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    for field in spec.fields:
        if field.name not in payload:
            continue
        field_value = payload[field.name]
        if field_value is None and field.nullable:
            continue
        _validate_result_value_type(
            surface,
            method,
            _nested_result_field_location(location, field.name),
            field_value,
            field.value_type,
            type_map,
        )


def _validate_result_array(
    surface: str,
    method: str,
    location: str,
    value: object,
    item_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise HephSdkError(f"{surface} method '{method}' {location} must be an array.")
    for index, item in enumerate(value):
        _validate_result_value_type(
            surface,
            method,
            _array_item_location(location, index),
            item,
            item_type,
            type_map,
        )


def _validate_result_map(
    surface: str,
    method: str,
    location: str,
    value: object,
    item_type: str,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    fields = _string_keyed_result_object(surface, method, location, value)
    for key, item in fields.items():
        _validate_result_value_type(
            surface,
            method,
            _map_item_location(location, key),
            item,
            item_type,
            type_map,
        )


def _validate_custom_result_type(
    surface: str,
    method: str,
    location: str,
    value: object,
    type_spec: SdkTypeSpec,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    if not isinstance(value, Mapping):
        raise HephSdkError(
            f"{surface} method '{method}' {location} must be {_type_message(type_spec.type_name)}."
        )
    fields = _string_keyed_result_object(surface, method, location, value)
    _validate_unknown_type_fields(surface, method, location, fields, type_spec)
    _validate_required_type_fields(surface, method, location, fields, type_spec)
    _validate_supplied_type_fields(surface, method, location, fields, type_spec, type_map)


def _string_keyed_result_object(
    surface: str,
    method: str,
    location: str,
    value: object,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise HephSdkError(f"{surface} method '{method}' {location} must be an object.")
    fields: dict[str, object] = {}
    for key, field_value in value.items():
        if not isinstance(key, str):
            raise HephSdkError(f"{surface} method '{method}' {location} must use string keys.")
        fields[key] = field_value
    return fields


def _validate_unknown_type_fields(
    surface: str,
    method: str,
    location: str,
    value: Mapping[str, object],
    type_spec: SdkTypeSpec,
) -> None:
    allowed_keys = frozenset(field.name for field in type_spec.fields)
    unknown_keys = tuple(sorted(key for key in value if key not in allowed_keys))
    if unknown_keys:
        raise HephSdkError(
            f"{surface} method '{method}' {location} does not accept "
            f"{_field_names_message(unknown_keys)}."
        )


def _validate_required_type_fields(
    surface: str,
    method: str,
    location: str,
    value: Mapping[str, object],
    type_spec: SdkTypeSpec,
) -> None:
    missing_keys = tuple(
        field.name for field in type_spec.fields if field.required and field.name not in value
    )
    if missing_keys:
        raise HephSdkError(
            f"{surface} method '{method}' {location} requires "
            f"{_field_names_message(missing_keys)}."
        )


def _validate_supplied_type_fields(
    surface: str,
    method: str,
    location: str,
    value: Mapping[str, object],
    type_spec: SdkTypeSpec,
    type_map: Mapping[str, SdkTypeSpec],
) -> None:
    for field in type_spec.fields:
        if field.name not in value:
            continue
        field_value = value[field.name]
        if field_value is None and field.nullable:
            continue
        _validate_result_value_type(
            surface,
            method,
            _nested_result_field_location(location, field.name),
            field_value,
            field.value_type,
            type_map,
        )


def _value_matches_type(value: object, value_type: str) -> bool:
    if rule := _TYPE_RULES.get(value_type):
        return rule.matches(value)
    if item_type := _array_item_type(value_type):
        return _value_is_array_of_type(value, item_type)
    if item_type := _map_item_type(value_type):
        return _value_is_map_of_type(value, item_type)
    literal_value = _literal_value(value_type)
    if literal_value is not None:
        return value == literal_value
    return True


def _array_item_type(value_type: str) -> str | None:
    return _enclosed_type_argument(value_type, prefix=_ARRAY_PREFIX)


def _map_item_type(value_type: str) -> str | None:
    return _enclosed_type_argument(value_type, prefix=_MAP_PREFIX)


def _literal_value(value_type: str) -> str | None:
    return _enclosed_type_argument(value_type, prefix=_LITERAL_PREFIX)


def _enclosed_type_argument(value_type: str, *, prefix: str) -> str | None:
    if value_type.startswith(prefix) and value_type.endswith(">"):
        return value_type.removeprefix(prefix).removesuffix(">")
    return None


def _value_is_array_of_type(value: object, item_type: str) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return False
    return all(_value_matches_type(item, item_type) for item in value)


def _value_is_map_of_type(value: object, item_type: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    return all(
        isinstance(key, str) and _value_matches_type(item, item_type)
        for key, item in value.items()
    )


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
    if _map_item_type(value_type) is not None:
        return "an object map"
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


__all__ = [
    "validate_jsonl_message_payload",
    "validate_jsonl_request_payload",
    "validate_method_params",
    "validate_result_payload",
    "validate_stream_event_payload",
]
