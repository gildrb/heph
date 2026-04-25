"""Tests for the directory browser in menu.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

import hephaistos.app.menu as menu_mod
from hephaistos.app import menu


def test_browse_directory_choose_current(tmp_path: Path) -> None:
    """Pressing 'c' should return the current directory."""
    start = tmp_path / "start"
    start.mkdir()

    with create_pipe_input() as pipe_input:
        pipe_input.send_text("c")
        result = menu._browse_with_prompt_toolkit(  # type: ignore[reportPrivateUsage]
            "Test Browse",
            start,
            input_obj=pipe_input,
            output_obj=DummyOutput(),
        )

    assert result is not None
    assert result.resolve() == start.resolve()


def test_browse_directory_cancel(tmp_path: Path) -> None:
    """Pressing 'q' should return None."""
    start = tmp_path / "start"
    start.mkdir()

    with create_pipe_input() as pipe_input:
        pipe_input.send_text("q")
        result = menu._browse_with_prompt_toolkit(  # type: ignore[reportPrivateUsage]
            "Test Browse",
            start,
            input_obj=pipe_input,
            output_obj=DummyOutput(),
        )

    assert result is None


def test_browse_directory_navigate_into_child(tmp_path: Path) -> None:
    """Pressing down then enter navigates into a child directory."""
    start = tmp_path / "start"
    start.mkdir()
    child = start / "subdir"
    child.mkdir()

    with create_pipe_input() as pipe_input:
        # down (select child), enter (descend), c (choose)
        pipe_input.send_text("\x1b[B\r\x1b[Bc")
        result = menu._browse_with_prompt_toolkit(  # type: ignore[reportPrivateUsage]
            "Test Browse",
            start,
            input_obj=pipe_input,
            output_obj=DummyOutput(),
        )

    # After descending into child, pressing 'c' should choose child
    assert result is not None
    assert result.resolve() == child.resolve()


def test_browse_directory_parent_entry(tmp_path: Path) -> None:
    """The parent entry (..) should be listed first."""
    start = tmp_path / "start"
    start.mkdir()
    entries = menu._format_browser("Test", start, ["..  (parent)", "child"], 0)  # type: ignore[reportPrivateUsage]
    # Just verify it doesn't crash and has content
    assert any("..  (parent)" in frag[1] for frag in entries)


def test_list_child_dirs_skips_hidden(tmp_path: Path) -> None:
    """Hidden directories (starting with .) should be excluded."""
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / ".hidden").mkdir()
    (parent / "visible").mkdir()

    dirs = menu._list_child_dirs(parent)  # type: ignore[reportPrivateUsage]
    names = [d.name for d in dirs]
    assert "visible" in names
    assert ".hidden" not in names


def test_list_child_dirs_handles_permission_error(tmp_path: Path) -> None:
    """PermissionError should return empty list instead of crashing."""
    parent = tmp_path / "parent"
    parent.mkdir()

    def _raising_iterdir(_self: Path):
        raise PermissionError("no access")

    original = menu_mod.Path.iterdir
    try:
        menu_mod.Path.iterdir = _raising_iterdir  # type: ignore[assignment]
        dirs = menu._list_child_dirs(parent)  # type: ignore[reportPrivateUsage]
        assert dirs == []
    finally:
        menu_mod.Path.iterdir = original  # type: ignore[assignment]


def test_browse_with_prompt_fallback_choose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-TTY fallback: choosing the current dir returns it."""
    start = tmp_path / "start"
    start.mkdir()

    monkeypatch.setattr(
        "hephaistos.app.menu.direct_input",
        lambda _prompt="": "c",  # type: ignore[reportUnknownLambdaType]
    )
    result = menu._browse_with_prompt("Test", start)  # type: ignore[reportPrivateUsage]
    assert result is not None
    assert result.resolve() == start.resolve()


def test_browse_with_prompt_fallback_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-TTY fallback: pressing q returns None."""
    start = Path("/tmp")
    monkeypatch.setattr(
        "hephaistos.app.menu.direct_input",
        lambda _prompt="": "q",  # type: ignore[reportUnknownLambdaType]
    )
    result = menu._browse_with_prompt("Test", start)  # type: ignore[reportPrivateUsage]
    assert result is None


def test_browse_directory_public_api_non_tty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """browse_directory() should use text fallback when not in a TTY."""
    start = tmp_path / "start"
    start.mkdir()
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.setattr(
        "hephaistos.app.menu.direct_input",
        lambda _prompt="": "c",  # type: ignore[reportUnknownLambdaType]
    )

    result = menu.browse_directory("Test", start)
    assert result is not None
    assert result.resolve() == start.resolve()
