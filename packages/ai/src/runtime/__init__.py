"""Shared LLM runtime primitives used across Heph packages."""

from runtime._api_types import (
    ApiMessage,
    ContentPart,
    ToolCallDelta,
    UsagePayload,
)
from runtime.config import ChatConfig
from runtime.conversation import Conversation, Message, to_chat_completion_messages
from runtime.delta import CompletionDelta
from runtime.engine import (
    build_client,
    has_configured_access,
    is_keyless_endpoint,
    missing_api_key_message,
    reset_provider_circuit_breaker,
    stream_completion,
    stream_reply,
)
from runtime.errors import EngineError, RetryConfig, StreamRecoveryError
from runtime.messages import api_content_text, message_content_text
from runtime.resilience import (
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
    "reset_provider_circuit_breaker",
    "stream_completion",
    "stream_reply",
    "to_chat_completion_messages",
]
