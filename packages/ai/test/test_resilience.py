"""Tests for runtime circuit-breaker helpers."""

from __future__ import annotations

import time

from runtime.resilience import (
    CircuitBreaker,
    CircuitState,
    is_network_error,
    offline_message,
)


class TestCircuitBreaker:
    def test_starts_closed(self) -> None:
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, name="test")
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_success_resets_to_closed(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, name="test")
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_transitions_to_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, name="test")
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_half_open_probe_success_closes(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, name="test")
        cb.record_failure()
        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_probe_failure_reopens(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, name="test")
        cb.record_failure()
        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_failure_below_threshold_stays_closed(self) -> None:
        cb = CircuitBreaker(failure_threshold=5, name="test")
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_independent_instances(self) -> None:
        cb1 = CircuitBreaker(failure_threshold=1, name="provider-a")
        cb2 = CircuitBreaker(failure_threshold=1, name="provider-b")

        cb1.record_failure()
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.CLOSED


class TestIsNetworkError:
    def test_connection_error_is_network(self) -> None:
        assert is_network_error(ConnectionError("refused")) is True

    def test_timeout_is_network(self) -> None:
        assert is_network_error(TimeoutError("timed out")) is True

    def test_os_error_is_network(self) -> None:
        assert is_network_error(OSError("network unreachable")) is True

    def test_runtime_error_is_not_network(self) -> None:
        assert is_network_error(RuntimeError("something else")) is False

    def test_value_error_is_not_network(self) -> None:
        assert is_network_error(ValueError("bad input")) is False

    def test_chained_os_error_is_network(self) -> None:
        inner = OSError("connection reset")
        exc = RuntimeError("wrap")
        exc.__cause__ = inner
        assert is_network_error(exc) is True

    def test_api_connection_error_by_name(self) -> None:
        exc_cls = type("APIConnectionError", (Exception,), {})
        exc = exc_cls.__new__(exc_cls)
        exc.__cause__ = None
        assert is_network_error(exc) is True

    def test_api_timeout_error_by_name(self) -> None:
        exc_cls = type("APITimeoutError", (Exception,), {})
        exc = exc_cls.__new__(exc_cls)
        exc.__cause__ = None
        assert is_network_error(exc) is True


class TestOfflineMessage:
    def test_mentions_provider(self) -> None:
        msg = offline_message("OpenRouter")
        assert "OpenRouter" in msg

    def test_mentions_offline_features(self) -> None:
        msg = offline_message("OpenRouter")
        assert "/vocabulary" in msg
        assert "/materials" in msg
        assert "/export" in msg
        assert "/status" in msg

    def test_mentions_reconnect(self) -> None:
        msg = offline_message("OpenRouter")
        assert "reconnect" in msg.lower()
