"""Small model-call helpers used by chat orchestration services."""

from __future__ import annotations

from _types import parse_json_object_fragment
from heph_ai.logging import get_logger
from heph_ai.runtime.config import ChatConfig
from heph_ai.runtime.conversation import Conversation
from heph_ai.runtime.engine import build_client, stream_completion
from heph_ai.runtime.errors import EngineError, RetryConfig

_log = get_logger("chat.model_text")


def _stream_one_shot_model_text(
    config: ChatConfig,
    conversation: Conversation,
    *,
    raise_errors: bool = False,
) -> str:
    parts: list[str] = []
    try:
        parts.extend(
            delta.content
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
                client_factory=build_client,
            )
            if delta.content
        )
    except EngineError:
        if raise_errors:
            raise
        return ""
    return "".join(parts)


def _model_json_payload(
    config: ChatConfig | None,
    *,
    system_prompt: str,
    user_prompt: str,
    raise_errors: bool = False,
) -> dict[str, object] | None:
    if config is None or not config.base_url or not config.model:
        return None
    conversation = Conversation()
    conversation.add("system", system_prompt)
    conversation.add("user", user_prompt)
    return parse_json_object_fragment(
        _stream_one_shot_model_text(config, conversation, raise_errors=raise_errors)
    )
