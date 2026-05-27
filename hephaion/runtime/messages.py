from __future__ import annotations

from hephaion._types import is_string_mapping
from hephaion.runtime._api_types import ContentPart


def message_content_text(content: object) -> str:
    return _content_parts_text(content, separator="\n")


def api_content_text(content: str | None | list[ContentPart]) -> str:
    return _content_parts_text(content, separator="")


def _content_parts_text(content: object, *, separator: str) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[str] = []
    for item in content:
        if not is_string_mapping(item):
            continue
        item_text = item.get("text", item.get("content", ""))
        if isinstance(item_text, str) and item_text:
            parts.append(item_text)
    return separator.join(parts)
