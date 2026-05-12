"""Tests for the web_fetch tool and structured bash output."""

from __future__ import annotations

import http.client
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from hephaistos.agent.tools import (
    TOOL_SCHEMAS,
    BashResult,
    get_handler,
    run_bash,
    run_create_armory,
    run_open_material,
    run_search_materials,
    run_validate_armory,
    run_web_fetch,
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
            patch.dict("os.environ", {"HEPHAISTOS_RTK": "0"}, clear=False),
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
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
            patch("hephaistos.agent.tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
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
                {"HEPHAISTOS_RTK": "1", "HEPHAISTOS_RTK_ULTRA": "1"},
                clear=False,
            ),
            patch("hephaistos.agent.tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
        ):
            run_bash("git status")

        assert run.call_args.args == (["/usr/local/bin/rtk", "--ultra-compact", "git", "status"],)

    def test_rtk_missing_falls_back_to_original_shell(self):
        completed = MagicMock(stdout="original\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAISTOS_RTK": "1"}, clear=False),
            patch("hephaistos.agent.tools.shutil.which", return_value=None),
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("git status")

        assert result == "original\n"
        assert run.call_args.args == ("git status",)
        assert run.call_args.kwargs["shell"] is True

    def test_rtk_execution_failure_falls_back_with_marker(self):
        completed = MagicMock(stdout="original\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAISTOS_RTK": "1"}, clear=False),
            patch("hephaistos.agent.tools.shutil.which", return_value="/usr/local/bin/rtk"),
            patch(
                "hephaistos.agent.tools.subprocess.run",
                side_effect=[OSError("missing"), completed],
            ) as run,
        ):
            result = run_bash("git status")

        assert "[rtk unavailable: missing; used original command output]" in result
        assert "original" in result
        assert run.call_count == 2
        assert run.call_args.args == ("git status",)
        assert run.call_args.kwargs["shell"] is True

    def test_rtk_min_command_chars_skips_short_commands(self):
        completed = MagicMock(stdout="short\n", stderr="", returncode=0)
        with (
            patch.dict(
                "os.environ",
                {"HEPHAISTOS_RTK": "1", "HEPHAISTOS_RTK_MIN_COMMAND_CHARS": "999"},
                clear=False,
            ),
            patch("hephaistos.agent.tools.shutil.which") as which,
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
        ):
            result = run_bash("ls")

        assert result == "short\n"
        which.assert_not_called()
        assert run.call_args.args == ("ls",)
        assert run.call_args.kwargs["shell"] is True

    def test_rtk_skips_shell_metachar_commands(self):
        completed = MagicMock(stdout="hello\n", stderr="", returncode=0)
        with (
            patch.dict("os.environ", {"HEPHAISTOS_RTK": "1"}, clear=False),
            patch("hephaistos.agent.tools.shutil.which") as which,
            patch("hephaistos.agent.tools.subprocess.run", return_value=completed) as run,
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
        assert (tmp_path / "linear-algebra" / ".hephaistos" / "armory.toml").is_file()
        assert (tmp_path / "linear-algebra" / ".hephaistos" / "chats").is_dir()
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
        assert "Valid Hephaistos armory" in result.content
        assert result.metadata["materials_dir"] == "materials"

    def test_validate_armory_reports_missing_marker(self, tmp_path: Path) -> None:
        (tmp_path / "not-armory").mkdir()

        result = run_validate_armory("not-armory", workspace=tmp_path)

        assert result.success is False
        assert result.error == "invalid_armory"

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

    def test_fetch_includes_source_attribution(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html><body>Test content</body></html>"
        mock_response.headers.get.return_value = "text/html"
        mock_response.__enter__ = lambda s: s  # type: ignore[reportUnknownLambdaType]
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "hephaistos.agent.web_tools.urllib.request.urlopen",
            return_value=mock_response,
        ):
            result = run_web_fetch("https://example.com/test")

        assert "Source: https://example.com/test" in result
        assert "Test content" in result
        assert "End of fetched content" in result

    def test_fetch_http_error(self):
        with patch(
            "hephaistos.agent.web_tools.urllib.request.urlopen",
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
        mock_response.__enter__ = lambda s: s  # type: ignore[reportUnknownLambdaType]
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "hephaistos.agent.web_tools.urllib.request.urlopen",
            return_value=mock_response,
        ):
            result = run_web_fetch("https://example.com/image.png")
            assert "non-text content" in result


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_web_fetch_schema_exists(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "web_fetch" in names

    def test_armory_tool_schemas_exist(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "create_armory" in names
        assert "validate_armory" in names
        assert "search_materials" in names
        assert "open_material" in names

    def test_web_fetch_handler_registered(self):
        handler = get_handler("web_fetch")
        assert handler is not None

    def test_armory_handlers_registered(self):
        assert get_handler("create_armory") is not None
        assert get_handler("validate_armory") is not None
        assert get_handler("search_materials") is not None
        assert get_handler("open_material") is not None

    def test_all_schemas_have_required_fields(self):
        for schema in TOOL_SCHEMAS:
            assert "type" in schema
            assert "function" in schema
            fn = schema["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
