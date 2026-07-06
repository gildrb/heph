"""Workspace file handlers for agent tools."""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import cast

from harness.agent.mutation_queue import get_queue
from harness.agent.path_safety import prepare_write_target, safe_path, write_text_no_follow
from harness.agent.tool_schema import ToolHandlerResult, ToolResult
from harness.armory.state_files import write_armory_state_text

_MAX_READ_CHARS = 50_000
_MAX_TEXT_FILE_BYTES = 1_000_000
_MAX_SEARCH_RESULTS = 50
_SEARCH_SKIP_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz"})
_BINARY_DOCUMENT_SUFFIXES = frozenset({".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".odt"})
_AGENT_WRITABLE_STATE_PATHS = frozenset({Path(".harness/exam_bank.json")})


@dataclass(frozen=True, slots=True)
class FileReadResult:
    text: str
    error: bool = False


@dataclass(frozen=True, slots=True)
class SearchFilesResult:
    file_count: int
    matches: list[str]


@dataclass(frozen=True, slots=True)
class EditOperation:
    old_text: str
    new_text: str


@dataclass(frozen=True, slots=True)
class EditMatch:
    start: int
    end: int
    new_text: str


def mutation_wrap(fn: Callable[..., ToolHandlerResult], **kwargs: object) -> ToolHandlerResult:
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
    old_text: str = "",
    new_text: str = "",
    *,
    workspace: Path,
    edits: object = None,
    **_kwargs: object,
) -> ToolResult:
    operations = _edit_operations(old_text=old_text, new_text=new_text, edits=edits)
    if isinstance(operations, ToolResult):
        return operations

    read_result = _edit_file_text(workspace, path)
    if isinstance(read_result, str):
        return _edit_error(read_result)

    _target, text = read_result
    bom, body = _strip_utf8_bom(text)
    original_ending = _detect_line_ending(body)
    normalized_body = _normalize_to_lf(body)
    normalized_operations = _normalized_edit_operations(operations)

    matches = _validated_edit_matches(path, normalized_body, normalized_operations)
    if isinstance(matches, ToolResult):
        return matches

    new_body = _apply_edit_matches(normalized_body, matches)
    if new_body == normalized_body:
        return _edit_error(_no_change_error(path, len(normalized_operations)))

    try:
        write_target = prepare_write_target(workspace, path)
        if isinstance(write_target, str):
            return _edit_error(write_target)
        final_text = bom + _restore_line_endings(new_body, original_ending)
        write_text_no_follow(write_target, final_text)
        return _edit_success(path, normalized_body, new_body, len(normalized_operations))
    except OSError as exc:
        return _edit_error(f"Error writing file: {exc}")


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
    if ".harness" in rel.parts:
        return "Access denied: .harness contains internal armory state."
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
        return target, target.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return _binary_read_error(path, target.suffix.lower())
    except OSError as exc:
        return f"Error reading file: {exc}"


def _edit_operations(
    *,
    old_text: str,
    new_text: str,
    edits: object,
) -> list[EditOperation] | ToolResult:
    operations = _edit_operations_from_edits(edits)
    if isinstance(operations, ToolResult):
        return operations
    if operations:
        if old_text or new_text:
            operations.append(EditOperation(old_text=old_text, new_text=new_text))
        return operations
    if not old_text:
        return _edit_error("Edit tool input is invalid. old_text or edits[] is required.")
    return [EditOperation(old_text=old_text, new_text=new_text)]


def _edit_operations_from_edits(edits: object) -> list[EditOperation] | ToolResult:
    if edits is None:
        return []
    if not isinstance(edits, list) or not edits:
        return _edit_error("Edit tool input is invalid. edits must be a non-empty array.")
    operations: list[EditOperation] = []
    for index, item in enumerate(edits):
        if not isinstance(item, Mapping):
            return _edit_error(f"edits[{index}] must be an object.")
        item_map = cast("Mapping[object, object]", item)
        old_text = item_map.get("old_text")
        if not isinstance(old_text, str):
            old_text = item_map.get("oldText")
        new_text = item_map.get("new_text")
        if not isinstance(new_text, str):
            new_text = item_map.get("newText")
        if not isinstance(old_text, str) or not isinstance(new_text, str):
            return _edit_error(
                f"edits[{index}].old_text and edits[{index}].new_text must be strings."
            )
        operations.append(EditOperation(old_text=old_text, new_text=new_text))
    return operations


def _normalized_edit_operations(operations: Sequence[EditOperation]) -> list[EditOperation]:
    return [
        EditOperation(
            old_text=_normalize_to_lf(operation.old_text),
            new_text=_normalize_to_lf(operation.new_text),
        )
        for operation in operations
    ]


def _validated_edit_matches(
    path: str,
    text: str,
    operations: Sequence[EditOperation],
) -> list[EditMatch] | ToolResult:
    matches: list[EditMatch] = []
    for index, operation in enumerate(operations):
        if not operation.old_text:
            return _edit_error(_empty_old_text_error(path, index, len(operations)))
        occurrences = _count_occurrences(text, operation.old_text)
        if occurrences == 0:
            return _edit_error(_not_found_error(path, index, len(operations)))
        if occurrences > 1:
            return _edit_error(_duplicate_error(path, index, len(operations), occurrences))
        start = text.index(operation.old_text)
        matches.append(
            EditMatch(
                start=start,
                end=start + len(operation.old_text),
                new_text=operation.new_text,
            )
        )
    if overlap_error := _edit_overlap_error(matches):
        return _edit_error(overlap_error)
    return matches


def _apply_edit_matches(text: str, matches: Sequence[EditMatch]) -> str:
    edited = text
    for match in sorted(matches, key=lambda item: item.start, reverse=True):
        edited = f"{edited[: match.start]}{match.new_text}{edited[match.end :]}"
    return edited


def _edit_overlap_error(matches: Sequence[EditMatch]) -> str:
    previous_end = -1
    for match in sorted(matches, key=lambda item: item.start):
        if match.start < previous_end:
            return "Edit ranges must not overlap."
        previous_end = match.end
    return ""


def _count_occurrences(text: str, needle: str) -> int:
    count = 0
    start = 0
    while True:
        index = text.find(needle, start)
        if index == -1:
            return count
        count += 1
        start = index + len(needle)


def _strip_utf8_bom(text: str) -> tuple[str, str]:
    return ("\ufeff", text[1:]) if text.startswith("\ufeff") else ("", text)


def _detect_line_ending(text: str) -> str:
    crlf_index = text.find("\r\n")
    lf_index = text.find("\n")
    if lf_index == -1 or crlf_index == -1:
        return "\n"
    return "\r\n" if crlf_index < lf_index else "\n"


def _normalize_to_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _restore_line_endings(text: str, ending: str) -> str:
    return text.replace("\n", "\r\n") if ending == "\r\n" else text


def _empty_old_text_error(path: str, index: int, total: int) -> str:
    if total == 1:
        return f"old_text must not be empty in {path}."
    return f"edits[{index}].old_text must not be empty in {path}."


def _not_found_error(path: str, index: int, total: int) -> str:
    if total == 1:
        return f"Text not found in {path}"
    return f"Text not found for edits[{index}] in {path}"


def _duplicate_error(path: str, index: int, total: int, occurrences: int) -> str:
    if total == 1:
        return (
            f"Found {occurrences} matches in {path}; "
            "please provide more context to make it unique."
        )
    return (
        f"Found {occurrences} matches for edits[{index}] in {path}; "
        "please provide more context to make it unique."
    )


def _no_change_error(path: str, total: int) -> str:
    if total == 1:
        return f"No changes made to {path}. The replacement produced identical content."
    return f"No changes made to {path}. The replacements produced identical content."


def _edit_success(path: str, old_text: str, new_text: str, edit_count: int) -> ToolResult:
    patch = _unified_patch(path, old_text, new_text)
    return ToolResult(
        success=True,
        content=f"Edited {path} (replaced {edit_count} block{'s' if edit_count != 1 else ''})",
        metadata={
            "path": path,
            "edits": edit_count,
            "patch": patch,
            "first_changed_line": _first_changed_line(old_text, new_text),
        },
    )


def _edit_error(message: str) -> ToolResult:
    return ToolResult(success=False, content=message, error=message)


def _unified_patch(path: str, old_text: str, new_text: str) -> str:
    return "".join(
        unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=path,
            tofile=path,
        )
    )


def _first_changed_line(old_text: str, new_text: str) -> int | None:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    max_len = max(len(old_lines), len(new_lines))
    for index in range(max_len):
        old_line = old_lines[index] if index < len(old_lines) else None
        new_line = new_lines[index] if index < len(new_lines) else None
        if old_line != new_line:
            return index + 1
    return None


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
