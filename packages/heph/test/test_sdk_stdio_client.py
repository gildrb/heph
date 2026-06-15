from __future__ import annotations

import io
import json
import os
import sys
import threading
from collections.abc import Iterator, Mapping
from dataclasses import fields
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from heph.sdk import (
    SDK_CAPABILITIES_VERSION,
    SDK_JSONL_CANCELLED_ERROR_CODE,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    HephSdkOptions,
    HephService,
    JsonlSdkClient,
    JsonlSdkClientProtocolError,
    JsonlSdkProcess,
    JsonlSdkProcessError,
    JsonlSdkProcessOptions,
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
from hephaion.chat.events import AssistantDeltaEvent, TurnCompleteEvent, TurnEvent
from hephaion.chat.session import ChatSession


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
        repo_root / "packages" / "hephaion" / "src",
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
    environment["HEPHAION_DISABLE_LIVE_MODELS"] = "1"
    environment["HEPHAION_NO_VENV_REEXEC"] = "1"
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


def test_jsonl_sdk_client_reports_malformed_server_message() -> None:
    with pytest.raises(
        JsonlSdkClientProtocolError,
        match=r"message 'response' field 'ok' must be a boolean",
    ):
        parse_jsonl_message(
            json.dumps({"type": "response", "id": "state-1", "ok": "yes", "result": {}})
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


def test_jsonl_sdk_process_options_cover_spawnable_sdk_options() -> None:
    sdk_option_fields = {field.name for field in fields(HephSdkOptions)}
    process_option_fields = {field.name for field in fields(JsonlSdkProcessOptions)}

    assert sdk_option_fields - process_option_fields == {"config", "feature_flags"}


def test_jsonl_sdk_process_options_reject_invalid_session_combination() -> None:
    options = JsonlSdkProcessOptions(session_id="session-1", start_session=False)

    with pytest.raises(JsonlSdkProcessError, match="--session-id cannot be used"):
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
    with pytest.raises(JsonlSdkProcessError, match="not running"):
        _ = transport.process


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
        shutdown_timeout=0.01,
    )

    with pytest.raises(JsonlSdkProcessError, match="did not send ready"):
        transport.start()

    assert transport.returncode is not None
    with pytest.raises(JsonlSdkProcessError, match="not running"):
        _ = transport.process


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
