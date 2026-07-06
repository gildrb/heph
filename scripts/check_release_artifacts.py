"""Fast structural checks for built Heph release artifacts."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from scripts.release_stress_test import (
    _artifact_version,
    _release_artifacts,
)

EXPECTED_WHEEL_MEMBERS = frozenset(
    {
        "ai/py.typed",
        "extensions/py.typed",
        "heph/__init__.py",
        "heph/py.typed",
        "heph/state/release.toml",
        "harness/parameters/default.toml",
        "harness/py.typed",
        "interfaces/py.typed",
    }
)
EXPECTED_ENTRY_POINT = "heph = heph.cli.main:main"
INTERNAL_DISTRIBUTIONS = frozenset(
    canonicalize_name(name)
    for name in ("heph-ai", "heph-extensions", "heph-interfaces", "harness")
)


def main_with_args(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    wheels = _release_artifacts(args.dist, suffix=".whl")
    sdists = _release_artifacts(args.dist, suffix=".tar.gz")
    wheel = wheels["heph"]
    sdist = sdists["heph"]
    wheel_version = _artifact_version(wheel, suffix=".whl")
    sdist_version = _artifact_version(sdist, suffix=".tar.gz")
    if wheel_version != sdist_version:
        raise SystemExit(f"wheel/sdist version mismatch: {wheel_version} != {sdist_version}")
    _validate_wheel(wheel, expected_version=wheel_version)
    _validate_sdist(sdist)
    return 0


def main() -> int:
    return main_with_args()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    return parser


def _validate_wheel(path: Path, *, expected_version: str) -> None:
    with zipfile.ZipFile(path) as wheel:
        names = frozenset(wheel.namelist())
        missing = sorted(EXPECTED_WHEEL_MEMBERS - names)
        if missing:
            raise SystemExit(f"wheel is missing expected package data: {', '.join(missing)}")
        dist_info = _single_dist_info(names, suffix=".dist-info/METADATA")
        metadata = Parser().parsestr(wheel.read(dist_info).decode("utf-8"))
        if metadata.get("Name") != "heph":
            raise SystemExit(f"wheel metadata has wrong name: {metadata.get('Name')!r}")
        if metadata.get("Version") != expected_version:
            raise SystemExit(f"wheel metadata has wrong version: {metadata.get('Version')!r}")
        _validate_requires_dist(metadata.get_all("Requires-Dist", []))
        entry_points = _single_dist_info(names, suffix=".dist-info/entry_points.txt")
        entry_points_text = wheel.read(entry_points).decode("utf-8")
        if EXPECTED_ENTRY_POINT not in entry_points_text:
            raise SystemExit("wheel is missing the heph console script entry point")


def _validate_requires_dist(requirements: list[str]) -> None:
    for raw in requirements:
        try:
            requirement = Requirement(raw)
        except InvalidRequirement as exc:
            raise SystemExit(f"invalid Requires-Dist metadata: {raw!r}") from exc
        name = canonicalize_name(requirement.name)
        if name in INTERNAL_DISTRIBUTIONS:
            raise SystemExit(f"release wheel depends on internal distribution: {raw}")
        if requirement.url is not None:
            raise SystemExit(f"release wheel contains direct URL dependency: {raw}")


def _validate_sdist(path: Path) -> None:
    expected_suffixes = (
        "/LICENSE",
        "/pyproject.toml",
        "/src/ai/py.typed",
        "/src/extensions/py.typed",
        "/src/heph/__init__.py",
        "/src/heph/py.typed",
        "/src/heph/state/release.toml",
        "/src/harness/parameters/default.toml",
        "/src/harness/py.typed",
        "/src/interfaces/py.typed",
    )
    with tarfile.open(path) as sdist:
        names = frozenset(sdist.getnames())
    missing = [
        suffix for suffix in expected_suffixes if not any(name.endswith(suffix) for name in names)
    ]
    if missing:
        raise SystemExit(f"sdist is missing expected package data: {', '.join(missing)}")
    generated = [
        name for name in names if "__pycache__" in name or name.endswith((".pyc", ".pyo"))
    ]
    if generated:
        raise SystemExit(f"sdist contains generated Python artifacts: {', '.join(generated[:5])}")


def _single_dist_info(names: frozenset[str], *, suffix: str) -> str:
    matches = sorted(name for name in names if name.endswith(suffix))
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {suffix} file, found {len(matches)}")
    return matches[0]


if __name__ == "__main__":
    raise SystemExit(main())
