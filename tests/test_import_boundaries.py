"""Import boundary enforcement tests for the new package structure.

Validates VAL-STRUCT-013, VAL-STRUCT-014, VAL-STRUCT-015, VAL-STRUCT-016:
- rag/ must not import agent/, chat/, or app/
- agent/ must not import chat.session
- chat/ must not import private (_-prefixed) symbols from agent/ or rag/
- No private cross-package imports anywhere
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "hephaistos"


def _module_imports(module_path: Path) -> list[str]:
    """Parse a Python file and return all imported hephaistos module paths."""
    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(module_path))
    except SyntaxError:
        return []
    return [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("hephaistos")
    ]


def _private_imports_from_other_package(
    module_path: Path,
) -> list[str]:
    """Find imports of _-prefixed names from a *different* top-level package."""
    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(module_path))
    except SyntaxError:
        return []

    parts = module_path.relative_to(ROOT).with_suffix("").parts
    my_top = parts[0]  # e.g. "rag", "agent", "chat"

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module or not node.module.startswith("hephaistos."):
            continue
        import_parts = node.module.split(".")
        if len(import_parts) < 2:
            continue
        their_top = import_parts[1]
        if their_top == my_top:
            continue  # same package, private imports are fine
        for alias in node.names or []:
            name = alias.name
            if name.startswith("_") and not name.startswith("__"):
                violations.append(
                    f"{module_path.relative_to(ROOT)}: "
                    f"from {node.module} import {name}"
                    f" (cross-package private)"
                )
    return violations


def _is_agent_or_rag_import(module_name: str) -> bool:
    """Check if a module name refers to hephaistos.agent or hephaistos.rag."""
    return module_name.startswith(("hephaistos.agent", "hephaistos.rag"))


# --- VAL-STRUCT-013: rag must not import agent, chat, or app ---


def _rag_modules() -> list[Path]:
    rag_dir = ROOT / "rag"
    if not rag_dir.is_dir():
        return []
    return sorted(p for p in rag_dir.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("module_path", _rag_modules(), ids=lambda p: str(p.relative_to(ROOT)))
def test_rag_does_not_import_agent_chat_app(
    module_path: Path,
) -> None:
    """VAL-STRUCT-013: No module under rag/ may import from agent, chat, or app."""
    forbidden_prefixes = (
        "hephaistos.agent",
        "hephaistos.chat",
        "hephaistos.app",
    )
    for imp in _module_imports(module_path):
        assert not imp.startswith(forbidden_prefixes), (
            f"{module_path.relative_to(ROOT)} imports {imp}, "
            f"which violates rag isolation from agent/chat/app"
        )


# --- VAL-STRUCT-014: agent must not import chat.session ---


def _agent_modules() -> list[Path]:
    agent_dir = ROOT / "agent"
    if not agent_dir.is_dir():
        return []
    return sorted(p for p in agent_dir.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("module_path", _agent_modules(), ids=lambda p: str(p.relative_to(ROOT)))
def test_agent_does_not_import_chat_session(
    module_path: Path,
) -> None:
    """VAL-STRUCT-014: No module under agent/ may import from chat.session."""
    forbidden = "hephaistos.chat.session"
    for imp in _module_imports(module_path):
        assert imp != forbidden, (
            f"{module_path.relative_to(ROOT)} imports {imp}, "
            f"which violates agent isolation from chat.session"
        )
        assert not imp.startswith(forbidden + "."), (
            f"{module_path.relative_to(ROOT)} imports {imp}, "
            f"which violates agent isolation from chat.session"
        )


# --- VAL-STRUCT-015: chat must not import private from agent or rag ---


def _chat_modules() -> list[Path]:
    chat_dir = ROOT / "chat"
    if not chat_dir.is_dir():
        return []
    return sorted(p for p in chat_dir.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("module_path", _chat_modules(), ids=lambda p: str(p.relative_to(ROOT)))
def test_chat_no_private_imports_from_agent_or_rag(
    module_path: Path,
) -> None:
    """VAL-STRUCT-015: chat/ must not import _-prefixed names from agent or rag."""
    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(module_path))
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module or not _is_agent_or_rag_import(node.module):
            continue
        for alias in node.names or []:
            name = alias.name
            if name.startswith("_") and not name.startswith("__"):
                pytest.fail(
                    f"{module_path.relative_to(ROOT)}: "
                    f"from {node.module} import {name}"
                    f" — private cross-package import"
                )


# --- VAL-STRUCT-016: no private cross-package imports anywhere ---


def _all_source_modules() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts and p.name != "__pycache__"
    )


@pytest.mark.parametrize(
    "module_path",
    _all_source_modules(),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_no_private_cross_package_imports(
    module_path: Path,
) -> None:
    """VAL-STRUCT-016: no _-prefixed cross-package imports."""
    violations = _private_imports_from_other_package(module_path)
    assert not violations, "\n".join(violations)


# --- VAL-STRUCT-018: import-linter contracts reference new packages ---


def test_import_linter_config_references_new_packages() -> None:
    """pyproject.toml lint-imports config must reference rag, agent, chat."""
    pyproject = (HERE.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "hephaistos.rag" in pyproject
    assert "hephaistos.agent" in pyproject
    assert "hephaistos.chat" in pyproject
    assert "hephaistos.materials" in pyproject
    assert "hephaistos.runtime" in pyproject


def test_import_linter_exits_clean() -> None:
    """lint-imports must exit 0 with all contracts kept."""
    lint_code = "from importlinter.cli import lint_imports_command; lint_imports_command()"
    result = subprocess.run(
        [sys.executable, "-c", lint_code],
        capture_output=True,
        text=True,
        cwd=str(HERE.parent),
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"lint-imports failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# --- Structural checks: no stale references ---


def test_no_harness_imports_remain() -> None:
    """No file should reference hephaistos.harness (deleted in Phase 3)."""
    result = subprocess.run(
        [
            "rg",
            "from hephaistos\\.harness",
            "hephaistos/",
            "tests/",
            "scripts/",
        ],
        capture_output=True,
        text=True,
        cwd=str(HERE.parent),
        check=False,
    )
    assert result.returncode != 0, f"Stale harness imports found:\n{result.stdout}"
