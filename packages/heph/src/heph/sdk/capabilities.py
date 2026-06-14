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
    SDK_EVENT_SPECS,
    SDK_EVENT_TYPES,
    SDK_JSONL_PROTOCOL,
    SDK_JSONL_VERSION,
    SDK_METHOD_AVAILABILITY_REQUIREMENTS,
    SDK_METHOD_REQUIREMENT_ALWAYS,
    SDK_METHOD_UNAVAILABLE_REASONS,
    SDK_TYPE_SPECS,
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
)
from heph.sdk.value_types import sdk_custom_type_references, sdk_value_type_shape_issue

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
_JSONL_REQUEST_ENVELOPE_FIELDS = (
    SdkObjectFieldSpec("id", "string_or_integer", required=False, nullable=True),
    SdkObjectFieldSpec("method", "string"),
    SdkObjectFieldSpec("params", "object", required=False, nullable=True),
)
type _DuplicateCheck = tuple[str, tuple[str, ...]]
type _MismatchCheck = tuple[str, tuple[str, ...], tuple[str, ...]]
type _AvailabilitySpecReference = tuple[str, SdkMethodAvailabilitySpec]
type _StreamSpecReference = tuple[str, SdkStreamSpec]
type _ValueTypeReference = tuple[str, str]


@dataclass(frozen=True, slots=True)
class HephSdkCapabilities:
    """JSON-ready SDK feature contract for direct and transport clients."""

    version: int
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

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
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
        }


SDK_CAPABILITIES = HephSdkCapabilities(
    version=SDK_CAPABILITIES_VERSION,
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
)


def get_sdk_capabilities() -> HephSdkCapabilities:
    return SDK_CAPABILITIES


def validate_sdk_capabilities(
    capabilities: HephSdkCapabilities = SDK_CAPABILITIES,
) -> tuple[str, ...]:
    """Return human-readable SDK capability contract issues."""
    issues: list[str] = []
    for label, names in _duplicate_checks(capabilities):
        _append_duplicate_issue(issues, label, names)
    for label, advertised, structured in _mismatch_checks(capabilities):
        _append_mismatch_issue(issues, label, advertised, structured)
    _append_subset_issue(
        issues,
        "service.busy_allowed_call_methods",
        capabilities.busy_allowed_call_methods,
        capabilities.service_call_methods,
    )
    _append_parameter_choice_issues(issues, capabilities)
    _append_availability_issues(issues, capabilities)
    _append_value_type_shape_issues(issues, capabilities)
    _append_unknown_type_issues(issues, capabilities)
    _append_stream_event_issues(issues, capabilities)
    _append_discriminator_issues(issues, capabilities)
    _append_jsonl_request_envelope_issues(issues, capabilities)
    return tuple(issues)


def _duplicate_checks(capabilities: HephSdkCapabilities) -> tuple[_DuplicateCheck, ...]:
    return (
        *_method_name_duplicate_checks(capabilities),
        *_jsonl_contract_duplicate_checks(capabilities),
        *_availability_duplicate_checks(capabilities),
        ("types", _type_names(capabilities.type_specs)),
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
        ("service.call_methods", capabilities.service_call_methods),
        ("service.stream_methods", capabilities.service_stream_methods),
        ("jsonl.call_methods", capabilities.jsonl_call_methods),
        ("jsonl.stream_methods", capabilities.jsonl_stream_methods),
    )


def _jsonl_contract_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        ("jsonl.request_spec.fields", _jsonl_request_field_names(capabilities)),
        ("jsonl.message_types", capabilities.jsonl_message_types),
        ("events.types", capabilities.event_types),
        ("jsonl.error_codes", capabilities.jsonl_error_codes),
        ("service.busy_allowed_call_methods", capabilities.busy_allowed_call_methods),
        ("service.method_unavailable_reasons", capabilities.method_unavailable_reasons),
    )


def _availability_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        ("availability.requirements", capabilities.method_availability_requirements),
        (
            "availability.service_call",
            _availability_method_names(capabilities.service_call_method_availability_specs),
        ),
        (
            "availability.service_stream",
            _availability_method_names(capabilities.service_stream_method_availability_specs),
        ),
        (
            "availability.jsonl_call",
            _availability_method_names(capabilities.jsonl_call_method_availability_specs),
        ),
        (
            "availability.jsonl_stream",
            _availability_method_names(capabilities.jsonl_stream_method_availability_specs),
        ),
    )


def _state_field_duplicate_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_DuplicateCheck, ...]:
    return (
        ("fields.service_state", _field_names(capabilities.service_state_field_specs)),
        ("fields.runtime_state", _field_names(capabilities.runtime_state_field_specs)),
        ("fields.session_state", _field_names(capabilities.session_state_field_specs)),
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


def _method_param_duplicate_checks(
    context: str,
    specs: tuple[SdkMethodSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        (f"{context}.{spec.method}.params", tuple(param.name for param in spec.params))
        for spec in specs
    )


def _event_field_duplicate_checks(
    specs: tuple[SdkEventSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        (f"events.{spec.event_type}.fields", tuple(field.name for field in spec.fields))
        for spec in specs
    )


def _jsonl_message_field_duplicate_checks(
    specs: tuple[SdkJsonlMessageSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        (
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
        (f"{context}.{spec.method}.fields", tuple(field.name for field in spec.fields))
        for spec in specs
    )


def _type_field_duplicate_checks(
    specs: tuple[SdkTypeSpec, ...],
) -> tuple[_DuplicateCheck, ...]:
    return tuple(
        (f"types.{spec.type_name}.fields", tuple(field.name for field in spec.fields))
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
        (
            "service.call_methods",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_method_specs),
        ),
        (
            "service.stream_methods",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_method_specs),
        ),
        (
            "jsonl.call_methods",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_method_specs),
        ),
        (
            "jsonl.stream_methods",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_method_specs),
        ),
    )


def _result_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        (
            "results.service_call",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_result_specs),
        ),
        (
            "results.jsonl_call",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_result_specs),
        ),
    )


def _stream_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        (
            "streams.service",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_specs),
        ),
        (
            "streams.jsonl",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_specs),
        ),
    )


def _availability_mismatch_checks(
    capabilities: HephSdkCapabilities,
) -> tuple[_MismatchCheck, ...]:
    return (
        (
            "availability.service_call",
            capabilities.service_call_methods,
            tuple(spec.method for spec in capabilities.service_call_method_availability_specs),
        ),
        (
            "availability.service_stream",
            capabilities.service_stream_methods,
            tuple(spec.method for spec in capabilities.service_stream_method_availability_specs),
        ),
        (
            "availability.jsonl_call",
            capabilities.jsonl_call_methods,
            tuple(spec.method for spec in capabilities.jsonl_call_method_availability_specs),
        ),
        (
            "availability.jsonl_stream",
            capabilities.jsonl_stream_methods,
            tuple(spec.method for spec in capabilities.jsonl_stream_method_availability_specs),
        ),
    )


def _event_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        (
            "events.types",
            capabilities.event_types,
            tuple(spec.event_type for spec in capabilities.event_specs),
        ),
        (
            "jsonl.message_types",
            capabilities.jsonl_message_types,
            tuple(spec.message_type for spec in capabilities.jsonl_message_specs),
        ),
    )


def _state_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        (
            "state.service_fields",
            capabilities.service_state_fields,
            tuple(spec.name for spec in capabilities.service_state_field_specs),
        ),
        (
            "state.runtime_fields",
            capabilities.runtime_state_fields,
            tuple(spec.name for spec in capabilities.runtime_state_field_specs),
        ),
        (
            "state.session_fields",
            capabilities.session_state_fields,
            tuple(spec.name for spec in capabilities.session_state_field_specs),
        ),
    )


def _error_mismatch_checks(capabilities: HephSdkCapabilities) -> tuple[_MismatchCheck, ...]:
    return (
        (
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
        for type_name in sdk_custom_type_references(value_type, _BUILTIN_TYPES)
        if type_name not in known_types
    )


def _append_value_type_shape_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    issues.extend(
        issue
        for context, value_type in _referenced_value_types(capabilities)
        if (issue := sdk_value_type_shape_issue(context, value_type)) is not None
    )


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
    for context, spec in _availability_spec_references(capabilities):
        _append_unknown_availability_requirement_issue(
            issues,
            context,
            spec,
            known_requirements,
        )
        _append_unknown_unavailable_reason_issue(issues, context, spec, known_reasons)
        _append_availability_reason_shape_issue(issues, context, spec)


def _availability_spec_references(
    capabilities: HephSdkCapabilities,
) -> tuple[_AvailabilitySpecReference, ...]:
    return (
        *(
            (f"availability.service_call.{spec.method}", spec)
            for spec in capabilities.service_call_method_availability_specs
        ),
        *(
            (f"availability.service_stream.{spec.method}", spec)
            for spec in capabilities.service_stream_method_availability_specs
        ),
        *(
            (f"availability.jsonl_call.{spec.method}", spec)
            for spec in capabilities.jsonl_call_method_availability_specs
        ),
        *(
            (f"availability.jsonl_stream.{spec.method}", spec)
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
    for context, spec in _stream_spec_references(capabilities):
        _append_stream_spec_event_issues(issues, context, spec, known_events)


def _stream_spec_references(
    capabilities: HephSdkCapabilities,
) -> tuple[_StreamSpecReference, ...]:
    return (
        *((f"streams.service.{spec.method}", spec) for spec in capabilities.service_stream_specs),
        *((f"streams.jsonl.{spec.method}", spec) for spec in capabilities.jsonl_stream_specs),
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


def _append_jsonl_request_envelope_issues(
    issues: list[str],
    capabilities: HephSdkCapabilities,
) -> None:
    advertised_names = tuple(field.name for field in capabilities.jsonl_request_spec.fields)
    expected_names = tuple(field.name for field in _JSONL_REQUEST_ENVELOPE_FIELDS)
    if advertised_names != expected_names:
        issues.append("jsonl.request_spec.fields must be exactly: " + ", ".join(expected_names))
    for expected in _JSONL_REQUEST_ENVELOPE_FIELDS:
        field = _field_by_name(capabilities.jsonl_request_spec.fields, expected.name)
        if field is not None:
            _append_jsonl_request_field_shape_issues(issues, field, expected)


def _append_jsonl_request_field_shape_issues(
    issues: list[str],
    field: SdkObjectFieldSpec,
    expected: SdkObjectFieldSpec,
) -> None:
    context = f"jsonl.request_spec.{expected.name}"
    if field.value_type != expected.value_type:
        issues.append(f"{context} must be {expected.value_type}.")
    if field.required != expected.required or field.nullable != expected.nullable:
        issues.append(f"{context} must be {_required_nullable_message(expected)}.")


def _required_nullable_message(field: SdkObjectFieldSpec) -> str:
    required = "required" if field.required else "optional"
    nullable = "nullable" if field.nullable else "non-null"
    return f"{required} and {nullable}"


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
        (f"{context}.{spec.method}.{param.name}", param.value_type)
        for spec in specs
        for param in spec.params
    )


def _field_value_type_references(
    context: str,
    specs: tuple[SdkFieldSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple((f"{context}.{spec.name}", spec.value_type) for spec in specs)


def _object_field_value_type_references(
    context: str,
    fields: tuple[SdkObjectFieldSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple((f"{context}.{field.name}", field.value_type) for field in fields)


def _event_value_type_references(
    specs: tuple[SdkEventSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        (f"events.{spec.event_type}.{field.name}", field.value_type)
        for spec in specs
        for field in spec.fields
    )


def _jsonl_message_value_type_references(
    specs: tuple[SdkJsonlMessageSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        (f"jsonl.message_specs.{spec.message_type}.{field.name}", field.value_type)
        for spec in specs
        for field in spec.fields
    )


def _result_value_type_references(
    context: str,
    specs: tuple[SdkResultSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    references: list[_ValueTypeReference] = []
    for spec in specs:
        references.append((f"{context}.{spec.method}", spec.value_type))
        references.extend(
            (f"{context}.{spec.method}.{field.name}", field.value_type) for field in spec.fields
        )
    return tuple(references)


def _type_value_type_references(
    specs: tuple[SdkTypeSpec, ...],
) -> tuple[_ValueTypeReference, ...]:
    return tuple(
        (f"types.{spec.type_name}.{field.name}", field.value_type)
        for spec in specs
        for field in spec.fields
    )


def _public_constant_exports() -> tuple[str, ...]:
    return tuple(sorted(name for name in globals() if name.isupper() and not name.startswith("_")))


__all__ = (  # noqa: PLE0604
    *_public_constant_exports(),
    "HephSdkCapabilities",
    "get_sdk_capabilities",
    "validate_sdk_capabilities",
)
