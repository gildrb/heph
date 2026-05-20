"""Enforce repository-specific typing and import policies."""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
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
TYPE_IGNORE_MARKER: Final[str] = "".join(("# type:", " ignore"))
PRIVATE_USAGE_IGNORE_CODE: Final[str] = "".join(("report", "PrivateUsage"))
TY_IGNORE_MARKER: Final[str] = "".join(("# ty:", "ignore"))
LEGACY_TY_IGNORE_MARKER: Final[str] = "".join(("# ty:", " ignore"))
TYPE_IGNORE_POLICY_MESSAGE: Final[str] = (
    f"`{TYPE_IGNORE_MARKER}` is forbidden; use `{TY_IGNORE_MARKER}[code]` or `# noqa: RULE`"
)
TY_IGNORE_POLICY_MESSAGE: Final[str] = (
    f"ty suppressions must use `{TY_IGNORE_MARKER}[exact-diagnostic]`"
)
BENCHMARK_ONLY_TOP_LEVEL_MODULES: Final[frozenset[str]] = frozenset({"benchmarks", "scripts"})
RUNTIME_BENCHMARK_PATH_MARKERS: Final[tuple[str, ...]] = (
    ".artifacts",
    ".artifacts/",
    "/.artifacts/",
    "benchmarks/",
)
DYNAMIC_IMPORT_CALL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__import__",
        "importlib.import_module",
        "importlib.util.module_from_spec",
        "importlib.util.spec_from_file_location",
    }
)
DYNAMIC_IMPORT_MODULE_TARGET_CALLS: Final[frozenset[str]] = frozenset(
    {
        "__import__",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
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
    "hephaistos/agent/tools.py": frozenset(
        {
            "importlib.util.module_from_spec",
            "importlib.util.spec_from_file_location",
        }
    ),
    "hephaistos/parameters/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/armory/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/cli/main.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/materials/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/rag/chunker.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "hephaistos/rag/optional_backends.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "tests/test_rag_retrieve.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
}
ALLOWED_DEFERRED_IMPORT_MODULES: Final[dict[str, frozenset[str]]] = {
    "hephaistos/agent/__init__.py": frozenset(
        {
            "hephaistos.agent.dispatch",
            "hephaistos.agent.prompt",
            "hephaistos.agent.tool_execution",
            "hephaistos.agent.tools",
        }
    ),
    "hephaistos/chat/session.py": frozenset(
        {
            "hephaistos.chat.events",
            "hephaistos.chat.orchestrator",
        }
    ),
    "hephaistos/runtime/engine.py": frozenset(
        {
            "openai",
        }
    ),
    "hephaistos/terminal/input.py": frozenset(
        {
            "hephaistos.chat.session",
            "hephaistos.runtime",
        }
    ),
    "hephaistos/tui/__init__.py": frozenset(
        {
            "hephaistos.chat.cli",
            "hephaistos.commands",
            "hephaistos.terminal.input",
        }
    ),
    "hephaistos/tui/slash_command.py": frozenset(
        {
            "hephaistos.commands",
        }
    ),
    "hephaistos/tui/status.py": frozenset(
        {
            "hephaistos.runtime",
        }
    ),
    "hephaistos/tui/streaming.py": frozenset(
        {
            "hephaistos.chat.automation",
            "hephaistos.runtime",
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


def _import_alias_binding(alias: ast.alias) -> tuple[str, str] | None:
    if alias.name == "importlib":
        return alias.asname or "importlib", "importlib"
    if not alias.name.startswith("importlib."):
        return None
    if alias.asname is None:
        return "importlib", "importlib"
    return alias.asname, alias.name


def _import_from_alias_binding(module: str | None, alias: ast.alias) -> tuple[str, str] | None:
    if (
        module is None
        or alias.name == "*"
        or not (module == "importlib" or module.startswith("importlib."))
    ):
        return None
    local_name = alias.asname or alias.name
    return local_name, f"{module}.{alias.name}"


def _is_type_checking_guard(test: ast.expr) -> bool:
    dotted = _dotted_name(test)
    return dotted in {"TYPE_CHECKING", "typing.TYPE_CHECKING"}


def _module_is_allowed(module: str | None, allowed: frozenset[str]) -> bool:
    if module is None:
        return False
    return any(module == item or module.startswith(f"{item}.") for item in allowed)


def _literal_string_keyword(node: ast.Call, keyword_name: str) -> str | None:
    for keyword in node.keywords:
        if keyword.arg != keyword_name:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def _literal_string_argument(node: ast.Call, keyword_name: str) -> str | None:
    if node.args:
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value
    return _literal_string_keyword(node, keyword_name)


def _literal_dynamic_import_target(node: ast.Call, dotted: str | None) -> str | None:
    if dotted not in DYNAMIC_IMPORT_MODULE_TARGET_CALLS:
        return None
    module = _literal_string_argument(node, "name")
    if module is None:
        return None
    if dotted == "importlib.import_module" and module.startswith("."):
        package = _literal_string_keyword(node, "package")
        if package is not None:
            stripped_module = module.lstrip(".")
            if stripped_module:
                return f"{package}.{stripped_module}"
            return package
    return module


class PolicyVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[Violation] = []
        self._stack: list[ast.AST] = []
        self._import_aliases: dict[str, str] = {}

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

    def _is_product_runtime_file(self) -> bool:
        return self.rel_path.startswith("hephaistos/")

    def _check_runtime_benchmark_import(self, node: ast.AST, module: str) -> None:
        if not self._is_product_runtime_file():
            return
        if _is_benchmark_only_module(module):
            self._add(
                node,
                f"product runtime modules must not import benchmark-only module `{module}`",
            )

    def _check_runtime_benchmark_path(self, node: ast.AST, value: str) -> None:
        if not self._is_product_runtime_file():
            return
        if _is_generated_or_benchmark_artifact_path(value):
            self._add(
                node,
                "product runtime modules must not reference generated benchmark artifact paths",
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

    def _deferred_import_is_allowed(self, modules: Sequence[str | None]) -> bool:
        allowed = ALLOWED_DEFERRED_IMPORT_MODULES.get(self.rel_path, frozenset())
        return bool(allowed) and all(_module_is_allowed(module, allowed) for module in modules)

    def _resolve_import_alias(self, dotted: str | None) -> str | None:
        if dotted is None:
            return None
        head, separator, tail = dotted.partition(".")
        alias_target = self._import_aliases.get(head)
        if alias_target is None:
            return dotted
        if separator:
            return f"{alias_target}.{tail}"
        return alias_target

    def visit_Import(self, node: ast.Import) -> None:
        modules = [alias.name for alias in node.names]
        for alias in node.names:
            binding = _import_alias_binding(alias)
            if binding is not None:
                local_name, canonical_name = binding
                self._import_aliases[local_name] = canonical_name
        if not self._import_context_is_allowed() and not self._deferred_import_is_allowed(modules):
            self._add(node, "deferred imports are forbidden outside module scope")
        for module in modules:
            self._check_runtime_benchmark_import(node, module)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        if node.level == 0:
            for alias in node.names:
                binding = _import_from_alias_binding(node.module, alias)
                if binding is not None:
                    local_name, canonical_name = binding
                    self._import_aliases[local_name] = canonical_name
        if not self._import_context_is_allowed() and not self._deferred_import_is_allowed(
            [module]
        ):
            self._add(node, "deferred imports are forbidden outside module scope")
        if node.level == 0 and node.module is not None:
            self._check_runtime_benchmark_import(node, node.module)
        if node.module in {"typing", "typing_extensions"}:
            for alias in node.names:
                if alias.name == "Any":
                    self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "Any":
            self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        dotted = _dotted_name(node)
        if dotted in {"typing.Any", "typing_extensions.Any"}:
            self._add(node, "explicit Any is forbidden")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self._check_runtime_benchmark_path(node, node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        dotted = self._resolve_import_alias(_dotted_name(node.func))
        if dotted in DYNAMIC_IMPORT_CALL_NAMES:
            allowed = ALLOWED_DYNAMIC_IMPORT_CALLS.get(self.rel_path, frozenset())
            if dotted not in allowed:
                self._add(node, f"dynamic import helper `{dotted}` is forbidden here")
            module = _literal_dynamic_import_target(node, dotted)
            if module is not None:
                self._check_runtime_benchmark_import(node, module)

        if dotted in {"cast", "typing.cast"} and node.args:
            first_arg = node.args[0]
            if (
                isinstance(first_arg, ast.Constant)
                and isinstance(first_arg.value, str)
                and "Any" in first_arg.value
            ):
                self._add(node, "cast strings may not reference Any")

        self.generic_visit(node)


def _is_benchmark_only_module(module: str) -> bool:
    top_level = module.split(".", maxsplit=1)[0]
    return top_level in BENCHMARK_ONLY_TOP_LEVEL_MODULES


def _is_generated_or_benchmark_artifact_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return any(marker in normalized for marker in RUNTIME_BENCHMARK_PATH_MARKERS)


def _check_source(source: str, rel_path: str, *, filename: str | None = None) -> list[Violation]:
    tree = ast.parse(source, filename=filename or rel_path)
    visitor = PolicyVisitor(rel_path)
    visitor.visit(tree)

    violations = visitor.violations
    for line_number, line in enumerate(source.splitlines(), start=1):
        if TYPE_IGNORE_MARKER in line:
            message = TYPE_IGNORE_POLICY_MESSAGE
            if PRIVATE_USAGE_IGNORE_CODE in line:
                message = "private-usage checks must not be suppressed with broad type ignores"
            violations.append(
                Violation(
                    path=rel_path,
                    line=line_number,
                    column=line.index(TYPE_IGNORE_MARKER) + 1,
                    message=message,
                )
            )

        if LEGACY_TY_IGNORE_MARKER in line:
            violations.append(
                Violation(
                    path=rel_path,
                    line=line_number,
                    column=line.index(LEGACY_TY_IGNORE_MARKER) + 1,
                    message=TY_IGNORE_POLICY_MESSAGE,
                )
            )
            continue

        if TY_IGNORE_MARKER not in line:
            continue
        marker_column = line.index(TY_IGNORE_MARKER) + 1
        code_start = line.find("[", marker_column - 1)
        code_end = line.find("]", marker_column - 1)
        if code_start == -1 or code_end == -1 or code_end <= code_start + 1:
            violations.append(
                Violation(
                    path=rel_path,
                    line=line_number,
                    column=marker_column,
                    message="ty suppressions must include an exact diagnostic code",
                )
            )
    return violations


def _check_file(path: Path) -> list[Violation]:
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    return _check_source(source, rel_path, filename=str(path))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enforce explicit Any, deferred-import, and type-suppression policies.",
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
