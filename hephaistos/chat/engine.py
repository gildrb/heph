"""LLM communication engine with streaming support.

Supports any OpenAI-compatible API endpoint, making it LLM-agnostic.
Configure via environment variables:
    HEPHAISTOS_API_KEY   – API key (falls back to OPENAI_API_KEY)
    HEPHAISTOS_BASE_URL  – Base URL for the API (default: https://api.openai.com/v1)
    HEPHAISTOS_MODEL     – Model name (default: gpt-4o-mini)
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass, field

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


@dataclass
class ChatConfig:
    """Configuration for the LLM engine."""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> ChatConfig:
        """Build config from environment variables."""
        api_key = os.environ.get("HEPHAISTOS_API_KEY") or os.environ.get(
            "OPENAI_API_KEY", ""
        )
        if not api_key or not api_key.strip():
            raise EngineError("No API key found. Set HEPHAISTOS_API_KEY or OPENAI_API_KEY.")
        base_url = os.environ.get("HEPHAISTOS_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("HEPHAISTOS_MODEL", "gpt-4o-mini")
        return cls(api_key=api_key.strip(), base_url=base_url, model=model)


class EngineError(Exception):
    """Raised when the engine cannot communicate with the LLM."""


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
    if not config.api_key or not config.api_key.strip():
        raise EngineError("No API key found. Set HEPHAISTOS_API_KEY or OPENAI_API_KEY.")
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def stream_reply(
    config: ChatConfig,
    conversation: Conversation,
) -> Iterator[str]:
    """Send the conversation to the LLM and yield response chunks.

    Each yielded string is a text delta from the streamed response.
    """
    client = _build_client(config)
    try:
        stream = client.chat.completions.create(
            model=config.model,
            messages=conversation.to_api_messages(),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as exc:
        raise EngineError(f"LLM request failed: {exc}") from exc


def get_reply(
    config: ChatConfig,
    conversation: Conversation,
) -> str:
    """Send the conversation and return the full reply as a string."""
    parts: list[str] = []
    for chunk in stream_reply(config, conversation):
        parts.append(chunk)
    return "".join(parts)
