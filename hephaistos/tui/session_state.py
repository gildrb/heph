"""TUI session state containers.

Named after Codex's focused `session_state` module: these objects persist adapter
state across Textual restarts while workflow/session behavior remains in chat and
workspace services.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from io import StringIO

from hephaistos.input_history import InputHistory


@dataclass
class TuiTranscriptEntry:
    content: str
    kind: str = "plain"


@dataclass
class TuiRuntimeState:
    transcript: list[TuiTranscriptEntry] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    history_obj: InputHistory | None = None
    history_index: int | None = None
    history_draft: str = ""
    pending_input: str | None = None
    armory_home_shown: bool = False


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
