from __future__ import annotations

import io
import json
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from heph.cli.main import build_parser, run_argv
from heph.sdk import (
    SDK_JSONL_PROTOCOL,
    HephSdkOptions,
    HephService,
    JsonlSdkServer,
)
from heph.sdk import runtime as sdk_runtime
from heph.sdk import stdio as sdk_stdio
from hephaion.chat.events import AssistantDeltaEvent, TurnCompleteEvent, TurnEvent
from hephaion.chat.session import ChatSession


class _FakeIndex:
    documents = ("doc-1",)
    chunk_count = 7


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
                {"id": "new-while-busy", "method": "new_session"},
                {"id": "abort-1", "method": "abort"},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    abort_response = next(payload for payload in payloads if payload.get("id") == "abort-1")
    busy_response = next(payload for payload in payloads if payload.get("id") == "new-while-busy")
    stream_events = [payload for payload in payloads if payload["type"] == "stream_event"]
    complete_event = _payload_mapping(stream_events[-1]["event"])

    assert busy_response["type"] == "error"
    assert _payload_mapping(busy_response["error"])["code"] == "busy"
    assert _payload_mapping(abort_response["result"])["aborted"] is True
    assert complete_event["finish_reason"] == "abort"
    assert payloads[-1] == {"type": "stream_end", "id": "turn-1", "ok": True}


def test_jsonl_sdk_server_maps_service_busy_errors_to_busy_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    service.new_session()
    started = threading.Event()
    release = threading.Event()
    prompt_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        _ = abort
        assert prompt == "external prompt"
        started.set()
        yield AssistantDeltaEvent("first")
        assert release.wait(timeout=2.0)
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def collect_prompt() -> None:
        try:
            list(service.prompt("external prompt"))
        except Exception as exc:
            prompt_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_prompt, name="test-sdk-stdio-busy")
    thread.start()
    assert started.wait(timeout=2.0)

    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )
    server.handle_request({"id": "new-while-service-busy", "method": "new_session"})

    release.set()
    thread.join(timeout=2.0)
    payloads = _payloads(output.getvalue())
    error = _payload_mapping(payloads[0]["error"])

    assert payloads[0]["type"] == "error"
    assert payloads[0]["id"] == "new-while-service-busy"
    assert error["code"] == "busy"
    assert prompt_errors == []
    assert not thread.is_alive()


def test_jsonl_abort_does_not_cancel_unowned_direct_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    service.new_session()
    started = threading.Event()
    release = threading.Event()
    direct_abort_seen = threading.Event()
    prompt_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        assert prompt == "direct prompt"
        assert abort is not None
        started.set()
        yield AssistantDeltaEvent("direct")
        assert release.wait(timeout=2.0)
        if abort.is_set():
            direct_abort_seen.set()
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def collect_prompt() -> None:
        try:
            list(service.prompt("direct prompt"))
        except Exception as exc:
            prompt_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_prompt, name="test-sdk-stdio-direct-prompt")
    thread.start()
    assert started.wait(timeout=2.0)

    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )
    active_prompt = sdk_stdio.ActivePrompt(
        request_id="jsonl-pending",
        abort=threading.Event(),
    )
    server._active_prompt = active_prompt

    server.handle_request({"id": "abort-jsonl", "method": "abort"})
    release.set()
    thread.join(timeout=2.0)
    payloads = _payloads(output.getvalue())

    assert active_prompt.abort.is_set()
    assert _payload_mapping(payloads[0]["result"])["aborted"] is True
    assert not direct_abort_seen.is_set()
    assert prompt_errors == []
    assert not thread.is_alive()


def test_jsonl_abort_without_owned_stream_is_noop_for_direct_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    service.new_session()
    started = threading.Event()
    release = threading.Event()
    direct_abort_seen = threading.Event()
    prompt_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        assert prompt == "direct prompt"
        assert abort is not None
        started.set()
        yield AssistantDeltaEvent("direct")
        assert release.wait(timeout=2.0)
        if abort.is_set():
            direct_abort_seen.set()
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def collect_prompt() -> None:
        try:
            list(service.prompt("direct prompt"))
        except Exception as exc:
            prompt_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_prompt, name="test-sdk-stdio-unowned-abort")
    thread.start()
    assert started.wait(timeout=2.0)

    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )
    server.handle_request({"id": "abort-jsonl", "method": "abort"})

    release.set()
    thread.join(timeout=2.0)
    payloads = _payloads(output.getvalue())
    result = _payload_mapping(payloads[0]["result"])

    assert result["aborted"] is False
    assert _payload_mapping(result["state"])["service"] == {
        "prompt_active": True,
        "active_operation": None,
    }
    assert not direct_abort_seen.is_set()
    assert prompt_errors == []
    assert not thread.is_alive()


def test_jsonl_sdk_server_handles_source_scope_toggle(tmp_path: Path) -> None:
    armory_path = tmp_path / ".armories" / "jsonl-scope"
    service = HephService.create_armory(armory_path, config=_config())
    materials_path = armory_path / "materials" / "notes.md"
    materials_path.write_text("# Notes\n\nTransport source.\n", encoding="utf-8")
    service.new_session()
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {
                    "id": "disable-notes",
                    "method": "set_source_enabled",
                    "params": {"source": "materials/notes.md", "enabled": False},
                },
                {"id": "state-after-toggle", "method": "state"},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    toggle_response = next(payload for payload in payloads if payload.get("id") == "disable-notes")
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-toggle"
    )
    toggle_result = _payload_mapping(toggle_response["result"])
    toggle_session = _payload_mapping(toggle_result["session"])
    state_session = _payload_mapping(_payload_mapping(state_response["result"])["session"])

    assert toggle_result["changed"] is True
    assert toggle_session["disabled_source_files"] == ["materials/notes.md"]
    assert toggle_session["enabled_source_files"] == []
    assert state_session["disabled_source_files"] == ["materials/notes.md"]


def test_jsonl_sdk_server_streams_build_index_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_path = tmp_path / ".armories" / "jsonl-index"
    service = HephService.create_armory(armory_path, config=_config())
    release = threading.Event()

    def fake_build_index(
        armory_path: Path,
        *,
        strategy: object | None = None,
        progress: Callable[[str, str], None] | None = None,
        previous: object | None = None,
    ) -> _FakeIndex:
        _ = armory_path, strategy, previous
        assert progress is not None
        progress("reading", "materials/notes.md")
        assert release.wait(timeout=2.0)
        progress("writing", ".hephaion/rag_index.json")
        return _FakeIndex()

    monkeypatch.setattr(sdk_runtime, "build_rag_index", fake_build_index)
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )

    server.handle_request({"id": "index-1", "method": "build_index_stream"})
    server.handle_request({"id": "state-immediate-index", "method": "state"})
    deadline = time.monotonic() + 2.0
    while "index_progress" not in output.getvalue() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert "index_progress" in output.getvalue()

    server.handle_request({"id": "state-during-index", "method": "state"})
    server.handle_request({"id": "abort-during-index", "method": "abort"})
    server.handle_request(
        {
            "id": "prompt-during-index",
            "method": "prompt",
            "params": {"text": "Prompt during index."},
        }
    )

    release.set()
    server._wait_for_streams()

    payloads = _payloads(output.getvalue())
    assert payloads[0] == {
        "type": "stream_start",
        "id": "index-1",
        "method": "build_index_stream",
    }
    immediate_state_response = next(
        payload for payload in payloads if payload.get("id") == "state-immediate-index"
    )
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-during-index"
    )
    abort_response = next(
        payload for payload in payloads if payload.get("id") == "abort-during-index"
    )
    prompt_error = next(
        payload for payload in payloads if payload.get("id") == "prompt-during-index"
    )
    immediate_service = _payload_mapping(
        _payload_mapping(immediate_state_response["result"])["service"]
    )
    state_service = _payload_mapping(_payload_mapping(state_response["result"])["service"])
    abort_result = _payload_mapping(abort_response["result"])
    abort_state_service = _payload_mapping(_payload_mapping(abort_result["state"])["service"])
    prompt_error_payload = _payload_mapping(prompt_error["error"])
    events = [
        _payload_mapping(payload["event"])
        for payload in payloads
        if payload["type"] == "stream_event"
    ]
    assert immediate_service == {"prompt_active": False, "active_operation": "build_index"}
    assert state_service == {"prompt_active": False, "active_operation": "build_index"}
    assert abort_result["aborted"] is False
    assert abort_state_service == {"prompt_active": False, "active_operation": "build_index"}
    assert prompt_error_payload["code"] == "busy"
    assert events == [
        {
            "type": "index_progress",
            "action": "reading",
            "detail": "materials/notes.md",
        },
        {
            "type": "index_progress",
            "action": "writing",
            "detail": ".hephaion/rag_index.json",
        },
        {
            "type": "index_complete",
            "index": {
                "documents": 1,
                "chunks": 7,
                "progress": [
                    {"action": "reading", "detail": "materials/notes.md"},
                    {"action": "writing", "detail": ".hephaion/rag_index.json"},
                ],
            },
        },
    ]
    assert payloads[-1] == {"type": "stream_end", "id": "index-1", "ok": True}


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
