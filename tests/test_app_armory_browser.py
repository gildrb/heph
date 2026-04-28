"""Tests for the inline Textual armory browser screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from hephaistos.app import armory_browser
from hephaistos.armory.storage import MARKER_FILE, initialize

# Skip the entire module if Textual is not installed.
pytestmark = pytest.mark.skipif(
    armory_browser.ModalScreen is object,  # type: ignore[comparison-overlap]
    reason="Textual is not installed",
)

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Input, Static
except ImportError:
    App = None  # type: ignore[assignment,misc]
    ComposeResult = None  # type: ignore[assignment,misc]
    Input = None  # type: ignore[assignment,misc]
    Static = None  # type: ignore[assignment,misc]


class _ShellApp(App[None]):
    """Minimal Textual app used to host screens under test."""

    def compose(self) -> ComposeResult:
        yield Static("test", id="placeholder")


def _make_dirs(parent: Path, *names: str) -> list[Path]:
    """Create child directories under *parent* and return them."""
    dirs: list[Path] = []
    for name in names:
        d = parent / name
        d.mkdir(parents=True, exist_ok=True)
        dirs.append(d)
    return dirs


def _make_armory(parent: Path, name: str) -> Path:
    """Create an initialized armory under *parent*."""
    path = parent / name
    initialize(path)
    return path


def test_list_child_dirs_skips_hidden_and_files(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "visible", ".hidden")
    (tmp_path / "a-file.txt").touch()

    dirs = armory_browser._list_child_dirs(tmp_path)

    names = [d.name for d in dirs]
    assert "visible" in names
    assert ".hidden" not in names
    assert "a-file.txt" not in names


def test_is_armory_detects_marker(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path, "my-armory")
    plain = tmp_path / "plain-dir"
    plain.mkdir()

    assert armory_browser._is_armory(armory)
    assert not armory_browser._is_armory(plain)


def test_browser_entries_include_parent_and_create(tmp_path: Path) -> None:
    screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)

    entries = screen._entries()

    assert entries[0] == armory_browser._PARENT_LABEL
    assert entries[1] == armory_browser._NEW_ARMORY_LABEL
    assert len(entries) >= 2


def test_browser_entries_without_create_flag(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "alpha", "beta")
    screen = armory_browser.ArmoryBrowserScreen(start=tmp_path, allow_create=False)

    entries = screen._entries()

    assert armory_browser._NEW_ARMORY_LABEL not in entries
    assert "alpha" in entries
    assert "beta" in entries


def test_browser_child_path_returns_correct_dir(tmp_path: Path) -> None:
    alpha, beta = _make_dirs(tmp_path, "alpha", "beta")
    screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
    # entries: 0=parent, 1=new-armory, 2=alpha, 3=beta
    assert screen._child_path(2) == alpha
    assert screen._child_path(3) == beta
    assert screen._child_path(0) is None
    assert screen._child_path(1) is None


def test_browser_screen_compose_and_mount(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "docs")

    async def run_screen() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            path_widget = screen.query_one("#armory-path", armory_browser.Static)
            rendered = path_widget.render()
            assert str(tmp_path.name) in str(rendered)

    asyncio.run(run_screen())


def test_browser_navigates_into_child(tmp_path: Path) -> None:
    child = _make_dirs(tmp_path, "child")[0]

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            # Entry index 2 = "child" (after parent + new-armory)
            screen._selected = 2
            screen._navigate_into()
            await pilot.pause()
            assert screen._current == child

    asyncio.run(run_nav())


def test_browser_navigates_to_parent(tmp_path: Path) -> None:
    child_dir = tmp_path / "child"
    child_dir.mkdir()

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=child_dir)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._selected = 0
            screen._navigate_into()
            await pilot.pause()
            assert screen._current == tmp_path

    asyncio.run(run_nav())


def test_browser_choose_current_dismisses_with_path(tmp_path: Path) -> None:
    result_path: Path | None = None

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_choose() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen._choose_current()
            await pilot.pause()

    asyncio.run(run_choose())
    assert result_path == tmp_path


def test_browser_cancel_dismisses_with_none(tmp_path: Path) -> None:
    result_path: Path | None = "NOT_NONE"  # sentinel

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_cancel() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen._cancel()
            await pilot.pause()

    asyncio.run(run_cancel())
    assert result_path is None


def test_browser_new_armory_creates_and_dismisses(tmp_path: Path) -> None:
    result_path: Path | None = None

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_new() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "test-armory"
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "test-armory", "test-armory")  # type: ignore[arg-type]
            )
            await pilot.pause()

    asyncio.run(run_new())
    assert result_path is not None
    assert result_path.name == "test-armory"
    assert (result_path / MARKER_FILE).exists()


def test_browser_new_armory_empty_name_cancels_create(tmp_path: Path) -> None:
    async def run_empty() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            assert screen._creating is True
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "   "
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "   ", "   ")  # type: ignore[arg-type]
            )
            await pilot.pause()
            assert screen._creating is False

    asyncio.run(run_empty())
