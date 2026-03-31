"""Chat-first interactive shell."""

from __future__ import annotations

from pathlib import Path
import sys

from hephaistos.app.menu import MenuOption, select_option
from hephaistos.armory.storage import (
    ArmoryError,
    discover_startup_armory,
    initialize,
    normalize_path,
)
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, EngineError
from hephaistos.chat.session import (
    ChatSession,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    send_user_message,
    session_has_messages,
    validate_armory_path,
)


ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its study context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Detach armory", "Keep chatting without workspace context."),
    MenuOption("Cancel", "Return to the chat prompt."),
]


def _default_armory_input(session: ChatSession) -> str:
    if session.armory_path is not None:
        return str(session.armory_path)
    return str((Path.cwd() / "armory").resolve())


def _prompt_path(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def _print_shell_intro(session: ChatSession) -> None:
    print("Hephaistos")
    if session.armory_path is None:
        print("Armory: none. Use /armory to open or create one.")
    else:
        print(f"Armory: {session.armory_path}")
        if session.source_file_count:
            print(
                f"Context: loaded {session.source_file_count} file(s) from source/ and library/."
            )
    print(f"Session: {session.session_id}")
    print(f"Model:   {session.config.model}")
    print(f"API:     {session.config.base_url}")
    print("Commands: /help, /armory, /save, /clear, /status, /exit\n")


def _chat_prompt(session: ChatSession) -> str:
    if session.armory_path is None:
        return "You> "
    return f"{session.armory_path.name}> "


def _save_before_switch(session: ChatSession) -> None:
    if not session.dirty:
        return

    if session.armory_path is None:
        print("Starting a fresh chat. Previous messages were not saved.")
        return

    try:
        path = save_session(session)
    except chat_storage.ChatStorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return

    print(f"Saved chat to {path}")


def _start_fresh_session(session: ChatSession, armory_path: Path | None) -> ChatSession:
    _save_before_switch(session)
    new_session = create_session(session.config, armory_path)

    if armory_path is None:
        print("Detached armory. Chat is now running without workspace context.")
    else:
        print(f"Using armory {armory_path}")
        if new_session.source_file_count:
            print(
                f"Loaded {new_session.source_file_count} file(s) from source/ and library/."
            )
    return new_session


def _open_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)

    try:
        armory_path = validate_armory_path(raw_path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return session

    return _start_fresh_session(session, armory_path)


def _create_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("New armory path", default_path)
    armory_path = normalize_path(raw_path)

    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return session

    print(f"Initialized armory at {armory_path}")
    return _start_fresh_session(session, armory_path)


def _prompt_armory_for_sessions(session: ChatSession) -> Path | None:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)

    try:
        return validate_armory_path(raw_path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return None


def _resume_saved_chat(session: ChatSession) -> ChatSession:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return session

    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print("No saved chats found.")
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
        print(f"error: {exc}", file=sys.stderr)
        return session

    print(f"Resumed session {resumed.session_id}")
    if resumed.title:
        print(f"Title: {resumed.title}")
    return resumed


def _list_saved_chats(session: ChatSession) -> None:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return

    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print("No saved chats found.")
        return

    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")


def _show_status(session: ChatSession) -> None:
    armory = str(session.armory_path) if session.armory_path is not None else "none"
    print(f"Armory: {armory}")
    print(f"Session: {session.session_id}")
    if session.title:
        print(f"Title: {session.title}")


def _print_help() -> None:
    print("/armory  Open the armory menu.")
    print("/save    Save the current chat to the active armory.")
    print("/clear   Start a fresh chat in the current armory.")
    print("/status  Show the active armory and session.")
    print("/exit    Leave the shell.")


def _handle_armory_command(session: ChatSession) -> ChatSession:
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    if selected is None or selected == 5:
        return session
    if selected == 0:
        return _open_armory(session)
    if selected == 1:
        return _create_armory(session)
    if selected == 2:
        return _resume_saved_chat(session)
    if selected == 3:
        _list_saved_chats(session)
        return session
    if selected == 4:
        return _start_fresh_session(session, None)
    return session


def _handle_command(session: ChatSession, user_input: str) -> tuple[ChatSession, bool]:
    command = user_input.strip().lower()

    if command in {"/exit", "/quit"}:
        return session, False
    if command == "/help":
        _print_help()
        return session, True
    if command == "/armory":
        return _handle_armory_command(session), True
    if command == "/save":
        try:
            path = save_session(session)
        except chat_storage.ChatStorageError as exc:
            print(f"error: {exc}", file=sys.stderr)
        else:
            print(f"Saved chat to {path}")
        return session, True
    if command == "/clear":
        return _start_fresh_session(session, session.armory_path), True
    if command == "/status":
        _show_status(session)
        return session, True

    print(f"Unknown command: {user_input}")
    print("Type /help for the available commands.")
    return session, True


def run_chat_shell(session: ChatSession | None = None) -> None:
    """Run the interactive chat shell."""
    if session is None:
        config = ChatConfig.from_env()
        session = create_session(config, discover_startup_armory())

    _print_shell_intro(session)

    while True:
        try:
            user_input = input(_chat_prompt(session)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            session, should_continue = _handle_command(session, user_input)
            if should_continue:
                print()
                continue
            break

        print("Assistant: ", end="", flush=True)
        try:
            send_user_message(session, user_input, stream=True)
        except EngineError as exc:
            print(f"\nerror: {exc}", file=sys.stderr)
        print()

    if session.armory_path is not None and session.dirty and session_has_messages(session):
        try:
            path = save_session(session)
        except chat_storage.ChatStorageError as exc:
            print(f"error: {exc}", file=sys.stderr)
        else:
            print(f"Saved chat to {path}")
