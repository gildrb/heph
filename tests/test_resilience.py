"""Tests for the circuit breaker in hephaistos.chat.resilience."""

from __future__ import annotations

import time

from hephaistos.chat.resilience import CircuitBreaker, CircuitState


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
