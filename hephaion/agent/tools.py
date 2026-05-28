"""Tool definitions, handlers, and registry for the agent harness.

Each tool has a JSON schema (for the OpenAI ``tools=`` param) and a
handler function.  Handlers receive the workspace root for path sandboxing.

**Registry protocol** — ``ToolRegistry`` is the single source of truth.
A global ``default_registry`` is pre-loaded with all built-in tools.
Armories can contribute extra tools by dropping ``*.py`` files into
``.hephaion/tools/`` only after the armory has been explicitly trusted.
Each plugin module must expose a top-level ``register(registry: ToolRegistry)
-> None`` function that calls ``registry.register(...)`` for every tool it
wants to add.
Tool philosophy for a document-grounded agent:
- Read/write tools are primary — the agent works with documents.
- Web fetch fills knowledge gaps, but with strict source attribution.
- The agent should NEVER guess. If information is not in the documents
  and cannot be fetched, it must say so.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shlex
import shutil
import subprocess  # nosec B404
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from hephaion.agent.material_tools import run_open_material, run_search_materials
from hephaion.agent.mutation_queue import get_queue
from hephaion.agent.tool_schema import (
    ToolHandlerResult,
    ToolParameter,
    ToolResult,
    ToolSchema,
    ToolSpec,
)
from hephaion.agent.web_tools import run_web_fetch
from hephaion.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    initialize,
    read_marker,
    validate,
)
from hephaion.env import get_env
from hephaion.memory import MemoryEntry, MemoryStore, load_memory, save_memory


def safe_path(workspace: Path, rel_path: str) -> Path:
    try:
        resolved = (workspace / rel_path).resolve()
        workspace_resolved = workspace.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Path cannot be resolved: {rel_path}") from exc
    if not resolved.is_relative_to(workspace_resolved):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved


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


def _prepare_write_target(workspace: Path, path: str) -> Path | str:
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


def _write_text_no_follow(target: Path, content: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(target), flags, 0o666)
    try:
        file = os.fdopen(fd, "w", encoding="utf-8")
    except Exception:
        os.close(fd)
        raise
    with file:
        file.write(content)


class ToolRegistry:
    def __init__(self, parent: ToolRegistry | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._parent = parent
        self._generation = 0
        self._schemas_cache: list[ToolSchema] | None = None
        self._schemas_cache_key: tuple[int, int] | None = None

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec
        self._generation += 1

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._generation += 1

    def get(self, name: str) -> ToolSpec | None:
        spec = self._tools.get(name)
        if spec is not None:
            return spec
        if self._parent is not None:
            return self._parent.get(name)
        return None

    def get_handler(self, name: str) -> Callable[..., ToolHandlerResult] | None:
        spec = self.get(name)
        return spec.handler if spec else None

    def is_control_tool(self, name: str) -> bool:
        spec = self.get(name)
        return spec.kind == "control" if spec is not None else False

    def _visible_generation(self) -> int:
        parent_generation = self._parent._visible_generation() if self._parent is not None else 0
        return self._generation + parent_generation

    @property
    def schemas(self) -> list[ToolSchema]:
        parent_generation = self._parent._visible_generation() if self._parent is not None else 0
        cache_key = (self._generation, parent_generation)
        if self._schemas_cache is not None and self._schemas_cache_key == cache_key:
            return list(self._schemas_cache)

        result = self._visible_schemas()
        self._schemas_cache = result
        self._schemas_cache_key = cache_key
        return list(result)

    def _visible_schemas(self) -> list[ToolSchema]:
        seen: set[str] = set()
        result: list[ToolSchema] = []
        for spec in self._tools.values():
            seen.add(spec.name)
            result.append(spec.schema)
        if self._parent is not None:
            for schema in self._parent.schemas:
                name = schema["function"]["name"]
                if name not in seen:
                    seen.add(name)
                    result.append(schema)
        return result

    @property
    def specs(self) -> list[ToolSpec]:
        seen: set[str] = set()
        result: list[ToolSpec] = []
        for spec in self._tools.values():
            seen.add(spec.name)
            result.append(spec)
        if self._parent is not None:
            for spec in self._parent.specs:
                if spec.name not in seen:
                    seen.add(spec.name)
                    result.append(spec)
        return result

    @property
    def tool_names(self) -> list[str]:
        return [s["function"]["name"] for s in self.schemas]

    def child(self) -> ToolRegistry:
        return ToolRegistry(parent=self)

    def load_plugins(self, tools_dir: Path) -> int:
        if not tools_dir.is_dir():
            return 0
        tools_dir = tools_dir.resolve()
        loaded = 0
        for py_file in sorted(tools_dir.glob("*.py")):
            loaded += int(_load_plugin_file(self, py_file, tools_dir))
        return loaded


def _load_plugin_file(registry: ToolRegistry, py_file: Path, tools_dir: Path) -> bool:
    if py_file.name.startswith("_"):
        return False
    if not py_file.resolve().is_relative_to(tools_dir):
        return False
    module_name = f"hephaion_armory_plugin_{py_file.stem}"
    try:
        return _register_plugin_module(registry, module_name, py_file)
    except Exception as exc:
        print(f"warning: failed to load tool plugin {py_file.name}: {exc}", file=sys.stderr)
        return False


def _register_plugin_module(registry: ToolRegistry, module_name: str, py_file: Path) -> bool:
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register_fn = getattr(module, "register", None)
    if not callable(register_fn):
        return False
    register_fn(registry)
    return True


def _string(description: str) -> ToolParameter:
    return {"type": "string", "description": description}


def _integer(description: str) -> ToolParameter:
    return {"type": "integer", "description": description}


def _tool(
    name: str,
    description: str,
    properties: dict[str, ToolParameter] | None = None,
    *,
    required: tuple[str, ...] = (),
) -> ToolSchema:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties if properties is not None else {},
                "required": list(required),
            },
        },
    }


_BUILTIN_SCHEMAS: list[ToolSchema] = [
    _tool(
        "compact",
        "Compress long conversation context.",
    ),
    _tool(
        "read_file",
        "Read workspace file contents.",
        {
            "path": _string("Relative path from workspace root."),
            "offset": _integer("Line number to start reading from (0-based)."),
            "limit": _integer("Maximum number of lines to read."),
        },
        required=("path",),
    ),
    _tool(
        "write_file",
        "Create or overwrite a workspace file.",
        {
            "path": _string("Relative path from workspace root."),
            "content": _string("The content to write."),
        },
        required=("path", "content"),
    ),
    _tool(
        "edit_file",
        "Replace exact text in a workspace file.",
        {
            "path": _string("Relative path from workspace root."),
            "old_text": _string("The exact text to find."),
            "new_text": _string("The replacement text."),
        },
        required=("path", "old_text", "new_text"),
    ),
    _tool(
        "list_files",
        "List workspace directory contents.",
        {
            "path": _string("Relative directory path. Defaults to workspace root."),
            "pattern": _string("Glob pattern to filter files (e.g. '*.py')."),
        },
    ),
    _tool(
        "create_armory",
        "Create or repair a portable Heph armory.",
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "validate_armory",
        "Validate an armory layout without modifying it.",
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "search_files",
        "Search text files in the workspace.",
        {
            "pattern": _string("Text or regex pattern to search for."),
            "path": _string("Directory to search in. Defaults to workspace root."),
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether the search is case-sensitive. Default: false.",
            },
        },
        required=("pattern",),
    ),
    _tool(
        "search_materials",
        "Search indexed armory materials.",
        {
            "query": _string("Natural-language topic, question, term, or formula to search for."),
            "top_k": _integer("Maximum number of excerpts to return. Default: 8."),
        },
        required=("query",),
    ),
    _tool(
        "open_material",
        "Read indexed material context around a source chunk.",
        {
            "source": _string("Indexed source path such as materials/lecture.pdf."),
            "chunk": _integer("Chunk number to center on. Defaults to the first chunk."),
            "context": _integer("Neighbor chunks to include on each side. Default: 1."),
        },
        required=("source",),
    ),
    _tool(
        "memory",
        (
            "Read or update durable armory memory. Use it for stable user preferences, "
            "corrections, armory conventions, and facts that should survive future sessions. "
            "Do not save temporary task progress."
        ),
        {
            "action": _string("One of: read, add, replace, remove."),
            "query": _string("Optional substring filter for read."),
            "topic": _string("Short topic for add or replace."),
            "content": _string("Compact memory entry content for add or replace."),
            "old_text": _string("Short unique substring for replace or remove."),
            "source": _string("Optional source label. Defaults to conversation."),
        },
        required=("action",),
    ),
    _tool(
        "web_fetch",
        "Fetch a web page when armory material is insufficient.",
        {
            "url": _string("The URL to fetch (must start with http:// or https://)."),
        },
        required=("url",),
    ),
]

_BASH_TIMEOUT = 30
_MAX_READ_CHARS = 50_000
_RTK_TIMEOUT_BUFFER_SECONDS = 5
_MAX_SEARCH_RESULTS = 50
_SEARCH_SKIP_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz"})
_RTK_SHELL_META_CHARS = frozenset("|&;<>(){}[]*$?`!~\n")
_RTK_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})
_BINARY_DOCUMENT_SUFFIXES = frozenset({".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".odt"})
_BLOCKED_BASH_PATTERNS = (
    r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r[a-zA-Z]*\s+|-r[a-zA-Z]*\s+-f[a-zA-Z]*\s+)",
    r"\brm\s+-rf\s+",
    r"\bmkfs\b",
    r"\bdd\s+",
    r"\bshutdown\b",
    r"\breboot\b",
    r">/dev/sd",
    r"\bchmod\s+(777|666)\b",
    r"\bcurl\b.*\|\s*(ba)?sh\b",
    r"\bwget\b.*\|\s*(ba)?sh\b",
    r"\bbase64\b.*\|\s*(ba)?sh\b",
    r"\bpython[23]?\s+-c\b",
    r"\bchmod\s+[0-7]*[0-7]{3}\s+/",
    r"\bchown\b.*\s+/",
)


@dataclass(frozen=True, slots=True)
class BashResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_seconds: float

    def to_display(self) -> str:
        return _bash_result_display(self)


def _bash_result_display(result: BashResult) -> str:
    parts = _bash_result_output_parts(result)
    status = _bash_result_status(result)
    if status:
        parts.append(status)
    return "\n".join(parts) if parts else "(no output)"


def _bash_result_output_parts(result: BashResult) -> list[str]:
    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"--- stderr ---\n{result.stderr}")
    return parts


def _bash_result_status(result: BashResult) -> str:
    if result.timed_out:
        return f"[timed out after {result.duration_seconds:.1f}s]"
    if result.exit_code != 0:
        return f"[exit code {result.exit_code}]"
    return ""


@dataclass(frozen=True, slots=True)
class FileReadResult:
    text: str
    error: bool = False


@dataclass(frozen=True, slots=True)
class SearchFilesResult:
    file_count: int
    matches: list[str]


def _rtk_command_prefix(command: str) -> list[str] | None:
    argv = _rtk_candidate_argv(command)
    if argv is None:
        return None
    rtk_path = shutil.which("rtk")
    if rtk_path is None:
        return None
    return [rtk_path, *_rtk_option_args(), *argv]


def _rtk_candidate_argv(command: str) -> list[str] | None:
    stripped = command.strip()
    if not _rtk_can_wrap_command(stripped):
        return None
    try:
        argv = shlex.split(stripped)
    except ValueError:
        return None
    return argv or None


def _rtk_can_wrap_command(stripped_command: str) -> bool:
    return (
        bool(stripped_command)
        and not stripped_command.startswith("rtk ")
        and len(stripped_command) >= _rtk_min_command_chars()
        and not any(char in stripped_command for char in _RTK_SHELL_META_CHARS)
    )


def _rtk_min_command_chars() -> int:
    raw_min_chars = get_env("HEPHAION_RTK_MIN_COMMAND_CHARS", "0").strip()
    try:
        return max(0, int(raw_min_chars))
    except ValueError:
        return 0


def _rtk_option_args() -> list[str]:
    if get_env("HEPHAION_RTK_ULTRA", "").strip().lower() in _RTK_TRUTHY:
        return ["--ultra-compact"]
    return []


def _rtk_enabled() -> bool:
    rtk_setting = get_env("HEPHAION_RTK")
    return rtk_setting is None or rtk_setting.strip().lower() in _RTK_TRUTHY


def _blocked_bash_command(command: str) -> bool:
    return any(
        re.search(blocked_pattern, command, re.IGNORECASE)
        for blocked_pattern in _BLOCKED_BASH_PATTERNS
    )


def _run_shell_command(command: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B602
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )  # nosec B602


def _run_rtk_command(rtk_argv: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        rtk_argv,
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout + _RTK_TIMEOUT_BUFFER_SECONDS,
        check=False,
    )


def _run_bash_command(command: str, timeout: int) -> subprocess.CompletedProcess[str]:
    rtk_argv = _rtk_command_prefix(command) if _rtk_enabled() else None
    if rtk_argv is None:
        return _run_shell_command(command, timeout)

    try:
        return _run_rtk_command(rtk_argv, timeout)
    except OSError as exc:
        fallback_result = _run_shell_command(command, timeout)
        fallback_result.stdout = (
            f"[rtk unavailable: {exc}; used original command output]\n"
            f"{fallback_result.stdout or ''}"
        )
        return fallback_result


def _bash_display(
    completed: subprocess.CompletedProcess[str],
    *,
    started_at: float,
    timed_out: bool = False,
) -> str:
    bash_result = BashResult(
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        exit_code=completed.returncode,
        timed_out=timed_out,
        duration_seconds=round(time.monotonic() - started_at, 2),
    )
    return bash_result.to_display()


def _bash_timeout_display(started_at: float) -> str:
    bash_result = BashResult(
        stdout="",
        stderr="",
        exit_code=-1,
        timed_out=True,
        duration_seconds=round(time.monotonic() - started_at, 2),
    )
    return bash_result.to_display()


def _truncate_tool_text(text: str) -> str:
    if len(text) <= _MAX_READ_CHARS:
        return text
    return text[:_MAX_READ_CHARS] + "\n... [truncated]"


def run_bash(command: str, timeout: int | None = None, **_kwargs: object) -> str:
    # Block destructive and dangerous commands (LLM-generated).
    # Note: this is a safety net, not a sandbox. Trivial bypasses exist
    # via encoding, variable expansion, etc. Treat as best-effort.
    if _blocked_bash_command(command):
        return f"Error: command blocked for safety: {command}"

    actual_timeout = _BASH_TIMEOUT if timeout is None else timeout
    started_at = time.monotonic()
    try:
        result = _run_bash_command(command, actual_timeout)
        output = _bash_display(result, started_at=started_at)
    except subprocess.TimeoutExpired:
        output = _bash_timeout_display(started_at)
    except Exception as exc:
        output = f"Error running command: {exc}"
    return output[:_MAX_READ_CHARS]


def _binary_read_error(path: str, suffix: str) -> str:
    if suffix in _BINARY_DOCUMENT_SUFFIXES:
        return (
            f"Cannot read binary document: {path}. "
            "Binary documents must be converted through the materials index before "
            "they are searchable. Rebuild the index with `heph index <armory>`."
        )
    return f"Cannot read (binary file): {path}"


def _read_file_text(target: Path, display_path: str) -> FileReadResult:
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
    target = _prepare_write_target(workspace, path)
    if isinstance(target, str):
        return target
    try:
        _write_text_no_follow(target, content)
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
        write_target = _prepare_write_target(workspace, path)
        if isinstance(write_target, str):
            return write_target
        _write_text_no_follow(write_target, text.replace(old_text, new_text, 1))
        return f"Edited {path} (replaced 1 match)"
    except OSError as exc:
        return f"Error writing file: {exc}"


def _edit_file_text(workspace: Path, path: str) -> tuple[Path, str] | str:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return str(exc)
    if not target.is_file():
        return f"File not found: {path}"
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


def run_create_armory(
    path: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return ToolResult(success=False, content=str(exc), error="path_escape")
    try:
        initialize(target)
        marker = read_marker(target)
    except OSError as exc:
        return ToolResult(
            success=False,
            content=f"Error creating armory: {exc}",
            error="io_error",
        )

    created_paths = [str((target / dirname).relative_to(target)) for dirname in ARMORY_DIRS]
    marker_rel = str(MARKER_FILE)
    lines = [
        f"Armory ready: {target}",
        "User source files belong in materials/.",
        "Internal Heph state belongs in .hephaion/.",
        "Required layout:",
        *(f"  - {dirname}/" for dirname in created_paths),
        f"  - {marker_rel}",
    ]
    return ToolResult(
        success=True,
        content="\n".join(lines),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": marker_rel,
        },
    )


def run_validate_armory(
    path: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return ToolResult(success=False, content=str(exc), error="path_escape")
    try:
        validate(target)
        marker = read_marker(target)
    except ArmoryValidationError as exc:
        return ToolResult(success=False, content=str(exc), error="invalid_armory")
    except OSError as exc:
        return ToolResult(success=False, content=f"Error reading armory: {exc}", error="io_error")

    return ToolResult(
        success=True,
        content=(
            f"Valid Heph armory: {target}\n"
            "Use materials/ for user source files. .hephaion/ is internal state."
        ),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": str(MARKER_FILE),
        },
    )


def _is_searchable_file(file_path: Path, workspace: Path) -> bool:
    rel = file_path.relative_to(workspace)
    return (
        file_path.is_file()
        and not file_path.is_symlink()
        and _path_resolves_within(file_path, workspace)
        and not any(part.startswith(".") for part in rel.parts)
        and file_path.suffix.lower() not in _SEARCH_SKIP_SUFFIXES
    )


def _path_resolves_within(path: Path, workspace: Path) -> bool:
    try:
        return path.resolve(strict=True).is_relative_to(workspace.resolve(strict=True))
    except (OSError, RuntimeError):
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
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        return f"Invalid regex pattern: {exc}"


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


def _format_memory_entry(entry: MemoryEntry) -> str:
    source = f" ({entry.source})" if entry.source else ""
    return f"- [{entry.confidence}] {entry.topic}: {entry.content}{source}"


def _format_memory_entries(entries: Sequence[MemoryEntry]) -> str:
    if not entries:
        return "(no memory entries)"
    return "\n".join(_format_memory_entry(entry) for entry in entries)


def run_memory(
    action: str,
    *,
    workspace: Path,
    query: str = "",
    topic: str = "",
    content: str = "",
    old_text: str = "",
    source: str = "conversation",
    **_kwargs: object,
) -> ToolResult:
    memory = load_memory(workspace)
    cleaned_action = action.strip().lower()
    if cleaned_action == "read":
        return _memory_read(memory, query)
    if cleaned_action == "add":
        return _memory_add(memory, topic=topic, content=content, source=source)
    if cleaned_action == "replace":
        return _memory_replace(
            memory,
            old_text,
            topic=topic,
            content=content,
            source=source,
        )
    if cleaned_action == "remove":
        return _memory_remove(memory, old_text)
    return ToolResult(
        success=False,
        content=f"Unknown memory action: {action}. Use read, add, replace, or remove.",
        error="unknown_memory_action",
    )


def _memory_read(memory: MemoryStore, query: str) -> ToolResult:
    entries = memory.read(query)
    save_memory(memory)
    return ToolResult(
        success=True,
        content=_format_memory_entries(entries),
        metadata={"entries": len(entries), "query": query},
    )


def _memory_add(
    memory: MemoryStore,
    *,
    topic: str,
    content: str,
    source: str,
) -> ToolResult:
    entry = memory.add(topic, content, source=source or "conversation", confidence="verified")
    if entry is None:
        return ToolResult(
            success=False,
            content="Memory entry was not saved. Use a unique topic and compact safe content.",
            error="memory_add_failed",
        )
    save_memory(memory)
    return ToolResult(success=True, content=f"Saved memory: {_format_memory_entry(entry)}")


def _memory_replace(
    memory: MemoryStore,
    old_text: str,
    *,
    topic: str,
    content: str,
    source: str,
) -> ToolResult:
    result = memory.replace(
        old_text,
        topic=topic,
        content=content,
        source=source or "conversation",
        confidence="verified",
    )
    if isinstance(result, str):
        return ToolResult(success=False, content=result, error="memory_replace_failed")
    save_memory(memory)
    return ToolResult(success=True, content=f"Replaced memory: {_format_memory_entry(result)}")


def _memory_remove(memory: MemoryStore, old_text: str) -> ToolResult:
    result = memory.remove(old_text)
    if isinstance(result, str):
        return ToolResult(success=False, content=result, error="memory_remove_failed")
    save_memory(memory)
    return ToolResult(
        success=True,
        content="Removed memory entry.",
        metadata={"removed": result},
    )


def _mutation_wrap(fn: Callable[..., str], **kwargs: object) -> str:
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


def get_handler(name: str):
    return default_registry.get_handler(name)


_HANDLERS: dict[str, Callable[..., ToolHandlerResult]] = {
    "compact": lambda **_kw: "[compact triggered]",
    "bash": run_bash,
    "read_file": run_read_file,
    "write_file": lambda **kwargs: _mutation_wrap(run_write_file, **kwargs),
    "edit_file": lambda **kwargs: _mutation_wrap(run_edit_file, **kwargs),
    "list_files": run_list_files,
    "create_armory": run_create_armory,
    "validate_armory": run_validate_armory,
    "search_files": run_search_files,
    "search_materials": run_search_materials,
    "open_material": run_open_material,
    "memory": run_memory,
    "web_fetch": run_web_fetch,
}

default_registry = ToolRegistry()

for _schema in _BUILTIN_SCHEMAS:
    _name = _schema["function"]["name"]
    _handler = _HANDLERS[_name]
    _kind: Literal["normal", "control"] = "control" if _name == "compact" else "normal"
    default_registry.register(
        ToolSpec(
            schema=_schema,
            handler=_handler,
            kind=_kind,
        )
    )

# Backward-compatible alias: TOOL_SCHEMAS delegates to the registry.
TOOL_SCHEMAS: list[ToolSchema] = default_registry.schemas
