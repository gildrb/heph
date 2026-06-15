"""Strict JSONL codec helpers for the SDK stdio transport."""

from __future__ import annotations

import json
from collections.abc import Mapping


class SdkJsonlDecodeError(ValueError):
    """Raised when a JSONL line is not strict JSON."""


def encode_jsonl_line(payload: Mapping[str, object]) -> str:
    """Return one strict JSON line for a validated SDK payload."""
    return json.dumps(payload, ensure_ascii=False, allow_nan=False) + "\n"


def decode_jsonl_line(line: str) -> object:
    """Decode one strict JSON line, rejecting non-standard constants."""
    try:
        return json.loads(line, parse_constant=_reject_nonstandard_json_constant)
    except json.JSONDecodeError as exc:
        raise SdkJsonlDecodeError(exc.msg) from exc


def _reject_nonstandard_json_constant(value: str) -> object:
    raise SdkJsonlDecodeError(f"non-standard JSON constant: {value}")
