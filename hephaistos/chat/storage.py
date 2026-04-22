"""Chat history persistence within an armory's chats/ directory.

Each chat session is stored as a JSON file named by its session ID.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.chat.engine import Conversation, Message
from hephaistos.logging import get_logger

_log = get_logger("chat.storage")

CHATS_DIR = "chats"


class ChatStorageError(Exception):
    """Raised on chat persistence failures."""


class SessionRecord(TypedDict):
    session_id: str
    title: str
    created_at: str
    updated_at: str


def _chats_path(armory_path: Path) -> Path:
    return armory_path / CHATS_DIR


def _session_path(armory_path: Path, session_id: str) -> Path:
    return _chats_path(armory_path) / f"{session_id}.json"


def _validate_session_path(armory_path: Path, session_id: str) -> None:
    """Ensure the resolved session path stays within the chats directory.

    Raises ChatStorageError if the path would escape the chats directory.
    """
    chats = _chats_path(armory_path).resolve()
    target = _session_path(armory_path, session_id).resolve()
    if not str(target).startswith(str(chats) + os.sep) and target != chats:
        raise ChatStorageError(f"invalid session id: {session_id}")


def new_session_id() -> str:
    """Generate a new unique session ID."""
    return uuid4().hex[:12]


def _message_to_dict(msg: Message) -> dict[str, str]:
    return {"role": msg.role, "content": msg.content}


def save(
    armory_path: Path,
    session_id: str,
    conversation: Conversation,
    *,
    title: str = "",
    metadata: dict[str, object] | None = None,
) -> Path:
    """Save a conversation to disk. Returns the path of the saved file."""
    _validate_session_path(armory_path, session_id)

    chats = _chats_path(armory_path)
    chats.mkdir(parents=True, exist_ok=True)

    file_path = _session_path(armory_path, session_id)

    data: dict[str, object] = {
        "session_id": session_id,
        "title": title,
        "updated_at": datetime.now(UTC).isoformat(),
        "messages": [_message_to_dict(m) for m in conversation.messages],
    }
    existing: dict[str, object] = {}
    if file_path.exists():
        raw_existing: object = json.loads(file_path.read_text(encoding="utf-8"))
        if is_string_mapping(raw_existing):
            existing = raw_existing
        data["created_at"] = existing.get("created_at", datetime.now(UTC).isoformat())
    else:
        data["created_at"] = datetime.now(UTC).isoformat()
    if metadata is not None:
        data["metadata"] = metadata
    elif is_string_mapping(existing.get("metadata")):
        data["metadata"] = existing["metadata"]

    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _log.info(
        "session saved",
        extra={
            "fields": {
                "session_id": session_id,
                "path": str(file_path),
                "message_count": len(conversation.messages),
            }
        },
    )
    return file_path


def _load_session_data(armory_path: Path, session_id: str) -> dict[str, object]:
    """Load the raw JSON payload for a saved chat session."""
    _validate_session_path(armory_path, session_id)

    file_path = _session_path(armory_path, session_id)
    if not file_path.exists():
        raise ChatStorageError(f"chat session not found: {session_id}")

    try:
        raw_data: object = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ChatStorageError(f"corrupt session file {session_id}") from exc
    if not is_string_mapping(raw_data):
        raise ChatStorageError(f"corrupt session file {session_id}")
    return raw_data


def load(armory_path: Path, session_id: str) -> tuple[Conversation, str]:
    """Load a conversation from disk.

    Returns (conversation, title).
    """
    data = _load_session_data(armory_path, session_id)
    conversation = Conversation()
    try:
        raw_messages = data.get("messages", [])
        if not is_object_list(raw_messages):
            raw_messages = []
        for msg in raw_messages:
            if not is_string_mapping(msg):
                continue
            role_val = msg.get("role")
            content_val = msg.get("content")
            if role_val is None or content_val is None:
                continue
            conversation.add(str(role_val), str(content_val))
    except KeyError as exc:
        _log.error(
            "corrupt session file",
            extra={
                "fields": {
                    "session_id": session_id,
                    "error": f"missing key {exc}",
                }
            },
        )
        raise ChatStorageError(f"corrupt session file {session_id}: missing key {exc}") from exc
    _log.debug(
        "session loaded",
        extra={
            "fields": {
                "session_id": session_id,
                "message_count": len(conversation.messages),
            }
        },
    )
    title = data.get("title", "")
    return conversation, title if isinstance(title, str) else ""


def load_metadata(armory_path: Path, session_id: str) -> dict[str, object]:
    """Load optional session metadata stored alongside the conversation."""
    data = _load_session_data(armory_path, session_id)
    metadata: object = data.get("metadata")
    if is_string_mapping(metadata):
        return metadata
    return {}


def list_sessions(armory_path: Path) -> list[SessionRecord]:
    """List all chat sessions in the armory.

    Returns a list of dicts with keys: session_id, title, created_at, updated_at.
    """
    chats = _chats_path(armory_path)
    if not chats.exists():
        return []

    sessions: list[SessionRecord] = []
    for file_path in sorted(chats.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if not is_string_mapping(data):
                continue
            sessions.append(
                {
                    "session_id": str(data.get("session_id", file_path.stem)),
                    "title": str(data.get("title", "")),
                    "created_at": str(data.get("created_at", "")),
                    "updated_at": str(data.get("updated_at", "")),
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions
