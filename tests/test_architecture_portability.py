from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from hephaion import armory, materials, memory, providers, rag, runtime, study

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = ROOT / "hephaion"


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


def test_copyable_packages_do_not_load_adapters_or_chat_session() -> None:
    forbidden = {
        "hephaion.terminal.input",
        "hephaion.tui",
        "hephaion.chat.session",
    }
    module_names = (
        "hephaion.runtime",
        "hephaion.providers",
        "hephaion.materials",
        "hephaion.rag",
        "hephaion.memory",
        "hephaion.armory",
        "hephaion.study",
        "hephaion.vocab",
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
        "materials must not import adapters, chat, agent, or rag",
        "rag must not import agent, chat, or adapters",
        "memory must not import adapters, chat, or agent",
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
        study: {"LearningState", "LearningTurnPlan", "plan_turn", "apply_turn_result"},
        armory: {"ArmoryError", "initialize", "validate", "normalize_path"},
    }
    for module, names in expected_exports.items():
        exported = set(getattr(module, "__all__", ()))
        assert names.issubset(exported), module.__name__


def test_overworked_module_guardrails() -> None:
    max_lines = {
        "tui/__init__.py": 1250,
        "terminal/input.py": 240,
        "agent/dispatch.py": 575,
        "agent/tools.py": 950,
        "rag/retrieve.py": 910,
    }
    for relative, limit in max_lines.items():
        line_count = len((PACKAGE_ROOT / relative).read_text(encoding="utf-8").splitlines())
        assert line_count <= limit, f"{relative} has {line_count} lines, expected <= {limit}"
