"""Tests for the optional Textual shell wrapper."""

from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.app import tui
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession


def _plain_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(base_url="https://example.test", model="test-model"),
        conversation=conversation,
        session_id="session-test",
    )


def test_session_status_for_plain_session() -> None:
    status = tui._status_lines(_plain_session())  # type: ignore[reportPrivateUsage]

    assert "test-model" in status
    assert "armory" in status
    assert "enter" in status


def test_command_help_is_command_first() -> None:
    help_text = tui._command_help()  # type: ignore[reportPrivateUsage]

    assert "/help" in help_text
    assert "/sources [query]" in help_text


def test_source_listing_filters_with_fuzzy_match() -> None:
    session = _plain_session()
    session.source_files = ("source/binary-search.md", "library/calculus.md")
    session.source_file_count = 2

    listing = tui._source_listing(session, "binary")  # type: ignore[reportPrivateUsage]

    assert listing.splitlines()[0] == "@source/binary-search.md"


def test_run_tui_reports_missing_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui, "Markdown", None)

    with pytest.raises(tui.TuiDependencyError) as exc_info:
        tui.run_tui(_plain_session())

    message = str(exc_info.value)
    assert "repository root" in message
    assert "uv run --group tui heph tui" in message
    assert "uv run --project" not in message
    assert "-m pip install -e '.[tui]'" in message


def test_run_tui_for_path_resolves_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_session: ChatSession | None = None

    def fake_resolve(path: str) -> ChatSession:
        assert path == str(tmp_path)
        return _plain_session()

    def fake_run_tui(session: ChatSession | None = None) -> None:
        nonlocal captured_session
        captured_session = session

    monkeypatch.setattr(tui, "resolve_armory_session", fake_resolve)
    monkeypatch.setattr(tui, "run_tui", fake_run_tui)

    tui.run_tui_for_path(tmp_path)

    assert captured_session is not None
