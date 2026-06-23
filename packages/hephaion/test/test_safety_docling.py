"""Tests for document conversion dependency policy."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_document_and_rag_backends_are_required_hephaion_dependencies() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    dependencies = pyproject["project"]["dependencies"]

    assert "bm25s==0.3.5" in dependencies
    assert "docling-slim[standard]==2.94.0" in dependencies
    assert "scikit-learn==1.8.0" in dependencies
    assert "sentence-transformers==5.3.0" in dependencies
    assert all(not dependency.startswith("docling==") for dependency in dependencies)


def test_managed_dependency_groups_do_not_duplicate_shipped_backends() -> None:
    pyproject_path = Path(__file__).parents[3] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())
    groups = pyproject["dependency-groups"]

    flattened = [dependency for group in groups.values() for dependency in group]

    assert all(not dependency.startswith("torch") for dependency in flattened)
    assert all(not dependency.startswith("bm25s") for dependency in flattened)
    assert all(not dependency.startswith("scikit-learn") for dependency in flattened)
    assert all(not dependency.startswith("sentence-transformers") for dependency in flattened)
