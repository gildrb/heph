"""Command-first Textual shell for Hephaistos.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from hephaistos.armory.search import SearchResult, load_known_armories
from hephaistos.parameters.cli import load_config
from hephaistos.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    load_app_settings,
)
from hephaistos.providers.catalog import prefetch_provider_model_catalogs
from hephaistos.providers.config import ProviderConfig
from hephaistos.terminal import ThemePalette, current_palette, set_theme
from hephaistos.terminal.history import InputHistory
from hephaistos.tui import armory as _tui_armory
from hephaistos.tui import widgets as _tui_widgets
from hephaistos.tui.armory import TuiArmoryMixin
from hephaistos.tui.armory_browser import _DirEntry
from hephaistos.tui.dependencies import TuiDependencyError, tui_dependency_message
from hephaistos.tui.display_text import (
    armory_footer_hints_text,
    armory_home_text,
    footer_hints_text,
    info_panel_default_text,
    info_panel_message_text,
    status_text,
)
from hephaistos.tui.flow_state import InlineFlow
from hephaistos.tui.history import TuiHistoryMixin
from hephaistos.tui.inline_flows import TuiInlineFlowMixin
from hephaistos.tui.keymap import armory_binding_keys, armory_shortcut_key
from hephaistos.tui.materials_view import MATERIAL_DISABLED_COLOR, MATERIAL_ENABLED_COLOR
from hephaistos.tui.no_armory import record_no_armory_turn
from hephaistos.tui.routing import (
    TERMINAL_INTERACTIVE_COMMANDS,
    TuiInputRoute,
    is_armory_command,
    pending_input_requires_terminal,
    tui_input_route,
)
from hephaistos.tui.search_screen import SearchScreen
from hephaistos.tui.session_actions import (
    create_startup_session,
    get_history_path,
    resolve_armory_session,
    save_on_exit,
)
from hephaistos.tui.session_actions import (
    start_fresh_session as start_fresh_session,
)
from hephaistos.tui.session_state import TuiCaptureWriter, TuiRuntimeState, TuiTranscriptEntry
from hephaistos.tui.shell import (
    command_output_text,
    filter_command_activity_details,
    run_shell_escape_captured,
)
from hephaistos.tui.slash_command import (
    command_help,
    slash_suggestion,
    tui_command_suggestions,
)
from hephaistos.tui.slash_completion import CompletionCandidate, SlashCompletionEngine
from hephaistos.tui.status import config_error, status_lines
from hephaistos.tui.streaming import run_tui_turn
from hephaistos.tui.style import _tui_css
from hephaistos.tui.transcript import TuiTranscriptMixin

if TYPE_CHECKING:
    from rich.text import Text

    from hephaistos.chat.session import ChatSession
    from hephaistos.commands import CommandRegistry

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
    from textual.suggester import Suggester
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
    Suggester = object  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


def get_registry() -> CommandRegistry:
    from hephaistos.commands import get_registry as commands_get_registry

    return commands_get_registry()


_tui_dependency_message = tui_dependency_message
_status_lines = status_lines
_status_text = status_text
_armory_footer_hints_text = armory_footer_hints_text
_footer_hints_text = footer_hints_text
_info_panel_default_text = info_panel_default_text


def _armory_home_text() -> str:
    recent = load_known_armories()[:5]
    if not recent:
        return armory_home_text()
    lines = [
        "No armory attached.",
        "",
        "Existing armories found.",
        f"Press {armory_shortcut_key()} to choose an armory or create a new one.",
        "Armories are saved locally in ~/.armories/",
        "Add your study materials to ~/.armories/<module>/materials/",
        "",
        "Recent armories:",
    ]
    lines.extend(f"  {path.name}  {path}" for path in recent)
    return "\n".join(lines)


_info_panel_message_text = info_panel_message_text

_config_error = config_error

_armory_command_mode = _tui_armory._armory_command_mode
_armory_usage_message = _tui_armory._armory_usage_message

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

_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7
_SIDEBAR_MIN_WINDOW_WIDTH = 120
# Let the terminal own click-drag selection so the whole TUI is copyable.
_TUI_ENABLE_MOUSE = False


def _completion_menu_scroll_y(
    highlighted: int,
    option_count: int,
    rendered_height: int,
    max_visible_rows: int = _COMPLETION_MENU_MAX_VISIBLE_ROWS,
) -> int:
    visible_rows = rendered_height if rendered_height > 0 else max_visible_rows
    visible_rows = max(1, min(option_count, visible_rows, max_visible_rows))
    max_scroll_y = max(0, option_count - visible_rows)
    centered_scroll_y = highlighted - (visible_rows // 2)
    return min(max(centered_scroll_y, 0), max_scroll_y)


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
_run_shell_escape_captured = run_shell_escape_captured
_filter_command_activity_details = filter_command_activity_details


class SlashSuggester(Suggester):
    def __init__(self, engine: SlashCompletionEngine) -> None:
        super().__init__()
        self.engine = engine

    async def get_suggestion(self, value: str) -> str | None:
        return _slash_suggestion(self.engine, value)


_InlineFlow = InlineFlow


class HephaistosTui(
    TuiHistoryMixin,
    TuiInlineFlowMixin,
    TuiArmoryMixin,
    TuiTranscriptMixin,
    App[None],
):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("tab", "complete", "Complete"),
        Binding("ctrl+p", "command_palette", "Commands", show=False, priority=True),
        Binding(armory_binding_keys(), "open_armory_home", "Armory", show=False, priority=True),
        Binding("ctrl+s", "open_search", "Search", show=False, priority=True),
        Binding("f8", "evidence", "Evidence", show=False, priority=True),
        Binding("ctrl+c", "cancel_turn", "Cancel", show=False, priority=True),
        Binding("ctrl+l", "clear_transcript", "Screen", priority=True),
        Binding("ctrl+d", "quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        active_session: ChatSession,
        runtime_state: _TuiRuntimeState,
        palette: ThemePalette,
    ) -> None:
        super().__init__()
        self.CSS = _tui_css()  # ty:ignore[invalid-attribute-access]
        self._widgets = _WidgetClasses.from_palette(palette)
        self.session = active_session
        self.state = runtime_state
        self.abort_event = threading.Event()
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
        self._armory_mode = "manage"
        self._armory_entries: list[_DirEntry] = []
        self._materials_inline_active = False
        self._materials_filter = ""
        self._materials_entries: list[str] = []
        self._materials_mode = "toggle"
        self._sidebar_width_visible = True
        self._sidebar_actual_visible: bool | None = None
        self._transcript_reflow_pending = False
        self._inline_flow = _InlineFlow()

    def get_default_screen(self) -> Screen:
        return self._widgets.screen(id="_default")

    def compose(self) -> ComposeResult:
        w = self._widgets
        with w.horizontal(id="main-layout"):
            with w.vertical(id="shell"):
                yield w.static(_status_text(self.session), id="status")
                yield w.static("", id="transcript-spacer")
                yield w.rich_log(id="transcript", markup=True, wrap=True, highlight=True)
                with w.vertical(id="armory-inline"):
                    yield w.static("", id="armory-header")
                    yield w.static("", id="armory-breadcrumbs")
                    yield w.static("", id="armory-mode-hint")
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
                    yield w.static("", id="materials-header")
                    yield w.option_list(id="materials-list")
                    yield w.static("", id="materials-footer")
                yield w.static("", id="thinking-indicator")
                with w.horizontal(id="composer-frame"):
                    yield w.static("▸", id="composer-prompt")
                    yield w.input(
                        placeholder='Ask anything... "What do I need to study next?"',
                        id="composer",
                    )
                with w.vertical(id="completion-stack"):
                    yield w.option_list(id="suggestions", markup=False)
                    yield w.static("", id="completion-position")
                    yield w.static(_footer_hints_text(self.session), id="footer-hints")
            yield w.static(
                _info_panel_default_text(
                    self.session,
                    session_seconds=self._tui_session_seconds(),
                ),
                id="info-panel",
            )

    def on_mount(self) -> None:
        self.title = "Hephaistos"
        self.sub_title = "command-first study shell"
        visible = self.size.width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        self._set_sidebar_visible(
            visible and not self._armory_inline_active and not self._materials_inline_active
        )
        for index, entry in enumerate(self.state.transcript):
            if index > 0:
                self._write_transcript_gap()
            self._write_transcript_entry(entry)
        composer = self.query_one("#composer", Input)
        composer.select_on_focus = False
        composer.focus()
        self.set_focus(composer)
        if self.session.armory_path is None and not self.state.armory_home_shown:
            self.state.armory_home_shown = True
            self._append_armory_home()
        self._schedule_transcript_reflow()
        self._prefetch_model_catalogs()
        self.set_interval(1.0, self._tick_session_duration)

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
            composer = self.query_one("#composer", Input)
            composer.focus()
            self.set_focus(composer)
            event.stop()

    def on_click(self, event: events.Click) -> None:
        composer = self.query_one("#composer", Input)
        if self.focused is not composer:
            composer.focus()
            self.set_focus(composer)

    def on_resize(self, event: events.Resize) -> None:
        visible = event.size.width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        target = visible and not self._armory_inline_active and not self._materials_inline_active
        self._set_sidebar_visible(target)
        self._schedule_transcript_reflow()

    def _set_sidebar_visible(self, visible: bool) -> None:
        if self._sidebar_actual_visible is visible:
            return
        self._sidebar_actual_visible = visible
        display = "block" if visible else "none"
        self.query_one("#info-panel", Static).styles.display = display
        self._schedule_transcript_reflow()

    def on_key(self, event: events.Key) -> None:
        composer = self.query_one("#composer", Input)
        if self._inline_flow.active and self._handle_inline_flow_key(event):
            return
        if self._armory_inline_active and self._handle_armory_key(event):
            return
        if self._materials_inline_active and self._handle_materials_key(event):
            return
        if event.key == "escape" and self.busy:
            self.action_cancel_turn()
            event.prevent_default()
            event.stop()
            return
        if event.key == "ctrl+up":
            self._focus_message(-1)
            event.prevent_default()
            event.stop()
            return
        if event.key == "ctrl+down":
            self._focus_message(1)
            event.prevent_default()
            event.stop()
            return
        if event.key == "up":
            if self._completion_menu_visible():
                self._move_completion(-1)
            else:
                self._history_previous()
            event.prevent_default()
            event.stop()
            return
        if event.key == "down":
            if self._completion_menu_visible():
                self._move_completion(1)
            else:
                self._history_next()
            event.prevent_default()
            event.stop()
            return
        if event.key == "escape" and self._completion_menu_visible():
            self._hide_completions()
            event.prevent_default()
            event.stop()
            return
        if event.key == "tab":
            self.action_complete()
            event.prevent_default()
            event.stop()
            return
        if self.focused is not composer and event.character and event.is_printable:
            composer.focus()
            self.set_focus(composer)
            composer.insert_text_at_cursor(event.character)
            event.prevent_default()
            event.stop()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "composer":
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
        if event.option_list.id == "materials-list":
            event.stop()
            if self._materials_mode == "toggle":
                self._toggle_highlighted_material()
            else:
                self._close_materials_inline()
            return
        if event.option_list.id != "suggestions":
            return
        if self._inline_flow.active:
            self._select_inline_flow_option(event.index)  # ty:ignore[unresolved-attribute]
        else:
            self._apply_completion(event.index)  # ty:ignore[unresolved-attribute]
        event.stop()

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._update_armory_preview()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        composer = self.query_one("#composer", Input)
        if self._completion_menu_visible() and self.completion_candidates:
            self._apply_highlighted_completion()
        value = composer.value.strip()
        if self._inline_flow.active:
            event.stop()
            self._submit_inline_flow(value)
            return
        if self._armory_inline_active:
            event.stop()
            if self._armory_creating:
                self._create_inline_armory(value)
            else:
                composer.value = ""
                self._armory_filter = ""
                self._armory_open_highlighted()
                self._refresh_armory_inline()
            return
        if self._materials_inline_active:
            event.stop()
            self._close_materials_inline()
            return
        route = _tui_input_route(value)
        composer.value = ""
        self._hide_completions()
        if route is _TuiInputRoute.EMPTY:
            return
        if self.busy:
            self.session.steering.enqueue(value)
            self._record_history(value)
            self._append_notice(f"Steering queued: {value}")
            return
        if route is _TuiInputRoute.MATERIALS:
            self._record_history(value)
            self._open_materials_inline(value)
            return
        if route is _TuiInputRoute.SESSIONS:
            self._record_history(value)
            self._append_user(value, mark_working=False)
            self._handle_sessions_command(value)
            return
        if route is _TuiInputRoute.NEW:
            self._record_history(value)
            self._handle_new()
            return
        if route is _TuiInputRoute.ARMORY:
            self._record_history(value)
            self._handle_armory_browser(value)
            return
        if value in {"/login", "/logout", "/settings", "/models"}:
            self._record_history(value)
            self._append_user(value, mark_working=False)
            self._handle_inline_command(value)
            return
        if route is _TuiInputRoute.EXTERNAL:
            self._record_history(value)
            self._handle_external_input(value)
            return
        if self.session.armory_path is None:
            reply = record_no_armory_turn(self.session, value)
            self._record_history(value)
            self._append_user(value, mark_working=False)
            self._append_assistant_reply(reply)
            self._refresh_status("ready")
            self._update_info_panel()
            return
        config_error = _config_error(self.session)
        if config_error is not None:
            self._append_error(config_error)
            return
        self._record_history(value)
        self._append_user(value)
        self.busy = True
        self.abort_event.clear()
        self._refresh_status("assistant working")
        self.run_worker(lambda: self._run_turn(value), thread=True)

    def action_cancel_turn(self) -> None:
        if self.busy:
            self.abort_event.set()
            self._stop_thinking_animation()
            self._append_notice("Interrupt requested.")

    def action_clear_transcript(self) -> None:
        self.state.transcript.clear()
        self.query_one("#transcript", RichLog).clear()
        self._append_notice("Screen cleared.")

    def action_open_search(self) -> None:
        self._open_search()

    def action_command_palette(self) -> None:
        composer = self.query_one("#composer", Input)
        composer.focus()
        self.set_focus(composer)
        if not composer.value.startswith("/"):
            composer.value = "/"
            composer.cursor_position = 1
        self._refresh_completions()

    def action_open_armory_home(self) -> None:
        self._handle_armory_browser("/armory")

    def action_complete(self) -> None:
        if not self.completion_candidates:
            self._refresh_completions()
        if not self.completion_candidates:
            return
        self._apply_highlighted_completion()

    def _apply_highlighted_completion(self) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        highlighted = suggestions.highlighted
        self._apply_completion(highlighted if highlighted is not None else 0)

    def _append_armory_home(self) -> None:
        self._append_plain(_armory_home_text())

    def _open_materials_inline(self, value: str = "", *, mode: str = "toggle") -> None:
        _, _, args = value.partition(" ")
        self._materials_filter = args.strip()
        self._materials_mode = mode
        self._materials_inline_active = True
        self.query_one("#transcript", RichLog).add_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).add_class("hidden-for-armory")
        self.query_one("#materials-inline").add_class("active")
        self._set_sidebar_visible(False)
        composer = self.query_one("#composer", Input)
        composer.value = self._materials_filter
        composer.placeholder = "Filter materials..."
        self._hide_completions()
        self._refresh_materials_inline()
        material_list = self.query_one("#materials-list", OptionList)
        material_list.focus()
        self.set_focus(material_list)

    def _close_materials_inline(self) -> None:
        self._materials_inline_active = False
        self._materials_filter = ""
        self._materials_mode = "toggle"
        self.query_one("#transcript", RichLog).remove_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).remove_class("hidden-for-armory")
        self.query_one("#materials-inline").remove_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        self._schedule_transcript_reflow()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "What do I need to study next?"'
        self._refresh_status("ready")
        self._update_info_panel()
        composer.focus()
        self.set_focus(composer)

    def _refresh_materials_inline(self) -> None:
        query = self._materials_filter.strip().lower()
        files = list(self.session.source_files)
        if query:
            files = [file for file in files if query in file.lower()]
        self._materials_entries = files
        enabled = len(self.session.source_files) - len(self.session.disabled_source_files)
        if self._materials_mode == "toggle":
            header = (
                f"materials  type filter  space toggle  enter toggle  esc close  {enabled} active"
            )
        else:
            header = f"sources  type filter  ↑/↓ browse  enter close  esc close  {enabled} active"
        self.query_one("#materials-header", Static).update(header)
        material_list = self.query_one("#materials-list", OptionList)
        previous = material_list.highlighted
        material_list.clear_options()
        highlighted = min(previous or 0, len(self._materials_entries) - 1)
        for index, file in enumerate(self._materials_entries):
            material_list.add_option(
                self._format_material_option(file, selected=index == highlighted)
            )
        if self._materials_entries:
            material_list.highlighted = highlighted
        self._refresh_materials_highlight_class()
        footer = self.query_one("#materials-footer", Static)
        if not self.session.source_files:
            footer.update("No materials attached.")
        elif query and not self._materials_entries:
            footer.update(f"No materials match: {self._materials_filter}")
        else:
            footer.update(self._materials_footer_text())

    def _materials_footer_text(self) -> str:
        if self._materials_mode == "toggle":
            return "Unchecked materials will not be used for retrieval."
        return "Use /materials to include or exclude retrieval sources."

    def _format_material_option(self, file: str, *, selected: bool) -> str | Text:
        enabled_file = file not in self.session.disabled_source_files
        label = f"@{file.removeprefix('materials/')}"
        state_color = MATERIAL_ENABLED_COLOR if enabled_file else MATERIAL_DISABLED_COLOR
        style = f"black on {state_color}" if selected else state_color
        return _RichText.styled(label, style) if _RichText is not None else label

    def _refresh_materials_highlight_class(self) -> None:
        material_list = self.query_one("#materials-list", OptionList)
        material_list.remove_class("material-enabled", "material-disabled")
        idx = material_list.highlighted
        if idx is None or idx < 0 or idx >= len(self._materials_entries):
            return
        file = self._materials_entries[idx]
        class_name = (
            "material-disabled"
            if file in self.session.disabled_source_files
            else "material-enabled"
        )
        material_list.add_class(class_name)

    def _toggle_highlighted_material(self) -> None:
        material_list = self.query_one("#materials-list", OptionList)
        idx = material_list.highlighted
        if idx is None or idx < 0 or idx >= len(self._materials_entries):
            return
        file = self._materials_entries[idx]
        if file in self.session.disabled_source_files:
            self.session.disabled_source_files.remove(file)
        else:
            self.session.disabled_source_files.add(file)
        self.session.dirty = True
        self._refresh_materials_inline()

    def _move_material_highlight(self, offset: int) -> None:
        if not self._materials_entries:
            return
        material_list = self.query_one("#materials-list", OptionList)
        highlighted = material_list.highlighted or 0
        material_list.highlighted = (highlighted + offset) % len(self._materials_entries)
        self._refresh_materials_inline()

    def _handle_materials_key(self, event: events.Key) -> bool:
        if event.key == "escape":
            self._close_materials_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key == "enter":
            if self._materials_mode == "toggle":
                self._toggle_highlighted_material()
            else:
                self._close_materials_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("up", "k"):
            self._move_material_highlight(-1)
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("down", "j"):
            self._move_material_highlight(1)
            event.prevent_default()
            event.stop()
            return True
        if event.key == "space" or event.character == " ":
            if self._materials_mode == "toggle":
                self._toggle_highlighted_material()
            event.prevent_default()
            event.stop()
            return True
        return False

    def _handle_new(self) -> None:
        from hephaistos.commands import NewCommand

        result = NewCommand().handle(self.session, "")
        if result.new_session is not None:
            self.session = result.new_session
            self.state.transcript.clear()
            self.query_one("#transcript", RichLog).clear()
            self._append_notice("New chat started.")
            self._refresh_status("ready")
            self._focused_msg_index = None
            self._update_info_panel()

    def _handle_external_input(self, value: str) -> None:
        if value.startswith("!"):
            output = _run_shell_escape_captured(value[1:].strip())
            if output:
                self._append_entry(output, "ansi")
            return
        if _pending_input_requires_terminal(value):
            self.state.pending_input = value
            self.exit()
            return

        self._thinking_label = "working"
        self._append_user(value)
        self.busy = True
        self.abort_event.clear()
        self._refresh_status("command working")
        self.run_worker(lambda: self._run_external_command(value), thread=True)

    def _run_external_command(self, value: str) -> None:
        from hephaistos.terminal.input import handle_input

        history = InputHistory(self.state.history)
        streamed_line = False
        activity_trace_mode = load_app_settings().activity_trace_mode
        stream_activity = activity_trace_mode == ACTIVITY_TRACE_TOOL_CALLS

        def stream_notice(line: str) -> None:
            nonlocal streamed_line
            streamed_line = True
            self.call_from_thread(self._append_notice, line)

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
            output = _command_output_text(stdout, stderr)
            if activity_trace_mode in {
                ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
                ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
            }:
                output = _filter_command_activity_details(output)
        self.call_from_thread(
            self._finish_external_command, new_session, history.entries, output, should_continue
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
        """Open the cross-armory search screen."""

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

    def _run_turn(self, user_input: str) -> None:
        last_activity_line = ""

        def on_reply(reply: str) -> None:
            self.call_from_thread(self._append_assistant_reply, reply)

        def on_notice(notice: str) -> None:
            self.call_from_thread(self._append_notice, notice)

        def on_progress(progress: str) -> None:
            self.call_from_thread(self._refresh_status, f"assistant {progress}")

        def on_activity(line: str) -> None:
            nonlocal last_activity_line
            if line == last_activity_line:
                return
            last_activity_line = line
            self.call_from_thread(self._append_notice, line)

        def on_error(error: str) -> None:
            self.call_from_thread(self._append_error, error)

        def on_finish() -> None:
            self.call_from_thread(self._finish_turn)

        run_tui_turn(
            self.session,
            user_input,
            self.abort_event,
            on_reply=on_reply,
            on_notice=on_notice,
            on_error=on_error,
            on_finish=on_finish,
            on_progress=on_progress,
            on_activity=on_activity,
        )

    def _completion_menu_visible(self) -> bool:
        suggestions = self.query_one("#suggestions", OptionList)
        return suggestions.has_class("visible") and (
            bool(self.completion_candidates) or self._inline_flow.active
        )

    def _refresh_completions(self) -> None:
        composer = self.query_one("#composer", Input)
        before_cursor = composer.value[: composer.cursor_position]
        self.completion_candidates = self.completion_engine.candidates(
            before_cursor,
            _tui_command_suggestions(),
        )
        suggestions = self.query_one("#suggestions", OptionList)
        if not self.completion_candidates:
            suggestions.set_options([])
            suggestions.remove_class("visible")
            self._refresh_footer_hints()
            return
        suggestions.set_options(
            [
                self._format_completion_candidate(candidate)
                for candidate in self.completion_candidates
            ]
        )
        suggestions.add_class("visible")
        suggestions.highlighted = 0
        suggestions.scroll_y = 0
        self._refresh_footer_hints()
        composer.focus()

    def _hide_completions(self) -> None:
        self.completion_candidates = []
        suggestions = self.query_one("#suggestions", OptionList)
        suggestions.set_options([])
        suggestions.remove_class("visible")
        self._refresh_footer_hints()

    def _move_completion(self, offset: int) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        option_count = len(self.completion_candidates) or len(self._inline_flow.options)
        if option_count == 0:
            return
        current = suggestions.highlighted
        if current is None:
            current = 0
        highlighted = (current + offset) % option_count
        suggestions.highlighted = highlighted
        suggestions.scroll_y = _completion_menu_scroll_y(
            highlighted,
            option_count,
            suggestions.size.height,
            _COMPLETION_MENU_MAX_VISIBLE_ROWS,
        )
        self._refresh_footer_hints()

    def _apply_completion(self, index: int) -> None:
        if not (0 <= index < len(self.completion_candidates)):
            return
        composer = self.query_one("#composer", Input)
        candidate = self.completion_candidates[index]
        before_cursor = composer.value[: composer.cursor_position]
        after_cursor = composer.value[composer.cursor_position :]
        replacement_start = len(before_cursor) + candidate.start_position
        next_value = before_cursor[:replacement_start] + candidate.text + after_cursor
        composer.value = next_value
        composer.cursor_position = replacement_start + len(candidate.text)
        composer.focus()
        self._refresh_completions()

    def _format_completion_candidate(self, candidate: CompletionCandidate) -> str:
        if candidate.display_provider:
            return (
                f"{candidate.display_provider:<14} "
                f"{candidate.display_model:<34} "
                f"{candidate.display_source:<16} "
                f"{candidate.display_tags}  "
            )
        value = self._completion_preview(candidate).strip()
        if candidate.description:
            return f"{value:<22} {candidate.description}  "
        return f"{value}  "

    def _completion_preview(self, candidate: CompletionCandidate) -> str:
        composer = self.query_one("#composer", Input)
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


def run_tui(session: ChatSession | None = None) -> None:
    """Run the command-first Textual shell."""
    from hephaistos.terminal.input import handle_input

    if (
        Markdown is None
        or Segment is None
        or _RichStyle is None
        or _RichText is None
        or Input is None
        or OptionList is None
        or RichLog is None
        or Static is None
        or Strip is None
    ):
        raise TuiDependencyError(_tui_dependency_message())

    if session is None:
        session = create_startup_session(load_config())

    set_theme(load_app_settings().theme)
    session_ref: list[ChatSession] = [session]
    history_path = get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_obj = InputHistory.load(history_path)
    state = _TuiRuntimeState(
        history=history_obj.entries[-500:],
        history_obj=history_obj,
    )

    try:
        while True:
            palette = current_palette()
            HephaistosTui(session_ref[0], state, palette).run(mouse=_TUI_ENABLE_MOUSE)

            pending_input = state.pending_input
            state.pending_input = None
            if pending_input is None:
                break

            if pending_input.startswith("!"):
                output = _run_shell_escape_captured(pending_input[1:].strip())
                if output:
                    state.transcript.append(_TuiTranscriptEntry(output, "ansi"))
                continue

            history = InputHistory(state.history)
            if _pending_input_requires_terminal(pending_input):
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

            stdout = _TuiCaptureWriter()
            stderr = _TuiCaptureWriter()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                new_session, should_continue = handle_input(
                    session_ref[0],
                    pending_input,
                    history,
                )
            session_ref[0] = new_session
            state.history = history.entries

            output = _command_output_text(stdout, stderr)
            if output:
                state.transcript.append(_TuiTranscriptEntry(output, "notice"))
            if not should_continue:
                break
    finally:
        if state.history_obj is not None:
            state.history_obj.save(history_path)
        save_on_exit(session_ref[0])


def run_tui_for_path(path: Path | None) -> None:
    """Create or attach a session and run the Textual shell."""
    if path is None:
        run_tui()
        return

    session = resolve_armory_session(str(path))
    run_tui(session)
