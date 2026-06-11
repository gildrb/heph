from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

SHORTCUT_HINT_SEPARATOR = "  "


@dataclass(frozen=True)
class ShortcutHint:
    label: str
    key: str


def shortcut_hint_part(hint: ShortcutHint) -> str:
    label = hint.label.strip().upper()
    key = hint.key.strip().lower()
    if not label:
        return key
    if not key:
        return label
    return f"{label} {key}"


def shortcut_hint_line(hints: Sequence[ShortcutHint]) -> str:
    parts = [shortcut_hint_part(hint) for hint in hints]
    return SHORTCUT_HINT_SEPARATOR.join(parts)
