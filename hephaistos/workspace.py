"""Armory and session workspace actions shared by commands and TUI."""
# pylint: disable=duplicate-code

from __future__ import annotations

import subprocess  # nosec B404
import threading
from collections.abc import Sequence
from pathlib import Path

from hephaistos.analytics import capture as capture_analytics
from hephaistos.armory.storage import ArmoryError, initialize, normalize_path
from hephaistos.chat import storage as chat_storage
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
from hephaistos.commands._base import get_registry_lazy
from hephaistos.fuzzy import ranked_matches
from hephaistos.input_history import InputHistory
from hephaistos.observability import capture_exception
from hephaistos.runtime import (
    ChatConfig,
    EngineError,
    StreamRecoveryError,
    is_keyless_endpoint,
    is_network_error,
    missing_api_key_message,
    offline_message,
)
from hephaistos.search_index import add_known_armory
from hephaistos.terminal import MenuOption, browse_directory, select_option
from hephaistos.terminal_display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    direct_input,
    print_error,
    print_info,
    print_success,
    styled,
)

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"

ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its study context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Detach armory", "Switch to plain chat without workspace tools."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Cancel", "Return to the chat prompt."),
]


def _default_armory_input(session: ChatSession) -> str:
    return str(session.armory_path or Path.cwd())


def _prompt_path(label: str, default: str) -> str | None:
    """Prompt the user for a path.  Returns *None* on cancel (empty or 'q')."""
    try:
        raw = direct_input(f"{label} [{default}] (q to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
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
        capture_analytics("armory_detached", {"model": new_session.config.model})
        return new_session
    add_known_armory(armory_path)
    print_success(f"Using armory {armory_path}")
    if new_session.source_file_count:
        print_info(f"Loaded {new_session.source_file_count} file(s).")
    capture_analytics(
        "armory_attached",
        {
            "source_file_count": new_session.source_file_count,
            "model": new_session.config.model,
        },
    )
    return new_session


def _detach_armory(session: ChatSession) -> ChatSession:
    return _start_fresh_session(session, None)


def _open_armory(session: ChatSession) -> ChatSession:
    default_path = Path(session.armory_path or Path.cwd())
    chosen = browse_directory("Open Armory", start=default_path)
    if chosen is None:
        print_info("Cancelled.")
        return session
    try:
        armory_path = validate_armory_path(str(chosen))
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    return _start_fresh_session(session, armory_path)


def _create_armory(session: ChatSession) -> ChatSession:
    default_path = Path(session.armory_path or Path.cwd())
    chosen = browse_directory("Create Armory", start=default_path)
    if chosen is None:
        print_info("Cancelled.")
        return session
    armory_path = normalize_path(str(chosen))
    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    print_success(f"Initialized armory at {armory_path}")
    capture_analytics("armory_created", {"mode": "shell"})
    try:
        return _start_fresh_session(session, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        print_info("Add files to materials/ and use /armory to attach it.")
        return session


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


def _session_armory(session: ChatSession) -> Path | None:
    """Return the active armory, or prompt for one in plain chat mode."""
    if session.armory_path is not None:
        return session.armory_path
    return _prompt_armory_for_sessions(session)


def _recent_sessions(
    sessions: Sequence[chat_storage.SessionRecord],
) -> list[chat_storage.SessionRecord]:
    """Return saved sessions with the most recently updated first."""
    return sorted(sessions, key=lambda entry: entry.get("updated_at", ""), reverse=True)


def _match_saved_session(
    sessions: Sequence[chat_storage.SessionRecord],
    selector: str,
) -> chat_storage.SessionRecord | None:
    """Return a saved session by exact ID or unique ID prefix."""
    session_id = selector.strip()
    if not session_id:
        return None

    exact = [entry for entry in sessions if entry["session_id"] == session_id]
    if exact:
        return exact[0]

    matches = [entry for entry in sessions if entry["session_id"].startswith(session_id)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        fuzzy = ranked_matches(
            session_id,
            list(sessions),
            key=lambda entry: f"{entry['session_id']} {entry['title']}",
            limit=3,
            min_score=70.0,
        )
        if len(fuzzy) == 1 and fuzzy[0].score >= 90.0:
            return fuzzy[0].value
        if fuzzy:
            print_error(f"No exact saved chat matches '{session_id}'. Close matches:")
            for match in fuzzy:
                entry = match.value
                title = entry["title"] or "(untitled)"
                print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
            return None
        print_error(f"No saved chat matches '{session_id}'.")
        return None

    print_error(f"Multiple saved chats match '{session_id}':")
    for entry in matches:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
    return None


def _resume_saved_chat(session: ChatSession, selector: str = "") -> ChatSession:
    armory_path = _session_armory(session)
    if armory_path is None:
        return session
    sessions = _recent_sessions(list_armory_sessions(armory_path))
    if not sessions:
        print_info("No saved chats found.")
        return session
    normalized_selector = selector.strip().lower()
    if normalized_selector in ("", "last", "latest", "recent"):
        entry = sessions[0]
    elif normalized_selector in ("browse", "menu"):
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
    else:
        entry = _match_saved_session(sessions, selector)
        if entry is None:
            return session
    _save_before_switch(session)
    try:
        resumed = resume_session(session.config, armory_path, entry["session_id"])
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))
        return session
    print_success(f"Resumed session {resumed.session_id}")
    if resumed.title:
        print_info(f"Title: {resumed.title}")
    capture_analytics("session_resumed", {"message_count": len(resumed.conversation.messages)})
    return resumed


def _list_saved_chats(session: ChatSession) -> None:
    armory_path = _session_armory(session)
    if armory_path is None:
        return
    sessions = _recent_sessions(list_armory_sessions(armory_path))
    if not sessions:
        print_info("No saved chats found.")
        return
    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")


def _handle_armory_command(session: ChatSession) -> ChatSession:  # ty: ignore
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    handlers = [
        _open_armory,
        _create_armory,
        _detach_armory,
        _resume_saved_chat,
        _list_saved_chats,
    ]
    if selected is None or selected < 0 or selected >= len(handlers):
        return session
    result = handlers[selected](session)
    if result is None:
        return session
    return result


def _discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass
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
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not is_keyless_endpoint(session.config.base_url) and not session.config.resolved_api_key:
        return missing_api_key_message(session.config)
    return None


def _report_engine_error(
    exc: EngineError | StreamRecoveryError,
    session: ChatSession,
) -> None:
    """Display an engine error and capture local diagnostic context."""
    provider = session.config.provider_slug or "the provider"

    if isinstance(exc, StreamRecoveryError):
        if is_network_error(exc):
            print(offline_message(provider))
        else:
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
                "provider": provider,
                "model": session.config.model,
                "partial_content_length": len(exc.partial_content),
            },
        )
        capture_analytics(
            "request_failed",
            {
                "provider": provider,
                "model": session.config.model,
                "kind": "stream_recovery",
                "partial_content_length": len(exc.partial_content),
            },
        )
    else:
        if is_network_error(exc):
            print(offline_message(provider))
        else:
            print_error(str(exc))
        capture_exception(
            exc,
            context={
                "provider": provider,
                "model": session.config.model,
            },
        )
        capture_analytics(
            "request_failed",
            {
                "provider": provider,
                "model": session.config.model,
                "kind": "engine_error",
            },
        )


def _handle_input(  # ty: ignore
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
            registry = get_registry_lazy()
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

        registry = get_registry_lazy()
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
        if result.output and not result.output.startswith("__RESEND__:"):
            print(result.output)
        if result.output and result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:") :]
            history.add(new_input)
            config_error = _preflight_config_check(session)
            if config_error:
                print_error(config_error)
                return session, True
            abort = threading.Event()
            reply_prefix = f"\r{styled('Hephaistos:', STYLE_ASSISTANT)} "
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
    reply_prefix = f"\r{styled('Hephaistos:', STYLE_ASSISTANT)} "
    try:
        send_user_message(session, user_input, abort=abort, reply_prefix=reply_prefix)
    except (StreamRecoveryError, EngineError) as exc:
        _report_engine_error(exc, session)
    return session, True


def _get_history_path(session: ChatSession) -> Path:  # ty: ignore
    if session.armory_path is None:
        return _HISTORY_DIR / "plain-history"
    return session.armory_path / ".hephaistos" / "history"


def _save_on_exit(session: ChatSession) -> None:  # ty: ignore
    if session.dirty and session_has_messages(session) and session.armory_path is not None:
        try:
            path = save_session(session)
            print_success(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
    session.trace.close()


def _create_startup_session(config: ChatConfig) -> ChatSession:  # ty: ignore
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


resume_saved_chat = _resume_saved_chat
list_saved_chats = _list_saved_chats
handle_armory_command = _handle_armory_command
open_armory_command = _open_armory
create_armory_command = _create_armory
start_fresh_session = _start_fresh_session
handle_input = _handle_input
get_history_path = _get_history_path
save_on_exit = _save_on_exit
create_startup_session = _create_startup_session
