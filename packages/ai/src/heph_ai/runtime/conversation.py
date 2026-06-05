"""Conversation message containers for runtime requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from heph_ai.runtime._api_types import ApiMessage

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam


@dataclass
class Message:
    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)
    _api_cache: list[ApiMessage] | None = field(default=None, init=False, repr=False)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self._api_cache = None

    def to_api_messages(self) -> list[ApiMessage]:
        if self._api_cache is not None:
            return self._api_cache
        self._api_cache = [{"role": msg.role, "content": msg.content} for msg in self.messages]
        return self._api_cache


def to_chat_completion_messages(messages: list[ApiMessage]) -> list[ChatCompletionMessageParam]:
    return cast("list[ChatCompletionMessageParam]", messages)
