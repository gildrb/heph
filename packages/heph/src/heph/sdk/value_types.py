"""Shared SDK value-type grammar helpers."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

_ARRAY_PREFIX = "array<"
_LITERAL_PREFIX = "literal<"
_MAP_PREFIX = "map<"


@dataclass(frozen=True, slots=True)
class _CollectionValueTypeSpec:
    prefix: str
    empty_message: str


_COLLECTION_VALUE_TYPE_SPECS = (
    _CollectionValueTypeSpec(_ARRAY_PREFIX, "empty array item type"),
    _CollectionValueTypeSpec(_MAP_PREFIX, "empty map item type"),
)


def sdk_array_item_type(value_type: str) -> str | None:
    """Return a non-empty SDK array item type argument."""
    item_type = _enclosed_type_argument(value_type, prefix=_ARRAY_PREFIX)
    if item_type:
        return item_type
    return None


def sdk_map_item_type(value_type: str) -> str | None:
    """Return a non-empty SDK map item type argument."""
    item_type = _enclosed_type_argument(value_type, prefix=_MAP_PREFIX)
    if item_type:
        return item_type
    return None


def sdk_literal_value(value_type: str) -> str | None:
    """Return a non-empty SDK literal value type argument."""
    literal_value = _enclosed_type_argument(value_type, prefix=_LITERAL_PREFIX)
    if literal_value:
        return literal_value
    return None


def sdk_custom_type_references(
    value_type: str,
    builtin_types: Collection[str],
) -> tuple[str, ...]:
    """Return custom DTO type names referenced by a valid SDK value type."""
    if _is_builtin_or_literal(value_type, builtin_types):
        return ()
    if sdk_value_type_shape_issue("", value_type) is not None:
        return ()
    item_type = _collection_item_type(value_type)
    if item_type is not None:
        return sdk_custom_type_references(item_type, builtin_types)
    return (value_type,)


def sdk_value_type_shape_issue(context: str, value_type: str) -> str | None:
    """Return a human-readable issue when an SDK value type has malformed grammar."""
    collection_spec = _collection_value_type_spec(value_type)
    if collection_spec is not None:
        return _nested_value_type_shape_issue(
            context,
            value_type,
            spec=collection_spec,
        )
    if value_type.startswith(_LITERAL_PREFIX):
        return _literal_value_type_shape_issue(context, value_type)
    if _looks_like_malformed_generic(value_type):
        return f"{context} has malformed SDK value type: {value_type}"
    return None


def _is_builtin_or_literal(value_type: str, builtin_types: Collection[str]) -> bool:
    return value_type in builtin_types or sdk_literal_value(value_type) is not None


def _collection_item_type(value_type: str) -> str | None:
    for spec in _COLLECTION_VALUE_TYPE_SPECS:
        item_type = _enclosed_type_argument(value_type, prefix=spec.prefix)
        if item_type:
            return item_type
    return None


def _collection_value_type_spec(value_type: str) -> _CollectionValueTypeSpec | None:
    return next(
        (spec for spec in _COLLECTION_VALUE_TYPE_SPECS if value_type.startswith(spec.prefix)),
        None,
    )


def _literal_value_type_shape_issue(context: str, value_type: str) -> str | None:
    literal_value = _enclosed_type_argument(value_type, prefix=_LITERAL_PREFIX)
    if literal_value is None:
        return f"{context} has malformed SDK value type: {value_type}"
    if literal_value == "":
        return f"{context} has empty literal value."
    return None


def _nested_value_type_shape_issue(
    context: str,
    value_type: str,
    *,
    spec: _CollectionValueTypeSpec,
) -> str | None:
    inner_type = _enclosed_type_argument(value_type, prefix=spec.prefix)
    if inner_type is None:
        return f"{context} has malformed SDK value type: {value_type}"
    if inner_type == "":
        return f"{context} has {spec.empty_message}."
    return sdk_value_type_shape_issue(context, inner_type)


def _enclosed_type_argument(value_type: str, *, prefix: str) -> str | None:
    if value_type.startswith(prefix) and value_type.endswith(">"):
        return value_type.removeprefix(prefix).removesuffix(">")
    return None


def _looks_like_malformed_generic(value_type: str) -> bool:
    return "<" in value_type or value_type.endswith(">")
