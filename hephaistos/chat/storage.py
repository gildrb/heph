"""Chat history persistence within an armory's chats/ directory.

Each chat session is stored as a JSON file named by its session ID.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from hephaistos.chat.engine import Conversation, Message

CHATS_DIR = "chats"


class ChatStorageError(Exception):
    """Raised on chat persistence failures."""


def _chats_path(armory_path: Path) -> Path:
    return armory_path / CHATS_DIR


def _session_path(armory_path: Path, session_id: str) -> Path:
    return _chats_path(armory_path) / f"{session_id}.json"


def new_session_id() -> str:
    """Generate a new unique session ID."""
    return uuid4().hex[:12]


def _message_to_dict(msg: Message) -> dict[str, str]:
    return {"role": msg.role, "content": msg.content}


def _dict_to_message(data: dict[str, str]) -> Message:
    return Message(role=data["role"], content=data["content"])


def save(
    armory_path: Path,
    session_id: str,
    conversation: Conversation,
    *,
    title: str = "",
) -> Path:
    """Save a conversation to disk. Returns the path of the saved file."""
    chats = _chats_path(armory_path)
    chats.mkdir(parents=True, exist_ok=True)

    file_path = _session_path(armory_path, session_id)

    data: dict[str, object] = {
        "session_id": session_id,
        "title": title,
        "updated_at": datetime.now(UTC).isoformat(),
        "messages": [_message_to_dict(m) for m in conversation.messages],
    }

    # Preserve created_at if the file already exists
    if file_path.exists():
        existing = json.loads(file_path.read_text(encoding="utf-8"))
        data["created_at"] = existing.get(
            "created_at", datetime.now(UTC).isoformat()
        )
    else:
        data["created_at"] = datetime.now(UTC).isoformat()

    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return file_path


def load(armory_path: Path, session_id: str) -> tuple[Conversation, str]:
    """Load a conversation from disk.

    Returns (conversation, title).
    """
    file_path = _session_path(armory_path, session_id)
    if not file_path.exists():
        raise ChatStorageError(f"chat session not found: {session_id}")

    data = json.loads(file_path.read_text(encoding="utf-8"))
    conversation = Conversation()
    for msg_data in data.get("messages", []):
        conversation.add(msg_data["role"], msg_data["content"])
    return conversation, data.get("title", "")


def list_sessions(armory_path: Path) -> list[dict[str, str]]:
    """List all chat sessions in the armory.

    Returns a list of dicts with keys: session_id, title, created_at, updated_at.
    """
    chats = _chats_path(armory_path)
    if not chats.exists():
        return []

    sessions: list[dict[str, str]] = []
    for file_path in sorted(chats.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            sessions.append(
                {
                    "session_id": data.get("session_id", file_path.stem),
                    "title": data.get("title", ""),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions
