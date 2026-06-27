"""Structured logging, redaction, and timers."""

from __future__ import annotations

import json
import logging
import os
import re as _re
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Self

from ai.types import is_object_list, is_string_mapping

_LOG_TEXT_MUTED = "#6F6F6F"
_LOG_ACCENT = "#D06A4A"
_LOG_ERROR = "#FF6B5A"


def _ansi_fg(hex_color: str) -> str:
    color = hex_color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"\033[38;2;{red};{green};{blue}m"


# -- Redaction / scrubbing ---------------------------------------------------

# Patterns for dict keys whose values should always be redacted
_SENSITIVE_KEY_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]

# Unanchored versions - find secrets embedded within longer text
_SENSITIVE_TEXT_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"sk-or-v1-[a-zA-Z0-9\-_]{20,}"),  # OpenRouter API keys
    _re.compile(r"sk-proj-[a-zA-Z0-9\-_]{20,}"),  # OpenAI project API keys
    _re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style API keys
    _re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"),  # Provider API keys
    _re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),  # AWS access keys
    _re.compile(r"AIza[0-9A-Za-z\-_]{35}"),  # Google API keys
    _re.compile(r"ya29\.[0-9A-Za-z\-_]+"),  # Google OAuth tokens
    _re.compile(r"Bearer\s+\S+", _re.IGNORECASE),  # Bearer tokens
    _re.compile(r"\b[a-f0-9]{32,}\b"),  # Long hex strings (potential tokens)
]

_REDACTED = "***REDACTED***"


def redact_text(text: str) -> str:
    if not text:
        return text
    for pattern in _SENSITIVE_TEXT_PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text


def _redact_dict(data: Mapping[str, object]) -> dict[str, object]:
    return {key: _redact_value(key, value) for key, value in data.items()}


def redact_mapping(data: Mapping[str, object]) -> dict[str, object]:
    return _redact_dict(data)


def _redact_value(key: str, value: object) -> object:
    if any(pattern.search(key) for pattern in _SENSITIVE_KEY_PATTERNS):
        return _REDACTED
    return _redact_unkeyed_value(value)


def _redact_unkeyed_value(value: object) -> object:
    if is_string_mapping(value):
        return _redact_dict(value)
    if is_object_list(value):
        return [_redact_unkeyed_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if is_string_mapping(fields):
            entry.update(fields)
        if record.exc_info and record.exc_info[1] is not None:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(_redact_dict(entry), default=str, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    _LEVEL_COLOURS: ClassVar[dict[str, str]] = {
        "DEBUG": _ansi_fg(_LOG_TEXT_MUTED),
        "INFO": _ansi_fg(_LOG_ACCENT),
        "WARNING": _ansi_fg(_LOG_ACCENT),
        "ERROR": _ansi_fg(_LOG_ERROR),
        "CRITICAL": f"\033[1m{_ansi_fg(_LOG_ERROR)}",
    }
    _RESET = "\033[0m"
    _DIM = f"\033[2m{_ansi_fg(_LOG_TEXT_MUTED)}"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        colour = self._LEVEL_COLOURS.get(record.levelname, "")
        level = f"{colour}{record.levelname:<8}{self._RESET}"
        parts = [f"{self._DIM}{ts}{self._RESET} {level} {record.name}: {record.getMessage()}"]
        parts.extend(self._field_lines(record))
        parts.extend(self._exception_lines(record))
        return "\n".join(parts)

    def _field_lines(self, record: logging.LogRecord) -> list[str]:
        fields = getattr(record, "fields", None)
        if not is_string_mapping(fields):
            return []
        return [
            f"  {self._DIM}{key}={value}{self._RESET}"
            for key, value in _redact_dict(fields).items()
        ]

    def _exception_lines(self, record: logging.LogRecord) -> list[str]:
        if record.exc_info and record.exc_info[1] is not None:
            return [self.formatException(record.exc_info)]
        return []


LOG_LEVEL_ENV = "HARNESS_LOG_LEVEL"
LOG_FILE_ENV = "HARNESS_LOG_FILE"
LOG_FORMAT_ENV = "HARNESS_LOG_FORMAT"

_harness_logger_initialised = False


def get_logger(name: str) -> logging.Logger:
    _ensure_harness_logger()
    if not name.startswith("harness"):
        name = f"harness.{name}"
    return logging.getLogger(name)


def _ensure_harness_logger() -> None:
    global _harness_logger_initialised  # noqa: PLW0603
    if _harness_logger_initialised:
        return
    _harness_logger_initialised = True

    level, fmt = _logging_config()
    logger = logging.getLogger("harness")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        logger.addHandler(_stderr_handler(level, fmt))
        if log_file := os.environ.get(LOG_FILE_ENV):
            logger.addHandler(_file_handler(Path(log_file), level))
    _quiet_noisy_loggers()


def _logging_config() -> tuple[int, str]:
    is_tty = sys.stderr.isatty()
    default_level_name = "ERROR" if is_tty else "WARNING"
    default_format = "text" if is_tty else "json"
    level_name = os.environ.get(LOG_LEVEL_ENV, default_level_name).upper()
    return getattr(logging, level_name, logging.WARNING), os.environ.get(
        LOG_FORMAT_ENV,
        default_format,
    ).lower()


def _stderr_handler(level: int, fmt: str) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(_JsonFormatter() if fmt == "json" else _TextFormatter())
    return handler


def _file_handler(path: Path, level: int) -> logging.Handler:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(_JsonFormatter())
    return handler


def _quiet_noisy_loggers() -> None:
    for noisy in ("openai", "httpx", "httpcore", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class Timer:
    __slots__ = ("_end", "_start")

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self._end = time.perf_counter()

    @property
    def ms(self) -> float:
        return (self._end - self._start) * 1000
