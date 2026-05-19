"""Validate mission boundary evidence for benchmark safety gates."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

SCHEMA_VERSION = "mission-boundary-gates-v1"

_DISABLED_EGRESS_MODES = frozenset(
    {
        "disabled",
        "disabled-after-materialization",
        "denied-by-default",
        "network-disabled",
        "offline",
    }
)
_PUBLIC_ONLY_EGRESS_MODES = frozenset({"public-only", "public_data", "public-only-data"})
_FORBIDDEN_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "proxy-authorization",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)
_SECRET_MARKERS = ("api_key", "apikey", "auth", "cookie", "key", "secret", "session", "token")
_PRIVATE_HOST_SUFFIXES = (".corp", ".internal", ".local", ".localhost", ".test")
_PRIVATE_HOST_NAMES = frozenset({"0.0.0.0", "localhost", "localhost.localdomain"})
_DOCS_ROOTS = frozenset({"docs", "droid-wiki"})
_DOCS_FILES = frozenset({"AGENTS.md", "README.md"})
_PUBLIC_EXPORT_KEYS = frozenset({"public_exports", "shareable_exports"})
_PUBLIC_VISIBILITY_VALUES = frozenset(
    {
        "external",
        "public",
        "published",
        "shareable",
        "shared",
    }
)
_REQUIRED_VALIDATORS = {
    "ruff": "uv run ruff check .",
    "format-check": "uv run ruff format --check .",
    "repo-policies": "uv run python -m scripts.check_repo_policies",
    "typecheck": "uv run ty check",
    "import-boundaries": "uv run lint-imports",
}
_PROHIBITED_HARNESS_RE = re.compile(
    r"(?i)\b(?:codex|factory[- ]?droid|frontier[- ]?agent|openai-codex|"
    r"swe[- ]?bench|terminal[- ]?bench)\b"
)
_PERSISTENT_COMMAND_PATTERNS = (
    re.compile(r"(?i)(?:^|\s)nohup(?:\s|$)"),
    re.compile(r"(?i)(?:^|\s)disown(?:\s|$)"),
    re.compile(r"(?i)&\s*$"),
    re.compile(r"(?i)\bpython\s+-m\s+http\.server\b"),
    re.compile(r"(?i)\b(?:flask\s+run|gunicorn|streamlit\s+run|uvicorn)\b"),
    re.compile(r"(?i)\b(?:npm|pnpm|yarn)\s+run\s+dev\b"),
    re.compile(r"(?i)\bserve_forever\b"),
)
_PORT_COMMAND_PATTERNS = (
    re.compile(r"(?i)(?:^|\s)--port(?:=|\s+)\d{2,5}\b"),
    re.compile(r"(?i)(?:^|\s)-p\s*\d{2,5}(?::\d{2,5})?\b"),
    re.compile(r"(?i)\bPORT=\d{2,5}\b"),
    re.compile(r"(?i)\b\d{2,5}:\d{2,5}\b"),
)
_PYTEST_XDIST_RE = re.compile(r"(?:^|\s)-n\s+(\d+)(?:\s|$)")
_PYTEST_XDIST_LONG_RE = re.compile(r"(?:^|\s)--numprocesses[=\s]+(\d+)(?:\s|$)")


@dataclass(frozen=True, slots=True)
class BoundaryFailure:
    """A stable mission-boundary validation failure."""

    code: str
    message: str
    evidence: str = ""


@dataclass(frozen=True, slots=True)
class BoundaryGateReport:
    """Result of validating a mission boundary evidence bundle."""

    status: str
    schema_version: str
    checks: tuple[str, ...]
    failures: tuple[BoundaryFailure, ...]


def validate_boundary_evidence(
    evidence: Mapping[str, object],
    *,
    repo_root: Path | None = None,
) -> BoundaryGateReport:
    """Validate generated evidence against this mission's safety boundaries."""
    root = _repo_root(repo_root)
    failures: list[BoundaryFailure] = []
    checks = (
        "artifact-containment",
        "artifact-gitignore",
        "docs-skipped",
        "private-artifact-default",
        "network-egress",
        "no-other-harness",
        "configured-validators",
        "one-shot-resources",
    )
    _check_artifact_containment(evidence, root, failures)
    _check_artifacts_gitignored(root, failures)
    _check_docs_skipped(evidence, root, failures)
    _check_private_artifact_default(evidence, failures)
    _check_network_egress(evidence, root, failures)
    _check_command_boundaries(evidence, failures)
    _check_validators(evidence, failures)
    _check_resources(evidence, failures)
    return BoundaryGateReport(
        status="failed" if failures else "passed",
        schema_version=SCHEMA_VERSION,
        checks=checks,
        failures=tuple(failures),
    )


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def _check_artifact_containment(
    evidence: Mapping[str, object],
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> None:
    artifact_roots = [repo_root / ".artifacts"]
    raw_artifact_roots = _path_inputs(evidence.get("artifact_roots"))
    artifact_roots.extend(
        _path_list(raw_artifact_roots, repo_root=repo_root, relative_to_repo=True)
    )
    raw_temp_roots = _path_inputs(evidence.get("temporary_armory_roots"))
    temp_roots = _path_list(
        raw_temp_roots,
        repo_root=repo_root,
        relative_to_repo=False,
    )
    raw_allowed_temp_roots = _path_inputs(evidence.get("allowed_temp_roots"))
    temp_roots.extend(
        _path_list(raw_allowed_temp_roots, repo_root=repo_root, relative_to_repo=False)
    )
    artifact_root_entries = (
        (".artifacts", repo_root / ".artifacts"),
        *zip(raw_artifact_roots, artifact_roots[1:], strict=True),
    )
    for raw_root, root in artifact_root_entries:
        if root != repo_root / ".artifacts" and not _artifact_root_allowed(root, repo_root):
            failures.append(
                BoundaryFailure(
                    "artifact_root_outside_allowed_roots",
                    "declared artifact roots must stay under repo .artifacts or temp roots",
                    str(root),
                )
            )
        if _evidence_path_has_existing_symlink(
            raw_root,
            repo_root=repo_root,
            relative_to_repo=True,
        ):
            failures.append(
                BoundaryFailure(
                    "artifact_root_symlink",
                    "declared artifact roots must not traverse symlinks",
                    str(raw_root),
                )
            )
    for raw_path in _artifact_entries(evidence.get("generated_artifacts")):
        if _evidence_path_has_existing_symlink(
            raw_path,
            repo_root=repo_root,
            relative_to_repo=True,
        ):
            failures.append(
                BoundaryFailure(
                    "artifact_path_symlink",
                    "generated artifact paths must not traverse symlinks",
                    raw_path,
                )
            )
            continue
        path = _resolve_evidence_path(raw_path, repo_root=repo_root, relative_to_repo=True)
        if not _artifact_path_allowed(path, repo_root, artifact_roots, temp_roots):
            failures.append(
                BoundaryFailure(
                    "artifact_outside_allowed_roots",
                    "generated artifacts must stay under .artifacts or temp copied armories",
                    str(path),
                )
            )


def _artifact_entries(value: object) -> list[str]:
    entries: list[str] = []
    if not isinstance(value, list):
        return entries
    for item in value:
        if isinstance(item, str):
            entries.append(item)
        elif isinstance(item, dict):
            path = cast("dict[object, object]", item).get("path")
            if isinstance(path, str):
                entries.append(path)
    return entries


def _artifact_metadata_entries(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast("Mapping[str, object]", item) for item in value if isinstance(item, dict)]


def _path_inputs(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _path_list(
    value: Sequence[str],
    *,
    repo_root: Path,
    relative_to_repo: bool,
) -> list[Path]:
    return [
        _resolve_evidence_path(
            item,
            repo_root=repo_root,
            relative_to_repo=relative_to_repo,
        )
        for item in value
    ]


def _resolve_evidence_path(
    raw_path: str,
    *,
    repo_root: Path,
    relative_to_repo: bool,
) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and relative_to_repo:
        path = repo_root / path
    return path.resolve(strict=False)


def _evidence_path_has_existing_symlink(
    raw_path: str,
    *,
    repo_root: Path,
    relative_to_repo: bool,
) -> bool:
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and relative_to_repo:
        path = repo_root / path
    return _has_existing_symlink(path)


def _artifact_root_allowed(root: Path, repo_root: Path) -> bool:
    if _is_relative_to(root, repo_root):
        artifacts_root = repo_root / ".artifacts"
        return root == artifacts_root or _is_relative_to(root, artifacts_root)
    return _is_temp_path(root)


def _artifact_path_allowed(
    path: Path,
    repo_root: Path,
    artifact_roots: Sequence[Path],
    temp_roots: Sequence[Path],
) -> bool:
    if _is_relative_to(path, repo_root):
        return any(path != root and _is_relative_to(path, root) for root in artifact_roots)
    if any(path != root and _is_relative_to(path, root) for root in temp_roots):
        return True
    return _is_temp_path(path)


def _is_temp_path(path: Path) -> bool:
    temp_candidates = {
        Path(tempfile.gettempdir()).resolve(strict=False),
        Path("/private/tmp").resolve(strict=False),
        Path("/tmp").resolve(strict=False),
        Path("/var/tmp").resolve(strict=False),
    }
    return any(path != root and _is_relative_to(path, root) for root in temp_candidates)


def _has_existing_symlink(path: Path) -> bool:
    for candidate in (path, *path.parents):
        try:
            if candidate.exists() and candidate.is_symlink():
                return True
        except OSError:
            return True
    return False


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _check_artifacts_gitignored(
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> None:
    gitignore = repo_root / ".gitignore"
    try:
        lines = gitignore.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        failures.append(
            BoundaryFailure(
                "artifacts_gitignore_missing",
                "repo .gitignore must be readable and ignore generated benchmark artifacts",
                str(exc),
            )
        )
        return
    if not any(_ignores_artifacts_root(line) for line in lines):
        failures.append(
            BoundaryFailure(
                "artifacts_not_gitignored",
                "repo .gitignore must include .artifacts/ for generated benchmark artifacts",
                gitignore.as_posix(),
            )
        )
    if not any(_ignores_benchmarks_root(line) for line in lines):
        failures.append(
            BoundaryFailure(
                "benchmarks_not_gitignored",
                "repo .gitignore must include benchmarks/ for private benchmark suites",
                gitignore.as_posix(),
            )
        )
    tracked_benchmarks = _tracked_benchmark_paths(repo_root)
    if tracked_benchmarks:
        failures.append(
            BoundaryFailure(
                "benchmarks_tracked",
                "benchmark suites, corpora, qrels, prompts, snapshots, and outputs "
                "must not be tracked",
                "\n".join(tracked_benchmarks),
            )
        )


def _ignores_artifacts_root(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "!")):
        return False
    normalized = stripped.lstrip("/").rstrip("/")
    return normalized == ".artifacts" or normalized.startswith(".artifacts/")


def _ignores_benchmarks_root(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "!")):
        return False
    normalized = stripped.lstrip("/").rstrip("/")
    return normalized == "benchmarks" or normalized.startswith("benchmarks/")


def _tracked_benchmark_paths(repo_root: Path) -> tuple[str, ...]:
    if not (repo_root / ".git").exists():
        return ()
    try:
        completed = subprocess.run(
            ["git", "ls-files", "benchmarks"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ()
    if completed.returncode != 0:
        return ()
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


def _check_docs_skipped(
    evidence: Mapping[str, object],
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> None:
    for raw_path in _string_list(evidence.get("changed_paths")):
        normalized = _normalize_changed_path(raw_path)
        if _is_docs_path(normalized):
            failures.append(
                BoundaryFailure(
                    "docs_changed",
                    "docs/README/AGENTS paths must remain unchanged for this mission",
                    raw_path,
                )
            )
    for raw_path in _artifact_entries(evidence.get("generated_artifacts")):
        path = _resolve_evidence_path(raw_path, repo_root=repo_root, relative_to_repo=True)
        if _is_relative_to(path, repo_root):
            relative = path.relative_to(repo_root).as_posix()
            if _is_docs_path(relative):
                failures.append(
                    BoundaryFailure(
                        "docs_generated_artifact",
                        "benchmark summaries must not be saved as user-facing docs",
                        relative,
                    )
                )


def _normalize_changed_path(raw_path: str) -> str:
    stripped = raw_path.strip()
    if len(stripped) > 3 and stripped[2] == " ":
        return stripped[3:].strip()
    if " -> " in stripped:
        return stripped.rsplit(" -> ", maxsplit=1)[-1].strip()
    return stripped


def _is_docs_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if not normalized:
        return False
    parts = tuple(part for part in normalized.split("/") if part)
    if not parts:
        return False
    return parts[0] in _DOCS_ROOTS or parts[0] in _DOCS_FILES or parts[-1] == "README.md"


def _check_private_artifact_default(
    evidence: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    publication = _mapping_or_empty(evidence.get("artifact_publication"))
    if publication.get("public_export_enabled") is True:
        failures.append(
            BoundaryFailure(
                "public_export_out_of_scope",
                "public/shareable benchmark export is out of default mission scope",
                "artifact_publication.public_export_enabled=true",
            )
        )
    for key in ("default_scope", "default_visibility"):
        raw_value = publication.get(key)
        if isinstance(raw_value, str) and _is_public_visibility(raw_value):
            failures.append(
                BoundaryFailure(
                    "public_export_out_of_scope",
                    "benchmark artifacts must be private/internal by default",
                    f"artifact_publication.{key}={raw_value}",
                )
            )
    failures.extend(
        BoundaryFailure(
            "public_export_out_of_scope",
            "public/shareable benchmark export is out of default mission scope",
            entry,
        )
        for key in _PUBLIC_EXPORT_KEYS
        for entry in _export_entries(evidence.get(key), key=key)
    )
    for entry in _artifact_metadata_entries(evidence.get("generated_artifacts")):
        visibility = entry.get("visibility")
        if isinstance(visibility, str) and _is_public_visibility(visibility):
            raw_path = entry.get("path")
            failures.append(
                BoundaryFailure(
                    "public_export_out_of_scope",
                    "generated benchmark artifacts must not be public/shareable by default",
                    str(raw_path) if isinstance(raw_path, str) else visibility,
                )
            )


def _export_entries(value: object, *, key: str) -> list[str]:
    if not isinstance(value, list):
        return []
    entries: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            entries.append(f"{key}: {item}")
        elif isinstance(item, dict):
            path = cast("dict[object, object]", item).get("path")
            visibility = cast("dict[object, object]", item).get("visibility")
            entries.append(f"{key}: {path or visibility or '<entry>'}")
    return entries


def _is_public_visibility(value: str) -> bool:
    normalized = value.strip().lower().replace("_", "-")
    tokens = {token for token in re.split(r"[^a-z0-9]+", normalized) if token}
    return normalized in _PUBLIC_VISIBILITY_VALUES or bool(tokens & _PUBLIC_VISIBILITY_VALUES)


def _check_network_egress(
    evidence: Mapping[str, object],
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> None:
    egress = evidence.get("egress")
    if not isinstance(egress, dict):
        failures.append(
            BoundaryFailure("egress_missing", "network egress evidence must be explicit")
        )
    else:
        _check_egress_manifest(cast("Mapping[str, object]", egress), failures)
    _check_report_network_state(evidence.get("reports"), repo_root, failures)


def _check_egress_manifest(
    egress: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    raw_mode = egress.get("mode")
    mode = raw_mode.strip().lower() if isinstance(raw_mode, str) else ""
    requests = _request_entries(egress.get("requests"))
    if mode in _DISABLED_EGRESS_MODES:
        if requests:
            failures.append(
                BoundaryFailure(
                    "egress_requests_when_disabled",
                    "disabled/offline validation must not declare network requests",
                )
            )
        return
    if mode not in _PUBLIC_ONLY_EGRESS_MODES:
        failures.append(
            BoundaryFailure(
                "egress_mode_invalid",
                "egress mode must be disabled, offline, or public-only",
                str(raw_mode),
            )
        )
        return
    for index, request in enumerate(requests, start=1):
        _check_public_request(request, failures, context=f"egress request {index}")


def _request_entries(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast("Mapping[str, object]", item) for item in value if isinstance(item, dict)]


def _check_public_request(
    request: Mapping[str, object],
    failures: list[BoundaryFailure],
    *,
    context: str,
) -> None:
    raw_method = request.get("method")
    method = raw_method.strip().upper() if isinstance(raw_method, str) else ""
    if method != "GET":
        failures.append(
            BoundaryFailure(
                "egress_method_not_get",
                "allowed public egress must use unauthenticated HTTPS GET",
                f"{context}: {raw_method}",
            )
        )
    raw_url = request.get("url")
    if not isinstance(raw_url, str) or not raw_url.strip():
        failures.append(
            BoundaryFailure("egress_url_missing", "egress requests must include a URL", context)
        )
        return
    parsed = urllib.parse.urlparse(raw_url.strip())
    if parsed.scheme != "https":
        failures.append(
            BoundaryFailure(
                "egress_url_not_https",
                "allowed public egress URLs must use https://",
                f"{context}: {raw_url}",
            )
        )
    if parsed.username or parsed.password:
        failures.append(
            BoundaryFailure(
                "egress_embedded_credentials",
                "egress URLs must not include embedded credentials",
                f"{context}: {raw_url}",
            )
        )
    host = parsed.hostname or ""
    if not host or _host_is_private(host):
        failures.append(
            BoundaryFailure(
                "egress_private_host",
                "egress URLs must target public global hosts only",
                f"{context}: {raw_url}",
            )
        )
    _check_query_credentials(parsed.query, failures, context=context)
    _check_request_headers(request.get("headers"), failures, context=context)


def _host_is_private(host: str) -> bool:
    lowered = host.strip().lower().rstrip(".")
    if lowered in _PRIVATE_HOST_NAMES:
        return True
    if any(lowered.endswith(suffix) for suffix in _PRIVATE_HOST_SUFFIXES):
        return True
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return not address.is_global


def _check_query_credentials(
    query: str,
    failures: list[BoundaryFailure],
    *,
    context: str,
) -> None:
    for key, value in urllib.parse.parse_qsl(query, keep_blank_values=True):
        haystack = f"{key}={value}".lower()
        if any(marker in haystack for marker in _SECRET_MARKERS):
            failures.append(
                BoundaryFailure(
                    "egress_credential_query",
                    "egress URLs must not include credential-like query parameters",
                    f"{context}: {key}",
                )
            )


def _check_request_headers(
    raw_headers: object,
    failures: list[BoundaryFailure],
    *,
    context: str,
) -> None:
    if raw_headers is None:
        return
    if not isinstance(raw_headers, dict):
        failures.append(
            BoundaryFailure(
                "egress_headers_invalid",
                "egress request headers must be an object when present",
                context,
            )
        )
        return
    headers = cast("dict[object, object]", raw_headers)
    for raw_name, raw_value in headers.items():
        name = str(raw_name).strip().lower()
        value = str(raw_value).strip().lower()
        if (
            name in _FORBIDDEN_HEADER_NAMES
            or any(marker in name for marker in _SECRET_MARKERS)
            or "bearer " in value
            or any(f"{marker}=" in value for marker in _SECRET_MARKERS)
        ):
            failures.append(
                BoundaryFailure(
                    "egress_forbidden_header",
                    "egress requests must not include credentials, cookies, or tokens",
                    f"{context}: {raw_name}",
                )
            )


def _check_report_network_state(
    raw_reports: object,
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> None:
    for report in _report_entries(raw_reports, repo_root, failures):
        metadata = _mapping_or_empty(report.get("metadata"))
        fixed_parameters = _mapping_or_empty(metadata.get("fixed_parameters"))
        raw_network_state = metadata.get("network_state")
        raw_network_access = fixed_parameters.get("network_access")
        network_state = (
            raw_network_state.strip().lower() if isinstance(raw_network_state, str) else ""
        )
        network_access = (
            raw_network_access.strip().lower() if isinstance(raw_network_access, str) else ""
        )
        if network_state not in _DISABLED_EGRESS_MODES:
            failures.append(
                BoundaryFailure(
                    "report_network_state_not_disabled",
                    "claim reports must declare disabled/offline network state",
                    str(raw_network_state),
                )
            )
        if network_access and network_access not in _DISABLED_EGRESS_MODES:
            failures.append(
                BoundaryFailure(
                    "report_network_access_not_disabled",
                    "runner fixed parameters must disable network after acquisition",
                    str(raw_network_access),
                )
            )


def _report_entries(
    raw_reports: object,
    repo_root: Path,
    failures: list[BoundaryFailure],
) -> list[Mapping[str, object]]:
    if not isinstance(raw_reports, list):
        return []
    reports: list[Mapping[str, object]] = []
    for raw_report in raw_reports:
        if isinstance(raw_report, dict):
            reports.append(cast("Mapping[str, object]", raw_report))
        elif isinstance(raw_report, str) and raw_report.strip():
            path = _resolve_evidence_path(raw_report, repo_root=repo_root, relative_to_repo=True)
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                failures.append(
                    BoundaryFailure(
                        "report_load_failed",
                        "declared report evidence path must be readable",
                        f"{path}: {exc}",
                    )
                )
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                failures.append(
                    BoundaryFailure(
                        "report_json_invalid",
                        "declared report evidence path must contain valid JSON",
                        f"{path}: {exc.msg} at line {exc.lineno} column {exc.colno}",
                    )
                )
                continue
            if not isinstance(payload, dict):
                failures.append(
                    BoundaryFailure(
                        "report_payload_invalid",
                        "declared report evidence JSON must be an object",
                        f"{path}: {type(payload).__name__}",
                    )
                )
                continue
            reports.append(cast("Mapping[str, object]", payload))
    return reports


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast("Mapping[str, object]", value)
    return {}


def _check_command_boundaries(
    evidence: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    for entry in _all_command_entries(evidence):
        command = _command_from_entry(entry)
        if not command:
            continue
        _check_single_command(command, failures)
        _check_command_concurrency(command, entry, failures)


def _all_command_entries(evidence: Mapping[str, object]) -> list[Mapping[str, object]]:
    entries: list[Mapping[str, object]] = []
    for key in ("commands", "command_transcript", "validators"):
        raw_entries = evidence.get(key)
        if not isinstance(raw_entries, list):
            continue
        for raw_entry in raw_entries:
            if isinstance(raw_entry, str):
                entries.append({"command": raw_entry})
            elif isinstance(raw_entry, dict):
                entries.append(cast("Mapping[str, object]", raw_entry))
    return entries


def _command_from_entry(entry: Mapping[str, object]) -> str:
    raw_command = entry.get("command")
    if isinstance(raw_command, str):
        return raw_command.strip()
    return ""


def _check_single_command(command: str, failures: list[BoundaryFailure]) -> None:
    if _PROHIBITED_HARNESS_RE.search(command):
        failures.append(
            BoundaryFailure(
                "prohibited_harness_command",
                "mission commands must not execute competing or frontier harnesses",
                command,
            )
        )
    if any(pattern.search(command) for pattern in _PERSISTENT_COMMAND_PATTERNS):
        failures.append(
            BoundaryFailure(
                "persistent_command",
                "validation commands must be one-shot and must not start persistent services",
                command,
            )
        )
    if any(pattern.search(command) for pattern in _PORT_COMMAND_PATTERNS):
        failures.append(
            BoundaryFailure(
                "port_binding_command",
                "mission validation must not bind or claim ports",
                command,
            )
        )


def _check_command_concurrency(
    command: str,
    entry: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    concurrency = _command_concurrency(command, entry)
    weight = _command_weight(command, entry)
    cap = 1 if weight == "heavy" else 2
    if concurrency > cap:
        failures.append(
            BoundaryFailure(
                "concurrency_cap_exceeded",
                "heavy validators are capped at 1 worker and light validators at 2 workers",
                f"{command} concurrency={concurrency} cap={cap}",
            )
        )


def _command_concurrency(command: str, entry: Mapping[str, object]) -> int:
    raw_concurrency = entry.get("concurrency")
    if isinstance(raw_concurrency, int) and not isinstance(raw_concurrency, bool):
        return raw_concurrency
    for pattern in (_PYTEST_XDIST_RE, _PYTEST_XDIST_LONG_RE):
        match = pattern.search(command)
        if match is None:
            continue
        try:
            return int(match.group(1))
        except ValueError:
            return 1
    return 1


def _command_weight(command: str, entry: Mapping[str, object]) -> str:
    raw_weight = entry.get("weight")
    if isinstance(raw_weight, str) and raw_weight.strip().lower() == "heavy":
        return "heavy"
    lowered = command.lower()
    if "pytest" in lowered or "ruff" in lowered or "ty check" in lowered:
        return "lightweight"
    if "benchmark" in lowered or "rerank" in lowered or "model" in lowered:
        return "heavy"
    return "lightweight"


def _check_validators(
    evidence: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    raw_validators = evidence.get("validators")
    validators: list[Mapping[str, object]] = []
    if isinstance(raw_validators, list):
        validators = [
            cast("Mapping[str, object]", item) for item in raw_validators if isinstance(item, dict)
        ]
    by_name = {name: entry for entry in validators if (name := _validator_name(entry))}
    commands = {
        _command_from_entry(entry): entry for entry in validators if _command_from_entry(entry)
    }
    for required_name, required_command in _REQUIRED_VALIDATORS.items():
        if required_name not in by_name and required_command not in commands:
            failures.append(
                BoundaryFailure(
                    "validator_missing",
                    "required repository validator evidence is missing",
                    required_command,
                )
            )
    if not _has_focused_pytest(validators):
        failures.append(
            BoundaryFailure(
                "validator_missing",
                "focused changed-area pytest evidence is missing",
                "focused pytest",
            )
        )
    if not _has_full_pytest(validators) and not _approved_full_suite_limitation(evidence):
        failures.append(
            BoundaryFailure(
                "validator_missing",
                "full pytest evidence or an approved substitute limitation is missing",
                "uv run pytest",
            )
        )
    for entry in validators:
        raw_exit_code = entry.get("exit_code")
        if raw_exit_code != 0:
            failures.append(
                BoundaryFailure(
                    "validator_failed",
                    "repository validators must have exit_code=0",
                    f"{_validator_name(entry) or _command_from_entry(entry)}={raw_exit_code}",
                )
            )


def _validator_name(entry: Mapping[str, object]) -> str:
    raw_name = entry.get("name")
    if isinstance(raw_name, str):
        return raw_name.strip()
    return ""


def _has_focused_pytest(validators: Sequence[Mapping[str, object]]) -> bool:
    for entry in validators:
        command = _command_from_entry(entry)
        name = _validator_name(entry)
        if command.startswith("uv run pytest") and ("tests/" in command or " -k " in command):
            return True
        if "focused" in name:
            return True
    return False


def _has_full_pytest(validators: Sequence[Mapping[str, object]]) -> bool:
    for entry in validators:
        command = " ".join(_command_from_entry(entry).split())
        name = _validator_name(entry)
        if name in {"full-tests", "test"} and command.startswith("uv run pytest"):
            return True
        if re.fullmatch(r"uv run pytest(?: -n \d+)?", command):
            return True
    return False


def _approved_full_suite_limitation(evidence: Mapping[str, object]) -> bool:
    limitation = evidence.get("full_suite_limitation")
    return isinstance(limitation, str) and bool(limitation.strip())


def _check_resources(
    evidence: Mapping[str, object],
    failures: list[BoundaryFailure],
) -> None:
    resources = evidence.get("resources")
    if not isinstance(resources, dict):
        failures.append(
            BoundaryFailure(
                "resource_evidence_missing",
                "process/port resource evidence must be present",
            )
        )
        return
    resource_map = cast("Mapping[str, object]", resources)
    before = set(_string_list(resource_map.get("before_listeners")))
    after = set(_string_list(resource_map.get("after_listeners")))
    new_listeners = sorted(after - before)
    if new_listeners:
        failures.append(
            BoundaryFailure(
                "listener_drift",
                "post-validation listener snapshot contains new listeners",
                ", ".join(new_listeners),
            )
        )
    services_started = _string_list(resource_map.get("services_started"))
    if services_started:
        failures.append(
            BoundaryFailure(
                "persistent_service_started",
                "mission validation must not start persistent repo services",
                ", ".join(services_started),
            )
        )
    ports_claimed = resource_map.get("ports_claimed")
    if isinstance(ports_claimed, list) and ports_claimed:
        failures.append(
            BoundaryFailure(
                "port_claimed",
                "this mission claims no service ports",
                ", ".join(str(port) for port in ports_claimed),
            )
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _report_payload(report: BoundaryGateReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "status": report.status,
        "checks": list(report.checks),
        "failures": [asdict(failure) for failure in report.failures],
    }


def _load_evidence(path: str, stdin_text: str | None) -> dict[str, object]:
    if path == "-":
        text = sys.stdin.read() if stdin_text is None else stdin_text
    else:
        text = Path(path).expanduser().read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError("boundary evidence must be a JSON object")
    return cast("dict[str, object]", payload)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, help="Boundary evidence JSON path, or '-'")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None, *, stdin_text: str | None = None) -> int:
    """CLI entrypoint for mission boundary validation."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        evidence = _load_evidence(cast("str", args.evidence), stdin_text)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        report = BoundaryGateReport(
            status="failed",
            schema_version=SCHEMA_VERSION,
            checks=("evidence-load",),
            failures=(
                BoundaryFailure(
                    "evidence_load_failed",
                    "could not load mission boundary evidence JSON",
                    str(exc),
                ),
            ),
        )
    else:
        report = validate_boundary_evidence(evidence, repo_root=cast("Path", args.repo_root))
    payload = _report_payload(report)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        path = json_report.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
