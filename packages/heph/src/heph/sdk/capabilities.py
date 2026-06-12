"""SDK capability discovery contracts."""

from __future__ import annotations

from dataclasses import dataclass

from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    JSONL_CALL_METHOD_SPECS,
    JSONL_CALL_METHODS,
    JSONL_CALL_RESULT_SPECS,
    JSONL_ERROR_CODES,
    JSONL_ERROR_SPECS,
    JSONL_MESSAGE_SPECS,
    JSONL_MESSAGE_TYPES,
    JSONL_REQUEST_SPEC,
    JSONL_STREAM_METHOD_SPECS,
    JSONL_STREAM_METHODS,
    RUNTIME_STATE_FIELD_SPECS,
    RUNTIME_STATE_FIELDS,
    SDK_CAPABILITIES_VERSION,
    SDK_EVENT_SPECS,
    SDK_EVENT_TYPES,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_TYPE_SPECS,
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_METHODS,
    SERVICE_CALL_RESULT_SPECS,
    SERVICE_STATE_FIELD_SPECS,
    SERVICE_STATE_FIELDS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_METHODS,
    SESSION_STATE_FIELD_SPECS,
    SESSION_STATE_FIELDS,
    SdkErrorSpec,
    SdkEventSpec,
    SdkFieldSpec,
    SdkJsonlMessageSpec,
    SdkJsonlRequestSpec,
    SdkMethodSpec,
    SdkResultSpec,
    SdkTypeSpec,
    error_specs_to_dict,
    event_specs_to_dict,
    field_specs_to_dict,
    jsonl_message_specs_to_dict,
    jsonl_request_spec_to_dict,
    method_specs_to_dict,
    result_specs_to_dict,
    type_specs_to_dict,
)

_BUILTIN_TYPES = frozenset(
    {
        "boolean",
        "integer",
        "number",
        "number_or_null",
        "object",
        "string",
        "string_or_integer",
    }
)
_ARRAY_PREFIX = "array<"
_LITERAL_PREFIX = "literal<"


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
    event_specs: tuple[SdkEventSpec, ...]
    jsonl_error_specs: tuple[SdkErrorSpec, ...]
    jsonl_message_specs: tuple[SdkJsonlMessageSpec, ...]
    jsonl_request_spec: SdkJsonlRequestSpec
    service_call_method_specs: tuple[SdkMethodSpec, ...]
    service_stream_method_specs: tuple[SdkMethodSpec, ...]
    jsonl_call_method_specs: tuple[SdkMethodSpec, ...]
    jsonl_stream_method_specs: tuple[SdkMethodSpec, ...]
    service_call_result_specs: tuple[SdkResultSpec, ...]
    jsonl_call_result_specs: tuple[SdkResultSpec, ...]
    service_state_field_specs: tuple[SdkFieldSpec, ...]
    runtime_state_field_specs: tuple[SdkFieldSpec, ...]
    session_state_field_specs: tuple[SdkFieldSpec, ...]
    type_specs: tuple[SdkTypeSpec, ...]

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
                "request_spec": jsonl_request_spec_to_dict(self.jsonl_request_spec),
                "message_types": list(self.jsonl_message_types),
                "message_specs": jsonl_message_specs_to_dict(self.jsonl_message_specs),
                "error_codes": list(self.jsonl_error_codes),
            },
            "events": {
                "types": list(self.event_types),
                "specs": event_specs_to_dict(self.event_specs),
            },
            "state": {
                "service_fields": list(self.service_state_fields),
                "runtime_fields": list(self.runtime_state_fields),
                "session_fields": list(self.session_state_fields),
            },
            "methods": {
                "service_call": method_specs_to_dict(self.service_call_method_specs),
                "service_stream": method_specs_to_dict(self.service_stream_method_specs),
                "jsonl_call": method_specs_to_dict(self.jsonl_call_method_specs),
                "jsonl_stream": method_specs_to_dict(self.jsonl_stream_method_specs),
            },
            "errors": {"jsonl": error_specs_to_dict(self.jsonl_error_specs)},
            "results": {
                "service_call": result_specs_to_dict(self.service_call_result_specs),
                "jsonl_call": result_specs_to_dict(self.jsonl_call_result_specs),
            },
            "fields": {
                "service_state": field_specs_to_dict(self.service_state_field_specs),
                "runtime_state": field_specs_to_dict(self.runtime_state_field_specs),
                "session_state": field_specs_to_dict(self.session_state_field_specs),
            },
            "types": type_specs_to_dict(self.type_specs),
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
    event_specs=SDK_EVENT_SPECS,
    jsonl_error_specs=JSONL_ERROR_SPECS,
    jsonl_message_specs=JSONL_MESSAGE_SPECS,
    jsonl_request_spec=JSONL_REQUEST_SPEC,
    service_call_method_specs=SERVICE_CALL_METHOD_SPECS,
    service_stream_method_specs=SERVICE_STREAM_METHOD_SPECS,
    jsonl_call_method_specs=JSONL_CALL_METHOD_SPECS,
    jsonl_stream_method_specs=JSONL_STREAM_METHOD_SPECS,
    service_call_result_specs=SERVICE_CALL_RESULT_SPECS,
    jsonl_call_result_specs=JSONL_CALL_RESULT_SPECS,
    service_state_field_specs=SERVICE_STATE_FIELD_SPECS,
    runtime_state_field_specs=RUNTIME_STATE_FIELD_SPECS,
    session_state_field_specs=SESSION_STATE_FIELD_SPECS,
    type_specs=SDK_TYPE_SPECS,
)


def get_sdk_capabilities() -> HephSdkCapabilities:
    return SDK_CAPABILITIES


def validate_sdk_capabilities(
    capabilities: HephSdkCapabilities = SDK_CAPABILITIES,
) -> tuple[str, ...]:
    """Return human-readable SDK capability contract issues."""
    issues: list[str] = []
    _append_duplicate_issue(issues, "service.call_methods", capabilities.service_call_methods)
    _append_duplicate_issue(issues, "service.stream_methods", capabilities.service_stream_methods)
    _append_duplicate_issue(issues, "jsonl.call_methods", capabilities.jsonl_call_methods)
    _append_duplicate_issue(issues, "jsonl.stream_methods", capabilities.jsonl_stream_methods)
    _append_duplicate_issue(
        issues,
        "jsonl.request_spec.fields",
        tuple(field.name for field in capabilities.jsonl_request_spec.fields),
    )
    _append_duplicate_issue(issues, "jsonl.message_types", capabilities.jsonl_message_types)
    _append_duplicate_issue(issues, "events.types", capabilities.event_types)
    _append_duplicate_issue(issues, "jsonl.error_codes", capabilities.jsonl_error_codes)
    _append_duplicate_issue(
        issues,
        "service.busy_allowed_call_methods",
        capabilities.busy_allowed_call_methods,
    )
    _append_duplicate_issue(
        issues,
        "types",
        tuple(spec.type_name for spec in capabilities.type_specs),
    )
    _append_mismatch_issue(
        issues,
        "service.call_methods",
        capabilities.service_call_methods,
        tuple(spec.method for spec in capabilities.service_call_method_specs),
    )
    _append_mismatch_issue(
        issues,
        "service.stream_methods",
        capabilities.service_stream_methods,
        tuple(spec.method for spec in capabilities.service_stream_method_specs),
    )
    _append_mismatch_issue(
        issues,
        "jsonl.call_methods",
        capabilities.jsonl_call_methods,
        tuple(spec.method for spec in capabilities.jsonl_call_method_specs),
    )
    _append_mismatch_issue(
        issues,
        "jsonl.stream_methods",
        capabilities.jsonl_stream_methods,
        tuple(spec.method for spec in capabilities.jsonl_stream_method_specs),
    )
    _append_mismatch_issue(
        issues,
        "results.service_call",
        capabilities.service_call_methods,
        tuple(spec.method for spec in capabilities.service_call_result_specs),
    )
    _append_mismatch_issue(
        issues,
        "results.jsonl_call",
        capabilities.jsonl_call_methods,
        tuple(spec.method for spec in capabilities.jsonl_call_result_specs),
    )
    _append_mismatch_issue(
        issues,
        "events.types",
        capabilities.event_types,
        tuple(spec.event_type for spec in capabilities.event_specs),
    )
    _append_mismatch_issue(
        issues,
        "jsonl.message_types",
        capabilities.jsonl_message_types,
        tuple(spec.message_type for spec in capabilities.jsonl_message_specs),
    )
    _append_mismatch_issue(
        issues,
        "state.service_fields",
        capabilities.service_state_fields,
        tuple(spec.name for spec in capabilities.service_state_field_specs),
    )
    _append_mismatch_issue(
        issues,
        "state.runtime_fields",
        capabilities.runtime_state_fields,
        tuple(spec.name for spec in capabilities.runtime_state_field_specs),
    )
    _append_mismatch_issue(
        issues,
        "state.session_fields",
        capabilities.session_state_fields,
        tuple(spec.name for spec in capabilities.session_state_field_specs),
    )
    _append_mismatch_issue(
        issues,
        "jsonl.error_codes",
        capabilities.jsonl_error_codes,
        tuple(spec.code for spec in capabilities.jsonl_error_specs),
    )
    _append_subset_issue(
        issues,
        "service.busy_allowed_call_methods",
        capabilities.busy_allowed_call_methods,
        capabilities.service_call_methods,
    )
    _append_unknown_type_issues(issues, capabilities)
    return tuple(issues)


def _append_duplicate_issue(issues: list[str], label: str, names: tuple[str, ...]) -> None:
    duplicates = _duplicates(names)
    if duplicates:
        issues.append(f"{label} contains duplicate entries: {', '.join(duplicates)}")


def _append_mismatch_issue(
    issues: list[str],
    label: str,
    advertised: tuple[str, ...],
    structured: tuple[str, ...],
) -> None:
    if advertised != structured:
        issues.append(f"{label} does not match its structured specs.")


def _append_subset_issue(
    issues: list[str],
    label: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> None:
    allowed = frozenset(allowed_values)
    unknown = tuple(value for value in values if value not in allowed)
    if unknown:
        issues.append(
            f"{label} contains entries that are not advertised calls: {', '.join(unknown)}"
        )


def _duplicates(names: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    duplicate_set: set[str] = set()
    for name in names:
        if name in seen and name not in duplicate_set:
            duplicates.append(name)
            duplicate_set.add(name)
        seen.add(name)
    return tuple(duplicates)


def _append_unknown_type_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    known_types = frozenset(spec.type_name for spec in capabilities.type_specs)
    issues.extend(
        f"{context} references unknown SDK type: {type_name}"
        for context, value_type in _referenced_value_types(capabilities)
        for type_name in _custom_type_references(value_type)
        if type_name not in known_types
    )


def _referenced_value_types(capabilities: HephSdkCapabilities) -> tuple[tuple[str, str], ...]:
    references: list[tuple[str, str]] = []
    for spec in capabilities.service_call_method_specs:
        references.extend(
            (f"methods.service_call.{spec.method}.{param.name}", param.value_type)
            for param in spec.params
        )
    for spec in capabilities.service_stream_method_specs:
        references.extend(
            (f"methods.service_stream.{spec.method}.{param.name}", param.value_type)
            for param in spec.params
        )
    for spec in capabilities.jsonl_call_method_specs:
        references.extend(
            (f"methods.jsonl_call.{spec.method}.{param.name}", param.value_type)
            for param in spec.params
        )
    for spec in capabilities.jsonl_stream_method_specs:
        references.extend(
            (f"methods.jsonl_stream.{spec.method}.{param.name}", param.value_type)
            for param in spec.params
        )
    references.extend(
        (f"fields.service_state.{spec.name}", spec.value_type)
        for spec in capabilities.service_state_field_specs
    )
    references.extend(
        (f"fields.runtime_state.{spec.name}", spec.value_type)
        for spec in capabilities.runtime_state_field_specs
    )
    references.extend(
        (f"fields.session_state.{spec.name}", spec.value_type)
        for spec in capabilities.session_state_field_specs
    )
    for spec in capabilities.event_specs:
        references.extend(
            (f"events.{spec.event_type}.{field.name}", field.value_type) for field in spec.fields
        )
    references.extend(
        (f"jsonl.request_spec.{field.name}", field.value_type)
        for field in capabilities.jsonl_request_spec.fields
    )
    for spec in capabilities.jsonl_message_specs:
        references.extend(
            (f"jsonl.message_specs.{spec.message_type}.{field.name}", field.value_type)
            for field in spec.fields
        )
    for spec in capabilities.service_call_result_specs:
        references.append((f"results.service_call.{spec.method}", spec.value_type))
        references.extend(
            (f"results.service_call.{spec.method}.{field.name}", field.value_type)
            for field in spec.fields
        )
    for spec in capabilities.jsonl_call_result_specs:
        references.append((f"results.jsonl_call.{spec.method}", spec.value_type))
        references.extend(
            (f"results.jsonl_call.{spec.method}.{field.name}", field.value_type)
            for field in spec.fields
        )
    for spec in capabilities.type_specs:
        references.extend(
            (f"types.{spec.type_name}.{field.name}", field.value_type) for field in spec.fields
        )
    return tuple(references)


def _custom_type_references(value_type: str) -> tuple[str, ...]:
    if value_type in _BUILTIN_TYPES:
        return ()
    if value_type.startswith(_LITERAL_PREFIX) and value_type.endswith(">"):
        return ()
    if value_type.startswith(_ARRAY_PREFIX) and value_type.endswith(">"):
        inner_type = value_type.removeprefix(_ARRAY_PREFIX).removesuffix(">")
        return _custom_type_references(inner_type)
    return (value_type,)


__all__ = [
    "BUSY_ALLOWED_CALL_METHODS",
    "JSONL_CALL_METHODS",
    "JSONL_CALL_METHOD_SPECS",
    "JSONL_CALL_RESULT_SPECS",
    "JSONL_ERROR_CODES",
    "JSONL_ERROR_SPECS",
    "JSONL_MESSAGE_SPECS",
    "JSONL_MESSAGE_TYPES",
    "JSONL_REQUEST_SPEC",
    "JSONL_STREAM_METHODS",
    "JSONL_STREAM_METHOD_SPECS",
    "RUNTIME_STATE_FIELDS",
    "RUNTIME_STATE_FIELD_SPECS",
    "SDK_CAPABILITIES",
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
    "HephSdkCapabilities",
    "get_sdk_capabilities",
    "validate_sdk_capabilities",
]
