"""Structured logging and observability for Hephaistos.

Provides:
- ``get_logger(name)`` — returns a logger that emits structured JSON to
  stderr and (optionally) a log file.
- ``TraceWriter`` — per-session request/response trace files stored inside
  the armory's ``.hephaistos/traces/`` directory.

Configuration (environment variables):
    HEPHAISTOS_LOG_LEVEL  — DEBUG, INFO, WARNING, ERROR (default: WARNING)
    HEPHAISTOS_LOG_FILE   — Path to a log file (append mode). Disabled if unset.
    HEPHAISTOS_LOG_FORMAT — "json" (default) or "text" for human-readable output.

The default level is WARNING so the CLI is silent in production unless the
user opts in.  Library code should use ``DEBUG`` for verbose diagnostics
and ``INFO`` for notable events (LLM request, tool call, index build).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Self

from hephaistos.app.palette import (
    FORGE_EMBER,
    FORGE_IRON,
    FORGE_SMOKE,
    ansi_fg,
)


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
            entry.update(fields)
        if record.exc_info and record.exc_info[1] is not None:
            entry["exc"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str, ensure_ascii=False)


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
            for k, v in fields.items():
                parts.append(f"  {self._DIM}{k}={v}{self._RESET}")

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

    level_name = os.environ.get(_LOG_LEVEL_ENV, "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    fmt = os.environ.get(_LOG_FORMAT_ENV, "json").lower()

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
    def seconds(self) -> float:
        return self._end - self._start

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
        line = json.dumps(event, default=str, ensure_ascii=False)
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

    def record_llm_request(
        self,
        *,
        model: str,
        latency_ms: float,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        finish_reason: str | None = None,
        error: str | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "type": "llm_request",
            "ts": self._ts(),
            "model": model,
            "latency_ms": round(latency_ms, 1),
        }
        if prompt_tokens is not None:
            event["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            event["completion_tokens"] = completion_tokens
        if finish_reason is not None:
            event["finish_reason"] = finish_reason
        if error is not None:
            event["error"] = error
        self._write(event)

    def record_tool_call(
        self,
        *,
        tool: str,
        args: dict[str, Any],
        result: str,
        latency_ms: float,
        error: str | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "type": "tool_call",
            "ts": self._ts(),
            "tool": tool,
            "args": args,
            "result_preview": result[:500],
            "latency_ms": round(latency_ms, 1),
        }
        if error is not None:
            event["error"] = error
        self._write(event)

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


logger = get_logger("hephaistos")
