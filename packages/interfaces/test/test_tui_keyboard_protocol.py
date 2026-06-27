"""Tests for terminal TUI compatibility."""

from __future__ import annotations

import asyncio

import pytest
from ai.runtime import ChatConfig
from harness.chat.session import create_plain_session
from interfaces import tui
from interfaces.tui import widgets as tui_widgets
from interfaces.tui.keyboard_protocol import install_textual_modified_key_compat
from interfaces.tui.resize import TuiResizeMixin
from interfaces.tui.widgets import csi_u_key_text, key_event_text
from textual import events
from textual._xterm_parser import XTermParser


def test_tmux_xterm_modified_enter_sequence_decodes_as_shift_enter() -> None:
    install_textual_modified_key_compat()

    key_events = [
        event for event in XTermParser().feed("\x1b[27;2;13~") if isinstance(event, events.Key)
    ]

    assert [(event.key, event.character) for event in key_events] == [("shift+enter", None)]


def test_csi_u_modified_printable_sequence_preserves_character() -> None:
    install_textual_modified_key_compat()

    key_events = [
        event for event in XTermParser().feed("\x1b[47;2u") if isinstance(event, events.Key)
    ]

    assert [(event.key, event.character) for event in key_events] == [("shift+slash", "/")]


def test_plain_ctrl_m_sequence_decodes_as_enter() -> None:
    key_events = [event for event in XTermParser().feed("\r") if isinstance(event, events.Key)]

    assert [(event.key, event.character) for event in key_events] == [("enter", "\r")]


def test_report_all_csi_u_key_names_restore_printable_text() -> None:
    assert csi_u_key_text("shift+a") == "A"
    assert csi_u_key_text("slash") == "/"
    assert csi_u_key_text("shift+slash") == "?"
    assert csi_u_key_text("space") == " "
    assert csi_u_key_text("shift+1") == "!"


def test_key_event_text_prefers_reported_character_over_us_layout_fallback() -> None:
    event = events.Key("shift+7", "/")

    assert key_event_text(event) == "/"


def test_terminal_keyboard_protocol_is_inert_by_default() -> None:
    class Recorder(TuiResizeMixin):
        def __init__(self) -> None:
            self.sequences: list[str] = []
            self._terminal_keyboard_protocol_pushed = False

        def _write_terminal_control(self, sequence: str) -> None:
            self.sequences.append(sequence)

    recorder = Recorder()

    recorder._push_terminal_keyboard_protocol()
    recorder._pop_terminal_keyboard_protocol()

    assert recorder._terminal_keyboard_protocol_pushed is False
    assert recorder.sequences == []


def test_terminal_keyboard_protocol_can_be_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HEPH_TUI_KEYBOARD_PROTOCOL", "1")

    class Recorder(TuiResizeMixin):
        def __init__(self) -> None:
            self.sequences: list[str] = []
            self._terminal_keyboard_protocol_pushed = False

        def _write_terminal_control(self, sequence: str) -> None:
            self.sequences.append(sequence)

    recorder = Recorder()

    recorder._push_terminal_keyboard_protocol()
    recorder._pop_terminal_keyboard_protocol()

    assert recorder._terminal_keyboard_protocol_pushed is False
    assert recorder.sequences == ["\x1b[>1u", "\x1b[<u"]


def test_german_shift_digit_csi_u_key_uses_active_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPH_TUI_KEYBOARD_LAYOUT", "de")
    tui_widgets._clear_csi_u_keyboard_layout_cache()
    try:
        assert csi_u_key_text("shift+7") == "/"
    finally:
        tui_widgets._clear_csi_u_keyboard_layout_cache()


def test_armory_home_notice_uses_neutral_text_style() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        create_plain_session(ChatConfig()),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )

    async def check_home_notice_styles() -> None:
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)
            styles = [
                str(segment.style).lower()
                for line in transcript.lines
                for segment in line
                if "Open:" in segment.text or "materials/" in segment.text
            ]

            assert styles
            assert all("magenta" not in style and "cyan" not in style for style in styles)

    asyncio.run(check_home_notice_styles())
