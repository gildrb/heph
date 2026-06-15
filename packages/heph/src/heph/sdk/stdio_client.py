"""Client helpers for the SDK JSONL stdio transport."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import TextIO

from hephaion._types import is_string_mapping

from heph.sdk.compatibility import ensure_sdk_client_payload_compatibility
from heph.sdk.method_validation import (
    validate_jsonl_message_payload,
    validate_jsonl_request_payload,
)
from heph.sdk.methods import SDK_CAPABILITIES_VERSION, SDK_JSONL_PROTOCOL, SDK_JSONL_VERSION
from heph.sdk.runtime import HephSdkError

type JsonlRequestId = str | int | None
type JsonlPayload = dict[str, object]


class JsonlSdkClientError(Exception):
    """Base class for client-side JSONL transport failures."""


class JsonlSdkClientProtocolError(JsonlSdkClientError):
    """Raised when the server stream does not match the SDK JSONL protocol."""


@dataclass(frozen=True, slots=True)
class JsonlSdkErrorPayload:
    """Structured JSONL error returned by the SDK transport."""

    code: str
    message: str
    unavailable_reason: str | None


class JsonlSdkServerError(JsonlSdkClientError):
    """Raised when the SDK JSONL server returns an error envelope."""

    def __init__(self, request_id: JsonlRequestId, error: JsonlSdkErrorPayload) -> None:
        self.request_id = request_id
        self.error = error
        self.code = error.code
        self.unavailable_reason = error.unavailable_reason
        super().__init__(f"SDK JSONL server returned {error.code}: {error.message}")


@dataclass(frozen=True, slots=True)
class JsonlSdkReady:
    """Initial SDK JSONL ready handshake."""

    protocol: str
    version: int
    capabilities: JsonlPayload
    state: JsonlPayload


@dataclass(slots=True)
class JsonlSdkClient:
    """Small sequential client for the Heph SDK JSONL stdio transport.

    The client validates framing and compatibility for the simple one-request-at-a-time path.
    Advanced GUI clients can still use ``read_message`` and ``write_request`` directly and route
    messages by id in their own event loop.
    """

    input_stream: TextIO
    output_stream: TextIO
    client_capabilities_version: int = SDK_CAPABILITIES_VERSION
    jsonl_version: int = SDK_JSONL_VERSION
    _request_counter: int = field(default=0, init=False, repr=False)

    def read_ready(self) -> JsonlSdkReady:
        """Read and validate the initial server ready message."""
        message = self.read_message()
        if _message_type(message) != "ready":
            raise JsonlSdkClientProtocolError("Expected SDK JSONL ready message.")
        ready = jsonl_ready_from_message(message)
        if ready.protocol != SDK_JSONL_PROTOCOL:
            raise JsonlSdkClientProtocolError(f"Unsupported SDK JSONL protocol: {ready.protocol}.")
        if ready.version != self.jsonl_version:
            raise JsonlSdkClientProtocolError(
                f"Unsupported SDK JSONL version {ready.version}; expected {self.jsonl_version}."
            )
        ensure_sdk_client_payload_compatibility(
            ready.capabilities,
            client_capabilities_version=self.client_capabilities_version,
            jsonl_version=ready.version,
        )
        return ready

    def read_message(self) -> JsonlPayload:
        """Read one validated JSONL message from the server stream."""
        line = self.input_stream.readline()
        if line == "":
            raise JsonlSdkClientProtocolError(
                "SDK JSONL stream ended before a message was available."
            )
        return parse_jsonl_message(line)

    def write_request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> str | int:
        """Write one validated request and return the request id used."""
        actual_request_id = request_id if request_id is not None else self._next_request_id(method)
        self.output_stream.write(
            encode_jsonl_request(method, params, request_id=actual_request_id)
        )
        self.output_stream.flush()
        return actual_request_id

    def call(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> JsonlPayload:
        """Write a call request and read its response payload."""
        actual_request_id = self.write_request(method, params, request_id=request_id)
        message = self.read_message()
        _require_request_id(message, actual_request_id)
        message_type = _message_type(message)
        if message_type == "error":
            raise JsonlSdkServerError(actual_request_id, jsonl_error_from_message(message))
        if message_type != "response":
            raise JsonlSdkClientProtocolError(
                f"Expected SDK JSONL response for {actual_request_id!r}, got {message_type!r}."
            )
        if message.get("ok") is not True:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL response for {actual_request_id!r} was not successful."
            )
        return _mapping_field(message, "result", "SDK JSONL response result")

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> Iterator[JsonlPayload]:
        """Write a stream request and yield each stream event payload."""
        actual_request_id = self.write_request(method, params, request_id=request_id)
        start = self.read_message()
        _require_request_id(start, actual_request_id)
        start_type = _message_type(start)
        if start_type == "error":
            raise JsonlSdkServerError(actual_request_id, jsonl_error_from_message(start))
        if start_type != "stream_start":
            raise JsonlSdkClientProtocolError(
                f"Expected SDK JSONL stream_start for {actual_request_id!r}, got {start_type!r}."
            )
        if start.get("method") != method:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL stream_start for {actual_request_id!r} reported method "
                f"{start.get('method')!r}, expected {method!r}."
            )
        yield from self._stream_events(actual_request_id)

    def _stream_events(self, request_id: str | int) -> Iterator[JsonlPayload]:
        while True:
            message = self.read_message()
            _require_request_id(message, request_id)
            message_type = _message_type(message)
            if message_type == "stream_event":
                yield _mapping_field(message, "event", "SDK JSONL stream event")
            elif message_type == "stream_end":
                if message.get("ok") is True:
                    return
                raise JsonlSdkServerError(request_id, jsonl_error_from_message(message))
            elif message_type == "error":
                raise JsonlSdkServerError(request_id, jsonl_error_from_message(message))
            else:
                raise JsonlSdkClientProtocolError(
                    f"Expected SDK JSONL stream_event or stream_end for {request_id!r}, got "
                    f"{message_type!r}."
                )

    def _next_request_id(self, method: str) -> str:
        self._request_counter += 1
        return f"{method}-{self._request_counter}"


def jsonl_request_payload(
    method: str,
    params: Mapping[str, object] | None = None,
    *,
    request_id: JsonlRequestId = None,
) -> JsonlPayload:
    """Build and validate a JSON-ready SDK JSONL request payload."""
    payload: JsonlPayload = {"method": method}
    if request_id is not None:
        payload["id"] = request_id
    if params is not None:
        payload["params"] = dict(params)
    try:
        return validate_jsonl_request_payload(payload)
    except HephSdkError as exc:
        raise JsonlSdkClientProtocolError(str(exc)) from exc


def encode_jsonl_request(
    method: str,
    params: Mapping[str, object] | None = None,
    *,
    request_id: JsonlRequestId = None,
) -> str:
    """Return a validated newline-delimited JSON request line."""
    payload = jsonl_request_payload(method, params, request_id=request_id)
    return json.dumps(payload, ensure_ascii=False) + "\n"


def parse_jsonl_message(line: str) -> JsonlPayload:
    """Parse and validate one JSONL message from the SDK server."""
    if not line.strip():
        raise JsonlSdkClientProtocolError("SDK JSONL messages must not be empty.")
    try:
        parsed: object = json.loads(line)
    except json.JSONDecodeError as exc:
        raise JsonlSdkClientProtocolError(f"Invalid SDK JSONL message: {exc.msg}") from exc
    if not is_string_mapping(parsed):
        raise JsonlSdkClientProtocolError("SDK JSONL messages must be JSON objects.")
    try:
        return validate_jsonl_message_payload(parsed)
    except HephSdkError as exc:
        raise JsonlSdkClientProtocolError(f"Invalid SDK JSONL message: {exc}") from exc


def jsonl_ready_from_message(message: Mapping[str, object]) -> JsonlSdkReady:
    """Convert a validated ready envelope into a typed handshake object."""
    return JsonlSdkReady(
        protocol=_string_field(message, "protocol", "SDK JSONL ready protocol"),
        version=_integer_field(message, "version", "SDK JSONL ready version"),
        capabilities=_mapping_field(message, "capabilities", "SDK JSONL ready capabilities"),
        state=_mapping_field(message, "state", "SDK JSONL ready state"),
    )


def jsonl_error_from_message(message: Mapping[str, object]) -> JsonlSdkErrorPayload:
    """Convert a validated error-bearing envelope into a structured error payload."""
    error = _mapping_field(message, "error", "SDK JSONL error")
    unavailable_reason = error.get("unavailable_reason")
    if unavailable_reason is not None and not isinstance(unavailable_reason, str):
        raise JsonlSdkClientProtocolError(
            "SDK JSONL error field 'unavailable_reason' must be a string or null."
        )
    return JsonlSdkErrorPayload(
        code=_string_field(error, "code", "SDK JSONL error code"),
        message=_string_field(error, "message", "SDK JSONL error message"),
        unavailable_reason=unavailable_reason,
    )


def _message_type(message: Mapping[str, object]) -> str:
    return _string_field(message, "type", "SDK JSONL message type")


def _require_request_id(message: Mapping[str, object], request_id: str | int) -> None:
    value = message.get("id")
    if value != request_id:
        raise JsonlSdkClientProtocolError(
            f"Expected SDK JSONL message for request {request_id!r}, got {value!r}."
        )


def _mapping_field(message: Mapping[str, object], key: str, label: str) -> JsonlPayload:
    value = message.get(key)
    if is_string_mapping(value):
        return dict(value)
    raise JsonlSdkClientProtocolError(f"{label} must be an object.")


def _string_field(message: Mapping[str, object], key: str, label: str) -> str:
    value = message.get(key)
    if isinstance(value, str):
        return value
    raise JsonlSdkClientProtocolError(f"{label} must be a string.")


def _integer_field(message: Mapping[str, object], key: str, label: str) -> int:
    value = message.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise JsonlSdkClientProtocolError(f"{label} must be an integer.")


__all__ = [
    "JsonlPayload",
    "JsonlRequestId",
    "JsonlSdkClient",
    "JsonlSdkClientError",
    "JsonlSdkClientProtocolError",
    "JsonlSdkErrorPayload",
    "JsonlSdkReady",
    "JsonlSdkServerError",
    "encode_jsonl_request",
    "jsonl_error_from_message",
    "jsonl_ready_from_message",
    "jsonl_request_payload",
    "parse_jsonl_message",
]
