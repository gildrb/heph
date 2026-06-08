"""TUI session state containers.

Named after Codex's focused `session_state` module: these objects persist adapter
state across Textual restarts while workflow/session behavior remains in chat and
workspace services.
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING

from interfaces.terminal.history import InputHistory

if TYPE_CHECKING:
    from hephaion.rag.context import TurnEvidence


@dataclass
class TuiTranscriptEntry:
    content: str
    kind: str = "plain"
    evidence: TurnEvidence | None = None


@dataclass
class TuiRuntimeState:
    transcript: list[TuiTranscriptEntry] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    history_obj: InputHistory | None = None
    history_index: int | None = None
    history_draft: str = ""
    pending_input: str | None = None
    armory_home_shown: bool = False
    startup_card_shown: bool = False


class TuiCaptureWriter(StringIO):
    """TTY-like stream for shared shell commands while the Textual app is parked."""

    encoding = "utf-8"

    def __init__(self, on_line: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.original_stdout = sys.stdout
        self._on_line = on_line
        self._line_buffer = ""
        self._lock = threading.Lock()
        self.emitted_line = False

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return self.original_stdout.fileno()

    def write(self, s: str) -> int:
        with self._lock:
            written = super().write(s)
            if self._on_line is None or not s:
                return written
            self._line_buffer += s
            self._drain_complete_lines()
            return written

    def flush_pending(self) -> None:
        with self._lock:
            if self._on_line is None:
                return
            pending = self._line_buffer.strip()
            self._line_buffer = ""
            if pending:
                self.emitted_line = True
                self._on_line(pending)

    def _drain_complete_lines(self) -> None:
        callback = self._on_line
        if callback is None:
            return
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            clean = line.strip()
            if not clean:
                continue
            self.emitted_line = True
            callback(clean)
