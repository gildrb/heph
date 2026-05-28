"""Verify direct dependency declarations use exact pins."""

from __future__ import annotations

import sys
import tomllib
from collections.abc import Iterable, Iterator
from pathlib import Path

_FORBIDDEN_SPECIFIERS = (">=", "~=", "!=", "<=", "<", ">")


def main() -> int:
    pyproject_path = Path("pyproject.toml")
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    unpinned = [
        f"{section}: {requirement}"
        for section, requirement in _iter_direct_requirements(data)
        if not _is_exact_pin(requirement)
    ]
    if not unpinned:
        return 0

    print("Direct dependencies must be pinned with == exact versions:", file=sys.stderr)
    for item in unpinned:
        print(f"- {item}", file=sys.stderr)
    return 1


def _iter_direct_requirements(data: dict[str, object]) -> Iterator[tuple[str, str]]:
    project = data.get("project")
    if isinstance(project, dict):
        yield from _iter_string_list("project.dependencies", project.get("dependencies"))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for group, requirements in optional.items():
                if isinstance(group, str):
                    yield from _iter_string_list(
                        f"project.optional-dependencies.{group}",
                        requirements,
                    )

    build_system = data.get("build-system")
    if isinstance(build_system, dict):
        yield from _iter_string_list("build-system.requires", build_system.get("requires"))

    dependency_groups = data.get("dependency-groups")
    if isinstance(dependency_groups, dict):
        for group, requirements in dependency_groups.items():
            if isinstance(group, str):
                yield from _iter_string_list(f"dependency-groups.{group}", requirements)


def _iter_string_list(section: str, value: object) -> Iterator[tuple[str, str]]:
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, str):
            yield section, item


def _is_exact_pin(requirement: str) -> bool:
    requirement_part = requirement.split(";", maxsplit=1)[0].strip()
    if "==" not in requirement_part:
        return False
    before_pin, after_pin = requirement_part.split("==", maxsplit=1)
    if not before_pin.strip() or not after_pin.strip():
        return False
    return not _contains_any(after_pin, _FORBIDDEN_SPECIFIERS)


def _contains_any(value: str, needles: Iterable[str]) -> bool:
    return any(needle in value for needle in needles)


if __name__ == "__main__":
    raise SystemExit(main())
