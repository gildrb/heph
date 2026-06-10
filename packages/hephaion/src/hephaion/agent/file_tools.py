"""Workspace file handlers for agent tools."""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion.agent.mutation_queue import get_queue
from hephaion.agent.path_safety import prepare_write_target, safe_path, write_text_no_follow
from hephaion.agent.tool_schema import ToolHandlerResult, ToolResult
from hephaion.armory.state_files import write_armory_state_text

_MAX_READ_CHARS = 50_000
_MAX_TEXT_FILE_BYTES = 1_000_000
_MAX_SEARCH_RESULTS = 50
_SEARCH_SKIP_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz"})
_BINARY_DOCUMENT_SUFFIXES = frozenset({".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".odt"})
_AGENT_WRITABLE_STATE_PATHS = frozenset({Path(".hephaion/exam_bank.json")})


@dataclass(frozen=True, slots=True)
class FileReadResult:
    text: str
    error: bool = False


@dataclass(frozen=True, slots=True)
class SearchFilesResult:
    file_count: int
    matches: list[str]


def mutation_wrap(fn: Callable[..., str], **kwargs: object) -> str:
    path = kwargs.get("path")
    workspace = kwargs.get("workspace")
    if isinstance(path, str) and isinstance(workspace, Path):
        try:
            target = safe_path(workspace, path)
            queue = get_queue(workspace)
            return queue.execute(target, fn, **kwargs)
        except ValueError:
            pass  # fall through to direct call
    return fn(**kwargs)


def run_read_file(
    path: str,
    *,
    workspace: Path,
    offset: int | None = None,
    limit: int | None = None,
    **_kwargs: object,
) -> str:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return str(exc)
    if error := _protected_workspace_path_error(workspace, target):
        return error
    if not target.is_file():
        return f"File not found: {path}"
    read_result = _read_file_text(target, path)
    if read_result.error:
        return read_result.text
    selected_lines = _slice_lines(read_result.text, offset=offset, limit=limit)
    return _truncate_tool_text("\n".join(selected_lines))


def run_write_file(
    path: str,
    content: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> str:
    if state_rel_path := _agent_writable_state_path(path):
        return _write_agent_state_file(workspace, state_rel_path, content, path)
    target = prepare_write_target(workspace, path)
    if isinstance(target, str):
        return target
    if error := _protected_workspace_path_error(workspace, target):
        return error
    try:
        write_text_no_follow(target, content)
        return f"Wrote {len(content)} chars to {path}"
    except OSError as exc:
        return f"Error writing file: {exc}"


def run_edit_file(
    path: str,
    old_text: str,
    new_text: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> str:
    read_result = _edit_file_text(workspace, path)
    if isinstance(read_result, str):
        return read_result

    _target, text = read_result
    match_error = _edit_match_error(path, text.count(old_text))
    if match_error:
        return match_error
    try:
        write_target = prepare_write_target(workspace, path)
        if isinstance(write_target, str):
            return write_target
        write_text_no_follow(write_target, text.replace(old_text, new_text, 1))
        return f"Edited {path} (replaced 1 match)"
    except OSError as exc:
        return f"Error writing file: {exc}"


def run_list_files(
    *,
    workspace: Path,
    path: str = "",
    pattern: str = "*",
    **_kwargs: object,
) -> str:
    target = _list_files_target(workspace, path)
    if isinstance(target, str):
        return target

    lines = list(_iter_list_file_lines(target, workspace, pattern))
    return "\n".join(lines) if lines else "(no files found)"


def run_search_files(
    pattern: str,
    *,
    workspace: Path,
    path: str = "",
    case_sensitive: bool = False,
    abort: threading.Event | None = None,
    **_kwargs: object,
) -> ToolHandlerResult:
    target = _target_search_dir(workspace, path)
    if isinstance(target, str):
        return target
    regex = _compile_search_pattern(pattern, case_sensitive=case_sensitive)
    if isinstance(regex, str):
        return regex

    search_result = _search_target_files(target, workspace=workspace, regex=regex, abort=abort)
    if isinstance(search_result, ToolResult):
        return search_result
    return _format_search_results(pattern, search_result.file_count, search_result.matches)


def _truncate_tool_text(text: str) -> str:
    if len(text) <= _MAX_READ_CHARS:
        return text
    return text[:_MAX_READ_CHARS] + "\n... [truncated]"


def _binary_read_error(path: str, suffix: str) -> str:
    if suffix in _BINARY_DOCUMENT_SUFFIXES:
        return (
            f"Cannot read binary document: {path}. "
            "Binary documents must be converted through the materials index before "
            "they are searchable. Rebuild the index with `heph index <armory>`."
        )
    return f"Cannot read (binary file): {path}"


def _agent_writable_state_path(path: str) -> Path | None:
    rel_path = Path(path)
    return rel_path if rel_path in _AGENT_WRITABLE_STATE_PATHS else None


def _write_agent_state_file(
    workspace: Path,
    rel_path: Path,
    content: str,
    display_path: str,
) -> str:
    try:
        write_armory_state_text(workspace, rel_path, content)
        return f"Wrote {len(content)} chars to {display_path}"
    except OSError as exc:
        return f"Error writing file: {exc}"


def _protected_workspace_path_error(workspace: Path, target: Path) -> str:
    try:
        rel = target.resolve(strict=False).relative_to(workspace.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return "Path escapes workspace."
    if ".hephaion" in rel.parts:
        return "Access denied: .hephaion contains internal armory state."
    return ""


def _large_text_file_error(target: Path, display_path: str) -> str:
    try:
        size = target.stat().st_size
    except OSError as exc:
        return f"Error reading file: {exc}"
    if size > _MAX_TEXT_FILE_BYTES:
        return f"File too large: {display_path} exceeds {_MAX_TEXT_FILE_BYTES:,} byte tool limit."
    return ""


def _read_file_text(target: Path, display_path: str) -> FileReadResult:
    if error := _large_text_file_error(target, display_path):
        return FileReadResult(error, error=True)
    try:
        return FileReadResult(target.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return FileReadResult(_binary_read_error(display_path, target.suffix.lower()), error=True)
    except OSError as exc:
        return FileReadResult(f"Error reading file: {exc}", error=True)


def _slice_lines(text: str, *, offset: int | None, limit: int | None) -> list[str]:
    lines = text.splitlines()
    if offset is not None and offset >= 0:
        lines = lines[offset:]
    if limit is not None and limit > 0:
        lines = lines[:limit]
    return lines


def _edit_file_text(workspace: Path, path: str) -> tuple[Path, str] | str:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return str(exc)
    if not target.is_file():
        return f"File not found: {path}"
    if error := _protected_workspace_path_error(workspace, target):
        return error
    if error := _large_text_file_error(target, path):
        return error
    try:
        return target, target.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error reading file: {exc}"


def _edit_match_error(path: str, count: int) -> str:
    if count == 0:
        return f"Text not found in {path}"
    if count > 1:
        return f"Found {count} matches in {path}; please provide more context to make it unique."
    return ""


def _list_files_target(workspace: Path, path: str) -> Path | str:
    try:
        target = safe_path(workspace, path or ".")
    except ValueError as exc:
        return str(exc)
    if not target.is_dir():
        return f"Not a directory: {path or '.'}"
    return target


def _iter_list_file_lines(target: Path, workspace: Path, pattern: str) -> Iterator[str]:
    for file_path in sorted(target.rglob(pattern)):
        line = _list_file_line(file_path, workspace)
        if line:
            yield line


def _list_file_line(file_path: Path, workspace: Path) -> str:
    rel = file_path.relative_to(workspace)
    if any(part.startswith(".") for part in rel.parts):
        return ""
    kind = "/" if file_path.is_dir() else ""
    return f"  {rel}{kind}"


def _is_searchable_file(file_path: Path, workspace: Path) -> bool:
    rel = file_path.relative_to(workspace)
    return (
        file_path.is_file()
        and not file_path.is_symlink()
        and _path_resolves_within(file_path, workspace)
        and not any(part.startswith(".") for part in rel.parts)
        and file_path.suffix.lower() not in _SEARCH_SKIP_SUFFIXES
        and _text_file_size_within_limit(file_path)
    )


def _path_resolves_within(path: Path, workspace: Path) -> bool:
    try:
        return path.resolve(strict=True).is_relative_to(workspace.resolve(strict=True))
    except (OSError, RuntimeError):
        return False


def _text_file_size_within_limit(file_path: Path) -> bool:
    try:
        return file_path.stat().st_size <= _MAX_TEXT_FILE_BYTES
    except OSError:
        return False


def _search_file(file_path: Path, workspace: Path, regex: re.Pattern[str]) -> list[str]:
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    rel = file_path.relative_to(workspace)
    return [
        f"{rel}:{line_no}: {line.strip()}"
        for line_no, line in enumerate(text.splitlines(), 1)
        if regex.search(line)
    ]


def _cancelled_search_result(file_count: int, matches: Sequence[str]) -> ToolResult:
    return ToolResult(
        success=False,
        content=f"Search cancelled after scanning {file_count} files.",
        metadata={"files_scanned": file_count, "matches": len(matches)},
        error="cancelled",
    )


def _format_search_results(pattern: str, file_count: int, matches: Sequence[str]) -> str:
    if not matches:
        return f"No matches found for '{pattern}' in {file_count} files."
    header = f"Found {len(matches)} matches for '{pattern}':"
    if len(matches) >= _MAX_SEARCH_RESULTS:
        header += f" (showing first {_MAX_SEARCH_RESULTS})"
    return header + "\n" + "\n".join(matches)


def _compile_search_pattern(pattern: str, *, case_sensitive: bool) -> re.Pattern[str] | str:
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(re.escape(pattern), flags)


def _target_search_dir(workspace: Path, path: str) -> Path | str:
    try:
        target = safe_path(workspace, path or ".")
    except ValueError as exc:
        return str(exc)
    if not target.is_dir():
        return f"Not a directory: {path or '.'}"
    return target


def _iter_searchable_files(target: Path, workspace: Path) -> Iterator[Path]:
    for file_path in sorted(target.rglob("*")):
        if _is_searchable_file(file_path, workspace):
            yield file_path


def _search_target_files(
    target: Path,
    *,
    workspace: Path,
    regex: re.Pattern[str],
    abort: threading.Event | None,
) -> ToolResult | SearchFilesResult:
    matches: list[str] = []
    file_count = 0
    for file_path in _iter_searchable_files(target, workspace):
        if abort is not None and abort.is_set():
            return _cancelled_search_result(file_count, matches)

        matches.extend(_search_file(file_path, workspace, regex))
        file_count += 1
        if len(matches) >= _MAX_SEARCH_RESULTS:
            return SearchFilesResult(file_count, matches[:_MAX_SEARCH_RESULTS])
    return SearchFilesResult(file_count, matches)
