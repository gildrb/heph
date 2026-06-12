"""JSON Lines stdio transport for the Heph SDK service."""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from typing import TextIO

from hephaion._types import is_string_mapping
from hephaion.armory.storage import ArmoryError

from heph.sdk.factory import HephSdkOptions, create_heph_service
from heph.sdk.runtime import HephSdkBusyError, HephSdkError
from heph.sdk.service import HephService, ServicePayload

SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1

type RequestId = str | int | None


class SdkProtocolError(Exception):
    """Raised when a JSONL SDK request does not match the transport contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ActivePrompt:
    request_id: RequestId
    abort: threading.Event


@dataclass(slots=True)
class JsonlSdkServer:
    """Run a stateful SDK service over newline-delimited JSON."""

    service: HephService
    input_stream: TextIO
    output_stream: TextIO
    _write_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _state_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _active_prompt: ActivePrompt | None = field(default=None, init=False, repr=False)
    _stream_threads: list[threading.Thread] = field(default_factory=list, init=False, repr=False)

    def serve(self) -> None:
        self._write(
            {
                "type": "ready",
                "protocol": SDK_JSONL_PROTOCOL,
                "version": SDK_JSONL_VERSION,
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
        if self._stream_is_pending() and method != "state":
            raise HephSdkBusyError()
        self._write_response(request_id, self.service.call(method, params))

    def _start_prompt_stream(self, request_id: RequestId, params: dict[str, object]) -> None:
        text = _required_string(params, "text")
        active_prompt = ActivePrompt(request_id=request_id, abort=threading.Event())
        with self._state_lock:
            if self._active_prompt is not None:
                raise HephSdkBusyError()
            self._active_prompt = active_prompt
        self._write({"type": "stream_start", "id": request_id, "method": "prompt"})
        thread = threading.Thread(
            target=self._run_prompt_stream,
            args=(active_prompt, text),
            name="heph-sdk-prompt",
        )
        self._stream_threads.append(thread)
        thread.start()

    def _run_prompt_stream(self, active_prompt: ActivePrompt, text: str) -> None:
        try:
            for event in self.service.prompt(text, abort=active_prompt.abort):
                self._write(
                    {
                        "type": "stream_event",
                        "id": active_prompt.request_id,
                        "event": event,
                    }
                )
        except HephSdkBusyError as exc:
            self._write_stream_end(
                active_prompt.request_id,
                ok=False,
                error=_error("busy", str(exc)),
            )
        except HephSdkError as exc:
            self._write_stream_end(
                active_prompt.request_id,
                ok=False,
                error=_error("sdk_error", str(exc)),
            )
        except Exception as exc:
            self._write_stream_end(
                active_prompt.request_id,
                ok=False,
                error=_error("internal_error", str(exc)),
            )
        else:
            self._write_stream_end(active_prompt.request_id, ok=True, error=None)
        finally:
            with self._state_lock:
                if self._active_prompt is active_prompt:
                    self._active_prompt = None

    def _abort_active_prompt(self) -> ServicePayload:
        with self._state_lock:
            active_prompt = self._active_prompt
        if active_prompt is None:
            return {"aborted": False, "state": self.service.state()}
        active_prompt.abort.set()
        return {"aborted": True, "state": self.service.state()}

    def _stream_is_pending(self) -> bool:
        with self._state_lock:
            return self._active_prompt is not None

    def _wait_for_streams(self) -> None:
        for thread in self._stream_threads:
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
