"""TUI-facing session action wrappers."""

from __future__ import annotations

import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.chat.cli import resolve_armory_session as chat_resolve_armory_session
from hephaistos.parameters.cli import load_config
from hephaistos.shell.armory_actions import start_fresh_session as shell_start_fresh_session
from hephaistos.shell.lifecycle import (
    create_startup_session as shell_create_startup_session,
)
from hephaistos.shell.lifecycle import get_history_path as shell_get_history_path
from hephaistos.shell.lifecycle import save_on_exit as shell_save_on_exit
from hephaistos.terminal import current_palette, set_theme
from hephaistos.terminal.history import InputHistory
from hephaistos.terminal.input import handle_input
from hephaistos.tui.dependencies import TuiDependencyError, tui_dependency_message

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession
    from hephaistos.runtime import ChatConfig


def start_fresh_session(session: ChatSession, armory_path: Path | None) -> ChatSession:
    return shell_start_fresh_session(session, armory_path)


def create_startup_session(config: ChatConfig) -> ChatSession:
    return shell_create_startup_session(config)


def get_history_path(session: ChatSession) -> Path:
    return shell_get_history_path(session)


def save_on_exit(session: ChatSession) -> None:
    shell_save_on_exit(session)


def run_tui(session: ChatSession | None = None) -> None:
    tui_module = sys.modules["hephaistos.tui"]

    missing_dependency = any(
        dependency is None
        for dependency in (
            tui_module.Markdown,
            tui_module.Segment,
            tui_module._RichStyle,
            tui_module._RichText,
            tui_module.Input,
            tui_module.OptionList,
            tui_module.RichLog,
            tui_module.Static,
            tui_module.Strip,
        )
    )
    if missing_dependency:
        raise TuiDependencyError(tui_dependency_message())

    if session is None:
        session = tui_module.create_startup_session(load_config())

    set_theme(tui_module.load_app_settings().theme)
    session_ref = [session]
    history_path = tui_module.get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_obj = InputHistory.load(history_path)
    state = tui_module._TuiRuntimeState(
        history=history_obj.entries[-500:],
        history_obj=history_obj,
    )

    try:
        while True:
            palette = current_palette()
            tui_module.HephaistosTui(session_ref[0], state, palette).run(
                mouse=tui_module._TUI_ENABLE_MOUSE
            )

            pending_input = state.pending_input
            state.pending_input = None
            if pending_input is None:
                break

            if pending_input.startswith("!"):
                output = tui_module._run_shell_escape_captured(pending_input[1:].strip())
                if output:
                    state.transcript.append(tui_module._TuiTranscriptEntry(output, "ansi"))
                continue

            history = InputHistory(state.history)
            if tui_module._pending_input_requires_terminal(pending_input):
                new_session, should_continue = handle_input(
                    session_ref[0],
                    pending_input,
                    history,
                )
                session_ref[0] = new_session
                state.history = history.entries
                if not should_continue:
                    break
                continue

            stdout = tui_module._TuiCaptureWriter()
            stderr = tui_module._TuiCaptureWriter()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                new_session, should_continue = handle_input(
                    session_ref[0],
                    pending_input,
                    history,
                )
            session_ref[0] = new_session
            state.history = history.entries

            output = tui_module._command_output_text(stdout, stderr)
            if output:
                state.transcript.append(tui_module._TuiTranscriptEntry(output, "notice"))
            if not should_continue:
                break
    finally:
        if state.history_obj is not None:
            state.history_obj.save(history_path)
        tui_module.save_on_exit(session_ref[0])


def run_tui_for_path(path: Path | None) -> None:
    tui_module = sys.modules["hephaistos.tui"]

    tui_module.run_tui(None if path is None else tui_module.resolve_armory_session(str(path)))


def resolve_armory_session(path: str) -> ChatSession:
    return chat_resolve_armory_session(path)
