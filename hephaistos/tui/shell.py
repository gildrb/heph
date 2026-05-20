"""Shell-command adapter helpers for the Textual runner."""

from __future__ import annotations

import re
import subprocess  # nosec B404
from io import StringIO

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_COMMAND_ACTIVITY_PREFIXES = (
    "built ",
    "checking web-backed ",
    "indexed @",
    "loaded ",
    "model synthesis ",
    "parsed ",
    "pdf compile ",
    "priority report verified ",
    "ran ",
    "ranked ",
    "read ",
    "rendered ",
    "requesting model ",
    "scoring ",
    "waiting on ",
    "wrote ",
)
_ACTIVITY_TRACE_INDENT = "    "


def command_output_text(stdout: StringIO, stderr: StringIO) -> str:
    parts = (stdout.getvalue().strip(), stderr.getvalue().strip())
    return "\n".join(part for part in parts if part)


def filter_command_activity_details(text: str) -> str:
    kept = [line for line in text.splitlines() if _command_activity_detail(line) is None]
    return "\n".join(kept).strip()


def format_command_activity_details(text: str) -> str:
    lines = [format_command_activity_line(line) for line in text.splitlines()]
    return "\n".join(lines).strip()


def format_command_activity_line(line: str) -> str:
    detail = _command_activity_detail(line)
    if detail is None:
        return line
    return f"{_ACTIVITY_TRACE_INDENT}{detail}"


def _command_activity_detail(line: str) -> str | None:
    clean = _ANSI_ESCAPE_RE.sub("", line).strip()
    if not clean.casefold().startswith("info:"):
        return None
    detail = clean[len("info:") :].strip()
    if detail.casefold().startswith(_COMMAND_ACTIVITY_PREFIXES):
        return detail
    return None


def run_shell_escape_captured(command: str) -> str:
    if not command:
        return ""

    parts = [f"$ {command}"]
    try:
        result = subprocess.run(  # nosec B602
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        parts.append(f"error: {exc}")
        return "\n".join(parts)

    if result.stdout:
        parts.append(result.stdout.rstrip("\n"))
    if result.stderr:
        parts.append(result.stderr.rstrip("\n"))
    return "\n".join(parts)
