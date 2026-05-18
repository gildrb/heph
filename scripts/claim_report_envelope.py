"""Claim-eligible benchmark report envelope helpers."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import cast

CLAIM_REPORT_ENVELOPE_SCHEMA_VERSION = "claim-report-envelope-v1"
CLAIM_REPORT_VERIFICATION_SCHEMA_VERSION = "claim-report-envelope-verification-v1"
DETERMINISTIC_PROJECTION_SCHEMA_VERSION = "deterministic-report-projection-v1"
SCORING_PROTOCOL_VERSION = "external-retrieval-scoring-v1"
THRESHOLD_PROFILE_SCHEMA_VERSION = "threshold-profile-v1"
THRESHOLD_PROFILE_VERSION = "external-runner-thresholds-v1"
KNOWN_LIMITS_SCHEMA_VERSION = "known-limits-v1"
KNOWN_LIMITS_POLICY_VERSION = "known-limits-policy-v1"
LATENCY_SCOPE_RETRIEVAL_ONLY = "retrieval_only_per_query"
LATENCY_SCOPE_NATIVE_RAG = "native_suite_rag_retrieval"

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HASH_FIELDS = ("cases_sha256", "manifest_sha256", "qrels_sha256", "corpus_sha256")
_REQUIRED_METADATA_STRINGS = (
    "command_invocation",
    "model",
    "network_state",
    "cache_state",
    "scoring_protocol_version",
    "dependency_lock_sha256",
    "latency_scope",
)
_REQUIRED_ENVIRONMENT_FIELDS = (
    "hardware_class",
    "cpu_count",
    "memory_total_bytes",
    "accelerator_availability",
    "thread_concurrency",
    "worker_concurrency",
    "process_parallelism",
    "warmup_policy",
    "background_load_assumption",
)
_DEPENDENCY_DISTRIBUTIONS = (
    "hephaistos",
    "bm25s",
    "sentence-transformers",
    "scikit-learn",
    "beir",
    "torch",
    "transformers",
    "numpy",
)
_INVALID_REQUIRED_STRINGS = frozenset({"", "unknown", "n/a", "na", "not applicable"})
_ALLOWED_LATENCY_SCOPES = frozenset(
    {
        LATENCY_SCOPE_RETRIEVAL_ONLY,
        LATENCY_SCOPE_NATIVE_RAG,
        "not_executed",
    }
)
_STRIPPED_RUNTIME_KEYS = frozenset(
    {
        "armory_path",
        "cases_path",
        "command_invocation",
        "elapsed_ms",
        "latency_ms",
        "mean_latency_ms",
        "mean_ms",
        "projection_sha256",
        "readiness_report_path",
        "report_path",
        "suite",
        "suite_path",
    }
)


@dataclass(frozen=True, slots=True)
class EnvelopeValidationResult:
    """Validation result for an independently checked claim envelope."""

    status: str
    claim_eligible: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def repo_root() -> Path:
    """Return the repository root used for independent envelope observations."""
    return _REPO_ROOT


def command_invocation(module_name: str, argv: Sequence[str]) -> str:
    """Render a reproducible one-shot uv command invocation."""
    quoted_args = " ".join(shlex.quote(argument) for argument in argv)
    command = f"uv run python -m {module_name}"
    if quoted_args:
        command = f"{command} {quoted_args}"
    return command


def sha256_file(path: Path) -> str:
    """Hash a file with SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_directory(path: Path) -> str:
    """Hash a directory by stable relative file names plus per-file hashes."""
    digest = hashlib.sha256()
    for child in sorted(path.rglob("*")):
        if not child.is_file():
            continue
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(child).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def finalize_claim_report(
    report: Mapping[str, object],
    *,
    command: str,
    root: Path | None = None,
) -> dict[str, object]:
    """Attach a reproducibility envelope and deterministic projection hash."""
    resolved_root = repo_root() if root is None else root
    payload = _json_clone(report)
    metadata = _ensure_mapping(payload, "metadata")
    fixed_parameters = _mapping_or_empty(metadata.get("fixed_parameters"))
    aggregate_metrics = _mapping_or_empty(payload.get("aggregate_metrics"))
    thresholds = _mapping_or_empty(payload.get("thresholds"))
    observed = observe_current_state(resolved_root)
    latency_scope = _latency_scope(aggregate_metrics)
    limitations = _default_limitations(fixed_parameters)

    metadata["command_invocation"] = command
    metadata["git_commit"] = _string_from_mapping(_mapping_or_empty(observed["git"]), "commit")
    metadata["git_dirty"] = _mapping_or_empty(observed["git"]).get("dirty", True)
    metadata["dependency_lock_sha256"] = observed["uv_lock_sha256"]
    metadata["os_python"] = observed["os_python"]
    metadata["dependency_versions"] = observed["dependency_versions"]
    metadata["environment"] = observed["environment"]
    metadata["network_state"] = _network_state(metadata, fixed_parameters)
    metadata["cache_state"] = _cache_state(metadata)
    metadata["latency_scope"] = latency_scope
    metadata["scoring_protocol_version"] = SCORING_PROTOCOL_VERSION
    metadata["random_seed"] = _random_seed(fixed_parameters)
    metadata["model"] = _model_label(metadata)
    _populate_input_hashes(metadata)
    metadata["runtime_only_fields"] = list(_runtime_only_fields(metadata))

    threshold_profile = _threshold_profile(payload, thresholds, fixed_parameters)
    known_limits = _known_limits(payload)
    payload["threshold_profile"] = threshold_profile
    payload["known_limits"] = known_limits
    metadata["threshold_profile_version"] = threshold_profile["version"]
    metadata["known_limits_policy_version"] = known_limits["policy_version"]

    envelope: dict[str, object] = {
        "schema_version": CLAIM_REPORT_ENVELOPE_SCHEMA_VERSION,
        "report_schema_version": _string_value(payload.get("schema_version")),
        "scoring_protocol_version": SCORING_PROTOCOL_VERSION,
        "claim_eligible": False,
        "ineligibility_reasons": [],
        "reproducibility": {
            "git": observed["git"],
            "command_invocation": command,
            "uv_lock_sha256": observed["uv_lock_sha256"],
            "os_python": observed["os_python"],
            "dependency_versions": observed["dependency_versions"],
            "input_hashes": _input_hashes(metadata),
            "random_seed": metadata["random_seed"],
            "models": _model_identities(metadata, fixed_parameters),
            "network_state": metadata["network_state"],
            "cache_state": metadata["cache_state"],
            "latency": _latency_metadata(latency_scope),
            "environment": observed["environment"],
        },
        "determinism": {
            "schema_version": DETERMINISTIC_PROJECTION_SCHEMA_VERSION,
            "runtime_only_fields": list(_runtime_only_fields(metadata)),
            "deterministic_fields_compared": list(_deterministic_fields(payload)),
            "projection_sha256": "",
        },
        "threshold_profile": threshold_profile,
        "known_limits": known_limits,
        "limitations": limitations,
    }
    payload["claim_envelope"] = envelope
    _set_projection(payload)
    validation = validate_claim_report_envelope(
        payload,
        root=resolved_root,
        require_claim_eligible=False,
    )
    reasons = list(validation.errors)
    reasons.extend(_claim_ineligibility_reasons(payload))
    envelope["claim_eligible"] = not reasons
    envelope["ineligibility_reasons"] = reasons
    _set_projection(payload)
    return payload


def observe_current_state(root: Path | None = None) -> dict[str, object]:
    """Observe independently verifiable checkout and runtime metadata."""
    resolved_root = repo_root() if root is None else root
    return {
        "git": _git_state(resolved_root),
        "uv_lock_sha256": sha256_file(resolved_root / "uv.lock"),
        "os_python": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "python_executable": Path(sys.executable).name,
        },
        "dependency_versions": _dependency_versions(),
        "environment": _environment_state(),
    }


def deterministic_report_projection(report: Mapping[str, object]) -> object:
    """Return report content with declared runtime-only and self-hash fields removed."""
    return _strip_runtime_fields(report)


def deterministic_projection_sha256(report: Mapping[str, object]) -> str:
    """Hash the deterministic report projection with stable JSON serialization."""
    projection = deterministic_report_projection(report)
    serialized = json.dumps(
        projection,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_claim_report_envelope(
    report: Mapping[str, object],
    *,
    root: Path | None = None,
    expected_command: str | None = None,
    require_claim_eligible: bool = True,
) -> EnvelopeValidationResult:
    """Validate a report envelope against the current checkout and runtime."""
    resolved_root = repo_root() if root is None else root
    errors: list[str] = []
    warnings: list[str] = []
    metadata = _required_mapping(report, "metadata", "report", errors)
    envelope = _required_mapping(report, "claim_envelope", "report", errors)
    threshold_profile = _required_mapping(report, "threshold_profile", "report", errors)
    known_limits = _required_mapping(report, "known_limits", "report", errors)
    if not metadata or not envelope:
        return _validation_result(errors, warnings, claim_eligible=False)

    _validate_metadata(metadata, report, errors)
    _validate_envelope(envelope, metadata, report, errors)
    _validate_threshold_profile(threshold_profile, report, errors)
    _validate_known_limits(known_limits, errors)
    _validate_live_state(
        envelope,
        metadata,
        resolved_root,
        errors,
        expected_command=expected_command,
    )
    _validate_projection_hash(envelope, report, errors)
    _validate_reproducibility_status(report, errors, require_claim_eligible)

    claim_eligible = envelope.get("claim_eligible") is True
    reasons = _string_list(envelope.get("ineligibility_reasons"))
    if require_claim_eligible:
        if not claim_eligible:
            errors.append("claim envelope marks report ineligible for public claims")
        if reasons:
            errors.append("claim envelope has ineligibility reason(s): " + "; ".join(reasons))
    return _validation_result(errors, warnings, claim_eligible=claim_eligible)


def verification_payload(
    report_path: Path,
    report: Mapping[str, object],
    result: EnvelopeValidationResult,
) -> dict[str, object]:
    """Build a deterministic verification-command payload."""
    return {
        "schema_version": CLAIM_REPORT_VERIFICATION_SCHEMA_VERSION,
        "status": result.status,
        "report_path": str(report_path),
        "report_sha256": sha256_file(report_path),
        "report_id": _string_value(report.get("report_id")) or "unknown",
        "claim_eligible": result.claim_eligible,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
    }


def _json_clone(report: Mapping[str, object]) -> dict[str, object]:
    return cast(
        "dict[str, object]",
        json.loads(json.dumps(report, ensure_ascii=False, sort_keys=True)),
    )


def _set_projection(payload: dict[str, object]) -> None:
    projection_hash = deterministic_projection_sha256(payload)
    payload["deterministic_projection"] = {
        "schema_version": DETERMINISTIC_PROJECTION_SCHEMA_VERSION,
        "hash_algorithm": "sha256",
        "sha256": projection_hash,
    }
    envelope = _mapping_or_empty(payload.get("claim_envelope"))
    determinism = _mapping_or_empty(envelope.get("determinism"))
    determinism["projection_sha256"] = projection_hash
    envelope["determinism"] = determinism
    payload["claim_envelope"] = envelope


def _git_state(root: Path) -> dict[str, object]:
    commit = _run_git(root, "rev-parse", "HEAD")
    status = _run_git(root, "status", "--porcelain")
    return {
        "commit": commit,
        "dirty": bool(status),
        "dirty_state_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    }


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return result.stdout.strip()


def _dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for distribution in _DEPENDENCY_DISTRIBUTIONS:
        try:
            versions[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            versions[distribution] = "not-installed"
    return versions


def _environment_state() -> dict[str, object]:
    cpu_count = os.cpu_count() or 1
    return {
        "hardware_class": platform.machine() or "platform-machine-not-reported",
        "cpu_count": cpu_count,
        "memory_total_bytes": _memory_total_bytes(),
        "accelerator_availability": "not_requested_by_runner",
        "thread_concurrency": os.environ.get("OMP_NUM_THREADS", "not-pinned"),
        "worker_concurrency": 1,
        "process_parallelism": 1,
        "warmup_policy": "no-explicit-warmup",
        "background_load_assumption": "not-measured-requires-matched-environment",
    }


def _memory_total_bytes() -> int:
    if hasattr(os, "sysconf"):
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            page_count = os.sysconf("SC_PHYS_PAGES")
        except (OSError, ValueError):
            page_size = 0
            page_count = 0
        if isinstance(page_size, int) and isinstance(page_count, int) and page_size > 0:
            return page_size * page_count
    return 1


def _ensure_mapping(parent: dict[str, object], field_name: str) -> dict[str, object]:
    value = parent.get(field_name)
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    created: dict[str, object] = {}
    parent[field_name] = created
    return created


def _mapping_or_empty(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return {}


def _string_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def _string_from_mapping(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    return value if isinstance(value, str) else ""


def _network_state(
    metadata: Mapping[str, object],
    fixed_parameters: Mapping[str, object],
) -> str:
    value = metadata.get("network_state")
    if isinstance(value, str) and value.strip():
        return value.strip()
    value = fixed_parameters.get("network_access")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "disabled-after-materialization"


def _cache_state(metadata: Mapping[str, object]) -> str:
    value = metadata.get("cache_state")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "local-cache-allowed"


def _random_seed(fixed_parameters: Mapping[str, object]) -> int:
    value = fixed_parameters.get("random_seed")
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    return 0


def _model_label(metadata: Mapping[str, object]) -> str:
    value = metadata.get("model")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "retrieval-only:no-generation"


def _model_identities(
    metadata: Mapping[str, object],
    fixed_parameters: Mapping[str, object],
) -> dict[str, object]:
    embedding_model = _string_value(fixed_parameters.get("embedding_model"))
    rerank_model = _string_value(fixed_parameters.get("rerank_model"))
    return {
        "model": {
            "name": _model_label(metadata),
            "version": "retrieval-only-or-user-supplied-label",
        },
        "embedding_model": {
            "name": embedding_model or "not-used",
            "version": "configured-name-cache-label",
        },
        "reranker_model": {
            "name": rerank_model or "not-used",
            "version": "configured-name-cache-label",
        },
    }


def _populate_input_hashes(metadata: dict[str, object]) -> None:
    cases_sha256 = _hash_value(metadata.get("cases_sha256"))
    manifest_sha256 = _hash_value(metadata.get("manifest_sha256"))
    if not manifest_sha256:
        manifest_sha256 = _hash_value(metadata.get("conversion_manifest_sha256"))
    if not manifest_sha256:
        manifest_sha256 = cases_sha256 or "0" * 64
    qrels_sha256 = _hash_value(metadata.get("qrels_sha256")) or cases_sha256 or manifest_sha256
    corpus_sha256 = _hash_value(metadata.get("corpus_sha256")) or manifest_sha256
    metadata["manifest_sha256"] = manifest_sha256
    metadata["qrels_sha256"] = qrels_sha256
    metadata["corpus_sha256"] = corpus_sha256
    if not cases_sha256:
        metadata["cases_sha256"] = qrels_sha256


def _input_hashes(metadata: Mapping[str, object]) -> dict[str, object]:
    payload = {
        "dataset": _string_value(metadata.get("dataset")),
    }
    for field_name in _HASH_FIELDS:
        payload[field_name] = metadata.get(field_name, "0" * 64)
    return payload


def _hash_value(value: object) -> str:
    if isinstance(value, str) and _is_sha256(value):
        return value
    return ""


def _threshold_profile(
    payload: Mapping[str, object],
    thresholds: Mapping[str, object],
    fixed_parameters: Mapping[str, object],
) -> dict[str, object]:
    existing = payload.get("threshold_profile")
    if isinstance(existing, dict):
        return cast("dict[str, object]", existing)
    return {
        "schema_version": THRESHOLD_PROFILE_SCHEMA_VERSION,
        "version": THRESHOLD_PROFILE_VERSION,
        "thresholds": dict(sorted(thresholds.items())),
        "scoring_threshold_parameters": {
            "min_score": fixed_parameters.get("min_score", 0.0),
            "top_k": fixed_parameters.get("top_k", 0),
            "candidate_multiplier": fixed_parameters.get("candidate_multiplier", 1),
        },
        "skip_policy_version": "no-skips-v1",
        "known_limits_policy_version": KNOWN_LIMITS_POLICY_VERSION,
        "diff_summary": "Initial external-runner threshold profile for this report.",
        "rationale": "Thresholds were supplied before report generation by the CLI invocation.",
        "limitation": (
            "Threshold identity applies only to the declared dataset, scope, and scoring protocol."
        ),
        "recorded_before_claim": True,
    }


def _known_limits(payload: Mapping[str, object]) -> dict[str, object]:
    existing = payload.get("known_limits")
    if isinstance(existing, dict):
        return cast("dict[str, object]", existing)
    return {
        "schema_version": KNOWN_LIMITS_SCHEMA_VERSION,
        "policy_version": KNOWN_LIMITS_POLICY_VERSION,
        "entries": [],
    }


def _latency_scope(aggregate_metrics: Mapping[str, object]) -> str:
    latency = aggregate_metrics.get("latency")
    if isinstance(latency, dict):
        scope = cast("dict[str, object]", latency).get("scope")
        if isinstance(scope, str) and scope.strip():
            return scope.strip()
    return LATENCY_SCOPE_RETRIEVAL_ONLY


def _latency_metadata(scope: str) -> dict[str, object]:
    return {
        "scope": scope,
        "unit": "milliseconds",
        "statistics": ["mean_ms"],
        "percentile_definitions": {
            "p50": "50th percentile over per-query wall-clock measurements",
            "p75": "75th percentile over per-query wall-clock measurements",
            "p90": "90th percentile over per-query wall-clock measurements",
            "p95": "95th percentile over per-query wall-clock measurements",
            "p99": "99th percentile over per-query wall-clock measurements",
        },
        "comparison_rule": "latency comparisons require identical scope and environment fields",
    }


def _runtime_only_fields(metadata: Mapping[str, object]) -> tuple[str, ...]:
    fields = _string_list(metadata.get("runtime_only_fields"))
    required = (
        "metadata.command_invocation",
        "claim_envelope.determinism.projection_sha256",
        "deterministic_projection.sha256",
    )
    return tuple(dict.fromkeys((*fields, *required)))


def _deterministic_fields(payload: Mapping[str, object]) -> tuple[str, ...]:
    reproducibility = _mapping_or_empty(payload.get("reproducibility"))
    fields = _string_list(reproducibility.get("deterministic_fields_compared"))
    if fields:
        return fields
    return ("metadata.fixed_parameters", "aggregate_metrics", "benchmarks[].per_query_results")


def _default_limitations(fixed_parameters: Mapping[str, object]) -> list[str]:
    limitations = [
        "Thread scheduling is not pinned; latency claims require matching thread policy.",
        (
            "Model artifact revisions are recorded as configured names/cache labels, "
            "not remote commits."
        ),
    ]
    if fixed_parameters.get("network_access") == "disabled-after-materialization":
        limitations.append("Network access is disabled after public input materialization.")
    return limitations


def _claim_ineligibility_reasons(report: Mapping[str, object]) -> list[str]:
    reasons: list[str] = []
    status = report.get("status")
    if status != "success":
        reasons.append(f"report status is {status!r}, not 'success'")
    reproducibility = _mapping_or_empty(report.get("reproducibility"))
    if reproducibility.get("enabled") is not True or reproducibility.get("status") != "passed":
        reasons.append("reproducibility validation was not enabled and passed")
    threshold_failures = report.get("threshold_failures")
    if isinstance(threshold_failures, list) and threshold_failures:
        reasons.append("threshold failures are present")
    known_limits = _mapping_or_empty(report.get("known_limits"))
    entries = known_limits.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                reasons.append("known_limits entries must be objects")
                continue
            typed_entry = cast("dict[str, object]", entry)
            claim_blocking = typed_entry.get("claim_blocking", True)
            if claim_blocking is not False:
                reasons.append("claim-blocking known_limits entry is present")
    return reasons


def _required_mapping(
    payload: Mapping[str, object],
    field_name: str,
    label: str,
    errors: list[str],
) -> dict[str, object]:
    value = payload.get(field_name)
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    errors.append(f"{label} missing object field {field_name!r}")
    return {}


def _validate_metadata(
    metadata: Mapping[str, object],
    report: Mapping[str, object],
    errors: list[str],
) -> None:
    for field_name in _REQUIRED_METADATA_STRINGS:
        _require_non_empty_string(metadata, field_name, "metadata", errors)
    for field_name in _HASH_FIELDS:
        _require_hash(metadata, field_name, "metadata", errors, reject_zero=True)
    if metadata.get("scoring_protocol_version") != SCORING_PROTOCOL_VERSION:
        errors.append("metadata scoring_protocol_version does not match current protocol")
    if metadata.get("latency_scope") not in _ALLOWED_LATENCY_SCOPES:
        errors.append("metadata latency_scope is missing or unsupported")
    fixed_parameters = _required_mapping(metadata, "fixed_parameters", "metadata", errors)
    if "top_k" not in fixed_parameters:
        errors.append("metadata fixed_parameters missing top_k")
    if "candidate_multiplier" not in fixed_parameters:
        errors.append("metadata fixed_parameters missing candidate_multiplier")
    thresholds = _required_mapping(report, "thresholds", "report", errors)
    if not isinstance(thresholds, dict):
        errors.append("report thresholds must be an object")


def _validate_envelope(
    envelope: Mapping[str, object],
    metadata: Mapping[str, object],
    report: Mapping[str, object],
    errors: list[str],
) -> None:
    if envelope.get("schema_version") != CLAIM_REPORT_ENVELOPE_SCHEMA_VERSION:
        errors.append("claim envelope schema_version is unsupported")
    if envelope.get("report_schema_version") != report.get("schema_version"):
        errors.append("claim envelope report_schema_version does not match report")
    if envelope.get("scoring_protocol_version") != metadata.get("scoring_protocol_version"):
        errors.append("claim envelope scoring_protocol_version does not match metadata")
    reproducibility = _required_mapping(envelope, "reproducibility", "claim envelope", errors)
    determinism = _required_mapping(envelope, "determinism", "claim envelope", errors)
    _required_mapping(envelope, "threshold_profile", "claim envelope", errors)
    _required_mapping(envelope, "known_limits", "claim envelope", errors)
    limitations = envelope.get("limitations")
    if not isinstance(limitations, list) or not _string_list(limitations):
        errors.append("claim envelope limitations must contain at least one limitation")
    _validate_reproducibility_mapping(reproducibility, metadata, errors)
    _validate_determinism_mapping(determinism, metadata, errors)


def _validate_reproducibility_mapping(
    reproducibility: Mapping[str, object],
    metadata: Mapping[str, object],
    errors: list[str],
) -> None:
    git = _required_mapping(reproducibility, "git", "claim envelope reproducibility", errors)
    _require_non_empty_string(git, "commit", "claim envelope git", errors)
    if not isinstance(git.get("dirty"), bool):
        errors.append("claim envelope git dirty must be boolean")
    _require_hash(git, "dirty_state_sha256", "claim envelope git", errors)
    command = _require_non_empty_string(
        reproducibility,
        "command_invocation",
        "claim envelope reproducibility",
        errors,
    )
    if command and command != metadata.get("command_invocation"):
        errors.append("claim envelope command_invocation does not match metadata")
    _require_hash(reproducibility, "uv_lock_sha256", "claim envelope reproducibility", errors)
    _required_mapping(reproducibility, "os_python", "claim envelope reproducibility", errors)
    _required_mapping(
        reproducibility,
        "dependency_versions",
        "claim envelope reproducibility",
        errors,
    )
    input_hashes = _required_mapping(
        reproducibility,
        "input_hashes",
        "claim envelope reproducibility",
        errors,
    )
    errors.extend(
        f"claim envelope input hash {field_name!r} does not match metadata"
        for field_name in _HASH_FIELDS
        if input_hashes.get(field_name) != metadata.get(field_name)
    )
    models = _required_mapping(reproducibility, "models", "claim envelope reproducibility", errors)
    for field_name in ("model", "embedding_model", "reranker_model"):
        model = _required_mapping(models, field_name, "claim envelope models", errors)
        _require_non_empty_string(model, "name", f"claim envelope {field_name}", errors)
        _require_non_empty_string(model, "version", f"claim envelope {field_name}", errors)
    if reproducibility.get("network_state") != metadata.get("network_state"):
        errors.append("claim envelope network_state does not match metadata")
    if reproducibility.get("cache_state") != metadata.get("cache_state"):
        errors.append("claim envelope cache_state does not match metadata")
    latency = _required_mapping(
        reproducibility,
        "latency",
        "claim envelope reproducibility",
        errors,
    )
    if latency.get("scope") != metadata.get("latency_scope"):
        errors.append("claim envelope latency scope does not match metadata")
    environment = _required_mapping(
        reproducibility,
        "environment",
        "claim envelope reproducibility",
        errors,
    )
    errors.extend(
        f"claim envelope environment missing {field_name!r}"
        for field_name in _REQUIRED_ENVIRONMENT_FIELDS
        if field_name not in environment
    )


def _validate_determinism_mapping(
    determinism: Mapping[str, object],
    metadata: Mapping[str, object],
    errors: list[str],
) -> None:
    if determinism.get("schema_version") != DETERMINISTIC_PROJECTION_SCHEMA_VERSION:
        errors.append("claim envelope determinism schema_version is unsupported")
    runtime_only_fields = _string_list(determinism.get("runtime_only_fields"))
    if not runtime_only_fields:
        errors.append("claim envelope determinism runtime_only_fields is empty")
    errors.extend(
        f"claim envelope determinism missing runtime-only field {required!r}"
        for required in _runtime_only_fields(metadata)
        if required not in runtime_only_fields
    )
    compared_fields = _string_list(determinism.get("deterministic_fields_compared"))
    if not compared_fields:
        errors.append("claim envelope determinism deterministic_fields_compared is empty")
    _require_hash(determinism, "projection_sha256", "claim envelope determinism", errors)


def _validate_threshold_profile(
    threshold_profile: Mapping[str, object],
    report: Mapping[str, object],
    errors: list[str],
) -> None:
    if threshold_profile.get("schema_version") != THRESHOLD_PROFILE_SCHEMA_VERSION:
        errors.append("threshold_profile schema_version is unsupported")
    _require_non_empty_string(threshold_profile, "version", "threshold_profile", errors)
    _required_mapping(
        threshold_profile,
        "scoring_threshold_parameters",
        "threshold_profile",
        errors,
    )
    if threshold_profile.get("recorded_before_claim") is not True:
        errors.append("threshold_profile must be recorded_before_claim=true")
    profile_thresholds = _required_mapping(
        threshold_profile,
        "thresholds",
        "threshold_profile",
        errors,
    )
    report_thresholds = _mapping_or_empty(report.get("thresholds"))
    if profile_thresholds != report_thresholds:
        errors.append("threshold_profile thresholds do not match report thresholds")
    _validate_threshold_weakening(threshold_profile, errors)


def _validate_threshold_weakening(
    threshold_profile: Mapping[str, object],
    errors: list[str],
) -> None:
    previous = threshold_profile.get("previous_profile")
    if not isinstance(previous, dict):
        return
    previous_profile = cast("dict[str, object]", previous)
    previous_thresholds = _mapping_or_empty(previous_profile.get("thresholds"))
    current_thresholds = _mapping_or_empty(threshold_profile.get("thresholds"))
    weakened = [
        name
        for name, previous_value in previous_thresholds.items()
        if _number_or_none(current_thresholds.get(name)) is not None
        and _number_or_none(previous_value) is not None
        and cast("float", _number_or_none(current_thresholds.get(name)))
        < cast("float", _number_or_none(previous_value))
    ]
    if not weakened:
        return
    previous_version = previous_profile.get("version")
    current_version = threshold_profile.get("version")
    if current_version == previous_version:
        errors.append("weakened thresholds require a new threshold_profile version")
    for field_name in ("diff_summary", "rationale", "limitation"):
        _require_non_empty_string(threshold_profile, field_name, "threshold_profile", errors)


def _validate_known_limits(
    known_limits: Mapping[str, object],
    errors: list[str],
) -> None:
    if known_limits.get("schema_version") != KNOWN_LIMITS_SCHEMA_VERSION:
        errors.append("known_limits schema_version is unsupported")
    if known_limits.get("policy_version") != KNOWN_LIMITS_POLICY_VERSION:
        errors.append("known_limits policy_version is unsupported")
    entries = known_limits.get("entries")
    if not isinstance(entries, list):
        errors.append("known_limits entries must be a list")
        return
    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"known_limits entry {index} must be an object")
            continue
        entry = cast("dict[str, object]", raw_entry)
        for field_name in ("id", "version", "rationale", "limitation"):
            _require_non_empty_string(entry, field_name, f"known_limits entry {index}", errors)
        if entry.get("recorded_before_claim") is not True:
            errors.append(f"known_limits entry {index} must be recorded_before_claim=true")
        claim_blocking = entry.get("claim_blocking", True)
        if not isinstance(claim_blocking, bool):
            errors.append(f"known_limits entry {index} claim_blocking must be boolean")


def _validate_live_state(
    envelope: Mapping[str, object],
    metadata: Mapping[str, object],
    root: Path,
    errors: list[str],
    *,
    expected_command: str | None,
) -> None:
    reproducibility = _mapping_or_empty(envelope.get("reproducibility"))
    observed = observe_current_state(root)
    git = _mapping_or_empty(reproducibility.get("git"))
    observed_git = _mapping_or_empty(observed["git"])
    if git.get("commit") != observed_git.get("commit"):
        errors.append("claim envelope git commit does not match checkout")
    if git.get("dirty") != observed_git.get("dirty"):
        errors.append("claim envelope git dirty state does not match checkout")
    if git.get("dirty_state_sha256") != observed_git.get("dirty_state_sha256"):
        errors.append("claim envelope git dirty state fingerprint does not match checkout")
    if reproducibility.get("uv_lock_sha256") != observed["uv_lock_sha256"]:
        errors.append("claim envelope uv.lock SHA-256 does not match checkout")
    if reproducibility.get("os_python") != observed["os_python"]:
        errors.append("claim envelope OS/Python metadata does not match runtime")
    if reproducibility.get("dependency_versions") != observed["dependency_versions"]:
        errors.append("claim envelope dependency versions do not match runtime")
    if reproducibility.get("environment") != observed["environment"]:
        errors.append("claim envelope environment metadata does not match runtime")
    if expected_command is not None and metadata.get("command_invocation") != expected_command:
        errors.append("metadata command_invocation does not match command transcript")


def _validate_projection_hash(
    envelope: Mapping[str, object],
    report: Mapping[str, object],
    errors: list[str],
) -> None:
    determinism = _mapping_or_empty(envelope.get("determinism"))
    observed = deterministic_projection_sha256(report)
    if determinism.get("projection_sha256") != observed:
        errors.append("claim envelope deterministic projection SHA-256 is stale")
    projection = _mapping_or_empty(report.get("deterministic_projection"))
    if projection.get("sha256") != observed:
        errors.append("top-level deterministic projection SHA-256 is stale")


def _validate_reproducibility_status(
    report: Mapping[str, object],
    errors: list[str],
    require_claim_eligible: bool,
) -> None:
    if not require_claim_eligible:
        return
    reproducibility = _mapping_or_empty(report.get("reproducibility"))
    if reproducibility.get("enabled") is not True:
        errors.append("report reproducibility.enabled must be true for claim eligibility")
    if reproducibility.get("status") != "passed":
        errors.append("report reproducibility.status must be passed for claim eligibility")


def _require_non_empty_string(
    payload: Mapping[str, object],
    field_name: str,
    label: str,
    errors: list[str],
) -> str:
    value = payload.get(field_name)
    if isinstance(value, str) and value.strip():
        normalized = value.strip().lower()
        if normalized not in _INVALID_REQUIRED_STRINGS:
            return value.strip()
    errors.append(f"{label} missing meaningful string field {field_name!r}")
    return ""


def _require_hash(
    payload: Mapping[str, object],
    field_name: str,
    label: str,
    errors: list[str],
    *,
    reject_zero: bool = False,
) -> None:
    value = payload.get(field_name)
    if not isinstance(value, str) or not _is_sha256(value):
        errors.append(f"{label} missing SHA-256 field {field_name!r}")
        return
    if reject_zero and value == "0" * 64:
        errors.append(f"{label} field {field_name!r} must not be a placeholder hash")


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _number_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _validation_result(
    errors: list[str],
    warnings: list[str],
    *,
    claim_eligible: bool,
) -> EnvelopeValidationResult:
    return EnvelopeValidationResult(
        status="passed" if not errors else "failed",
        claim_eligible=claim_eligible,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _strip_runtime_fields(value: object, *, key_name: str = "") -> object:
    if key_name == "deterministic_projection":
        return None
    if key_name in _STRIPPED_RUNTIME_KEYS:
        return None
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for raw_key, raw_child in sorted(value.items(), key=lambda item: str(item[0])):
            if not isinstance(raw_key, str):
                continue
            if raw_key == "deterministic_projection" or raw_key in _STRIPPED_RUNTIME_KEYS:
                continue
            normalized[raw_key] = _strip_runtime_fields(raw_child, key_name=raw_key)
        return normalized
    if isinstance(value, list):
        return [_strip_runtime_fields(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_runtime_fields(item) for item in value]
    return value
