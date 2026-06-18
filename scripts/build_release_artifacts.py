"""Build official Heph release artifacts for the reviewed stable tag."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from scripts.check_release_state import load_release_manifest, release_state_errors

ROOT = Path(__file__).resolve().parent.parent
RELEASE_CONFIG_PATH = (
    ROOT / "packages" / "hephaion" / "src" / "hephaion" / "privacy" / "release.py"
)
BUILD_INPUT_PATHS = (
    "packages",
    "pyproject.toml",
    "uv.lock",
    "build-constraints.txt",
    "LICENSE",
)


@dataclass(frozen=True, slots=True)
class ReleaseBuildConfig:
    channel: str
    version: str
    posthog_host: str | None
    posthog_project_token: str | None
    sentry_dsn: str | None


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    manifest = load_release_manifest()
    release_version = args.release_version or manifest.tag
    errors = release_state_errors(
        current_version_must_match_stable=True,
        require_tag=True,
        tag=manifest.tag,
        commit=None,
    )
    if not args.allow_dirty_build_inputs:
        errors.extend(release_build_input_errors(manifest.tag))
    if errors:
        print("Release artifact build refused:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    config = release_build_config_from_env(
        os.environ,
        channel=args.channel,
        release_version=release_version,
    )
    dist = args.dist
    if args.clean:
        clean_dist(dist)
    with patched_release_config(RELEASE_CONFIG_PATH, config):
        _run(
            [
                "uv",
                "build",
                "--all-packages",
                "--build-constraints",
                str(args.build_constraints),
                "--require-hashes",
                "--no-sources",
                "--out-dir",
                str(dist),
            ],
            cwd=ROOT,
        )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--build-constraints", type=Path, default=Path("build-constraints.txt"))
    parser.add_argument("--channel", default="pypi")
    parser.add_argument(
        "--release-version",
        help="Runtime release version to inject; defaults to the stable manifest tag.",
    )
    parser.add_argument(
        "--allow-dirty-build-inputs",
        action="store_true",
        help="Allow package, lockfile, build constraint, or license changes outside the tag.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_false",
        dest="clean",
        help="Do not remove existing wheel and sdist files from the output directory first.",
    )
    parser.set_defaults(clean=True)
    return parser


def release_build_config_from_env(
    env: Mapping[str, str],
    *,
    channel: str,
    release_version: str,
) -> ReleaseBuildConfig:
    return ReleaseBuildConfig(
        channel=channel,
        version=release_version,
        posthog_host=env.get("HEPHAION_POSTHOG_HOST"),
        posthog_project_token=env.get("HEPHAION_POSTHOG_PROJECT_TOKEN"),
        sentry_dsn=env.get("HEPHAION_SENTRY_DSN"),
    )


def render_release_config(config: ReleaseBuildConfig) -> str:
    lines = [
        '"""Release-time privacy and diagnostics configuration."""',
        "",
        "from __future__ import annotations",
        "",
        f"POSTHOG_HOST: str | None = {_literal(config.posthog_host)}",
        f"POSTHOG_PROJECT_TOKEN: str | None = {_literal(config.posthog_project_token)}",
        f"SENTRY_DSN: str | None = {_literal(config.sentry_dsn)}",
        f"RELEASE_CHANNEL: str | None = {_literal(config.channel)}",
        f"RELEASE_VERSION: str | None = {_literal(config.version)}",
        "",
    ]
    return "\n".join(lines)


@contextmanager
def patched_release_config(path: Path, config: ReleaseBuildConfig) -> Iterator[None]:
    original = path.read_text(encoding="utf-8")
    path.write_text(render_release_config(config), encoding="utf-8")
    try:
        yield
    finally:
        path.write_text(original, encoding="utf-8")


def clean_dist(dist: Path) -> None:
    dist.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.whl", "*.tar.gz"):
        for path in dist.glob(pattern):
            path.unlink()


def _literal(value: str | None) -> str:
    if value is None:
        return "None"
    stripped = value.strip()
    return json.dumps(stripped) if stripped else "None"


def release_build_input_errors(tag: str) -> list[str]:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *BUILD_INPUT_PATHS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode != 0:
        return ["could not check uncommitted release build inputs"]
    uncommitted = [line for line in status.stdout.splitlines() if line.strip()]
    if uncommitted:
        return ["release build inputs have uncommitted changes: " + ", ".join(uncommitted)]

    diff = subprocess.run(
        ["git", "diff", "--name-only", f"refs/tags/{tag}", "--", *BUILD_INPUT_PATHS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff.returncode != 0:
        return [f"could not compare release build inputs with {tag}"]
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    if not changed:
        return []
    return [f"release build inputs differ from {tag}: " + ", ".join(changed)]


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
