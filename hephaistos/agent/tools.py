"""Tool definitions, handlers, and registry for the agent harness.

Each tool has a JSON schema (for the OpenAI ``tools=`` param) and a
handler function.  Handlers receive the workspace root for path sandboxing.

**Registry protocol** — ``ToolRegistry`` is the single source of truth.
A global ``default_registry`` is pre-loaded with all built-in tools.
Armories can contribute extra tools by dropping ``*.py`` files into
``.hephaistos/tools/``.  Each plugin module must expose a top-level
``register(registry: ToolRegistry) -> None`` function that calls
``registry.register(...)`` for every tool it wants to add.
Tool philosophy for a study RAG agent:
- Read/write tools are primary — the agent works with documents.
- Bash is available but strictly limited (timeout, structured output).
- Web fetch fills knowledge gaps, but with strict source attribution.
- The agent should NEVER guess. If information is not in the documents
  and cannot be fetched, it must say so.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import os
import re
import shlex
import shutil
import socket
import subprocess  # nosec B404
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from hephaistos.agent.mutation_queue import get_queue
from hephaistos.agent.tool_schema import (
    ToolHandlerResult,
    ToolParameter,
    ToolResult,
    ToolSchema,
    ToolSpec,
)
from hephaistos.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    initialize,
    read_marker,
    validate,
)


def safe_path(workspace: Path, rel_path: str) -> Path:
    """Resolve *rel_path* inside *workspace* and ensure it doesn't escape."""
    resolved = (workspace / rel_path).resolve()
    if not resolved.is_relative_to(workspace.resolve()):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved


def _resolve_hostname_ips(hostname: str) -> list[str]:
    """Resolve a hostname to its IP addresses (to prevent DNS rebinding)."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return [str(sockaddr[0]) for _, _, _, _, sockaddr in addr_info]


class ToolRegistry:
    """Extensible registry of :class:`ToolSpec` entries.

    Supports hierarchical scoping via :meth:`child` — a child registry
    inherits everything from its parent and can override or add tools
    without mutating the parent.  This is the mechanism used for
    per-armory tool loading.
    """

    def __init__(self, parent: ToolRegistry | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._parent = parent
        self._generation = 0
        self._schemas_cache: list[ToolSchema] | None = None
        self._schemas_cache_key: tuple[int, int] | None = None

    # -- mutation -----------------------------------------------------------

    def register(self, spec: ToolSpec) -> None:
        """Add or replace a tool by name."""
        self._tools[spec.name] = spec
        self._generation += 1

    def unregister(self, name: str) -> None:
        """Remove a locally-registered tool (does not affect parent)."""
        self._tools.pop(name, None)
        self._generation += 1

    # -- query --------------------------------------------------------------

    def get(self, name: str) -> ToolSpec | None:
        """Look up a tool by name, checking local then parent."""
        spec = self._tools.get(name)
        if spec is not None:
            return spec
        if self._parent is not None:
            return self._parent.get(name)
        return None

    def get_handler(self, name: str) -> Callable[..., ToolHandlerResult] | None:
        """Return the handler for *name*, or ``None``."""
        spec = self.get(name)
        return spec.handler if spec else None

    def is_control_tool(self, name: str) -> bool:
        """Return whether *name* is a control-flow tool."""
        spec = self.get(name)
        return spec.kind == "control" if spec is not None else False

    def _visible_generation(self) -> int:
        parent_generation = self._parent._visible_generation() if self._parent is not None else 0
        return self._generation + parent_generation

    @property
    def schemas(self) -> list[ToolSchema]:
        """All visible tool schemas (local + inherited, local overrides first)."""
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
    def tool_names(self) -> list[str]:
        return [s["function"]["name"] for s in self.schemas]

    # -- hierarchy ----------------------------------------------------------

    def child(self) -> ToolRegistry:
        """Create a child registry that inherits from this one."""
        return ToolRegistry(parent=self)

    # -- armory plugin discovery --------------------------------------------

    def load_plugins(self, tools_dir: Path) -> int:
        """Load ``*.py`` plugin modules from *tools_dir*.

        Each module may define a ``register(registry: ToolRegistry) -> None``
        function.  Returns the number of plugins loaded.

        **Security note**: plugins are loaded from the armory's
        ``.hephaistos/tools/`` directory.  Only trusted armories should
        have tool plugins.  Each plugin is executed with full process
        privileges.
        """
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


# ---------------------------------------------------------------------------
# Built-in tool definitions
# ---------------------------------------------------------------------------


def _param(json_type: str, description: str) -> ToolParameter:
    """Build a JSON-schema property for a tool parameter."""
    return {"type": json_type, "description": description}


def _string(description: str) -> ToolParameter:
    return _param("string", description)


def _integer(description: str) -> ToolParameter:
    return _param("integer", description)


def _boolean(description: str) -> ToolParameter:
    return _param("boolean", description)


def _tool(
    name: str,
    description: str,
    properties: dict[str, ToolParameter] | None = None,
    *,
    required: tuple[str, ...] = (),
) -> ToolSchema:
    """Build the OpenAI-compatible function tool schema."""
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
        (
            "Compress the conversation context to free up space. "
            "Use when you notice the conversation is getting long or "
            "you are running low on context."
        ),
    ),
    _tool(
        "bash",
        "Run a shell command and return structured output with exit code.",
        {
            "command": _string("The shell command to run."),
            "timeout": _integer("Timeout in seconds (default: 30)."),
        },
        required=("command",),
    ),
    _tool(
        "read_file",
        "Read the contents of a file in the workspace.",
        {
            "path": _string("Relative path from workspace root."),
            "offset": _integer("Line number to start reading from (0-based)."),
            "limit": _integer("Maximum number of lines to read."),
        },
        required=("path",),
    ),
    _tool(
        "write_file",
        "Create or overwrite a file in the workspace.",
        {
            "path": _string("Relative path from workspace root."),
            "content": _string("The content to write."),
        },
        required=("path", "content"),
    ),
    _tool(
        "edit_file",
        "Replace an exact text match in a file.",
        {
            "path": _string("Relative path from workspace root."),
            "old_text": _string("The exact text to find."),
            "new_text": _string("The replacement text."),
        },
        required=("path", "old_text", "new_text"),
    ),
    _tool(
        "list_files",
        "List files in a workspace directory.",
        {
            "path": _string("Relative directory path. Defaults to workspace root."),
            "pattern": _string("Glob pattern to filter files (e.g. '*.py')."),
        },
    ),
    _tool(
        "create_armory",
        (
            "Create or repair a Hephaistos armory with the canonical layout: "
            "materials/ for user study files and .hephaistos/ for internal state."
        ),
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "validate_armory",
        (
            "Validate that a folder is a Hephaistos armory. Reports missing required "
            "directories and marker metadata without modifying files."
        ),
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "search_files",
        (
            "Search for a text pattern across files in the workspace. "
            "Returns matching lines with file paths and line numbers. "
            "Use this to find where a topic, term, or formula is discussed "
            "in source documents before answering."
        ),
        {
            "pattern": _string("Text or regex pattern to search for."),
            "path": _string("Directory to search in. Defaults to workspace root."),
            "case_sensitive": _boolean("Whether the search is case-sensitive. Default: false."),
        },
        required=("pattern",),
    ),
    _tool(
        "web_fetch",
        (
            "Fetch a web page and return its text content. "
            "Use ONLY when the answer cannot be found in the armory documents. "
            "The response always includes the source URL for verification. "
            "Do NOT guess or fabricate information — if the fetch fails or "
            "doesn't contain the answer, say so explicitly."
        ),
        {
            "url": _string("The URL to fetch (must start with http:// or https://)."),
        },
        required=("url",),
    ),
]

_BASH_TIMEOUT = 30
_MAX_READ_CHARS = 50_000
_RTK_TIMEOUT_BUFFER_SECONDS = 5
_WEB_FETCH_TIMEOUT = 15
_WEB_FETCH_MAX_CHARS = 20_000
_WEB_USER_AGENT = "Hephaistos/0.1 (study agent)"
_MAX_SEARCH_RESULTS = 50
_RTK_SHELL_META_CHARS = frozenset("|&;<>(){}[]*$?`!~\n")
_RTK_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})


@dataclass(frozen=True, slots=True)
class BashResult:
    """Structured result from a bash command execution."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_seconds: float

    def to_display(self) -> str:
        """Format for display to the LLM."""
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


def _rtk_enabled() -> bool:
    """Return whether model-generated bash calls should go through RTK.

    RTK is reliability-safe only as a best-effort filter for simple command
    output: missing RTK falls back to the original command, and commands with
    shell metacharacters are never rewritten.  Enable that safe path by default
    when available; allow operators to opt out with ``HEPHAISTOS_RTK=0``.
    """
    raw = os.environ.get("HEPHAISTOS_RTK")
    if raw is None:
        return True
    return raw.strip().lower() in _RTK_TRUTHY


def _rtk_ultra_compact() -> bool:
    """Return whether RTK should use its ultra-compact output mode."""
    return os.environ.get("HEPHAISTOS_RTK_ULTRA", "").strip().lower() in _RTK_TRUTHY


def _rtk_min_command_chars() -> int:
    """Return the minimum command length for RTK rewrites."""
    raw = os.environ.get("HEPHAISTOS_RTK_MIN_COMMAND_CHARS", "0").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _rtk_command_prefix(command: str) -> list[str] | None:
    """Return an RTK argv prefix for a simple shell command, if safe to rewrite."""
    stripped = command.strip()
    if not stripped or stripped.startswith("rtk "):
        return None
    if len(stripped) < _rtk_min_command_chars():
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
    if _rtk_ultra_compact():
        prefix.append("--ultra-compact")
    return [*prefix, *argv]


def run_bash(command: str, timeout: int | None = None, **_kwargs: object) -> str:
    """Execute a shell command and return structured output."""
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
    rtk_argv = _rtk_command_prefix(command) if _rtk_enabled() else None
    try:
        if rtk_argv is None:
            result = subprocess.run(  # nosec B602
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=actual_timeout,
                check=False,
            )  # nosec B602
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
                fallback = subprocess.run(  # nosec B602
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=actual_timeout,
                    check=False,
                )  # nosec B602
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
    """Read a file from the workspace."""
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
    """Write content to a file in the workspace."""
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
    """Replace old_text with new_text in a workspace file."""
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
    """List files in a workspace directory."""
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
    """Create or repair a Hephaistos armory inside the workspace."""
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
        "User study files belong in materials/.",
        "Internal Hephaistos state belongs in .hephaistos/.",
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
    """Validate a Hephaistos armory inside the workspace."""
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
            f"Valid Hephaistos armory: {target}\n"
            "Use materials/ for user study files. .hephaistos/ is internal state."
        ),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": str(MARKER_FILE),
        },
    )


def run_search_files(
    pattern: str,
    *,
    workspace: Path,
    path: str = "",
    case_sensitive: bool = False,
    abort: threading.Event | None = None,
    **_kwargs: object,
) -> ToolHandlerResult:
    """Search for text patterns across armory documents."""
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
            return ToolResult(
                success=False,
                content=f"Search cancelled after scanning {file_count} files.",
                metadata={"files_scanned": file_count, "matches": len(matches)},
                error="cancelled",
            )
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(workspace)
        if any(part.startswith(".") for part in rel.parts):
            continue
        suffix = file_path.suffix.lower()
        if suffix in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz"):
            continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                matches.append(f"{rel}:{line_no}: {line.strip()}")
                if len(matches) >= _MAX_SEARCH_RESULTS:
                    break
        file_count += 1
        if len(matches) >= _MAX_SEARCH_RESULTS:
            break

    if not matches:
        return f"No matches found for '{pattern}' in {file_count} files."

    header = f"Found {len(matches)} matches for '{pattern}':"
    if len(matches) >= _MAX_SEARCH_RESULTS:
        header += f" (showing first {_MAX_SEARCH_RESULTS})"
    return header + "\n" + "\n".join(matches)


def run_web_fetch(url: str, timeout: int | None = None, **_kwargs: object) -> str:
    """Fetch a URL and return the text content with source attribution.

    This tool is for filling knowledge gaps that cannot be answered from
    the armory documents.  The response always includes the source URL
    so the user can verify the information.
    """
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname:
        # Resolve once and use the IP directly to prevent DNS rebinding.
        resolved_ips = _resolve_hostname_ips(hostname)
        if not resolved_ips:
            return f"Error: could not resolve host ({hostname})"
        for ip_str in resolved_ips:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return f"Error: blocked private/internal host ({hostname})"
        # Replace hostname with resolved IP, set Host header for virtual hosting.
        first_ip = resolved_ips[0]
        # Format IPv6 addresses with brackets.
        ip_host = f"[{first_ip}]" if ":" in first_ip else first_ip
        netloc = parsed.netloc.replace(hostname, ip_host, 1)
        safe_url = parsed._replace(netloc=netloc).geturl()
        host_header = hostname if not parsed.port else f"{hostname}:{parsed.port}"
    else:
        safe_url = url
        host_header = None

    req = urllib.request.Request(
        safe_url,
        headers={"User-Agent": _WEB_USER_AGENT},
    )
    if host_header:
        req.add_header("Host", host_header)
    try:
        with urllib.request.urlopen(req, timeout=timeout or _WEB_FETCH_TIMEOUT) as resp:  # nosec B310
            content_type = resp.headers.get("Content-Type", "")
            if not any(ct in content_type for ct in ("text", "json", "xml")):
                return f"Error: non-text content type ({content_type}). URL: {url}"
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return f"Error: HTTP {exc.code} fetching {url}"
    except urllib.error.URLError as exc:
        return f"Error: could not reach {url} — {exc.reason}"
    except Exception as exc:
        return f"Error fetching {url}: {exc}"
    if len(raw) > _WEB_FETCH_MAX_CHARS:
        raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"
    if "<html" in raw.lower() or "<body" in raw.lower():
        raw = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        if len(raw) > _WEB_FETCH_MAX_CHARS:
            raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"

    return f"--- Source: {url} ---\n{raw}\n--- End of fetched content ---"


def _mutation_wrap(path_str: str, fn: Callable[..., str], **kwargs: object) -> str:
    """Wrap a file mutation handler with the mutation queue for safety."""
    workspace = kwargs.get("workspace")
    if workspace and isinstance(workspace, Path):
        try:
            target = safe_path(workspace, str(path_str))
            queue = get_queue(workspace)
            return queue.execute(target, fn, **kwargs)
        except ValueError:
            pass  # fall through to direct call
    return fn(**kwargs)


def get_handler(name: str):
    """Return the handler function for a tool name, or None.

    Delegates to the global :data:`default_registry`.
    """
    return default_registry.get_handler(name)


def _queued_write_file(
    path: str,
    content: str,
    *,
    workspace: Path,
    **kwargs: object,
) -> str:
    return _mutation_wrap(
        path,
        run_write_file,
        path=path,
        content=content,
        workspace=workspace,
        **kwargs,
    )


def _queued_edit_file(
    path: str,
    old_text: str,
    new_text: str,
    *,
    workspace: Path,
    **kwargs: object,
) -> str:
    return _mutation_wrap(
        path,
        run_edit_file,
        path=path,
        old_text=old_text,
        new_text=new_text,
        workspace=workspace,
        **kwargs,
    )


def _compact_handler(**_kw: object) -> str:
    return "[compact triggered]"


_HANDLERS: dict[str, Callable[..., ToolHandlerResult]] = {
    "compact": _compact_handler,
    "bash": run_bash,
    "read_file": run_read_file,
    "write_file": _queued_write_file,
    "edit_file": _queued_edit_file,
    "list_files": run_list_files,
    "create_armory": run_create_armory,
    "validate_armory": run_validate_armory,
    "search_files": run_search_files,
    "web_fetch": run_web_fetch,
}

# ---------------------------------------------------------------------------
# Global default registry — pre-loaded with all built-in tools
# ---------------------------------------------------------------------------

default_registry = ToolRegistry()

for _schema in _BUILTIN_SCHEMAS:
    _name = _schema["function"]["name"]
    _handler = _HANDLERS[_name]
    _kind: Literal["normal", "control"] = "control" if _name == "compact" else "normal"
    default_registry.register(ToolSpec(schema=_schema, handler=_handler, kind=_kind))

# Backward-compatible alias: TOOL_SCHEMAS delegates to the registry.
TOOL_SCHEMAS: list[ToolSchema] = default_registry.schemas
