from __future__ import annotations

import ast
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from hephaistos import armory, materials, memory, providers, rag, runtime, study

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = ROOT / "hephaistos"


def _imported_modules_after_import(module_name: str) -> set[str]:
    code = (
        "import importlib, json, sys\n"
        f"importlib.import_module({module_name!r})\n"
        "print(json.dumps(sorted(sys.modules)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    loaded: object = json.loads(result.stdout)
    assert isinstance(loaded, list)
    modules = cast("list[object]", loaded)
    return {item for item in modules if isinstance(item, str)}


def test_copyable_packages_do_not_load_app_or_chat_session() -> None:
    forbidden = {"hephaistos.app.tui", "hephaistos.app.workspace", "hephaistos.chat.session"}
    module_names = (
        "hephaistos.runtime",
        "hephaistos.providers",
        "hephaistos.materials",
        "hephaistos.rag",
        "hephaistos.memory",
        "hephaistos.armory",
        "hephaistos.study",
        "hephaistos.vocab",
    )
    with ThreadPoolExecutor(max_workers=len(module_names)) as pool:
        module_results = list(
            zip(module_names, pool.map(_imported_modules_after_import, module_names), strict=True)
        )
    for module_name, loaded in module_results:
        assert not forbidden.intersection(loaded), module_name


def test_import_linter_contracts_cover_portability_tiers() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    expected_contracts = (
        "runtime must stay below product workflows",
        "providers must stay below product workflows",
        "materials must not import app, chat, agent, or rag",
        "rag must not import agent, chat, or app",
        "memory must not import app, chat, or agent",
        "study must remain a pure controller layer",
    )
    for contract in expected_contracts:
        assert contract in pyproject


def test_public_reusable_package_apis_are_explicit() -> None:
    expected_exports = {
        runtime: {"ChatConfig", "Conversation", "stream_completion", "CircuitBreaker"},
        providers: {"ProviderConfig", "get_registry", "hydrate_provider_models", "resolve_key"},
        materials: {"MaterialFile", "iter_materials", "material_manifest"},
        rag: {"ArmoryIndex", "ScoredChunk", "retrieve", "build_turn_evidence"},
        memory: {"MemoryStore", "MemoryEntry", "load_memory", "save_memory"},
        study: {"StudyState", "StudyTurnPlan", "plan_turn", "apply_turn_result"},
        armory: {"ArmoryError", "initialize", "validate", "normalize_path"},
    }
    for module, names in expected_exports.items():
        exported = set(getattr(module, "__all__", ()))
        assert names.issubset(exported), module.__name__


def test_source_cli_is_a_thin_compatibility_adapter() -> None:
    source = PACKAGE_ROOT / "source" / "cli.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports: list[str] = []
    functions: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.append(node.func.id)

    assert functions == ["register"]
    assert "hephaistos.materials.cli" in imports
    assert "hephaistos.rag.index" not in imports
    assert calls == ["register_source_alias"]


def test_overworked_module_guardrails() -> None:
    max_lines = {
        "app/tui.py": 1510,
        "app/workspace.py": 520,
        "agent/dispatch.py": 575,
        "agent/tools.py": 750,
        "rag/retrieve.py": 910,
    }
    for relative, limit in max_lines.items():
        line_count = len((PACKAGE_ROOT / relative).read_text(encoding="utf-8").splitlines())
        assert line_count <= limit, f"{relative} has {line_count} lines, expected <= {limit}"
