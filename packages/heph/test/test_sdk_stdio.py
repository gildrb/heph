from __future__ import annotations

import io
import json
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from heph.cli.main import build_parser, run_argv
from heph.sdk import SDK_JSONL_PROTOCOL, HephSdkOptions, HephService, JsonlSdkServer
from heph.sdk import runtime as sdk_runtime
from hephaion.chat.events import AssistantDeltaEvent, TurnCompleteEvent, TurnEvent
from hephaion.chat.session import ChatSession


def _config() -> ChatConfig:
    return ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini")


def _jsonl(*requests: dict[str, object]) -> str:
    return "\n".join(json.dumps(request) for request in requests) + "\n"


def _payloads(output: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for line in output.splitlines():
        parsed: object = json.loads(line)
        assert isinstance(parsed, dict)
        payloads.append({str(key): value for key, value in parsed.items()})
    return payloads


def _payload_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return {str(key): item for key, item in value.items()}


def test_jsonl_sdk_server_handles_state_and_prompt(
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

    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {"id": "state-1", "method": "state"},
                {"id": "turn-1", "method": "prompt", "params": {"text": "hello sdk"}},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    assert payloads[0]["type"] == "ready"
    assert payloads[0]["protocol"] == SDK_JSONL_PROTOCOL
    assert payloads[1]["type"] == "response"
    assert payloads[1]["id"] == "state-1"
    assert payloads[2] == {"type": "stream_start", "id": "turn-1", "method": "prompt"}
    assert payloads[3] == {
        "type": "stream_event",
        "id": "turn-1",
        "event": {"type": "assistant_delta", "delta": "hello native app"},
    }
    assert payloads[-1] == {"type": "stream_end", "id": "turn-1", "ok": True}


def test_jsonl_sdk_server_abort_reaches_active_prompt(
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
        _ = raw_session
        assert prompt == "cancel this"
        assert abort is not None
        yield AssistantDeltaEvent("first")
        deadline = time.monotonic() + 1.0
        while not abort.is_set() and time.monotonic() < deadline:
            time.sleep(0.01)
        yield TurnCompleteEvent("stopped", 0, 1.0, "abort" if abort.is_set() else "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {"id": "turn-1", "method": "prompt", "params": {"text": "cancel this"}},
                {"id": "abort-1", "method": "abort"},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    abort_response = next(payload for payload in payloads if payload.get("id") == "abort-1")
    stream_events = [payload for payload in payloads if payload["type"] == "stream_event"]
    complete_event = _payload_mapping(stream_events[-1]["event"])

    assert _payload_mapping(abort_response["result"])["aborted"] is True
    assert complete_event["finish_reason"] == "abort"
    assert payloads[-1] == {"type": "stream_end", "id": "turn-1", "ok": True}


def test_jsonl_sdk_server_reports_protocol_errors() -> None:
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO("{broken\n[]\n"),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    errors = [payload for payload in payloads if payload["type"] == "error"]
    assert [_payload_mapping(error["error"])["code"] for error in errors] == [
        "invalid_json",
        "invalid_request",
    ]


def test_jsonl_sdk_server_reports_service_errors_and_continues(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {
                    "id": "bad-armory",
                    "method": "open_armory",
                    "params": {"path": str(tmp_path / "missing")},
                },
                {"id": "state-after-error", "method": "state"},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    service_error = next(payload for payload in payloads if payload.get("id") == "bad-armory")
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-error"
    )

    assert service_error["type"] == "error"
    assert _payload_mapping(service_error["error"])["code"] == "sdk_error"
    assert state_response["type"] == "response"
    assert state_response["ok"] is True


def test_sdk_serve_cli_dispatches_options(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: HephSdkOptions | None = None

    def fake_serve_stdio(options: HephSdkOptions | None = None) -> None:
        nonlocal captured
        captured = options

    monkeypatch.setattr("heph.sdk.stdio.serve_stdio", fake_serve_stdio)

    run_argv(
        build_parser(),
        [
            "sdk",
            "serve",
            "--armory",
            "notes",
            "--create-armory",
            "--session-id",
            "session-1",
            "--model",
            "sdk-model",
            "--temperature",
            "0.5",
            "--max-tokens",
            "512",
        ],
    )

    assert captured is not None
    assert captured.armory_path == "notes"
    assert captured.create_armory
    assert captured.session_id == "session-1"
    assert captured.start_session
    assert captured.model == "sdk-model"
    assert captured.temperature == 0.5
    assert captured.max_tokens == 512


def test_sdk_serve_cli_starts_session_for_created_armory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: HephSdkOptions | None = None

    def fake_serve_stdio(options: HephSdkOptions | None = None) -> None:
        nonlocal captured
        captured = options

    monkeypatch.setattr("heph.sdk.stdio.serve_stdio", fake_serve_stdio)

    run_argv(
        build_parser(),
        [
            "sdk",
            "serve",
            "--armory",
            "new-notes",
            "--create-armory",
        ],
    )

    assert captured is not None
    assert captured.armory_path == "new-notes"
    assert captured.create_armory
    assert captured.session_id is None
    assert captured.start_session
