"""Tests for terminal keyboard protocol compatibility."""

from __future__ import annotations

from textual import events
from textual._xterm_parser import XTermParser

from hephaion.tui.keyboard_protocol import install_textual_modified_key_compat
from hephaion.tui.widgets import csi_u_key_text


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
