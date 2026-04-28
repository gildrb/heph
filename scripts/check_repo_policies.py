"""Enforce repository-specific typing and import policies."""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
SCAN_ROOTS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "hephaistos",
    REPO_ROOT / "tests",
    REPO_ROOT / "scripts",
    REPO_ROOT / "vulture-whitelist.py",
)
SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "build",
        "dist",
    }
)
ALLOWED_DYNAMIC_IMPORT_CALLS: Final[dict[str, frozenset[str]]] = {
    "hephaistos/app/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/app/workspace.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/harness/tools.py": frozenset(
        {
            "importlib.util.module_from_spec",
            "importlib.util.spec_from_file_location",
        }
    ),
    "hephaistos/source/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
}


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    column: int
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}:{self.column}: {self.message}"


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        for path in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def _dotted_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None


def _is_type_checking_guard(test: ast.expr) -> bool:
    dotted = _dotted_name(test)
    return dotted in {"TYPE_CHECKING", "typing.TYPE_CHECKING"}


class PolicyVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[Violation] = []
        self._stack: list[ast.AST] = []

    def visit(self, node: ast.AST) -> None:
        self._stack.append(node)
        super().visit(node)
        self._stack.pop()

    def _add(self, node: ast.AST, message: str) -> None:
        self.violations.append(
            Violation(
                path=self.rel_path,
                line=getattr(node, "lineno", 1),
                column=getattr(node, "col_offset", 0) + 1,
                message=message,
            )
        )

    def _import_context_is_allowed(self) -> bool:
        for ancestor in self._stack[:-1]:
            if isinstance(ancestor, ast.Module):
                continue
            if isinstance(ancestor, ast.Try):
                continue
            if isinstance(ancestor, ast.If) and _is_type_checking_guard(ancestor.test):
                continue
            return False
        return True

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        if not self._import_context_is_allowed():
            self._add(node, "deferred imports are forbidden outside module scope")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if not self._import_context_is_allowed():
            self._add(node, "deferred imports are forbidden outside module scope")
        if node.module in {"typing", "typing_extensions"}:
            for alias in node.names:
                if alias.name == "Any":
                    self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if node.id == "Any":
            self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        dotted = _dotted_name(node)
        if dotted in {"typing.Any", "typing_extensions.Any"}:
            self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        dotted = _dotted_name(node.func)
        if dotted in {
            "__import__",
            "importlib.import_module",
            "importlib.util.module_from_spec",
            "importlib.util.spec_from_file_location",
        }:
            allowed = ALLOWED_DYNAMIC_IMPORT_CALLS.get(self.rel_path, frozenset())
            if dotted not in allowed:
                self._add(node, f"dynamic import helper `{dotted}` is forbidden here")

        if dotted in {"cast", "typing.cast"} and node.args:
            first_arg = node.args[0]
            if (
                isinstance(first_arg, ast.Constant)
                and isinstance(first_arg.value, str)
                and "Any" in first_arg.value
            ):
                self._add(node, "cast strings may not reference Any")

        self.generic_visit(node)


def _check_file(path: Path) -> list[Violation]:
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = PolicyVisitor(rel_path)
    visitor.visit(tree)
    return visitor.violations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enforce explicit Any and deferred-import repo policies.",
    )
    parser.parse_args()

    violations: list[Violation] = []
    for path in _iter_python_files():
        violations.extend(_check_file(path))

    if not violations:
        print("Repo policy check passed.")
        return

    for violation in violations:
        print(violation.render(), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
