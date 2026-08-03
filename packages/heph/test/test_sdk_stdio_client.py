from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping
from dataclasses import fields
from pathlib import Path
from typing import cast

import pytest
from ai.runtime import ChatConfig
from harness.chat.events import AssistantDeltaEvent, TurnCompleteEvent, TurnEvent
from harness.chat.session import ChatSession
from heph.sdk import (
    SDK_CAPABILITIES_VERSION,
    SDK_JSONL_CANCELLED_ERROR_CODE,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_STABILITY_PREVIEW,
    SDK_STABILITY_PUBLIC,
    HephSdkOptions,
    HephService,
    JsonlSdkClient,
    JsonlSdkClientProtocolError,
    JsonlSdkErrorPayload,
    JsonlSdkProcess,
    JsonlSdkProcessError,
    JsonlSdkProcessOptions,
    JsonlSdkReady,
    JsonlSdkServer,
    JsonlSdkServerError,
    JsonlSdkStreamCancelledError,
    SdkClientCompatibilityError,
    parse_jsonl_message,
    validate_jsonl_call_params,
    validate_jsonl_request_params,
    validate_jsonl_stream_params,
)
from heph.sdk import runtime as sdk_runtime
from heph.sdk.stdio_json import encode_jsonl_line


def _config() -> ChatConfig:
    return ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini")


def _jsonl(*requests: dict[str, object]) -> str:
    return "\n".join(json.dumps(request) for request in requests) + "\n"


def _payload_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return {str(key): item for key, item in value.items()}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _source_python_path(repo_root: Path, environment: Mapping[str, str]) -> str:
    source_roots = (
        repo_root / "packages" / "ai" / "src",
        repo_root / "packages" / "extensions" / "src",
        repo_root / "packages" / "harness" / "src",
        repo_root / "packages" / "heph" / "src",
        repo_root / "packages" / "interfaces" / "src",
    )
    entries = [str(path) for path in source_roots]
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        entries.append(existing_python_path)
    return os.pathsep.join(entries)


def _real_sdk_serve_environment(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir()
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    environment["HARNESS_DISABLE_LIVE_MODELS"] = "1"
    environment["HARNESS_NO_VENV_REEXEC"] = "1"
    environment["PYTHONPATH"] = _source_python_path(_repo_root(), environment)
    return environment


def _ready_message(service: HephService) -> dict[str, object]:
    return {
        "type": "ready",
        "protocol": SDK_JSONL_PROTOCOL,
        "version": SDK_JSONL_VERSION,
        "capabilities": service.capabilities()["capabilities"],
        "state": service.state(),
    }


def _wait_for_output(output: io.StringIO, needle: str) -> None:
    deadline = time.monotonic() + 2.0
    while needle not in output.getvalue() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert needle in output.getvalue()


def _written_requests(output: io.StringIO) -> list[dict[str, object]]:
    return [_payload_mapping(json.loads(line)) for line in output.getvalue().splitlines()]


def test_jsonl_sdk_client_reads_ready_call_and_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    service.new_session()

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = abort
        assert prompt == "hello sdk"
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "hello native app")
        raw_session.dirty = True
        yield AssistantDeltaEvent("hello native app")
        yield TurnCompleteEvent("hello native app", 0, 1.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    server_output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {"id": "state-1", "method": "state"},
                {"id": "turn-1", "method": "prompt", "params": {"text": "hello sdk"}},
            )
        ),
        output_stream=server_output,
    )
    server.serve()

    client_output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(server_output.getvalue()),
        output_stream=client_output,
    )

    ready = client.read_ready()
    state = client.call("state", request_id="state-1")
    stream_events = tuple(client.stream("prompt", {"text": "hello sdk"}, request_id="turn-1"))

    written_requests = [
        _payload_mapping(json.loads(line)) for line in client_output.getvalue().splitlines()
    ]
    state_service = _payload_mapping(state["service"])

    assert ready.protocol == SDK_JSONL_PROTOCOL
    assert ready.version == SDK_JSONL_VERSION
    assert ready.capabilities["version"] == SDK_CAPABILITIES_VERSION
    assert state_service["available_stream_methods"] == ["prompt"]
    assert stream_events[0] == {"type": "assistant_delta", "delta": "hello native app"}
    assert stream_events[-1]["type"] == "turn_complete"
    assert written_requests == [
        {"method": "state", "id": "state-1"},
        {"method": "prompt", "id": "turn-1", "params": {"text": "hello sdk"}},
    ]


def test_jsonl_sdk_client_raises_server_error_for_call() -> None:
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {
                    "type": "error",
                    "id": "ask-1",
                    "ok": False,
                    "error": {
                        "code": "unavailable",
                        "message": "No active SDK session.",
                        "unavailable_reason": "missing_session",
                    },
                }
            )
        ),
        output_stream=io.StringIO(),
    )

    with pytest.raises(JsonlSdkServerError, match="SDK JSONL server returned unavailable") as exc:
        client.call("ask", {"text": "hello"}, request_id="ask-1")

    assert exc.value.request_id == "ask-1"
    assert exc.value.code == "unavailable"
    assert exc.value.unavailable_reason == "missing_session"


def test_jsonl_sdk_client_validates_request_params_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="request method"):
        client.write_request("")
    with pytest.raises(JsonlSdkClientProtocolError, match=r"request method.*null bytes"):
        client.write_request("state\0")
    with pytest.raises(JsonlSdkClientProtocolError, match="request id"):
        client.write_request("state", request_id=cast("str | int | None", True))
    with pytest.raises(JsonlSdkClientProtocolError, match=r"request id.*null bytes"):
        client.write_request("state", request_id="bad\0id")
    with pytest.raises(JsonlSdkClientProtocolError, match="requires parameter: text"):
        client.write_request("prompt")
    with pytest.raises(JsonlSdkClientProtocolError, match="does not accept parameter: extra"):
        client.write_request("state", {"extra": True})
    with pytest.raises(JsonlSdkClientProtocolError, match="Unknown SDK JSONL method"):
        client.write_request("missing_method")

    assert output.getvalue() == ""


def test_jsonl_request_param_validation_returns_normalized_params() -> None:
    assert validate_jsonl_request_params("prompt", {"text": "hello"}) == {"text": "hello"}
    assert validate_jsonl_request_params("state") == {}
    assert validate_jsonl_call_params("state") == {}
    assert validate_jsonl_stream_params("prompt", {"text": "hello"}) == {"text": "hello"}


def test_jsonl_client_call_and_stream_validate_method_category_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="Unknown SDK JSONL call method"):
        client.call("prompt", {"text": "hello"})
    with pytest.raises(JsonlSdkClientProtocolError, match="Unknown SDK JSONL stream method"):
        tuple(client.stream("state"))

    assert output.getvalue() == ""


def test_jsonl_sdk_client_validates_call_result_payload() -> None:
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {
                    "type": "response",
                    "id": "state-1",
                    "ok": True,
                    "result": {"service": {}},
                }
            )
        ),
        output_stream=io.StringIO(),
    )

    with pytest.raises(
        JsonlSdkClientProtocolError,
        match=r"SDK JSONL client method 'state'",
    ):
        client.call("state", request_id="state-1")


def test_jsonl_sdk_client_validates_stream_event_contract() -> None:
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {"type": "assistant_delta", "delta": "wrong stream"},
                },
            )
        ),
        output_stream=io.StringIO(),
    )

    with pytest.raises(
        JsonlSdkClientProtocolError,
        match="does not advertise event type: assistant_delta",
    ):
        tuple(client.stream("build_index_stream", request_id="index-1"))


def test_jsonl_sdk_client_raises_server_error_for_stream_end() -> None:
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "turn-1", "method": "prompt"},
                {
                    "type": "stream_end",
                    "id": "turn-1",
                    "ok": False,
                    "error": {
                        "code": "engine_error",
                        "message": "model failed",
                        "unavailable_reason": None,
                    },
                },
            )
        ),
        output_stream=io.StringIO(),
    )

    with pytest.raises(JsonlSdkServerError, match="SDK JSONL server returned engine_error"):
        tuple(client.stream("prompt", {"text": "hello"}, request_id="turn-1"))


def test_jsonl_sdk_client_raises_cancelled_error_for_stream_end() -> None:
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_end",
                    "id": "index-1",
                    "ok": False,
                    "error": {
                        "code": SDK_JSONL_CANCELLED_ERROR_CODE,
                        "message": "SDK operation was cancelled.",
                        "unavailable_reason": None,
                    },
                },
            )
        ),
        output_stream=io.StringIO(),
    )

    with pytest.raises(
        JsonlSdkStreamCancelledError,
        match="SDK JSONL server returned cancelled",
    ) as exc:
        tuple(client.stream("build_index_stream", request_id="index-1"))

    assert isinstance(exc.value, JsonlSdkServerError)
    assert exc.value.code == SDK_JSONL_CANCELLED_ERROR_CODE
    assert exc.value.unavailable_reason is None


def test_jsonl_sdk_client_consumes_abort_response_during_stream() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {
                    "type": "response",
                    "id": "abort-1",
                    "ok": True,
                    "result": {"aborted": True, "state": state},
                },
                {
                    "type": "stream_end",
                    "id": "index-1",
                    "ok": False,
                    "error": {
                        "code": SDK_JSONL_CANCELLED_ERROR_CODE,
                        "message": "SDK operation was cancelled.",
                        "unavailable_reason": None,
                    },
                },
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    assert client.abort_active_stream(request_id="abort-1") == "abort-1"
    with pytest.raises(JsonlSdkStreamCancelledError):
        tuple(stream)

    written_requests = [
        _payload_mapping(json.loads(line)) for line in output.getvalue().splitlines()
    ]
    assert written_requests == [
        {"method": "build_index_stream", "id": "index-1"},
        {"method": "abort", "id": "abort-1"},
    ]


def test_jsonl_sdk_client_drains_late_abort_response_after_stream_end() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {
                    "type": "stream_end",
                    "id": "index-1",
                    "ok": False,
                    "error": {
                        "code": SDK_JSONL_CANCELLED_ERROR_CODE,
                        "message": "SDK operation was cancelled.",
                        "unavailable_reason": None,
                    },
                },
                {
                    "type": "response",
                    "id": "abort-1",
                    "ok": True,
                    "result": {"aborted": True, "state": state},
                },
                {"type": "response", "id": "state-1", "ok": True, "result": state},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    assert client.abort_active_stream(request_id="abort-1") == "abort-1"
    with pytest.raises(JsonlSdkStreamCancelledError):
        tuple(stream)
    state = client.call("state", request_id="state-1")

    assert "service" in state


def test_jsonl_sdk_client_resolves_active_stream_state_call() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "response", "id": "state-1", "ok": True, "result": state},
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    state_results: list[dict[str, object]] = []
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            state_results.append(
                client.call_active_stream("state", request_id="state-1", timeout=2.0)
            )
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-active-state")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    assert list(stream) == []
    thread.join(timeout=2.0)

    assert not thread.is_alive()
    assert errors == []
    assert state_results == [state]


def test_jsonl_sdk_client_drains_late_active_stream_call_response_after_stream_end() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
                {"type": "response", "id": "state-1", "ok": True, "result": state},
                {"type": "response", "id": "state-2", "ok": True, "result": state},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    state_results: list[dict[str, object]] = []
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            state_results.append(
                client.call_active_stream("state", request_id="state-1", timeout=2.0)
            )
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-late-active-state")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    assert list(stream) == []
    thread.join(timeout=2.0)
    next_state = client.call("state", request_id="state-2")

    assert not thread.is_alive()
    assert errors == []
    assert state_results == [state]
    assert next_state == state


def test_jsonl_sdk_client_discards_timed_out_active_stream_call_response() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "response", "id": "state-1", "ok": True, "result": state},
                {"type": "stream_end", "id": "index-1", "ok": True},
                {"type": "response", "id": "state-2", "ok": True, "result": state},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            client.call_active_stream("state", request_id="state-1", timeout=0.01)
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-timeout-state")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    assert list(stream) == []
    next_state = client.call("state", request_id="state-2")

    assert len(errors) == 1
    assert isinstance(errors[0], JsonlSdkClientProtocolError)
    assert "Timed out waiting" in str(errors[0])
    assert next_state == state


def test_jsonl_sdk_client_discards_timed_out_active_stream_call_after_stream_end() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
                {"type": "response", "id": "state-1", "ok": True, "result": state},
                {"type": "response", "id": "state-2", "ok": True, "result": state},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            client.call_active_stream("state", request_id="state-1", timeout=0.01)
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-timeout-late-state")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    assert list(stream) == []
    next_state = client.call("state", request_id="state-2")

    assert len(errors) == 1
    assert isinstance(errors[0], JsonlSdkClientProtocolError)
    assert "Timed out waiting" in str(errors[0])
    assert next_state == state


def test_jsonl_sdk_client_discards_timed_out_active_stream_call_error() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {
                    "type": "error",
                    "id": "state-1",
                    "ok": False,
                    "error": {
                        "code": "unavailable",
                        "message": "No active SDK session.",
                        "unavailable_reason": "missing_session",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
                {"type": "response", "id": "state-2", "ok": True, "result": state},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            client.call_active_stream("state", request_id="state-1", timeout=0.01)
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-timeout-state-error")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    assert list(stream) == []
    next_state = client.call("state", request_id="state-2")

    assert len(errors) == 1
    assert isinstance(errors[0], JsonlSdkClientProtocolError)
    assert "Timed out waiting" in str(errors[0])
    assert next_state == state


def test_jsonl_sdk_client_routes_active_stream_call_errors_to_waiting_caller() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {
                    "type": "error",
                    "id": "state-1",
                    "ok": False,
                    "error": {
                        "code": "unavailable",
                        "message": "No active SDK session.",
                        "unavailable_reason": "missing_session",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            client.call_active_stream("state", request_id="state-1", timeout=2.0)
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-active-state-error")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')
    assert list(stream) == []
    thread.join(timeout=2.0)

    assert not thread.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], JsonlSdkServerError)
    assert errors[0].code == "unavailable"


def test_jsonl_sdk_client_rejects_unsafe_active_stream_call_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="not available during an active stream"):
        client.call_active_stream("ask", {"text": "hello"}, timeout=0.01)

    assert output.getvalue() == ""


def test_jsonl_sdk_client_rejects_active_stream_call_without_stream_reader_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="require an active stream reader"):
        client.call_active_stream("state", request_id="state-1", timeout=0.01)

    assert output.getvalue() == ""


def test_jsonl_sdk_client_rejects_active_stream_abort_without_stream_reader_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="require an active stream reader"):
        client.abort_active_stream(request_id="abort-1")

    assert output.getvalue() == ""


def test_jsonl_sdk_client_rejects_regular_call_while_stream_active_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    with pytest.raises(JsonlSdkClientProtocolError, match="call_active_stream"):
        client.call("state", request_id="state-1")

    assert list(stream) == []
    assert _written_requests(output) == [{"method": "build_index_stream", "id": "index-1"}]


def test_jsonl_sdk_client_rejects_second_stream_while_stream_active_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    with pytest.raises(JsonlSdkClientProtocolError, match="another stream"):
        tuple(client.stream("build_index_stream", request_id="index-2"))

    assert list(stream) == []
    assert _written_requests(output) == [{"method": "build_index_stream", "id": "index-1"}]


def test_jsonl_sdk_client_rejects_active_stream_call_id_collision_before_write() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    with pytest.raises(JsonlSdkClientProtocolError, match="already in use by an active stream"):
        client.call_active_stream("state", request_id="index-1", timeout=0.01)

    assert list(stream) == []
    assert _written_requests(output) == [{"method": "build_index_stream", "id": "index-1"}]


def test_jsonl_sdk_client_rejects_duplicate_active_stream_control_id_before_write() -> None:
    service = HephService.plain(config=_config())
    state = service.state()
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
                {
                    "type": "response",
                    "id": "abort-1",
                    "ok": True,
                    "result": {"aborted": True, "state": state},
                },
                {"type": "stream_end", "id": "index-1", "ok": True},
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")

    assert next(stream)["type"] == "index_progress"
    assert client.abort_active_stream(request_id="abort-1") == "abort-1"
    with pytest.raises(
        JsonlSdkClientProtocolError,
        match="already in use by an active stream control request",
    ):
        client.abort_active_stream(request_id="abort-1")

    assert list(stream) == []
    assert _written_requests(output) == [
        {"method": "build_index_stream", "id": "index-1"},
        {"method": "abort", "id": "abort-1"},
    ]


@pytest.mark.parametrize("timeout", [-0.01, float("nan"), float("inf")])
def test_jsonl_sdk_client_rejects_invalid_stream_control_timeout_before_write(
    timeout: float,
) -> None:
    output = io.StringIO()
    client = JsonlSdkClient(input_stream=io.StringIO(), output_stream=output)

    with pytest.raises(JsonlSdkClientProtocolError, match="stream control timeout"):
        client.call_active_stream("state", timeout=timeout)

    assert output.getvalue() == ""


def test_jsonl_codec_rejects_nonstandard_json_constants_on_encode() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        encode_jsonl_line({"type": "response", "result": {"latency": float("nan")}})


def test_jsonl_sdk_client_reports_malformed_server_message() -> None:
    with pytest.raises(
        JsonlSdkClientProtocolError,
        match=r"message 'response' field 'ok' must be a boolean",
    ):
        parse_jsonl_message(
            json.dumps({"type": "response", "id": "state-1", "ok": "yes", "result": {}})
        )


def test_jsonl_sdk_client_rejects_nonstandard_json_constants() -> None:
    with pytest.raises(JsonlSdkClientProtocolError, match="non-standard JSON constant: NaN"):
        parse_jsonl_message(
            '{"type":"response","id":"state-1","ok":true,"result":{"latency":NaN}}'
        )


def test_jsonl_sdk_client_wraps_stream_io_failures() -> None:
    closed_input = io.StringIO("")
    closed_input.close()
    reader = JsonlSdkClient(input_stream=closed_input, output_stream=io.StringIO())

    with pytest.raises(JsonlSdkClientProtocolError, match="Failed to read SDK JSONL message"):
        reader.read_message()

    closed_output = io.StringIO()
    closed_output.close()
    writer = JsonlSdkClient(input_stream=io.StringIO(""), output_stream=closed_output)

    with pytest.raises(
        JsonlSdkClientProtocolError,
        match="Failed to write SDK JSONL request 'state-1'",
    ):
        writer.write_request("state", request_id="state-1")


def test_jsonl_sdk_client_close_rejects_future_io_before_touching_streams() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl({"type": "response", "id": "state-1", "ok": True, "result": {}})
        ),
        output_stream=output,
    )

    assert not client.closed
    client.close()
    client.close()

    assert client.closed
    with pytest.raises(JsonlSdkClientProtocolError, match="client is closed"):
        client.read_message()
    with pytest.raises(JsonlSdkClientProtocolError, match="client is closed"):
        client.write_request("state", request_id="state-1")

    assert output.getvalue() == ""


def test_jsonl_sdk_client_close_wakes_active_stream_call_waiter() -> None:
    output = io.StringIO()
    client = JsonlSdkClient(
        input_stream=io.StringIO(
            _jsonl(
                {"type": "stream_start", "id": "index-1", "method": "build_index_stream"},
                {
                    "type": "stream_event",
                    "id": "index-1",
                    "event": {
                        "type": "index_progress",
                        "action": "reading",
                        "detail": "materials/notes.md",
                    },
                },
            )
        ),
        output_stream=output,
    )
    stream = client.stream("build_index_stream", request_id="index-1")
    errors: list[Exception] = []

    def call_state() -> None:
        try:
            client.call_active_stream("state", request_id="state-1", timeout=2.0)
        except Exception as exc:
            errors.append(exc)

    assert next(stream)["type"] == "index_progress"
    thread = threading.Thread(target=call_state, name="test-sdk-jsonl-close-state-waiter")
    thread.start()
    _wait_for_output(output, '"id": "state-1"')

    client.close()
    thread.join(timeout=2.0)

    assert not thread.is_alive()
    assert client.closed
    assert len(errors) == 1
    assert isinstance(errors[0], JsonlSdkClientProtocolError)
    assert "client is closed" in str(errors[0])
    assert _written_requests(output) == [
        {"method": "build_index_stream", "id": "index-1"},
        {"method": "state", "id": "state-1"},
    ]


def test_jsonl_sdk_client_rejects_incompatible_ready_payload() -> None:
    service = HephService.plain(config=_config())
    capabilities = dict(_payload_mapping(service.capabilities()["capabilities"]))
    compatibility = dict(_payload_mapping(capabilities["compatibility"]))
    compatibility["min_client_capabilities_version"] = SDK_CAPABILITIES_VERSION + 1
    compatibility["current_capabilities_version"] = SDK_CAPABILITIES_VERSION + 1
    capabilities["compatibility"] = compatibility
    ready_message = {
        "type": "ready",
        "protocol": SDK_JSONL_PROTOCOL,
        "version": SDK_JSONL_VERSION,
        "capabilities": capabilities,
        "state": service.state(),
    }
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
    )

    with pytest.raises(SdkClientCompatibilityError, match="older than minimum supported"):
        client.read_ready()


def test_jsonl_sdk_client_rejects_malformed_client_compatibility_versions() -> None:
    service = HephService.plain(config=_config())
    ready_message = _ready_message(service)
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
        client_capabilities_version=cast("int", True),
        jsonl_version=cast("int", True),
    )

    with pytest.raises(SdkClientCompatibilityError, match="capability version") as exc:
        client.read_ready()

    assert exc.value.issues == (
        "SDK client capability version must be an integer.",
        "SDK JSONL version must be an integer or None.",
    )


def test_jsonl_sdk_client_rejects_malformed_client_jsonl_version_before_compare() -> None:
    service = HephService.plain(config=_config())
    ready_message = _ready_message(service)
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
        jsonl_version=cast("int", "1"),
    )

    with pytest.raises(SdkClientCompatibilityError, match="JSONL version") as exc:
        client.read_ready()

    assert exc.value.issues == ("SDK JSONL version must be an integer or None.",)


def test_jsonl_sdk_client_requires_accepted_ready_stability() -> None:
    service = HephService.plain(config=_config())
    capabilities = dict(_payload_mapping(service.capabilities()["capabilities"]))
    compatibility = dict(_payload_mapping(capabilities["compatibility"]))
    compatibility["stability"] = SDK_STABILITY_PREVIEW
    capabilities["compatibility"] = compatibility
    ready_message = {
        "type": "ready",
        "protocol": SDK_JSONL_PROTOCOL,
        "version": SDK_JSONL_VERSION,
        "capabilities": capabilities,
        "state": service.state(),
    }
    default_client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
    )
    preview_client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
        accepted_stability_levels=(SDK_STABILITY_PUBLIC, SDK_STABILITY_PREVIEW),
    )

    with pytest.raises(SdkClientCompatibilityError, match="preview"):
        default_client.read_ready()

    assert preview_client.read_ready().capabilities["compatibility"] == compatibility


def test_jsonl_sdk_client_ignores_unknown_ready_capability_fields() -> None:
    service = HephService.plain(config=_config())
    capabilities = dict(_payload_mapping(service.capabilities()["capabilities"]))
    compatibility = dict(_payload_mapping(capabilities["compatibility"]))
    jsonl = dict(_payload_mapping(capabilities["jsonl"]))
    value_types = dict(_payload_mapping(capabilities["value_types"]))
    string_value_type = dict(_payload_mapping(value_types["string"]))
    compatibility["future_policy"] = "ignore me"
    jsonl["future_transport"] = {"name": "future"}
    string_value_type["future_value_type_field"] = True
    value_types["string"] = string_value_type
    capabilities["compatibility"] = compatibility
    capabilities["jsonl"] = jsonl
    capabilities["value_types"] = value_types
    capabilities["future_section"] = {"enabled": True}
    ready_message = {
        "type": "ready",
        "protocol": SDK_JSONL_PROTOCOL,
        "version": SDK_JSONL_VERSION,
        "capabilities": capabilities,
        "state": service.state(),
    }
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
    )

    ready = client.read_ready()

    assert ready.capabilities["future_section"] == {"enabled": True}
    assert _payload_mapping(ready.capabilities["compatibility"])["future_policy"] == "ignore me"
    assert _payload_mapping(ready.capabilities["jsonl"])["future_transport"] == {"name": "future"}


def test_jsonl_sdk_client_ignores_unknown_ready_state_fields() -> None:
    service = HephService.plain(config=_config())
    ready_message = _ready_message(service)
    state = dict(_payload_mapping(ready_message["state"]))
    service_state = dict(_payload_mapping(state["service"]))
    service_state["future_service_field"] = {"name": "future"}
    state["service"] = service_state
    state["future_state_section"] = {"enabled": True}
    ready_message["state"] = state
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
    )

    ready = client.read_ready()

    ready_state = _payload_mapping(ready.state)
    ready_service_state = _payload_mapping(ready_state["service"])
    assert ready_state["future_state_section"] == {"enabled": True}
    assert ready_service_state["future_service_field"] == {"name": "future"}


def test_jsonl_sdk_client_rejects_malformed_known_ready_state_fields() -> None:
    service = HephService.plain(config=_config())
    ready_message = _ready_message(service)
    state = dict(_payload_mapping(ready_message["state"]))
    service_state = dict(_payload_mapping(state["service"]))
    service_state["is_busy"] = "no"
    state["service"] = service_state
    ready_message["state"] = state
    client = JsonlSdkClient(
        input_stream=io.StringIO(json.dumps(ready_message) + "\n"),
        output_stream=io.StringIO(),
    )

    with pytest.raises(JsonlSdkClientProtocolError, match=r"is_busy.*boolean"):
        client.read_ready()


def test_jsonl_ready_and_error_payloads_export_snapshots() -> None:
    capabilities: dict[str, object] = {"version": SDK_CAPABILITIES_VERSION}
    state: dict[str, object] = {"service": {"is_busy": False}}
    ready = JsonlSdkReady(
        SDK_JSONL_PROTOCOL,
        SDK_JSONL_VERSION,
        capabilities,
        state,
    )
    capabilities["version"] = 0
    state["service"] = {"is_busy": True}

    ready_payload = ready.to_dict()

    assert ready_payload["capabilities"] == {"version": SDK_CAPABILITIES_VERSION}
    assert ready_payload["state"] == {"service": {"is_busy": False}}
    exported_capabilities = cast("dict[str, object]", ready_payload["capabilities"])
    exported_state = cast("dict[str, object]", ready_payload["state"])
    exported_capabilities["version"] = 0
    exported_state["service"] = {"is_busy": True}
    assert ready.to_dict()["capabilities"] == {"version": SDK_CAPABILITIES_VERSION}
    assert ready.to_dict()["state"] == {"service": {"is_busy": False}}

    error = JsonlSdkErrorPayload("unavailable", "No active SDK session.", "missing_session")

    assert error.to_dict() == {
        "code": "unavailable",
        "message": "No active SDK session.",
        "unavailable_reason": "missing_session",
    }


def test_jsonl_sdk_process_options_build_command() -> None:
    options = JsonlSdkProcessOptions(
        armory_path="notes",
        create_armory=True,
        session_id="session-1",
        base_url="https://example.test/v1",
        model="sdk-model",
        max_tokens=512,
        rag_context_budget=4096,
        reasoning_level="medium",
        thinking_visibility="all",
        temperature=0.5,
    )

    assert options.command() == (
        "heph",
        "sdk",
        "serve",
        "--armory",
        "notes",
        "--create-armory",
        "--session-id",
        "session-1",
        "--base-url",
        "https://example.test/v1",
        "--model",
        "sdk-model",
        "--max-tokens",
        "512",
        "--rag-context-budget",
        "4096",
        "--reasoning-level",
        "medium",
        "--thinking-visibility",
        "all",
        "--temperature",
        "0.5",
    )


def test_jsonl_sdk_process_options_expand_user_armory_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    options = JsonlSdkProcessOptions(armory_path="~/notes")

    assert options.command()[3:5] == ("--armory", str(home / "notes"))


def test_jsonl_sdk_process_options_cover_spawnable_sdk_options() -> None:
    sdk_option_fields = {field.name for field in fields(HephSdkOptions)}
    process_option_fields = {field.name for field in fields(JsonlSdkProcessOptions)}

    assert sdk_option_fields - process_option_fields == {"config", "feature_flags"}


def test_jsonl_sdk_process_options_reject_invalid_session_combination() -> None:
    options = JsonlSdkProcessOptions(session_id="session-1", start_session=False)

    with pytest.raises(JsonlSdkProcessError, match="--session-id cannot be used"):
        options.command()


@pytest.mark.parametrize(
    "options",
    [
        JsonlSdkProcessOptions(executable=""),
        JsonlSdkProcessOptions(executable=" "),
        JsonlSdkProcessOptions(executable=cast("str", None)),
        JsonlSdkProcessOptions(executable="heph\0"),
    ],
)
def test_jsonl_sdk_process_options_reject_invalid_executable(
    options: JsonlSdkProcessOptions,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match="executable"):
        options.command()


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (JsonlSdkProcessOptions(armory_path=""), "armory_path"),
        (JsonlSdkProcessOptions(armory_path=" "), "armory_path"),
        (JsonlSdkProcessOptions(armory_path="notes\0"), "armory_path"),
        (JsonlSdkProcessOptions(armory_path=cast("Path", 7)), "armory_path"),
    ],
)
def test_jsonl_sdk_process_options_reject_invalid_armory_path(
    options: JsonlSdkProcessOptions,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        options.command()


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (JsonlSdkProcessOptions(session_id=""), "session_id"),
        (JsonlSdkProcessOptions(session_id="session\0"), "session_id"),
        (JsonlSdkProcessOptions(base_url=" "), "base_url"),
        (JsonlSdkProcessOptions(model=""), "model"),
        (JsonlSdkProcessOptions(reasoning_level=" "), "reasoning_level"),
        (JsonlSdkProcessOptions(thinking_visibility=""), "thinking_visibility"),
    ],
)
def test_jsonl_sdk_process_options_reject_empty_string_options(
    options: JsonlSdkProcessOptions,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        options.command()


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (JsonlSdkProcessOptions(reasoning_level="turbo"), "reasoning_level"),
        (JsonlSdkProcessOptions(thinking_visibility="verbose"), "thinking_visibility"),
    ],
)
def test_jsonl_sdk_process_options_reject_unknown_choice_options(
    options: JsonlSdkProcessOptions,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        options.command()


def test_jsonl_sdk_process_options_reject_create_armory_without_path() -> None:
    options = JsonlSdkProcessOptions(create_armory=True)

    with pytest.raises(JsonlSdkProcessError, match="requires an armory_path"):
        options.command()


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (JsonlSdkProcessOptions(max_tokens=cast("int", True)), "max_tokens"),
        (JsonlSdkProcessOptions(max_tokens=cast("int", 1.5)), "max_tokens"),
        (JsonlSdkProcessOptions(max_tokens=-1), "max_tokens"),
        (
            JsonlSdkProcessOptions(rag_context_budget=cast("int", True)),
            "rag_context_budget",
        ),
        (
            JsonlSdkProcessOptions(rag_context_budget=cast("int", 1.5)),
            "rag_context_budget",
        ),
        (JsonlSdkProcessOptions(rag_context_budget=-1), "rag_context_budget"),
        (JsonlSdkProcessOptions(temperature=cast("float", True)), "temperature"),
        (JsonlSdkProcessOptions(temperature=float("nan")), "temperature"),
        (JsonlSdkProcessOptions(temperature=float("inf")), "temperature"),
    ],
)
def test_jsonl_sdk_process_options_reject_invalid_numeric_options(
    options: JsonlSdkProcessOptions,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        options.command()


def test_jsonl_sdk_process_reads_ready_and_closes(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())
    server_script = tmp_path / "fake_sdk_server.py"
    ready_line = json.dumps(_ready_message(service)) + "\n"
    server_script.write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "import sys",
                f"sys.stdout.write({ready_line!r})",
                "sys.stdout.flush()",
                "for _line in sys.stdin:",
                "    pass",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    transport = JsonlSdkProcess(command=(sys.executable, str(server_script)))

    with transport as running:
        ready = running.ready
        process = running.process
        client = running.client

        assert ready.protocol == SDK_JSONL_PROTOCOL
        assert ready.version == SDK_JSONL_VERSION
        assert ready.capabilities["version"] == SDK_CAPABILITIES_VERSION
        assert client is running.client
        assert process.poll() is None
        assert running.returncode is None

    assert process.poll() == 0
    assert transport.returncode == 0
    assert client.closed
    with pytest.raises(JsonlSdkProcessError, match="not running"):
        _ = transport.process
    with pytest.raises(JsonlSdkClientProtocolError, match="client is closed"):
        client.call("state", request_id="state-after-close")


def test_jsonl_sdk_process_passes_accepted_ready_stability(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())
    ready_payload = _ready_message(service)
    capabilities = dict(_payload_mapping(ready_payload["capabilities"]))
    compatibility = dict(_payload_mapping(capabilities["compatibility"]))
    compatibility["stability"] = SDK_STABILITY_PREVIEW
    capabilities["compatibility"] = compatibility
    ready_payload["capabilities"] = capabilities
    ready_line = json.dumps(ready_payload) + "\n"
    server_script = tmp_path / "fake_preview_sdk_server.py"
    server_script.write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "import sys",
                f"sys.stdout.write({ready_line!r})",
                "sys.stdout.flush()",
                "for _line in sys.stdin:",
                "    pass",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    transport = JsonlSdkProcess(
        command=(sys.executable, str(server_script)),
        accepted_stability_levels=(SDK_STABILITY_PUBLIC, SDK_STABILITY_PREVIEW),
    )

    with transport as running:
        assert running.ready.capabilities["compatibility"] == compatibility

    assert transport.returncode == 0


def test_jsonl_sdk_process_ignores_pipe_close_errors() -> None:
    class BrokenCloseStream(io.StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.raise_on_close = True

        def close(self) -> None:
            if self.raise_on_close:
                self.raise_on_close = False
                raise BrokenPipeError("pipe already closed")
            super().close()

    stream = BrokenCloseStream()

    JsonlSdkProcess._close_process_stream(stream)
    stream.close()


def test_jsonl_sdk_process_close_wraps_kill_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = subprocess.Popen(
        (sys.executable, "-c", "import time; time.sleep(10)"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    transport = JsonlSdkProcess(shutdown_timeout=0.01)
    client = JsonlSdkClient(input_stream=process.stdout, output_stream=process.stdin)
    transport._process = process
    transport._client = client
    real_wait = process.wait
    wait_calls = 0

    def fake_wait(timeout: float | None = None) -> int:
        nonlocal wait_calls
        wait_calls += 1
        raise subprocess.TimeoutExpired(process.args, timeout if timeout is not None else 0.0)

    monkeypatch.setattr(process, "wait", fake_wait)
    try:
        with pytest.raises(JsonlSdkProcessError, match="did not exit after kill") as exc:
            transport.close()

        assert "shutdown timeout" in str(exc.value)
        assert wait_calls == 2
        assert client.closed
        with pytest.raises(JsonlSdkProcessError, match="not running"):
            _ = transport.process
    finally:
        monkeypatch.setattr(process, "wait", real_wait)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2.0)


def test_jsonl_sdk_process_runs_real_sdk_serve_cli(tmp_path: Path) -> None:
    command = (
        sys.executable,
        "-c",
        "from heph.cli.main import build_parser, run_argv; "
        "run_argv(build_parser(), ['sdk', 'serve', '--no-session'])",
    )
    transport = JsonlSdkProcess(
        command=command,
        cwd=_repo_root(),
        env=_real_sdk_serve_environment(tmp_path),
    )

    with transport as running:
        ready = running.ready
        state = running.client.call("state", request_id="state-1")
        capabilities = running.client.call("capabilities", request_id="caps-1")

        state_service = _payload_mapping(state["service"])
        capability_payload = _payload_mapping(capabilities["capabilities"])

        assert ready.protocol == SDK_JSONL_PROTOCOL
        assert ready.version == SDK_JSONL_VERSION
        assert ready.capabilities["version"] == SDK_CAPABILITIES_VERSION
        assert state_service["available_stream_methods"] == []
        assert capability_payload["version"] == SDK_CAPABILITIES_VERSION

        with pytest.raises(
            JsonlSdkServerError, match="SDK JSONL server returned unavailable"
        ) as exc:
            running.client.call("ask", {"text": "hello"}, request_id="ask-1")

        assert exc.value.code == "unavailable"
        assert exc.value.unavailable_reason == "missing_session"


def test_jsonl_sdk_process_times_out_waiting_for_ready() -> None:
    transport = JsonlSdkProcess(
        command=(sys.executable, "-c", "import time; time.sleep(10)"),
        startup_timeout=0.01,
        shutdown_timeout=0.1,
    )

    with pytest.raises(JsonlSdkProcessError, match="did not send ready"):
        transport.start()

    assert transport.returncode is not None
    with pytest.raises(JsonlSdkProcessError, match="not running"):
        _ = transport.process


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                client_capabilities_version=cast("int", True),
            ),
            "capability version",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                jsonl_version=cast("int", "1"),
            ),
            "JSONL version",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                accepted_stability_levels=(),
            ),
            "must not be empty",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                accepted_stability_levels=("beta",),
            ),
            "unknown values",
        ),
    ],
)
def test_jsonl_sdk_process_rejects_invalid_client_options_before_spawn(
    transport: JsonlSdkProcess,
    message: str,
) -> None:
    with pytest.raises(SdkClientCompatibilityError, match=message):
        transport.start()

    assert transport.returncode is None


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                capture_stderr=cast("bool", "yes"),
            ),
            "capture_stderr",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                stderr_tail_limit=cast("int", True),
            ),
            "stderr_tail_limit",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                stderr_tail_limit=cast("int", None),
            ),
            "stderr_tail_limit",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                stderr_tail_limit=-1,
            ),
            "stderr_tail_limit",
        ),
    ],
)
def test_jsonl_sdk_process_rejects_invalid_diagnostic_options_before_spawn(
    transport: JsonlSdkProcess,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        transport.start()

    assert transport.returncode is None


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (
            JsonlSdkProcess(command=cast("tuple[str, ...]", ())),
            "must not be empty",
        ),
        (
            JsonlSdkProcess(command=cast("tuple[str, ...]", "")),
            "sequence of strings",
        ),
        (
            JsonlSdkProcess(command=("",)),
            "executable",
        ),
        (
            JsonlSdkProcess(command=("heph\0",)),
            "executable",
        ),
        (
            JsonlSdkProcess(command=(sys.executable, cast("str", 7))),
            "arguments must be strings",
        ),
        (
            JsonlSdkProcess(command=(sys.executable, "bad\0")),
            "arguments",
        ),
    ],
)
def test_jsonl_sdk_process_rejects_invalid_command_before_spawn(
    transport: JsonlSdkProcess,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        transport.start()

    assert transport.returncode is None


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                cwd="",
            ),
            "cwd",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                cwd="bad\0",
            ),
            "cwd",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                cwd=cast("str | Path | None", 7),
            ),
            "cwd",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env=cast("Mapping[str, str]", "PATH=/tmp"),
            ),
            "env",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env={"": "value"},
            ),
            "env keys",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env={"BAD=KEY": "value"},
            ),
            "env keys",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env={"BAD\0KEY": "value"},
            ),
            "env keys",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env={"PATH": cast("str", 7)},
            ),
            "env values",
        ),
        (
            JsonlSdkProcess(
                command=(sys.executable, "-c", "raise SystemExit(3)"),
                env={"PATH": "bad\0"},
            ),
            "env values",
        ),
    ],
)
def test_jsonl_sdk_process_rejects_invalid_launch_environment_before_spawn(
    transport: JsonlSdkProcess,
    message: str,
) -> None:
    with pytest.raises(JsonlSdkProcessError, match=message):
        transport.start()

    assert transport.returncode is None


@pytest.mark.parametrize("timeout", [-0.01, float("nan"), float("inf")])
def test_jsonl_sdk_process_rejects_invalid_timeouts_before_spawn(timeout: float) -> None:
    startup_transport = JsonlSdkProcess(
        command=(sys.executable, "-c", "raise SystemExit(3)"),
        startup_timeout=timeout,
    )
    shutdown_transport = JsonlSdkProcess(
        command=(sys.executable, "-c", "raise SystemExit(3)"),
        shutdown_timeout=timeout,
    )

    with pytest.raises(JsonlSdkProcessError, match="startup_timeout"):
        startup_transport.start()
    with pytest.raises(JsonlSdkProcessError, match="shutdown_timeout"):
        shutdown_transport.start()

    assert startup_transport.returncode is None
    assert shutdown_transport.returncode is None


@pytest.mark.parametrize("timeout", [-0.01, float("nan"), float("inf")])
def test_jsonl_sdk_process_rejects_invalid_close_timeout(
    tmp_path: Path,
    timeout: float,
) -> None:
    service = HephService.plain(config=_config())
    server_script = tmp_path / "fake_sdk_server.py"
    ready_line = json.dumps(_ready_message(service)) + "\n"
    server_script.write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "import sys",
                f"sys.stdout.write({ready_line!r})",
                "sys.stdout.flush()",
                "for _line in sys.stdin:",
                "    pass",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    transport = JsonlSdkProcess(command=(sys.executable, str(server_script)))
    transport.start()
    try:
        with pytest.raises(JsonlSdkProcessError, match="close timeout"):
            transport.close(timeout=timeout)
    finally:
        transport.close(timeout=1.0)


def test_jsonl_sdk_process_reports_startup_stderr() -> None:
    transport = JsonlSdkProcess(
        command=(
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('sdk startup failed\\n'); sys.stderr.flush()",
        ),
        startup_timeout=5.0,
        shutdown_timeout=1.0,
    )

    with pytest.raises(JsonlSdkProcessError, match="sdk startup failed") as exc:
        transport.start()

    assert "stream ended before a message" in str(exc.value)
    assert transport.stderr_tail == "sdk startup failed\n"
    assert transport.returncode == 0
