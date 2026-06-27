"""Verify Heph release metadata and the official stable release pointer."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parent.parent
LICENSE_PATH = ROOT / "LICENSE"
RELEASE_MANIFEST_PATH = ROOT / "packages" / "heph" / "src" / "heph" / "state" / "release.toml"
PACKAGE_PYPROJECTS = (
    ROOT / "packages" / "ai" / "pyproject.toml",
    ROOT / "packages" / "extensions" / "pyproject.toml",
    ROOT / "packages" / "heph" / "pyproject.toml",
    ROOT / "packages" / "harness" / "pyproject.toml",
    ROOT / "packages" / "interfaces" / "pyproject.toml",
)


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    package: str
    command: str
    channel: str
    version: str
    tag: str
    release_workflow: str
    edge_workflow: str


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    errors = release_state_errors(
        current_version_must_match_stable=args.current_version_must_match_stable,
        require_tag=args.require_tag,
        tag=args.tag,
        commit=args.commit,
    )
    if not errors:
        print("Release state is coherent.")
        return 0

    print("Release state check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-version-must-match-stable",
        action="store_true",
        help="Require every workspace package version to match heph/state/release.toml.",
    )
    parser.add_argument(
        "--require-tag",
        action="store_true",
        help="Require the stable tag to exist in the local git repository.",
    )
    parser.add_argument(
        "--tag",
        help="Release tag being validated; defaults to the manifest tag.",
    )
    parser.add_argument(
        "--commit",
        help="Commit the release tag must point to; defaults to the tag target only check.",
    )
    return parser


def release_state_errors(
    *,
    current_version_must_match_stable: bool,
    require_tag: bool,
    tag: str | None,
    commit: str | None,
) -> list[str]:
    manifest = load_release_manifest()
    errors = [
        *_manifest_errors(manifest),
        *_license_errors(),
        *_package_metadata_errors(manifest, current_version_must_match_stable),
    ]
    release_tag = tag or manifest.tag
    if tag is not None and tag != manifest.tag:
        errors.append(f"release tag {tag!r} does not match manifest tag {manifest.tag!r}")
    if require_tag:
        errors.extend(_tag_errors(release_tag, commit=commit))
    return errors


def load_release_manifest() -> ReleaseManifest:
    data = cast(
        "dict[str, object]",
        tomllib.loads(RELEASE_MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    return ReleaseManifest(
        package=_required_string(data, "package"),
        command=_required_string(data, "command"),
        channel=_required_string(data, "channel"),
        version=_required_string(data, "version"),
        tag=_required_string(data, "tag"),
        release_workflow=_required_string(data, "release_workflow"),
        edge_workflow=_required_string(data, "edge_workflow"),
    )


def _required_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"release manifest field {key!r} must be a non-empty string")
    return value


def _manifest_errors(manifest: ReleaseManifest) -> list[str]:
    errors: list[str] = []
    if manifest.package != "heph":
        errors.append("release manifest package must be heph")
    if manifest.command != "heph":
        errors.append("release manifest command must be heph")
    if manifest.channel != "stable":
        errors.append("release manifest channel must be stable")
    expected_tag = f"v{manifest.version}"
    if manifest.tag != expected_tag:
        errors.append(
            f"release manifest tag {manifest.tag!r} must match version tag {expected_tag!r}"
        )
    if not (ROOT / manifest.release_workflow).is_file():
        errors.append(f"release workflow does not exist: {manifest.release_workflow}")
    if not (ROOT / manifest.edge_workflow).is_file():
        errors.append(f"edge workflow does not exist: {manifest.edge_workflow}")
    return errors


def _license_errors() -> list[str]:
    text = LICENSE_PATH.read_text(encoding="utf-8")
    if text.startswith("MIT License\n"):
        return []
    return ["root LICENSE must be the MIT License"]


def _package_metadata_errors(
    manifest: ReleaseManifest,
    current_version_must_match_stable: bool,
) -> list[str]:
    errors: list[str] = []
    for pyproject_path in PACKAGE_PYPROJECTS:
        project = _project_table(pyproject_path)
        name = _metadata_string(project, "name", pyproject_path)
        version = _metadata_string(project, "version", pyproject_path)
        license_name = _metadata_string(project, "license", pyproject_path)
        if license_name != "MIT":
            errors.append(f"{name} license must be MIT, got {license_name!r}")
        if current_version_must_match_stable and version != manifest.version:
            errors.append(
                f"{name} version {version!r} must match stable version {manifest.version!r}"
            )
    return errors


def _project_table(pyproject_path: Path) -> dict[str, object]:
    data = cast("dict[str, object]", tomllib.loads(pyproject_path.read_text(encoding="utf-8")))
    project = data.get("project")
    if not isinstance(project, dict):
        raise TypeError(f"{pyproject_path.relative_to(ROOT)} has no [project] table")
    return project


def _metadata_string(project: dict[str, object], key: str, pyproject_path: Path) -> str:
    value = project.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{pyproject_path.relative_to(ROOT)} project.{key} is invalid")
    return value


def _tag_errors(tag: str, *, commit: str | None) -> list[str]:
    observed = _git_ref_commit(f"refs/tags/{tag}")
    if observed is None:
        return [f"stable release tag does not exist: {tag}"]
    if commit is not None and observed != commit:
        return [f"stable release tag {tag} points to {observed}, not {commit}"]
    return []


def _git_ref_commit(ref: str) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
