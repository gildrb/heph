"""Tests for chat engine (LLM communication)."""

from __future__ import annotations

import pytest

from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    Message,
    build_client,
    missing_api_key_message,
)


def test_build_client_allows_pollinations_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEPHAISTOS_API_KEY", raising=False)
    config = ChatConfig(
        api_key="",
        base_url="https://text.pollinations.ai/openai",
        model="openai",
    )

    client = build_client(config)

    assert client.api_key == "no-key-required"


def test_build_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEPHAISTOS_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ChatConfig(api_key="", base_url="http://localhost/v1", model="test")
    with pytest.raises(EngineError, match="No API key found"):
        build_client(config)


def test_keyless_provider_does_not_resolve_key(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ChatConfig(base_url="https://text.pollinations.ai/openai", model="openai")
    config.apply_provider_reference("pollinations", "")

    def fail_resolve(_slug: str, _env: str = "") -> str:
        raise AssertionError("resolved key")

    monkeypatch.setattr(
        "hephaistos.runtime.engine.resolve_key",
        fail_resolve,
    )

    assert config.resolved_api_key == ""
    client = build_client(config)
    assert str(client.base_url) == "https://text.pollinations.ai/openai/"


def test_missing_api_key_message_explains_free_openrouter_auth() -> None:
    config = ChatConfig(
        api_key="",
        base_url="https://openrouter.ai/api/v1",
        model="arcee-ai/trinity-large-preview:free",
    )

    message = missing_api_key_message(config)

    assert "free-priced" in message
    assert "still requires an API key" in message
    assert "/login" in message


def test_build_client_rejects_unavailable_model_for_known_endpoint() -> None:
    config = ChatConfig(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="legacy-model",
    )
    with pytest.raises(EngineError, match="Model unavailable for endpoint"):
        build_client(config)


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


def test_is_feature_enabled() -> None:
    config = ChatConfig(feature_flags=frozenset({"alpha", "beta"}))
    assert config.is_feature_enabled("alpha")
    assert config.is_feature_enabled("beta")
    assert not config.is_feature_enabled("gamma")


def test_is_feature_enabled_default_empty() -> None:
    config = ChatConfig()
    assert not config.is_feature_enabled("anything")
