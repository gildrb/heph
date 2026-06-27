from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from harness.chat.session import save_session

from interfaces.tui.streaming import run_tui_turn

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class _TurnHost(Protocol):
    session: ChatSession
    abort_event: threading.Event
    _active_turns: dict[str, threading.Event]
    _active_turn_sessions: dict[str, ChatSession]
    _active_turn_tokens: dict[str, int]
    _cancelled_turn_tokens: set[int]
    _turn_sessions: dict[str, ChatSession]
    busy: bool
    _side_panel_progress: str

    def call_from_thread(
        self,
        callback: Callable[..., object],
        *args: object,
    ) -> object: ...

    def _append_activity(self, text: str) -> None: ...

    def _append_assistant_reply(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_notice(self, text: str) -> None: ...

    def _finish_turn(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _current_turn_key(self) -> str: ...

    def _finish_background_turn(
        self,
        turn_key: str,
        turn_session: ChatSession,
        turn_token: int | None = None,
    ) -> None: ...

    def _handle_turn_activity(self, turn_key: str, turn_token: int | None, line: str) -> None: ...

    def _handle_turn_error(self, turn_key: str, turn_token: int | None, error: str) -> None: ...

    def _handle_turn_notice(self, turn_key: str, turn_token: int | None, notice: str) -> None: ...

    def _handle_turn_progress(
        self, turn_key: str, turn_token: int | None, progress: str
    ) -> None: ...

    def _handle_turn_reply(self, turn_key: str, turn_token: int | None, reply: str) -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _turn_is_visible(self, turn_key: str) -> bool: ...

    def _turn_accepts_callback(self, turn_key: str, turn_token: int | None) -> bool: ...

    def _turn_key_for_armory_path(self, armory_path: Path) -> str: ...

    def _turn_key_for_session(self, session: ChatSession) -> str: ...


class TuiTurnMixin:
    def _turn_key_for_session(self: _TurnHost, session: ChatSession) -> str:
        if session.armory_path is not None:
            return self._turn_key_for_armory_path(session.armory_path)
        return f"session:{session.session_id}"

    def _turn_key_for_armory_path(self: _TurnHost, armory_path: Path) -> str:
        return f"armory:{armory_path.expanduser().resolve(strict=False)}"

    def _current_turn_key(self: _TurnHost) -> str:
        return self._turn_key_for_session(self.session)

    def _turn_is_visible(self: _TurnHost, turn_key: str) -> bool:
        return self._current_turn_key() == turn_key

    def _turn_accepts_callback(self: _TurnHost, turn_key: str, turn_token: int | None) -> bool:
        if turn_token is not None:
            if turn_token in self._cancelled_turn_tokens:
                return False
            if self._active_turn_tokens.get(turn_key) != turn_token:
                return False
        return self._turn_is_visible(turn_key)

    def _sync_busy_to_current_session(self: _TurnHost) -> None:
        abort_event = self._active_turns.get(self._current_turn_key())
        self.busy = abort_event is not None
        self.abort_event = abort_event or threading.Event()
        self._refresh_status()
        self._refresh_footer_hints()

    def _handle_turn_reply(
        self: _TurnHost,
        turn_key: str,
        turn_token: int | None,
        reply: str,
    ) -> None:
        if not self._turn_accepts_callback(turn_key, turn_token):
            return
        self._append_assistant_reply(reply)

    def _handle_turn_notice(
        self: _TurnHost,
        turn_key: str,
        turn_token: int | None,
        notice: str,
    ) -> None:
        if self._turn_accepts_callback(turn_key, turn_token):
            self._append_notice(notice)

    def _handle_turn_progress(
        self: _TurnHost,
        turn_key: str,
        turn_token: int | None,
        progress: str,
    ) -> None:
        if self._turn_accepts_callback(turn_key, turn_token):
            self._side_panel_progress = progress
            self._update_info_panel()

    def _handle_turn_activity(
        self: _TurnHost,
        turn_key: str,
        turn_token: int | None,
        line: str,
    ) -> None:
        if self._turn_accepts_callback(turn_key, turn_token):
            self._append_activity(line)

    def _handle_turn_error(
        self: _TurnHost,
        turn_key: str,
        turn_token: int | None,
        error: str,
    ) -> None:
        if self._turn_accepts_callback(turn_key, turn_token):
            self._append_error(error)

    def _finish_background_turn(
        self: _TurnHost,
        turn_key: str,
        turn_session: ChatSession,
        turn_token: int | None = None,
    ) -> None:
        is_current_run = turn_token is None or self._active_turn_tokens.get(turn_key) == turn_token
        if is_current_run:
            self._active_turns.pop(turn_key, None)
            self._active_turn_sessions.pop(turn_key, None)
            self._active_turn_tokens.pop(turn_key, None)
            self._turn_sessions[turn_key] = turn_session
        if turn_token is not None:
            self._cancelled_turn_tokens.discard(turn_token)
        if turn_session.armory_path is not None and turn_session.dirty:
            with contextlib.suppress(Exception):
                save_session(turn_session)
        if is_current_run and self._turn_is_visible(turn_key):
            self._finish_turn()
            return
        self._sync_busy_to_current_session()

    def _run_turn(
        self: _TurnHost,
        turn_session: ChatSession,
        turn_key: str,
        turn_token: int,
        abort_event: threading.Event,
        user_input: str,
    ) -> None:
        last_activity_line = ""

        def on_reply(reply: str) -> None:
            self.call_from_thread(self._handle_turn_reply, turn_key, turn_token, reply)

        def on_notice(notice: str) -> None:
            self.call_from_thread(self._handle_turn_notice, turn_key, turn_token, notice)

        def on_activity(line: str) -> None:
            nonlocal last_activity_line
            if line == last_activity_line:
                return
            last_activity_line = line
            self.call_from_thread(self._handle_turn_activity, turn_key, turn_token, line)

        def on_progress(progress: str) -> None:
            self.call_from_thread(self._handle_turn_progress, turn_key, turn_token, progress)

        def on_error(error: str) -> None:
            self.call_from_thread(self._handle_turn_error, turn_key, turn_token, error)

        def on_finish() -> None:
            self.call_from_thread(self._finish_background_turn, turn_key, turn_session, turn_token)

        run_tui_turn(
            turn_session,
            user_input,
            abort_event,
            on_reply=on_reply,
            on_notice=on_notice,
            on_error=on_error,
            on_finish=on_finish,
            on_progress=on_progress,
            on_activity=on_activity,
        )
