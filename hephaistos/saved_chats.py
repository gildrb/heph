"""Saved chat listing and resume actions for armory sessions."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from hephaistos.armory.storage import ArmoryError
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import (
    ChatSession,
    list_armory_sessions,
    resume_session,
    save_session,
    validate_armory_path,
)
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.fuzzy import ranked_matches
from hephaistos.terminal import MenuOption, select_option
from hephaistos.terminal_display import direct_input, print_error, print_info, print_success


def default_armory_input(session: ChatSession) -> str:
    return str(session.armory_path or Path.cwd())


def prompt_path(label: str, default: str) -> str | None:
    """Prompt the user for a path. Returns ``None`` on cancel."""
    try:
        raw = direct_input(f"{label} [{default}] (q to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
    if raw.lower() in ("q", "quit", "cancel", "back"):
        return None
    return raw or default


def save_before_switch(session: ChatSession) -> None:
    if not session.dirty or session.armory_path is None:
        return
    try:
        path = save_session(session)
        print_success(f"Saved chat to {path}")
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))


def prompt_armory_for_sessions(session: ChatSession) -> Path | None:
    default_path = default_armory_input(session)
    raw_path = prompt_path("Armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return None
    try:
        return validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return None


def session_armory(session: ChatSession) -> Path | None:
    """Return the active armory, or prompt for one in plain chat mode."""
    if session.armory_path is not None:
        return session.armory_path
    return prompt_armory_for_sessions(session)


def recent_sessions(
    sessions: Sequence[chat_storage.SessionRecord],
) -> list[chat_storage.SessionRecord]:
    """Return saved sessions with the most recently updated first."""
    return sorted(sessions, key=lambda entry: entry.get("updated_at", ""), reverse=True)


def match_saved_session(
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


def resume_saved_chat(session: ChatSession, selector: str = "") -> ChatSession:
    armory_path = session_armory(session)
    if armory_path is None:
        return session
    sessions = recent_sessions(list_armory_sessions(armory_path))
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
        entry = match_saved_session(sessions, selector)
        if entry is None:
            return session
    save_before_switch(session)
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


def list_saved_chats(session: ChatSession) -> None:
    armory_path = session_armory(session)
    if armory_path is None:
        return
    sessions = recent_sessions(list_armory_sessions(armory_path))
    if not sessions:
        print_info("No saved chats found.")
        return
    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
