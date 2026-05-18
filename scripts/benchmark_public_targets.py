"""Validate public-target benchmark ledgers before competitive claim generation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from scripts import claim_report_envelope

BASELINE_LEDGER_SCHEMA_VERSION = "baseline-ledger-v1"
PUBLIC_SNAPSHOT_SCHEMA_VERSION = "enterprise-rag-public-snapshot-v1"
DATASET_VERSION_LEDGER_SCHEMA_VERSION = "dataset-version-ledger-v1"
EVALUATION_PLAN_SCHEMA_VERSION = "evaluation-plan-v1"
CLAIM_GATE_SCHEMA_VERSION = "public-target-claim-gate-v1"

_HASH_FIELDS = ("manifest_sha256", "cases_sha256", "qrels_sha256", "corpus_sha256")
_MATCHED_METADATA_FIELDS = (
    "benchmark_type",
    "dataset",
    "cases_sha256",
    "manifest_sha256",
    "qrels_sha256",
    "corpus_sha256",
    "scoring_protocol_version",
    "top_k",
    "candidate_multiplier",
    "candidate_depth",
    "latency_scope",
    "dependency_lock_sha256",
    "model",
    "prompt_hash",
    "metric_formulas_sha256",
    "cache_state",
    "network_state",
    "permission_scope",
)
_SNAPSHOT_COLUMN_MAPPING_FIELDS = ("system_label", "rank_metric", "dataset", "split", "scope")


class PublicTargetError(Exception):
    """Expected public-target validation failure with a stable code."""

    def __init__(self, code: str, message: str, remediation: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.remediation = remediation


@dataclass(frozen=True, slots=True)
class BaselineLedger:
    path: Path
    artifact_path: Path
    artifact_sha256: str
    baseline_id: str
    baseline_version: str
    target_role: str
    selected_metrics: tuple[str, ...]
    matched_metadata: dict[str, object]
    baseline_report: dict[str, object]


@dataclass(frozen=True, slots=True)
class PublicSnapshot:
    path: Path
    raw_path: Path
    raw_sha256: str
    source_url: str
    request_command: str
    retrieved_at: str
    target_role: str
    benchmark_type: str
    dataset: str
    split: str
    scope: str
    row_count: int
    byte_count: int
    source_schema_version: str
    rank_metric: str
    rank_order: str
    metric_units: dict[str, str]
    column_mapping: dict[str, str]
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True, slots=True)
class DatasetVersion:
    ledger_path: Path
    dataset_id: str
    version: str
    entry: dict[str, object]


@dataclass(frozen=True, slots=True)
class EvaluationPlan:
    path: Path
    plan_id: str
    primary_target: str
    primary_metrics: tuple[str, ...]
    secondary_metrics: tuple[str, ...]
    top_k_values: tuple[int, ...]
    candidate_depth_values: tuple[int, ...]
    statistical_method: str
    run_policy: str
    seed_policy: tuple[int, ...]
    failure_handling: str
    baseline_improvement: dict[str, object]
    known_public_target: dict[str, object]


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    metric: str
    baseline: float
    current: float
    delta: float
    tolerance: float
    passed: bool


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PublicTargetError(
            "input_not_found",
            f"could not read {label}: {path}",
            "Pass existing ledger, snapshot, plan, and report files.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise PublicTargetError(
            "malformed_json",
            f"{label} contains invalid JSON at line {exc.lineno}: {path}",
            "Regenerate the JSON artifact with deterministic formatting.",
        ) from exc
    if not isinstance(raw, dict):
        raise PublicTargetError(
            "malformed_json",
            f"{label} must be a JSON object: {path}",
            "Regenerate the JSON artifact with an object at the top level.",
        )
    return cast("dict[str, object]", raw)


def _write_json(path: Path | None, payload: Mapping[str, object]) -> None:
    if path is None:
        return
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PublicTargetError(
            "input_not_found",
            f"could not read file for SHA-256: {path}",
            "Ensure every ledger path points to an existing immutable artifact.",
        ) from exc


def metric_formulas_sha256(report: Mapping[str, object]) -> str:
    """Return a stable SHA-256 over report metric formula metadata."""
    metadata = report.get("metadata")
    formulas: object = {}
    if isinstance(metadata, dict):
        raw_formulas = cast("dict[str, object]", metadata).get("metric_formulas")
        if isinstance(raw_formulas, dict):
            formulas = raw_formulas
    serialized = json.dumps(formulas, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_relative_path(raw_path: str, owner_path: Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = owner_path.parent / path
    return path.resolve()


def _required_string(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> str:
    value = payload.get(field_name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise PublicTargetError(
        code,
        f"{label} is missing non-empty string field {field_name!r}",
        "Add the required provenance/schema field before claim generation.",
    )


def _required_bool(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> bool:
    value = payload.get(field_name)
    if isinstance(value, bool):
        return value
    raise PublicTargetError(
        code,
        f"{label} is missing boolean field {field_name!r}",
        "Record the explicit boolean gate in the ledger or plan.",
    )


def _required_mapping(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> dict[str, object]:
    value = payload.get(field_name)
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    raise PublicTargetError(
        code,
        f"{label} is missing object field {field_name!r}",
        "Record the required object before claim generation.",
    )


def _required_list(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> list[object]:
    value = payload.get(field_name)
    if isinstance(value, list):
        return value
    raise PublicTargetError(
        code,
        f"{label} is missing list field {field_name!r}",
        "Record the required list before claim generation.",
    )


def _string_list(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> tuple[str, ...]:
    raw_items = _required_list(payload, field_name, code=code, label=label)
    items = tuple(item.strip() for item in raw_items if isinstance(item, str) and item.strip())
    if len(items) == len(raw_items) and items:
        return items
    raise PublicTargetError(
        code,
        f"{label} field {field_name!r} must contain non-empty strings",
        "Use explicit metric, column, or policy names.",
    )


def _int_list(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> tuple[int, ...]:
    raw_items = _required_list(payload, field_name, code=code, label=label)
    items = tuple(
        item for item in raw_items if isinstance(item, int) and not isinstance(item, bool)
    )
    if len(items) == len(raw_items) and items:
        return items
    raise PublicTargetError(
        code,
        f"{label} field {field_name!r} must contain integer values",
        "Declare top-k or candidate-depth values as integers.",
    )


def _required_int(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> int:
    value = payload.get(field_name)
    if isinstance(value, bool):
        value = None
    if isinstance(value, int):
        return value
    raise PublicTargetError(
        code,
        f"{label} is missing integer field {field_name!r}",
        "Record the exact count in the provenance sidecar.",
    )


def _required_number(
    payload: Mapping[str, object],
    field_name: str,
    *,
    code: str,
    label: str,
) -> float:
    value = payload.get(field_name)
    if isinstance(value, bool):
        value = None
    if isinstance(value, int | float):
        return float(value)
    raise PublicTargetError(
        code,
        f"{label} is missing numeric field {field_name!r}",
        "Declare the numeric tolerance, delta, or metric before claim generation.",
    )


def _validate_hash(value: object, *, field_name: str, code: str, label: str) -> str:
    if isinstance(value, str) and len(value) == 64:
        allowed = set("0123456789abcdef")
        if all(character in allowed for character in value.lower()):
            return value.lower()
    raise PublicTargetError(
        code,
        f"{label} field {field_name!r} must be a SHA-256 hex digest",
        "Record a lowercase 64-character SHA-256 digest.",
    )


def _validate_schema(
    payload: Mapping[str, object],
    expected: str,
    *,
    code: str,
    label: str,
) -> None:
    schema_version = _required_string(payload, "schema_version", code=code, label=label)
    if schema_version != expected:
        raise PublicTargetError(
            code,
            f"{label} has unsupported schema_version {schema_version!r}; expected {expected!r}",
            "Migrate or regenerate the artifact with the current schema version.",
        )


def load_baseline_ledger(path: Path) -> BaselineLedger:
    """Read and validate a frozen baseline ledger and its referenced report."""
    ledger_path = path.expanduser().resolve()
    ledger = _read_json_object(ledger_path, label="baseline ledger")
    _validate_schema(
        ledger,
        BASELINE_LEDGER_SCHEMA_VERSION,
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    if not _required_bool(
        ledger,
        "frozen",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    ):
        raise PublicTargetError(
            "baseline_not_frozen",
            "baseline ledger must set frozen=true",
            "Freeze the baseline artifact before using it for claims.",
        )
    baseline_id = _required_string(
        ledger,
        "baseline_id",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    baseline_version = _required_string(
        ledger,
        "baseline_version",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    artifact_path = _resolve_relative_path(
        _required_string(
            ledger,
            "artifact_path",
            code="baseline_ledger_invalid",
            label="baseline ledger",
        ),
        ledger_path,
    )
    artifact_sha256 = _validate_hash(
        ledger.get("artifact_sha256"),
        field_name="artifact_sha256",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    actual_sha256 = _sha256_file(artifact_path)
    if actual_sha256 != artifact_sha256:
        raise PublicTargetError(
            "baseline_hash_mismatch",
            f"baseline artifact hash changed: {artifact_path}",
            "Restore the frozen baseline or create an explicit new baseline version.",
        )
    selected_metrics = _string_list(
        ledger,
        "selected_metrics",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    matched_metadata = _required_mapping(
        ledger,
        "matched_metadata",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    for field_name in _MATCHED_METADATA_FIELDS:
        if field_name not in matched_metadata:
            raise PublicTargetError(
                "baseline_ledger_invalid",
                f"baseline matched_metadata is missing {field_name!r}",
                "Record every field needed to prove matched baseline comparison inputs.",
            )
    for field_name in _HASH_FIELDS:
        _validate_hash(
            matched_metadata.get(field_name),
            field_name=field_name,
            code="baseline_ledger_invalid",
            label="baseline ledger matched_metadata",
        )
    _validate_hash(
        matched_metadata.get("dependency_lock_sha256"),
        field_name="dependency_lock_sha256",
        code="baseline_ledger_invalid",
        label="baseline ledger matched_metadata",
    )
    _validate_hash(
        matched_metadata.get("metric_formulas_sha256"),
        field_name="metric_formulas_sha256",
        code="baseline_ledger_invalid",
        label="baseline ledger matched_metadata",
    )
    target_role = _required_string(
        ledger,
        "target_role",
        code="baseline_ledger_invalid",
        label="baseline ledger",
    )
    if target_role not in {"primary", "secondary"}:
        raise PublicTargetError(
            "baseline_ledger_invalid",
            f"baseline target_role must be primary or secondary, got {target_role!r}",
            "Classify the target role before claim generation.",
        )
    baseline_report = _read_json_object(artifact_path, label="baseline report")
    for metric in selected_metrics:
        _metric_value(baseline_report, metric)
    return BaselineLedger(
        path=ledger_path,
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        baseline_id=baseline_id,
        baseline_version=baseline_version,
        target_role=target_role,
        selected_metrics=selected_metrics,
        matched_metadata=matched_metadata,
        baseline_report=baseline_report,
    )


def load_public_snapshot(path: Path) -> PublicSnapshot:
    """Read, hash-check, and schema-validate a public EnterpriseRAG snapshot sidecar."""
    snapshot_path = path.expanduser().resolve()
    snapshot = _read_json_object(snapshot_path, label="public snapshot")
    _validate_schema(
        snapshot,
        PUBLIC_SNAPSHOT_SCHEMA_VERSION,
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    target_role = _required_string(
        snapshot,
        "target_role",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if target_role not in {"primary", "secondary"}:
        raise PublicTargetError(
            "snapshot_schema_invalid",
            f"public snapshot target_role must be primary or secondary, got {target_role!r}",
            "Classify the public target role before claim generation.",
        )
    source_url = _required_string(
        snapshot,
        "source_url",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if not source_url.startswith("https://"):
        raise PublicTargetError(
            "snapshot_source_not_public",
            f"public snapshot source_url must be HTTPS: {source_url}",
            "Use an explicit public HTTPS URL for snapshot provenance.",
        )
    request_command = _required_string(
        snapshot,
        "request_command",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if "curl" not in request_command.split() or source_url not in request_command:
        raise PublicTargetError(
            "snapshot_schema_invalid",
            "public snapshot request_command must record the curl request and source URL",
            "Record the exact public curl command used to acquire the raw snapshot.",
        )
    http_status = _required_int(
        snapshot,
        "http_status",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if not 200 <= http_status <= 399:
        raise PublicTargetError(
            "snapshot_http_status_failed",
            f"public snapshot HTTP status must be 2xx/3xx, got {http_status}",
            "Acquire the snapshot from a successful public request.",
        )
    raw_path = _resolve_relative_path(
        _required_string(
            snapshot,
            "raw_path",
            code="snapshot_schema_invalid",
            label="public snapshot",
        ),
        snapshot_path,
    )
    expected_sha256 = _validate_hash(
        snapshot.get("raw_sha256"),
        field_name="raw_sha256",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    actual_sha256 = _sha256_file(raw_path)
    if actual_sha256 != expected_sha256:
        raise PublicTargetError(
            "snapshot_hash_mismatch",
            f"public snapshot raw bytes changed: {raw_path}",
            "Restore the immutable snapshot bytes or capture a new dated snapshot.",
        )
    byte_count = _required_int(
        snapshot,
        "byte_count",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if raw_path.stat().st_size != byte_count:
        raise PublicTargetError(
            "snapshot_byte_count_mismatch",
            f"public snapshot byte_count does not match raw file: {raw_path}",
            "Record the byte count from the immutable raw artifact.",
        )
    row_count = _required_int(
        snapshot,
        "row_count",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    source_schema_version = _required_string(
        snapshot,
        "source_schema_version",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    rank_metric = _required_string(
        snapshot,
        "rank_metric",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    rank_order = _required_string(
        snapshot,
        "rank_order",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    if rank_order not in {"ascending", "descending"}:
        raise PublicTargetError(
            "snapshot_schema_invalid",
            f"rank_order must be ascending or descending, got {rank_order!r}",
            "Pin the official rank direction in the snapshot sidecar.",
        )
    column_mapping = _string_mapping(
        _required_mapping(
            snapshot,
            "column_mapping",
            code="snapshot_schema_invalid",
            label="public snapshot",
        ),
        code="snapshot_schema_invalid",
        label="public snapshot column_mapping",
    )
    for field_name in _SNAPSHOT_COLUMN_MAPPING_FIELDS:
        if field_name not in column_mapping:
            raise PublicTargetError(
                "snapshot_schema_invalid",
                f"public snapshot column_mapping is missing {field_name!r}",
                "Pin row identity, rank metric, dataset, split, and scope mappings.",
            )
    metric_units = _string_mapping(
        _required_mapping(
            snapshot,
            "metric_units",
            code="snapshot_schema_invalid",
            label="public snapshot",
        ),
        code="snapshot_schema_invalid",
        label="public snapshot metric_units",
    )
    if rank_metric not in metric_units:
        raise PublicTargetError(
            "snapshot_schema_invalid",
            f"metric_units must declare the official rank metric {rank_metric!r}",
            "Pin rank metric units before comparing public snapshots.",
        )
    benchmark_type = _required_string(
        snapshot,
        "benchmark_type",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    dataset = _required_string(
        snapshot,
        "dataset",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    split = _required_string(
        snapshot,
        "split",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    scope = _required_string(
        snapshot,
        "scope",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    required_columns = _string_list(
        snapshot,
        "required_columns",
        code="snapshot_schema_invalid",
        label="public snapshot",
    )
    rows = _read_snapshot_rows(
        raw_path,
        row_count=row_count,
        required_columns=required_columns,
        column_mapping=column_mapping,
        rank_metric=rank_metric,
        expected_values={"dataset": dataset, "split": split, "scope": scope},
    )
    return PublicSnapshot(
        path=snapshot_path,
        raw_path=raw_path,
        raw_sha256=expected_sha256,
        source_url=source_url,
        request_command=request_command,
        retrieved_at=_required_string(
            snapshot,
            "retrieved_at",
            code="snapshot_schema_invalid",
            label="public snapshot",
        ),
        target_role=target_role,
        benchmark_type=benchmark_type,
        dataset=dataset,
        split=split,
        scope=scope,
        row_count=row_count,
        byte_count=byte_count,
        source_schema_version=source_schema_version,
        rank_metric=rank_metric,
        rank_order=rank_order,
        metric_units=metric_units,
        column_mapping=column_mapping,
        rows=rows,
    )


def _string_mapping(payload: Mapping[str, object], *, code: str, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        if isinstance(raw_key, str) and isinstance(raw_value, str) and raw_value.strip():
            result[raw_key] = raw_value.strip()
    if len(result) == len(payload):
        return result
    raise PublicTargetError(
        code,
        f"{label} must map strings to non-empty strings",
        "Use explicit, non-empty schema mapping strings.",
    )


def _read_snapshot_rows(
    raw_path: Path,
    *,
    row_count: int,
    required_columns: Sequence[str],
    column_mapping: Mapping[str, str],
    rank_metric: str,
    expected_values: Mapping[str, str],
) -> tuple[dict[str, str], ...]:
    try:
        with raw_path.open(newline="", encoding="utf-8") as handle:
            rows = tuple(dict(row) for row in csv.DictReader(handle))
    except OSError as exc:
        raise PublicTargetError(
            "snapshot_raw_unreadable",
            f"could not read public snapshot CSV: {raw_path}",
            "Keep immutable raw snapshot bytes available beside the sidecar.",
        ) from exc
    if len(rows) != row_count:
        raise PublicTargetError(
            "snapshot_row_count_mismatch",
            f"snapshot row_count={row_count} but raw CSV has {len(rows)} row(s)",
            "Record the exact public snapshot row count.",
        )
    headers = set(rows[0]) if rows else set()
    missing_columns = sorted(set(required_columns) - headers)
    mapped_columns = set(column_mapping.values())
    missing_mapped_columns = sorted(mapped_columns - headers)
    if missing_columns or missing_mapped_columns:
        missing = ", ".join(missing_columns + missing_mapped_columns)
        raise PublicTargetError(
            "snapshot_schema_invalid",
            f"snapshot raw CSV is missing required column(s): {missing}",
            "Update the source schema version and column mapping for changed public snapshots.",
        )
    rank_column = column_mapping["rank_metric"]
    if rank_column != rank_metric:
        raise PublicTargetError(
            "snapshot_schema_invalid",
            "rank_metric must match column_mapping.rank_metric for this pinned schema",
            "Keep the official rank basis explicit and unambiguous.",
        )
    for index, row in enumerate(rows, start=2):
        for field_name, expected_value in expected_values.items():
            column_name = column_mapping[field_name]
            observed_value = row[column_name]
            if observed_value != expected_value:
                raise PublicTargetError(
                    "snapshot_row_mismatch",
                    f"snapshot row {index} has {field_name}={observed_value!r}; "
                    f"expected {expected_value!r}",
                    "Use a snapshot whose row dataset, split, and scope match the sidecar.",
                )
        try:
            float(row[rank_column])
        except (TypeError, ValueError) as exc:
            raise PublicTargetError(
                "snapshot_schema_invalid",
                f"snapshot row {index} has non-numeric rank metric {rank_column!r}",
                "Use the official numeric rank metric column.",
            ) from exc
    return tuple(cast("dict[str, str]", row) for row in rows)


def load_dataset_version(path: Path) -> DatasetVersion:
    """Read and validate the current dataset version ledger entry."""
    ledger_path = path.expanduser().resolve()
    ledger = _read_json_object(ledger_path, label="dataset version ledger")
    _validate_schema(
        ledger,
        DATASET_VERSION_LEDGER_SCHEMA_VERSION,
        code="dataset_ledger_invalid",
        label="dataset version ledger",
    )
    dataset_id = _required_string(
        ledger,
        "dataset_id",
        code="dataset_ledger_invalid",
        label="dataset version ledger",
    )
    current_version = _required_string(
        ledger,
        "current_version",
        code="dataset_ledger_invalid",
        label="dataset version ledger",
    )
    entries = _required_list(
        ledger,
        "entries",
        code="dataset_ledger_invalid",
        label="dataset version ledger",
    )
    matching_entry: dict[str, object] | None = None
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            continue
        entry = cast("dict[str, object]", raw_entry)
        if entry.get("version") == current_version:
            matching_entry = entry
            break
    if matching_entry is None:
        raise PublicTargetError(
            "dataset_version_missing",
            f"dataset ledger has no entry for current_version {current_version!r}",
            "Add a current version entry before using new corpus/case hashes for claims.",
        )
    for field_name in _HASH_FIELDS:
        _validate_hash(
            matching_entry.get(field_name),
            field_name=field_name,
            code="dataset_ledger_invalid",
            label="dataset version ledger entry",
        )
    for field_name in ("role", "diff_summary", "edit_rationale"):
        _required_string(
            matching_entry,
            field_name,
            code="dataset_ledger_invalid",
            label="dataset version ledger entry",
        )
    if not _required_bool(
        matching_entry,
        "recorded_before_claim",
        code="dataset_ledger_invalid",
        label="dataset version ledger entry",
    ):
        raise PublicTargetError(
            "dataset_version_not_predeclared",
            "dataset version entry must be recorded_before_claim=true",
            "Record dataset edits, rationale, and role before claim generation.",
        )
    return DatasetVersion(
        ledger_path=ledger_path,
        dataset_id=dataset_id,
        version=current_version,
        entry=matching_entry,
    )


def load_evaluation_plan(path: Path) -> EvaluationPlan:
    """Read and validate a predeclared public-target evaluation plan."""
    plan_path = path.expanduser().resolve()
    plan = _read_json_object(plan_path, label="evaluation plan")
    _validate_schema(
        plan,
        EVALUATION_PLAN_SCHEMA_VERSION,
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    if not _required_bool(
        plan,
        "declared_before_results",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    ):
        raise PublicTargetError(
            "evaluation_plan_not_predeclared",
            "evaluation plan must set declared_before_results=true",
            "Record the plan before selecting final result metrics or modes.",
        )
    primary_metrics = _string_list(
        plan,
        "primary_metrics",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    secondary_metrics = _string_list(
        plan,
        "secondary_metrics",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    top_k_values = _int_list(
        plan,
        "top_k_values",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    candidate_depth_values = _int_list(
        plan,
        "candidate_depth_values",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    statistical_method = _required_string(
        plan,
        "statistical_method",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    _validate_statistical_method(statistical_method)
    run_policy = _required_string(
        plan,
        "run_policy",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    _required_string(
        plan,
        "mode_selection_policy",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    failure_handling = _required_string(
        plan,
        "failure_handling",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    raw_seed_policy = _required_list(
        plan,
        "seed_policy",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    seed_policy = tuple(item for item in raw_seed_policy if isinstance(item, int))
    if len(seed_policy) != len(raw_seed_policy):
        raise PublicTargetError(
            "evaluation_plan_invalid",
            "evaluation plan seed_policy must contain integer seed values",
            "Record every attempted run seed as an integer.",
        )
    baseline_improvement = _required_mapping(
        plan,
        "baseline_improvement",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    known_public_target = _required_mapping(
        plan,
        "known_public_target",
        code="evaluation_plan_invalid",
        label="evaluation plan",
    )
    _required_bool(
        known_public_target,
        "optimized_against_public_target",
        code="evaluation_plan_invalid",
        label="evaluation plan known_public_target",
    )
    _required_string(
        known_public_target,
        "limitation",
        code="evaluation_plan_invalid",
        label="evaluation plan known_public_target",
    )
    primary_metric = _required_string(
        baseline_improvement,
        "primary_metric",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    if primary_metric not in primary_metrics:
        raise PublicTargetError(
            "evaluation_plan_invalid",
            f"baseline improvement primary metric {primary_metric!r} is not predeclared",
            "Add the primary improvement metric to primary_metrics before running claims.",
        )
    guardrail_metrics = _required_list(
        baseline_improvement,
        "guardrail_metrics",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    declared_metrics = {*primary_metrics, *secondary_metrics}
    for raw_guardrail in guardrail_metrics:
        if not isinstance(raw_guardrail, dict):
            raise PublicTargetError(
                "evaluation_plan_invalid",
                "guardrail_metrics entries must be objects",
                "Declare each guardrail as an object with metric and tolerance.",
            )
        guardrail = cast("dict[str, object]", raw_guardrail)
        metric = _required_string(
            guardrail,
            "metric",
            code="evaluation_plan_invalid",
            label="evaluation plan guardrail",
        )
        _required_number(
            guardrail,
            "tolerance",
            code="evaluation_plan_invalid",
            label="evaluation plan guardrail",
        )
        if metric not in declared_metrics:
            raise PublicTargetError(
                "evaluation_plan_invalid",
                f"guardrail metric {metric!r} is not predeclared",
                "List guardrails in primary_metrics or secondary_metrics before use.",
            )
    return EvaluationPlan(
        path=plan_path,
        plan_id=_required_string(
            plan,
            "plan_id",
            code="evaluation_plan_invalid",
            label="evaluation plan",
        ),
        primary_target=_required_string(
            plan,
            "primary_target",
            code="evaluation_plan_invalid",
            label="evaluation plan",
        ),
        primary_metrics=primary_metrics,
        secondary_metrics=secondary_metrics,
        top_k_values=top_k_values,
        candidate_depth_values=candidate_depth_values,
        statistical_method=statistical_method,
        run_policy=run_policy,
        seed_policy=seed_policy,
        failure_handling=failure_handling,
        baseline_improvement=baseline_improvement,
        known_public_target=known_public_target,
    )


def _validate_statistical_method(statistical_method: str) -> None:
    normalized = statistical_method.casefold()
    has_pairing = "paired" in normalized or "unpaired" in normalized
    has_uncertainty = any(
        term in normalized
        for term in (
            "bootstrap",
            "confidence",
            "ci",
            "mcnemar",
            "permutation",
            "randomization",
            "within noise",
        )
    )
    if not has_pairing or not has_uncertainty:
        raise PublicTargetError(
            "evaluation_plan_invalid",
            "evaluation plan statistical_method must declare pairing and uncertainty method",
            "Use paired bootstrap/McNemar/randomization wording or an explicit "
            "aggregate-only limitation.",
        )
    if "aggregate percentages only" in normalized:
        raise PublicTargetError(
            "evaluation_plan_invalid",
            "evaluation plan statistical_method cannot rely on aggregate percentages only",
            "Use per-query paired evidence for direct improvement, rank, or superiority claims.",
        )


def _metric_value(report: Mapping[str, object], metric_path: str) -> float:
    value: object = report
    for part in metric_path.split("."):
        if not isinstance(value, dict):
            raise PublicTargetError(
                "metric_missing",
                f"metric path {metric_path!r} is missing from report",
                "Ensure all selected and guardrail metrics are present in both reports.",
            )
        value = value.get(part)
    if isinstance(value, bool):
        value = None
    if isinstance(value, int | float):
        return float(value)
    raise PublicTargetError(
        "metric_missing",
        f"metric path {metric_path!r} is not numeric",
        "Ensure all selected and guardrail metrics are numeric in both reports.",
    )


def _report_metadata_value(report: Mapping[str, object], field_name: str) -> object:
    if field_name == "candidate_depth":
        try:
            return _integer_metadata_value(report, "top_k") * _integer_metadata_value(
                report,
                "candidate_multiplier",
            )
        except PublicTargetError:
            return None
    if field_name == "metric_formulas_sha256":
        return metric_formulas_sha256(report)
    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        return None
    typed_metadata = cast("dict[str, object]", metadata)
    if field_name in typed_metadata:
        return typed_metadata[field_name]
    if field_name == "prompt_hash":
        return "retrieval-only-no-prompt"
    if field_name == "permission_scope":
        return "public-benchmark-materials"
    fixed_parameters = typed_metadata.get("fixed_parameters")
    if isinstance(fixed_parameters, dict):
        return cast("dict[str, object]", fixed_parameters).get(field_name)
    return None


def _integer_metadata_value(report: Mapping[str, object], field_name: str) -> int:
    value = _report_metadata_value(report, field_name)
    if isinstance(value, bool):
        value = None
    if isinstance(value, int):
        return value
    raise PublicTargetError(
        "report_metadata_missing",
        f"current report is missing integer metadata field {field_name!r}",
        "Record predeclared top-k and candidate-depth inputs in report metadata.",
    )


def _validate_claim_report(report: Mapping[str, object], *, label: str) -> None:
    status = _required_string(
        report,
        "status",
        code="claim_report_incomplete",
        label=f"{label} report",
    )
    if status != "success":
        raise PublicTargetError(
            "claim_report_not_success",
            f"{label} report status must be success, got {status!r}",
            "Only successful benchmark reports may enter public target claim gates.",
        )
    metadata = _required_mapping(
        report,
        "metadata",
        code="claim_report_incomplete",
        label=f"{label} report",
    )
    for field_name in ("command_invocation", "model", "network_state", "cache_state"):
        _required_string(
            metadata,
            field_name,
            code="claim_report_incomplete",
            label=f"{label} report metadata",
        )
    aggregate_metrics = _required_mapping(
        report,
        "aggregate_metrics",
        code="claim_report_incomplete",
        label=f"{label} report",
    )
    query_count = _required_int(
        aggregate_metrics,
        "query_count",
        code="claim_report_incomplete",
        label=f"{label} report aggregate_metrics",
    )
    if query_count <= 0:
        raise PublicTargetError(
            "claim_report_incomplete",
            f"{label} report query_count must be positive",
            "Run the benchmark over a non-empty public target case set.",
        )
    per_query_count = _per_query_row_count(report)
    if per_query_count != query_count:
        raise PublicTargetError(
            "claim_report_incomplete",
            f"{label} report per-query rows do not reconcile with query_count={query_count}",
            "Regenerate the report with complete per-query rows for paired claim evidence.",
        )
    envelope_result = claim_report_envelope.validate_claim_report_envelope(
        report,
        require_claim_eligible=True,
    )
    if envelope_result.errors:
        raise PublicTargetError(
            "claim_report_envelope_invalid",
            f"{label} report envelope is invalid: " + "; ".join(envelope_result.errors[:5]),
            "Regenerate the benchmark report with the current claim envelope schema "
            "and reproducibility validation enabled.",
        )


def _per_query_row_count(report: Mapping[str, object]) -> int | None:
    raw_benchmarks = report.get("benchmarks")
    if not isinstance(raw_benchmarks, list):
        return None
    row_count = 0
    saw_rows = False
    for raw_benchmark in raw_benchmarks:
        if not isinstance(raw_benchmark, dict):
            continue
        benchmark = cast("dict[str, object]", raw_benchmark)
        per_query_results = benchmark.get("per_query_results")
        if isinstance(per_query_results, list):
            saw_rows = True
            row_count += len(per_query_results)
    return row_count if saw_rows else None


def _per_query_rows(report: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    raw_benchmarks = report.get("benchmarks")
    if not isinstance(raw_benchmarks, list):
        return ()
    rows: list[dict[str, object]] = []
    for raw_benchmark in raw_benchmarks:
        if not isinstance(raw_benchmark, dict):
            continue
        benchmark = cast("dict[str, object]", raw_benchmark)
        per_query_results = benchmark.get("per_query_results")
        if not isinstance(per_query_results, list):
            continue
        rows.extend(
            cast("dict[str, object]", raw_result)
            for raw_result in per_query_results
            if isinstance(raw_result, dict)
        )
    return tuple(rows)


def _per_query_hash(rows: Sequence[Mapping[str, object]]) -> str:
    serialized = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _paired_rows(
    baseline_report: Mapping[str, object],
    current_report: Mapping[str, object],
) -> tuple[tuple[tuple[dict[str, object], dict[str, object]], ...], list[str]]:
    baseline_rows = _per_query_rows(baseline_report)
    current_rows = _per_query_rows(current_report)
    failures: list[str] = []
    if not baseline_rows or not current_rows:
        return (), ["statistical evidence missing per-query rows"]
    baseline_by_id = _rows_by_case_id(baseline_rows, label="baseline", failures=failures)
    current_by_id = _rows_by_case_id(current_rows, label="current", failures=failures)
    if failures:
        return (), failures
    baseline_ids = set(baseline_by_id)
    current_ids = set(current_by_id)
    if baseline_ids != current_ids:
        failures.append("statistical evidence missing paired per-query rows")
        return (), failures
    paired = tuple(
        (baseline_by_id[case_id], current_by_id[case_id]) for case_id in sorted(baseline_ids)
    )
    return paired, []


def _rows_by_case_id(
    rows: Sequence[dict[str, object]],
    *,
    label: str,
    failures: list[str],
) -> dict[str, dict[str, object]]:
    by_id: dict[str, dict[str, object]] = {}
    for index, row in enumerate(rows, start=1):
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            failures.append(f"{label} per-query row {index} is missing case_id")
            continue
        if case_id in by_id:
            failures.append(f"{label} per-query rows contain duplicate case_id {case_id!r}")
            continue
        by_id[case_id] = row
    return by_id


def _statistical_evidence(
    plan: EvaluationPlan,
    baseline_report: Mapping[str, object],
    current_report: Mapping[str, object],
    *,
    metric_paths: Sequence[str],
    primary_metric: str,
) -> dict[str, object]:
    paired, failures = _paired_rows(baseline_report, current_report)
    baseline_rows = _per_query_rows(baseline_report)
    current_rows = _per_query_rows(current_report)
    if failures:
        return {
            "status": "failed",
            "pairing": "unpaired",
            "failures": failures,
            "sample_size": 0,
            "baseline_per_query_sha256": _per_query_hash(baseline_rows),
            "current_per_query_sha256": _per_query_hash(current_rows),
            "method_policy": plan.statistical_method,
        }

    methods: dict[str, object] = {}
    uncertainty: dict[str, object] = {}
    metric_failures: list[str] = []
    for metric_path in metric_paths:
        deltas = _paired_metric_deltas(paired, metric_path)
        if not deltas:
            metric_failures.append(f"missing per-query metric values for {metric_path}")
            continue
        lower, upper = _empirical_interval(deltas)
        methods[metric_path] = {
            "method": _metric_method(metric_path),
            "paired": True,
            "sample_size": len(deltas),
        }
        uncertainty[metric_path] = {
            "mean_delta": sum(deltas) / len(deltas),
            "confidence_interval": [lower, upper],
            "within_noise": lower <= 0.0 <= upper,
        }

    primary_deltas = _paired_metric_deltas(paired, primary_metric)
    wins = sum(1 for delta in primary_deltas if delta > 0)
    losses = sum(1 for delta in primary_deltas if delta < 0)
    ties = sum(1 for delta in primary_deltas if delta == 0)
    hit_miss = _hit_miss_counts(paired)
    return {
        "status": "passed" if not metric_failures else "failed",
        "pairing": "paired",
        "method_policy": plan.statistical_method,
        "sample_size": len(paired),
        "baseline_per_query_sha256": _per_query_hash(baseline_rows),
        "current_per_query_sha256": _per_query_hash(current_rows),
        "methods": methods,
        "uncertainty": uncertainty,
        "win_loss_tie": {"wins": wins, "losses": losses, "ties": ties},
        "hit_miss_table": hit_miss,
        "claim_wording": (
            "within noise"
            if any(
                isinstance(item, dict) and item.get("within_noise") is True
                for item in uncertainty.values()
            )
            else "paired directional delta with uncertainty"
        ),
        "failures": metric_failures,
    }


def _paired_metric_deltas(
    paired_rows: Sequence[tuple[dict[str, object], dict[str, object]]],
    metric_path: str,
) -> list[float]:
    deltas: list[float] = []
    for baseline_row, current_row in paired_rows:
        baseline_value = _per_query_metric_value(baseline_row, metric_path)
        current_value = _per_query_metric_value(current_row, metric_path)
        if baseline_value is None or current_value is None:
            continue
        deltas.append(current_value - baseline_value)
    return deltas


def _per_query_metric_value(row: Mapping[str, object], metric_path: str) -> float | None:
    metric_name = metric_path.rsplit(".", 1)[-1]
    if metric_name == "hit_rate":
        return 1.0 if row.get("hit") is True else 0.0
    if metric_name == "mrr":
        reciprocal_rank = _number_or_none(row.get("reciprocal_rank"))
        if reciprocal_rank is not None:
            return reciprocal_rank
        rank = _number_or_none(row.get("rank"))
        if rank is not None and rank > 0:
            return 1.0 / rank
        return 0.0
    value = _number_or_none(row.get(metric_name))
    if value is not None:
        return value
    if metric_name == "expected_recall":
        return _number_or_none(row.get("recall_at_k"))
    return None


def _metric_method(metric_path: str) -> str:
    metric_name = metric_path.rsplit(".", 1)[-1]
    if metric_name == "hit_rate":
        return "paired_hit_miss_mcnemar_inputs"
    return "paired_empirical_ci"


def _empirical_interval(values: Sequence[float]) -> tuple[float, float]:
    ordered = sorted(values)
    if not ordered:
        return 0.0, 0.0
    lower_index = math.floor(0.025 * (len(ordered) - 1))
    upper_index = math.ceil(0.975 * (len(ordered) - 1))
    return ordered[lower_index], ordered[upper_index]


def _hit_miss_counts(
    paired_rows: Sequence[tuple[dict[str, object], dict[str, object]]],
) -> dict[str, int]:
    both_hit = baseline_only = current_only = both_miss = 0
    for baseline_row, current_row in paired_rows:
        baseline_hit = baseline_row.get("hit") is True
        current_hit = current_row.get("hit") is True
        if baseline_hit and current_hit:
            both_hit += 1
        elif baseline_hit:
            baseline_only += 1
        elif current_hit:
            current_only += 1
        else:
            both_miss += 1
    return {
        "both_hit": both_hit,
        "baseline_only": baseline_only,
        "current_only": current_only,
        "both_miss": both_miss,
    }


def _number_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _object_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _validate_report_metadata(
    report: Mapping[str, object],
    expected_metadata: Mapping[str, object],
    *,
    label: str,
) -> list[dict[str, object]]:
    mismatches: list[dict[str, object]] = []
    for field_name in _MATCHED_METADATA_FIELDS:
        expected = expected_metadata.get(field_name)
        observed = _report_metadata_value(report, field_name)
        if observed != expected:
            mismatches.append(
                {
                    "field": field_name,
                    "expected": expected,
                    "observed": observed,
                    "report": label,
                }
            )
    return mismatches


def _validate_dataset_matches(
    dataset_version: DatasetVersion,
    matched_metadata: Mapping[str, object],
) -> list[dict[str, object]]:
    mismatches: list[dict[str, object]] = []
    for field_name in _HASH_FIELDS:
        expected = dataset_version.entry.get(field_name)
        observed = matched_metadata.get(field_name)
        if observed != expected:
            mismatches.append(
                {
                    "field": field_name,
                    "expected": expected,
                    "observed": observed,
                    "source": "dataset_ledger_vs_baseline_ledger",
                }
            )
    return mismatches


def _guardrail_results(
    plan: EvaluationPlan,
    baseline_report: Mapping[str, object],
    current_report: Mapping[str, object],
) -> tuple[GuardrailResult, ...]:
    guardrails = _required_list(
        plan.baseline_improvement,
        "guardrail_metrics",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    results: list[GuardrailResult] = []
    for raw_guardrail in guardrails:
        guardrail = cast("dict[str, object]", raw_guardrail)
        metric = _required_string(
            guardrail,
            "metric",
            code="evaluation_plan_invalid",
            label="evaluation plan guardrail",
        )
        tolerance = _required_number(
            guardrail,
            "tolerance",
            code="evaluation_plan_invalid",
            label="evaluation plan guardrail",
        )
        baseline = _metric_value(baseline_report, metric)
        current = _metric_value(current_report, metric)
        delta = current - baseline
        results.append(
            GuardrailResult(
                metric=metric,
                baseline=baseline,
                current=current,
                delta=delta,
                tolerance=tolerance,
                passed=delta + tolerance >= 0,
            )
        )
    return tuple(results)


def _run_disclosure(
    plan: EvaluationPlan,
    baseline_report: Mapping[str, object],
    current_report: Mapping[str, object],
    *,
    primary_metric: str,
) -> dict[str, object]:
    attempts = [
        _attempt_disclosure("baseline", baseline_report),
        _attempt_disclosure("current", current_report),
    ]
    failed_count = sum(1 for attempt in attempts if attempt["status"] != "success")
    primary_values = [
        value
        for row in _per_query_rows(current_report)
        if (value := _per_query_metric_value(row, primary_metric)) is not None
    ]
    return {
        "status": "passed",
        "run_count": len(attempts),
        "successful_count": len(attempts) - failed_count,
        "failed_count": failed_count,
        "denominator": len(attempts),
        "seed_policy": list(plan.seed_policy),
        "run_policy": plan.run_policy,
        "failure_handling": plan.failure_handling,
        "attempts": attempts,
        "variance": {
            "metric": primary_metric,
            "sample_size": len(primary_values),
            "value": _variance(primary_values),
        },
    }


def _attempt_disclosure(label: str, report: Mapping[str, object]) -> dict[str, object]:
    return {
        "label": label,
        "report_id": _report_id(report),
        "status": report.get("status", "unknown"),
        "random_seed": _report_seed(report),
        "query_count": _report_query_count(report),
        "claim_eligible": _report_claim_eligible(report),
    }


def _report_seed(report: Mapping[str, object]) -> object:
    metadata = report.get("metadata")
    if isinstance(metadata, dict):
        fixed_parameters = cast("dict[str, object]", metadata).get("fixed_parameters")
        if isinstance(fixed_parameters, dict):
            return cast("dict[str, object]", fixed_parameters).get("random_seed", "unknown")
    return "unknown"


def _report_query_count(report: Mapping[str, object]) -> int:
    aggregate_metrics = report.get("aggregate_metrics")
    if isinstance(aggregate_metrics, dict):
        value = cast("dict[str, object]", aggregate_metrics).get("query_count")
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return len(_per_query_rows(report))


def _report_claim_eligible(report: Mapping[str, object]) -> bool:
    claim_envelope = report.get("claim_envelope")
    if isinstance(claim_envelope, dict):
        return cast("dict[str, object]", claim_envelope).get("claim_eligible") is True
    return False


def _variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _claim_language_result(claim_text: str | None) -> dict[str, object]:
    text = claim_text or ""
    findings = claim_report_envelope.claim_language_findings(text, path="claim_text")
    return {
        "status": "passed" if not findings else "failed",
        "checked": bool(text),
        "findings": list(findings),
        "policy": (
            "Use scoped matched-comparison wording; avoid unsupported beats/wins/"
            "outperforms/best/superiority language."
        ),
    }


def _public_rank(
    snapshot: PublicSnapshot,
    *,
    current_value: float,
) -> tuple[int, int]:
    rank_column = snapshot.column_mapping["rank_metric"]
    values = [_snapshot_metric_value(snapshot, row[rank_column]) for row in snapshot.rows]
    values.append(current_value)
    reverse = snapshot.rank_order == "descending"
    ordered = sorted(values, reverse=reverse)
    return ordered.index(current_value) + 1, len(ordered)


def _snapshot_metric_value(snapshot: PublicSnapshot, raw_value: str) -> float:
    value = float(raw_value)
    if snapshot.metric_units.get(snapshot.rank_metric) == "percent":
        return value / 100
    return value


def _comparison_dict(
    metric: str,
    baseline_report: Mapping[str, object],
    current_report: Mapping[str, object],
) -> dict[str, object]:
    baseline = _metric_value(baseline_report, metric)
    current = _metric_value(current_report, metric)
    return {
        "metric": metric,
        "baseline": baseline,
        "current": current,
        "delta": current - baseline,
    }


def run_claim_gate(
    *,
    baseline_ledger_path: Path,
    current_report_path: Path,
    public_snapshot_path: Path,
    dataset_ledger_path: Path,
    evaluation_plan_path: Path,
    claim_text: str | None = None,
) -> tuple[dict[str, object], int]:
    """Run the baseline/public-target claim gate and return payload plus exit code."""
    baseline = load_baseline_ledger(baseline_ledger_path)
    baseline_pre_sha256 = _sha256_file(baseline.artifact_path)
    current_path = current_report_path.expanduser().resolve()
    current_report = _read_json_object(current_path, label="current benchmark report")
    current_report_sha256 = _sha256_file(current_path)
    snapshot = load_public_snapshot(public_snapshot_path)
    dataset_version = load_dataset_version(dataset_ledger_path)
    plan = load_evaluation_plan(evaluation_plan_path)
    _validate_claim_report(baseline.baseline_report, label="baseline")
    _validate_claim_report(current_report, label="current")

    if plan.primary_target != snapshot.dataset:
        raise PublicTargetError(
            "evaluation_plan_invalid",
            f"evaluation plan primary_target={plan.primary_target!r} does not match snapshot",
            "Use the predeclared plan for the exact public target being compared.",
        )
    if dataset_version.dataset_id != snapshot.dataset:
        raise PublicTargetError(
            "dataset_target_mismatch",
            f"dataset ledger dataset_id={dataset_version.dataset_id!r} does not match snapshot",
            "Use a dataset ledger entry for the same public target snapshot and reports.",
        )
    if baseline.matched_metadata.get("dataset") != snapshot.dataset:
        raise PublicTargetError(
            "dataset_target_mismatch",
            "baseline matched_metadata dataset does not match the public snapshot dataset",
            "Use matched baseline, current report, dataset ledger, and snapshot target IDs.",
        )
    if baseline.baseline_id != _required_string(
        plan.baseline_improvement,
        "baseline_id",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    ):
        raise PublicTargetError(
            "evaluation_plan_invalid",
            "evaluation plan baseline_id does not match the frozen baseline ledger",
            "Use the predeclared plan for the frozen baseline artifact.",
        )
    declared_metrics = {*plan.primary_metrics, *plan.secondary_metrics}
    missing_planned_metrics = [
        metric for metric in baseline.selected_metrics if metric not in declared_metrics
    ]
    if missing_planned_metrics:
        raise PublicTargetError(
            "evaluation_plan_invalid",
            "baseline selected metric(s) were not predeclared: "
            + ", ".join(missing_planned_metrics),
            "Add selected metrics to primary_metrics or secondary_metrics before claims.",
        )

    metadata_mismatches = []
    metadata_mismatches.extend(
        _validate_report_metadata(
            baseline.baseline_report,
            baseline.matched_metadata,
            label="baseline",
        )
    )
    metadata_mismatches.extend(
        _validate_report_metadata(
            current_report,
            baseline.matched_metadata,
            label="current",
        )
    )
    metadata_mismatches.extend(
        _validate_dataset_matches(dataset_version, baseline.matched_metadata)
    )
    current_top_k = _integer_metadata_value(current_report, "top_k")
    current_candidate_multiplier = _integer_metadata_value(current_report, "candidate_multiplier")
    current_candidate_depth = current_top_k * current_candidate_multiplier
    plan_mismatches: list[dict[str, object]] = []
    if current_top_k not in plan.top_k_values:
        plan_mismatches.append(
            {
                "field": "top_k",
                "observed": current_top_k,
                "predeclared": list(plan.top_k_values),
            }
        )
    if current_candidate_depth not in plan.candidate_depth_values:
        plan_mismatches.append(
            {
                "field": "candidate_depth",
                "observed": current_candidate_depth,
                "predeclared": list(plan.candidate_depth_values),
            }
        )

    selected_comparisons = [
        _comparison_dict(metric, baseline.baseline_report, current_report)
        for metric in baseline.selected_metrics
    ]
    primary_metric = _required_string(
        plan.baseline_improvement,
        "primary_metric",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    minimum_delta = _required_number(
        plan.baseline_improvement,
        "minimum_delta",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    tolerance = _required_number(
        plan.baseline_improvement,
        "tolerance",
        code="evaluation_plan_invalid",
        label="evaluation plan baseline_improvement",
    )
    primary_baseline = _metric_value(baseline.baseline_report, primary_metric)
    primary_current = _metric_value(current_report, primary_metric)
    primary_delta = primary_current - primary_baseline
    primary_passed = primary_delta + tolerance >= minimum_delta
    guardrails = _guardrail_results(plan, baseline.baseline_report, current_report)
    metric_paths = tuple(dict.fromkeys((*baseline.selected_metrics, primary_metric)))
    statistical_evidence = _statistical_evidence(
        plan,
        baseline.baseline_report,
        current_report,
        metric_paths=metric_paths,
        primary_metric=primary_metric,
    )
    run_disclosure = _run_disclosure(
        plan,
        baseline.baseline_report,
        current_report,
        primary_metric=primary_metric,
    )
    claim_language = _claim_language_result(claim_text)

    failures: list[str] = []
    if metadata_mismatches:
        failures.append("matched metadata did not match baseline/dataset ledger")
    if plan_mismatches:
        failures.append("current run used an unplanned top-k or candidate-depth value")
    if statistical_evidence["status"] != "passed":
        failures.extend(str(item) for item in _object_list(statistical_evidence.get("failures")))
    if claim_language["status"] != "passed":
        failures.append("unsupported competitive language in proposed claim text")
    if not primary_passed:
        failures.append("primary improvement did not meet the predeclared minimum delta")
    failures.extend(
        f"guardrail metric {guardrail.metric} regressed beyond tolerance"
        for guardrail in guardrails
        if not guardrail.passed
    )

    baseline_post_sha256 = _sha256_file(baseline.artifact_path)
    if baseline_post_sha256 != baseline_pre_sha256:
        raise PublicTargetError(
            "baseline_mutated_during_gate",
            f"baseline artifact hash changed during claim gate: {baseline.artifact_path}",
            "Do not regenerate or edit the frozen baseline during comparison.",
        )

    rank, total = _public_rank(snapshot, current_value=primary_current)
    status = "passed" if not failures else "failed"
    payload: dict[str, object] = {
        "schema_version": CLAIM_GATE_SCHEMA_VERSION,
        "status": status,
        "baseline": {
            "ledger_path": str(baseline.path),
            "artifact_path": str(baseline.artifact_path),
            "baseline_id": baseline.baseline_id,
            "baseline_version": baseline.baseline_version,
            "target_role": baseline.target_role,
            "pre_sha256": baseline_pre_sha256,
            "post_sha256": baseline_post_sha256,
            "immutable": baseline_pre_sha256 == baseline_post_sha256 == baseline.artifact_sha256,
            "selected_metrics": list(baseline.selected_metrics),
        },
        "current_report": {
            "path": str(current_path),
            "sha256": current_report_sha256,
            "report_id": _report_id(current_report),
        },
        "public_snapshot": {
            "path": str(snapshot.path),
            "raw_path": str(snapshot.raw_path),
            "source_url": snapshot.source_url,
            "request_command": snapshot.request_command,
            "retrieved_at": snapshot.retrieved_at,
            "raw_sha256": snapshot.raw_sha256,
            "byte_count": snapshot.byte_count,
            "row_count": snapshot.row_count,
            "target_role": snapshot.target_role,
            "benchmark_type": snapshot.benchmark_type,
            "dataset": snapshot.dataset,
            "split": snapshot.split,
            "scope": snapshot.scope,
            "source_schema_version": snapshot.source_schema_version,
            "rank_metric": snapshot.rank_metric,
            "rank_order": snapshot.rank_order,
            "metric_units": snapshot.metric_units,
            "column_mapping": snapshot.column_mapping,
        },
        "dataset_version": {
            "ledger_path": str(dataset_version.ledger_path),
            "dataset_id": dataset_version.dataset_id,
            "version": dataset_version.version,
            "role": dataset_version.entry["role"],
            "manifest_sha256": dataset_version.entry["manifest_sha256"],
            "cases_sha256": dataset_version.entry["cases_sha256"],
            "qrels_sha256": dataset_version.entry["qrels_sha256"],
            "corpus_sha256": dataset_version.entry["corpus_sha256"],
            "diff_summary": dataset_version.entry["diff_summary"],
            "edit_rationale": dataset_version.entry["edit_rationale"],
        },
        "evaluation_plan": {
            "path": str(plan.path),
            "sha256": _sha256_file(plan.path),
            "plan_id": plan.plan_id,
            "predeclared": True,
            "primary_target": plan.primary_target,
            "primary_metrics": list(plan.primary_metrics),
            "secondary_metrics": list(plan.secondary_metrics),
            "top_k_values": list(plan.top_k_values),
            "candidate_depth_values": list(plan.candidate_depth_values),
        },
        "known_public_target": dict(plan.known_public_target),
        "matched_metadata": {
            "status": "passed" if not metadata_mismatches else "failed",
            "mismatches": metadata_mismatches,
            "expected": dict(baseline.matched_metadata),
        },
        "predeclared_run_parameters": {
            "status": "passed" if not plan_mismatches else "failed",
            "mismatches": plan_mismatches,
            "top_k": current_top_k,
            "candidate_depth": current_candidate_depth,
        },
        "baseline_improvement": {
            "primary_metric": primary_metric,
            "primary_metric_delta": primary_delta,
            "minimum_delta": minimum_delta,
            "tolerance": tolerance,
            "primary_passed": primary_passed,
            "selected_metric_comparisons": selected_comparisons,
            "guardrails": [
                {
                    "metric": guardrail.metric,
                    "baseline": guardrail.baseline,
                    "current": guardrail.current,
                    "delta": guardrail.delta,
                    "tolerance": guardrail.tolerance,
                    "passed": guardrail.passed,
                }
                for guardrail in guardrails
            ],
        },
        "statistical_evidence": statistical_evidence,
        "run_disclosure": run_disclosure,
        "claim_language": claim_language,
        "public_comparison_summary": {
            "snapshot_source": snapshot.source_url,
            "snapshot_date": snapshot.retrieved_at,
            "snapshot_hash": snapshot.raw_sha256,
            "rank_metric": snapshot.rank_metric,
            "current_metric": primary_metric,
            "current_metric_value": primary_current,
            "current_rank_in_snapshot": rank,
            "snapshot_rank_denominator": total,
            "uncertainty": statistical_evidence,
            "limitations": _required_string(
                plan.known_public_target,
                "limitation",
                code="evaluation_plan_invalid",
                label="evaluation plan known_public_target",
            ),
        },
        "failures": failures,
    }
    return payload, 0 if status == "passed" else 1


def _report_id(report: Mapping[str, object]) -> str:
    value = report.get("report_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    claim_gate = subparsers.add_parser(
        "claim-gate",
        help="Validate frozen baseline, public snapshot, dataset ledger, and plan.",
    )
    claim_gate.add_argument("--baseline-ledger", required=True, type=Path)
    claim_gate.add_argument("--current-report", required=True, type=Path)
    claim_gate.add_argument("--public-snapshot", required=True, type=Path)
    claim_gate.add_argument("--dataset-ledger", required=True, type=Path)
    claim_gate.add_argument("--evaluation-plan", required=True, type=Path)
    claim_gate.add_argument(
        "--claim-text",
        help="Optional proposed public claim text to scan before emitting gate evidence.",
    )
    claim_gate.add_argument("--output", type=Path, help="Write claim-gate evidence JSON")
    verify_report = subparsers.add_parser(
        "verify-report",
        help="Independently verify a claim report reproducibility envelope.",
    )
    verify_report.add_argument("--report", required=True, type=Path)
    verify_report.add_argument(
        "--command-invocation",
        help="Exact benchmark command transcript expected in the report envelope.",
    )
    verify_report.add_argument(
        "--allow-claim-ineligible",
        action="store_true",
        help="Check envelope structure without requiring claim eligibility.",
    )
    verify_report.add_argument("--output", type=Path, help="Write verification evidence JSON")
    return parser


def _run_claim_gate_command(args: argparse.Namespace) -> int:
    payload, status = run_claim_gate(
        baseline_ledger_path=cast("Path", args.baseline_ledger),
        current_report_path=cast("Path", args.current_report),
        public_snapshot_path=cast("Path", args.public_snapshot),
        dataset_ledger_path=cast("Path", args.dataset_ledger),
        evaluation_plan_path=cast("Path", args.evaluation_plan),
        claim_text=cast("str | None", args.claim_text),
    )
    _write_json(cast("Path | None", args.output), payload)
    if status == 0:
        print(
            "public target claim gate passed: "
            f"baseline={payload['baseline']['artifact_path']} "
            f"snapshot_hash={payload['public_snapshot']['raw_sha256']}"
        )
        return 0
    failures = payload.get("failures")
    if isinstance(failures, list):
        print(
            "public target claim gate failed: " + "; ".join(str(item) for item in failures),
            file=sys.stderr,
        )
    else:
        print("public target claim gate failed", file=sys.stderr)
    return 1


def _run_verify_report_command(args: argparse.Namespace) -> int:
    report_path = cast("Path", args.report).expanduser().resolve()
    report = _read_json_object(report_path, label="claim report")
    result = claim_report_envelope.validate_claim_report_envelope(
        report,
        expected_command=cast("str | None", args.command_invocation),
        require_claim_eligible=not cast("bool", args.allow_claim_ineligible),
    )
    payload = claim_report_envelope.verification_payload(report_path, report, result)
    _write_json(cast("Path | None", args.output), payload)
    if result.status == "passed":
        print(
            "claim report envelope verified: "
            f"report={payload['report_id']} sha256={payload['report_sha256']}"
        )
        return 0
    print(
        "claim report envelope verification failed: " + "; ".join(result.errors),
        file=sys.stderr,
    )
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if cast("str", args.command) == "claim-gate":
            return _run_claim_gate_command(args)
        if cast("str", args.command) == "verify-report":
            return _run_verify_report_command(args)
    except PublicTargetError as exc:
        print(
            f"public target validation error [{exc.code}]: {exc.message} "
            f"remediation: {exc.remediation}",
            file=sys.stderr,
        )
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
