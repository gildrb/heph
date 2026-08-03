from __future__ import annotations

import math
from collections.abc import Sequence
from typing import cast


def _maybe_list(values: object) -> object:
    tolist = getattr(values, "tolist", None)
    return tolist() if callable(tolist) else values


def float_list(values: object) -> list[float]:
    values = _maybe_list(values)
    if not isinstance(values, list):
        return []
    result: list[float] = []
    typed_values = cast("list[object]", values)
    for value in typed_values:
        if not isinstance(value, int | float):
            return []
        result.append(float(value))
    return result


def embedding_rows(values: object) -> list[list[float]]:
    values = _maybe_list(values)
    if not isinstance(values, list):
        return []
    rows: list[list[float]] = []
    typed_values = cast("list[object]", values)
    for row in typed_values:
        typed_row = float_list(row)
        if typed_row:
            rows.append(typed_row)
    return rows


def object_rows(values: object) -> list[list[object]]:
    values = _maybe_list(values)
    if not isinstance(values, list):
        return []
    typed_values = cast("list[object]", values)
    return [cast("list[object]", row) for row in typed_values if isinstance(row, list)]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
