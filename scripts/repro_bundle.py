"""Export and verify private benchmark reproducibility bundles."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict, cast

from scripts import claim_report_envelope

BUNDLE_SCHEMA_VERSION = "heph-private-repro-bundle-v1"
_ROLE_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_REPO_ROOT = Path(__file__).resolve().parent.parent
_PRIVATE_REPO_ROOTS = (
    _REPO_ROOT / ".artifacts",
    _REPO_ROOT / ".factory",
)


class RawArtifactSpec(TypedDict):
    role: str
    path: Path


class RawArtifactEntry(TypedDict):
    role: str
    path: str
    original_path: str
    sha256: str
    size_bytes: int


class RawBundleManifest(TypedDict):
    schema_version: str
    command_invocation: str
    privacy: dict[str, object]
    environment: dict[str, object]
    artifacts: list[RawArtifactEntry]


@dataclass(frozen=True, slots=True)
class ReproBundleExport:
    """Result for a private reproducibility bundle export."""

    status: str
    bundle_path: str
    manifest_path: str
    artifact_count: int
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReproBundleVerification:
    """Result for independent verification of a bundle manifest."""

    status: str
    manifest_path: str
    bundle_path: str
    artifact_count: int
    errors: tuple[str, ...] = ()


def export_bundle(
    output_dir: Path,
    artifact_specs: list[RawArtifactSpec],
    *,
    command_invocation: str,
) -> ReproBundleExport:
    """Copy artifacts into a private bundle directory and write a hash manifest."""
    errors = _bundle_input_errors(output_dir, artifact_specs, command_invocation)
    if not _is_private_output_path(output_dir):
        errors.append(
            "output directory must be outside the repository or under an ignored private root "
            "such as .artifacts/"
        )
    if errors:
        return ReproBundleExport(
            status="failed",
            bundle_path=str(output_dir.expanduser()),
            manifest_path=str(output_dir.expanduser() / "manifest.json"),
            artifact_count=0,
            errors=tuple(errors),
        )

    resolved_output = output_dir.expanduser().resolve()
    artifacts_dir = resolved_output / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    entries: list[RawArtifactEntry] = []
    used_names: set[str] = set()
    for spec in artifact_specs:
        source_path = spec["path"].expanduser().resolve()
        bundle_name = _bundle_artifact_name(spec["role"], source_path, used_names)
        copied_path = artifacts_dir / bundle_name
        shutil.copy2(source_path, copied_path)
        entries.append(_artifact_entry(spec["role"], copied_path, source_path, resolved_output))

    manifest: RawBundleManifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "command_invocation": command_invocation.strip(),
        "privacy": {
            "scope": "private-internal",
            "public_export": False,
            "shareable_without_review": False,
            "output_policy": "local artifact bundle; do not commit benchmark data",
        },
        "environment": _environment_metadata(),
        "artifacts": entries,
    }
    manifest_path = resolved_output / "manifest.json"
    _write_json(manifest_path, manifest)
    verification = verify_bundle(manifest_path)
    return ReproBundleExport(
        status=verification.status,
        bundle_path=str(resolved_output),
        manifest_path=str(manifest_path),
        artifact_count=len(entries),
        errors=verification.errors,
    )


def verify_bundle(manifest_path: Path) -> ReproBundleVerification:
    """Verify a private reproducibility bundle manifest and artifact hashes."""
    resolved_manifest = manifest_path.expanduser().resolve()
    bundle_path = resolved_manifest.parent
    errors: list[str] = []
    try:
        payload = json.loads(resolved_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ReproBundleVerification(
            status="failed",
            manifest_path=str(resolved_manifest),
            bundle_path=str(bundle_path),
            artifact_count=0,
            errors=(f"could not read manifest: {exc}",),
        )
    if not isinstance(payload, dict):
        return ReproBundleVerification(
            status="failed",
            manifest_path=str(resolved_manifest),
            bundle_path=str(bundle_path),
            artifact_count=0,
            errors=("manifest must be a JSON object",),
        )
    manifest = cast("dict[str, object]", payload)
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append("manifest schema_version is unsupported")
    command = manifest.get("command_invocation")
    if not isinstance(command, str) or not command.strip():
        errors.append("manifest command_invocation must be a non-empty string")
    privacy = manifest.get("privacy")
    privacy_map = cast("dict[str, object]", privacy) if isinstance(privacy, dict) else {}
    if privacy_map.get("public_export") is not False:
        errors.append("manifest privacy.public_export must be false")

    artifact_entries = _artifact_entries(manifest.get("artifacts"), errors)
    seen_roles: set[str] = set()
    for entry in artifact_entries:
        role = entry["role"]
        if role in seen_roles:
            errors.append(f"duplicate artifact role: {role}")
        seen_roles.add(role)
        _verify_artifact_entry(entry, bundle_path, errors)

    return ReproBundleVerification(
        status="passed" if not errors else "failed",
        manifest_path=str(resolved_manifest),
        bundle_path=str(bundle_path),
        artifact_count=len(artifact_entries),
        errors=tuple(errors),
    )


def _bundle_input_errors(
    output_dir: Path,
    artifact_specs: list[RawArtifactSpec],
    command_invocation: str,
) -> list[str]:
    errors: list[str] = []
    if not str(output_dir.expanduser()).strip():
        errors.append("output directory is required")
    if not command_invocation.strip():
        errors.append("command invocation is required")
    if not artifact_specs:
        errors.append("at least one --artifact role=path is required")
    seen_roles: set[str] = set()
    for spec in artifact_specs:
        role = spec["role"]
        path = spec["path"].expanduser()
        if not role:
            errors.append("artifact role must be non-empty")
        elif role in seen_roles:
            errors.append(f"duplicate artifact role: {role}")
        seen_roles.add(role)
        if not path.is_file():
            errors.append(f"artifact does not exist: {path}")
    return errors


def _is_private_output_path(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(_REPO_ROOT)
    except ValueError:
        return True
    return any(
        _is_relative_to(resolved, private_root.resolve()) for private_root in _PRIVATE_REPO_ROOTS
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _artifact_entries(value: object, errors: list[str]) -> list[RawArtifactEntry]:
    if not isinstance(value, list):
        errors.append("manifest artifacts must be a list")
        return []
    entries: list[RawArtifactEntry] = []
    for index, raw_entry in enumerate(value, start=1):
        if not isinstance(raw_entry, dict):
            errors.append(f"artifact {index} must be an object")
            continue
        entry_map = cast("dict[str, object]", raw_entry)
        role = entry_map.get("role")
        path = entry_map.get("path")
        original_path = entry_map.get("original_path")
        sha256 = entry_map.get("sha256")
        size_bytes = entry_map.get("size_bytes")
        if not isinstance(role, str) or not role.strip():
            errors.append(f"artifact {index} role must be a non-empty string")
            continue
        if not isinstance(path, str) or not path.strip():
            errors.append(f"artifact {role} path must be a non-empty string")
            continue
        if not isinstance(original_path, str):
            errors.append(f"artifact {role} original_path must be a string")
            continue
        if not isinstance(sha256, str) or not sha256.strip():
            errors.append(f"artifact {role} sha256 must be a non-empty string")
            continue
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
            errors.append(f"artifact {role} size_bytes must be a non-negative integer")
            continue
        entries.append(
            {
                "role": role,
                "path": path,
                "original_path": original_path,
                "sha256": sha256,
                "size_bytes": size_bytes,
            }
        )
    return entries


def _verify_artifact_entry(
    entry: RawArtifactEntry,
    bundle_path: Path,
    errors: list[str],
) -> None:
    artifact_path = (bundle_path / entry["path"]).resolve()
    if not _is_relative_to(artifact_path, bundle_path.resolve()):
        errors.append(f"artifact {entry['role']} path escapes bundle")
        return
    if not artifact_path.is_file():
        errors.append(f"artifact {entry['role']} path does not exist: {artifact_path}")
        return
    if artifact_path.stat().st_size != entry["size_bytes"]:
        errors.append(f"artifact {entry['role']} size_bytes mismatch")
    actual_sha = claim_report_envelope.sha256_file(artifact_path)
    if actual_sha != entry["sha256"]:
        errors.append(f"artifact {entry['role']} sha256 mismatch")


def _artifact_entry(
    role: str,
    copied_path: Path,
    original_path: Path,
    bundle_path: Path,
) -> RawArtifactEntry:
    return {
        "role": role,
        "path": copied_path.relative_to(bundle_path).as_posix(),
        "original_path": str(original_path),
        "sha256": claim_report_envelope.sha256_file(copied_path),
        "size_bytes": copied_path.stat().st_size,
    }


def _bundle_artifact_name(role: str, path: Path, used_names: set[str]) -> str:
    safe_role = _safe_role(role)
    suffix = "".join(path.suffixes) or ".artifact"
    candidate = f"{safe_role}{suffix}"
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate
    stem = candidate.removesuffix(suffix)
    index = 2
    while f"{stem}-{index}{suffix}" in used_names:
        index += 1
    candidate = f"{stem}-{index}{suffix}"
    used_names.add(candidate)
    return candidate


def _safe_role(role: str) -> str:
    cleaned = _ROLE_RE.sub("-", role.strip()).strip("-._")
    if not cleaned:
        raise ValueError("artifact role must contain at least one safe character")
    return cleaned


def _environment_metadata() -> dict[str, object]:
    observed = claim_report_envelope.observe_current_state(_REPO_ROOT)
    return {
        "git": observed.get("git"),
        "uv_lock_sha256": observed.get("uv_lock_sha256"),
        "os_python": observed.get("os_python"),
        "dependency_versions": observed.get("dependency_versions"),
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_artifact_spec(raw_spec: str) -> RawArtifactSpec:
    role, separator, raw_path = raw_spec.partition("=")
    if not separator:
        raise ValueError("--artifact must use role=path")
    safe_role = _safe_role(role)
    return {"role": safe_role, "path": Path(raw_path).expanduser()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a private bundle")
    export_parser.add_argument("output_dir", type=Path)
    export_parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Artifact to include, formatted as role=path. Repeatable.",
    )
    export_parser.add_argument(
        "--command-invocation",
        required=True,
        help="Exact command that produced the bundled artifacts.",
    )
    verify_parser = subparsers.add_parser("verify", help="Verify a private bundle manifest")
    verify_parser.add_argument("manifest", type=Path)
    verify_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = cast("str", args.command)
    if command == "export":
        try:
            artifact_specs = [
                _parse_artifact_spec(raw_spec) for raw_spec in cast("list[str]", args.artifact)
            ]
        except ValueError as exc:
            parser.error(str(exc))
        result = export_bundle(
            cast("Path", args.output_dir),
            artifact_specs,
            command_invocation=cast("str", args.command_invocation),
        )
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 0 if result.status == "passed" else 1
    if command == "verify":
        result = verify_bundle(cast("Path", args.manifest))
        if cast("bool", args.json):
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(f"repro_bundle={result.status}")
            print(f"artifacts={result.artifact_count}")
            if result.errors:
                print("errors=" + "; ".join(result.errors))
        return 0 if result.status == "passed" else 1
    parser.error(f"unsupported command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
