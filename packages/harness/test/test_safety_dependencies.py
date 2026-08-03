"""Tests for document and RAG dependency policy."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_document_and_rag_backends_are_removed_from_harness_dependencies() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    dependencies = pyproject["project"]["dependencies"]
    assert all(
        not dependency.startswith(("bm25s", "scikit-learn", "sentence-transformers"))
        for dependency in dependencies
    )
    assert "optional-dependencies" not in pyproject["project"]


def test_managed_dependency_groups_do_not_duplicate_shipped_backends() -> None:
    pyproject_path = Path(__file__).parents[3] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())
    groups = pyproject["dependency-groups"]

    flattened = [dependency for group in groups.values() for dependency in group]

    assert all(not dependency.startswith("torch") for dependency in flattened)
    assert all(not dependency.startswith("bm25s") for dependency in flattened)
    assert all(not dependency.startswith("scikit-learn") for dependency in flattened)
    assert all(not dependency.startswith("sentence-transformers") for dependency in flattened)


def test_heph_does_not_forward_optional_profiles() -> None:
    harness = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())["project"]
    heph = tomllib.loads((Path(__file__).parents[2] / "heph" / "pyproject.toml").read_text())[
        "project"
    ]
    assert "optional-dependencies" not in harness
    assert "optional-dependencies" not in heph
