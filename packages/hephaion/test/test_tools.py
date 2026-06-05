"""Tests for the web_fetch tool and structured bash output."""

from __future__ import annotations

import http.client
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agent.tools import (
    TOOL_SCHEMAS,
    BashResult,
    get_handler,
    run_bash,
    run_create_armory,
    run_create_named_armory,
    run_import_materials,
    run_memory,
    run_open_material,
    run_search_files,
    run_search_materials,
    run_validate_armory,
    run_web_fetch,
    run_write_file,
)

# ---------------------------------------------------------------------------
# BashResult
# ---------------------------------------------------------------------------


class TestBashResult:
    def test_success(self):
        br = BashResult(
            stdout="hello\n",
            stderr="",
            exit_code=0,
            timed_out=False,
            duration_seconds=0.5,
        )
        display = br.to_display()
        assert "hello" in display
        assert "exit code" not in display
        assert "timed out" not in display

    def test_nonzero_exit(self):
        br = BashResult(
            stdout="",
            stderr="error",
            exit_code=1,
            timed_out=False,
            duration_seconds=0.1,
        )
        display = br.to_display()
        assert "exit code 1" in display
        assert "error" in display

    def test_timeout(self):
        br = BashResult(stdout="", stderr="", exit_code=-1, timed_out=True, duration_seconds=30.0)
        display = br.to_display()
        assert "timed out" in display
        assert "30.0s" in display

    def test_no_output(self):
        br = BashResult(stdout="", stderr="", exit_code=0, timed_out=False, duration_seconds=0.01)
        assert br.to_display() == "(no output)"


# ---------------------------------------------------------------------------
# run_bash
# ---------------------------------------------------------------------------


class TestRunBash:
    def test_successful_command(self):
        result = run_bash("echo hello")
        assert "hello" in result

    def test_failed_command(self):
        result = run_bash("false")
        assert "exit code" in result

    def test_stderr_included(self):
        result = run_bash("echo error >&2")
        assert "error" in result

    def test_timeout(self):
        result = run_bash("sleep 60", timeout=1)
        assert "timed out" in result

    def test_custom_timeout(self):
        result = run_bash("echo fast", timeout=10)
        assert "fast" in result

    def test_rtk_disabled_uses_original_shell(self):
        completed = MagicMock(stdout="hello\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAION_RTK": "0"}, clear=False),
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("echo hello")

        assert result == "hello\n"
        run.assert_called_once()
        assert run.call_args.args == ("echo hello",)
        assert run.call_args.kwargs["shell"] is True

    def test_rtk_default_rewrites_simple_command_when_available(self):
        completed = MagicMock(stdout="compact\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("agent.shell_tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("git status")

        assert result == "compact\n"
        run.assert_called_once()
        assert run.call_args.args == (["/usr/local/bin/rtk", "git", "status"],)
        assert run.call_args.kwargs["shell"] is False

    def test_rtk_enabled_uses_ultra_compact_flag(self):
        completed = MagicMock(stdout="compact\n", stderr="", returncode=0)
        with (
            patch.dict(
                "os.environ",
                {"HEPHAION_RTK": "1", "HEPHAION_RTK_ULTRA": "1"},
                clear=False,
            ),
            patch("agent.shell_tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            run_bash("git status")

        assert run.call_args.args == (["/usr/local/bin/rtk", "--ultra-compact", "git", "status"],)

    def test_rtk_missing_falls_back_to_original_shell(self):
        completed = MagicMock(stdout="original\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAION_RTK": "1"}, clear=False),
            patch("agent.shell_tools.shutil.which", return_value=None),
            patch("agent.shell_tools._log.warning") as warning,
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("git status")

        assert result == "original\n"
        assert run.call_args.args == ("git status",)
        assert run.call_args.kwargs["shell"] is True
        warning.assert_called_once()

    def test_rtk_missing_can_fail_closed(self):
        with (
            patch.dict(
                "os.environ",
                {"HEPHAION_RTK": "1", "HEPHAION_RTK_FALLBACK_ALLOWED": "0"},
                clear=False,
            ),
            patch("agent.shell_tools.shutil.which", return_value=None),
            patch("agent.shell_tools._log.warning") as warning,
            patch("agent.shell_tools.subprocess.run") as run,
        ):
            result = run_bash("git status")

        assert "rtk unavailable or command unsupported and shell fallback disabled" in result
        run.assert_not_called()
        warning.assert_called_once()

    def test_rtk_execution_failure_falls_back_with_marker(self):
        completed = MagicMock(stdout="original\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAION_RTK": "1"}, clear=False),
            patch("agent.shell_tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("agent.shell_tools._log.warning") as warning,
            patch(
                "agent.shell_tools.subprocess.run",
                side_effect=[OSError("missing"), completed],
            ) as run,
        ):
            result = run_bash("git status")

        assert "[rtk unavailable: missing; used original command output]" in result
        assert "original" in result
        assert run.call_count == 2
        assert run.call_args.args == ("git status",)
        assert run.call_args.kwargs["shell"] is True
        warning.assert_called_once()

    def test_rtk_execution_failure_can_fail_closed(self):
        with (
            patch.dict(
                "os.environ",
                {"HEPHAION_RTK": "1", "HEPHAION_RTK_FALLBACK_ALLOWED": "0"},
                clear=False,
            ),
            patch("agent.shell_tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("agent.shell_tools._log.warning") as warning,
            patch(
                "agent.shell_tools.subprocess.run",
                side_effect=OSError("missing"),
            ) as run,
        ):
            result = run_bash("git status")

        assert "rtk unavailable and shell fallback disabled" in result
        assert run.call_count == 1
        warning.assert_called_once()

    def test_rtk_min_command_chars_skips_short_commands(self):
        completed = MagicMock(stdout="short\n", stderr="", returncode=0)
        with (
            patch.dict(
                "os.environ",
                {"HEPHAION_RTK": "1", "HEPHAION_RTK_MIN_COMMAND_CHARS": "999"},
                clear=False,
            ),
            patch("agent.shell_tools.shutil.which") as which,
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("ls")

        assert result == "short\n"
        which.assert_not_called()
        assert run.call_args.args == ("ls",)
        assert run.call_args.kwargs["shell"] is True

    def test_rtk_skips_shell_metachar_commands(self):
        completed = MagicMock(stdout="hello\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAION_RTK": "1"}, clear=False),
            patch("agent.shell_tools.shutil.which") as which,
            patch("agent.shell_tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("echo hello >&2")

        assert result == "hello\n"
        which.assert_not_called()
        assert run.call_args.args == ("echo hello >&2",)
        assert run.call_args.kwargs["shell"] is True

    def test_output_truncated(self):
        # Generate very large output
        result = run_bash("python3 -c \"print('x' * 100000)\"")
        assert len(result) <= 50_200  # _MAX_READ_CHARS + margin


# ---------------------------------------------------------------------------
# armory tools
# ---------------------------------------------------------------------------


class TestArmoryTools:
    def test_create_armory_builds_canonical_layout(self, tmp_path: Path) -> None:
        result = run_create_armory("linear-algebra", workspace=tmp_path)

        assert result.success is True
        assert "materials/" in result.content
        assert (tmp_path / "linear-algebra" / "materials").is_dir()
        assert (tmp_path / "linear-algebra" / ".hephaion" / "armory.toml").is_file()
        assert (tmp_path / "linear-algebra" / ".hephaion" / "chats").is_dir()
        assert not (tmp_path / "linear-algebra" / "source").exists()
        assert not (tmp_path / "linear-algebra" / "library").exists()
        assert not (tmp_path / "linear-algebra" / "notes").exists()

    def test_create_armory_rejects_workspace_escape(self, tmp_path: Path) -> None:
        result = run_create_armory("../outside", workspace=tmp_path)

        assert result.success is False
        assert result.error == "path_escape"

    def test_validate_armory_reports_valid_layout(self, tmp_path: Path) -> None:
        run_create_armory("exam-prep", workspace=tmp_path)

        result = run_validate_armory("exam-prep", workspace=tmp_path)

        assert result.success is True
        assert "Valid Heph armory" in result.content
        assert result.metadata["materials_dir"] == "materials"

    def test_validate_armory_reports_missing_marker(self, tmp_path: Path) -> None:
        (tmp_path / "not-armory").mkdir()

        result = run_validate_armory("not-armory", workspace=tmp_path)

        assert result.success is False
        assert result.error == "invalid_armory"

    def test_create_named_armory_uses_exact_home_name(self, tmp_path: Path) -> None:
        home = tmp_path / "armories"

        with patch.dict("os.environ", {"HEPHAION_ARMORY_HOME": str(home)}, clear=False):
            result = run_create_named_armory("bfi-2", workspace=tmp_path)

        assert result.success is True
        assert result.metadata["created"] is True
        assert (home / "bfi-2" / "materials").is_dir()
        assert (home / "bfi-2" / ".hephaion" / "armory.toml").is_file()

    def test_create_named_armory_rejects_path_like_name(self, tmp_path: Path) -> None:
        result = run_create_named_armory("../bfi-2", workspace=tmp_path)

        assert result.success is False
        assert result.error == "invalid_armory_name"

    def test_import_materials_copies_absolute_source_to_current_armory(
        self,
        tmp_path: Path,
    ) -> None:
        armory = tmp_path / "current"
        run_create_armory(".", workspace=armory)
        source = tmp_path / "lecture.md"
        source.write_text("source notes", encoding="utf-8")

        result = run_import_materials(str(source), workspace=armory)

        assert result.success is True
        assert result.metadata["current_armory"] is True
        assert result.metadata["refresh_current_armory"] is True
        assert result.metadata["imported"] == ["lecture.md"]
        assert (armory / "materials" / "lecture.md").read_text(encoding="utf-8") == "source notes"
        assert source.read_text(encoding="utf-8") == "source notes"

    def test_import_materials_rejects_missing_exact_armory_without_fuzzy_fallback(
        self,
        tmp_path: Path,
    ) -> None:
        home = tmp_path / "armories"
        armory = tmp_path / "current"
        run_create_armory(".", workspace=armory)
        run_create_armory("reference-armory", workspace=home)
        source = tmp_path / "notes.md"
        source.write_text("notes", encoding="utf-8")

        with patch.dict("os.environ", {"HEPHAION_ARMORY_HOME": str(home)}, clear=False):
            result = run_import_materials(
                str(source),
                target_armory="missing-armory",
                workspace=armory,
            )

        assert result.success is False
        assert result.error == "missing_armory"
        assert not (home / "missing-armory").exists()
        assert not (home / "reference-armory" / "materials" / "notes.md").exists()

    def test_import_materials_can_create_exact_target_when_explicit(
        self,
        tmp_path: Path,
    ) -> None:
        home = tmp_path / "armories"
        armory = tmp_path / "current"
        run_create_armory(".", workspace=armory)
        source = tmp_path / "notes.md"
        source.write_text("notes", encoding="utf-8")

        with patch.dict("os.environ", {"HEPHAION_ARMORY_HOME": str(home)}, clear=False):
            result = run_import_materials(
                str(source),
                target_armory="bfi-2",
                create_if_missing=True,
                workspace=armory,
            )

        assert result.success is True
        assert result.metadata["current_armory"] is False
        assert (home / "bfi-2" / "materials" / "notes.md").read_text(encoding="utf-8") == "notes"

    def test_import_materials_rejects_ambiguous_relative_source(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "current"
        launch = tmp_path / "launch"
        launch.mkdir()
        run_create_armory(".", workspace=armory)
        (armory / "shared.md").write_text("armory copy", encoding="utf-8")
        (launch / "shared.md").write_text("launch copy", encoding="utf-8")
        monkeypatch.chdir(launch)

        result = run_import_materials("shared.md", workspace=armory)

        assert result.success is False
        assert result.error == "ambiguous_source_path"
        assert not (armory / "materials" / "shared.md").exists()

    def test_search_materials_uses_indexed_armory_content(self, tmp_path: Path) -> None:
        run_create_armory(".", workspace=tmp_path)
        material = tmp_path / "materials" / "enzyme-notes.md"
        material.write_text(
            "# Enzyme Kinetics\n\n"
            "Michaelis-Menten kinetics explains how substrate concentration changes "
            "reaction velocity through Vmax and Km.\n",
            encoding="utf-8",
        )

        result = run_search_materials("substrate concentration velocity", workspace=tmp_path)

        assert result.success is True
        assert "materials/enzyme-notes.md#chunk=0" in result.content
        assert "Michaelis-Menten" in result.content
        assert result.metadata["matches"] == 1

    def test_open_material_reads_indexed_neighbor_chunks(self, tmp_path: Path) -> None:
        run_create_armory(".", workspace=tmp_path)
        material = tmp_path / "materials" / "lab-guide.md"
        material.write_text(
            "# Extraction\n\n"
            "Prepare the sample and record the buffer conditions.\n\n"
            "# Analysis\n\n"
            "Compare the measured band intensity against the calibration curve.\n",
            encoding="utf-8",
        )

        result = run_open_material(
            "materials/lab-guide.md",
            chunk=1,
            context=1,
            workspace=tmp_path,
        )

        assert result.success is True
        assert "Opened indexed material: materials/lab-guide.md" in result.content
        assert "Prepare the sample" in result.content
        assert "calibration curve" in result.content

    def test_memory_tool_adds_and_reads_armory_memory(self, tmp_path: Path) -> None:
        run_create_armory(".", workspace=tmp_path)

        added = run_memory(
            "add",
            topic="citation style",
            content="User prefers compact cited answers.",
            workspace=tmp_path,
        )
        read = run_memory("read", query="citation", workspace=tmp_path)

        assert added.success is True
        assert read.success is True
        assert "compact cited answers" in read.content
        assert (tmp_path / ".hephaion" / "memory.json").is_file()

    def test_memory_tool_replaces_by_unique_substring(self, tmp_path: Path) -> None:
        run_create_armory(".", workspace=tmp_path)
        run_memory("add", topic="style", content="Use long answers.", workspace=tmp_path)

        replaced = run_memory(
            "replace",
            old_text="long answers",
            topic="style",
            content="Use short answers.",
            workspace=tmp_path,
        )
        read = run_memory("read", workspace=tmp_path)

        assert replaced.success is True
        assert "Use short answers" in read.content

    def test_memory_tool_removes_by_unique_substring(self, tmp_path: Path) -> None:
        run_create_armory(".", workspace=tmp_path)
        run_memory("add", topic="tool quirk", content="Always inspect first.", workspace=tmp_path)

        removed = run_memory("remove", old_text="inspect first", workspace=tmp_path)
        read = run_memory("read", workspace=tmp_path)

        assert removed.success is True
        assert "inspect first" not in read.content


class TestWorkspaceFileTools:
    def test_search_files_skips_symlink_escape(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside-secret.txt"
        outside.write_text("needle outside workspace\n", encoding="utf-8")
        link = workspace / "linked-secret.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        result = run_search_files("needle", workspace=workspace)

        assert isinstance(result, str)
        assert "No matches found" in result

    def test_write_file_rejects_symlink_parent_escape(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        link = workspace / "linked-dir"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        result = run_write_file("linked-dir/secret.txt", "leak", workspace=workspace)

        assert "Path escapes workspace" in result or "parent directory escapes workspace" in result
        assert not (outside / "secret.txt").exists()


# ---------------------------------------------------------------------------
# web_fetch
# ---------------------------------------------------------------------------


class TestWebFetch:
    def test_rejects_non_http(self):
        result = run_web_fetch("ftp://example.com")
        assert "Error" in result

    def test_rejects_no_protocol(self):
        result = run_web_fetch("example.com")
        assert "Error" in result

    def test_rejects_url_credentials(self):
        with patch("agent.web_tools._open_without_redirect") as open_url:
            result = run_web_fetch("https://user:pass@example.com/test")

        assert "must not include credentials" in result
        open_url.assert_not_called()

    def test_rejects_invalid_port(self):
        result = run_web_fetch("https://example.com:99999/test")

        assert "invalid port" in result

    def test_fetch_includes_source_attribution(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html><body>Test content</body></html>"
        mock_response.headers.get.return_value = "text/html"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.web_tools._open_without_redirect",
            return_value=mock_response,
        ):
            result = run_web_fetch("https://example.com/test")

        assert "Source: https://example.com/test" in result
        assert "Test content" in result
        assert "End of fetched content" in result

    def test_fetch_http_error(self):
        with patch(
            "agent.web_tools._open_without_redirect",
            side_effect=urllib.error.HTTPError(
                "url",
                404,
                "Not Found",
                http.client.HTTPMessage(),
                None,
            ),
        ):
            result = run_web_fetch("https://example.com/missing")
            assert "HTTP 404" in result

    def test_fetch_non_text_content_type(self):
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "image/png"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.web_tools._open_without_redirect",
            return_value=mock_response,
        ):
            result = run_web_fetch("https://example.com/image.png")
            assert "non-text content" in result

    def test_fetch_blocks_private_redirect_target(self):
        headers = Message()
        headers["Location"] = "http://127.0.0.1/secret"
        redirect = urllib.error.HTTPError("url", 302, "Found", headers, None)

        def resolve(hostname: str) -> list[str]:
            if hostname == "example.com":
                return ["93.184.216.34"]
            if hostname == "127.0.0.1":
                return ["127.0.0.1"]
            return []

        with (
            patch("agent.web_tools._resolve_hostname_ips", side_effect=resolve),
            patch("agent.web_tools._open_without_redirect", side_effect=redirect),
        ):
            result = run_web_fetch("https://example.com/start")

        assert "blocked private/internal host" in result

    def test_fetch_follows_safe_redirect(self):
        headers = Message()
        headers["Location"] = "https://example.org/final"
        redirect = urllib.error.HTTPError("url", 302, "Found", headers, None)
        mock_response = MagicMock()
        mock_response.read.return_value = b"Redirected content"
        mock_response.headers.get.return_value = "text/plain"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch(
                "agent.web_tools._resolve_hostname_ips",
                return_value=["93.184.216.34"],
            ),
            patch(
                "agent.web_tools._open_without_redirect",
                side_effect=[redirect, mock_response],
            ),
        ):
            result = run_web_fetch("https://example.com/start")

        assert "Source: https://example.com/start" in result
        assert "Final URL: https://example.org/final" in result
        assert "Redirected content" in result


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_web_fetch_schema_exists(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "web_fetch" in names

    def test_bash_schema_is_not_registered_by_default(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "bash" not in names

    def test_armory_tool_schemas_exist(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "create_armory" in names
        assert "validate_armory" in names
        assert "create_named_armory" in names
        assert "import_materials" in names
        assert "search_materials" in names
        assert "open_material" in names
        assert "memory" in names

    def test_web_fetch_handler_registered(self):
        handler = get_handler("web_fetch")
        assert handler is not None

    def test_armory_handlers_registered(self):
        assert get_handler("create_armory") is not None
        assert get_handler("validate_armory") is not None
        assert get_handler("create_named_armory") is not None
        assert get_handler("import_materials") is not None
        assert get_handler("search_materials") is not None
        assert get_handler("open_material") is not None
        assert get_handler("memory") is not None

    def test_all_schemas_have_required_fields(self):
        for schema in TOOL_SCHEMAS:
            assert "type" in schema
            assert "function" in schema
            fn = schema["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
