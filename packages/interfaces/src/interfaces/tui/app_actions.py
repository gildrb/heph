"""Submission, command, search, and thinking actions for the TUI app."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import threading
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol, TypeVar

from hephaion.armory.search import SearchResult

from interfaces.tui.command_access import get_registry
from interfaces.tui.display_text import armory_home_text as _armory_home_text
from interfaces.tui.display_text import new_chat_card_text as _new_chat_card_text
from interfaces.tui.ids import COMPOSER_SELECTOR, TRANSCRIPT_SELECTOR
from interfaces.tui.routing import TuiInputRoute as _TuiInputRoute
from interfaces.tui.routing import local_picker_query as _local_picker_query
from interfaces.tui.routing import tui_input_route as _tui_input_route
from interfaces.tui.search_screen import SearchScreen
from interfaces.tui.status import config_error as _config_error

try:
    from textual.widgets import Input, RichLog, Static
except ImportError:
    Input = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from textual.widget import Widget

    from interfaces.tui.flow_state import InlineFlow
    from interfaces.tui.session_state import TuiRuntimeState

_WidgetT = TypeVar("_WidgetT")

_INLINE_COMMANDS = {"/login", "/local", "/logout", "/settings", "/models"}
_THINKING_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class _TimerLike(Protocol):
    def stop(self) -> None: ...


class _AppActionsHost(Protocol):
    session: ChatSession
    state: TuiRuntimeState
    abort_event: threading.Event
    busy: bool

    @property
    def completion_candidates(self) -> Sequence[object]: ...

    _active_turns: dict[str, threading.Event]
    _active_turn_sessions: dict[str, ChatSession]
    _turn_sessions: dict[str, ChatSession]
    _inline_flow: InlineFlow
    _armory_inline_active: bool
    _armory_creating: bool
    _armory_filter: str
    _materials_inline_active: bool
    _thinking_timer: _TimerLike | None
    _thinking_start: float
    _thinking_label: str
    _focused_msg_index: int | None

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_focus(self, widget: Widget | None) -> None: ...

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def push_screen(
        self,
        screen: SearchScreen,
        callback: Callable[[object], None],
    ) -> object: ...

    def set_interval(self, interval: float, callback: Callable[[], object]) -> _TimerLike: ...

    def _submit_composer_value(self, *, apply_highlighted_completion: bool) -> None: ...

    def _composer_submission_value(
        self,
        composer: Input,
        apply_highlighted_completion: bool,
    ) -> str: ...

    def _clear_submitted_composer(self, composer: Input) -> None: ...

    def _submit_routed_value(self, route: _TuiInputRoute, value: str) -> None: ...

    def _submit_external_value(self, value: str) -> None: ...

    def _submit_chat_value(self, value: str) -> None: ...

    def _submit_active_inline_surface(self, composer: Input, value: str) -> bool: ...

    def _submit_special_route(self, route: _TuiInputRoute, value: str) -> bool: ...

    def _submit_materials_route(self, value: str) -> None: ...

    def _submit_sessions_route(self, value: str) -> None: ...

    def _submit_turn_route(self, value: str) -> None: ...

    def _submit_local_route(self, value: str) -> None: ...

    def _submit_new_route(self, value: str) -> None: ...

    def _submit_detach_route(self, value: str) -> None: ...

    def _submit_armory_route(self, value: str) -> None: ...

    def _submit_live_tokens_route(self, value: str) -> None: ...

    def _submit_thinking_visibility_route(self, value: str) -> None: ...

    def _submit_live_tokens_command(self, value: str) -> None: ...

    def _submit_thinking_visibility_command(self, value: str) -> None: ...

    def _submit_busy_value(self, route: _TuiInputRoute, value: str) -> bool: ...

    def _open_armory_reference_from_input(self, value: str) -> bool: ...

    def _detach_current_armory_from_input(self, value: str) -> bool: ...

    def _start_chat_turn(self, value: str) -> None: ...

    def _handle_new(self) -> None: ...

    def _handle_detach(self) -> None: ...

    def _open_search(self) -> None: ...

    def _tick_thinking(self) -> None: ...

    def _stop_thinking_animation(self) -> None: ...

    def _completion_menu_visible(self) -> bool: ...

    def _apply_highlighted_completion(self) -> None: ...

    def _hide_completions(self) -> None: ...

    def _refresh_completions(self) -> None: ...

    def _submit_inline_flow(self, value: str) -> None: ...

    def _record_history(self, value: str) -> None: ...

    def _handle_external_input(self, value: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _create_inline_armory(self, name: str) -> None: ...

    def _armory_open_highlighted(self) -> None: ...

    def _refresh_armory_inline(self) -> None: ...

    def _close_materials_inline(self) -> None: ...

    def _append_user(self, text: str, *, mark_working: bool = True) -> None: ...

    def _handle_inline_command(self, value: str) -> None: ...

    def _open_local_flow(self, query: str = "") -> None: ...

    def _open_materials_inline(self, value: str) -> None: ...

    def _handle_sessions_command(self, value: str) -> None: ...

    def _handle_turn_command(self, value: str) -> None: ...

    def _handle_armory_browser(self, value: str) -> None: ...

    def _append_notice(self, text: str) -> None: ...

    def _turn_key_for_session(self, session: ChatSession) -> str: ...

    def _refresh_status(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _run_turn(
        self,
        turn_session: ChatSession,
        turn_key: str,
        abort_event: threading.Event,
        user_input: str,
    ) -> None: ...

    def _current_turn_key(self) -> str: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _append_plain(self, text: str) -> None: ...

    def _append_armory_home(self) -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _update_info_panel(self) -> None: ...


class TuiAppActionsMixin:
    session: ChatSession
    state: TuiRuntimeState
    abort_event: threading.Event
    busy: bool
    _active_turns: dict[str, threading.Event]
    _active_turn_sessions: dict[str, ChatSession]
    _turn_sessions: dict[str, ChatSession]
    _inline_flow: InlineFlow
    _armory_inline_active: bool
    _armory_creating: bool
    _armory_filter: str
    _materials_inline_active: bool
    _thinking_timer: _TimerLike | None
    _thinking_start: float
    _thinking_label: str
    _focused_msg_index: int | None

    def on_input_submitted(self: _AppActionsHost, event: Input.Submitted) -> None:
        del event
        self._submit_composer_value(apply_highlighted_completion=True)

    def _submit_composer_value(
        self: _AppActionsHost,
        *,
        apply_highlighted_completion: bool,
    ) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        if self._inline_flow.active:
            self._submit_inline_flow(composer.value.strip())
            return
        value = self._composer_submission_value(composer, apply_highlighted_completion)
        if self._submit_active_inline_surface(composer, value):
            return
        route = _tui_input_route(value)
        self._clear_submitted_composer(composer)
        self._submit_routed_value(route, value)

    def _submit_routed_value(
        self: _AppActionsHost,
        route: _TuiInputRoute,
        value: str,
    ) -> None:
        if route is _TuiInputRoute.EMPTY:
            return
        if self._submit_special_route(route, value):
            return
        if route is _TuiInputRoute.CHAT and self._detach_current_armory_from_input(value):
            return
        if self.busy:
            self._submit_busy_value(route, value)
            return
        if route is _TuiInputRoute.CHAT and self._open_armory_reference_from_input(value):
            return
        route_handlers = {
            _TuiInputRoute.EXTERNAL: self._submit_external_value,
            _TuiInputRoute.CHAT: self._submit_chat_value,
        }
        if handler := route_handlers.get(route):
            handler(value)

    def _composer_submission_value(
        self: _AppActionsHost,
        composer: Input,
        apply_highlighted_completion: bool,
    ) -> str:
        if (
            apply_highlighted_completion
            and self._completion_menu_visible()
            and self.completion_candidates
        ):
            self._apply_highlighted_completion()
        return composer.value.strip()

    def _clear_submitted_composer(self: _AppActionsHost, composer: Input) -> None:
        composer.value = ""
        self._hide_completions()

    def _submit_external_value(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_external_input(value)

    def _submit_chat_value(self: _AppActionsHost, value: str) -> None:
        config_error = _config_error(self.session)
        if config_error is not None:
            self._append_error(config_error)
            return
        self._start_chat_turn(value)

    def _submit_active_inline_surface(
        self: _AppActionsHost,
        composer: Input,
        value: str,
    ) -> bool:
        if self._armory_inline_active:
            if self._armory_creating:
                self._create_inline_armory(value)
            else:
                composer.value = ""
                self._armory_filter = ""
                self._armory_open_highlighted()
                self._refresh_armory_inline()
            return True
        if self._materials_inline_active:
            self._close_materials_inline()
            return True
        return False

    def _submit_special_route(
        self: _AppActionsHost,
        route: _TuiInputRoute,
        value: str,
    ) -> bool:
        route_handlers = {
            _TuiInputRoute.MATERIALS: self._submit_materials_route,
            _TuiInputRoute.SESSIONS: self._submit_sessions_route,
            _TuiInputRoute.TURN: self._submit_turn_route,
            _TuiInputRoute.LOCAL: self._submit_local_route,
            _TuiInputRoute.NEW: self._submit_new_route,
            _TuiInputRoute.DETACH: self._submit_detach_route,
            _TuiInputRoute.ARMORY: self._submit_armory_route,
            _TuiInputRoute.LIVE_TOKENS: self._submit_live_tokens_route,
            _TuiInputRoute.THINKING_VISIBILITY: self._submit_thinking_visibility_route,
        }
        if handler := route_handlers.get(route):
            handler(value)
            return True
        if value in _INLINE_COMMANDS:
            self._handle_inline_command(value)
            return True
        return False

    def _submit_materials_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._open_materials_inline(value)

    def _submit_sessions_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_sessions_command(value)

    def _submit_turn_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_turn_command(value)

    def _submit_local_route(self: _AppActionsHost, value: str) -> None:
        query = _local_picker_query(value)
        if query is None:
            self._submit_external_value(value)
            return
        self._open_local_flow(query)

    def _submit_new_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_new()

    def _submit_detach_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_detach()

    def _detach_current_armory_from_input(self: _AppActionsHost, value: str) -> bool:
        if self.session.armory_path is None or value.strip() != "detach":
            return False
        self._submit_detach_route(value)
        return True

    def _submit_armory_route(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._handle_armory_browser(value)

    def _submit_live_tokens_route(self: _AppActionsHost, value: str) -> None:
        self._submit_live_tokens_command(value)

    def _submit_thinking_visibility_route(self: _AppActionsHost, value: str) -> None:
        self._submit_thinking_visibility_command(value)

    def _submit_busy_value(
        self: _AppActionsHost,
        route: _TuiInputRoute,
        value: str,
    ) -> bool:
        if route is _TuiInputRoute.CHAT:
            self.session.steering.enqueue(value)
            self._record_history(value)
            self._append_notice(f"Steering queued: {value}")
            return True
        self._record_history(value)
        self._append_notice(f"Command unavailable while this answer is running: {value}")
        return True

    def _start_chat_turn(self: _AppActionsHost, value: str) -> None:
        self._record_history(value)
        self._append_user(value)
        turn_session = self.session
        turn_key = self._turn_key_for_session(turn_session)
        turn_abort_event = threading.Event()
        self._active_turns[turn_key] = turn_abort_event
        self._active_turn_sessions[turn_key] = turn_session
        self._turn_sessions[turn_key] = turn_session
        self.abort_event = turn_abort_event
        self.busy = True
        self._refresh_status()
        self._refresh_footer_hints()
        self.run_worker(
            lambda: self._run_turn(turn_session, turn_key, turn_abort_event, value),
            thread=True,
        )

    def action_cancel_turn(self: _AppActionsHost) -> None:
        abort_event = self._active_turns.get(self._current_turn_key())
        if abort_event is None and self.busy:
            abort_event = self.abort_event
        if abort_event is None:
            return
        abort_event.set()
        self._stop_thinking_animation()
        self._append_notice("Interrupt requested.")

    def action_clear_transcript(self: _AppActionsHost) -> None:
        self.state.transcript.clear()
        self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
        self._append_notice("Screen cleared.")

    def action_open_search(self: _AppActionsHost) -> None:
        self._open_search()

    def action_command_palette(self: _AppActionsHost) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        composer.focus()
        self.set_focus(composer)
        if not composer.value.startswith("/"):
            composer.value = "/"
            composer.cursor_position = 1
        self._refresh_completions()

    def action_insert_composer_newline(self: _AppActionsHost) -> None:
        if self._inline_flow.active or self._armory_inline_active or self._materials_inline_active:
            return
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        cursor = composer.cursor_position
        composer.value = f"{composer.value[:cursor]}\n{composer.value[cursor:]}"
        composer.cursor_position = cursor + 1
        self._hide_completions()

    def action_open_armory_home(self: _AppActionsHost) -> None:
        self._handle_armory_browser("/armory")

    def _append_armory_home(self: _AppActionsHost) -> None:
        self._append_plain(_armory_home_text())

    def _handle_new(self: _AppActionsHost) -> None:
        command = get_registry().find("new")
        if command is None:
            return
        result = command.handle(self.session, "")
        if result.new_session is not None:
            tui_module = sys.modules["interfaces.tui"]
            self.session = tui_module.apply_display_settings(result.new_session)
            self._turn_sessions[self._turn_key_for_session(self.session)] = self.session
            self.state.transcript.clear()
            self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
            self._append_entry(_new_chat_card_text(), "startup")
            self._append_notice("New chat started.")
            self._focused_msg_index = None
            self._sync_busy_to_current_session()
            self._update_info_panel()

    def _handle_detach(self: _AppActionsHost) -> None:
        if self.session.armory_path is None:
            self._append_notice("No armory attached.")
            return
        previous_session = self.session
        turn_key = self._turn_key_for_session(previous_session)
        self._turn_sessions[turn_key] = previous_session
        tui_module = sys.modules["interfaces.tui"]
        self.session = tui_module.start_fresh_session(self.session, None)
        self._turn_sessions[self._turn_key_for_session(self.session)] = self.session
        self.state.transcript.clear()
        self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
        self._append_armory_home()
        self._append_notice("Armory detached.")
        self._focused_msg_index = None
        self._sync_busy_to_current_session()
        self._update_info_panel()

    def _replace_transcript_from_session(self: _AppActionsHost) -> None:
        self.state.transcript.clear()
        self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
        for message in self.session.conversation.messages:
            if message.role == "user":
                self._append_entry(message.content, "user")
            elif message.role == "assistant":
                self._append_entry(message.content, "markdown")

    def _open_search(self: _AppActionsHost) -> None:
        def on_search_result(result: object) -> None:
            if result is None:
                return
            if not isinstance(result, SearchResult):
                return
            src_path = result.source_path
            if src_path.suffix.lower() == ".pdf" and src_path.exists():
                if sys.platform == "darwin":
                    subprocess.Popen(["open", str(src_path)])  # nosec B603 B607
                elif sys.platform == "linux":
                    subprocess.Popen(["xdg-open", str(src_path)])  # nosec B603 B607
                self._append_notice(f"Opened {src_path}")
            else:
                preview = result.chunk_text[:200]
                self._append_notice(
                    f"Found in {result.armory_name}/{result.source_rel}: {preview}"
                )

        self.push_screen(SearchScreen(), on_search_result)

    def action_evidence(self: _AppActionsHost) -> None:
        self._handle_external_input("/evidence")

    def _start_thinking_animation(self: _AppActionsHost) -> None:
        self._thinking_start = time.monotonic()
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(f"[dim]{_THINKING_FRAMES[0]} {self._thinking_label}...[/dim]")
        indicator.remove_class("hidden")
        indicator.add_class("active")
        self._refresh_footer_hints()
        self._thinking_timer = self.set_interval(0.12, self._tick_thinking)

    def _tick_thinking(self: _AppActionsHost) -> None:
        if not self.busy:
            self._stop_thinking_animation()
            return
        elapsed = time.monotonic() - self._thinking_start
        frame_idx = int(elapsed / 0.12) % len(_THINKING_FRAMES)
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(f"[dim]{_THINKING_FRAMES[frame_idx]} {self._thinking_label}...[/dim]")

    def _stop_thinking_animation(self: _AppActionsHost) -> None:
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update("")
        indicator.remove_class("active")
        indicator.add_class("hidden")
        self._refresh_footer_hints()
