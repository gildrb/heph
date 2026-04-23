"""Chat-first interactive shell with rich terminal UX.

Features:
- Slash commands with tab-autocomplete
- Shell mode via ! prefix
- Arrow-key history navigation
- Multi-line input with backslash continuation
- Streaming interrupt via Ctrl+C

All keybindings are configurable via ``DEFAULT_SHELL_KEYBINDINGS``.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess  # nosec B404
import sys
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit.application import Application, run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import ANSI, FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import DynamicStyle
from prompt_toolkit.styles import Style as PtStyle

from hephaistos import __version__
from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands import get_registry
from hephaistos.app.display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    STYLE_PROMPT,
    format_shell_header,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.app.input_history import InputHistory
from hephaistos.app.keybindings import DEFAULT_SHELL_KEYBINDINGS
from hephaistos.app.palette import (
    set_theme,
    shell_style_dict,
)
from hephaistos.armory.storage import ArmoryError
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, EngineError, StreamRecoveryError
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    save_session,
    send_user_message,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.harness.persona import list_personas
from hephaistos.logging import get_logger
from hephaistos.observability import capture_exception
from hephaistos.parameters.cli import load_config
from hephaistos.parameters.settings import load_app_settings
from hephaistos.providers.config import Provider, ProviderConfig
from hephaistos.telemetry import mark_telemetry_notice_seen, should_show_telemetry_notice
from hephaistos.vocab.parser import scan_armory

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"
_log = get_logger("app.shell")

_PT_STYLE = DynamicStyle(lambda: PtStyle.from_dict(shell_style_dict()))


@dataclass
class ShellRuntime:
    busy: bool = False
    steering_count: int = 0
    abort_event: threading.Event = field(default_factory=threading.Event)
    worker: threading.Thread | None = None


class SlashCommandCompleter(Completer):
    """Context-aware completion for slash commands and their common arguments."""

    def __init__(self) -> None:
        self._cached_providers: dict[str, Provider] = {}
        self._refresh_provider_cache()

    def _refresh_provider_cache(self) -> None:
        """Reload provider list from cached config."""
        self._cached_providers = dict(ProviderConfig.load().providers)

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        text = document.text_before_cursor
        stripped = text.lstrip()

        if not stripped.startswith("/") or "\n" in stripped:
            return

        body = stripped[1:]
        registry = get_registry()

        if not body or " " not in body:
            prefix = body.lower()
            seen: set[str] = set()
            for cmd in registry.commands:
                if cmd.hidden:
                    continue
                matches_name = cmd.name.lower().startswith(prefix)
                matches_alias = any(alias.lower().startswith(prefix) for alias in cmd.aliases)
                if not (matches_name or matches_alias) or cmd.name in seen:
                    continue
                seen.add(cmd.name)
                yield Completion(
                    text=cmd.name + " ",
                    start_position=-len(body),
                    display_meta=cmd.description,
                )
            return

        parts = body.split()
        if not parts:
            return

        ends_with_space = stripped.endswith(" ")
        cmd_name = parts[0].lower()
        arg_parts = parts[1:]
        if ends_with_space:
            arg_parts.append("")

        for suggestion, description in self._argument_suggestions(cmd_name, arg_parts):
            current = arg_parts[-1] if arg_parts else ""
            if current and not suggestion.lower().startswith(current.lower()):
                continue
            suffix = "" if suggestion.endswith(" ") else " "
            yield Completion(
                text=suggestion + suffix,
                start_position=-len(current),
                display_meta=description,
            )

    def _argument_suggestions(
        self,
        cmd_name: str,
        arg_parts: list[str],
    ) -> list[tuple[str, str]]:
        if cmd_name == "api":
            if len(arg_parts) <= 1:
                return [
                    ("key", "Store an API key for the active provider"),
                    ("url", "Override the provider base URL"),
                ]
            return []

        if cmd_name == "provider":
            return self._provider_suggestions(arg_parts)

        if cmd_name == "model":
            return [(model, f"via {slug}") for slug, model in self._all_models()]

        if cmd_name == "persona":
            return self._persona_suggestions(arg_parts)

        return []

    def _provider_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) <= 1:
            return [
                ("use", "Switch active provider (and optional model)"),
                ("model", "Switch model within the active provider"),
            ]

        subcmd = arg_parts[0].lower()
        providers = self._cached_providers

        if subcmd == "use":
            if len(arg_parts) == 2:
                return [(slug, provider.display_name) for slug, provider in providers.items()]
            if len(arg_parts) == 3:
                provider = providers.get(arg_parts[1].lower())
                if provider is None:
                    return []
                return [(model, provider.display_name) for model in provider.models]

        if subcmd == "model":
            active = ProviderConfig.load().get_active()
            if active is None:
                return []
            return [(model, active.display_name) for model in active.models]

        return []

    def _all_models(self) -> list[tuple[str, str]]:
        providers = self._cached_providers
        models: list[tuple[str, str]] = []
        for slug, provider in providers.items():
            models.extend((slug, model) for model in provider.models)
        return models

    def _persona_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) > 1:
            return []
        return [(p.slug, p.description) for p in list_personas()]


def _toolbar_columns(default: int = 80) -> int:
    """Return the active terminal width for toolbar/background padding."""
    return max(default, shutil.get_terminal_size(fallback=(default, 24)).columns)


def _build_bottom_toolbar_status(
    session: ChatSession,
    runtime: ShellRuntime | None = None,
) -> str:
    """Build the compact helper bar shown below the composer."""
    api_state = "configured" if session.config.resolved_api_key else "missing"
    if runtime is not None and runtime.busy:
        steering_suffix = f" · queued {runtime.steering_count}" if runtime.steering_count else ""
        return f"assistant working · enter queues follow-up · ctrl+c interrupt{steering_suffix}"
    input_hint = "alt+enter newline · /help commands · /settings prefs · ! shell"
    if api_state == "missing":
        return f"{input_hint} · api missing"
    return input_hint


def _refresh_bottom_toolbar(
    session: ChatSession,
    toolbar_ref: list[str],
    runtime: ShellRuntime | None = None,
) -> None:
    """Refresh the cached prompt_toolkit toolbar text for the active session."""
    toolbar_ref[0] = _build_bottom_toolbar_status(session, runtime)


def _get_bottom_toolbar(toolbar_ref: list[str]):
    """Return the cached metadata shown below the composer."""
    line = toolbar_ref[0]
    width = _toolbar_columns()
    fragments: list[tuple[str, str]] = []
    if not line:
        return FormattedText([])
    if "api missing" in line:
        prefix, suffix = line.split("api missing", 1)
        used = len(prefix) + len("api missing") + len(suffix)
        fragments.append(("class:bottom-toolbar", prefix))
        fragments.append(("class:toolbar-error", "api missing"))
        fragments.append(("class:bottom-toolbar", suffix))
        fragments.append(("class:bottom-toolbar", " " * max(0, width - used)))
        return FormattedText(fragments)
    if line.startswith("assistant working"):
        prefix, suffix = line.split("assistant working", 1)
        used = len(prefix) + len("assistant working") + len(suffix)
        fragments.append(("class:bottom-toolbar", prefix))
        fragments.append(("class:toolbar-accent", "assistant working"))
        fragments.append(("class:bottom-toolbar", suffix))
        fragments.append(("class:bottom-toolbar", " " * max(0, width - used)))
        return FormattedText(fragments)
    fragments.append(("class:bottom-toolbar", line))
    fragments.append(("class:bottom-toolbar", " " * max(0, width - len(line))))
    return FormattedText(fragments)


def _discover_startup_armory() -> Path | None:
    candidates = [Path.cwd(), Path.cwd() / "armory"]
    for candidate in candidates:
        try:
            return validate_armory_path(str(candidate))
        except ArmoryError:
            continue
    default_armory = load_app_settings().default_armory_path
    if default_armory:
        try:
            return validate_armory_path(default_armory)
        except ArmoryError as exc:
            print_info(f"Saved default armory unavailable: {exc}")
    return None


def _run_shell_command(cmd: str) -> None:
    """Execute a shell command and display output.

    **Security note**: This is the user-initiated ``!`` shell escape.
    Commands run with the full privileges of the current user.  The
    ``!`` prefix makes this intentional and user-controlled.

    When a caller has redirected ``sys.stdout`` (e.g. the fullscreen shell
    piping into its chat buffer) the subprocess output is captured and
    re-emitted through the redirected stream so it renders inside the
    fullscreen layout instead of being written directly to the terminal.
    """
    print(styled(f"$ {cmd}", STYLE_DIM))
    capture = getattr(sys.stdout, "_hephaistos_chat_capture", False)
    try:
        result = subprocess.run(  # nosec B602
            cmd,
            shell=True,
            capture_output=bool(capture),
            text=True,
            check=False,
        )
    except Exception as exc:
        print_error(str(exc))
        return
    if capture:
        if result.stdout:
            sys.stdout.write(result.stdout)
            if not result.stdout.endswith("\n"):
                sys.stdout.write("\n")
        if result.stderr:
            print_error(result.stderr.rstrip("\n"))


def _preflight_config_check(session: ChatSession) -> str | None:
    """Return an error message if the session config is unusable, else None."""
    if not session.config.base_url:
        return "No provider configured. Use /provider use <slug> to select one."
    if not session.config.model:
        return "No model configured. Use /model to select one."
    if not session.config.resolved_api_key:
        return (
            "No API key found. "
            "Configure one via /api key, environment variable, or OAuth (/login)."
        )
    return None


def _report_engine_error(
    exc: EngineError | StreamRecoveryError,
    session: ChatSession,
) -> None:
    """Display an engine error and capture local diagnostic context."""
    if isinstance(exc, StreamRecoveryError):
        msg = (
            f"{styled('warning:', STYLE_ERROR)} "
            f"Stream interrupted — connection lost after partial reply."
        )
        if exc.partial_content:
            msg += f" ({len(exc.partial_content)} chars received)"
        print(msg)
        capture_exception(
            exc,
            context={
                "provider": session.config.provider_slug,
                "model": session.config.model,
                "partial_content_length": len(exc.partial_content),
            },
        )
        capture_analytics(
            "request_failed",
            {
                "provider": session.config.provider_slug or "unknown",
                "model": session.config.model,
                "kind": "stream_recovery",
                "partial_content_length": len(exc.partial_content),
            },
        )
    else:
        print_error(str(exc))
        capture_exception(
            exc,
            context={
                "provider": session.config.provider_slug,
                "model": session.config.model,
            },
        )
        capture_analytics(
            "request_failed",
            {
                "provider": session.config.provider_slug or "unknown",
                "model": session.config.model,
                "kind": "engine_error",
            },
        )


# ---------------------------------------------------------------------------
# Fullscreen shell
# ---------------------------------------------------------------------------

# Chat lines are ``(style_class, text)`` tuples compatible with FormattedText.
ChatFragment = tuple[str, str]


@dataclass
class _ChatWriter:
    """Stdout proxy that funnels writes into a chat-buffer callback."""

    emit: Callable[[str], None]
    _buffer: str = ""
    _hephaistos_chat_capture: bool = True

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.emit(line + "\n")
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self.emit(self._buffer)
            self._buffer = ""

    def isatty(self) -> bool:
        return False


@contextlib.contextmanager
def _capture_stdout_to_chat(emit: Callable[[str], None]) -> Iterator[None]:
    """Redirect ``sys.stdout`` to a chat-emitter for the duration of the block."""
    original = sys.stdout
    proxy = _ChatWriter(emit=emit)
    sys.stdout = proxy
    try:
        yield
    finally:
        proxy.flush()
        sys.stdout = original


def _append_chat_text(
    chat_lines: list[ChatFragment],
    text: str,
    default_style: str = "class:chat-area",
) -> None:
    """Append ANSI-aware text to ``chat_lines`` as styled fragments.

    If ``text`` contains ANSI escape codes (as emitted by ``styled(...)``) they
    are parsed into prompt_toolkit fragments so the fullscreen renderer shows
    bold/colored text correctly.  Plain text falls back to ``default_style``.
    """
    if not text:
        return
    parsed = list(ANSI(text).__pt_formatted_text__())
    if parsed:
        for fragment in parsed:
            style = fragment[0]
            segment = fragment[1]
            chat_lines.append((style or default_style, segment))
    else:
        chat_lines.append((default_style, text))


def _start_fullscreen_reply(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    runtime: ShellRuntime,
    chat_lines: list[ChatFragment],
    app_ref: list[Application[None] | None],
    toolbar_ref: list[str],
) -> None:
    """Start a streamed assistant reply whose output is routed to ``chat_lines``."""
    history.add(user_input)

    config_error = _preflight_config_check(session)
    if config_error:
        _append_chat_text(chat_lines, f"{styled('error:', STYLE_ERROR)} {config_error}\n")
        _invalidate_app(app_ref)
        return

    runtime.busy = True
    runtime.steering_count = 0
    runtime.abort_event.clear()
    _refresh_bottom_toolbar(session, toolbar_ref, runtime)
    _invalidate_app(app_ref)

    reply_prefix = f"\n{styled('Assistant:', STYLE_ASSISTANT)} "

    def _writer(text: str) -> None:
        _append_chat_text(chat_lines, text, default_style="class:chat-area.assistant")
        _invalidate_app(app_ref)

    def _worker() -> None:
        try:
            send_user_message(
                session,
                user_input,
                abort=runtime.abort_event,
                reply_prefix=reply_prefix,
                writer=_writer,
            )
        except (StreamRecoveryError, EngineError) as exc:
            _append_chat_text(
                chat_lines,
                f"{styled('error:', STYLE_ERROR)} {exc}\n",
                default_style="class:chat-area.error",
            )
            capture_exception(
                exc,
                context={
                    "provider": session.config.provider_slug,
                    "model": session.config.model,
                },
            )
            capture_analytics(
                "request_failed",
                {
                    "provider": session.config.provider_slug or "unknown",
                    "model": session.config.model,
                    "kind": (
                        "stream_recovery"
                        if isinstance(exc, StreamRecoveryError)
                        else "engine_error"
                    ),
                },
            )
        finally:
            runtime.worker = None
            runtime.abort_event.clear()
            runtime.busy = False
            _refresh_bottom_toolbar(session, toolbar_ref, runtime)
            _invalidate_app(app_ref)

    runtime.worker = threading.Thread(target=_worker, name="hephaistos-shell-reply", daemon=True)
    runtime.worker.start()


def _invalidate_app(app_ref: list[Application[None] | None]) -> None:
    app = app_ref[0]
    if app is None:
        return
    with contextlib.suppress(Exception):
        app.invalidate()


def _handle_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    streaming: bool = False,
) -> tuple[ChatSession, bool]:
    """Process a single input. Returns (session, should_continue).

    If *streaming* is True, the agent is currently running. The input is
    enqueued as a steering message instead of being processed normally.
    """
    if not user_input or not user_input.strip():
        return session, True
    if streaming:
        session.steering.enqueue(user_input)
        return session, True
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            _run_shell_command(cmd)
        return session, True
    if user_input.startswith("/"):
        history.add(user_input)
        stripped = user_input.strip()
        if stripped == "/":
            registry = get_registry()
            cmd = registry.find("help")
            if cmd:
                cmd.handle(session, "")
            return session, True
        space_idx = stripped.find(" ")
        if space_idx == -1:
            cmd_name = stripped[1:].lower()
            cmd_args = ""
        else:
            cmd_name = stripped[1:space_idx].lower()
            cmd_args = stripped[space_idx + 1 :].strip()

        registry = get_registry()
        cmd = registry.find(cmd_name)
        if cmd is None:
            print_error(f"Unknown command: {stripped}")
            print_info("Type /help for available commands.")
            return session, True

        result = cmd.handle(session, cmd_args)

        if result.should_exit:
            return session, False

        if result.new_session is not None:
            session = result.new_session
        if result.output and result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:") :]
            history.add(new_input)
            config_error = _preflight_config_check(session)
            if config_error:
                print_error(config_error)
                return session, True
            abort = threading.Event()
            reply_prefix = f"\r{styled('Assistant:', STYLE_ASSISTANT)} "
            try:
                send_user_message(session, new_input, abort=abort, reply_prefix=reply_prefix)
            except (StreamRecoveryError, EngineError) as exc:
                _report_engine_error(exc, session)
        return session, True
    history.add(user_input)
    config_error = _preflight_config_check(session)
    if config_error:
        print_error(config_error)
        return session, True
    abort = threading.Event()
    reply_prefix = f"\r{styled('Assistant:', STYLE_ASSISTANT)} "
    try:
        send_user_message(session, user_input, abort=abort, reply_prefix=reply_prefix)
    except (StreamRecoveryError, EngineError) as exc:
        _report_engine_error(exc, session)
    return session, True


def _get_history_path(session: ChatSession) -> Path:
    if session.armory_path is None:
        return _HISTORY_DIR / "plain-history"
    return session.armory_path / ".hephaistos" / "history"


def _save_on_exit(session: ChatSession) -> None:
    if session.dirty and session_has_messages(session) and session.armory_path is not None:
        try:
            path = save_session(session)
            print_success(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
    session.trace.close()


def _create_startup_session(config: ChatConfig) -> ChatSession:
    """Try to create a session with the auto-discovered armory, fall back to plain."""
    armory = _discover_startup_armory()
    if armory is None:
        return create_plain_session(config)
    try:
        return create_session(config, armory)
    except SessionError as exc:
        print_error(f"Auto-discovered armory unusable: {exc}")
        print_info("Falling back to plain chat mode.")
        return create_plain_session(config)


def _build_fullscreen_keybindings(
    keybindings: dict[str, str | list[str]],
    runtime: ShellRuntime,
    request_exit: Callable[[], None],
) -> KeyBindings:
    """Build keybindings for the fullscreen shell's input buffer."""
    kb = KeyBindings()

    submit_keys = keybindings["submit"]
    submit_key_list = (
        [k.strip() for k in submit_keys.split(",")]
        if isinstance(submit_keys, str)
        else submit_keys
    )

    @kb.add(*submit_key_list)
    def _(event: KeyPressEvent) -> None:
        buf = event.current_buffer
        line = buf.document.current_line_before_cursor
        if line.rstrip().endswith("\\"):
            stripped = line.rstrip()
            buf.delete_before_cursor(count=len(line) - len(stripped) + 1)
            buf.insert_text("\n")
            return
        if not buf.text.strip():
            return
        buf.validate_and_handle()

    newline_keys = keybindings["newline"]
    newline_key_list = (
        [k.strip() for k in newline_keys.split(",")]
        if isinstance(newline_keys, str)
        else newline_keys
    )

    @kb.add(*newline_key_list)
    def _(event: KeyPressEvent) -> None:
        event.current_buffer.insert_text("\n")

    @kb.add("c-c")
    def _(event: KeyPressEvent) -> None:
        if runtime.busy:
            runtime.abort_event.set()
            return
        event.current_buffer.reset()

    @kb.add("c-d")
    def _(event: KeyPressEvent) -> None:
        _ = event
        request_exit()

    return kb


def _default_history_path(session: ChatSession) -> Path:
    """Return the history file used by :func:`run_chat_shell`."""
    return _get_history_path(session)


def _stick_to_bottom(window: Window) -> int:
    """``get_vertical_scroll`` hook that anchors the chat pane to its tail."""
    info = window.render_info
    if info is None:
        return 0
    return max(0, info.content_height - info.window_height)


def _build_fullscreen_layout(
    header_fragments: Callable[[], FormattedText],
    chat_fragments: Callable[[], FormattedText],
    status_fragments: Callable[[], FormattedText],
    input_buffer: Buffer,
) -> tuple[Layout, Window]:
    """Build the Mole-style fullscreen layout.  Returns layout and chat Window."""
    header_window = Window(
        content=FormattedTextControl(header_fragments, focusable=False),
        height=Dimension(min=3, max=6),
        dont_extend_height=True,
        wrap_lines=True,
        style="class:header",
    )
    separator_top = Window(
        char="─",
        height=1,
        dont_extend_height=True,
        style="class:separator",
    )
    chat_window = Window(
        content=FormattedTextControl(chat_fragments, focusable=False),
        wrap_lines=True,
        style="class:chat-area",
        always_hide_cursor=True,
        get_vertical_scroll=_stick_to_bottom,
    )
    separator_mid = Window(
        char="─",
        height=1,
        dont_extend_height=True,
        style="class:separator",
    )
    input_window = Window(
        content=BufferControl(buffer=input_buffer, focusable=True),
        height=Dimension(min=1, max=5),
        dont_extend_height=True,
        wrap_lines=True,
        style="class:composer",
    )
    status_window = Window(
        content=FormattedTextControl(status_fragments, focusable=False),
        height=Dimension(min=1, max=2),
        dont_extend_height=True,
        style="class:bottom-toolbar",
    )
    layout = Layout(
        HSplit(
            [
                header_window,
                separator_top,
                chat_window,
                separator_mid,
                input_window,
                status_window,
            ]
        ),
        focused_element=input_window,
    )
    return layout, chat_window


def run_chat_shell(
    session: ChatSession | None = None,
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> None:
    """Run the interactive chat shell with rich terminal UX.

    Uses a single ``prompt_toolkit.Application(full_screen=True)`` with a
    Mole-style layout: header, chat history, input, status bar.  Streamed
    assistant replies, slash command output, and shell-escape output all
    render inline within the chat pane without leaving the alternate screen.
    Slash and ``!`` commands that spawn sub-applications (menus, directory
    browsers) use ``app.run_in_terminal`` to suspend the fullscreen layout
    briefly while the sub-application handles input.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _run_fallback_shell(session)
        return

    set_theme(load_app_settings().theme)
    if session is None:
        session = _create_startup_session(load_config())

    capture_analytics(
        "shell_started",
        {
            "mode": "armory" if session.armory_path is not None else "plain",
            "source_file_count": session.source_file_count,
            "model": session.config.model,
        },
    )

    kb_config = keybindings or DEFAULT_SHELL_KEYBINDINGS
    runtime = ShellRuntime()
    session_ref: list[ChatSession] = [session]
    chat_lines: list[ChatFragment] = []
    app_ref: list[Application[None] | None] = [None]
    toolbar_ref = [_build_bottom_toolbar_status(session, runtime)]
    history = InputHistory()
    history_path = _default_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # Seed the chat pane with the usual intro hints.
    _append_chat_text(
        chat_lines,
        f"{styled('/help', STYLE_PROMPT)} for commands  "
        f"{styled('/settings', STYLE_PROMPT)} for preferences  "
        f"{styled('!cmd', STYLE_PROMPT)} for shell\n\n",
        default_style="class:chat-area.system",
    )
    if session.armory_path is not None:
        try:
            deck = scan_armory(session.armory_path)
            if deck.cards:
                _append_chat_text(
                    chat_lines,
                    f"{styled('info:', STYLE_DIM)} Vocabulary deck detected "
                    f"({deck.size} words). Use {styled('/vocab', STYLE_PROMPT)} to drill.\n",
                    default_style="class:chat-area.system",
                )
        except Exception:
            _log.debug("vocabulary hint scan failed", exc_info=True)
    if should_show_telemetry_notice():
        _append_chat_text(
            chat_lines,
            f"{styled('info:', STYLE_DIM)} Optional anonymous analytics available. "
            f"Open {styled('/settings', STYLE_PROMPT)} to review.\n",
            default_style="class:chat-area.system",
        )
        mark_telemetry_notice_seen()

    def _header() -> FormattedText:
        s = session_ref[0]
        return FormattedText(
            format_shell_header(
                version=__version__,
                armory_path=str(s.armory_path or "none"),
                source_file_count=s.source_file_count or 0,
                model=s.config.model,
                has_api_key=bool(s.config.resolved_api_key),
            )
        )

    def _chat() -> FormattedText:
        marker = "+ " if runtime.busy else "> "
        # Show a live marker to hint who "owns" the next line.
        trailing: list[ChatFragment] = [("class:prompt-mark", f"\n{marker}")]
        return FormattedText([*chat_lines, *trailing])

    def _status() -> FormattedText:
        _refresh_bottom_toolbar(session_ref[0], toolbar_ref, runtime)
        return _get_bottom_toolbar(toolbar_ref)

    def _emit_chat(text: str) -> None:
        _append_chat_text(chat_lines, text, default_style="class:chat-area")
        _invalidate_app(app_ref)

    def _handle_command_in_terminal(user_input: str) -> None:
        """Run a slash/bang command with stdout captured into the chat pane.

        Executed via ``app.run_in_terminal`` so sub-applications (menus,
        directory browsers) can render in the normal terminal area without
        conflicting with the fullscreen outer app.
        """

        def _run() -> None:
            with _capture_stdout_to_chat(_emit_chat):
                s, cont = _handle_input(session_ref[0], user_input, history)
                session_ref[0] = s
                if not cont:
                    current = app_ref[0]
                    if current is not None:
                        current.exit()
            _refresh_bottom_toolbar(session_ref[0], toolbar_ref, runtime)
            _invalidate_app(app_ref)

        current_app = app_ref[0]
        if current_app is None:
            _run()
            return
        run_in_terminal(_run)

    def _accept(buff: Buffer) -> bool:
        user_input = buff.text
        buff.reset()
        stripped = user_input.strip()
        if not stripped:
            return False

        _append_chat_text(
            chat_lines,
            f"\n{styled('>', STYLE_PROMPT)} {user_input}\n",
            default_style="class:chat-area.user",
        )
        _invalidate_app(app_ref)

        # Exit shortcuts while a reply is streaming.
        if runtime.busy and stripped.lower() in {"/exit", "/quit", "/q"}:
            runtime.abort_event.set()
            worker = runtime.worker
            if worker is not None:
                worker.join(timeout=5.0)
            current = app_ref[0]
            if current is not None:
                current.exit()
            return False

        if runtime.busy:
            if user_input.startswith("/"):
                _handle_command_in_terminal(user_input)
                return False
            # Steering: enqueue the follow-up so the running turn picks it up.
            session_ref[0].steering.enqueue(user_input)
            history.add(user_input)
            runtime.steering_count += 1
            _refresh_bottom_toolbar(session_ref[0], toolbar_ref, runtime)
            _invalidate_app(app_ref)
            return False

        if user_input.startswith(("/", "!")):
            _handle_command_in_terminal(user_input)
            return False

        _start_fullscreen_reply(
            session_ref[0],
            user_input,
            history,
            runtime,
            chat_lines,
            app_ref,
            toolbar_ref,
        )
        return False

    input_buffer = Buffer(
        multiline=True,
        history=FileHistory(str(history_path)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        accept_handler=_accept,
    )

    def _request_exit() -> None:
        current = app_ref[0]
        if current is None:
            return
        if runtime.busy:
            runtime.abort_event.set()
            worker = runtime.worker
            if worker is not None:
                worker.join(timeout=5.0)
        current.exit()

    bindings = _build_fullscreen_keybindings(kb_config, runtime, _request_exit)

    layout, _chat_window = _build_fullscreen_layout(_header, _chat, _status, input_buffer)

    app: Application[None] = Application(
        layout=layout,
        key_bindings=bindings,
        style=_PT_STYLE,
        full_screen=True,
        mouse_support=False,
        erase_when_done=False,
    )
    app_ref[0] = app

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        app_ref[0] = None
        if runtime.busy:
            runtime.abort_event.set()
            worker = runtime.worker
            if worker is not None:
                worker.join(timeout=5.0)

    _save_on_exit(session_ref[0])


def _run_fallback_shell(session: ChatSession | None = None) -> None:
    """Simple fallback shell when the terminal is not a TTY."""
    set_theme(load_app_settings().theme)
    if session is None:
        session = _create_startup_session(load_config())

    print("Hephaistos (basic mode)")
    history = InputHistory()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        session, should_continue = _handle_input(session, user_input, history)
        if not should_continue:
            break

    _save_on_exit(session)
