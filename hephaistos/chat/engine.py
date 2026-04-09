"""LLM communication engine with streaming support.

Supports any OpenAI-compatible API endpoint, making it LLM-agnostic.
Configure via environment variables:
    HEPHAISTOS_API_KEY   - API key (falls back to OPENAI_API_KEY)
    HEPHAISTOS_BASE_URL  - Base URL for the API (default: https://api.openai.com/v1)
    HEPHAISTOS_MODEL     - Model name (default: gpt-4o-mini)

Streaming error recovery:
    Transient failures (connection drops, timeouts, server errors) are
    retried automatically with exponential backoff.  If a retry fails
    after content has already been streamed to the caller, a
    ``StreamRecoveryError`` is raised carrying the partial response so
    that the caller can decide how to proceed.
"""

from __future__ import annotations

import os
import random
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessageParam

from hephaistos.logging import Timer, get_logger
from hephaistos.providers.model_support import is_supported_model_for_endpoint

_log = get_logger("chat.engine")


@dataclass
class ChatConfig:
    """Configuration for the LLM engine.

    API keys are resolved lazily at call time from the OS keychain →
    environment variable → volatile in-memory store.  The ``api_key`` field
    is kept for backward compatibility but should not be used to store raw
    keys persistently.  Use the ``resolved_api_key`` property instead.
    """

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    rag_context_budget: int = 2000
    _provider_slug: str = field(default="", repr=False)
    _provider_env: str = field(default="", repr=False)

    @property
    def resolved_api_key(self) -> str:
        """Resolve the API key via keychain → env → volatile → raw fallback."""
        if self._provider_slug:
            from hephaistos.providers.keyring_store import resolve_key

            key = resolve_key(self._provider_slug, self._provider_env)
            if key:
                return key
        env_key = os.environ.get("HEPHAISTOS_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        if env_key.strip():
            return env_key.strip()
        return self.api_key



class EngineError(Exception):
    """Raised when the engine cannot communicate with the LLM."""


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


@dataclass
class RetryConfig:
    """Configuration for automatic retry of transient failures."""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds



_RETRYABLE_TYPES = (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class Conversation:
    """An ordered list of messages forming a conversation."""

    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_api_messages(self) -> list[ChatCompletionMessageParam]:
        """Convert to the format expected by the OpenAI client."""
        return [
            {"role": msg.role, "content": msg.content}  # type: ignore[misc]
            for msg in self.messages
        ]


def _build_client(config: ChatConfig) -> OpenAI:
    """Create an OpenAI client from the given config."""
    if not is_supported_model_for_endpoint(config.model, config.base_url):
        raise EngineError(f"Model unavailable for endpoint: {config.model}")
    api_key = config.resolved_api_key
    if not api_key:
        raise EngineError(
            "No API key found. Set one via /api key, environment variable, or the OS keychain."
        )
    return OpenAI(api_key=api_key, base_url=config.base_url)


def is_retryable_error(exc: Exception) -> bool:
    """Return True if *exc* is a transient error worth retrying."""
    return isinstance(exc, _RETRYABLE_TYPES)


def _wait_backoff(
    attempt: int,
    config: RetryConfig,
    abort: threading.Event | None = None,
) -> bool:
    """Sleep with exponential backoff + jitter.  Returns False if aborted."""
    delay = min(config.base_delay * (2**attempt), config.max_delay)
    jitter = random.uniform(0, delay * 0.5)
    if abort is not None:
        return not abort.wait(timeout=jitter)
    time.sleep(jitter)
    return True


def stream_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
) -> Iterator[str]:
    """Send the conversation to the LLM and yield response chunks.

    Each yielded string is a text delta from the streamed response.
    If *abort* is provided and becomes set, the iterator stops early.

    Transient errors (connection drops, timeouts, server errors) are
    retried automatically with exponential backoff.  If a failure occurs
    *after* content has already been yielded, a
    :class:`StreamRecoveryError` is raised carrying the partial text.
    """
    retry = retry or RetryConfig()
    msg_count = len(conversation.messages)
    _log.debug(
        "stream_reply start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": msg_count,
                "max_tokens": config.max_tokens,
                "max_retries": retry.max_retries,
            }
        },
    )

    client = _build_client(config)
    last_error: Exception | None = None

    for attempt in range(retry.max_retries + 1):
        if abort is not None and abort.is_set():
            return

        timer = Timer()
        try:
            with timer:
                stream = client.chat.completions.create(
                    model=config.model,
                    messages=conversation.to_api_messages(),
                    max_tokens=config.max_tokens,
                    stream=True,
                )
        except Exception as exc:
            last_error = exc
            _log.warning(
                "stream_reply request failed (attempt %d/%d)",
                attempt + 1,
                retry.max_retries + 1,
                extra={"fields": {"error": str(exc), "latency_ms": timer.ms}},
            )
            if is_retryable_error(exc) and attempt < retry.max_retries:
                if not _wait_backoff(attempt, retry, abort):
                    return  # aborted during backoff
                continue
            raise EngineError(f"LLM request failed: {exc}") from exc
        partial_content = ""
        try:
            for chunk in stream:
                if abort is not None and abort.is_set():
                    stream.close()
                    _log.info(
                        "stream_reply aborted",
                        extra={
                            "fields": {
                                "model": config.model,
                                "latency_ms": timer.ms,
                            }
                        },
                    )
                    return
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    partial_content += delta.content
                    yield delta.content
        except Exception as exc:
            _log.error(
                "stream_reply mid-stream failure (attempt %d/%d, %d chars received)",
                attempt + 1,
                retry.max_retries + 1,
                len(partial_content),
                extra={"fields": {"error": str(exc), "latency_ms": timer.ms}},
            )
            # If we already streamed content, we cannot cleanly retry
            # (the caller has already received partial output).  Raise
            # a recovery error so the caller can decide what to do.
            if partial_content:
                raise StreamRecoveryError(partial_content, exc) from exc
            # No content yet — safe to retry
            last_error = exc
            if is_retryable_error(exc) and attempt < retry.max_retries:
                if not _wait_backoff(attempt, retry, abort):
                    return
                continue
            raise EngineError(f"LLM stream failed: {exc}") from exc
        _log.info(
            "stream_reply complete",
            extra={
                "fields": {
                    "model": config.model,
                    "latency_ms": timer.ms,
                    "message_count": msg_count,
                }
            },
        )
        return
    raise EngineError(
        f"LLM request failed after {retry.max_retries + 1} attempts: {last_error}"
    ) from last_error


def get_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
) -> str:
    """Send the conversation and return the full reply as a string.

    Also prints streamed chunks to stdout in real time.
    On :class:`StreamRecoveryError` the partial text is preserved in the
    exception for the caller to inspect.
    """
    parts: list[str] = []
    try:
        for chunk in stream_reply(config, conversation, abort=abort, retry=retry):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            parts.append(chunk)
    except StreamRecoveryError:
        if parts:
            sys.stdout.write("\n")
            sys.stdout.flush()
        raise
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(parts)
