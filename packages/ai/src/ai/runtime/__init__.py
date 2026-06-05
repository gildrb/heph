"""Shared LLM runtime primitives used across Heph packages."""

from ai.runtime._api_types import (
    ApiMessage,
    ContentPart,
    ToolCallDelta,
    UsagePayload,
)
from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation, Message, to_chat_completion_messages
from ai.runtime.delta import CompletionDelta
from ai.runtime.engine import (
    build_client,
    has_configured_access,
    is_keyless_endpoint,
    missing_api_key_message,
    reset_provider_circuit_breaker,
    stream_completion,
    stream_reply,
)
from ai.runtime.errors import EngineError, RetryConfig, StreamRecoveryError
from ai.runtime.messages import api_content_text, message_content_text
from ai.runtime.resilience import (
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
