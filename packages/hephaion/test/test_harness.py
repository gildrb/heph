"""Unit tests for the harness: tools, dispatch, and path sandboxing."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import agent.dispatch as dispatch_mod
import agent.model_stream as model_stream_mod
import pytest
from agent.dispatch import summarize_result
from agent.tool_execution import (
    ToolCall,
    execute_tool_calls,
    format_tool_args,
    merge_tool_call_deltas,
)
from agent.tools import (
    TOOL_SCHEMAS,
    get_handler,
    run_bash,
    run_edit_file,
    run_list_files,
    run_read_file,
    run_search_files,
    run_write_file,
    safe_path,
)
from ai.runtime import ApiMessage, ChatConfig, CompletionDelta, Conversation
from chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
)

from conftest import message_text

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
        result = run_bash("sleep 60", timeout=1)
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

    def test_read_binary_pdf_gives_helpful_error(self, workspace: Path) -> None:
        pdf = workspace / "slides.pdf"
        pdf.write_bytes(b"%PDF-1.4\x80\x81\x82fake pdf")
        result = run_read_file("slides.pdf", workspace=workspace)
        assert "binary document" in result.lower()
        assert "heph index" in result.lower()

    def test_read_binary_unknown_gives_generic_error(self, workspace: Path) -> None:
        binary = workspace / "data.dat"
        binary.write_bytes(b"\x80\x81\x82\x83")
        result = run_read_file("data.dat", workspace=workspace)
        assert "Cannot read (binary file)" in result


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
        result = run_edit_file("hello.py", 'print("hello")', 'print("world")', workspace=workspace)
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


class TestSearchFiles:
    def test_search_finds_matching_lines(self, workspace: Path) -> None:
        result = run_search_files("hello", workspace=workspace)

        assert isinstance(result, str)
        assert "hello.py:1:" in result
        assert 'print("hello")' in result

    def test_search_skips_hidden_and_binary_document_files(self, workspace: Path) -> None:
        hidden_dir = workspace / ".hephaion"
        hidden_dir.mkdir()
        (hidden_dir / "trace.txt").write_text("needle\n")
        (workspace / "slides.pdf").write_text("needle\n")

        result = run_search_files("needle", workspace=workspace)

        assert isinstance(result, str)
        assert "No matches found" in result

    def test_search_can_cancel_before_scan(self, workspace: Path) -> None:
        abort = threading.Event()
        abort.set()

        result = run_search_files("hello", workspace=workspace, abort=abort)

        assert not isinstance(result, str)
        assert result.error == "cancelled"
        assert result.metadata == {"files_scanned": 0, "matches": 0}


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_schema_names_match_registered_tools(self) -> None:
        names = {schema["function"]["name"] for schema in TOOL_SCHEMAS}

        assert names == {
            "compact",
            "create_armory",
            "create_named_armory",
            "edit_file",
            "import_materials",
            "list_files",
            "memory",
            "open_material",
            "read_file",
            "search_files",
            "search_materials",
            "validate_armory",
            "web_fetch",
            "write_file",
        }

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
        accumulated: list[ToolCall] = []
        merge_tool_call_deltas(
            accumulated,
            [
                {
                    "index": 0,
                    "id": "call_1",
                    "function": {"name": "bash", "arguments": '{"com'},
                }
            ],
        )
        assert len(accumulated) == 1
        assert accumulated[0]["id"] == "call_1"
        assert accumulated[0]["function"]["name"] == "bash"

    def test_multi_chunk_args(self) -> None:
        accumulated: list[ToolCall] = []
        merge_tool_call_deltas(
            accumulated,
            [
                {
                    "index": 0,
                    "id": "call_1",
                    "function": {"name": "bash", "arguments": '{"com'},
                }
            ],
        )
        merge_tool_call_deltas(
            accumulated,
            [{"index": 0, "function": {"name": "", "arguments": 'mand": "ls"}'}}],
        )
        assert accumulated[0]["function"]["arguments"] == '{"command": "ls"}'

    def test_multiple_tool_calls(self) -> None:
        accumulated: list[ToolCall] = []
        merge_tool_call_deltas(
            accumulated,
            [
                {
                    "index": 0,
                    "id": "call_1",
                    "function": {"name": "bash", "arguments": '{"co'},
                }
            ],
        )
        merge_tool_call_deltas(
            accumulated,
            [
                {
                    "index": 1,
                    "id": "call_2",
                    "function": {"name": "read_file", "arguments": '{"pa'},
                }
            ],
        )
        assert len(accumulated) == 2


class TestFormatToolArgs:
    def test_bash(self) -> None:
        result = format_tool_args("bash", {"command": "ls -la"})
        assert "Running: ls -la" in result

    def test_read(self) -> None:
        result = format_tool_args("read_file", {"path": "src/main.py"})
        assert "Reading: src/main.py" in result

    def test_write(self) -> None:
        result = format_tool_args("write_file", {"path": "out.txt", "content": "hi"})
        assert "Writing: out.txt" in result
        assert "2 chars" in result

    def test_edit(self) -> None:
        result = format_tool_args("edit_file", {"path": "a.py"})
        assert "Editing: a.py" in result

    def test_list(self) -> None:
        result = format_tool_args("list_files", {"path": "."})
        assert "Listing: ." in result

    def test_search_materials(self) -> None:
        result = format_tool_args("search_materials", {"query": "enzyme kinetics"})
        assert "Searching materials: enzyme kinetics" in result

    def test_open_material(self) -> None:
        result = format_tool_args(
            "open_material",
            {"source": "materials/lecture.pdf", "chunk": 3},
        )
        assert "Opening material: materials/lecture.pdf#chunk=3" in result


class TestSummarizeResult:
    def test_short(self) -> None:
        result = summarize_result("ok")
        assert "-> ok" in result

    def test_long(self) -> None:
        content = "\n".join(f"line {i}" for i in range(100))
        result = summarize_result(content)
        assert "..." in result
        assert "100 lines" in result


class TestExecuteToolCalls:
    def test_default_registry_rejects_bash(self, workspace: Path) -> None:
        tool_calls: list[ToolCall] = [
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
        assert results[0].get("tool_call_id") == "call_1"
        assert "Unknown tool: bash" in message_text(results[0])
        assert results[0].get("tool_success") is False

    def test_execute_unknown_tool(self, workspace: Path) -> None:
        tool_calls: list[ToolCall] = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "fly_rocket", "arguments": "{}"},
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert "Unknown tool" in message_text(results[0])

    def test_execute_invalid_json(self, workspace: Path) -> None:
        tool_calls: list[ToolCall] = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "bash", "arguments": "not-json"},
            }
        ]
        results = execute_tool_calls(tool_calls, workspace)
        assert "invalid JSON" in message_text(results[0])

    def test_execute_read_file(self, workspace: Path) -> None:
        tool_calls: list[ToolCall] = [
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
        assert "hello" in message_text(results[0])


class TestIterAgentEvents:
    def test_dry_run_skips_streaming(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fail_stream(*_args: object, **_kwargs: object) -> None:
            raise AssertionError("streaming should be skipped")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fail_stream)
        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
                dry_run=True,
            )
        )

        assert events[0].kind == "notice"
        assert isinstance(events[-1], TurnCompleteEvent)
        assert events[-1].finish_reason == "dry_run"

    def test_turn_complete_event_after_text_reply(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_stream(*_args: object, **_kwargs: object):
            yield CompletionDelta(content="hello")
            yield CompletionDelta(finish_reason="stop")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        assert any(isinstance(event, AssistantDeltaEvent) for event in events)
        complete = events[-1]
        assert isinstance(complete, TurnCompleteEvent)
        assert complete.full_text == "hello"
        assert complete.finish_reason == "stop"

    def test_model_stream_emits_activity_notices(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_stream(*_args: object, **_kwargs: object):
            yield CompletionDelta(content="hello")
            yield CompletionDelta(content=" world")
            yield CompletionDelta(finish_reason="stop")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        notices = [event for event in events if isinstance(event, NoticeEvent)]
        assert any(event.code == "model_request" for event in notices)
        assert any(event.code == "model_delta" for event in notices)
        assert any(event.code == "model_complete" for event in notices)

    def test_first_turn_without_evidence_requires_tool_choice(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        seen_tool_choice: list[object | None] = []

        def fake_stream(*_args: object, **kwargs: object):
            seen_tool_choice.append(kwargs.get("tool_choice"))
            yield CompletionDelta(content="hello")
            yield CompletionDelta(finish_reason="stop")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)

        list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        assert seen_tool_choice == ["required"]

    def test_compact_tool_emits_control_event(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls = 0

        def fake_stream(*_args: object, **_kwargs: object):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield CompletionDelta(
                    tool_calls=[
                        {
                            "index": 0,
                            "id": "call_compact",
                            "function": {"name": "compact", "arguments": "{}"},
                        }
                    ],
                    finish_reason="tool_calls",
                )
                return
            yield CompletionDelta(content="after compact")
            yield CompletionDelta(finish_reason="stop")

        def no_op_compact(
            messages: list[ApiMessage],
            _config: ChatConfig,
            _workspace: Path,
        ) -> list[ApiMessage]:
            return messages

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)
        monkeypatch.setattr(dispatch_mod, "auto_compact", no_op_compact)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        assert any(isinstance(event, CompactRequestEvent) for event in events)
        assert isinstance(events[-1], TurnCompleteEvent)
        assert events[-1].full_text == "after compact"

    def test_material_search_tool_emits_readable_events(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        materials = workspace / "materials"
        materials.mkdir()
        (materials / "lecture.md").write_text(
            "# Protein Folding\n\n"
            "Chaperone proteins help prevent misfolding during translation.\n",
            encoding="utf-8",
        )
        calls = 0

        def fake_stream(*_args: object, **_kwargs: object):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield CompletionDelta(
                    tool_calls=[
                        {
                            "index": 0,
                            "id": "call_search",
                            "function": {
                                "name": "search_materials",
                                "arguments": json.dumps({"query": "chaperone proteins"}),
                            },
                        }
                    ],
                    finish_reason="tool_calls",
                )
                return
            yield CompletionDelta(content="Chaperones prevent misfolding [M1].")
            yield CompletionDelta(finish_reason="stop")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        tool_calls = [event for event in events if isinstance(event, ToolCallEvent)]
        tool_results = [event for event in events if isinstance(event, ToolResultEvent)]
        assert tool_calls
        assert tool_calls[0].display == "    Searching materials: chaperone proteins"
        assert tool_results
        assert tool_results[0].success is True
        assert "materials/lecture.md#chunk=0" in tool_results[0].content
        assert isinstance(events[-1], TurnCompleteEvent)
        assert events[-1].full_text == "Chaperones prevent misfolding [M1]."

    def test_tool_failure_injects_runtime_note_for_next_turn(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls = 0
        observed_system_notes: list[str] = []

        def fake_stream(_config: object, messages: list[ApiMessage], **_kwargs: object):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield CompletionDelta(
                    tool_calls=[
                        {
                            "index": 0,
                            "id": "call_read",
                            "function": {
                                "name": "read_file",
                                "arguments": json.dumps({"path": "missing.md"}),
                            },
                        }
                    ],
                    finish_reason="tool_calls",
                )
                return
            observed_system_notes.extend(
                str(message["content"])
                for message in messages
                if message["role"] == "system"
                and "Execution note: tool 'read_file' failed" in str(message["content"])
            )
            yield CompletionDelta(content="I will inspect a narrower path.")
            yield CompletionDelta(finish_reason="stop")

        def fake_execute_tool_calls(*_args: object, **_kwargs: object) -> list[ApiMessage]:
            return [
                {
                    "role": "tool",
                    "tool_call_id": "call_read",
                    "content": "Error: file not found",
                    "tool_success": False,
                    "tool_metadata": {
                        "tool": "read_file",
                        "latency_ms": 3.2,
                        "result_length": len("Error: file not found"),
                    },
                    "tool_error": "file not found",
                }
            ]

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)
        monkeypatch.setattr(dispatch_mod, "execute_tool_calls", fake_execute_tool_calls)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        runtime_notices = [
            event
            for event in events
            if isinstance(event, NoticeEvent) and event.code == "tool_runtime"
        ]
        assert runtime_notices
        assert runtime_notices[0].metadata["reason"] == "failed"
        assert observed_system_notes
        assert isinstance(events[-1], TurnCompleteEvent)
        assert events[-1].full_text == "I will inspect a narrower path."

    def test_repeated_tool_call_injects_runtime_note_for_next_turn(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls = 0
        observed_system_notes: list[str] = []

        def fake_stream(_config: object, messages: list[ApiMessage], **_kwargs: object):
            nonlocal calls
            calls += 1
            if calls in {1, 2}:
                yield CompletionDelta(
                    tool_calls=[
                        {
                            "index": 0,
                            "id": f"call_read_{calls}",
                            "function": {
                                "name": "read_file",
                                "arguments": json.dumps({"path": "hello.py"}),
                            },
                        }
                    ],
                    finish_reason="tool_calls",
                )
                return
            observed_system_notes.extend(
                str(message["content"])
                for message in messages
                if message["role"] == "system"
                and "was called with the same arguments 2 times" in str(message["content"])
            )
            yield CompletionDelta(content="I will change strategy.")
            yield CompletionDelta(finish_reason="stop")

        def fake_execute_tool_calls(tool_calls: list[ToolCall], *_args: object, **_kwargs: object):
            return [
                {
                    "role": "tool",
                    "tool_call_id": tool_calls[0]["id"],
                    "content": 'print("hello")',
                    "tool_success": True,
                    "tool_metadata": {
                        "tool": "read_file",
                        "latency_ms": 1.0,
                        "result_length": len('print("hello")'),
                    },
                    "tool_error": None,
                }
            ]

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)
        monkeypatch.setattr(dispatch_mod, "execute_tool_calls", fake_execute_tool_calls)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        repeat_notices = [
            event
            for event in events
            if isinstance(event, NoticeEvent)
            and event.code == "tool_runtime"
            and event.metadata.get("reason") == "repeated_call"
        ]
        assert repeat_notices
        assert repeat_notices[0].metadata["repeat_count"] == 2
        assert repeat_notices[0].metadata["tool"] == "read_file"
        assert observed_system_notes
        assert isinstance(events[-1], TurnCompleteEvent)
        assert events[-1].full_text == "I will change strategy."

    def test_first_tool_turn_exposes_acceptance_criteria(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        observed_message_count: list[int] = []

        def fake_stream(_config: object, messages: list[ApiMessage], **_kwargs: object):
            observed_message_count.append(len(messages))
            assert not any(
                "Acceptance criteria: inspect" in str(message["content"]) for message in messages
            )
            yield CompletionDelta(content="Done.")
            yield CompletionDelta(finish_reason="stop")

        monkeypatch.setattr(model_stream_mod, "stream_completion", fake_stream)

        events = list(
            dispatch_mod.iter_agent_events(
                ChatConfig(base_url="https://example.invalid", model="test-model"),
                Conversation(),
                workspace,
            )
        )

        criteria_notices = [
            event
            for event in events
            if isinstance(event, NoticeEvent) and event.code == "acceptance_criteria"
        ]
        assert criteria_notices
        assert criteria_notices[0].metadata["requires_tools"] is True
        assert observed_message_count
