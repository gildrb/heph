from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from heph.sdk import (
    JSONL_ERROR_CODES,
    JSONL_MESSAGE_TYPES,
    SDK_CAPABILITIES,
    AssistantDelta,
    HephRuntime,
    HephSdkBusyError,
    HephSdkCapabilities,
    HephSdkError,
    HephSdkOptions,
    HephSdkRuntimeState,
    HephSdkServiceState,
    HephSdkSessionState,
    HephSdkState,
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
    get_sdk_capabilities,
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


class _FakeIndex:
    documents = ("doc-1",)
    chunk_count = 7


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


def test_sdk_capabilities_describe_direct_and_jsonl_contracts() -> None:
    capabilities = get_sdk_capabilities()
    payload = capabilities.to_dict()
    service = _payload_mapping(payload["service"])
    jsonl = _payload_mapping(payload["jsonl"])
    events = _payload_mapping(payload["events"])
    state = _payload_mapping(payload["state"])
    service_call_methods = _payload_list(service["call_methods"])
    service_stream_methods = _payload_list(service["stream_methods"])
    busy_allowed_call_methods = _payload_list(service["busy_allowed_call_methods"])
    jsonl_stream_methods = _payload_list(jsonl["stream_methods"])
    jsonl_message_types = _payload_list(jsonl["message_types"])
    jsonl_error_codes = _payload_list(jsonl["error_codes"])
    event_types = _payload_list(events["types"])
    service_fields = _payload_list(state["service_fields"])
    runtime_fields = _payload_list(state["runtime_fields"])
    session_fields = _payload_list(state["session_fields"])

    assert isinstance(capabilities, HephSdkCapabilities)
    assert capabilities is SDK_CAPABILITIES
    assert payload["version"] == 3
    assert "capabilities" in service_call_methods
    assert "build_index" in service_stream_methods
    assert busy_allowed_call_methods == ["state", "abort", "capabilities"]
    assert jsonl["protocol"] == "heph-sdk-jsonl"
    assert "build_index_stream" in jsonl_stream_methods
    assert jsonl_message_types == list(JSONL_MESSAGE_TYPES)
    assert jsonl_error_codes == list(JSONL_ERROR_CODES)
    assert "reasoning_delta" in event_types
    assert "index_progress" in event_types
    assert "index_complete" in event_types
    assert "active_operation" in service_fields
    assert "reasoning_level" in runtime_fields
    assert "enabled_source_files" in session_fields
    assert "is_disposed" in session_fields


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


def test_session_exposes_and_toggles_source_file_scope(tmp_path: Path) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()

    assert session.source_file_count == 1
    assert session.source_files == ("materials/notes.md",)
    assert session.enabled_source_files == ("materials/notes.md",)
    assert session.disabled_source_files == frozenset()

    assert session.set_source_enabled("materials/notes.md", enabled=False)
    assert session.disabled_source_files == frozenset({"materials/notes.md"})
    assert session.enabled_source_files == ()
    assert session.to_dict()["disabled_source_files"] == ["materials/notes.md"]
    assert session.to_dict()["enabled_source_files"] == []
    assert session.has_unsaved_changes

    assert not session.set_source_enabled("materials/notes.md", enabled=False)
    assert session.set_source_enabled("materials/notes.md", enabled=True)
    assert session.disabled_source_files == frozenset()

    with pytest.raises(HephSdkError, match="not attached"):
        session.set_source_enabled("materials/missing.md", enabled=False)


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
    assert not session.is_disposed
    session.dispose()
    assert session.is_disposed
    assert session.to_dict()["is_disposed"] is True


def test_session_dispose_is_idempotent_and_rejects_stale_use(tmp_path: Path) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()

    session.dispose()
    session.dispose()

    assert session.is_disposed
    assert session.to_dict()["is_disposed"] is True
    session.abort()

    with pytest.raises(HephSdkError, match="disposed"):
        session.subscribe(lambda event: None)
    with pytest.raises(HephSdkError, match="disposed"):
        list(session.prompt("This stale session should not stream."))
    with pytest.raises(HephSdkError, match="disposed"):
        session.refresh_materials()
    with pytest.raises(HephSdkError, match="disposed"):
        session.set_source_enabled("materials/notes.md", enabled=False)
    with pytest.raises(HephSdkError, match="disposed"):
        session.save()


def test_session_subscriber_can_unsubscribe_while_events_emit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    first_listener_events: list[str] = []
    second_listener_events: list[str] = []
    unsubscribe_first: list[Callable[[], None]] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session, prompt, abort
        yield AssistantDeltaEvent("first")
        yield AssistantDeltaEvent("second")
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def first_listener(event: object) -> None:
        if isinstance(event, AssistantDelta):
            first_listener_events.append(event.delta)
            unsubscribe_first[0]()

    def second_listener(event: object) -> None:
        if isinstance(event, AssistantDelta):
            second_listener_events.append(f"delta:{event.delta}")
        elif isinstance(event, TurnComplete):
            second_listener_events.append("complete")

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    unsubscribe_first.append(session.subscribe(first_listener))
    unsubscribe_second = session.subscribe(second_listener)

    events = list(session.prompt("Emit multiple events."))

    assert [event.kind for event in events] == [
        "assistant_delta",
        "assistant_delta",
        "turn_complete",
    ]
    assert first_listener_events == ["first"]
    assert second_listener_events == ["delta:first", "delta:second", "complete"]
    unsubscribe_second()


def test_session_rejects_concurrent_prompt_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    started = threading.Event()
    release = threading.Event()
    abort_seen = threading.Event()
    streamed_events: list[object] = []
    stream_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        assert prompt == "First prompt."
        assert abort is not None
        started.set()
        yield AssistantDeltaEvent("first")
        assert release.wait(timeout=2.0)
        if abort.is_set():
            abort_seen.set()
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def collect_events() -> None:
        try:
            streamed_events.extend(session.prompt("First prompt."))
        except Exception as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_events, name="test-sdk-session-prompt")

    thread.start()
    assert started.wait(timeout=2.0)

    assert session.is_streaming
    with pytest.raises(HephSdkBusyError, match="already streaming"):
        list(session.prompt("Second prompt."))

    session.abort()
    release.set()
    thread.join(timeout=2.0)

    assert abort_seen.is_set()
    assert not session.is_streaming
    assert stream_errors == []
    assert len(streamed_events) == 2
    assert not thread.is_alive()


def test_session_rejects_mutations_while_streaming(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    started = threading.Event()
    release = threading.Event()
    stream_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session, prompt, abort
        started.set()
        yield AssistantDeltaEvent("first")
        assert release.wait(timeout=2.0)
        yield TurnCompleteEvent("done", 0, 1.0, "stop", 100)

    def collect_events() -> None:
        try:
            list(session.prompt("First prompt."))
        except Exception as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_events, name="test-sdk-session-mutations")

    thread.start()
    assert started.wait(timeout=2.0)

    with pytest.raises(HephSdkBusyError, match="already streaming"):
        session.set_source_enabled("materials/notes.md", enabled=False)
    with pytest.raises(HephSdkBusyError, match="already streaming"):
        session.refresh_materials()
    with pytest.raises(HephSdkBusyError, match="already streaming"):
        session.save()

    release.set()
    thread.join(timeout=2.0)

    assert stream_errors == []
    assert not thread.is_alive()
    assert not session.is_streaming
    assert session.set_source_enabled("materials/notes.md", enabled=False)
    assert session.save().is_file()


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
        reasoning_level="HIGH",
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
    assert config.reasoning_level == "high"
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
    assert service_state["active_operation"] is None
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


def test_service_state_snapshot_exposes_typed_client_state(tmp_path: Path) -> None:
    config = ChatConfig(
        base_url="https://example.invalid/v1",
        model="typed-state-model",
        temperature=None,
        feature_flags=frozenset({"beta", "alpha"}),
    )
    armory_path = _armory(tmp_path)
    service = HephService.open_armory(armory_path, config=config)

    empty_snapshot = service.state_snapshot()
    session_payload = service.new_session()
    snapshot = service.state_snapshot()

    assert isinstance(empty_snapshot, HephSdkState)
    assert isinstance(empty_snapshot.service, HephSdkServiceState)
    assert isinstance(empty_snapshot.runtime, HephSdkRuntimeState)
    assert empty_snapshot.session is None
    assert snapshot.service.prompt_active is False
    assert snapshot.service.active_operation is None
    assert snapshot.runtime.armory_path == armory_path.resolve()
    assert snapshot.runtime.model == "typed-state-model"
    assert snapshot.runtime.temperature is None
    assert snapshot.runtime.reasoning_level == "low"
    assert snapshot.runtime.feature_flags == ("alpha", "beta")
    assert isinstance(snapshot.session, HephSdkSessionState)
    assert snapshot.session.source_file_count == 1
    assert snapshot.session.source_files == ("materials/notes.md",)
    assert snapshot.session.enabled_source_files == ("materials/notes.md",)
    assert snapshot.session.disabled_source_files == frozenset()
    assert not snapshot.session.has_unsaved_changes
    assert snapshot.session.messages == ()
    assert session_payload["runtime"] == snapshot.runtime.to_dict()
    assert service.state() == snapshot.to_dict()


def test_runtime_state_constructor_keeps_legacy_positional_shape() -> None:
    runtime_state = HephSdkRuntimeState(
        None,
        "sdk-model",
        "https://example.invalid/v1",
        123,
        456,
        None,
        "off",
        (),
    )

    assert runtime_state.reasoning_level == "low"
    assert runtime_state.to_dict()["reasoning_level"] == "low"


def test_session_state_constructor_keeps_legacy_positional_shape() -> None:
    session_state = HephSdkSessionState("session-1", "Title", None, "sdk-model", False, ())

    assert session_state.source_file_count == 0
    assert session_state.source_files == ()
    assert session_state.disabled_source_files == frozenset()
    assert session_state.enabled_source_files == ()
    assert session_state.to_dict() == {
        "session_id": "session-1",
        "title": "Title",
        "armory_path": None,
        "model": "sdk-model",
        "is_streaming": False,
        "is_disposed": False,
        "source_file_count": 0,
        "source_files": [],
        "disabled_source_files": [],
        "enabled_source_files": [],
        "has_unsaved_changes": False,
        "messages": [],
    }


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
    assert active_state["active_operation"] is None
    active_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    active_capability_service = _payload_mapping(active_capabilities["service"])
    assert "capabilities" in _payload_list(active_capability_service["busy_allowed_call_methods"])
    source = tmp_path / "late-material.md"
    source.write_text("# Late\n\nShould not import during streaming.\n", encoding="utf-8")
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.call("new_session")
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.ask("Nested prompt.")
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.update_config({"model": "mutated-during-stream"})
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.import_materials(source)
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.build_index()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.save_session()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.messages()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.list_sessions()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.list_materials()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.scan_extraction_health()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.list_armories()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.set_source_enabled("materials/notes.md", enabled=False)

    abort_payload = service.call("abort")
    release.set()
    thread.join(timeout=2.0)

    idle_state = _payload_mapping(service.state()["service"])
    assert abort_payload["aborted"] is True
    assert abort_seen.is_set()
    assert idle_state["prompt_active"] is False
    assert idle_state["active_operation"] is None
    assert not thread.is_alive()
    assert stream_errors == []
    assert streamed_events[0] == {"type": "notice", "message": "Waiting.", "code": "sdk_test"}


def test_service_treats_direct_session_stream_as_busy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    service.new_session()
    session = service.session
    assert session is not None
    started = threading.Event()
    release = threading.Event()
    abort_seen = threading.Event()
    streamed_events: list[object] = []
    stream_errors: list[Exception] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session
        assert prompt == "Direct session prompt."
        assert abort is not None
        started.set()
        yield NoticeEvent("Waiting.", code="sdk_test")
        assert release.wait(timeout=2.0)
        if abort.is_set():
            abort_seen.set()
        yield TurnCompleteEvent("Stopped.", 0, 1.0, "abort", 100)

    def collect_events() -> None:
        try:
            streamed_events.extend(session.prompt("Direct session prompt."))
        except Exception as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_events, name="test-sdk-direct-session-stream")

    thread.start()
    assert started.wait(timeout=2.0)

    active_state = service.state_snapshot()
    assert active_state.service.prompt_active
    assert active_state.session is not None
    assert active_state.session.is_streaming
    direct_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    direct_capability_service = _payload_mapping(direct_capabilities["service"])
    assert "capabilities" in _payload_list(direct_capability_service["busy_allowed_call_methods"])
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.call("new_session")
    with pytest.raises(HephSdkBusyError, match="already streaming"):
        list(service.prompt("Nested service prompt."))

    abort_payload = service.call("abort")
    release.set()
    thread.join(timeout=2.0)

    assert _payload_mapping(abort_payload["session"])["is_streaming"] is True
    assert abort_seen.is_set()
    assert stream_errors == []
    assert len(streamed_events) == 2
    assert not thread.is_alive()
    assert not service.state_snapshot().service.prompt_active


def test_service_direct_session_stream_start_blocks_replacement_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    service.new_session()
    session = service.session
    assert session is not None
    _assert_direct_stream_start_blocks_service_replacement(service, session, monkeypatch)


def test_service_constructor_session_gets_direct_stream_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    service = HephService(runtime=runtime, session=session)

    _assert_direct_stream_start_blocks_service_replacement(service, session, monkeypatch)


def _assert_direct_stream_start_blocks_service_replacement(
    service: HephService,
    session: HephSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutation_started = threading.Event()
    mutation_done = threading.Event()
    stream_started = threading.Event()
    release = threading.Event()
    streamed_events: list[object] = []
    stream_errors: list[Exception] = []
    mutation_errors: list[Exception] = []
    mutation_payloads: list[dict[str, object]] = []

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session, abort
        assert prompt == "Direct session prompt."
        stream_started.set()
        yield NoticeEvent("Waiting.", code="sdk_test")
        assert release.wait(timeout=2.0)
        yield TurnCompleteEvent("Stopped.", 0, 1.0, "abort", 100)

    def replace_session_during_stream_start() -> None:
        mutation_started.set()
        try:
            mutation_payloads.append(service.new_session())
        except Exception as exc:
            mutation_errors.append(exc)
        finally:
            mutation_done.set()

    mutation_thread = threading.Thread(
        target=replace_session_during_stream_start,
        name="test-sdk-direct-session-replacement-race",
    )
    original_begin_stream = HephSession._begin_stream

    def delayed_begin_stream(active_session: HephSession, abort: threading.Event) -> None:
        if active_session is session:
            mutation_thread.start()
            assert mutation_started.wait(timeout=2.0)
        original_begin_stream(active_session, abort)

    def collect_events() -> None:
        try:
            streamed_events.extend(session.prompt("Direct session prompt."))
        except Exception as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    monkeypatch.setattr(HephSession, "_begin_stream", delayed_begin_stream)
    stream_thread = threading.Thread(target=collect_events, name="test-sdk-direct-session-stream")

    stream_thread.start()
    assert stream_started.wait(timeout=2.0)
    assert mutation_done.wait(timeout=2.0)

    assert mutation_payloads == []
    assert len(mutation_errors) == 1
    assert isinstance(mutation_errors[0], HephSdkBusyError)
    assert service.session is session
    assert service.state_snapshot().service.prompt_active

    release.set()
    stream_thread.join(timeout=2.0)
    mutation_thread.join(timeout=2.0)

    assert stream_errors == []
    assert len(streamed_events) == 2
    assert not stream_thread.is_alive()
    assert not mutation_thread.is_alive()
    assert not service.state_snapshot().service.prompt_active


def test_session_clears_streaming_when_autosave_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    service.new_session()
    session = service.session
    assert session is not None

    def fake_iter_chat_events(
        raw_session: ChatSession,
        prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        _ = raw_session, prompt, abort
        yield TurnCompleteEvent("Stopped.", 0, 1.0, "abort", 100)

    def fail_autosave(raw_session: ChatSession) -> None:
        _ = raw_session
        raise RuntimeError("save failed")

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    monkeypatch.setattr(sdk_runtime, "save_dirty_session_if_needed", fail_autosave)

    with pytest.raises(RuntimeError, match="save failed"):
        list(session.prompt("Prompt that fails autosave."))

    assert not session.is_streaming
    assert not service.state_snapshot().service.prompt_active
    service.new_session()


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
    assert first_session.is_disposed
    with pytest.raises(HephSdkError, match="disposed"):
        list(first_session.prompt("Stale session."))

    service.resume_session(first_session.session_id)
    resumed_session = service.session
    assert resumed_session is not None
    assert resumed_session.session_id == first_session.session_id
    assert disposed_sessions == [first_session, second_session]
    assert second_session.is_disposed

    service.use_plain_runtime()

    assert service.session is None
    assert disposed_sessions == [first_session, second_session, resumed_session]
    assert resumed_session.is_disposed


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


def test_service_streams_build_index_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    service.new_session()
    session = service.session
    assert session is not None
    release = threading.Event()
    finished = threading.Event()

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
        finished.set()
        return _FakeIndex()

    monkeypatch.setattr(sdk_runtime, "build_rag_index", fake_build_index)
    stream = service.stream("build_index")

    first_event = next(stream)
    active_service = _payload_mapping(service.state()["service"])
    assert active_service["prompt_active"] is False
    assert active_service["active_operation"] == "build_index"
    active_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    active_capability_service = _payload_mapping(active_capabilities["service"])
    assert "build_index" in _payload_list(active_capability_service["stream_methods"])
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.new_session()
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        list(service.prompt("Prompt during index."))
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        list(session.prompt("Direct prompt during index."))
    abort_payload = service.call("abort")
    abort_result = _payload_mapping(abort_payload)
    abort_service = _payload_mapping(_payload_mapping(abort_result["state"])["service"])
    assert abort_result["aborted"] is False
    assert abort_service["active_operation"] == "build_index"

    release.set()
    assert finished.wait(timeout=2.0)
    finished_but_unconsumed_service = _payload_mapping(service.state()["service"])
    assert finished_but_unconsumed_service["active_operation"] == "build_index"
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.list_materials()
    remaining_events = list(stream)
    idle_service = _payload_mapping(service.state()["service"])

    assert first_event == {
        "type": "index_progress",
        "action": "reading",
        "detail": "materials/notes.md",
    }
    assert remaining_events == [
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
    assert idle_service["active_operation"] is None


def test_service_streams_build_index_clears_operation_on_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.open_armory(_armory(tmp_path), config=_config())
    release = threading.Event()

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
        assert release.wait(timeout=2.0)
        raise RuntimeError("index failed")

    monkeypatch.setattr(sdk_runtime, "build_rag_index", failing_build_index)
    stream = service.stream("build_index")

    first_event = next(stream)
    active_service = _payload_mapping(service.state()["service"])
    assert active_service["active_operation"] == "build_index"

    release.set()
    with pytest.raises(RuntimeError, match="index failed"):
        list(stream)

    idle_service = _payload_mapping(service.state()["service"])
    assert first_event == {
        "type": "index_progress",
        "action": "reading",
        "detail": "materials/notes.md",
    }
    assert idle_service["active_operation"] is None


def test_service_streams_build_index_with_file_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.create_armory(tmp_path / ".armories" / "service", config=_config())
    armory_path = service.runtime.armory_path
    assert armory_path is not None
    pdf = armory_path / "materials" / "slow.pdf"
    pdf.write_bytes(b"%PDF-1.4\n\x00")

    def slow_chunk_file(*_args: object, **_kwargs: object) -> object:
        time.sleep(3)
        return None

    monkeypatch.setenv("HEPHAION_INDEX_FILE_TIMEOUT_SECONDS", "1")
    monkeypatch.setattr("hephaion.rag.index._is_docling_available", lambda: True)
    monkeypatch.setattr("hephaion.rag.index.chunk_file", slow_chunk_file)

    events = list(service.stream("build_index"))
    skipped = [
        event
        for event in events
        if event.get("type") == "index_progress" and event.get("action") == "skipped"
    ]
    complete = _payload_mapping(events[-1])
    index = _payload_mapping(complete["index"])

    assert skipped == [
        {
            "type": "index_progress",
            "action": "skipped",
            "detail": "materials/slow.pdf: document conversion timed out after 1 second(s)",
        }
    ]
    assert complete["type"] == "index_complete"
    assert index["documents"] == 0
    assert index["chunks"] == 0
    assert _payload_mapping(service.state()["service"])["active_operation"] is None


def test_service_import_materials_refreshes_active_session_sources(tmp_path: Path) -> None:
    service = HephService.create_armory(tmp_path / ".armories" / "service", config=_config())
    first_source = tmp_path / "week-1.md"
    first_source.write_text("# Week 1\n\nFirst material.\n", encoding="utf-8")
    second_source = tmp_path / "week-2.md"
    second_source.write_text("# Week 2\n\nSecond material.\n", encoding="utf-8")

    service.import_materials(first_source)
    service.new_session()
    assert service.session is not None
    assert service.session.source_files == ("materials/week-1.md",)

    service.import_materials(second_source)

    assert service.session.source_files == (
        "materials/week-1.md",
        "materials/week-2.md",
    )
    toggle_payload = service.call(
        "set_source_enabled",
        {"source": "materials/week-1.md", "enabled": False},
    )
    session_payload = _payload_mapping(toggle_payload["session"])

    assert toggle_payload["changed"] is True
    assert session_payload["disabled_source_files"] == ["materials/week-1.md"]
    assert session_payload["enabled_source_files"] == ["materials/week-2.md"]
    assert session_payload["has_unsaved_changes"] is True

    no_change_payload = service.set_source_enabled("materials/week-1.md", enabled=False)
    assert no_change_payload["changed"] is False


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
            "reasoning_level": "xhigh",
            "thinking_visibility": "all",
        },
    )
    zero_config_payload = service.call(
        "update_config",
        {"max_tokens": 0, "rag_context_budget": 0},
    )
    default_reasoning_payload = service.call("update_config", {"reasoning_level": ""})
    capabilities_payload = service.call("capabilities")
    events = list(service.stream("prompt", {"text": "Dispatch this."}))
    ask = service.call("ask", {"text": "Return final text."})

    runtime_payload = _payload_mapping(config_payload["runtime"])
    zero_runtime_payload = _payload_mapping(zero_config_payload["runtime"])
    default_reasoning_runtime = _payload_mapping(default_reasoning_payload["runtime"])
    capabilities = _payload_mapping(capabilities_payload["capabilities"])
    capability_service = _payload_mapping(capabilities["service"])
    assert runtime_payload["model"] == "updated-model"
    assert runtime_payload["max_tokens"] == 500
    assert runtime_payload["temperature"] == 2.0
    assert runtime_payload["reasoning_level"] == "xhigh"
    assert runtime_payload["thinking_visibility"] == "all"
    assert zero_runtime_payload["max_tokens"] == 0
    assert zero_runtime_payload["rag_context_budget"] == 0
    assert default_reasoning_runtime["reasoning_level"] == "low"
    assert capabilities_payload == service.capabilities()
    assert "capabilities" in _payload_list(capability_service["call_methods"])
    assert events[0] == {"type": "assistant_delta", "delta": "Dispatched."}
    assert _payload_mapping(ask)["text"] == "Dispatched."

    with pytest.raises(HephSdkError, match="Unknown SDK service method"):
        service.call("missing")
    with pytest.raises(HephSdkError, match="non-empty string"):
        list(service.stream("prompt", {"text": ""}))
    with pytest.raises(HephSdkError, match="must be a boolean"):
        service.call("set_source_enabled", {"source": "materials/notes.md", "enabled": "no"})


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
