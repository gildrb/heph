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


def command_output_text(stdout: StringIO, stderr: StringIO) -> str:
    parts = (stdout.getvalue().strip(), stderr.getvalue().strip())
    return "\n".join(part for part in parts if part)


def filter_command_activity_details(text: str) -> str:
    kept = [line for line in text.splitlines() if not _is_command_activity_detail(line)]
    return "\n".join(kept).strip()


def _is_command_activity_detail(line: str) -> bool:
    clean = _ANSI_ESCAPE_RE.sub("", line).strip().casefold()
    if not clean.startswith("info:"):
        return False
    detail = clean.removeprefix("info:").strip()
    return detail.startswith(_COMMAND_ACTIVITY_PREFIXES)


def run_shell_escape_captured(command: str) -> str:
    """Run a user-requested shell escape and return output for the TUI transcript."""
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
