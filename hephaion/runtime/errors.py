"""Runtime engine error types."""

from __future__ import annotations

from dataclasses import dataclass


class EngineError(Exception):
    pass


class StreamRecoveryError(EngineError):
    """Raised when a streaming response was interrupted.

    Carries the partial content that was already received (and possibly
    displayed) so that callers can preserve it or retry.
    """

    def __init__(self, partial_content: str, last_error: Exception | None = None) -> None:
        self.partial_content = partial_content
        msg = f"Stream interrupted after {len(partial_content)} chars"
        if last_error:
            msg += f": {last_error}"
        super().__init__(msg)
        self.__cause__ = last_error


class _RetryOpenAIStreamError(Exception):
    def __init__(self, cause: Exception) -> None:
        super().__init__(str(cause))
        self.cause = cause


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
