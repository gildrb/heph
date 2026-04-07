"""Unit tests for the harness: tools, dispatch, and path sandboxing."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from hephaistos.harness.tools import (
    TOOL_SCHEMAS,
    get_handler,
    run_bash,
    run_edit_file,
    run_list_files,
    run_read_file,
    run_write_file,
    safe_path,
)
from hephaistos.harness.dispatch import (
    _format_tool_args,
    _merge_tool_call_deltas,
    _summarize_result,
    execute_tool_calls,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with some test files."""
    (tmp_path / "hello.py").write_text('print("hello")\n')
    (tmp_path / "README.md").write_text("# Test\n")
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "main.py").write_text("def main(): pass\n")
    return tmp_path


# ---------------------------------------------------------------------------
# safe_path
# ---------------------------------------------------------------------------


class TestSafePath:
    def test_normal_relative(self, workspace: Path) -> None:
        result = safe_path(workspace, "hello.py")
        assert result == workspace / "hello.py"

    def test_subdirectory(self, workspace: Path) -> None:
        result = safe_path(workspace, "src/main.py")
        assert result == workspace / "src" / "main.py"

    def test_escape_traversal(self, workspace: Path) -> None:
        with pytest.raises(ValueError, match="escapes workspace"):
            safe_path(workspace, "../../../etc/passwd")

    def test_absolute_path_inside(self, workspace: Path) -> None:
        abs_path = str(workspace / "hello.py")
        result = safe_path(workspace, abs_path)
        assert result == workspace / "hello.py"

    def test_absolute_path_outside(self, workspace: Path) -> None:
        with pytest.raises(ValueError, match="escapes workspace"):
            safe_path(workspace, "/etc/passwd")


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


class TestBash:
    def test_simple_command(self) -> None:
        result = run_bash("echo hello")
        assert "hello" in result

    def test_failed_command(self) -> None:
        result = run_bash("false")
        assert "exit code" in result

    def test_stderr(self) -> None:
        result = run_bash("echo error >&2")
        assert "error" in result

    def test_timeout(self) -> None:
        result = run_bash("sleep 60")
        assert "timed out" in result.lower() or "exit code" in result.lower()


class TestReadFile:
    def test_read_existing(self, workspace: Path) -> None:
        result = run_read_file("hello.py", workspace=workspace)
        assert 'print("hello")' in result

    def test_read_missing(self, workspace: Path) -> None:
        result = run_read_file("nope.py", workspace=workspace)
        assert "not found" in result.lower()

    def test_read_with_offset(self, workspace: Path) -> None:
        result = run_read_file("hello.py", workspace=workspace, offset=1)
        assert "hello" not in result

    def test_read_with_limit(self, workspace: Path) -> None:
        result = run_read_file("hello.py", workspace=workspace, limit=1)
        assert "hello" in result
        assert result.count("\n") == 0  # only first line

    def test_read_escape_path(self, workspace: Path) -> None:
        result = run_read_file("../../../etc/passwd", workspace=workspace)
        assert "escapes" in result.lower()


class TestWriteFile:
    def test_write_new(self, workspace: Path) -> None:
        result = run_write_file("new.txt", "hello world", workspace=workspace)
        assert "Wrote" in result
        assert (workspace / "new.txt").read_text() == "hello world"

    def test_write_overwrite(self, workspace: Path) -> None:
        run_write_file("hello.py", "# replaced", workspace=workspace)
        assert (workspace / "hello.py").read_text() == "# replaced"

    def test_write_creates_dirs(self, workspace: Path) -> None:
        result = run_write_file("a/b/c.txt", "deep", workspace=workspace)
        assert "Wrote" in result
        assert (workspace / "a" / "b" / "c.txt").read_text() == "deep"

    def test_write_escape(self, workspace: Path) -> None:
        result = run_write_file("/tmp/evil.txt", "x", workspace=workspace)
        assert "escapes" in result.lower()


class TestEditFile:
    def test_edit_existing(self, workspace: Path) -> None:
        result = run_edit_file(
            "hello.py", 'print("hello")', 'print("world")', workspace=workspace
        )
        assert "Edited" in result
        assert (workspace / "hello.py").read_text() == 'print("world")\n'

    def test_edit_not_found(self, workspace: Path) -> None:
        result = run_edit_file("hello.py", "nonexistent", "x", workspace=workspace)
        assert "not found" in result.lower()

    def test_edit_multiple_matches(self, workspace: Path) -> None:
        (workspace / "dup.txt").write_text("aaa\naaa\n")
        result = run_edit_file("dup.txt", "aaa", "bbb", workspace=workspace)
        assert "2 matches" in result


class TestListFiles:
    def test_list_root(self, workspace: Path) -> None:
        result = run_list_files(workspace=workspace)
        assert "hello.py" in result
        assert "README.md" in result

    def test_list_subdir(self, workspace: Path) -> None:
        result = run_list_files(path="src", workspace=workspace)
        assert "main.py" in result

    def test_list_with_pattern(self, workspace: Path) -> None:
        result = run_list_files(pattern="*.py", workspace=workspace)
        assert "hello.py" in result
        assert "README.md" not in result

    def test_list_empty(self, tmp_path: Path) -> None:
        result = run_list_files(workspace=tmp_path)
        assert "no files" in result.lower()


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_schema_count(self) -> None:
        assert len(TOOL_SCHEMAS) == 6

    def test_all_have_function_type(self) -> None:
        for schema in TOOL_SCHEMAS:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "parameters" in schema["function"]

    def test_all_handlers_registered(self) -> None:
        names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        for name in names:
            assert get_handler(name) is not None

    def test_unknown_handler(self) -> None:
        assert get_handler("nonexistent_tool") is None


# ---------------------------------------------------------------------------
# Dispatch helpers
# ---------------------------------------------------------------------------


class TestMergeToolCallDeltas:
    def test_single_delta(self) -> None:
        accumulated: list[dict] = []
        _merge_tool_call_deltas(accumulated, [
            {"index": 0, "id": "call_1", "function": {"name": "bash", "arguments": '{"com'}}
        ])
        assert len(accumulated) == 1
        assert accumulated[0]["id"] == "call_1"
        assert accumulated[0]["function"]["name"] == "bash"

    def test_multi_chunk_args(self) -> None:
        accumulated: list[dict] = []
        _merge_tool_call_deltas(accumulated, [
            {"index": 0, "id": "call_1", "function": {"name": "bash", "arguments": '{"com'}}
        ])
        _merge_tool_call_deltas(accumulated, [
            {"index": 0, "function": {"arguments": 'mand": "ls"}'}}
        ])
        assert accumulated[0]["function"]["arguments"] == '{"command": "ls"}'

    def test_multiple_tool_calls(self) -> None:
        accumulated: list[dict] = []
        _merge_tool_call_deltas(accumulated, [
            {"index": 0, "id": "call_1", "function": {"name": "bash", "arguments": '{"co'}}
        ])
        _merge_tool_call_deltas(accumulated, [
            {"index": 1, "id": "call_2", "function": {"name": "read_file", "arguments": '{"pa'}}
        ])
        assert len(accumulated) == 2


class TestFormatToolArgs:
    def test_bash(self) -> None:
        result = _format_tool_args("bash", {"command": "ls -la"})
        assert "$ ls -la" in result

    def test_read(self) -> None:
        result = _format_tool_args("read_file", {"path": "src/main.py"})
        assert "[read] src/main.py" in result

    def test_write(self) -> None:
        result = _format_tool_args("write_file", {"path": "out.txt", "content": "hi"})
        assert "[write] out.txt" in result
        assert "2 chars" in result

    def test_edit(self) -> None:
        result = _format_tool_args("edit_file", {"path": "a.py"})
        assert "[edit] a.py" in result

    def test_list(self) -> None:
        result = _format_tool_args("list_files", {"path": "."})
        assert "[list] ." in result


class TestSummarizeResult:
    def test_short(self) -> None:
        result = _summarize_result("ok")
        assert "-> ok" in result

    def test_long(self) -> None:
        content = "\n".join(f"line {i}" for i in range(100))
        result = _summarize_result(content)
        assert "..." in result
        assert "100 lines" in result


class TestExecuteToolCalls:
    def test_execute_bash(self, workspace: Path) -> None:
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json.dumps({"command": "echo hello"}),
                },
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_1"
        assert "hello" in results[0]["content"]

    def test_execute_unknown_tool(self, workspace: Path) -> None:
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "fly_rocket", "arguments": "{}"},
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert "Unknown tool" in results[0]["content"]

    def test_execute_invalid_json(self, workspace: Path) -> None:
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "bash", "arguments": "not-json"},
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert "invalid JSON" in results[0]["content"]

    def test_execute_read_file(self, workspace: Path) -> None:
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": json.dumps({"path": "hello.py"}),
                },
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert "hello" in results[0]["content"]
