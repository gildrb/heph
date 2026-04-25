"""Integration tests for the chat pipeline.

These tests wire together real components (ChatConfig, Conversation, engine)
with mocked LLM transport to verify end-to-end behaviour without network access.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from openai import APITimeoutError, AuthenticationError

from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    StreamRecoveryError,
    stream_completion,
    stream_reply,
)
from hephaistos.chat.session import ChatSession


def _make_config() -> ChatConfig:
    return ChatConfig(
        api_key="test-key",
        base_url="https://api.example.com/v1",
        model="test-model",
        max_tokens=256,
    )


def _mock_chunk(
    content: str | None = None,
    tool_calls: list[object] | None = None,
    finish_reason: str | None = None,
) -> MagicMock:
    """Create a mock object that behaves like an OpenAI streaming chunk."""
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = tool_calls

    choice = MagicMock()
    choice.delta = delta
    choice.finish_reason = finish_reason

    chunk = MagicMock()
    chunk.choices = [choice]
    chunk.usage = None
    return chunk


def _mock_client(*chunks: MagicMock) -> MagicMock:
    """Return a mock OpenAI client whose chat.completions.create yields chunks."""
    client = MagicMock()
    client.chat.completions.create.return_value = iter(chunks)
    return client


def _client_factory(mock_client: MagicMock):
    """Wrap a mock client in a factory callable for the client_factory param."""

    def factory(_config: ChatConfig) -> MagicMock:
        return mock_client

    return factory


class TestStreamCompletionPipeline:
    """Test the full streaming pipeline with real component wiring."""

    def test_single_chunk_content(self) -> None:
        config = _make_config()
        chunks = [
            _mock_chunk(content="Hello"),
            _mock_chunk(content=" world"),
            _mock_chunk(finish_reason="stop"),
        ]
        client = _mock_client(*chunks)

        result = list(
            stream_completion(
                config,
                Conversation(),
                retry=RetryConfig(max_retries=0),
                client_factory=_client_factory(client),
            )
        )

        contents = [d.content for d in result if d.content]
        assert "".join(contents) == "Hello world"
        assert result[-1].finish_reason == "stop"

    def test_retry_on_transient_error(self) -> None:
        config = _make_config()
        client = MagicMock()

        timeout = APITimeoutError(request=MagicMock())
        success_chunk = _mock_chunk(content="recovered", finish_reason="stop")
        client.chat.completions.create.side_effect = [
            timeout,
            iter([success_chunk]),
        ]

        result = list(
            stream_completion(
                config,
                Conversation(),
                retry=RetryConfig(max_retries=2, base_delay=0.01),
                client_factory=_client_factory(client),
            )
        )

        assert result[-1].content == "recovered"
        assert client.chat.completions.create.call_count == 2

    def test_non_retryable_error_raises_immediately(self) -> None:
        config = _make_config()
        client = MagicMock()

        auth_error = AuthenticationError(
            message="bad key",
            response=MagicMock(status_code=401),
            body=None,
        )
        client.chat.completions.create.side_effect = auth_error

        with pytest.raises(EngineError, match="bad key"):
            list(
                stream_completion(
                    config,
                    Conversation(),
                    retry=RetryConfig(max_retries=3, base_delay=0.01),
                    client_factory=_client_factory(client),
                ),
            )

        assert client.chat.completions.create.call_count == 1

    def test_stream_recovery_preserves_partial(self) -> None:
        config = _make_config()
        client = MagicMock()
        chunk1 = _mock_chunk(content="partial ")

        def streaming_response(**_kwargs: object) -> Iterator[MagicMock]:
            yield chunk1
            raise RuntimeError("connection lost")

        client.chat.completions.create.return_value = streaming_response()

        with pytest.raises(StreamRecoveryError) as exc_info:
            list(
                stream_completion(
                    config,
                    Conversation(),
                    retry=RetryConfig(max_retries=0),
                    client_factory=_client_factory(client),
                ),
            )

        assert exc_info.value.partial_content == "partial "


class TestStreamReplyPipeline:
    """Test the stream_reply convenience wrapper."""

    def test_yields_content_strings(self) -> None:
        config = _make_config()
        chunks = [
            _mock_chunk(content="Hello"),
            _mock_chunk(content="!"),
            _mock_chunk(finish_reason="stop"),
        ]
        client = _mock_client(*chunks)

        with patch("hephaistos.chat.engine._build_client", return_value=client):
            result = list(
                stream_reply(
                    config,
                    Conversation(),
                    retry=RetryConfig(max_retries=0),
                )
            )

        assert result == ["Hello", "!"]


class TestConversationToPipeline:
    """Test Conversation → stream_completion wiring."""

    def test_conversation_messages_passed_to_api(self) -> None:
        config = _make_config()
        conv = Conversation()
        conv.add("system", "You are helpful.")
        conv.add("user", "Hi there")

        client = _mock_client(_mock_chunk(finish_reason="stop"))

        list(
            stream_completion(
                config,
                conv,
                retry=RetryConfig(max_retries=0),
                client_factory=_client_factory(client),
            )
        )

        call_kwargs = client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hi there"


class TestChatSessionPipeline:
    """Test ChatSession wiring."""

    def test_session_stores_config(self) -> None:
        config = _make_config()
        session = ChatSession(
            config=config,
            conversation=Conversation(),
            session_id="test-session",
        )
        assert session.config.model == "test-model"
        assert session.config.max_tokens == 256
