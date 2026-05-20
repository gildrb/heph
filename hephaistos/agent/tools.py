"""Tool definitions, handlers, and registry for the agent harness.

Each tool has a JSON schema (for the OpenAI ``tools=`` param) and a
handler function.  Handlers receive the workspace root for path sandboxing.

**Registry protocol** — ``ToolRegistry`` is the single source of truth.
A global ``default_registry`` is pre-loaded with all built-in tools.
Armories can contribute extra tools by dropping ``*.py`` files into
``.hephaistos/tools/`` only after the armory has been explicitly trusted.
Each plugin module must expose a top-level ``register(registry: ToolRegistry)
-> None`` function that calls ``registry.register(...)`` for every tool it
wants to add.
Tool philosophy for a study RAG agent:
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
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from hephaistos.agent.material_tools import run_open_material, run_search_materials
from hephaistos.agent.mutation_queue import get_queue
from hephaistos.agent.tool_schema import (
    ToolHandlerResult,
    ToolParameter,
    ToolResult,
    ToolSchema,
    ToolSpec,
)
from hephaistos.agent.web_tools import run_web_fetch
from hephaistos.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    initialize,
    read_marker,
    validate,
)


def safe_path(workspace: Path, rel_path: str) -> Path:
    resolved = (workspace / rel_path).resolve()
    if not resolved.is_relative_to(workspace.resolve()):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved


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
        self._schemas_cache = result
        self._schemas_cache_key = cache_key
        return list(result)

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
        # Resolve tools directory so symlink checks below are reliable.
        tools_dir = tools_dir.resolve()
        loaded = 0
        for py_file in sorted(tools_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            # Ensure the file is actually inside tools_dir (no symlinks out).
            if not py_file.resolve().is_relative_to(tools_dir):
                continue
            module_name = f"hephaistos_armory_plugin_{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                register_fn = getattr(module, "register", None)
                if callable(register_fn):
                    register_fn(self)
                    loaded += 1
            except Exception as exc:
                print(
                    f"warning: failed to load tool plugin {py_file.name}: {exc}",
                    file=sys.stderr,
                )
        return loaded


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


@dataclass(frozen=True, slots=True)
class BashResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_seconds: float

    def to_display(self) -> str:
        parts: list[str] = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(f"--- stderr ---\n{self.stderr}")
        if self.timed_out:
            parts.append(f"[timed out after {self.duration_seconds:.1f}s]")
        elif self.exit_code != 0:
            parts.append(f"[exit code {self.exit_code}]")
        return "\n".join(parts) if parts else "(no output)"


def _rtk_command_prefix(command: str) -> list[str] | None:
    stripped = command.strip()
    if not stripped or stripped.startswith("rtk "):
        return None
    raw_min_chars = os.environ.get("HEPHAISTOS_RTK_MIN_COMMAND_CHARS", "0").strip()
    try:
        min_chars = max(0, int(raw_min_chars))
    except ValueError:
        min_chars = 0
    if len(stripped) < min_chars:
        return None
    if any(char in stripped for char in _RTK_SHELL_META_CHARS):
        return None

    try:
        argv = shlex.split(stripped)
    except ValueError:
        return None
    if not argv:
        return None

    rtk_path = shutil.which("rtk")
    if rtk_path is None:
        return None

    prefix = [rtk_path]
    if os.environ.get("HEPHAISTOS_RTK_ULTRA", "").strip().lower() in _RTK_TRUTHY:
        prefix.append("--ultra-compact")
    return [*prefix, *argv]


def _run_shell_command(command: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B602
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )  # nosec B602


def run_bash(command: str, timeout: int | None = None, **_kwargs: object) -> str:
    # Block destructive and dangerous commands (LLM-generated).
    # Note: this is a safety net, not a sandbox. Trivial bypasses exist
    # via encoding, variable expansion, etc. Treat as best-effort.
    _blocked_patterns = (
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
    for pat in _blocked_patterns:
        if re.search(pat, command, re.IGNORECASE):
            return f"Error: command blocked for safety: {command}"

    actual_timeout = _BASH_TIMEOUT if timeout is None else timeout
    start = time.monotonic()
    rtk_setting = os.environ.get("HEPHAISTOS_RTK")
    rtk_enabled = rtk_setting is None or rtk_setting.strip().lower() in _RTK_TRUTHY
    rtk_argv = _rtk_command_prefix(command) if rtk_enabled else None
    try:
        if rtk_argv is None:
            result = _run_shell_command(command, actual_timeout)
        else:
            try:
                result = subprocess.run(  # nosec B603
                    rtk_argv,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=actual_timeout + _RTK_TIMEOUT_BUFFER_SECONDS,
                    check=False,
                )
            except OSError as exc:
                fallback = _run_shell_command(command, actual_timeout)
                fallback.stdout = (
                    f"[rtk unavailable: {exc}; used original command output]\n"
                    f"{fallback.stdout or ''}"
                )
                result = fallback
        elapsed = time.monotonic() - start
        br = BashResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.returncode,
            timed_out=False,
            duration_seconds=round(elapsed, 2),
        )
        output = br.to_display()
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        br = BashResult(
            stdout="",
            stderr="",
            exit_code=-1,
            timed_out=True,
            duration_seconds=round(elapsed, 2),
        )
        output = br.to_display()
    except Exception as exc:
        output = f"Error running command: {exc}"
    return output[:_MAX_READ_CHARS]


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
    try:
        text = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        suffix = target.suffix.lower()
        if suffix in (".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".odt"):
            return (
                f"Cannot read binary document: {path}. "
                "Binary documents must be converted through the materials index before "
                "they are searchable. Rebuild the index with `heph index <armory>`."
            )
        return f"Cannot read (binary file): {path}"
    except OSError as exc:
        return f"Error reading file: {exc}"

    lines = text.splitlines()
    if offset is not None and offset >= 0:
        lines = lines[offset:]
    if limit is not None and limit > 0:
        lines = lines[:limit]

    result = "\n".join(lines)
    if len(result) > _MAX_READ_CHARS:
        result = result[:_MAX_READ_CHARS] + "\n... [truncated]"
    return result


def run_write_file(
    path: str,
    content: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> str:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return str(exc)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
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
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return str(exc)
    if not target.is_file():
        return f"File not found: {path}"
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error reading file: {exc}"

    count = text.count(old_text)
    if count == 0:
        return f"Text not found in {path}"
    if count > 1:
        return f"Found {count} matches in {path}; please provide more context to make it unique."

    updated = text.replace(old_text, new_text, 1)
    try:
        target.write_text(updated, encoding="utf-8")
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
    try:
        target = safe_path(workspace, path or ".")
    except ValueError as exc:
        return str(exc)
    if not target.is_dir():
        return f"Not a directory: {path or '.'}"

    files = sorted(target.rglob(pattern))
    lines: list[str] = []
    for f in files:
        rel = f.relative_to(workspace)
        if any(part.startswith(".") for part in rel.parts):
            continue
        kind = "/" if f.is_dir() else ""
        lines.append(f"  {rel}{kind}")
    if not lines:
        return "(no files found)"
    return "\n".join(lines)


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
        "Internal Heph state belongs in .hephaistos/.",
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
            "Use materials/ for user source files. .hephaistos/ is internal state."
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
        and not any(part.startswith(".") for part in rel.parts)
        and file_path.suffix.lower() not in _SEARCH_SKIP_SUFFIXES
    )


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


def run_search_files(
    pattern: str,
    *,
    workspace: Path,
    path: str = "",
    case_sensitive: bool = False,
    abort: threading.Event | None = None,
    **_kwargs: object,
) -> ToolHandlerResult:
    try:
        target = safe_path(workspace, path or ".")
    except ValueError as exc:
        return str(exc)
    if not target.is_dir():
        return f"Not a directory: {path or '.'}"

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        return f"Invalid regex pattern: {exc}"

    matches: list[str] = []
    file_count = 0

    for file_path in sorted(target.rglob("*")):
        if abort is not None and abort.is_set():
            return _cancelled_search_result(file_count, matches)
        if not _is_searchable_file(file_path, workspace):
            continue

        matches.extend(_search_file(file_path, workspace, regex))
        file_count += 1
        if len(matches) >= _MAX_SEARCH_RESULTS:
            matches = matches[:_MAX_SEARCH_RESULTS]
            break

    return _format_search_results(pattern, file_count, matches)


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
