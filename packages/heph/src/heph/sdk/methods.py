"""SDK method and wire-contract names shared by services and transports."""

from __future__ import annotations

from dataclasses import dataclass

SDK_CAPABILITIES_VERSION = 14
SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1


@dataclass(frozen=True, slots=True)
class SdkFieldSpec:
    """A JSON-ready SDK state-field contract."""

    name: str
    value_type: str
    nullable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"type": self.value_type, "nullable": self.nullable}


@dataclass(frozen=True, slots=True)
class SdkEventFieldSpec:
    """A JSON-ready SDK event payload field contract."""

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


@dataclass(frozen=True, slots=True)
class SdkEventSpec:
    """A JSON-ready SDK stream event payload contract."""

    event_type: str
    fields: tuple[SdkEventFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": event_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkTypeFieldSpec:
    """A JSON-ready reusable SDK DTO field contract."""

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


@dataclass(frozen=True, slots=True)
class SdkTypeSpec:
    """A JSON-ready reusable SDK DTO contract."""

    type_name: str
    fields: tuple[SdkTypeFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": type_field_specs_to_dict(self.fields)}


@dataclass(frozen=True, slots=True)
class SdkResultFieldSpec:
    """A JSON-ready SDK call result field contract."""

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


@dataclass(frozen=True, slots=True)
class SdkResultSpec:
    """A JSON-ready SDK call result contract."""

    method: str
    value_type: str = "object"
    fields: tuple[SdkResultFieldSpec, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.value_type,
            "fields": result_field_specs_to_dict(self.fields),
        }


@dataclass(frozen=True, slots=True)
class SdkErrorSpec:
    """A JSON-ready SDK transport error-code contract."""

    code: str
    description: str

    def to_dict(self) -> dict[str, object]:
        return {"description": self.description}


@dataclass(frozen=True, slots=True)
class SdkJsonlMessageFieldSpec:
    """A JSON-ready JSONL transport message field contract."""

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


@dataclass(frozen=True, slots=True)
class SdkJsonlMessageSpec:
    """A JSON-ready JSONL transport envelope contract."""

    message_type: str
    fields: tuple[SdkJsonlMessageFieldSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {"fields": jsonl_message_field_specs_to_dict(self.fields)}


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


def _type_fields_from_state_specs(specs: tuple[SdkFieldSpec, ...]) -> tuple[SdkTypeFieldSpec, ...]:
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
    SdkErrorSpec("sdk_error", "The SDK rejected a valid request."),
    SdkErrorSpec("internal_error", "An unexpected server-side exception escaped the SDK layer."),
)
JSONL_ERROR_CODES = tuple(spec.code for spec in JSONL_ERROR_SPECS)
BUSY_ALLOWED_CALL_METHODS = ("state", "abort", "capabilities")
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
SERVICE_STATE_FIELD_SPECS = (
    SdkFieldSpec("prompt_active", "boolean"),
    SdkFieldSpec("active_operation", "string", nullable=True),
    SdkFieldSpec("is_busy", "boolean"),
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


def method_specs_to_dict(specs: tuple[SdkMethodSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def error_specs_to_dict(specs: tuple[SdkErrorSpec, ...]) -> dict[str, object]:
    return {spec.code: spec.to_dict() for spec in specs}


def field_specs_to_dict(specs: tuple[SdkFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def event_field_specs_to_dict(specs: tuple[SdkEventFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def event_specs_to_dict(specs: tuple[SdkEventSpec, ...]) -> dict[str, object]:
    return {spec.event_type: spec.to_dict() for spec in specs}


def jsonl_message_field_specs_to_dict(
    specs: tuple[SdkJsonlMessageFieldSpec, ...],
) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def jsonl_message_specs_to_dict(specs: tuple[SdkJsonlMessageSpec, ...]) -> dict[str, object]:
    return {spec.message_type: spec.to_dict() for spec in specs}


def result_field_specs_to_dict(specs: tuple[SdkResultFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def result_specs_to_dict(specs: tuple[SdkResultSpec, ...]) -> dict[str, object]:
    return {spec.method: spec.to_dict() for spec in specs}


def type_field_specs_to_dict(specs: tuple[SdkTypeFieldSpec, ...]) -> dict[str, object]:
    return {spec.name: spec.to_dict() for spec in specs}


def type_specs_to_dict(specs: tuple[SdkTypeSpec, ...]) -> dict[str, object]:
    return {spec.type_name: spec.to_dict() for spec in specs}


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "JSONL_CALL_METHODS",
    "JSONL_CALL_METHOD_SPECS",
    "JSONL_CALL_RESULT_SPECS",
    "JSONL_ERROR_CODES",
    "JSONL_ERROR_SPECS",
    "JSONL_MESSAGE_SPECS",
    "JSONL_MESSAGE_TYPES",
    "JSONL_OPERATION_STREAM_METHODS",
    "JSONL_STREAM_METHODS",
    "JSONL_STREAM_METHOD_SPECS",
    "RUNTIME_STATE_FIELDS",
    "RUNTIME_STATE_FIELD_SPECS",
    "SDK_CAPABILITIES_VERSION",
    "SDK_EVENT_SPECS",
    "SDK_EVENT_TYPES",
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "SDK_TYPE_SPECS",
    "SERVICE_CALL_METHODS",
    "SERVICE_CALL_METHOD_SPECS",
    "SERVICE_CALL_RESULT_SPECS",
    "SERVICE_STATE_FIELDS",
    "SERVICE_STATE_FIELD_SPECS",
    "SERVICE_STREAM_METHODS",
    "SERVICE_STREAM_METHOD_SPECS",
    "SESSION_STATE_FIELDS",
    "SESSION_STATE_FIELD_SPECS",
    "SdkErrorSpec",
    "SdkEventFieldSpec",
    "SdkEventSpec",
    "SdkFieldSpec",
    "SdkJsonlMessageFieldSpec",
    "SdkJsonlMessageSpec",
    "SdkMethodParameter",
    "SdkMethodSpec",
    "SdkResultFieldSpec",
    "SdkResultSpec",
    "SdkTypeFieldSpec",
    "SdkTypeSpec",
    "error_specs_to_dict",
    "event_field_specs_to_dict",
    "event_specs_to_dict",
    "field_specs_to_dict",
    "jsonl_message_field_specs_to_dict",
    "jsonl_message_specs_to_dict",
    "method_specs_to_dict",
    "result_field_specs_to_dict",
    "result_specs_to_dict",
    "service_stream_method_for_jsonl",
    "type_field_specs_to_dict",
    "type_specs_to_dict",
]
