from __future__ import annotations

from typing import TypeGuard, cast

type JSONPrimitive = None | bool | int | float | str
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type JSONObject = dict[str, JSONValue]


def is_string_mapping(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    typed_value = cast("dict[object, object]", value)
    return all(isinstance(raw_key, str) for raw_key in typed_value)


def is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)
