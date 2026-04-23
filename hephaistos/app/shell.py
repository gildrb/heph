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

import shutil
import subprocess  # nosec B404
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from prompt_toolkit.application import Application, run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.styles import DynamicStyle
from prompt_toolkit.styles import Style as PtStyle

from hephaistos import __version__
from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands import get_registry
from hephaistos.app.display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
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


class _Invalidatable(Protocol):
    def invalidate(self) -> None: ...


def _run_shell_command_captured(
    cmd: str,
    chat_lines: list[tuple[str, str]],
    app: _Invalidatable,
) -> None:
    """Execute a ``!`` shell command, routing output into the chat buffer.

    **Security note**: This is the user-initiated ``!`` shell escape.
    Commands run with the full privileges of the current user.  The
    ``!`` prefix makes this intentional and user-controlled.
    """
    chat_lines.append(("class:chat-area.system", f"$ {cmd}\n"))
    try:
        result = subprocess.run(  # nosec B602
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            chat_lines.append(("class:chat-area", result.stdout))
            if not result.stdout.endswith("\n"):
                chat_lines.append(("", "\n"))
        if result.stderr:
            chat_lines.append(("class:chat-area.error", result.stderr))
            if not result.stderr.endswith("\n"):
                chat_lines.append(("", "\n"))
    except OSError as exc:
        chat_lines.append(("class:chat-area.error", f"error: {exc}\n"))
    app.invalidate()


class _ChatWriter:
    """File-like object that routes ``write`` calls into ``chat_lines``."""

    encoding: str = "utf-8"

    def __init__(
        self,
        chat_lines: list[tuple[str, str]],
        app: _Invalidatable,
        *,
        style_class: str = "class:chat-area.system",
    ) -> None:
        self._chat_lines = chat_lines
        self._app = app
        self._style_class = style_class

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._chat_lines.append((self._style_class, text))
        self._app.invalidate()
        return len(text)

    def flush(self) -> None:  # pragma: no cover - nothing to flush
        return

    def isatty(self) -> bool:
        return False


@contextmanager
def _capture_to_chat(
    chat_lines: list[tuple[str, str]],
    app: _Invalidatable,
) -> Iterator[None]:
    """Redirect ``sys.stdout`` writes to the chat history buffer."""
    writer = _ChatWriter(chat_lines, app)
    original = sys.stdout
    sys.stdout = writer  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.stdout = original


def _report_engine_error_silent(
    exc: EngineError | StreamRecoveryError,
    session: ChatSession,
) -> None:
    """Capture diagnostics without printing (the caller renders its own notice)."""
    if isinstance(exc, StreamRecoveryError):
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


def _start_background_reply_fullscreen(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    runtime: ShellRuntime,
    chat_lines: list[tuple[str, str]],
    app: _Invalidatable,
) -> None:
    """Dispatch a user message turn and stream events into ``chat_lines``."""
    history.add(user_input)

    config_error = _preflight_config_check(session)
    if config_error:
        chat_lines.append(("class:chat-area.error", f"error: {config_error}\n"))
        app.invalidate()
        return

    runtime.busy = True
    runtime.steering_count = 0
    runtime.abort_event.clear()
    app.invalidate()

    chat_lines.append(("class:chat-area.assistant-label", "\nAssistant: "))

    def _chat_writer(text: str) -> None:
        if text:
            chat_lines.append(("class:chat-area.assistant", text))
            app.invalidate()

    def _worker() -> None:
        try:
            send_user_message(
                session,
                user_input,
                abort=runtime.abort_event,
                writer=_chat_writer,
            )
        except (StreamRecoveryError, EngineError) as exc:
            chat_lines.append(("class:chat-area.error", f"\nerror: {exc}\n"))
            _report_engine_error_silent(exc, session)
        finally:
            runtime.worker = None
            runtime.abort_event.clear()
            runtime.busy = False
            app.invalidate()

    runtime.worker = threading.Thread(
        target=_worker,
        name="hephaistos-shell-reply",
        daemon=True,
    )
    runtime.worker.start()


async def _await_run_in_terminal(func: Callable[[], None]) -> None:
    """Wrap ``run_in_terminal`` as a coroutine suitable for background tasks."""
    await run_in_terminal(func, in_executor=True)


def _build_fullscreen_keybindings(
    kb_config: dict[str, str | list[str]],
    runtime: ShellRuntime,
    chat_lines: list[tuple[str, str]],
) -> KeyBindings:
    """Extend the shared composer bindings with app-level interrupt/exit keys."""
    kb = _build_keybindings(kb_config)

    @kb.add("c-c")
    def _(event: KeyPressEvent) -> None:
        if runtime.busy:
            runtime.abort_event.set()
            chat_lines.append(("class:chat-area.system", "\nInterrupt requested.\n"))
            event.app.invalidate()

    @kb.add("c-d")
    def _(event: KeyPressEvent) -> None:
        if runtime.busy:
            runtime.abort_event.set()
            if runtime.worker is not None:
                runtime.worker.join(timeout=5.0)
        event.app.exit()

    return kb


def run_chat_shell(
    session: ChatSession | None = None,
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> None:
    """Run the interactive chat shell with rich terminal UX."""
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

    history = InputHistory()
    chat_lines: list[tuple[str, str]] = []
    session_ref: list[ChatSession] = [session]

    if session.armory_path is not None:
        try:
            deck = scan_armory(session.armory_path)
            if deck.cards:
                chat_lines.append(
                    (
                        "class:chat-area.system",
                        (
                            f"info: Vocabulary deck detected ({deck.size} words). "
                            "Use /vocab to start a drill.\n"
                        ),
                    )
                )
        except OSError:
            _log.debug("vocabulary hint scan failed", exc_info=True)

    if should_show_telemetry_notice():
        chat_lines.append(
            (
                "class:chat-area.system",
                (
                    "info: Optional anonymous analytics and crash reports are available. "
                    "Open /settings to review and enable them.\n"
                ),
            )
        )
        mark_telemetry_notice_seen()

    def get_header() -> FormattedText:
        active = session_ref[0]
        return FormattedText(
            format_shell_header(
                version=__version__,
                armory_path=str(active.armory_path or "none"),
                source_file_count=active.source_file_count or 0,
                model=active.config.model,
                has_api_key=bool(active.config.resolved_api_key),
            )
        )

    def get_chat() -> FormattedText:
        return FormattedText(chat_lines)

    def get_status() -> FormattedText:
        _refresh_bottom_toolbar(session_ref[0], toolbar_ref, runtime)
        return _get_bottom_toolbar(toolbar_ref)

    app_holder: list[Application[None] | None] = [None]

    def on_accept(buff: Buffer) -> bool:
        user_input = buff.text.strip()
        if not user_input:
            return False
        current_app = app_holder[0]
        if current_app is None:
            return False

        chat_lines.append(("class:chat-area.user", f"\n> {user_input}\n"))
        active = session_ref[0]
        stripped_lower = user_input.lower()

        if runtime.busy and stripped_lower in {"/exit", "/quit", "/q"}:
            runtime.abort_event.set()
            if runtime.worker is not None:
                runtime.worker.join(timeout=5.0)
            current_app.exit()
            return False

        if runtime.busy:
            if user_input.startswith("/"):
                with _capture_to_chat(chat_lines, current_app):
                    new_session, _ = _handle_input(active, user_input, history)
                    session_ref[0] = new_session
            else:
                new_session, _ = _handle_input(active, user_input, history, streaming=True)
                session_ref[0] = new_session
                runtime.steering_count += 1
            current_app.invalidate()
            return False

        if user_input.startswith("!"):
            cmd = user_input[1:].strip()
            if cmd:
                history.add(user_input)
                _run_shell_command_captured(cmd, chat_lines, current_app)
            return False

        if user_input.startswith("/"):
            # Slash commands may invoke menu sub-applications (e.g. /model,
            # /armory, /settings). Nested ``Application.run()`` cannot be
            # called from the outer app's event loop, so we execute the
            # command via ``run_in_terminal(in_executor=True)`` which runs the
            # callback in a worker thread where a new event loop can be
            # created for any sub-app.
            def _exec_slash() -> None:
                with _capture_to_chat(chat_lines, current_app):
                    new_session, should_continue = _handle_input(active, user_input, history)
                    session_ref[0] = new_session
                if not should_continue:
                    current_app.exit()
                current_app.invalidate()

            current_app.create_background_task(_await_run_in_terminal(_exec_slash))
            return False

        _start_background_reply_fullscreen(
            session_ref[0], user_input, history, runtime, chat_lines, current_app
        )
        current_app.invalidate()
        return False

    input_buffer = Buffer(
        name="input",
        multiline=True,
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        history=FileHistory(str(history_path)),
        accept_handler=on_accept,
    )

    bindings = _build_fullscreen_keybindings(kb, runtime, chat_lines)

    layout = Layout(
        HSplit(
            [
                Window(
                    FormattedTextControl(get_header),
                    dont_extend_height=True,
                    height=Dimension(min=3, preferred=4),
                    style="class:header",
                ),
                Window(
                    char="─",
                    height=1,
                    style="class:separator",
                    dont_extend_height=True,
                ),
                Window(
                    FormattedTextControl(get_chat, focusable=False),
                    wrap_lines=True,
                    right_margins=[ScrollbarMargin(display_arrows=True)],
                    style="class:chat-area",
                ),
                Window(
                    char="─",
                    height=1,
                    style="class:separator",
                    dont_extend_height=True,
                ),
                Window(
                    BufferControl(buffer=input_buffer),
                    height=Dimension(min=1, max=5, preferred=3),
                    dont_extend_height=True,
                    style="class:composer",
                ),
                Window(
                    FormattedTextControl(get_status),
                    height=1,
                    dont_extend_height=True,
                    style="class:bottom-toolbar",
                ),
            ]
        ),
        focused_element=input_buffer,
    )

    app: Application[None] = Application(
        layout=layout,
        full_screen=True,
        key_bindings=bindings,
        style=_PT_STYLE,
        mouse_support=False,
    )
    app_holder[0] = app

    try:
        app.run()
    finally:
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
