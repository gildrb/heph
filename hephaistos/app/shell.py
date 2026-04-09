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

import signal
import subprocess
import sys
import threading
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style as PtStyle

from hephaistos import __version__
from hephaistos.app.commands import get_registry
from hephaistos.app.display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    print_error,
    print_info,
    print_shell_intro,
    print_success,
    styled,
)
from hephaistos.app.input_history import InputHistory
from hephaistos.app.keybindings import DEFAULT_SHELL_KEYBINDINGS
from hephaistos.app.menu import MenuOption, select_option
from hephaistos.app.palette import (
    FORGE_ASH,
    FORGE_EMBER,
    FORGE_PANEL,
    FORGE_SMOKE,
)
from hephaistos.armory.storage import ArmoryError, initialize, normalize_path
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import EngineError, StreamRecoveryError
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    send_user_message,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.chat.usage import ContextBudget
from hephaistos.harness.permissions import classify_bash_command, tier_allows
from hephaistos.parameters.cli import load_config

ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its study context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Detach armory", "Switch to plain chat without workspace tools."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Cancel", "Return to the chat prompt."),
]

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"

_PT_STYLE = PtStyle.from_dict(
    {
        "armory": f"bold {FORGE_EMBER}",
        "prompt-mark": f"bold {FORGE_EMBER}",
        "bottom-toolbar": f"{FORGE_SMOKE}",
        "completion-menu.completion.current": f"bg:{FORGE_EMBER} fg:{FORGE_ASH} bold",
        "completion-menu.completion": f"bg:{FORGE_PANEL} fg:{FORGE_ASH}",
        "completion-menu.meta.completion.current": f"bg:{FORGE_EMBER} fg:{FORGE_ASH}",
        "completion-menu.meta.completion": f"bg:{FORGE_PANEL} fg:{FORGE_SMOKE}",
        "scrollbar.background": f"bg:{FORGE_PANEL}",
        "scrollbar.button": f"bg:{FORGE_EMBER}",
    }
)


class SlashCommandCompleter(Completer):
    """Tab-completion for slash commands."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        if not stripped.startswith("/") or " " in stripped:
            return

        prefix = stripped[1:].lower()
        registry = get_registry()

        for cmd in registry.suggestions():
            if cmd.name.lower().startswith(prefix):
                yield Completion(
                    text=cmd.name + " ",
                    start_position=-(len(stripped) - 1),
                    display_meta=cmd.description,
                )


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
    def _(event):
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
    def _(event):
        """Insert a newline (e.g. Alt+Enter)."""
        event.current_buffer.insert_text("\n")

    return kb


def _session_label(session: ChatSession) -> str:
    return session.armory_path.name if session.armory_path is not None else "chat"


def _get_prompt_message(session_ref: list[ChatSession]):
    """Return a callable that builds the prompt for each iteration."""

    def message():
        name = _session_label(session_ref[0])
        return FormattedText([("class:armory", name), ("class:prompt-mark", " > ")])

    return message


def _display_path(path: Path) -> str:
    """Render a path relative to the user's home directory when possible."""
    resolved = path.expanduser().resolve()
    try:
        rel = resolved.relative_to(Path.home())
        return "~" if str(rel) == "." else f"~/{rel}"
    except ValueError:
        return str(resolved)


def _context_left(session: ChatSession) -> int:
    """Return the estimated prompt-budget percentage left for the session."""
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    prompt_budget = max(1, budget.prompt_budget)
    remaining = budget.tokens_remaining(session.conversation.to_api_messages())  # type: ignore[arg-type]
    return max(0, min(100, round((remaining / prompt_budget) * 100)))


def _build_bottom_toolbar_status(session: ChatSession) -> str:
    """Build the compact status line shown directly below the input."""
    location = session.armory_path or Path.cwd()
    return (
        f"  {session.config.model} · {session.autonomy}"
        f" · {_context_left(session)}% left · {_display_path(location)}"
    )


def _refresh_bottom_toolbar(session: ChatSession, toolbar_ref: list[str]) -> None:
    """Refresh the cached prompt_toolkit toolbar text for the active session."""
    toolbar_ref[0] = _build_bottom_toolbar_status(session)


def _get_bottom_toolbar(toolbar_ref: list[str]):
    """Return the cached bottom-toolbar text for prompt_toolkit redraws."""
    return FormattedText([("class:bottom-toolbar", toolbar_ref[0])])


def _discover_startup_armory() -> Path | None:
    candidates = [Path.cwd(), Path.cwd() / "armory"]
    for candidate in candidates:
        try:
            return validate_armory_path(str(candidate))
        except ArmoryError:
            continue
    return None


def _default_armory_input(session: ChatSession) -> str:
    return str(session.armory_path or Path.cwd())


def _prompt_path(label: str, default: str) -> str | None:
    """Prompt the user for a path.  Returns *None* on cancel (empty or 'q')."""
    raw = input(f"{label} [{default}] (q to cancel): ").strip()
    if raw.lower() in ("q", "quit", "cancel", "back"):
        return None
    return raw or default


def _save_before_switch(session: ChatSession) -> None:
    if not session.dirty or session.armory_path is None:
        return
    try:
        path = save_session(session)
        print_success(f"Saved chat to {path}")
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))


def _start_fresh_session(
    session: ChatSession,
    armory_path: Path | None,
) -> ChatSession:
    if armory_path is None and session.armory_path is None:
        print_info("Already in plain chat mode.")
        return session
    _save_before_switch(session)
    try:
        if armory_path is None:
            new_session = create_plain_session(session.config)
        else:
            new_session = create_session(session.config, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return session
    if armory_path is None:
        print_success("Detached armory. Plain chat mode.")
        return new_session
    print_success(f"Using armory {armory_path}")
    if new_session.source_file_count:
        print_info(f"Loaded {new_session.source_file_count} file(s).")
    return new_session


def _detach_armory(session: ChatSession) -> ChatSession:
    return _start_fresh_session(session, None)


def _open_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return session
    try:
        armory_path = validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    return _start_fresh_session(session, armory_path)


def _create_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("New armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return session
    armory_path = normalize_path(raw_path)
    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    print_success(f"Initialized armory at {armory_path}")
    return _start_fresh_session(session, armory_path)


def _prompt_armory_for_sessions(session: ChatSession) -> Path | None:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return None
    try:
        return validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return None


def _resume_saved_chat(session: ChatSession) -> ChatSession:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return session
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return session
    options = [
        MenuOption(
            entry["title"] or entry["session_id"],
            f"{entry['session_id']}  {entry['updated_at']}",
        )
        for entry in sessions
    ]
    selected = select_option("Resume Saved Chat", options)
    if selected is None:
        return session
    entry = sessions[selected]
    _save_before_switch(session)
    try:
        resumed = resume_session(session.config, armory_path, entry["session_id"])
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))
        return session
    print_success(f"Resumed session {resumed.session_id}")
    if resumed.title:
        print_info(f"Title: {resumed.title}")
    return resumed


def _list_saved_chats(session: ChatSession) -> None:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return
    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")


def _handle_armory_command(session: ChatSession) -> ChatSession:
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    if selected is None or selected == 5:
        return session
    if selected == 0:
        return _open_armory(session)
    if selected == 1:
        return _create_armory(session)
    if selected == 2:
        return _detach_armory(session)
    if selected == 3:
        return _resume_saved_chat(session)
    if selected == 4:
        _list_saved_chats(session)
        return session
    return session


def _run_shell_command(cmd: str) -> None:
    """Execute a shell command and display output."""
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True, check=False)
    except Exception as exc:
        print_error(str(exc))


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
        from hephaistos.harness.dispatch import SteeringQueue

        if isinstance(session.steering, SteeringQueue):
            session.steering.enqueue(user_input)
        return session, True
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            required_tier = classify_bash_command(cmd)
            if not tier_allows(required_tier, session.autonomy):
                print_error(
                    f"Permission denied: command requires '{required_tier}' autonomy "
                    f"(current: '{session.autonomy}')"
                )
            else:
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
            session = result.new_session  # type: ignore[assignment]
        if result.output and result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:") :]
            history.add(new_input)
            print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
            abort = threading.Event()
            try:
                send_user_message(session, new_input, abort=abort)
            except StreamRecoveryError as rec:
                msg = (
                    f"{styled('warning:', STYLE_ERROR)} "
                    f"Stream interrupted — connection lost after partial reply."
                )
                if rec.partial_content:
                    msg += f" ({len(rec.partial_content)} chars received)"
                print(msg)
            except EngineError as exc:
                print_error(str(exc))
            else:
                print()

        return session, True
    history.add(user_input)
    print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
    abort = threading.Event()
    try:
        send_user_message(session, user_input, abort=abort)
    except StreamRecoveryError as rec:
        msg = (
            f"{styled('warning:', STYLE_ERROR)} "
            f"Stream interrupted — connection lost after partial reply."
        )
        if rec.partial_content:
            msg += f" ({len(rec.partial_content)} chars received)"
        print(msg)
    except EngineError as exc:
        print_error(str(exc))
    else:
        print()
    return session, True


def _print_shell_intro(session: ChatSession) -> None:
    print_shell_intro(
        version=__version__,
        armory_path=str(session.armory_path or "none"),
        source_file_count=session.source_file_count or 0,
        model=session.config.model,
        has_api_key=bool(session.config.resolved_api_key),
    )


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


def run_chat_shell(
    session: ChatSession | None = None,
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> None:
    """Run the interactive chat shell with rich terminal UX."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _run_fallback_shell(session)
        return

    if session is None:
        config = load_config()
        armory = _discover_startup_armory()
        session = (
            create_plain_session(config) if armory is None else create_session(config, armory)
        )

    _print_shell_intro(session)

    kb = keybindings or DEFAULT_SHELL_KEYBINDINGS

    session_ref = [session]
    toolbar_ref = [_build_bottom_toolbar_status(session)]
    history_path = _get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    pt_session = PromptSession(
        message=_get_prompt_message(session_ref),
        style=_PT_STYLE,
        history=FileHistory(str(history_path)),
        completer=SlashCommandCompleter(),
        key_bindings=_build_keybindings(kb),
        bottom_toolbar=lambda: _get_bottom_toolbar(toolbar_ref),
        multiline=True,
        complete_while_typing=True,
    )

    abort_event = threading.Event()
    original_sigint = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signum: int, frame: object) -> None:
        abort_event.set()

    history = InputHistory()

    while True:
        try:
            signal.signal(signal.SIGINT, original_sigint)
            user_input = pt_session.prompt()
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

        if not user_input or not user_input.strip():
            continue

        signal.signal(signal.SIGINT, _sigint_handler)
        abort_event.clear()

        session, should_continue = _handle_input(session, user_input, history)
        session_ref[0] = session
        _refresh_bottom_toolbar(session, toolbar_ref)

        signal.signal(signal.SIGINT, original_sigint)

        if not should_continue:
            break

    _save_on_exit(session)


def _run_fallback_shell(session: ChatSession | None = None) -> None:
    """Simple fallback shell when the terminal is not a TTY."""
    if session is None:
        config = load_config()
        armory = _discover_startup_armory()
        session = (
            create_plain_session(config) if armory is None else create_session(config, armory)
        )

    print("Hephaistos (basic mode)")
    history = InputHistory()

    while True:
        try:
            user_input = input(f"{_session_label(session)}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        session, should_continue = _handle_input(session, user_input, history)
        if not should_continue:
            break

    _save_on_exit(session)
