from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from ai.logging import get_logger
from ai.runtime import Conversation

from harness._types import is_object_list, is_string_mapping
from harness.armory.state_files import read_armory_state_text, write_armory_state_text
from harness.chat.titles import sanitize_title_text

_log = get_logger("harness.chat.storage")

CHATS_DIR = ".harness/chats"


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


def _session_rel_path(session_id: str) -> str:
    return f"{CHATS_DIR}/{session_id}.json"


def _session_id_is_safe(session_id: str) -> bool:
    return (
        bool(session_id.strip())
        and "\x00" not in session_id
        and "/" not in session_id
        and "\\" not in session_id
        and ".." not in session_id
        and not session_id.startswith(".")
    )


def _validate_session_path(armory_path: Path, session_id: str) -> None:
    if not _session_id_is_safe(session_id):
        raise ChatStorageError(f"invalid session id: {session_id}")
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

    now = datetime.now(UTC).isoformat()
    existing = _read_existing_session_data(armory_path, session_id)
    data = _session_data(
        session_id=session_id,
        title=title,
        conversation=conversation,
        now=now,
        existing=existing,
        metadata=metadata,
    )

    file_path = write_armory_state_text(
        armory_path,
        _session_rel_path(session_id),
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
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


def _session_data(
    *,
    session_id: str,
    title: str,
    conversation: Conversation,
    now: str,
    existing: dict[str, object],
    metadata: dict[str, object] | None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "session_id": session_id,
        "title": sanitize_title_text(title),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "messages": [
            {"role": message.role, "content": message.content} for message in conversation.messages
        ],
    }
    if metadata is not None:
        data["metadata"] = metadata
    elif is_string_mapping(existing.get("metadata")):
        data["metadata"] = existing["metadata"]
    return data


def _read_existing_session_data(armory_path: Path, session_id: str) -> dict[str, object]:
    file_path = _session_path(armory_path, session_id)
    if not file_path.exists():
        return {}
    raw_existing: object = json.loads(
        read_armory_state_text(armory_path, _session_rel_path(session_id))
    )
    return raw_existing if is_string_mapping(raw_existing) else {}


def _load_session_data(armory_path: Path, session_id: str) -> dict[str, object]:
    _validate_session_path(armory_path, session_id)

    file_path = _session_path(armory_path, session_id)
    if not file_path.exists():
        raise ChatStorageError(f"chat session not found: {session_id}")

    try:
        raw_data: object = json.loads(
            read_armory_state_text(armory_path, _session_rel_path(session_id))
        )
    except (json.JSONDecodeError, OSError) as exc:
        raise ChatStorageError(f"corrupt session file {session_id}") from exc
    if not is_string_mapping(raw_data):
        raise ChatStorageError(f"corrupt session file {session_id}")
    return raw_data


def load(armory_path: Path, session_id: str) -> tuple[Conversation, str]:
    data = _load_session_data(armory_path, session_id)
    conversation = _conversation_from_data(data)
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
    return conversation, sanitize_title_text(title) if isinstance(title, str) else ""


def _conversation_from_data(data: dict[str, object]) -> Conversation:
    conversation = Conversation()
    raw_messages = data.get("messages", [])
    if not is_object_list(raw_messages):
        return conversation
    for msg in raw_messages:
        _add_message_from_payload(conversation, msg)
    return conversation


def _add_message_from_payload(conversation: Conversation, payload: object) -> None:
    if not is_string_mapping(payload):
        return
    role_val = payload.get("role")
    content_val = payload.get("content")
    if role_val is not None and content_val is not None:
        conversation.add(str(role_val), str(content_val))


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
            data = json.loads(
                read_armory_state_text(armory_path, _session_rel_path(file_path.stem))
            )
            if not is_string_mapping(data):
                continue
            sessions.append(
                {
                    "session_id": str(data.get("session_id", file_path.stem)),
                    "title": sanitize_title_text(str(data.get("title", ""))),
                    "created_at": str(data.get("created_at", "")),
                    "updated_at": str(data.get("updated_at", "")),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    return sessions
