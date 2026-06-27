"""Build official Heph release artifacts for the reviewed stable tag."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from scripts.check_release_state import load_release_manifest, release_state_errors

ROOT = Path(__file__).resolve().parent.parent
RELEASE_CONFIG_PATH = ROOT / "packages" / "harness" / "src" / "harness" / "privacy" / "release.py"
RELEASE_BUILD_ROOT = ROOT / ".artifacts" / "release-build"
BUILD_INPUT_PATHS = (
    "packages",
    "pyproject.toml",
    "uv.lock",
    "build-constraints.txt",
    "LICENSE",
)
INTERNAL_DISTRIBUTIONS = frozenset(
    canonicalize_name(name)
    for name in ("heph-ai", "heph-extensions", "heph-interfaces", "harness")
)
RELEASE_PACKAGE_PYPROJECTS = (
    ROOT / "packages" / "ai" / "pyproject.toml",
    ROOT / "packages" / "extensions" / "pyproject.toml",
    ROOT / "packages" / "heph" / "pyproject.toml",
    ROOT / "packages" / "harness" / "pyproject.toml",
    ROOT / "packages" / "interfaces" / "pyproject.toml",
)


@dataclass(frozen=True, slots=True)
class PackageSource:
    package: str
    source: Path


@dataclass(frozen=True, slots=True)
class ProjectAuthor:
    name: str
    email: str | None


RELEASE_PACKAGE_SOURCES = (
    PackageSource("ai", ROOT / "packages" / "ai" / "src" / "ai"),
    PackageSource("extensions", ROOT / "packages" / "extensions" / "src" / "extensions"),
    PackageSource("heph", ROOT / "packages" / "heph" / "src" / "heph"),
    PackageSource("harness", ROOT / "packages" / "harness" / "src" / "harness"),
    PackageSource("interfaces", ROOT / "packages" / "interfaces" / "src" / "interfaces"),
)
RELEASE_SOURCE_IGNORE_PATTERNS = (
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
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
        project_dir = stage_release_project(args.build_root)
        _run(
            [
                "uv",
                "build",
                "--build-constraints",
                str(args.build_constraints),
                "--require-hashes",
                "--no-sources",
                "--out-dir",
                str(dist),
                str(project_dir),
            ],
            cwd=ROOT,
        )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--build-constraints", type=Path, default=Path("build-constraints.txt"))
    parser.add_argument("--build-root", type=Path, default=RELEASE_BUILD_ROOT)
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
        posthog_host=env.get("HARNESS_POSTHOG_HOST"),
        posthog_project_token=env.get("HARNESS_POSTHOG_PROJECT_TOKEN"),
        sentry_dsn=env.get("HARNESS_SENTRY_DSN"),
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


def stage_release_project(build_root: Path) -> Path:
    project = load_project_table(ROOT / "packages" / "heph" / "pyproject.toml")
    version = string_field(project, "version")
    project_dir = build_root / f"heph-{version}"
    if project_dir.exists():
        shutil.rmtree(project_dir)
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True)
    for package_source in RELEASE_PACKAGE_SOURCES:
        shutil.copytree(
            package_source.source,
            src_dir / package_source.package,
            ignore=shutil.ignore_patterns(*RELEASE_SOURCE_IGNORE_PATTERNS),
        )
    shutil.copy2(ROOT / "LICENSE", project_dir / "LICENSE")
    shutil.copy2(ROOT / "packages" / "heph" / "README.md", project_dir / "README.md")
    (project_dir / "pyproject.toml").write_text(
        render_release_project(project, release_dependencies()),
        encoding="utf-8",
    )
    return project_dir


def render_release_project(
    project: Mapping[str, object],
    dependencies: Sequence[str],
) -> str:
    lines = [
        "[project]",
        f"name = {toml_string(string_field(project, 'name'))}",
        f"version = {toml_string(string_field(project, 'version'))}",
        f"description = {toml_string(string_field(project, 'description'))}",
        f"readme = {toml_string(string_field(project, 'readme'))}",
        f"license = {toml_string(string_field(project, 'license'))}",
        render_authors(author_entries(project)),
        f"requires-python = {toml_string(string_field(project, 'requires-python'))}",
        render_string_array("keywords", string_sequence_field(project, "keywords")),
        render_string_array("classifiers", string_sequence_field(project, "classifiers")),
        render_string_array("dependencies", dependencies),
        "",
        "[project.urls]",
        render_string_table(table_field(project, "urls")),
        "",
        "[project.scripts]",
        render_string_table(table_field(project, "scripts")),
        "",
        "[build-system]",
        'requires = ["setuptools==81.0.0"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[tool.setuptools]",
        'package-dir = {"" = "src"}',
        "include-package-data = true",
        "",
        "[tool.setuptools.packages.find]",
        'where = ["src"]',
        'include = ["ai*", "extensions*", "heph*", "harness*", "interfaces*"]',
        "",
        "[tool.setuptools.package-data]",
        '"*" = ["*.md", "*.toml", "*.jsonl", "py.typed"]',
        "",
    ]
    return "\n".join(lines)


def release_dependencies() -> tuple[str, ...]:
    dependencies: list[str] = []
    seen_by_name: dict[str, str] = {}
    for path in RELEASE_PACKAGE_PYPROJECTS:
        for dependency in project_dependencies(path):
            dependency_name = requirement_name(dependency, source=path)
            if dependency_name in INTERNAL_DISTRIBUTIONS:
                continue
            previous = seen_by_name.get(dependency_name)
            if previous is None:
                dependencies.append(dependency)
                seen_by_name[dependency_name] = dependency
            elif previous != dependency:
                raise ValueError(
                    f"conflicting release dependency for {dependency_name}: "
                    f"{previous!r} and {dependency!r}"
                )
    return tuple(dependencies)


def load_project_table(pyproject: Path) -> Mapping[str, object]:
    with pyproject.open("rb") as file:
        data = tomllib.load(file)
    project = data.get("project")
    if not isinstance(project, dict):
        raise TypeError(f"{pyproject} has no [project] table")
    return project


def project_dependencies(pyproject: Path) -> tuple[str, ...]:
    project = load_project_table(pyproject)
    value = project.get("dependencies")
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{pyproject} [project].dependencies must be a string array")
    return tuple(value)


def requirement_name(dependency: str, *, source: Path) -> str:
    try:
        return str(canonicalize_name(Requirement(dependency).name))
    except InvalidRequirement as exc:
        raise ValueError(f"{source} has invalid dependency {dependency!r}") from exc


def string_field(table: Mapping[str, object], key: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"[project].{key} must be a non-empty string")
    return value


def string_sequence_field(table: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = table.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"[project].{key} must be a string array")
    return tuple(value)


def table_field(table: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = table.get(key)
    if not isinstance(value, dict):
        raise TypeError(f"[project].{key} must be a table")
    return value


def author_entries(project: Mapping[str, object]) -> tuple[ProjectAuthor, ...]:
    value = project.get("authors")
    if not isinstance(value, list):
        raise TypeError("[project].authors must be an array")
    authors: list[ProjectAuthor] = []
    for author in value:
        if not isinstance(author, dict):
            raise TypeError("[project].authors entries must be tables")
        name = author.get("name")
        email = author.get("email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("[project].authors entries must include a non-empty name")
        if email is not None and not isinstance(email, str):
            raise ValueError("[project].authors email must be a string")
        authors.append(ProjectAuthor(name=name, email=email))
    if not authors:
        raise ValueError("[project].authors must not be empty")
    return tuple(authors)


def render_authors(authors: Sequence[ProjectAuthor]) -> str:
    lines = ["authors = ["]
    for author in authors:
        fields = [f"name = {toml_string(author.name)}"]
        if author.email is not None:
            fields.append(f"email = {toml_string(author.email)}")
        lines.append("    { " + ", ".join(fields) + " },")
    lines.append("]")
    return "\n".join(lines)


def render_string_array(key: str, values: Sequence[str]) -> str:
    if not values:
        return f"{key} = []"
    lines = [f"{key} = ["]
    lines.extend(f"    {toml_string(value)}," for value in values)
    lines.append("]")
    return "\n".join(lines)


def render_string_table(table: Mapping[str, object]) -> str:
    lines: list[str] = []
    for key, value in table.items():
        if not isinstance(value, str):
            raise TypeError(f"table value for {key!r} must be a string")
        lines.append(f"{key} = {toml_string(value)}")
    return "\n".join(lines)


def toml_string(value: str) -> str:
    return json.dumps(value)


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
