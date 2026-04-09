"""Tests for chat engine (LLM communication)."""

from __future__ import annotations

from hephaistos.chat.engine import ChatConfig, Conversation, Message


def test_build_client_raises_without_api_key(monkeypatch) -> None:
    import pytest

    from hephaistos.chat.engine import EngineError, _build_client

    monkeypatch.delenv("HEPHAISTOS_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ChatConfig(api_key="", base_url="http://localhost/v1", model="test")
    with pytest.raises(EngineError, match="No API key found"):
        _build_client(config)


def test_build_client_rejects_unavailable_model_for_known_endpoint() -> None:
    import pytest

    from hephaistos.chat.engine import EngineError, _build_client

    config = ChatConfig(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="legacy/vendor-model",
    )
    with pytest.raises(EngineError, match="Model unavailable for endpoint"):
        _build_client(config)


def test_conversation_add_and_convert() -> None:
    conv = Conversation()
    conv.add("system", "You are helpful.")
    conv.add("user", "Hello")

    assert len(conv.messages) == 2
    assert conv.messages[0].role == "system"
    assert conv.messages[1].content == "Hello"

    api_msgs = conv.to_api_messages()
    assert len(api_msgs) == 2
    assert api_msgs[0]["role"] == "system"
    assert api_msgs[1]["role"] == "user"
    assert api_msgs[1]["content"] == "Hello"


def test_message_dataclass() -> None:
    msg = Message(role="user", content="test")
    assert msg.role == "user"
    assert msg.content == "test"
