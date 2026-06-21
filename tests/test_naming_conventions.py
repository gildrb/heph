"""Regression test: test naming conventions are followed."""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTS_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# File naming
# ---------------------------------------------------------------------------


def test_all_test_files_match_convention() -> None:
    """Every .py file in tests/ must be test_*.py or conftest.py."""
    for path in sorted(TESTS_DIR.glob("*.py")):
        assert path.name.startswith("test_") or path.name == "conftest.py", (
            f"Unexpected test file name: {path.name} (expected test_*.py or conftest.py)"
        )


def test_no_suffix_test_files() -> None:
    """No *_test.py files should exist (we use test_*.py only)."""
    suffix_files = list(TESTS_DIR.glob("*_test.py"))
    assert not suffix_files, (
        f"Found *_test.py files: {[p.name for p in suffix_files]} (use test_*.py instead)"
    )


# ---------------------------------------------------------------------------
# Function and class naming inside test files
# ---------------------------------------------------------------------------


def _collect_top_level_test_functions(path: Path) -> list[str]:
    """Return top-level test function names (not methods inside a class)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    func_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    return [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, func_types) and node.name.startswith("test_")
    ]


def _collect_test_classes(path: Path) -> list[str]:
    """Return test class names (Test*)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
    ]


def test_top_level_function_names_are_descriptive() -> None:
    """Top-level test functions must have at least two words after 'test_'.

    Methods inside test classes are exempt — the class name provides context.
    """
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        for name in _collect_top_level_test_functions(path):
            after_prefix = name.removeprefix("test_")
            parts = after_prefix.split("_")
            assert len(parts) >= 2, (
                f"{path.name}: top-level test function '{name}' "
                f"is too short — use test_<verb>_<object> pattern "
                f"(got only '{parts[0]}')"
            )


def test_class_names_are_pascal_case_after_test_prefix() -> None:
    """Test class names must be Test + PascalCase (e.g. TestBuildIndex)."""
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        for name in _collect_test_classes(path):
            after_prefix = name.removeprefix("Test")
            assert after_prefix, (
                f"{path.name}: test class '{name}' is just 'Test' with no descriptor"
            )
            assert re.match(r"^[A-Z]", after_prefix), (
                f"{path.name}: test class '{name}' must use PascalCase after 'Test' prefix"
            )
            assert "_" not in after_prefix, (
                f"{path.name}: test class '{name}' must not contain underscores (use PascalCase)"
            )
