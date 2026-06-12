"""Thread-aware file chunk timeout helpers for RAG indexing."""

from __future__ import annotations

import multiprocessing
import multiprocessing.reduction
import signal
import threading
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Protocol, cast

from hephaion.rag.chunker import ChunkedDocument, ChunkStrategy


class ChunkFileFn(Protocol):
    def __call__(
        self,
        path: Path,
        armory_root: Path,
        chunk_size: int,
        overlap: int,
        *,
        strategy: ChunkStrategy,
    ) -> ChunkedDocument | None: ...


type _ProcessPayload = tuple[str, ChunkedDocument | None | Exception]


class _IndexFileTimeoutError(TimeoutError):
    pass


def chunk_file_with_timeout(
    file_path: Path,
    armory_path: Path,
    *,
    strategy: ChunkStrategy,
    timeout_seconds: int,
    chunk_size: int,
    overlap: int,
    chunk_file_fn: ChunkFileFn,
) -> tuple[ChunkedDocument | None, bool]:
    if timeout_seconds <= 0:
        return (
            chunk_file_fn(
                file_path,
                armory_path,
                chunk_size,
                overlap,
                strategy=strategy,
            ),
            False,
        )

    # SDK operation streams run indexing outside the main thread; Python signals do not.
    if threading.current_thread() is not threading.main_thread():
        return _chunk_file_with_process_timeout(
            file_path,
            armory_path,
            strategy=strategy,
            timeout_seconds=timeout_seconds,
            chunk_size=chunk_size,
            overlap=overlap,
            chunk_file_fn=chunk_file_fn,
        )

    return _chunk_file_with_signal_timeout(
        file_path,
        armory_path,
        strategy=strategy,
        timeout_seconds=timeout_seconds,
        chunk_size=chunk_size,
        overlap=overlap,
        chunk_file_fn=chunk_file_fn,
    )


def _chunk_file_with_signal_timeout(
    file_path: Path,
    armory_path: Path,
    *,
    strategy: ChunkStrategy,
    timeout_seconds: int,
    chunk_size: int,
    overlap: int,
    chunk_file_fn: ChunkFileFn,
) -> tuple[ChunkedDocument | None, bool]:
    timed_out = False
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _handle_timeout(_signum: int, _frame: object) -> None:
        nonlocal timed_out
        timed_out = True
        raise _IndexFileTimeoutError(
            f"document conversion timed out after {timeout_seconds} second(s)"
        )

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(timeout_seconds)
    try:
        document = chunk_file_fn(
            file_path,
            armory_path,
            chunk_size,
            overlap,
            strategy=strategy,
        )
    except _IndexFileTimeoutError:
        document = None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
    return document, timed_out


def _chunk_file_with_process_timeout(
    file_path: Path,
    armory_path: Path,
    *,
    strategy: ChunkStrategy,
    timeout_seconds: int,
    chunk_size: int,
    overlap: int,
    chunk_file_fn: ChunkFileFn,
) -> tuple[ChunkedDocument | None, bool]:
    context = _process_context(chunk_file_fn)
    parent, child = context.Pipe(duplex=False)
    process = context.Process(  # ty:ignore[unresolved-attribute]
        target=_convert_chunk_file_in_process,
        args=(
            child,
            file_path,
            armory_path,
            strategy,
            chunk_size,
            overlap,
            chunk_file_fn,
        ),
        name="heph-rag-chunk-timeout",
    )
    process.start()
    child.close()
    try:
        if not parent.poll(timeout_seconds):
            _terminate_process(process)
            return None, True
        status, payload = cast("_ProcessPayload", parent.recv())
    except EOFError as exc:
        raise RuntimeError("document conversion process exited without a result") from exc
    finally:
        parent.close()
    process.join(timeout=1.0)
    if process.is_alive():
        _terminate_process(process)
    if status == "error":
        if isinstance(payload, Exception):
            raise payload
        raise RuntimeError(str(payload))
    return payload if isinstance(payload, ChunkedDocument) else None, False


def _process_context(chunk_file_fn: ChunkFileFn) -> multiprocessing.context.BaseContext:
    methods = multiprocessing.get_all_start_methods()
    if _can_pickle(chunk_file_fn):
        if "forkserver" in methods:
            return multiprocessing.get_context("forkserver")
        if "spawn" in methods:
            return multiprocessing.get_context("spawn")
    if "fork" in methods:
        return multiprocessing.get_context("fork")
    return multiprocessing.get_context()


def _convert_chunk_file_in_process(
    connection: Connection,
    file_path: Path,
    armory_path: Path,
    strategy: ChunkStrategy,
    chunk_size: int,
    overlap: int,
    chunk_file_fn: ChunkFileFn,
) -> None:
    try:
        document = chunk_file_fn(
            file_path,
            armory_path,
            chunk_size,
            overlap,
            strategy=strategy,
        )
    except Exception as exc:
        payload: _ProcessPayload = ("error", _pickleable_exception(exc))
    else:
        payload = ("ok", document)
    connection.send(payload)
    connection.close()


def _pickleable_exception(exc: Exception) -> Exception:
    if not _can_pickle(exc):
        return RuntimeError(str(exc))
    return exc


def _can_pickle(value: object) -> bool:
    try:
        multiprocessing.reduction.ForkingPickler.dumps(value)
    except Exception:
        return False
    return True


def _terminate_process(process: multiprocessing.Process) -> None:
    process.terminate()
    process.join(timeout=1.0)
    if process.is_alive():
        process.kill()
        process.join()
