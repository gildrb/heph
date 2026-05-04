"""Command-first Textual shell for Hephaistos.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import hephaistos.workspace as _workspace
from hephaistos.analytics import capture as capture_analytics
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.chat.model_selection import switch_model
from hephaistos.chat.session import ChatSession
from hephaistos.commands import NewCommand
from hephaistos.commands import get_registry as _get_registry
from hephaistos.input_history import InputHistory
from hephaistos.parameters.cli import load_config
from hephaistos.providers.model_choices import configured_model_choices
from hephaistos.search_index import SearchResult, load_known_armories
from hephaistos.terminal import ThemePalette, current_palette
from hephaistos.tui import armory as _tui_armory
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
from hephaistos.tui.inline_flows import TuiInlineFlowMixin
from hephaistos.tui.materials_view import material_listing
from hephaistos.tui.routing import (
    TERMINAL_INTERACTIVE_COMMANDS,
    TuiInputRoute,
    is_armory_command,
    is_models_input,
    pending_input_requires_terminal,
    tui_input_route,
)
from hephaistos.tui.search_screen import SearchScreen
from hephaistos.tui.session_state import TuiCaptureWriter, TuiRuntimeState, TuiTranscriptEntry
from hephaistos.tui.shell import command_output_text, run_shell_escape_captured
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
from hephaistos.tui.transparent import (
    make_blank_background_cls,
    make_transparent_cls,
    nonfocus_rich_log_class,
)
from hephaistos.workspace import (
    create_startup_session,
    get_history_path,
    handle_input,
    save_on_exit,
)

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
    Binding = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    _RichStyle = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Markdown = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Segment = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    _RichText = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    events = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    App = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    ComposeResult = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    Horizontal = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    Vertical = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    Screen = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    Suggester = object  # type: ignore[assignment, misc]  # ty:ignore[invalid-assignment]
    Strip = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Input = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    RichLog = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Static = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

start_fresh_session = _workspace.start_fresh_session
get_registry = _get_registry


_TRANSCRIPT_ENTRY_GAP = ""


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
        "Press ctrl+a to open or create an armory.",
        "Put study files in materials/.",
        "Hephaistos handles indexing, retrieval, memory, chats, traces, and usage.",
        "",
        "Recent armories:",
    ]
    lines.extend(f"  {path.name}  {path}" for path in recent)
    return "\n".join(lines)


_info_panel_message_text = info_panel_message_text


_config_error = config_error


_source_listing = material_listing
_armory_command_mode = _tui_armory._armory_command_mode
_armory_usage_message = _tui_armory._armory_usage_message


_THINKING_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


@dataclass
class _WidgetClasses:
    """Palette-dependent widget classes for compose()."""

    screen: type
    vertical: type
    horizontal: type
    static: type
    rich_log: type
    input: type
    option_list: type

    @classmethod
    def from_palette(cls, palette: ThemePalette) -> _WidgetClasses:
        if palette.is_transparent:
            transparent_rich_log_base = make_transparent_cls(RichLog)

            class TransparentNonFocusRichLog(transparent_rich_log_base):  # type: ignore[misc]  # ty:ignore[unsupported-base]
                can_focus = False

            return cls(
                screen=make_blank_background_cls(Screen),
                vertical=make_blank_background_cls(Vertical),
                horizontal=make_blank_background_cls(Horizontal),
                static=make_transparent_cls(Static),
                rich_log=TransparentNonFocusRichLog,
                input=make_transparent_cls(Input),
                option_list=make_transparent_cls(OptionList),
            )
        return cls(
            screen=Screen,
            vertical=Vertical,
            horizontal=Horizontal,
            static=Static,
            rich_log=nonfocus_rich_log_class(),
            input=Input,
            option_list=OptionList,
        )


# Backward-compatible per-type factory wrappers for tests.
# Prefer _WidgetClasses.from_palette() for production use.


def _transparent_screen_class() -> type:
    return make_blank_background_cls(Screen)


def _transparent_vertical_class() -> type:
    return make_blank_background_cls(Vertical)


def _transparent_horizontal_class() -> type:
    return make_blank_background_cls(Horizontal)


def _transparent_static_class() -> type:
    return make_transparent_cls(Static)


def _transparent_rich_log_class() -> type:
    base = make_transparent_cls(RichLog)

    class TransparentNonFocusRichLog(base):  # type: ignore[misc]  # ty:ignore[unsupported-base]
        can_focus = False

    return TransparentNonFocusRichLog


def _transparent_input_class() -> type:
    return make_transparent_cls(Input)


def _transparent_option_list_class() -> type:
    return make_transparent_cls(OptionList)


_slash_suggestion = slash_suggestion


_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7
_MODEL_MENU_MAX_VISIBLE_ROWS = 20


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
_is_models_input = is_models_input
_is_armory_command = is_armory_command
_tui_input_route = tui_input_route
_TuiInputRoute = TuiInputRoute


_command_output_text = command_output_text
_run_shell_escape_captured = run_shell_escape_captured


class SlashSuggester(Suggester):  # type: ignore[misc]
    def __init__(self, engine: SlashCompletionEngine) -> None:
        super().__init__()
        self.engine = engine

    async def get_suggestion(self, value: str) -> str | None:
        return _slash_suggestion(self.engine, value)


_InlineFlow = InlineFlow


class HephaistosTui(TuiInlineFlowMixin, TuiArmoryMixin, TuiTranscriptMixin, App[None]):
    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("tab", "complete", "Complete"),
        Binding("ctrl+p", "command_palette", "Commands", show=False, priority=True),
        Binding("ctrl+a", "open_armory_home", "Armory", show=False, priority=True),
        Binding("ctrl+s", "open_search", "Search", show=False, priority=True),
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
        self._focused_msg_index: int | None = None
        self._armory_inline_active = False
        self._armory_current = active_session.armory_path or Path.home()
        self._armory_filter = ""
        self._armory_creating = False
        self._armory_mode = "manage"
        self._armory_entries: list[_DirEntry] = []
        self._armory_parent_entries: list[tuple[str, Path]] = []
        self._inline_flow = _InlineFlow()

    def get_default_screen(self) -> Screen:
        return self._widgets.screen(id="_default")  # type: ignore[reportCallIssue]

    def compose(self) -> ComposeResult:
        w = self._widgets
        with w.horizontal(id="main-layout"):  # type: ignore[reportCallIssue]
            with w.vertical(id="shell"):  # type: ignore[reportCallIssue]
                yield w.static(_status_text(self.session), id="status")
                yield w.rich_log(id="transcript", markup=True, wrap=True, highlight=True)
                with w.vertical(id="armory-inline"):  # type: ignore[reportCallIssue]
                    yield w.static("", id="armory-header")
                    with w.horizontal(id="armory-columns-inline"):  # type: ignore[reportCallIssue]
                        yield w.option_list(id="armory-parent-inline")
                        yield w.option_list(id="armory-current-inline")
                        yield w.static("", id="armory-preview-inline")
                    yield w.static("", id="armory-error-inline")
                yield w.static("", id="thinking-indicator")
                yield w.option_list(id="suggestions", markup=False)
                with w.vertical(id="composer-frame"):  # type: ignore[reportCallIssue]
                    yield w.input(
                        placeholder='Ask anything... "What do I need to study next?"',
                        id="composer",
                    )
                    yield w.static(_footer_hints_text(self.session), id="footer-hints")
            yield w.static("", id="info-separator")
            yield w.static(_info_panel_default_text(self.session), id="info-panel")

    def on_mount(self) -> None:
        self.title = "Hephaistos"
        self.sub_title = "command-first study shell"
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

    def on_app_focus(self, event: events.AppFocus) -> None:
        if self._armory_inline_active:
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
        visible = event.size.width >= 100
        panel = self.query_one("#info-panel", Static)
        separator = self.query_one("#info-separator", Static)
        panel.styles.display = "block" if visible else "none"
        separator.styles.display = "block" if visible else "none"

    def on_key(self, event: events.Key) -> None:
        composer = self.query_one("#composer", Input)
        if self._inline_flow.active and self._handle_inline_flow_key(event):
            return
        if self._armory_inline_active and self._handle_armory_key(event):
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
                return
            if self._armory_inline_active:
                if not self._armory_creating:
                    self._armory_filter = event.value
                    self._refresh_armory_inline()
                self._refresh_footer_hints()
                return
            self._refresh_completions()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._armory_open_highlighted()
            self._refresh_armory_inline()
            return
        if event.option_list.id == "armory-parent-inline":
            event.stop()
            idx = event.option_list.highlighted
            if idx is not None and 0 <= idx < len(self._armory_parent_entries):
                _label, path = self._armory_parent_entries[idx]
                self._armory_current = path
                self._armory_filter = ""
                self.query_one("#composer", Input).value = ""
                self._refresh_armory_inline()
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
        value = event.value.strip()
        composer = self.query_one("#composer", Input)
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
        route = _tui_input_route(value)
        if route is _TuiInputRoute.MODELS:
            self._record_history(value)
            self._handle_models(value)
            composer.value = ""
            self._hide_completions()
            return
        composer.value = ""
        self._hide_completions()
        if route is _TuiInputRoute.EMPTY:
            return
        if self.busy:
            self.session.steering.enqueue(value)
            self._record_history(value)
            self._append_notice(f"Steering queued: {value}")
            return
        if route is _TuiInputRoute.SOURCES:
            self._record_history(value)
            self._handle_sources(value)
            return
        if route is _TuiInputRoute.NEW:
            self._record_history(value)
            self._handle_new()
            return
        if route is _TuiInputRoute.ARMORY:
            self._record_history(value)
            self._handle_armory_browser(value)
            return
        if value in {"/login", "/logout", "/settings"}:
            self._record_history(value)
            self._handle_inline_command(value)
            return
        if route is _TuiInputRoute.EXTERNAL:
            self._record_history(value)
            self._handle_external_input(value)
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
        suggestions = self.query_one("#suggestions", OptionList)
        highlighted = suggestions.highlighted
        self._apply_completion(highlighted if highlighted is not None else 0)

    def _append_armory_home(self) -> None:
        self._append_plain(_armory_home_text())

    def _handle_sources(self, value: str) -> None:
        _, _, args = value.partition(" ")
        self._append_plain(material_listing(self.session, args))

    def _handle_models(self, value: str) -> None:
        _, _, args = value.partition(" ")
        query = args.strip().lower()
        choices = configured_model_choices()
        if query:
            choices = [
                choice
                for choice in choices
                if query in f"{choice[0]} {choice[1]} {choice[2]}".lower()
            ]
        if not choices:
            self._append_notice("No matching models.")
            return

        highlighted = self.query_one("#suggestions", OptionList).highlighted
        selected = highlighted if highlighted is not None else 0
        selected_model = ""
        if 0 <= selected < len(self.completion_candidates):
            selected_model = self.completion_candidates[selected].text.strip()
        if selected_model:
            matching_choice = next(
                (choice for choice in choices if choice[1] == selected_model),
                None,
            )
        else:
            matching_choice = choices[0]
        if matching_choice is None:
            self._append_notice("No matching models.")
            return
        slug, model, display_name, _is_free = matching_choice
        old_model = self.session.config.model
        if not switch_model(self.session, slug, model):
            self._append_error("Model unavailable.")
            return
        capture_analytics(
            "model_changed",
            {"provider": slug, "from_model": old_model, "to_model": model},
        )
        self._refresh_status("ready")
        self._update_info_panel()
        self._append_notice(f"Switched to {display_name} / {model}")

    def _handle_new(self) -> None:
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

        history = InputHistory(self.state.history)
        stdout = _TuiCaptureWriter()
        stderr = _TuiCaptureWriter()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            new_session, should_continue = handle_input(self.session, value, history)
        self.session = new_session
        self.state.history = history.entries
        output = _command_output_text(stdout, stderr)
        if output:
            self._append_entry(output, "ansi")
        self._refresh_status("ready")
        self._update_info_panel()
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
                    subprocess.Popen(["open", str(src_path)])  # nosec B603
                elif sys.platform == "linux":
                    subprocess.Popen(["xdg-open", str(src_path)])  # nosec B603
                self._append_notice(f"Opened {src_path}")
            else:
                preview = result.chunk_text[:200]
                self._append_notice(
                    f"Found in {result.armory_name}/{result.source_rel}: {preview}"
                )

        self.push_screen(SearchScreen(), on_search_result)

    def _run_turn(self, user_input: str) -> None:
        def on_reply(reply: str) -> None:
            self.call_from_thread(self._append_assistant_reply, reply)

        def on_notice(notice: str) -> None:
            self.call_from_thread(self._append_notice, notice)

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
        )

    def _completion_menu_visible(self) -> bool:
        suggestions = self.query_one("#suggestions", OptionList)
        return suggestions.has_class("visible") and (
            bool(self.completion_candidates) or self._inline_flow.active
        )

    def _refresh_completions(self) -> None:
        composer = self.query_one("#composer", Input)
        before_cursor = composer.value[: composer.cursor_position]
        is_model_picker = _is_models_input(before_cursor)
        self.completion_candidates = self.completion_engine.candidates(
            before_cursor,
            _tui_command_suggestions(),
        )
        suggestions = self.query_one("#suggestions", OptionList)
        if not self.completion_candidates:
            suggestions.set_options([])
            suggestions.remove_class("visible")
            suggestions.remove_class("model-picker")
            return
        if is_model_picker:
            suggestions.add_class("model-picker")
        else:
            suggestions.remove_class("model-picker")
        suggestions.set_options(
            [
                self._format_completion_candidate(candidate)
                for candidate in self.completion_candidates
            ]
        )
        suggestions.add_class("visible")
        suggestions.highlighted = 0
        composer.focus()

    def _hide_completions(self) -> None:
        self.completion_candidates = []
        suggestions = self.query_one("#suggestions", OptionList)
        suggestions.set_options([])
        suggestions.remove_class("visible")
        suggestions.remove_class("model-picker")

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
            _MODEL_MENU_MAX_VISIBLE_ROWS if suggestions.has_class("model-picker") else 7,
        )

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

    def _record_history(self, value: str) -> None:
        value = value.strip()
        if not value:
            return
        if not self.state.history or self.state.history[-1] != value:
            self.state.history.append(value)
            self.state.history = self.state.history[-500:]
            if self.state.history_obj is not None:
                self.state.history_obj.add(value)
        self.state.history_index = None
        self.state.history_draft = ""

    def _history_previous(self) -> None:
        if not self.state.history:
            return
        composer = self.query_one("#composer", Input)
        if self.state.history_index is None:
            self.state.history_draft = composer.value
            self.state.history_index = len(self.state.history) - 1
        else:
            self.state.history_index = max(0, self.state.history_index - 1)
        composer.value = self.state.history[self.state.history_index]
        composer.cursor_position = len(composer.value)

    def _history_next(self) -> None:
        if self.state.history_index is None:
            return
        composer = self.query_one("#composer", Input)
        if self.state.history_index >= len(self.state.history) - 1:
            composer.value = self.state.history_draft
            self.state.history_index = None
            self.state.history_draft = ""
        else:
            self.state.history_index += 1
            composer.value = self.state.history[self.state.history_index]
        composer.cursor_position = len(composer.value)

    def _start_thinking_animation(self) -> None:
        self._thinking_start = time.monotonic()
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(f"[dim]{_THINKING_FRAMES[0]} thinking...[/dim]")
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
        indicator.update(f"[dim]{_THINKING_FRAMES[frame_idx]} thinking...[/dim]")

    def _stop_thinking_animation(self) -> None:
        if self._thinking_timer is not None:
            self._thinking_timer.stop()  # type: ignore[union-attr]  # ty:ignore[unresolved-attribute]
            self._thinking_timer = None
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update("")
        indicator.remove_class("active")
        indicator.add_class("hidden")
        self._refresh_footer_hints()


def run_tui(session: ChatSession | None = None) -> None:
    """Run the command-first Textual shell."""
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

    palette = current_palette()
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
            HephaistosTui(session_ref[0], state, palette).run()

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
                state.transcript.append(_TuiTranscriptEntry(output, "ansi"))
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
