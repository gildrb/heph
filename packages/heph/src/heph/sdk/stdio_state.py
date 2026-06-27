"""JSONL state projection helpers for the SDK stdio transport."""

from __future__ import annotations

from dataclasses import dataclass

from harness._types import is_string_mapping

from heph.sdk.method_validation import validate_result_payload
from heph.sdk.methods import (
    BUSY_ALLOWED_CALL_METHODS,
    JSONL_CALL_METHODS,
    JSONL_CALL_RESULT_SPECS,
    JSONL_STREAM_METHODS,
    SDK_METHOD_UNAVAILABLE_BUSY,
    jsonl_stream_method_for_service,
)
from heph.sdk.service_routes import ServicePayload


@dataclass(frozen=True, slots=True)
class TransportBusyState:
    prompt_active: bool
    active_operation: str | None

    @property
    def is_busy(self) -> bool:
        return self.prompt_active or self.active_operation is not None


def _service_state_includes_transport_busy(
    service_state: dict[str, object],
    transport_state: TransportBusyState,
) -> bool:
    prompt_recorded = (
        not transport_state.prompt_active or service_state.get("prompt_active") is True
    )
    operation_recorded = (
        transport_state.active_operation is None
        or service_state.get("active_operation") is not None
    )
    return prompt_recorded and operation_recorded


def _merge_transport_busy_state(
    service_state: dict[str, object],
    transport_state: TransportBusyState,
) -> dict[str, object]:
    merged_service = dict(service_state)
    if transport_state.prompt_active:
        merged_service["prompt_active"] = True
    if (
        transport_state.active_operation is not None
        and merged_service.get("active_operation") is None
    ):
        merged_service["active_operation"] = transport_state.active_operation
    merged_service["is_busy"] = True
    merged_service["available_call_methods"] = list(BUSY_ALLOWED_CALL_METHODS)
    merged_service["available_stream_methods"] = []
    merged_service["call_method_availability"] = _busy_method_availability(
        JSONL_CALL_METHODS,
        BUSY_ALLOWED_CALL_METHODS,
    )
    merged_service["stream_method_availability"] = _busy_method_availability(
        JSONL_STREAM_METHODS,
        (),
    )
    return merged_service


def _state_with_jsonl_stream_methods(state: ServicePayload) -> ServicePayload:
    service_state = state.get("service")
    if not is_string_mapping(service_state):
        return state
    merged_service = dict(service_state)
    if service_state.get("is_busy") is True:
        merged_service["available_stream_methods"] = []
    elif "available_stream_methods" in service_state:
        merged_service["available_stream_methods"] = _jsonl_available_stream_methods(service_state)
    else:
        merged_service["available_stream_methods"] = list(JSONL_STREAM_METHODS)
    if "stream_method_availability" in service_state:
        merged_service["stream_method_availability"] = _jsonl_stream_method_availability(
            service_state
        )
    merged_state = dict(state)
    merged_state["service"] = merged_service
    return merged_state


def _jsonl_available_stream_methods(service_state: dict[str, object]) -> list[str]:
    available = service_state.get("available_stream_methods")
    if not isinstance(available, list):
        return []
    methods: list[str] = []
    for method in available:
        if not isinstance(method, str):
            continue
        jsonl_method = jsonl_stream_method_for_service(method)
        if jsonl_method is not None:
            methods.append(jsonl_method)
    return methods


def _jsonl_stream_method_availability(service_state: dict[str, object]) -> list[dict[str, object]]:
    availability = service_state.get("stream_method_availability")
    if not isinstance(availability, list):
        return []
    return [
        record
        for item in availability
        if (record := _jsonl_stream_availability_record(item)) is not None
    ]


def _jsonl_stream_availability_record(item: object) -> dict[str, object] | None:
    if not is_string_mapping(item):
        return None
    jsonl_method = _jsonl_stream_availability_method(item)
    if jsonl_method is None:
        return None
    record = dict(item)
    record["method"] = jsonl_method
    return record


def _jsonl_stream_availability_method(item: dict[str, object]) -> str | None:
    method = item.get("method")
    if not isinstance(method, str):
        return None
    return jsonl_stream_method_for_service(method)


def _busy_method_availability(
    methods: tuple[str, ...],
    available_methods: tuple[str, ...],
) -> list[dict[str, object]]:
    available = frozenset(available_methods)
    available_records: list[dict[str, object]] = [
        {
            "method": method,
            "available": True,
            "unavailable_reason": None,
        }
        for method in available_methods
    ]
    unavailable_records: list[dict[str, object]] = [
        {
            "method": method,
            "available": False,
            "unavailable_reason": SDK_METHOD_UNAVAILABLE_BUSY,
        }
        for method in methods
        if method not in available
    ]
    return [*available_records, *unavailable_records]


def _jsonl_result_payload(result: ServicePayload) -> ServicePayload:
    result = _state_with_jsonl_stream_methods(result)
    state_value = result.get("state")
    if not is_string_mapping(state_value):
        return result
    merged_result = dict(result)
    merged_result["state"] = _state_with_jsonl_stream_methods(state_value)
    return merged_result


def _jsonl_validated_result_payload(
    method: str,
    result: ServicePayload,
    *,
    translate_state_streams: bool,
) -> ServicePayload:
    payload = _jsonl_result_payload(result) if translate_state_streams else dict(result)
    return validate_result_payload(
        method,
        payload,
        JSONL_CALL_RESULT_SPECS,
        surface="SDK JSONL",
    )
