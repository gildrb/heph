"""Input history helpers for the TUI."""

from __future__ import annotations

from typing import Protocol

from textual.widgets import Input

from tui.session_state import TuiRuntimeState


class _HistoryHost(Protocol):
    state: TuiRuntimeState

    def query_one(self, selector: str, expect_type: type[Input]) -> Input: ...


class TuiHistoryMixin:
    def _record_history(self: _HistoryHost, value: str) -> None:
        value = value.strip()
        if not value:
            return
        if not self.state.history or self.state.history[-1] != value:
            self.state.history.append(value)
            self.state.history = self.state.history[-500:]
            if self.state.history_obj is not None:
                self.state.history_obj.add(value)
        self.state.history_index = None
        self.state.history_draft = ""

    def _history_previous(self: _HistoryHost) -> None:
        if not self.state.history:
            return
        composer = self.query_one("#composer", Input)
        if self.state.history_index is None:
            self.state.history_draft = composer.value
            self.state.history_index = len(self.state.history) - 1
        else:
            self.state.history_index = max(0, self.state.history_index - 1)
        composer.value = self.state.history[self.state.history_index]
        composer.cursor_position = len(composer.value)

    def _history_next(self: _HistoryHost) -> None:
        if self.state.history_index is None:
            return
        composer = self.query_one("#composer", Input)
        if self.state.history_index >= len(self.state.history) - 1:
            composer.value = self.state.history_draft
            self.state.history_index = None
            self.state.history_draft = ""
        else:
            self.state.history_index += 1
            composer.value = self.state.history[self.state.history_index]
        composer.cursor_position = len(composer.value)
