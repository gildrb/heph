from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.runtime import Conversation

_log = get_logger("chat.storage")

CHATS_DIR = ".hephaistos/chats"


class ChatStorageError(Exception):
    pass


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
    chats = _chats_path(armory_path).resolve()
    target = _session_path(armory_path, session_id).resolve()
    if not target.is_relative_to(chats):
        raise ChatStorageError(f"invalid session id: {session_id}")


def new_session_id() -> str:
    return uuid4().hex[:12]


def save(
    armory_path: Path,
    session_id: str,
    conversation: Conversation,
    *,
    title: str = "",
    metadata: dict[str, object] | None = None,
) -> Path:
    _validate_session_path(armory_path, session_id)

    chats = _chats_path(armory_path)
    chats.mkdir(parents=True, exist_ok=True)

    file_path = _session_path(armory_path, session_id)
    now = datetime.now(UTC).isoformat()

    data: dict[str, object] = {
        "session_id": session_id,
        "title": title,
        "updated_at": now,
        "messages": [
            {"role": message.role, "content": message.content} for message in conversation.messages
        ],
    }
    existing: dict[str, object] = {}
    if file_path.exists():
        raw_existing: object = json.loads(file_path.read_text(encoding="utf-8"))
        if is_string_mapping(raw_existing):
            existing = raw_existing
        data["created_at"] = existing.get("created_at", now)
    else:
        data["created_at"] = now
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
    data = _load_session_data(armory_path, session_id)
    conversation = Conversation()
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
    data = _load_session_data(armory_path, session_id)
    metadata: object = data.get("metadata")
    return metadata if is_string_mapping(metadata) else {}


def list_sessions(armory_path: Path) -> list[SessionRecord]:
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
        except json.JSONDecodeError:
            continue
    return sessions
