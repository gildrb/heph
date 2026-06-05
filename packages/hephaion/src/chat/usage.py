"""Chat usage persistence and compatibility exports."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import TypeGuard

from _types import is_string_mapping
from heph_ai.logging import get_logger
from heph_ai.runtime import usage as _runtime_usage
from heph_ai.runtime._api_types import ApiMessage
from heph_ai.runtime.usage import (
    ContextBudget,
    SessionUsage,
    TokenUsage,
    get_context_window,
)

_log = get_logger("chat.usage")


_USAGE_DIR = "usage"
_encoder = _runtime_usage._encoder
_get_pricing = _runtime_usage._get_pricing


def estimate_message_tokens(content: str) -> int:
    previous_encoder = _runtime_usage._encoder
    _runtime_usage._encoder = _encoder
    try:
        return _runtime_usage.estimate_message_tokens(content)
    finally:
        _runtime_usage._encoder = previous_encoder


def estimate_conversation_tokens(messages: Sequence[ApiMessage]) -> int:
    previous_encoder = _runtime_usage._encoder
    _runtime_usage._encoder = _encoder
    try:
        return _runtime_usage.estimate_conversation_tokens(messages)
    finally:
        _runtime_usage._encoder = previous_encoder


def save_usage(
    armory_path: Path,
    session_id: str,
    usage: SessionUsage,
) -> Path | None:
    if armory_path is None:
        return None

    # Defense-in-depth: validate session_id has no path traversal.
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        _log.warning(
            "invalid session_id in save_usage",
            extra={"fields": {"session_id": session_id}},
        )
        return None

    usage_dir = armory_path / ".hephaion" / _USAGE_DIR
    usage_dir.mkdir(parents=True, exist_ok=True)
    path = usage_dir / f"{session_id}.json"

    data = {
        "session_id": session_id,
        **usage.summary(),
    }

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_usage_summaries(armory_path: Path) -> list[dict[str, int | float | str]]:
    usage_dir = armory_path / ".hephaion" / _USAGE_DIR
    if not usage_dir.exists():
        return []

    summaries: list[dict[str, int | float | str]] = []
    for path in sorted(usage_dir.glob("*.json")):
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not is_string_mapping(raw):
            continue
        summaries.append(_usage_summary_from_payload(raw, fallback_session_id=path.stem))
    return summaries


def _usage_summary_from_payload(
    raw: dict[str, object],
    *,
    fallback_session_id: str,
) -> dict[str, int | float | str]:
    session_id = raw.get("session_id")
    return {
        "session_id": session_id if isinstance(session_id, str) else fallback_session_id,
        "api_calls": _number_value(raw.get("api_calls")),
        "prompt_tokens": _number_value(raw.get("prompt_tokens")),
        "completion_tokens": _number_value(raw.get("completion_tokens")),
        "total_tokens": _number_value(raw.get("total_tokens")),
        "cost_usd": _number_value(raw.get("cost_usd"), as_float=True),
    }


def _number_value(value: object, *, as_float: bool = False) -> int | float:
    default = 0.0 if as_float else 0
    if _is_number_value(value):
        return float(value) if as_float else int(value)
    if isinstance(value, str):
        return _number_from_string(value, default=default, as_float=as_float)
    return default


def _is_number_value(value: object) -> TypeGuard[int | float]:
    return not isinstance(value, bool) and isinstance(value, int | float)


def _number_from_string(value: str, *, default: float, as_float: bool) -> int | float:
    try:
        return float(value) if as_float else int(value)
    except ValueError:
        return default


__all__ = [
    "ContextBudget",
    "SessionUsage",
    "TokenUsage",
    "_get_pricing",
    "estimate_conversation_tokens",
    "estimate_message_tokens",
    "get_context_window",
    "load_usage_summaries",
    "save_usage",
]
