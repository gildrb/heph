"""Command-output helpers for the Textual runner."""

from __future__ import annotations

import re
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


def is_command_activity_line(line: str) -> bool:
    return _command_activity_detail(line) is not None


def _command_activity_detail(line: str) -> str | None:
    clean = _ANSI_ESCAPE_RE.sub("", line).strip()
    if not clean.casefold().startswith("info:"):
        return None
    detail = clean[len("info:") :].strip()
    if detail.casefold().startswith(_COMMAND_ACTIVITY_PREFIXES):
        return detail
    return None
