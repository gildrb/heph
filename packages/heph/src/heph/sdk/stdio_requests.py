"""JSONL request parsing and parameter validation for the SDK stdio server."""

from __future__ import annotations

import json
from dataclasses import dataclass

from hephaion._types import is_string_mapping

from heph.sdk.method_validation import (
    validate_jsonl_request_payload,
    validate_method_params,
)
from heph.sdk.methods import SdkMethodSpec
from heph.sdk.runtime import HephSdkError

type RequestId = str | int | None


class SdkProtocolError(Exception):
    """Raised when a JSONL SDK request does not match the transport contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class _JsonlRequest:
    request_id: RequestId
    method: str
    params: dict[str, object]


def _parse_request(line: str) -> dict[str, object]:
    try:
        parsed: object = json.loads(line)
    except json.JSONDecodeError as exc:
        raise SdkProtocolError("invalid_json", f"Invalid JSON request: {exc.msg}") from exc
    if not is_string_mapping(parsed):
        raise SdkProtocolError("invalid_request", "SDK requests must be JSON objects.")
    try:
        return validate_jsonl_request_payload(parsed)
    except HephSdkError as exc:
        raise SdkProtocolError("invalid_request", str(exc)) from exc


def _jsonl_request_from_mapping(request: dict[str, object]) -> _JsonlRequest:
    return _JsonlRequest(
        request_id=_request_id(request.get("id")),
        method=_request_method(request),
        params=_request_params(request),
    )


def _validate_jsonl_call_params(
    request: _JsonlRequest,
    specs: tuple[SdkMethodSpec, ...],
) -> dict[str, object]:
    return validate_method_params(
        request.method,
        request.params,
        specs,
        surface="SDK JSONL",
    )


def _validate_jsonl_stream_params(
    request: _JsonlRequest,
    specs: tuple[SdkMethodSpec, ...],
) -> dict[str, object]:
    return validate_method_params(
        request.method,
        request.params,
        specs,
        surface="SDK JSONL",
    )


def _request_id(value: object) -> RequestId:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise SdkProtocolError("invalid_request", "SDK request id must be a string, integer, or null.")


def _request_method(request: dict[str, object]) -> str:
    method = request.get("method")
    if not isinstance(method, str) or not method.strip():
        raise SdkProtocolError("invalid_request", "SDK request method must be a non-empty string.")
    return method


def _request_params(request: dict[str, object]) -> dict[str, object]:
    value = request.get("params", {})
    if value is None:
        return {}
    if not is_string_mapping(value):
        raise SdkProtocolError("invalid_request", "SDK request params must be a JSON object.")
    return value


def _required_string(params: dict[str, object], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SdkProtocolError(
            "invalid_request",
            f"SDK request parameter '{key}' must be a string.",
        )
    return value
