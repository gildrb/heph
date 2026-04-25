# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportInvalidTypeArguments=false, reportInvalidTypeForm=false, reportOptionalCall=false
# pyright: reportUnknownParameterType=false
"""Experimental command-first Textual shell for Hephaistos.

Textual is optional, so imports stay lazy and the default CLI remains light.
Install it with ``uv sync --group tui``.
"""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from hephaistos import __version__
from hephaistos.app.shell import _create_startup_session  # type: ignore[reportPrivateUsage]
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.chat.engine import EngineError, StreamRecoveryError
from hephaistos.chat.session import ChatSession, send_user_message
from hephaistos.fuzzy import ranked_matches
from hephaistos.parameters.cli import load_config

try:
    from rich.markdown import Markdown
    from textual.app import App, ComposeResult
    from textual.widgets import Input, RichLog, Static
except ImportError:
    Markdown = None  # type: ignore[assignment]
    App = object  # type: ignore[assignment, misc]
    ComposeResult = object  # type: ignore[assignment, misc]
    Input = None  # type: ignore[assignment]
    RichLog = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pathlib import Path


class TuiDependencyError(RuntimeError):
    """Raised when the optional Textual dependency group is missing."""


@dataclass(frozen=True, slots=True)
class TuiCommand:
    """A typed command available inside the TUI composer."""

    signature: str
    description: str


_COMMANDS: tuple[TuiCommand, ...] = (
    TuiCommand("/help", "Show commands."),
    TuiCommand("/status", "Show model, mode, armory, and source count."),
    TuiCommand("/sources [query]", "List or fuzzy-filter source files."),
    TuiCommand("/clear", "Clear the visible transcript."),
    TuiCommand("/exit", "Leave the TUI."),
)


def _tui_dependency_message() -> str:
    return (
        "Textual UI dependencies are not available in this Python environment.\n"
        f"Current Python: {sys.executable}\n"
        "From a source checkout, run this from the repository root:\n"
        "  uv run --group tui heph tui\n"
        "For an installed or editable `heph` entrypoint, install the TUI extra "
        "into that same Python environment from the repository root:\n"
        f"  {sys.executable} -m pip install -e '.[tui]'"
    )


def _status_lines(session: ChatSession, state: str = "ready") -> str:
    armory = str(session.armory_path) if session.armory_path is not None else "none"
    model = session.config.model or "none"
    if session.config.resolved_api_key:
        api = "[#7F9A6A]configured[/#7F9A6A]"
    else:
        api = "[#CC3333]missing[/#CC3333]"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    state_tag = f"[{state}]" if state != "ready" else ""
    return (
        f"[bold #9B4A2E]Hephaistos[/bold #9B4A2E] [dim]v{__version__}[/dim]"
        f"{'  ' + state_tag if state_tag else ''}\n"
        f"[dim]armory[/dim] {armory}  "
        f"[dim]model[/dim] {model}  "
        f"[dim]api[/dim] {api}  "
        f"[dim]source[/dim] {source_str}\n"
        f"[dim]enter[/dim] send  "
        f"[dim]tab[/dim] complete  "
        f"[dim]ctrl+c[/dim] interrupt  "
        f"[dim]ctrl+d[/dim] exit"
    )


def _command_help() -> str:
    width = max(len(command.signature) for command in _COMMANDS)
    rows = [f"{command.signature:<{width}}  {command.description}" for command in _COMMANDS]
    return "\n".join(rows)


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


def run_tui(session: ChatSession | None = None) -> None:
    """Run the experimental command-first Textual shell."""
    if Markdown is None or Input is None or RichLog is None or Static is None:
        raise TuiDependencyError(_tui_dependency_message())

    if session is None:
        session = _create_startup_session(load_config())

    class HephaistosTui(App[None]):
        CSS = """
        Screen {
            layout: vertical;
        }
        #status {
            height: 3;
            padding: 0 1;
            color: #808080;
        }
        #transcript {
            height: 1fr;
            padding: 0 1;
            scrollbar-size: 0 0;
        }
        #composer {
            height: 3;
            color: #FFFFFF;
        }
        Input {
            border: none;
            border-bottom: tall #333;
            padding: 0 1;
        }
        Input:focus {
            border: none;
            border-bottom: tall #9B4A2E;
        }
        """

        BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
            ("ctrl+c", "cancel_turn", "Cancel"),
            ("ctrl+l", "clear_transcript", "Clear"),
            ("ctrl+d", "quit", "Quit"),
        ]

        def __init__(self, active_session: ChatSession) -> None:
            super().__init__()
            self.session = active_session
            self.abort_event = threading.Event()
            self.busy = False

        def compose(self) -> ComposeResult:
            yield Static(_status_lines(self.session), id="status")
            yield RichLog(id="transcript", markup=True, wrap=True, highlight=True)
            yield Input(placeholder="type a study prompt or /help", id="composer")

        def on_mount(self) -> None:
            self.title = "Hephaistos"
            self.sub_title = "command-first study shell"

        def on_input_submitted(self, event: Input.Submitted) -> None:
            value = event.value.strip()
            composer = self.query_one("#composer", Input)
            composer.value = ""
            if not value:
                return
            if self.busy:
                self.session.steering.enqueue(value)
                self._append_notice(f"Steering queued: {value}")
                return
            if self._handle_command(value):
                return
            config_error = _config_error(self.session)
            if config_error is not None:
                self._append_error(config_error)
                return
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
            self.query_one("#transcript", RichLog).clear()
            self._append_notice("Transcript cleared.")

        def _handle_command(self, value: str) -> bool:
            if not value.startswith("/"):
                return False
            command, _, args = value.partition(" ")
            if command in {"/exit", "/quit"}:
                self.exit()
                return True
            if command == "/clear":
                self.action_clear_transcript()
                return True
            if command == "/help":
                self.query_one("#transcript", RichLog).write(_command_help())
                return True
            if command == "/status":
                self.query_one("#transcript", RichLog).write(_status_lines(self.session))
                return True
            if command == "/sources":
                self.query_one("#transcript", RichLog).write(_source_listing(self.session, args))
                return True
            self._append_error(f"Unknown command: {command}. Type /help.")
            return True

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
                self.call_from_thread(self._append_error, str(exc))
            finally:
                self.call_from_thread(self._finish_turn)

        def _append_user(self, text: str) -> None:
            log = self.query_one("#transcript", RichLog)
            log.write(f"[bold #E0E0E0]You:[/bold #E0E0E0] {text}")
            log.write("[dim]assistant working...[/dim]")

        def _append_assistant_reply(self, text: str) -> None:
            log = self.query_one("#transcript", RichLog)
            log.write("[bold #7F9A6A]Assistant:[/bold #7F9A6A]")
            log.write(Markdown(text))

        def _append_notice(self, text: str) -> None:
            self.query_one("#transcript", RichLog).write(f"[#808080]{text}[/#808080]")

        def _append_error(self, text: str) -> None:
            self.query_one("#transcript", RichLog).write(
                f"[bold #CC3333]error:[/bold #CC3333] {text}"
            )

        def _finish_turn(self) -> None:
            self.busy = False
            self.abort_event.clear()
            self._refresh_status("ready")

        def _refresh_status(self, state: str = "ready") -> None:
            status = self.query_one("#status", Static)
            status.update(_status_lines(self.session, state))

    HephaistosTui(session).run()


def run_tui_for_path(path: Path | None) -> None:
    """Create or attach a session and run the Textual shell."""
    if path is None:
        run_tui()
        return
    session = resolve_armory_session(str(path))
    run_tui(session)
