"""File mutation queue: serializes concurrent write/edit operations.

When the agent makes multiple tool calls in a single turn (e.g. edit_file
on the same file, or write_file while another write is in progress), this
queue ensures operations execute sequentially per-file to prevent race
conditions and data corruption.

The queue is per-workspace and thread-safe.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from ai.logging import Timer, get_logger

MutationFn = Callable[..., str]
_log = get_logger("harness.agent.mutation_queue")


class FileMutationQueue:
    """Serializes file write/edit operations to prevent races.

    Each file path gets its own lock, so independent files can be
    mutated in parallel while same-file operations are serialized.
    """

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()
        self._pending: int = 0
        self._pending_lock = threading.Lock()

    def execute(
        self,
        path: Path,
        fn: MutationFn,
        **kwargs: object,
    ) -> str:
        key = str(path.resolve())
        with self._global_lock:
            lock = self._locks[key]

        with self._pending_lock:
            self._pending += 1

        timer = Timer()
        try:
            with lock, timer:
                result = fn(**kwargs)
        except Exception as exc:
            result = f"Error: {exc}"
            _log.error(
                "mutation failed",
                extra={
                    "fields": {
                        "path": str(path),
                        "latency_ms": timer.ms,
                        "error": str(exc),
                    }
                },
            )
        finally:
            with self._pending_lock:
                self._pending -= 1

        _log.info(
            "mutation complete",
            extra={
                "fields": {
                    "path": str(path),
                    "latency_ms": round(timer.ms, 1),
                    "result_len": len(result),
                    "pending": self._pending,
                }
            },
        )
        return result

    def clear(self) -> None:
        with self._global_lock:
            self._locks.clear()


_queues: dict[str, FileMutationQueue] = {}
_queues_lock = threading.Lock()


def get_queue(workspace: Path) -> FileMutationQueue:
    key = str(workspace.resolve())
    with _queues_lock:
        if key not in _queues:
            _queues[key] = FileMutationQueue()
        return _queues[key]
