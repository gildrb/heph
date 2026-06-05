"""Tests for the structured logging and diagnostics module."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import pytest
from hephaion.logging import (
    Timer,
    TraceWriter,
    _JsonFormatter,
    _TextFormatter,
    get_logger,
    redact_text,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def trace_dir(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    armory.mkdir()
    (armory / ".hephaion").mkdir()
    return armory


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------


class TestJsonFormatter:
    def test_basic_message(self) -> None:
        fmt = _JsonFormatter()
        record = logging.LogRecord(
            name="hephaion.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert data["msg"] == "hello world"
        assert data["level"] == "INFO"
        assert data["logger"] == "hephaion.test"
        assert "ts" in data

    def test_structured_fields(self) -> None:
        fmt = _JsonFormatter()
        record = logging.LogRecord(
            name="hephaion.test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="test event",
            args=(),
            exc_info=None,
        )
        record.fields = {"model": "gpt-4o", "latency_ms": 123.4}
        output = fmt.format(record)
        data = json.loads(output)
        assert data["model"] == "gpt-4o"
        assert data["latency_ms"] == 123.4

    def test_redacts_openrouter_key_in_text(self) -> None:
        value = "provider key sk-or-v1-" + "a" * 32

        output = redact_text(value)

        assert "sk-or-v1-" not in output
        assert "***REDACTED***" in output

    def test_exception_info(self) -> None:
        fmt = _JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="hephaion.test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert "exc" in data
        assert "ValueError: boom" in data["exc"]


# ---------------------------------------------------------------------------
# TextFormatter
# ---------------------------------------------------------------------------


class TestTextFormatter:
    def test_basic_message(self) -> None:
        fmt = _TextFormatter()
        record = logging.LogRecord(
            name="hephaion.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "hello" in output
        assert "INFO" in output

    def test_fields_on_separate_lines(self) -> None:
        fmt = _TextFormatter()
        record = logging.LogRecord(
            name="hephaion.test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="event",
            args=(),
            exc_info=None,
        )
        record.fields = {"key": "val"}
        output = fmt.format(record)
        assert "key=val" in output


# ---------------------------------------------------------------------------
# get_logger / _ensure_root
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger(self) -> None:
        log = get_logger("test.module")
        assert isinstance(log, logging.Logger)
        assert log.name == "hephaion.test.module"

    def test_prepends_namespace(self) -> None:
        log = get_logger("hephaion.custom")
        assert log.name == "hephaion.custom"

    def test_stderr_handler_added(self) -> None:
        get_logger("test")
        hephaion_logger = logging.getLogger("hephaion")
        assert len(hephaion_logger.handlers) >= 1
        assert isinstance(hephaion_logger.handlers[0], logging.StreamHandler)
        assert hephaion_logger.propagate is False

    def test_file_handler_when_env_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        log_file = tmp_path / "test.log"
        monkeypatch.setenv("HEPHAION_LOG_FILE", str(log_file))
        get_logger("test")
        hephaion_logger = logging.getLogger("hephaion")
        assert any(isinstance(h, logging.FileHandler) for h in hephaion_logger.handlers)

    def test_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAION_LOG_LEVEL", "DEBUG")
        get_logger("test")
        hephaion_logger = logging.getLogger("hephaion")
        assert hephaion_logger.level == logging.DEBUG

    def test_text_format_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAION_LOG_FORMAT", "text")
        get_logger("test")
        hephaion_logger = logging.getLogger("hephaion")
        assert isinstance(hephaion_logger.handlers[0].formatter, _TextFormatter)

    def test_json_format_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HEPHAION_LOG_FORMAT", raising=False)
        get_logger("test")
        hephaion_logger = logging.getLogger("hephaion")
        assert isinstance(hephaion_logger.handlers[0].formatter, _JsonFormatter)

    def test_file_logging(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        log_file = tmp_path / "output.log"
        monkeypatch.setenv("HEPHAION_LOG_FILE", str(log_file))
        monkeypatch.setenv("HEPHAION_LOG_LEVEL", "DEBUG")
        log = get_logger("test.file")
        log.info("test message", extra={"fields": {"key": "value"}})

        content = log_file.read_text()
        assert "test message" in content
        data = json.loads(content.strip())
        assert data["key"] == "value"


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


class TestTimer:
    def test_basic_timing(self) -> None:
        with Timer() as t:
            time.sleep(0.01)
        assert t.ms > 0

    def test_zero_work(self) -> None:
        with Timer() as t:
            pass
        # Should be very small but non-negative
        assert t.ms >= 0

    def test_context_manager_returns_self(self) -> None:
        with Timer() as t:
            assert isinstance(t, Timer)


# ---------------------------------------------------------------------------
# TraceWriter
# ---------------------------------------------------------------------------


class TestTraceWriter:
    def test_no_armory_no_file(self) -> None:
        tw = TraceWriter("sess1", armory_path=None)
        assert tw.path is None
        # Should not raise
        tw.record_user_message("hello")

    def test_creates_trace_file(self, trace_dir: Path) -> None:
        tw = TraceWriter("sess1", armory_path=trace_dir)
        tw.record_user_message("hello world")
        tw.close()

        trace_path = trace_dir / ".hephaion" / "traces" / "sess1.jsonl"
        assert trace_path.exists()
        lines = trace_path.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["type"] == "user_message"
        assert data["content"] == "hello world"
        assert "ts" in data

    def test_record_rag_retrieve(self, trace_dir: Path) -> None:
        tw = TraceWriter("sess6", armory_path=trace_dir)
        tw.record_rag_retrieve(
            query="what is async await?",
            top_k=5,
            retrieved=3,
            scores=[0.95, 0.82, 0.71],
            latency_ms=120.3,
            chunks=[
                {
                    "ref": "materials/notes.md#chunk=0",
                    "score": 0.95,
                    "text_excerpt": "async await suspends work without blocking the thread",
                }
            ],
        )
        tw.close()

        data = json.loads((trace_dir / ".hephaion" / "traces" / "sess6.jsonl").read_text().strip())
        assert data["type"] == "rag_retrieve"
        assert data["retrieved"] == 3
        assert data["scores"] == [0.95, 0.82, 0.71]
        assert data["chunks"][0]["ref"] == "materials/notes.md#chunk=0"
        assert "async await" in data["chunks"][0]["text_excerpt"]

    def test_record_rag_retrieve_redacts_nested_chunk_secrets(self, trace_dir: Path) -> None:
        tw = TraceWriter("sess6-secret", armory_path=trace_dir)
        tw.record_rag_retrieve(
            query="secret",
            top_k=1,
            retrieved=1,
            scores=[1.0],
            latency_ms=1.0,
            chunks=[
                {
                    "ref": "materials/secrets.md#chunk=0",
                    "text_excerpt": "AWS key AKIAIOSFODNN7EXAMPLE should not persist",
                }
            ],
        )
        tw.close()

        raw = (trace_dir / ".hephaion" / "traces" / "sess6-secret.jsonl").read_text()
        assert "AKIAIOSFODNN7EXAMPLE" not in raw
        assert "***REDACTED***" in raw

    def test_record_session_event(self, trace_dir: Path) -> None:
        tw = TraceWriter("sess7", armory_path=trace_dir)
        tw.record_session_event("created", model="glm-5")
        tw.record_session_event("saved", path="/tmp/save.json")
        tw.close()

        lines = (
            (trace_dir / ".hephaion" / "traces" / "sess7.jsonl").read_text().strip().split("\n")
        )
        assert len(lines) == 2
        assert json.loads(lines[0])["event"] == "created"
        assert json.loads(lines[1])["event"] == "saved"

    def test_append_mode(self, trace_dir: Path) -> None:
        # First write
        tw = TraceWriter("sess8", armory_path=trace_dir)
        tw.record_user_message("first")
        tw.close()

        # Second write (append)
        tw2 = TraceWriter("sess8", armory_path=trace_dir)
        tw2.record_user_message("second")
        tw2.close()

        lines = (
            (trace_dir / ".hephaion" / "traces" / "sess8.jsonl").read_text().strip().split("\n")
        )
        assert len(lines) == 2
        assert json.loads(lines[0])["content"] == "first"
        assert json.loads(lines[1])["content"] == "second"

    def test_close_idempotent(self, trace_dir: Path) -> None:
        tw = TraceWriter("sess9", armory_path=trace_dir)
        tw.record_user_message("hello")
        tw.close()
        tw.close()  # Should not raise


# ---------------------------------------------------------------------------
# Integration: structured logging round-trip
# ---------------------------------------------------------------------------


class TestLoggingIntegration:
    def test_structured_log_roundtrip(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        log_file = tmp_path / "integration.log"
        monkeypatch.setenv("HEPHAION_LOG_FILE", str(log_file))
        monkeypatch.setenv("HEPHAION_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("HEPHAION_LOG_FORMAT", "json")

        log = get_logger("integration")
        log.info(
            "llm request sent",
            extra={
                "fields": {
                    "model": "glm-5",
                    "tokens": 120,
                    "latency_ms": 340,
                }
            },
        )

        data = json.loads(log_file.read_text().strip())
        assert data["msg"] == "llm request sent"
        assert data["model"] == "glm-5"
        assert data["tokens"] == 120
        assert data["latency_ms"] == 340
        assert data["level"] == "INFO"

    def test_multiple_loggers_share_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAION_LOG_LEVEL", "DEBUG")
        get_logger("module1")
        get_logger("module2")
        hephaion_logger = logging.getLogger("hephaion")
        # Both share the same root handler
        assert len(hephaion_logger.handlers) == 1  # only stderr, no file
