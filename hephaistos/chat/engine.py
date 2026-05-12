"""Compatibility exports for the shared LLM runtime.

New code should import these primitives from :mod:`hephaistos.runtime`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from hephaistos.runtime import (
    ChatConfig,
    CompletionDelta,
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    is_keyless_endpoint,
    missing_api_key_message,
    to_chat_completion_messages,
)
from hephaistos.runtime import engine as _runtime_engine
from hephaistos.runtime import (
    stream_completion as _runtime_stream_completion,
)

_circuit_breaker = _runtime_engine._circuit_breaker
_wait_backoff = _runtime_engine._wait_backoff
is_retryable_error = _runtime_engine.is_retryable_error
resolve_key = _runtime_engine.resolve_key


def stream_completion(
    config: ChatConfig,
    conversation: Conversation,
    *,
    tools: list[dict[str, object]] | None = None,
    abort: object | None = None,
    retry: RetryConfig | None = None,
    client_factory: Callable[[ChatConfig], object] | None = None,
) -> Iterator[CompletionDelta]:
    """Compatibility wrapper that keeps ``chat.engine.build_client`` patchable."""
    yield from _runtime_stream_completion(
        config,
        conversation,
        tools=tools,
        abort=abort,  # ty:ignore[invalid-argument-type]
        retry=retry,
        client_factory=client_factory or _runtime_engine.build_client,  # ty:ignore[invalid-argument-type]
    )


def stream_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: object | None = None,
    retry: RetryConfig | None = None,
) -> Iterator[str]:
    """Yield assistant text content only."""
    for delta in stream_completion(config, conversation, abort=abort, retry=retry):
        if delta.content:
            yield delta.content


def get_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    retry: RetryConfig | None = None,
) -> str:
    """Return a complete non-streaming assistant reply."""
    return "".join(stream_reply(config, conversation, retry=retry))


__all__ = [
    "ChatConfig",
    "CompletionDelta",
    "Conversation",
    "EngineError",
    "Message",
    "RetryConfig",
    "StreamRecoveryError",
    "_circuit_breaker",
    "_wait_backoff",
    "build_client",
    "get_reply",
    "is_keyless_endpoint",
    "is_retryable_error",
    "missing_api_key_message",
    "resolve_key",
    "stream_completion",
    "stream_reply",
    "to_chat_completion_messages",
]
