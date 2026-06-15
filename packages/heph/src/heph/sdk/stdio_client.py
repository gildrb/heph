"""Client helpers for the SDK JSONL stdio transport."""

from __future__ import annotations

import json
import queue
import subprocess
import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Self

from hephaion._types import is_string_mapping

from heph.sdk.compatibility import ensure_sdk_client_payload_compatibility
from heph.sdk.method_validation import (
    validate_jsonl_message_payload,
    validate_jsonl_request_payload,
    validate_method_params,
)
from heph.sdk.methods import (
    JSONL_CALL_METHOD_SPECS,
    JSONL_STREAM_METHOD_SPECS,
    SDK_CAPABILITIES_VERSION,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SdkMethodSpec,
)
from heph.sdk.runtime import HephSdkError

type JsonlRequestId = str | int | None
type JsonlPayload = dict[str, object]
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


class JsonlSdkServerError(JsonlSdkClientError):
    """Raised when the SDK JSONL server returns an error envelope."""

    def __init__(self, request_id: JsonlRequestId, error: JsonlSdkErrorPayload) -> None:
        self.request_id = request_id
        self.error = error
        self.code = error.code
        self.unavailable_reason = error.unavailable_reason
        super().__init__(f"SDK JSONL server returned {error.code}: {error.message}")


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
        if self.session_id is not None and not self.start_session:
            raise JsonlSdkProcessError("--session-id cannot be used with start_session=False.")
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


@dataclass(slots=True)
class JsonlSdkProcess:
    """Manage a ``heph sdk serve`` subprocess and its validated JSONL client."""

    options: JsonlSdkProcessOptions = field(default_factory=JsonlSdkProcessOptions)
    command: tuple[str, ...] | None = None
    client_capabilities_version: int = SDK_CAPABILITIES_VERSION
    jsonl_version: int = SDK_JSONL_VERSION
    startup_timeout: float | None = 10.0
    shutdown_timeout: float = 5.0
    cwd: str | Path | None = None
    env: Mapping[str, str] | None = None
    capture_stderr: bool = True
    stderr_tail_limit: int = _DEFAULT_STDERR_TAIL_LIMIT
    _process: subprocess.Popen[str] | None = field(default=None, init=False, repr=False)
    _client: JsonlSdkClient | None = field(default=None, init=False, repr=False)
    _ready: JsonlSdkReady | None = field(default=None, init=False, repr=False)
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

    def start(self) -> Self:
        """Start the subprocess and read the validated ready handshake."""
        if self._process is not None:
            raise JsonlSdkProcessError("SDK JSONL process is already running.")
        process = self._spawn_process()
        stdout, stdin = self._process_pipes(process)
        self._process = process
        self._start_stderr_capture(process.stderr)
        self._client = JsonlSdkClient(
            input_stream=stdout,
            output_stream=stdin,
            client_capabilities_version=self.client_capabilities_version,
            jsonl_version=self.jsonl_version,
        )
        self._read_ready_or_close()
        return self

    def _spawn_process(self) -> subprocess.Popen[str]:
        try:
            return subprocess.Popen(
                self.command or self.options.command(),
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

    def _process_pipes(self, process: subprocess.Popen[str]) -> tuple[IO[str], IO[str]]:
        if process.stdin is None or process.stdout is None:
            process.kill()
            process.wait(timeout=self.shutdown_timeout)
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
        wait_timeout = self.shutdown_timeout if timeout is None else timeout
        try:
            self._close_process_stdin(process)
            if process.poll() is None:
                try:
                    process.wait(timeout=wait_timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=wait_timeout)
        finally:
            self._join_stderr_thread(wait_timeout)
            self._close_process_stdout(process)
            self._close_process_stderr(process)
            self._process = None
            self._client = None
            self._ready = None
            self._stderr_thread = None

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @staticmethod
    def _close_process_stdin(process: subprocess.Popen[str]) -> None:
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()

    @staticmethod
    def _close_process_stdout(process: subprocess.Popen[str]) -> None:
        if process.stdout is not None and not process.stdout.closed:
            process.stdout.close()

    @staticmethod
    def _close_process_stderr(process: subprocess.Popen[str]) -> None:
        if process.stderr is not None and not process.stderr.closed:
            process.stderr.close()

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


type _ReadyResult = JsonlSdkReady | Exception


@dataclass(slots=True)
class JsonlSdkClient:
    """Small sequential client for the Heph SDK JSONL stdio transport.

    The client validates framing and compatibility for the simple one-request-at-a-time path.
    Advanced GUI clients can still use ``read_message`` and ``write_request`` directly and route
    messages by id in their own event loop.
    """

    input_stream: IO[str]
    output_stream: IO[str]
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


def validate_jsonl_request_params(
    method: str,
    params: Mapping[str, object] | None = None,
) -> JsonlPayload:
    """Validate request params against the advertised JSONL method specs."""
    specs = _jsonl_request_method_specs(method)
    if not specs:
        raise JsonlSdkClientProtocolError(f"Unknown SDK JSONL method: {method}")
    try:
        return validate_method_params(
            method,
            params,
            specs,
            surface="SDK JSONL client",
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


def _startup_error_with_stderr(message: str, stderr_tail: str) -> str:
    clean_message = message.rstrip(".")
    return f"{clean_message}. SDK JSONL process stderr:\n{stderr_tail}"


def _read_ready_with_timeout(
    client: JsonlSdkClient,
    timeout: float | None,
) -> JsonlSdkReady:
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


def _jsonl_request_method_specs(method: str) -> tuple[SdkMethodSpec, ...]:
    return tuple(
        spec
        for spec in (*JSONL_CALL_METHOD_SPECS, *JSONL_STREAM_METHOD_SPECS)
        if spec.method == method
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


def _append_optional_path(command: list[str], flag: str, value: str | Path | None) -> None:
    if value is not None:
        command.extend((flag, str(value)))


def _append_optional_value(
    command: list[str],
    flag: str,
    value: str | float | None,
) -> None:
    if value is not None:
        command.extend((flag, str(value)))
