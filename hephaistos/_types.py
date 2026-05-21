from __future__ import annotations

import json
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


def parse_json_object_fragment(text: str) -> dict[str, object] | None:
    """Extract a JSON object from plain text or a fenced JSON block."""
    fragment = _json_object_fragment(_strip_json_fence(text.strip()))
    if fragment is None:
        return None
    try:
        parsed: object = json.loads(fragment)
    except json.JSONDecodeError:
        return None
    return parsed if is_string_mapping(parsed) else None


def _strip_json_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    stripped = text.strip("`").strip()
    return stripped[4:].strip() if stripped.casefold().startswith("json") else stripped


def _json_object_fragment(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    return text[start : end + 1]
