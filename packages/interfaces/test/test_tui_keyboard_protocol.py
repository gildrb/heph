"""Tests for terminal TUI compatibility."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from ai.runtime import ChatConfig
from hephaion.chat.session import create_plain_session
from interfaces import tui
from interfaces.tui.keyboard_protocol import install_textual_modified_key_compat
from interfaces.tui.widgets import csi_u_key_text
from textual import events
from textual._xterm_parser import XTermParser


def test_tmux_xterm_modified_enter_sequence_decodes_as_shift_enter() -> None:
    install_textual_modified_key_compat()

    key_events = [
        event for event in XTermParser().feed("\x1b[27;2;13~") if isinstance(event, events.Key)
    ]

    assert [(event.key, event.character) for event in key_events] == [("shift+enter", None)]


def test_report_all_csi_u_key_names_restore_printable_text() -> None:
    assert csi_u_key_text("shift+a") == "A"
    assert csi_u_key_text("slash") == "/"
    assert csi_u_key_text("shift+slash") == "?"
    assert csi_u_key_text("space") == " "
    assert csi_u_key_text("shift+1") == "!"


def test_armory_home_notice_does_not_use_rich_path_highlight_colors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")
    known = [tmp_path / ".armories" / "sample-1778273613"]
    monkeypatch.setattr("interfaces.tui.display_text.load_available_armories", lambda: known)

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
                if ".armories" in segment.text or "1778273613" in segment.text
            ]

            assert styles
            assert all("magenta" not in style and "cyan" not in style for style in styles)

    asyncio.run(check_home_notice_styles())
