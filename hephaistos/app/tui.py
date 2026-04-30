# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportPrivateUsage=false
# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportInvalidTypeArguments=false, reportInvalidTypeForm=false, reportOptionalCall=false
# pyright: reportUnknownParameterType=false, reportArgumentType=false, reportUnusedFunction=false
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

from hephaistos import __version__
from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.armory_browser import ArmoryBrowserScreen
from hephaistos.app.autocomplete import (
    CommandSuggestion,
    CompletionCandidate,
    SlashCompletionEngine,
)
from hephaistos.app.commands import NewCommand, get_registry
from hephaistos.app.input_history import InputHistory
from hephaistos.app.materials_view import material_listing
from hephaistos.app.model_picker import configured_model_choices, switch_model
from hephaistos.app.palette import ThemePalette, current_palette
from hephaistos.app.rich_transcript import enrich_reply, evidence_summary_text
from hephaistos.app.search_index import SearchResult, load_known_armories
from hephaistos.app.search_screen import SearchScreen
from hephaistos.app.transparent import (
    make_blank_background_cls,
    make_transparent_cls,
    nonfocus_rich_log_class,
)
from hephaistos.app.workspace import (
    create_startup_session,
    get_history_path,
    handle_input,
    save_on_exit,
    start_fresh_session,
)
from hephaistos.armory.storage import ArmoryError
from hephaistos.armory.storage import validate as _validate_armory
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.chat.session import ChatSession, send_user_message
from hephaistos.memory.supermemory import supermemory_configured
from hephaistos.parameters.cli import load_config
from hephaistos.runtime import (
    EngineError,
    StreamRecoveryError,
    is_keyless_endpoint,
    is_network_error,
    missing_api_key_message,
    offline_message,
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
    Binding = None  # type: ignore[assignment]
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
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = keyless or bool(session.config.resolved_api_key)
    if keyless:
        api = "free"
    elif key_ok:
        api = "configured"
    else:
        api = "missing"
    mem_status = "on" if supermemory_configured() else "/memory"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    state_tag = f" [{state}]" if state != "ready" else ""
    return (
        f"Hephaistos v{__version__}{state_tag}"
        f"  armory {armory}"
        f"  model {model}"
        f"  api {api}"
        f"  memory {mem_status}"
        f"  materials {source_str}"
    )


def _status_text(session: ChatSession, state: str = "ready") -> Text:
    plain = _status_lines(session, state)
    palette = current_palette()
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = keyless or bool(session.config.resolved_api_key)
    if keyless:
        api = "free"
        api_style = palette.dim
    elif key_ok:
        api = "configured"
        api_style = palette.configured
    else:
        api = "missing"
        api_style = palette.error

    mem_configured = supermemory_configured()
    mem_status = "on" if mem_configured else "/memory"
    mem_style = palette.configured if mem_configured else palette.dim

    if _RichText is None:
        raise TuiDependencyError(_tui_dependency_message())

    text = _RichText(plain, style=palette.dim)

    hep_idx = plain.index("Hephaistos")
    text.stylize(f"bold {palette.ember}", hep_idx, hep_idx + len("Hephaistos"))

    for label in ("armory", "model", "api", "memory", "materials"):
        start = plain.index(label)
        text.stylize(f"dim {palette.dim}", start, start + len(label))

    api_start = plain.index(api, plain.index("api "))
    text.stylize(api_style, api_start, api_start + len(api))

    mem_value_start = plain.index(mem_status, plain.index("memory "))
    text.stylize(mem_style, mem_value_start, mem_value_start + len(mem_status))
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

    key_ok = is_keyless_endpoint(session.config.base_url) or bool(session.config.resolved_api_key)
    parts = [
        "enter send",
        "tab complete",
        "ctrl+p commands",
        "ctrl+a armory",
        "ctrl+d exit",
    ]
    if not key_ok:
        parts.append("api missing")
    plain = "  ".join(parts)
    text = _RichText(plain, style=palette.dim)
    for label in ("enter", "tab", "ctrl+p", "ctrl+a", "ctrl+c", "ctrl+d"):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(f"dim {palette.dim}", start, start + len(label))
    for label in ("ctrl+p",):
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
    """Build the default info panel content showing armory, model, materials."""
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
        f"materials {source_str}",
        f"evidence {evidence_str}",
    ]
    plain = "\n".join(lines)
    text = _RichText(plain, style="#808080")
    title_end = len(lines[0])
    text.stylize("bold #9B4A2E", 0, title_end)
    for label in ("armory", "model", "materials", "evidence"):
        try:
            start = plain.index(label)
            text.stylize("dim #808080", start, start + len(label))
        except ValueError:
            pass
    return text


def _armory_home_text() -> str:
    """Return the no-armory home card shown on first TUI launch."""
    recent = load_known_armories()[:5]
    lines = [
        "No armory attached.",
        "",
        "Press ctrl+a to open or create an armory.",
        "Put study files in materials/.",
        "Hephaistos handles indexing, retrieval, memory, chats, traces, and usage.",
    ]
    if recent:
        lines.extend(["", "Recent armories:"])
        lines.extend(f"  {path.name}  {path}" for path in recent)
    return "\n".join(lines)


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


def _config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No provider configured. Use /provider to select one."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not is_keyless_endpoint(session.config.base_url) and not session.config.resolved_api_key:
        return missing_api_key_message(session.config)
    return None


_source_listing = material_listing


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
    margin-top: 1;
    padding: 0 0;
    background: {bg};
    color: {p.text};
}}
#suggestions {{
    dock: bottom;
    margin-bottom: 3;
    height: auto;
    max-height: 7;
    min-width: 30;
    width: 85%;
    max-width: 85%;
    padding-right: 1;
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
    display: none;
}}
#suggestions.visible {{
    display: block;
}}
#suggestions.model-picker {{
    max-height: 20;
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

            class TransparentNonFocusRichLog(transparent_rich_log_base):  # type: ignore[misc]
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

    class TransparentNonFocusRichLog(base):  # type: ignore[misc]
        can_focus = False

    return TransparentNonFocusRichLog


def _transparent_input_class() -> type:
    return make_transparent_cls(Input)


def _transparent_option_list_class() -> type:
    return make_transparent_cls(OptionList)


def _slash_suggestion(engine: SlashCompletionEngine, value: str) -> str | None:
    return engine.suggestion(value, _tui_command_suggestions())


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


def _tui_command_suggestions() -> list[CommandSuggestion]:
    suggestions = get_registry().suggestions()
    suggestions.append(
        CommandSuggestion(
            name="sources",
            description="List or fuzzy-filter material files",
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
    history_obj: InputHistory | None = None
    history_index: int | None = None
    history_draft: str = ""
    pending_input: str | None = None
    armory_home_shown: bool = False


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
    if command_name == "persona":
        return not arg_text
    if command_name == "vocab":
        return arg_text.lower() != "status"

    return command_name in _TERMINAL_INTERACTIVE_COMMANDS


def _is_models_input(value: str) -> bool:
    stripped = value.lstrip().lower()
    return stripped == "/models" or stripped.startswith("/models ")


def _is_armory_command(value: str) -> bool:
    """Return True when *value* is a /armory command handled inline by the TUI."""
    stripped = value.strip().lower()
    return stripped == "/armory" or stripped.startswith("/armory ")


def _armory_command_mode(value: str) -> str | None:
    """Return the TUI armory browser mode, or None for invalid usage."""
    parts = value.strip().lower().split()
    command = tuple(parts)
    if command in (("/armory",), ("/armory", "menu")):
        return "manage"
    if command == ("/armory", "open"):
        return "open"
    if command in (("/armory", "create"), ("/armory", "new")):
        return "create"
    return None


def _armory_usage_message() -> str:
    return "Usage: /armory [open|create]\nOpen or create a local study armory."


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


class SlashSuggester(Suggester):  # type: ignore[misc]
    def __init__(self, engine: SlashCompletionEngine) -> None:
        super().__init__()
        self.engine = engine

    async def get_suggestion(self, value: str) -> str | None:
        return _slash_suggestion(self.engine, value)


class HephaistosTui(App[None]):
    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("tab", "complete", "Complete"),
        Binding("ctrl+p", "command_palette", "Commands", show=False),
        Binding("ctrl+a", "open_armory_home", "Armory", show=False),
        Binding("ctrl+s", "open_search", "Search", show=False),
        Binding("ctrl+c", "cancel_turn", "Cancel", show=False),
        Binding("ctrl+l", "clear_transcript", "Clear"),
        Binding("ctrl+d", "quit", "Quit"),
    ]

    def __init__(
        self,
        active_session: ChatSession,
        runtime_state: _TuiRuntimeState,
        palette: ThemePalette,
    ) -> None:
        super().__init__()
        self.CSS = _tui_css()
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

    def get_default_screen(self) -> Screen:
        return self._widgets.screen(id="_default")  # type: ignore[reportCallIssue]

    def compose(self) -> ComposeResult:
        w = self._widgets
        with w.horizontal(id="main-layout"):  # type: ignore[reportCallIssue]
            with w.vertical(id="shell"):  # type: ignore[reportCallIssue]
                yield w.static(_status_text(self.session), id="status")
                yield w.rich_log(id="transcript", markup=True, wrap=True, highlight=True)
                yield w.static("", id="thinking-indicator")
                yield w.option_list(id="suggestions", markup=False)
                with w.vertical(id="composer-frame"):  # type: ignore[reportCallIssue]
                    yield w.input(
                        placeholder='Ask anything... "What do I need to study next?"',
                        suggester=SlashSuggester(self.completion_engine),
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
            self._refresh_completions()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "suggestions":
            return
        self._apply_completion(event.index)
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        composer = self.query_one("#composer", Input)
        if value == "/models" or value.startswith("/models "):
            self._record_history(value)
            self._append_user(value, mark_working=False)
            self._handle_models(value)
            composer.value = ""
            self._hide_completions()
            return
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
        mode = _armory_command_mode(value)
        composer = self.query_one("#composer", Input)
        if mode is None:
            self._append_error(_armory_usage_message())
            composer.focus()
            return

        allow_create = mode in ("manage", "create")
        title = {
            "manage": "Armory",
            "open": "Open armory",
            "create": "Create armory",
        }[mode]
        start = self.session.armory_path or None
        screen = ArmoryBrowserScreen(start, allow_create=allow_create, title=title)

        def on_result(result: Path | None) -> None:
            if result is None:
                self._append_notice("Cancelled.")
                composer.focus()
                return
            try:
                _validate_armory(result)
            except OSError as exc:
                self._append_error(f"Could not read armory: {exc}")
                composer.focus()
                return
            except ArmoryError as exc:
                self._append_error(f"Not a valid armory: {exc}")
                composer.focus()
                return
            previous = self.session
            self.session = start_fresh_session(self.session, result)
            self._refresh_status("ready")
            self._focused_msg_index = None
            self._update_info_panel()
            src_count = self.session.source_file_count or 0
            if self.session is previous:
                self._append_error(f"Could not open armory: {result}")
            else:
                self._append_notice(f"Using armory {result}")
                if src_count:
                    self._append_notice(f"Loaded {src_count} file(s).")
            composer.focus()

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
        return bool(self.completion_candidates) and suggestions.has_class("visible")

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
        if not self.completion_candidates:
            return
        current = suggestions.highlighted
        if current is None:
            current = 0
        highlighted = (current + offset) % len(self.completion_candidates)
        suggestions.highlighted = highlighted
        suggestions.scroll_y = _completion_menu_scroll_y(
            highlighted,
            len(self.completion_candidates),
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
