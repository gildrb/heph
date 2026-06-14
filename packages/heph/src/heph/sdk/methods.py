"""SDK method and wire-contract names shared by services and transports."""

from __future__ import annotations

from dataclasses import dataclass

from ai.providers.reasoning import REASONING_LEVELS
from ai.runtime import EngineErrorCode
from ai.runtime.thinking import THINKING_VISIBILITY_MODES
from hephaion.parameters.settings import (
    ACTIVITY_TRACE_MODES,
    THEME_PRESETS,
    VOCAB_STRICTNESS_MODES,
)

SDK_CAPABILITIES_VERSION = 29
SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1
SDK_ENGINE_ERROR_CODE = "engine_error"
SDK_METHOD_REQUIREMENT_ALWAYS = "always"
SDK_METHOD_REQUIREMENT_ARMORY = "armory"
SDK_METHOD_REQUIREMENT_SESSION = "session"
SDK_METHOD_REQUIREMENT_ARMORY_SESSION = "armory_session"
SDK_METHOD_REQUIREMENT_SESSION_SOURCES = "session_sources"
SDK_METHOD_AVAILABILITY_REQUIREMENTS = (
    SDK_METHOD_REQUIREMENT_ALWAYS,
    SDK_METHOD_REQUIREMENT_ARMORY,
    SDK_METHOD_REQUIREMENT_SESSION,
    SDK_METHOD_REQUIREMENT_ARMORY_SESSION,
    SDK_METHOD_REQUIREMENT_SESSION_SOURCES,
)
SDK_METHOD_UNAVAILABLE_BUSY = "busy"
SDK_METHOD_UNAVAILABLE_MISSING_ARMORY = "missing_armory"
SDK_METHOD_UNAVAILABLE_MISSING_SESSION = "missing_session"
SDK_METHOD_UNAVAILABLE_MISSING_ARMORY_SESSION = "missing_armory_session"
SDK_METHOD_UNAVAILABLE_MISSING_SESSION_SOURCES = "missing_session_sources"
SDK_METHOD_UNAVAILABLE_GENERIC = "unavailable"
SDK_METHOD_UNAVAILABLE_REASONS = (
    SDK_METHOD_UNAVAILABLE_BUSY,
    SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    SDK_METHOD_UNAVAILABLE_MISSING_ARMORY_SESSION,
    SDK_METHOD_UNAVAILABLE_MISSING_SESSION_SOURCES,
    SDK_METHOD_UNAVAILABLE_GENERIC,
)


@dataclass(frozen=True, slots=True)
class SdkFieldSpec:
    """A JSON-ready SDK state-field contract."""

    name: str
    value_type: str
    nullable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"type": self.value_type, "nullable": self.nullable}


@dataclass(frozen=True, slots=True)
class SdkObjectFieldSpec:
    """A JSON-ready SDK object field contract."""

    name: str
    value_type: str
    required: bool = True
    nullable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.value_type,
            "required": self.required,
            "nullable": self.nullable,
        }


SdkEventFieldSpec = SdkObjectFieldSpec
SdkTypeFieldSpec = SdkObjectFieldSpec
SdkResultFieldSpec = SdkObjectFieldSpec
SdkJsonlMessageFieldSpec = SdkObjectFieldSpec


@dataclass(frozen=True, slots=True)
class SdkEventSpec:
    """A JSON-ready SDK stream event payload contract."""

    event_type: str
    fields: tuple[SdkObjectFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": event_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkTypeSpec:
    """A JSON-ready reusable SDK DTO contract."""

    type_name: str
    fields: tuple[SdkObjectFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": type_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkResultSpec:
    """A JSON-ready SDK call result contract."""

    method: str
    value_type: str = "object"
    fields: tuple[SdkObjectFieldSpec, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.value_type,
            "fields": result_field_specs_to_dict(self.fields),
        }


@dataclass(frozen=True, slots=True)
class SdkStreamSpec:
    """A JSON-ready SDK stream event contract."""

    method: str
    event_types: tuple[str, ...]
    completion_event: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "event_types": list(self.event_types),
            "completion_event": self.completion_event,
        }


@dataclass(frozen=True, slots=True)
class SdkErrorSpec:
    """A JSON-ready SDK transport error-code contract."""

    code: str
    description: str

    def to_dict(self) -> dict[str, object]:
        return {"description": self.description}


@dataclass(frozen=True, slots=True)
class SdkJsonlMessageSpec:
    """A JSON-ready JSONL transport envelope contract."""

    message_type: str
    fields: tuple[SdkObjectFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": jsonl_message_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkJsonlRequestSpec:
    """A JSON-ready JSONL request envelope contract."""

    fields: tuple[SdkObjectFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": jsonl_message_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkMethodParameter:
    """A JSON-ready SDK method parameter contract."""

    name: str
    value_type: str
    required: bool
    choices: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "type": self.value_type,
            "required": self.required,
        }
        if self.choices:
            payload["choices"] = list(self.choices)
        return payload


@dataclass(frozen=True, slots=True)
class SdkMethodSpec:
    """A JSON-ready SDK method contract."""

    method: str
    params: tuple[SdkMethodParameter, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"params": [param.to_dict() for param in self.params]}


@dataclass(frozen=True, slots=True)
class SdkMethodAvailabilitySpec:
    """A JSON-ready SDK method availability precondition contract."""

    method: str
    requirement: str = SDK_METHOD_REQUIREMENT_ALWAYS
    unavailable_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "requirement": self.requirement,
            "unavailable_reason": self.unavailable_reason,
        }


def _type_fields_from_state_specs(
    specs: tuple[SdkFieldSpec, ...],
) -> tuple[SdkObjectFieldSpec, ...]:
    return tuple(
        SdkTypeFieldSpec(spec.name, spec.value_type, nullable=spec.nullable) for spec in specs
    )


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
REASONING_LEVEL_PARAM = SdkMethodParameter(
    "reasoning_level",
    "string",
    False,
    choices=REASONING_LEVELS,
)
THINKING_VISIBILITY_PARAM = SdkMethodParameter(
    "thinking_visibility",
    "string",
    False,
    choices=THINKING_VISIBILITY_MODES,
)
THEME_PARAM = SdkMethodParameter("theme", "string", False, choices=THEME_PRESETS)
DEFAULT_ARMORY_PATH_PARAM = SdkMethodParameter("default_armory_path", "string", False)
ACTIVITY_TRACE_MODE_PARAM = SdkMethodParameter(
    "activity_trace_mode",
    "string",
    False,
    choices=ACTIVITY_TRACE_MODES,
)
VOCAB_STRICTNESS_PARAM = SdkMethodParameter(
    "vocab_strictness",
    "string",
    False,
    choices=VOCAB_STRICTNESS_MODES,
)
LIVE_TOKENS_VISIBLE_PARAM = SdkMethodParameter("live_tokens_visible", "boolean", False)
LIVE_COST_VISIBLE_PARAM = SdkMethodParameter("live_cost_visible", "boolean", False)

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
    SdkMethodSpec("settings"),
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
    SdkMethodSpec(
        "update_settings",
        (
            THEME_PARAM,
            DEFAULT_ARMORY_PATH_PARAM,
            ACTIVITY_TRACE_MODE_PARAM,
            VOCAB_STRICTNESS_PARAM,
            THINKING_VISIBILITY_PARAM,
            LIVE_TOKENS_VISIBLE_PARAM,
            LIVE_COST_VISIBLE_PARAM,
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
SERVICE_OPERATION_STREAM_METHODS = {
    service_method: jsonl_method
    for jsonl_method, service_method in JSONL_OPERATION_STREAM_METHODS.items()
}
SERVICE_CALL_METHOD_AVAILABILITY_SPECS = (
    SdkMethodAvailabilitySpec("state"),
    SdkMethodAvailabilitySpec("capabilities"),
    SdkMethodAvailabilitySpec("use_plain_runtime"),
    SdkMethodAvailabilitySpec("open_armory"),
    SdkMethodAvailabilitySpec("create_armory"),
    SdkMethodAvailabilitySpec("list_armories"),
    SdkMethodAvailabilitySpec("validate_armory"),
    SdkMethodAvailabilitySpec("new_session"),
    SdkMethodAvailabilitySpec(
        "resume_session",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
    SdkMethodAvailabilitySpec(
        "fork_session",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec("list_sessions"),
    SdkMethodAvailabilitySpec(
        "save_session",
        SDK_METHOD_REQUIREMENT_ARMORY_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY_SESSION,
    ),
    SdkMethodAvailabilitySpec(
        "messages",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec(
        "ask",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec(
        "abort",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec("settings"),
    SdkMethodAvailabilitySpec("list_providers"),
    SdkMethodAvailabilitySpec("list_model_choices"),
    SdkMethodAvailabilitySpec("switch_model"),
    SdkMethodAvailabilitySpec(
        "set_source_enabled",
        SDK_METHOD_REQUIREMENT_SESSION_SOURCES,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION_SOURCES,
    ),
    SdkMethodAvailabilitySpec(
        "list_materials",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
    SdkMethodAvailabilitySpec(
        "import_materials",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
    SdkMethodAvailabilitySpec(
        "build_index",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
    SdkMethodAvailabilitySpec(
        "scan_extraction_health",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
    SdkMethodAvailabilitySpec("update_config"),
    SdkMethodAvailabilitySpec("update_settings"),
)
SERVICE_STREAM_METHOD_AVAILABILITY_SPECS = (
    SdkMethodAvailabilitySpec(
        "prompt",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec(
        "build_index",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
)
JSONL_CALL_METHOD_AVAILABILITY_SPECS = SERVICE_CALL_METHOD_AVAILABILITY_SPECS
JSONL_STREAM_METHOD_AVAILABILITY_SPECS = (
    SdkMethodAvailabilitySpec(
        "prompt",
        SDK_METHOD_REQUIREMENT_SESSION,
        SDK_METHOD_UNAVAILABLE_MISSING_SESSION,
    ),
    SdkMethodAvailabilitySpec(
        "build_index_stream",
        SDK_METHOD_REQUIREMENT_ARMORY,
        SDK_METHOD_UNAVAILABLE_MISSING_ARMORY,
    ),
)
JSONL_REQUEST_SPEC = SdkJsonlRequestSpec(
    fields=(
        SdkJsonlMessageFieldSpec("id", "string_or_integer", required=False, nullable=True),
        SdkJsonlMessageFieldSpec("method", "string"),
        SdkJsonlMessageFieldSpec("params", "object", required=False, nullable=True),
    ),
)
REQUEST_ID_MESSAGE_FIELD = SdkJsonlMessageFieldSpec(
    "id",
    "string_or_integer",
    nullable=True,
)
JSONL_ERROR_MESSAGE_FIELD = SdkJsonlMessageFieldSpec("error", "jsonl_error")
JSONL_MESSAGE_SPECS = (
    SdkJsonlMessageSpec(
        "ready",
        (
            SdkJsonlMessageFieldSpec("type", "literal<ready>"),
            SdkJsonlMessageFieldSpec("protocol", "string"),
            SdkJsonlMessageFieldSpec("version", "integer"),
            SdkJsonlMessageFieldSpec("capabilities", "sdk_capabilities"),
            SdkJsonlMessageFieldSpec("state", "sdk_state"),
        ),
    ),
    SdkJsonlMessageSpec(
        "response",
        (
            SdkJsonlMessageFieldSpec("type", "literal<response>"),
            REQUEST_ID_MESSAGE_FIELD,
            SdkJsonlMessageFieldSpec("ok", "boolean"),
            SdkJsonlMessageFieldSpec("result", "object"),
        ),
    ),
    SdkJsonlMessageSpec(
        "error",
        (
            SdkJsonlMessageFieldSpec("type", "literal<error>"),
            REQUEST_ID_MESSAGE_FIELD,
            SdkJsonlMessageFieldSpec("ok", "boolean"),
            JSONL_ERROR_MESSAGE_FIELD,
        ),
    ),
    SdkJsonlMessageSpec(
        "stream_start",
        (
            SdkJsonlMessageFieldSpec("type", "literal<stream_start>"),
            REQUEST_ID_MESSAGE_FIELD,
            SdkJsonlMessageFieldSpec("method", "string"),
        ),
    ),
    SdkJsonlMessageSpec(
        "stream_event",
        (
            SdkJsonlMessageFieldSpec("type", "literal<stream_event>"),
            REQUEST_ID_MESSAGE_FIELD,
            SdkJsonlMessageFieldSpec("event", "sdk_event"),
        ),
    ),
    SdkJsonlMessageSpec(
        "stream_end",
        (
            SdkJsonlMessageFieldSpec("type", "literal<stream_end>"),
            REQUEST_ID_MESSAGE_FIELD,
            SdkJsonlMessageFieldSpec("ok", "boolean"),
            SdkJsonlMessageFieldSpec("error", "jsonl_error", required=False),
        ),
    ),
)
JSONL_MESSAGE_TYPES = tuple(spec.message_type for spec in JSONL_MESSAGE_SPECS)
JSONL_ERROR_SPECS = (
    SdkErrorSpec("invalid_json", "A request line was not valid JSON."),
    SdkErrorSpec(
        "invalid_request",
        "A request envelope, id, method, or params shape was invalid.",
    ),
    SdkErrorSpec("busy", "The service rejected a request while a stream was active."),
    SdkErrorSpec(
        "unavailable",
        "The requested method exists but is not available for the current runtime/session state.",
    ),
    SdkErrorSpec("sdk_error", "The SDK rejected a valid request."),
    SdkErrorSpec(
        SDK_ENGINE_ERROR_CODE,
        "The model runtime rejected a request without a more specific code.",
    ),
    SdkErrorSpec(
        EngineErrorCode.ACCOUNT_SETUP.value,
        "Provider account setup or billing prevented the model request.",
    ),
    SdkErrorSpec(
        EngineErrorCode.PROVIDER_CAPACITY.value,
        "Provider capacity or rate limiting prevented the model request.",
    ),
    SdkErrorSpec(
        EngineErrorCode.MISSING_CREDENTIALS.value,
        "Provider credentials are missing for the selected model.",
    ),
    SdkErrorSpec(
        EngineErrorCode.MISSING_MODEL_SOURCE.value,
        "No model source is configured.",
    ),
    SdkErrorSpec(EngineErrorCode.MISSING_MODEL.value, "No model is configured."),
    SdkErrorSpec(
        EngineErrorCode.MODEL_UNAVAILABLE.value,
        "The selected model is unavailable for the configured provider endpoint.",
    ),
    SdkErrorSpec(
        EngineErrorCode.CIRCUIT_OPEN.value,
        "The model provider circuit breaker is open after recent failures.",
    ),
    SdkErrorSpec("internal_error", "An unexpected server-side exception escaped the SDK layer."),
)
JSONL_ERROR_CODES = tuple(spec.code for spec in JSONL_ERROR_SPECS)
BUSY_ALLOWED_CALL_METHODS = ("state", "abort", "capabilities", "settings")
SERVICE_CALL_RESULT_SPECS = (
    SdkResultSpec("state", value_type="sdk_state"),
    SdkResultSpec(
        "capabilities",
        fields=(SdkResultFieldSpec("capabilities", "sdk_capabilities"),),
    ),
    SdkResultSpec("use_plain_runtime", value_type="sdk_state"),
    SdkResultSpec("open_armory", value_type="sdk_state"),
    SdkResultSpec("create_armory", value_type="sdk_state"),
    SdkResultSpec(
        "list_armories",
        fields=(SdkResultFieldSpec("armories", "array<armory_summary>"),),
    ),
    SdkResultSpec(
        "validate_armory",
        fields=(SdkResultFieldSpec("armory", "armory_validation_summary"),),
    ),
    SdkResultSpec(
        "new_session",
        fields=(
            SdkResultFieldSpec("session", "sdk_session_state"),
            SdkResultFieldSpec("runtime", "sdk_runtime_state"),
        ),
    ),
    SdkResultSpec(
        "resume_session",
        fields=(
            SdkResultFieldSpec("session", "sdk_session_state"),
            SdkResultFieldSpec("runtime", "sdk_runtime_state"),
        ),
    ),
    SdkResultSpec(
        "fork_session",
        fields=(
            SdkResultFieldSpec("session", "sdk_session_state"),
            SdkResultFieldSpec("runtime", "sdk_runtime_state"),
        ),
    ),
    SdkResultSpec(
        "list_sessions",
        fields=(SdkResultFieldSpec("sessions", "array<session_summary>"),),
    ),
    SdkResultSpec(
        "save_session",
        fields=(
            SdkResultFieldSpec("path", "string"),
            SdkResultFieldSpec("session", "sdk_session_state"),
        ),
    ),
    SdkResultSpec(
        "messages",
        fields=(SdkResultFieldSpec("messages", "array<message>"),),
    ),
    SdkResultSpec(
        "ask",
        fields=(
            SdkResultFieldSpec("text", "string"),
            SdkResultFieldSpec("session", "sdk_session_state"),
        ),
    ),
    SdkResultSpec(
        "abort",
        fields=(
            SdkResultFieldSpec("aborted", "boolean"),
            SdkResultFieldSpec("state", "sdk_state", required=False),
            SdkResultFieldSpec("session", "sdk_session_state", required=False),
        ),
    ),
    SdkResultSpec(
        "settings",
        fields=(SdkResultFieldSpec("settings", "sdk_app_settings"),),
    ),
    SdkResultSpec(
        "list_providers",
        fields=(SdkResultFieldSpec("providers", "array<provider_summary>"),),
    ),
    SdkResultSpec(
        "list_model_choices",
        fields=(SdkResultFieldSpec("models", "array<model_choice_summary>"),),
    ),
    SdkResultSpec(
        "switch_model",
        fields=(
            SdkResultFieldSpec("changed", "boolean"),
            SdkResultFieldSpec("runtime", "sdk_runtime_state"),
            SdkResultFieldSpec("session", "sdk_session_state", nullable=True),
        ),
    ),
    SdkResultSpec(
        "set_source_enabled",
        fields=(
            SdkResultFieldSpec("changed", "boolean"),
            SdkResultFieldSpec("session", "sdk_session_state"),
        ),
    ),
    SdkResultSpec(
        "list_materials",
        fields=(SdkResultFieldSpec("materials", "array<material_summary>"),),
    ),
    SdkResultSpec(
        "import_materials",
        fields=(SdkResultFieldSpec("import", "import_materials_summary"),),
    ),
    SdkResultSpec(
        "build_index",
        fields=(SdkResultFieldSpec("index", "index_summary"),),
    ),
    SdkResultSpec(
        "scan_extraction_health",
        fields=(SdkResultFieldSpec("health", "extraction_health_summary"),),
    ),
    SdkResultSpec(
        "update_config",
        fields=(SdkResultFieldSpec("runtime", "sdk_runtime_state"),),
    ),
    SdkResultSpec(
        "update_settings",
        fields=(
            SdkResultFieldSpec("settings", "sdk_app_settings"),
            SdkResultFieldSpec("runtime", "sdk_runtime_state"),
            SdkResultFieldSpec("session", "sdk_session_state", nullable=True),
        ),
    ),
)
JSONL_CALL_RESULT_SPECS = SERVICE_CALL_RESULT_SPECS
SDK_EVENT_SPECS = (
    SdkEventSpec(
        "assistant_delta",
        (
            SdkEventFieldSpec("type", "literal<assistant_delta>"),
            SdkEventFieldSpec("delta", "string"),
        ),
    ),
    SdkEventSpec(
        "reasoning_delta",
        (
            SdkEventFieldSpec("type", "literal<reasoning_delta>"),
            SdkEventFieldSpec("delta", "string"),
            SdkEventFieldSpec("summary", "boolean"),
        ),
    ),
    SdkEventSpec(
        "tool_call",
        (
            SdkEventFieldSpec("type", "literal<tool_call>"),
            SdkEventFieldSpec("call_id", "string"),
            SdkEventFieldSpec("name", "string"),
            SdkEventFieldSpec("arguments", "object"),
            SdkEventFieldSpec("display", "string"),
        ),
    ),
    SdkEventSpec(
        "tool_result",
        (
            SdkEventFieldSpec("type", "literal<tool_result>"),
            SdkEventFieldSpec("call_id", "string"),
            SdkEventFieldSpec("name", "string"),
            SdkEventFieldSpec("content", "string"),
            SdkEventFieldSpec("summary", "string"),
            SdkEventFieldSpec("success", "boolean"),
            SdkEventFieldSpec("metadata", "object", required=False),
            SdkEventFieldSpec("error", "string", required=False),
        ),
    ),
    SdkEventSpec(
        "material_operation",
        (
            SdkEventFieldSpec("type", "literal<material_operation>"),
            SdkEventFieldSpec("operation", "string"),
            SdkEventFieldSpec("message", "string"),
            SdkEventFieldSpec("metadata", "object", required=False),
        ),
    ),
    SdkEventSpec(
        "compact_request",
        (
            SdkEventFieldSpec("type", "literal<compact_request>"),
            SdkEventFieldSpec("call_id", "string"),
            SdkEventFieldSpec("name", "string"),
            SdkEventFieldSpec("arguments", "object"),
        ),
    ),
    SdkEventSpec(
        "turn_complete",
        (
            SdkEventFieldSpec("type", "literal<turn_complete>"),
            SdkEventFieldSpec("full_text", "string"),
            SdkEventFieldSpec("turn_index", "integer"),
            SdkEventFieldSpec("latency_ms", "number"),
            SdkEventFieldSpec("finish_reason", "string"),
            SdkEventFieldSpec("tokens_remaining", "integer"),
        ),
    ),
    SdkEventSpec(
        "notice",
        (
            SdkEventFieldSpec("type", "literal<notice>"),
            SdkEventFieldSpec("message", "string"),
            SdkEventFieldSpec("code", "string"),
            SdkEventFieldSpec("metadata", "object", required=False),
        ),
    ),
    SdkEventSpec(
        "guardrail",
        (
            SdkEventFieldSpec("type", "literal<guardrail>"),
            SdkEventFieldSpec("stage", "string"),
            SdkEventFieldSpec("action", "string"),
            SdkEventFieldSpec("message", "string"),
            SdkEventFieldSpec("metadata", "object", required=False),
        ),
    ),
    SdkEventSpec(
        "index_progress",
        (
            SdkEventFieldSpec("type", "literal<index_progress>"),
            SdkEventFieldSpec("action", "string"),
            SdkEventFieldSpec("detail", "string"),
        ),
    ),
    SdkEventSpec(
        "index_complete",
        (
            SdkEventFieldSpec("type", "literal<index_complete>"),
            SdkEventFieldSpec("index", "index_summary"),
        ),
    ),
)
SDK_EVENT_TYPES = tuple(spec.event_type for spec in SDK_EVENT_SPECS)
TURN_STREAM_EVENT_TYPES = tuple(
    event_type
    for event_type in SDK_EVENT_TYPES
    if event_type not in {"index_progress", "index_complete"}
)
INDEX_STREAM_EVENT_TYPES = ("index_progress", "index_complete")
SERVICE_STREAM_SPECS = (
    SdkStreamSpec("prompt", TURN_STREAM_EVENT_TYPES, completion_event="turn_complete"),
    SdkStreamSpec("build_index", INDEX_STREAM_EVENT_TYPES, completion_event="index_complete"),
)
JSONL_STREAM_SPECS = (
    SdkStreamSpec("prompt", TURN_STREAM_EVENT_TYPES, completion_event="turn_complete"),
    SdkStreamSpec(
        "build_index_stream",
        INDEX_STREAM_EVENT_TYPES,
        completion_event="index_complete",
    ),
)
SERVICE_STATE_FIELD_SPECS = (
    SdkFieldSpec("prompt_active", "boolean"),
    SdkFieldSpec("active_operation", "string", nullable=True),
    SdkFieldSpec("is_busy", "boolean"),
    SdkFieldSpec("available_call_methods", "array<string>"),
    SdkFieldSpec("available_stream_methods", "array<string>"),
    SdkFieldSpec("call_method_availability", "array<sdk_method_availability>"),
    SdkFieldSpec("stream_method_availability", "array<sdk_method_availability>"),
)
RUNTIME_STATE_FIELD_SPECS = (
    SdkFieldSpec("armory_path", "string", nullable=True),
    SdkFieldSpec("provider_slug", "string"),
    SdkFieldSpec("model", "string"),
    SdkFieldSpec("base_url", "string"),
    SdkFieldSpec("max_tokens", "integer"),
    SdkFieldSpec("rag_context_budget", "integer"),
    SdkFieldSpec("temperature", "number", nullable=True),
    SdkFieldSpec("reasoning_level", "string"),
    SdkFieldSpec("thinking_visibility", "string"),
    SdkFieldSpec("feature_flags", "array<string>"),
)
SESSION_STATE_FIELD_SPECS = (
    SdkFieldSpec("session_id", "string"),
    SdkFieldSpec("title", "string"),
    SdkFieldSpec("armory_path", "string", nullable=True),
    SdkFieldSpec("provider_slug", "string"),
    SdkFieldSpec("model", "string"),
    SdkFieldSpec("thinking_visibility", "string"),
    SdkFieldSpec("live_tokens_visible", "boolean"),
    SdkFieldSpec("live_cost_visible", "boolean"),
    SdkFieldSpec("is_streaming", "boolean"),
    SdkFieldSpec("is_disposed", "boolean"),
    SdkFieldSpec("source_file_count", "integer"),
    SdkFieldSpec("source_files", "array<string>"),
    SdkFieldSpec("disabled_source_files", "array<string>"),
    SdkFieldSpec("enabled_source_files", "array<string>"),
    SdkFieldSpec("has_unsaved_changes", "boolean"),
    SdkFieldSpec("messages", "array<message>"),
)
SERVICE_STATE_FIELDS = tuple(spec.name for spec in SERVICE_STATE_FIELD_SPECS)
RUNTIME_STATE_FIELDS = tuple(spec.name for spec in RUNTIME_STATE_FIELD_SPECS)
SESSION_STATE_FIELDS = tuple(spec.name for spec in SESSION_STATE_FIELD_SPECS)
SDK_TYPE_SPECS = (
    SdkTypeSpec(
        "sdk_capabilities",
        (
            SdkTypeFieldSpec("version", "integer"),
            SdkTypeFieldSpec("service", "object"),
            SdkTypeFieldSpec("jsonl", "object"),
            SdkTypeFieldSpec("events", "object"),
            SdkTypeFieldSpec("state", "object"),
            SdkTypeFieldSpec("methods", "object"),
            SdkTypeFieldSpec("errors", "object"),
            SdkTypeFieldSpec("results", "object"),
            SdkTypeFieldSpec("streams", "object"),
            SdkTypeFieldSpec("availability", "object"),
            SdkTypeFieldSpec("fields", "object"),
            SdkTypeFieldSpec("types", "object"),
        ),
    ),
    SdkTypeSpec(
        "jsonl_error",
        (
            SdkTypeFieldSpec("code", "string"),
            SdkTypeFieldSpec("message", "string"),
        ),
    ),
    SdkTypeSpec(
        "sdk_event",
        (SdkTypeFieldSpec("type", "string"),),
    ),
    SdkTypeSpec(
        "sdk_state",
        (
            SdkTypeFieldSpec("service", "sdk_service_state"),
            SdkTypeFieldSpec("runtime", "sdk_runtime_state"),
            SdkTypeFieldSpec("session", "sdk_session_state", nullable=True),
        ),
    ),
    SdkTypeSpec(
        "sdk_method_availability",
        (
            SdkTypeFieldSpec("method", "string"),
            SdkTypeFieldSpec("available", "boolean"),
            SdkTypeFieldSpec("unavailable_reason", "string", nullable=True),
        ),
    ),
    SdkTypeSpec(
        "sdk_method_availability_spec",
        (
            SdkTypeFieldSpec("requirement", "string"),
            SdkTypeFieldSpec("unavailable_reason", "string", nullable=True),
        ),
    ),
    SdkTypeSpec("sdk_service_state", _type_fields_from_state_specs(SERVICE_STATE_FIELD_SPECS)),
    SdkTypeSpec("sdk_runtime_state", _type_fields_from_state_specs(RUNTIME_STATE_FIELD_SPECS)),
    SdkTypeSpec("sdk_session_state", _type_fields_from_state_specs(SESSION_STATE_FIELD_SPECS)),
    SdkTypeSpec(
        "message",
        (
            SdkTypeFieldSpec("role", "string"),
            SdkTypeFieldSpec("content", "string"),
        ),
    ),
    SdkTypeSpec(
        "setting_choice",
        (
            SdkTypeFieldSpec("value", "string"),
            SdkTypeFieldSpec("label", "string"),
        ),
    ),
    SdkTypeSpec(
        "sdk_settings_choices",
        (
            SdkTypeFieldSpec("themes", "array<setting_choice>"),
            SdkTypeFieldSpec("activity_trace_modes", "array<setting_choice>"),
            SdkTypeFieldSpec("thinking_visibility_modes", "array<setting_choice>"),
            SdkTypeFieldSpec("vocab_strictness_modes", "array<setting_choice>"),
        ),
    ),
    SdkTypeSpec(
        "sdk_privacy_settings",
        (
            SdkTypeFieldSpec("analytics_enabled", "boolean"),
            SdkTypeFieldSpec("analytics_available", "boolean"),
            SdkTypeFieldSpec("analytics_env_override", "boolean"),
            SdkTypeFieldSpec("crash_reports_enabled", "boolean"),
            SdkTypeFieldSpec("crash_reports_available", "boolean"),
            SdkTypeFieldSpec("crash_reports_env_override", "boolean"),
        ),
    ),
    SdkTypeSpec(
        "sdk_app_settings",
        (
            SdkTypeFieldSpec("theme", "string"),
            SdkTypeFieldSpec("default_armory_path", "string"),
            SdkTypeFieldSpec("last_armory_path", "string"),
            SdkTypeFieldSpec("activity_trace_mode", "string"),
            SdkTypeFieldSpec("vocab_strictness", "string"),
            SdkTypeFieldSpec("thinking_visibility", "string"),
            SdkTypeFieldSpec("live_tokens_visible", "boolean"),
            SdkTypeFieldSpec("live_cost_visible", "boolean"),
            SdkTypeFieldSpec("privacy", "sdk_privacy_settings"),
            SdkTypeFieldSpec("choices", "sdk_settings_choices"),
            SdkTypeFieldSpec("mutable_keys", "array<string>"),
        ),
    ),
    SdkTypeSpec(
        "armory_summary",
        (
            SdkTypeFieldSpec("name", "string"),
            SdkTypeFieldSpec("path", "string"),
            SdkTypeFieldSpec("exists", "boolean"),
            SdkTypeFieldSpec("valid", "boolean"),
        ),
    ),
    SdkTypeSpec(
        "armory_validation_summary",
        (
            SdkTypeFieldSpec("name", "string"),
            SdkTypeFieldSpec("path", "string"),
            SdkTypeFieldSpec("exists", "boolean"),
            SdkTypeFieldSpec("is_dir", "boolean"),
            SdkTypeFieldSpec("valid", "boolean"),
            SdkTypeFieldSpec("error", "string"),
        ),
    ),
    SdkTypeSpec(
        "session_summary",
        (
            SdkTypeFieldSpec("session_id", "string"),
            SdkTypeFieldSpec("title", "string"),
            SdkTypeFieldSpec("created_at", "string"),
            SdkTypeFieldSpec("updated_at", "string"),
        ),
    ),
    SdkTypeSpec(
        "provider_summary",
        (
            SdkTypeFieldSpec("provider_slug", "string"),
            SdkTypeFieldSpec("display_name", "string"),
            SdkTypeFieldSpec("endpoint", "string"),
            SdkTypeFieldSpec("api_key_env", "string"),
            SdkTypeFieldSpec("current_model", "string"),
            SdkTypeFieldSpec("model_count", "integer"),
            SdkTypeFieldSpec("is_active", "boolean"),
            SdkTypeFieldSpec("is_current", "boolean"),
            SdkTypeFieldSpec("credential_kind", "string"),
            SdkTypeFieldSpec("credential_source", "string"),
            SdkTypeFieldSpec("credential_required", "boolean"),
            SdkTypeFieldSpec("credential_configured", "boolean"),
        ),
    ),
    SdkTypeSpec(
        "model_choice_summary",
        (
            SdkTypeFieldSpec("provider_slug", "string"),
            SdkTypeFieldSpec("provider_display_name", "string"),
            SdkTypeFieldSpec("model", "string"),
            SdkTypeFieldSpec("endpoint", "string"),
            SdkTypeFieldSpec("is_free", "boolean"),
            SdkTypeFieldSpec("is_current", "boolean"),
            SdkTypeFieldSpec("free_description", "string"),
        ),
    ),
    SdkTypeSpec(
        "material_summary",
        (
            SdkTypeFieldSpec("path", "string"),
            SdkTypeFieldSpec("rel_path", "string"),
            SdkTypeFieldSpec("display_name", "string"),
            SdkTypeFieldSpec("kind", "literal<materials>"),
            SdkTypeFieldSpec("role", "string"),
            SdkTypeFieldSpec("confidence", "number"),
            SdkTypeFieldSpec("reason", "string"),
        ),
    ),
    SdkTypeSpec(
        "import_materials_summary",
        (
            SdkTypeFieldSpec("imported", "array<string>"),
            SdkTypeFieldSpec("considered", "integer"),
            SdkTypeFieldSpec("skipped", "integer"),
            SdkTypeFieldSpec("skipped_duplicates", "integer"),
            SdkTypeFieldSpec("skipped_unsupported", "integer"),
        ),
    ),
    SdkTypeSpec(
        "index_progress_event",
        (
            SdkTypeFieldSpec("action", "string"),
            SdkTypeFieldSpec("detail", "string"),
        ),
    ),
    SdkTypeSpec(
        "index_summary",
        (
            SdkTypeFieldSpec("documents", "integer"),
            SdkTypeFieldSpec("chunks", "integer"),
            SdkTypeFieldSpec("progress", "array<index_progress_event>"),
        ),
    ),
    SdkTypeSpec(
        "extraction_health_issue_summary",
        (
            SdkTypeFieldSpec("source", "string"),
            SdkTypeFieldSpec("forbidden_text_present", "array<string>"),
        ),
    ),
    SdkTypeSpec(
        "extraction_health_summary",
        (
            SdkTypeFieldSpec("armory_path", "string"),
            SdkTypeFieldSpec("documents", "integer"),
            SdkTypeFieldSpec("checks", "integer"),
            SdkTypeFieldSpec("pass_rate", "number"),
            SdkTypeFieldSpec("passed", "boolean"),
            SdkTypeFieldSpec("forbidden_text", "array<string>"),
            SdkTypeFieldSpec("issues", "array<extraction_health_issue_summary>"),
        ),
    ),
)


def service_stream_method_for_jsonl(method: str) -> str | None:
    """Return the SDK service stream method for a JSONL operation stream."""
    if method not in JSONL_OPERATION_STREAM_METHODS:
        return None
    return JSONL_OPERATION_STREAM_METHODS[method]


def jsonl_stream_method_for_service(method: str) -> str | None:
    """Return the JSONL stream method for an available SDK service stream."""
    if method in SERVICE_OPERATION_STREAM_METHODS:
        return SERVICE_OPERATION_STREAM_METHODS[method]
    if method in SERVICE_STREAM_METHODS and method in JSONL_STREAM_METHODS:
        return method
    return None


def method_specs_to_dict(specs: tuple[SdkMethodSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def method_availability_specs_to_dict(
    specs: tuple[SdkMethodAvailabilitySpec, ...],
) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def error_specs_to_dict(specs: tuple[SdkErrorSpec, ...]) -> dict[str, object]:
    return {spec.code: spec.to_dict() for spec in specs}


def field_specs_to_dict(specs: tuple[SdkFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def _object_field_specs_to_dict(specs: tuple[SdkObjectFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def event_field_specs_to_dict(specs: tuple[SdkObjectFieldSpec, ...]) -> dict[str, object]:
    return _object_field_specs_to_dict(specs)


def event_specs_to_dict(specs: tuple[SdkEventSpec, ...]) -> dict[str, object]:
    return {spec.event_type: spec.to_dict() for spec in specs}


def jsonl_message_field_specs_to_dict(
    specs: tuple[SdkObjectFieldSpec, ...],
) -> dict[str, object]:
    return _object_field_specs_to_dict(specs)


def jsonl_message_specs_to_dict(specs: tuple[SdkJsonlMessageSpec, ...]) -> dict[str, object]:
    return {spec.message_type: spec.to_dict() for spec in specs}


def jsonl_request_spec_to_dict(spec: SdkJsonlRequestSpec) -> dict[str, object]:
    return spec.to_dict()


def result_field_specs_to_dict(specs: tuple[SdkObjectFieldSpec, ...]) -> dict[str, object]:
    return _object_field_specs_to_dict(specs)


def result_specs_to_dict(specs: tuple[SdkResultSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def stream_specs_to_dict(specs: tuple[SdkStreamSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def type_field_specs_to_dict(specs: tuple[SdkObjectFieldSpec, ...]) -> dict[str, object]:
    return _object_field_specs_to_dict(specs)


def type_specs_to_dict(specs: tuple[SdkTypeSpec, ...]) -> dict[str, object]:
    return {spec.type_name: spec.to_dict() for spec in specs}


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "INDEX_STREAM_EVENT_TYPES",
    "JSONL_CALL_METHODS",
    "JSONL_CALL_METHOD_AVAILABILITY_SPECS",
    "JSONL_CALL_METHOD_SPECS",
    "JSONL_CALL_RESULT_SPECS",
    "JSONL_ERROR_CODES",
    "JSONL_ERROR_SPECS",
    "JSONL_MESSAGE_SPECS",
    "JSONL_MESSAGE_TYPES",
    "JSONL_OPERATION_STREAM_METHODS",
    "JSONL_REQUEST_SPEC",
    "JSONL_STREAM_METHODS",
    "JSONL_STREAM_METHOD_AVAILABILITY_SPECS",
    "JSONL_STREAM_METHOD_SPECS",
    "JSONL_STREAM_SPECS",
    "RUNTIME_STATE_FIELDS",
    "RUNTIME_STATE_FIELD_SPECS",
    "SDK_CAPABILITIES_VERSION",
    "SDK_ENGINE_ERROR_CODE",
    "SDK_EVENT_SPECS",
    "SDK_EVENT_TYPES",
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "SDK_METHOD_AVAILABILITY_REQUIREMENTS",
    "SDK_METHOD_REQUIREMENT_ALWAYS",
    "SDK_METHOD_REQUIREMENT_ARMORY",
    "SDK_METHOD_REQUIREMENT_ARMORY_SESSION",
    "SDK_METHOD_REQUIREMENT_SESSION",
    "SDK_METHOD_REQUIREMENT_SESSION_SOURCES",
    "SDK_METHOD_UNAVAILABLE_BUSY",
    "SDK_METHOD_UNAVAILABLE_GENERIC",
    "SDK_METHOD_UNAVAILABLE_MISSING_ARMORY",
    "SDK_METHOD_UNAVAILABLE_MISSING_ARMORY_SESSION",
    "SDK_METHOD_UNAVAILABLE_MISSING_SESSION",
    "SDK_METHOD_UNAVAILABLE_MISSING_SESSION_SOURCES",
    "SDK_METHOD_UNAVAILABLE_REASONS",
    "SDK_TYPE_SPECS",
    "SERVICE_CALL_METHODS",
    "SERVICE_CALL_METHOD_AVAILABILITY_SPECS",
    "SERVICE_CALL_METHOD_SPECS",
    "SERVICE_CALL_RESULT_SPECS",
    "SERVICE_OPERATION_STREAM_METHODS",
    "SERVICE_STATE_FIELDS",
    "SERVICE_STATE_FIELD_SPECS",
    "SERVICE_STREAM_METHODS",
    "SERVICE_STREAM_METHOD_AVAILABILITY_SPECS",
    "SERVICE_STREAM_METHOD_SPECS",
    "SERVICE_STREAM_SPECS",
    "SESSION_STATE_FIELDS",
    "SESSION_STATE_FIELD_SPECS",
    "TURN_STREAM_EVENT_TYPES",
    "SdkErrorSpec",
    "SdkEventFieldSpec",
    "SdkEventSpec",
    "SdkFieldSpec",
    "SdkJsonlMessageFieldSpec",
    "SdkJsonlMessageSpec",
    "SdkJsonlRequestSpec",
    "SdkMethodAvailabilitySpec",
    "SdkMethodParameter",
    "SdkMethodSpec",
    "SdkObjectFieldSpec",
    "SdkResultFieldSpec",
    "SdkResultSpec",
    "SdkStreamSpec",
    "SdkTypeFieldSpec",
    "SdkTypeSpec",
    "error_specs_to_dict",
    "event_field_specs_to_dict",
    "event_specs_to_dict",
    "field_specs_to_dict",
    "jsonl_message_field_specs_to_dict",
    "jsonl_message_specs_to_dict",
    "jsonl_request_spec_to_dict",
    "jsonl_stream_method_for_service",
    "method_availability_specs_to_dict",
    "method_specs_to_dict",
    "result_field_specs_to_dict",
    "result_specs_to_dict",
    "service_stream_method_for_jsonl",
    "stream_specs_to_dict",
    "type_field_specs_to_dict",
    "type_specs_to_dict",
]
