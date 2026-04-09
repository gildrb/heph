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
from typing import Any

from hephaistos.logging import Timer, get_logger

_log = get_logger("harness.mutation_queue")

# Type for mutation functions: takes kwargs, returns result string
MutationFn = Callable[..., str]


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

    def _get_lock(self, path: Path) -> threading.Lock:
        """Get (or create) a lock for a specific file path."""
        key = str(path.resolve())
        with self._global_lock:
            return self._locks[key]

    def execute(
        self,
        path: Path,
        fn: MutationFn,
        **kwargs: Any,
    ) -> str:
        """Execute a file mutation under a per-file lock.

        Parameters
        ----------
        path :
            The target file path (used as the lock key).
        fn :
            The mutation function to call. Receives **kwargs.
        **kwargs :
            Arguments passed through to fn.

        Returns
        -------
        str
            The result from fn.
        """
        lock = self._get_lock(path)

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
        """Remove all cached locks (for testing / cleanup)."""
        with self._global_lock:
            self._locks.clear()


_queues: dict[str, FileMutationQueue] = {}
_queues_lock = threading.Lock()


def get_queue(workspace: Path) -> FileMutationQueue:
    """Get or create a mutation queue for a workspace."""
    key = str(workspace.resolve())
    with _queues_lock:
        if key not in _queues:
            _queues[key] = FileMutationQueue()
        return _queues[key]
