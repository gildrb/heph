"""Tests for the ToolRegistry, ToolSpec, and armory plugin loading."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from hephaistos.harness.dispatch import execute_tool_calls
from hephaistos.harness.tools import (
    TOOL_SCHEMAS,
    ToolRegistry,
    ToolSpec,
    default_registry,
    get_handler,
)


def _default_handler(**_kw: object) -> str:
    return ""


def _make_spec(
    name: str,
    handler: Callable[..., str] | None = None,
    description: str = "",
) -> ToolSpec:
    """Create a minimal ToolSpec for testing."""
    return ToolSpec(
        schema={
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        handler=handler if handler is not None else _default_handler,
    )


# ---------------------------------------------------------------------------
# ToolSpec
# ---------------------------------------------------------------------------


class TestToolSpec:
    def test_name_extraction(self) -> None:
        spec = _make_spec("my_tool")
        assert spec.name == "my_tool"


# ---------------------------------------------------------------------------
# ToolRegistry basics
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_default_registry_has_builtins(self) -> None:
        assert len(default_registry.schemas) >= 8
        assert "bash" in default_registry.tool_names
        assert "read_file" in default_registry.tool_names

    def test_register_and_get(self) -> None:
        reg = ToolRegistry()
        spec = _make_spec("custom", handler=lambda **kw: "custom result")  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        reg.register(spec)
        assert reg.get("custom") is spec
        assert reg.get_handler("custom") is spec.handler
        assert reg.get("nonexistent") is None
        assert reg.get_handler("nonexistent") is None

    def test_unregister(self) -> None:
        reg = ToolRegistry()
        reg.register(_make_spec("temp"))
        assert reg.get("temp") is not None
        reg.unregister("temp")
        assert reg.get("temp") is None

    def test_unregister_nonexistent_is_noop(self) -> None:
        reg = ToolRegistry()
        reg.unregister("nothing")  # should not raise

    def test_register_overrides(self) -> None:
        reg = ToolRegistry()
        reg.register(_make_spec("tool", handler=lambda **kw: "v1"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        reg.register(_make_spec("tool", handler=lambda **kw: "v2"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        handler = reg.get_handler("tool")
        assert handler is not None
        assert handler() == "v2"
        assert len(reg.schemas) == 1


# ---------------------------------------------------------------------------
# Child registries (hierarchical scoping)
# ---------------------------------------------------------------------------


class TestChildRegistry:
    def test_child_inherits_parent_tools(self) -> None:
        parent = ToolRegistry()
        parent.register(_make_spec("parent_tool", handler=lambda **kw: "parent"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        child = parent.child()
        assert child.get("parent_tool") is not None
        h = child.get_handler("parent_tool")
        assert h is not None
        assert h() == "parent"

    def test_child_can_add_tools(self) -> None:
        parent = ToolRegistry()
        child = parent.child()
        child.register(_make_spec("child_tool", handler=lambda **kw: "child"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        assert child.get("child_tool") is not None
        assert parent.get("child_tool") is None  # parent unaffected

    def test_child_can_override_parent(self) -> None:
        parent = ToolRegistry()
        parent.register(_make_spec("tool", handler=lambda **kw: "parent"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        child = parent.child()
        child.register(_make_spec("tool", handler=lambda **kw: "child"))  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        h_child = child.get_handler("tool")
        h_parent = parent.get_handler("tool")
        assert h_child is not None
        assert h_parent is not None
        assert h_child() == "child"
        assert h_parent() == "parent"

    def test_schemas_merges_local_and_parent(self) -> None:
        parent = ToolRegistry()
        parent.register(_make_spec("a"))
        child = parent.child()
        child.register(_make_spec("b"))
        names = child.tool_names
        assert "a" in names
        assert "b" in names
        assert len(parent.tool_names) == 1

    def test_schemas_include_full_ancestor_chain(self) -> None:
        grandparent = ToolRegistry()
        grandparent.register(_make_spec("grandparent_tool"))
        parent = grandparent.child()
        parent.register(_make_spec("parent_tool"))
        child = parent.child()
        child.register(_make_spec("child_tool"))

        assert child.get_handler("grandparent_tool") is not None
        assert child.tool_names == ["child_tool", "parent_tool", "grandparent_tool"]

    def test_unregister_in_child_does_not_affect_parent(self) -> None:
        parent = ToolRegistry()
        parent.register(_make_spec("shared"))
        child = parent.child()
        child.unregister("shared")
        # Child no longer has it locally, but inherits from parent
        assert child.get("shared") is not None  # falls through to parent
        assert parent.get("shared") is not None

    def test_default_registry_child_inherits_builtins(self) -> None:
        child = default_registry.child()
        assert len(child.schemas) >= 8
        assert child.get_handler("bash") is not None


# ---------------------------------------------------------------------------
# Armory plugin loading
# ---------------------------------------------------------------------------


class TestPluginLoading:
    def test_load_from_nonexistent_dir(self, tmp_path: Path) -> None:
        reg = ToolRegistry()
        loaded = reg.load_plugins(tmp_path / "nope")
        assert loaded == 0

    def test_load_empty_dir(self, tmp_path: Path) -> None:
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        reg = ToolRegistry()
        loaded = reg.load_plugins(tools_dir)
        assert loaded == 0

    def test_skip_underscore_prefix(self, tmp_path: Path) -> None:
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "_helper.py").write_text(
            "def register(r): r.register(42)\n"  # deliberately broken
        )
        reg = ToolRegistry()
        loaded = reg.load_plugins(tools_dir)
        assert loaded == 0

    def test_load_valid_plugin(self, tmp_path: Path) -> None:
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        plugin_code = (
            "from hephaistos.harness.tools import ToolSpec\n"
            "def register(registry):\n"
            "    schema = {\n"
            "        'type': 'function',\n"
            "        'function': {\n"
            "            'name': 'greet',\n"
            "            'description': 'Say hi',\n"
            "            'parameters': {\n"
            "                'type': 'object',\n"
            "                'properties': {},\n"
            "                'required': [],\n"
            "            },\n"
            "        },\n"
            "    }\n"
            "    registry.register(ToolSpec(\n"
            "        schema=schema,\n"
            "        handler=lambda **kw: 'hello from plugin',\n"
            "    ))\n"
        )
        (tools_dir / "greet.py").write_text(plugin_code)
        reg = ToolRegistry()
        loaded = reg.load_plugins(tools_dir)
        assert loaded == 1
        h = reg.get_handler("greet")
        assert h is not None
        assert h() == "hello from plugin"

    def test_load_plugin_without_register_function(self, tmp_path: Path) -> None:
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "empty.py").write_text("x = 1\n")
        reg = ToolRegistry()
        loaded = reg.load_plugins(tools_dir)
        assert loaded == 0

    def test_load_broken_plugin_does_not_crash(self, tmp_path: Path) -> None:
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "broken.py").write_text("raise RuntimeError('boom')\n")
        reg = ToolRegistry()
        loaded = reg.load_plugins(tools_dir)
        assert loaded == 0

    def test_armory_scoped_registry_with_plugins(self, tmp_path: Path) -> None:
        """Simulate per-armory tool loading via child registry."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        plugin_code = (
            "from hephaistos.harness.tools import ToolSpec\n"
            "def register(registry):\n"
            "    schema = {\n"
            "        'type': 'function',\n"
            "        'function': {\n"
            "            'name': 'calc',\n"
            "            'description': 'Calculator',\n"
            "            'parameters': {\n"
            "                'type': 'object',\n"
            "                'properties': {},\n"
            "                'required': [],\n"
            "            },\n"
            "        },\n"
            "    }\n"
            "    registry.register(ToolSpec(\n"
            "        schema=schema,\n"
            "        handler=lambda **kw: '42',\n"
            "    ))\n"
        )
        (tools_dir / "calc.py").write_text(plugin_code)
        child = default_registry.child()
        child.load_plugins(tools_dir)
        # Built-ins inherited, plugin added
        assert "bash" in child.tool_names
        assert "calc" in child.tool_names
        # Parent unaffected
        assert "calc" not in default_registry.tool_names


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    def test_tool_schemas_matches_registry(self) -> None:
        registry_schemas = default_registry.schemas
        assert len(TOOL_SCHEMAS) == len(registry_schemas)
        by_name = {s["function"]["name"]: s for s in TOOL_SCHEMAS}
        for s in registry_schemas:
            assert s["function"]["name"] in by_name

    def test_get_handler_delegates_to_registry(self) -> None:
        assert get_handler("bash") is default_registry.get_handler("bash")
        assert get_handler("nonexistent") is None


# ---------------------------------------------------------------------------
# Dispatch integration with custom registry
# ---------------------------------------------------------------------------


class TestDispatchWithRegistry:
    def test_execute_with_custom_registry(self, tmp_path: Path) -> None:
        reg = ToolRegistry()
        reg.register(
            ToolSpec(
                schema={
                    "type": "function",
                    "function": {
                        "name": "echo_tool",
                        "description": "",
                        "parameters": {
                            "type": "object",
                            "properties": {"msg": {"type": "string"}},
                            "required": ["msg"],
                        },
                    },
                },
                handler=lambda msg, **kw: f"echo: {msg}",  # type: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
            )
        )
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "echo_tool",
                    "arguments": json.dumps({"msg": "hello"}),
                },
            }
        ]
        results = execute_tool_calls(tool_calls, tmp_path, registry=reg)
        assert len(results) == 1
        assert "echo: hello" in results[0]["content"]

    def test_execute_unknown_tool_with_custom_registry(self, tmp_path: Path) -> None:
        reg = ToolRegistry()  # empty registry
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json.dumps({"command": "echo hi"}),
                },
            }
        ]
        results = execute_tool_calls(tool_calls, tmp_path, registry=reg)
        assert "Unknown tool" in results[0]["content"]
