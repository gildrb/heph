"""Tests for streaming error recovery: retry logic, partial content, state consistency."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from ai.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    EngineErrorCode,
    RetryConfig,
    StreamRecoveryError,
    stream_reply,
)
from ai.runtime.engine import _wait_backoff, get_reply, is_retryable_error
from harness.agent.dispatch import iter_agent_events
from harness.chat.events import AssistantDeltaEvent, render_turn_event
from harness.chat.orchestrator import TurnOrchestrator
from harness.chat.session import ChatSession, send_user_message
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request() -> httpx.Request:
    return httpx.Request("POST", "http://localhost/v1/chat/completions")


def _connection_error() -> APIConnectionError:
    return APIConnectionError(request=_make_request())


def _timeout_error() -> APITimeoutError:
    return APITimeoutError(request=_make_request())


def _server_error() -> InternalServerError:
    req = _make_request()
    resp = httpx.Response(500, request=req)
    return InternalServerError("server error", response=resp, body=None)


def _rate_limit_error() -> RateLimitError:
    req = _make_request()
    resp = httpx.Response(429, request=req)
    return RateLimitError("rate limited", response=resp, body=None)


def _insufficient_balance_error() -> RateLimitError:
    body = {
        "error": {
            "code": "1113",
            "message": "Insufficient balance or no resource package. Please recharge.",
        }
    }
    req = _make_request()
    resp = httpx.Response(429, request=req, json=body)
    return RateLimitError("rate limited", response=resp, body=body)


def _queue_full_error() -> RateLimitError:
    body = {
        "error": "Queue full for IP: 31.16.250.211: 1 requests already queued (max: 1).",
        "status": 429,
    }
    req = _make_request()
    resp = httpx.Response(429, request=req, json=body)
    return RateLimitError("rate limited", response=resp, body=body)


def _queue_full_response_error() -> RateLimitError:
    body = {
        "error": "Queue full for IP: 31.16.250.211: 1 requests already queued (max: 1).",
        "status": 429,
    }
    req = _make_request()
    resp = httpx.Response(429, request=req, json=body)
    return RateLimitError("rate limited", response=resp, body=None)


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


class FailingIterator:
    """Stream iterator that yields one chunk then raises."""

    def __init__(self, content: str, error: Exception | None = None) -> None:
        self._content = content
        self._error = error or _connection_error()
        self._yielded = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self._yielded:
            self._yielded = True
            return _make_chunk(self._content)
        raise self._error


class EmptyFailingIterator:
    """Stream iterator that raises immediately (no content)."""

    def __init__(self, error: Exception | None = None) -> None:
        self._error = error or _connection_error()

    def __iter__(self):
        return self

    def __next__(self):
        raise self._error


def _workspace():
    return Path("/tmp/fake_workspace")


# ---------------------------------------------------------------------------
# is_retryable_error
# ---------------------------------------------------------------------------


class TestIsRetryableError:
    def test_connection_error_is_retryable(self) -> None:
        assert is_retryable_error(_connection_error()) is True

    def test_timeout_is_retryable(self) -> None:
        assert is_retryable_error(_timeout_error()) is True

    def test_internal_server_error_is_retryable(self) -> None:
        assert is_retryable_error(_server_error()) is True

    def test_rate_limit_is_retryable(self) -> None:
        assert is_retryable_error(_rate_limit_error()) is True

    def test_account_setup_rate_limit_is_not_retryable(self) -> None:
        assert is_retryable_error(_insufficient_balance_error()) is False

    def test_queue_full_rate_limit_is_not_retryable(self) -> None:
        assert is_retryable_error(_queue_full_error()) is False

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


# ---------------------------------------------------------------------------
# _wait_backoff
# ---------------------------------------------------------------------------


class TestWaitBackoff:
    def test_returns_true_on_normal_sleep(self) -> None:
        cfg = RetryConfig(base_delay=0.01, max_delay=0.01)
        assert _wait_backoff(0, cfg) is True

    def test_returns_false_when_aborted(self) -> None:
        cfg = RetryConfig(base_delay=0.01, max_delay=0.01)
        abort = threading.Event()
        abort.set()
        assert _wait_backoff(0, cfg, abort) is False


# ---------------------------------------------------------------------------
# StreamRecoveryError
# ---------------------------------------------------------------------------


class TestStreamRecoveryError:
    def test_carries_partial_content(self) -> None:
        original = _connection_error()
        err = StreamRecoveryError("Hello, world!", original)
        assert err.partial_content == "Hello, world!"
        assert "13 chars" in str(err)
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
# stream_reply - retry logic
# ---------------------------------------------------------------------------


class TestStreamReplyRetry:
    def test_succeeds_on_first_try(self) -> None:
        """No retry needed - stream completes normally."""
        chunks = [_make_chunk("Hi "), _make_chunk("there")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(chunks)

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Hi ", "there"]
        assert mock_client.chat.completions.create.call_count == 1

    def test_retries_on_pre_stream_connection_error(self) -> None:
        """Connection error before any content -> retry succeeds."""
        chunks = [_make_chunk("Recovered")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            _connection_error(),
            iter(chunks),
        ]

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Recovered"]
        assert mock_client.chat.completions.create.call_count == 2

    def test_retries_on_pre_stream_timeout(self) -> None:
        """Timeout before content -> retry succeeds."""
        chunks = [_make_chunk("OK")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            _timeout_error(),
            iter(chunks),
        ]

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["OK"]

    def test_raises_engine_error_after_max_retries(self) -> None:
        """All retries exhausted -> EngineError."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _connection_error()

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM request failed"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        # Should have retried 3 times total (max_retries + 1)
        assert mock_client.chat.completions.create.call_count == 3

    def test_non_retryable_error_raises_immediately(self) -> None:
        """Non-retryable error -> raise immediately, no retry."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("auth fail")

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM request failed"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        assert mock_client.chat.completions.create.call_count == 1

    def test_account_setup_rate_limit_raises_immediately_with_code(self) -> None:
        """Account/quota 429s need user action, not retry backoff."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _insufficient_balance_error()

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(EngineError) as exc_info,
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        msg = str(exc_info.value)
        assert mock_client.chat.completions.create.call_count == 1
        assert exc_info.value.code == EngineErrorCode.ACCOUNT_SETUP
        assert "Insufficient balance or no resource package. Please recharge." in msg
        assert "Configure provider credentials and select an available model." in msg
        assert "/login" not in msg
        assert "/models" not in msg
        assert "{'error'" not in msg

    def test_queue_full_rate_limit_raises_immediately_with_provider_hint(self) -> None:
        """Shared free-provider queue saturation needs a clear user action."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _queue_full_response_error()

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(EngineError) as exc_info,
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        msg = str(exc_info.value)
        assert mock_client.chat.completions.create.call_count == 1
        assert "Provider is busy" in msg
        assert "free model provider is busy" in msg
        assert "31.16.250.211" not in msg

    def test_mid_stream_failure_with_partial_raises_recovery(self) -> None:
        """Stream drops AFTER content -> StreamRecoveryError with partial."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailingIterator("Hello ")

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        assert exc_info.value.partial_content == "Hello "

    def test_mid_stream_failure_no_content_retries(self) -> None:
        """Stream drops with NO content yet -> safe to retry."""
        good_chunks = [_make_chunk("Retry OK")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            EmptyFailingIterator(),
            iter(good_chunks),
        ]

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), retry=retry))

        assert result == ["Retry OK"]

    def test_abort_event_stops_before_stream(self) -> None:
        """Abort event set before streaming starts -> returns empty."""
        mock_client = MagicMock()
        abort = threading.Event()
        abort.set()

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), abort=abort, retry=retry))

        assert result == []
        mock_client.chat.completions.create.assert_not_called()

    @pytest.mark.flaky(reruns=2, reruns_delay=1)
    def test_abort_event_stops_mid_backoff(self) -> None:
        """Abort event set during backoff -> returns empty."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _connection_error()

        abort = threading.Event()
        threading.Timer(0.01, abort.set).start()

        retry = RetryConfig(max_retries=5, base_delay=10.0, max_delay=30.0)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = list(stream_reply(_config(), _conv(), abort=abort, retry=retry))

        assert result == []
        assert mock_client.chat.completions.create.call_count >= 1

    def test_non_retryable_mid_stream_no_content_raises(self) -> None:
        """Non-retryable mid-stream failure with no content -> raise immediately."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = EmptyFailingIterator(
            error=RuntimeError("unexpected")
        )

        retry = RetryConfig(max_retries=3, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM stream failed"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        assert mock_client.chat.completions.create.call_count == 1

    def test_stream_with_empty_chunks_times_out(self) -> None:
        """A live stream that never produces answer progress fails clearly."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter([_make_chunk()])

        retry = RetryConfig(max_retries=0, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            patch("ai.runtime.engine._openai_stream_progress_timeout_seconds", return_value=1.0),
            patch("ai.runtime.engine.time.monotonic", side_effect=[0.0, 2.0]),
            pytest.raises(EngineError, match="stream stalled without answer"),
        ):
            list(stream_reply(_config(), _conv(), retry=retry))

        assert mock_client.chat.completions.create.call_count == 1


# ---------------------------------------------------------------------------
# get_reply - integration with retry
# ---------------------------------------------------------------------------


class TestGetReply:
    def test_get_reply_normal(self) -> None:
        chunks = [_make_chunk("Hello"), _make_chunk(" world")]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(chunks)

        retry = RetryConfig(max_retries=0, base_delay=0.01)
        with patch("ai.runtime.engine.build_client", return_value=mock_client):
            result = get_reply(_config(), _conv(), retry=retry)

        assert result == "Hello world"

    def test_get_reply_propagates_stream_recovery_error(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailingIterator("Partial ")

        retry = RetryConfig(max_retries=0, base_delay=0.01)
        with (
            patch("ai.runtime.engine.build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            get_reply(_config(), _conv(), retry=retry)

        assert exc_info.value.partial_content == "Partial "


# ---------------------------------------------------------------------------
# Conversation state consistency
# ---------------------------------------------------------------------------


class TestConversationConsistency:
    def test_rollback_on_engine_error(self) -> None:
        """Verify conversation is rolled back on EngineError."""
        config = _config()
        conv = _conv("test prompt")
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-rollback",
            armory_path=_workspace(),
        )

        assert len(conv.messages) == 1

        with (
            patch(
                "harness.chat.orchestrator.TurnOrchestrator._resolve_turn_plan",
                return_value=MagicMock(),
            ),
            patch(
                "harness.chat.orchestrator.TurnOrchestrator._iter_learning_events",
                side_effect=EngineError("boom"),
            ),
            pytest.raises(EngineError),
        ):
            send_user_message(session, "hello")

        # Conversation rolled back to original state
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "test prompt"

    def test_rollback_on_stream_recovery(self) -> None:
        """Verify conversation is rolled back on StreamRecoveryError."""
        config = _config()
        conv = _conv("test prompt")
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-recovery",
            armory_path=_workspace(),
        )

        assert len(conv.messages) == 1

        with (
            patch(
                "harness.chat.orchestrator.TurnOrchestrator._resolve_turn_plan",
                return_value=MagicMock(),
            ),
            patch(
                "harness.chat.orchestrator.TurnOrchestrator._iter_learning_events",
                side_effect=StreamRecoveryError("Partial reply"),
            ),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            send_user_message(session, "hello")

        # Conversation rolled back
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "test prompt"
        # Partial content available in the exception
        assert exc_info.value.partial_content == "Partial reply"
        # Session marked dirty
        assert session.dirty is True

    def test_successful_reply_does_not_rollback(self) -> None:
        """Successful reply adds messages without rollback."""
        config = _config()
        conv = Conversation()
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-success",
            armory_path=_workspace(),
        )

        def fake_iter_events(
            self: TurnOrchestrator,
            user_input: str,
            *,
            abort: threading.Event | None = None,
        ):
            self.session.conversation.add("user", user_input)
            self.session.conversation.add("assistant", "Hello!")
            self.last_reply = "Hello!"
            yield AssistantDeltaEvent("Hello!")

        with patch(
            "harness.chat.orchestrator.TurnOrchestrator.iter_events",
            fake_iter_events,
        ):
            result = send_user_message(session, "Hi")

        assert result == "Hello!"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].content == "Hello!"

    def test_send_user_message_prints_reply_prefix_on_first_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reply labels are printed only when a turn emits output."""
        config = _config()
        conv = Conversation()
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-prefix",
            armory_path=_workspace(),
        )

        def fake_iter_events(
            self: TurnOrchestrator,
            user_input: str,
            *,
            abort: threading.Event | None = None,
        ):
            self.session.conversation.add("user", user_input)
            self.session.conversation.add("assistant", "Hello!")
            self.last_reply = "Hello!"
            yield AssistantDeltaEvent("Hello!")

        with patch(
            "harness.chat.orchestrator.TurnOrchestrator.iter_events",
            fake_iter_events,
        ):
            result = send_user_message(session, "Hi", reply_prefix="Assistant: ")

        assert result == "Hello!"
        assert capsys.readouterr().out == "Assistant: Hello!\n"

    def test_turn_lifecycle_prepares_model_before_request(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = _config()
        conv = Conversation()
        session = ChatSession(
            config=config,
            conversation=conv,
            session_id="test-model-ready",
            armory_path=_workspace(),
        )
        prepared_sessions: list[str] = []

        def fake_ensure_model_ready(active_session: ChatSession) -> bool:
            prepared_sessions.append(active_session.session_id)
            return True

        def fake_iter_prepared_turn(
            self: TurnOrchestrator,
            _prepared: object,
            _user_input: str,
            *,
            abort: threading.Event | None = None,
        ):
            assert abort is None
            self.session.conversation.add("assistant", "Hello!")
            self.last_reply = "Hello!"
            yield AssistantDeltaEvent("Hello!")

        monkeypatch.setattr(
            "harness.chat.turn_lifecycle.ensure_session_model_ready",
            fake_ensure_model_ready,
        )
        monkeypatch.setattr(TurnOrchestrator, "_iter_prepared_turn", fake_iter_prepared_turn)

        events = list(TurnOrchestrator(session).iter_events("Hi"))

        assert prepared_sessions == ["test-model-ready"]
        assert events == [AssistantDeltaEvent("Hello!")]
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hi"


# ---------------------------------------------------------------------------
# Agent loop retry
# ---------------------------------------------------------------------------


class TestAgentLoopRetry:
    def test_iter_agent_events_retries_on_connection_error(self) -> None:
        """Agent event stream retries the API call on connection error."""
        chunks = [_make_chunk("Done")]
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            _connection_error(),
            iter(chunks),
        ]

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with patch("harness.agent.model_stream.build_client", return_value=mock_client):
            events = list(
                iter_agent_events(_config(), _conv(), workspace=_workspace(), retry=retry)
            )

        rendered = "".join(render_turn_event(event) for event in events)
        assert "Acceptance criteria: inspect" in rendered
        assert rendered.endswith("Done")
        assert mock_client.chat.completions.create.call_count == 2

    def test_iter_agent_events_raises_recovery_on_mid_stream_failure(self) -> None:
        """Agent event stream raises StreamRecoveryError when stream drops mid-content."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = FailingIterator("Partial agent ")

        retry = RetryConfig(max_retries=2, base_delay=0.01)
        with (
            patch("harness.agent.model_stream.build_client", return_value=mock_client),
            pytest.raises(StreamRecoveryError) as exc_info,
        ):
            list(iter_agent_events(_config(), _conv(), workspace=_workspace(), retry=retry))

        assert exc_info.value.partial_content == "Partial agent "

    def test_iter_agent_events_exhausts_retries(self) -> None:
        """Agent event stream raises EngineError after all retries exhausted."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _connection_error()

        retry = RetryConfig(max_retries=1, base_delay=0.01)
        with (
            patch("harness.agent.model_stream.build_client", return_value=mock_client),
            pytest.raises(EngineError, match="LLM request failed"),
        ):
            list(iter_agent_events(_config(), _conv(), workspace=_workspace(), retry=retry))

        # Should have retried 2 times total (max_retries + 1)
        assert mock_client.chat.completions.create.call_count == 2
