"""No-follow material file reads for RAG indexing."""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import BinaryIO

_READ_BYTES = 1024 * 1024


def open_regular_file_fd(path: Path, *, root: Path | None = None) -> int | None:
    if root is not None:
        return _open_regular_file_fd_under_root(path, root)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        return None
    return _regular_fd_or_none(fd)


def _open_regular_file_fd_under_root(path: Path, root: Path) -> int | None:
    rel_parts = _relative_parts_under_root(path, root)
    if not rel_parts:
        return None
    current_fd: int | None = None
    try:
        current_fd = os.open(root, _directory_flags())
        for part in rel_parts[:-1]:
            next_fd = os.open(part, _directory_flags(), dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        fd = os.open(
            rel_parts[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=current_fd,
        )
    except (OSError, TypeError, ValueError):
        return None
    finally:
        if current_fd is not None:
            with contextlib.suppress(OSError):
                os.close(current_fd)
    return _regular_fd_or_none(fd)


def _relative_parts_under_root(path: Path, root: Path) -> tuple[str, ...] | None:
    try:
        rel = _absolute_lexical_path(path).relative_to(_absolute_lexical_path(root))
    except ValueError:
        return None
    if not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        return None
    return tuple(rel.parts)


def _absolute_lexical_path(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _directory_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _regular_fd_or_none(fd: int) -> int | None:
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            return None
    except OSError:
        os.close(fd)
        return None
    return fd


@contextlib.contextmanager
def regular_file_reader(path: Path, *, root: Path | None = None) -> Iterator[BinaryIO | None]:
    fd = open_regular_file_fd(path, root=root)
    if fd is None:
        yield None
        return
    with os.fdopen(fd, "rb") as file:
        yield file


def open_file_exceeds_limit(file: BinaryIO, limit: int) -> bool:
    try:
        return os.fstat(file.fileno()).st_size > limit
    except OSError:
        return True


@contextlib.contextmanager
def temporary_regular_file_copy(
    path: Path,
    *,
    root: Path | None = None,
    max_bytes: int,
    on_limit_exceeded: Callable[[], None] | None = None,
) -> Iterator[Path | None]:
    with regular_file_reader(path, root=root) as source:
        if source is None:
            yield None
            return
        if open_file_exceeds_limit(source, max_bytes):
            if on_limit_exceeded is not None:
                on_limit_exceeded()
            yield None
            return
        fd, raw_temp_path = tempfile.mkstemp(suffix=path.suffix)
        temp_path = Path(raw_temp_path)
        try:
            with os.fdopen(fd, "wb") as target:
                shutil.copyfileobj(source, target, _READ_BYTES)
            yield temp_path
        finally:
            with contextlib.suppress(OSError):
                temp_path.unlink()


def regular_file_content_hash(
    path: Path,
    *,
    root: Path | None = None,
    max_bytes: int | None = None,
) -> str | None:
    digest = hashlib.sha256()
    with regular_file_reader(path, root=root) as file:
        if file is None:
            return None
        if max_bytes is not None and open_file_exceeds_limit(file, max_bytes):
            return None
        for chunk in iter(lambda: file.read(_READ_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]
