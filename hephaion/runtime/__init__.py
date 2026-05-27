"""Shared LLM runtime primitives used across Heph packages."""

from hephaion.runtime._api_types import (
    ApiMessage,
    ContentPart,
    ToolCallDelta,
    UsagePayload,
)
from hephaion.runtime.engine import (
    ChatConfig,
    CompletionDelta,
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    StreamRecoveryError,
    build_client,
    has_configured_access,
    is_keyless_endpoint,
    missing_api_key_message,
    stream_completion,
    stream_reply,
    to_chat_completion_messages,
)
from hephaion.runtime.messages import api_content_text, message_content_text
from hephaion.runtime.resilience import (
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
    "api_content_text",
    "build_client",
    "has_configured_access",
    "is_keyless_endpoint",
    "is_network_error",
    "message_content_text",
    "missing_api_key_message",
    "offline_message",
    "stream_completion",
    "stream_reply",
    "to_chat_completion_messages",
]
