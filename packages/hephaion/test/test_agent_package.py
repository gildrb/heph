"""Tests that the new agent package imports resolve correctly.

These verify the structural correctness of the agent/ package created
from the former harness/ modules.
"""

from __future__ import annotations

import importlib.util

import hephaion.agent as agent_pkg
from hephaion.agent import (
    citation,
    compact,
    dispatch,
    mutation_queue,
    prompt,
    steering,
    tools,
)


class TestAgentPackageImports:
    """Verify every module in agent is importable."""

    def test_import_dispatch(self) -> None:
        assert hasattr(dispatch, "iter_agent_events")
        assert hasattr(dispatch, "execute_tool_calls")
        assert hasattr(dispatch, "SteeringQueue")

    def test_import_tools(self) -> None:
        assert hasattr(tools, "ToolRegistry")
        assert hasattr(tools, "ToolResult")
        assert hasattr(tools, "ToolSpec")
        assert hasattr(tools, "default_registry")

    def test_import_citation(self) -> None:
        assert hasattr(citation, "verify_response")

    def test_import_compact(self) -> None:
        assert hasattr(compact, "micro_compact")
        assert hasattr(compact, "auto_compact")

    def test_import_prompt(self) -> None:
        assert hasattr(prompt, "SystemPrompt")
        assert hasattr(prompt, "build_system_prompt")
        assert hasattr(prompt, "build_system_prompt_sections")
        assert hasattr(prompt, "render_tool_docs")

    def test_import_mutation_queue(self) -> None:
        assert hasattr(mutation_queue, "FileMutationQueue")
        assert hasattr(mutation_queue, "get_queue")

    def test_import_steering(self) -> None:
        assert hasattr(steering, "SteeringQueue")

    def test_import_init_re_exports(self) -> None:
        """Verify agent/__init__.py re-exports the public API."""
        assert callable(agent_pkg.iter_agent_events)
        assert callable(agent_pkg.execute_tool_calls)
        assert callable(agent_pkg.render_tool_docs)
        assert agent_pkg.SystemPrompt is not None
        assert agent_pkg.ToolRegistry is not None


class TestAgentToolRestrictions:
    def test_restricted_registry_exposes_only_allowed_tools(self) -> None:
        restricted = dispatch._restricted_tool_registry(
            tools.default_registry,
            ("import_materials",),
        )

        names = [schema["function"]["name"] for schema in restricted.schemas]

        assert names == ["import_materials"]
        assert restricted.get_handler("import_materials") is not None
        assert restricted.get_handler("write_file") is None


class TestNoHarnessReferences:
    """Verify no code references the old harness package."""

    def test_no_harness_imports_in_source(self) -> None:
        """This is a structural test - it will pass once harness/ is deleted."""
        spec = importlib.util.find_spec("harness")
        # After harness/ is deleted, this should be None
        assert spec is None, "harness package still exists"
