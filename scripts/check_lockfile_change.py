"""Block accidental uv.lock changes unless explicitly allowed."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_ALLOW_ENV = "HEPH_ALLOW_LOCKFILE_CHANGE"
_TRUTHY = {"1", "true", "yes", "on"}


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
    completed = subprocess.run(
        ["git", "diff", "--name-only", git_diff, "--", "uv.lock"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in completed.stdout.splitlines() if line)


def _working_tree_lockfiles() -> tuple[str, ...]:
    staged = _git_name_only(["git", "diff", "--cached", "--name-only", "--", "uv.lock"])
    unstaged = _git_name_only(["git", "diff", "--name-only", "--", "uv.lock"])
    return tuple(dict.fromkeys((*staged, *unstaged)))


def _git_name_only(command: list[str]) -> tuple[str, ...]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return tuple(line for line in completed.stdout.splitlines() if line)


if __name__ == "__main__":
    raise SystemExit(main())
