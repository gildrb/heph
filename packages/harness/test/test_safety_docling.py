"""Tests for document conversion dependency policy."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_document_and_rag_backends_are_optional_harness_dependencies() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    dependencies = pyproject["project"]["dependencies"]
    optional = pyproject["project"]["optional-dependencies"]

    assert all(
        not dependency.startswith(
            ("bm25s", "docling-slim", "scikit-learn", "sentence-transformers")
        )
        for dependency in dependencies
    )
    assert optional["search"] == ["bm25s==0.3.5"]
    assert optional["embeddings"] == [
        "scikit-learn==1.8.0",
        "sentence-transformers==5.3.0",
    ]
    assert optional["documents"] == ["docling-slim[standard]==2.94.0"]
    assert set(optional["all"]) == {
        dependency
        for group in ("search", "embeddings", "documents")
        for dependency in optional[group]
    }
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


def test_heph_forwards_the_harness_optional_profiles() -> None:
    harness = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())["project"][
        "optional-dependencies"
    ]
    heph = tomllib.loads((Path(__file__).parents[2] / "heph" / "pyproject.toml").read_text())[
        "project"
    ]["optional-dependencies"]

    assert set(harness) == {"search", "embeddings", "documents", "all"}
    assert set(heph) == set(harness)
    assert heph == {name: [f"harness[{name}]==0.0.59"] for name in harness}
