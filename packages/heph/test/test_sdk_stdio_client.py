from __future__ import annotations

import io
import json
import threading
from collections.abc import Iterator

import pytest
from ai.runtime import ChatConfig
from heph.sdk import (
    SDK_CAPABILITIES_VERSION,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    HephService,
    JsonlSdkClient,
    JsonlSdkClientProtocolError,
    JsonlSdkServer,
    JsonlSdkServerError,
    SdkClientCompatibilityError,
    parse_jsonl_message,
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


def test_jsonl_sdk_client_reports_malformed_server_message() -> None:
    with pytest.raises(
        JsonlSdkClientProtocolError,
        match=r"message 'response' field 'ok' must be a boolean",
    ):
        parse_jsonl_message(
            json.dumps({"type": "response", "id": "state-1", "ok": "yes", "result": {}})
        )


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
