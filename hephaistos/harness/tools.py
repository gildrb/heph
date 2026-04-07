"""Tool definitions and handlers for the agent harness.

Each tool has a JSON schema (for the OpenAI tools= param) and a handler
function.  Handlers receive the workspace root for path sandboxing.

Tool philosophy for a study RAG agent:
- Read/write tools are primary — the agent works with documents.
- Bash is available but strictly limited (timeout, structured output).
- Web fetch fills knowledge gaps, but with strict source attribution.
- The agent should NEVER guess. If information is not in the documents
  and cannot be fetched, it must say so.
"""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Path sandboxing
# ---------------------------------------------------------------------------


def safe_path(workspace: Path, rel_path: str) -> Path:
    """Resolve *rel_path* inside *workspace* and ensure it doesn't escape."""
    resolved = (workspace / rel_path).resolve()
    if not resolved.is_relative_to(workspace.resolve()):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved


# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "compact",
            "description": (
                "Compress the conversation context to free up space. "
                "Use when you notice the conversation is getting long or "
                "you are running low on context."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return structured output with exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30).",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from workspace root.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (0-based).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from workspace root.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace an exact text match in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from workspace root.",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "The exact text to find.",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "The replacement text.",
                    },
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path. Defaults to workspace root.",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g. '*.py').",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Fetch a web page and return its text content. "
                "Use ONLY when the answer cannot be found in the armory documents. "
                "The response always includes the source URL for verification. "
                "Do NOT guess or fabricate information — if the fetch fails or "
                "doesn't contain the answer, say so explicitly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch (must start with http:// or https://).",
                    },
                },
                "required": ["url"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

_BASH_TIMEOUT = 30
_MAX_READ_CHARS = 50_000
_WEB_FETCH_TIMEOUT = 15
_WEB_FETCH_MAX_CHARS = 20_000
_WEB_USER_AGENT = "Hephaistos/0.1 (study agent)"


# ---------------------------------------------------------------------------
# Structured bash result
# ---------------------------------------------------------------------------


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


def run_bash(command: str, timeout: int | None = None, **_kwargs: object) -> str:
    """Execute a shell command and return structured output."""
    import time as _time

    actual_timeout = timeout or _BASH_TIMEOUT
    start = _time.monotonic()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=actual_timeout,
        )
        elapsed = _time.monotonic() - start
        br = BashResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.returncode,
            timed_out=False,
            duration_seconds=round(elapsed, 2),
        )
        output = br.to_display()
    except subprocess.TimeoutExpired:
        elapsed = _time.monotonic() - start
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


# ---------------------------------------------------------------------------
# Web fetch tool
# ---------------------------------------------------------------------------


def run_web_fetch(url: str, **_kwargs: object) -> str:
    """Fetch a URL and return the text content with source attribution.

    This tool is for filling knowledge gaps that cannot be answered from
    the armory documents.  The response always includes the source URL
    so the user can verify the information.
    """
    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": _WEB_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=_WEB_FETCH_TIMEOUT) as resp:
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

    # Truncate
    if len(raw) > _WEB_FETCH_MAX_CHARS:
        raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"

    # Strip HTML tags if it looks like HTML (basic)
    if "<html" in raw.lower() or "<body" in raw.lower():
        # Remove script/style blocks
        raw = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", raw, flags=re.IGNORECASE)
        # Remove tags
        raw = re.sub(r"<[^>]+>", " ", raw)
        # Collapse whitespace
        raw = re.sub(r"\s+", " ", raw).strip()
        if len(raw) > _WEB_FETCH_MAX_CHARS:
            raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"

    return (
        f"--- Source: {url} ---\n"
        f"{raw}\n"
        f"--- End of fetched content ---"
    )


# ---------------------------------------------------------------------------
# Dispatch map
# ---------------------------------------------------------------------------

def get_handler(name: str):
    """Return the handler function for a tool name, or None."""
    return _HANDLERS.get(name)


_HANDLERS: dict[str, callable] = {
    "compact": lambda **_kw: "[compact triggered]",
    "bash": lambda **kw: run_bash(kw["command"], timeout=kw.get("timeout")),
    "read_file": lambda **kw: run_read_file(kw["path"], offset=kw.get("offset"), limit=kw.get("limit"), **_workspace_kw(kw)),
    "write_file": lambda **kw: run_write_file(kw["path"], kw["content"], **_workspace_kw(kw)),
    "edit_file": lambda **kw: run_edit_file(kw["path"], kw["old_text"], kw["new_text"], **_workspace_kw(kw)),
    "list_files": lambda **kw: run_list_files(path=kw.get("path", ""), pattern=kw.get("pattern", "*"), **_workspace_kw(kw)),
    "web_fetch": lambda **kw: run_web_fetch(kw["url"]),
}


def _workspace_kw(kw: dict) -> dict:
    """Extract workspace from kwargs if present."""
    ws = kw.get("workspace")
    return {"workspace": ws} if ws is not None else {}
