"""Tests for the structured logging and diagnostics module."""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Generator
from pathlib import Path

import ai.logging as logging_module
import pytest
from ai.logging import (
    Timer,
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
    (armory / ".harness").mkdir()
    return armory


@pytest.fixture(autouse=True)
def reset_harness_logger(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Keep env-driven logger initialization isolated between tests."""
    for env_name in ("HARNESS_LOG_FILE", "HARNESS_LOG_LEVEL", "HARNESS_LOG_FORMAT"):
        monkeypatch.delenv(env_name, raising=False)

    logger = logging.getLogger("harness")
    previous_handlers = list(logger.handlers)
    previous_level = logger.level
    previous_propagate = logger.propagate
    for handler in previous_handlers:
        logger.removeHandler(handler)
    logging_module._harness_logger_initialised = False

    try:
        yield
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        for handler in previous_handlers:
            logger.addHandler(handler)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
        logging_module._harness_logger_initialised = False


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------


class TestJsonFormatter:
    def test_basic_message(self) -> None:
        fmt = _JsonFormatter()
        record = logging.LogRecord(
            name="harness.test",
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
        assert data["logger"] == "harness.test"
        assert "ts" in data

    def test_structured_fields(self) -> None:
        fmt = _JsonFormatter()
        record = logging.LogRecord(
            name="harness.test",
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
            name="harness.test",
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
            name="harness.test",
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
            name="harness.test",
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
        assert log.name == "harness.test.module"

    def test_prepends_namespace(self) -> None:
        log = get_logger("harness.custom")
        assert log.name == "harness.custom"

    def test_stderr_handler_added(self) -> None:
        get_logger("test")
        harness_logger = logging.getLogger("harness")
        assert len(harness_logger.handlers) >= 1
        assert isinstance(harness_logger.handlers[0], logging.StreamHandler)
        assert harness_logger.propagate is False

    def test_file_handler_when_env_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        log_file = tmp_path / "test.log"
        monkeypatch.setenv("HARNESS_LOG_FILE", str(log_file))
        get_logger("test")
        harness_logger = logging.getLogger("harness")
        assert any(isinstance(h, logging.FileHandler) for h in harness_logger.handlers)

    def test_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HARNESS_LOG_LEVEL", "DEBUG")
        get_logger("test")
        harness_logger = logging.getLogger("harness")
        assert harness_logger.level == logging.DEBUG

    def test_text_format_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HARNESS_LOG_FORMAT", "text")
        get_logger("test")
        harness_logger = logging.getLogger("harness")
        assert isinstance(harness_logger.handlers[0].formatter, _TextFormatter)

    def test_json_format_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HARNESS_LOG_FORMAT", raising=False)
        get_logger("test")
        harness_logger = logging.getLogger("harness")
        assert isinstance(harness_logger.handlers[0].formatter, _JsonFormatter)

    def test_file_logging(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        log_file = tmp_path / "output.log"
        monkeypatch.setenv("HARNESS_LOG_FILE", str(log_file))
        monkeypatch.setenv("HARNESS_LOG_LEVEL", "DEBUG")
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
# Integration: structured logging round-trip
# ---------------------------------------------------------------------------


class TestLoggingIntegration:
    def test_structured_log_roundtrip(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        log_file = tmp_path / "integration.log"
        monkeypatch.setenv("HARNESS_LOG_FILE", str(log_file))
        monkeypatch.setenv("HARNESS_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("HARNESS_LOG_FORMAT", "json")

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
        monkeypatch.setenv("HARNESS_LOG_LEVEL", "DEBUG")
        get_logger("module1")
        get_logger("module2")
        harness_logger = logging.getLogger("harness")
        # Both share the same root handler
        assert len(harness_logger.handlers) == 1  # only stderr, no file
