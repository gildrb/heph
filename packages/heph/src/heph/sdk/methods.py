"""SDK method and wire-contract names shared by services and transports."""

from __future__ import annotations

from dataclasses import dataclass

SDK_CAPABILITIES_VERSION = 9
SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1


@dataclass(frozen=True, slots=True)
class SdkErrorSpec:
    """A JSON-ready SDK transport error-code contract."""

    code: str
    description: str

    def to_dict(self) -> dict[str, object]:
        return {"description": self.description}


@dataclass(frozen=True, slots=True)
class SdkMethodParameter:
    """A JSON-ready SDK method parameter contract."""

    name: str
    value_type: str
    required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "type": self.value_type,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class SdkMethodSpec:
    """A JSON-ready SDK method contract."""

    method: str
    params: tuple[SdkMethodParameter, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"params": [param.to_dict() for param in self.params]}


PATH_PARAM = SdkMethodParameter("path", "string", True)
TEXT_PARAM = SdkMethodParameter("text", "string", True)
SOURCE_PARAM = SdkMethodParameter("source", "string", True)
SESSION_ID_PARAM = SdkMethodParameter("session_id", "string", True)
TURN_ID_PARAM = SdkMethodParameter("turn_id", "string", True)
PROVIDER_SLUG_PARAM = SdkMethodParameter("provider_slug", "string", True)
MODEL_PARAM = SdkMethodParameter("model", "string", True)
ENABLED_PARAM = SdkMethodParameter("enabled", "boolean", True)
REFRESH_LIVE_PARAM = SdkMethodParameter("refresh_live", "boolean", False)
BASE_URL_PARAM = SdkMethodParameter("base_url", "string", False)
OPTIONAL_MODEL_PARAM = SdkMethodParameter("model", "string", False)
MAX_TOKENS_PARAM = SdkMethodParameter("max_tokens", "integer", False)
RAG_CONTEXT_BUDGET_PARAM = SdkMethodParameter("rag_context_budget", "integer", False)
TEMPERATURE_PARAM = SdkMethodParameter("temperature", "number_or_null", False)
REASONING_LEVEL_PARAM = SdkMethodParameter("reasoning_level", "string", False)
THINKING_VISIBILITY_PARAM = SdkMethodParameter("thinking_visibility", "string", False)

SERVICE_CALL_METHOD_SPECS = (
    SdkMethodSpec("state"),
    SdkMethodSpec("capabilities"),
    SdkMethodSpec("use_plain_runtime"),
    SdkMethodSpec("open_armory", (PATH_PARAM,)),
    SdkMethodSpec("create_armory", (PATH_PARAM,)),
    SdkMethodSpec("list_armories"),
    SdkMethodSpec("validate_armory", (PATH_PARAM,)),
    SdkMethodSpec("new_session"),
    SdkMethodSpec("resume_session", (SESSION_ID_PARAM,)),
    SdkMethodSpec("fork_session", (TURN_ID_PARAM,)),
    SdkMethodSpec("list_sessions"),
    SdkMethodSpec("save_session"),
    SdkMethodSpec("messages"),
    SdkMethodSpec("ask", (TEXT_PARAM,)),
    SdkMethodSpec("abort"),
    SdkMethodSpec("list_providers"),
    SdkMethodSpec("list_model_choices", (REFRESH_LIVE_PARAM,)),
    SdkMethodSpec("switch_model", (PROVIDER_SLUG_PARAM, MODEL_PARAM)),
    SdkMethodSpec("set_source_enabled", (SOURCE_PARAM, ENABLED_PARAM)),
    SdkMethodSpec("list_materials"),
    SdkMethodSpec("import_materials", (SOURCE_PARAM,)),
    SdkMethodSpec("build_index"),
    SdkMethodSpec("scan_extraction_health"),
    SdkMethodSpec(
        "update_config",
        (
            BASE_URL_PARAM,
            OPTIONAL_MODEL_PARAM,
            MAX_TOKENS_PARAM,
            RAG_CONTEXT_BUDGET_PARAM,
            TEMPERATURE_PARAM,
            REASONING_LEVEL_PARAM,
            THINKING_VISIBILITY_PARAM,
        ),
    ),
)
SERVICE_STREAM_METHOD_SPECS = (
    SdkMethodSpec("prompt", (TEXT_PARAM,)),
    SdkMethodSpec("build_index"),
)
JSONL_CALL_METHOD_SPECS = SERVICE_CALL_METHOD_SPECS
JSONL_STREAM_METHOD_SPECS = (
    SdkMethodSpec("prompt", (TEXT_PARAM,)),
    SdkMethodSpec("build_index_stream"),
)
SERVICE_CALL_METHODS = tuple(spec.method for spec in SERVICE_CALL_METHOD_SPECS)
SERVICE_STREAM_METHODS = tuple(spec.method for spec in SERVICE_STREAM_METHOD_SPECS)
JSONL_CALL_METHODS = SERVICE_CALL_METHODS
JSONL_STREAM_METHODS = tuple(spec.method for spec in JSONL_STREAM_METHOD_SPECS)
JSONL_OPERATION_STREAM_METHODS = {"build_index_stream": "build_index"}
JSONL_MESSAGE_TYPES = (
    "ready",
    "response",
    "error",
    "stream_start",
    "stream_event",
    "stream_end",
)
JSONL_ERROR_SPECS = (
    SdkErrorSpec("invalid_json", "A request line was not valid JSON."),
    SdkErrorSpec(
        "invalid_request",
        "A request envelope, id, method, or params shape was invalid.",
    ),
    SdkErrorSpec("busy", "The service rejected a request while a stream was active."),
    SdkErrorSpec("sdk_error", "The SDK rejected a valid request."),
    SdkErrorSpec("internal_error", "An unexpected server-side exception escaped the SDK layer."),
)
JSONL_ERROR_CODES = tuple(spec.code for spec in JSONL_ERROR_SPECS)
BUSY_ALLOWED_CALL_METHODS = ("state", "abort", "capabilities")
SDK_EVENT_TYPES = (
    "assistant_delta",
    "reasoning_delta",
    "tool_call",
    "tool_result",
    "material_operation",
    "compact_request",
    "turn_complete",
    "notice",
    "guardrail",
    "index_progress",
    "index_complete",
)
SERVICE_STATE_FIELDS = ("prompt_active", "active_operation", "is_busy")
RUNTIME_STATE_FIELDS = (
    "armory_path",
    "provider_slug",
    "model",
    "base_url",
    "max_tokens",
    "rag_context_budget",
    "temperature",
    "reasoning_level",
    "thinking_visibility",
    "feature_flags",
)
SESSION_STATE_FIELDS = (
    "session_id",
    "title",
    "armory_path",
    "provider_slug",
    "model",
    "is_streaming",
    "is_disposed",
    "source_file_count",
    "source_files",
    "disabled_source_files",
    "enabled_source_files",
    "has_unsaved_changes",
    "messages",
)


def service_stream_method_for_jsonl(method: str) -> str | None:
    """Return the SDK service stream method for a JSONL operation stream."""
    if method not in JSONL_OPERATION_STREAM_METHODS:
        return None
    return JSONL_OPERATION_STREAM_METHODS[method]


def method_specs_to_dict(specs: tuple[SdkMethodSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def error_specs_to_dict(specs: tuple[SdkErrorSpec, ...]) -> dict[str, object]:
    return {spec.code: spec.to_dict() for spec in specs}


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "JSONL_CALL_METHODS",
    "JSONL_CALL_METHOD_SPECS",
    "JSONL_ERROR_CODES",
    "JSONL_ERROR_SPECS",
    "JSONL_MESSAGE_TYPES",
    "JSONL_OPERATION_STREAM_METHODS",
    "JSONL_STREAM_METHODS",
    "JSONL_STREAM_METHOD_SPECS",
    "RUNTIME_STATE_FIELDS",
    "SDK_CAPABILITIES_VERSION",
    "SDK_EVENT_TYPES",
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "SERVICE_CALL_METHODS",
    "SERVICE_CALL_METHOD_SPECS",
    "SERVICE_STATE_FIELDS",
    "SERVICE_STREAM_METHODS",
    "SERVICE_STREAM_METHOD_SPECS",
    "SESSION_STATE_FIELDS",
    "SdkErrorSpec",
    "SdkMethodParameter",
    "SdkMethodSpec",
    "error_specs_to_dict",
    "method_specs_to_dict",
    "service_stream_method_for_jsonl",
]
