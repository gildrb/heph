"""External command and managed-resend behavior for the Heph TUI."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING, ParamSpec, Protocol

from hephaion.parameters.settings import (
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
from interfaces.tui.slash_completion import slash_command_name as _slash_command_name
from interfaces.tui.status import config_error as _config_error
from interfaces.tui.streaming import run_tui_turn

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

    from interfaces.tui.command_access import CommandResult
    from interfaces.tui.session_state import TuiRuntimeState

_P = ParamSpec("_P")

_RESEND_PREFIX = "__RESEND__:"
_TUI_MANAGED_RESEND_COMMANDS = {"exam"}


@dataclass(slots=True)
class _ManagedResendCommand:
    result: CommandResult
    output: str
    resend_input: str


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

    def _append_user(self, text: str) -> None: ...

    def _append_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_activity(self, text: str) -> None: ...

    def _append_assistant_reply(self, text: str) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _refresh_status(self) -> None: ...

    def _finish_turn(self) -> None: ...

    def _run_external_command(self, value: str) -> None: ...

    def _run_tui_managed_resend_command(
        self,
        value: str,
        history: InputHistory,
        activity_trace_mode: str,
    ) -> bool: ...

    def _run_managed_resend_command(
        self,
        value: str,
        history: InputHistory,
        activity_trace_mode: str,
    ) -> _ManagedResendCommand | None: ...

    def _run_resend_input(self, resend_input: str, history: InputHistory) -> None: ...

    def _run_resend_chat_turn(self, resend_input: str) -> None: ...

    def _finish_managed_resend_command(
        self,
        history: InputHistory,
        *,
        output: str = "",
        should_continue: bool = True,
    ) -> None: ...

    def _finish_external_command(
        self,
        new_session: ChatSession,
        history_entries: list[str],
        output: str,
        should_continue: bool,
    ) -> None: ...


def _managed_resend_output(captured_output: str, command_output: str | None) -> tuple[str, str]:
    if not command_output:
        return captured_output, ""
    if command_output.startswith(_RESEND_PREFIX):
        return captured_output, command_output[len(_RESEND_PREFIX) :]
    return "\n".join(part for part in (captured_output, command_output) if part), ""


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
        self._append_user(value)
        self.busy = True
        self.abort_event.clear()
        self._refresh_status()
        self.run_worker(lambda: self._run_external_command(value), thread=True)

    def _run_external_command(self: _ExternalCommandHost, value: str) -> None:
        from interfaces.terminal.input import handle_input

        history = InputHistory(self.state.history)
        activity_trace_mode = load_app_settings().activity_trace_mode
        command_name = _slash_command_name(value)
        if command_name in _TUI_MANAGED_RESEND_COMMANDS:
            handled = self._run_tui_managed_resend_command(value, history, activity_trace_mode)
            if handled:
                return

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

    def _run_tui_managed_resend_command(
        self: _ExternalCommandHost,
        value: str,
        history: InputHistory,
        activity_trace_mode: str,
    ) -> bool:
        command = self._run_managed_resend_command(value, history, activity_trace_mode)
        if command is None:
            return False

        if command.output:
            self.call_from_thread(self._append_notice, command.output)

        if command.result.should_exit:
            self._finish_managed_resend_command(history, should_continue=False)
            return True
        if not command.resend_input:
            self._finish_managed_resend_command(history)
            return True

        self._run_resend_input(command.resend_input, history)
        return True

    def _run_managed_resend_command(
        self: _ExternalCommandHost,
        value: str,
        history: InputHistory,
        activity_trace_mode: str,
    ) -> _ManagedResendCommand | None:
        from interfaces.tui.command_access import get_registry

        history.add(value)
        command_name, _, command_args = value.strip()[1:].partition(" ")
        cmd = get_registry().find(command_name.lower())
        if cmd is None:
            return None

        stdout = _TuiCaptureWriter()
        stderr = _TuiCaptureWriter()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = cmd.handle(self.session, command_args.strip())
        if result.new_session is not None:
            self.session = result.new_session

        output = _captured_command_output(stdout, stderr, activity_trace_mode)
        output, resend_input = _managed_resend_output(output, result.output)
        self.state.history = history.entries
        return _ManagedResendCommand(result=result, output=output, resend_input=resend_input)

    def _run_resend_input(
        self: _ExternalCommandHost,
        resend_input: str,
        history: InputHistory,
    ) -> None:
        history.add(resend_input)
        self.state.history = history.entries
        config_error = _config_error(self.session)
        if config_error is not None:
            self.call_from_thread(self._append_error, config_error)
            self._finish_managed_resend_command(history)
            return

        self._run_resend_chat_turn(resend_input)

    def _run_resend_chat_turn(self: _ExternalCommandHost, resend_input: str) -> None:
        def on_reply(reply: str) -> None:
            self.call_from_thread(self._append_assistant_reply, reply)

        def on_notice(notice: str) -> None:
            self.call_from_thread(self._append_notice, notice)

        def on_activity(line: str) -> None:
            self.call_from_thread(self._append_activity, line)

        def on_error(error: str) -> None:
            self.call_from_thread(self._append_error, error)

        def on_finish() -> None:
            self.call_from_thread(self._finish_turn)

        run_tui_turn(
            self.session,
            resend_input,
            self.abort_event,
            on_reply=on_reply,
            on_notice=on_notice,
            on_error=on_error,
            on_finish=on_finish,
            on_activity=on_activity,
        )

    def _finish_managed_resend_command(
        self: _ExternalCommandHost,
        history: InputHistory,
        *,
        output: str = "",
        should_continue: bool = True,
    ) -> None:
        self.call_from_thread(
            self._finish_external_command,
            self.session,
            history.entries,
            output,
            should_continue,
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
