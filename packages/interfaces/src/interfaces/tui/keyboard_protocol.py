"""Terminal keyboard protocol compatibility for Textual."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from textual.events import Key
else:
    Key = object

try:
    import textual._keyboard_protocol as _imported_keyboard_protocol_module
    import textual._xterm_parser as _imported_xterm_parser_module
    import textual.events as _imported_textual_events_module
    import textual.keys as _imported_textual_keys_module
except ImportError:
    _FUNCTIONAL_KEYS: Mapping[str, str] = {}
    _TextualKey: type[Key] | None = None
    _TextualXTermParser: type[object] | None = None
    _textual_character_to_key: Callable[[str], str] | None = None
else:
    _FUNCTIONAL_KEYS: Mapping[str, str] = cast(
        "Mapping[str, str]",
        _imported_keyboard_protocol_module.FUNCTIONAL_KEYS,
    )
    _TextualKey: type[Key] | None = cast("type[Key]", _imported_textual_events_module.Key)
    _TextualXTermParser: type[object] | None = cast(
        "type[object]",
        _imported_xterm_parser_module.XTermParser,
    )
    _textual_character_to_key: Callable[[str], str] | None = cast(
        "Callable[[str], str]",
        _imported_textual_keys_module._character_to_key,
    )

_XTERM_MODIFIED_KEY_RE = re.compile(r"\x1b\[27;(?P<modifier>\d+);(?P<codepoint>\d+)~\Z")
_CSI_U_KEY_RE = re.compile(r"\x1b\[(?P<codepoint>\d+)(?:;(?P<modifier>\d+))?u\Z")
_XTERM_MODIFIERS = ("shift", "alt", "ctrl")
_CSI_U_MODIFIERS = ("shift", "alt", "ctrl", "super", "hyper", "meta")
_installed = False


class _XTermParserClass(Protocol):
    _sequence_to_key_events: Callable[[object, str, bool], Iterable[Key]]


def install_textual_modified_key_compat() -> None:
    """Teach Textual 8.x to decode tmux/xterm modified printable key sequences."""

    global _installed  # noqa: PLW0603
    if _installed or _TextualXTermParser is None:
        return

    parser_class = cast("_XTermParserClass", _TextualXTermParser)
    original_sequence_to_key_events = parser_class._sequence_to_key_events

    def _sequence_to_key_events(
        parser: object,
        sequence: str,
        alt: bool = False,
    ) -> Iterable[Key]:
        event = _csi_u_key_event(sequence) or _xterm_modified_key_event(sequence)
        if event is not None:
            yield event
            return
        yield from original_sequence_to_key_events(parser, sequence, alt)

    parser_class._sequence_to_key_events = _sequence_to_key_events
    _installed = True


def _xterm_modified_key_event(sequence: str) -> Key | None:
    if _TextualKey is None:
        return None
    match = _XTERM_MODIFIED_KEY_RE.fullmatch(sequence)
    if match is None:
        return None

    modifier = int(match.group("modifier"))
    codepoint = int(match.group("codepoint"))
    key = _base_key(codepoint)
    if key is None:
        return None

    modifier_tokens = _modifier_tokens(modifier, _XTERM_MODIFIERS)
    if not modifier_tokens:
        return None
    modifier_tokens.sort()
    return _TextualKey("+".join((*modifier_tokens, key.lower())), None)


def _csi_u_key_event(sequence: str) -> Key | None:
    if _TextualKey is None:
        return None
    match = _CSI_U_KEY_RE.fullmatch(sequence)
    if match is None:
        return None

    codepoint = int(match.group("codepoint"))
    key = _base_key(codepoint)
    if key is None:
        return None

    raw_modifier = match.group("modifier")
    modifier_tokens = _modifier_tokens(int(raw_modifier), _CSI_U_MODIFIERS) if raw_modifier else []
    modifier_tokens.sort()
    character = _csi_u_printable_character(codepoint, modifier_tokens)
    return _TextualKey("+".join((*modifier_tokens, key.lower())), character)


def _csi_u_printable_character(codepoint: int, modifier_tokens: list[str]) -> str | None:
    if _FUNCTIONAL_KEYS.get(f"{codepoint}u"):
        return None
    try:
        character = chr(codepoint)
    except ValueError:
        return None
    if not character.isprintable():
        return None
    if not modifier_tokens:
        return character
    if modifier_tokens == ["shift"] and not character.isalnum():
        return character
    return None


def _modifier_tokens(modifier: int, modifier_names: tuple[str, ...]) -> list[str]:
    modifier_bits = modifier - 1
    return [
        modifier_name
        for bit, modifier_name in enumerate(modifier_names)
        if modifier_bits & (1 << bit)
    ]


def _base_key(codepoint: int) -> str | None:
    if key := _FUNCTIONAL_KEYS.get(f"{codepoint}u"):
        return key
    try:
        character = chr(codepoint)
    except ValueError:
        return None
    if _textual_character_to_key is None:
        return character
    return _textual_character_to_key(character)
