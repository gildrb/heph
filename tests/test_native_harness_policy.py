from __future__ import annotations

import re
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_agent_frameworks_are_not_project_dependencies() -> None:
    root = _project_root()
    dependency_manifests = (root / "pyproject.toml", root / "uv.lock")
    forbidden = ("langgraph", "llama-index", "llama_index", "llamaindex", "langchain")

    for manifest in dependency_manifests:
        text = manifest.read_text(encoding="utf-8").casefold()
        assert not any(name in text for name in forbidden), manifest


def test_runtime_harness_does_not_contain_fixture_specific_course_terms() -> None:
    root = _project_root()
    forbidden = re.compile(
        r"\b(?:"
        r"jesse|ratzkin|mfi|mathematik für informatiker|mathematik fuer informatiker|"
        r"amelia carter|northbridge|biochemistry 201"
        r")\b"
    )
    runtime_paths = [*(root / "hephaistos").rglob("*.py")]
    offenders = [
        f"{path.relative_to(root)} contains {match.group(0)!r}"
        for path in runtime_paths
        for match in forbidden.finditer(path.read_text(encoding="utf-8").casefold())
    ]

    assert not offenders, "\n".join(offenders)


def test_non_fixture_harness_scripts_do_not_contain_fixture_specific_course_terms() -> None:
    root = _project_root()
    forbidden = re.compile(
        r"\b(?:"
        r"jesse|ratzkin|mfi|mathematik für informatiker|mathematik fuer informatiker|"
        r"amelia carter|northbridge|biochemistry 201"
        r")\b"
    )
    excluded = {"audit_agent_harness_completion.py"}
    harness_paths = [
        path for path in (root / "scripts").rglob("*.py") if path.name not in excluded
    ]
    offenders = [
        f"{path.relative_to(root)} contains {match.group(0)!r}"
        for path in harness_paths
        for match in forbidden.finditer(path.read_text(encoding="utf-8").casefold())
    ]

    assert not offenders, "\n".join(offenders)
