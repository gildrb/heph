# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportPrivateUsage=false
# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportInvalidTypeArguments=false, reportInvalidTypeForm=false, reportOptionalCall=false
# pyright: reportUnknownParameterType=false
"""Command-first Textual shell for Hephaistos.

Imports stay lazy so test suites can exercise dependency errors cleanly.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING, ClassVar

from prompt_toolkit.history import FileHistory

from hephaistos import __version__
from hephaistos.app.autocomplete import (
    CommandSuggestion,
    CompletionCandidate,
    SlashCompletionEngine,
)
from hephaistos.app.commands import get_registry
from hephaistos.app.input_history import InputHistory
from hephaistos.app.shell import (  # type: ignore[reportPrivateUsage]
    _create_startup_session,
    _get_history_path,
    _handle_input,
    _save_on_exit,
)
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.chat.engine import EngineError, StreamRecoveryError, is_keyless_endpoint
from hephaistos.chat.resilience import is_network_error, offline_message
from hephaistos.chat.session import ChatSession, send_user_message
from hephaistos.fuzzy import ranked_matches
from hephaistos.parameters.cli import load_config
from hephaistos.parameters.settings import load_app_settings

try:
    from rich.markdown import Markdown
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual import events
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.screen import Screen
    from textual.strip import Strip
    from textual.suggester import Suggester
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    _RichStyle = None  # type: ignore[assignment]
    Markdown = None  # type: ignore[assignment]
    Segment = None  # type: ignore[assignment]
    _RichText = None  # type: ignore[assignment]
    events = None  # type: ignore[assignment]
    App = object  # type: ignore[assignment, misc]
    ComposeResult = object  # type: ignore[assignment, misc]
    Vertical = object  # type: ignore[assignment, misc]
    Screen = object  # type: ignore[assignment, misc]
    Suggester = object  # type: ignore[assignment, misc]
    Strip = None  # type: ignore[assignment]
    Input = None  # type: ignore[assignment]
    OptionList = None  # type: ignore[assignment]
    RichLog = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text


class TuiDependencyError(RuntimeError):
    """Raised when the optional Textual dependency group is missing."""


def _tui_dependency_message() -> str:
    return (
        "Textual UI dependencies are not available in this Python environment.\n"
        f"Current Python: {sys.executable}\n"
        "From a source checkout, sync dependencies from the repository root:\n"
        "  uv sync --frozen\n"
        "For an installed or editable `heph` entrypoint, reinstall Hephaistos "
        "into that same Python environment from the repository root:\n"
        f"  {sys.executable} -m pip install -e ."
    )


def _status_lines(
    session: ChatSession,
    state: str = "ready",
) -> str:
    armory = str(session.armory_path) if session.armory_path is not None else "none"
    model = session.config.model or "none"
    key_ok = bool(session.config.resolved_api_key) or is_keyless_endpoint(session.config.base_url)
    api = "configured" if key_ok else "missing"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    state_tag = f"[{state}]" if state != "ready" else ""
    return (
        f"Hephaistos v{__version__}{'  ' + state_tag if state_tag else ''}\n"
        f"armory {armory}  "
        f"model {model}  "
        f"api {api}  "
        f"source {source_str}"
    )


def _status_text(session: ChatSession, state: str = "ready") -> Text:
    plain = _status_lines(session, state)
    key_ok = bool(session.config.resolved_api_key) or is_keyless_endpoint(session.config.base_url)
    api = "configured" if key_ok else "missing"
    api_style = "#7F9A6A" if key_ok else "#CC3333"

    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    text = _RichText(plain, style="#808080")
    text.stylize("bold #9B4A2E", 0, len("Hephaistos"))

    first_line_end = plain.index("\n")
    text.stylize("dim #808080", len("Hephaistos "), first_line_end)

    cursor = first_line_end + 1
    for label in ("armory", "model", "api", "source"):
        start = plain.index(label, cursor)
        text.stylize("dim #808080", start, start + len(label))
        cursor = start + len(label)

    api_start = plain.index(api, plain.index("api "))
    text.stylize(api_style, api_start, api_start + len(api))
    return text


def _composer_meta(session: ChatSession) -> str:  # pyright: ignore[reportUnusedFunction]
    key_ok = bool(session.config.resolved_api_key) or is_keyless_endpoint(session.config.base_url)
    api_hint = "" if key_ok else "api missing"

    session_count = load_app_settings().session_count
    parts = ["enter send", "tab complete", "/help commands", "ctrl+c interrupt", "ctrl+d exit"]
    if session_count >= 3:
        parts.extend(["/vocab drill", "/model model", "/theme theme"])
    if session_count >= 5:
        parts.extend(["! shell", "\\ continuation"])
    if api_hint:
        parts.append(api_hint)
    return "  ".join(parts)


def _composer_meta_text(session: ChatSession) -> Text:
    plain = _composer_meta(session)
    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    text = _RichText(plain, style="#808080")
    for label in ("enter", "tab", "/help", "ctrl+c", "ctrl+d", "/vocab", "/model", "/theme", "!"):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(
            "bold #9B4A2E" if label.startswith("/") or label == "!" else "dim #808080",
            start,
            start + len(label),
        )
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize("#CC3333", api_start, api_start + len("api missing"))
    return text


def _source_listing(session: ChatSession, query: str = "") -> str:
    files = list(session.source_files)
    if not files:
        return "No source files are attached."
    if query.strip():
        matches = ranked_matches(query, files, key=lambda value: value, limit=12, min_score=35.0)
        files = [match.value for match in matches]
        if not files:
            return f"No sources match: {query}"
    visible = files[:16]
    body = "\n".join(f"@{name}" for name in visible)
    if len(files) > len(visible):
        body += f"\n... {len(files) - len(visible)} more"
    return body


def _config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No provider configured. Use the classic shell /provider command first."
    if not session.config.model:
        return "No model configured. Use the classic shell /model command first."
    if not session.config.resolved_api_key:
        return "No API key found. Configure one via /api key, env var, or OAuth first."
    return None


_TUI_CSS = """
App {
    background: transparent;
    color: #E0E0E0;
}
Screen {
    layout: vertical;
    background: transparent;
    color: #E0E0E0;
}
#shell {
    layout: vertical;
    height: 100%;
    width: 100%;
    background: transparent;
    color: #E0E0E0;
}
#status {
    height: 2;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: transparent;
    color: #808080;
}
#transcript {
    height: 1fr;
    padding: 0 0;
    background: transparent;
    color: #E0E0E0;
    scrollbar-size: 0 0;
    background-tint: transparent;
}
#transcript:focus {
    background: transparent;
    background-tint: transparent;
}
#composer-frame {
    height: 11;
    min-height: 11;
    max-height: 11;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: transparent;
    color: #E0E0E0;
}
#suggestions {
    height: 7;
    min-height: 7;
    max-height: 7;
    width: 100%;
    max-width: 100%;
    padding-right: 1;
    margin-bottom: 1;
    background: transparent;
    color: #E0E0E0;
    scrollbar-color: #333333;
    scrollbar-color-hover: #444444;
    scrollbar-color-active: #555555;
    scrollbar-background: #111111;
    scrollbar-background-hover: #111111;
    scrollbar-background-active: #111111;
    scrollbar-corner-color: transparent;
    scrollbar-size-vertical: 1;
}
.hidden {
    visibility: hidden;
}
OptionList {
    width: 100%;
    background: transparent;
    color: #E0E0E0;
}
OptionList > .option-list--option {
    background: transparent;
    color: #E0E0E0;
}
OptionList > .option-list--option-highlighted {
    background: #333333;
    color: #FFFFFF;
}
OptionList:focus > .option-list--option-highlighted {
    background: #333333;
    color: #FFFFFF;
}
#composer {
    height: 1;
    min-height: 1;
    max-height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: transparent;
    color: #FFFFFF;
}
#composer-meta {
    height: 1;
    width: auto;
    max-width: 100%;
    margin-top: 1;
    background: transparent;
    color: #808080;
}
Input {
    height: 1;
    min-height: 1;
    max-height: 1;
    border: none;
    padding: 0 0;
    background: transparent;
    background-tint: transparent;
    color: #FFFFFF;
}
Input > .input--placeholder,
Input > .input--suggestion {
    color: #808080;
}
Input:focus {
    border: none;
    background: transparent;
    background-tint: transparent;
}
Input > .input--cursor {
    background: #E0E0E0;
    color: #000000;
}
Input > .input--selection {
    background: #555555;
}
"""


def _transparent_screen_class() -> type[Screen]:
    """Return a Textual screen class whose empty cells have no background."""
    if Strip is None or _RichStyle is None:
        raise TuiDependencyError(_tui_dependency_message())
    strip_class = Strip
    transparent_style = _RichStyle()

    class TransparentScreen(Screen[None]):  # type: ignore[index, misc]
        def render_line(self, _y: int) -> Strip:
            return strip_class.blank(self.size.width, transparent_style)

    return TransparentScreen


def _transparent_vertical_class() -> type[Vertical]:
    """Return a Textual vertical layout class whose empty cells have no background."""
    if Strip is None or _RichStyle is None:
        raise TuiDependencyError(_tui_dependency_message())
    strip_class = Strip
    transparent_style = _RichStyle()

    class TransparentVertical(Vertical):  # type: ignore[misc]
        def render_line(self, _y: int) -> Strip:
            return strip_class.blank(self.size.width, transparent_style)

    return TransparentVertical


def _style_without_black_background(style: _RichStyle | None) -> _RichStyle:
    if _RichStyle is None:
        raise TuiDependencyError(_tui_dependency_message())
    if style is None:
        return _RichStyle()
    bgcolor = style.bgcolor
    triplet = bgcolor.triplet if bgcolor is not None else None
    if triplet is None or (triplet.red, triplet.green, triplet.blue) != (0, 0, 0):
        return style
    return _RichStyle(
        color=style.color,
        bold=style.bold,
        dim=style.dim,
        italic=style.italic,
        underline=style.underline,
        blink=style.blink,
        blink2=style.blink2,
        reverse=style.reverse,
        conceal=style.conceal,
        strike=style.strike,
        underline2=style.underline2,
        frame=style.frame,
        encircle=style.encircle,
        overline=style.overline,
        link=style.link,
        meta=style.meta or None,
    )


def _transparent_strip(strip: Strip, cell_length: int) -> Strip:
    """Drop synthetic black backgrounds and pad short rows with transparent cells."""
    if Segment is None:
        raise TuiDependencyError(_tui_dependency_message())
    changed = False
    segments: list[Segment] = []
    for segment in strip:
        style = _style_without_black_background(segment.style)
        changed = changed or style is not segment.style
        segments.append(segment._replace(style=style))
    if not changed:
        return strip.extend_cell_length(cell_length, _RichStyle())
    return Strip(segments, strip.cell_length).extend_cell_length(cell_length, _RichStyle())


def _transparent_static_class() -> type[Static]:
    class TransparentStatic(Static):  # type: ignore[misc]
        def render_line(self, y: int) -> Strip:
            return _transparent_strip(super().render_line(y), self.size.width)

    return TransparentStatic


def _transparent_rich_log_class() -> type[RichLog]:
    class TransparentRichLog(RichLog):  # type: ignore[misc]
        def render_line(self, y: int) -> Strip:
            return _transparent_strip(super().render_line(y), self.size.width)

    return TransparentRichLog


def _transparent_input_class() -> type[Input]:
    class TransparentInput(Input):  # type: ignore[misc]
        def render_line(self, y: int) -> Strip:
            return _transparent_strip(super().render_line(y), self.size.width)

    return TransparentInput


def _transparent_option_list_class() -> type[OptionList]:
    class TransparentOptionList(OptionList):  # type: ignore[misc]
        def render_line(self, y: int) -> Strip:
            return _transparent_strip(super().render_line(y), self.size.width)

    return TransparentOptionList


def _slash_suggestion(engine: SlashCompletionEngine, value: str) -> str | None:
    return engine.suggestion(value, _tui_command_suggestions())


def _tui_command_suggestions() -> list[CommandSuggestion]:
    suggestions = get_registry().suggestions()
    suggestions.append(
        CommandSuggestion(
            name="sources",
            description="List or fuzzy-filter source files",
        )
    )
    return suggestions


def _command_help() -> str:  # pyright: ignore[reportUnusedFunction]
    suggestions = _tui_command_suggestions()
    max_name = max(len(s.name) for s in suggestions)
    lines: list[str] = []
    for s in sorted(suggestions, key=lambda s: s.name):
        padded = f"  /{s.name}".ljust(max_name + 4)
        lines.append(f"{padded} {s.description}")
    return "\n".join(lines)


def _command_output_text(stdout: StringIO, stderr: StringIO) -> str:
    parts = (stdout.getvalue().strip(), stderr.getvalue().strip())
    return "\n".join(part for part in parts if part)


@dataclass
class _TuiTranscriptEntry:
    content: str
    kind: str = "plain"


@dataclass
class _TuiRuntimeState:
    transcript: list[_TuiTranscriptEntry] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    history_file: FileHistory | None = None
    history_index: int | None = None
    history_draft: str = ""
    pending_input: str | None = None


class _TuiCaptureWriter(StringIO):
    """TTY-like stream for shared shell commands while the Textual app is parked."""

    encoding = "utf-8"

    def __init__(self) -> None:
        super().__init__()
        self.original_stdout = sys.stdout

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return self.original_stdout.fileno()


_TERMINAL_INTERACTIVE_COMMANDS = {
    "armory",
    "clear",
    "edit",
    "login",
    "logout",
    "model",
    "persona",
    "resume",
    "settings",
    "vocab",
}


def _pending_input_requires_terminal(value: str) -> bool:
    """Return True when a shared slash command should own the real terminal."""
    stripped = value.strip()
    if not stripped.startswith("/"):
        return False

    command, _, args = stripped[1:].partition(" ")
    command_name = command.lower()
    arg_text = args.strip()

    if command_name == "memory":
        return arg_text.lower().startswith("setup")
    if command_name == "model":
        return not arg_text
    if command_name == "persona":
        return not arg_text
    if command_name == "vocab":
        return arg_text.lower() != "status"

    return command_name in _TERMINAL_INTERACTIVE_COMMANDS


def _run_shell_escape_captured(command: str) -> str:
    """Run a user-requested shell escape and return output for the TUI transcript."""
    if not command:
        return ""

    parts = [f"$ {command}"]
    try:
        result = subprocess.run(  # nosec B602
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        parts.append(f"error: {exc}")
        return "\n".join(parts)

    if result.stdout:
        parts.append(result.stdout.rstrip("\n"))
    if result.stderr:
        parts.append(result.stderr.rstrip("\n"))
    return "\n".join(parts)


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
        session = _create_startup_session(load_config())

    transparent_screen = _transparent_screen_class()
    transparent_vertical = _transparent_vertical_class()
    transparent_static = _transparent_static_class()
    transparent_rich_log = _transparent_rich_log_class()
    transparent_input = _transparent_input_class()
    transparent_option_list = _transparent_option_list_class()

    session_ref: list[ChatSession] = [session]
    history_path = _get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_file = FileHistory(str(history_path))
    state = _TuiRuntimeState(
        history=list(history_file.load_history_strings())[-500:],
        history_file=history_file,
    )

    class SlashSuggester(Suggester):  # type: ignore[misc]
        def __init__(self, engine: SlashCompletionEngine) -> None:
            super().__init__()
            self.engine = engine

        async def get_suggestion(self, value: str) -> str | None:
            return _slash_suggestion(self.engine, value)

    class HephaistosTui(App[None]):
        CSS = _TUI_CSS

        BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
            ("tab", "complete", "Complete"),
            ("ctrl+c", "cancel_turn", "Cancel"),
            ("ctrl+l", "clear_transcript", "Clear"),
            ("ctrl+d", "quit", "Quit"),
        ]

        def __init__(self, active_session: ChatSession, runtime_state: _TuiRuntimeState) -> None:
            super().__init__()
            self.session = active_session
            self.state = runtime_state
            self.abort_event = threading.Event()
            self.busy = False
            self.completion_engine = SlashCompletionEngine()
            self.completion_candidates: list[CompletionCandidate] = []

        def get_default_screen(self) -> Screen:
            return transparent_screen(id="_default")

        def compose(self) -> ComposeResult:
            with transparent_vertical(id="shell"):  # type: ignore[reportCallIssue]
                yield transparent_static(_status_text(self.session), id="status")
                yield transparent_rich_log(id="transcript", markup=True, wrap=True, highlight=True)
                with transparent_vertical(id="composer-frame"):  # type: ignore[reportCallIssue]
                    yield transparent_option_list(id="suggestions", classes="hidden", markup=False)
                    yield transparent_input(
                        placeholder='Ask anything... "What do I need to study next?"',
                        suggester=SlashSuggester(self.completion_engine),
                        id="composer",
                    )
                    yield transparent_static(_composer_meta_text(self.session), id="composer-meta")

        def on_mount(self) -> None:
            self.title = "Hephaistos"
            self.sub_title = "command-first study shell"
            for entry in self.state.transcript:
                self._write_transcript_entry(entry)
            composer = self.query_one("#composer", Input)
            composer.focus()
            self.set_focus(composer)

        def on_key(self, event: events.Key) -> None:
            composer = self.query_one("#composer", Input)
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
            if self.focused is not composer and event.character and event.is_printable:
                composer.focus()
                self.set_focus(composer)
                composer.insert_text_at_cursor(event.character)
                event.prevent_default()
                event.stop()

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "composer":
                self._refresh_completions()

        def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
            if event.option_list.id != "suggestions":
                return
            self._apply_completion(event.index)
            event.stop()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            value = event.value.strip()
            composer = self.query_one("#composer", Input)
            composer.value = ""
            self._hide_completions()
            if not value:
                return
            if self.busy:
                self.session.steering.enqueue(value)
                self._record_history(value)
                self._append_notice(f"Steering queued: {value}")
                return
            if value == "/sources" or value.startswith("/sources "):
                self._record_history(value)
                self._append_user(value, mark_working=False)
                self._handle_sources(value)
                return
            if value.startswith(("/", "!")):
                self._record_history(value)
                self._append_user(value, mark_working=False)
                self.state.pending_input = value
                self.exit()
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
                self._append_notice("Interrupt requested.")

        def action_clear_transcript(self) -> None:
            self.state.transcript.clear()
            self.query_one("#transcript", RichLog).clear()
            self._append_notice("Transcript cleared.")

        def action_complete(self) -> None:
            if not self.completion_candidates:
                self._refresh_completions()
            if not self.completion_candidates:
                return
            suggestions = self.query_one("#suggestions", OptionList)
            highlighted = suggestions.highlighted
            self._apply_completion(highlighted if highlighted is not None else 0)

        def _handle_sources(self, value: str) -> None:
            _, _, args = value.partition(" ")
            self._append_plain(_source_listing(self.session, args))

        def _run_turn(self, user_input: str) -> None:
            parts: list[str] = []

            def writer(text: str) -> None:
                if text:
                    parts.append(text)

            try:
                send_user_message(
                    self.session,
                    user_input,
                    abort=self.abort_event,
                    writer=writer,
                )
                reply = "".join(parts).strip()
                if reply:
                    self.call_from_thread(self._append_assistant_reply, reply)
            except (StreamRecoveryError, EngineError) as exc:
                provider = self.session.config.provider_slug or "the provider"
                if is_network_error(exc):
                    self.call_from_thread(self._append_notice, offline_message(provider))
                else:
                    self.call_from_thread(self._append_error, str(exc))
            finally:
                self.call_from_thread(self._finish_turn)

        def _completion_menu_visible(self) -> bool:
            suggestions = self.query_one("#suggestions", OptionList)
            return bool(self.completion_candidates) and not suggestions.has_class("hidden")

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
                suggestions.add_class("hidden")
                return
            suggestions.set_options(
                [
                    self._format_completion_candidate(candidate)
                    for candidate in self.completion_candidates[:8]
                ]
            )
            suggestions.highlighted = 0
            suggestions.remove_class("hidden")

        def _hide_completions(self) -> None:
            self.completion_candidates = []
            suggestions = self.query_one("#suggestions", OptionList)
            suggestions.set_options([])
            suggestions.add_class("hidden")

        def _move_completion(self, offset: int) -> None:
            suggestions = self.query_one("#suggestions", OptionList)
            if not self.completion_candidates:
                return
            current = suggestions.highlighted
            if current is None:
                current = 0
            suggestions.highlighted = (current + offset) % min(len(self.completion_candidates), 8)

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
            self.set_focus(composer)
            self._refresh_completions()

        def _format_completion_candidate(self, candidate: CompletionCandidate) -> str:
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
                if self.state.history_file is not None:
                    self.state.history_file.append_string(value)
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

        def _write_transcript_entry(self, entry: _TuiTranscriptEntry) -> None:
            log = self.query_one("#transcript", RichLog)
            if entry.kind == "markdown":
                log.write(Markdown(entry.content))
            elif entry.kind == "ansi":
                if _RichText is None:
                    log.write(entry.content)
                    return
                log.write(_RichText.from_ansi(entry.content))
            else:
                log.write(entry.content)

        def _append_entry(self, content: str, kind: str = "plain") -> None:
            entry = _TuiTranscriptEntry(content, kind)
            self.state.transcript.append(entry)
            self._write_transcript_entry(entry)

        def _append_plain(self, text: str) -> None:
            self._append_entry(text)

        def _append_user(self, text: str, *, mark_working: bool = True) -> None:
            self._append_entry(f"[bold #E0E0E0]You:[/bold #E0E0E0] {text}")
            if mark_working:
                self._append_entry("[dim]assistant working...[/dim]")

        def _append_assistant_reply(self, text: str) -> None:
            self._append_entry("[bold #7F9A6A]Assistant:[/bold #7F9A6A]")
            self._append_entry(text, "markdown")

        def _append_notice(self, text: str) -> None:
            self._append_entry(f"[#808080]{text}[/#808080]")

        def _append_error(self, text: str) -> None:
            self._append_entry(f"[bold #CC3333]error:[/bold #CC3333] {text}")

        def _finish_turn(self) -> None:
            self.busy = False
            self.abort_event.clear()
            self._refresh_status("ready")

        def _refresh_status(self, state: str = "ready") -> None:
            status = self.query_one("#status", Static)
            status.update(_status_text(self.session, state))

    try:
        while True:
            HephaistosTui(session_ref[0], state).run()

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
                new_session, should_continue = _handle_input(
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
                new_session, should_continue = _handle_input(
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
        _save_on_exit(session_ref[0])


def run_tui_for_path(path: Path | None) -> None:
    """Create or attach a session and run the Textual shell."""
    if path is None:
        run_tui()
        return
    session = resolve_armory_session(str(path))
    run_tui(session)
