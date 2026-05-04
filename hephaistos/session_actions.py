"""Application actions for replacing the active chat session."""

from __future__ import annotations

from contextlib import suppress

from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    save_session,
    session_has_messages,
)
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.terminal_display import print_error, print_info, print_success


def autosave_before_replacement(session: ChatSession, *, announce: bool) -> None:
    if not (session.armory_path and session.dirty and session_has_messages(session)):
        return
    if announce:
        try:
            save_session(session)
            print_info("Previous session saved.")
        except chat_storage.ChatStorageError:
            pass
        return
    with suppress(chat_storage.ChatStorageError):
        save_session(session)


def create_replacement_session(session: ChatSession) -> ChatSession | None:
    try:
        if session.armory_path is None:
            return create_plain_session(session.config)
        return create_session(session.config, session.armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return None


def start_replacement_session(
    session: ChatSession,
    *,
    analytics_event: str,
    success_message: str,
    announce_autosave: bool,
) -> ChatSession | None:
    autosave_before_replacement(session, announce=announce_autosave)
    new_session = create_replacement_session(session)
    if new_session is None:
        return None
    print_success(success_message)
    capture_analytics(
        analytics_event,
        {
            "mode": "armory" if new_session.armory_path is not None else "plain",
            "model": new_session.config.model,
        },
    )
    return new_session
