"""Tests for chat storage (persistence)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat.storage import (
    ChatStorageError,
    list_sessions,
    load,
    load_metadata,
    new_session_id,
    save,
)
from hephaistos.runtime import Conversation


def _init_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "test-armory"
    initialize(armory)
    return armory


def test_new_session_id_is_unique() -> None:
    ids = {new_session_id() for _ in range(100)}
    assert len(ids) == 100


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    session_id = new_session_id()

    conv = Conversation()
    conv.add("system", "You are helpful.")
    conv.add("user", "Hello")
    conv.add("assistant", "Hi there!")

    save(armory, session_id, conv, title="test chat")

    loaded_conv, title = load(armory, session_id)
    assert title == "test chat"
    assert len(loaded_conv.messages) == 3
    assert loaded_conv.messages[0].role == "system"
    assert loaded_conv.messages[1].role == "user"
    assert loaded_conv.messages[1].content == "Hello"
    assert loaded_conv.messages[2].role == "assistant"
    assert loaded_conv.messages[2].content == "Hi there!"


def test_save_preserves_created_at(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    session_id = new_session_id()

    conv = Conversation()
    conv.add("system", "You are helpful.")
    conv.add("user", "First message")
    save(armory, session_id, conv, title="v1")

    path = armory / ".hephaistos" / "chats" / f"{session_id}.json"
    data = json.loads(path.read_text())
    original_created = data["created_at"]

    conv.add("assistant", "Reply")
    save(armory, session_id, conv, title="v2")

    data2 = json.loads(path.read_text())
    assert data2["created_at"] == original_created
    assert len(data2["messages"]) == 3


def test_save_and_load_metadata_roundtrip(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    session_id = new_session_id()

    conv = Conversation()
    conv.add("system", "sys")
    conv.add("user", "hi")

    save(
        armory,
        session_id,
        conv,
        title="meta",
        metadata={"study_state": {"phase": "recall", "attempt_count": 2}},
    )

    metadata = load_metadata(armory, session_id)
    assert metadata == {"study_state": {"phase": "recall", "attempt_count": 2}}


def test_load_nonexistent_raises(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    with pytest.raises(ChatStorageError):
        load(armory, "does-not-exist")


def test_session_id_cannot_escape_chats_directory(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    conv = Conversation()
    conv.add("user", "hello")

    with pytest.raises(ChatStorageError, match="invalid session id"):
        save(armory, "../escape", conv)


def test_list_sessions_empty(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)
    sessions = list_sessions(armory)
    assert sessions == []


def test_list_sessions_returns_saved(tmp_path: Path) -> None:
    armory = _init_armory(tmp_path)

    conv = Conversation()
    conv.add("system", "sys")
    conv.add("user", "hi")

    s1 = new_session_id()
    s2 = new_session_id()
    save(armory, s1, conv, title="Chat A")
    save(armory, s2, conv, title="Chat B")

    sessions = list_sessions(armory)
    assert len(sessions) == 2
    ids = {s["session_id"] for s in sessions}
    assert s1 in ids
    assert s2 in ids
