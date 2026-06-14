from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import get_type_hints

import pytest
from ai.providers.config import default_config
from ai.providers.reasoning import REASONING_LEVELS
from ai.runtime import ChatConfig, EngineError, EngineErrorCode
from ai.runtime.thinking import THINKING_VISIBILITY_MODES
from heph.sdk import (
    JSONL_ERROR_CODES,
    JSONL_MESSAGE_SPECS,
    JSONL_MESSAGE_TYPES,
    JSONL_REQUEST_SPEC,
    SDK_CAPABILITIES,
    SDK_MUTABLE_APP_SETTINGS,
    ArmoryValidationSummary,
    AssistantDelta,
    CompactRequest,
    Guardrail,
    HephMessage,
    HephRuntime,
    HephSdkBusyError,
    HephSdkCapabilities,
    HephSdkError,
    HephSdkModelError,
    HephSdkOptions,
    HephSdkRuntimeState,
    HephSdkServiceState,
    HephSdkSessionState,
    HephSdkState,
    HephSdkUnavailableError,
    HephService,
    HephSession,
    ImportMaterialsSummary,
    IndexSummary,
    MaterialOperation,
    ModelChoiceSummary,
    Notice,
    ProviderSummary,
    ReasoningDelta,
    SdkAppSettings,
    SdkSettingsError,
    SettingChoice,
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
    load_sdk_app_settings,
    update_sdk_app_settings,
    validate_sdk_capabilities,
)
from heph.sdk import methods as sdk_methods
from heph.sdk import models as sdk_models
from heph.sdk import providers as sdk_providers
from heph.sdk import runtime as sdk_runtime
from heph.sdk.method_validation import validate_method_params
from hephaion.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    GuardrailEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ReasoningDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from hephaion.chat.session import ChatSession
from hephaion.parameters.settings import (
    ACTIVITY_TRACE_MODES,
    THEME_PRESETS,
    VOCAB_STRICTNESS_MODES,
)
from hephaion.rag.health import ExtractionHealthIssue, ExtractionHealthReport

from hephaion.parameters import settings as settings_store


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


def _service_call_methods(*methods: str) -> tuple[str, ...]:
    available = set(methods)
    return tuple(method for method in sdk_methods.SERVICE_CALL_METHODS if method in available)


def _service_stream_methods(*methods: str) -> tuple[str, ...]:
    available = set(methods)
    return tuple(method for method in sdk_methods.SERVICE_STREAM_METHODS if method in available)


def _isolate_settings_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_dir = tmp_path / ".config" / "hephaion"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)
    return config_file


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

    compact = from_turn_event(CompactRequestEvent("compact-1", "compact", {"ratio": 0.5}))
    assert isinstance(compact, CompactRequest)
    assert event_to_dict(compact) == {
        "type": "compact_request",
        "call_id": "compact-1",
        "name": "compact",
        "arguments": {"ratio": 0.5},
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

    guardrail = from_turn_event(
        GuardrailEvent("input", "block", "Blocked locally.", {"reason": "policy"})
    )
    assert isinstance(guardrail, Guardrail)
    assert event_to_dict(guardrail) == {
        "type": "guardrail",
        "stage": "input",
        "action": "block",
        "message": "Blocked locally.",
        "metadata": {"reason": "policy"},
    }


def test_sdk_object_field_spec_keeps_compatible_aliases() -> None:
    assert sdk_methods.SdkEventFieldSpec is sdk_methods.SdkObjectFieldSpec
    assert sdk_methods.SdkTypeFieldSpec is sdk_methods.SdkObjectFieldSpec
    assert sdk_methods.SdkResultFieldSpec is sdk_methods.SdkObjectFieldSpec
    assert sdk_methods.SdkJsonlMessageFieldSpec is sdk_methods.SdkObjectFieldSpec

    field = sdk_methods.SdkEventFieldSpec("metadata", "object", required=False)

    assert field.to_dict() == {
        "type": "object",
        "required": False,
        "nullable": False,
    }


def test_sdk_method_validation_accepts_advertised_value_types() -> None:
    specs = (
        sdk_methods.SdkMethodSpec(
            "check",
            (
                sdk_methods.SdkMethodParameter("name", "string", True),
                sdk_methods.SdkMethodParameter("enabled", "boolean", True),
                sdk_methods.SdkMethodParameter("count", "integer", True),
                sdk_methods.SdkMethodParameter("ratio", "number", True),
                sdk_methods.SdkMethodParameter("maybe", "number_or_null", True),
                sdk_methods.SdkMethodParameter("identity", "string_or_integer", True),
                sdk_methods.SdkMethodParameter("payload", "object", True),
                sdk_methods.SdkMethodParameter("items", "array<string>", True),
                sdk_methods.SdkMethodParameter("status", "literal<ready>", True),
            ),
        ),
    )
    params: dict[str, object] = {
        "name": "heph",
        "enabled": True,
        "count": 3,
        "ratio": 0.5,
        "maybe": None,
        "identity": 7,
        "payload": {"ok": True},
        "items": ["a", "b"],
        "status": "ready",
    }

    assert validate_method_params("check", params, specs) == params


def test_sdk_service_call_routes_match_advertised_methods() -> None:
    service = HephService.plain(config=_config())

    assert tuple(service._call_routes()) == sdk_methods.SERVICE_CALL_METHODS


def test_sdk_service_stream_routes_match_advertised_methods() -> None:
    service = HephService.plain(config=_config())

    assert tuple(service._stream_routes()) == sdk_methods.SERVICE_STREAM_METHODS


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("name", 7, "a string"),
        ("enabled", "yes", "a boolean"),
        ("count", True, "an integer"),
        ("ratio", False, "a number"),
        ("maybe", "1", "a number or null"),
        ("identity", False, "a string or integer"),
        ("payload", [], "an object"),
        ("items", "not an array", "an array"),
        ("items", [1], "an array"),
        ("status", "waiting", "literal value 'ready'"),
    ],
)
def test_sdk_method_validation_rejects_advertised_value_type_mismatch(
    name: str,
    value: object,
    message: str,
) -> None:
    specs = (
        sdk_methods.SdkMethodSpec(
            "check",
            (
                sdk_methods.SdkMethodParameter("name", "string", False),
                sdk_methods.SdkMethodParameter("enabled", "boolean", False),
                sdk_methods.SdkMethodParameter("count", "integer", False),
                sdk_methods.SdkMethodParameter("ratio", "number", False),
                sdk_methods.SdkMethodParameter("maybe", "number_or_null", False),
                sdk_methods.SdkMethodParameter("identity", "string_or_integer", False),
                sdk_methods.SdkMethodParameter("payload", "object", False),
                sdk_methods.SdkMethodParameter("items", "array<string>", False),
                sdk_methods.SdkMethodParameter("status", "literal<ready>", False),
            ),
        ),
    )

    with pytest.raises(HephSdkError, match=message):
        validate_method_params("check", {name: value}, specs)


def test_sdk_app_settings_snapshot_and_update_are_structured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_file = _isolate_settings_store(tmp_path, monkeypatch)
    monkeypatch.delenv("HEPHAION_ANALYTICS_ENABLED", raising=False)
    monkeypatch.delenv("HEPHAION_CRASH_REPORTS_ENABLED", raising=False)
    settings_store.save_setting("theme", "light")

    settings = load_sdk_app_settings()
    payload = settings.to_dict()
    choices = _payload_mapping(payload["choices"])
    theme_choices = [_payload_mapping(choice) for choice in _payload_list(choices["themes"])]
    privacy = _payload_mapping(payload["privacy"])
    mutable_keys = _payload_list(payload["mutable_keys"])

    assert isinstance(settings, SdkAppSettings)
    assert settings.theme == "light"
    assert settings.choices.themes[0] == SettingChoice("dark", "Dark")
    assert mutable_keys == list(SDK_MUTABLE_APP_SETTINGS)
    assert "analytics_enabled" not in mutable_keys
    assert theme_choices == [
        {"value": "dark", "label": "Dark"},
        {"value": "light", "label": "Light"},
    ]
    assert privacy["analytics_env_override"] is False
    assert privacy["crash_reports_env_override"] is False

    default_armory = tmp_path / "default-armory"
    updated = update_sdk_app_settings(
        {
            "theme": "dark",
            "default_armory_path": str(default_armory),
            "activity_trace_mode": "hidden_tool_calls",
            "vocab_strictness": "lenient",
            "thinking_visibility": "all",
            "live_tokens_visible": True,
            "live_cost_visible": True,
        }
    )
    stored = settings_store.load_app_settings()

    assert config_file.is_file()
    assert updated.theme == "dark"
    assert updated.default_armory_path == str(default_armory.resolve())
    assert stored.activity_trace_mode == "hidden_tool_calls"
    assert stored.vocab_strictness == "lenient"
    assert stored.thinking_visibility == "all"
    assert stored.live_tokens_visible is True
    assert stored.live_cost_visible is True


def test_sdk_app_settings_update_rejects_unsupported_or_invalid_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_settings_store(tmp_path, monkeypatch)
    settings_store.save_setting("theme", "light")

    with pytest.raises(SdkSettingsError, match="Unsupported SDK app setting: analytics_enabled"):
        update_sdk_app_settings({"analytics_enabled": True})
    with pytest.raises(SdkSettingsError, match="Invalid SDK app setting 'theme'"):
        update_sdk_app_settings({"theme": "solarized", "live_tokens_visible": True})
    with pytest.raises(SdkSettingsError, match="'live_tokens_visible' must be a boolean"):
        update_sdk_app_settings({"live_tokens_visible": "maybe"})
    with pytest.raises(SdkSettingsError, match="'default_armory_path' must be a string"):
        update_sdk_app_settings({"default_armory_path": None})

    stored = settings_store.load_app_settings()
    assert stored.theme == "light"
    assert stored.live_tokens_visible is False
    assert stored.default_armory_path == ""


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
    streams = _payload_mapping(payload["streams"])
    fields = _payload_mapping(payload["fields"])
    types = _payload_mapping(payload["types"])
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
    service_stream_contracts = _payload_mapping(streams["service"])
    jsonl_stream_contracts = _payload_mapping(streams["jsonl"])
    jsonl_error_specs = _payload_mapping(errors["jsonl"])
    jsonl_request_spec = _payload_mapping(jsonl["request_spec"])
    jsonl_message_types = _payload_list(jsonl["message_types"])
    jsonl_message_specs = _payload_mapping(jsonl["message_specs"])
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
    assert validate_sdk_capabilities(capabilities) == ()
    assert payload["version"] == sdk_methods.SDK_CAPABILITIES_VERSION
    assert "sdk_capabilities" in types
    assert "sdk_state" in types
    assert "provider_summary" in types
    assert "model_choice_summary" in types
    assert "setting_choice" in types
    assert "sdk_settings_choices" in types
    assert "sdk_privacy_settings" in types
    assert "sdk_app_settings" in types
    assert "index_summary" in types
    assert "extraction_health_summary" in types
    assert "jsonl_error" in types
    assert "sdk_event" in types
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
    assert list(service_stream_contracts) == service_stream_methods
    assert list(jsonl_stream_contracts) == jsonl_stream_methods
    assert "capabilities" in service_call_methods
    assert "validate_armory" in service_call_methods
    assert "list_providers" in service_call_methods
    assert "list_model_choices" in service_call_methods
    assert "switch_model" in service_call_methods
    assert "settings" in service_call_methods
    assert "update_settings" in service_call_methods
    assert "settings" in busy_allowed_call_methods
    assert "build_index" in service_stream_methods
    assert jsonl["protocol"] == "heph-sdk-jsonl"
    assert "build_index_stream" in jsonl_stream_methods
    assert sdk_methods.service_stream_method_for_jsonl("build_index_stream") == "build_index"
    assert sdk_methods.service_stream_method_for_jsonl("prompt") is None
    assert sdk_methods.service_stream_method_for_jsonl("unknown") is None
    assert sdk_methods.jsonl_stream_method_for_service("build_index") == "build_index_stream"
    assert sdk_methods.jsonl_stream_method_for_service("prompt") == "prompt"
    assert sdk_methods.jsonl_stream_method_for_service("unknown") is None
    request_fields = _payload_mapping(jsonl_request_spec["fields"])
    assert list(request_fields) == [field.name for field in JSONL_REQUEST_SPEC.fields]
    assert _payload_mapping(request_fields["id"]) == {
        "type": "string_or_integer",
        "required": False,
        "nullable": True,
    }
    assert _payload_mapping(request_fields["method"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(request_fields["params"]) == {
        "type": "object",
        "required": False,
        "nullable": True,
    }
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
    update_config_params_by_name = {str(param["name"]): param for param in update_config_params}
    update_settings_spec = _payload_mapping(service_call_specs["update_settings"])
    update_settings_params = [
        _payload_mapping(param) for param in _payload_list(update_settings_spec["params"])
    ]
    update_settings_params_by_name = {
        str(param["name"]): param for param in update_settings_params
    }
    assert open_armory_params == [{"name": "path", "type": "string", "required": True}]
    assert switch_model_params == [
        {"name": "provider_slug", "type": "string", "required": True},
        {"name": "model", "type": "string", "required": True},
    ]
    assert prompt_params == [{"name": "text", "type": "string", "required": True}]
    assert {"name": "temperature", "type": "number_or_null", "required": False} in (
        update_config_params
    )
    assert update_config_params_by_name["reasoning_level"] == {
        "name": "reasoning_level",
        "type": "string",
        "required": False,
        "choices": list(REASONING_LEVELS),
    }
    assert update_config_params_by_name["thinking_visibility"] == {
        "name": "thinking_visibility",
        "type": "string",
        "required": False,
        "choices": list(THINKING_VISIBILITY_MODES),
    }
    assert update_settings_params_by_name["theme"] == {
        "name": "theme",
        "type": "string",
        "required": False,
        "choices": list(THEME_PRESETS),
    }
    assert update_settings_params_by_name["thinking_visibility"] == {
        "name": "thinking_visibility",
        "type": "string",
        "required": False,
        "choices": list(THINKING_VISIBILITY_MODES),
    }
    assert update_settings_params_by_name["activity_trace_mode"] == {
        "name": "activity_trace_mode",
        "type": "string",
        "required": False,
        "choices": list(ACTIVITY_TRACE_MODES),
    }
    assert update_settings_params_by_name["vocab_strictness"] == {
        "name": "vocab_strictness",
        "type": "string",
        "required": False,
        "choices": list(VOCAB_STRICTNESS_MODES),
    }
    assert {"name": "live_tokens_visible", "type": "boolean", "required": False} in (
        update_settings_params
    )
    service_prompt_stream = _payload_mapping(service_stream_contracts["prompt"])
    service_index_stream = _payload_mapping(service_stream_contracts["build_index"])
    jsonl_prompt_stream = _payload_mapping(jsonl_stream_contracts["prompt"])
    jsonl_index_stream = _payload_mapping(jsonl_stream_contracts["build_index_stream"])
    assert _payload_list(service_prompt_stream["event_types"]) == list(
        sdk_methods.TURN_STREAM_EVENT_TYPES
    )
    assert service_prompt_stream["completion_event"] == "turn_complete"
    assert _payload_list(service_index_stream["event_types"]) == list(
        sdk_methods.INDEX_STREAM_EVENT_TYPES
    )
    assert service_index_stream["completion_event"] == "index_complete"
    assert _payload_list(jsonl_prompt_stream["event_types"]) == list(
        sdk_methods.TURN_STREAM_EVENT_TYPES
    )
    assert jsonl_prompt_stream["completion_event"] == "turn_complete"
    assert _payload_list(jsonl_index_stream["event_types"]) == list(
        sdk_methods.INDEX_STREAM_EVENT_TYPES
    )
    assert jsonl_index_stream["completion_event"] == "index_complete"
    state_result = _payload_mapping(service_call_results["state"])
    capabilities_result = _payload_mapping(service_call_results["capabilities"])
    capabilities_result_fields = _payload_mapping(capabilities_result["fields"])
    list_providers_result = _payload_mapping(service_call_results["list_providers"])
    list_providers_result_fields = _payload_mapping(list_providers_result["fields"])
    switch_model_result = _payload_mapping(service_call_results["switch_model"])
    switch_model_result_fields = _payload_mapping(switch_model_result["fields"])
    settings_result = _payload_mapping(service_call_results["settings"])
    settings_result_fields = _payload_mapping(settings_result["fields"])
    update_settings_result = _payload_mapping(service_call_results["update_settings"])
    update_settings_result_fields = _payload_mapping(update_settings_result["fields"])
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
    assert _payload_mapping(settings_result_fields["settings"]) == {
        "type": "sdk_app_settings",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(update_settings_result_fields["settings"]) == {
        "type": "sdk_app_settings",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(update_settings_result_fields["session"]) == {
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
    assert jsonl_message_types == [spec.message_type for spec in JSONL_MESSAGE_SPECS]
    assert list(jsonl_message_specs) == jsonl_message_types
    ready_message_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["ready"])["fields"]
    )
    response_message_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["response"])["fields"]
    )
    error_message_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["error"])["fields"]
    )
    stream_start_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["stream_start"])["fields"]
    )
    stream_event_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["stream_event"])["fields"]
    )
    stream_end_fields = _payload_mapping(
        _payload_mapping(jsonl_message_specs["stream_end"])["fields"]
    )
    assert _payload_mapping(ready_message_fields["type"]) == {
        "type": "literal<ready>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(ready_message_fields["capabilities"]) == {
        "type": "sdk_capabilities",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(ready_message_fields["state"]) == {
        "type": "sdk_state",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(response_message_fields["id"]) == {
        "type": "string_or_integer",
        "required": True,
        "nullable": True,
    }
    assert _payload_mapping(response_message_fields["result"]) == {
        "type": "object",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(error_message_fields["error"]) == {
        "type": "jsonl_error",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(stream_start_fields["method"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(stream_event_fields["event"]) == {
        "type": "sdk_event",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(stream_end_fields["error"]) == {
        "type": "jsonl_error",
        "required": False,
        "nullable": False,
    }
    assert jsonl_error_codes == list(JSONL_ERROR_CODES)
    assert list(jsonl_error_specs) == jsonl_error_codes
    busy_error_spec = _payload_mapping(jsonl_error_specs["busy"])
    unavailable_error_spec = _payload_mapping(jsonl_error_specs["unavailable"])
    engine_error_spec = _payload_mapping(jsonl_error_specs[sdk_methods.SDK_ENGINE_ERROR_CODE])
    missing_credentials_error_spec = _payload_mapping(
        jsonl_error_specs[EngineErrorCode.MISSING_CREDENTIALS.value]
    )
    internal_error_spec = _payload_mapping(jsonl_error_specs["internal_error"])
    assert "stream was active" in str(busy_error_spec["description"])
    assert "not available" in str(unavailable_error_spec["description"])
    assert "model runtime" in str(engine_error_spec["description"])
    assert "credentials" in str(missing_credentials_error_spec["description"])
    assert "unexpected server-side exception" in str(internal_error_spec["description"])
    assert all(error_code.value in jsonl_error_codes for error_code in EngineErrorCode)
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
    assert "available_call_methods" in service_fields
    assert "available_stream_methods" in service_fields
    assert "provider_slug" in runtime_fields
    assert "reasoning_level" in runtime_fields
    assert "provider_slug" in session_fields
    assert "enabled_source_files" in session_fields
    assert "is_disposed" in session_fields
    assert list(service_field_specs) == service_fields
    assert list(runtime_field_specs) == runtime_fields
    assert list(session_field_specs) == session_fields
    sdk_state_fields = _payload_mapping(_payload_mapping(types["sdk_state"])["fields"])
    sdk_capabilities_fields = _payload_mapping(
        _payload_mapping(types["sdk_capabilities"])["fields"]
    )
    runtime_type_fields = _payload_mapping(_payload_mapping(types["sdk_runtime_state"])["fields"])
    session_type_fields = _payload_mapping(_payload_mapping(types["sdk_session_state"])["fields"])
    message_type_fields = _payload_mapping(_payload_mapping(types["message"])["fields"])
    setting_choice_type_fields = _payload_mapping(
        _payload_mapping(types["setting_choice"])["fields"]
    )
    settings_choices_type_fields = _payload_mapping(
        _payload_mapping(types["sdk_settings_choices"])["fields"]
    )
    privacy_type_fields = _payload_mapping(
        _payload_mapping(types["sdk_privacy_settings"])["fields"]
    )
    settings_type_fields = _payload_mapping(_payload_mapping(types["sdk_app_settings"])["fields"])
    provider_type_fields = _payload_mapping(_payload_mapping(types["provider_summary"])["fields"])
    model_type_fields = _payload_mapping(_payload_mapping(types["model_choice_summary"])["fields"])
    material_type_fields = _payload_mapping(_payload_mapping(types["material_summary"])["fields"])
    index_type_fields = _payload_mapping(_payload_mapping(types["index_summary"])["fields"])
    health_type_fields = _payload_mapping(
        _payload_mapping(types["extraction_health_summary"])["fields"]
    )
    jsonl_error_type_fields = _payload_mapping(_payload_mapping(types["jsonl_error"])["fields"])
    sdk_event_type_fields = _payload_mapping(_payload_mapping(types["sdk_event"])["fields"])
    assert _payload_mapping(sdk_state_fields["session"]) == {
        "type": "sdk_session_state",
        "required": True,
        "nullable": True,
    }
    assert _payload_mapping(sdk_capabilities_fields["streams"]) == {
        "type": "object",
        "required": True,
        "nullable": False,
    }
    assert list(runtime_type_fields) == runtime_fields
    assert list(session_type_fields) == session_fields
    assert _payload_mapping(session_type_fields["messages"]) == {
        "type": "array<message>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(message_type_fields["content"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(setting_choice_type_fields["label"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(settings_choices_type_fields["themes"]) == {
        "type": "array<setting_choice>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(privacy_type_fields["analytics_enabled"]) == {
        "type": "boolean",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(settings_type_fields["privacy"]) == {
        "type": "sdk_privacy_settings",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(settings_type_fields["choices"]) == {
        "type": "sdk_settings_choices",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(settings_type_fields["mutable_keys"]) == {
        "type": "array<string>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(provider_type_fields["credential_configured"]) == {
        "type": "boolean",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(model_type_fields["free_description"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(material_type_fields["kind"]) == {
        "type": "literal<materials>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(index_type_fields["progress"]) == {
        "type": "array<index_progress_event>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(health_type_fields["issues"]) == {
        "type": "array<extraction_health_issue_summary>",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(jsonl_error_type_fields["code"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    assert _payload_mapping(sdk_event_type_fields["type"]) == {
        "type": "string",
        "required": True,
        "nullable": False,
    }
    service_operation_spec = _payload_mapping(service_field_specs["active_operation"])
    service_available_methods_spec = _payload_mapping(
        service_field_specs["available_call_methods"]
    )
    service_available_stream_methods_spec = _payload_mapping(
        service_field_specs["available_stream_methods"]
    )
    runtime_armory_spec = _payload_mapping(runtime_field_specs["armory_path"])
    runtime_flags_spec = _payload_mapping(runtime_field_specs["feature_flags"])
    session_messages_spec = _payload_mapping(session_field_specs["messages"])
    assert service_operation_spec == {"type": "string", "nullable": True}
    assert service_available_methods_spec == {"type": "array<string>", "nullable": False}
    assert service_available_stream_methods_spec == {
        "type": "array<string>",
        "nullable": False,
    }
    assert runtime_armory_spec == {"type": "string", "nullable": True}
    assert runtime_flags_spec == {"type": "array<string>", "nullable": False}
    assert session_messages_spec == {"type": "array<message>", "nullable": False}


def test_sdk_capabilities_validator_reports_contract_drift() -> None:
    capabilities = get_sdk_capabilities()
    broken_result_specs = tuple(
        replace(spec, value_type="array<array<missing_custom_type>>")
        if spec.method == "state"
        else spec
        for spec in capabilities.service_call_result_specs
    )
    broken_message_specs = tuple(
        replace(
            spec,
            fields=(
                *(
                    replace(field, value_type="missing_jsonl_message_type")
                    if spec.message_type == "stream_event" and field.name == "event"
                    else field
                    for field in spec.fields
                ),
                spec.fields[0],
            )
            if spec.message_type == "stream_event"
            else spec.fields,
        )
        for spec in capabilities.jsonl_message_specs
    )
    broken_request_fields = tuple(
        replace(field, value_type="missing_jsonl_request_type")
        if field.name == "params"
        else field
        for field in capabilities.jsonl_request_spec.fields
    )
    broken_service_call_method_specs = tuple(
        replace(
            spec,
            params=(
                *(
                    replace(param, choices=(*param.choices, param.choices[0]))
                    if spec.method == "update_settings" and param.name == "theme"
                    else param
                    for param in spec.params
                ),
                spec.params[0],
            )
            if spec.method == "update_settings"
            else spec.params,
        )
        if spec.method == "update_settings"
        else spec
        for spec in capabilities.service_call_method_specs
    )
    broken_service_call_result_specs = tuple(
        replace(spec, fields=(*spec.fields, spec.fields[0])) if spec.method == "abort" else spec
        for spec in capabilities.service_call_result_specs
    )
    broken_type_specs = tuple(
        replace(spec, fields=(*spec.fields, spec.fields[0]))
        if spec.type_name == "sdk_state"
        else spec
        for spec in capabilities.type_specs
    )
    broken_service_stream_specs = tuple(
        replace(
            spec,
            event_types=(
                *spec.event_types,
                spec.event_types[0],
                "missing_stream_event",
            ),
            completion_event="missing_completion_event",
        )
        if spec.method == "prompt"
        else spec
        for spec in capabilities.service_stream_specs
    )
    broken_jsonl_stream_specs = tuple(
        spec for spec in capabilities.jsonl_stream_specs if spec.method != "build_index_stream"
    )
    broken_capabilities = replace(
        capabilities,
        busy_allowed_call_methods=(*capabilities.busy_allowed_call_methods, "bogus"),
        service_call_methods=(*capabilities.service_call_methods, "state"),
        service_call_method_specs=broken_service_call_method_specs,
        service_call_result_specs=broken_service_call_result_specs,
        jsonl_request_spec=replace(
            capabilities.jsonl_request_spec,
            fields=(*broken_request_fields, broken_request_fields[0]),
        ),
        jsonl_message_types=(*capabilities.jsonl_message_types, "bogus_message"),
        jsonl_message_specs=broken_message_specs,
        jsonl_call_result_specs=broken_result_specs,
        service_stream_specs=broken_service_stream_specs,
        jsonl_stream_specs=broken_jsonl_stream_specs,
        type_specs=broken_type_specs,
    )

    issues = validate_sdk_capabilities(broken_capabilities)

    assert "service.call_methods contains duplicate entries: state" in issues
    assert "service.call_methods does not match its structured specs." in issues
    assert (
        "service.busy_allowed_call_methods contains entries that are not advertised calls: bogus"
        in issues
    )
    assert "jsonl.request_spec.fields contains duplicate entries: id" in issues
    assert "jsonl.message_types does not match its structured specs." in issues
    assert "streams.jsonl does not match its structured specs." in issues
    assert (
        "methods.service_call.update_settings.params contains duplicate entries: theme" in issues
    )
    assert "jsonl.message_specs.stream_event.fields contains duplicate entries: type" in issues
    assert "results.service_call.abort.fields contains duplicate entries: aborted" in issues
    assert "types.sdk_state.fields contains duplicate entries: service" in issues
    assert (
        "methods.service_call.update_settings.theme.choices contains duplicate entries: dark"
        in (issues)
    )
    assert "results.jsonl_call.state references unknown SDK type: missing_custom_type" in issues
    assert (
        "jsonl.request_spec.params references unknown SDK type: missing_jsonl_request_type"
        in issues
    )
    assert (
        "jsonl.message_specs.stream_event.event references unknown SDK type: "
        "missing_jsonl_message_type" in issues
    )
    assert (
        "streams.service.prompt.event_types contains duplicate entries: assistant_delta" in issues
    )
    assert "streams.service.prompt references unknown SDK events: missing_stream_event" in issues
    assert "streams.service.prompt completion event is unknown: missing_completion_event" in issues


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


def test_session_prompt_wraps_engine_errors_with_sdk_code(
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
        _ = raw_session, abort
        assert prompt == "Needs a model."
        yield from ()
        raise EngineError("No API key found.", code=EngineErrorCode.MISSING_CREDENTIALS)

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    with pytest.raises(HephSdkModelError, match="No API key found") as exc_info:
        list(session.prompt("Needs a model."))

    assert exc_info.value.code == EngineErrorCode.MISSING_CREDENTIALS.value
    assert exc_info.value.engine_code == EngineErrorCode.MISSING_CREDENTIALS
    assert session.is_streaming is False


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


def test_service_state_available_methods_reflect_runtime_and_session(tmp_path: Path) -> None:
    base_methods = (
        "state",
        "capabilities",
        "use_plain_runtime",
        "open_armory",
        "create_armory",
        "list_armories",
        "validate_armory",
        "new_session",
        "list_sessions",
        "settings",
        "list_providers",
        "list_model_choices",
        "switch_model",
        "update_config",
        "update_settings",
    )
    session_methods = ("fork_session", "messages", "ask", "abort")
    armory_methods = (
        "resume_session",
        "list_materials",
        "import_materials",
        "build_index",
        "scan_extraction_health",
    )
    service = HephService.plain(config=_config())

    plain_service = _payload_mapping(service.state()["service"])
    service.new_session()
    plain_session_service = _payload_mapping(service.state()["service"])
    armory_service = HephService.open_armory(_armory(tmp_path), config=_config())
    armory_no_session_service = _payload_mapping(armory_service.state()["service"])
    armory_service.new_session()
    armory_session_service = _payload_mapping(armory_service.state()["service"])

    assert plain_service["available_call_methods"] == list(_service_call_methods(*base_methods))
    assert plain_service["available_stream_methods"] == []
    assert plain_session_service["available_call_methods"] == list(
        _service_call_methods(*base_methods, *session_methods)
    )
    assert plain_session_service["available_stream_methods"] == ["prompt"]
    assert armory_no_session_service["available_call_methods"] == list(
        _service_call_methods(*base_methods, *armory_methods)
    )
    assert armory_no_session_service["available_stream_methods"] == ["build_index"]
    assert armory_session_service["available_call_methods"] == list(
        sdk_methods.SERVICE_CALL_METHODS
    )
    assert armory_session_service["available_stream_methods"] == list(
        sdk_methods.SERVICE_STREAM_METHODS
    )


def test_service_rejects_unavailable_call_methods_before_dispatch(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())

    with pytest.raises(HephSdkUnavailableError, match=r"service call 'ask'.*not available"):
        service.call("ask", {"text": "hello"})
    with pytest.raises(HephSdkUnavailableError, match="service call 'list_materials'"):
        service.call("list_materials")
    with pytest.raises(HephSdkUnavailableError, match="service call 'abort'"):
        service.call("abort")

    service.new_session()

    with pytest.raises(HephSdkUnavailableError, match="service call 'save_session'"):
        service.call("save_session")
    with pytest.raises(HephSdkUnavailableError, match="service call 'set_source_enabled'"):
        service.call(
            "set_source_enabled",
            {"source": "materials/missing.md", "enabled": False},
        )
    assert _payload_mapping(service.call("messages"))["messages"] == []

    armory_service = HephService.open_armory(_armory(tmp_path), config=_config())

    with pytest.raises(HephSdkUnavailableError, match="service call 'ask'"):
        armory_service.call("ask", {"text": "hello"})
    assert "materials" in armory_service.call("list_materials")


def test_service_rejects_unavailable_stream_methods_before_start(tmp_path: Path) -> None:
    service = HephService.plain(config=_config())

    with pytest.raises(HephSdkUnavailableError, match="service stream 'prompt'"):
        list(service.stream("prompt", {"text": "hello"}))
    with pytest.raises(HephSdkUnavailableError, match="service stream 'build_index'"):
        list(service.stream("build_index"))
    with pytest.raises(HephSdkUnavailableError, match="service stream 'build_index'"):
        list(service.build_index_stream())
    assert _payload_mapping(service.state()["service"])["is_busy"] is False

    service.new_session()
    armory_service = HephService.open_armory(_armory(tmp_path), config=_config())

    with pytest.raises(HephSdkUnavailableError, match="service stream 'build_index'"):
        list(service.stream("build_index"))
    with pytest.raises(HephSdkUnavailableError, match="service stream 'prompt'"):
        list(armory_service.stream("prompt", {"text": "hello"}))


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
    assert service_state["available_call_methods"] == list(sdk_methods.SERVICE_CALL_METHODS)
    assert service_state["available_stream_methods"] == list(sdk_methods.SERVICE_STREAM_METHODS)
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
    assert empty_snapshot.service.available_call_methods == _service_call_methods(
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
    assert empty_snapshot.service.available_stream_methods == _service_stream_methods(
        "build_index"
    )
    assert snapshot.service.prompt_active is False
    assert snapshot.service.active_operation is None
    assert snapshot.service.is_busy is False
    assert snapshot.service.available_call_methods == sdk_methods.SERVICE_CALL_METHODS
    assert snapshot.service.available_stream_methods == sdk_methods.SERVICE_STREAM_METHODS
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
    assert HephSdkServiceState(False).available_call_methods == sdk_methods.SERVICE_CALL_METHODS
    assert HephSdkServiceState(False).available_stream_methods == (
        sdk_methods.SERVICE_STREAM_METHODS
    )
    assert HephSdkServiceState(True).available_call_methods == (
        sdk_methods.BUSY_ALLOWED_CALL_METHODS
    )
    assert HephSdkServiceState(True).available_stream_methods == ()
    assert (
        HephSdkServiceState(
            True,
            available_stream_methods=sdk_methods.SERVICE_STREAM_METHODS,
        ).available_stream_methods
        == ()
    )
    assert HephSdkServiceState(False, "build_index").available_call_methods == (
        sdk_methods.BUSY_ALLOWED_CALL_METHODS
    )
    assert HephSdkServiceState(False, "build_index").available_stream_methods == ()


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
    assert sdk_runtime.HephMessage is HephMessage
    assert sdk_runtime.HephSdkSessionState is HephSdkSessionState
    assert get_type_hints(HephSdkSessionState)["messages"] == tuple[HephMessage, ...]
    assert get_type_hints(HephSdkRuntimeState.from_runtime)["return"] is HephSdkRuntimeState
    assert get_type_hints(HephSdkSessionState.from_session)["return"] is HephSdkSessionState

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
        "thinking_visibility": "",
        "live_tokens_visible": False,
        "live_cost_visible": False,
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

    def fail_retrieve_key(slug: str) -> str | None:
        raise AssertionError(f"keychain should not be queried for {slug!r} with global env set")

    monkeypatch.setattr(sdk_providers, "retrieve_key", fail_retrieve_key)
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


def test_sdk_provider_credential_sources_ignore_empty_stored_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _pollinations_config(monkeypatch)
    monkeypatch.delenv("HEPHAION_API_KEY", raising=False)
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    monkeypatch.setattr(sdk_providers.oauth, "list_providers", lambda: ())
    monkeypatch.setattr(
        sdk_providers,
        "retrieve_key",
        lambda slug: "" if slug in {"openrouter", "zai"} else None,
    )
    monkeypatch.setattr(sdk_providers, "get_volatile", lambda slug: "" if slug == "zai" else None)
    service = HephService.plain(config=config)

    payload = service.call("list_providers")
    providers = _payloads_by_slug(payload["providers"])
    assert providers["openrouter"]["credential_source"] == "provider_env"
    assert providers["openrouter"]["credential_configured"] is True
    assert providers["zai"]["credential_source"] == "missing"
    assert providers["zai"]["credential_configured"] is False


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
    assert active_state["available_call_methods"] == list(sdk_methods.BUSY_ALLOWED_CALL_METHODS)
    assert active_state["available_stream_methods"] == []
    active_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    active_capability_service = _payload_mapping(active_capabilities["service"])
    active_settings = _payload_mapping(service.call("settings")["settings"])
    assert "capabilities" in _payload_list(active_capability_service["busy_allowed_call_methods"])
    assert "settings" in _payload_list(active_capability_service["busy_allowed_call_methods"])
    assert active_settings["theme"] in {"dark", "light"}
    source = tmp_path / "late-material.md"
    source.write_text("# Late\n\nShould not import during streaming.\n", encoding="utf-8")
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.call("new_session")
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.ask("Nested prompt.")
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.update_config({"model": "mutated-during-stream"})
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.import_materials(source)
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.build_index()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.save_session()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.messages()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.list_sessions()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.list_materials()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.scan_extraction_health()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.list_armories()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.validate_armory(tmp_path)
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.list_providers()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.list_model_choices()
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
        service.switch_model("pollinations", "openai")
    with pytest.raises(HephSdkError, match="only state, abort, capabilities, and settings"):
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
    assert idle_state["available_call_methods"] == list(sdk_methods.SERVICE_CALL_METHODS)
    assert idle_state["available_stream_methods"] == list(sdk_methods.SERVICE_STREAM_METHODS)
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
    assert active_state.service.available_call_methods == sdk_methods.BUSY_ALLOWED_CALL_METHODS
    assert active_state.service.available_stream_methods == ()
    assert active_state.session is not None
    assert active_state.session.is_streaming
    direct_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    direct_capability_service = _payload_mapping(direct_capabilities["service"])
    direct_settings = _payload_mapping(service.call("settings")["settings"])
    assert "capabilities" in _payload_list(direct_capability_service["busy_allowed_call_methods"])
    assert "settings" in _payload_list(direct_capability_service["busy_allowed_call_methods"])
    assert direct_settings["theme"] in {"dark", "light"}
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
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
    assert service.state_snapshot().service.available_call_methods == (
        sdk_methods.SERVICE_CALL_METHODS
    )
    assert service.state_snapshot().service.available_stream_methods == (
        sdk_methods.SERVICE_STREAM_METHODS
    )


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
    assert service.state_snapshot().service.available_call_methods == (
        sdk_methods.BUSY_ALLOWED_CALL_METHODS
    )
    assert service.state_snapshot().service.available_stream_methods == ()

    release.set()
    stream_thread.join(timeout=2.0)
    mutation_thread.join(timeout=2.0)

    assert stream_errors == []
    assert len(streamed_events) == 2
    assert not stream_thread.is_alive()
    assert not mutation_thread.is_alive()
    assert not service.state_snapshot().service.prompt_active
    assert service.state_snapshot().service.available_call_methods == (
        sdk_methods.SERVICE_CALL_METHODS
    )
    assert service.state_snapshot().service.available_stream_methods == (
        sdk_methods.SERVICE_STREAM_METHODS
    )


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
    assert service.state_snapshot().service.available_call_methods == (
        sdk_methods.SERVICE_CALL_METHODS
    )
    assert service.state_snapshot().service.available_stream_methods == (
        sdk_methods.SERVICE_STREAM_METHODS
    )
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
    assert active_service["available_call_methods"] == list(sdk_methods.BUSY_ALLOWED_CALL_METHODS)
    assert active_service["available_stream_methods"] == []
    active_capabilities = _payload_mapping(service.call("capabilities")["capabilities"])
    active_capability_service = _payload_mapping(active_capabilities["service"])
    active_settings = _payload_mapping(service.call("settings")["settings"])
    assert "build_index" in _payload_list(active_capability_service["stream_methods"])
    assert "settings" in _payload_list(active_capability_service["busy_allowed_call_methods"])
    assert active_settings["theme"] in {"dark", "light"}
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.new_session()
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        list(service.prompt("Prompt during index."))
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        list(session.prompt("Direct prompt during index."))
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.list_providers()
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.list_model_choices()
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.switch_model("pollinations", "openai")
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
        service.validate_armory(tmp_path)
    abort_payload = service.call("abort")
    abort_result = _payload_mapping(abort_payload)
    abort_service = _payload_mapping(_payload_mapping(abort_result["state"])["service"])
    assert abort_result["aborted"] is False
    assert abort_service["active_operation"] == "build_index"
    assert abort_service["is_busy"] is True
    assert abort_service["available_call_methods"] == list(sdk_methods.BUSY_ALLOWED_CALL_METHODS)
    assert abort_service["available_stream_methods"] == []

    release.set()
    assert finished.wait(timeout=2.0)
    finished_but_unconsumed_service = _payload_mapping(service.state()["service"])
    assert finished_but_unconsumed_service["active_operation"] == "build_index"
    assert finished_but_unconsumed_service["is_busy"] is True
    assert finished_but_unconsumed_service["available_call_methods"] == list(
        sdk_methods.BUSY_ALLOWED_CALL_METHODS
    )
    assert finished_but_unconsumed_service["available_stream_methods"] == []
    with pytest.raises(HephSdkBusyError, match="only state, abort, capabilities, and settings"):
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
    assert idle_service["available_call_methods"] == list(sdk_methods.SERVICE_CALL_METHODS)
    assert idle_service["available_stream_methods"] == list(sdk_methods.SERVICE_STREAM_METHODS)


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
    assert active_service["available_call_methods"] == list(sdk_methods.BUSY_ALLOWED_CALL_METHODS)
    assert active_service["available_stream_methods"] == []

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
    assert idle_service["available_call_methods"] == list(
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
    )
    assert idle_service["available_stream_methods"] == ["build_index"]


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


def test_service_settings_methods_return_and_apply_display_preferences(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_settings_store(tmp_path, monkeypatch)
    service = HephService.plain(config=_config())
    service.new_session()

    settings_payload = _payload_mapping(service.call("settings")["settings"])
    choices_payload = _payload_mapping(settings_payload["choices"])
    updated_payload = service.call(
        "update_settings",
        {
            "theme": "light",
            "activity_trace_mode": "hidden_tool_calls",
            "thinking_visibility": "all",
            "live_tokens_visible": True,
            "live_cost_visible": True,
            "vocab_strictness": "lenient",
        },
    )
    updated_settings = _payload_mapping(updated_payload["settings"])
    runtime_payload = _payload_mapping(updated_payload["runtime"])
    session_payload = _payload_mapping(updated_payload["session"])
    stored = settings_store.load_app_settings()

    assert "themes" in choices_payload
    assert updated_settings["theme"] == "light"
    assert updated_settings["thinking_visibility"] == "all"
    assert updated_settings["live_tokens_visible"] is True
    assert updated_settings["live_cost_visible"] is True
    assert runtime_payload["thinking_visibility"] == "all"
    assert session_payload["thinking_visibility"] == "all"
    assert session_payload["live_tokens_visible"] is True
    assert session_payload["live_cost_visible"] is True
    assert session_payload["is_disposed"] is False
    assert stored.activity_trace_mode == "hidden_tool_calls"
    assert stored.vocab_strictness == "lenient"
    assert stored.live_tokens_visible is True
    assert stored.live_cost_visible is True
    assert service.session is not None
    assert service.session.thinking_visibility == "all"
    assert service.session.live_tokens_visible is True
    assert service.session.live_cost_visible is True

    with pytest.raises(HephSdkError, match="does not accept parameter: analytics_enabled"):
        service.call("update_settings", {"analytics_enabled": True})


def test_service_settings_apply_to_session_created_after_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_settings_store(tmp_path, monkeypatch)
    service = HephService.plain(config=_config())

    updated_payload = service.call(
        "update_settings",
        {
            "thinking_visibility": "all",
            "live_tokens_visible": True,
            "live_cost_visible": True,
        },
    )

    assert updated_payload["session"] is None

    session_payload = service.call("new_session")
    runtime_payload = _payload_mapping(session_payload["runtime"])
    active_session_payload = _payload_mapping(session_payload["session"])

    assert runtime_payload["thinking_visibility"] == "all"
    assert active_session_payload["thinking_visibility"] == "all"
    assert active_session_payload["live_tokens_visible"] is True
    assert active_session_payload["live_cost_visible"] is True
    assert service.session is not None
    assert service.session.thinking_visibility == "all"
    assert service.session.live_tokens_visible is True
    assert service.session.live_cost_visible is True


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
        assert raw_session.config.model == "updated-model"
        assert raw_session.config.max_tokens == 0
        assert raw_session.config.rag_context_budget == 0
        assert raw_session.config.temperature == 2.0
        assert raw_session.config.reasoning_level == "xhigh"
        assert raw_session.config.thinking_visibility == "all"
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
    capabilities_payload = service.call("capabilities")
    validation_payload = service.call("validate_armory", {"path": str(armory)})
    events = list(service.stream("prompt", {"text": "Dispatch this."}))
    ask = service.call("ask", {"text": "Return final text."})

    runtime_payload = _payload_mapping(config_payload["runtime"])
    zero_runtime_payload = _payload_mapping(zero_config_payload["runtime"])
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
    assert service.session is not None
    assert service.session.model == "updated-model"
    assert service.session.thinking_visibility == "all"
    assert capabilities_payload == service.capabilities()
    assert "capabilities" in _payload_list(capability_service["call_methods"])
    assert validated_armory["valid"] is True
    assert validated_armory["path"] == str(armory.resolve())
    assert events[0] == {"type": "assistant_delta", "delta": "Dispatched."}
    assert _payload_mapping(ask)["text"] == "Dispatched."

    with pytest.raises(HephSdkError, match="Unknown SDK service method"):
        service.call("missing")
    with pytest.raises(HephSdkError, match="does not accept parameter: typo"):
        service.call("state", {"typo": True})
    with pytest.raises(HephSdkError, match="requires parameter: path"):
        service.call("open_armory")
    with pytest.raises(HephSdkError, match="parameter 'text' must be a string"):
        service.call("ask", {"text": 123})
    with pytest.raises(HephSdkError, match="non-empty string"):
        list(service.stream("prompt", {"text": ""}))
    with pytest.raises(HephSdkError, match="does not accept parameter: text"):
        list(service.stream("build_index", {"text": "unused"}))
    with pytest.raises(HephSdkError, match="must be a boolean"):
        service.call("set_source_enabled", {"source": "materials/notes.md", "enabled": "no"})
    with pytest.raises(HephSdkError, match="must be a boolean"):
        service.call("list_model_choices", {"refresh_live": "yes"})
    with pytest.raises(HephSdkError, match="does not accept parameter: typo"):
        service.call("update_config", {"typo": "ignored before this change"})
    with pytest.raises(HephSdkError, match="parameter 'reasoning_level' must be one of"):
        service.call("update_config", {"reasoning_level": "turbo"})
    with pytest.raises(HephSdkError, match="parameter 'theme' must be one of"):
        service.call("update_settings", {"theme": "neon"})


def test_service_ask_falls_back_to_streamed_deltas(
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
        raw_session.conversation.add("user", prompt)
        raw_session.conversation.add("assistant", "Delta fallback.")
        raw_session.dirty = True
        yield AssistantDeltaEvent("Delta ")
        yield AssistantDeltaEvent("fallback.")

    monkeypatch.setattr(sdk_runtime, "iter_chat_events", fake_iter_chat_events)

    response = service.call("ask", {"text": "Return deltas only."})
    session = _payload_mapping(response["session"])

    assert response["text"] == "Delta fallback."
    assert session["model"] == "gpt-4o-mini"


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
