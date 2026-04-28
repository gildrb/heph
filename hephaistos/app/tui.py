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
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING, ClassVar

from prompt_toolkit.history import FileHistory

from hephaistos import __version__
from hephaistos.app.armory_browser import ArmoryBrowserScreen
from hephaistos.app.autocomplete import (
    CommandSuggestion,
    CompletionCandidate,
    SlashCompletionEngine,
)
from hephaistos.app.commands import NewCommand, get_registry
from hephaistos.app.input_history import InputHistory
from hephaistos.app.palette import current_palette
from hephaistos.app.rich_transcript import enrich_reply, evidence_summary_text
from hephaistos.app.search_index import SearchResult
from hephaistos.app.search_screen import SearchScreen
from hephaistos.app.shell import (  # type: ignore[reportPrivateUsage]
    _create_startup_session,
    _get_history_path,
    _handle_input,
    _save_on_exit,
)
from hephaistos.app.workspace import _start_fresh_session  # type: ignore[reportPrivateUsage]
from hephaistos.armory.storage import validate as _validate_armory
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.chat.engine import EngineError, StreamRecoveryError, is_keyless_endpoint
from hephaistos.chat.resilience import is_network_error, offline_message
from hephaistos.chat.session import ChatSession, send_user_message
from hephaistos.fuzzy import ranked_matches
from hephaistos.parameters.cli import load_config

try:
    from rich.markdown import Markdown
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual import events
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
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
    Horizontal = object  # type: ignore[assignment, misc]
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


_TRANSCRIPT_ENTRY_GAP = ""


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
    keyless = is_keyless_endpoint(session.config.base_url)
    if keyless:
        api = "free"
    elif key_ok:
        api = "configured"
    else:
        api = "missing"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    state_tag = f" [{state}]" if state != "ready" else ""
    return (
        f"Hephaistos v{__version__}{state_tag}"
        f"  armory {armory}"
        f"  model {model}"
        f"  api {api}"
        f"  source {source_str}"
    )


def _status_text(session: ChatSession, state: str = "ready") -> Text:
    plain = _status_lines(session, state)
    palette = current_palette()
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = bool(session.config.resolved_api_key) or keyless
    if keyless:
        api = "free"
        api_style = palette.dim
    elif key_ok:
        api = "configured"
        api_style = palette.configured
    else:
        api = "missing"
        api_style = palette.error

    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    text = _RichText(plain, style=palette.dim)

    hep_idx = plain.index("Hephaistos")
    text.stylize(f"bold {palette.ember}", hep_idx, hep_idx + len("Hephaistos"))

    for label in ("armory", "model", "api", "source"):
        start = plain.index(label)
        text.stylize(f"dim {palette.dim}", start, start + len(label))

    api_start = plain.index(api, plain.index("api "))
    text.stylize(api_style, api_start, api_start + len(api))
    return text


def _footer_hints_text(session: ChatSession, *, busy: bool = False) -> Text:
    """Build contextual footer hints that change based on current state."""
    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    palette = current_palette()

    if busy:
        plain = "ctrl+c cancel"
        text = _RichText(plain, style=palette.dim)
        for label in ("ctrl+c",):
            start = plain.index(label)
            text.stylize(f"dim {palette.dim}", start, start + len(label))
        return text

    key_ok = bool(session.config.resolved_api_key) or is_keyless_endpoint(session.config.base_url)
    parts = ["enter send", "tab complete", "/help commands", "ctrl+d exit"]
    if not key_ok:
        parts.append("api missing")
    plain = "  ".join(parts)
    text = _RichText(plain, style=palette.dim)
    for label in ("enter", "tab", "/help", "ctrl+c", "ctrl+d"):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(f"dim {palette.dim}", start, start + len(label))
    for label in ("/help",):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(f"bold {palette.ember}", start, start + len(label))
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize(palette.error, api_start, api_start + len("api missing"))
    return text


def _info_panel_default_text(session: ChatSession) -> Text:
    """Build the default info panel content showing armory, model, sources."""
    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())
    title = session.title or "New conversation"
    armory_name = session.armory_path.name if session.armory_path is not None else "none"
    model = session.config.model or "none"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    evidence_str = evidence_summary_text(session.last_turn_evidence)

    lines: list[str] = [
        title,
        "\u2500" * 26,
        f"armory  {armory_name}",
        f"model   {model}",
        f"sources {source_str}",
        f"evidence {evidence_str}",
    ]
    plain = "\n".join(lines)
    text = _RichText(plain, style="#808080")
    title_end = len(lines[0])
    text.stylize("bold #9B4A2E", 0, title_end)
    for label in ("armory", "model", "sources", "evidence"):
        try:
            start = plain.index(label)
            text.stylize("dim #808080", start, start + len(label))
        except ValueError:
            pass
    return text


def _info_panel_message_text(
    entry: _TuiTranscriptEntry,
    session: ChatSession,
) -> Text:
    """Build info panel content for a focused transcript message."""
    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    is_user = entry.content.startswith("[bold #E0E0E0]You:")
    is_assistant = entry.kind == "markdown" and "Hephaistos:" in entry.content

    if is_user:
        content = entry.content.replace("[bold #E0E0E0]You:[/bold #E0E0E0] ", "")
        preview = content[:120] + ("..." if len(content) > 120 else "")
        sep = "\u2500" * 26
        plain = f"You message\n{sep}\n{preview}"
    elif is_assistant:
        model = session.config.model or "unknown"
        evidence_str = evidence_summary_text(session.last_turn_evidence)
        usage = session.usage.summary()
        sep = "\u2500" * 26
        plain = (
            f"Assistant reply\n{sep}"
            f"\nmodel   {model}"
            f"\ntokens  {usage['total_tokens']}"
            f"\ncost    ${usage['cost_usd']:.4f}"
            f"\nevidence {evidence_str}"
        )
    else:
        sep = "\u2500" * 26
        plain = f"Message\n{sep}\n{entry.kind}"

    text = _RichText(plain, style="#808080")
    first_newline = plain.index("\n") if "\n" in plain else len(plain)
    text.stylize("bold #9B4A2E", 0, first_newline)
    for label in ("model", "tokens", "cost", "evidence"):
        try:
            start = plain.index(label)
            text.stylize("dim #808080", start, start + len(label))
        except ValueError:
            pass
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
        return "No provider configured. Use /provider to select one."
    if not session.config.model:
        return "No model configured. Use /model to select one."
    if not session.config.resolved_api_key and not is_keyless_endpoint(session.config.base_url):
        return "No API key found. Configure one via /api key, env var, or OAuth first."
    return None


def _tui_css() -> str:
    """Generate TUI CSS from the current theme palette.

    Transparent themes (forge) use ``background: transparent`` so the
    terminal shows through.  Opaque themes set an explicit background
    colour on every surface so no transparency leaks.
    """
    p = current_palette()
    bg = "transparent" if p.is_transparent else p.background
    bt = "transparent"
    return f"""
App {{
    background: {bg};
    color: {p.text};
}}
Screen {{
    layout: vertical;
    background: {bg};
    color: {p.text};
    layers: base suggestions;
}}
#main-layout {{
    layer: base;
    layout: horizontal;
    height: 100%;
    width: 100%;
    background: {bg};
    color: {p.text};
}}
#shell {{
    layout: vertical;
    height: 100%;
    width: 1fr;
    background: {bg};
    color: {p.text};
}}
#status {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.dim};
}}
#transcript {{
    height: 1fr;
    padding: 0 0;
    background: {bg};
    color: {p.text};
    scrollbar-size: 0 0;
    background-tint: {bt};
}}
#transcript:focus {{
    background: {bg};
    background-tint: {bt};
}}
#transcript RichLog {{
    color: {p.text};
}}
#transcript RichLog .md-code-inline {{
    color: {p.text};
    text-style: bold;
}}
#thinking-indicator {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.dim};
    display: none;
}}
#thinking-indicator.active {{
    display: block;
}}
#composer-frame {{
    height: auto;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.text};
}}
#suggestions {{
    position: absolute;
    height: auto;
    max-height: 50%;
    width: 80%;
    padding-right: 1;
    margin-bottom: 1;
    background: {bg};
    color: {p.text};
    scrollbar-color: {p.highlight};
    scrollbar-color-hover: {p.stone};
    scrollbar-color-active: {p.stone};
    scrollbar-background: {p.panel};
    scrollbar-background-hover: {p.panel};
    scrollbar-background-active: {p.panel};
    scrollbar-corner-color: {bg};
    scrollbar-size-vertical: 1;
    layer: suggestions;
}}
.hidden {{
    visibility: hidden;
}}
OptionList {{
    width: 100%;
    background: {bg};
    color: {p.text};
    border: none;
    padding: 0;
}}
OptionList > .option-list--option {{
    background: {bg};
    color: {p.text};
    padding: 0 0;
}}
OptionList > .option-list--option-highlighted {{
    background: {p.highlight};
    color: {p.text};
    padding: 0 0;
}}
OptionList:focus > .option-list--option-highlighted {{
    background: {p.highlight};
    color: {p.text};
    padding: 0 0;
}}
#composer {{
    height: 1;
    min-height: 1;
    max-height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.text};
}}
#footer-hints {{
    height: 1;
    width: auto;
    max-width: 100%;
    margin-top: 1;
    background: {bg};
    color: {p.dim};
}}
#info-separator {{
    width: 1;
    height: 100%;
    background: {bg};
    color: {p.stone};
}}
#info-panel {{
    width: 30;
    min-width: 30;
    max-width: 30;
    height: 100%;
    padding: 0 1;
    background: {bg};
    color: {p.dim};
}}
Input {{
    height: 1;
    min-height: 1;
    max-height: 1;
    border: none;
    padding: 0 0;
    background: {bg};
    background-tint: {bt};
    color: {p.text};
}}
Input > .input--placeholder,
Input > .input--suggestion {{
    color: {p.dim};
}}
Input:focus {{
    border: none;
    background: {bg};
    background-tint: {bt};
}}
Input > .input--cursor {{
    background: {p.text};
    color: {p.panel};
}}
Input > .input--selection {{
    background: {p.stone};
}}
"""


_THINKING_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


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


def _transparent_horizontal_class() -> type[Horizontal]:
    """Return a Textual horizontal layout class whose empty cells have no background."""
    if Strip is None or _RichStyle is None:
        raise TuiDependencyError(_tui_dependency_message())
    strip_class = Strip
    transparent_style = _RichStyle()

    class TransparentHorizontal(Horizontal):  # type: ignore[misc]
        def render_line(self, _y: int) -> Strip:
            return strip_class.blank(self.size.width, transparent_style)

    return TransparentHorizontal


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


def _is_armory_command(value: str) -> bool:
    """Return True when *value* is a /armory command handled inline by the TUI."""
    stripped = value.strip().lower()
    return stripped in ("/armory", "/armory open", "/armory create")


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

    palette = current_palette()
    css = _tui_css()

    transparent_screen = _transparent_screen_class()
    transparent_vertical = _transparent_vertical_class()
    transparent_horizontal = _transparent_horizontal_class()
    transparent_static = _transparent_static_class()
    transparent_rich_log = _transparent_rich_log_class()
    transparent_input = _transparent_input_class()
    transparent_option_list = _transparent_option_list_class()

    screen_cls = transparent_screen if palette.is_transparent else Screen  # type: ignore[misc]
    vertical_cls = transparent_vertical if palette.is_transparent else Vertical
    horizontal_cls = transparent_horizontal if palette.is_transparent else Horizontal
    static_cls = transparent_static if palette.is_transparent else Static  # type: ignore[misc]
    rich_log_cls = transparent_rich_log if palette.is_transparent else RichLog  # type: ignore[misc]
    input_cls = transparent_input if palette.is_transparent else Input  # type: ignore[misc]
    option_list_cls = transparent_option_list if palette.is_transparent else OptionList  # type: ignore[misc]

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
        CSS = css

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
            self._thinking_timer: object = None
            self._thinking_start: float = 0.0
            self._focused_msg_index: int | None = None

        def get_default_screen(self) -> Screen:
            return screen_cls(id="_default")  # type: ignore[reportCallIssue]

        def compose(self) -> ComposeResult:
            with horizontal_cls(id="main-layout"):  # type: ignore[reportCallIssue]
                with vertical_cls(id="shell"):  # type: ignore[reportCallIssue]
                    yield static_cls(_status_text(self.session), id="status")
                    yield rich_log_cls(id="transcript", markup=True, wrap=True, highlight=True)
                    yield static_cls("", id="thinking-indicator")
                    with vertical_cls(id="composer-frame"):  # type: ignore[reportCallIssue]
                        yield input_cls(
                            placeholder='Ask anything... "What do I need to study next?"',
                            suggester=SlashSuggester(self.completion_engine),
                            id="composer",
                        )
                        yield static_cls(_footer_hints_text(self.session), id="footer-hints")
                yield static_cls("", id="info-separator")
                yield static_cls(_info_panel_default_text(self.session), id="info-panel")
            yield option_list_cls(id="suggestions", classes="hidden", markup=False)

        def on_mount(self) -> None:
            self.title = "Hephaistos"
            self.sub_title = "command-first study shell"
            for index, entry in enumerate(self.state.transcript):
                if index > 0:
                    self._write_transcript_gap()
                self._write_transcript_entry(entry)
            composer = self.query_one("#composer", Input)
            composer.focus()
            self.set_focus(composer)

        def on_click(self, event: events.Click) -> None:
            composer = self.query_one("#composer", Input)
            if self.focused is not composer:
                composer.focus()
                self.set_focus(composer)

        def on_key(self, event: events.Key) -> None:
            composer = self.query_one("#composer", Input)
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
            if event.key == "/" and not composer.value.strip():
                self._open_search()
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
            if value == "/new":
                self._record_history(value)
                self._handle_new()
                return
            if _is_armory_command(value):
                self._record_history(value)
                self._append_user(value, mark_working=False)
                self._handle_armory_browser(value)
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
                self._stop_thinking_animation()
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

        def _handle_armory_browser(self, value: str) -> None:
            allow_create = "create" in value.strip().lower()
            start = self.session.armory_path or None
            screen = ArmoryBrowserScreen(start, allow_create=allow_create)

            def on_result(result: Path | None) -> None:
                if result is None:
                    self._append_notice("Cancelled.")
                    return
                try:
                    _validate_armory(result)
                except Exception:
                    self._append_error(f"Not a valid armory: {result}")
                    return
                self.session = _start_fresh_session(self.session, result)
                self._refresh_status("ready")
                src_count = self.session.source_file_count or 0
                self._append_notice(f"Using armory {result}")
                if src_count:
                    self._append_notice(f"Loaded {src_count} file(s).")
                self.query_one("#composer", Input).focus()

            self.push_screen(screen, on_result)

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
                    for candidate in self.completion_candidates
                ]
            )
            suggestions.highlighted = 0
            suggestions.remove_class("hidden")
            self.set_focus(suggestions)
            self.set_focus(composer)
            self._position_suggestions()

        def _position_suggestions(self) -> None:
            suggestions = self.query_one("#suggestions", OptionList)
            composer_frame = self.query_one("#composer-frame")
            screen_height = self.size.height
            screen_width = self.size.width
            frame_region = composer_frame.region
            offset_y = frame_region.y - screen_height
            suggestions.styles.offset = (0, offset_y)
            suggestions.styles.width = int(screen_width * 0.85)

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
            suggestions.highlighted = (current + offset) % len(self.completion_candidates)

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

        def _write_transcript_gap(self) -> None:
            self.query_one("#transcript", RichLog).write(_TRANSCRIPT_ENTRY_GAP)

        def _append_entry(self, content: str, kind: str = "plain") -> None:
            if self.state.transcript:
                self._write_transcript_gap()
            entry = _TuiTranscriptEntry(content, kind)
            self.state.transcript.append(entry)
            self._write_transcript_entry(entry)

        def _append_plain(self, text: str) -> None:
            self._append_entry(text)

        def _append_user(self, text: str, *, mark_working: bool = True) -> None:
            p = current_palette()
            self._append_entry(f"[bold {p.text}]You:[/bold {p.text}] {text}")
            if mark_working:
                self._start_thinking_animation()

        def _append_assistant_reply(self, text: str) -> None:
            evidence = self.session.last_turn_evidence
            enriched = enrich_reply(text, evidence)
            entry = _TuiTranscriptEntry(enriched.markdown_text, "markdown")
            if self.state.transcript:
                self._write_transcript_gap()
            self.state.transcript.append(entry)
            log = self.query_one("#transcript", RichLog)
            log.write(Markdown(enriched.markdown_text))

        def _append_notice(self, text: str) -> None:
            p = current_palette()
            self._append_entry(f"[{p.dim}]{text}[/{p.dim}]")

        def _append_error(self, text: str) -> None:
            p = current_palette()
            self._append_entry(f"[bold {p.error}]error:[/bold {p.error}] {text}")

        def _finish_turn(self) -> None:
            self.busy = False
            self.abort_event.clear()
            self._stop_thinking_animation()
            self._refresh_status("ready")
            self._refresh_footer_hints()
            self._focused_msg_index = None
            self._update_info_panel()

        def _refresh_status(self, state: str = "ready") -> None:
            status = self.query_one("#status", Static)
            status.update(_status_text(self.session, state))

        def _refresh_footer_hints(self) -> None:
            hints = self.query_one("#footer-hints", Static)
            hints.update(_footer_hints_text(self.session, busy=self.busy))

        def _focus_message(self, direction: int) -> None:
            """Navigate transcript focus for the info panel. direction: -1=up, +1=down."""
            entries = [
                e
                for e in self.state.transcript
                if e.kind in ("markdown", "plain")
                and not e.content.startswith("[dim")
                and not e.content.startswith("[#808080]")
                and not e.content.startswith("[bold #CC3333]")
            ]
            if not entries:
                return
            if self._focused_msg_index is None:
                self._focused_msg_index = len(entries) - 1 if direction < 0 else 0
            else:
                self._focused_msg_index = max(
                    0, min(len(entries) - 1, self._focused_msg_index + direction)
                )
            entry = entries[self._focused_msg_index]
            panel = self.query_one("#info-panel", Static)
            panel.update(_info_panel_message_text(entry, self.session))

        def _update_info_panel(self) -> None:
            """Refresh the info panel to reflect current state."""
            panel = self.query_one("#info-panel", Static)
            if self._focused_msg_index is not None:
                entries = [
                    e
                    for e in self.state.transcript
                    if e.kind in ("markdown", "plain")
                    and not e.content.startswith("[dim")
                    and not e.content.startswith("[#808080]")
                    and not e.content.startswith("[bold #CC3333]")
                ]
                if self._focused_msg_index < len(entries):
                    panel.update(
                        _info_panel_message_text(entries[self._focused_msg_index], self.session)
                    )
                    return
            panel.update(_info_panel_default_text(self.session))

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
                self._thinking_timer.stop()  # type: ignore[union-attr]
                self._thinking_timer = None
            indicator = self.query_one("#thinking-indicator", Static)
            indicator.update("")
            indicator.remove_class("active")
            indicator.add_class("hidden")
            self._refresh_footer_hints()

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
