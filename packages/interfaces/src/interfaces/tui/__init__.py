"""Command-first Textual app for Heph.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from hephaion.parameters.settings import load_app_settings

from interfaces.palette import Theme
from interfaces.terminal.history import InputHistory
from interfaces.terminal.theme_state import current_palette as current_palette
from interfaces.terminal.theme_state import set_theme as set_theme
from interfaces.tui import armory as _tui_armory
from interfaces.tui import widgets as _tui_widgets
from interfaces.tui.app_actions import TuiAppActionsMixin
from interfaces.tui.armory import TuiArmoryMixin
from interfaces.tui.armory_browser import _DirEntry
from interfaces.tui.command_access import (
    CommandRegistry as CommandRegistry,
)
from interfaces.tui.command_access import (
    get_registry as get_registry,
)
from interfaces.tui.command_access import (
    set_command_registry_fn as set_command_registry_fn,
)
from interfaces.tui.composer_controls import TuiComposerControlsMixin
from interfaces.tui.dependencies import (
    TuiDependencyError as TuiDependencyError,
)
from interfaces.tui.display_text import (
    COMPOSER_PLACEHOLDER,
    armory_footer_hints_text,
    footer_hints_text,
    info_panel_default_text,
    info_panel_message_text,
    new_chat_card_text,
    startup_card_text,
    status_text,
)
from interfaces.tui.external_commands import (
    TuiExternalCommandMixin,
    _command_output_text,
    _TuiCaptureWriter,
)
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.history import TuiHistoryMixin
from interfaces.tui.ids import (
    COMPLETION_POSITION_ID,
    COMPLETION_STACK_ID,
    COMPOSER_FRAME_ID,
    COMPOSER_ID,
    COMPOSER_PROMPT_ID,
    FOOTER_HINTS_ID,
    INFO_PANEL_ID,
    SUGGESTIONS_ID,
    TRANSCRIPT_ID,
    TRANSCRIPT_SPACER_ID,
)
from interfaces.tui.inline_flows import TuiInlineFlowMixin
from interfaces.tui.keyboard_protocol import install_textual_modified_key_compat
from interfaces.tui.keymap import armory_binding_keys
from interfaces.tui.materials import TuiMaterialsMixin
from interfaces.tui.render_state import DirtyRegion, TuiRenderCache
from interfaces.tui.resize import (
    _LIVE_RESIZE_POLL_SECONDS,
    _RESIZE_REDRAW_DELAY_SECONDS,
    _TERMINAL_CLEAR_SCREEN,
    TuiResizeMixin,
    _ResizeRedrawState,
)
from interfaces.tui.routing import (
    TERMINAL_INTERACTIVE_COMMANDS as _TERMINAL_INTERACTIVE_COMMANDS,
)
from interfaces.tui.routing import (
    TuiInputRoute,
    tui_input_route,
)
from interfaces.tui.routing import (
    is_armory_command as _is_armory_command,
)
from interfaces.tui.routing import (
    pending_input_requires_terminal as _pending_input_requires_terminal,
)
from interfaces.tui.session_actions import (
    create_startup_session as create_startup_session,
)
from interfaces.tui.session_actions import (
    get_history_path as get_history_path,
)
from interfaces.tui.session_actions import (
    resolve_armory_session as resolve_armory_session,
)
from interfaces.tui.session_actions import (
    run_tui as run_tui,
)
from interfaces.tui.session_actions import (
    run_tui_for_path as run_tui_for_path,
)
from interfaces.tui.session_actions import (
    save_on_exit as save_on_exit,
)
from interfaces.tui.session_actions import (
    start_fresh_session as start_fresh_session,
)
from interfaces.tui.session_state import TuiRuntimeState, TuiTranscriptEntry
from interfaces.tui.slash_command import (
    command_help,
    slash_suggestion,
    tui_command_suggestions,
)
from interfaces.tui.slash_completion import (
    CompletionCandidate,
    SlashCompletionEngine,
)
from interfaces.tui.status import config_error, status_lines
from interfaces.tui.style import _tui_css
from interfaces.tui.transcript import TuiTranscriptMixin
from interfaces.tui.turns import TuiTurnMixin

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
    from hephaion.chat.session import ChatSession

    from interfaces.tui.app_actions import _TimerLike

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
    TuiComposerControlsMixin,
    TuiAppActionsMixin,
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
        self._thinking_timer: _TimerLike | None = None
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

    def on_unmount(self) -> None:
        self._pop_terminal_keyboard_protocol()
