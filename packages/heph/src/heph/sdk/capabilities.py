"""SDK capability discovery contracts."""

from __future__ import annotations

from dataclasses import dataclass

from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    JSONL_CALL_METHOD_AVAILABILITY_SPECS,
    JSONL_CALL_METHOD_SPECS,
    JSONL_CALL_METHODS,
    JSONL_CALL_RESULT_SPECS,
    JSONL_ERROR_CODES,
    JSONL_ERROR_SPECS,
    JSONL_MESSAGE_SPECS,
    JSONL_MESSAGE_TYPES,
    JSONL_REQUEST_SPEC,
    JSONL_STREAM_METHOD_AVAILABILITY_SPECS,
    JSONL_STREAM_METHOD_SPECS,
    JSONL_STREAM_METHODS,
    JSONL_STREAM_SPECS,
    RUNTIME_STATE_FIELD_SPECS,
    RUNTIME_STATE_FIELDS,
    SDK_CAPABILITIES_VERSION,
    SDK_COMPATIBILITY_POLICY,
    SDK_DEPRECATION_SPECS,
    SDK_DEPRECATION_SURFACES,
    SDK_EVENT_SPECS,
    SDK_EVENT_TYPES,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_METHOD_AVAILABILITY_REQUIREMENTS,
    SDK_METHOD_REQUIREMENT_ALWAYS,
    SDK_METHOD_UNAVAILABLE_REASONS,
    SDK_STABILITY_LEVELS,
    SDK_TYPE_SPECS,
    SDK_VALUE_TYPE_SPECS,
    SERVICE_CALL_METHOD_AVAILABILITY_SPECS,
    SERVICE_CALL_METHOD_SPECS,
    SERVICE_CALL_METHODS,
    SERVICE_CALL_RESULT_SPECS,
    SERVICE_STATE_FIELD_SPECS,
    SERVICE_STATE_FIELDS,
    SERVICE_STREAM_METHOD_AVAILABILITY_SPECS,
    SERVICE_STREAM_METHOD_SPECS,
    SERVICE_STREAM_METHODS,
    SERVICE_STREAM_SPECS,
    SESSION_STATE_FIELD_SPECS,
    SESSION_STATE_FIELDS,
    SdkCompatibilityPolicy,
    SdkDeprecationSpec,
    SdkErrorSpec,
    SdkEventSpec,
    SdkFieldSpec,
    SdkJsonlMessageSpec,
    SdkJsonlRequestSpec,
    SdkMethodAvailabilitySpec,
    SdkMethodParameter,
    SdkMethodSpec,
    SdkObjectFieldSpec,
    SdkResultSpec,
    SdkStreamSpec,
    SdkTypeSpec,
    SdkValueTypeSpec,
    deprecation_specs_to_list,
    error_specs_to_dict,
    event_specs_to_dict,
    field_specs_to_dict,
    jsonl_message_specs_to_dict,
    jsonl_request_spec_to_dict,
    method_availability_specs_to_dict,
    method_specs_to_dict,
    result_specs_to_dict,
    stream_specs_to_dict,
    type_specs_to_dict,
    value_type_specs_to_dict,
)
from heph.sdk.value_types import (
    sdk_custom_type_references,
    sdk_json_object_is_safe,
    sdk_value_type_shape_issue,
)

_JSONL_REQUEST_ENVELOPE_FIELDS = (
    SdkObjectFieldSpec("id", "string_or_integer", required=False, nullable=True),
    SdkObjectFieldSpec("method", "string"),
    SdkObjectFieldSpec("params", "object", required=False, nullable=True),
)


@dataclass(frozen=True, slots=True)
class _DuplicateCheck:
    label: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _MismatchCheck:
    label: str
    advertised: tuple[str, ...]
    structured: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _AvailabilitySpecReference:
    context: str
    spec: SdkMethodAvailabilitySpec


@dataclass(frozen=True, slots=True)
class _StreamSpecReference:
    context: str
    spec: SdkStreamSpec


@dataclass(frozen=True, slots=True)
class _ValueTypeReference:
    context: str
    value_type: str


@dataclass(frozen=True, slots=True)
class HephSdkCapabilities:
    """JSON-ready SDK feature contract for direct and transport clients."""

    version: int
    compatibility: SdkCompatibilityPolicy
    deprecation_specs: tuple[SdkDeprecationSpec, ...]
    service_call_methods: tuple[str, ...]
    service_stream_methods: tuple[str, ...]
    jsonl_call_methods: tuple[str, ...]
    jsonl_stream_methods: tuple[str, ...]
    busy_allowed_call_methods: tuple[str, ...]
    method_unavailable_reasons: tuple[str, ...]
    method_availability_requirements: tuple[str, ...]
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
    service_call_method_availability_specs: tuple[SdkMethodAvailabilitySpec, ...]
    service_stream_method_availability_specs: tuple[SdkMethodAvailabilitySpec, ...]
    jsonl_call_method_availability_specs: tuple[SdkMethodAvailabilitySpec, ...]
    jsonl_stream_method_availability_specs: tuple[SdkMethodAvailabilitySpec, ...]
    service_call_result_specs: tuple[SdkResultSpec, ...]
    jsonl_call_result_specs: tuple[SdkResultSpec, ...]
    service_stream_specs: tuple[SdkStreamSpec, ...]
    jsonl_stream_specs: tuple[SdkStreamSpec, ...]
    service_state_field_specs: tuple[SdkFieldSpec, ...]
    runtime_state_field_specs: tuple[SdkFieldSpec, ...]
    session_state_field_specs: tuple[SdkFieldSpec, ...]
    type_specs: tuple[SdkTypeSpec, ...]
    value_type_specs: tuple[SdkValueTypeSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "compatibility": self.compatibility.to_dict(),
            "deprecations": deprecation_specs_to_list(self.deprecation_specs),
            "service": {
                "call_methods": list(self.service_call_methods),
                "stream_methods": list(self.service_stream_methods),
                "busy_allowed_call_methods": list(self.busy_allowed_call_methods),
                "method_unavailable_reasons": list(self.method_unavailable_reasons),
            },
            "jsonl": {
                "protocol": self.jsonl_protocol,
                "version": self.jsonl_version,
                "call_methods": list(self.jsonl_call_methods),
                "stream_methods": list(self.jsonl_stream_methods),
                "busy_allowed_call_methods": list(self.busy_allowed_call_methods),
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
            "availability": {
                "requirements": list(self.method_availability_requirements),
                "service_call": method_availability_specs_to_dict(
                    self.service_call_method_availability_specs
                ),
                "service_stream": method_availability_specs_to_dict(
                    self.service_stream_method_availability_specs
                ),
                "jsonl_call": method_availability_specs_to_dict(
                    self.jsonl_call_method_availability_specs
                ),
                "jsonl_stream": method_availability_specs_to_dict(
                    self.jsonl_stream_method_availability_specs
                ),
            },
            "errors": {"jsonl": error_specs_to_dict(self.jsonl_error_specs)},
            "results": {
                "service_call": result_specs_to_dict(self.service_call_result_specs),
                "jsonl_call": result_specs_to_dict(self.jsonl_call_result_specs),
            },
            "streams": {
                "service": stream_specs_to_dict(self.service_stream_specs),
                "jsonl": stream_specs_to_dict(self.jsonl_stream_specs),
            },
            "fields": {
                "service_state": field_specs_to_dict(self.service_state_field_specs),
                "runtime_state": field_specs_to_dict(self.runtime_state_field_specs),
                "session_state": field_specs_to_dict(self.session_state_field_specs),
            },
            "types": type_specs_to_dict(self.type_specs),
            "value_types": value_type_specs_to_dict(self.value_type_specs),
        }


SDK_CAPABILITIES = HephSdkCapabilities(
    version=SDK_CAPABILITIES_VERSION,
    compatibility=SDK_COMPATIBILITY_POLICY,
    deprecation_specs=SDK_DEPRECATION_SPECS,
    service_call_methods=SERVICE_CALL_METHODS,
    service_stream_methods=SERVICE_STREAM_METHODS,
    jsonl_call_methods=JSONL_CALL_METHODS,
    jsonl_stream_methods=JSONL_STREAM_METHODS,
    busy_allowed_call_methods=BUSY_ALLOWED_CALL_METHODS,
    method_unavailable_reasons=SDK_METHOD_UNAVAILABLE_REASONS,
    method_availability_requirements=SDK_METHOD_AVAILABILITY_REQUIREMENTS,
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
    service_call_method_availability_specs=SERVICE_CALL_METHOD_AVAILABILITY_SPECS,
    service_stream_method_availability_specs=SERVICE_STREAM_METHOD_AVAILABILITY_SPECS,
    jsonl_call_method_availability_specs=JSONL_CALL_METHOD_AVAILABILITY_SPECS,
    jsonl_stream_method_availability_specs=JSONL_STREAM_METHOD_AVAILABILITY_SPECS,
    service_call_result_specs=SERVICE_CALL_RESULT_SPECS,
    jsonl_call_result_specs=JSONL_CALL_RESULT_SPECS,
    service_stream_specs=SERVICE_STREAM_SPECS,
    jsonl_stream_specs=JSONL_STREAM_SPECS,
    service_state_field_specs=SERVICE_STATE_FIELD_SPECS,
    runtime_state_field_specs=RUNTIME_STATE_FIELD_SPECS,
    session_state_field_specs=SESSION_STATE_FIELD_SPECS,
    type_specs=SDK_TYPE_SPECS,
    value_type_specs=SDK_VALUE_TYPE_SPECS,
)


def get_sdk_capabilities() -> HephSdkCapabilities:
    return SDK_CAPABILITIES


def validate_sdk_capabilities(
    capabilities: HephSdkCapabilities = SDK_CAPABILITIES,
) -> tuple[str, ...]:
    """Return human-readable SDK capability contract issues."""
    issues: list[str] = []
    for check in _duplicate_checks(capabilities):
        _append_duplicate_issue(issues, check.label, check.names)
    for check in _mismatch_checks(capabilities):
        _append_mismatch_issue(issues, check.label, check.advertised, check.structured)
    _append_subset_issue(
        issues,
        "service.busy_allowed_call_methods",
        capabilities.busy_allowed_call_methods,
        capabilities.service_call_methods,
    )
    _append_subset_issue(
        issues,
        "jsonl.busy_allowed_call_methods",
        capabilities.busy_allowed_call_methods,
        capabilities.jsonl_call_methods,
    )
    _append_compatibility_issues(issues, capabilities)
    _append_deprecation_issues(issues, capabilities)
    _append_parameter_choice_issues(issues, capabilities)
    _append_availability_issues(issues, capabilities)
    _append_value_type_shape_issues(issues, capabilities)
    _append_unknown_type_issues(issues, capabilities)
    _append_stream_event_issues(issues, capabilities)
    _append_discriminator_issues(issues, capabilities)
    _append_jsonl_request_envelope_issues(issues, capabilities)
    _append_payload_json_safety_issue(issues, capabilities)
    return tuple(issues)


def _duplicate_checks(capabilities: HephSdkCapabilities) -> tuple[_DuplicateCheck, ...]:
    return (
        *_method_name_duplicate_checks(capabilities),
        *_jsonl_contract_duplicate_checks(capabilities),
        *_availability_duplicate_checks(capabilities),
        _DuplicateCheck("types", _type_names(capabilities.type_specs)),
        _DuplicateCheck("value_types", _value_type_names(capabilities.value_type_specs)),
        _DuplicateCheck("deprecations", _deprecation_keys(capabilities.deprecation_specs)),
        *_method_param_duplicate_checks(
            "methods.service_call",
            capabilities.service_call_method_specs,
        ),
        *_method_param_duplicate_checks(
            "methods.service_stream",
            capabilities.service_stream_method_specs,
        ),
        *_method_param_duplicate_checks(
            "methods.jsonl_call",
            capabilities.jsonl_call_method_specs,
        ),
        *_method_param_duplicate_checks(
            "methods.jsonl_stream",
            capabilities.jsonl_stream_method_specs,
        ),
        *_event_field_duplicate_checks(capabilities.event_specs),
        *_jsonl_message_field_duplicate_checks(capabilities.jsonl_message_specs),
        *_result_field_duplicate_checks(
            "results.service_call",
            capabilities.service_call_result_specs,
        ),
        *_result_field_duplicate_checks(
            "results.jsonl_call",
            capabilities.jsonl_call_result_specs,
        ),
        *_state_field_duplicate_checks(capabilities),
        *_type_field_duplicate_checks(capabilities.type_specs),
    )


def _method_name_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        _DuplicateCheck("service.call_methods", capabilities.service_call_methods),
        _DuplicateCheck("service.stream_methods", capabilities.service_stream_methods),
        _DuplicateCheck("jsonl.call_methods", capabilities.jsonl_call_methods),
        _DuplicateCheck("jsonl.stream_methods", capabilities.jsonl_stream_methods),
    )


def _jsonl_contract_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        _DuplicateCheck("jsonl.request_spec.fields", _jsonl_request_field_names(capabilities)),
        _DuplicateCheck("jsonl.message_types", capabilities.jsonl_message_types),
        _DuplicateCheck("events.types", capabilities.event_types),
        _DuplicateCheck("jsonl.error_codes", capabilities.jsonl_error_codes),
        _DuplicateCheck(
            "service.busy_allowed_call_methods",
            capabilities.busy_allowed_call_methods,
        ),
        _DuplicateCheck(
            "jsonl.busy_allowed_call_methods",
            capabilities.busy_allowed_call_methods,
        ),
        _DuplicateCheck(
            "service.method_unavailable_reasons",
            capabilities.method_unavailable_reasons,
        ),
    )


def _availability_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        _DuplicateCheck(
            "availability.requirements", capabilities.method_availability_requirements
        ),
        _DuplicateCheck(
            "availability.service_call",
            _availability_method_names(capabilities.service_call_method_availability_specs),
        ),
        _DuplicateCheck(
            "availability.service_stream",
            _availability_method_names(capabilities.service_stream_method_availability_specs),
        ),
        _DuplicateCheck(
            "availability.jsonl_call",
            _availability_method_names(capabilities.jsonl_call_method_availability_specs),
        ),
        _DuplicateCheck(
            "availability.jsonl_stream",
            _availability_method_names(capabilities.jsonl_stream_method_availability_specs),
        ),
    )


def _state_field_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        _DuplicateCheck(
            "fields.service_state", _field_names(capabilities.service_state_field_specs)
        ),
        _DuplicateCheck(
            "fields.runtime_state", _field_names(capabilities.runtime_state_field_specs)
        ),
        _DuplicateCheck(
            "fields.session_state", _field_names(capabilities.session_state_field_specs)
        ),
    )


def _jsonl_request_field_names(capabilities: HephSdkCapabilities) -> tuple[str, ...]:
    return tuple(field.name for field in capabilities.jsonl_request_spec.fields)


def _availability_method_names(
    specs: tuple[SdkMethodAvailabilitySpec, ...],
) -> tuple[str, ...]:
    return tuple(spec.method for spec in specs)


def _field_names(specs: tuple[SdkFieldSpec, ...]) -> tuple[str, ...]:
    return tuple(spec.name for spec in specs)


def _type_names(specs: tuple[SdkTypeSpec, ...]) -> tuple[str, ...]:
    return tuple(spec.type_name for spec in specs)


def _value_type_names(specs: tuple[SdkValueTypeSpec, ...]) -> tuple[str, ...]:
    return tuple(spec.name for spec in specs)


def _deprecation_keys(specs: tuple[SdkDeprecationSpec, ...]) -> tuple[str, ...]:
    return tuple(f"{spec.surface}:{spec.name}" for spec in specs)


def _method_param_duplicate_checks(
    context: str,
    specs: tuple[SdkMethodSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        _DuplicateCheck(
            f"{context}.{spec.method}.params",
            tuple(param.name for param in spec.params),
        )
        for spec in specs
    )


def _event_field_duplicate_checks(
    specs: tuple[SdkEventSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        _DuplicateCheck(
            f"events.{spec.event_type}.fields",
            tuple(field.name for field in spec.fields),
        )
        for spec in specs
    )


def _jsonl_message_field_duplicate_checks(
    specs: tuple[SdkJsonlMessageSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        _DuplicateCheck(
            f"jsonl.message_specs.{spec.message_type}.fields",
            tuple(field.name for field in spec.fields),
        )
        for spec in specs
    )


def _result_field_duplicate_checks(
    context: str,
    specs: tuple[SdkResultSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        _DuplicateCheck(
            f"{context}.{spec.method}.fields",
            tuple(field.name for field in spec.fields),
        )
        for spec in specs
    )


def _type_field_duplicate_checks(
    specs: tuple[SdkTypeSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        _DuplicateCheck(
            f"types.{spec.type_name}.fields",
            tuple(field.name for field in spec.fields),
        )
        for spec in specs
    )


def _mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        *_method_mismatch_checks(capabilities),
        *_result_mismatch_checks(capabilities),
        *_stream_mismatch_checks(capabilities),
        *_availability_mismatch_checks(capabilities),
        *_event_mismatch_checks(capabilities),
        *_state_mismatch_checks(capabilities),
        *_error_mismatch_checks(capabilities),
    )


def _method_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "service.call_methods",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_method_specs),
        ),
        _MismatchCheck(
            "service.stream_methods",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_method_specs),
        ),
        _MismatchCheck(
            "jsonl.call_methods",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_method_specs),
        ),
        _MismatchCheck(
            "jsonl.stream_methods",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_method_specs),
        ),
    )


def _result_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "results.service_call",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_result_specs),
        ),
        _MismatchCheck(
            "results.jsonl_call",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_result_specs),
        ),
    )


def _stream_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "streams.service",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_specs),
        ),
        _MismatchCheck(
            "streams.jsonl",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_specs),
        ),
    )


def _availability_mismatch_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "availability.service_call",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_method_availability_specs),
        ),
        _MismatchCheck(
            "availability.service_stream",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_method_availability_specs),
        ),
        _MismatchCheck(
            "availability.jsonl_call",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_method_availability_specs),
        ),
        _MismatchCheck(
            "availability.jsonl_stream",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_method_availability_specs),
        ),
    )


def _event_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "events.types",
            capabilities.event_types,
            tuple(spec.event_type for spec in capabilities.event_specs),
        ),
        _MismatchCheck(
            "jsonl.message_types",
            capabilities.jsonl_message_types,
            tuple(spec.message_type for spec in capabilities.jsonl_message_specs),
        ),
    )


def _state_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "state.service_fields",
            capabilities.service_state_fields,
            tuple(spec.name for spec in capabilities.service_state_field_specs),
        ),
        _MismatchCheck(
            "state.runtime_fields",
            capabilities.runtime_state_fields,
            tuple(spec.name for spec in capabilities.runtime_state_field_specs),
        ),
        _MismatchCheck(
            "state.session_fields",
            capabilities.session_state_fields,
            tuple(spec.name for spec in capabilities.session_state_field_specs),
        ),
    )


def _error_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        _MismatchCheck(
            "jsonl.error_codes",
            capabilities.jsonl_error_codes,
            tuple(spec.code for spec in capabilities.jsonl_error_specs),
        ),
    )


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


def _append_compatibility_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    policy = capabilities.compatibility
    _append_compatibility_stability_issue(issues, policy)
    _append_compatibility_version_issues(issues, capabilities.version, policy)
    _append_compatibility_jsonl_version_issues(issues, capabilities.jsonl_version, policy)
    _append_compatibility_text_issues(issues, policy)


def _append_compatibility_stability_issue(
    issues: list[str],
    policy: SdkCompatibilityPolicy,
) -> None:
    if policy.stability not in SDK_STABILITY_LEVELS:
        issues.append(f"compatibility.stability is unknown: {policy.stability}")


def _append_compatibility_version_issues(
    issues: list[str],
    capabilities_version: int,
    policy: SdkCompatibilityPolicy,
) -> None:
    if policy.current_capabilities_version != capabilities_version:
        issues.append("compatibility.current_capabilities_version must match version.")
    if policy.min_client_capabilities_version < 1:
        issues.append("compatibility.min_client_capabilities_version must be positive.")
    if policy.min_client_capabilities_version > policy.current_capabilities_version:
        issues.append(
            "compatibility.min_client_capabilities_version must not exceed "
            "current_capabilities_version."
        )


def _append_compatibility_jsonl_version_issues(
    issues: list[str],
    jsonl_version: int,
    policy: SdkCompatibilityPolicy,
) -> None:
    _append_duplicate_issue(
        issues,
        "compatibility.supported_jsonl_versions",
        tuple(str(version) for version in policy.supported_jsonl_versions),
    )
    if jsonl_version not in policy.supported_jsonl_versions:
        issues.append("compatibility.supported_jsonl_versions must include jsonl.version.")
    issues.extend(
        "compatibility.supported_jsonl_versions must be positive."
        for version in policy.supported_jsonl_versions
        if version < 1
    )


def _append_compatibility_text_issues(
    issues: list[str],
    policy: SdkCompatibilityPolicy,
) -> None:
    for field_name, value in (
        ("breaking_change_policy", policy.breaking_change_policy),
        ("additive_change_policy", policy.additive_change_policy),
        ("deprecation_policy", policy.deprecation_policy),
    ):
        if not value.strip():
            issues.append(f"compatibility.{field_name} must not be empty.")


def _append_deprecation_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    for spec in capabilities.deprecation_specs:
        context = f"deprecations.{spec.surface}.{spec.name}"
        _append_deprecation_surface_issue(issues, context, spec)
        _append_deprecation_text_issues(issues, context, spec)
        _append_deprecation_version_issues(issues, context, capabilities.version, spec)


def _append_deprecation_surface_issue(
    issues: list[str],
    context: str,
    spec: SdkDeprecationSpec,
) -> None:
    if spec.surface not in SDK_DEPRECATION_SURFACES:
        issues.append(f"{context} references unknown deprecation surface: {spec.surface}")


def _append_deprecation_text_issues(
    issues: list[str],
    context: str,
    spec: SdkDeprecationSpec,
) -> None:
    if not spec.name.strip():
        issues.append(f"{context} must advertise a deprecated name.")
    if not spec.message.strip():
        issues.append(f"{context} must advertise a deprecation message.")


def _append_deprecation_version_issues(
    issues: list[str],
    context: str,
    capabilities_version: int,
    spec: SdkDeprecationSpec,
) -> None:
    if spec.since_version < 1:
        issues.append(f"{context}.since_version must be positive.")
    if spec.since_version > capabilities_version:
        issues.append(f"{context}.since_version must not exceed version.")
    if spec.removal_version is not None and spec.removal_version <= spec.since_version:
        issues.append(f"{context}.removal_version must be greater than since_version.")


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
    builtin_types = _builtin_value_type_names(capabilities.value_type_specs)
    issues.extend(
        f"{reference.context} references unknown SDK type: {type_name}"
        for reference in _referenced_value_types(capabilities)
        for type_name in sdk_custom_type_references(reference.value_type, builtin_types)
        if type_name not in known_types
    )


def _builtin_value_type_names(specs: tuple[SdkValueTypeSpec, ...]) -> frozenset[str]:
    return frozenset(spec.name for spec in specs if not spec.template)


def _append_value_type_shape_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    for reference in _referenced_value_types(capabilities):
        issue = sdk_value_type_shape_issue(reference.context, reference.value_type)
        if issue is not None:
            issues.append(issue)


def _append_parameter_choice_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    for context, method_specs in (
        ("methods.service_call", capabilities.service_call_method_specs),
        ("methods.service_stream", capabilities.service_stream_method_specs),
        ("methods.jsonl_call", capabilities.jsonl_call_method_specs),
        ("methods.jsonl_stream", capabilities.jsonl_stream_method_specs),
    ):
        for spec in method_specs:
            for param in spec.params:
                if param.choices:
                    choice_context = f"{context}.{spec.method}.{param.name}.choices"
                    _append_duplicate_issue(issues, choice_context, param.choices)
                    _append_parameter_choice_type_issue(issues, choice_context, param)
                    _append_empty_parameter_choice_issue(issues, choice_context, param)


def _append_parameter_choice_type_issue(
    issues: list[str],
    context: str,
    param: SdkMethodParameter,
) -> None:
    if param.value_type != "string":
        issues.append(f"{context} require a string parameter type.")


def _append_empty_parameter_choice_issue(
    issues: list[str],
    context: str,
    param: SdkMethodParameter,
) -> None:
    if "" in param.choices:
        issues.append(f"{context} must not include empty values.")


def _append_availability_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    known_requirements = frozenset(capabilities.method_availability_requirements)
    known_reasons = frozenset(capabilities.method_unavailable_reasons)
    for reference in _availability_spec_references(capabilities):
        _append_unknown_availability_requirement_issue(
            issues,
            reference.context,
            reference.spec,
            known_requirements,
        )
        _append_unknown_unavailable_reason_issue(
            issues,
            reference.context,
            reference.spec,
            known_reasons,
        )
        _append_availability_reason_shape_issue(issues, reference.context, reference.spec)


def _availability_spec_references(
    capabilities: HephSdkCapabilities,
) -> tuple[_AvailabilitySpecReference, ...]:
    return (
        *(
            _AvailabilitySpecReference(f"availability.service_call.{spec.method}", spec)
            for spec in capabilities.service_call_method_availability_specs
        ),
        *(
            _AvailabilitySpecReference(f"availability.service_stream.{spec.method}", spec)
            for spec in capabilities.service_stream_method_availability_specs
        ),
        *(
            _AvailabilitySpecReference(f"availability.jsonl_call.{spec.method}", spec)
            for spec in capabilities.jsonl_call_method_availability_specs
        ),
        *(
            _AvailabilitySpecReference(f"availability.jsonl_stream.{spec.method}", spec)
            for spec in capabilities.jsonl_stream_method_availability_specs
        ),
    )


def _append_unknown_availability_requirement_issue(
    issues: list[str],
    context: str,
    spec: SdkMethodAvailabilitySpec,
    known_requirements: frozenset[str],
) -> None:
    if spec.requirement not in known_requirements:
        issues.append(f"{context} references unknown availability requirement: {spec.requirement}")


def _append_unknown_unavailable_reason_issue(
    issues: list[str],
    context: str,
    spec: SdkMethodAvailabilitySpec,
    known_reasons: frozenset[str],
) -> None:
    if spec.unavailable_reason is not None and spec.unavailable_reason not in known_reasons:
        issues.append(
            f"{context} references unknown unavailable reason: {spec.unavailable_reason}"
        )


def _append_availability_reason_shape_issue(
    issues: list[str],
    context: str,
    spec: SdkMethodAvailabilitySpec,
) -> None:
    if spec.requirement == SDK_METHOD_REQUIREMENT_ALWAYS and spec.unavailable_reason is not None:
        issues.append(f"{context} must not advertise an unavailable reason for always.")
    elif spec.requirement != SDK_METHOD_REQUIREMENT_ALWAYS and spec.unavailable_reason is None:
        issues.append(f"{context} must advertise an unavailable reason.")


def _append_stream_event_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    known_events = frozenset(capabilities.event_types)
    for reference in _stream_spec_references(capabilities):
        _append_stream_spec_event_issues(
            issues,
            reference.context,
            reference.spec,
            known_events,
        )


def _stream_spec_references(
    capabilities: HephSdkCapabilities,
) -> tuple[_StreamSpecReference, ...]:
    return (
        *(
            _StreamSpecReference(f"streams.service.{spec.method}", spec)
            for spec in capabilities.service_stream_specs
        ),
        *(
            _StreamSpecReference(f"streams.jsonl.{spec.method}", spec)
            for spec in capabilities.jsonl_stream_specs
        ),
    )


def _append_stream_spec_event_issues(
    issues: list[str],
    context: str,
    spec: SdkStreamSpec,
    known_events: frozenset[str],
) -> None:
    _append_duplicate_issue(issues, f"{context}.event_types", spec.event_types)
    _append_unknown_stream_event_issue(issues, context, spec, known_events)
    _append_unknown_completion_event_issue(issues, context, spec, known_events)


def _append_unknown_stream_event_issue(
    issues: list[str],
    context: str,
    spec: SdkStreamSpec,
    known_events: frozenset[str],
) -> None:
    unknown_events = tuple(
        event_type for event_type in spec.event_types if event_type not in known_events
    )
    if unknown_events:
        issues.append(f"{context} references unknown SDK events: {', '.join(unknown_events)}")


def _append_unknown_completion_event_issue(
    issues: list[str],
    context: str,
    spec: SdkStreamSpec,
    known_events: frozenset[str],
) -> None:
    if spec.completion_event is not None and spec.completion_event not in known_events:
        issues.append(f"{context} completion event is unknown: {spec.completion_event}")


def _append_discriminator_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    for spec in capabilities.event_specs:
        _append_object_discriminator_issues(
            issues,
            f"events.{spec.event_type}",
            spec.event_type,
            spec.fields,
        )
    for spec in capabilities.jsonl_message_specs:
        _append_object_discriminator_issues(
            issues,
            f"jsonl.message_specs.{spec.message_type}",
            spec.message_type,
            spec.fields,
        )


def _append_object_discriminator_issues(
    issues: list[str],
    context: str,
    discriminator_value: str,
    fields: tuple[SdkObjectFieldSpec, ...],
) -> None:
    field = _field_by_name(fields, "type")
    if field is None:
        issues.append(f"{context} must advertise a type discriminator.")
        return
    if not field.required or field.nullable:
        issues.append(f"{context}.type must be required and non-null.")
    expected_type = f"literal<{discriminator_value}>"
    if field.value_type != expected_type:
        issues.append(f"{context}.type must be {expected_type}.")


def _field_by_name(
    fields: tuple[SdkObjectFieldSpec, ...],
    name: str,
) -> SdkObjectFieldSpec | None:
    return next((field for field in fields if field.name == name), None)


def _fields_by_name(fields: tuple[SdkObjectFieldSpec, ...]) -> dict[str, SdkObjectFieldSpec]:
    return {field.name: field for field in fields}


def _append_jsonl_request_envelope_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    fields = capabilities.jsonl_request_spec.fields
    _append_jsonl_request_field_order_issue(issues, fields)
    _append_jsonl_request_field_shape_issues(issues, _fields_by_name(fields))


def _append_jsonl_request_field_order_issue(
    issues: list[str],
    fields: tuple[SdkObjectFieldSpec, ...],
) -> None:
    advertised_names = tuple(field.name for field in fields)
    expected_names = _jsonl_request_envelope_field_names()
    if advertised_names != expected_names:
        issues.append("jsonl.request_spec.fields must be exactly: " + ", ".join(expected_names))


def _append_jsonl_request_field_shape_issues(
    issues: list[str],
    fields_by_name: dict[str, SdkObjectFieldSpec],
) -> None:
    for expected in _JSONL_REQUEST_ENVELOPE_FIELDS:
        field = fields_by_name.get(expected.name)
        if field is not None:
            _append_jsonl_request_field_shape_issue(issues, field, expected)


def _append_jsonl_request_field_shape_issue(
    issues: list[str],
    field: SdkObjectFieldSpec,
    expected: SdkObjectFieldSpec,
) -> None:
    context = f"jsonl.request_spec.{expected.name}"
    if field.value_type != expected.value_type:
        issues.append(f"{context} must be {expected.value_type}.")
    if field.required != expected.required or field.nullable != expected.nullable:
        issues.append(f"{context} must be {_required_nullable_message(expected)}.")


def _jsonl_request_envelope_field_names() -> tuple[str, ...]:
    return tuple(field.name for field in _JSONL_REQUEST_ENVELOPE_FIELDS)


def _required_nullable_message(field: SdkObjectFieldSpec) -> str:
    required = "required" if field.required else "optional"
    nullable = "nullable" if field.nullable else "non-null"
    return f"{required} and {nullable}"


def _append_payload_json_safety_issue(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    if sdk_json_object_is_safe(capabilities.to_dict()):
        return
    issues.append("capabilities payload must use string keys and JSON-safe values.")


def _referenced_value_types(capabilities: HephSdkCapabilities) -> tuple[_ValueTypeReference, ...]:
    return (
        *_method_value_type_references(
            "methods.service_call",
            capabilities.service_call_method_specs,
        ),
        *_method_value_type_references(
            "methods.service_stream",
            capabilities.service_stream_method_specs,
        ),
        *_method_value_type_references("methods.jsonl_call", capabilities.jsonl_call_method_specs),
        *_method_value_type_references(
            "methods.jsonl_stream",
            capabilities.jsonl_stream_method_specs,
        ),
        *_field_value_type_references(
            "fields.service_state", capabilities.service_state_field_specs
        ),
        *_field_value_type_references(
            "fields.runtime_state", capabilities.runtime_state_field_specs
        ),
        *_field_value_type_references(
            "fields.session_state", capabilities.session_state_field_specs
        ),
        *_event_value_type_references(capabilities.event_specs),
        *_object_field_value_type_references(
            "jsonl.request_spec",
            capabilities.jsonl_request_spec.fields,
        ),
        *_jsonl_message_value_type_references(capabilities.jsonl_message_specs),
        *_result_value_type_references(
            "results.service_call",
            capabilities.service_call_result_specs,
        ),
        *_result_value_type_references(
            "results.jsonl_call",
            capabilities.jsonl_call_result_specs,
        ),
        *_type_value_type_references(capabilities.type_specs),
    )


def _method_value_type_references(
    context: str,
    specs: tuple[SdkMethodSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        _ValueTypeReference(f"{context}.{spec.method}.{param.name}", param.value_type)
        for spec in specs
        for param in spec.params
    )


def _field_value_type_references(
    context: str,
    specs: tuple[SdkFieldSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(_ValueTypeReference(f"{context}.{spec.name}", spec.value_type) for spec in specs)


def _object_field_value_type_references(
    context: str,
    fields: tuple[SdkObjectFieldSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        _ValueTypeReference(f"{context}.{field.name}", field.value_type) for field in fields
    )


def _event_value_type_references(
    specs: tuple[SdkEventSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        _ValueTypeReference(f"events.{spec.event_type}.{field.name}", field.value_type)
        for spec in specs
        for field in spec.fields
    )


def _jsonl_message_value_type_references(
    specs: tuple[SdkJsonlMessageSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        _ValueTypeReference(
            f"jsonl.message_specs.{spec.message_type}.{field.name}",
            field.value_type,
        )
        for spec in specs
        for field in spec.fields
    )


def _result_value_type_references(
    context: str,
    specs: tuple[SdkResultSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    references: list[_ValueTypeReference] = []
    for spec in specs:
        references.append(_ValueTypeReference(f"{context}.{spec.method}", spec.value_type))
        references.extend(
            _ValueTypeReference(f"{context}.{spec.method}.{field.name}", field.value_type)
            for field in spec.fields
        )
    return tuple(references)


def _type_value_type_references(
    specs: tuple[SdkTypeSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        _ValueTypeReference(f"types.{spec.type_name}.{field.name}", field.value_type)
        for spec in specs
        for field in spec.fields
    )


def _public_constant_exports() -> tuple[str, ...]:
    return tuple(sorted(name for name in globals() if name.isupper() and not name.startswith("_")))


__all__ = (  # noqa: PLE0604
    *_public_constant_exports(),
    "HephSdkCapabilities",
    "SdkCompatibilityPolicy",
    "SdkDeprecationSpec",
    "SdkValueTypeSpec",
    "get_sdk_capabilities",
    "validate_sdk_capabilities",
)
