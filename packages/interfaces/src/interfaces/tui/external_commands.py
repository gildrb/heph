"""External command and managed-resend behavior for the Heph TUI."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from threading import Event
from typing import TYPE_CHECKING, ParamSpec, Protocol

from harness.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    load_app_settings,
)

from interfaces.terminal.history import InputHistory

from interfaces.tui.command_output import (
    command_output_text as _command_output_text,
)
from interfaces.tui.command_output import (
    filter_command_activity_details as _filter_command_activity_details,
)
from interfaces.tui.command_output import (
    format_command_activity_details as _format_command_activity_details,
)
from interfaces.tui.command_output import (
    format_command_activity_line as _format_command_activity_line,
)
from interfaces.tui.command_output import (
    is_command_activity_line as _is_command_activity_line,
)
from interfaces.tui.routing import (
    pending_input_requires_terminal as _pending_input_requires_terminal,
)
from interfaces.tui.session_state import TuiCaptureWriter as _TuiCaptureWriter

if TYPE_CHECKING:
    from harness.chat.session import ChatSession

    from interfaces.tui.session_state import TuiRuntimeState

_P = ParamSpec("_P")


class _ExternalCommandHost(Protocol):
    state: TuiRuntimeState
    session: ChatSession
    abort_event: Event
    busy: bool
    _thinking_label: str

    def exit(self) -> object: ...

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def _append_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_activity(self, text: str) -> None: ...

    def _append_assistant_reply(self, text: str) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _refresh_status(self) -> None: ...

    def _finish_turn(self) -> None: ...

    def _run_external_command(self, value: str) -> None: ...






    def _finish_external_command(
        self,
        new_session: ChatSession,
        history_entries: list[str],
        output: str,
        should_continue: bool,
    ) -> None: ...




def _captured_command_output(
    stdout: _TuiCaptureWriter,
    stderr: _TuiCaptureWriter,
    activity_trace_mode: str,
) -> str:
    output = _command_output_text(stdout, stderr)
    if activity_trace_mode in {
        ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
        ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    }:
        return _filter_command_activity_details(output)
    return _format_command_activity_details(output)


class TuiExternalCommandMixin:
    def _handle_external_input(self: _ExternalCommandHost, value: str) -> None:
        if _pending_input_requires_terminal(value):
            self.state.pending_input = value
            self.exit()
            return

        self._thinking_label = "working"
        self.busy = True
        self.abort_event.clear()
        self._refresh_status()
        self.run_worker(lambda: self._run_external_command(value), thread=True)

    def _run_external_command(self: _ExternalCommandHost, value: str) -> None:
        from interfaces.terminal.input import handle_input

        history = InputHistory(self.state.history)
        activity_trace_mode = load_app_settings().activity_trace_mode
        streamed_line = False
        stream_activity = activity_trace_mode == ACTIVITY_TRACE_TOOL_CALLS

        def stream_notice(line: str) -> None:
            nonlocal streamed_line
            if not _is_command_activity_line(line):
                return
            streamed_line = True
            self.call_from_thread(self._append_notice, _format_command_activity_line(line))

        line_callback = stream_notice if stream_activity else None
        stdout = _TuiCaptureWriter(on_line=line_callback)
        stderr = _TuiCaptureWriter(on_line=line_callback)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            new_session, should_continue = handle_input(self.session, value, history)
        stdout.flush_pending()
        stderr.flush_pending()
        if streamed_line:
            output = _filter_command_activity_details(_command_output_text(stdout, stderr))
        else:
            output = _captured_command_output(stdout, stderr, activity_trace_mode)
        self.call_from_thread(
            self._finish_external_command, new_session, history.entries, output, should_continue
        )






    def _finish_external_command(
        self: _ExternalCommandHost,
        new_session: ChatSession,
        history_entries: list[str],
        output: str,
        should_continue: bool,
    ) -> None:
        self.session = new_session
        self.state.history = history_entries
        if output:
            self._append_entry(output, "notice")
        self._finish_turn()
        if not should_continue:
            self.exit()
