"""Tests for the file mutation queue (sequential write/edit safety)."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from agent.mutation_queue import FileMutationQueue, get_queue


class TestFileMutationQueue:
    def test_execute_returns_function_result(self) -> None:
        queue = FileMutationQueue()
        result = queue.execute(Path("/tmp/test.txt"), lambda: "hello")
        assert result == "hello"

    def test_execute_passes_kwargs(self) -> None:
        queue = FileMutationQueue()

        def handler(**kwargs: object) -> str:
            return f"{kwargs['file_path']}:{kwargs['content']}"

        result = queue.execute(Path("/tmp/test.txt"), handler, file_path="x", content="data")
        assert result == "x:data"

    def test_execute_catches_exception(self) -> None:
        queue = FileMutationQueue()

        def failing_handler(**_kwargs: object) -> str:
            raise ValueError("disk full")

        result = queue.execute(Path("/tmp/test.txt"), failing_handler)
        assert "Error:" in result
        assert "disk full" in result

    def test_clear_removes_locks(self) -> None:
        queue = FileMutationQueue()
        queue.execute(Path("/tmp/a.txt"), lambda: "a")
        assert len(queue._locks) == 1
        queue.clear()
        assert len(queue._locks) == 0

    def test_same_file_serializes(self) -> None:
        """Two mutations on the same file path must run sequentially."""
        queue = FileMutationQueue()
        order: list[int] = []
        handler_1_entered = threading.Event()
        handler_1_release = threading.Event()

        def handler_1(**_kwargs: object) -> str:
            order.append(1)
            handler_1_entered.set()
            handler_1_release.wait(timeout=5)
            return "r1"

        def handler_2(**_kwargs: object) -> str:
            order.append(2)
            return "r2"

        t1 = threading.Thread(target=lambda: queue.execute(Path("/tmp/serial.txt"), handler_1))
        t2 = threading.Thread(target=lambda: queue.execute(Path("/tmp/serial.txt"), handler_2))
        t1.start()
        handler_1_entered.wait(timeout=5)  # wait until handler_1 is inside
        t2.start()
        # handler_2 should be blocked — only handler_1 should have run so far
        assert order == [1]
        handler_1_release.set()
        t1.join(timeout=5)
        t2.join(timeout=5)

        # handler_1 must complete before handler_2 starts
        assert order == [1, 2]

    @pytest.mark.flaky(reruns=2, reruns_delay=1)
    def test_different_files_parallel(self) -> None:
        """Mutations on different file paths can run in parallel."""
        queue = FileMutationQueue()
        entered = threading.Event()
        release = threading.Event()
        started: list[int] = []

        def slow_handler(**_kwargs: object) -> str:
            started.append(1)
            entered.set()
            release.wait(timeout=5)
            return "ok"

        results: list[str] = []

        t1 = threading.Thread(
            target=lambda: results.append(queue.execute(Path("/tmp/alpha.txt"), slow_handler))
        )
        t2 = threading.Thread(
            target=lambda: results.append(queue.execute(Path("/tmp/beta.txt"), slow_handler))
        )
        t1.start()
        entered.wait(timeout=5)
        t2.start()
        # Both should have started (they ran in parallel on different files)
        time.sleep(0.1)
        assert len(started) == 2
        release.set()
        t1.join(timeout=5)
        t2.join(timeout=5)


class TestGetQueue:
    def test_returns_same_queue_for_same_workspace(self, tmp_path: Path) -> None:
        q1 = get_queue(tmp_path)
        q2 = get_queue(tmp_path)
        assert q1 is q2

    def test_returns_different_queue_for_different_workspaces(self, tmp_path: Path) -> None:
        other = tmp_path / "other"
        other.mkdir()
        q1 = get_queue(tmp_path)
        q2 = get_queue(other)
        assert q1 is not q2
