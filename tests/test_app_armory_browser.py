"""Tests for the inline Textual armory browser screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from hephaistos.armory.storage import MARKER_FILE, initialize
from hephaistos.tui import armory_browser

# Skip the entire module if Textual is not installed.
pytestmark = pytest.mark.skipif(
    armory_browser.ModalScreen is object,  # type: ignore[comparison-overlap]
    reason="Textual is not installed",
)

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Input, OptionList, Static
except ImportError:
    App = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    ComposeResult = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Input = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Static = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]


class _ShellApp(App[None]):
    """Minimal Textual app used to host screens under test."""

    def compose(self) -> ComposeResult:
        yield Static("test", id="placeholder")


class _SubmissionCountingApp(_ShellApp):
    """Host app that records bubbled input submissions."""

    def __init__(self) -> None:
        super().__init__()
        self.submission_count = 0

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submission_count += 1


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


def test_build_entries_include_parent_and_create(tmp_path: Path) -> None:
    entries = armory_browser.build_entries(tmp_path, allow_create=True)

    assert entries[0].is_parent
    assert entries[0].label == armory_browser._PARENT_LABEL
    assert entries[1].is_create
    assert entries[1].label == armory_browser._NEW_ARMORY_LABEL
    assert len(entries) >= 2


def test_build_entries_without_create_flag(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "alpha", "beta")
    entries = armory_browser.build_entries(tmp_path, allow_create=False)

    labels = [e.label for e in entries]
    assert not any(e.is_create for e in entries)
    assert any("alpha" in label for label in labels)
    assert any("beta" in label for label in labels)


def test_build_entries_can_include_common_places(tmp_path: Path) -> None:
    entries = armory_browser.build_entries(tmp_path, allow_create=True, show_places=True)

    labels = [entry.label for entry in entries]
    assert any(label.startswith("place   home") for label in labels)
    assert any(entry.path == Path("/") for entry in entries)


def test_build_entries_returns_correct_paths(tmp_path: Path) -> None:
    alpha, beta = _make_dirs(tmp_path, "alpha", "beta")
    entries = armory_browser.build_entries(tmp_path, allow_create=True)

    # entries: 0=parent, 1=create, 2=alpha, 3=beta
    assert entries[0].path is None
    assert entries[0].is_parent
    assert entries[1].path is None
    assert entries[1].is_create
    assert entries[2].path == alpha
    assert entries[3].path == beta


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


def test_browser_css_uses_borderless_transparent_surface() -> None:
    css = armory_browser._armory_browser_css(armory_browser.current_palette())

    dialog_start = css.index("#armory-dialog {")
    dialog_end = css.index("}", dialog_start)
    dialog_block = css[dialog_start:dialog_end]
    assert "border: none" in dialog_block
    assert "background-tint: transparent" in dialog_block
    assert "border: round" not in css


def test_browser_arrow_keys_move_highlight(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "alpha", "beta")

    async def run_keys() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(100, 28)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            assert ol.highlighted == 0

            await pilot.press("down")
            await pilot.pause()
            assert ol.highlighted == 1

            await pilot.press("up")
            await pilot.pause()
            assert ol.highlighted == 0

    asyncio.run(run_keys())


def test_browser_navigates_into_child_via_action(tmp_path: Path) -> None:
    child = _make_dirs(tmp_path, "child")[0]

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.path == child
            )
            await pilot.pause()
            screen.action_activate()
            await pilot.pause()
            assert screen._current == child

    asyncio.run(run_nav())


def test_browser_right_arrow_navigates_into_child(tmp_path: Path) -> None:
    child = _make_dirs(tmp_path, "child")[0]

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(100, 28)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.path == child
            )
            await pilot.press("right")
            await pilot.pause()
            assert screen._current == child

    asyncio.run(run_nav())


def test_browser_navigates_to_parent_via_action(tmp_path: Path) -> None:
    child_dir = tmp_path / "child"
    child_dir.mkdir()

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=child_dir)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.is_parent
            )
            await pilot.pause()
            screen.action_activate()
            await pilot.pause()
            assert screen._current == tmp_path

    asyncio.run(run_nav())


def test_browser_choose_dismisses_with_path(tmp_path: Path) -> None:
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
            screen.action_choose()
            await pilot.pause()

    asyncio.run(run_choose())
    assert result_path == tmp_path


def test_browser_cancel_dismisses_with_none(tmp_path: Path) -> None:
    result_path: Path | None = "NOT_NONE"  # sentinel  # ty:ignore[invalid-assignment]

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_cancel() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen.action_cancel()
            await pilot.pause()

    asyncio.run(run_cancel())
    assert result_path is None


def test_browser_escape_key_dismisses_with_none(tmp_path: Path) -> None:
    result_path: Path | None = "NOT_NONE"  # sentinel  # ty:ignore[invalid-assignment]

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_cancel() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            await pilot.press("escape")
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
                armory_browser.Input.Submitted(inp, "test-armory", "test-armory")  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()

    asyncio.run(run_new())
    assert result_path is not None
    assert result_path.name == "test-armory"
    assert (result_path / MARKER_FILE).exists()


def test_browser_new_armory_submission_does_not_bubble_to_chat(tmp_path: Path) -> None:
    async def run_new() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _SubmissionCountingApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "maths"
            await pilot.press("enter")
            await pilot.pause()
            assert app.submission_count == 0

    asyncio.run(run_new())


def test_new_armory_path_rejects_escape_names(tmp_path: Path) -> None:
    bad_names = ("../outside", "/tmp/outside", "nested/armory")

    for name in bad_names:
        path, error = armory_browser.new_armory_path(tmp_path, name)
        assert path is None
        assert error is not None


def test_new_armory_path_rejects_existing_folder(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()

    path, error = armory_browser.new_armory_path(tmp_path, "existing")

    assert path is None
    assert error is not None
    assert "already exists" in error


def test_browser_new_armory_refuses_unwritable_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def not_writable(_path: Path) -> bool:
        return False

    monkeypatch.setattr(armory_browser, "_is_writable_directory", not_writable)

    async def run_error() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "blocked"
            await pilot.press("enter")
            await pilot.pause()
            error = screen.query_one("#armory-error", armory_browser.Static)
            assert "read-only folder" in str(error.render())
            assert not (tmp_path / "blocked").exists()

    asyncio.run(run_error())


def test_browser_new_armory_surfaces_creation_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_initialize(_path: Path) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr(armory_browser, "initialize", fail_initialize)

    async def run_error() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=tmp_path)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "blocked", "blocked")  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()
            error = screen.query_one("#armory-error", armory_browser.Static)
            assert "Could not create armory" in str(error.render())
            assert screen._creating is True

    asyncio.run(run_error())


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
                armory_browser.Input.Submitted(inp, "   ", "   ")  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()
            assert screen._creating is False

    asyncio.run(run_empty())
