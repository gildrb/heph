"""Command-first Textual app for Heph.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
import threading
import time
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from hephaion.armory.search import SearchResult
from hephaion.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    load_app_settings,
)
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
from hephaion.tui.command_output import (
    command_output_text,
    filter_command_activity_details,
    format_command_activity_details,
    format_command_activity_line,
)
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
from hephaion.tui.flow_state import InlineFlow
from hephaion.tui.history import TuiHistoryMixin
from hephaion.tui.ids import (
    COMPLETION_POSITION_ID,
    COMPLETION_STACK_ID,
    COMPLETION_STACK_SELECTOR,
    COMPOSER_FRAME_ID,
    COMPOSER_FRAME_SELECTOR,
    COMPOSER_ID,
    COMPOSER_PROMPT_ID,
    COMPOSER_SELECTOR,
    FOOTER_HINTS_ID,
    FOOTER_HINTS_SELECTOR,
    INFO_PANEL_ID,
    INFO_PANEL_SELECTOR,
    SUGGESTIONS_ID,
    SUGGESTIONS_SELECTOR,
    TRANSCRIPT_ID,
    TRANSCRIPT_SELECTOR,
    TRANSCRIPT_SPACER_ID,
)
from hephaion.tui.inline_flows import TuiInlineFlowMixin
from hephaion.tui.keymap import armory_binding_keys
from hephaion.tui.materials import TuiMaterialsMixin
from hephaion.tui.render_state import DirtyRegion, TuiRenderCache
from hephaion.tui.routing import (
    TERMINAL_INTERACTIVE_COMMANDS,
    TuiInputRoute,
    is_armory_command,
    pending_input_requires_terminal,
    tui_input_route,
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
from hephaion.tui.session_state import TuiCaptureWriter, TuiRuntimeState, TuiTranscriptEntry
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
from hephaion.tui.slash_completion import (
    slash_command_name as _slash_command_name,
)
from hephaion.tui.status import config_error, status_lines
from hephaion.tui.streaming import run_tui_turn
from hephaion.tui.style import _tui_css
from hephaion.tui.transcript import TuiTranscriptMixin
from hephaion.tui.turns import TuiTurnMixin

if TYPE_CHECKING:
    from rich.text import Text

    from hephaion.chat.session import ChatSession
    from hephaion.commands import CommandRegistry, CommandResult

try:
    from rich.markdown import Markdown
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual import events
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.css.query import NoMatches
    from textual.geometry import Size
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
    NoMatches = Exception  # ty:ignore[invalid-assignment]
    Size = None  # ty:ignore[invalid-assignment]
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

_SIDEBAR_MIN_WINDOW_WIDTH = 120
_COMPACT_COMPLETION_STACK_MAX_HEIGHT = 12
_COMPLETION_DESCRIPTION_GAP = 4
_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7
_LIVE_RESIZE_POLL_SECONDS = 1 / 60
_RESIZE_REDRAW_DELAY_SECONDS = 0.075
_TERMINAL_CLEAR_SCREEN = "\x1b[0m\x1b[2J\x1b[H"
_RESIZE_SENSITIVE_SELECTORS = (
    "#status",
    TRANSCRIPT_SELECTOR,
    "#transcript-spacer",
    "#thinking-indicator",
    "#armory-inline",
    "#materials-inline",
    COMPOSER_FRAME_SELECTOR,
    f"#{COMPOSER_PROMPT_ID}",
    COMPOSER_SELECTOR,
    COMPLETION_STACK_SELECTOR,
    SUGGESTIONS_SELECTOR,
    f"#{COMPLETION_POSITION_ID}",
    FOOTER_HINTS_SELECTOR,
    INFO_PANEL_SELECTOR,
)
_RESIZE_MATERIALS_FOCUS_IDS = ("materials-list", "materials-list-right")
# Textual owns mouse events so widgets can be clicked, while ALLOW_SELECT on
# individual widgets keeps selection scoped to rendered text.
_TUI_ENABLE_MOUSE = True


_tui_command_suggestions = tui_command_suggestions
_command_help = command_help

_TuiTranscriptEntry = TuiTranscriptEntry
_TuiRuntimeState = TuiRuntimeState
_TuiCaptureWriter = TuiCaptureWriter
_TERMINAL_INTERACTIVE_COMMANDS = TERMINAL_INTERACTIVE_COMMANDS
_pending_input_requires_terminal = pending_input_requires_terminal
_is_armory_command = is_armory_command
_tui_input_route = tui_input_route
_TuiInputRoute = TuiInputRoute

_command_output_text = command_output_text
_filter_command_activity_details = filter_command_activity_details
_format_command_activity_details = format_command_activity_details
_format_command_activity_line = format_command_activity_line
_RESEND_PREFIX = "__RESEND__:"
_INLINE_COMMANDS = {"/login", "/logout", "/settings", "/models", "/recommend", "/recommend-model"}
_TUI_MANAGED_RESEND_COMMANDS = {"exam"}


@dataclass(slots=True)
class _ManagedResendCommand:
    result: CommandResult
    output: str
    resend_input: str


@dataclass(slots=True)
class _ResizeRedrawState:
    """Track terminal-size observations separately from completed repair frames."""

    last_size: tuple[int, int] | None = None
    refresh_pending: bool = False
    changed_while_pending: bool = False
    quiet_until: float | None = None
    timer_running: bool = False

    def note_size(self, size: tuple[int, int]) -> bool:
        if self.last_size == size:
            return False
        if self.refresh_pending:
            self.changed_while_pending = True
        self.last_size = size
        return True

    def schedule_trailing_refresh(self, *, now: float, delay: float) -> bool:
        self.quiet_until = now + delay
        self.refresh_pending = True
        if self.timer_running:
            return False
        self.timer_running = True
        return True

    def refresh_delay(self, *, now: float) -> float | None:
        if self.quiet_until is None:
            self.timer_running = False
            self.refresh_pending = False
            return None
        remaining = self.quiet_until - now
        if remaining > 0:
            return remaining
        return 0.0

    def finish_trailing_refresh(self) -> bool:
        changed_while_pending = self.changed_while_pending
        self.quiet_until = None
        self.timer_running = False
        self.refresh_pending = False
        self.changed_while_pending = False
        return changed_while_pending


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


_InlineFlow = InlineFlow


class HephTui(
    TuiHistoryMixin,
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
                yield w.rich_log(id=TRANSCRIPT_ID, markup=True, wrap=True, highlight=True)
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

    def _initialize_layout_visibility(self) -> None:
        visible = self.size.width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        self._set_sidebar_visible(
            visible and not self._armory_inline_active and not self._materials_inline_active
        )
        self._refresh_compact_layout_class()

    def _replay_transcript(self) -> None:
        for index, entry in enumerate(self.state.transcript):
            if index > 0:
                self._write_transcript_gap()
            self._write_transcript_entry(entry)

    def _focus_composer(self) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        composer.select_on_focus = False
        composer.focus()
        self.set_focus(composer)

    def _append_initial_cards(self) -> None:
        if self.state.history_obj is not None and not self.state.startup_card_shown:
            self.state.startup_card_shown = True
            self._append_startup_card()
        if self.session.armory_path is None and not self.state.armory_home_shown:
            self.state.armory_home_shown = True
            self._append_armory_home()

    def _tui_session_seconds(self) -> int:
        return max(0, int(time.monotonic() - self.state.tui_started_at))

    def _tick_session_duration(self) -> None:
        if self._focused_msg_index is None:
            self._update_info_panel()

    def _prefetch_model_catalogs(self) -> None:
        try:
            pc = ProviderConfig.load()
        except Exception:
            return
        active = pc.get_active()
        if active is not None:
            prefetch_provider_model_catalogs(pc, provider_slugs={active.slug})

    def on_app_focus(self, event: events.AppFocus) -> None:
        if self._armory_inline_active or self._materials_inline_active:
            composer = self.query_one(COMPOSER_SELECTOR, Input)
            composer.focus()
            self.set_focus(composer)
            event.stop()

    def on_click(self, event: events.Click) -> None:
        if isinstance(event.widget, OptionList):
            return
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        if self.focused is not composer:
            composer.focus()
            self.set_focus(composer)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        self._handle_suggestions_mouse_move(event)

    def on_resize(self, event: events.Resize) -> None:
        self._handle_resize_dimensions(event.size.width, event.size.height)

    def _handle_resize_dimensions(self, width: int, height: int) -> None:
        size = (width, height)
        if not self._resize_redraw.note_size(size):
            return
        visible = width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        target = visible and not self._armory_inline_active and not self._materials_inline_active
        self._set_sidebar_visible(target)
        self._refresh_compact_layout_class(height=height)
        self._invalidate_after_resize()

    def _invalidate_after_resize(self) -> None:
        self._clear_terminal_viewport()
        self._clear_resize_sensitive_widget_caches()
        self._render_cache.forget(*DirtyRegion)
        self._transcript_render_width = None
        self._refresh_status()
        self._refresh_footer_hints()
        self._update_info_panel()
        self._schedule_transcript_reflow()
        self.refresh(repaint=True, layout=True)
        self._schedule_resize_refresh()

    def _finish_resize_refresh(self) -> None:
        self._resize_redraw_timer = None
        refresh_delay = self._resize_redraw.refresh_delay(now=time.monotonic())
        if refresh_delay is None:
            return
        if refresh_delay > 0:
            self._resize_redraw_timer = self.set_timer(
                refresh_delay,
                self._finish_resize_refresh,
            )
            return
        self._resize_redraw.finish_trailing_refresh()
        if not self._core_widgets_available():
            return
        self._clear_resize_sensitive_widget_caches()
        self._render_cache.forget(*DirtyRegion)
        self._transcript_render_width = None
        self._refresh_status()
        self._refresh_footer_hints()
        self._update_info_panel()
        self._schedule_transcript_reflow()
        self._restore_focus_after_resize()
        self.refresh(repaint=True, layout=True)

    def _schedule_resize_refresh(self) -> None:
        should_start_timer = self._resize_redraw.schedule_trailing_refresh(
            now=time.monotonic(),
            delay=_RESIZE_REDRAW_DELAY_SECONDS,
        )
        if should_start_timer:
            self._resize_redraw_timer = self.set_timer(
                _RESIZE_REDRAW_DELAY_SECONDS,
                self._finish_resize_refresh,
            )

    def _install_tty_resize_reader(self) -> None:
        driver = getattr(self, "_driver", None)
        fallback = getattr(driver, "_get_terminal_size", None)
        if driver is None or not callable(fallback):
            return

        def get_terminal_size() -> tuple[int, int]:
            terminal_size = self._terminal_size_from_tty()
            if terminal_size is not None:
                return terminal_size
            return cast("Callable[[], tuple[int, int]]", fallback)()

        driver._get_terminal_size = get_terminal_size

    def _sync_terminal_size_from_tty(self) -> None:
        terminal_size = self._terminal_size_from_tty()
        if terminal_size is None or terminal_size == (self.size.width, self.size.height):
            return

        driver = getattr(self, "_driver", None)
        if driver is not None:
            with suppress(AttributeError):
                driver._size = terminal_size
        if Size is None:
            return
        width, height = terminal_size
        resize_event = events.Resize(Size(width, height), Size(width, height))
        self.post_message(resize_event)

    def _terminal_size_from_tty(self) -> tuple[int, int] | None:
        driver = getattr(self, "_driver", None)
        fileno = getattr(driver, "fileno", None)
        if not isinstance(fileno, int):
            return None
        try:
            size = os.get_terminal_size(fileno)
        except OSError:
            return None
        if size.columns <= 0 or size.lines <= 0:
            return None
        return size.columns, size.lines

    def _clear_terminal_viewport(self) -> None:
        driver = getattr(self, "_driver", None)
        write = getattr(driver, "write", None)
        flush = getattr(driver, "flush", None)
        if not callable(write):
            return
        write(_TERMINAL_CLEAR_SCREEN)
        if callable(flush):
            flush()
        self._force_full_screen_repaint()

    def _force_full_screen_repaint(self) -> None:
        self.screen.refresh(self.size.region, repaint=True, layout=True)

    def _clear_resize_sensitive_widget_caches(self) -> None:
        self.screen.clear_cached_dimensions()
        self._force_full_screen_repaint()
        for selector in _RESIZE_SENSITIVE_SELECTORS:
            try:
                widget = self.query_one(selector)
            except NoMatches:
                continue
            widget.clear_cached_dimensions()
            widget.refresh(repaint=True, layout=True)

    def _restore_focus_after_resize(self) -> None:
        if self._materials_inline_active:
            focused_id = getattr(self.focused, "id", None)
            if focused_id in _RESIZE_MATERIALS_FOCUS_IDS:
                return
            target = self._materials_focus_target_after_resize()
            target.focus()
            self.set_focus(target)
            return
        self._focus_composer()

    def _materials_focus_target_after_resize(self) -> OptionList:
        highlighted = self._materials_highlighted_index
        if highlighted is not None and highlighted >= len(self._materials_columns[0]):
            return self.query_one("#materials-list-right", OptionList)
        return self.query_one("#materials-list", OptionList)

    def _core_widgets_available(self) -> bool:
        try:
            self.query_one(COMPOSER_SELECTOR, Input)
            self.query_one(SUGGESTIONS_SELECTOR, OptionList)
            self.query_one(FOOTER_HINTS_SELECTOR, Static)
        except NoMatches:
            return False
        return True

    def _set_sidebar_visible(self, visible: bool) -> None:
        if self._sidebar_actual_visible is visible:
            return
        self._sidebar_actual_visible = visible
        display = "block" if visible else "none"
        self.query_one(INFO_PANEL_SELECTOR, Static).styles.display = display
        self._transcript_render_width = None
        self._schedule_transcript_reflow()

    def _update_static_region(
        self,
        selector: str,
        widget_type: type[Static],
        region: DirtyRegion,
        renderable: object,
    ) -> None:
        plain = getattr(renderable, "plain", None)
        snapshot = plain if isinstance(plain, str) else str(renderable)
        if self._render_cache.should_update(region, snapshot):
            content = renderable if isinstance(renderable, str) else cast("Text", renderable)
            try:
                self.query_one(selector, widget_type).update(content)
            except NoMatches:
                self._render_cache.forget(region)

    def _refresh_compact_layout_class(self, *, height: int | None = None) -> None:
        stack = self.query_one(COMPLETION_STACK_SELECTOR)
        frame = self.query_one(COMPOSER_FRAME_SELECTOR)
        layout_height = self.size.height if height is None else height
        if layout_height <= _COMPACT_COMPLETION_STACK_MAX_HEIGHT:
            stack.add_class("compact")
            frame.add_class("compact")
        else:
            stack.remove_class("compact")
            frame.remove_class("compact")

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
        if self.focused is composer or not event.character or not event.is_printable:
            return
        composer.focus()
        self.set_focus(composer)
        composer.insert_text_at_cursor(event.character)
        self._consume_key(event)

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

    def _handle_external_input(self, value: str) -> None:
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

    def _run_external_command(self, value: str) -> None:
        from hephaion.terminal.input import handle_input

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
            output = ""
        else:
            output = _captured_command_output(stdout, stderr, activity_trace_mode)
        self.call_from_thread(
            self._finish_external_command, new_session, history.entries, output, should_continue
        )

    def _run_tui_managed_resend_command(
        self,
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
        self,
        value: str,
        history: InputHistory,
        activity_trace_mode: str,
    ) -> _ManagedResendCommand | None:
        from hephaion.commands import get_registry

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

    def _run_resend_input(self, resend_input: str, history: InputHistory) -> None:
        history.add(resend_input)
        self.state.history = history.entries
        config_error = _config_error(self.session)
        if config_error is not None:
            self.call_from_thread(self._append_error, config_error)
            self._finish_managed_resend_command(history)
            return

        self._run_resend_chat_turn(resend_input)

    def _run_resend_chat_turn(self, resend_input: str) -> None:
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
        self,
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
        self,
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
