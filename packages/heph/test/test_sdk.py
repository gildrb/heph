from __future__ import annotations

import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from heph.sdk import (
    AssistantDelta,
    HephRuntime,
    HephSdkError,
    HephSdkOptions,
    HephService,
    HephSession,
    ImportMaterialsSummary,
    IndexSummary,
    MaterialOperation,
    Notice,
    ReasoningDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
    create_chat_config,
    create_heph_runtime,
    create_heph_service,
    create_heph_session,
    event_to_dict,
    from_turn_event,
)
from heph.sdk import runtime as sdk_runtime
from hephaion.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ReasoningDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaion.chat.session import ChatSession
from hephaion.rag.health import ExtractionHealthIssue, ExtractionHealthReport


def _config() -> ChatConfig:
    return ChatConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini")


def _armory(tmp_path: Path) -> Path:
    armory_path = tmp_path / ".armories" / "sdk-armory"
    runtime = HephRuntime.create_armory(armory_path, config=_config())
    assert runtime.armory_path == armory_path.resolve()
    materials_path = armory_path / "materials" / "notes.md"
    materials_path.write_text("# Notes\n\nLocal source content.\n", encoding="utf-8")
    return armory_path


def _payload_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return {str(key): item for key, item in value.items()}


def _payload_list(value: object) -> list[object]:
    assert isinstance(value, list)
    result: list[object] = list(value)
    return result


def test_sdk_event_conversion_keeps_json_ready_shape() -> None:
    assert from_turn_event(AssistantDeltaEvent("hello")) == AssistantDelta("hello")

    reasoning = from_turn_event(ReasoningDeltaEvent("checking", summary=True))
    assert isinstance(reasoning, ReasoningDelta)
    assert event_to_dict(reasoning) == {
        "type": "reasoning_delta",
        "delta": "checking",
        "summary": True,
    }

    tool_call = from_turn_event(
        ToolCallEvent("call-1", "search_materials", {"query": "notes"}, "search")
    )
    assert isinstance(tool_call, ToolCall)
    assert event_to_dict(tool_call) == {
        "type": "tool_call",
        "call_id": "call-1",
        "name": "search_materials",
        "arguments": {"query": "notes"},
        "display": "search",
    }

    tool_result = from_turn_event(
        ToolResultEvent(
            "call-1",
            "search_materials",
            "full result",
            "summary",
            metadata={"latency_ms": 12},
        )
    )
    assert isinstance(tool_result, ToolResult)
    assert event_to_dict(tool_result)["metadata"] == {"latency_ms": 12}

    material = from_turn_event(
        MaterialOperationEvent("search_index", "Searching materials.", {"query": "notes"})
    )
    assert isinstance(material, MaterialOperation)
    assert event_to_dict(material) == {
        "type": "material_operation",
        "operation": "search_index",
        "message": "Searching materials.",
        "metadata": {"query": "notes"},
    }

    notice = from_turn_event(NoticeEvent("Checking citations.", code="verification"))
    assert isinstance(notice, Notice)
    assert event_to_dict(notice) == {
        "type": "notice",
        "message": "Checking citations.",
        "code": "verification",
    }

    complete = from_turn_event(TurnCompleteEvent("done", 2, 4.5, "stop", 123))
    assert isinstance(complete, TurnComplete)
    assert complete.to_dict()["full_text"] == "done"


def test_session_prompt_streams_sdk_events_and_autosaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_path = _armory(tmp_path)
    runtime = HephRuntime.open_armory(armory_path, config=_config())
    session = runtime.new_session()

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        assert prompt == "Explain the notes."
        assert abort is not None
        assert not abort.is_set()
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "The notes are local.")
        raw_session.dirty = True
        yield NoticeEvent("Searching materials.", code="evidence")
        yield AssistantDeltaEvent("The notes are local.")
        yield TurnCompleteEvent("The notes are local.", 0, 3.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    events = list(session.prompt("Explain the notes."))

    assert [event.kind for event in events] == ["notice", "assistant_delta", "turn_complete"]
    assert session.messages[-2].to_dict() == {"role": "user", "content": "Explain the notes."}
    assert session.messages[-1].content == "The notes are local."
    assert (armory_path / ".hephaion" / "chats" / f"{session.session_id}.json").is_file()


def test_session_ask_returns_final_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = abort
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "Final reply.")
        raw_session.dirty = True
        yield AssistantDeltaEvent("Partial")
        yield TurnCompleteEvent("Final reply.", 0, 2.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    assert session.ask("What changed?") == "Final reply."


def test_session_messages_hide_internal_system_prompt(tmp_path: Path) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()

    assert any(message.role == "system" for message in session._session.conversation.messages)
    assert session.messages == ()
    assert session.to_dict()["messages"] == []


def test_session_subscribe_abort_and_dispose(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    received: list[str] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        _ = prompt
        assert abort is not None
        yield AssistantDeltaEvent("first")
        assert abort.is_set()
        yield TurnCompleteEvent("stopped", 0, 1.0, "abort", 100)

    def listener(event: object) -> None:
        assert session.is_streaming
        if isinstance(event, AssistantDelta):
            received.append(event.delta)
            session.abort()

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    unsubscribe = session.subscribe(listener)

    events = list(session.prompt("Stop after first event."))

    assert received == ["first"]
    assert [event.kind for event in events] == ["assistant_delta", "turn_complete"]
    assert not session.is_streaming
    unsubscribe()
    session.dispose()


def test_runtime_lists_saves_and_resumes_sessions(tmp_path: Path) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()

    saved_path = session.save()
    summaries = runtime.list_sessions()
    resumed = runtime.resume_session(session.session_id)

    assert saved_path.is_file()
    assert [summary.session_id for summary in summaries] == [session.session_id]
    assert resumed.session_id == session.session_id
    assert resumed.armory_path == runtime.armory_path


def test_factory_creates_runtime_service_and_session(tmp_path: Path) -> None:
    options = HephSdkOptions(
        armory_path=tmp_path / ".armories" / "factory",
        create_armory=True,
        model="sdk-model",
        base_url="https://example.invalid/v1",
        max_tokens=123,
        rag_context_budget=456,
        temperature=3.0,
        feature_flags=frozenset({"sdk"}),
        thinking_visibility="all",
    )
    materials_path = Path(options.armory_path or "") / "materials" / "notes.md"

    runtime_result = create_heph_runtime(options)
    materials_path.write_text("# Factory\n\nSource text.\n", encoding="utf-8")
    service_result = create_heph_service(options)
    session_result = create_heph_session(options)
    config = create_chat_config(options)

    assert runtime_result.runtime.armory_path == Path(options.armory_path or "").resolve()
    assert service_result.service.runtime.config.model == "sdk-model"
    assert service_result.session is not None
    assert session_result.session.armory_path == runtime_result.runtime.armory_path
    assert config.temperature == 2.0
    assert config.feature_flags == frozenset({"sdk"})
    assert config.thinking_visibility == "all"


def test_plain_runtime_cannot_resume_saved_session() -> None:
    runtime = HephRuntime.plain(config=_config())

    assert runtime.list_sessions() == ()
    with pytest.raises(HephSdkError, match="without an armory"):
        runtime.resume_session("abc123")


def test_runtime_imports_lists_indexes_and_scans_materials(tmp_path: Path) -> None:
    runtime = HephRuntime.create_armory(tmp_path / ".armories" / "fresh", config=_config())
    source = tmp_path / "external-notes.md"
    source.write_text("# External Notes\n\nFormula-not-decoded appears here.\n", encoding="utf-8")

    imported = runtime.import_materials(source)
    materials = runtime.list_materials()
    index = runtime.build_index()
    health = runtime.scan_extraction_health()

    assert isinstance(imported, ImportMaterialsSummary)
    assert imported.to_dict() == {
        "imported": ["external-notes.md"],
        "considered": 1,
        "skipped": 0,
        "skipped_duplicates": 0,
        "skipped_unsupported": 0,
    }
    assert len(materials) == 1
    assert materials[0].rel_path == "materials/external-notes.md"
    assert materials[0].display_name == "external-notes.md"
    assert materials[0].to_dict()["role"] == "reference"
    assert isinstance(index, IndexSummary)
    assert index.documents == 1
    assert index.chunks >= 1
    assert index.progress
    assert health.passed
    assert health.issues == ()
    assert health.to_dict()["passed"] is True


def test_runtime_extraction_health_converts_issues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())

    def fake_scan_extraction_health_report(_armory_path: Path) -> ExtractionHealthReport:
        return ExtractionHealthReport(
            armory_path=str(runtime.armory_path),
            documents=1,
            checks=2,
            pass_rate=0.5,
            forbidden_text=("Formula-not-decoded", "Image-not-decoded"),
            issues=(
                ExtractionHealthIssue(
                    source="materials/broken.pdf",
                    forbidden_text_present=("Formula-not-decoded",),
                ),
            ),
        )

    monkeypatch.setattr(
        sdk_runtime,
        "scan_extraction_health_report",
        fake_scan_extraction_health_report,
    )

    health = runtime.scan_extraction_health()

    assert not health.passed
    assert health.issues[0].source == "materials/broken.pdf"
    assert health.issues[0].to_dict() == {
        "source": "materials/broken.pdf",
        "forbidden_text_present": ["Formula-not-decoded"],
    }


def test_plain_runtime_rejects_material_operations(tmp_path: Path) -> None:
    runtime = HephRuntime.plain(config=_config())

    with pytest.raises(HephSdkError, match="without an armory"):
        runtime.list_materials()
    with pytest.raises(HephSdkError, match="without an armory"):
        runtime.import_materials(tmp_path / "notes.md")
    with pytest.raises(HephSdkError, match="without an armory"):
        runtime.build_index()
    with pytest.raises(HephSdkError, match="without an armory"):
        runtime.scan_extraction_health()


def test_service_manages_runtime_session_and_streams_json_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    session_payload = service.new_session()

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = abort
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "Service reply.")
        raw_session.dirty = True
        yield AssistantDeltaEvent("Service reply.")
        yield TurnCompleteEvent("Service reply.", 0, 1.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    events = list(service.prompt("Use the service."))
    messages = service.messages()

    service_state = _payload_mapping(service.state()["service"])
    runtime_payload = _payload_mapping(session_payload["runtime"])
    message_payloads = _payload_list(messages["messages"])

    assert service_state["prompt_active"] is False
    assert runtime_payload["model"] == "gpt-4o-mini"
    assert events == [
        {"type": "assistant_delta", "delta": "Service reply."},
        {
            "type": "turn_complete",
            "full_text": "Service reply.",
            "turn_index": 0,
            "latency_ms": 1.0,
            "finish_reason": "stop",
            "tokens_remaining": 100,
        },
    ]
    assert message_payloads[-2:] == [
        {"role": "user", "content": "Use the service."},
        {"role": "assistant", "content": "Service reply."},
    ]


def test_service_blocks_state_changes_while_prompt_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    service.new_session()
    started = threading.Event()
    release = threading.Event()
    abort_seen = threading.Event()
    streamed_events: list[dict[str, object]] = []
    stream_errors: list[BaseException] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "Delayed reply.")
        raw_session.dirty = True
        started.set()
        yield NoticeEvent("Waiting.", code="sdk_test")
        assert release.wait(timeout=2.0)
        if abort is not None and abort.is_set():
            abort_seen.set()
        yield TurnCompleteEvent("Delayed reply.", 0, 1.0, "stop", 100)

    def collect_events() -> None:
        try:
            streamed_events.extend(service.prompt("Wait for abort."))
        except BaseException as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_events, name="test-sdk-service-prompt")

    thread.start()
    assert started.wait(timeout=2.0)

    active_state = _payload_mapping(service.state()["service"])
    assert active_state["prompt_active"] is True
    source = tmp_path / "late-material.md"
    source.write_text("# Late\n\nShould not import during streaming.\n", encoding="utf-8")
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.call("new_session")
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.ask("Nested prompt.")
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.update_config({"model": "mutated-during-stream"})
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.import_materials(source)
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.build_index()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.save_session()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.messages()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.list_sessions()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.list_materials()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.scan_extraction_health()
    with pytest.raises(HephSdkError, match="only state and abort"):
        service.list_armories()

    abort_payload = service.call("abort")
    release.set()
    thread.join(timeout=2.0)

    idle_state = _payload_mapping(service.state()["service"])
    assert abort_payload["aborted"] is True
    assert abort_seen.is_set()
    assert idle_state["prompt_active"] is False
    assert not thread.is_alive()
    assert stream_errors == []
    assert streamed_events[0] == {"type": "notice", "message": "Waiting.", "code": "sdk_test"}


def test_service_disposes_replaced_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    disposed_sessions: list[HephSession] = []
    original_dispose = HephSession.dispose

    def record_dispose(session: HephSession) -> None:
        disposed_sessions.append(session)
        original_dispose(session)

    monkeypatch.setattr(HephSession, "dispose", record_dispose)

    service.new_session()
    first_session = service.session
    assert first_session is not None
    first_session.save()

    service.new_session()
    second_session = service.session
    assert second_session is not None
    assert disposed_sessions == [first_session]

    service.resume_session(first_session.session_id)
    resumed_session = service.session
    assert resumed_session is not None
    assert resumed_session.session_id == first_session.session_id
    assert disposed_sessions == [first_session, second_session]

    service.use_plain_runtime()

    assert service.session is None
    assert disposed_sessions == [first_session, second_session, resumed_session]


def test_service_material_methods_return_transport_ready_payloads(tmp_path: Path) -> None:
    service = HephService.create_armory(tmp_path / ".armories" / "service", config=_config())
    source = tmp_path / "week-1.md"
    source.write_text("# Week 1\n\nService material.\n", encoding="utf-8")

    imported = service.import_materials(source)
    materials = service.list_materials()
    index = service.build_index()
    health = service.scan_extraction_health()

    import_payload = _payload_mapping(imported["import"])
    material_payloads = _payload_list(materials["materials"])
    first_material = _payload_mapping(material_payloads[0])
    index_payload = _payload_mapping(index["index"])
    health_payload = _payload_mapping(health["health"])

    assert import_payload["imported"] == ["week-1.md"]
    assert first_material["display_name"] == "week-1.md"
    assert index_payload["documents"] == 1
    assert health_payload["passed"] is True


def test_service_import_materials_refreshes_active_session_sources(tmp_path: Path) -> None:
    service = HephService.create_armory(tmp_path / ".armories" / "service", config=_config())
    first_source = tmp_path / "week-1.md"
    first_source.write_text("# Week 1\n\nFirst material.\n", encoding="utf-8")
    second_source = tmp_path / "week-2.md"
    second_source.write_text("# Week 2\n\nSecond material.\n", encoding="utf-8")

    service.import_materials(first_source)
    service.new_session()
    assert service.session is not None
    assert service.session._session.source_files == ("materials/week-1.md",)

    service.import_materials(second_source)

    assert service.session._session.source_files == (
        "materials/week-1.md",
        "materials/week-2.md",
    )


def test_service_call_and_stream_dispatcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_config())
    armory = _armory(tmp_path)
    service.call("open_armory", {"path": str(armory)})
    service.call("new_session")

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = abort
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "Dispatched.")
        raw_session.dirty = True
        yield AssistantDeltaEvent("Dispatched.")
        yield TurnCompleteEvent("Dispatched.", 0, 1.0, "stop", 100)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    config_payload = service.call(
        "update_config",
        {
            "model": "updated-model",
            "max_tokens": 500,
            "temperature": 4.0,
            "thinking_visibility": "all",
        },
    )
    zero_config_payload = service.call(
        "update_config",
        {"max_tokens": 0, "rag_context_budget": 0},
    )
    events = list(service.stream("prompt", {"text": "Dispatch this."}))
    ask = service.call("ask", {"text": "Return final text."})

    runtime_payload = _payload_mapping(config_payload["runtime"])
    zero_runtime_payload = _payload_mapping(zero_config_payload["runtime"])
    assert runtime_payload["model"] == "updated-model"
    assert runtime_payload["max_tokens"] == 500
    assert runtime_payload["temperature"] == 2.0
    assert runtime_payload["thinking_visibility"] == "all"
    assert zero_runtime_payload["max_tokens"] == 0
    assert zero_runtime_payload["rag_context_budget"] == 0
    assert events[0] == {"type": "assistant_delta", "delta": "Dispatched."}
    assert _payload_mapping(ask)["text"] == "Dispatched."

    with pytest.raises(HephSdkError, match="Unknown SDK service method"):
        service.call("missing")
    with pytest.raises(HephSdkError, match="non-empty string"):
        list(service.stream("prompt", {"text": ""}))


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("max_tokens", True, "integer"),
        ("max_tokens", False, "integer"),
        ("rag_context_budget", True, "integer"),
        ("rag_context_budget", False, "integer"),
        ("temperature", True, "number or null"),
        ("temperature", False, "number or null"),
    ],
)
def test_service_update_config_rejects_boolean_numeric_values(
    key: str,
    value: bool,
    message: str,
) -> None:
    service = HephService.plain(config=_config())
    original = service.runtime.config

    with pytest.raises(HephSdkError, match=message):
        service.call("update_config", {key: value})

    assert original.max_tokens == 4096
    assert original.rag_context_budget == 2000
    assert original.temperature == 0.0


def test_service_requires_active_session_for_session_operations() -> None:
    service = HephService.plain(config=_config())

    with pytest.raises(HephSdkError, match="No active SDK session"):
        service.messages()
    with pytest.raises(HephSdkError, match="No active SDK session"):
        list(service.prompt("hello"))
    with pytest.raises(HephSdkError, match="No active SDK session"):
        service.save_session()
