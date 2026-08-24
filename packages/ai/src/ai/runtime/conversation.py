"""Durable conversation messages and provider request conversion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from ai.runtime._api_types import ApiMessage
from ai.runtime.messages import api_content_text

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, object] = field(default_factory=dict)

    def to_api_message(self) -> ApiMessage:
        message: ApiMessage = {"role": self.role, "content": self.content}
        message.update(self.metadata)  # type: ignore[arg-type]
        return message


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def add_api_message(self, message: ApiMessage) -> None:
        metadata = {key: value for key, value in message.items() if key not in {"role", "content"}}
        content = api_content_text(message.get("content"))
        if not content and message.get("tool_calls"):
            content = "[tool calls]"
        self.messages.append(Message(str(message["role"]), content, metadata))

    def to_api_messages(self) -> list[ApiMessage]:
        return [message.to_api_message() for message in self.messages]


def to_chat_completion_messages(messages: list[ApiMessage]) -> list[ChatCompletionMessageParam]:
    return cast("list[ChatCompletionMessageParam]", messages)
