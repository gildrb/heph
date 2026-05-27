"""Runtime notices that steer the agent away from unproductive tool loops."""

from __future__ import annotations

import json

from hephaion.chat.events import NoticeEvent
from hephaion.runtime import ApiMessage

SLOW_TOOL_LATENCY_MS = 30_000.0
LARGE_TOOL_RESULT_CHARS = 20_000
ACCEPTANCE_CRITERIA = (
    "Acceptance criteria: inspect the relevant workspace or sources with tools; "
    "base conclusions on observed tool output; call out missing evidence or failed tools; "
    "stop only after the result is validated against those observations."
)


def metadata_float(metadata: dict[str, object], key: str) -> float | None:
    value = metadata.get(key)
    if isinstance(value, int | float):
        return float(value)
    return None


def metadata_int(metadata: dict[str, object], key: str) -> int | None:
    value = metadata.get(key)
    if isinstance(value, int):
        return value
    return None


def tool_runtime_note(name: str, tool_result: ApiMessage) -> NoticeEvent | None:
    metadata_raw = tool_result.get("tool_metadata", {})
    metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
    success = bool(tool_result.get("tool_success", True))
    latency_ms = metadata_float(metadata, "latency_ms")
    result_length = metadata_int(metadata, "result_length")

    notice_metadata = _tool_notice_metadata(
        name,
        latency_ms=latency_ms,
        result_length=result_length,
    )

    if not success:
        return _failed_tool_notice(name, tool_result, notice_metadata)

    if latency_ms is not None and latency_ms >= SLOW_TOOL_LATENCY_MS:
        return _slow_tool_notice(name, latency_ms, notice_metadata)

    if result_length is not None and result_length >= LARGE_TOOL_RESULT_CHARS:
        return _large_tool_result_notice(name, result_length, notice_metadata)

    return None


def _tool_notice_metadata(
    name: str,
    *,
    latency_ms: float | None,
    result_length: int | None,
) -> dict[str, object]:
    metadata: dict[str, object] = {"tool": name}
    if latency_ms is not None:
        metadata["latency_ms"] = latency_ms
    if result_length is not None:
        metadata["result_length"] = result_length
    return metadata


def _failed_tool_notice(
    name: str,
    tool_result: ApiMessage,
    metadata: dict[str, object],
) -> NoticeEvent:
    error = tool_result.get("tool_error")
    if isinstance(error, str) and error:
        metadata["error"] = error
    metadata["reason"] = "failed"
    return NoticeEvent(
        (
            f"Execution note: tool '{name}' failed. Inspect the error before retrying "
            "the same call."
        ),
        code="tool_runtime",
        metadata=metadata,
    )


def _slow_tool_notice(
    name: str,
    latency_ms: float,
    metadata: dict[str, object],
) -> NoticeEvent:
    metadata["reason"] = "slow"
    return NoticeEvent(
        (
            f"Execution note: tool '{name}' took {latency_ms / 1000:.1f}s. "
            "Prefer a narrower action before repeating it."
        ),
        code="tool_runtime",
        metadata=metadata,
    )


def _large_tool_result_notice(
    name: str,
    result_length: int,
    metadata: dict[str, object],
) -> NoticeEvent:
    metadata["reason"] = "large_result"
    return NoticeEvent(
        (
            f"Execution note: tool '{name}' returned {result_length} characters. "
            "Use a narrower query or inspect the specific file next."
        ),
        code="tool_runtime",
        metadata=metadata,
    )


def acceptance_criteria_notice() -> NoticeEvent:
    return NoticeEvent(
        ACCEPTANCE_CRITERIA,
        code="acceptance_criteria",
        metadata={"source": "agent_harness", "requires_tools": True},
    )


def tool_call_fingerprint(name: str, arguments: dict[str, object]) -> str:
    try:
        rendered_args = json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    except TypeError:
        rendered_args = repr(sorted(arguments.items()))
    return f"{name}:{rendered_args}"


def repeated_tool_call_notice(
    name: str,
    arguments: dict[str, object],
    repeat_count: int,
) -> NoticeEvent:
    return NoticeEvent(
        (
            f"Execution note: tool '{name}' was called with the same arguments "
            f"{repeat_count} times. Change strategy before repeating it again."
        ),
        code="tool_runtime",
        metadata={
            "tool": name,
            "reason": "repeated_call",
            "repeat_count": repeat_count,
            "arguments": arguments,
        },
    )
