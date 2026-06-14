"""JSON Lines stdio transport for the Heph SDK service."""

from __future__ import annotations

import json
import sys
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import TextIO

from hephaion._types import is_string_mapping
from hephaion.armory.storage import ArmoryError

from heph.sdk.factory import HephSdkOptions, create_heph_service
from heph.sdk.method_validation import validate_method_params
from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    JSONL_CALL_METHODS,
    JSONL_REQUEST_SPEC,
    JSONL_STREAM_METHOD_SPECS,
    JSONL_STREAM_METHODS,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_METHOD_UNAVAILABLE_BUSY,
    jsonl_stream_method_for_service,
    service_stream_method_for_jsonl,
)
from heph.sdk.runtime import HephSdkBusyError, HephSdkError, HephSdkUnavailableError
from heph.sdk.service import HephService, ServicePayload

type RequestId = str | int | None
type JsonlStreamEvents = Callable[[], Iterator[ServicePayload]]
type JsonlStreamCleanup = Callable[[], None]
type _JsonlCallHandler = Callable[["JsonlSdkServer", RequestId, dict[str, object]], None]

_REQUEST_FIELDS = frozenset(field.name for field in JSONL_REQUEST_SPEC.fields)


class SdkProtocolError(Exception):
    """Raised when a JSONL SDK request does not match the transport contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ActivePrompt:
    request_id: RequestId
    abort: threading.Event


@dataclass(frozen=True, slots=True)
class ActiveOperation:
    request_id: RequestId
    active_operation: str


@dataclass(frozen=True, slots=True)
class _JsonlRequest:
    request_id: RequestId
    method: str
    params: dict[str, object]


@dataclass(frozen=True, slots=True)
class _JsonlErrorPayload:
    code: str
    message: str
    unavailable_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass(frozen=True, slots=True)
class _JsonlCallRoute:
    handler: _JsonlCallHandler

    def dispatch(
        self,
        server: JsonlSdkServer,
        request_id: RequestId,
        params: dict[str, object],
    ) -> None:
        self.handler(server, request_id, params)


@dataclass(frozen=True, slots=True)
class TransportBusyState:
    prompt_active: bool
    active_operation: str | None

    @property
    def is_busy(self) -> bool:
        return self.prompt_active or self.active_operation is not None


@dataclass(slots=True)
class JsonlSdkServer:
    """Run a stateful SDK service over newline-delimited JSON."""

    service: HephService
    input_stream: TextIO
    output_stream: TextIO
    _write_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _state_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _active_prompt: ActivePrompt | None = field(default=None, init=False, repr=False)
    _active_operation: ActiveOperation | None = field(default=None, init=False, repr=False)
    _stream_threads_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )
    _stream_threads: list[threading.Thread] = field(default_factory=list, init=False, repr=False)

    def serve(self) -> None:
        self._write(
            {
                "type": "ready",
                "protocol": SDK_JSONL_PROTOCOL,
                "version": SDK_JSONL_VERSION,
                "capabilities": self._capabilities_payload(),
                "state": self._state_with_transport_busy(),
            }
        )
        for raw_line in self.input_stream:
            self.handle_line(raw_line)
        self._wait_for_streams()

    def handle_line(self, raw_line: str) -> None:
        line = raw_line.strip()
        if not line:
            return
        try:
            request = _parse_request(line)
            self.handle_request(request)
        except SdkProtocolError as exc:
            self._write_error(None, _request_error_payload(exc))

    def handle_request(self, request: dict[str, object]) -> None:
        request_id: RequestId = None
        try:
            parsed_request = _jsonl_request_from_mapping(request)
            request_id = parsed_request.request_id
            self._dispatch_request(parsed_request)
        except Exception as exc:
            error = _request_error_payload(exc)
            self._write_error(request_id, error)

    def _dispatch_request(self, request: _JsonlRequest) -> None:
        if request.method == "prompt":
            self._start_prompt_stream(request.request_id, _validate_jsonl_stream_params(request))
            return
        service_method = service_stream_method_for_jsonl(request.method)
        if service_method is not None:
            self._start_operation_stream(
                request.request_id,
                request.method,
                service_method,
                _validate_jsonl_stream_params(request),
            )
            return
        self._handle_call(request)

    def _handle_call(self, request: _JsonlRequest) -> None:
        params = self.service.validate_call_params(request.method, request.params)
        if route := _JSONL_CALL_ROUTES.get(request.method):
            route.dispatch(self, request.request_id, params)
            return
        self._write_service_call_response(request.request_id, request.method, params)

    def _write_service_call_response(
        self,
        request_id: RequestId,
        method: str,
        params: dict[str, object],
    ) -> None:
        if self._stream_is_pending():
            raise HephSdkBusyError()
        self._write_response(request_id, _jsonl_result_payload(self.service.call(method, params)))

    def _capabilities_payload(self) -> ServicePayload:
        capabilities = self.service.capabilities().get("capabilities")
        return capabilities if is_string_mapping(capabilities) else {}

    def _start_prompt_stream(self, request_id: RequestId, params: dict[str, object]) -> None:
        text = _required_string(params, "text")
        self.service.ensure_stream_available("prompt")
        active_prompt = ActivePrompt(request_id=request_id, abort=threading.Event())
        with self._state_lock:
            if self._active_prompt is not None or self._active_operation is not None:
                raise HephSdkBusyError()
            self._active_prompt = active_prompt

        def events() -> Iterator[ServicePayload]:
            yield from self.service.prompt(text, abort=active_prompt.abort)

        def cleanup() -> None:
            with self._state_lock:
                if self._active_prompt is active_prompt:
                    self._active_prompt = None

        self._start_stream_thread(
            request_id=request_id,
            method="prompt",
            thread_name="heph-sdk-prompt",
            events=events,
            cleanup=cleanup,
        )

    def _start_operation_stream(
        self,
        request_id: RequestId,
        method: str,
        service_method: str,
        params: dict[str, object],
    ) -> None:
        self.service.ensure_stream_available(service_method)
        active_operation = ActiveOperation(
            request_id=request_id,
            active_operation=service_method,
        )
        with self._state_lock:
            if self._active_prompt is not None or self._active_operation is not None:
                raise HephSdkBusyError()
            self._active_operation = active_operation

        def events() -> Iterator[ServicePayload]:
            yield from self.service.stream(service_method, params)

        def cleanup() -> None:
            with self._state_lock:
                if self._active_operation is active_operation:
                    self._active_operation = None

        self._start_stream_thread(
            request_id=request_id,
            method=method,
            thread_name=f"heph-sdk-{method}",
            events=events,
            cleanup=cleanup,
        )

    def _start_stream_thread(
        self,
        *,
        request_id: RequestId,
        method: str,
        thread_name: str,
        events: JsonlStreamEvents,
        cleanup: JsonlStreamCleanup,
    ) -> None:
        self._write({"type": "stream_start", "id": request_id, "method": method})
        thread = threading.Thread(
            target=self._run_stream,
            args=(request_id, events, cleanup),
            name=thread_name,
        )
        self._track_stream_thread(thread)
        try:
            thread.start()
        except BaseException:
            self._forget_stream_thread(thread)
            cleanup()
            raise

    def _run_stream(
        self,
        request_id: RequestId,
        events: JsonlStreamEvents,
        cleanup: JsonlStreamCleanup,
    ) -> None:
        try:
            self._write_stream_events(request_id, events())
        except Exception as exc:
            self._write_stream_end(request_id, ok=False, error=_stream_error(exc))
        else:
            self._write_stream_end(request_id, ok=True, error=None)
        finally:
            try:
                cleanup()
            finally:
                self._forget_stream_thread(threading.current_thread())

    def _write_stream_events(
        self,
        request_id: RequestId,
        events: Iterator[ServicePayload],
    ) -> None:
        for event in events:
            self._write(
                {
                    "type": "stream_event",
                    "id": request_id,
                    "event": event,
                }
            )

    def _abort_active_prompt(self) -> ServicePayload:
        with self._state_lock:
            active_prompt = self._active_prompt
        if active_prompt is None:
            return {"aborted": False, "state": self._state_with_transport_busy()}
        active_prompt.abort.set()
        return {"aborted": True, "state": self._state_with_transport_busy()}

    def _state_with_transport_busy(self) -> ServicePayload:
        state = _state_with_jsonl_stream_methods(self.service.state())
        transport_state = self._transport_busy_state()
        if not transport_state.is_busy:
            return state
        service_state = state.get("service")
        if not is_string_mapping(service_state):
            return state
        if _service_state_includes_transport_busy(service_state, transport_state):
            return state
        merged_service = _merge_transport_busy_state(service_state, transport_state)
        merged_state = dict(state)
        merged_state["service"] = merged_service
        return merged_state

    def _transport_busy_state(self) -> TransportBusyState:
        with self._state_lock:
            active_operation = (
                self._active_operation.active_operation
                if self._active_operation is not None
                else None
            )
            return TransportBusyState(
                prompt_active=self._active_prompt is not None,
                active_operation=active_operation,
            )

    def _stream_is_pending(self) -> bool:
        with self._state_lock:
            return self._active_prompt is not None or self._active_operation is not None

    def _track_stream_thread(self, thread: threading.Thread) -> None:
        with self._stream_threads_lock:
            self._stream_threads.append(thread)

    def _forget_stream_thread(self, thread: threading.Thread) -> None:
        with self._stream_threads_lock:
            if thread in self._stream_threads:
                self._stream_threads.remove(thread)

    def _wait_for_streams(self) -> None:
        while True:
            with self._stream_threads_lock:
                threads = tuple(self._stream_threads)
            if not threads:
                return
            for thread in threads:
                thread.join()

    def _write_response(self, request_id: RequestId, result: ServicePayload) -> None:
        self._write({"type": "response", "id": request_id, "ok": True, "result": result})

    def _write_stream_end(
        self,
        request_id: RequestId,
        *,
        ok: bool,
        error: dict[str, object] | None,
    ) -> None:
        payload: dict[str, object] = {"type": "stream_end", "id": request_id, "ok": ok}
        if error is not None:
            payload["error"] = error
        self._write(payload)

    def _write_error(self, request_id: RequestId, error: _JsonlErrorPayload) -> None:
        self._write(
            {
                "type": "error",
                "id": request_id,
                "ok": False,
                "error": error.to_dict(),
            }
        )

    def _write(self, payload: dict[str, object]) -> None:
        with self._write_lock:
            self.output_stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.output_stream.flush()


def serve_stdio(
    options: HephSdkOptions | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    service_result = create_heph_service(options or HephSdkOptions())
    server = JsonlSdkServer(
        service=service_result.service,
        input_stream=input_stream or sys.stdin,
        output_stream=output_stream or sys.stdout,
    )
    server.serve()


def _parse_request(line: str) -> dict[str, object]:
    try:
        parsed: object = json.loads(line)
    except json.JSONDecodeError as exc:
        raise SdkProtocolError("invalid_json", f"Invalid JSON request: {exc.msg}") from exc
    if not is_string_mapping(parsed):
        raise SdkProtocolError("invalid_request", "SDK requests must be JSON objects.")
    _validate_request_fields(parsed)
    return parsed


def _jsonl_request_from_mapping(request: dict[str, object]) -> _JsonlRequest:
    return _JsonlRequest(
        request_id=_request_id(request.get("id")),
        method=_request_method(request),
        params=_request_params(request),
    )


def _validate_jsonl_stream_params(request: _JsonlRequest) -> dict[str, object]:
    return validate_method_params(
        request.method,
        request.params,
        JSONL_STREAM_METHOD_SPECS,
        surface="SDK JSONL",
    )


def _write_jsonl_abort_call(
    server: JsonlSdkServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_response(request_id, server._abort_active_prompt())


def _write_jsonl_state_call(
    server: JsonlSdkServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_response(request_id, server._state_with_transport_busy())


def _write_jsonl_capabilities_call(
    server: JsonlSdkServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_response(request_id, server.service.capabilities())


def _write_jsonl_settings_call(
    server: JsonlSdkServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_response(request_id, server.service.settings())


_JSONL_CALL_ROUTES: dict[str, _JsonlCallRoute] = {
    "abort": _JsonlCallRoute(_write_jsonl_abort_call),
    "state": _JsonlCallRoute(_write_jsonl_state_call),
    "capabilities": _JsonlCallRoute(_write_jsonl_capabilities_call),
    "settings": _JsonlCallRoute(_write_jsonl_settings_call),
}


def _validate_request_fields(request: dict[str, object]) -> None:
    unknown_fields = tuple(sorted(field for field in request if field not in _REQUEST_FIELDS))
    if unknown_fields:
        raise SdkProtocolError(
            "invalid_request",
            f"SDK request envelope does not accept {_field_names_message(unknown_fields)}.",
        )


def _field_names_message(names: tuple[str, ...]) -> str:
    joined = ", ".join(names)
    return f"field: {joined}" if len(names) == 1 else f"fields: {joined}"


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


def _service_state_includes_transport_busy(
    service_state: dict[str, object],
    transport_state: TransportBusyState,
) -> bool:
    prompt_recorded = (
        not transport_state.prompt_active or service_state.get("prompt_active") is True
    )
    operation_recorded = (
        transport_state.active_operation is None
        or service_state.get("active_operation") is not None
    )
    return prompt_recorded and operation_recorded


def _merge_transport_busy_state(
    service_state: dict[str, object],
    transport_state: TransportBusyState,
) -> dict[str, object]:
    merged_service = dict(service_state)
    if transport_state.prompt_active:
        merged_service["prompt_active"] = True
    if (
        transport_state.active_operation is not None
        and merged_service.get("active_operation") is None
    ):
        merged_service["active_operation"] = transport_state.active_operation
    merged_service["is_busy"] = True
    merged_service["available_call_methods"] = list(BUSY_ALLOWED_CALL_METHODS)
    merged_service["available_stream_methods"] = []
    merged_service["call_method_availability"] = _busy_method_availability(
        JSONL_CALL_METHODS,
        BUSY_ALLOWED_CALL_METHODS,
    )
    merged_service["stream_method_availability"] = _busy_method_availability(
        JSONL_STREAM_METHODS,
        (),
    )
    return merged_service


def _state_with_jsonl_stream_methods(state: ServicePayload) -> ServicePayload:
    service_state = state.get("service")
    if not is_string_mapping(service_state):
        return state
    merged_service = dict(service_state)
    if service_state.get("is_busy") is True:
        merged_service["available_stream_methods"] = []
    elif "available_stream_methods" in service_state:
        merged_service["available_stream_methods"] = _jsonl_available_stream_methods(service_state)
    else:
        merged_service["available_stream_methods"] = list(JSONL_STREAM_METHODS)
    if "stream_method_availability" in service_state:
        merged_service["stream_method_availability"] = _jsonl_stream_method_availability(
            service_state
        )
    merged_state = dict(state)
    merged_state["service"] = merged_service
    return merged_state


def _jsonl_available_stream_methods(service_state: dict[str, object]) -> list[str]:
    available = service_state.get("available_stream_methods")
    if not isinstance(available, list):
        return []
    methods: list[str] = []
    for method in available:
        if not isinstance(method, str):
            continue
        jsonl_method = jsonl_stream_method_for_service(method)
        if jsonl_method is not None:
            methods.append(jsonl_method)
    return methods


def _jsonl_stream_method_availability(service_state: dict[str, object]) -> list[dict[str, object]]:
    availability = service_state.get("stream_method_availability")
    if not isinstance(availability, list):
        return []
    return [
        record
        for item in availability
        if (record := _jsonl_stream_availability_record(item)) is not None
    ]


def _jsonl_stream_availability_record(item: object) -> dict[str, object] | None:
    if not is_string_mapping(item):
        return None
    jsonl_method = _jsonl_stream_availability_method(item)
    if jsonl_method is None:
        return None
    record = dict(item)
    record["method"] = jsonl_method
    return record


def _jsonl_stream_availability_method(item: dict[str, object]) -> str | None:
    method = item.get("method")
    if not isinstance(method, str):
        return None
    return jsonl_stream_method_for_service(method)


def _busy_method_availability(
    methods: tuple[str, ...],
    available_methods: tuple[str, ...],
) -> list[dict[str, object]]:
    available = frozenset(available_methods)
    available_records: list[dict[str, object]] = [
        {
            "method": method,
            "available": True,
            "unavailable_reason": None,
        }
        for method in available_methods
    ]
    unavailable_records: list[dict[str, object]] = [
        {
            "method": method,
            "available": False,
            "unavailable_reason": SDK_METHOD_UNAVAILABLE_BUSY,
        }
        for method in methods
        if method not in available
    ]
    return [*available_records, *unavailable_records]


def _jsonl_result_payload(result: ServicePayload) -> ServicePayload:
    result = _state_with_jsonl_stream_methods(result)
    state_value = result.get("state")
    if not is_string_mapping(state_value):
        return result
    merged_result = dict(result)
    merged_result["state"] = _state_with_jsonl_stream_methods(state_value)
    return merged_result


def _request_error_payload(exc: Exception) -> _JsonlErrorPayload:
    if isinstance(exc, HephSdkBusyError):
        return _JsonlErrorPayload(exc.code, str(exc), SDK_METHOD_UNAVAILABLE_BUSY)
    if isinstance(exc, HephSdkUnavailableError):
        return _JsonlErrorPayload(exc.code, str(exc), exc.unavailable_reason)
    if isinstance(exc, (SdkProtocolError, HephSdkError)):
        return _JsonlErrorPayload(exc.code, str(exc))
    if isinstance(exc, ArmoryError):
        return _JsonlErrorPayload("sdk_error", str(exc))
    return _JsonlErrorPayload("internal_error", str(exc))


def _stream_error(exc: Exception) -> dict[str, object]:
    return _request_error_payload(exc).to_dict()


__all__ = [
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "JsonlSdkServer",
    "SdkProtocolError",
    "serve_stdio",
]
