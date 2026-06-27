from __future__ import annotations

from harness._types import parse_json_object_fragment


def test_parse_json_object_fragment_accepts_plain_object() -> None:
    assert parse_json_object_fragment('prefix {"answer": "yes"} suffix') == {"answer": "yes"}


def test_parse_json_object_fragment_accepts_fenced_json() -> None:
    assert parse_json_object_fragment('```json\n{"intent": "chat"}\n```') == {"intent": "chat"}


def test_parse_json_object_fragment_rejects_non_object_json() -> None:
    assert parse_json_object_fragment("```json\n[1, 2]\n```") is None
