"""Workspace path safety helpers for agent tools."""

from __future__ import annotations

import os
from pathlib import Path


def safe_path(workspace: Path, rel_path: str) -> Path:
    try:
        resolved = (workspace / rel_path).resolve()
        workspace_resolved = workspace.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Path cannot be resolved: {rel_path}") from exc
    if not resolved.is_relative_to(workspace_resolved):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved


def prepare_write_target(workspace: Path, path: str) -> Path | str:
    try:
        workspace_resolved = workspace.resolve()
        target = Path(os.path.normpath(str(workspace_resolved / path)))
        if not target.is_relative_to(workspace_resolved):
            raise ValueError(f"Path escapes workspace: {path}")
        if not target.resolve().is_relative_to(workspace_resolved):
            raise ValueError(f"Path escapes workspace: {path}")
    except (OSError, RuntimeError, ValueError) as exc:
        return str(exc)
    parent_error = _ensure_workspace_parent(workspace, target.parent)
    return parent_error or target


def write_text_no_follow(target: Path, content: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(target), flags, 0o666)
    try:
        file = os.fdopen(fd, "w", encoding="utf-8")
    except Exception:
        os.close(fd)
        raise
    with file:
        file.write(content)


def _ensure_workspace_parent(workspace: Path, parent: Path) -> str:
    workspace_resolved = workspace.resolve()
    try:
        relative_parent = parent.relative_to(workspace_resolved)
    except ValueError:
        return "Error: parent directory escapes workspace"

    current = workspace_resolved
    for part in relative_parent.parts:
        current /= part
        if not _ensure_workspace_directory(current, workspace_resolved):
            return "Error: parent directory escapes workspace"
    return ""


def _ensure_workspace_directory(path: Path, workspace: Path) -> bool:
    try:
        path.mkdir()
    except FileExistsError:
        pass
    except (OSError, RuntimeError):
        return False
    if path.is_symlink() or not path.is_dir():
        return False
    try:
        return path.resolve(strict=True).is_relative_to(workspace)
    except OSError:
        return False
