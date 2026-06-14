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
    JSONL_ERROR_CODES,
    JSONL_MESSAGE_TYPES,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    HephRuntime,
    HephSdkOptions,
    HephService,
    JsonlSdkServer,
)
from heph.sdk import methods as sdk_methods
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


def _payload_list(value: object) -> list[object]:
    assert isinstance(value, list)
    result: list[object] = list(value)
    return result


def _service_call_methods(*methods: str) -> tuple[str, ...]:
    available = set(methods)
    return tuple(method for method in sdk_methods.SERVICE_CALL_METHODS if method in available)


def _jsonl_stream_methods(*methods: str) -> tuple[str, ...]:
    available = set(methods)
    return tuple(method for method in sdk_methods.JSONL_STREAM_METHODS if method in available)


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
                {"id": "caps-1", "method": "capabilities"},
                {"id": "turn-1", "method": "prompt", "params": {"text": "hello sdk"}},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    ready_capabilities = _payload_mapping(payloads[0]["capabilities"])
    ready_state = _payload_mapping(payloads[0]["state"])
    ready_service = _payload_mapping(ready_state["service"])
    ready_jsonl = _payload_mapping(ready_capabilities["jsonl"])
    ready_call_methods = _payload_list(ready_jsonl["call_methods"])
    ready_stream_methods = _payload_list(ready_jsonl["stream_methods"])
    ready_message_types = _payload_list(ready_jsonl["message_types"])
    ready_error_codes = _payload_list(ready_jsonl["error_codes"])
    capabilities_response = _payload_mapping(payloads[2]["result"])
    capabilities = _payload_mapping(capabilities_response["capabilities"])
    capabilities_jsonl = _payload_mapping(capabilities["jsonl"])
    capability_message_types = _payload_list(capabilities_jsonl["message_types"])
    capability_error_codes = _payload_list(capabilities_jsonl["error_codes"])
    assert payloads[0]["type"] == "ready"
    assert payloads[0]["protocol"] == SDK_JSONL_PROTOCOL
    assert payloads[0]["version"] == SDK_JSONL_VERSION
    assert ready_jsonl["protocol"] == SDK_JSONL_PROTOCOL
    assert "validate_armory" in ready_call_methods
    assert "list_providers" in ready_call_methods
    assert "list_model_choices" in ready_call_methods
    assert "switch_model" in ready_call_methods
    assert "settings" in ready_call_methods
    assert "update_settings" in ready_call_methods
    assert "build_index_stream" in ready_stream_methods
    assert ready_service["available_stream_methods"] == ["prompt"]
    assert ready_message_types == list(JSONL_MESSAGE_TYPES)
    assert ready_error_codes == list(JSONL_ERROR_CODES)
    assert payloads[1]["type"] == "response"
    assert payloads[1]["id"] == "state-1"
    assert payloads[2]["type"] == "response"
    assert payloads[2]["id"] == "caps-1"
    assert capabilities_jsonl["protocol"] == SDK_JSONL_PROTOCOL
    assert capability_message_types == list(JSONL_MESSAGE_TYPES)
    assert capability_error_codes == list(JSONL_ERROR_CODES)
    assert payloads[3] == {"type": "stream_start", "id": "turn-1", "method": "prompt"}
    assert payloads[4] == {
        "type": "stream_event",
        "id": "turn-1",
        "event": {"type": "assistant_delta", "delta": "hello native app"},
    }
    assert payloads[-1] == {"type": "stream_end", "id": "turn-1", "ok": True}


def test_jsonl_sdk_server_translates_stateful_call_results(tmp_path: Path) -> None:
    armory_path = tmp_path / "armory"
    service = HephService.create_armory(armory_path, config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {"id": "plain-1", "method": "use_plain_runtime"},
                {"id": "open-1", "method": "open_armory", "params": {"path": str(armory_path)}},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    plain_response = next(payload for payload in payloads if payload.get("id") == "plain-1")
    open_response = next(payload for payload in payloads if payload.get("id") == "open-1")
    plain_result = _payload_mapping(plain_response["result"])
    open_result = _payload_mapping(open_response["result"])
    plain_service = _payload_mapping(plain_result["service"])
    open_service = _payload_mapping(open_result["service"])

    assert plain_service["available_stream_methods"] == []
    assert open_service["available_stream_methods"] == ["build_index_stream"]
    assert "build_index" not in _payload_list(plain_service["available_stream_methods"])
    assert "build_index" not in _payload_list(open_service["available_stream_methods"])


def test_jsonl_sdk_server_rejects_unavailable_calls_and_streams_before_start() -> None:
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {"id": "ask-plain", "method": "ask", "params": {"text": "hello"}},
                {"id": "prompt-plain", "method": "prompt", "params": {"text": "hello"}},
                {"id": "index-plain", "method": "build_index_stream"},
                {"id": "state-after-unavailable", "method": "state"},
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    ask_error = _payload_mapping(
        next(payload for payload in payloads if payload.get("id") == "ask-plain")["error"]
    )
    prompt_error = _payload_mapping(
        next(payload for payload in payloads if payload.get("id") == "prompt-plain")["error"]
    )
    index_error = _payload_mapping(
        next(payload for payload in payloads if payload.get("id") == "index-plain")["error"]
    )
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-unavailable"
    )
    state_service = _payload_mapping(_payload_mapping(state_response["result"])["service"])

    assert ask_error["code"] == "unavailable"
    assert "ask" in str(ask_error["message"])
    assert prompt_error["code"] == "unavailable"
    assert "prompt" in str(prompt_error["message"])
    assert index_error["code"] == "unavailable"
    assert "build_index" in str(index_error["message"])
    assert [payload for payload in payloads if payload["type"] == "stream_start"] == []
    assert [payload for payload in payloads if payload["type"] == "stream_end"] == []
    assert state_service["is_busy"] is False
    assert state_service["available_stream_methods"] == []


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


def test_jsonl_sdk_server_prunes_completed_stream_threads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    service.new_session()
    started = threading.Event()
    release = threading.Event()

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session, abort
        assert prompt in {"tracked once", "tracked twice"}
        started.set()
        yield AssistantDeltaEvent(prompt)
        assert release.wait(timeout=2.0)
        yield TurnCompleteEvent(prompt, 0, 1.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )

    server.handle_request({"id": "turn-1", "method": "prompt", "params": {"text": "tracked once"}})
    assert started.wait(timeout=2.0)
    with server._stream_threads_lock:
        assert len(server._stream_threads) == 1

    release.set()
    server._wait_for_streams()
    with server._stream_threads_lock:
        assert server._stream_threads == []

    started.clear()
    release.clear()
    server.handle_request(
        {"id": "turn-2", "method": "prompt", "params": {"text": "tracked twice"}}
    )
    assert started.wait(timeout=2.0)
    release.set()
    server._wait_for_streams()

    with server._stream_threads_lock:
        assert server._stream_threads == []
    assert output.getvalue().count('"type": "stream_end"') == 2


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
        "is_busy": True,
        "available_call_methods": list(sdk_methods.BUSY_ALLOWED_CALL_METHODS),
        "available_stream_methods": [],
    }
    assert not direct_abort_seen.is_set()
    assert prompt_errors == []
    assert not thread.is_alive()


def test_jsonl_state_marks_pending_prompt_busy() -> None:
    service = HephService.plain(config=_config())
    service.new_session()
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )
    server._active_prompt = sdk_stdio.ActivePrompt(
        request_id="prompt-pending",
        abort=threading.Event(),
    )

    server.handle_request({"id": "state-during-pending-prompt", "method": "state"})

    payloads = _payloads(output.getvalue())
    result = _payload_mapping(payloads[0]["result"])
    assert _payload_mapping(result["service"]) == {
        "prompt_active": True,
        "active_operation": None,
        "is_busy": True,
        "available_call_methods": list(sdk_methods.BUSY_ALLOWED_CALL_METHODS),
        "available_stream_methods": [],
    }


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
    server.handle_request({"id": "caps-during-index", "method": "capabilities"})
    server.handle_request({"id": "settings-during-index", "method": "settings"})
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
    capabilities_response = next(
        payload for payload in payloads if payload.get("id") == "caps-during-index"
    )
    settings_response = next(
        payload for payload in payloads if payload.get("id") == "settings-during-index"
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
    capabilities = _payload_mapping(
        _payload_mapping(capabilities_response["result"])["capabilities"]
    )
    capability_service = _payload_mapping(capabilities["service"])
    settings = _payload_mapping(_payload_mapping(settings_response["result"])["settings"])
    abort_result = _payload_mapping(abort_response["result"])
    abort_state_service = _payload_mapping(_payload_mapping(abort_result["state"])["service"])
    prompt_error_payload = _payload_mapping(prompt_error["error"])
    events = [
        _payload_mapping(payload["event"])
        for payload in payloads
        if payload["type"] == "stream_event"
    ]
    assert immediate_service == {
        "prompt_active": False,
        "active_operation": "build_index",
        "is_busy": True,
        "available_call_methods": list(sdk_methods.BUSY_ALLOWED_CALL_METHODS),
        "available_stream_methods": [],
    }
    assert state_service == {
        "prompt_active": False,
        "active_operation": "build_index",
        "is_busy": True,
        "available_call_methods": list(sdk_methods.BUSY_ALLOWED_CALL_METHODS),
        "available_stream_methods": [],
    }
    assert capabilities_response["type"] == "response"
    assert "capabilities" in _payload_list(capability_service["busy_allowed_call_methods"])
    assert "settings" in _payload_list(capability_service["busy_allowed_call_methods"])
    assert settings_response["type"] == "response"
    assert settings["theme"] in {"dark", "light"}
    assert abort_result["aborted"] is False
    assert abort_state_service == {
        "prompt_active": False,
        "active_operation": "build_index",
        "is_busy": True,
        "available_call_methods": list(sdk_methods.BUSY_ALLOWED_CALL_METHODS),
        "available_stream_methods": [],
    }
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


def test_jsonl_sdk_server_reports_prompt_stream_errors_and_clears_state(
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
        _ = raw_session, abort
        assert prompt == "fail prompt"
        yield AssistantDeltaEvent("before failure")
        raise RuntimeError("prompt failed")

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )

    server.handle_request(
        {"id": "prompt-error", "method": "prompt", "params": {"text": "fail prompt"}}
    )
    server._wait_for_streams()
    server.handle_request({"id": "state-after-error", "method": "state"})

    payloads = _payloads(output.getvalue())
    stream_events = [payload for payload in payloads if payload["type"] == "stream_event"]
    stream_end = next(
        payload
        for payload in payloads
        if payload.get("id") == "prompt-error" and payload["type"] == "stream_end"
    )
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-error"
    )
    stream_error = _payload_mapping(stream_end["error"])
    service_state = _payload_mapping(_payload_mapping(state_response["result"])["service"])

    assert stream_events == [
        {
            "type": "stream_event",
            "id": "prompt-error",
            "event": {"type": "assistant_delta", "delta": "before failure"},
        }
    ]
    assert stream_end["type"] == "stream_end"
    assert stream_end["ok"] is False
    assert stream_error["code"] == "internal_error"
    assert "prompt failed" in str(stream_error["message"])
    assert service_state == {
        "prompt_active": False,
        "active_operation": None,
        "is_busy": False,
        "available_call_methods": list(
            _service_call_methods(
                "state",
                "capabilities",
                "use_plain_runtime",
                "open_armory",
                "create_armory",
                "list_armories",
                "validate_armory",
                "new_session",
                "fork_session",
                "list_sessions",
                "messages",
                "ask",
                "abort",
                "settings",
                "list_providers",
                "list_model_choices",
                "switch_model",
                "update_config",
                "update_settings",
            )
        ),
        "available_stream_methods": list(_jsonl_stream_methods("prompt")),
    }


def test_jsonl_sdk_server_reports_operation_stream_errors_and_clears_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_path = tmp_path / ".armories" / "jsonl-index-error"
    service = HephService.create_armory(armory_path, config=_config())

    def failing_build_index(
        armory_path: Path,
        *,
        strategy: object | None = None,
        progress: Callable[[str, str], None] | None = None,
        previous: object | None = None,
    ) -> _FakeIndex:
        _ = armory_path, strategy, previous
        assert progress is not None
        progress("reading", "materials/notes.md")
        raise RuntimeError("index failed")

    monkeypatch.setattr(sdk_runtime, "build_rag_index", failing_build_index)
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(""),
        output_stream=output,
    )

    server.handle_request({"id": "index-error", "method": "build_index_stream"})
    server._wait_for_streams()
    server.handle_request({"id": "state-after-error", "method": "state"})

    payloads = _payloads(output.getvalue())
    stream_events = [payload for payload in payloads if payload["type"] == "stream_event"]
    stream_end = next(
        payload
        for payload in payloads
        if payload.get("id") == "index-error" and payload["type"] == "stream_end"
    )
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-error"
    )
    stream_error = _payload_mapping(stream_end["error"])
    service_state = _payload_mapping(_payload_mapping(state_response["result"])["service"])

    assert stream_events == [
        {
            "type": "stream_event",
            "id": "index-error",
            "event": {
                "type": "index_progress",
                "action": "reading",
                "detail": "materials/notes.md",
            },
        }
    ]
    assert stream_end["type"] == "stream_end"
    assert stream_end["ok"] is False
    assert stream_error["code"] == "internal_error"
    assert "index failed" in str(stream_error["message"])
    assert service_state == {
        "prompt_active": False,
        "active_operation": None,
        "is_busy": False,
        "available_call_methods": list(
            _service_call_methods(
                "state",
                "capabilities",
                "use_plain_runtime",
                "open_armory",
                "create_armory",
                "list_armories",
                "validate_armory",
                "new_session",
                "resume_session",
                "list_sessions",
                "settings",
                "list_providers",
                "list_model_choices",
                "switch_model",
                "list_materials",
                "import_materials",
                "build_index",
                "scan_extraction_health",
                "update_config",
                "update_settings",
            )
        ),
        "available_stream_methods": list(_jsonl_stream_methods("build_index_stream")),
    }


def test_jsonl_sdk_server_reports_protocol_errors() -> None:
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            "{broken\n"
            "[]\n"
            f"{json.dumps({'id': 'extra-field', 'method': 'state', 'extra': True})}\n"
            f"{json.dumps({'id': True, 'method': 'state'})}\n"
            f"{json.dumps({'id': 'state-after-protocol-errors', 'method': 'state'})}\n"
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    errors = [payload for payload in payloads if payload["type"] == "error"]
    assert [_payload_mapping(error["error"])["code"] for error in errors] == [
        "invalid_json",
        "invalid_request",
        "invalid_request",
        "invalid_request",
    ]
    extra_field_error = next(
        payload
        for payload in errors
        if "does not accept field: extra" in str(_payload_mapping(payload["error"])["message"])
    )
    assert extra_field_error["type"] == "error"
    assert "does not accept field: extra" in str(
        _payload_mapping(extra_field_error["error"])["message"]
    )
    invalid_id_error = next(
        payload
        for payload in errors
        if "request id must be" in str(_payload_mapping(payload["error"])["message"])
    )
    assert invalid_id_error["id"] is None
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-protocol-errors"
    )
    assert state_response["type"] == "response"
    assert state_response["ok"] is True


def test_jsonl_sdk_server_reports_service_errors_and_continues(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {
                    "id": "bad-param",
                    "method": "state",
                    "params": {"typo": True},
                },
                {
                    "id": "bad-prompt-param",
                    "method": "prompt",
                    "params": {"text": "hello", "typo": True},
                },
                {
                    "id": "bad-index-param",
                    "method": "build_index_stream",
                    "params": {"text": "unused"},
                },
                {
                    "id": "bad-choice",
                    "method": "update_settings",
                    "params": {"theme": "neon"},
                },
                {
                    "id": "bad-type",
                    "method": "ask",
                    "params": {"text": 123},
                },
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
    bad_param = next(payload for payload in payloads if payload.get("id") == "bad-param")
    bad_prompt_param = next(
        payload for payload in payloads if payload.get("id") == "bad-prompt-param"
    )
    bad_index_param = next(
        payload for payload in payloads if payload.get("id") == "bad-index-param"
    )
    bad_choice = next(payload for payload in payloads if payload.get("id") == "bad-choice")
    bad_type = next(payload for payload in payloads if payload.get("id") == "bad-type")
    service_error = next(payload for payload in payloads if payload.get("id") == "bad-armory")
    state_response = next(
        payload for payload in payloads if payload.get("id") == "state-after-error"
    )

    assert bad_param["type"] == "error"
    assert _payload_mapping(bad_param["error"])["code"] == "sdk_error"
    assert "does not accept parameter: typo" in str(
        _payload_mapping(bad_param["error"])["message"]
    )
    assert bad_prompt_param["type"] == "error"
    assert _payload_mapping(bad_prompt_param["error"])["code"] == "sdk_error"
    assert "does not accept parameter: typo" in str(
        _payload_mapping(bad_prompt_param["error"])["message"]
    )
    assert bad_index_param["type"] == "error"
    assert _payload_mapping(bad_index_param["error"])["code"] == "sdk_error"
    assert "does not accept parameter: text" in str(
        _payload_mapping(bad_index_param["error"])["message"]
    )
    assert bad_choice["type"] == "error"
    assert _payload_mapping(bad_choice["error"])["code"] == "sdk_error"
    assert "parameter 'theme' must be one of" in str(
        _payload_mapping(bad_choice["error"])["message"]
    )
    assert bad_type["type"] == "error"
    assert _payload_mapping(bad_type["error"])["code"] == "sdk_error"
    assert "parameter 'text' must be a string" in str(
        _payload_mapping(bad_type["error"])["message"]
    )
    assert service_error["type"] == "error"
    assert _payload_mapping(service_error["error"])["code"] == "sdk_error"
    assert state_response["type"] == "response"
    assert state_response["ok"] is True


def test_jsonl_sdk_server_validates_armory_candidates(tmp_path: Path) -> None:
    armory_path = tmp_path / ".armories" / "valid"
    HephRuntime.create_armory(armory_path, config=_config())
    missing_path = tmp_path / "missing"
    service = HephService.plain(config=_config())
    output = io.StringIO()
    server = JsonlSdkServer(
        service=service,
        input_stream=io.StringIO(
            _jsonl(
                {
                    "id": "valid-armory",
                    "method": "validate_armory",
                    "params": {"path": str(armory_path)},
                },
                {
                    "id": "missing-armory",
                    "method": "validate_armory",
                    "params": {"path": str(missing_path)},
                },
            )
        ),
        output_stream=output,
    )

    server.serve()

    payloads = _payloads(output.getvalue())
    valid_response = next(payload for payload in payloads if payload.get("id") == "valid-armory")
    missing_response = next(
        payload for payload in payloads if payload.get("id") == "missing-armory"
    )
    valid_armory = _payload_mapping(_payload_mapping(valid_response["result"])["armory"])
    missing_armory = _payload_mapping(_payload_mapping(missing_response["result"])["armory"])
    runtime_state = _payload_mapping(_payload_mapping(payloads[0]["state"])["runtime"])

    assert valid_response["type"] == "response"
    assert valid_response["ok"] is True
    assert valid_armory["valid"] is True
    assert valid_armory["path"] == str(armory_path.resolve())
    assert missing_response["type"] == "response"
    assert missing_response["ok"] is True
    assert missing_armory["valid"] is False
    assert missing_armory["exists"] is False
    assert "does not exist" in str(missing_armory["error"])
    assert runtime_state["armory_path"] is None


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
