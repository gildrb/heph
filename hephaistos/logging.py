"""Structured logging, redaction, and local trace files."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re as _re
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Self, TextIO

from hephaistos._types import is_string_mapping
from hephaistos.terminal.palette import FORGE_THEME, ansi_fg

# -- Redaction / scrubbing ---------------------------------------------------

# Patterns for dict keys whose values should always be redacted
_SENSITIVE_KEY_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]

# Unanchored versions — find secrets embedded within longer text
_SENSITIVE_TEXT_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style API keys
    _re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"),  # Anthropic-style keys
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
    redacted: dict[str, object] = {}
    for key, value in data.items():
        if any(pattern.search(key) for pattern in _SENSITIVE_KEY_PATTERNS):
            redacted[key] = _REDACTED
        elif is_string_mapping(value):
            redacted[key] = _redact_dict(value)
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        else:
            redacted[key] = value
    return redacted


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
        "DEBUG": ansi_fg(FORGE_THEME.text_muted),
        "INFO": ansi_fg(FORGE_THEME.action_primary_bg),
        "WARNING": ansi_fg(FORGE_THEME.action_primary_bg),
        "ERROR": ansi_fg(FORGE_THEME.status_error_text),
        "CRITICAL": f"\033[1m{ansi_fg(FORGE_THEME.status_error_text)}",
    }
    _RESET = "\033[0m"
    _DIM = f"\033[2m{ansi_fg(FORGE_THEME.text_muted)}"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        colour = self._LEVEL_COLOURS.get(record.levelname, "")
        level = f"{colour}{record.levelname:<8}{self._RESET}"
        fields = getattr(record, "fields", None)

        parts = [f"{self._DIM}{ts}{self._RESET} {level} {record.name}: {record.getMessage()}"]
        if is_string_mapping(fields):
            redacted_fields = _redact_dict(fields)
            for k, v in redacted_fields.items():
                parts.append(f"  {self._DIM}{k}={v}{self._RESET}")

        if record.exc_info and record.exc_info[1] is not None:
            parts.append(self.formatException(record.exc_info))

        return "\n".join(parts)


_LOG_LEVEL_ENV = "HEPHAISTOS_LOG_LEVEL"
_LOG_FILE_ENV = "HEPHAISTOS_LOG_FILE"
_LOG_FORMAT_ENV = "HEPHAISTOS_LOG_FORMAT"

_root_initialised = False


def get_logger(name: str) -> logging.Logger:
    global _root_initialised  # noqa: PLW0603
    if not _root_initialised:
        _root_initialised = True

        is_tty = sys.stderr.isatty()
        default_level_name = "ERROR" if is_tty else "WARNING"
        default_format = "text" if is_tty else "json"

        level_name = os.environ.get(_LOG_LEVEL_ENV, default_level_name).upper()
        level = getattr(logging, level_name, logging.WARNING)
        fmt = os.environ.get(_LOG_FORMAT_ENV, default_format).lower()

        hephaistos_logger = logging.getLogger("hephaistos")
        hephaistos_logger.setLevel(level)
        hephaistos_logger.propagate = False
        if not hephaistos_logger.handlers:
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(level)
            stderr_handler.setFormatter(_JsonFormatter() if fmt == "json" else _TextFormatter())
            hephaistos_logger.addHandler(stderr_handler)
            log_file = os.environ.get(_LOG_FILE_ENV)
            if log_file:
                path = Path(log_file)
                path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(path, encoding="utf-8")
                file_handler.setLevel(level)
                file_handler.setFormatter(_JsonFormatter())
                hephaistos_logger.addHandler(file_handler)
        for noisy in ("openai", "httpx", "httpcore", "urllib3", "sentence_transformers"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
    if not name.startswith("hephaistos"):
        name = f"hephaistos.{name}"
    return logging.getLogger(name)


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


_TRACES_DIR = "traces"


class TraceWriter:
    def __init__(self, session_id: str, armory_path: Path | None = None) -> None:
        # Defense-in-depth: reject path traversal in session_id.
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            raise ValueError(f"Invalid session_id: {session_id}")
        self.session_id = session_id
        self._armory_path = armory_path
        self._path: Path | None = None
        self._file_handle: TextIO | None = None
        self._log = get_logger("trace")

    @property
    def path(self) -> Path | None:
        if self._path is None and self._armory_path is not None:
            self._path = (
                self._armory_path / ".hephaistos" / _TRACES_DIR / f"{self.session_id}.jsonl"
            )
        return self._path

    def _write(self, event: Mapping[str, object]) -> None:
        if self._file_handle is None:
            if self._armory_path is None:
                return
            p = self.path
            assert p is not None
            p.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = p.open("a", encoding="utf-8")
        fh = self._file_handle
        if fh is None:
            return
        line = json.dumps(_redact_dict(event), default=str, ensure_ascii=False)
        try:
            fh.write(line + "\n")
            fh.flush()
        except OSError as exc:
            self._log.warning("trace write failed", extra={"fields": {"error": str(exc)}})

    @staticmethod
    def _ts() -> str:
        return datetime.now(UTC).isoformat()

    def record_user_message(self, content: str) -> None:
        self._write({"type": "user_message", "ts": self._ts(), "content": content})

    def record_rag_retrieve(
        self,
        *,
        query: str,
        top_k: int,
        retrieved: int,
        scores: list[float],
        latency_ms: float,
        chunks: list[Mapping[str, object]] | None = None,
    ) -> None:
        event: dict[str, object] = {
            "type": "rag_retrieve",
            "ts": self._ts(),
            "query": query[:200],
            "top_k": top_k,
            "retrieved": retrieved,
            "scores": [round(s, 4) for s in scores],
            "latency_ms": round(latency_ms, 1),
        }
        if chunks is not None:
            event["chunks"] = chunks
        self._write(event)

    def record_material_operation(
        self,
        *,
        operation: str,
        message: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        event: dict[str, object] = {
            "type": "material_operation",
            "ts": self._ts(),
            "operation": operation,
            "message": message,
        }
        if metadata:
            event["metadata"] = dict(metadata)
        self._write(event)

    def record_session_event(self, event: str, **details: object) -> None:
        entry: dict[str, object] = {
            "type": "session",
            "ts": self._ts(),
            "event": event,
        }
        entry.update(details)
        self._write(entry)

    def close(self) -> None:
        if self._file_handle is not None:
            with contextlib.suppress(OSError):
                self._file_handle.close()
            self._file_handle = None
