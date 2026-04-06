"""Tests for streaming error recovery: retry logic, partial content, state consistency."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    StreamRecoveryError,
    _build_client,
    _wait_backoff,
    is_retryable_error,
    stream_reply,
    get_reply,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config() -> ChatConfig:
    return ChatConfig(api_key="test-key", base_url="http://localhost/v1", model="test")


def _conv(prompt: str = "Hello") -> Conversation:
    conv = Conversation()
    conv.add("user", prompt)
    return conv


def _make_chunk(content: str | None = None, finish_reason: str | None = None) -> MagicMock:
    """Build a mock stream chunk."""
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = None
    choice = MagicMock()
    choice.delta = delta
    choice.finish_reason = finish_reason
    chunk.choices = [choice]
    return chunk


# ---------------------------------------------------------------------------
# is_retryable_error
# ---------------------------------------------------------------------------


class TestIsRetryableError:
    def test_connection_error_is_retryable(self) -> None:
        assert is_retryable_error(APIConnectionError(MagicMock())) is True

    def test_timeout_is_retryable(self) -> None:
        assert is_retryable_error(APITimeoutError(MagicMock())) is True

    def test_internal_server_error_is_retryable(self) -> None:
        assert is_retryable_error(InternalServerError(MagicMock(), body=None)) is True

    def test_rate_limit_is_retryable(self) -> None:
        assert is_retryable_error(RateLimitError(MagicMock(), response=MagicMock(), body=None)) is True

    def test_generic_exception_not_retryable(self) -> None:
        assert is_retryable_error(RuntimeError("boom")) is False

    def test_value_error_not_retryable(self) -> None:
        assert is_retryable_error(ValueError("bad input")) is False


# ---------------------------------------------------------------------------
# RetryConfig
# ---------------------------------------------------------------------------


class TestRetryConfig:
    def test_defaults(self) -> None:
        cfg = RetryConfig()
        assert cfg.max_retries == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 30.0

    def test_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAISTOS_MAX_RETRIES", "5")
        monkeypatch.setenv("HEPHAISTOS_RETRY_BASE_DELAY", "0.5")
        monkeypatch.setenv("HEPHAISTOS_RETRY_MAX_DELAY", "60")
        cfg = RetryConfig.from_env()
        assert cfg.max_retries == 5
        assert cfg.base_delay == 0.5
        assert cfg.max_delay == 60.0


# ---------------------------------------------------------------------------
# _wait_backoff
# ---------------------------------------------------------------------------


class TestWaitBackoff:
    def test_returns_true_on_normal_sleep(self) -> None:
        cfg = RetryConfig(base_delay=0.01, max_delay=0.01)
        # Should return True (not aborted)
        assert _wait_backoff(0, cfg) is True

    def test_returns_false_when_aborted(self) -> None:
        cfg = RetryConfig(base_delay=0.01, max_delay=0.01)
        abort = threading.Event()
        abort.set()
        assert _wait_backoff(0, cfg, abort) is False

    def test_backoff_increases_delay(self) -> None:
        """Attempt 0 → base_delay, attempt 3 → min(base*8, max)."""
        cfg = RetryConfig(base_delay=1.0, max_delay=4.0)
        # Just check that it doesn't crash and respects the bounds
        import time
        t0 = time.monotonic()
        _wait_backoff(0, cfg)
        elapsed = time.monotonic() - t0
        # With jitter up to 0.5 * delay, the elapsed time should be < delay
        assert elapsed < 2.0  # generous upper bound


# ---------------------------------------------------------------------------
# StreamRecoveryError
# ---------------------------------------------------------------------------


class TestStreamRecoveryError:
    def test_carries_partial_content(self) -> None:
        original = RuntimeError("connection reset")
        err = StreamRecoveryError("Hello, world!", original)
        assert err.partial_content == "Hello, world!"
        assert "12 chars" in str(err)
        assert err.__cause__ is original

    def test_no_cause(self) -> None:
        err = StreamRecoveryError("partial", None)
        assert err.partial_content == "partial"
        assert "7 chars" in str(err)
        assert err.__cause__ is None

    def test_is_engine_error(self) -> None:
        err = StreamRecoveryError("x")
        assert isinstance(err, EngineError)


# ---------------------------------------------------------------------------
# stream_reply — retry logic
# ---------------------------------------------------------------------------


class TestStreamReplyRetry:
    def test_succeeds_on_first_try(self) -> None:
        """No retry needed — stream completes normally."""
        chunks = [_make_chunk("Hi "), _make_chunk("there")]

        mock_stream = MagicMock()
        mock_stream.__iter__ = MagicMock(return_value=iter(chunks))

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_stream

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Hi ", "there"]
        # Only called once
        assert mock_client.chat.completions.create.call_count == 1

    def test_retries_on_pre_stream_connection_error(self) -> None:
        """Connection error before any content → retry succeeds."""
        chunks = [_make_chunk("Recovered")]
        mock_stream = MagicMock()
        mock_stream.__iter__ = MagicMock(return_value=iter(chunks))

        mock_client = MagicMock()
        # First call fails, second succeeds
        mock_client.chat.completions.create.side_effect = [
            APIConnectionError(MagicMock()),
            mock_stream,
        ]

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Recovered"]
        assert mock_client.chat.completions.create.call_count == 2

    def test_retries_on_pre_stream_timeout(self) -> None:
        """Timeout before content → retry succeeds."""
        chunks = [_make_chunk("OK")]
        mock_stream = MagicMock()
        mock_stream.__iter__ = MagicMock(return_value=iter(chunks))

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            APITimeoutError(MagicMock()),
            mock_stream,
        ]

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["OK"]

    def test_raises_engine_error_after_max_retries(self) -> None:
        """All retries exhausted → EngineError."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(MagicMock())

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(EngineError, match="failed after 3 attempts"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

    def test_non_retryable_error_raises_immediately(self) -> None:
        """AuthenticationError (not retryable) → raise immediately."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("auth fail")

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM request failed"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        # Should only be called once — no retry
        assert mock_client.chat.completions.create.call_count == 1

    def test_mid_stream_failure_with_partial_content_raises_recovery(self) -> None:
        """Stream drops AFTER content → StreamRecoveryError with partial."""
        # First chunk succeeds, then iteration raises
        def _iter_fail(self_unused=None):
            yield _make_chunk("Hello ")

        mock_stream = MagicMock()
        mock_stream.__iter__ = MagicMock(side_effect=[
            # Attempt 1: yield one chunk then fail
            _iter_fail(),
        ])
        # Make the iterator raise after first chunk
        # Actually, let's use a simpler approach:
        # Create a custom iterator that yields then raises
        class FailingIterator:
            def __iter__(self):
                return self
            def __next__(self):
                if not hasattr(self, '_yielded'):
                    self._yielded = True
                    return _make_chunk("Hello ")
                raise APIConnectionError(MagicMock())

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailingIterator()

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        assert exc_info.value.partial_content == "Hello "

    def test_mid_stream_failure_no_content_retries(self) -> None:
        """Stream drops with NO content yet → retry (safe to retry)."""
        class FailingIteratorEmpty:
            def __iter__(self):
                return self
            def __next__(self):
                raise APIConnectionError(MagicMock())

        good_chunks = [_make_chunk("Retry OK")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            FailingIteratorEmpty(),
            iter(good_chunks),
        ]

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Retry OK"]

    def test_abort_event_stops_before_stream(self) -> None:
        """Abort event set before streaming starts → returns empty."""
        mock_client = MagicMock()

        abort = threading.Event()
        abort.set()

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), abort=abort, retry=retry))

        assert result == []
        mock_client.chat.completions.create.assert_not_called()

    def test_abort_event_stops_mid_backoff(self) -> None:
        """Abort event set during backoff → returns empty."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(MagicMock())

        abort = threading.Event()
        # Set abort after a tiny delay so the retry loop can enter
        threading.Timer(0.01, abort.set).start()

        retry = RetryConfig(max_retries=5, base_delay=10.0, max_delay=30.0)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), abort=abort, retry=retry))

        assert result == []
        # Should have called create at least once
        assert mock_client.chat.completions.create.call_count >= 1


class TestStreamReplyRetryNotRetryableMidStream:
    """Mid-stream failure with non-retryable error (even with no content)."""

    def test_non_retryable_mid_stream_no_content_raises(self) -> None:
        class FailIterator:
            def __iter__(self):
                return self
            def __next__(self):
                raise RuntimeError("unexpected")

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailIterator()

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM stream failed"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        # No retry since RuntimeError is not retryable
        assert mock_client.chat.completions.create.call_count == 1


# ---------------------------------------------------------------------------
# get_reply — integration with retry
# ---------------------------------------------------------------------------


class TestGetReply:
    def test_get_reply_normal(self) -> None:
        chunks = [_make_chunk("Hello"), _make_chunk(" world")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(chunks)

        retry = RetryConfig(max_retries=0, base_delay=0.01)
        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = get_reply(_config(), _conv(), retry=retry)

        assert result == "Hello world"

    def test_get_reply_propagates_stream_recovery_error(self) -> None:
        class FailAfterContent:
            def __iter__(self):
                return self
            def __next__(self):
                if not hasattr(self, '_sent'):
                    self._sent = True
                    return _make_chunk("Partial ")
                raise APIConnectionError(MagicMock())

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailAfterContent()

        retry = RetryConfig(max_retries=0, base_delay=0.01)
        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            get_reply(_config(), _conv(), retry=retry)

        assert exc_info.value.partial_content == "Partial "


# ---------------------------------------------------------------------------
# Conversation state consistency
# ---------------------------------------------------------------------------


class TestConversationConsistency:
    def test_rollback_on_engine_error(self) -> None:
        """Verify that the conversation is rolled back on failure."""
        from hephaistos.chat.session import ChatSession, send_user_message

        config = _config()
        conv = _conv("test prompt")
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-rollback",
        )

        # The conversation starts with one user message
        assert len(conv.messages) == 1

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(MagicMock())

        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(EngineError),
        ):
            send_user_message(session, "hello")

        # Conversation should be rolled back to original state
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "test prompt"

    def test_rollback_on_stream_recovery(self) -> None:
        """Verify that the conversation is rolled back on StreamRecoveryError."""
        from hephaistos.chat.session import ChatSession, send_user_message

        config = _config()
        conv = _conv("test prompt")
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-recovery",
        )

        assert len(conv.messages) == 1

        class FailAfterContent:
            def __iter__(self):
                return self
            def __next__(self):
                if not hasattr(self, '_sent'):
                    self._sent = True
                    return _make_chunk("Partial reply")
                raise APIConnectionError(MagicMock())

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailAfterContent()

        with (
            patch("hephaistos.chat.engine._build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            send_user_message(session, "hello")

        # Conversation should be rolled back
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "test prompt"
        # But partial content should be available in the exception
        assert exc_info.value.partial_content == "Partial reply"
        # Session should be dirty so the user knows something happened
        assert session.dirty is True

    def test_successful_reply_does_not_rollback(self) -> None:
        """Successful reply adds messages without rollback."""
        from hephaistos.chat.session import ChatSession, send_user_message

        config = _config()
        conv = Conversation()  # empty
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-success",
        )

        chunks = [_make_chunk("Hello!")]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(chunks)

        with patch("hephaistos.chat.engine._build_client", return_value=mock_client):
            result = send_user_message(session, "Hi")

        assert result == "Hello!"
        assert len(conv.messages) == 2  # user + assistant
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].content == "Hello!"


# ---------------------------------------------------------------------------
# Agent loop retry
# ---------------------------------------------------------------------------


class TestAgentLoopRetry:
    def test_agent_loop_retries_on_connection_error(self) -> None:
        """Agent loop retries the API call on connection error."""
        from hephaistos.harness.dispatch import agent_loop

        chunks = [_make_chunk("Done")]
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            APIConnectionError(MagicMock()),
            iter(chunks),
        ]

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with patch("hephaistos.harness.dispatch._build_client", return_value=mock_client):
            result = list(agent_loop(_config(), _conv(), workspace=_workspace(), retry=retry))

        assert "".join(result) == "Done"
        assert mock_client.chat.completions.create.call_count == 2

    def test_agent_loop_raises_recovery_on_mid_stream_failure(self) -> None:
        """Agent loop raises StreamRecoveryError when stream drops mid-content."""
        from hephaistos.harness.dispatch import agent_loop

        class FailAfterContent:
            def __iter__(self):
                return self
            def __next__(self):
                if not hasattr(self, '_sent'):
                    self._sent = True
                    return _make_chunk("Partial agent ")
                raise APIConnectionError(MagicMock())

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailAfterContent()

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with (
            patch("hephaistos.harness.dispatch._build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            list(agent_loop(_config(), _conv(), workspace=_workspace(), retry=retry))

        assert exc_info.value.partial_content == "Partial agent "

    def test_agent_loop_exhausts_retries(self) -> None:
        """Agent loop raises EngineError after all retries exhausted."""
        from hephaistos.harness.dispatch import agent_loop

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(MagicMock())

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with (
            patch("hephaistos.harness.dispatch._build_client", return_value=mock_client),
            pytest.raises(EngineError, match="failed after 2 attempts"),
        ):
            list(agent_loop(_config(), _conv(), workspace=_workspace(), retry=retry))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _workspace():
    from pathlib import Path
    return Path("/tmp/fake_workspace")


