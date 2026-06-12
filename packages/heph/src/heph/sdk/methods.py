"""SDK method and wire-contract names shared by services and transports."""

from __future__ import annotations

SDK_CAPABILITIES_VERSION = 7
SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1

SERVICE_CALL_METHODS = (
    "state",
    "capabilities",
    "use_plain_runtime",
    "open_armory",
    "create_armory",
    "list_armories",
    "validate_armory",
    "new_session",
    "resume_session",
    "fork_session",
    "list_sessions",
    "save_session",
    "messages",
    "ask",
    "abort",
    "list_providers",
    "list_model_choices",
    "switch_model",
    "set_source_enabled",
    "list_materials",
    "import_materials",
    "build_index",
    "scan_extraction_health",
    "update_config",
)
SERVICE_STREAM_METHODS = ("prompt", "build_index")
JSONL_CALL_METHODS = SERVICE_CALL_METHODS
JSONL_STREAM_METHODS = ("prompt", "build_index_stream")
JSONL_OPERATION_STREAM_METHODS = {"build_index_stream": "build_index"}
JSONL_MESSAGE_TYPES = (
    "ready",
    "response",
    "error",
    "stream_start",
    "stream_event",
    "stream_end",
)
JSONL_ERROR_CODES = (
    "invalid_json",
    "invalid_request",
    "busy",
    "sdk_error",
    "internal_error",
)
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


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "JSONL_CALL_METHODS",
    "JSONL_ERROR_CODES",
    "JSONL_MESSAGE_TYPES",
    "JSONL_OPERATION_STREAM_METHODS",
    "JSONL_STREAM_METHODS",
    "RUNTIME_STATE_FIELDS",
    "SDK_CAPABILITIES_VERSION",
    "SDK_EVENT_TYPES",
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "SERVICE_CALL_METHODS",
    "SERVICE_STATE_FIELDS",
    "SERVICE_STREAM_METHODS",
    "SESSION_STATE_FIELDS",
    "service_stream_method_for_jsonl",
]
