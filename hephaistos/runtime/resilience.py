"""Circuit breaker for LLM API calls.

Prevents cascading failures when an LLM provider is degraded.  The circuit
breaker wraps API calls and tracks consecutive failures.  After a configurable
threshold it opens, rejecting further calls for a cooldown period before
probing again (half-open state).

States:
    CLOSED    — normal operation, calls pass through
    OPEN      — blocking, calls raise ``CircuitOpenError``
    HALF_OPEN — allowing one probe call to test recovery
"""

from __future__ import annotations

import enum
import threading
import time
from dataclasses import dataclass, field

from hephaistos.diagnostics.crashes import get_meter
from hephaistos.logging import get_logger

_log = get_logger("chat.resilience")
_meter = get_meter("chat.resilience")

_state_gauge = _meter.create_gauge(
    "llm.circuit_breaker.state",
    description="Circuit breaker state: 0=closed, 1=open, 2=half-open",
)


class CircuitState(enum.IntEnum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and rejecting calls."""


@dataclass
class CircuitBreaker:
    """Thread-safe circuit breaker for a single endpoint.

    Args:
        failure_threshold: Consecutive failures before opening.
        recovery_timeout: Seconds to wait before allowing a probe.
        name: Identifier for logging and metrics.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    name: str = "default"

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def allow_request(self) -> bool:
        """Check whether a request is allowed.

        Returns True if the call should proceed, False if the circuit is open.
        In HALF_OPEN state, one probe call is allowed.
        """
        with self._lock:
            self._maybe_transition_to_half_open()

            return self._state != CircuitState.OPEN

    def record_success(self) -> None:
        """Record a successful call — resets failure count and closes circuit."""
        with self._lock:
            prev = self._state
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            if prev != CircuitState.CLOSED:
                _log.info(
                    "circuit closed",
                    extra={"fields": {"circuit": self.name, "prev_state": prev.name}},
                )
                _state_gauge.set(CircuitState.CLOSED, {"circuit": self.name})

    def record_failure(self) -> None:
        """Record a failed call — may open the circuit if threshold reached."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                _log.warning(
                    "circuit reopened (probe failed)",
                    extra={"fields": {"circuit": self.name}},
                )
                _state_gauge.set(CircuitState.OPEN, {"circuit": self.name})
                return

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                _log.warning(
                    "circuit opened",
                    extra={
                        "fields": {
                            "circuit": self.name,
                            "failure_count": self._failure_count,
                            "threshold": self.failure_threshold,
                        }
                    },
                )
                _state_gauge.set(CircuitState.OPEN, {"circuit": self.name})

    def reset(self) -> None:
        """Reset to CLOSED state, clearing all failure tracking."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0

    def _maybe_transition_to_half_open(self) -> None:
        """Transition OPEN → HALF_OPEN if recovery_timeout has elapsed."""
        if self._state != CircuitState.OPEN:
            return
        elapsed = time.monotonic() - self._last_failure_time
        if elapsed >= self.recovery_timeout:
            self._state = CircuitState.HALF_OPEN
            _log.info(
                "circuit half-open (probing)",
                extra={"fields": {"circuit": self.name}},
            )
            _state_gauge.set(CircuitState.HALF_OPEN, {"circuit": self.name})


def is_network_error(exc: BaseException) -> bool:
    """Return True when the exception is a network connectivity error.

    Distinguishes network failures from auth errors, rate limits, and
    server-side issues so the UI can show appropriate offline guidance.
    """
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, ConnectionError | OSError | TimeoutError):
            return True
        exc_name = type(current).__name__
        if exc_name in ("APIConnectionError", "APITimeoutError"):
            return True
        current = current.__cause__
    return False


def offline_message(provider_name: str) -> str:
    """Return a friendly message for when the LLM API is unreachable."""
    return (
        f"Can't reach {provider_name}. "
        "You're offline — but you can still:\n"
        "  · Review vocabulary with /vocab drill\n"
        "  · Browse materials with /materials\n"
        "  · Export the chat with /export\n"
        "  · Check /stats for session progress\n"
        "\n"
        "Hephaistos will reconnect automatically when connectivity returns."
    )
