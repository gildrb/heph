from __future__ import annotations

from ai.runtime import ContentPart
from ai.runtime.messages import api_content_text, message_content_text


def test_api_content_text_preserves_agent_part_concatenation() -> None:
    parts: list[ContentPart] = [
        {"type": "input_text", "text": "alpha"},
        {"type": "input_text", "content": "beta"},
    ]

    assert api_content_text(parts) == "alphabeta"


def test_message_content_text_keeps_runtime_part_boundaries_readable() -> None:
    content = [
        {"type": "input_text", "text": "alpha"},
        {"type": "input_text", "content": "beta"},
        {"type": "ignored", "image_url": "https://example.invalid/image.png"},
    ]

    assert message_content_text(content) == "alpha\nbeta"


def test_message_content_text_handles_empty_and_scalar_content() -> None:
    assert message_content_text(None) == ""
    assert message_content_text("plain") == "plain"
    assert message_content_text(42) == "42"
