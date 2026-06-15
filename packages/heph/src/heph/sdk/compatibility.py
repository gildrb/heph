"""Client-side SDK compatibility checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from heph.sdk.capabilities import HephSdkCapabilities
from heph.sdk.methods import SDK_STABILITY_LEVELS, SDK_STABILITY_PUBLIC

_DEFAULT_ACCEPTED_STABILITY_LEVELS = (SDK_STABILITY_PUBLIC,)


class SdkClientCompatibilityError(Exception):
    """Raised when an SDK client rejects an incompatible server contract."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("SDK client is not compatible: " + "; ".join(issues))


def validate_sdk_client_compatibility(
    capabilities: HephSdkCapabilities,
    *,
    client_capabilities_version: int,
    jsonl_version: int | None = None,
    accepted_stability_levels: Sequence[str] = _DEFAULT_ACCEPTED_STABILITY_LEVELS,
) -> tuple[str, ...]:
    """Return compatibility issues for a native capabilities object."""
    return _compatibility_issues(
        stability=capabilities.compatibility.stability,
        capabilities_version=capabilities.version,
        current_capabilities_version=capabilities.compatibility.current_capabilities_version,
        min_client_capabilities_version=capabilities.compatibility.min_client_capabilities_version,
        supported_jsonl_versions=capabilities.compatibility.supported_jsonl_versions,
        client_capabilities_version=client_capabilities_version,
        jsonl_version=jsonl_version,
        accepted_stability_levels=accepted_stability_levels,
    )


def ensure_sdk_client_compatibility(
    capabilities: HephSdkCapabilities,
    *,
    client_capabilities_version: int,
    jsonl_version: int | None = None,
    accepted_stability_levels: Sequence[str] = _DEFAULT_ACCEPTED_STABILITY_LEVELS,
) -> None:
    """Raise when a native SDK client cannot use the advertised capabilities."""
    issues = validate_sdk_client_compatibility(
        capabilities,
        client_capabilities_version=client_capabilities_version,
        jsonl_version=jsonl_version,
        accepted_stability_levels=accepted_stability_levels,
    )
    if issues:
        raise SdkClientCompatibilityError(issues)


def validate_sdk_client_payload_compatibility(
    capabilities: Mapping[str, object],
    *,
    client_capabilities_version: int,
    jsonl_version: int | None = None,
    accepted_stability_levels: Sequence[str] = _DEFAULT_ACCEPTED_STABILITY_LEVELS,
) -> tuple[str, ...]:
    """Return compatibility issues for a JSON-ready capabilities payload."""
    payload_issues: list[str] = []
    compatibility = _mapping_field(
        payload_issues,
        capabilities,
        key="compatibility",
        label="capabilities.compatibility",
    )
    capabilities_version = _integer_field(
        payload_issues,
        capabilities,
        key="version",
        label="capabilities.version",
    )
    if compatibility is None:
        return tuple(payload_issues)
    stability = _string_field(
        payload_issues,
        compatibility,
        key="stability",
        label="capabilities.compatibility.stability",
    )
    current_capabilities_version = _integer_field(
        payload_issues,
        compatibility,
        key="current_capabilities_version",
        label="capabilities.compatibility.current_capabilities_version",
    )
    min_client_capabilities_version = _integer_field(
        payload_issues,
        compatibility,
        key="min_client_capabilities_version",
        label="capabilities.compatibility.min_client_capabilities_version",
    )
    supported_jsonl_versions = _integer_sequence_field(
        payload_issues,
        compatibility,
        key="supported_jsonl_versions",
        label="capabilities.compatibility.supported_jsonl_versions",
    )
    if (
        stability is None
        or capabilities_version is None
        or current_capabilities_version is None
        or min_client_capabilities_version is None
        or supported_jsonl_versions is None
    ):
        return tuple(payload_issues)
    return (
        *payload_issues,
        *_compatibility_issues(
            capabilities_version=capabilities_version,
            current_capabilities_version=current_capabilities_version,
            min_client_capabilities_version=min_client_capabilities_version,
            supported_jsonl_versions=supported_jsonl_versions,
            client_capabilities_version=client_capabilities_version,
            jsonl_version=jsonl_version,
            stability=stability,
            accepted_stability_levels=accepted_stability_levels,
        ),
    )


def ensure_sdk_client_payload_compatibility(
    capabilities: Mapping[str, object],
    *,
    client_capabilities_version: int,
    jsonl_version: int | None = None,
    accepted_stability_levels: Sequence[str] = _DEFAULT_ACCEPTED_STABILITY_LEVELS,
) -> None:
    """Raise when a JSON-ready SDK client cannot use the advertised capabilities."""
    issues = validate_sdk_client_payload_compatibility(
        capabilities,
        client_capabilities_version=client_capabilities_version,
        jsonl_version=jsonl_version,
        accepted_stability_levels=accepted_stability_levels,
    )
    if issues:
        raise SdkClientCompatibilityError(issues)


def _mapping_field(
    issues: list[str],
    payload: Mapping[str, object],
    *,
    key: str,
    label: str,
) -> dict[str, object] | None:
    value = payload.get(key)
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for item_key, item in value.items():
            if not isinstance(item_key, str):
                issues.append(f"{label} keys must be strings.")
                return None
            result[item_key] = item
        return result
    issues.append(f"{label} must be an object.")
    return None


def _integer_field(
    issues: list[str],
    payload: Mapping[str, object],
    *,
    key: str,
    label: str,
) -> int | None:
    value = payload.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    issues.append(f"{label} must be an integer.")
    return None


def _string_field(
    issues: list[str],
    payload: Mapping[str, object],
    *,
    key: str,
    label: str,
) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    issues.append(f"{label} must be a non-empty string.")
    return None


def _integer_sequence_field(
    issues: list[str],
    payload: Mapping[str, object],
    *,
    key: str,
    label: str,
) -> tuple[int, ...] | None:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        issues.append(f"{label} must be an array of integers.")
        return None
    items: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            issues.append(f"{label} must be an array of integers.")
            return None
        items.append(item)
    return tuple(items)


def _compatibility_issues(
    *,
    stability: str,
    capabilities_version: int,
    current_capabilities_version: int,
    min_client_capabilities_version: int,
    supported_jsonl_versions: tuple[int, ...],
    client_capabilities_version: int,
    jsonl_version: int | None,
    accepted_stability_levels: Sequence[str],
) -> tuple[str, ...]:
    issues: list[str] = []
    _append_stability_issues(
        issues,
        stability,
        accepted_stability_levels,
    )
    _append_capability_version_issues(
        issues,
        capabilities_version=capabilities_version,
        current_capabilities_version=current_capabilities_version,
        min_client_capabilities_version=min_client_capabilities_version,
        client_capabilities_version=client_capabilities_version,
    )
    if jsonl_version is not None:
        _append_jsonl_version_issues(issues, jsonl_version, supported_jsonl_versions)
    return tuple(issues)


def _append_stability_issues(
    issues: list[str],
    stability: str,
    accepted_stability_levels: Sequence[str],
) -> None:
    accepted_levels, accepted_level_issues = _accepted_stability_levels(accepted_stability_levels)
    issues.extend(accepted_level_issues)
    if not accepted_levels:
        return
    if stability in accepted_levels:
        return
    issues.append(
        f"SDK stability '{stability}' is not accepted by this client; accepted levels: "
        f"{', '.join(accepted_levels)}."
    )


def _accepted_stability_levels(levels: Sequence[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    accepted_levels: list[str] = []
    invalid_type_found = False
    unknown_levels: list[str] = []
    for level in _raw_stability_levels(levels):
        if not _accept_stability_level(level, accepted_levels, unknown_levels):
            invalid_type_found = True
    return tuple(accepted_levels), _accepted_stability_level_issues(
        accepted_levels,
        invalid_type_found=invalid_type_found,
        unknown_levels=unknown_levels,
    )


def _raw_stability_levels(levels: Sequence[str]) -> tuple[object, ...]:
    return (levels,) if isinstance(levels, str) else tuple(levels)


def _accept_stability_level(
    level: object,
    accepted_levels: list[str],
    unknown_levels: list[str],
) -> bool:
    if not isinstance(level, str):
        return False
    if not level:
        return True
    if level not in SDK_STABILITY_LEVELS:
        unknown_levels.append(level)
        return True
    if level not in accepted_levels:
        accepted_levels.append(level)
    return True


def _accepted_stability_level_issues(
    accepted_levels: list[str],
    *,
    invalid_type_found: bool,
    unknown_levels: list[str],
) -> tuple[str, ...]:
    issues: list[str] = []
    if invalid_type_found:
        issues.append("SDK client accepted stability levels must be strings.")
    if unknown_levels:
        issues.append(
            "SDK client accepted stability levels contain unknown values: "
            f"{', '.join(unknown_levels)}."
        )
    if not accepted_levels and not issues:
        issues.append("SDK client accepted stability levels must not be empty.")
    return tuple(issues)


def _append_capability_version_issues(
    issues: list[str],
    *,
    capabilities_version: int,
    current_capabilities_version: int,
    min_client_capabilities_version: int,
    client_capabilities_version: int,
) -> None:
    if capabilities_version != current_capabilities_version:
        issues.append("SDK capabilities version does not match compatibility policy.")
    if client_capabilities_version < 1:
        issues.append("SDK client capability version must be positive.")
    if client_capabilities_version < min_client_capabilities_version:
        issues.append(
            "SDK client capability version "
            f"{client_capabilities_version} is older than minimum supported "
            f"{min_client_capabilities_version}."
        )
    if client_capabilities_version > current_capabilities_version:
        issues.append(
            "SDK client capability version "
            f"{client_capabilities_version} is newer than server capabilities "
            f"{current_capabilities_version}."
        )


def _append_jsonl_version_issues(
    issues: list[str],
    jsonl_version: int,
    supported_jsonl_versions: tuple[int, ...],
) -> None:
    if jsonl_version in supported_jsonl_versions:
        return
    issues.append(
        f"SDK JSONL version {jsonl_version} is not supported; supported versions: "
        f"{_version_list(supported_jsonl_versions)}."
    )


def _version_list(versions: tuple[int, ...]) -> str:
    return ", ".join(str(version) for version in versions) or "none"


__all__ = [
    "SdkClientCompatibilityError",
    "ensure_sdk_client_compatibility",
    "ensure_sdk_client_payload_compatibility",
    "validate_sdk_client_compatibility",
    "validate_sdk_client_payload_compatibility",
]
