from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Self

from study.priority_types import PriorityProgressReporter

_MODEL_HEARTBEAT_SECONDS = 10.0


def _emit_progress(progress: PriorityProgressReporter | None, message: str) -> None:
    if progress is not None:
        progress(message)


class _ProgressHeartbeat:
    def __init__(
        self,
        progress: PriorityProgressReporter | None,
        message: str,
        *,
        interval_seconds: float = _MODEL_HEARTBEAT_SECONDS,
    ) -> None:
        self._progress = progress
        self._message = message
        self._interval_seconds = interval_seconds
        self._started_at = time.perf_counter()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> Self:
        if self._progress is None:
            return self
        self._thread = threading.Thread(target=self._run, name="priority-progress", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.stop()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.2)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            _emit_progress(
                self._progress,
                f"{self._message} ({_format_elapsed_since(self._started_at)} elapsed).",
            )


def _format_elapsed_since(started_at: float) -> str:
    seconds = max(0.0, time.perf_counter() - started_at)
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.1f}s"


def _write_text_artifact(
    path: Path,
    text: str,
    *,
    progress: PriorityProgressReporter | None,
    label: str,
) -> None:
    started_at = time.perf_counter()
    path.write_text(text, encoding="utf-8")
    _emit_progress(
        progress,
        f"Wrote {label} {path} ({len(text.encode('utf-8'))} bytes) "
        f"in {_format_elapsed_since(started_at)}.",
    )
