"""Structured logging and local diagnostics for Hephaistos.

This module implements **log sanitization** as a security mechanism: all
structured log output and trace files pass through redaction functions that
scrub API keys, Bearer tokens, and other secrets before they are written.
See ``redact_value``, ``redact_text``, and ``_redact_dict``.

Provides:
- ``get_logger(name)`` — returns a logger that emits structured JSON to
  stderr and (optionally) a log file.
- ``TraceWriter`` — per-session request/response trace files stored inside
  the armory's ``.hephaistos/traces/`` directory.
- ``redact_value(value)`` — redact a string value if it matches a known
  secret pattern (for use by other modules).
- ``redact_text(text)`` — redact secrets found embedded within longer text.

Configuration (environment variables):
    HEPHAISTOS_LOG_LEVEL  — DEBUG, INFO, WARNING, ERROR.
                           Defaults to ERROR on interactive TTYs and
                           WARNING otherwise.
    HEPHAISTOS_LOG_FILE   — Path to a log file (append mode). Disabled if unset.
    HEPHAISTOS_LOG_FORMAT — "json" or "text".
                           Defaults to text on interactive TTYs and
                           json otherwise.

Interactive shells should stay readable by default. Library code should use
``DEBUG`` for verbose diagnostics and ``INFO`` for notable events (LLM
request, tool call, index build).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re as _re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Self

from hephaistos.palette import (
    FORGE_EMBER,
    FORGE_IRON,
    FORGE_SMOKE,
    ansi_fg,
)

# -- Redaction / scrubbing ---------------------------------------------------

# Patterns for dict keys whose values should always be redacted
_SENSITIVE_KEY_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]

# Patterns for string values that look like secrets (anchored — value IS the secret)
_SENSITIVE_VALUE_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"^sk-[a-zA-Z0-9]{20,}$"),  # OpenAI-style API keys
    _re.compile(r"^sk-ant-[a-zA-Z0-9\-]{20,}$"),  # Anthropic-style keys
    _re.compile(r"^Bearer\s+\S+$", _re.IGNORECASE),  # Bearer tokens
    _re.compile(r"^[a-f0-9]{32,}$"),  # Long hex strings (potential tokens)
]

# Unanchored versions — find secrets embedded within longer text
_SENSITIVE_TEXT_PATTERNS: list[_re.Pattern[str]] = [
    _re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style API keys
    _re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"),  # Anthropic-style keys
    _re.compile(r"Bearer\s+\S+", _re.IGNORECASE),  # Bearer tokens
    _re.compile(r"\b[a-f0-9]{32,}\b"),  # Long hex strings (potential tokens)
]

_REDACTED = "***REDACTED***"


def _is_sensitive_key(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_KEY_PATTERNS)


def redact_value(value: str) -> str:
    """Redact a string value if it matches a known secret pattern."""
    if any(p.search(value) for p in _SENSITIVE_VALUE_PATTERNS):
        return _REDACTED
    return value


def redact_text(text: str) -> str:
    """Redact secrets found embedded within longer text.

    Unlike :func:`redact_value`, which only matches when the entire value
    is a secret, this function scans for secrets anywhere inside *text*
    and replaces each occurrence with ``***REDACTED***``.
    """
    if not text:
        return text
    for pattern in _SENSITIVE_TEXT_PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *data* with sensitive keys and values redacted."""
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            redacted[key] = _REDACTED
        elif isinstance(value, dict):
            nested: dict[str, Any] = value  # type: ignore[assignment]
            redacted[key] = _redact_dict(nested)
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        else:
            redacted[key] = value
    return redacted


def _get_trace_context() -> dict[str, str]:
    """Return local trace context.

    Remote tracing is intentionally disabled in the open-source CLI build, so
    log records do not carry an external trace ID.
    """
    return {}


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if fields and isinstance(fields, dict):
            typed_fields: dict[str, Any] = fields  # type: ignore[assignment]
            entry.update(_redact_dict(typed_fields))
        if record.exc_info and record.exc_info[1] is not None:
            entry["exc"] = self.formatException(record.exc_info)
        trace_ctx = _get_trace_context()
        if trace_ctx:
            entry.update(trace_ctx)
        return json.dumps(_redact_dict(entry), default=str, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    """Human-readable coloured formatter for development."""

    _LEVEL_COLOURS: ClassVar[dict[str, str]] = {
        "DEBUG": ansi_fg(FORGE_SMOKE),
        "INFO": ansi_fg(FORGE_EMBER),
        "WARNING": ansi_fg(FORGE_EMBER),
        "ERROR": ansi_fg(FORGE_IRON),
        "CRITICAL": f"\033[1m{ansi_fg(FORGE_IRON)}",
    }
    _RESET = "\033[0m"
    _DIM = f"\033[2m{ansi_fg(FORGE_SMOKE)}"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        colour = self._LEVEL_COLOURS.get(record.levelname, "")
        level = f"{colour}{record.levelname:<8}{self._RESET}"
        fields = getattr(record, "fields", None)

        parts = [f"{self._DIM}{ts}{self._RESET} {level} {record.name}: {record.getMessage()}"]
        if fields and isinstance(fields, dict):
            typed_fields: dict[str, Any] = fields  # type: ignore[assignment]
            redacted_fields = _redact_dict(typed_fields)
            for k, v in redacted_fields.items():
                parts.append(f"  {self._DIM}{k}={v}{self._RESET}")

        trace_ctx = _get_trace_context()
        if trace_ctx:
            parts.append(f"  {self._DIM}trace_id={trace_ctx['trace_id'][:16]}…{self._RESET}")

        if record.exc_info and record.exc_info[1] is not None:
            parts.append(self.formatException(record.exc_info))

        return "\n".join(parts)


_LOG_LEVEL_ENV = "HEPHAISTOS_LOG_LEVEL"
_LOG_FILE_ENV = "HEPHAISTOS_LOG_FILE"
_LOG_FORMAT_ENV = "HEPHAISTOS_LOG_FORMAT"

_root_initialised = False


def _ensure_root() -> None:
    """Configure the ``hephaistos`` root logger exactly once."""
    global _root_initialised  # noqa: PLW0603
    if _root_initialised:
        return
    _root_initialised = True

    is_tty = sys.stderr.isatty()
    default_level_name = "ERROR" if is_tty else "WARNING"
    default_format = "text" if is_tty else "json"

    level_name = os.environ.get(_LOG_LEVEL_ENV, default_level_name).upper()
    level = getattr(logging, level_name, logging.WARNING)
    fmt = os.environ.get(_LOG_FORMAT_ENV, default_format).lower()

    root = logging.getLogger("hephaistos")
    root.setLevel(level)
    if root.handlers:
        return
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(_JsonFormatter() if fmt == "json" else _TextFormatter())
    root.addHandler(stderr_handler)
    log_file = os.environ.get(_LOG_FILE_ENV)
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(_JsonFormatter())
        root.addHandler(file_handler)
    for noisy in ("openai", "httpx", "httpcore", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a structured logger under the ``hephaistos`` namespace.

    Usage::

        log = get_logger("chat.engine")
        log.info("llm request sent", extra={"fields": {
            "model": "gpt-4o-mini",
            "tokens": 120,
            "latency_ms": 340,
        }})
    """
    _ensure_root()
    if not name.startswith("hephaistos"):
        name = f"hephaistos.{name}"
    return logging.getLogger(name)


class Timer:
    """Simple wall-clock timer for latency tracking.

    Usage::

        with Timer() as t:
            ...  # do work
        log.info("done", extra={"fields": {"latency_ms": t.ms}})
    """

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
    """Append-only JSON-lines trace file for a single chat session.

    Each line is a self-contained JSON event:
      {"type": "user_message", "ts": "...", "content": "..."}
      {"type": "llm_request", "ts": "...", "model": "...", "latency_ms": 340, ...}
      {"type": "tool_call", "ts": "...", "tool": "bash", "args": {...}, "result": "..."}

    Traces are stored in ``<armory>/.hephaistos/traces/<session_id>.jsonl``.
    """

    def __init__(self, session_id: str, armory_path: Path | None = None) -> None:
        self.session_id = session_id
        self._armory_path = armory_path
        self._path: Path | None = None
        self._file_handle: Any = None
        self._log = get_logger("trace")

    @property
    def path(self) -> Path | None:
        if self._path is None and self._armory_path is not None:
            self._path = (
                self._armory_path / ".hephaistos" / _TRACES_DIR / f"{self.session_id}.jsonl"
            )
        return self._path

    def _ensure_handle(self) -> Any:
        if self._file_handle is not None:
            return self._file_handle
        if self._armory_path is None:
            return None
        p = self.path
        if p is None:
            return None
        p.parent.mkdir(parents=True, exist_ok=True)
        self._file_handle = p.open("a", encoding="utf-8")
        return self._file_handle

    def _write(self, event: dict[str, Any]) -> None:
        fh = self._ensure_handle()
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
    ) -> None:
        self._write(
            {
                "type": "rag_retrieve",
                "ts": self._ts(),
                "query": query[:200],
                "top_k": top_k,
                "retrieved": retrieved,
                "scores": [round(s, 4) for s in scores],
                "latency_ms": round(latency_ms, 1),
            }
        )

    def record_session_event(self, event: str, **details: Any) -> None:
        entry: dict[str, Any] = {
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
