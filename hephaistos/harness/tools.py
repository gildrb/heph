"""Tool definitions and handlers for the agent harness.

Each tool has a JSON schema (for the OpenAI tools= param) and a handler
function.  Handlers receive the workspace root for path sandboxing.
"""

from __future__ import annotations

import subprocess
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
            "description": "Run a shell command and return stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
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


def run_bash(command: str, **_kwargs: object) -> str:
    """Execute a shell command and return stdout + stderr."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=_BASH_TIMEOUT,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n--- stderr ---\n" + result.stderr) if output else result.stderr
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}]"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {_BASH_TIMEOUT}s"
    except Exception as exc:
        return f"Error running command: {exc}"


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
