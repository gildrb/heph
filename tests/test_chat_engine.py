"""Tests for chat engine (LLM communication)."""

from __future__ import annotations


from hephaistos.chat.engine import ChatConfig, Conversation, Message


def test_chat_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("HEPHAISTOS_API_KEY", "test-key")
    monkeypatch.setenv("HEPHAISTOS_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("HEPHAISTOS_MODEL", "local-model")

    config = ChatConfig.from_env()
    assert config.api_key == "test-key"
    assert config.base_url == "http://localhost:1234/v1"
    assert config.model == "local-model"


def test_chat_config_falls_back_to_openai_key(monkeypatch) -> None:
    monkeypatch.delenv("HEPHAISTOS_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-fallback")

    config = ChatConfig.from_env()
    assert config.api_key == "openai-fallback"


def test_chat_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("HEPHAISTOS_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("HEPHAISTOS_BASE_URL", raising=False)
    monkeypatch.delenv("HEPHAISTOS_MODEL", raising=False)

    config = ChatConfig.from_env()
    assert config.api_key == ""
    assert config.base_url == "https://api.openai.com/v1"
    assert config.model == "gpt-4o-mini"


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
