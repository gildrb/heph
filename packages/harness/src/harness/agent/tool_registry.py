"""Tool registry and trusted armory plugin loading."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path

from harness.agent.tool_schema import ToolHandlerResult, ToolSchema, ToolSpec


class ToolRegistry:
    def __init__(self, parent: ToolRegistry | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._parent = parent
        self._generation = 0
        self._schemas_cache: list[ToolSchema] | None = None
        self._schemas_cache_key: tuple[int, int] | None = None

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec
        self._generation += 1

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._generation += 1

    def get(self, name: str) -> ToolSpec | None:
        spec = self._tools.get(name)
        if spec is not None:
            return spec
        if self._parent is not None:
            return self._parent.get(name)
        return None

    def get_handler(self, name: str) -> Callable[..., ToolHandlerResult] | None:
        spec = self.get(name)
        return spec.handler if spec else None

    def is_control_tool(self, name: str) -> bool:
        spec = self.get(name)
        return spec.kind == "control" if spec is not None else False

    def _visible_generation(self) -> int:
        parent_generation = self._parent._visible_generation() if self._parent is not None else 0
        return self._generation + parent_generation

    @property
    def schemas(self) -> list[ToolSchema]:
        parent_generation = self._parent._visible_generation() if self._parent is not None else 0
        cache_key = (self._generation, parent_generation)
        if self._schemas_cache is not None and self._schemas_cache_key == cache_key:
            return list(self._schemas_cache)

        result = self._visible_schemas()
        self._schemas_cache = result
        self._schemas_cache_key = cache_key
        return list(result)

    def _visible_schemas(self) -> list[ToolSchema]:
        seen: set[str] = set()
        result: list[ToolSchema] = []
        for spec in self._tools.values():
            seen.add(spec.name)
            result.append(spec.schema)
        if self._parent is not None:
            for schema in self._parent.schemas:
                name = schema["function"]["name"]
                if name not in seen:
                    seen.add(name)
                    result.append(schema)
        return result

    @property
    def specs(self) -> list[ToolSpec]:
        seen: set[str] = set()
        result: list[ToolSpec] = []
        for spec in self._tools.values():
            seen.add(spec.name)
            result.append(spec)
        if self._parent is not None:
            for spec in self._parent.specs:
                if spec.name not in seen:
                    seen.add(spec.name)
                    result.append(spec)
        return result

    @property
    def tool_names(self) -> list[str]:
        return [s["function"]["name"] for s in self.schemas]

    def child(self) -> ToolRegistry:
        return ToolRegistry(parent=self)

    def load_plugins(self, tools_dir: Path) -> int:
        if not tools_dir.is_dir():
            return 0
        tools_dir = tools_dir.resolve()
        loaded = 0
        for py_file in sorted(tools_dir.glob("*.py")):
            loaded += int(_load_plugin_file(self, py_file, tools_dir))
        return loaded


def _load_plugin_file(registry: ToolRegistry, py_file: Path, tools_dir: Path) -> bool:
    if py_file.name.startswith("_"):
        return False
    if not py_file.resolve().is_relative_to(tools_dir):
        return False
    module_name = f"harness_armory_plugin_{py_file.stem}"
    try:
        return _register_plugin_module(registry, module_name, py_file)
    except Exception as exc:
        print(f"warning: failed to load tool plugin {py_file.name}: {exc}", file=sys.stderr)
        return False


def _register_plugin_module(registry: ToolRegistry, module_name: str, py_file: Path) -> bool:
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register_fn = getattr(module, "register", None)
    if not callable(register_fn):
        return False
    register_fn(registry)
    return True
