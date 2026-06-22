"""Verify source-only locked dependencies are explicitly reviewed."""

from __future__ import annotations

import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import TypeGuard

_ALLOWED_SOURCE_ONLY_SDISTS = {
    (
        "antlr4-python3-runtime",
        "4.9.3",
    ): "sha256:f224469b4168294902bb1efa80a8bf7855f24c99aef99cbefc1bcd3cce77881b",
    (
        "pylatexenc",
        "2.10",
    ): "sha256:3dd8fd84eb46dc30bee1e23eaab8d8fb5a7f507347b23e5f38ad9675c84f40d3",
    (
        "unicodeit",
        "0.7.5",
    ): "sha256:f100df7a1b8c64d7b5160859426b641cd9f30218173c5a3450842370e242a168",
}


def allowed_source_only_package_names() -> tuple[str, ...]:
    return tuple(sorted({name for name, _version in _ALLOWED_SOURCE_ONLY_SDISTS}))


def main() -> int:
    lock_path = Path("uv.lock")
    data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    violations = list(_source_only_sdist_violations(data))
    if not violations:
        return 0

    print("Unreviewed source-only sdists found in uv.lock:", file=sys.stderr)
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    print(
        "Review the package and add its exact name/version/hash to the allowlist.", file=sys.stderr
    )
    return 1


def _source_only_sdist_violations(data: dict[str, object]) -> list[str]:
    packages = data.get("package")
    if not isinstance(packages, list):
        return ["uv.lock has no package array"]

    violations: list[str] = []
    for package in packages:
        if not _is_string_key_mapping(package):
            continue
        name = package.get("name")
        version = package.get("version")
        sdist = package.get("sdist")
        wheels = package.get("wheels")
        if (
            not isinstance(name, str)
            or not isinstance(version, str)
            or not _is_string_key_mapping(sdist)
        ):
            continue
        if isinstance(wheels, list) and wheels:
            continue
        observed_hash = sdist.get("hash")
        allowed_hash = _ALLOWED_SOURCE_ONLY_SDISTS.get((name, version))
        if observed_hash != allowed_hash:
            violations.append(f"{name}=={version} ({observed_hash})")
    return violations


def _is_string_key_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


if __name__ == "__main__":
    raise SystemExit(main())
