"""Shell execution handler for agent tools."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess  # nosec B404
import time
from dataclasses import dataclass

from ai.logging import get_logger

_log = get_logger("harness.agent.tools")

_BASH_TIMEOUT = 30
_MAX_READ_CHARS = 50_000
_RTK_TIMEOUT_BUFFER_SECONDS = 5
_RTK_SHELL_META_CHARS = frozenset("|&;<>(){}[]*$?`!~\n")
_RTK_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})
_RTK_FALLBACK_ALLOWED_ENV = "HARNESS_RTK_FALLBACK_ALLOWED"
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
    raw_min_chars = os.environ.get("HARNESS_RTK_MIN_COMMAND_CHARS", "0").strip()
    try:
        return max(0, int(raw_min_chars))
    except ValueError:
        return 0


def _rtk_option_args() -> list[str]:
    if os.environ.get("HARNESS_RTK_ULTRA", "").strip().lower() in _RTK_TRUTHY:
        return ["--ultra-compact"]
    return []


def _rtk_enabled() -> bool:
    rtk_setting = os.environ.get("HARNESS_RTK")
    return rtk_setting is None or rtk_setting.strip().lower() in _RTK_TRUTHY


def _rtk_fallback_allowed() -> bool:
    fallback_setting = os.environ.get(_RTK_FALLBACK_ALLOWED_ENV)
    return fallback_setting is None or fallback_setting.strip().lower() in _RTK_TRUTHY


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
    if not _rtk_enabled():
        return _run_shell_command(command, timeout)

    rtk_argv = _rtk_command_prefix(command)
    if rtk_argv is None:
        fallback_allowed = _rtk_fallback_allowed()
        if _rtk_candidate_argv(command) is not None and shutil.which("rtk") is None:
            _log.warning(
                "rtk command wrapper unavailable",
                extra={"fields": {"error": "rtk not found", "fallback_allowed": fallback_allowed}},
            )
        if not fallback_allowed:
            message = "rtk unavailable or command unsupported and shell fallback disabled"
            raise RuntimeError(message)
        return _run_shell_command(command, timeout)

    try:
        return _run_rtk_command(rtk_argv, timeout)
    except OSError as exc:
        fallback_allowed = _rtk_fallback_allowed()
        _log.warning(
            "rtk command wrapper unavailable",
            extra={"fields": {"error": str(exc), "fallback_allowed": fallback_allowed}},
        )
        if not fallback_allowed:
            raise RuntimeError(f"rtk unavailable and shell fallback disabled: {exc}") from exc
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
