"""Block accidental uv.lock changes unless explicitly allowed."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path

_ALLOW_ENV = "HEPH_ALLOW_LOCKFILE_CHANGE"
_TRUTHY = {"1", "true", "yes", "on"}
_PYPROJECT = "pyproject.toml"


def main() -> int:
    args = _build_parser().parse_args()
    if _lockfile_change_allowed():
        return 0

    changed = _changed_lockfiles(args)
    if not changed:
        return 0

    print(
        f"uv.lock changed. Set {_ALLOW_ENV}=1 only after dependency changes are reviewed.",
        file=sys.stderr,
    )
    for path in changed:
        print(f"- {path}", file=sys.stderr)
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument(
        "--git-diff", help="Git diff range to inspect, for example origin/main...HEAD"
    )
    return parser


def _lockfile_change_allowed() -> bool:
    return os.environ.get(_ALLOW_ENV, "").strip().casefold() in _TRUTHY


def _changed_lockfiles(args: argparse.Namespace) -> tuple[str, ...]:
    if isinstance(args.git_diff, str) and args.git_diff:
        return _lockfiles_from_git_diff(args.git_diff)
    paths = tuple(path for path in args.paths if Path(path).name == "uv.lock")
    if paths:
        return paths
    return _working_tree_lockfiles()


def _lockfiles_from_git_diff(git_diff: str) -> tuple[str, ...]:
    dependency_declarations_changed = _dependency_declarations_changed(git_diff)
    completed = subprocess.run(
        ["git", "diff", "--name-only", git_diff, "--", "uv.lock"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        path
        for path in completed.stdout.splitlines()
        if path
        and _lockfile_requires_dependency_review(
            git_diff,
            path,
            dependency_declarations_changed=dependency_declarations_changed,
        )
    )


def _lockfile_requires_dependency_review(
    git_diff: str,
    path: str,
    *,
    dependency_declarations_changed: bool,
) -> bool:
    if dependency_declarations_changed:
        return False
    before = _lockfile_package_payloads(_git_file_at_diff_base(git_diff, path))
    after = _lockfile_package_payloads(Path(path).read_bytes())
    return before != after


def _dependency_declarations_changed(git_diff: str) -> bool:
    base_ref = _git_diff_base_ref(git_diff)
    before = _pyproject_dependency_payloads(_git_file_at_ref(base_ref, _PYPROJECT))
    after = _pyproject_dependency_payloads(Path(_PYPROJECT).read_bytes())
    return before != after


def _git_file_at_diff_base(git_diff: str, path: str) -> bytes:
    base_ref = _git_diff_base_ref(git_diff)
    return _git_file_at_ref(base_ref, path)


def _git_file_at_ref(ref: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _git_diff_base_ref(git_diff: str) -> str:
    if "..." not in git_diff:
        return git_diff.rsplit("..", 1)[0]
    left, right = git_diff.split("...", 1)
    completed = subprocess.run(
        ["git", "merge-base", left, right or "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _lockfile_package_payloads(content: bytes) -> tuple[str, ...]:
    data = tomllib.loads(content.decode("utf-8"))
    packages = data.get("package")
    if not isinstance(packages, list):
        return ()
    return tuple(
        sorted(
            repr(package)
            for package in packages
            if isinstance(package, dict) and not _is_editable_project_package(package)
        )
    )


def _pyproject_dependency_payloads(content: bytes) -> tuple[str, ...]:
    data = tomllib.loads(content.decode("utf-8"))
    payloads: list[str] = []
    project = data.get("project")
    if isinstance(project, dict):
        dependencies = project.get("dependencies")
        if isinstance(dependencies, list):
            payloads.extend(repr(dependency) for dependency in dependencies)
        optional_dependencies = project.get("optional-dependencies")
        if isinstance(optional_dependencies, dict):
            payloads.extend(
                repr((group, dependency))
                for group, dependencies in optional_dependencies.items()
                if isinstance(group, str)
                for dependency in dependencies
                if isinstance(dependency, str)
            )
    dependency_groups = data.get("dependency-groups")
    if isinstance(dependency_groups, dict):
        payloads.extend(
            repr((group, dependency))
            for group, dependencies in dependency_groups.items()
            if isinstance(group, str)
            for dependency in dependencies
            if isinstance(dependency, str)
        )
    return tuple(sorted(payloads))


def _is_editable_project_package(package: Mapping[object, object]) -> bool:
    source = package.get("source")
    if not isinstance(source, Mapping):
        return False
    return any(key == "editable" and value == "." for key, value in source.items())


def _working_tree_lockfiles() -> tuple[str, ...]:
    staged = _git_name_only(["git", "diff", "--cached", "--name-only", "--", "uv.lock"])
    unstaged = _git_name_only(["git", "diff", "--name-only", "--", "uv.lock"])
    return tuple(dict.fromkeys((*staged, *unstaged)))


def _git_name_only(command: list[str]) -> tuple[str, ...]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return tuple(line for line in completed.stdout.splitlines() if line)


if __name__ == "__main__":
    raise SystemExit(main())
