from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from ai.providers.config import default_config
from ai.runtime import ChatConfig
from heph.sdk import (
    JSONL_ERROR_CODES,
    JSONL_MESSAGE_TYPES,
    SDK_CAPABILITIES,
    ArmoryValidationSummary,
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
    ModelChoiceSummary,
    Notice,
    ProviderSummary,
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
from heph.sdk import methods as sdk_methods
from heph.sdk import models as sdk_models
from heph.sdk import providers as sdk_providers
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


def _pollinations_config(monkeypatch: pytest.MonkeyPatch) -> ChatConfig:
    provider_config = default_config()
    monkeypatch.setattr(
        sdk_models.ProviderConfig,
        "load",
        classmethod(lambda _cls: provider_config),
    )
    monkeypatch.setattr(sdk_models.ProviderConfig, "save", lambda _self, path=None: None)
    config = ChatConfig()
    provider_config.apply_to_config(config)
    return config


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


def _payloads_by_slug(items: object) -> dict[str, dict[str, object]]:
    providers: dict[str, dict[str, object]] = {}
    for item in _payload_list(items):
        provider = _payload_mapping(item)
        providers[str(provider["provider_slug"])] = provider
    return providers


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
    methods = _payload_mapping(payload["methods"])
    errors = _payload_mapping(payload["errors"])
    results = _payload_mapping(payload["results"])
    fields = _payload_mapping(payload["fields"])
    service_call_methods = _payload_list(service["call_methods"])
    service_stream_methods = _payload_list(service["stream_methods"])
    busy_allowed_call_methods = _payload_list(service["busy_allowed_call_methods"])
    jsonl_call_methods = _payload_list(jsonl["call_methods"])
    jsonl_stream_methods = _payload_list(jsonl["stream_methods"])
    service_call_specs = _payload_mapping(methods["service_call"])
    service_stream_specs = _payload_mapping(methods["service_stream"])
    jsonl_call_specs = _payload_mapping(methods["jsonl_call"])
    jsonl_stream_specs = _payload_mapping(methods["jsonl_stream"])
    service_call_results = _payload_mapping(results["service_call"])
    jsonl_call_results = _payload_mapping(results["jsonl_call"])
    jsonl_error_specs = _payload_mapping(errors["jsonl"])
    jsonl_message_types = _payload_list(jsonl["message_types"])
    jsonl_error_codes = _payload_list(jsonl["error_codes"])
    event_types = _payload_list(events["types"])
    event_specs = _payload_mapping(events["specs"])
    service_fields = _payload_list(state["service_fields"])
    runtime_fields = _payload_list(state["runtime_fields"])
    session_fields = _payload_list(state["session_fields"])
    service_field_specs = _payload_mapping(fields["service_state"])
    runtime_field_specs = _payload_mapping(fields["runtime_state"])
    session_field_specs = _payload_mapping(fields["session_state"])

    assert isinstance(capabilities, HephSdkCapabilities)
    assert capabilities is SDK_CAPABILITIES
    assert payload["version"] == sdk_methods.SDK_CAPABILITIES_VERSION
    assert service_call_methods == list(sdk_methods.SERVICE_CALL_METHODS)
    assert service_stream_methods == list(sdk_methods.SERVICE_STREAM_METHODS)
    assert busy_allowed_call_methods == list(sdk_methods.BUSY_ALLOWED_CALL_METHODS)
    assert jsonl_call_methods == list(sdk_methods.JSONL_CALL_METHODS)
    assert jsonl_stream_methods == list(sdk_methods.JSONL_STREAM_METHODS)
    assert list(service_call_specs) == service_call_methods
    assert list(service_stream_specs) == service_stream_methods
    assert list(jsonl_call_specs) == jsonl_call_methods
    assert list(jsonl_stream_specs) == jsonl_stream_methods
    assert list(service_call_results) == service_call_methods
    assert list(jsonl_call_results) == jsonl_call_methods
    assert "capabilities" in service_call_methods
    assert "validate_armory" in service_call_methods
    assert "list_providers" in service_call_methods
    assert "list_model_choices" in service_call_methods
    assert "switch_model" in service_call_methods
    assert "build_index" in service_stream_methods
    assert jsonl["protocol"] == "heph-sdk-jsonl"
    assert "build_index_stream" in jsonl_stream_methods
    assert sdk_methods.service_stream_method_for_jsonl("build_index_stream") == "build_index"
    assert sdk_methods.service_stream_method_for_jsonl("prompt") is None
    assert sdk_methods.service_stream_method_for_jsonl("unknown") is None
    open_armory_spec = _payload_mapping(service_call_specs["open_armory"])
    open_armory_params = [
        _payload_mapping(param) for param in _payload_list(open_armory_spec["params"])
    ]
    switch_model_spec = _payload_mapping(service_call_specs["switch_model"])
    switch_model_params = [
        _payload_mapping(param) for param in _payload_list(switch_model_spec["params"])
    ]
    prompt_spec = _payload_mapping(jsonl_stream_specs["prompt"])
    prompt_params = [_payload_mapping(param) for param in _payload_list(prompt_spec["params"])]
    update_config_spec = _payload_mapping(service_call_specs["update_config"])
    update_config_params = [
        _payload_mapping(param) for param in _payload_list(update_config_spec["params"])
    ]
    assert open_armory_params == [{"name": "path", "type": "string", "required": True}]
    assert switch_model_params == [
        {"name": "provider_slug", "type": "string", "required": True},
        {"name": "model", "type": "string", "required": True},
    ]
    assert prompt_params == [{"name": "text", "type": "string", "required": True}]
    assert {"name": "temperature", "type": "number_or_null", "required": False} in (
        update_config_params
    )
    state_result = _payload_mapping(service_call_results["state"])
    capabilities_result = _payload_mapping(service_call_results["capabilities"])
    capabilities_result_fields = _payload_mapping(capabilities_result["fields"])
    list_providers_result = _payload_mapping(service_call_results["list_providers"])
    list_providers_result_fields = _payload_mapping(list_providers_result["fields"])
    switch_model_result = _payload_mapping(service_call_results["switch_model"])
    switch_model_result_fields = _payload_mapping(switch_model_result["fields"])
    abort_result = _payload_mapping(service_call_results["abort"])
    abort_result_fields = _payload_mapping(abort_result["fields"])
    messages_result = _payload_mapping(service_call_results["messages"])
    messages_result_fields = _payload_mapping(messages_result["fields"])
    assert state_result == {"type": "sdk_state", "fields": {}}
    assert _payload_mapping(capabilities_result_fields["capabilities"]) == {
        "type": "sdk_capabilities",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(list_providers_result_fields["providers"]) == {
        "type": "array<provider_summary>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(switch_model_result_fields["session"]) == {
        "type": "sdk_session_state",
        "required": True,
        "nullable": True,
    }
    assert _payload_mapping(abort_result_fields["state"]) == {
        "type": "sdk_state",
        "required": False,
        "nullable": False,
    }
    assert _payload_mapping(abort_result_fields["session"]) == {
        "type": "sdk_session_state",
        "required": False,
        "nullable": False,
    }
    assert _payload_mapping(messages_result_fields["messages"]) == {
        "type": "array<message>",
        "required": True,
        "nullable": False,
    }
    assert jsonl_message_types == list(JSONL_MESSAGE_TYPES)
    assert jsonl_error_codes == list(JSONL_ERROR_CODES)
    assert list(jsonl_error_specs) == jsonl_error_codes
    busy_error_spec = _payload_mapping(jsonl_error_specs["busy"])
    internal_error_spec = _payload_mapping(jsonl_error_specs["internal_error"])
    assert "stream was active" in str(busy_error_spec["description"])
    assert "unexpected server-side exception" in str(internal_error_spec["description"])
    assert "reasoning_delta" in event_types
    assert "index_progress" in event_types
    assert "index_complete" in event_types
    assert list(event_specs) == event_types
    assistant_event_fields = _payload_mapping(
        _payload_mapping(event_specs["assistant_delta"])["fields"]
    )
    turn_complete_fields = _payload_mapping(
        _payload_mapping(event_specs["turn_complete"])["fields"]
    )
    tool_result_fields = _payload_mapping(_payload_mapping(event_specs["tool_result"])["fields"])
    index_complete_fields = _payload_mapping(
        _payload_mapping(event_specs["index_complete"])["fields"]
    )
    assistant_type_spec = _payload_mapping(assistant_event_fields["type"])
    assistant_delta_spec = _payload_mapping(assistant_event_fields["delta"])
    turn_latency_spec = _payload_mapping(turn_complete_fields["latency_ms"])
    tool_metadata_spec = _payload_mapping(tool_result_fields["metadata"])
    tool_error_spec = _payload_mapping(tool_result_fields["error"])
    index_summary_spec = _payload_mapping(index_complete_fields["index"])
    assert assistant_type_spec == {
        "type": "literal<assistant_delta>",
        "required": True,
        "nullable": False,
    }
    assert assistant_delta_spec == {"type": "string", "required": True, "nullable": False}
    assert turn_latency_spec == {"type": "number", "required": True, "nullable": False}
    assert tool_metadata_spec == {"type": "object", "required": False, "nullable": False}
    assert tool_error_spec == {"type": "string", "required": False, "nullable": False}
    assert index_summary_spec == {"type": "index_summary", "required": True, "nullable": False}
    assert "active_operation" in service_fields
    assert "is_busy" in service_fields
    assert "provider_slug" in runtime_fields
    assert "reasoning_level" in runtime_fields
    assert "provider_slug" in session_fields
    assert "enabled_source_files" in session_fields
    assert "is_disposed" in session_fields
    assert list(service_field_specs) == service_fields
    assert list(runtime_field_specs) == runtime_fields
    assert list(session_field_specs) == session_fields
    service_operation_spec = _payload_mapping(service_field_specs["active_operation"])
    runtime_armory_spec = _payload_mapping(runtime_field_specs["armory_path"])
    runtime_flags_spec = _payload_mapping(runtime_field_specs["feature_flags"])
    session_messages_spec = _payload_mapping(session_field_specs["messages"])
    assert service_operation_spec == {"type": "string", "nullable": True}
    assert runtime_armory_spec == {"type": "string", "nullable": True}
    assert runtime_flags_spec == {"type": "array<string>", "nullable": False}
    assert session_messages_spec == {"type": "array<message>", "nullable": False}


def test_runtime_validates_armory_paths_without_opening_runtime(tmp_path: Path) -> None:
    armory_path = _armory(tmp_path)
    missing_path = tmp_path / "missing-armory"
    file_path = tmp_path / "not-an-armory.txt"
    file_path.write_text("not a directory", encoding="utf-8")
    broken_path = tmp_path / "broken-armory"
    broken_path.mkdir()
    service = HephService.plain(config=_config())

    valid = HephRuntime.validate_armory(armory_path)
    valid_payload = _payload_mapping(
        service.call("validate_armory", {"path": str(armory_path)})["armory"]
    )
    missing = HephRuntime.validate_armory(missing_path)
    file_candidate = HephRuntime.validate_armory(file_path)
    broken_payload = _payload_mapping(service.validate_armory(broken_path)["armory"])
    unknown_user = HephRuntime.validate_armory("~definitely_no_such_user/armory")
    plain_runtime = _payload_mapping(service.state()["runtime"])

    assert isinstance(valid, ArmoryValidationSummary)
    assert valid.path == armory_path.resolve()
    assert valid.name == "sdk-armory"
    assert valid.exists
    assert valid.is_dir
    assert valid.valid
    assert valid.error == ""
    assert valid_payload == valid.to_dict()
    assert missing.exists is False
    assert missing.is_dir is False
    assert missing.valid is False
    assert "does not exist" in missing.error
    assert file_candidate.exists is True
    assert file_candidate.is_dir is False
    assert file_candidate.valid is False
    assert "not a directory" in file_candidate.error
    assert broken_payload["exists"] is True
    assert broken_payload["is_dir"] is True
    assert broken_payload["valid"] is False
    assert "missing armory marker file" in str(broken_payload["error"])
    assert unknown_user.exists is False
    assert unknown_user.is_dir is False
    assert unknown_user.valid is False
    assert unknown_user.error
    assert plain_runtime["armory_path"] is None


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


def test_session_listener_failure_does_not_stop_stream_or_other_listeners(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ListenerFailureError(Exception):
        pass

    runtime = HephRuntime.open_armory(_armory(tmp_path), config=_config())
    session = runtime.new_session()
    failing_listener_events: list[str] = []
    healthy_listener_events: list[str] = []

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

    def failing_listener(event: object) -> None:
        if isinstance(event, AssistantDelta):
            failing_listener_events.append(event.delta)
            raise ListenerFailureError("listener failed")

    def healthy_listener(event: object) -> None:
        if isinstance(event, AssistantDelta):
            healthy_listener_events.append(event.delta)
        elif isinstance(event, TurnComplete):
            healthy_listener_events.append("complete")

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    session.subscribe(failing_listener)
    session.subscribe(healthy_listener)

    events = list(session.prompt("Keep streaming after listener failure."))

    assert [event.kind for event in events] == [
        "assistant_delta",
        "assistant_delta",
        "turn_complete",
    ]
    assert failing_listener_events == ["first", "second"]
    assert healthy_listener_events == ["first", "second", "complete"]
    assert not session.is_streaming


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


def test_runtime_rejects_fork_from_streaming_or_disposed_session(
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
            list(session.prompt("Prompt before fork."))
        except Exception as exc:
            stream_errors.append(exc)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)
    thread = threading.Thread(target=collect_events, name="test-sdk-runtime-fork-source")

    thread.start()
    assert started.wait(timeout=2.0)

    with pytest.raises(HephSdkBusyError, match="already streaming"):
        runtime.fork_session(session, "T1")

    release.set()
    thread.join(timeout=2.0)

    assert stream_errors == []
    assert not thread.is_alive()
    assert not session.is_streaming

    session.dispose()
    with pytest.raises(HephSdkError, match="disposed"):
        runtime.fork_session(session, "T1")


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
    assert service_state["is_busy"] is False
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
    assert empty_snapshot.service.is_busy is False
    assert snapshot.service.prompt_active is False
    assert snapshot.service.active_operation is None
    assert snapshot.service.is_busy is False
    assert snapshot.runtime.armory_path == armory_path.resolve()
    assert snapshot.runtime.provider_slug == ""
    assert snapshot.runtime.model == "typed-state-model"
    assert snapshot.runtime.temperature is None
    assert snapshot.runtime.reasoning_level == "low"
    assert snapshot.runtime.feature_flags == ("alpha", "beta")
    assert isinstance(snapshot.session, HephSdkSessionState)
    assert snapshot.session.provider_slug == ""
    assert snapshot.session.source_file_count == 1
    assert snapshot.session.source_files == ("materials/notes.md",)
    assert snapshot.session.enabled_source_files == ("materials/notes.md",)
    assert snapshot.session.disabled_source_files == frozenset()
    assert not snapshot.session.has_unsaved_changes
    assert snapshot.session.messages == ()
    assert session_payload["runtime"] == snapshot.runtime.to_dict()
    assert service.state() == snapshot.to_dict()


def test_service_state_constructor_derives_busy_flag() -> None:
    assert HephSdkServiceState(False).is_busy is False
    assert HephSdkServiceState(True).is_busy is True
    assert HephSdkServiceState(False, "build_index").is_busy is True


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
    assert runtime_state.provider_slug == ""
    assert runtime_state.to_dict()["provider_slug"] == ""
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
        "provider_slug": "",
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


def test_sdk_provider_summaries_are_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _pollinations_config(monkeypatch)
    monkeypatch.delenv("HEPHAION_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setattr(
        sdk_providers,
        "retrieve_key",
        lambda slug: "keychain-key" if slug == "openrouter" else None,
    )
    monkeypatch.setattr(
        sdk_providers,
        "get_volatile",
        lambda slug: "session-key" if slug == "zai" else None,
    )
    monkeypatch.setattr(sdk_providers.oauth, "list_providers", lambda: ["openai-codex"])
    service = HephService.plain(config=config)

    provider_summaries = service.runtime.list_providers()
    assert provider_summaries
    pollinations = next(
        provider for provider in provider_summaries if provider.provider_slug == "pollinations"
    )
    assert isinstance(pollinations, ProviderSummary)
    assert pollinations.display_name == "Pollinations AI (free)"
    assert pollinations.current_model == "openai"
    assert pollinations.model_count == 2
    assert pollinations.is_active is True
    assert pollinations.is_current is True
    assert pollinations.credential_kind == "keyless"
    assert pollinations.credential_source == "keyless"
    assert pollinations.credential_required is False
    assert pollinations.credential_configured is True

    payload = service.call("list_providers")
    providers = _payloads_by_slug(payload["providers"])
    assert providers["openai"]["credential_kind"] == "api_key"
    assert providers["openai"]["credential_source"] == "provider_env"
    assert providers["openai"]["credential_configured"] is True
    assert providers["openai"]["api_key_env"] == "OPENAI_API_KEY"
    assert providers["openrouter"]["credential_source"] == "keychain"
    assert providers["zai"]["credential_source"] == "session"
    assert providers["openai-codex"]["credential_kind"] == "oauth"
    assert providers["openai-codex"]["credential_source"] == "oauth"
    assert providers["deepseek"]["credential_source"] == "missing"
    assert providers["deepseek"]["credential_configured"] is False

    monkeypatch.setenv("HEPHAION_API_KEY", "global-key")
    global_payload = service.call("list_providers")
    global_providers = _payloads_by_slug(global_payload["providers"])
    assert global_providers["deepseek"]["credential_source"] == "global_env"
    assert global_providers["pollinations"]["credential_source"] == "keyless"

    service.new_session()
    session_payload = service.call("list_providers")
    session_providers = _payload_list(session_payload["providers"])
    assert any(
        _payload_mapping(provider)["is_current"] is True
        and _payload_mapping(provider)["provider_slug"] == "pollinations"
        for provider in session_providers
    )


def test_sdk_model_choices_and_switching_are_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = HephService.plain(config=_pollinations_config(monkeypatch))

    runtime_choices = service.runtime.list_model_choices()
    assert runtime_choices
    current_choice = next(
        choice
        for choice in runtime_choices
        if choice.provider_slug == "pollinations" and choice.model == "openai"
    )
    assert isinstance(current_choice, ModelChoiceSummary)
    assert current_choice.provider_display_name == "Pollinations AI (free)"
    assert current_choice.endpoint == "https://text.pollinations.ai/openai"
    assert current_choice.is_free is True
    assert current_choice.is_current is True
    assert current_choice.free_description == "free, no API key"

    service_choices = _payload_list(service.call("list_model_choices")["models"])
    service_choice = next(
        choice_payload
        for choice in service_choices
        if (choice_payload := _payload_mapping(choice))["provider_slug"] == "pollinations"
        and choice_payload["model"] == "openai"
    )
    assert service_choice["is_current"] is True
    assert service_choice["free_description"] == "free, no API key"

    switch_payload = service.call(
        "switch_model",
        {"provider_slug": "pollinations", "model": "openai-fast"},
    )
    runtime_payload = _payload_mapping(switch_payload["runtime"])
    assert switch_payload["changed"] is True
    assert runtime_payload["provider_slug"] == "pollinations"
    assert runtime_payload["model"] == "openai-fast"
    assert switch_payload["session"] is None

    missing_payload = service.call(
        "switch_model",
        {"provider_slug": "pollinations", "model": "missing-model"},
    )
    missing_runtime = _payload_mapping(missing_payload["runtime"])
    assert missing_payload["changed"] is False
    assert missing_runtime["model"] == "openai-fast"

    service.new_session()
    session_switch = service.call(
        "switch_model",
        {"provider_slug": "pollinations", "model": "openai"},
    )
    session_payload = _payload_mapping(session_switch["session"])
    session_runtime = _payload_mapping(session_switch["runtime"])
    assert session_switch["changed"] is True
    assert session_payload["provider_slug"] == "pollinations"
    assert session_payload["model"] == "openai"
    assert session_runtime["model"] == "openai"
    assert service.session is not None
    assert any(
        choice.is_current
        for choice in service.session.list_model_choices()
        if choice.provider_slug == "pollinations" and choice.model == "openai"
    )


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
    assert active_state["is_busy"] is True
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
        service.validate_armory(tmp_path)
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.list_providers()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.list_model_choices()
    with pytest.raises(HephSdkError, match="only state, abort, and capabilities"):
        service.switch_model("pollinations", "openai")
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
    assert idle_state["is_busy"] is False
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
    assert active_state.service.is_busy
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
    assert not service.state_snapshot().service.is_busy


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
    assert active_service["is_busy"] is True
    active_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    active_capability_service = _payload_mapping(active_capabilities["service"])
    assert "build_index" in _payload_list(active_capability_service["stream_methods"])
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.new_session()
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        list(service.prompt("Prompt during index."))
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        list(session.prompt("Direct prompt during index."))
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.list_providers()
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.list_model_choices()
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.switch_model("pollinations", "openai")
    with pytest.raises(HephSdkBusyError, match="only state, abort, and capabilities"):
        service.validate_armory(tmp_path)
    abort_payload = service.call("abort")
    abort_result = _payload_mapping(abort_payload)
    abort_service = _payload_mapping(_payload_mapping(abort_result["state"])["service"])
    assert abort_result["aborted"] is False
    assert abort_service["active_operation"] == "build_index"
    assert abort_service["is_busy"] is True

    release.set()
    assert finished.wait(timeout=2.0)
    finished_but_unconsumed_service = _payload_mapping(service.state()["service"])
    assert finished_but_unconsumed_service["active_operation"] == "build_index"
    assert finished_but_unconsumed_service["is_busy"] is True
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
    assert idle_service["is_busy"] is False


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
    assert active_service["is_busy"] is True

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
    assert idle_service["is_busy"] is False


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
    validation_payload = service.call("validate_armory", {"path": str(armory)})
    events = list(service.stream("prompt", {"text": "Dispatch this."}))
    ask = service.call("ask", {"text": "Return final text."})

    runtime_payload = _payload_mapping(config_payload["runtime"])
    zero_runtime_payload = _payload_mapping(zero_config_payload["runtime"])
    default_reasoning_runtime = _payload_mapping(default_reasoning_payload["runtime"])
    capabilities = _payload_mapping(capabilities_payload["capabilities"])
    capability_service = _payload_mapping(capabilities["service"])
    validated_armory = _payload_mapping(validation_payload["armory"])
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
    assert validated_armory["valid"] is True
    assert validated_armory["path"] == str(armory.resolve())
    assert events[0] == {"type": "assistant_delta", "delta": "Dispatched."}
    assert _payload_mapping(ask)["text"] == "Dispatched."

    with pytest.raises(HephSdkError, match="Unknown SDK service method"):
        service.call("missing")
    with pytest.raises(HephSdkError, match="non-empty string"):
        list(service.stream("prompt", {"text": ""}))
    with pytest.raises(HephSdkError, match="must be a boolean"):
        service.call("set_source_enabled", {"source": "materials/notes.md", "enabled": "no"})
    with pytest.raises(HephSdkError, match="must be a boolean"):
        service.call("list_model_choices", {"refresh_live": "yes"})


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
