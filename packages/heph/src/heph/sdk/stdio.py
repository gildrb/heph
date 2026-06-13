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
from heph.sdk.methods import (
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    service_stream_method_for_jsonl,
)
from heph.sdk.runtime import HephSdkBusyError, HephSdkError
from heph.sdk.service import HephService, ServicePayload

type RequestId = str | int | None
type JsonlStreamEvents = Callable[[], Iterator[ServicePayload]]
type JsonlStreamCleanup = Callable[[], None]


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
                "state": self.service.state(),
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
            self._write_error(None, exc.code, str(exc))

    def handle_request(self, request: dict[str, object]) -> None:
        request_id = _request_id(request.get("id"))
        try:
            method = _request_method(request)
            params = _request_params(request)
            if method == "prompt":
                self._start_prompt_stream(request_id, params)
                return
            service_method = service_stream_method_for_jsonl(method)
            if service_method is not None:
                self._start_operation_stream(request_id, method, service_method, params)
                return
            self._handle_call(request_id, method, params)
        except SdkProtocolError as exc:
            self._write_error(request_id, exc.code, str(exc))
        except HephSdkBusyError as exc:
            self._write_error(request_id, "busy", str(exc))
        except (HephSdkError, ArmoryError) as exc:
            self._write_error(request_id, "sdk_error", str(exc))
        except Exception as exc:
            self._write_error(request_id, "internal_error", str(exc))

    def _handle_call(
        self,
        request_id: RequestId,
        method: str,
        params: dict[str, object],
    ) -> None:
        if method == "abort":
            self._write_response(request_id, self._abort_active_prompt())
            return
        if method == "state":
            self._write_response(request_id, self._state_with_transport_busy())
            return
        if method == "capabilities":
            self._write_response(request_id, self.service.capabilities())
            return
        if method == "settings":
            self._write_response(request_id, self.service.settings())
            return
        if self._stream_is_pending():
            raise HephSdkBusyError()
        self._write_response(request_id, self.service.call(method, params))

    def _capabilities_payload(self) -> ServicePayload:
        capabilities = self.service.capabilities().get("capabilities")
        return capabilities if is_string_mapping(capabilities) else {}

    def _start_prompt_stream(self, request_id: RequestId, params: dict[str, object]) -> None:
        text = _required_string(params, "text")
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
            for event in events():
                self._write(
                    {
                        "type": "stream_event",
                        "id": request_id,
                        "event": event,
                    }
                )
        except HephSdkBusyError as exc:
            self._write_stream_end(request_id, ok=False, error=_error("busy", str(exc)))
        except HephSdkError as exc:
            self._write_stream_end(request_id, ok=False, error=_error("sdk_error", str(exc)))
        except Exception as exc:
            self._write_stream_end(
                request_id,
                ok=False,
                error=_error("internal_error", str(exc)),
            )
        else:
            self._write_stream_end(request_id, ok=True, error=None)
        finally:
            try:
                cleanup()
            finally:
                self._forget_stream_thread(threading.current_thread())

    def _abort_active_prompt(self) -> ServicePayload:
        with self._state_lock:
            active_prompt = self._active_prompt
        if active_prompt is None:
            return {"aborted": False, "state": self._state_with_transport_busy()}
        active_prompt.abort.set()
        return {"aborted": True, "state": self._state_with_transport_busy()}

    def _state_with_transport_busy(self) -> ServicePayload:
        state = self.service.state()
        with self._state_lock:
            active_prompt = self._active_prompt is not None
            active_operation = (
                self._active_operation.active_operation
                if self._active_operation is not None
                else None
            )
        if not active_prompt and active_operation is None:
            return state
        service_state = state.get("service")
        if not is_string_mapping(service_state):
            return state
        if (not active_prompt or service_state.get("prompt_active") is True) and (
            active_operation is None or service_state.get("active_operation") is not None
        ):
            return state
        merged_service = dict(service_state)
        if active_prompt:
            merged_service["prompt_active"] = True
        if active_operation is not None and merged_service.get("active_operation") is None:
            merged_service["active_operation"] = active_operation
        merged_service["is_busy"] = True
        merged_state = dict(state)
        merged_state["service"] = merged_service
        return merged_state

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

    def _write_error(self, request_id: RequestId, code: str, message: str) -> None:
        self._write(
            {
                "type": "error",
                "id": request_id,
                "ok": False,
                "error": _error(code, message),
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
    return parsed


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


def _error(code: str, message: str) -> dict[str, object]:
    return {"code": code, "message": message}


__all__ = [
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "JsonlSdkServer",
    "SdkProtocolError",
    "serve_stdio",
]
