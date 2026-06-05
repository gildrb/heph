"""TUI-facing session action wrappers."""

from __future__ import annotations

import sys
from contextlib import redirect_stderr, redirect_stdout, suppress
from pathlib import Path
from typing import TYPE_CHECKING

from armory.search import add_known_armory, set_last_armory
from chat import storage as chat_storage
from chat.cli import resolve_armory_session as chat_resolve_armory_session
from chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    empty_armory_guidance,
    save_session,
    session_has_messages,
)
from diagnostics.events import capture as capture_analytics
from parameters.cli import load_config
from terminal import current_palette, print_error, print_info, set_theme
from terminal.history import InputHistory
from terminal.input import handle_input

from tui.dependencies import TuiDependencyError, tui_dependency_message
from tui.startup_discovery import (
    discover_available_armories,
    discover_startup_armory,
)

if TYPE_CHECKING:
    from runtime import ChatConfig

_HISTORY_DIR = Path.home() / ".cache" / "hephaion"


def start_fresh_session(session: ChatSession, armory_path: Path | None) -> ChatSession:
    if armory_path is None and session.armory_path is None:
        return session
    if session.armory_path and session.dirty and session_has_messages(session):
        with suppress(chat_storage.ChatStorageError):
            save_session(session)
    try:
        new_session = (
            create_plain_session(session.config)
            if armory_path is None
            else create_session(session.config, armory_path)
        )
    except SessionError:
        return session
    if armory_path is None:
        capture_analytics("armory_detached", {"model": new_session.config.model})
    else:
        add_known_armory(armory_path)
        set_last_armory(armory_path)
        capture_analytics(
            "armory_attached",
            {
                "source_file_count": new_session.source_file_count,
                "model": new_session.config.model,
            },
        )
    return new_session


def create_startup_session(config: ChatConfig) -> ChatSession:
    armory = discover_startup_armory()
    if armory is None:
        if discover_available_armories():
            print_info("Multiple armories found. Use /armory to choose one.")
        else:
            print_info("No armory attached. Use /armory or `heph armory init <name>`.")
        return create_plain_session(config)
    try:
        session = create_session(config, armory)
        set_last_armory(armory)
        return session
    except SessionError:
        print_error("Auto-discovered armory has no materials.")
        print_info(empty_armory_guidance(armory))
        return create_plain_session(config)


def get_history_path(session: ChatSession) -> Path:
    if session.armory_path is None:
        return _HISTORY_DIR / "plain-history"
    return session.armory_path / ".hephaion" / "history"


def save_on_exit(session: ChatSession) -> None:
    if session.dirty and session_has_messages(session) and session.armory_path is not None:
        try:
            path = save_session(session)
            print_info(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
    session.trace.close()


def _tui_module():
    return sys.modules["tui"]


def _ensure_tui_dependencies(tui_module) -> None:
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


def _startup_session(tui_module, session: ChatSession | None) -> ChatSession:
    if session is not None:
        return session
    return tui_module.create_startup_session(load_config())


def _runtime_state(tui_module, session: ChatSession):
    history_path = tui_module.get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_obj = InputHistory.load(history_path)
    return (
        tui_module._TuiRuntimeState(
            history=history_obj.entries[-500:],
            history_obj=history_obj,
        ),
        history_path,
    )


def _run_app_once(tui_module, session: ChatSession, state) -> None:
    palette = current_palette()
    tui_module.HephTui(session, state, palette).run(mouse=tui_module._TUI_ENABLE_MOUSE)


def _consume_pending_input(tui_module, session: ChatSession, state) -> tuple[ChatSession, bool]:
    pending_input = state.pending_input
    state.pending_input = None
    if pending_input is None:
        return session, False

    history = InputHistory(state.history)
    if tui_module._pending_input_requires_terminal(pending_input):
        new_session, should_continue = handle_input(session, pending_input, history)
    else:
        stdout = tui_module._TuiCaptureWriter()
        stderr = tui_module._TuiCaptureWriter()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            new_session, should_continue = handle_input(session, pending_input, history)
        output = tui_module._command_output_text(stdout, stderr)
        if output:
            state.transcript.append(tui_module._TuiTranscriptEntry(output, "notice"))
    state.history = history.entries
    return new_session, should_continue


def _save_tui_exit_state(tui_module, session: ChatSession, state, history_path: Path) -> None:
    if state.history_obj is not None:
        state.history_obj.save(history_path)
    tui_module.save_on_exit(session)


def run_tui(session: ChatSession | None = None) -> None:
    tui_module = sys.modules["tui"]
    _ensure_tui_dependencies(tui_module)
    session = _startup_session(tui_module, session)

    set_theme(tui_module.load_app_settings().theme)
    state, history_path = _runtime_state(tui_module, session)

    try:
        while True:
            _run_app_once(tui_module, session, state)
            session, should_continue = _consume_pending_input(tui_module, session, state)
            if not should_continue:
                break
    finally:
        _save_tui_exit_state(tui_module, session, state, history_path)


def run_tui_for_path(path: Path | None) -> None:
    tui_module = sys.modules["tui"]

    tui_module.run_tui(None if path is None else tui_module.resolve_armory_session(str(path)))


def resolve_armory_session(path: str) -> ChatSession:
    return chat_resolve_armory_session(path)
