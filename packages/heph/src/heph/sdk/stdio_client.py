"""Client helpers for the SDK JSONL stdio transport."""

from __future__ import annotations

import math
import queue
import subprocess
import threading
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Self

from ai.providers.reasoning import REASONING_LEVELS
from ai.runtime.thinking import THINKING_VISIBILITY_MODES
from hephaion._types import is_string_mapping

from heph.sdk.compatibility import (
    ensure_sdk_client_options,
    ensure_sdk_client_payload_compatibility,
)
from heph.sdk.method_validation import (
    validate_jsonl_message_payload,
    validate_jsonl_request_payload,
    validate_method_params,
    validate_result_payload,
    validate_stream_event_payload,
)
from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    JSONL_CALL_METHOD_SPECS,
    JSONL_CALL_RESULT_SPECS,
    JSONL_STREAM_METHOD_SPECS,
    JSONL_STREAM_SPECS,
    SDK_CAPABILITIES_VERSION,
    SDK_JSONL_CANCELLED_ERROR_CODE,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_STABILITY_PUBLIC,
    SdkMethodSpec,
)
from heph.sdk.runtime import HephSdkError
from heph.sdk.stdio_json import SdkJsonlDecodeError, decode_jsonl_line, encode_jsonl_line

type JsonlRequestId = str | int | None
type JsonlPayload = dict[str, object]
type _StreamControlResult = JsonlPayload | Exception
_DEFAULT_STDERR_TAIL_LIMIT = 16_384


class JsonlSdkClientError(Exception):
    """Base class for client-side JSONL transport failures."""


class JsonlSdkClientProtocolError(JsonlSdkClientError):
    """Raised when the server stream does not match the SDK JSONL protocol."""


class JsonlSdkProcessError(JsonlSdkClientError):
    """Raised when a managed SDK JSONL subprocess cannot be started or used."""


@dataclass(frozen=True, slots=True)
class JsonlSdkErrorPayload:
    """Structured JSONL error returned by the SDK transport."""

    code: str
    message: str
    unavailable_reason: str | None

    def to_dict(self) -> JsonlPayload:
        return {
            "code": self.code,
            "message": self.message,
            "unavailable_reason": self.unavailable_reason,
        }


class JsonlSdkServerError(JsonlSdkClientError):
    """Raised when the SDK JSONL server returns an error envelope."""

    def __init__(self, request_id: JsonlRequestId, error: JsonlSdkErrorPayload) -> None:
        self.request_id = request_id
        self.error = error
        self.code = error.code
        self.unavailable_reason = error.unavailable_reason
        super().__init__(f"SDK JSONL server returned {error.code}: {error.message}")


class JsonlSdkStreamCancelledError(JsonlSdkServerError):
    """Raised when the SDK JSONL server reports stream cancellation."""


@dataclass(slots=True)
class _BoundedTextTail:
    limit: int
    text: str = ""

    def append(self, chunk: str) -> None:
        if self.limit <= 0 or not chunk:
            return
        next_text = self.text + chunk
        self.text = next_text[-self.limit :]


@dataclass(frozen=True, slots=True)
class JsonlSdkProcessOptions:
    """Command-line options for spawning ``heph sdk serve``."""

    executable: str = "heph"
    armory_path: str | Path | None = None
    create_armory: bool = False
    session_id: str | None = None
    start_session: bool = True
    base_url: str | None = None
    model: str | None = None
    max_tokens: int | None = None
    rag_context_budget: int | None = None
    reasoning_level: str | None = None
    temperature: float | None = None
    thinking_visibility: str | None = None

    def command(self) -> tuple[str, ...]:
        """Return the argv tuple for ``heph sdk serve``."""
        self._validate_command_options()
        command = [self.executable, "sdk", "serve"]
        _append_optional_path(command, "--armory", self.armory_path)
        if self.create_armory:
            command.append("--create-armory")
        _append_optional_value(command, "--session-id", self.session_id)
        if not self.start_session:
            command.append("--no-session")
        _append_optional_value(command, "--base-url", self.base_url)
        _append_optional_value(command, "--model", self.model)
        _append_optional_value(command, "--max-tokens", self.max_tokens)
        _append_optional_value(command, "--rag-context-budget", self.rag_context_budget)
        _append_optional_value(command, "--reasoning-level", self.reasoning_level)
        _append_optional_value(command, "--thinking-visibility", self.thinking_visibility)
        _append_optional_value(command, "--temperature", self.temperature)
        return tuple(command)

    def _validate_command_options(self) -> None:
        if self.session_id is not None and not self.start_session:
            raise JsonlSdkProcessError("--session-id cannot be used with start_session=False.")
        if self.create_armory and self.armory_path is None:
            raise JsonlSdkProcessError("create_armory=True requires an armory_path.")
        _validate_process_required_string_option(self.executable, "executable")
        _validate_process_path_option(self.armory_path, "armory_path")
        _validate_process_string_option(self.session_id, "session_id")
        _validate_process_string_option(self.base_url, "base_url")
        _validate_process_string_option(self.model, "model")
        _validate_process_choice_option(
            self.reasoning_level,
            "reasoning_level",
            REASONING_LEVELS,
        )
        _validate_process_choice_option(
            self.thinking_visibility,
            "thinking_visibility",
            THINKING_VISIBILITY_MODES,
        )
        _validate_process_integer_option(self.max_tokens, "max_tokens")
        _validate_process_integer_option(self.rag_context_budget, "rag_context_budget")
        _validate_process_number_option(self.temperature, "temperature")


@dataclass(slots=True)
class JsonlSdkProcess:
    """Manage a ``heph sdk serve`` subprocess and its validated JSONL client."""

    options: JsonlSdkProcessOptions = field(default_factory=JsonlSdkProcessOptions)
    command: tuple[str, ...] | None = None
    client_capabilities_version: int = SDK_CAPABILITIES_VERSION
    jsonl_version: int = SDK_JSONL_VERSION
    accepted_stability_levels: Sequence[str] = (SDK_STABILITY_PUBLIC,)
    startup_timeout: float | None = 10.0
    shutdown_timeout: float = 5.0
    cwd: str | Path | None = None
    env: Mapping[str, str] | None = None
    capture_stderr: bool = True
    stderr_tail_limit: int = _DEFAULT_STDERR_TAIL_LIMIT
    _process: subprocess.Popen[str] | None = field(default=None, init=False, repr=False)
    _client: JsonlSdkClient | None = field(default=None, init=False, repr=False)
    _ready: JsonlSdkReady | None = field(default=None, init=False, repr=False)
    _returncode: int | None = field(default=None, init=False, repr=False)
    _stderr_tail: _BoundedTextTail | None = field(default=None, init=False, repr=False)
    _stderr_thread: threading.Thread | None = field(default=None, init=False, repr=False)

    @property
    def process(self) -> subprocess.Popen[str]:
        if self._process is None:
            raise JsonlSdkProcessError("SDK JSONL process is not running.")
        return self._process

    @property
    def client(self) -> JsonlSdkClient:
        if self._client is None:
            raise JsonlSdkProcessError("SDK JSONL process has not started.")
        return self._client

    @property
    def ready(self) -> JsonlSdkReady:
        if self._ready is None:
            raise JsonlSdkProcessError("SDK JSONL ready handshake has not completed.")
        return self._ready

    @property
    def stderr_tail(self) -> str:
        """Return the captured stderr tail for the managed process."""
        if self._stderr_tail is None:
            return ""
        return self._stderr_tail.text

    @property
    def returncode(self) -> int | None:
        """Return the latest known subprocess return code."""
        process = self._process
        if process is not None:
            return process.poll()
        return self._returncode

    def start(self) -> Self:
        """Start the subprocess and read the validated ready handshake."""
        if self._process is not None:
            raise JsonlSdkProcessError("SDK JSONL process is already running.")
        _validate_process_timeout(self.startup_timeout, "startup_timeout")
        _validate_process_timeout(self.shutdown_timeout, "shutdown_timeout")
        _validate_process_boolean_option(self.capture_stderr, "capture_stderr")
        _validate_process_required_integer_option(self.stderr_tail_limit, "stderr_tail_limit")
        _validate_process_cwd_option(self.cwd)
        _validate_process_env_option(self.env)
        ensure_sdk_client_options(
            client_capabilities_version=self.client_capabilities_version,
            jsonl_version=self.jsonl_version,
            accepted_stability_levels=self.accepted_stability_levels,
        )
        self._returncode = None
        process = self._spawn_process()
        stdout, stdin = self._process_pipes(process)
        self._process = process
        self._start_stderr_capture(process.stderr)
        self._client = JsonlSdkClient(
            input_stream=stdout,
            output_stream=stdin,
            client_capabilities_version=self.client_capabilities_version,
            jsonl_version=self.jsonl_version,
            accepted_stability_levels=self.accepted_stability_levels,
        )
        self._read_ready_or_close()
        return self

    def _spawn_process(self) -> subprocess.Popen[str]:
        try:
            return subprocess.Popen(
                self._command_for_spawn(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                cwd=str(self.cwd) if self.cwd is not None else None,
                env=dict(self.env) if self.env is not None else None,
                stderr=subprocess.PIPE if self.capture_stderr else None,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise JsonlSdkProcessError(f"Failed to start SDK JSONL process: {exc}") from exc

    def _command_for_spawn(self) -> tuple[str, ...]:
        if self.command is None:
            return self.options.command()
        return _validate_process_command(self.command)

    def _process_pipes(self, process: subprocess.Popen[str]) -> tuple[IO[str], IO[str]]:
        if process.stdin is None or process.stdout is None:
            _kill_and_wait_for_process(
                process,
                timeout=self.shutdown_timeout,
                reason="stdin/stdout pipes were unavailable",
            )
            raise JsonlSdkProcessError("SDK JSONL process did not expose stdin/stdout pipes.")
        return process.stdout, process.stdin

    def _read_ready_or_close(self) -> None:
        client = self._client
        if client is None:
            raise JsonlSdkProcessError("SDK JSONL process has not started.")
        try:
            self._ready = _read_ready_with_timeout(client, self.startup_timeout)
        except (JsonlSdkClientProtocolError, JsonlSdkProcessError) as exc:
            self.close()
            if stderr_tail := self.stderr_tail.strip():
                raise JsonlSdkProcessError(
                    _startup_error_with_stderr(str(exc), stderr_tail)
                ) from exc
            raise
        except Exception:
            self.close()
            raise

    def close(self, timeout: float | None = None) -> None:
        """Close stdin and wait for the subprocess, killing it after the timeout."""
        process = self._process
        if process is None:
            return
        client = self._client
        wait_timeout = self.shutdown_timeout if timeout is None else timeout
        _validate_process_timeout(wait_timeout, "close timeout")
        try:
            if client is not None:
                client.close()
            self._close_process_stream(process.stdin)
            if process.poll() is None:
                try:
                    process.wait(timeout=wait_timeout)
                except subprocess.TimeoutExpired:
                    _kill_and_wait_for_process(
                        process,
                        timeout=wait_timeout,
                        reason="shutdown timeout",
                    )
        finally:
            self._returncode = process.poll()
            self._join_stderr_thread(wait_timeout)
            self._close_process_stream(process.stdout)
            self._close_process_stream(process.stderr)
            self._process = None
            self._client = None
            self._ready = None
            self._stderr_thread = None

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @staticmethod
    def _close_process_stream(stream: IO[str] | None) -> None:
        if stream is None or stream.closed:
            return
        try:
            stream.close()
        except (OSError, ValueError):
            return

    def _start_stderr_capture(self, stream: IO[str] | None) -> None:
        if stream is None:
            self._stderr_tail = None
            self._stderr_thread = None
            return
        tail = _BoundedTextTail(self.stderr_tail_limit)
        self._stderr_tail = tail

        def read_stderr() -> None:
            try:
                while True:
                    chunk = stream.read(1024)
                    if chunk == "":
                        return
                    tail.append(chunk)
            except (OSError, ValueError):
                return

        thread = threading.Thread(
            target=read_stderr,
            name="heph-sdk-jsonl-stderr",
            daemon=True,
        )
        thread.start()
        self._stderr_thread = thread

    def _join_stderr_thread(self, timeout: float | None) -> None:
        thread = self._stderr_thread
        if thread is not None:
            thread.join(timeout=timeout)


@dataclass(frozen=True, slots=True)
class JsonlSdkReady:
    """Initial SDK JSONL ready handshake."""

    protocol: str
    version: int
    capabilities: JsonlPayload
    state: JsonlPayload

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", dict(self.capabilities))
        object.__setattr__(self, "state", dict(self.state))

    def to_dict(self) -> JsonlPayload:
        return {
            "type": "ready",
            "protocol": self.protocol,
            "version": self.version,
            "capabilities": dict(self.capabilities),
            "state": dict(self.state),
        }


type _ReadyResult = JsonlSdkReady | Exception


@dataclass(frozen=True, slots=True)
class _JsonlStreamEnd:
    error: JsonlSdkServerError | None = None


@dataclass(frozen=True, slots=True)
class _JsonlStreamMessage:
    event: JsonlPayload | None = None
    stream_end: _JsonlStreamEnd | None = None


@dataclass(frozen=True, slots=True)
class _StreamControlRequest:
    method: str
    response_queue: queue.Queue[_StreamControlResult] | None = None
    discard_result: bool = False


@dataclass(slots=True)
class JsonlSdkClient:
    """Validated client for the Heph SDK JSONL stdio transport.

    The client validates framing and compatibility for simple calls, streams, and busy-safe
    calls interleaved with an active stream. Advanced GUI clients can still use ``read_message``
    and ``write_request`` directly and route messages by id in their own event loop.
    """

    input_stream: IO[str]
    output_stream: IO[str]
    client_capabilities_version: int = SDK_CAPABILITIES_VERSION
    jsonl_version: int = SDK_JSONL_VERSION
    accepted_stability_levels: Sequence[str] = (SDK_STABILITY_PUBLIC,)
    _request_counter: int = field(default=0, init=False, repr=False)
    _write_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _stream_control_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )
    _active_stream_request_ids: set[str | int] = field(
        default_factory=set,
        init=False,
        repr=False,
    )
    _stream_control_requests: dict[str | int, _StreamControlRequest] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def closed(self) -> bool:
        """Return whether this client helper has been closed."""
        with self._stream_control_lock:
            return self._closed

    def close(self) -> None:
        """Mark the helper closed and release pending stream-control waiters.

        The helper does not own ``input_stream`` or ``output_stream``. Managed
        process callers should close those pipes through ``JsonlSdkProcess``.
        """
        pending_requests = self._close_state()
        close_error = JsonlSdkClientProtocolError("SDK JSONL client is closed.")
        for control_request in pending_requests:
            if control_request.response_queue is None:
                continue
            try:
                control_request.response_queue.put_nowait(close_error)
            except queue.Full:
                continue

    def _close_state(self) -> tuple[_StreamControlRequest, ...]:
        with self._stream_control_lock:
            if self._closed:
                return ()
            self._closed = True
            pending_requests = tuple(self._stream_control_requests.values())
            self._stream_control_requests.clear()
            self._active_stream_request_ids.clear()
            return pending_requests

    def read_ready(self) -> JsonlSdkReady:
        """Read and validate the initial server ready message."""
        message = self.read_message()
        if _message_type(message) != "ready":
            raise JsonlSdkClientProtocolError("Expected SDK JSONL ready message.")
        ready = jsonl_ready_from_message(message)
        if ready.protocol != SDK_JSONL_PROTOCOL:
            raise JsonlSdkClientProtocolError(f"Unsupported SDK JSONL protocol: {ready.protocol}.")
        ensure_sdk_client_payload_compatibility(
            ready.capabilities,
            client_capabilities_version=self.client_capabilities_version,
            jsonl_version=self.jsonl_version,
            accepted_stability_levels=self.accepted_stability_levels,
        )
        if ready.version != self.jsonl_version:
            raise JsonlSdkClientProtocolError(
                f"Unsupported SDK JSONL version {ready.version}; expected {self.jsonl_version}."
            )
        return ready

    def read_message(self) -> JsonlPayload:
        """Read one validated JSONL message from the server stream."""
        self._ensure_open()
        try:
            line = self.input_stream.readline()
        except (OSError, ValueError) as exc:
            raise JsonlSdkClientProtocolError(f"Failed to read SDK JSONL message: {exc}") from exc
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
        with self._write_lock:
            actual_request_id = self._request_id_for_write(method, request_id)
            self._write_request_line(method, params, actual_request_id)
        return actual_request_id

    def abort_active_stream(self, *, request_id: str | int | None = None) -> str | int:
        """Write an abort request for the active stream and return the request id used."""
        with self._write_lock:
            actual_request_id = self._request_id_for_write("abort", request_id)
            self._track_stream_control_request(
                actual_request_id,
                "abort",
                require_active_stream=True,
            )
            try:
                self._write_request_line("abort", None, actual_request_id)
            except Exception:
                self._forget_stream_control_request(actual_request_id)
                raise
        return actual_request_id

    def call_active_stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
        timeout: float | None = None,
    ) -> JsonlPayload:
        """Write a busy-safe call while ``stream()`` is being consumed elsewhere."""
        _validate_client_timeout(timeout, "stream control timeout")
        if method not in BUSY_ALLOWED_CALL_METHODS:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL method '{method}' is not available during an active stream."
            )
        response_queue: queue.Queue[_StreamControlResult] = queue.Queue(maxsize=1)
        with self._write_lock:
            actual_request_id = self._request_id_for_write(method, request_id)
            self._track_stream_control_request(
                actual_request_id,
                method,
                response_queue,
                require_active_stream=True,
            )
            try:
                self._write_request_line(method, params, actual_request_id)
            except Exception:
                self._forget_stream_control_request(actual_request_id)
                raise
        return self._wait_for_stream_control_response(
            actual_request_id,
            response_queue,
            timeout,
        )

    def _request_id_for_write(self, method: str, request_id: str | int | None) -> str | int:
        return request_id if request_id is not None else self._next_request_id(method)

    def _write_request_line(
        self,
        method: str,
        params: Mapping[str, object] | None,
        request_id: str | int,
    ) -> None:
        self._ensure_open()
        try:
            self.output_stream.write(encode_jsonl_request(method, params, request_id=request_id))
            self.output_stream.flush()
        except (OSError, ValueError) as exc:
            raise JsonlSdkClientProtocolError(
                f"Failed to write SDK JSONL request {request_id!r}: {exc}"
            ) from exc

    def call(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> JsonlPayload:
        """Write a call request and read its response payload."""
        validate_jsonl_call_params(method, params)
        self._ensure_no_active_stream_for_call()
        actual_request_id = self.write_request(method, params, request_id=request_id)
        message = self.read_message()
        _require_request_id(message, actual_request_id)
        message_type = _message_type(message)
        if message_type == "error":
            raise _server_error_from_message(actual_request_id, message)
        if message_type != "response":
            raise JsonlSdkClientProtocolError(
                f"Expected SDK JSONL response for {actual_request_id!r}, got {message_type!r}."
            )
        if message.get("ok") is not True:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL response for {actual_request_id!r} was not successful."
            )
        return _validate_jsonl_call_result(
            method,
            _mapping_field(message, "result", "SDK JSONL response result"),
        )

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> Iterator[JsonlPayload]:
        """Write a stream request and yield each stream event payload."""
        validate_jsonl_stream_params(method, params)
        actual_request_id = self._write_stream_request(method, params, request_id=request_id)
        try:
            start = self.read_message()
            _require_request_id(start, actual_request_id)
            start_type = _message_type(start)
            if start_type == "error":
                raise _server_error_from_message(actual_request_id, start)
            if start_type != "stream_start":
                raise JsonlSdkClientProtocolError(
                    f"Expected SDK JSONL stream_start for {actual_request_id!r}, "
                    f"got {start_type!r}."
                )
            if start.get("method") != method:
                raise JsonlSdkClientProtocolError(
                    f"SDK JSONL stream_start for {actual_request_id!r} reported method "
                    f"{start.get('method')!r}, expected {method!r}."
                )
            yield from self._stream_events(actual_request_id, method)
        finally:
            self._forget_active_stream_request(actual_request_id)

    def _write_stream_request(
        self,
        method: str,
        params: Mapping[str, object] | None,
        *,
        request_id: str | int | None,
    ) -> str | int:
        with self._write_lock:
            actual_request_id = self._request_id_for_write(method, request_id)
            self._track_active_stream_request(actual_request_id)
            try:
                self._write_request_line(method, params, actual_request_id)
            except Exception:
                self._forget_active_stream_request(actual_request_id)
                raise
        return actual_request_id

    def _stream_events(self, request_id: str | int, method: str) -> Iterator[JsonlPayload]:
        pending_end: _JsonlStreamEnd | None = None
        while True:
            message = self.read_message()
            if self._consume_stream_control_if_tracked(message):
                if pending_end is not None and not self._has_stream_control_requests():
                    self._finish_pending_stream_end(pending_end)
                    return
                continue
            if pending_end is not None:
                raise JsonlSdkClientProtocolError(
                    "Expected SDK JSONL response for an active stream control request."
                )
            stream_message = self._stream_message_from_payload(request_id, method, message)
            if stream_message.event is not None:
                yield stream_message.event
                continue
            if stream_message.stream_end is not None:
                if not self._has_stream_control_requests():
                    self._finish_pending_stream_end(stream_message.stream_end)
                    return
                pending_end = stream_message.stream_end

    def _next_request_id(self, method: str) -> str:
        self._request_counter += 1
        return f"{method}-{self._request_counter}"

    def _ensure_open(self) -> None:
        with self._stream_control_lock:
            if not self._closed:
                return
        raise JsonlSdkClientProtocolError("SDK JSONL client is closed.")

    def _track_stream_control_request(
        self,
        request_id: str | int,
        method: str,
        response_queue: queue.Queue[_StreamControlResult] | None = None,
        *,
        require_active_stream: bool = False,
    ) -> None:
        with self._stream_control_lock:
            if self._closed:
                raise JsonlSdkClientProtocolError("SDK JSONL client is closed.")
            if require_active_stream and not self._active_stream_request_ids:
                raise JsonlSdkClientProtocolError(
                    "SDK JSONL stream control requests require an active stream reader."
                )
            self._ensure_request_id_available_locked(request_id)
            self._stream_control_requests[request_id] = _StreamControlRequest(
                method=method,
                response_queue=response_queue,
            )

    def _forget_stream_control_request(self, request_id: str | int) -> None:
        with self._stream_control_lock:
            self._stream_control_requests.pop(request_id, None)

    def _discard_stream_control_response(self, request_id: str | int) -> None:
        with self._stream_control_lock:
            control_request = self._stream_control_requests.get(request_id)
            if control_request is None:
                return
            self._stream_control_requests[request_id] = _StreamControlRequest(
                method=control_request.method,
                discard_result=True,
            )

    def _has_stream_control_requests(self) -> bool:
        with self._stream_control_lock:
            return bool(self._stream_control_requests)

    def _track_active_stream_request(self, request_id: str | int) -> None:
        with self._stream_control_lock:
            if self._closed:
                raise JsonlSdkClientProtocolError("SDK JSONL client is closed.")
            if self._active_stream_request_ids:
                raise JsonlSdkClientProtocolError(
                    "Cannot start an SDK JSONL stream while another stream() is active."
                )
            self._ensure_request_id_available_locked(request_id)
            self._active_stream_request_ids.add(request_id)

    def _forget_active_stream_request(self, request_id: str | int) -> None:
        with self._stream_control_lock:
            self._active_stream_request_ids.discard(request_id)

    def _ensure_no_active_stream_for_call(self) -> None:
        with self._stream_control_lock:
            if not self._active_stream_request_ids:
                return
        raise JsonlSdkClientProtocolError(
            "Cannot use JsonlSdkClient.call() while stream() is active; use "
            "call_active_stream() for busy-safe methods."
        )

    def _ensure_request_id_available_locked(self, request_id: str | int) -> None:
        if request_id in self._active_stream_request_ids:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL request id {request_id!r} is already in use by an active stream."
            )
        if request_id in self._stream_control_requests:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL request id {request_id!r} is already in use by "
                "an active stream control request."
            )

    def _consume_stream_control_if_tracked(self, message: Mapping[str, object]) -> bool:
        control_request_id = self._stream_control_request_id(message)
        if control_request_id is None:
            return False
        self._consume_stream_control_message(control_request_id, message)
        return True

    def _stream_message_from_payload(
        self,
        request_id: str | int,
        method: str,
        message: Mapping[str, object],
    ) -> _JsonlStreamMessage:
        _require_request_id(message, request_id)
        message_type = _message_type(message)
        if message_type == "stream_event":
            return _JsonlStreamMessage(
                event=_validate_jsonl_stream_event(
                    method,
                    _mapping_field(message, "event", "SDK JSONL stream event"),
                )
            )
        if message_type == "stream_end":
            return _JsonlStreamMessage(
                stream_end=self._stream_end_from_message(request_id, message)
            )
        if message_type == "error":
            raise _server_error_from_message(request_id, message)
        raise JsonlSdkClientProtocolError(
            f"Expected SDK JSONL stream_event or stream_end for {request_id!r}, got "
            f"{message_type!r}."
        )

    def _stream_end_from_message(
        self,
        request_id: str | int,
        message: Mapping[str, object],
    ) -> _JsonlStreamEnd:
        if message.get("ok") is True:
            return _JsonlStreamEnd()
        return _JsonlStreamEnd(error=_server_error_from_message(request_id, message))

    @staticmethod
    def _finish_pending_stream_end(stream_end: _JsonlStreamEnd) -> None:
        if stream_end.error is not None:
            raise stream_end.error

    def _stream_control_request_id(self, message: Mapping[str, object]) -> str | int | None:
        request_id = message.get("id")
        if not isinstance(request_id, (str, int)) or isinstance(request_id, bool):
            return None
        with self._stream_control_lock:
            if request_id in self._stream_control_requests:
                return request_id
        return None

    def _consume_stream_control_message(
        self,
        request_id: str | int,
        message: Mapping[str, object],
    ) -> None:
        control_request = self._stream_control_request(request_id)
        try:
            result = self._stream_control_result(request_id, control_request.method, message)
            self._publish_stream_control_result(control_request, result)
        finally:
            self._forget_stream_control_request(request_id)

    def _stream_control_request(self, request_id: str | int) -> _StreamControlRequest:
        with self._stream_control_lock:
            control_request = self._stream_control_requests.get(request_id)
        if control_request is None:
            raise JsonlSdkClientProtocolError(
                f"SDK JSONL stream control request {request_id!r} is not active."
            )
        return control_request

    def _stream_control_result(
        self,
        request_id: str | int,
        method: str,
        message: Mapping[str, object],
    ) -> _StreamControlResult:
        message_type = _message_type(message)
        if message_type == "response":
            if message.get("ok") is not True:
                return JsonlSdkClientProtocolError(
                    f"SDK JSONL response for {request_id!r} was not successful."
                )
            return _validate_jsonl_call_result(
                method,
                _mapping_field(message, "result", "SDK JSONL response result"),
            )
        if message_type == "error":
            return _server_error_from_message(request_id, message)
        return JsonlSdkClientProtocolError(
            f"Expected SDK JSONL response for stream control request {request_id!r}, "
            f"got {message_type!r}."
        )

    @staticmethod
    def _publish_stream_control_result(
        control_request: _StreamControlRequest,
        result: _StreamControlResult,
    ) -> None:
        if control_request.discard_result:
            return
        if control_request.response_queue is None:
            if isinstance(result, Exception):
                raise result
            return
        control_request.response_queue.put(result)

    def _wait_for_stream_control_response(
        self,
        request_id: str | int,
        response_queue: queue.Queue[_StreamControlResult],
        timeout: float | None,
    ) -> JsonlPayload:
        _validate_client_timeout(timeout, "stream control timeout")
        try:
            result = response_queue.get(timeout=timeout)
        except queue.Empty as exc:
            self._discard_stream_control_response(request_id)
            raise JsonlSdkClientProtocolError(
                f"Timed out waiting for SDK JSONL stream control response {request_id!r}."
            ) from exc
        if isinstance(result, Exception):
            raise result
        return result


def jsonl_request_payload(
    method: str,
    params: Mapping[str, object] | None = None,
    *,
    request_id: JsonlRequestId = None,
) -> JsonlPayload:
    """Build and validate a JSON-ready SDK JSONL request payload."""
    _validate_jsonl_request_envelope(method, request_id)
    parameters = validate_jsonl_request_params(method, params)
    payload: JsonlPayload = {"method": method}
    if request_id is not None:
        payload["id"] = request_id
    if params is not None:
        payload["params"] = parameters
    try:
        return validate_jsonl_request_payload(payload)
    except HephSdkError as exc:
        raise JsonlSdkClientProtocolError(str(exc)) from exc


def _validate_jsonl_request_envelope(method: object, request_id: JsonlRequestId) -> None:
    if not isinstance(method, str) or not method.strip():
        raise JsonlSdkClientProtocolError("SDK JSONL request method must be a non-empty string.")
    _raise_if_jsonl_request_null_string(method, "SDK JSONL request method")
    if request_id is None:
        return
    if isinstance(request_id, str):
        _raise_if_jsonl_request_null_string(request_id, "SDK JSONL request id")
        return
    if isinstance(request_id, int) and not isinstance(request_id, bool):
        return
    raise JsonlSdkClientProtocolError("SDK JSONL request id must be a string, integer, or null.")


def _raise_if_jsonl_request_null_string(value: str, label: str) -> None:
    if "\0" not in value:
        return
    raise JsonlSdkClientProtocolError(f"{label} must not contain null bytes.")


def validate_jsonl_request_params(
    method: str,
    params: Mapping[str, object] | None = None,
) -> JsonlPayload:
    """Validate request params against the advertised JSONL method specs."""
    return _validate_jsonl_params(
        method,
        params,
        _jsonl_request_method_specs(method),
        surface="SDK JSONL",
    )


def validate_jsonl_call_params(
    method: str,
    params: Mapping[str, object] | None = None,
) -> JsonlPayload:
    """Validate params for a JSONL call method."""
    return _validate_jsonl_params(
        method,
        params,
        _jsonl_call_method_specs(method),
        surface="SDK JSONL call",
    )


def validate_jsonl_stream_params(
    method: str,
    params: Mapping[str, object] | None = None,
) -> JsonlPayload:
    """Validate params for a JSONL stream method."""
    return _validate_jsonl_params(
        method,
        params,
        _jsonl_stream_method_specs(method),
        surface="SDK JSONL stream",
    )


def _validate_jsonl_call_result(method: str, result: Mapping[str, object]) -> JsonlPayload:
    try:
        return validate_result_payload(
            method,
            result,
            JSONL_CALL_RESULT_SPECS,
            surface="SDK JSONL client",
        )
    except HephSdkError as exc:
        raise JsonlSdkClientProtocolError(str(exc)) from exc


def _validate_jsonl_stream_event(method: str, event: Mapping[str, object]) -> JsonlPayload:
    try:
        return validate_stream_event_payload(
            method,
            event,
            JSONL_STREAM_SPECS,
            surface="SDK JSONL client",
        )
    except HephSdkError as exc:
        raise JsonlSdkClientProtocolError(str(exc)) from exc


def _validate_jsonl_params(
    method: str,
    params: Mapping[str, object] | None,
    specs: tuple[SdkMethodSpec, ...],
    *,
    surface: str,
) -> JsonlPayload:
    if not specs:
        raise JsonlSdkClientProtocolError(f"Unknown {surface} method: {method}")
    try:
        return validate_method_params(
            method,
            params,
            specs,
            surface=f"{surface} client",
        )
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
    try:
        return encode_jsonl_line(payload)
    except ValueError as exc:
        raise JsonlSdkClientProtocolError(
            f"SDK JSONL request payload is not strict JSON: {exc}"
        ) from exc


def parse_jsonl_message(line: str) -> JsonlPayload:
    """Parse and validate one JSONL message from the SDK server."""
    if not line.strip():
        raise JsonlSdkClientProtocolError("SDK JSONL messages must not be empty.")
    try:
        parsed = decode_jsonl_line(line)
    except SdkJsonlDecodeError as exc:
        raise JsonlSdkClientProtocolError(f"Invalid SDK JSONL message: {exc}") from exc
    if not is_string_mapping(parsed):
        raise JsonlSdkClientProtocolError("SDK JSONL messages must be JSON objects.")
    try:
        return validate_jsonl_message_payload(
            parsed,
            allow_unknown_capability_fields=True,
            allow_unknown_ready_state_fields=True,
        )
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


def _server_error_from_message(
    request_id: str | int,
    message: Mapping[str, object],
) -> JsonlSdkServerError:
    error = jsonl_error_from_message(message)
    if error.code == SDK_JSONL_CANCELLED_ERROR_CODE:
        return JsonlSdkStreamCancelledError(request_id, error)
    return JsonlSdkServerError(request_id, error)


def _startup_error_with_stderr(message: str, stderr_tail: str) -> str:
    clean_message = message.rstrip(".")
    return f"{clean_message}. SDK JSONL process stderr:\n{stderr_tail}"


def _read_ready_with_timeout(
    client: JsonlSdkClient,
    timeout: float | None,
) -> JsonlSdkReady:
    _validate_process_timeout(timeout, "startup_timeout")
    if timeout is None:
        return client.read_ready()
    results: queue.Queue[_ReadyResult] = queue.Queue(maxsize=1)

    def read_ready() -> None:
        try:
            results.put(client.read_ready())
        except Exception as exc:
            results.put(exc)

    thread = threading.Thread(
        target=read_ready,
        name="heph-sdk-jsonl-ready",
        daemon=True,
    )
    thread.start()
    try:
        result = results.get(timeout=timeout)
    except queue.Empty as exc:
        raise JsonlSdkProcessError(
            f"SDK JSONL process did not send ready within {timeout:g} seconds."
        ) from exc
    if isinstance(result, Exception):
        raise result
    return result


def _kill_and_wait_for_process(
    process: subprocess.Popen[str],
    *,
    timeout: float | None,
    reason: str,
) -> None:
    process.kill()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise JsonlSdkProcessError(
            "SDK JSONL process did not exit after kill "
            f"({reason}; timeout={_timeout_label(timeout)})."
        ) from exc


def _timeout_label(timeout: float | None) -> str:
    if timeout is None:
        return "none"
    return f"{timeout:g}s"


def _validate_process_timeout(timeout: float | None, label: str) -> None:
    if issue := _timeout_issue(timeout, label):
        raise JsonlSdkProcessError(issue)


def _validate_client_timeout(timeout: float | None, label: str) -> None:
    if issue := _timeout_issue(timeout, label):
        raise JsonlSdkClientProtocolError(issue)


def _timeout_issue(timeout: object, label: str) -> str | None:
    if timeout is None:
        return None
    timeout_value = _timeout_number(timeout)
    if timeout_value is None:
        return f"SDK JSONL {label} must be a finite non-negative number or None."
    return _numeric_timeout_issue(timeout_value, label)


def _timeout_number(timeout: object) -> float | None:
    if isinstance(timeout, bool) or not isinstance(timeout, int | float):
        return None
    try:
        return float(timeout)
    except OverflowError:
        return math.inf


def _numeric_timeout_issue(timeout: float, label: str) -> str | None:
    if not math.isfinite(timeout):
        return f"SDK JSONL {label} must be finite."
    if timeout < 0:
        return f"SDK JSONL {label} must be non-negative."
    return None


def _validate_process_integer_option(value: object, label: str) -> None:
    if value is None:
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if value < 0:
            raise JsonlSdkProcessError(f"SDK JSONL process option '{label}' must be non-negative.")
        return
    raise JsonlSdkProcessError(f"SDK JSONL process option '{label}' must be an integer or None.")


def _validate_process_required_integer_option(value: object, label: str) -> None:
    if isinstance(value, int) and not isinstance(value, bool):
        if value < 0:
            raise JsonlSdkProcessError(f"SDK JSONL process option '{label}' must be non-negative.")
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be a non-negative integer."
    )


def _validate_process_boolean_option(value: object, label: str) -> None:
    if isinstance(value, bool):
        return
    raise JsonlSdkProcessError(f"SDK JSONL process option '{label}' must be a boolean.")


def _validate_process_command(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise JsonlSdkProcessError(
            "SDK JSONL process command must be a non-empty sequence of strings."
        )
    command = tuple(value)
    if not command:
        raise JsonlSdkProcessError("SDK JSONL process command must not be empty.")
    executable = command[0]
    if not isinstance(executable, str) or not executable.strip():
        raise JsonlSdkProcessError("SDK JSONL process command executable must be non-empty.")
    if "\0" in executable:
        raise JsonlSdkProcessError(
            "SDK JSONL process command executable must not contain null bytes."
        )
    validated_command = [executable]
    for item in command[1:]:
        if not isinstance(item, str):
            raise JsonlSdkProcessError("SDK JSONL process command arguments must be strings.")
        if "\0" in item:
            raise JsonlSdkProcessError(
                "SDK JSONL process command arguments must not contain null bytes."
            )
        validated_command.append(item)
    return tuple(validated_command)


def _validate_process_cwd_option(value: object) -> None:
    if value is None:
        return
    if isinstance(value, Path):
        if "\0" not in str(value):
            return
    elif isinstance(value, str) and value.strip() and "\0" not in value:
        return
    raise JsonlSdkProcessError(
        "SDK JSONL process cwd must be a non-empty path string, Path, or None without null bytes."
    )


def _validate_process_env_option(value: object) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise JsonlSdkProcessError("SDK JSONL process env must be a mapping or None.")
    for key, item in value.items():
        if not isinstance(key, str) or not key or "=" in key or "\0" in key:
            raise JsonlSdkProcessError(
                "SDK JSONL process env keys must be non-empty strings without '=' or null bytes."
            )
        if not isinstance(item, str):
            raise JsonlSdkProcessError("SDK JSONL process env values must be strings.")
        if "\0" in item:
            raise JsonlSdkProcessError("SDK JSONL process env values must not contain null bytes.")


def _validate_process_string_option(value: object, label: str) -> None:
    if value is None:
        return
    if isinstance(value, str) and value.strip() and "\0" not in value:
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be a non-empty string without "
        "null bytes or None."
    )


def _validate_process_required_string_option(value: object, label: str) -> None:
    if isinstance(value, str) and value.strip() and "\0" not in value:
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be a non-empty string without null bytes."
    )


def _validate_process_path_option(value: object, label: str) -> None:
    if value is None:
        return
    if isinstance(value, Path):
        if "\0" not in str(value):
            return
    elif isinstance(value, str) and value.strip() and "\0" not in value:
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be a non-empty path string, Path, "
        "or None without null bytes."
    )


def _validate_process_choice_option(
    value: object,
    label: str,
    choices: tuple[str, ...],
) -> None:
    _validate_process_string_option(value, label)
    if value is None or value in choices:
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be one of: {', '.join(choices)}."
    )


def _validate_process_number_option(value: object, label: str) -> None:
    if value is None:
        return
    number = _timeout_number(value)
    if number is not None and math.isfinite(number):
        return
    raise JsonlSdkProcessError(
        f"SDK JSONL process option '{label}' must be a finite number or None."
    )


def _jsonl_request_method_specs(method: str) -> tuple[SdkMethodSpec, ...]:
    return tuple(
        spec
        for spec in (*JSONL_CALL_METHOD_SPECS, *JSONL_STREAM_METHOD_SPECS)
        if spec.method == method
    )


def _jsonl_call_method_specs(method: str) -> tuple[SdkMethodSpec, ...]:
    return tuple(spec for spec in JSONL_CALL_METHOD_SPECS if spec.method == method)


def _jsonl_stream_method_specs(method: str) -> tuple[SdkMethodSpec, ...]:
    return tuple(spec for spec in JSONL_STREAM_METHOD_SPECS if spec.method == method)


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


def _append_optional_path(command: list[str], flag: str, value: str | Path | None) -> None:
    if value is not None:
        command.extend((flag, str(Path(value).expanduser())))


def _append_optional_value(
    command: list[str],
    flag: str,
    value: str | float | None,
) -> None:
    if value is not None:
        command.extend((flag, str(value)))
