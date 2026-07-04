"""Import boundary enforcement tests for the new package structure.

Validates VAL-STRUCT-013, VAL-STRUCT-014, VAL-STRUCT-015, VAL-STRUCT-016:
- rag/ must not import agent/, chat/, or adapters
- agent/ must not import chat.session
- chat/ must not import private (_-prefixed) symbols from agent/ or rag/
- No private cross-package imports anywhere
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
ROOT = REPO_ROOT / "packages" / "harness" / "src" / "harness"
HARNESS_CONCERNS = {
    "agent",
    "armory",
    "chat",
    "diagnostics",
    "matching",
    "materials",
    "memory",
    "parameters",
    "privacy",
    "rag",
    "safety",
    "documents",
    "vocab",
}


def test_source_root_exists() -> None:
    """Import-boundary checks must scan the real source tree."""
    assert ROOT.is_dir()


def _module_imports(module_path: Path) -> list[str]:
    """Parse a Python file and return imported module paths."""
    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(module_path))
    except SyntaxError:
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
    return imports


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
        if not node.module:
            continue
        import_parts = node.module.split(".")
        if len(import_parts) < 2 or import_parts[0] != "harness":
            continue
        their_top = import_parts[1]
        if their_top not in HARNESS_CONCERNS:
            continue
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
    """Check if a module name refers to agent or rag."""
    return module_name.startswith(("harness.agent", "harness.rag"))


# --- VAL-STRUCT-013: rag must not import agent, chat, or adapters ---


def _rag_modules() -> list[Path]:
    rag_dir = ROOT / "rag"
    if not rag_dir.is_dir():
        return []
    return sorted(p for p in rag_dir.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("module_path", _rag_modules(), ids=lambda p: str(p.relative_to(ROOT)))
def test_rag_does_not_import_agent_chat_adapters(
    module_path: Path,
) -> None:
    """VAL-STRUCT-013: No module under rag/ may import from agent, chat, or adapters."""
    forbidden_prefixes = (
        "heph.cli",
        "heph.commands",
        "harness.agent",
        "harness.chat",
        "interfaces.tui",
    )
    for imp in _module_imports(module_path):
        assert not imp.startswith(forbidden_prefixes), (
            f"{module_path.relative_to(ROOT)} imports {imp}, "
            f"which violates rag isolation from agent/chat/adapters"
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
    forbidden = "harness.chat.session"
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
                    f" - private cross-package import"
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
    assert "rag" in pyproject
    assert "agent" in pyproject
    assert "chat" in pyproject
    assert "materials" in pyproject
    assert "runtime" in pyproject


def test_import_linter_exits_clean() -> None:
    """lint-imports must exit 0 with all contracts kept."""
    lint_code = "from importlinter.cli import lint_imports_command; lint_imports_command()"
    result = subprocess.run(
        [sys.executable, "-c", lint_code],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"lint-imports failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# --- Structural checks: no stale references ---


def test_no_removed_harness_namespace_imports_remain() -> None:
    """No file should import through the removed flat concern modules."""
    stale_pattern = (
        "^(from|import) "
        "(agent|armory|chat|diagnostics|extension_contracts|matching|materials|memory|"
        "palette|parameters|privacy|rag|safety|documents|terminal|tui|version|vocab|_types)"
        "(\\.|\\s|$)"
    )
    if shutil.which("rg") is not None:
        result = subprocess.run(
            [
                "rg",
                stale_pattern,
                "packages/",
                "tests/",
                "scripts/",
                "conftest.py",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert result.returncode != 0, f"Stale flat concern imports found:\n{result.stdout}"
        return

    matches: list[str] = []
    prefixes = (
        "from agent",
        "from armory",
        "from chat",
        "from diagnostics",
        "from extension_contracts",
        "from matching",
        "from materials",
        "from memory",
        "from palette",
        "from parameters",
        "from privacy",
        "from rag",
        "from safety",
        "from documents",
        "from terminal",
        "from tui",
        "from version",
        "from vocab",
        "from _types",
        "import agent",
        "import armory",
        "import chat",
        "import diagnostics",
        "import extension_contracts",
        "import matching",
        "import materials",
        "import memory",
        "import palette",
        "import parameters",
        "import privacy",
        "import rag",
        "import safety",
        "import documents",
        "import terminal",
        "import tui",
        "import version",
        "import vocab",
        "import _types",
    )
    for relative in ("packages", "tests", "scripts"):
        base = REPO_ROOT / relative
        for path in sorted(base.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if line.startswith(prefixes):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{line_no}:{line}")
    assert not matches, "Stale flat concern imports found:\n" + "\n".join(matches)
