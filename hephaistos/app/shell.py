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
import io
import shutil
import subprocess  # nosec B404
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit.application import Application
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import ANSI, FormattedText, to_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout, ScrollbarMargin, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
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


def _build_keybindings(
    keybindings: dict[str, str | list[str]],
) -> KeyBindings:
    """Build prompt_toolkit key bindings from a config dict."""
    kb = KeyBindings()
    submit_keys = keybindings["submit"]
    newline_keys = keybindings["newline"]

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

    newline_key_list = (
        [k.strip() for k in newline_keys.split(",")]
        if isinstance(newline_keys, str)
        else newline_keys
    )

    @kb.add(*newline_key_list)
    def _(event: KeyPressEvent) -> None:
        """Insert a newline (e.g. Alt+Enter)."""
        event.current_buffer.insert_text("\n")

    return kb


def _get_prompt_message(runtime: ShellRuntime | None = None):
    """Return the compact composer prefix used for every prompt line."""

    def message():
        marker = "+ " if runtime is not None and runtime.busy else "> "
        return FormattedText([("class:prompt-mark", marker)])

    return message


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
    """
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True, check=False)  # nosec B602
    except Exception as exc:
        print_error(str(exc))


def _invalidate_prompt(app: Application[object] | None) -> None:
    if app is None:
        return
    try:
        app.invalidate()
    except Exception:
        return


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


def _append_chat_text(chat_lines: list[tuple[str, str]], text: str) -> None:
    """Parse ANSI-escaped text and append it to ``chat_lines`` as fragments."""
    if not text:
        return
    fragments = to_formatted_text(ANSI(text))
    # ``to_formatted_text`` yields fragments of the form ``(style, content)``
    # or ``(style, content, mouse_handler)``. We only care about the first two
    # elements when rendering into the static chat buffer.
    for fragment in fragments:
        style = fragment[0]
        content = fragment[1]
        chat_lines.append((style, content))


class _ChatWriter(io.TextIOBase):
    """File-like adapter that appends writes to the chat area."""

    def __init__(self, chat_lines: list[tuple[str, str]]) -> None:
        super().__init__()
        self._chat_lines = chat_lines

    def writable(self) -> bool:  # pragma: no cover - trivial
        return True

    def write(self, text: str, /) -> int:  # type: ignore[override]
        _append_chat_text(self._chat_lines, text)
        return len(text)

    def flush(self) -> None:  # pragma: no cover - no-op
        return None


@contextlib.contextmanager
def _capture_to_chat(chat_lines: list[tuple[str, str]]) -> Iterator[None]:
    """Redirect ``sys.stdout`` so that command output lands in the chat area."""
    writer = _ChatWriter(chat_lines)
    old_stdout = sys.stdout
    sys.stdout = writer
    try:
        yield
    finally:
        sys.stdout = old_stdout


def _run_shell_command_captured(cmd: str, chat_lines: list[tuple[str, str]]) -> None:
    """Run a ``!`` shell command and append its output to the chat area.

    Unlike :func:`_run_shell_command` which streams directly to the terminal,
    this variant captures stdout/stderr so they can be rendered inside the
    full-screen chat area.

    **Security note**: user-initiated ``!`` escape, same semantics as
    :func:`_run_shell_command`.
    """
    _append_chat_text(chat_lines, styled(f"$ {cmd}", STYLE_DIM) + "\n")
    try:
        result = subprocess.run(  # nosec B602
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        _append_chat_text(chat_lines, styled("error:", STYLE_ERROR) + f" {exc}\n")
        return
    if result.stdout:
        _append_chat_text(chat_lines, result.stdout)
        if not result.stdout.endswith("\n"):
            _append_chat_text(chat_lines, "\n")
    if result.stderr:
        _append_chat_text(chat_lines, result.stderr)
        if not result.stderr.endswith("\n"):
            _append_chat_text(chat_lines, "\n")


def _start_background_reply_fullscreen(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    runtime: ShellRuntime,
    toolbar_ref: list[str],
    chat_lines: list[tuple[str, str]],
    app: Application[object],
) -> None:
    """Stream an assistant reply into ``chat_lines`` from a background thread."""
    history.add(user_input)

    config_error = _preflight_config_check(session)
    if config_error:
        _append_chat_text(chat_lines, styled("error:", STYLE_ERROR) + f" {config_error}\n")
        _invalidate_prompt(app)
        return

    runtime.busy = True
    runtime.steering_count = 0
    runtime.abort_event.clear()
    _refresh_bottom_toolbar(session, toolbar_ref, runtime)
    _invalidate_prompt(app)

    reply_prefix = f"\n{styled('Assistant:', STYLE_ASSISTANT)} "

    def _writer(chunk: str) -> None:
        _append_chat_text(chat_lines, chunk)
        _invalidate_prompt(app)

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
            with _capture_to_chat(chat_lines):
                _report_engine_error(exc, session)
        finally:
            runtime.worker = None
            runtime.abort_event.clear()
            runtime.busy = False
            _refresh_bottom_toolbar(session, toolbar_ref, runtime)
            _invalidate_prompt(app)

    runtime.worker = threading.Thread(target=_worker, name="hephaistos-shell-reply", daemon=True)
    runtime.worker.start()


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


def _print_settings_hint() -> None:
    if not should_show_telemetry_notice():
        return
    print_info(
        "Optional anonymous analytics and crash reports are available for this install. "
        "Open /settings to review and enable them."
    )
    mark_telemetry_notice_seen()


def _print_vocab_hint(session: ChatSession) -> None:
    """Show a hint if the armory contains vocabulary files."""
    if session.armory_path is None:
        return
    try:
        deck = scan_armory(session.armory_path)
        if deck.cards:
            print_info(
                f"Vocabulary deck detected ({deck.size} words). "
                f"Use {styled('/vocab', STYLE_PROMPT)} to start a drill."
            )
    except Exception:
        _log.debug("vocabulary hint scan failed", exc_info=True)


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


def _build_fullscreen_bindings(
    keybindings: dict[str, str | list[str]],
    runtime: ShellRuntime,
) -> KeyBindings:
    """Composer bindings plus Ctrl+C/Ctrl+D wired to the full-screen runtime."""
    bindings = _build_keybindings(keybindings)

    @bindings.add("c-c")
    def _(event: KeyPressEvent) -> None:
        if runtime.busy:
            runtime.abort_event.set()
        event.app.invalidate()

    @bindings.add("c-d")
    def _(event: KeyPressEvent) -> None:
        if runtime.busy:
            runtime.abort_event.set()
            if runtime.worker is not None:
                runtime.worker.join(timeout=5.0)
        event.app.exit()

    return bindings


def _build_fullscreen_status(toolbar_ref: list[str]) -> FormattedText:
    """Reuse the compact composer toolbar text as the full-screen status bar."""
    return _get_bottom_toolbar(toolbar_ref)


def _fullscreen_header(session: ChatSession) -> FormattedText:
    return FormattedText(
        format_shell_header(
            version=__version__,
            armory_path=str(session.armory_path or "none"),
            source_file_count=session.source_file_count or 0,
            model=session.config.model,
            has_api_key=bool(session.config.resolved_api_key),
        )
    )


def run_chat_shell(
    session: ChatSession | None = None,
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> None:
    """Run the interactive chat shell as a persistent full-screen application."""
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

    kb = keybindings or DEFAULT_SHELL_KEYBINDINGS

    runtime = ShellRuntime()
    toolbar_ref = [_build_bottom_toolbar_status(session, runtime)]
    history_path = _get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    chat_lines: list[tuple[str, str]] = []
    history = InputHistory()

    # Session cell is indirected via a list so that closures can rebind it
    # when commands swap in a new session (e.g. /armory open).
    session_ref: list[ChatSession] = [session]

    def _seed_chat_lines() -> None:
        """Populate chat_lines with intro hints the classic shell used to print."""
        with _capture_to_chat(chat_lines):
            _print_vocab_hint(session_ref[0])
            _print_settings_hint()

    app_ref: list[Application[object] | None] = [None]

    def _get_app() -> Application[object] | None:
        return app_ref[0]

    def _accept(buffer: Buffer) -> bool:
        raw = buffer.text
        buffer.reset(append_to_history=False)
        text = raw.strip()
        current = session_ref[0]

        if not text:
            return False

        app = _get_app()
        lower = text.lower()

        if runtime.busy and lower in {"/exit", "/quit", "/q"}:
            runtime.abort_event.set()
            if runtime.worker is not None:
                runtime.worker.join(timeout=5.0)
            if app is not None:
                app.exit()
            return False

        _append_chat_text(
            chat_lines,
            styled("> ", STYLE_PROMPT) + raw.rstrip() + "\n",
        )
        history.add(raw)

        if runtime.busy:
            if text.startswith("/"):
                with _capture_to_chat(chat_lines):
                    current, _ = _handle_input(current, text, history)
            else:
                with _capture_to_chat(chat_lines):
                    current, _ = _handle_input(current, text, history, streaming=True)
                runtime.steering_count += 1
            session_ref[0] = current
            _refresh_bottom_toolbar(current, toolbar_ref, runtime)
            _invalidate_prompt(app)
            return False

        try:
            if text.startswith("!"):
                cmd = text[1:].strip()
                if cmd:
                    _run_shell_command_captured(cmd, chat_lines)
            elif text.startswith("/"):
                with _capture_to_chat(chat_lines):
                    current, should_continue = _handle_input(current, text, history)
                session_ref[0] = current
                if not should_continue:
                    if app is not None:
                        app.exit()
                    return False
            elif app is not None:
                _start_background_reply_fullscreen(
                    current, text, history, runtime, toolbar_ref, chat_lines, app
                )
        except KeyboardInterrupt:
            _append_chat_text(chat_lines, styled("info:", STYLE_DIM) + " Cancelled.\n")

        _refresh_bottom_toolbar(session_ref[0], toolbar_ref, runtime)
        _invalidate_prompt(app)
        return False

    input_buffer = Buffer(
        name="chat-composer",
        multiline=True,
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        auto_suggest=AutoSuggestFromHistory(),
        history=FileHistory(str(history_path)),
        accept_handler=_accept,
    )

    header_control = FormattedTextControl(
        lambda: _fullscreen_header(session_ref[0]),
        focusable=False,
    )
    chat_control = FormattedTextControl(
        lambda: FormattedText(chat_lines),
        focusable=False,
    )
    status_control = FormattedTextControl(
        lambda: _build_fullscreen_status(toolbar_ref),
        focusable=False,
    )
    input_control = BufferControl(
        buffer=input_buffer,
        focusable=True,
    )

    header_window = Window(
        content=header_control,
        height=Dimension(min=2, max=6),
        style="class:header",
        wrap_lines=True,
    )
    separator_top = Window(height=1, char="─", style="class:separator")
    chat_window = Window(
        content=chat_control,
        wrap_lines=True,
        style="class:chat-area",
        right_margins=[ScrollbarMargin(display_arrows=False)],
    )
    separator_bottom = Window(height=1, char="─", style="class:separator")
    prompt_marker = _get_prompt_message(runtime)
    input_window = Window(
        content=input_control,
        height=Dimension(min=1, max=8),
        style="class:composer",
        wrap_lines=True,
        get_line_prefix=lambda _ln, _wc: prompt_marker(),
    )
    status_window = Window(
        content=status_control,
        height=1,
        style="class:bottom-toolbar",
    )

    layout = Layout(
        HSplit(
            [
                header_window,
                separator_top,
                chat_window,
                separator_bottom,
                input_window,
                status_window,
            ]
        ),
        focused_element=input_window,
    )

    bindings = _build_fullscreen_bindings(kb, runtime)

    app: Application[object] = Application(
        layout=layout,
        key_bindings=bindings,
        style=_PT_STYLE,
        full_screen=True,
        mouse_support=False,
    )
    app_ref[0] = app

    _append_chat_text(
        chat_lines,
        styled("Hephaistos", STYLE_PROMPT)
        + " "
        + styled(f"v{__version__}", STYLE_DIM)
        + " — type /help for commands.\n",
    )
    _seed_chat_lines()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        if runtime.busy:
            runtime.abort_event.set()
            if runtime.worker is not None:
                runtime.worker.join(timeout=5.0)

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
