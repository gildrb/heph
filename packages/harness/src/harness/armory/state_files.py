"""No-follow filesystem helpers for armory-local state files."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path

STATE_DIR_MODE = 0o700
STATE_FILE_MODE = 0o600
_INTERNAL_ROOT = ".harness"


class ArmoryStateError(OSError):
    pass


def armory_state_location(path: Path) -> tuple[Path, Path]:
    parts = path.parts
    internal_indices = tuple(index for index, part in enumerate(parts) if part == _INTERNAL_ROOT)
    if not internal_indices:
        raise ArmoryStateError(f"armory state path must live under {_INTERNAL_ROOT}: {path}")
    internal_index = internal_indices[-1]
    armory_parts = parts[:internal_index]
    armory_path = Path(*armory_parts) if armory_parts else Path()
    return armory_path, Path(*parts[internal_index:])


def ensure_armory_state_dir(
    armory_path: Path,
    rel_path: str | Path,
    *,
    mode: int = STATE_DIR_MODE,
) -> Path:
    rel = _state_rel_path(rel_path)
    root = _resolved_armory_root(armory_path, create=True)
    return _ensure_state_directory(root, rel, create=True, mode=mode)


def read_armory_state_text(
    armory_path: Path,
    rel_path: str | Path,
    *,
    encoding: str = "utf-8",
) -> str:
    target = _state_target(armory_path, rel_path, create_parent=False)
    flags = os.O_RDONLY | _no_follow_flag()
    fd = os.open(str(target), flags)
    with os.fdopen(fd, "r", encoding=encoding) as file:
        return file.read()


def write_armory_state_text(
    armory_path: Path,
    rel_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: int = STATE_FILE_MODE,
) -> Path:
    target = _state_target(armory_path, rel_path, create_parent=True)
    _atomic_write_state_file(target, content, encoding=encoding, mode=mode)
    return target


def create_armory_state_text(
    armory_path: Path,
    rel_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: int = STATE_FILE_MODE,
) -> Path | None:
    target = _state_target(armory_path, rel_path, create_parent=True)
    try:
        _write_state_file(
            target,
            content,
            encoding=encoding,
            mode=mode,
            flags=os.O_EXCL,
            text_mode="w",
        )
    except FileExistsError:
        return None
    return target


def append_armory_state_text(
    armory_path: Path,
    rel_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: int = STATE_FILE_MODE,
) -> Path:
    target = _state_target(armory_path, rel_path, create_parent=True)
    _write_state_file(
        target,
        content,
        encoding=encoding,
        mode=mode,
        flags=os.O_APPEND,
        text_mode="a",
    )
    return target


def _atomic_write_state_file(target: Path, content: str, *, encoding: str, mode: int) -> None:
    """Replace a state file only after the complete payload reaches disk."""
    if target.is_symlink():
        raise ArmoryStateError(f"armory state file must not be a symlink: {target}")
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary_path = Path(temporary)
    try:
        try:
            os.fchmod(fd, mode)
        except AttributeError:
            temporary_path.chmod(mode)
        with os.fdopen(fd, "w", encoding=encoding) as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, target)
        try:
            directory_fd = os.open(str(target.parent), os.O_RDONLY)
        except OSError:
            pass
        else:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except Exception:
        with suppress(OSError):
            os.close(fd)
        temporary_path.unlink(missing_ok=True)
        raise


def _write_state_file(
    target: Path,
    content: str,
    *,
    encoding: str,
    mode: int,
    flags: int,
    text_mode: str,
) -> None:
    if target.is_symlink():
        raise ArmoryStateError(f"armory state file must not be a symlink: {target}")
    open_flags = os.O_WRONLY | os.O_CREAT | flags | _no_follow_flag()
    fd = os.open(str(target), open_flags, mode)
    try:
        _set_state_file_mode(fd, target, mode)
        file = os.fdopen(fd, text_mode, encoding=encoding)
    except Exception:
        os.close(fd)
        raise
    with file:
        file.write(content)


def _set_state_file_mode(fd: int, target: Path, mode: int) -> None:
    try:
        os.fchmod(fd, mode)
    except AttributeError:
        target.chmod(mode)


def _state_target(armory_path: Path, rel_path: str | Path, *, create_parent: bool) -> Path:
    rel = _state_rel_path(rel_path)
    parent = _ensure_state_directory(
        _resolved_armory_root(armory_path, create=create_parent),
        rel.parent,
        create=create_parent,
        mode=STATE_DIR_MODE,
    )
    target = parent / rel.name
    if target.is_symlink():
        raise ArmoryStateError(f"armory state file must not be a symlink: {target}")
    return target


def _state_rel_path(rel_path: str | Path) -> Path:
    rel = Path(rel_path)
    if rel.is_absolute():
        raise ArmoryStateError(f"armory state path must be relative: {rel_path}")
    parts = rel.parts
    if not parts or parts[0] != _INTERNAL_ROOT or any(part == ".." for part in parts):
        raise ArmoryStateError(f"armory state path must stay under {_INTERNAL_ROOT}: {rel_path}")
    return rel


def _resolved_armory_root(armory_path: Path, *, create: bool) -> Path:
    if create:
        with suppress(FileExistsError):
            armory_path.mkdir(mode=STATE_DIR_MODE, parents=True)
    try:
        root = armory_path.resolve(strict=True)
    except OSError as exc:
        raise ArmoryStateError(f"armory path cannot be resolved: {armory_path}") from exc
    if not root.is_dir():
        raise ArmoryStateError(f"armory path is not a directory: {armory_path}")
    return root


def _ensure_state_directory(
    root: Path,
    rel_path: Path,
    *,
    create: bool,
    mode: int,
) -> Path:
    current = root
    for part in rel_path.parts:
        current /= part
        _ensure_directory(current, root, create=create, mode=mode)
    return current


def _ensure_directory(path: Path, root: Path, *, create: bool, mode: int) -> None:
    if path.is_symlink():
        raise ArmoryStateError(f"armory state directory must not be a symlink: {path}")
    if create:
        with suppress(FileExistsError):
            path.mkdir(mode=mode)
    elif not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise ArmoryStateError(f"armory state path is not a directory: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ArmoryStateError(f"armory state directory cannot be resolved: {path}") from exc
    if not resolved.is_relative_to(root):
        raise ArmoryStateError(f"armory state directory escapes armory: {path}")
    with suppress(OSError):
        path.chmod(mode)


def _no_follow_flag() -> int:
    return getattr(os, "O_NOFOLLOW", 0)
