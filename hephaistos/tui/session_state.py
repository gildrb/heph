"""TUI session state containers.

Named after Codex's focused `session_state` module: these objects persist adapter
state across Textual restarts while workflow/session behavior remains in chat and
workspace services.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING

from hephaistos.terminal.history import InputHistory

if TYPE_CHECKING:
    from hephaistos.rag.context import TurnEvidence


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
    tui_started_at: float = field(default_factory=time.monotonic)


class TuiCaptureWriter(StringIO):
    """TTY-like stream for shared shell commands while the Textual app is parked."""

    encoding = "utf-8"

    def __init__(self) -> None:
        super().__init__()
        self.original_stdout = sys.stdout

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return self.original_stdout.fileno()
