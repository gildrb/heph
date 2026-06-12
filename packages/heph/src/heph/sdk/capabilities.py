"""SDK capability discovery contracts."""

from __future__ import annotations

from dataclasses import dataclass

SDK_CAPABILITIES_VERSION = 2
SDK_JSONL_PROTOCOL = "heph-sdk-jsonl"
SDK_JSONL_VERSION = 1

SERVICE_CALL_METHODS = (
    "state",
    "capabilities",
    "use_plain_runtime",
    "open_armory",
    "create_armory",
    "list_armories",
    "new_session",
    "resume_session",
    "fork_session",
    "list_sessions",
    "save_session",
    "messages",
    "ask",
    "abort",
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
SERVICE_STATE_FIELDS = ("prompt_active", "active_operation")
RUNTIME_STATE_FIELDS = (
    "armory_path",
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
    "model",
    "is_streaming",
    "source_file_count",
    "source_files",
    "disabled_source_files",
    "enabled_source_files",
    "has_unsaved_changes",
    "messages",
)


@dataclass(frozen=True, slots=True)
class HephSdkCapabilities:
    """JSON-ready SDK feature contract for direct and transport clients."""

    version: int
    service_call_methods: tuple[str, ...]
    service_stream_methods: tuple[str, ...]
    jsonl_call_methods: tuple[str, ...]
    jsonl_stream_methods: tuple[str, ...]
    busy_allowed_call_methods: tuple[str, ...]
    event_types: tuple[str, ...]
    service_state_fields: tuple[str, ...]
    runtime_state_fields: tuple[str, ...]
    session_state_fields: tuple[str, ...]
    jsonl_protocol: str
    jsonl_version: int
    jsonl_message_types: tuple[str, ...]
    jsonl_error_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "service": {
                "call_methods": list(self.service_call_methods),
                "stream_methods": list(self.service_stream_methods),
                "busy_allowed_call_methods": list(self.busy_allowed_call_methods),
            },
            "jsonl": {
                "protocol": self.jsonl_protocol,
                "version": self.jsonl_version,
                "call_methods": list(self.jsonl_call_methods),
                "stream_methods": list(self.jsonl_stream_methods),
                "message_types": list(self.jsonl_message_types),
                "error_codes": list(self.jsonl_error_codes),
            },
            "events": {"types": list(self.event_types)},
            "state": {
                "service_fields": list(self.service_state_fields),
                "runtime_fields": list(self.runtime_state_fields),
                "session_fields": list(self.session_state_fields),
            },
        }


SDK_CAPABILITIES = HephSdkCapabilities(
    version=SDK_CAPABILITIES_VERSION,
    service_call_methods=SERVICE_CALL_METHODS,
    service_stream_methods=SERVICE_STREAM_METHODS,
    jsonl_call_methods=JSONL_CALL_METHODS,
    jsonl_stream_methods=JSONL_STREAM_METHODS,
    busy_allowed_call_methods=BUSY_ALLOWED_CALL_METHODS,
    event_types=SDK_EVENT_TYPES,
    service_state_fields=SERVICE_STATE_FIELDS,
    runtime_state_fields=RUNTIME_STATE_FIELDS,
    session_state_fields=SESSION_STATE_FIELDS,
    jsonl_protocol=SDK_JSONL_PROTOCOL,
    jsonl_version=SDK_JSONL_VERSION,
    jsonl_message_types=JSONL_MESSAGE_TYPES,
    jsonl_error_codes=JSONL_ERROR_CODES,
)


def get_sdk_capabilities() -> HephSdkCapabilities:
    return SDK_CAPABILITIES


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "JSONL_CALL_METHODS",
    "JSONL_ERROR_CODES",
    "JSONL_MESSAGE_TYPES",
    "JSONL_STREAM_METHODS",
    "RUNTIME_STATE_FIELDS",
    "SDK_CAPABILITIES",
    "SDK_CAPABILITIES_VERSION",
    "SDK_EVENT_TYPES",
    "SDK_JSONL_PROTOCOL",
    "SDK_JSONL_VERSION",
    "SERVICE_CALL_METHODS",
    "SERVICE_STATE_FIELDS",
    "SERVICE_STREAM_METHODS",
    "SESSION_STATE_FIELDS",
    "HephSdkCapabilities",
    "get_sdk_capabilities",
]
