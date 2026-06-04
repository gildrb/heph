"""Command-first Textual app for Heph.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from hephaion.armory.search import SearchResult
from hephaion.parameters.settings import load_app_settings
from hephaion.providers.catalog import prefetch_provider_model_catalogs
from hephaion.providers.config import ProviderConfig
from hephaion.providers.reasoning import next_reasoning_level, reasoning_levels_for_model
from hephaion.terminal import Theme, current_palette
from hephaion.terminal import set_theme as set_theme
from hephaion.terminal.history import InputHistory
from hephaion.tui import armory as _tui_armory
from hephaion.tui import widgets as _tui_widgets
from hephaion.tui.armory import TuiArmoryMixin
from hephaion.tui.armory_browser import _DirEntry
from hephaion.tui.dependencies import (
    TuiDependencyError as TuiDependencyError,
)
from hephaion.tui.display_text import (
    COMPOSER_PLACEHOLDER,
    armory_footer_hints_text,
    footer_hints_text,
    info_panel_default_text,
    info_panel_message_text,
    new_chat_card_text,
    startup_card_text,
    status_text,
)
from hephaion.tui.display_text import (
    armory_home_text as _armory_home_text,
)
from hephaion.tui.external_commands import (
    TuiExternalCommandMixin,
    _command_output_text,
    _TuiCaptureWriter,
)
from hephaion.tui.flow_state import InlineFlow
from hephaion.tui.history import TuiHistoryMixin
from hephaion.tui.ids import (
    COMPLETION_POSITION_ID,
    COMPLETION_STACK_ID,
    COMPOSER_FRAME_ID,
    COMPOSER_ID,
    COMPOSER_PROMPT_ID,
    COMPOSER_SELECTOR,
    FOOTER_HINTS_ID,
    FOOTER_HINTS_SELECTOR,
    INFO_PANEL_ID,
    SUGGESTIONS_ID,
    SUGGESTIONS_SELECTOR,
    TRANSCRIPT_ID,
    TRANSCRIPT_SELECTOR,
    TRANSCRIPT_SPACER_ID,
)
from hephaion.tui.inline_flows import TuiInlineFlowMixin
from hephaion.tui.keyboard_protocol import install_textual_modified_key_compat
from hephaion.tui.keymap import armory_binding_keys
from hephaion.tui.materials import TuiMaterialsMixin
from hephaion.tui.render_state import DirtyRegion, TuiRenderCache
from hephaion.tui.resize import (
    _LIVE_RESIZE_POLL_SECONDS,
    _RESIZE_REDRAW_DELAY_SECONDS,
    _TERMINAL_CLEAR_SCREEN,
    TuiResizeMixin,
    _ResizeRedrawState,
)
from hephaion.tui.routing import (
    TERMINAL_INTERACTIVE_COMMANDS as _TERMINAL_INTERACTIVE_COMMANDS,
)
from hephaion.tui.routing import (
    TuiInputRoute,
    tui_input_route,
)
from hephaion.tui.routing import (
    is_armory_command as _is_armory_command,
)
from hephaion.tui.routing import (
    pending_input_requires_terminal as _pending_input_requires_terminal,
)
from hephaion.tui.search_screen import SearchScreen
from hephaion.tui.session_actions import (
    create_startup_session as create_startup_session,
)
from hephaion.tui.session_actions import (
    get_history_path as get_history_path,
)
from hephaion.tui.session_actions import (
    resolve_armory_session as resolve_armory_session,
)
from hephaion.tui.session_actions import (
    run_tui as run_tui,
)
from hephaion.tui.session_actions import (
    run_tui_for_path as run_tui_for_path,
)
from hephaion.tui.session_actions import (
    save_on_exit as save_on_exit,
)
from hephaion.tui.session_actions import (
    start_fresh_session as start_fresh_session,
)
from hephaion.tui.session_state import TuiRuntimeState, TuiTranscriptEntry
from hephaion.tui.slash_command import (
    command_help,
    slash_suggestion,
    tui_command_suggestions,
)
from hephaion.tui.slash_completion import (
    CompletionCandidate,
    SlashCompletionEngine,
)
from hephaion.tui.slash_completion import (
    changed_highlight_indices as _changed_highlight_indices,
)
from hephaion.tui.slash_completion import (
    completion_menu_scroll_y as _completion_menu_scroll_y,
)
from hephaion.tui.slash_completion import (
    completion_menu_visible_slice as _completion_menu_visible_slice,
)
from hephaion.tui.status import config_error, status_lines
from hephaion.tui.style import _tui_css
from hephaion.tui.transcript import TuiTranscriptMixin
from hephaion.tui.turns import TuiTurnMixin

_TUI_COMPAT_EXPORTS = (
    InputHistory,
    DirtyRegion,
    _RESIZE_REDRAW_DELAY_SECONDS,
    _TERMINAL_CLEAR_SCREEN,
    _TERMINAL_INTERACTIVE_COMMANDS,
    _is_armory_command,
    _pending_input_requires_terminal,
    _command_output_text,
    _TuiCaptureWriter,
    load_app_settings,
)

if TYPE_CHECKING:
    from rich.text import Text

    from hephaion.chat.session import ChatSession
    from hephaion.commands import CommandRegistry

try:
    from rich.markdown import Markdown
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual import events
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.screen import Screen
    from textual.strip import Strip
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    Binding = None  # ty:ignore[invalid-assignment]
    _RichStyle = None  # ty:ignore[invalid-assignment]
    Markdown = None  # ty:ignore[invalid-assignment]
    Segment = None  # ty:ignore[invalid-assignment]
    _RichText = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    App = object  # ty:ignore[invalid-assignment]
    ComposeResult = object  # ty:ignore[invalid-assignment]
    Horizontal = object  # ty:ignore[invalid-assignment]
    Vertical = object  # ty:ignore[invalid-assignment]
    Screen = object  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


def get_registry() -> CommandRegistry:
    from hephaion.commands import get_registry as commands_get_registry

    return commands_get_registry()


_status_lines = status_lines
_status_text = status_text
_armory_footer_hints_text = armory_footer_hints_text
_footer_hints_text = footer_hints_text
_info_panel_default_text = info_panel_default_text
_info_panel_message_text = info_panel_message_text
_startup_card_text = startup_card_text
_new_chat_card_text = new_chat_card_text
_config_error = config_error

_armory_command_flow = _tui_armory._armory_command_flow

_THINKING_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_WidgetClasses = _tui_widgets._WidgetClasses
_transparent_screen_class = _tui_widgets._transparent_screen_class
_transparent_vertical_class = _tui_widgets._transparent_vertical_class
_transparent_horizontal_class = _tui_widgets._transparent_horizontal_class
_transparent_static_class = _tui_widgets._transparent_static_class
_transparent_rich_log_class = _tui_widgets._transparent_rich_log_class
_transparent_input_class = _tui_widgets._transparent_input_class
_transparent_option_list_class = _tui_widgets._transparent_option_list_class


_slash_suggestion = slash_suggestion

_COMPLETION_DESCRIPTION_GAP = 4
_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7
# Textual owns mouse events so widgets can be clicked, while ALLOW_SELECT on
# individual widgets keeps selection scoped to rendered text.
_TUI_ENABLE_MOUSE = True


_tui_command_suggestions = tui_command_suggestions
_command_help = command_help

_TuiTranscriptEntry = TuiTranscriptEntry
_TuiRuntimeState = TuiRuntimeState
_tui_input_route = tui_input_route
_TuiInputRoute = TuiInputRoute

_INLINE_COMMANDS = {"/login", "/logout", "/settings", "/models"}
_InlineFlow = InlineFlow


class HephTui(
    TuiHistoryMixin,
    TuiResizeMixin,
    TuiExternalCommandMixin,
    TuiInlineFlowMixin,
    TuiArmoryMixin,
    TuiMaterialsMixin,
    TuiTranscriptMixin,
    TuiTurnMixin,
    App[None],
):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("tab", "complete", "Complete"),
        Binding("shift+tab", "cycle_reasoning_level", "Reasoning", show=False, priority=True),
        Binding("ctrl+p", "command_palette", "Commands", show=False, priority=True),
        Binding(armory_binding_keys(), "open_armory_home", "Armory", show=False, priority=True),
        Binding("ctrl+s", "open_search", "Search", show=False, priority=True),
        Binding("f8", "evidence", "Evidence", show=False, priority=True),
        Binding(
            "shift+enter,ctrl+enter,alt+enter,ctrl+j",
            "insert_composer_newline",
            "Newline",
            show=False,
            priority=True,
        ),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear_transcript", "Screen", priority=True),
        Binding("ctrl+d", "quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        active_session: ChatSession,
        runtime_state: _TuiRuntimeState,
        palette: Theme,
    ) -> None:
        install_textual_modified_key_compat()
        super().__init__()
        self.CSS = _tui_css(palette)  # ty:ignore[invalid-attribute-access]
        self._widgets = _WidgetClasses.from_palette(palette)
        self.session = active_session
        self.state = runtime_state
        self.abort_event = threading.Event()
        self._active_turns: dict[str, threading.Event] = {}
        self._active_turn_sessions: dict[str, ChatSession] = {}
        self._turn_sessions: dict[str, ChatSession] = {}
        self.busy = False
        self.completion_engine = SlashCompletionEngine()
        self.completion_candidates: list[CompletionCandidate] = []
        self._thinking_timer: object = None
        self._thinking_start: float = 0.0
        self._thinking_label = "thinking"
        self._focused_msg_index: int | None = None
        self._armory_inline_active = False
        self._armory_current = active_session.armory_path or Path.home()
        self._armory_filter = ""
        self._armory_creating = False
        self._armory_flow = "manage"
        self._armory_entries: list[_DirEntry] = []
        self._materials_inline_active = False
        self._materials_filter = ""
        self._materials_entries: list[str] = []
        self._materials_columns: tuple[list[str], list[str]] = ([], [])
        self._materials_highlighted_index: int | None = None
        self._materials_flow = "toggle"
        self._sidebar_width_visible = True
        self._sidebar_actual_visible: bool | None = None
        self._transcript_reflow_pending = False
        self._transcript_reflow_requested_while_pending = False
        self._transcript_render_width: int | None = None
        self._render_cache = TuiRenderCache()
        self._suggestions_mouse_hovering = False
        self._completion_command_column_width = 22
        self._side_panel_progress = ""
        self._inline_flow = _InlineFlow()
        self._resize_redraw = _ResizeRedrawState()
        self._resize_redraw_timer: object | None = None

    def get_default_screen(self) -> Screen:
        return self._widgets.screen(id="_default")

    def compose(self) -> ComposeResult:
        w = self._widgets
        with w.horizontal(id="main-layout"):
            with w.vertical(id="shell"):
                yield w.static(_status_text(self.session), id="status")
                yield w.static("", id=TRANSCRIPT_SPACER_ID)
                yield w.rich_log(id=TRANSCRIPT_ID, markup=True, wrap=True, highlight=False)
                with w.vertical(id="armory-inline"):
                    yield w.static("", id="armory-header")
                    yield w.static("", id="armory-breadcrumbs")
                    yield w.static("", id="armory-flow-hint")
                    yield w.static("", id="armory-pane-hint")
                    yield w.static("", id="armory-count-hint")
                    with w.horizontal(id="armory-columns-inline-labels"):
                        yield w.static("armories", id="armory-current-label")
                        yield w.static("preview", id="armory-preview-label")
                    with w.horizontal(id="armory-columns-inline"):
                        yield w.option_list(id="armory-current-inline")
                        yield w.static("", id="armory-preview-inline")
                    yield w.static("", id="armory-error-inline")
                with w.vertical(id="materials-inline"):
                    yield w.static("", id="materials-top-gap")
                    yield w.static("", id="materials-header")
                    with w.horizontal(id="materials-columns"):
                        yield w.option_list(id="materials-list")
                        yield w.option_list(id="materials-list-right")
                    yield w.static("", id="materials-footer")
                    yield w.static("", id="materials-bottom-gap")
                yield w.static("", id="thinking-indicator")
                with w.horizontal(id=COMPOSER_FRAME_ID):
                    yield w.static("→", id=COMPOSER_PROMPT_ID)
                    yield w.input(
                        placeholder=COMPOSER_PLACEHOLDER,
                        id=COMPOSER_ID,
                    )
                with w.vertical(id=COMPLETION_STACK_ID):
                    yield w.option_list(id=SUGGESTIONS_ID, markup=False)
                    yield w.static("", id=COMPLETION_POSITION_ID)
                    yield w.static(_footer_hints_text(self.session), id=FOOTER_HINTS_ID)
            yield w.static(
                _info_panel_default_text(
                    self.session,
                    session_seconds=self._tui_session_seconds(),
                    busy=self.busy,
                    progress=self._side_panel_progress,
                ),
                id=INFO_PANEL_ID,
            )

    def on_mount(self) -> None:
        self.title = "Heph"
        self.sub_title = "agent inside Hephaion"
        self._push_terminal_keyboard_protocol()
        self._install_tty_resize_reader()
        self._sync_terminal_size_from_tty()
        self._initialize_layout_visibility()
        self._replay_transcript()
        self._focus_composer()
        self._append_initial_cards()
        self._schedule_transcript_reflow()
        self._prefetch_model_catalogs()
        self.set_interval(_LIVE_RESIZE_POLL_SECONDS, self._sync_terminal_size_from_tty)
        self.set_interval(1.0, self._tick_session_duration)

    def on_unmount(self) -> None:
        self._pop_terminal_keyboard_protocol()

    def on_key(self, event: events.Key) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        if self._handle_active_overlay_key(event):
            return
        if self._handle_composer_shortcut(event):
            return
        self._redirect_printable_key_to_composer(event, composer)

    def _handle_active_overlay_key(self, event: events.Key) -> bool:
        return (
            (self._inline_flow.active and self._handle_inline_flow_key(event))
            or (self._armory_inline_active and self._handle_armory_key(event))
            or (self._materials_inline_active and self._handle_materials_key(event))
        )

    def _handle_composer_shortcut(self, event: events.Key) -> bool:
        shortcut = self._composer_shortcut_handler(event.key)
        if shortcut is None or not shortcut():
            return False

        self._consume_key(event)
        return True

    def _composer_shortcut_handler(self, key: str) -> Callable[[], bool] | None:
        movement_offsets = {
            "ctrl+up": lambda: self._focus_message(-1),
            "ctrl+down": lambda: self._focus_message(1),
            "up": lambda: self._move_completion_or_history(-1),
            "down": lambda: self._move_completion_or_history(1),
        }
        actions = {
            "escape": self._handle_escape_shortcut,
            "alt+enter": self._insert_composer_newline_shortcut,
            "ctrl+enter": self._insert_composer_newline_shortcut,
            "ctrl+j": self._insert_composer_newline_shortcut,
            "newline": self._insert_composer_newline_shortcut,
            "shift+enter": self._insert_composer_newline_shortcut,
            "shift+tab": self._cycle_reasoning_shortcut,
            "tab": self._complete_shortcut,
        }
        if key in movement_offsets:
            return lambda: self._run_shortcut(movement_offsets[key])
        return actions.get(key)

    @staticmethod
    def _run_shortcut(shortcut: Callable[[], None]) -> bool:
        shortcut()
        return True

    def _cycle_reasoning_shortcut(self) -> bool:
        self.action_cycle_reasoning_level()
        return True

    def _complete_shortcut(self) -> bool:
        self.action_complete()
        return True

    def _insert_composer_newline_shortcut(self) -> bool:
        self.action_insert_composer_newline()
        return True

    def _handle_escape_shortcut(self) -> bool:
        if self.busy:
            self.action_cancel_turn()
            return True
        if self._completion_menu_visible():
            self._hide_completions()
            return True
        return False

    def _move_completion_or_history(self, offset: int) -> None:
        if self._completion_menu_visible():
            self._move_completion(offset)
        elif offset < 0:
            self._history_previous()
        else:
            self._history_next()

    def _redirect_printable_key_to_composer(self, event: events.Key, composer: Input) -> None:
        if self.focused is composer:
            return
        character = self._composer_character_for_key(event)
        if character is None:
            return
        composer.focus()
        self.set_focus(composer)
        composer.insert_text_at_cursor(character)
        self._consume_key(event)

    @staticmethod
    def _composer_character_for_key(event: events.Key) -> str | None:
        if event.character and event.is_printable:
            return event.character
        return _tui_widgets.csi_u_key_text(event.key)

    @staticmethod
    def _consume_key(event: events.Key) -> None:
        event.prevent_default()
        event.stop()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == COMPOSER_ID:
            if self._inline_flow.active:
                self._filter_inline_menu_options(event.value)
                return
            if self._armory_inline_active:
                if not self._armory_creating:
                    self._armory_filter = event.value
                    self._refresh_armory_inline()
                self._refresh_footer_hints()
                return
            if self._materials_inline_active:
                self._materials_filter = event.value
                self._refresh_materials_inline()
                return
            self._refresh_completions()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._armory_open_highlighted()
            self._refresh_armory_inline()
            return
        if event.option_list.id in ("materials-list", "materials-list-right"):
            event.stop()
            if not self._materials_inline_active:
                return
            self._handle_materials_option_selected(
                event.option_list.id,
                event.option_index,
            )
            return
        if event.option_list.id != SUGGESTIONS_ID:
            return
        if self._inline_flow.active:
            self._select_inline_flow_option(event.option_index)
        else:
            self._apply_completion(event.option_index)
            self._submit_composer_value(apply_highlighted_completion=False)
        event.stop()

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._update_armory_preview()
            return
        if event.option_list.id in ("materials-list", "materials-list-right"):
            event.stop()
            if not self._materials_inline_active:
                return
            self._handle_materials_option_highlighted(
                event.option_list.id,
                event.option_index,
            )

    def _handle_suggestions_mouse_move(self, event: events.MouseMove) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        option_index = self._suggestions_hover_index(event, suggestions)
        if option_index is None:
            self._clear_suggestions_mouse_hovering(suggestions)
            return

        self._set_suggestions_mouse_hovering(suggestions)
        if suggestions.highlighted == option_index:
            return
        if self._inline_flow.active:
            self._highlight_inline_menu_option(option_index, suggestions)
        else:
            self._highlight_completion_option(option_index, suggestions)

    def _suggestions_hover_index(
        self,
        event: events.MouseMove,
        suggestions: OptionList,
    ) -> int | None:
        if getattr(getattr(event, "widget", None), "id", None) != SUGGESTIONS_ID:
            return None
        if not suggestions.has_class("visible"):
            return None
        option_index = event.style.meta.get("option")
        if not isinstance(option_index, int):
            return None
        if not self._suggestions_option_in_range(option_index):
            return None
        return option_index

    def _suggestions_option_in_range(self, option_index: int) -> bool:
        option_count = (
            len(self._inline_flow.options)
            if self._inline_flow.active
            else len(self.completion_candidates)
        )
        return 0 <= option_index < option_count

    def _set_suggestions_mouse_hovering(self, suggestions: OptionList) -> None:
        if self._suggestions_mouse_hovering:
            return
        suggestions.add_class("mouse-hovering")
        self._suggestions_mouse_hovering = True

    def _clear_suggestions_mouse_hovering(self, suggestions: OptionList | None = None) -> None:
        if not self._suggestions_mouse_hovering:
            return
        if suggestions is None:
            suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.remove_class("mouse-hovering")
        self._suggestions_mouse_hovering = False

    def _highlight_completion_option(
        self,
        highlighted: int,
        suggestions: OptionList | None = None,
    ) -> None:
        if suggestions is None:
            suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        previous = suggestions.highlighted
        if previous == highlighted:
            return
        command_width = self._completion_command_width(highlighted, suggestions.size.height)
        if command_width != self._completion_command_column_width:
            self._set_completion_options(highlighted=highlighted)
        else:
            for option_index in _changed_highlight_indices(
                previous,
                highlighted,
                len(self.completion_candidates),
            ):
                suggestions.replace_option_prompt_at_index(
                    option_index,
                    self._format_completion_candidate(
                        self.completion_candidates[option_index],
                        selected=option_index == highlighted,
                        command_width=command_width,
                    ),
                )
        suggestions.highlighted = highlighted
        self._refresh_completion_position()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        del event
        self._submit_composer_value(apply_highlighted_completion=True)

    def _submit_composer_value(self, *, apply_highlighted_completion: bool) -> None:
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

    def _submit_routed_value(self, route: _TuiInputRoute, value: str) -> None:
        if route is _TuiInputRoute.EMPTY:
            return
        if self._submit_special_route(route, value):
            return
        if self.busy:
            self._submit_busy_value(route, value)
            return
        route_handlers = {
            _TuiInputRoute.EXTERNAL: self._submit_external_value,
            _TuiInputRoute.CHAT: self._submit_chat_value,
        }
        if handler := route_handlers.get(route):
            handler(value)

    def _composer_submission_value(
        self,
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

    def _clear_submitted_composer(self, composer: Input) -> None:
        composer.value = ""
        self._hide_completions()

    def _submit_external_value(self, value: str) -> None:
        self._record_history(value)
        self._handle_external_input(value)

    def _submit_chat_value(self, value: str) -> None:
        config_error = _config_error(self.session)
        if config_error is not None:
            self._append_error(config_error)
            return
        self._start_chat_turn(value)

    def _submit_active_inline_surface(self, composer: Input, value: str) -> bool:
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

    def _submit_special_route(self, route: _TuiInputRoute, value: str) -> bool:
        route_handlers = {
            _TuiInputRoute.MATERIALS: self._submit_materials_route,
            _TuiInputRoute.SESSIONS: self._submit_sessions_route,
            _TuiInputRoute.TURN: self._submit_turn_route,
            _TuiInputRoute.NEW: self._submit_new_route,
            _TuiInputRoute.ARMORY: self._submit_armory_route,
        }
        if handler := route_handlers.get(route):
            handler(value)
            return True
        if value in _INLINE_COMMANDS:
            self._record_history(value)
            self._append_user(value, mark_working=False)
            self._handle_inline_command(value)
            return True
        return False

    def _submit_materials_route(self, value: str) -> None:
        self._record_history(value)
        self._open_materials_inline(value)

    def _submit_sessions_route(self, value: str) -> None:
        self._record_history(value)
        self._append_user(value, mark_working=False)
        self._handle_sessions_command(value)

    def _submit_turn_route(self, value: str) -> None:
        self._record_history(value)
        self._append_user(value, mark_working=False)
        self._handle_turn_command(value)

    def _submit_new_route(self, value: str) -> None:
        self._record_history(value)
        self._handle_new()

    def _submit_armory_route(self, value: str) -> None:
        self._record_history(value)
        self._handle_armory_browser(value)

    def _submit_busy_value(self, route: _TuiInputRoute, value: str) -> bool:
        if route is _TuiInputRoute.CHAT:
            self.session.steering.enqueue(value)
            self._record_history(value)
            self._append_notice(f"Steering queued: {value}")
            return True
        self._record_history(value)
        self._append_notice(f"Command unavailable while this answer is running: {value}")
        return True

    def _start_chat_turn(self, value: str) -> None:
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

    def action_cancel_turn(self) -> None:
        abort_event = self._active_turns.get(self._current_turn_key())
        if abort_event is None and self.busy:
            abort_event = self.abort_event
        if abort_event is None:
            return
        abort_event.set()
        self._stop_thinking_animation()
        self._append_notice("Interrupt requested.")

    def action_clear_transcript(self) -> None:
        self.state.transcript.clear()
        self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
        self._append_notice("Screen cleared.")

    def action_open_search(self) -> None:
        self._open_search()

    def action_command_palette(self) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        composer.focus()
        self.set_focus(composer)
        if not composer.value.startswith("/"):
            composer.value = "/"
            composer.cursor_position = 1
        self._refresh_completions()

    def action_insert_composer_newline(self) -> None:
        if self._inline_flow.active or self._armory_inline_active or self._materials_inline_active:
            return
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        cursor = composer.cursor_position
        composer.value = f"{composer.value[:cursor]}\n{composer.value[cursor:]}"
        composer.cursor_position = cursor + 1
        self._hide_completions()

    def action_open_armory_home(self) -> None:
        self._handle_armory_browser("/armory")

    def action_complete(self) -> None:
        if self._inline_flow.active:
            return
        if not self.completion_candidates:
            self._refresh_completions()
        if not self.completion_candidates:
            return
        self._apply_highlighted_completion()

    def action_cycle_reasoning_level(self) -> None:
        if self.busy:
            return

        self._hide_completions()
        prefetch_provider_model_catalogs(ProviderConfig.load())
        levels = reasoning_levels_for_model(
            self.session.config.model,
            self.session.config.provider_slug or None,
        )
        if not levels:
            self._replace_last_notice("Reasoning unavailable.")
            return
        self.session.config.reasoning_level = next_reasoning_level(
            self.session.config.reasoning_level,
            levels=levels,
        )
        self.session.dirty = True
        self.query_one("#status", Static).update(_status_text(self.session))
        self.query_one(FOOTER_HINTS_SELECTOR, Static).update(_footer_hints_text(self.session))
        self._replace_last_notice(f"Reasoning {self.session.config.reasoning_level}.")

    def _apply_highlighted_completion(self) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        highlighted = suggestions.highlighted
        self._apply_completion(highlighted if highlighted is not None else 0)

    def _append_startup_card(self) -> None:
        self._append_entry(_startup_card_text(), "startup")

    def _append_armory_home(self) -> None:
        self._append_plain(_armory_home_text())

    def _handle_new(self) -> None:
        from hephaion.commands import NewCommand

        result = NewCommand().handle(self.session, "")
        if result.new_session is not None:
            self.session = result.new_session
            self._turn_sessions[self._turn_key_for_session(self.session)] = self.session
            self.state.transcript.clear()
            self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
            self._append_entry(_new_chat_card_text(), "startup")
            self._append_notice("New chat started.")
            self._focused_msg_index = None
            self._sync_busy_to_current_session()
            self._update_info_panel()

    def _replace_transcript_from_session(self) -> None:
        self.state.transcript.clear()
        self.query_one(TRANSCRIPT_SELECTOR, RichLog).clear()
        for message in self.session.conversation.messages:
            if message.role == "user":
                self._append_entry(message.content, "user")
            elif message.role == "assistant":
                self._append_entry(message.content, "markdown")

    def _open_search(self) -> None:
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

    def action_evidence(self) -> None:
        self._handle_external_input("/evidence")

    def _completion_menu_visible(self) -> bool:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        return suggestions.has_class("visible") and (
            bool(self.completion_candidates) or self._inline_flow.active
        )

    def _refresh_completions(self) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        before_cursor = composer.value[: composer.cursor_position]
        self.completion_candidates = self.completion_engine.candidates(
            before_cursor,
            _tui_command_suggestions(),
        )
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.remove_class("inline-menu")
        if not self.completion_candidates:
            suggestions.set_options([])
            suggestions.remove_class("visible")
            self._refresh_footer_hints()
            return
        self._set_completion_options(highlighted=0)
        suggestions.add_class("visible")
        self._clear_suggestions_mouse_hovering(suggestions)
        suggestions.highlighted = 0
        suggestions.scroll_y = 0
        self._refresh_footer_hints()
        composer.focus()

    def _hide_completions(self) -> None:
        self.completion_candidates = []
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.set_options([])
        suggestions.remove_class("inline-menu")
        suggestions.remove_class("visible")
        self._clear_suggestions_mouse_hovering(suggestions)
        self._refresh_footer_hints()

    def _move_completion(self, offset: int) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        self._clear_suggestions_mouse_hovering(suggestions)
        flow = self._inline_flow
        options = flow.options if flow.active else self.completion_candidates
        if not options:
            return
        highlighted = ((suggestions.highlighted or 0) + offset) % len(options)
        if flow.active:
            self._render_inline_menu_options(flow.options, highlighted=highlighted)
        elif self.completion_candidates:
            self._set_completion_options(highlighted=highlighted)
        suggestions.highlighted = highlighted
        suggestions.scroll_y = _completion_menu_scroll_y(
            highlighted,
            len(options),
            suggestions.size.height,
        )
        self._refresh_footer_hints()

    def _apply_completion(self, index: int) -> None:
        if not (0 <= index < len(self.completion_candidates)):
            return
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        candidate = self.completion_candidates[index]
        before_cursor = composer.value[: composer.cursor_position]
        after_cursor = composer.value[composer.cursor_position :]
        replacement_start = len(before_cursor) + candidate.start_position
        next_value = before_cursor[:replacement_start] + candidate.text + after_cursor
        composer.value = next_value
        composer.cursor_position = replacement_start + len(candidate.text)
        composer.focus()
        self._refresh_completions()

    def _set_completion_options(self, *, highlighted: int | None) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        command_width = self._completion_command_width(highlighted, suggestions.size.height)
        self._completion_command_column_width = command_width
        suggestions.set_options(
            [
                self._format_completion_candidate(
                    candidate,
                    selected=index == highlighted,
                    command_width=command_width,
                )
                for index, candidate in enumerate(self.completion_candidates)
            ]
        )

    def _completion_command_width(self, highlighted: int | None, _rendered_height: int) -> int:
        candidates = self.completion_candidates
        if not candidates:
            return 0
        highlighted_index = highlighted if highlighted is not None else 0
        # OptionList height can lag one refresh behind after filtering narrows the menu.
        visible_slice = _completion_menu_visible_slice(
            highlighted_index,
            len(candidates),
            min(len(candidates), _COMPLETION_MENU_MAX_VISIBLE_ROWS),
        )
        visible_candidates = candidates[visible_slice]
        return max(
            (len(self._completion_preview(candidate).strip()) for candidate in visible_candidates),
            default=0,
        )

    def _format_completion_candidate(
        self,
        candidate: CompletionCandidate,
        *,
        selected: bool = False,
        command_width: int = 22,
    ) -> str | Text:
        if candidate.display_provider:
            return (
                f"{candidate.display_provider:<14} "
                f"{candidate.display_model:<34} "
                f"{candidate.display_source:<16} "
                f"{candidate.display_tags}  "
            )
        value = self._completion_preview(candidate).strip()
        if _RichText is None:
            if candidate.description:
                return (
                    f"{value:<{command_width}}"
                    f"{' ' * _COMPLETION_DESCRIPTION_GAP}{candidate.description}  "
                )
            return f"{value}  "
        palette = current_palette()
        command_style = f"bold {palette.brand_primary}" if selected else palette.text_secondary
        description_style = f"bold {palette.brand_primary}" if selected else palette.text_muted
        text = _RichText()
        if candidate.description:
            text.append(
                f"{value:<{command_width}}{' ' * _COMPLETION_DESCRIPTION_GAP}",
                style=command_style,
            )
            text.append(f"{candidate.description}  ", style=description_style)
            return text
        text.append(f"{value}  ", style=command_style)
        return text

    def _completion_preview(self, candidate: CompletionCandidate) -> str:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        before_cursor = composer.value[: composer.cursor_position]
        replacement_start = len(before_cursor) + candidate.start_position
        return before_cursor[:replacement_start] + candidate.text

    def _start_thinking_animation(self) -> None:
        self._thinking_start = time.monotonic()
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(f"[dim]{_THINKING_FRAMES[0]} {self._thinking_label}...[/dim]")
        indicator.remove_class("hidden")
        indicator.add_class("active")
        self._refresh_footer_hints()
        self._thinking_timer = self.set_interval(0.12, self._tick_thinking)

    def _tick_thinking(self) -> None:
        if not self.busy:
            self._stop_thinking_animation()
            return
        elapsed = time.monotonic() - self._thinking_start
        frame_idx = int(elapsed / 0.12) % len(_THINKING_FRAMES)
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(f"[dim]{_THINKING_FRAMES[frame_idx]} {self._thinking_label}...[/dim]")

    def _stop_thinking_animation(self) -> None:
        if self._thinking_timer is not None:
            self._thinking_timer.stop()  # ty:ignore[unresolved-attribute]
            self._thinking_timer = None
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update("")
        indicator.remove_class("active")
        indicator.add_class("hidden")
        self._refresh_footer_hints()
