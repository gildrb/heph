from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path
from typing import cast

import pytest

from scripts import generate_benchmark_summary

ROOT = Path(__file__).resolve().parent.parent


def _pyproject() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _project_table() -> dict[str, object]:
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    return cast("dict[str, object]", project)


def _optional_dependencies() -> dict[str, list[str]]:
    project = _project_table()
    optional = project["optional-dependencies"]
    assert isinstance(optional, dict)
    result: dict[str, list[str]] = {}
    for extra, dependencies in optional.items():
        assert isinstance(extra, str)
        assert isinstance(dependencies, list)
        result[extra] = [dependency for dependency in dependencies if isinstance(dependency, str)]
    return result


def test_beir_extra_uses_verified_dependency_without_unavailable_package() -> None:
    optional = _optional_dependencies()

    assert optional["beir"] == ["beir>=2.2.0"]
    assert all(
        "beir-datasets" not in dependency.lower()
        for dependencies in optional.values()
        for dependency in dependencies
    )


def test_visualization_extra_is_optional_and_matches_summary_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    optional = _optional_dependencies()
    default_dependencies = _project_table()["dependencies"]
    assert isinstance(default_dependencies, list)

    assert "visualization" in optional
    assert any(dependency.startswith("matplotlib>=") for dependency in optional["visualization"])
    assert all(not str(dependency).startswith("matplotlib") for dependency in default_dependencies)

    original_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, package: str | None = None) -> object | None:
        if name == "matplotlib":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    notes = generate_benchmark_summary._visualization_notes(include_visualizations=True)

    assert notes
    assert "uv sync --extra visualization" in notes[0]


def test_lockfile_metadata_tracks_benchmark_optional_extras() -> None:
    lock_text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    match = re.search(r"provides-extras = \[(?P<extras>[^\]]+)\]", lock_text)

    assert match is not None
    extras = {item.strip().strip('"') for item in match.group("extras").split(",")}
    assert {"beir", "visualization"} <= extras
