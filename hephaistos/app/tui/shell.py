"""Shell-command adapter helpers for the Textual runner."""

from __future__ import annotations

import subprocess  # nosec B404
from io import StringIO


def command_output_text(stdout: StringIO, stderr: StringIO) -> str:
    parts = (stdout.getvalue().strip(), stderr.getvalue().strip())
    return "\n".join(part for part in parts if part)


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
