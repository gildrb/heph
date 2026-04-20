"""Armory and session workspace actions shared by commands and shell."""

from __future__ import annotations

from pathlib import Path

from hephaistos.app.display import (
    direct_input,
    print_error,
    print_info,
    print_success,
)
from hephaistos.app.menu import MenuOption, browse_directory, select_option
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
    validate_armory_path,
)

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
        return new_session
    print_success(f"Using armory {armory_path}")
    if new_session.source_file_count:
        print_info(f"Loaded {new_session.source_file_count} file(s).")
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
    try:
        return _start_fresh_session(session, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        print_info("Add source files and use /armory to attach it.")
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


def _recent_sessions(sessions: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return saved sessions with the most recently updated first."""
    return sorted(sessions, key=lambda entry: entry.get("updated_at", ""), reverse=True)


def _match_saved_session(
    sessions: list[dict[str, str]],
    selector: str,
) -> dict[str, str] | None:
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
    if selector.strip():
        entry = _match_saved_session(sessions, selector)
        if entry is None:
            return session
    else:
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


def _handle_armory_command(session: ChatSession) -> ChatSession:  # pyright: ignore[reportUnusedFunction]
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
