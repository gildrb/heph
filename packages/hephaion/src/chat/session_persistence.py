"""Chat session persistence helpers."""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from ai.logging import get_logger
from diagnostics.events import capture as capture_analytics

import chat.storage as chat_storage
from chat.titles import derive_title as _derive_title

if TYPE_CHECKING:
    from chat.session import ChatSession

_log = get_logger("chat.session_persistence")


def session_has_messages(session: ChatSession) -> bool:
    return any(message.role != "system" for message in session.conversation.messages)


def save_dirty_session_if_needed(session: ChatSession) -> None:
    if session.armory_path is None or not session.dirty or not session_has_messages(session):
        return
    with contextlib.suppress(chat_storage.ChatStorageError):
        save_session(session)


def save_session(session: ChatSession) -> Path:
    if session.armory_path is None:
        raise chat_storage.ChatStorageError(
            "cannot save chat without an active armory; use /armory first"
        )
    title = session.title or _derive_title(session.conversation)
    path = chat_storage.save(
        session.armory_path,
        session.session_id,
        session.conversation,
        title=title,
        metadata={
            "learning_state": session.learning_state.to_dict(),
            "disabled_source_files": sorted(session.disabled_source_files),
            "last_plan_intent": session.last_plan_intent,
            "last_turn_contract": (
                session.last_turn_contract.to_dict() if session.last_turn_contract else {}
            ),
            "last_turn_evidence": (
                session.last_turn_evidence.to_dict() if session.last_turn_evidence else {}
            ),
            "turn_history": [snapshot.to_dict() for snapshot in session.turn_history],
            "started_at": session.started_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
        },
    )
    session.dirty = False
    capture_analytics(
        "session_saved",
        {
            "message_count": len(session.conversation.messages),
            "mode": "armory",
            "model": session.config.model,
        },
    )
    _log.info(
        "session saved",
        extra={
            "fields": {
                "session_id": session.session_id,
                "path": str(path),
                "message_count": len(session.conversation.messages),
            }
        },
    )
    session.trace.record_session_event("saved", path=str(path))
    return path
