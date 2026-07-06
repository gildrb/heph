"""Enforce repository-specific typing and import policies."""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
PACKAGE_IMPORT_ROOTS: Final[dict[Path, str]] = {
    REPO_ROOT / "packages" / "ai" / "src" / "ai": "ai",
    REPO_ROOT / "packages" / "extensions" / "src" / "extensions": "extensions",
    REPO_ROOT / "packages" / "heph" / "src" / "heph": "heph",
    REPO_ROOT / "packages" / "harness" / "src" / "harness": "harness",
    REPO_ROOT / "packages" / "interfaces" / "src" / "interfaces": "interfaces",
}
PACKAGE_TEST_ROOTS: Final[dict[Path, str]] = {
    REPO_ROOT / "packages" / "ai" / "test": "ai/test",
    REPO_ROOT / "packages" / "extensions" / "test": "extensions/test",
    REPO_ROOT / "packages" / "heph" / "test": "heph/test",
    REPO_ROOT / "packages" / "harness" / "test": "harness/test",
    REPO_ROOT / "packages" / "interfaces" / "test": "interfaces/test",
}
SCAN_ROOTS: Final[tuple[Path, ...]] = (
    *PACKAGE_IMPORT_ROOTS.keys(),
    *PACKAGE_TEST_ROOTS.keys(),
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
EXTENSION_CONTRACTS_FORBIDDEN_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "ai",
        "heph",
        "harness",
        "interfaces",
    }
)
EXTENSION_CONTRACTS_POLICY_MESSAGE: Final[str] = (
    "extension contracts must not import concrete product, harness, AI, or interface modules"
)
FOUNDATION_PACKAGE_FORBIDDEN_IMPORTS: Final[dict[str, frozenset[str]]] = {
    "ai": frozenset(
        {
            "extensions",
            "heph",
            "harness",
            "interfaces",
        }
    ),
    "extensions": frozenset(
        {
            "ai",
            "heph",
            "harness",
            "interfaces",
        }
    ),
}
FOUNDATION_PACKAGE_POLICY_MESSAGE: Final[str] = (
    "foundation packages must not import higher product, harness, AI, or interface modules"
)
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
    "harness/agent/tool_registry.py": frozenset(
        {
            "importlib.util.module_from_spec",
            "importlib.util.spec_from_file_location",
        }
    ),
    "harness/armory/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "heph/cli/main.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "harness/materials/cli.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "harness/rag/chunker.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "harness/rag/optional_backends.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
    "harness/test/test_rag_retrieve.py": frozenset(
        {
            "importlib.import_module",
        }
    ),
}
ALLOWED_DEFERRED_IMPORT_MODULES: Final[dict[str, frozenset[str]]] = {
    "harness/agent/__init__.py": frozenset(
        {
            "harness.agent.dispatch",
            "harness.agent.prompt",
            "harness.agent.tool_execution",
            "harness.agent.tools",
        }
    ),
    "ai/runtime/engine.py": frozenset(
        {
            "openai",
        }
    ),
    "interfaces/terminal/input.py": frozenset(
        {
            "harness.chat.session",
            "ai.runtime",
        }
    ),
    "interfaces/tui/__init__.py": frozenset(
        {
            "harness.chat.cli",
            "heph.commands",
            "interfaces.terminal.input",
        }
    ),
    "interfaces/tui/external_commands.py": frozenset(
        {
            "interfaces.tui.command_access",
            "interfaces.terminal.input",
        }
    ),
    "interfaces/tui/slash_command.py": frozenset(
        {
            "heph.commands",
        }
    ),
    "interfaces/tui/status.py": frozenset(
        {
            "ai.runtime",
        }
    ),
    "interfaces/tui/streaming.py": frozenset(
        {
            "harness.chat.automation",
            "ai.runtime",
        }
    ),
    "harness/rag/docling_worker.py": frozenset(
        {
            "docling.document_converter",
        }
    ),
}
PROMPT_RULE_SCAN_ROOTS: Final[tuple[str, ...]] = (
    "harness/agent/",
    "harness/chat/",
    "harness/documents/",
)
PROMPT_RULE_DUPLICATE_MESSAGE: Final[str] = (
    "duplicate model-facing prompt rule; define the rule once as a named policy constant"
)
HARDCODED_ANSWER_SCAN_ROOTS: Final[tuple[str, ...]] = (
    "harness/chat/",
    "harness/documents/",
    "interfaces/tui/",
)
HARDCODED_ANSWER_CALL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "_direct_reply_plan",
        "_DeterministicStudyReply",
        "no_armory_guidance_reply",
    }
)
HARDCODED_ANSWER_KEYWORDS: Final[frozenset[str]] = frozenset({"direct_reply", "reply"})
HARDCODED_ANSWER_TARGET_PARTS: Final[frozenset[str]] = frozenset(
    {
        "answer",
        "direct_reply",
        "guidance",
        "message",
        "question",
        "reply",
        "response",
    }
)
HARDCODED_ANSWER_FUNCTION_NAME_PARTS: Final[frozenset[str]] = frozenset(
    {
        "answer",
        "fallback",
        "guidance",
        "message",
        "question",
        "reply",
        "response",
    }
)
HARDCODED_REPLY_FUNCTION_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "_all_material_disabled_reply",
        "_empty_document_reply",
        "_empty_material_index_reply",
        "_fallback_assessment_message",
        "_generic_empty_document_reply",
        "_index_unavailable_reply",
        "_missing_indexed_material_reply",
        "_missing_source_span_message",
        "_no_matching_indexed_evidence_reply",
        "_overview_unavailable_reply",
        "_plain_empty_reply",
        "_source_qa_abstain_reply",
        "_source_qa_partial_progress_reply",
        "empty_armory_guidance",
        "tui_dependency_message",
        "_unindexable_material_reply",
        "_validation_guard_abstain_reply",
    }
)
HARDCODED_ANSWER_MESSAGE: Final[str] = (
    "hardcoded assistant answer for non-deterministic chat is forbidden; use a "
    "model-facing prompt or an allowlisted harness fallback"
)
SEMANTIC_DISPATCH_MESSAGE: Final[str] = (
    "semantic intent, follow-up, or source-relevance dispatch must not use regexes or "
    "phrase tables; use serialized turn state and model-resolved intent"
)
SEMANTIC_DISPATCH_SCAN_ROOTS: Final[tuple[str, ...]] = (
    "harness/chat/",
    "harness/rag/",
    "harness/documents/",
)
SEMANTIC_DISPATCH_TARGET_PARTS: Final[frozenset[str]] = frozenset(
    {
        "followup",
        "follow",
        "intent",
        "keyword",
        "phrase",
        "relevance",
        "semantic",
    }
)
QUARANTINED_SEMANTIC_DISPATCH_NAMES: Final[dict[str, frozenset[str]]] = {}
GENERATED_CACHE_MESSAGE: Final[str] = (
    "generated Python cache files must not live inside repository source roots"
)
PRIVATE_CORPUS_TERMS_FILES: Final[tuple[Path, ...]] = (
    REPO_ROOT / ".git" / "info" / "heph-private-corpus-terms",
    REPO_ROOT / ".heph-private-corpus-terms",
)
PRIVATE_CORPUS_TERMS_ENV_VAR: Final[str] = "HARNESS_PRIVATE_CORPUS_TERMS"
PRIVATE_CORPUS_TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".cfg",
        ".css",
        ".html",
        ".ini",
        ".js",
        ".json",
        ".md",
        ".py",
        ".sh",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)
PRIVATE_CORPUS_HARDCODING_MESSAGE: Final[str] = (
    "private corpus, university, course, lecturer, or local armory identifiers are "
    "forbidden outside tests; use generic fixtures, prompts, and semantic evidence handling"
)
PYTORCH_JIT_SCRIPT_SCAN_ROOTS: Final[tuple[str, ...]] = (
    "ai/",
    "extensions/",
    "heph/",
    "harness/",
    "interfaces/",
    "scripts/",
)
PYTORCH_JIT_SCRIPT_TEST_ROOTS: Final[tuple[str, ...]] = (
    "ai/test/",
    "extensions/test/",
    "heph/test/",
    "harness/test/",
    "interfaces/test/",
    "tests/",
)
PYTORCH_JIT_SCRIPT_POLICY_MESSAGE: Final[str] = (
    "direct `torch.jit.script` usage is forbidden while GHSA-rrmf-rvhw-rf47 is accepted; "
    "use eager PyTorch APIs or re-review the vulnerability waiver"
)


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


def _tracked_repo_paths() -> tuple[str, ...]:
    try:
        result = subprocess.run(
            ("git", "ls-files"),
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ()
    return tuple(line for line in result.stdout.splitlines() if line)


def _private_corpus_terms() -> tuple[str, ...]:
    terms = [
        line.strip()
        for line in os.environ.get(PRIVATE_CORPUS_TERMS_ENV_VAR, "").splitlines()
        if line.strip()
    ]
    for terms_file in PRIVATE_CORPUS_TERMS_FILES:
        if not terms_file.is_file():
            continue
        terms.extend(
            line.strip()
            for line in terms_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    return tuple(dict.fromkeys(terms))


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
    if alias.name == "harness.chat.orchestrator" and alias.asname is not None:
        return alias.asname, alias.name
    if alias.name == "torch":
        return alias.asname or "torch", "torch"
    if alias.name.startswith("torch.") and alias.asname is not None:
        return alias.asname, alias.name
    if alias.name == "importlib":
        return alias.asname or "importlib", "importlib"
    if not alias.name.startswith("importlib."):
        return None
    if alias.asname is None:
        return "importlib", "importlib"
    return alias.asname, alias.name


def _import_from_alias_binding(module: str | None, alias: ast.alias) -> tuple[str, str] | None:
    if module is None or alias.name == "*":
        return None
    if module == "torch" or module.startswith("torch."):
        return alias.asname or alias.name, f"{module}.{alias.name}"
    if not (module == "importlib" or module.startswith("importlib.")):
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


def _should_scan_for_pytorch_jit_script(rel_path: str) -> bool:
    return (
        rel_path.startswith(PYTORCH_JIT_SCRIPT_SCAN_ROOTS)
        and not rel_path.startswith(PYTORCH_JIT_SCRIPT_TEST_ROOTS)
        and not Path(rel_path).name.startswith("test_")
    )


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
        return self.rel_path.startswith(("ai/", "extensions/", "heph/", "harness/", "interfaces/"))

    def _is_product_script_file(self) -> bool:
        return self.rel_path.startswith("scripts/")

    def _check_private_orchestrator_import(self, node: ast.AST, module: str | None) -> None:
        if not self._is_product_script_file() or module != "harness.chat.orchestrator":
            return
        if not isinstance(node, ast.ImportFrom):
            return
        for alias in node.names:
            if alias.name.startswith("_"):
                self._add(
                    node,
                    (
                        "product scripts must not import private names from "
                        "`chat.orchestrator`; use stable chat modules"
                    ),
                )

    def _check_private_orchestrator_attribute(self, node: ast.AST, dotted: str | None) -> None:
        if not self._is_product_script_file() or dotted is None:
            return
        resolved = self._resolve_import_alias(dotted)
        if resolved is None:
            return
        if resolved.startswith("harness.chat.orchestrator._"):
            self._add(
                node,
                (
                    "product scripts must not access private names from "
                    "`chat.orchestrator`; use stable chat modules"
                ),
            )

    def _check_pytorch_jit_script_reference(self, node: ast.AST, dotted: str | None) -> None:
        if not _should_scan_for_pytorch_jit_script(self.rel_path):
            return
        if self._resolve_import_alias(dotted) == "torch.jit.script":
            self._add(node, PYTORCH_JIT_SCRIPT_POLICY_MESSAGE)

    def _check_pytorch_jit_script_getattr(self, node: ast.Call) -> None:
        if not _should_scan_for_pytorch_jit_script(self.rel_path):
            return
        if self._resolve_import_alias(_dotted_name(node.func)) != "getattr" or len(node.args) < 2:
            return
        target = self._resolve_import_alias(_dotted_name(node.args[0]))
        attr = node.args[1]
        if target == "torch.jit" and isinstance(attr, ast.Constant) and attr.value == "script":
            self._add(node, PYTORCH_JIT_SCRIPT_POLICY_MESSAGE)

    def _check_runtime_benchmark_import(self, node: ast.AST, module: str) -> None:
        if not self._is_product_runtime_file():
            return
        if _is_benchmark_only_module(module):
            self._add(
                node,
                f"product runtime modules must not import benchmark-only module `{module}`",
            )

    def _check_extension_contract_import(self, node: ast.AST, module: str | None) -> None:
        if self.rel_path != "extensions/contracts.py" or module is None:
            return
        top_level = module.lstrip(".").split(".", maxsplit=1)[0]
        if top_level in EXTENSION_CONTRACTS_FORBIDDEN_IMPORTS:
            self._add(node, EXTENSION_CONTRACTS_POLICY_MESSAGE)

    def _check_foundation_package_import(self, node: ast.AST, module: str | None) -> None:
        if module is None:
            return
        package = self.rel_path.split("/", maxsplit=1)[0]
        forbidden = FOUNDATION_PACKAGE_FORBIDDEN_IMPORTS.get(package)
        if forbidden is None:
            return
        top_level = module.lstrip(".").split(".", maxsplit=1)[0]
        if top_level in forbidden:
            self._add(node, FOUNDATION_PACKAGE_POLICY_MESSAGE)

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
            self._check_extension_contract_import(node, module)
            self._check_foundation_package_import(node, module)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        if node.level == 0:
            for alias in node.names:
                binding = _import_from_alias_binding(node.module, alias)
                if binding is not None:
                    local_name, canonical_name = binding
                    self._import_aliases[local_name] = canonical_name
                if node.module == "harness.chat" and alias.name == "orchestrator":
                    self._import_aliases[alias.asname or alias.name] = "harness.chat.orchestrator"
        if not self._import_context_is_allowed() and not self._deferred_import_is_allowed(
            [module]
        ):
            self._add(node, "deferred imports are forbidden outside module scope")
        if node.level == 0 and node.module is not None:
            self._check_runtime_benchmark_import(node, node.module)
        self._check_extension_contract_import(node, node.module)
        self._check_foundation_package_import(node, node.module)
        if node.module in {"typing", "typing_extensions"}:
            for alias in node.names:
                if alias.name == "Any":
                    self._add(node, "explicit Any is forbidden")
        self._check_private_orchestrator_import(node, node.module)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "Any":
            self._add(node, "explicit Any is forbidden")
        self._check_pytorch_jit_script_reference(node, node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        dotted = _dotted_name(node)
        if dotted in {"typing.Any", "typing_extensions.Any"}:
            self._add(node, "explicit Any is forbidden")
        self._check_private_orchestrator_attribute(node, dotted)
        self._check_pytorch_jit_script_reference(node, dotted)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self._check_runtime_benchmark_path(node, node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        dotted = self._resolve_import_alias(_dotted_name(node.func))
        self._check_pytorch_jit_script_getattr(node)
        if dotted in DYNAMIC_IMPORT_CALL_NAMES:
            allowed = ALLOWED_DYNAMIC_IMPORT_CALLS.get(self.rel_path, frozenset())
            if dotted not in allowed:
                self._add(node, f"dynamic import helper `{dotted}` is forbidden here")
            module = _literal_dynamic_import_target(node, dotted)
            if module is not None:
                self._check_runtime_benchmark_import(node, module)
                self._check_foundation_package_import(node, module)

        if dotted in {"cast", "typing.cast"} and node.args:
            first_arg = node.args[0]
            if (
                isinstance(first_arg, ast.Constant)
                and isinstance(first_arg.value, str)
                and "Any" in first_arg.value
            ):
                self._add(node, "cast strings may not reference Any")

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        target_names = tuple(
            name for target in node.targets for name in _semantic_dispatch_target_names(target)
        )
        self._check_semantic_dispatch_assignment(node.value, target_names)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target_names = tuple(_semantic_dispatch_target_names(node.target))
        if node.value is not None:
            self._check_semantic_dispatch_assignment(node.value, target_names)
        self.generic_visit(node)

    def _check_semantic_dispatch_assignment(
        self,
        value: ast.AST,
        target_names: Sequence[str],
    ) -> None:
        if not self.rel_path.startswith(SEMANTIC_DISPATCH_SCAN_ROOTS):
            return
        for target_name in target_names:
            if _semantic_dispatch_target_is_quarantined(self.rel_path, target_name):
                continue
            if _is_semantic_dispatch_regex(target_name, value) or (
                _is_semantic_dispatch_phrase_table_name(target_name)
                and _is_string_literal_container(value)
            ):
                self._add(value, SEMANTIC_DISPATCH_MESSAGE)


@dataclass(frozen=True)
class PromptRuleLiteral:
    text: str
    path: str
    line: int
    column: int


@dataclass(frozen=True)
class HardcodedAnswerLiteral:
    text: str
    path: str
    line: int
    column: int


def _is_benchmark_only_module(module: str) -> bool:
    top_level = module.split(".", maxsplit=1)[0]
    return top_level in BENCHMARK_ONLY_TOP_LEVEL_MODULES


def _is_generated_or_benchmark_artifact_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return any(marker in normalized for marker in RUNTIME_BENCHMARK_PATH_MARKERS)


def _semantic_dispatch_target_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    if isinstance(node, ast.Tuple | ast.List):
        return tuple(
            name for element in node.elts for name in _semantic_dispatch_target_names(element)
        )
    return ()


def _semantic_dispatch_target_is_quarantined(rel_path: str, target_name: str) -> bool:
    return target_name in QUARANTINED_SEMANTIC_DISPATCH_NAMES.get(rel_path, frozenset())


def _is_semantic_dispatch_regex(target_name: str, value: ast.AST) -> bool:
    if not _is_semantic_dispatch_phrase_table_name(target_name):
        return False
    return (
        isinstance(value, ast.Call)
        and _dotted_name(value.func) == "re.compile"
        and bool(value.args)
    )


def _is_semantic_dispatch_phrase_table_name(target_name: str) -> bool:
    normalized = target_name.strip("_").casefold()
    parts = frozenset(part for part in normalized.split("_") if part)
    return bool(parts & SEMANTIC_DISPATCH_TARGET_PARTS)


def _is_string_literal_container(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and _dotted_name(node.func) in {
        "frozenset",
        "list",
        "set",
        "tuple",
    }:
        return any(_is_string_literal_container(arg) for arg in node.args)
    return isinstance(node, ast.Dict | ast.Set | ast.List | ast.Tuple) and any(
        isinstance(child, ast.Constant) and isinstance(child.value, str)
        for child in ast.walk(node)
    )


def _check_source(source: str, rel_path: str, *, filename: str | None = None) -> list[Violation]:
    tree = ast.parse(source, filename=filename or rel_path)
    visitor = PolicyVisitor(rel_path)
    visitor.visit(tree)

    violations = visitor.violations
    violations.extend(
        _hardcoded_answer_violations(
            _hardcoded_answer_literals(source, rel_path, filename=filename),
        )
    )
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


def _prompt_rule_literals(
    source: str,
    rel_path: str,
    *,
    filename: str | None = None,
) -> list[PromptRuleLiteral]:
    if not rel_path.startswith(PROMPT_RULE_SCAN_ROOTS):
        return []
    tree = ast.parse(source, filename=filename or rel_path)
    parent_by_child = {
        child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
    }
    literals: list[PromptRuleLiteral] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if isinstance(parent_by_child.get(node), ast.JoinedStr):
            continue
        for line in node.value.splitlines():
            normalized = _normalize_prompt_rule_line(line)
            if normalized is None:
                continue
            literals.append(
                PromptRuleLiteral(
                    text=normalized,
                    path=rel_path,
                    line=getattr(node, "lineno", 1),
                    column=getattr(node, "col_offset", 0) + 1,
                )
            )
    return literals


def _normalize_prompt_rule_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("- ") or len(stripped) < 32:
        return None
    if "{" in stripped or "}" in stripped:
        return None
    return " ".join(stripped.casefold().split())


def _check_file(path: Path) -> list[Violation]:
    rel_path = _repo_relative_path(path)
    source = path.read_text(encoding="utf-8")
    return _check_source(source, rel_path, filename=str(path))


def _check_duplicate_prompt_rules() -> list[Violation]:
    literals: list[PromptRuleLiteral] = []
    for path in _iter_python_files():
        rel_path = _repo_relative_path(path)
        source = path.read_text(encoding="utf-8")
        literals.extend(_prompt_rule_literals(source, rel_path, filename=str(path)))

    return _duplicate_prompt_rule_violations(literals)


def _repo_relative_path(path: Path) -> str:
    for package_root, import_root in PACKAGE_IMPORT_ROOTS.items():
        if path.is_relative_to(package_root):
            return f"{import_root}/{path.relative_to(package_root).as_posix()}"
    for package_root, logical_root in PACKAGE_TEST_ROOTS.items():
        if path.is_relative_to(package_root):
            return f"{logical_root}/{path.relative_to(package_root).as_posix()}"
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        root_parts = REPO_ROOT.parts
        path_parts = path.parts
        if len(path_parts) >= len(root_parts) and tuple(
            part.casefold() for part in path_parts[: len(root_parts)]
        ) == tuple(part.casefold() for part in root_parts):
            return Path(*path_parts[len(root_parts) :]).as_posix()
        raise


def _hardcoded_answer_literals(
    source: str,
    rel_path: str,
    *,
    filename: str | None = None,
) -> list[HardcodedAnswerLiteral]:
    if not rel_path.startswith(HARDCODED_ANSWER_SCAN_ROOTS):
        return []
    tree = ast.parse(source, filename=filename or rel_path)
    literals: list[HardcodedAnswerLiteral] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            literals.extend(_hardcoded_answer_literals_from_call(node, rel_path))
        elif isinstance(node, ast.Assign):
            literals.extend(_hardcoded_answer_literals_from_assignment(node, rel_path))
        elif isinstance(node, ast.AnnAssign):
            literals.extend(_hardcoded_answer_literals_from_annotated_assignment(node, rel_path))
        elif isinstance(node, ast.FunctionDef):
            literals.extend(_hardcoded_answer_literals_from_reply_function(node, rel_path))
    return literals


def _hardcoded_answer_literals_from_call(
    node: ast.Call,
    rel_path: str,
) -> list[HardcodedAnswerLiteral]:
    dotted = _dotted_name(node.func)
    literals: list[HardcodedAnswerLiteral] = []
    if dotted is not None and dotted.split(".")[-1] in HARDCODED_ANSWER_CALL_NAMES:
        if node.args:
            literal = _string_literal_value(node.args[0])
            if literal is not None:
                literals.append(_hardcoded_answer_literal(literal, rel_path, node.args[0]))
        for keyword in node.keywords:
            if keyword.arg in HARDCODED_ANSWER_KEYWORDS:
                literal = _string_literal_value(keyword.value)
                if literal is not None:
                    literals.append(_hardcoded_answer_literal(literal, rel_path, keyword.value))

    for keyword in node.keywords:
        if keyword.arg not in HARDCODED_ANSWER_KEYWORDS:
            continue
        literal = _string_literal_value(keyword.value)
        if literal is not None:
            literals.append(_hardcoded_answer_literal(literal, rel_path, keyword.value))
    return literals


def _hardcoded_answer_literals_from_assignment(
    node: ast.Assign,
    rel_path: str,
) -> list[HardcodedAnswerLiteral]:
    if not any(_hardcoded_answer_target_name(target) is not None for target in node.targets):
        return []
    literal = _string_literal_value(node.value)
    if literal is None:
        return []
    return [_hardcoded_answer_literal(literal, rel_path, node.value)]


def _hardcoded_answer_literals_from_annotated_assignment(
    node: ast.AnnAssign,
    rel_path: str,
) -> list[HardcodedAnswerLiteral]:
    if node.value is None or _hardcoded_answer_target_name(node.target) is None:
        return []
    literal = _string_literal_value(node.value)
    if literal is None:
        return []
    return [_hardcoded_answer_literal(literal, rel_path, node.value)]


def _hardcoded_answer_target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        name = node.id
    elif isinstance(node, ast.Attribute):
        name = node.attr
    elif isinstance(node, ast.Subscript):
        name = _literal_subscript_key(node)
        if name is None:
            return None
    else:
        return None
    parts = frozenset(part for part in name.strip("_").split("_") if part)
    if name == "direct_reply" or parts & HARDCODED_ANSWER_TARGET_PARTS:
        return name
    return None


def _literal_subscript_key(node: ast.Subscript) -> str | None:
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return node.slice.value
    return None


def _hardcoded_answer_literals_from_reply_function(
    node: ast.FunctionDef,
    rel_path: str,
) -> list[HardcodedAnswerLiteral]:
    if not _is_guarded_reply_function(node.name):
        return []
    literals: list[HardcodedAnswerLiteral] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Return) or child.value is None:
            continue
        literal = _string_literal_value(child.value)
        if literal is not None:
            literals.append(_hardcoded_answer_literal(literal, rel_path, child.value))
    return literals


def _is_guarded_reply_function(name: str) -> bool:
    if name in HARDCODED_REPLY_FUNCTION_ALLOWLIST:
        return False
    parts = frozenset(part for part in name.strip("_").split("_") if part)
    return bool(parts & HARDCODED_ANSWER_FUNCTION_NAME_PARTS)


def _string_literal_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{}")
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_literal_value(node.left)
        right = _string_literal_value(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.Call):
        return _joined_string_literal_value(node)
    return None


def _joined_string_literal_value(node: ast.Call) -> str | None:
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "join":
        return None
    separator = _string_literal_value(node.func.value)
    if separator is None or len(node.args) != 1:
        return None
    values_node = node.args[0]
    if not isinstance(values_node, ast.List | ast.Tuple):
        return None
    parts: list[str] = []
    for element in values_node.elts:
        part = _string_literal_value(element)
        if part is None:
            return None
        parts.append(part)
    return separator.join(parts)


def _hardcoded_answer_literal(
    text: str,
    rel_path: str,
    node: ast.AST,
) -> HardcodedAnswerLiteral:
    return HardcodedAnswerLiteral(
        text=" ".join(text.split()),
        path=rel_path,
        line=getattr(node, "lineno", 1),
        column=getattr(node, "col_offset", 0) + 1,
    )


def _check_generated_caches(paths: Sequence[str] | None = None) -> list[Violation]:
    return [
        Violation(
            path=path,
            line=1,
            column=1,
            message=GENERATED_CACHE_MESSAGE,
        )
        for path in (paths if paths is not None else _tracked_repo_paths())
        if _is_generated_python_cache_path(path)
    ]


def _is_generated_python_cache_path(path: str) -> bool:
    parts = Path(path).parts
    return "__pycache__" in parts or path.endswith((".pyc", ".pyo"))


def _private_corpus_identifier_violations(
    paths: Sequence[str] | None = None,
    *,
    terms: Sequence[str] | None = None,
) -> list[Violation]:
    blocked_terms = tuple(terms) if terms is not None else _private_corpus_terms()
    if not blocked_terms:
        return []
    violations: list[Violation] = []
    for rel_path in paths if paths is not None else _tracked_repo_paths():
        if _skip_private_corpus_scan(rel_path):
            continue
        path = REPO_ROOT / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        violations.extend(_private_corpus_identifier_hits(rel_path, text, blocked_terms))
    return violations


def _skip_private_corpus_scan(path: str) -> bool:
    return (
        path.startswith("tests/") or Path(path).suffix.lower() not in PRIVATE_CORPUS_TEXT_SUFFIXES
    )


def _private_corpus_identifier_hits(
    rel_path: str,
    text: str,
    terms: Sequence[str],
) -> list[Violation]:
    violations: list[Violation] = []
    for term in terms:
        if not term:
            continue
        search_from = 0
        while True:
            index = text.casefold().find(term.casefold(), search_from)
            if index < 0:
                break
            violations.append(
                Violation(
                    path=rel_path,
                    line=text.count("\n", 0, index) + 1,
                    column=index - text.rfind("\n", 0, index),
                    message=PRIVATE_CORPUS_HARDCODING_MESSAGE,
                )
            )
            search_from = index + len(term)
    return violations


def _hardcoded_answer_violations(
    literals: Sequence[HardcodedAnswerLiteral],
) -> list[Violation]:
    violations: list[Violation] = []
    for literal in literals:
        if _is_allowed_hardcoded_answer(literal.text):
            continue
        violations.append(
            Violation(
                path=literal.path,
                line=literal.line,
                column=literal.column,
                message=HARDCODED_ANSWER_MESSAGE,
            )
        )
    return violations


def _is_allowed_hardcoded_answer(text: str) -> bool:
    return not any(char.isalpha() for char in text)


def _duplicate_prompt_rule_violations(literals: Sequence[PromptRuleLiteral]) -> list[Violation]:
    by_text: dict[str, list[PromptRuleLiteral]] = {}
    for literal in literals:
        by_text.setdefault(literal.text, []).append(literal)
    violations: list[Violation] = []
    for duplicates in by_text.values():
        if len(duplicates) < 2:
            continue
        for duplicate in duplicates[1:]:
            first = duplicates[0]
            violations.append(
                Violation(
                    path=duplicate.path,
                    line=duplicate.line,
                    column=duplicate.column,
                    message=(
                        f"{PROMPT_RULE_DUPLICATE_MESSAGE} "
                        f"(first seen at {first.path}:{first.line})"
                    ),
                )
            )
    return violations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enforce explicit Any, deferred-import, and type-suppression policies.",
    )
    parser.parse_args()

    violations: list[Violation] = []
    for path in _iter_python_files():
        violations.extend(_check_file(path))
    violations.extend(_check_duplicate_prompt_rules())
    violations.extend(_check_generated_caches())
    violations.extend(_private_corpus_identifier_violations())

    if not violations:
        print("Repo policy check passed.")
        return

    for violation in violations:
        print(violation.render(), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
