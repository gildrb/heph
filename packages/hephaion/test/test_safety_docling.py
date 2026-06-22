"""Tests for quality-first Docling dependency policy."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_docling_is_core_dependency_not_optional_extra() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    assert "docling==2.94.0" in pyproject["project"]["dependencies"]
    assert "docling" not in pyproject["project"].get("optional-dependencies", {})
    assert "docling" not in pyproject.get("dependency-groups", {})
