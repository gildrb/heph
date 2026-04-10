"""Tests for the web_fetch tool and structured bash output."""

from __future__ import annotations

import http.client
from unittest.mock import MagicMock, patch

from hephaistos.harness.tools import (
    TOOL_SCHEMAS,
    BashResult,
    get_handler,
    run_bash,
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

    def test_output_truncated(self):
        # Generate very large output
        result = run_bash("python3 -c \"print('x' * 100000)\"")
        assert len(result) <= 50_200  # _MAX_READ_CHARS + margin


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
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("hephaistos.harness.tools.urllib.request.urlopen", return_value=mock_response):
            result = run_web_fetch("https://example.com/test")

        assert "Source: https://example.com/test" in result
        assert "Test content" in result
        assert "End of fetched content" in result

    def test_fetch_http_error(self):
        import urllib.error

        with patch(
            "hephaistos.harness.tools.urllib.request.urlopen",
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

        with patch("hephaistos.harness.tools.urllib.request.urlopen", return_value=mock_response):
            result = run_web_fetch("https://example.com/image.png")
            assert "non-text content" in result


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_web_fetch_schema_exists(self):
        names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        assert "web_fetch" in names

    def test_web_fetch_handler_registered(self):
        handler = get_handler("web_fetch")
        assert handler is not None

    def test_all_schemas_have_required_fields(self):
        for schema in TOOL_SCHEMAS:
            assert "type" in schema
            assert "function" in schema
            fn = schema["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
