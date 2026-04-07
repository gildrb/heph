"""Persistent bash session: maintains shell state across tool calls.

Instead of spawning a fresh subprocess for each command, this module
maintains a long-running bash process with persistent stdin/stdout pipes.
This means:

- ``cd`` changes survive across calls
- Environment variables persist
- Shell aliases and functions can be defined and reused
- Working directory is always accurate

Thread safety: all access is serialized through a threading lock.
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

from hephaistos.logging import get_logger

_log = get_logger("harness.bash_session")

_DEFAULT_TIMEOUT = 30
_MARKER = "__HEPH_RESULT__:"

# Bash wrapper that prints a marker + exit code after each command
_SHELL_INIT = (
    'export PS1=""\n'
    f'_heph_run() {{ eval "$1"; echo "{_MARKER}$?"; }}\n'
)


class BashSession:
    """A persistent bash shell that survives across tool calls.

    Usage::

        session = BashSession(cwd="/path/to/workspace")
        output = session.run("ls -la")  # runs in the persistent shell
        output = session.run("cd subdir && pwd")  # cwd persists
        session.close()
    """

    def __init__(self, cwd: Path | None = None, timeout: int = _DEFAULT_TIMEOUT) -> None:
        self._cwd = cwd or Path.cwd()
        self._timeout = timeout
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._closed = False

    def _ensure_process(self) -> subprocess.Popen:
        """Start the persistent shell if not already running."""
        if self._proc is not None and self._proc.poll() is None:
            return self._proc

        self._proc = subprocess.Popen(
            ["bash", "--norc", "--noprofile", "-s"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._cwd,
            text=True,
            bufsize=0,
        )

        # Send initialization
        assert self._proc.stdin is not None
        self._proc.stdin.write(_SHELL_INIT)
        self._proc.stdin.flush()

        _log.info("bash session started", extra={"fields": {
            "cwd": str(self._cwd),
            "pid": self._proc.pid,
        }})
        return self._proc

    def run(self, command: str, timeout: int | None = None) -> str:
        """Execute a command in the persistent shell.

        Returns stdout + stderr combined, with an exit code indicator.
        """
        timeout = timeout or self._timeout

        with self._lock:
            proc = self._ensure_process()

            if proc.stdin is None or proc.stdout is None or proc.stderr is None:
                return "Error: bash session pipes unavailable"

            try:
                return self._run_locked(proc, command, timeout)
            except Exception as exc:
                _log.warning("bash command failed, restarting session", extra={
                    "fields": {"error": str(exc)}
                })
                self._kill()
                proc = self._ensure_process()
                try:
                    return self._run_locked(proc, command, timeout)
                except Exception as exc2:
                    self._kill()
                    return f"Error running command: {exc2}"

    def _run_locked(self, proc: subprocess.Popen, command: str, timeout: int) -> str:
        """Run a command. Must be called with self._lock held."""
        assert proc.stdin is not None
        assert proc.stdout is not None

        # Write command wrapped in marker function
        # Use a unique delimiter so we can detect the end of output
        proc.stdin.write(f"_heph_run {command!r}\n")
        proc.stdin.flush()

        # Read output until we see the marker
        output_lines: list[str] = []
        deadline_ns = _DEFAULT_TIMEOUT * 1_000_000_000
        import time
        deadline_ns = time.monotonic_ns() + timeout * 1_000_000_000

        while time.monotonic_ns() < deadline_ns:
            line = proc.stdout.readline()
            if not line:
                # Process died
                self._kill()
                return "Error: bash process terminated"

            line_stripped = line.rstrip("\n")

            if line_stripped.startswith(_MARKER):
                exit_code_str = line_stripped[len(_MARKER):]
                try:
                    exit_code = int(exit_code_str)
                except ValueError:
                    exit_code = -1

                result = "\n".join(output_lines)
                if exit_code != 0:
                    result += f"\n[exit code {exit_code}]"
                return result or "(no output)"

            output_lines.append(line_stripped)

        # Timeout
        return f"Command timed out after {timeout}s"

    def _kill(self) -> None:
        """Kill the current process."""
        if self._proc is not None:
            try:
                self._proc.kill()
                self._proc.wait(timeout=2)
            except Exception:
                pass
            self._proc = None

    def close(self) -> None:
        """Shut down the persistent shell."""
        self._closed = True
        self._kill()
        _log.info("bash session closed")

    @property
    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def __del__(self) -> None:
        if not self._closed:
            self.close()


# ---------------------------------------------------------------------------
# Session pool (one per workspace path)
# ---------------------------------------------------------------------------

_sessions: dict[str, BashSession] = {}
_sessions_lock = threading.Lock()


def get_session(workspace: Path, timeout: int = _DEFAULT_TIMEOUT) -> BashSession:
    """Get or create a persistent bash session for a workspace.

    Sessions are cached by workspace path so state persists across tool calls.
    """
    key = str(workspace.resolve())
    with _sessions_lock:
        if key not in _sessions or not _sessions[key].is_alive:
            _sessions[key] = BashSession(cwd=workspace, timeout=timeout)
        return _sessions[key]


def close_all() -> None:
    """Close all cached bash sessions."""
    with _sessions_lock:
        for session in _sessions.values():
            session.close()
        _sessions.clear()
