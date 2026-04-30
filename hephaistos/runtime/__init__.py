"""Shared LLM runtime primitives used across Hephaistos packages."""

from hephaistos.runtime._api_types import (
    ApiMessage,
    ContentPart,
    ToolCallDelta,
    UsagePayload,
)
from hephaistos.runtime.engine import (
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
    stream_completion,
    stream_reply,
    to_chat_completion_messages,
)
from hephaistos.runtime.resilience import (
    CircuitBreaker,
    CircuitState,
    is_network_error,
    offline_message,
)

__all__ = [
    "ApiMessage",
    "ChatConfig",
    "CircuitBreaker",
    "CircuitState",
    "CompletionDelta",
    "ContentPart",
    "Conversation",
    "EngineError",
    "Message",
    "RetryConfig",
    "StreamRecoveryError",
    "ToolCallDelta",
    "UsagePayload",
    "build_client",
    "is_keyless_endpoint",
    "is_network_error",
    "missing_api_key_message",
    "offline_message",
    "stream_completion",
    "stream_reply",
    "to_chat_completion_messages",
]
