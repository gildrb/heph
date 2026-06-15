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
from heph.sdk.method_validation import (
    validate_jsonl_message_payload,
)
from heph.sdk.methods import (
    JSONL_CALL_METHOD_SPECS,
    JSONL_OPERATION_STREAM_METHODS,
    JSONL_STREAM_METHOD_SPECS,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_METHOD_UNAVAILABLE_BUSY,
    service_stream_method_for_jsonl,
)
from heph.sdk.runtime import HephSdkBusyError, HephSdkError, HephSdkUnavailableError
from heph.sdk.service import HephService, ServicePayload
from heph.sdk.stdio_contract import (
    validate_sdk_jsonl_transport_contract as _validate_sdk_jsonl_transport_contract,
)
from heph.sdk.stdio_requests import (
    RequestId,
    SdkProtocolError,
    _jsonl_request_from_mapping,
    _JsonlRequest,
    _parse_request,
    _required_string,
    _validate_jsonl_call_params,
    _validate_jsonl_stream_params,
)
from heph.sdk.stdio_routes import _JSONL_CALL_ROUTES
from heph.sdk.stdio_state import (
    TransportBusyState,
    _jsonl_validated_result_payload,
    _merge_transport_busy_state,
    _service_state_includes_transport_busy,
    _state_with_jsonl_stream_methods,
)

type JsonlStreamEvents = Callable[[], Iterator[ServicePayload]]
type JsonlStreamCleanup = Callable[[], None]


@dataclass(frozen=True, slots=True)
class ActivePrompt:
    request_id: RequestId
    abort: threading.Event


@dataclass(frozen=True, slots=True)
class ActiveOperation:
    request_id: RequestId
    active_operation: str


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

    def __post_init__(self) -> None:
        issues = validate_sdk_jsonl_transport_contract(self.service)
        if issues:
            message = "SDK JSONL transport contract drift: " + "; ".join(issues)
            raise HephSdkError(message)

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
            self._start_prompt_stream(
                request.request_id,
                _validate_jsonl_stream_params(request, JSONL_STREAM_METHOD_SPECS),
            )
            return
        service_method = service_stream_method_for_jsonl(request.method)
        if service_method is not None:
            self._start_operation_stream(
                request.request_id,
                request.method,
                service_method,
                _validate_jsonl_stream_params(request, JSONL_STREAM_METHOD_SPECS),
            )
            return
        self._handle_call(request)

    def _handle_call(self, request: _JsonlRequest) -> None:
        params = _validate_jsonl_call_params(request, JSONL_CALL_METHOD_SPECS)
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
        self._write_call_response(request_id, method, self.service.call(method, params))

    def _write_call_response(
        self,
        request_id: RequestId,
        method: str,
        result: ServicePayload,
        *,
        translate_state_streams: bool = True,
    ) -> None:
        payload = _jsonl_validated_result_payload(
            method,
            result,
            translate_state_streams=translate_state_streams,
        )
        self._write_response(request_id, payload)

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
        message = validate_jsonl_message_payload(payload)
        with self._write_lock:
            self.output_stream.write(json.dumps(message, ensure_ascii=False) + "\n")
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


def validate_sdk_jsonl_transport_contract(service: HephService) -> tuple[str, ...]:
    """Return implementation drift between JSONL routes and advertised SDK specs."""
    return _validate_sdk_jsonl_transport_contract(
        service,
        jsonl_call_routes=_JSONL_CALL_ROUTES,
        jsonl_operation_stream_methods=JSONL_OPERATION_STREAM_METHODS,
        jsonl_call_method_specs=JSONL_CALL_METHOD_SPECS,
        jsonl_stream_method_specs=JSONL_STREAM_METHOD_SPECS,
    )


__all__ = [
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "JsonlSdkServer",
    "SdkProtocolError",
    "serve_stdio",
    "validate_sdk_jsonl_transport_contract",
]
